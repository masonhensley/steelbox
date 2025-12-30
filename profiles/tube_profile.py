"""
TubeProfile - Data model for tube cross-section profiles with tolerances.

Each profile bundles geometry (from DXF or manual entry) with manufacturer-specific
tolerances for tab/slot joinery.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path
import json


@dataclass
class ProfileGeometry:
    """Geometric properties of a tube cross-section."""
    outer_width_mm: float
    outer_height_mm: float
    wall_thickness_mm: float
    corner_radius_mm: float = 0.0
    inner_corner_radius_mm: Optional[float] = None  # Derived if not specified
    dxf_file: Optional[str] = None  # Relative path to source DXF
    orientation_top_edge: str = "Y+"  # Which edge is "top" for tab placement

    def __post_init__(self):
        # Default inner corner radius to outer - wall thickness (clamped to 0)
        if self.inner_corner_radius_mm is None:
            self.inner_corner_radius_mm = max(0, self.corner_radius_mm - self.wall_thickness_mm)

    @property
    def inner_width_mm(self) -> float:
        return self.outer_width_mm - 2 * self.wall_thickness_mm

    @property
    def inner_height_mm(self) -> float:
        return self.outer_height_mm - 2 * self.wall_thickness_mm


@dataclass
class ProfileTolerances:
    """
    Manufacturer-specific tolerances for laser cutting.

    These values come from your fabricator (Oshcut, SendCutSend, etc.)
    and are specific to each profile/material/process combination.
    """
    slot_clearance_mm: float = 0.10      # Added to slot width
    tab_undersize_mm: float = 0.05       # Removed from tab width
    kerf_compensation_mm: float = 0.15   # Half kerf width
    corner_relief_radius_mm: float = 1.5 # Radius for slot corners
    finish_allowance_mm: float = 0.0     # Per side (e.g., powder coat)

    @property
    def slot_width(self) -> float:
        """Calculate slot width given a wall thickness."""
        # Note: actual calc needs wall_thickness, done in TubeProfile
        raise NotImplementedError("Use TubeProfile.calc_slot_width()")

    @property
    def total_clearance_mm(self) -> float:
        """Total gap between tab and slot."""
        return (self.slot_clearance_mm +
                self.tab_undersize_mm +
                2 * self.kerf_compensation_mm)


@dataclass
class ProfileMaterial:
    """Material properties for weight calculation and BOM."""
    grade: str = "A36"
    density_kg_m3: float = 7850.0  # Steel default


@dataclass
class ProfileMetadata:
    """Tracking info for the profile source."""
    manufacturer: str = ""
    cutting_process: str = ""  # "Fiber laser", "CO2 laser", "Plasma", etc.
    verified_date: str = ""
    notes: str = ""


@dataclass
class TubeProfile:
    """
    Complete tube profile definition with geometry and tolerances.

    This is the main class used throughout SteelBox. Each profile is
    self-contained - tolerances travel with the geometry.
    """
    name: str
    description: str = ""
    geometry: ProfileGeometry = field(default_factory=lambda: ProfileGeometry(
        outer_width_mm=50.8, outer_height_mm=50.8, wall_thickness_mm=3.175
    ))
    tolerances: ProfileTolerances = field(default_factory=ProfileTolerances)
    material: ProfileMaterial = field(default_factory=ProfileMaterial)
    metadata: ProfileMetadata = field(default_factory=ProfileMetadata)

    # Computed tab/slot dimensions
    def calc_slot_width(self, wall_thickness_mm: Optional[float] = None) -> float:
        """
        Calculate slot width for cutting into a member.

        Args:
            wall_thickness_mm: Override wall thickness (for mating member).
                              Defaults to this profile's wall thickness.
        """
        wall = wall_thickness_mm or self.geometry.wall_thickness_mm
        return (wall +
                self.tolerances.slot_clearance_mm +
                self.tolerances.kerf_compensation_mm)

    def calc_tab_width(self, wall_thickness_mm: Optional[float] = None) -> float:
        """
        Calculate tab width for extending from a member.

        Args:
            wall_thickness_mm: Override wall thickness.
                              Defaults to this profile's wall thickness.
        """
        wall = wall_thickness_mm or self.geometry.wall_thickness_mm
        return (wall -
                self.tolerances.tab_undersize_mm -
                self.tolerances.kerf_compensation_mm)

    def calc_fit_clearance(self) -> float:
        """Total clearance between tab and slot (should be ~0.3-0.5mm for slip fit)."""
        return self.calc_slot_width() - self.calc_tab_width()

    def calc_tab_depth(self, mating_depth_mm: float, ratio: float = 0.6) -> float:
        """
        Calculate how deep a tab should extend into a slot.

        Args:
            mating_depth_mm: Depth of the mating member (perpendicular to tab).
            ratio: Depth ratio (0.5-0.75 typical). Default 0.6.
        """
        return mating_depth_mm * ratio

    # Serialization
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "geometry": asdict(self.geometry),
            "tolerances": asdict(self.tolerances),
            "material": asdict(self.material),
            "metadata": asdict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TubeProfile":
        """Create from dictionary (JSON deserialization)."""
        return cls(
            name=data.get("name", "Unnamed"),
            description=data.get("description", ""),
            geometry=ProfileGeometry(**data.get("geometry", {})),
            tolerances=ProfileTolerances(**data.get("tolerances", {})),
            material=ProfileMaterial(**data.get("material", {})),
            metadata=ProfileMetadata(**data.get("metadata", {})),
        )

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "TubeProfile":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def save(self, path: Path) -> None:
        """Save profile to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json())

    @classmethod
    def load(cls, path: Path) -> "TubeProfile":
        """Load profile from JSON file."""
        return cls.from_json(Path(path).read_text())

    def __repr__(self) -> str:
        g = self.geometry
        return (f"TubeProfile('{self.name}', "
                f"{g.outer_width_mm}x{g.outer_height_mm}x{g.wall_thickness_mm}mm)")


# Convenience factory for common tube sizes
def create_square_tube(
    size_inch: float,
    wall_inch: float,
    name: Optional[str] = None,
    manufacturer: str = "",
) -> TubeProfile:
    """
    Create a square tube profile from imperial dimensions.

    Args:
        size_inch: Outer dimension in inches (e.g., 2.0 for 2x2)
        wall_inch: Wall thickness in inches (e.g., 0.125 for 1/8")
        name: Profile name. Auto-generated if not provided.
        manufacturer: Fabricator name for metadata.
    """
    size_mm = size_inch * 25.4
    wall_mm = wall_inch * 25.4
    corner_mm = wall_mm * 1.5  # Typical corner radius ~1.5x wall

    if name is None:
        # Format: 2x2x0.125
        name = f"{size_inch}x{size_inch}x{wall_inch}"

    return TubeProfile(
        name=name,
        description=f"{size_inch}\"x{size_inch}\" square tube, {wall_inch}\" wall",
        geometry=ProfileGeometry(
            outer_width_mm=size_mm,
            outer_height_mm=size_mm,
            wall_thickness_mm=wall_mm,
            corner_radius_mm=corner_mm,
        ),
        metadata=ProfileMetadata(manufacturer=manufacturer),
    )
