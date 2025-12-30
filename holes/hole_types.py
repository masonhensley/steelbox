"""
Hole Types - Standard hole specifications for fasteners.

Defines common hole types for rivets, riv-nuts, bolts, and custom holes.
"""

from dataclasses import dataclass
from typing import Optional, Dict
from enum import Enum


class HoleType(Enum):
    """Standard hole types."""
    RIVET = "rivet"
    RIV_NUT = "riv_nut"
    BOLT = "bolt"
    CUSTOM = "custom"
    PILOT = "pilot"          # Small pilot hole
    COUNTERSINK = "countersink"


@dataclass
class HoleSpec:
    """
    Specification for a single hole.

    Includes diameter, countersink info, and metadata.
    """
    hole_type: HoleType
    diameter_mm: float
    name: str = ""
    description: str = ""

    # Countersink options
    countersink: bool = False
    countersink_diameter_mm: float = 0.0
    countersink_angle_deg: float = 82.0  # Standard for flat head screws
    countersink_depth_mm: float = 0.0

    # Counterbore options (for socket head cap screws)
    counterbore: bool = False
    counterbore_diameter_mm: float = 0.0
    counterbore_depth_mm: float = 0.0

    def __post_init__(self):
        if not self.name:
            self.name = f"{self.hole_type.value}_{self.diameter_mm}mm"


# Standard rivet holes
@dataclass
class RivetHole(HoleSpec):
    """Standard rivet hole specifications."""

    def __init__(self, rivet_diameter_mm: float = 4.8):
        """
        Create rivet hole spec.

        Args:
            rivet_diameter_mm: Rivet body diameter (e.g., 4.8mm for 3/16" rivet)
        """
        # Hole is slightly larger than rivet
        clearance = 0.2
        super().__init__(
            hole_type=HoleType.RIVET,
            diameter_mm=rivet_diameter_mm + clearance,
            name=f"Rivet_{rivet_diameter_mm}mm",
            description=f"Clearance hole for {rivet_diameter_mm}mm rivet",
        )


# Standard riv-nut holes
@dataclass
class RivNutHole(HoleSpec):
    """
    Riv-nut (threaded insert) hole specifications.

    Riv-nuts require specific hole sizes based on thread size.
    """

    # Standard riv-nut hole sizes (thread size -> hole diameter in mm)
    STANDARD_SIZES: Dict[str, float] = None

    def __init__(self, thread_size: str = "M5"):
        """
        Create riv-nut hole spec.

        Args:
            thread_size: Thread size (e.g., "M5", "M6", "1/4-20")
        """
        if self.STANDARD_SIZES is None:
            RivNutHole.STANDARD_SIZES = {
                "M3": 5.0,
                "M4": 6.0,
                "M5": 7.0,
                "M6": 9.0,
                "M8": 11.0,
                "M10": 13.0,
                "#6-32": 6.5,
                "#8-32": 7.5,
                "#10-24": 8.5,
                "#10-32": 8.5,
                "1/4-20": 9.5,
                "5/16-18": 11.0,
                "3/8-16": 13.0,
            }

        diameter = self.STANDARD_SIZES.get(thread_size, 7.0)  # Default to M5

        super().__init__(
            hole_type=HoleType.RIV_NUT,
            diameter_mm=diameter,
            name=f"RivNut_{thread_size}",
            description=f"Hole for {thread_size} riv-nut installation",
        )


