"""
Interference Checker - Detect tab/slot collisions.

Identifies when tabs from different joints would collide or when
end cap tabs would interfere with member tabs.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional, Set
from enum import Enum
import math

try:
    import FreeCAD as App
    from FreeCAD import Vector
    HAS_FREECAD = True
except ImportError:
    HAS_FREECAD = False

from .joint_detector import Joint, JointType, MemberAxis
from .tab_slot import TabGeometry, SlotGeometry


class InterferenceType(Enum):
    """Types of interference."""
    TAB_TAB = "tab_tab"           # Two tabs would occupy same space
    TAB_SLOT = "tab_slot"         # Tab intersects unintended slot
    SLOT_SLOT = "slot_slot"       # Two slots overlap (structural weakness)
    CAP_TAB = "cap_tab"           # End cap tab hits member tab


@dataclass
class Interference:
    """Describes an interference between features."""
    interference_type: InterferenceType
    feature_a: str  # ID/description of first feature
    feature_b: str  # ID/description of second feature
    location: Tuple[float, float, float]  # Approximate location
    overlap_volume: float = 0.0  # mm³ of overlap (if calculated)
    resolution: str = ""  # Suggested resolution


@dataclass
class BoundingBox:
    """Axis-aligned bounding box for quick intersection tests."""
    min_x: float
    min_y: float
    min_z: float
    max_x: float
    max_y: float
    max_z: float

    def intersects(self, other: "BoundingBox", tolerance: float = 0.1) -> bool:
        """Check if two bounding boxes intersect."""
        return not (
            self.max_x < other.min_x - tolerance or
            self.min_x > other.max_x + tolerance or
            self.max_y < other.min_y - tolerance or
            self.min_y > other.max_y + tolerance or
            self.max_z < other.min_z - tolerance or
            self.min_z > other.max_z + tolerance
        )

    @classmethod
    def from_tab(cls, tab: TabGeometry) -> "BoundingBox":
        """Create bounding box from tab geometry."""
        px, py, pz = tab.position
        dx, dy, dz = tab.direction

        # Tab extends from position along direction by depth
        end = (
            px + dx * tab.depth,
            py + dy * tab.depth,
            pz + dz * tab.depth,
        )

        # Expand by half width/thickness in perpendicular directions
        half_w = tab.width / 2
        half_t = tab.thickness / 2

        return cls(
            min_x=min(px, end[0]) - half_w,
            min_y=min(py, end[1]) - half_w,
            min_z=min(pz, end[2]) - half_t,
            max_x=max(px, end[0]) + half_w,
            max_y=max(py, end[1]) + half_w,
            max_z=max(pz, end[2]) + half_t,
        )

    @classmethod
    def from_slot(cls, slot: SlotGeometry) -> "BoundingBox":
        """Create bounding box from slot geometry."""
        px, py, pz = slot.position
        dx, dy, dz = slot.direction

        # Slot extends from position along direction by depth
        end = (
            px + dx * slot.depth,
            py + dy * slot.depth,
            pz + dz * slot.depth,
        )

        # Expand by half width/length
        half_w = slot.width / 2
        half_l = slot.length / 2

        return cls(
            min_x=min(px, end[0]) - max(half_w, half_l),
            min_y=min(py, end[1]) - max(half_w, half_l),
            min_z=min(pz, end[2]) - max(half_w, half_l),
            max_x=max(px, end[0]) + max(half_w, half_l),
            max_y=max(py, end[1]) + max(half_w, half_l),
            max_z=max(pz, end[2]) + max(half_w, half_l),
        )


def check_tab_tab_interference(
    tabs: List[Tuple[str, TabGeometry]],
    tolerance: float = 0.5,
) -> List[Interference]:
    """
    Check for interference between tabs.

    Args:
        tabs: List of (joint_id, TabGeometry) tuples
        tolerance: Minimum distance between tabs (mm)

    Returns:
        List of detected interferences
    """
    interferences = []

    for i, (id_a, tab_a) in enumerate(tabs):
        box_a = BoundingBox.from_tab(tab_a)

        for j, (id_b, tab_b) in enumerate(tabs[i+1:], i+1):
            box_b = BoundingBox.from_tab(tab_b)

            if box_a.intersects(box_b, tolerance):
                # Potential interference - calculate center
                center = (
                    (tab_a.position[0] + tab_b.position[0]) / 2,
                    (tab_a.position[1] + tab_b.position[1]) / 2,
                    (tab_a.position[2] + tab_b.position[2]) / 2,
                )

                interferences.append(Interference(
                    interference_type=InterferenceType.TAB_TAB,
                    feature_a=f"Tab from {id_a}",
                    feature_b=f"Tab from {id_b}",
                    location=center,
                    resolution="Offset tabs or reduce tab width",
                ))

    return interferences


def check_slot_slot_interference(
    slots: List[Tuple[str, SlotGeometry]],
    min_web: float = 3.0,  # Minimum material between slots (mm)
) -> List[Interference]:
    """
    Check for slots that are too close together (structural weakness).

    Args:
        slots: List of (joint_id, SlotGeometry) tuples
        min_web: Minimum material to leave between slots (mm)

    Returns:
        List of detected interferences
    """
    interferences = []

    for i, (id_a, slot_a) in enumerate(slots):
        box_a = BoundingBox.from_slot(slot_a)

        for j, (id_b, slot_b) in enumerate(slots[i+1:], i+1):
            box_b = BoundingBox.from_slot(slot_b)

            if box_a.intersects(box_b, -min_web):  # Negative tolerance = require gap
                center = (
                    (slot_a.position[0] + slot_b.position[0]) / 2,
                    (slot_a.position[1] + slot_b.position[1]) / 2,
                    (slot_a.position[2] + slot_b.position[2]) / 2,
                )

                interferences.append(Interference(
                    interference_type=InterferenceType.SLOT_SLOT,
                    feature_a=f"Slot from {id_a}",
                    feature_b=f"Slot from {id_b}",
                    location=center,
                    resolution=f"Slots too close - need {min_web}mm minimum web",
                ))

    return interferences


def find_cap_tab_conflicts(
    member_id: str,
    member_tabs: List[TabGeometry],
    cap_tab_positions: List[Tuple[float, float]],  # Positions along tube perimeter
    tube_width: float,
    tube_height: float,
) -> List[Tuple[float, float]]:
    """
    Find where end cap tabs would conflict with member tabs.

    Returns positions where cap tabs should NOT be placed (need notches).

    Args:
        member_id: ID of the member
        member_tabs: Tabs that enter this member at its end
        cap_tab_positions: Proposed cap tab positions (x, y offsets from center)
        tube_width: Tube width (mm)
        tube_height: Tube height (mm)

    Returns:
        List of (x, y) positions that conflict with member tabs
    """
    conflicts = []

    for cap_x, cap_y in cap_tab_positions:
        for tab in member_tabs:
            # Check if cap tab position overlaps with member tab
            tab_half_w = tab.width / 2

            # Member tabs are on tube faces
            # Cap tabs are also on tube faces
            # Check if they're on same face and overlapping

            # Simplified: check if cap position is within tab width
            # of any member tab position
            tab_face_coord = None

            # Determine which face the member tab is on based on position
            px, py, pz = tab.position
            if abs(px) > tube_width / 2 - 1:
                # Tab on X face
                if abs(cap_x - px) < tab_half_w:
                    conflicts.append((cap_x, cap_y))
                    break
            elif abs(py) > tube_height / 2 - 1:
                # Tab on Y face
                if abs(cap_y - py) < tab_half_w:
                    conflicts.append((cap_x, cap_y))
                    break

    return conflicts


def calc_notch_positions(
    member_tabs: List[TabGeometry],
    tube_width: float,
    tube_height: float,
    notch_clearance: float = 1.0,  # Extra clearance around tab (mm)
) -> List[Tuple[float, float, float, float]]:
    """
    Calculate notch positions for end cap slots to avoid member tab interference.

    Returns list of (center_x, center_y, width, height) for each notch.

    Args:
        member_tabs: Tabs that enter the tube end
        tube_width: Tube width (mm)
        tube_height: Tube height (mm)
        notch_clearance: Extra clearance around each tab (mm)

    Returns:
        List of notch definitions (center_x, center_y, width, depth)
    """
    notches = []

    for tab in member_tabs:
        px, py, pz = tab.position

        # Notch needs to clear the full tab width plus clearance
        notch_width = tab.width + 2 * notch_clearance
        notch_depth = tab.depth + notch_clearance

        # Position relative to tube end center
        # The notch is centered on the tab position
        notches.append((px, py, notch_width, notch_depth))

    return notches


class InterferenceChecker:
    """
    Checks for and resolves interference in joinery.
    """

    def __init__(
        self,
        tolerance: float = 0.5,
        min_slot_web: float = 3.0,
    ):
        """
        Initialize checker.

        Args:
            tolerance: Minimum clearance between features (mm)
            min_slot_web: Minimum material between slots (mm)
        """
        self.tolerance = tolerance
        self.min_slot_web = min_slot_web

    def check_all(
        self,
        tabs: List[Tuple[str, TabGeometry]],
        slots: List[Tuple[str, SlotGeometry]],
    ) -> List[Interference]:
        """
        Run all interference checks.

        Args:
            tabs: List of (joint_id, TabGeometry) tuples
            slots: List of (joint_id, SlotGeometry) tuples

        Returns:
            List of all detected interferences
        """
        interferences = []

        # Check tab-tab
        interferences.extend(check_tab_tab_interference(tabs, self.tolerance))

        # Check slot-slot
        interferences.extend(check_slot_slot_interference(slots, self.min_slot_web))

        return interferences

    def report(self, interferences: List[Interference]) -> str:
        """
        Generate a human-readable report of interferences.

        Args:
            interferences: List of detected interferences

        Returns:
            Formatted report string
        """
        if not interferences:
            return "No interferences detected."

        lines = [f"Found {len(interferences)} interference(s):", ""]

        for i, intf in enumerate(interferences, 1):
            lines.append(f"{i}. {intf.interference_type.value.upper()}")
            lines.append(f"   Between: {intf.feature_a}")
            lines.append(f"   And: {intf.feature_b}")
            lines.append(f"   Location: ({intf.location[0]:.1f}, {intf.location[1]:.1f}, {intf.location[2]:.1f})")
            if intf.resolution:
                lines.append(f"   Resolution: {intf.resolution}")
            lines.append("")

        return "\n".join(lines)
