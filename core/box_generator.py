"""
Box Generator - Generate parametric tube steel cabinet frames.

Creates frame members based on BoxSpecs spreadsheet and tube profile.
Phase 1: Basic corners + rails (no tabs yet).
"""

from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

# FreeCAD imports
try:
    import FreeCAD as App
    import Part
    from FreeCAD import Vector, Placement, Rotation
    HAS_FREECAD = True
except ImportError:
    HAS_FREECAD = False
    App = None
    Part = None
    Vector = None
    Placement = None
    Rotation = None

from .box_specs import BoxSpecsData, DimensionReference

# Handle both relative and absolute imports
try:
    from ..profiles import TubeProfile, get_profile, create_tube_solid
except ImportError:
    from profiles import TubeProfile, get_profile, create_tube_solid


class MemberType(Enum):
    """Types of frame members."""
    CORNER_VERTICAL = "corner_vertical"
    VERTICAL_SUPPORT = "vertical_support"
    HORIZONTAL_RAIL_TOP = "horizontal_rail_top"
    HORIZONTAL_RAIL_BOTTOM = "horizontal_rail_bottom"
    DEPTH_RAIL = "depth_rail"
    CROSS_MEMBER_TOP = "cross_member_top"
    CROSS_MEMBER_BOTTOM = "cross_member_bottom"
    FOOT = "foot"


class MemberFace(Enum):
    """Which face of the box a member is on."""
    FRONT = "front"
    BACK = "back"
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"


@dataclass
class FrameMember:
    """
    Definition of a single frame member.

    Stores position, orientation, and metadata before creating geometry.
    """
    member_type: MemberType
    face: Optional[MemberFace]
    position: Tuple[float, float, float]  # Start position (x, y, z) in mm
    length_mm: float
    rotation: Tuple[float, float, float] = (0, 0, 0)  # Euler angles (deg)
    name: str = ""
    index: int = 0  # For numbering duplicates

    def get_name(self) -> str:
        """Generate a descriptive name for this member."""
        if self.name:
            return self.name
        parts = [self.member_type.value.replace("_", " ").title()]
        if self.face:
            parts.append(self.face.value.title())
        if self.index > 0:
            parts.append(str(self.index))
        return "_".join(parts).replace(" ", "_")


