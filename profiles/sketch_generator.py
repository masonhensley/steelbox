"""
Sketch Generator - Convert TubeProfile to FreeCAD Sketch for extrusion.

Creates a fully constrained FreeCAD Sketcher sketch representing the
tube cross-section, ready for Part extrusion.
"""

from typing import Optional, Tuple
import math

# FreeCAD imports - only available when running inside FreeCAD
try:
    import FreeCAD as App
    import Part
    from FreeCAD import Vector
    HAS_FREECAD = True
except ImportError:
    HAS_FREECAD = False
    App = None
    Part = None
    Vector = None

from .tube_profile import TubeProfile, ProfileGeometry


def _check_freecad():
    """Raise error if FreeCAD is not available."""
    if not HAS_FREECAD:
        raise RuntimeError(
            "FreeCAD not available. This function must be run inside FreeCAD."
        )


def create_tube_wire(
    geometry: ProfileGeometry,
    center: Tuple[float, float] = (0, 0),
    is_outer: bool = True
) -> "Part.Wire":
    """
    Create a Part.Wire representing the tube profile boundary.

    Args:
        geometry: ProfileGeometry with dimensions.
        center: Center point (x, y) in mm.
        is_outer: True for outer boundary, False for inner.

    Returns:
        Part.Wire forming a closed loop.
    """
    _check_freecad()

    cx, cy = center

    if is_outer:
        w = geometry.outer_width_mm / 2
        h = geometry.outer_height_mm / 2
        r = geometry.corner_radius_mm
    else:
        w = geometry.inner_width_mm / 2
        h = geometry.inner_height_mm / 2
        r = geometry.inner_corner_radius_mm or 0

    # Clamp corner radius to half the smaller dimension
    r = min(r, w, h)

    # Build edges: 4 lines + 4 arcs for rounded rectangle
    edges = []

    if r > 0:
        # Use consistent midpoint calculation: 45° from arc center
        # For a quarter circle arc, the midpoint is at 45° between start and end angles
        sqrt2_2 = math.sqrt(2) / 2  # cos(45°) = sin(45°) ≈ 0.707

        # Bottom edge (left to right)
        edges.append(Part.LineSegment(
            Vector(cx - w + r, cy - h, 0),
            Vector(cx + w - r, cy - h, 0)
        ))
        # Bottom-right arc (center at cx+w-r, cy-h+r, from 270° to 360°/0°)
        br_cx, br_cy = cx + w - r, cy - h + r
        edges.append(Part.Arc(
            Vector(cx + w - r, cy - h, 0),  # Start at 270°
            Vector(br_cx + r * sqrt2_2, br_cy - r * sqrt2_2, 0),  # Mid at 315°
            Vector(cx + w, cy - h + r, 0)   # End at 0°
        ))
        # Right edge (bottom to top)
        edges.append(Part.LineSegment(
            Vector(cx + w, cy - h + r, 0),
            Vector(cx + w, cy + h - r, 0)
        ))
        # Top-right arc (center at cx+w-r, cy+h-r, from 0° to 90°)
        tr_cx, tr_cy = cx + w - r, cy + h - r
        edges.append(Part.Arc(
            Vector(cx + w, cy + h - r, 0),   # Start at 0°
            Vector(tr_cx + r * sqrt2_2, tr_cy + r * sqrt2_2, 0),  # Mid at 45°
            Vector(cx + w - r, cy + h, 0)    # End at 90°
        ))
        # Top edge (right to left)
        edges.append(Part.LineSegment(
            Vector(cx + w - r, cy + h, 0),
            Vector(cx - w + r, cy + h, 0)
        ))
        # Top-left arc (center at cx-w+r, cy+h-r, from 90° to 180°)
        tl_cx, tl_cy = cx - w + r, cy + h - r
        edges.append(Part.Arc(
            Vector(cx - w + r, cy + h, 0),   # Start at 90°
            Vector(tl_cx - r * sqrt2_2, tl_cy + r * sqrt2_2, 0),  # Mid at 135°
            Vector(cx - w, cy + h - r, 0)    # End at 180°
        ))
        # Left edge (top to bottom)
        edges.append(Part.LineSegment(
            Vector(cx - w, cy + h - r, 0),
            Vector(cx - w, cy - h + r, 0)
        ))
        # Bottom-left arc (center at cx-w+r, cy-h+r, from 180° to 270°)
        bl_cx, bl_cy = cx - w + r, cy - h + r
        edges.append(Part.Arc(
            Vector(cx - w, cy - h + r, 0),   # Start at 180°
            Vector(bl_cx - r * sqrt2_2, bl_cy - r * sqrt2_2, 0),  # Mid at 225°
            Vector(cx - w + r, cy - h, 0)    # End at 270°
        ))
    else:
        # Simple rectangle without rounded corners
        edges.append(Part.LineSegment(
            Vector(cx - w, cy - h, 0),
            Vector(cx + w, cy - h, 0)
        ))
        edges.append(Part.LineSegment(
            Vector(cx + w, cy - h, 0),
            Vector(cx + w, cy + h, 0)
        ))
        edges.append(Part.LineSegment(
            Vector(cx + w, cy + h, 0),
            Vector(cx - w, cy + h, 0)
        ))
        edges.append(Part.LineSegment(
            Vector(cx - w, cy + h, 0),
            Vector(cx - w, cy - h, 0)
        ))

    # Convert to edges and make wire
    edge_shapes = [e.toShape() for e in edges]
    wire = Part.Wire(edge_shapes)

    return wire


