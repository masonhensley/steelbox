"""
Joint Detector - Find intersections between tube members.

Analyzes frame geometry to identify where members meet and what
type of joint each intersection requires.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple, Optional, Set
import math

# Try FreeCAD imports
try:
    import FreeCAD as App
    from FreeCAD import Vector
    HAS_FREECAD = True
except ImportError:
    HAS_FREECAD = False
    Vector = None


class JointType(Enum):
    """Types of tube joints."""
    T_JOINT = "t_joint"           # Perpendicular, one member ends at another
    CORNER = "corner"             # Two members meet at corner (both end)
    CROSS = "cross"               # Members cross through each other
    INLINE = "inline"             # End-to-end alignment
    SKEW = "skew"                 # Non-perpendicular intersection


class TabPosition(Enum):
    """Which face of the tube the tab is on."""
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


@dataclass
class MemberAxis:
    """
    Simplified representation of a tube member for intersection detection.

    Members are represented as line segments along their centerline.
    """
    member_id: str
    start: Tuple[float, float, float]  # (x, y, z) in mm
    end: Tuple[float, float, float]
    width: float   # Tube width (mm)
    height: float  # Tube height (mm)

    @property
    def direction(self) -> Tuple[float, float, float]:
        """Unit vector along member axis."""
        dx = self.end[0] - self.start[0]
        dy = self.end[1] - self.start[1]
        dz = self.end[2] - self.start[2]
        length = math.sqrt(dx*dx + dy*dy + dz*dz)
        if length < 1e-6:
            return (0, 0, 1)
        return (dx/length, dy/length, dz/length)

    @property
    def length(self) -> float:
        """Member length in mm."""
        dx = self.end[0] - self.start[0]
        dy = self.end[1] - self.start[1]
        dz = self.end[2] - self.start[2]
        return math.sqrt(dx*dx + dy*dy + dz*dz)

    @property
    def midpoint(self) -> Tuple[float, float, float]:
        """Center point of member."""
        return (
            (self.start[0] + self.end[0]) / 2,
            (self.start[1] + self.end[1]) / 2,
            (self.start[2] + self.end[2]) / 2,
        )

    def is_vertical(self, tol: float = 0.01) -> bool:
        """Check if member is primarily vertical (Z-axis)."""
        d = self.direction
        return abs(d[2]) > 1 - tol

    def is_horizontal_x(self, tol: float = 0.01) -> bool:
        """Check if member runs along X axis."""
        d = self.direction
        return abs(d[0]) > 1 - tol

    def is_horizontal_y(self, tol: float = 0.01) -> bool:
        """Check if member runs along Y axis."""
        d = self.direction
        return abs(d[1]) > 1 - tol

    def point_at_param(self, t: float) -> Tuple[float, float, float]:
        """Get point along member axis at parameter t (0=start, 1=end)."""
        return (
            self.start[0] + t * (self.end[0] - self.start[0]),
            self.start[1] + t * (self.end[1] - self.start[1]),
            self.start[2] + t * (self.end[2] - self.start[2]),
        )


@dataclass
class Joint:
    """
    Describes a joint between two members.

    Stores which members meet, where they meet, and what type of joint it is.
    """
    joint_type: JointType
    member_a: MemberAxis        # The "receiving" member (gets slot)
    member_b: MemberAxis        # The "inserting" member (has tab)
    intersection_point: Tuple[float, float, float]
    param_a: float              # Parameter along member_a (0-1)
    param_b: float              # Parameter along member_b (0-1)

    # Tab placement info
    tab_face: TabPosition = TabPosition.TOP
    slot_face: TabPosition = TabPosition.TOP

    @property
    def is_end_joint_a(self) -> bool:
        """Does joint occur at end of member A?"""
        return self.param_a < 0.01 or self.param_a > 0.99

    @property
    def is_end_joint_b(self) -> bool:
        """Does joint occur at end of member B?"""
        return self.param_b < 0.01 or self.param_b > 0.99


def _dot(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> float:
    """Dot product of two 3D vectors."""
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]


def _cross(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Cross product of two 3D vectors."""
    return (
        a[1]*b[2] - a[2]*b[1],
        a[2]*b[0] - a[0]*b[2],
        a[0]*b[1] - a[1]*b[0],
    )


