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
        tab_depth_mm: float = 10.0,
        relief_type: CornerReliefType = CornerReliefType.RADIUS,
    ):
        """
        Initialize generator with profile and settings.

        Args:
            profile: Tube profile with tolerance values.
            tab_depth_mm: Fixed tab depth in mm (default 10mm).
            relief_type: Type of corner relief for slots.
        """
        self.profile = profile
        self.tab_depth_mm = tab_depth_mm
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

        Tabs are placed on FLAT faces (top/bottom) of tubes, NOT on curved sides.
        For square tubes, this means the faces perpendicular to the "up" direction.

        Args:
            joint: Joint where tab will be placed.
            face: Which face of the tube to place tab on.

        Returns:
            TabGeometry defining the tab.
        """
        # Tab extends from the "tab member" toward the "slot member"
        tab_member = joint.member_b
        slot_member = joint.member_a

        # Use fixed tab depth from generator settings
        tab_depth = self.tab_depth_mm

        # Tab position at end of tab member
        if joint.param_b > 0.5:
            base_pos = tab_member.end
        else:
            base_pos = tab_member.start

        tab_dir = tab_member.direction
        slot_dir = slot_member.direction

        # Determine the direction the tab extends (toward receiving member)
        # This should be perpendicular to both the tab member axis and the tab face normal
        # For proper joinery, tabs extend from the member END toward the receiving member

        # Calculate direction from tab base toward the slot member's centerline
        slot_center = slot_member.point_at_param(joint.param_a)
        dx = slot_center[0] - base_pos[0]
        dy = slot_center[1] - base_pos[1]
        dz = slot_center[2] - base_pos[2]
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)

        if dist > 1e-6:
            extend_dir = (dx/dist, dy/dist, dz/dist)
        else:
            extend_dir = slot_dir

        # CRITICAL: Tab faces should be on FLAT faces (top/bottom), not curved sides
        # For a tube, "flat" faces are perpendicular to the secondary axis:
        # - Vertical tube (along Z): flat faces are perpendicular to Y (front/back)
        # - Horizontal tube along X: flat faces are perpendicular to Z (top/bottom)
        # - Horizontal tube along Y: flat faces are perpendicular to Z (top/bottom)

        # Determine tab face normal (perpendicular to tube axis AND extend direction)
        # This ensures tab is on a flat face
        if abs(tab_dir[2]) > 0.9:  # Vertical member (along Z)
            # Tab extends horizontally, tab face normal should be horizontal too
            # Use the perpendicular to extend_dir in XY plane
            if abs(extend_dir[0]) > abs(extend_dir[1]):
                # Extending mainly in X, tab face normal in Y
                face_normal = (0, 1, 0) if face == TabPosition.TOP else (0, -1, 0)
            else:
                # Extending mainly in Y, tab face normal in X
                face_normal = (1, 0, 0) if face == TabPosition.TOP else (-1, 0, 0)
        else:
            # Horizontal member - tab face normal should be in Z (top/bottom)
            face_normal = (0, 0, 1) if face == TabPosition.TOP else (0, 0, -1)

        # Tab position: offset from tube centerline to the face
        # The offset moves the tab to the outer surface of the tube wall
        face_offset = self.tube_height / 2 - self.wall_thickness / 2

        position = (
            base_pos[0] + face_normal[0] * face_offset,
            base_pos[1] + face_normal[1] * face_offset,
            base_pos[2] + face_normal[2] * face_offset,
        )

        return TabGeometry(
            width=self.tab_width,
            depth=tab_depth,
            thickness=self.wall_thickness,
            position=position,
            direction=extend_dir,
            normal=face_normal,
            corner_radius=self.relief_radius if self.relief_type == CornerReliefType.RADIUS else 0,
        )

    def calc_slot_geometry(
        self,
        joint: Joint,
        face: TabPosition = TabPosition.TOP,
    ) -> SlotGeometry:
        """
        Calculate slot geometry for a joint.

        Slots are cut into FLAT faces (top/bottom) of the receiving tube.
        The slot receives the tab from the joining member.

        Args:
            joint: Joint where slot will be cut.
            face: Which face of the tube to cut slot in.

        Returns:
            SlotGeometry defining the slot cut.
        """
        slot_member = joint.member_a
        tab_member = joint.member_b

        # Slot depth - goes through tube wall plus extra for clean cut
        slot_depth = self.wall_thickness * 2.0

        # Slot length matches tab depth plus relief for clearance
        slot_length = self.tab_depth_mm + self.relief_radius * 2

        # Slot position: on the slot member at the intersection point
        position = slot_member.point_at_param(joint.param_a)

        member_dir = slot_member.direction

        # Determine where the tab is coming FROM to know which face to cut
        # The slot should be on the face that the tab member approaches
        tab_base = tab_member.end if joint.param_b > 0.5 else tab_member.start
        approach_dx = position[0] - tab_base[0]
        approach_dy = position[1] - tab_base[1]
        approach_dz = position[2] - tab_base[2]

        # SLOT FACE LOGIC:
        # The slot is cut on the face of the receiving member that faces the tab member
        # For FLAT faces only (top/bottom):
        # - Horizontal member along X: top/bottom faces are Z faces
        # - Horizontal member along Y: top/bottom faces are Z faces
        # - Vertical member along Z: "top/bottom" are Y faces (front/back)

        if abs(member_dir[2]) > 0.9:  # Vertical slot member
            # Slot is on Y face (front or back)
            if approach_dy > 0:
                slot_into = (0, 1, 0)   # Tab coming from front, slot on front face
            else:
                slot_into = (0, -1, 0)  # Tab coming from back, slot on back face
            # Slot extends along X
            along = (1, 0, 0)

        elif abs(member_dir[0]) > 0.9:  # Horizontal along X
            # Slot is on Z face (top or bottom)
            if approach_dz > 0:
                slot_into = (0, 0, 1)   # Tab coming from above, slot on top
            else:
                slot_into = (0, 0, -1)  # Tab coming from below, slot on bottom
            # Slot extends along Y
            along = (0, 1, 0)

        else:  # Horizontal along Y (depth rails)
            # Slot is on Z face (top or bottom)
            if approach_dz > 0:
                slot_into = (0, 0, 1)
            else:
                slot_into = (0, 0, -1)
            # Slot extends along X
            along = (1, 0, 0)

        # Offset position to the face surface
        face_offset = self.tube_height / 2
        slot_position = (
            position[0] + slot_into[0] * face_offset,
            position[1] + slot_into[1] * face_offset,
            position[2] + slot_into[2] * face_offset,
        )

        return SlotGeometry(
            width=self.slot_width,
            depth=slot_depth,
            length=slot_length,
            position=slot_position,
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