@dataclass
class BoltHole(HoleSpec):
    """
    Bolt clearance hole specifications.

    Creates clearance holes for bolts with optional countersink.
    """

    # Standard bolt clearance holes (nominal size -> close fit hole in mm)
    CLEARANCE_CLOSE: Dict[str, float] = None
    CLEARANCE_NORMAL: Dict[str, float] = None

    def __init__(
        self,
        bolt_size: str = "M5",
        fit: str = "normal",
        countersunk: bool = False,
    ):
        """
        Create bolt hole spec.

        Args:
            bolt_size: Bolt size (e.g., "M5", "M6", "1/4")
            fit: "close" or "normal" clearance
            countersunk: Whether to add countersink for flat head
        """
        if self.CLEARANCE_CLOSE is None:
            BoltHole.CLEARANCE_CLOSE = {
                "M3": 3.2,
                "M4": 4.3,
                "M5": 5.3,
                "M6": 6.4,
                "M8": 8.4,
                "M10": 10.5,
                "M12": 13.0,
                "#6": 3.6,
                "#8": 4.4,
                "#10": 5.0,
                "1/4": 6.6,
                "5/16": 8.3,
                "3/8": 9.9,
            }
            BoltHole.CLEARANCE_NORMAL = {
                "M3": 3.4,
                "M4": 4.5,
                "M5": 5.5,
                "M6": 6.6,
                "M8": 9.0,
                "M10": 11.0,
                "M12": 13.5,
                "#6": 3.8,
                "#8": 4.6,
                "#10": 5.3,
                "1/4": 7.0,
                "5/16": 8.7,
                "3/8": 10.3,
            }

        sizes = self.CLEARANCE_CLOSE if fit == "close" else self.CLEARANCE_NORMAL
        diameter = sizes.get(bolt_size, 5.5)

        # Countersink dimensions
        cs_diameter = 0.0
        cs_depth = 0.0
        if countersunk:
            # Flat head countersink is about 2x hole diameter
            cs_diameter = diameter * 2.0
            cs_depth = diameter * 0.5

        super().__init__(
            hole_type=HoleType.BOLT,
            diameter_mm=diameter,
            name=f"Bolt_{bolt_size}_{fit}",
            description=f"{fit.title()} fit clearance for {bolt_size} bolt",
            countersink=countersunk,
            countersink_diameter_mm=cs_diameter,
            countersink_depth_mm=cs_depth,
        )


@dataclass
class CustomHole(HoleSpec):
    """Custom hole with user-specified diameter."""

    def __init__(
        self,
        diameter_mm: float,
        name: str = "",
        countersink: bool = False,
        countersink_diameter_mm: float = 0.0,
    ):
        """
        Create custom hole spec.

        Args:
            diameter_mm: Hole diameter in mm.
            name: Optional name.
            countersink: Whether to add countersink.
            countersink_diameter_mm: Countersink diameter (0 = auto).
        """
        super().__init__(
            hole_type=HoleType.CUSTOM,
            diameter_mm=diameter_mm,
            name=name or f"Custom_{diameter_mm}mm",
            countersink=countersink,
            countersink_diameter_mm=countersink_diameter_mm or diameter_mm * 2,
        )


# Convenience function to get standard holes
def get_hole_spec(
    hole_type: str,
    size: str = "",
    **kwargs,
) -> HoleSpec:
    """
    Get a hole specification by type and size.

    Args:
        hole_type: "rivet", "riv_nut", "bolt", or "custom"
        size: Size specification (e.g., "4.8mm" for rivet, "M5" for bolt)
        **kwargs: Additional arguments passed to hole constructor

    Returns:
        HoleSpec instance

    Examples:
        get_hole_spec("rivet", "4.8")
        get_hole_spec("bolt", "M6", countersunk=True)
        get_hole_spec("riv_nut", "M5")
        get_hole_spec("custom", diameter_mm=8.0)
    """
    if hole_type == "rivet":
        diameter = float(size) if size else 4.8
        return RivetHole(diameter)

    elif hole_type == "riv_nut":
        thread = size or "M5"
        return RivNutHole(thread)

    elif hole_type == "bolt":
        bolt_size = size or "M5"
        return BoltHole(bolt_size, **kwargs)

    elif hole_type == "custom":
        diameter = kwargs.get("diameter_mm", float(size) if size else 5.0)
        return CustomHole(diameter, **kwargs)

    else:
        raise ValueError(f"Unknown hole type: {hole_type}")