def _subtract(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Subtract two 3D vectors."""
    return (a[0]-b[0], a[1]-b[1], a[2]-b[2])


def _norm(v: Tuple[float, float, float]) -> float:
    """Length of 3D vector."""
    return math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])


def _closest_points_on_lines(
    p1: Tuple[float, float, float],
    d1: Tuple[float, float, float],
    p2: Tuple[float, float, float],
    d2: Tuple[float, float, float],
) -> Tuple[float, float, float]:
    """
    Find closest points between two infinite lines.

    Returns: (t1, t2, distance) where t1, t2 are parameters along each line.
    """
    # Line 1: p1 + t1*d1
    # Line 2: p2 + t2*d2

    w0 = _subtract(p1, p2)
    a = _dot(d1, d1)
    b = _dot(d1, d2)
    c = _dot(d2, d2)
    d = _dot(d1, w0)
    e = _dot(d2, w0)

    denom = a*c - b*b

    if abs(denom) < 1e-10:
        # Lines are parallel
        t1 = 0
        t2 = d / b if abs(b) > 1e-10 else 0
    else:
        t1 = (b*e - c*d) / denom
        t2 = (a*e - b*d) / denom

    # Calculate distance
    pt1 = (p1[0] + t1*d1[0], p1[1] + t1*d1[1], p1[2] + t1*d1[2])
    pt2 = (p2[0] + t2*d2[0], p2[1] + t2*d2[1], p2[2] + t2*d2[2])
    dist = _norm(_subtract(pt1, pt2))

    return (t1, t2, dist)


def find_intersection(
    member_a: MemberAxis,
    member_b: MemberAxis,
    tolerance: float = 1.0,  # mm - how close to count as intersection
) -> Optional[Joint]:
    """
    Find if two members intersect and classify the joint type.

    Args:
        member_a: First member
        member_b: Second member
        tolerance: Distance threshold for intersection (mm)

    Returns:
        Joint object if members intersect, None otherwise.
    """
    # Get line parameters
    p1 = member_a.start
    d1_raw = _subtract(member_a.end, member_a.start)
    len1 = _norm(d1_raw)
    d1 = (d1_raw[0]/len1, d1_raw[1]/len1, d1_raw[2]/len1) if len1 > 1e-6 else (0, 0, 1)

    p2 = member_b.start
    d2_raw = _subtract(member_b.end, member_b.start)
    len2 = _norm(d2_raw)
    d2 = (d2_raw[0]/len2, d2_raw[1]/len2, d2_raw[2]/len2) if len2 > 1e-6 else (0, 0, 1)

    # Find closest approach
    t1, t2, dist = _closest_points_on_lines(p1, d1, p2, d2)

    # Convert to segment parameters (0-1)
    param_a = t1 / len1 if len1 > 1e-6 else 0
    param_b = t2 / len2 if len2 > 1e-6 else 0

    # Check if intersection is within both segments (with some margin for tube width)
    margin_a = (member_a.width / 2 + tolerance) / len1 if len1 > 1e-6 else 0
    margin_b = (member_b.width / 2 + tolerance) / len2 if len2 > 1e-6 else 0

    if param_a < -margin_a or param_a > 1 + margin_a:
        return None
    if param_b < -margin_b or param_b > 1 + margin_b:
        return None

    # Check distance including tube widths
    effective_tolerance = tolerance + (member_a.width + member_b.width) / 2
    if dist > effective_tolerance:
        return None

    # Clamp parameters to valid range
    param_a = max(0, min(1, param_a))
    param_b = max(0, min(1, param_b))

    # Calculate intersection point
    int_pt = member_a.point_at_param(param_a)

    # Classify joint type
    dot_dirs = abs(_dot(d1, d2))

    if dot_dirs > 0.99:
        # Parallel - inline joint
        joint_type = JointType.INLINE
    elif dot_dirs < 0.01:
        # Perpendicular
        if param_a < 0.01 or param_a > 0.99:
            if param_b < 0.01 or param_b > 0.99:
                joint_type = JointType.CORNER
            else:
                joint_type = JointType.T_JOINT
        elif param_b < 0.01 or param_b > 0.99:
            joint_type = JointType.T_JOINT
        else:
            joint_type = JointType.CROSS
    else:
        joint_type = JointType.SKEW

    # Determine which member receives slot vs has tab
    # Rule: The member that continues past the joint gets the slot
    # The member that ends at the joint has the tab
    if param_b < 0.01 or param_b > 0.99:
        # Member B ends at joint - it has the tab
        slot_member = member_a
        tab_member = member_b
    else:
        # Member A ends or cross - A has tab
        slot_member = member_b
        tab_member = member_a

    # Determine tab face based on relative orientation
    # Tabs go on TOP/BOTTOM (Z faces for vertical, Y faces for horizontal)
    tab_face = TabPosition.TOP
    slot_face = TabPosition.TOP

    if tab_member.is_vertical():
        # Vertical member - tab on side facing the slot member
        tab_face = TabPosition.TOP  # Will be refined
    elif tab_member.is_horizontal_x():
        # Horizontal along X - tabs on top/bottom (Z faces)
        tab_face = TabPosition.TOP
    elif tab_member.is_horizontal_y():
        # Horizontal along Y - tabs on top/bottom (Z faces)
        tab_face = TabPosition.TOP

    return Joint(
        joint_type=joint_type,
        member_a=slot_member,
        member_b=tab_member,
        intersection_point=int_pt,
        param_a=param_a if slot_member == member_a else param_b,
        param_b=param_b if tab_member == member_b else param_a,
        tab_face=tab_face,
        slot_face=slot_face,
    )


def detect_all_joints(
    members: List[MemberAxis],
    tolerance: float = 1.0,
) -> List[Joint]:
    """
    Find all joints between a list of members.

    Args:
        members: List of MemberAxis objects
        tolerance: Distance threshold for intersection (mm)

    Returns:
        List of Joint objects for all detected intersections.
    """
    joints = []
    n = len(members)

    for i in range(n):
        for j in range(i + 1, n):
            joint = find_intersection(members[i], members[j], tolerance)
            if joint:
                joints.append(joint)

    return joints


def members_from_frame_members(frame_members: list) -> List[MemberAxis]:
    """
    Convert FrameMember objects to MemberAxis for joint detection.

    Args:
        frame_members: List of FrameMember from box_generator

    Returns:
        List of MemberAxis objects
    """
    axes = []

    for fm in frame_members:
        # Calculate end point from start + length along direction
        px, py, pz = fm.position
        length = fm.length_mm
        rx, ry, rz = fm.rotation

        # Determine direction based on rotation
        # Default direction is +Z (vertical)
        # 90° X rotation -> +Y direction
        # 90° Y rotation -> +X direction
        if abs(rx - 90) < 1:
            # Rotated around X -> points along Y
            end = (px, py + length, pz)
        elif abs(ry - 90) < 1:
            # Rotated around Y -> points along X
            end = (px + length, py, pz)
        else:
            # Default vertical (along Z)
            end = (px, py, pz + length)

        # Get tube dimensions from profile (assume square for now)
        # This should come from the profile, but we'll use a default
        tube_size = 50.8  # Default 2" tube

        axes.append(MemberAxis(
            member_id=fm.get_name(),
            start=fm.position,
            end=end,
            width=tube_size,
            height=tube_size,
        ))

    return axes