class BoxFrameGenerator:
    """
    Generates frame members for a box cabinet.

    Usage:
        gen = BoxFrameGenerator(specs, profile)
        members = gen.generate_members()
        parts = gen.create_parts(doc)
    """

    def __init__(
        self,
        specs: BoxSpecsData,
        profile: TubeProfile,
    ):
        """
        Initialize the generator.

        Args:
            specs: Box specifications.
            profile: Tube profile to use for all members.
        """
        self.specs = specs
        self.profile = profile

        # Cache tube dimensions
        self.tube_w = profile.geometry.outer_width_mm
        self.tube_h = profile.geometry.outer_height_mm

        # Calculate effective dimensions based on reference mode
        self._calc_effective_dims()

    def _calc_effective_dims(self):
        """Calculate effective interior dimensions based on reference mode."""
        s = self.specs
        tw = self.tube_w

        if s.dimension_reference == DimensionReference.EXTERIOR:
            # Dimensions are exterior - interior is smaller
            self.eff_length = s.length_mm
            self.eff_height = s.height_mm
            self.eff_depth = s.depth_mm
        elif s.dimension_reference == DimensionReference.INTERIOR:
            # Dimensions are interior - add tube widths for exterior
            self.eff_length = s.length_mm + 2 * tw
            self.eff_height = s.height_mm + 2 * tw
            self.eff_depth = s.depth_mm + 2 * tw
        else:  # CENTERLINE
            # Dimensions are centerline - add tube widths
            self.eff_length = s.length_mm + tw
            self.eff_height = s.height_mm + tw
            self.eff_depth = s.depth_mm + tw

    def generate_members(self) -> List[FrameMember]:
        """
        Generate all frame member definitions.

        Returns:
            List of FrameMember objects defining the frame.
        """
        members = []

        # Corner verticals (4)
        members.extend(self._gen_corner_verticals())

        # Horizontal rails - top and bottom (8 total)
        members.extend(self._gen_horizontal_rails())

        # Depth rails (4)
        members.extend(self._gen_depth_rails())

        # Vertical supports front/back
        members.extend(self._gen_vertical_supports())

        # Cross members top/bottom
        members.extend(self._gen_cross_members())

        # Feet if specified
        if self.specs.foot_height_mm > 0:
            members.extend(self._gen_feet())

        return members

    def _gen_corner_verticals(self) -> List[FrameMember]:
        """Generate 4 corner vertical members."""
        members = []
        tw = self.tube_w
        half = tw / 2  # Offset for centered profile
        h = self.eff_height
        l = self.eff_length
        d = self.eff_depth

        # Vertical length is height minus top/bottom rail thicknesses
        vert_len = h - 2 * tw

        # Corners: (face1, face2, x_offset, y_offset)
        # Position offset by half tube width since profile is centered
        corners = [
            (MemberFace.FRONT, MemberFace.LEFT, half, half),           # Front-left
            (MemberFace.FRONT, MemberFace.RIGHT, l - half, half),      # Front-right
            (MemberFace.BACK, MemberFace.LEFT, half, d - half),        # Back-left
            (MemberFace.BACK, MemberFace.RIGHT, l - half, d - half),   # Back-right
        ]

        for i, (face1, face2, x, y) in enumerate(corners):
            members.append(FrameMember(
                member_type=MemberType.CORNER_VERTICAL,
                face=face1,
                position=(x, y, tw),  # Start above bottom rail
                length_mm=vert_len,
                rotation=(0, 0, 0),  # Vertical = no rotation
                index=i + 1,
            ))

        return members

    def _gen_horizontal_rails(self) -> List[FrameMember]:
        """Generate horizontal rails (top/bottom, front/back)."""
        members = []
        tw = self.tube_w
        half = tw / 2  # Offset for centered profile
        l = self.eff_length
        d = self.eff_depth
        h = self.eff_height

        # Rail length (front/back) - full length
        rail_len = l

        # After rotation (0, 90, 0), profile is in Y-Z plane
        # Rails at Z=half (bottom, occupies 0 to tw) and Z=h-half (top, occupies h-tw to h)
        # Front: Y=half (occupies 0 to tw), Back: Y=d-half (occupies d-tw to d)
        positions = [
            # (face, z_center, y_center)
            (MemberFace.FRONT, half, half),           # Bottom front
            (MemberFace.FRONT, h - half, half),       # Top front
            (MemberFace.BACK, half, d - half),        # Bottom back
            (MemberFace.BACK, h - half, d - half),    # Top back
        ]

        for i, (face, z, y) in enumerate(positions):
            mtype = MemberType.HORIZONTAL_RAIL_TOP if z > half else MemberType.HORIZONTAL_RAIL_BOTTOM
            members.append(FrameMember(
                member_type=mtype,
                face=face,
                position=(0, y, z),
                length_mm=rail_len,
                rotation=(0, 90, 0),  # Rotate to lie along X axis
                index=i + 1,
            ))

        return members

    def _gen_depth_rails(self) -> List[FrameMember]:
        """Generate depth rails connecting front to back."""
        members = []
        tw = self.tube_w
        half = tw / 2  # Offset for centered profile
        l = self.eff_length
        d = self.eff_depth
        h = self.eff_height

        # Depth rail length - goes from front to back inside corners
        depth_len = d - 2 * tw

        # After rotation (90, 0, 0), profile is in X-Z plane
        # Need to offset x and z by half to align with corners
        corners = [
            # (face, x_center, z_center)
            (MemberFace.LEFT, half, half),           # Bottom left
            (MemberFace.LEFT, half, h - half),       # Top left
            (MemberFace.RIGHT, l - half, half),      # Bottom right
            (MemberFace.RIGHT, l - half, h - half),  # Top right
        ]

        for i, (face, x, z) in enumerate(corners):
            members.append(FrameMember(
                member_type=MemberType.DEPTH_RAIL,
                face=face,
                position=(x, tw, z),  # Start after front corner (Y=tw is correct start)
                length_mm=depth_len,
                rotation=(-90, 0, 0),  # Rotate to lie along +Y axis (negative rotation)
                index=i + 1,
            ))

        return members

    def _gen_vertical_supports(self) -> List[FrameMember]:
        """Generate vertical support members based on OC spacing."""
        members = []
        tw = self.tube_w
        half = tw / 2  # Offset for centered profile
        l = self.eff_length
        d = self.eff_depth
        h = self.eff_height

        vert_len = h - 2 * tw

        # Front supports - centered along the front face
        n_front = self.specs.calc_vertical_count_front(tw)
        if n_front > 0 and self.specs.vertical_oc_front_mm > 0:
            spacing = (l - tw) / (n_front + 1)
            for i in range(n_front):
                x = spacing * (i + 1)
                members.append(FrameMember(
                    member_type=MemberType.VERTICAL_SUPPORT,
                    face=MemberFace.FRONT,
                    position=(x, half, tw),  # Offset Y by half for centering
                    length_mm=vert_len,
                    rotation=(0, 0, 0),
                    index=i + 1,
                ))

        # Back supports
        n_back = self.specs.calc_vertical_count_back(tw)
        if n_back > 0 and self.specs.vertical_oc_back_mm > 0:
            spacing = (l - tw) / (n_back + 1)
            for i in range(n_back):
                x = spacing * (i + 1)
                members.append(FrameMember(
                    member_type=MemberType.VERTICAL_SUPPORT,
                    face=MemberFace.BACK,
                    position=(x, d - half, tw),  # Offset Y by half for centering
                    length_mm=vert_len,
                    rotation=(0, 0, 0),
                    index=i + 1,
                ))

        return members

    def _gen_cross_members(self) -> List[FrameMember]:
        """Generate horizontal cross members (top/bottom)."""
        members = []
        tw = self.tube_w
        half = tw / 2  # Offset for centered profile
        l = self.eff_length
        d = self.eff_depth
        h = self.eff_height

        cross_len = d - 2 * tw

        # After rotation (90, 0, 0), profile is in X-Z plane
        # Top cross members
        n_top = self.specs.calc_horizontal_count_top(tw)
        if n_top > 0 and self.specs.horizontal_oc_top_mm > 0:
            spacing = (l - tw) / (n_top + 1)
            for i in range(n_top):
                x = spacing * (i + 1)
                members.append(FrameMember(
                    member_type=MemberType.CROSS_MEMBER_TOP,
                    face=MemberFace.TOP,
                    position=(x, tw, h - half),  # Offset Z by half
                    length_mm=cross_len,
                    rotation=(-90, 0, 0),  # Rotate to lie along +Y axis
                    index=i + 1,
                ))

        # Bottom cross members
        n_bottom = self.specs.calc_horizontal_count_bottom(tw)
        if n_bottom > 0 and self.specs.horizontal_oc_bottom_mm > 0:
            spacing = (l - tw) / (n_bottom + 1)
            for i in range(n_bottom):
                x = spacing * (i + 1)
                members.append(FrameMember(
                    member_type=MemberType.CROSS_MEMBER_BOTTOM,
                    face=MemberFace.BOTTOM,
                    position=(x, tw, half),  # Offset Z by half
                    length_mm=cross_len,
                    rotation=(-90, 0, 0),  # Rotate to lie along +Y axis
                    index=i + 1,
                ))

        return members

    def _gen_feet(self) -> List[FrameMember]:
        """Generate foot members at corners."""
        members = []
        tw = self.tube_w
        half = tw / 2  # Offset for centered profile
        l = self.eff_length
        d = self.eff_depth
        foot_h = self.specs.foot_height_mm

        # Feet align with corner verticals (same X, Y positions)
        corners = [
            (half, half),               # Front-left
            (l - half, half),           # Front-right
            (half, d - half),           # Back-left
            (l - half, d - half),       # Back-right
        ]

        for i, (x, y) in enumerate(corners):
            members.append(FrameMember(
                member_type=MemberType.FOOT,
                face=MemberFace.BOTTOM,
                position=(x, y, -foot_h),  # Below the frame (extrudes up to Z=0)
                length_mm=foot_h,
                rotation=(0, 0, 0),
                index=i + 1,
            ))

        return members

    def create_parts(
        self,
        doc: "App.Document",
        group_name: str = "Frame"
    ) -> List["App.DocumentObject"]:
        """
        Create FreeCAD Part objects for all frame members.

        Args:
            doc: FreeCAD document.
            group_name: Name for the group containing parts.

        Returns:
            List of created Part::Feature objects.
        """
        if not HAS_FREECAD:
            raise RuntimeError("FreeCAD not available")

        # Create group for organization
        group = doc.addObject("App::DocumentObjectGroup", group_name)

        members = self.generate_members()
        parts = []

        for member in members:
            # Create tube solid
            shape = create_tube_solid(self.profile, member.length_mm)

            # Apply rotation
            rx, ry, rz = member.rotation
            if rx != 0 or ry != 0 or rz != 0:
                shape.rotate(Vector(0, 0, 0), Vector(1, 0, 0), rx)
                shape.rotate(Vector(0, 0, 0), Vector(0, 1, 0), ry)
                shape.rotate(Vector(0, 0, 0), Vector(0, 0, 1), rz)

            # Apply translation
            px, py, pz = member.position
            shape.translate(Vector(px, py, pz))

            # Create Part::Feature
            name = member.get_name()
            part = doc.addObject("Part::Feature", name)
            part.Shape = shape

            # Add to group
            group.addObject(part)
            parts.append(part)

        doc.recompute()
        return parts


def create_box_frame(
    doc: "App.Document",
    specs: Optional[BoxSpecsData] = None,
    profile_name: str = "2x2x0.125_A36",
) -> List["App.DocumentObject"]:
    """
    Convenience function to create a complete box frame.

    Args:
        doc: FreeCAD document.
        specs: Box specifications (uses defaults if None).
        profile_name: Name of tube profile to use.

    Returns:
        List of created Part::Feature objects.
    """
    if specs is None:
        specs = BoxSpecsData()

    profile = get_profile(profile_name)
    if profile is None:
        raise ValueError(f"Profile not found: {profile_name}")

    generator = BoxFrameGenerator(specs, profile)
    return generator.create_parts(doc)
