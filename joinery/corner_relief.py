"""
Corner Relief - Generate corner relief geometry for slots.

Provides different relief strategies to ensure tabs can fully seat in slots
despite the limitations of laser/plasma cutting.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Tuple, List, Optional
import math

try:
    import FreeCAD as App
    import Part
    from FreeCAD import Vector
    HAS_FREECAD = True
except ImportError:
    HAS_FREECAD = False
    Part = None
    Vector = None

from .tab_slot import CornerReliefType


@dataclass
class CornerReliefParams:
    """Parameters for corner relief generation."""
    relief_type: CornerReliefType
    radius: float  # mm - radius for dogbone circles or corner rounding
    slot_width: float  # mm
    slot_length: float  # mm
    slot_depth: float  # mm


def create_dogbone_relief(
    slot_width: float,
    slot_length: float,
    slot_depth: float,
    radius: float,
) -> "Part.Shape":
    """
    Create dogbone corner relief (circles at corners).

    Dogbone relief places circular cutouts at each corner of the slot,
    allowing square-cornered tabs to fully seat.

    Args:
        slot_width: Width of the slot (mm)
        slot_length: Length of the slot (mm)
        slot_depth: Depth of the slot cut (mm)
        radius: Radius of dogbone circles (mm)

    Returns:
        Part.Shape to be fused with slot for relief.
    """
    if not HAS_FREECAD:
        raise RuntimeError("FreeCAD not available")

    half_w = slot_width / 2
    half_l = slot_length / 2

    # Corner positions - offset inward by radius so circle extends to corner
    corners = [
        (half_w - radius, half_l - radius),
        (half_w - radius, -half_l + radius),
        (-half_w + radius, half_l - radius),
        (-half_w + radius, -half_l + radius),
    ]

    shapes = []
    for cx, cy in corners:
        # Cylinder at each corner
        cyl = Part.makeCylinder(
            radius,
            slot_depth * 2,
            Vector(cx, cy, -slot_depth),
            Vector(0, 0, 1),
        )
        shapes.append(cyl)

    if shapes:
        result = shapes[0]
        for s in shapes[1:]:
            result = result.fuse(s)
        return result

    return Part.Shape()  # Empty shape


def create_tbone_relief(
    slot_width: float,
    slot_length: float,
    slot_depth: float,
    radius: float,
) -> "Part.Shape":
    """
    Create T-bone corner relief.

    T-bone relief extends one side of each corner perpendicular to the slot,
    creating a T-shape that allows tabs to seat.

    Args:
        slot_width: Width of the slot (mm)
        slot_length: Length of the slot (mm)
        slot_depth: Depth of the slot cut (mm)
        radius: Extension length for T-bone (mm)

    Returns:
        Part.Shape to be fused with slot for relief.
    """
    if not HAS_FREECAD:
        raise RuntimeError("FreeCAD not available")

    half_w = slot_width / 2
    half_l = slot_length / 2

    # T-bone extensions at ends of slot (along length direction)
    extension_width = radius * 2
    extension_length = slot_width + radius * 2

    shapes = []

    # Extension at +length end
    box1 = Part.makeBox(
        extension_length,
        extension_width,
        slot_depth * 2,
        Vector(-extension_length/2, half_l - extension_width/2, -slot_depth),
    )
    shapes.append(box1)

    # Extension at -length end
    box2 = Part.makeBox(
        extension_length,
        extension_width,
        slot_depth * 2,
        Vector(-extension_length/2, -half_l - extension_width/2, -slot_depth),
    )
    shapes.append(box2)

    if shapes:
        result = shapes[0]
        for s in shapes[1:]:
            result = result.fuse(s)
        return result

    return Part.Shape()


def create_radius_slot_profile(
    slot_width: float,
    slot_length: float,
    radius: float,
) -> "Part.Wire":
    """
    Create a rounded rectangle wire for radius corner slots.

    Args:
        slot_width: Width of the slot (mm)
        slot_length: Length of the slot (mm)
        radius: Corner radius (mm)

    Returns:
        Part.Wire forming the slot profile.
    """
    if not HAS_FREECAD:
        raise RuntimeError("FreeCAD not available")

    half_w = slot_width / 2
    half_l = slot_length / 2
    r = min(radius, half_w, half_l)  # Clamp radius

    edges = []

    if r > 0.01:
        # Rounded rectangle: 4 lines + 4 arcs
        # Bottom edge
        edges.append(Part.LineSegment(
            Vector(-half_w + r, -half_l, 0),
            Vector(half_w - r, -half_l, 0),
        ))
        # Bottom-right arc
        edges.append(Part.Arc(
            Vector(half_w - r, -half_l, 0),
            Vector(half_w - r + r * math.cos(math.radians(-45)),
                   -half_l + r - r * math.sin(math.radians(-45)), 0),
            Vector(half_w, -half_l + r, 0),
        ))
        # Right edge
        edges.append(Part.LineSegment(
            Vector(half_w, -half_l + r, 0),
            Vector(half_w, half_l - r, 0),
        ))
        # Top-right arc
        edges.append(Part.Arc(
            Vector(half_w, half_l - r, 0),
            Vector(half_w - r + r * math.cos(math.radians(45)),
                   half_l - r + r * math.sin(math.radians(45)), 0),
            Vector(half_w - r, half_l, 0),
        ))
        # Top edge
        edges.append(Part.LineSegment(
            Vector(half_w - r, half_l, 0),
            Vector(-half_w + r, half_l, 0),
        ))
        # Top-left arc
        edges.append(Part.Arc(
            Vector(-half_w + r, half_l, 0),
            Vector(-half_w + r - r * math.cos(math.radians(45)),
                   half_l - r + r * math.sin(math.radians(45)), 0),
            Vector(-half_w, half_l - r, 0),
        ))
        # Left edge
        edges.append(Part.LineSegment(
            Vector(-half_w, half_l - r, 0),
            Vector(-half_w, -half_l + r, 0),
        ))
        # Bottom-left arc
        edges.append(Part.Arc(
            Vector(-half_w, -half_l + r, 0),
            Vector(-half_w + r - r * math.cos(math.radians(-45)),
                   -half_l + r - r * math.sin(math.radians(-45)), 0),
            Vector(-half_w + r, -half_l, 0),
        ))
    else:
        # Simple rectangle
        edges.append(Part.LineSegment(Vector(-half_w, -half_l, 0), Vector(half_w, -half_l, 0)))
        edges.append(Part.LineSegment(Vector(half_w, -half_l, 0), Vector(half_w, half_l, 0)))
        edges.append(Part.LineSegment(Vector(half_w, half_l, 0), Vector(-half_w, half_l, 0)))
        edges.append(Part.LineSegment(Vector(-half_w, half_l, 0), Vector(-half_w, -half_l, 0)))

    edge_shapes = [e.toShape() for e in edges]
    return Part.Wire(edge_shapes)


def create_slot_with_relief(
    slot_width: float,
    slot_length: float,
    slot_depth: float,
    relief_type: CornerReliefType,
    relief_radius: float,
) -> "Part.Shape":
    """
    Create complete slot shape with specified corner relief.

    Args:
        slot_width: Width of the slot (mm)
        slot_length: Length of the slot (mm)
        slot_depth: Depth of the slot cut (mm)
        relief_type: Type of corner relief
        relief_radius: Radius/size for relief

    Returns:
        Part.Shape ready for boolean subtraction.
    """
    if not HAS_FREECAD:
        raise RuntimeError("FreeCAD not available")

    half_w = slot_width / 2
    half_l = slot_length / 2

    if relief_type == CornerReliefType.RADIUS:
        # Create rounded rectangle profile and extrude
        profile = create_radius_slot_profile(slot_width, slot_length, relief_radius)
        face = Part.Face(profile)
        slot = face.extrude(Vector(0, 0, -slot_depth * 2))
        slot.translate(Vector(0, 0, slot_depth))

    elif relief_type == CornerReliefType.DOGBONE:
        # Create square slot + dogbone circles
        base_slot = Part.makeBox(
            slot_width,
            slot_length,
            slot_depth * 2,
            Vector(-half_w, -half_l, -slot_depth),
        )
        dogbones = create_dogbone_relief(slot_width, slot_length, slot_depth, relief_radius)
        slot = base_slot.fuse(dogbones)

    elif relief_type == CornerReliefType.TBONE:
        # Create square slot + T-bone extensions
        base_slot = Part.makeBox(
            slot_width,
            slot_length,
            slot_depth * 2,
            Vector(-half_w, -half_l, -slot_depth),
        )
        tbones = create_tbone_relief(slot_width, slot_length, slot_depth, relief_radius)
        slot = base_slot.fuse(tbones)

    else:
        # No relief - simple box
        slot = Part.makeBox(
            slot_width,
            slot_length,
            slot_depth * 2,
            Vector(-half_w, -half_l, -slot_depth),
        )

    return slot


def recommend_relief_type(
    cutting_process: str,
    tab_corner_radius: float,
) -> CornerReliefType:
    """
    Recommend corner relief type based on cutting process.

    Args:
        cutting_process: "laser", "plasma", "waterjet", "cnc"
        tab_corner_radius: If tabs have rounded corners, match with radius relief

    Returns:
        Recommended CornerReliefType
    """
    process = cutting_process.lower()

    if tab_corner_radius > 0.1:
        # Tabs have rounded corners - use radius relief
        return CornerReliefType.RADIUS

    if process in ("laser", "fiber laser", "co2 laser"):
        # Laser can do small radii easily
        return CornerReliefType.RADIUS

    if process in ("plasma",):
        # Plasma has larger kerf, dogbone works well
        return CornerReliefType.DOGBONE

    if process in ("waterjet",):
        # Waterjet can do either
        return CornerReliefType.RADIUS

    if process in ("cnc", "mill", "router"):
        # CNC needs dogbone for square corners
        return CornerReliefType.DOGBONE

    # Default to radius for laser cutting
    return CornerReliefType.RADIUS
