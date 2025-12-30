"""
Tab/Slot Generator - Create tab and slot geometry for tube joints.

Generates the 3D shapes needed for tab/slot joinery:
- Tabs: Protrusions from tube ends/faces
- Slots: Cuts into tubes to receive tabs
- Corner relief: Dogbone or radius corners for manufacturability
"""

from dataclasses import dataclass
from enum import Enum
from typing import Tuple, Optional, List
import math

# FreeCAD imports
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

# Local imports
try:
    from ..profiles import TubeProfile
except ImportError:
    from profiles import TubeProfile

from .joint_detector import Joint, JointType, TabPosition


class CornerReliefType(Enum):
    """Types of corner relief for slots."""
    NONE = "none"           # Square corners (not recommended)
    DOGBONE = "dogbone"     # Circular cutouts at corners
    RADIUS = "radius"       # Rounded corners (requires rounded tab corners)
    TBONE = "tbone"         # T-shaped relief


@dataclass
class TabGeometry:
    """
    Defines the geometry of a single tab.

    All dimensions in mm.
    """
    width: float            # Tab width (perpendicular to insertion)
    depth: float            # How far tab extends into slot
    thickness: float        # Tab thickness (wall thickness adjusted)
    position: Tuple[float, float, float]  # Center of tab base
    direction: Tuple[float, float, float]  # Direction tab extends (unit vector)
    normal: Tuple[float, float, float]     # Normal to tab face (thickness direction)

    # Corner treatment
    corner_radius: float = 0.0  # Radius on tab corners (for RADIUS relief)


@dataclass
class SlotGeometry:
    """
    Defines the geometry of a slot cut.

    All dimensions in mm.
    """
    width: float            # Slot width (includes clearance)
    depth: float            # Slot depth into tube
    length: float           # Slot length (along tube face)
    position: Tuple[float, float, float]  # Center of slot opening
    direction: Tuple[float, float, float]  # Direction slot goes into tube
    along: Tuple[float, float, float]      # Direction along slot length

    # Corner relief
    relief_type: CornerReliefType = CornerReliefType.RADIUS
    relief_radius: float = 1.5  # Radius for relief (dogbone circle or corner radius)


