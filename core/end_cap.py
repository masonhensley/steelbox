"""
End Cap Generator - Create caps for open tube ends with tabs.

End caps fit into tube ends and have tabs that slot into the tube walls.
Critical feature: notches to avoid interference with member tabs at joints.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
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

try:
    from ..profiles import TubeProfile
    from ..joinery import TabGeometry, calc_notch_positions
except ImportError:
    from profiles import TubeProfile
    from joinery import TabGeometry, calc_notch_positions


class CapTabPosition(Enum):
    """Which sides of the cap have tabs."""
    ALL_SIDES = "all_sides"       # Tabs on all 4 sides
    TOP_BOTTOM = "top_bottom"     # Tabs on top/bottom only (for tab/slot joinery)
    LEFT_RIGHT = "left_right"     # Tabs on left/right only
    NONE = "none"                 # No tabs (flat cap)


@dataclass
class CapTabSpec:
    """Specification for a single cap tab."""
    side: str                    # "top", "bottom", "left", "right"
    offset_along_edge: float     # Distance from edge center (mm)
    width: float                 # Tab width (mm)
    depth: float                 # How far tab extends (mm)
    thickness: float             # Tab thickness (mm)


@dataclass
class EndCapSpec:
    """Specification for an end cap."""
    tube_width: float            # Outer tube width (mm)
    tube_height: float           # Outer tube height (mm)
    wall_thickness: float        # Tube wall thickness (mm)
    corner_radius: float         # Inner corner radius (mm)

    # Cap properties
    cap_thickness: float = 3.0   # Thickness of cap plate (mm)
    tab_depth: float = 15.0      # How far tabs extend into tube (mm)
    tab_width: float = 20.0      # Width of each tab (mm)
    tabs_per_side: int = 1       # Number of tabs per side
    tab_position: CapTabPosition = CapTabPosition.TOP_BOTTOM

    # Tolerances
    fit_clearance: float = 0.2   # Gap between cap and tube interior (mm)

    # Notches for member tab clearance
    notches: List[Tuple[float, float, float, float]] = field(default_factory=list)
    # Each notch: (center_x, center_y, width, depth)


@dataclass
class EndCap:
    """
    An end cap for a tube member.

    The cap fits inside the tube end and has tabs that extend
    outward to slot into the tube walls.
    """
    spec: EndCapSpec
    member_id: str = ""
    end: str = "start"  # "start" or "end" of the member
    position: Tuple[float, float, float] = (0, 0, 0)
    normal: Tuple[float, float, float] = (0, 0, 1)  # Direction cap faces
    shape: Optional["Part.Shape"] = None

    def get_name(self) -> str:
        """Generate name for this cap."""
        end_label = "Start" if self.end == "start" else "End"
        if self.member_id:
            return f"Cap_{self.member_id}_{end_label}"
        return f"EndCap_{end_label}"


class EndCapGenerator:
    """
    Generates end caps for tube members.

    Usage:
        gen = EndCapGenerator(profile)
        cap_spec = gen.create_cap_spec(member_tabs)
        shape = gen.create_cap_shape(cap_spec)
    """

    def __init__(
        self,
        profile: TubeProfile,
        cap_thickness: float = 3.0,
        tab_depth_ratio: float = 0.5,
    ):
        """
        Initialize end cap generator.

        Args:
            profile: Tube profile for cap dimensions.
            cap_thickness: Thickness of cap plate (mm).
            tab_depth_ratio: Tab depth as ratio of tube dimension.
        """
        self.profile = profile
        self.cap_thickness = cap_thickness
        self.tab_depth_ratio = tab_depth_ratio

        # Cache geometry
        self.tube_w = profile.geometry.outer_width_mm
        self.tube_h = profile.geometry.outer_height_mm
        self.wall_t = profile.geometry.wall_thickness_mm
        self.corner_r = profile.geometry.inner_corner_radius_mm or 0

    def create_cap_spec(
        self,
        member_tabs: Optional[List[TabGeometry]] = None,
        tab_position: CapTabPosition = CapTabPosition.TOP_BOTTOM,
        tabs_per_side: int = 1,
    ) -> EndCapSpec:
        """
        Create cap specification with notches for member tabs.

        Args:
            member_tabs: Tabs that enter this tube end (need notches).
            tab_position: Which sides get tabs.
            tabs_per_side: Number of tabs per side.

        Returns:
            EndCapSpec with notch positions calculated.
        """
        spec = EndCapSpec(
            tube_width=self.tube_w,
            tube_height=self.tube_h,
            wall_thickness=self.wall_t,
            corner_radius=self.corner_r,
            cap_thickness=self.cap_thickness,
            tab_depth=self.wall_t * self.tab_depth_ratio * 10,  # Into tube wall
            tab_width=min(self.tube_w, self.tube_h) * 0.4,
            tabs_per_side=tabs_per_side,
            tab_position=tab_position,
            fit_clearance=self.profile.tolerances.slot_clearance_mm,
        )

        # Calculate notches for member tabs
        if member_tabs:
            spec.notches = calc_notch_positions(
                member_tabs,
                self.tube_w,
                self.tube_h,
                notch_clearance=1.0,
            )

        return spec

    def create_cap_shape(
        self,
        spec: EndCapSpec,
    ) -> "Part.Shape":
        """
        Create the 3D shape for an end cap.

        The cap consists of:
        1. A base plate that fits inside the tube
        2. Tabs extending outward on specified sides
        3. Notches cut where member tabs would interfere

        Args:
            spec: End cap specification.

        Returns:
            Part.Shape (solid) for the cap.
        """
        if not HAS_FREECAD:
            raise RuntimeError("FreeCAD not available")

        # Inner dimensions (cap base fits inside tube)
        inner_w = spec.tube_width - 2 * spec.wall_thickness - 2 * spec.fit_clearance
        inner_h = spec.tube_height - 2 * spec.wall_thickness - 2 * spec.fit_clearance

        # Create base plate (fits inside tube)
        base = self._create_rounded_box(
            inner_w, inner_h, spec.cap_thickness,
            spec.corner_radius,
        )

        # Add tabs based on position setting
        if spec.tab_position != CapTabPosition.NONE:
            tabs_shape = self._create_tabs(spec, inner_w, inner_h)
            if tabs_shape:
                base = base.fuse(tabs_shape)

        # Cut notches for member tabs
        if spec.notches:
            for notch in spec.notches:
                notch_shape = self._create_notch(spec, notch)
                if notch_shape:
                    base = base.cut(notch_shape)

        return base

    def _create_rounded_box(
        self,
        width: float,
        height: float,
        thickness: float,
        corner_radius: float,
    ) -> "Part.Shape":
        """Create a box with rounded corners in XY plane."""
        r = min(corner_radius, width / 2, height / 2)
        hw = width / 2
        hh = height / 2

        if r > 0.1:
            # Create rounded rectangle profile
            edges = []
            sqrt2_2 = math.sqrt(2) / 2

            # Bottom edge
            edges.append(Part.LineSegment(
                Vector(-hw + r, -hh, 0),
                Vector(hw - r, -hh, 0)
            ))
            # Bottom-right arc
            br_cx, br_cy = hw - r, -hh + r
            edges.append(Part.Arc(
                Vector(hw - r, -hh, 0),
                Vector(br_cx + r * sqrt2_2, br_cy - r * sqrt2_2, 0),
                Vector(hw, -hh + r, 0)
            ))
            # Right edge
            edges.append(Part.LineSegment(
                Vector(hw, -hh + r, 0),
                Vector(hw, hh - r, 0)
            ))
            # Top-right arc
            tr_cx, tr_cy = hw - r, hh - r
            edges.append(Part.Arc(
                Vector(hw, hh - r, 0),
                Vector(tr_cx + r * sqrt2_2, tr_cy + r * sqrt2_2, 0),
                Vector(hw - r, hh, 0)
            ))
            # Top edge
            edges.append(Part.LineSegment(
                Vector(hw - r, hh, 0),
                Vector(-hw + r, hh, 0)
            ))
            # Top-left arc
            tl_cx, tl_cy = -hw + r, hh - r
            edges.append(Part.Arc(
                Vector(-hw + r, hh, 0),
                Vector(tl_cx - r * sqrt2_2, tl_cy + r * sqrt2_2, 0),
                Vector(-hw, hh - r, 0)
            ))
            # Left edge
            edges.append(Part.LineSegment(
                Vector(-hw, hh - r, 0),
                Vector(-hw, -hh + r, 0)
            ))
            # Bottom-left arc
            bl_cx, bl_cy = -hw + r, -hh + r
            edges.append(Part.Arc(
                Vector(-hw, -hh + r, 0),
                Vector(bl_cx - r * sqrt2_2, bl_cy - r * sqrt2_2, 0),
                Vector(-hw + r, -hh, 0)
            ))

            edge_shapes = [e.toShape() for e in edges]
            wire = Part.Wire(edge_shapes)
        else:
            # Simple rectangle
            wire = Part.makePolygon([
                Vector(-hw, -hh, 0),
                Vector(hw, -hh, 0),
                Vector(hw, hh, 0),
                Vector(-hw, hh, 0),
                Vector(-hw, -hh, 0),
            ])

        face = Part.Face(wire)
        return face.extrude(Vector(0, 0, thickness))

    def _create_tabs(
        self,
        spec: EndCapSpec,
        inner_w: float,
        inner_h: float,
    ) -> Optional["Part.Shape"]:
        """Create tabs extending from cap edges."""
        tabs = []

        # Determine which sides get tabs
        do_top_bottom = spec.tab_position in (
            CapTabPosition.ALL_SIDES, CapTabPosition.TOP_BOTTOM
        )
        do_left_right = spec.tab_position in (
            CapTabPosition.ALL_SIDES, CapTabPosition.LEFT_RIGHT
        )

        tab_t = spec.wall_thickness - spec.fit_clearance  # Tab fits in wall slot

        if do_top_bottom:
            # Top tabs (Y+)
            for i in range(spec.tabs_per_side):
                offset = self._calc_tab_offset(i, spec.tabs_per_side, inner_w)
                tab = Part.makeBox(
                    spec.tab_width,
                    spec.tab_depth,
                    tab_t,
                    Vector(offset - spec.tab_width / 2, inner_h / 2, 0),
                )
                tabs.append(tab)

            # Bottom tabs (Y-)
            for i in range(spec.tabs_per_side):
                offset = self._calc_tab_offset(i, spec.tabs_per_side, inner_w)
                tab = Part.makeBox(
                    spec.tab_width,
                    spec.tab_depth,
                    tab_t,
                    Vector(offset - spec.tab_width / 2, -inner_h / 2 - spec.tab_depth, 0),
                )
                tabs.append(tab)

        if do_left_right:
            # Right tabs (X+)
            for i in range(spec.tabs_per_side):
                offset = self._calc_tab_offset(i, spec.tabs_per_side, inner_h)
                tab = Part.makeBox(
                    spec.tab_depth,
                    spec.tab_width,
                    tab_t,
                    Vector(inner_w / 2, offset - spec.tab_width / 2, 0),
                )
                tabs.append(tab)

            # Left tabs (X-)
            for i in range(spec.tabs_per_side):
                offset = self._calc_tab_offset(i, spec.tabs_per_side, inner_h)
                tab = Part.makeBox(
                    spec.tab_depth,
                    spec.tab_width,
                    tab_t,
                    Vector(-inner_w / 2 - spec.tab_depth, offset - spec.tab_width / 2, 0),
                )
                tabs.append(tab)

        if not tabs:
            return None

        # Fuse all tabs together
        result = tabs[0]
        for tab in tabs[1:]:
            result = result.fuse(tab)

        return result

    def _calc_tab_offset(
        self,
        index: int,
        total: int,
        edge_length: float,
    ) -> float:
        """Calculate tab center offset along an edge."""
        if total == 1:
            return 0  # Centered
        # Distribute evenly
        spacing = edge_length / (total + 1)
        return -edge_length / 2 + spacing * (index + 1)

    def _create_notch(
        self,
        spec: EndCapSpec,
        notch: Tuple[float, float, float, float],
    ) -> Optional["Part.Shape"]:
        """Create a notch cutout for member tab clearance."""
        cx, cy, width, depth = notch

        # Notch is a box that cuts through the cap and into tab area
        # Make it tall enough to cut through everything
        notch_height = spec.cap_thickness + spec.tab_depth + 10

        return Part.makeBox(
            width,
            depth,
            notch_height,
            Vector(cx - width / 2, cy - depth / 2, -5),
        )


def generate_end_caps_for_frame(
    frame_members: List,
    profile: TubeProfile,
    joints: List,
) -> Dict[str, EndCap]:
    """
    Generate end caps for all open tube ends in a frame.

    Args:
        frame_members: List of FrameMember objects.
        profile: Tube profile.
        joints: List of Joint objects.

    Returns:
        Dictionary mapping member_id + end to EndCap objects.
    """
    generator = EndCapGenerator(profile)
    caps = {}

    # Find which ends have joints (don't need caps there usually)
    jointed_ends = set()
    for joint in joints:
        # Track which member ends are involved in joints
        jointed_ends.add((joint.member_a.member_id, "end"))
        jointed_ends.add((joint.member_b.member_id, "start"))

    # Generate caps for open ends
    for member in frame_members:
        member_id = member.get_name() if hasattr(member, 'get_name') else str(member)

        # Check start end
        if (member_id, "start") not in jointed_ends:
            spec = generator.create_cap_spec()
            caps[f"{member_id}_start"] = EndCap(
                spec=spec,
                member_id=member_id,
                end="start",
            )

        # Check end end
        if (member_id, "end") not in jointed_ends:
            spec = generator.create_cap_spec()
            caps[f"{member_id}_end"] = EndCap(
                spec=spec,
                member_id=member_id,
                end="end",
            )

    return caps
