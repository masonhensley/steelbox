"""
SteelBox Holes Module

Hole pattern generation for frames and panels.

Usage:
    from holes import HolePattern, HoleType, generate_hole_pattern
"""

from .hole_types import (
    HoleType,
    HoleSpec,
    RivetHole,
    RivNutHole,
    BoltHole,
    CustomHole,
    get_hole_spec,
)

from .pattern_generator import (
    HolePattern,
    PatternDistribution,
    HolePatternGenerator,
    generate_hole_pattern,
    apply_holes_to_face,
)

__all__ = [
    # Hole types
    "HoleType",
    "HoleSpec",
    "RivetHole",
    "RivNutHole",
    "BoltHole",
    "CustomHole",
    "get_hole_spec",
    # Pattern generation
    "HolePattern",
    "PatternDistribution",
    "HolePatternGenerator",
    "generate_hole_pattern",
    "apply_holes_to_face",
]
