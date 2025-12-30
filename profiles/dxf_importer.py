"""
DXF Importer - Extract tube profile geometry from DXF files.

Parses DXF files containing tube cross-sections (typically outer and inner
boundaries made of lines and arcs) and extracts geometric parameters.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional
import math

try:
    import ezdxf
    from ezdxf.entities import Line, Arc, LWPolyline, Circle
    HAS_EZDXF = True
except ImportError:
    HAS_EZDXF = False

from .tube_profile import TubeProfile, ProfileGeometry, ProfileTolerances, ProfileMetadata


@dataclass
class ExtractedLoop:
    """A closed loop extracted from DXF entities."""
    entities: list
    bounds: Tuple[float, float, float, float]  # min_x, min_y, max_x, max_y
    width: float
    height: float
    corner_radius: float  # Average corner radius from arcs
    is_outer: bool = True


def _get_entity_bounds(entity) -> Tuple[float, float, float, float]:
    """Get bounding box for a DXF entity."""
    if isinstance(entity, Line):
        x1, y1 = entity.dxf.start.x, entity.dxf.start.y
        x2, y2 = entity.dxf.end.x, entity.dxf.end.y
        return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

    elif isinstance(entity, Arc):
        # Arc bounds - use center and radius for approximation
        cx, cy = entity.dxf.center.x, entity.dxf.center.y
        r = entity.dxf.radius
        # For tube profiles, arcs are usually quarter circles at corners
        # Use conservative bounds
        return (cx - r, cy - r, cx + r, cy + r)

    elif isinstance(entity, Circle):
        cx, cy = entity.dxf.center.x, entity.dxf.center.y
        r = entity.dxf.radius
        return (cx - r, cy - r, cx + r, cy + r)

    return (0, 0, 0, 0)


def _classify_entities_by_size(
    entities: list
) -> Tuple[List, List]:
    """
    Separate entities into outer and inner loops based on extent.

    For tube profiles, outer boundary entities will have larger coordinates
    than inner boundary entities.
    """
    if not entities:
        return [], []

    # Calculate bounds for each entity
    entity_bounds = []
    for e in entities:
        bounds = _get_entity_bounds(e)
        max_extent = max(abs(bounds[2] - bounds[0]), abs(bounds[3] - bounds[1]))
        entity_bounds.append((e, bounds, max_extent))

    # Find the extent threshold (midpoint between min and max extents)
    extents = [eb[2] for eb in entity_bounds]
    min_extent = min(extents)
    max_extent = max(extents)
    threshold = (min_extent + max_extent) / 2

    # For arcs, use radius to classify
    outer = []
    inner = []

    for e, bounds, extent in entity_bounds:
        if isinstance(e, Arc):
            # Use arc radius for classification
            r = e.dxf.radius
            arc_radii = [eb[0].dxf.radius for eb in entity_bounds if isinstance(eb[0], Arc)]
            if arc_radii:
                max_arc_r = max(arc_radii)
                min_arc_r = min(arc_radii)
                r_threshold = (min_arc_r + max_arc_r) / 2
                if r >= r_threshold:
                    outer.append(e)
                else:
                    inner.append(e)
            else:
                outer.append(e)
        elif isinstance(e, Line):
            # Use line extent/position to classify
            # Lines farther from center are outer
            line_center = (
                (bounds[0] + bounds[2]) / 2,
                (bounds[1] + bounds[3]) / 2
            )
            dist_from_origin = math.sqrt(line_center[0]**2 + line_center[1]**2)

            # Get all line centers to find threshold
            line_entities = [(eb[0], eb[1]) for eb in entity_bounds if isinstance(eb[0], Line)]
            if line_entities:
                distances = []
                for le, lb in line_entities:
                    lc = ((lb[0] + lb[2]) / 2, (lb[1] + lb[3]) / 2)
                    distances.append(math.sqrt(lc[0]**2 + lc[1]**2))
                d_threshold = (min(distances) + max(distances)) / 2
                if dist_from_origin >= d_threshold:
                    outer.append(e)
                else:
                    inner.append(e)
            else:
                outer.append(e)
        else:
            outer.append(e)

    return outer, inner


def _extract_geometry_from_entities(
    entities: list,
    is_outer: bool = True
) -> Tuple[float, float, float]:
    """
    Extract width, height, and corner radius from a set of entities.

    Returns: (width, height, corner_radius)
    """
    if not entities:
        return (0, 0, 0)

    # Get overall bounds
    all_bounds = [_get_entity_bounds(e) for e in entities]
    min_x = min(b[0] for b in all_bounds)
    min_y = min(b[1] for b in all_bounds)
    max_x = max(b[2] for b in all_bounds)
    max_y = max(b[3] for b in all_bounds)

    width = max_x - min_x
    height = max_y - min_y

    # Get corner radius from arcs
    arc_radii = [e.dxf.radius for e in entities if isinstance(e, Arc)]
    corner_radius = sum(arc_radii) / len(arc_radii) if arc_radii else 0

    return (width, height, corner_radius)


def extract_geometry_from_dxf(
    dxf_path: Path,
    units: str = "inch"
) -> Tuple[ProfileGeometry, dict]:
    """
    Extract tube profile geometry from a DXF file.

    Args:
        dxf_path: Path to the DXF file.
        units: Units of the DXF file ("inch" or "mm").

    Returns:
        Tuple of (ProfileGeometry, raw_data_dict)

    Raises:
        ImportError: If ezdxf is not installed.
        ValueError: If DXF cannot be parsed or has no valid geometry.
    """
    if not HAS_EZDXF:
        raise ImportError(
            "ezdxf is required for DXF import. "
            "Install with: pip install ezdxf"
        )

    dxf_path = Path(dxf_path)
    if not dxf_path.exists():
        raise FileNotFoundError(f"DXF file not found: {dxf_path}")

    # Load DXF
    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()

    # Collect relevant entities (lines and arcs for tube profiles)
    entities = []
    for entity in msp:
        if entity.dxftype() in ('LINE', 'ARC', 'CIRCLE', 'LWPOLYLINE'):
            entities.append(entity)

    if not entities:
        raise ValueError(f"No geometry found in DXF: {dxf_path}")

    # Separate into outer and inner loops
    outer_entities, inner_entities = _classify_entities_by_size(entities)

    # Extract dimensions
    outer_w, outer_h, outer_r = _extract_geometry_from_entities(outer_entities, is_outer=True)
    inner_w, inner_h, inner_r = _extract_geometry_from_entities(inner_entities, is_outer=False)

    # Convert units if needed
    scale = 25.4 if units == "inch" else 1.0

    outer_w_mm = outer_w * scale
    outer_h_mm = outer_h * scale
    outer_r_mm = outer_r * scale
    inner_r_mm = inner_r * scale

    # Calculate wall thickness from difference
    wall_thickness_mm = (outer_w_mm - inner_w * scale) / 2

    # Build geometry
    geometry = ProfileGeometry(
        outer_width_mm=outer_w_mm,
        outer_height_mm=outer_h_mm,
        wall_thickness_mm=wall_thickness_mm,
        corner_radius_mm=outer_r_mm,
        inner_corner_radius_mm=inner_r_mm,
        dxf_file=dxf_path.name,
    )

    # Raw data for debugging
    raw_data = {
        "dxf_path": str(dxf_path),
        "units": units,
        "scale": scale,
        "entity_count": len(entities),
        "outer_entities": len(outer_entities),
        "inner_entities": len(inner_entities),
        "outer_dims_raw": (outer_w, outer_h, outer_r),
        "inner_dims_raw": (inner_w, inner_h, inner_r),
    }

    return geometry, raw_data


def import_dxf_profile(
    dxf_path: Path,
    name: Optional[str] = None,
    description: str = "",
    units: str = "inch",
    manufacturer: str = "",
    tolerances: Optional[ProfileTolerances] = None,
) -> TubeProfile:
    """
    Import a DXF file and create a TubeProfile.

    Args:
        dxf_path: Path to the DXF file.
        name: Profile name (defaults to filename stem).
        description: Profile description.
        units: DXF units ("inch" or "mm").
        manufacturer: Fabricator name.
        tolerances: Tolerance values (uses defaults if not provided).

    Returns:
        TubeProfile with extracted geometry.
    """
    dxf_path = Path(dxf_path)

    # Extract geometry
    geometry, raw_data = extract_geometry_from_dxf(dxf_path, units=units)

    # Generate name from filename if not provided
    if name is None:
        name = dxf_path.stem.replace(" ", "_").replace("-", "x")

    # Build profile
    profile = TubeProfile(
        name=name,
        description=description or f"Imported from {dxf_path.name}",
        geometry=geometry,
        tolerances=tolerances or ProfileTolerances(),
        metadata=ProfileMetadata(
            manufacturer=manufacturer,
            notes=f"Imported from DXF: {dxf_path.name}",
        ),
    )

    return profile


def detect_dxf_units(dxf_path: Path) -> str:
    """
    Attempt to detect DXF units based on $INSUNITS header.

    Returns: "inch", "mm", or "unknown"
    """
    if not HAS_EZDXF:
        return "unknown"

    try:
        doc = ezdxf.readfile(str(dxf_path))
        insunits = doc.header.get("$INSUNITS", 0)
        # DXF INSUNITS: 1=inches, 4=mm, 5=cm, 6=m
        if insunits == 1:
            return "inch"
        elif insunits == 4:
            return "mm"
        elif insunits == 5:
            return "cm"
        elif insunits == 6:
            return "m"
        else:
            # Try to guess from geometry extent
            msp = doc.modelspace()
            all_x = []
            for e in msp:
                if hasattr(e.dxf, 'start'):
                    all_x.append(abs(e.dxf.start.x))
                if hasattr(e.dxf, 'end'):
                    all_x.append(abs(e.dxf.end.x))
                if hasattr(e.dxf, 'center'):
                    all_x.append(abs(e.dxf.center.x))
            if all_x:
                max_coord = max(all_x)
                # If max coordinate is < 20, probably inches
                # If > 20, probably mm
                return "inch" if max_coord < 20 else "mm"
            return "unknown"
    except Exception:
        return "unknown"