def create_tube_face(
    geometry: ProfileGeometry,
    center: Tuple[float, float] = (0, 0)
) -> "Part.Face":
    """
    Create a Part.Face representing the tube cross-section.

    The face has a hole in the middle (outer boundary minus inner).

    Args:
        geometry: ProfileGeometry with dimensions.
        center: Center point (x, y) in mm.

    Returns:
        Part.Face with hollow center.
    """
    _check_freecad()

    outer_wire = create_tube_wire(geometry, center, is_outer=True)
    inner_wire = create_tube_wire(geometry, center, is_outer=False)

    # Create face from outer wire with inner wire as hole
    face = Part.Face([outer_wire, inner_wire])

    return face


def create_tube_solid(
    profile: TubeProfile,
    length_mm: float,
    center: Tuple[float, float] = (0, 0)
) -> "Part.Shape":
    """
    Create a Part.Shape (solid) by extruding the tube profile.

    Args:
        profile: TubeProfile to extrude.
        length_mm: Extrusion length in mm.
        center: Center point for profile.

    Returns:
        Part.Shape (solid tube).
    """
    _check_freecad()

    face = create_tube_face(profile.geometry, center)
    solid = face.extrude(Vector(0, 0, length_mm))

    return solid


def create_profile_sketch(
    doc: "App.Document",
    profile: TubeProfile,
    name: Optional[str] = None,
    center: Tuple[float, float] = (0, 0)
) -> "App.DocumentObject":
    """
    Create a FreeCAD Sketcher sketch from a tube profile.

    This creates a fully constrained parametric sketch that can be
    used for extrusion and maintains editability.

    Args:
        doc: FreeCAD document.
        profile: TubeProfile to convert.
        name: Sketch name (defaults to profile name).
        center: Center point in mm.

    Returns:
        Sketcher.SketchObject
    """
    _check_freecad()

    # Create sketch object
    sketch_name = name or f"Profile_{profile.name}"
    sketch = doc.addObject("Sketcher::SketchObject", sketch_name)

    g = profile.geometry
    cx, cy = center

    # Helper to add geometry
    def add_line(x1, y1, x2, y2):
        return sketch.addGeometry(
            Part.LineSegment(Vector(x1, y1, 0), Vector(x2, y2, 0))
        )

    def add_arc_by_center(cx, cy, r, start_angle, end_angle):
        # FreeCAD Sketcher uses radians
        return sketch.addGeometry(
            Part.ArcOfCircle(
                Part.Circle(Vector(cx, cy, 0), Vector(0, 0, 1), r),
                math.radians(start_angle),
                math.radians(end_angle)
            )
        )

    # Add outer boundary
    ow = g.outer_width_mm / 2
    oh = g.outer_height_mm / 2
    r_out = min(g.corner_radius_mm, ow, oh) if g.corner_radius_mm > 0 else 0

    if r_out > 0:
        # Rounded rectangle - 4 lines + 4 arcs
        # Bottom
        add_line(cx - ow + r_out, cy - oh, cx + ow - r_out, cy - oh)
        add_arc_by_center(cx + ow - r_out, cy - oh + r_out, r_out, 270, 360)
        # Right
        add_line(cx + ow, cy - oh + r_out, cx + ow, cy + oh - r_out)
        add_arc_by_center(cx + ow - r_out, cy + oh - r_out, r_out, 0, 90)
        # Top
        add_line(cx + ow - r_out, cy + oh, cx - ow + r_out, cy + oh)
        add_arc_by_center(cx - ow + r_out, cy + oh - r_out, r_out, 90, 180)
        # Left
        add_line(cx - ow, cy + oh - r_out, cx - ow, cy - oh + r_out)
        add_arc_by_center(cx - ow + r_out, cy - oh + r_out, r_out, 180, 270)
    else:
        # Simple rectangle
        add_line(cx - ow, cy - oh, cx + ow, cy - oh)
        add_line(cx + ow, cy - oh, cx + ow, cy + oh)
        add_line(cx + ow, cy + oh, cx - ow, cy + oh)
        add_line(cx - ow, cy + oh, cx - ow, cy - oh)

    # Add inner boundary
    iw = g.inner_width_mm / 2
    ih = g.inner_height_mm / 2
    r_in = min(g.inner_corner_radius_mm or 0, iw, ih)

    if r_in > 0:
        # Inner rounded rectangle
        add_line(cx - iw + r_in, cy - ih, cx + iw - r_in, cy - ih)
        add_arc_by_center(cx + iw - r_in, cy - ih + r_in, r_in, 270, 360)
        add_line(cx + iw, cy - ih + r_in, cx + iw, cy + ih - r_in)
        add_arc_by_center(cx + iw - r_in, cy + ih - r_in, r_in, 0, 90)
        add_line(cx + iw - r_in, cy + ih, cx - iw + r_in, cy + ih)
        add_arc_by_center(cx - iw + r_in, cy + ih - r_in, r_in, 90, 180)
        add_line(cx - iw, cy + ih - r_in, cx - iw, cy - ih + r_in)
        add_arc_by_center(cx - iw + r_in, cy - ih + r_in, r_in, 180, 270)
    else:
        # Simple inner rectangle
        add_line(cx - iw, cy - ih, cx + iw, cy - ih)
        add_line(cx + iw, cy - ih, cx + iw, cy + ih)
        add_line(cx + iw, cy + ih, cx - iw, cy + ih)
        add_line(cx - iw, cy + ih, cx - iw, cy - ih)

    doc.recompute()
    return sketch


def profile_to_part(
    doc: "App.Document",
    profile: TubeProfile,
    length_mm: float,
    name: Optional[str] = None
) -> "App.DocumentObject":
    """
    Create a Part object from a tube profile.

    This creates a non-parametric Part::Feature with the extruded shape.
    For parametric parts, use create_profile_sketch() + Pad.

    Args:
        doc: FreeCAD document.
        profile: TubeProfile to convert.
        length_mm: Extrusion length.
        name: Part name (defaults to profile name).

    Returns:
        Part::Feature object.
    """
    _check_freecad()

    part_name = name or f"Tube_{profile.name}"
    part = doc.addObject("Part::Feature", part_name)
    part.Shape = create_tube_solid(profile, length_mm)

    doc.recompute()
    return part
