"""
Jointed Box Generator - Complete box frame with tab/slot joints.

Combines the frame generator with the joinery system to produce
ready-to-manufacture parts with self-fixturing joints.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

try:
    import FreeCAD as App
    import Part
    from FreeCAD import Vector
    HAS_FREECAD = True
except ImportError:
    HAS_FREECAD = False
    App = None
    Part = None

from .box_specs import BoxSpecsData
from .box_generator import BoxFrameGenerator, FrameMember, MemberType

try:
    from ..profiles import TubeProfile, get_profile, create_tube_solid
    from ..joinery import (
        Joint,
        JointType,
        MemberAxis,
        TabSlotGenerator,
        TabGeometry,
        SlotGeometry,
        CornerReliefType,
        InterferenceChecker,
        detect_all_joints,
        members_from_frame_members,
        apply_slots_to_member,
        apply_tabs_to_member,
    )
except ImportError:
    from profiles import TubeProfile, get_profile, create_tube_solid
    from joinery import (
        Joint,
        JointType,
        MemberAxis,
        TabSlotGenerator,
        TabGeometry,
        SlotGeometry,
        CornerReliefType,
        InterferenceChecker,
        detect_all_joints,
        members_from_frame_members,
        apply_slots_to_member,
        apply_tabs_to_member,
    )


@dataclass
class JointedMember:
    """
    A frame member with its associated joints, tabs, and slots.
    """
    member: FrameMember
    axis: MemberAxis
    joints: List[Joint] = field(default_factory=list)
    tabs: List[TabGeometry] = field(default_factory=list)
    slots: List[SlotGeometry] = field(default_factory=list)
    shape: Optional["Part.Shape"] = None


class JointedBoxGenerator:
    """
    Generates complete box frames with tab/slot joinery.

    This is the main entry point for creating manufacturable cabinet frames.

    Usage:
        gen = JointedBoxGenerator(specs, profile)
        gen.generate()
        parts = gen.create_parts(doc)
    """

    def __init__(
        self,
        specs: BoxSpecsData,
        profile: TubeProfile,
        relief_type: CornerReliefType = CornerReliefType.RADIUS,
    ):
        """
        Initialize the jointed box generator.

        Args:
            specs: Box specifications.
            profile: Tube profile (includes tolerances).
            relief_type: Corner relief type for slots.
        """
        self.specs = specs
        self.profile = profile
        self.relief_type = relief_type

        # Sub-generators
        self.frame_gen = BoxFrameGenerator(specs, profile)
        self.tab_slot_gen = TabSlotGenerator(
            profile,
            tab_depth_ratio=specs.tab_depth_ratio,
            relief_type=relief_type,
        )
        self.interference_checker = InterferenceChecker()

        # Generated data
        self.frame_members: List[FrameMember] = []
        self.member_axes: List[MemberAxis] = []
        self.joints: List[Joint] = []
        self.jointed_members: Dict[str, JointedMember] = {}

        # State
        self._generated = False

    def generate(self) -> None:
        """
        Generate all frame members and joints.

        Call this before create_parts() or accessing member data.
        """
        # Generate frame members
        self.frame_members = self.frame_gen.generate_members()

        # Convert to member axes for joint detection
        self.member_axes = self._create_member_axes()

        # Detect all joints
        self.joints = detect_all_joints(self.member_axes)

        # Create jointed member entries
        self._build_jointed_members()

        # Generate tab/slot geometry for each joint
        self._generate_joint_features()

        self._generated = True

    def _create_member_axes(self) -> List[MemberAxis]:
        """Convert FrameMembers to MemberAxis for joint detection."""
        axes = []

        for fm in self.frame_members:
            px, py, pz = fm.position
            length = fm.length_mm
            rx, ry, rz = fm.rotation

            # Determine end point based on rotation
            # Check for rotation around X axis (±90° means tube lies along Y)
            if abs(abs(rx) - 90) < 1:
                end = (px, py + length, pz)
            # Check for rotation around Y axis (±90° means tube lies along X)
            elif abs(abs(ry) - 90) < 1:
                end = (px + length, py, pz)
            # No rotation means tube lies along Z
            else:
                end = (px, py, pz + length)

            axes.append(MemberAxis(
                member_id=fm.get_name(),
                start=fm.position,
                end=end,
                width=self.profile.geometry.outer_width_mm,
                height=self.profile.geometry.outer_height_mm,
            ))

        return axes

    def _build_jointed_members(self) -> None:
        """Build JointedMember entries for each frame member."""
        # Create entry for each member
        for fm, axis in zip(self.frame_members, self.member_axes):
            self.jointed_members[axis.member_id] = JointedMember(
                member=fm,
                axis=axis,
            )

        # Associate joints with their members
        for joint in self.joints:
            # Member A (slot member)
            if joint.member_a.member_id in self.jointed_members:
                self.jointed_members[joint.member_a.member_id].joints.append(joint)

            # Member B (tab member)
            if joint.member_b.member_id in self.jointed_members:
                self.jointed_members[joint.member_b.member_id].joints.append(joint)

    def _generate_joint_features(self) -> None:
        """Generate tab/slot geometry for all joints."""
        for joint in self.joints:
            if joint.joint_type == JointType.INLINE:
                continue

            # Generate tab and slot
            tab, slot = self.tab_slot_gen.generate_joint_features(joint)

            if tab and joint.member_b.member_id in self.jointed_members:
                self.jointed_members[joint.member_b.member_id].tabs.append(tab)

            if slot and joint.member_a.member_id in self.jointed_members:
                self.jointed_members[joint.member_a.member_id].slots.append(slot)

    def check_interference(self) -> List:
        """
        Check for interference between tabs and slots.

        Returns:
            List of Interference objects.
        """
        if not self._generated:
            self.generate()

        # Collect all tabs and slots with IDs
        all_tabs = []
        all_slots = []

        for member_id, jm in self.jointed_members.items():
            for tab in jm.tabs:
                all_tabs.append((member_id, tab))
            for slot in jm.slots:
                all_slots.append((member_id, slot))

        return self.interference_checker.check_all(all_tabs, all_slots)

    def create_parts(
        self,
        doc: "App.Document",
        group_name: str = "JointedFrame",
        apply_joinery: bool = True,
    ) -> List["App.DocumentObject"]:
        """
        Create FreeCAD Part objects with tab/slot features.

        Args:
            doc: FreeCAD document.
            group_name: Name for the part group.
            apply_joinery: If True, apply tabs and slots. If False, plain tubes.

        Returns:
            List of Part::Feature objects.
        """
        if not HAS_FREECAD:
            raise RuntimeError("FreeCAD not available")

        if not self._generated:
            self.generate()

        # Create group
        group = doc.addObject("App::DocumentObjectGroup", group_name)
        parts = []

        for member_id, jm in self.jointed_members.items():
            # Create base tube shape
            shape = create_tube_solid(self.profile, jm.member.length_mm)

            # Apply rotation
            rx, ry, rz = jm.member.rotation
            if rx != 0:
                shape.rotate(Vector(0, 0, 0), Vector(1, 0, 0), rx)
            if ry != 0:
                shape.rotate(Vector(0, 0, 0), Vector(0, 1, 0), ry)
            if rz != 0:
                shape.rotate(Vector(0, 0, 0), Vector(0, 0, 1), rz)

            # Apply translation
            px, py, pz = jm.member.position
            shape.translate(Vector(px, py, pz))

            # Apply joinery if enabled
            if apply_joinery and self.specs.tabs_enabled:
                # Apply slots (cut)
                if jm.slots:
                    shape = apply_slots_to_member(shape, jm.slots, self.tab_slot_gen)

                # Apply tabs (add)
                if jm.tabs:
                    shape = apply_tabs_to_member(shape, jm.tabs, self.tab_slot_gen)

            # Store shape
            jm.shape = shape

            # Create Part::Feature
            part = doc.addObject("Part::Feature", member_id)
            part.Shape = shape
            group.addObject(part)
            parts.append(part)

        doc.recompute()
        return parts

    def get_member_summary(self) -> str:
        """Get a text summary of all members and their joints."""
        if not self._generated:
            self.generate()

        lines = [
            f"Box Frame Summary",
            f"================",
            f"Dimensions: {self.specs.length_mm}x{self.specs.height_mm}x{self.specs.depth_mm}mm",
            f"Profile: {self.profile.name}",
            f"Total members: {len(self.jointed_members)}",
            f"Total joints: {len(self.joints)}",
            "",
            "Members:",
        ]

        for member_id, jm in self.jointed_members.items():
            lines.append(f"  {member_id}:")
            lines.append(f"    Length: {jm.member.length_mm:.1f}mm")
            lines.append(f"    Joints: {len(jm.joints)}")
            lines.append(f"    Tabs: {len(jm.tabs)}")
            lines.append(f"    Slots: {len(jm.slots)}")

        return "\n".join(lines)


def create_jointed_box_frame(
    doc: "App.Document",
    specs: Optional[BoxSpecsData] = None,
    profile_name: str = "2x2x0.125_A36",
    relief_type: CornerReliefType = CornerReliefType.RADIUS,
) -> Tuple[List["App.DocumentObject"], JointedBoxGenerator]:
    """
    Convenience function to create a complete jointed box frame.

    Args:
        doc: FreeCAD document.
        specs: Box specifications (uses defaults if None).
        profile_name: Name of tube profile.
        relief_type: Corner relief type.

    Returns:
        Tuple of (list of parts, generator instance).
    """
    if specs is None:
        specs = BoxSpecsData()

    profile = get_profile(profile_name)
    if profile is None:
        raise ValueError(f"Profile not found: {profile_name}")

    generator = JointedBoxGenerator(specs, profile, relief_type)
    parts = generator.create_parts(doc)

    return parts, generator
