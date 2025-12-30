"""
SteelBox Joinery Module

Tab/slot joint generation with corner relief and interference checking.

Usage:
    from joinery import (
        detect_all_joints,
        TabSlotGenerator,
        InterferenceChecker,
    )
"""

from .joint_detector import (
    Joint,
    JointType,
    MemberAxis,
    TabPosition,
    find_intersection,
    detect_all_joints,
    members_from_frame_members,
)

from .tab_slot import (
    CornerReliefType,
    TabGeometry,
    SlotGeometry,
    TabSlotGenerator,
    apply_slots_to_member,
    apply_tabs_to_member,
)

from .corner_relief import (
    CornerReliefParams,
    create_dogbone_relief,
    create_tbone_relief,
    create_radius_slot_profile,
    create_slot_with_relief,
    recommend_relief_type,
)

from .interference import (
    Interference,
    InterferenceType,
    InterferenceChecker,
    check_tab_tab_interference,
    check_slot_slot_interference,
    calc_notch_positions,
)

__all__ = [
    # Joint detection
    "Joint",
    "JointType",
    "MemberAxis",
    "TabPosition",
    "find_intersection",
    "detect_all_joints",
    "members_from_frame_members",
    # Tab/Slot generation
    "CornerReliefType",
    "TabGeometry",
    "SlotGeometry",
    "TabSlotGenerator",
    "apply_slots_to_member",
    "apply_tabs_to_member",
    # Corner relief
    "CornerReliefParams",
    "create_dogbone_relief",
    "create_tbone_relief",
    "create_radius_slot_profile",
    "create_slot_with_relief",
    "recommend_relief_type",
    # Interference
    "Interference",
    "InterferenceType",
    "InterferenceChecker",
    "check_tab_tab_interference",
    "check_slot_slot_interference",
    "calc_notch_positions",
]
