"""
Hole Pattern Generator - Distribute holes across surfaces.

Generates hole patterns for frames and panels with support for:
- Distribution by count (N holes evenly spaced)
- Distribution by distance (hole every X mm)
- Edge margins
- Alignment with mating parts
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Union
from enum import Enum
import math

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

from .hole_types import HoleSpec, HoleType


class PatternDistribution(Enum):
    """How holes are distributed in a pattern."""
    BY_COUNT = "by_count"         # Specific number of holes
    BY_SPACING = "by_spacing"     # Holes at fixed intervals
    SINGLE = "single"             # Single hole at position
    GRID = "grid"                 # 2D grid pattern


@dataclass
class HolePosition:
    """A single hole position in 3D space."""
    x: float
    y: float
    z: float
    hole_spec: HoleSpec
    normal: Tuple[float, float, float] = (0, 0, 1)  # Hole direction

    def as_vector(self) -> "Vector":
        """Convert to FreeCAD Vector."""
        if not HAS_FREECAD:
            raise RuntimeError("FreeCAD not available")
        return Vector(self.x, self.y, self.z)


@dataclass
class HolePattern:
    """
    A pattern of holes to be applied to a surface.

    Can be a linear row, 2D grid, or custom positions.
    """
    name: str = "HolePattern"
    distribution: PatternDistribution = PatternDistribution.BY_COUNT
    hole_spec: HoleSpec = None

    # Linear pattern parameters
    start: Tuple[float, float, float] = (0, 0, 0)
    end: Tuple[float, float, float] = (100, 0, 0)
    count: int = 3
    spacing_mm: float = 50.0

    # Grid pattern parameters (adds second axis)
    grid_count_2: int = 1         # Count in second direction
    grid_spacing_2: float = 50.0  # Spacing in second direction
    grid_direction_2: Tuple[float, float, float] = (0, 1, 0)

    # Margins
    margin_start: float = 25.0    # Margin from start
    margin_end: float = 25.0      # Margin from end

    # Normal direction for holes
    normal: Tuple[float, float, float] = (0, 0, 1)

    # Computed positions
    positions: List[HolePosition] = field(default_factory=list)

    def compute_positions(self) -> List[HolePosition]:
        """Compute all hole positions based on pattern parameters."""
        self.positions = []

        if self.distribution == PatternDistribution.SINGLE:
            self.positions.append(HolePosition(
                x=self.start[0],
                y=self.start[1],
                z=self.start[2],
                hole_spec=self.hole_spec,
                normal=self.normal,
            ))

        elif self.distribution == PatternDistribution.BY_COUNT:
            self._compute_by_count()

        elif self.distribution == PatternDistribution.BY_SPACING:
            self._compute_by_spacing()

        elif self.distribution == PatternDistribution.GRID:
            self._compute_grid()

        return self.positions

    def _compute_by_count(self):
        """Compute positions for fixed count distribution."""
        if self.count < 1:
            return

        # Direction vector
        dx = self.end[0] - self.start[0]
        dy = self.end[1] - self.start[1]
        dz = self.end[2] - self.start[2]
        length = math.sqrt(dx*dx + dy*dy + dz*dz)

        if length < 0.001:
            return

        # Normalize direction
        dx, dy, dz = dx/length, dy/length, dz/length

        # Usable length after margins
        usable = length - self.margin_start - self.margin_end
        if usable <= 0:
            return

        # Spacing between holes
        if self.count == 1:
            spacing = 0
            start_offset = self.margin_start + usable / 2
        else:
            spacing = usable / (self.count - 1)
            start_offset = self.margin_start

        # Generate positions
        for i in range(self.count):
            offset = start_offset + i * spacing
            self.positions.append(HolePosition(
                x=self.start[0] + dx * offset,
                y=self.start[1] + dy * offset,
                z=self.start[2] + dz * offset,
                hole_spec=self.hole_spec,
                normal=self.normal,
            ))

    def _compute_by_spacing(self):
        """Compute positions for fixed spacing distribution."""
        if self.spacing_mm <= 0:
            return

        # Direction vector
        dx = self.end[0] - self.start[0]
        dy = self.end[1] - self.start[1]
        dz = self.end[2] - self.start[2]
        length = math.sqrt(dx*dx + dy*dy + dz*dz)

        if length < 0.001:
            return

        # Normalize
        dx, dy, dz = dx/length, dy/length, dz/length

        # Usable length
        usable = length - self.margin_start - self.margin_end
        if usable <= 0:
            return

        # Number of holes that fit
        count = int(usable / self.spacing_mm) + 1

        # Center the pattern
        actual_length = (count - 1) * self.spacing_mm
        start_offset = self.margin_start + (usable - actual_length) / 2

        for i in range(count):
            offset = start_offset + i * self.spacing_mm
            self.positions.append(HolePosition(
                x=self.start[0] + dx * offset,
                y=self.start[1] + dy * offset,
                z=self.start[2] + dz * offset,
                hole_spec=self.hole_spec,
                normal=self.normal,
            ))

    def _compute_grid(self):
        """Compute positions for 2D grid pattern."""
        # First compute primary axis positions
        primary_positions = []

        # Direction vector for primary axis
        dx = self.end[0] - self.start[0]
        dy = self.end[1] - self.start[1]
        dz = self.end[2] - self.start[2]
        length = math.sqrt(dx*dx + dy*dy + dz*dz)

        if length < 0.001:
            return

        dx, dy, dz = dx/length, dy/length, dz/length
        usable = length - self.margin_start - self.margin_end

        if self.count == 1:
            spacing = 0
            start_offset = self.margin_start + usable / 2
        else:
            spacing = usable / (self.count - 1) if usable > 0 else 0
            start_offset = self.margin_start

        for i in range(self.count):
            offset = start_offset + i * spacing
            primary_positions.append((
                self.start[0] + dx * offset,
                self.start[1] + dy * offset,
                self.start[2] + dz * offset,
            ))

        # Secondary axis
        d2x, d2y, d2z = self.grid_direction_2

        # Center secondary axis
        secondary_offset_start = -((self.grid_count_2 - 1) * self.grid_spacing_2) / 2

        for px, py, pz in primary_positions:
            for j in range(self.grid_count_2):
                offset_2 = secondary_offset_start + j * self.grid_spacing_2
                self.positions.append(HolePosition(
                    x=px + d2x * offset_2,
                    y=py + d2y * offset_2,
                    z=pz + d2z * offset_2,
                    hole_spec=self.hole_spec,
                    normal=self.normal,
                ))


class HolePatternGenerator:
    """
    Generates hole patterns and applies them to geometry.

    Usage:
        gen = HolePatternGenerator()
        pattern = gen.create_linear_pattern(
            hole_spec=RivetHole(4.8),
            start=(0, 0, 0),
            end=(500, 0, 0),
            count=5,
        )
        shape = gen.apply_pattern_to_shape(base_shape, pattern)
    """

    def __init__(self):
        """Initialize pattern generator."""
        pass

    def create_linear_pattern(
        self,
        hole_spec: HoleSpec,
        start: Tuple[float, float, float],
        end: Tuple[float, float, float],
        count: Optional[int] = None,
        spacing_mm: Optional[float] = None,
        margin_start: float = 25.0,
        margin_end: float = 25.0,
        normal: Tuple[float, float, float] = (0, 0, 1),
    ) -> HolePattern:
        """
        Create a linear hole pattern.

        Specify either count OR spacing, not both.

        Args:
            hole_spec: Hole specification.
            start: Start point of pattern line.
            end: End point of pattern line.
            count: Number of holes (mutually exclusive with spacing).
            spacing_mm: Spacing between holes (mutually exclusive with count).
            margin_start: Margin from start point.
            margin_end: Margin from end point.
            normal: Direction holes face.

        Returns:
            HolePattern with computed positions.
        """
        if count is not None and spacing_mm is not None:
            raise ValueError("Specify either count or spacing_mm, not both")

        if count is not None:
            distribution = PatternDistribution.BY_COUNT
            spacing = 0
        elif spacing_mm is not None:
            distribution = PatternDistribution.BY_SPACING
            spacing = spacing_mm
            count = 0
        else:
            raise ValueError("Must specify either count or spacing_mm")

        pattern = HolePattern(
            name="LinearPattern",
            distribution=distribution,
            hole_spec=hole_spec,
            start=start,
            end=end,
            count=count,
            spacing_mm=spacing,
            margin_start=margin_start,
            margin_end=margin_end,
            normal=normal,
        )

        pattern.compute_positions()
        return pattern

    def create_grid_pattern(
        self,
        hole_spec: HoleSpec,
        start: Tuple[float, float, float],
        end: Tuple[float, float, float],
        count_primary: int,
        count_secondary: int,
        spacing_secondary: float,
        direction_secondary: Tuple[float, float, float] = (0, 1, 0),
        margin_start: float = 25.0,
        margin_end: float = 25.0,
        normal: Tuple[float, float, float] = (0, 0, 1),
    ) -> HolePattern:
        """
        Create a 2D grid hole pattern.

        Args:
            hole_spec: Hole specification.
            start: Start point of primary axis.
            end: End point of primary axis.
            count_primary: Number of holes along primary axis.
            count_secondary: Number of holes along secondary axis.
            spacing_secondary: Spacing along secondary axis (mm).
            direction_secondary: Unit vector for secondary axis.
            margin_start: Margin from start.
            margin_end: Margin from end.
            normal: Direction holes face.

        Returns:
            HolePattern with computed positions.
        """
        pattern = HolePattern(
            name="GridPattern",
            distribution=PatternDistribution.GRID,
            hole_spec=hole_spec,
            start=start,
            end=end,
            count=count_primary,
            grid_count_2=count_secondary,
            grid_spacing_2=spacing_secondary,
            grid_direction_2=direction_secondary,
            margin_start=margin_start,
            margin_end=margin_end,
            normal=normal,
        )

        pattern.compute_positions()
        return pattern

    def create_hole_shape(
        self,
        hole_pos: HolePosition,
        depth: float = 100.0,
    ) -> "Part.Shape":
        """
        Create a cylinder shape for a hole.

        Args:
            hole_pos: Hole position and spec.
            depth: Depth of hole (for cutting through).

        Returns:
            Part.Shape (cylinder) for boolean cut.
        """
        if not HAS_FREECAD:
            raise RuntimeError("FreeCAD not available")

        radius = hole_pos.hole_spec.diameter_mm / 2
        nx, ny, nz = hole_pos.normal

        # Create cylinder along the normal direction
        cylinder = Part.makeCylinder(
            radius,
            depth,
            hole_pos.as_vector() - Vector(nx, ny, nz) * (depth / 2),
            Vector(nx, ny, nz),
        )

        # Add countersink if specified
        if hole_pos.hole_spec.countersink:
            cs_radius = hole_pos.hole_spec.countersink_diameter_mm / 2
            cs_depth = hole_pos.hole_spec.countersink_depth_mm

            if cs_radius > 0 and cs_depth > 0:
                # Countersink cone
                cone = Part.makeCone(
                    cs_radius, radius,
                    cs_depth,
                    hole_pos.as_vector(),
                    Vector(nx, ny, nz),
                )
                cylinder = cylinder.fuse(cone)

        return cylinder

    def apply_pattern_to_shape(
        self,
        base_shape: "Part.Shape",
        pattern: HolePattern,
        depth: float = 100.0,
    ) -> "Part.Shape":
        """
        Apply a hole pattern to a shape using boolean cuts.

        Args:
            base_shape: Shape to cut holes from.
            pattern: Hole pattern to apply.
            depth: Depth for hole cuts.

        Returns:
            Shape with holes cut.
        """
        if not HAS_FREECAD:
            raise RuntimeError("FreeCAD not available")

        result = base_shape

        for hole_pos in pattern.positions:
            hole_shape = self.create_hole_shape(hole_pos, depth)
            result = result.cut(hole_shape)

        return result


def generate_hole_pattern(
    hole_type: str,
    size: str,
    start: Tuple[float, float, float],
    end: Tuple[float, float, float],
    count: Optional[int] = None,
    spacing_mm: Optional[float] = None,
    **kwargs,
) -> HolePattern:
    """
    Convenience function to generate a hole pattern.

    Args:
        hole_type: "rivet", "riv_nut", "bolt", or "custom"
        size: Size for hole spec
        start: Pattern start point
        end: Pattern end point
        count: Number of holes (or use spacing_mm)
        spacing_mm: Spacing between holes
        **kwargs: Additional args for hole spec or pattern

    Returns:
        HolePattern with positions computed.
    """
    from .hole_types import get_hole_spec

    hole_spec = get_hole_spec(hole_type, size, **kwargs)
    gen = HolePatternGenerator()

    return gen.create_linear_pattern(
        hole_spec=hole_spec,
        start=start,
        end=end,
        count=count,
        spacing_mm=spacing_mm,
        margin_start=kwargs.get("margin_start", 25.0),
        margin_end=kwargs.get("margin_end", 25.0),
        normal=kwargs.get("normal", (0, 0, 1)),
    )


def apply_holes_to_face(
    shape: "Part.Shape",
    face_index: int,
    hole_spec: HoleSpec,
    count: Optional[int] = None,
    spacing_mm: Optional[float] = None,
    margin: float = 25.0,
) -> "Part.Shape":
    """
    Apply holes along a face of a shape.

    Automatically determines hole positions based on face geometry.

    Args:
        shape: Shape containing the face.
        face_index: Index of face in shape.Faces.
        hole_spec: Hole specification.
        count: Number of holes (or use spacing_mm).
        spacing_mm: Spacing between holes.
        margin: Edge margin.

    Returns:
        Shape with holes applied.
    """
    if not HAS_FREECAD:
        raise RuntimeError("FreeCAD not available")

    face = shape.Faces[face_index]
    bbox = face.BoundBox

    # Get face normal
    normal = face.normalAt(0.5, 0.5)

    # Determine primary axis (longest dimension)
    dims = [(bbox.XLength, 0), (bbox.YLength, 1), (bbox.ZLength, 2)]
    dims.sort(reverse=True)
    primary_axis = dims[0][1]

    # Create start/end points along primary axis
    center = face.CenterOfMass

    if primary_axis == 0:  # X
        start = (bbox.XMin + margin, center.y, center.z)
        end = (bbox.XMax - margin, center.y, center.z)
    elif primary_axis == 1:  # Y
        start = (center.x, bbox.YMin + margin, center.z)
        end = (center.x, bbox.YMax - margin, center.z)
    else:  # Z
        start = (center.x, center.y, bbox.ZMin + margin)
        end = (center.x, center.y, bbox.ZMax - margin)

    gen = HolePatternGenerator()
    pattern = gen.create_linear_pattern(
        hole_spec=hole_spec,
        start=start,
        end=end,
        count=count,
        spacing_mm=spacing_mm,
        margin_start=0,  # Already applied above
        margin_end=0,
        normal=(normal.x, normal.y, normal.z),
    )

    return gen.apply_pattern_to_shape(shape, pattern)
