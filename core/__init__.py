"""
SteelBox Core Module

Box generation and spreadsheet integration.

Usage:
    from core import BoxSpecsData, BoxFrameGenerator
    from core import create_box_specs_spreadsheet, create_box_frame
"""

from .box_specs import (
    BoxSpecsData,
    DimensionReference,
    create_box_specs_spreadsheet,
    read_box_specs,
)

from .box_generator import (
    BoxFrameGenerator,
    FrameMember,
    MemberType,
    MemberFace,
    create_box_frame,
)

from .jointed_box import (
    JointedMember,
    JointedBoxGenerator,
    create_jointed_box_frame,
)

__all__ = [
    # Specs
    "BoxSpecsData",
    "DimensionReference",
    "create_box_specs_spreadsheet",
    "read_box_specs",
    # Basic Generator
    "BoxFrameGenerator",
    "FrameMember",
    "MemberType",
    "MemberFace",
    "create_box_frame",
    # Jointed Generator
    "JointedMember",
    "JointedBoxGenerator",
    "create_jointed_box_frame",
]