class TabSlotGenerator:
    """
    Generates tab and slot geometry for joints.

    Uses profile tolerances to calculate proper dimensions.
    """

    def __init__(
        self,
        profile: TubeProfile,
        tab_depth_ratio: float = 0.6,
        relief_type: CornerReliefType = CornerReliefType.RADIUS,
    ):
        """
        Initialize generator with profile and settings.

        Args:
            profile: Tube profile with tolerance values.
            tab_depth_ratio: Tab depth as fraction of mating member depth (0.5-0.75).
            relief_type: Type of corner relief for slots.
        """
        self.profile = profile
        self.tab_depth_ratio = tab_depth_ratio
        self.relief_type = relief_type

        # Cache computed dimensions
        self.wall_thickness = profile.geometry.wall_thickness_mm
        self.tube_width = profile.geometry.outer_width_mm
        self.tube_height = profile.geometry.outer_height_mm

        # Tab/slot dimensions from tolerances
        self.tab_width = profile.calc_tab_width()
        self.slot_width = profile.calc_slot_width()
        self.relief_radius = profile.tolerances.corner_relief_radius_mm

    def calc_tab_geometry(
        self,
        joint: Joint,
        face: TabPosition = TabPosition.TOP,
    ) -> TabGeometry:
        """
        Calculate tab geometry for a joint.

        Args:
            joint: Joint where tab will be placed.
            face: Which face of the tube to place tab on.

        Returns:
            TabGeometry defining the tab.
        """
        # Tab extends from the "tab member" toward the "slot member"
        tab_member = joint.member_b
        slot_member = joint.member_a

        # Tab depth based on mating member depth
        mating_depth = slot_member.width  # Tube width of receiving member
        tab_depth = mating_depth * self.tab_depth_ratio

        # Tab position at end of tab member
        if joint.param_b > 0.5:
            # Tab at end of member
            base_pos = tab_member.end
        else:
            # Tab at start of member
            base_pos = tab_member.start

        # Direction from tab member toward slot member
        # This is perpendicular to the tab member axis
        tab_dir = tab_member.direction
        slot_dir = slot_member.direction

        # Tab extends perpendicular to its own member, toward the slot
        # Calculate the direction from tab base to slot centerline
        dx = joint.intersection_point[0] - base_pos[0]
        dy = joint.intersection_point[1] - base_pos[1]
        dz = joint.intersection_point[2] - base_pos[2]
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)

        if dist > 1e-6:
            extend_dir = (dx/dist, dy/dist, dz/dist)
        else:
            # Default to slot member direction if at same point
            extend_dir = slot_dir

        # Tab normal is along tab member axis
        normal = tab_dir

        # Adjust position based on face
        # Tab center offset from tube centerline
        offset = self.tube_width / 2 - self.wall_thickness / 2

        if face == TabPosition.TOP:
            # Offset in +Z (or +Y for horizontal members)
            if abs(tab_dir[2]) > 0.9:  # Vertical member
                pos_offset = (0, offset, 0)
            else:
                pos_offset = (0, 0, offset)
        elif face == TabPosition.BOTTOM:
            if abs(tab_dir[2]) > 0.9:
                pos_offset = (0, -offset, 0)
            else:
                pos_offset = (0, 0, -offset)
        else:
            pos_offset = (0, 0, 0)

        position = (
            base_pos[0] + pos_offset[0],
            base_pos[1] + pos_offset[1],
            base_pos[2] + pos_offset[2],
        )

        return TabGeometry(
            width=self.tab_width,
            depth=tab_depth,
            thickness=self.wall_thickness,
            position=position,
            direction=extend_dir,
            normal=normal,
            corner_radius=self.relief_radius if self.relief_type == CornerReliefType.RADIUS else 0,
        )

    def calc_slot_geometry(
        self,
        joint: Joint,
        face: TabPosition = TabPosition.TOP,
    ) -> SlotGeometry:
        """
        Calculate slot geometry for a joint.

        Args:
            joint: Joint where slot will be cut.
            face: Which face of the tube to cut slot in.

        Returns:
            SlotGeometry defining the slot cut.
        """
        slot_member = joint.member_a
        tab_member = joint.member_b

        # Slot depth - goes through tube wall
        slot_depth = self.wall_thickness * 1.5  # Extra depth for clean cut

        # Slot length matches tab depth
        mating_depth = tab_member.width
        slot_length = mating_depth * self.tab_depth_ratio + self.relief_radius * 2

        # Slot position on slot member at intersection
        position = slot_member.point_at_param(joint.param_a)

        # Slot direction goes into the tube (perpendicular to surface)
        slot_dir = slot_member.direction

        # Slot "along" direction - perpendicular to slot_dir and member axis
        # This is the direction the slot extends along the tube face
        member_dir = slot_member.direction

        # For a tube along X, slots on top face extend into -Z, along Y
        # For a tube along Y, slots on top face extend into -Z, along X
        # For a tube along Z, slots on top face extend into -Y, along X

        if abs(member_dir[2]) > 0.9:  # Vertical
            slot_into = (0, -1, 0) if face == TabPosition.TOP else (0, 1, 0)
            along = (1, 0, 0)
        elif abs(member_dir[0]) > 0.9:  # Along X
            slot_into = (0, 0, -1) if face == TabPosition.TOP else (0, 0, 1)
            along = (0, 1, 0)
        else:  # Along Y
            slot_into = (0, 0, -1) if face == TabPosition.TOP else (0, 0, 1)
            along = (1, 0, 0)

        return SlotGeometry(
            width=self.slot_width,
            depth=slot_depth,
            length=slot_length,
            position=position,
            direction=slot_into,
            along=along,
            relief_type=self.relief_type,
            relief_radius=self.relief_radius,
        )

    def create_tab_shape(self, tab: TabGeometry) -> "Part.Shape":
        """
        Create a FreeCAD Part.Shape for a tab.

        Args:
            tab: TabGeometry defining the tab.

        Returns:
            Part.Shape (solid box or rounded box for the tab)
        """
        if not HAS_FREECAD:
            raise RuntimeError("FreeCAD not available")

        # Create base box
        # Tab dimensions: width x thickness x depth
        half_w = tab.width / 2
        half_t = tab.thickness / 2

        if tab.corner_radius > 0:
            # Create rounded rectangle profile
            r = min(tab.corner_radius, half_w, half_t)
            # Use a simple box for now, rounding can be added later
            box = Part.makeBox(
                tab.width,
                tab.thickness,
                tab.depth,
                Vector(-half_w, -half_t, 0),
            )
        else:
            box = Part.makeBox(
                tab.width,
                tab.thickness,
                tab.depth,
                Vector(-half_w, -half_t, 0),
            )

        # Orient and position the tab
        # Default box is at origin extending in +Z
        # Need to rotate so +Z aligns with tab.direction

        # Calculate rotation to align Z with direction
        z_axis = Vector(0, 0, 1)
        target = Vector(*tab.direction)

        if target.Length > 1e-6:
            rotation_axis = z_axis.cross(target)
            if rotation_axis.Length > 1e-6:
                angle = math.degrees(math.acos(max(-1, min(1, z_axis.dot(target)))))
                box.rotate(Vector(0, 0, 0), rotation_axis, angle)
            elif z_axis.dot(target) < 0:
                # Opposite direction - rotate 180° around X
                box.rotate(Vector(0, 0, 0), Vector(1, 0, 0), 180)

        # Translate to position
        box.translate(Vector(*tab.position))

        return box

    def create_slot_shape(self, slot: SlotGeometry) -> "Part.Shape":
        """
        Create a FreeCAD Part.Shape for a slot cut (including corner relief).

        Args:
            slot: SlotGeometry defining the slot.

        Returns:
            Part.Shape (solid to be subtracted from tube)
        """
        if not HAS_FREECAD:
            raise RuntimeError("FreeCAD not available")

        half_w = slot.width / 2
        half_l = slot.length / 2

        # Main slot box
        main_box = Part.makeBox(
            slot.width,
            slot.length,
            slot.depth * 2,  # Extra depth to ensure clean cut
            Vector(-half_w, -half_l, -slot.depth),
        )

        # Add corner relief
        if slot.relief_type == CornerReliefType.DOGBONE and slot.relief_radius > 0:
            # Dogbone: Add cylinders at corners
            r = slot.relief_radius
            corners = [
                (-half_w, -half_l),
                (-half_w, half_l),
                (half_w, -half_l),
                (half_w, half_l),
            ]

            for cx, cy in corners:
                cyl = Part.makeCylinder(
                    r,
                    slot.depth * 2,
                    Vector(cx, cy, -slot.depth),
                    Vector(0, 0, 1),
                )
                main_box = main_box.fuse(cyl)

        elif slot.relief_type == CornerReliefType.RADIUS and slot.relief_radius > 0:
            # Radius corners - the box edges are already there
            # For proper radius, we'd create a rounded rectangle profile
            # For now, use the box as-is (laser will naturally radius)
            pass

        # Orient slot: default is Z-up, need to align with slot.direction
        z_axis = Vector(0, 0, 1)
        target = Vector(*slot.direction)

        if target.Length > 1e-6:
            rotation_axis = z_axis.cross(target)
            if rotation_axis.Length > 1e-6:
                angle = math.degrees(math.acos(max(-1, min(1, z_axis.dot(target)))))
                main_box.rotate(Vector(0, 0, 0), rotation_axis, angle)
            elif z_axis.dot(target) < 0:
                main_box.rotate(Vector(0, 0, 0), Vector(1, 0, 0), 180)

        # Translate to position
        main_box.translate(Vector(*slot.position))

        return main_box

    def generate_joint_features(
        self,
        joint: Joint,
    ) -> Tuple[Optional[TabGeometry], Optional[SlotGeometry]]:
        """
        Generate tab and slot geometry for a joint.

        Args:
            joint: Joint to generate features for.

        Returns:
            Tuple of (TabGeometry, SlotGeometry) or (None, None) if not applicable.
        """
        if joint.joint_type == JointType.INLINE:
            # No tab/slot for inline joints
            return (None, None)

        # Generate both tab and slot
        tab = self.calc_tab_geometry(joint, joint.tab_face)
        slot = self.calc_slot_geometry(joint, joint.slot_face)

        return (tab, slot)


def apply_slots_to_member(
    member_shape: "Part.Shape",
    slots: List[SlotGeometry],
    generator: TabSlotGenerator,
) -> "Part.Shape":
    """
    Apply multiple slot cuts to a member shape.

    Args:
        member_shape: Original tube shape.
        slots: List of slots to cut.
        generator: Generator to create slot shapes.

    Returns:
        Modified shape with slots cut.
    """
    if not HAS_FREECAD:
        raise RuntimeError("FreeCAD not available")

    result = member_shape

    for slot in slots:
        slot_shape = generator.create_slot_shape(slot)
        result = result.cut(slot_shape)

    return result


def apply_tabs_to_member(
    member_shape: "Part.Shape",
    tabs: List[TabGeometry],
    generator: TabSlotGenerator,
) -> "Part.Shape":
    """
    Add tabs to a member shape.

    Args:
        member_shape: Original tube shape.
        tabs: List of tabs to add.
        generator: Generator to create tab shapes.

    Returns:
        Modified shape with tabs added.
    """
    if not HAS_FREECAD:
        raise RuntimeError("FreeCAD not available")

    result = member_shape

    for tab in tabs:
        tab_shape = generator.create_tab_shape(tab)
        result = result.fuse(tab_shape)

    return result
