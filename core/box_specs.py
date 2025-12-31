"""
BoxSpecs - Parametric spreadsheet-driven box specifications.

The BoxSpecs spreadsheet is the single source of truth for all box dimensions.
All frame members, panels, and features reference cells in this spreadsheet.
"""

from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# FreeCAD imports
try:
    import FreeCAD as App
    HAS_FREECAD = True
except ImportError:
    HAS_FREECAD = False
    App = None


class DimensionReference(Enum):
    """How dimensions are measured."""
    EXTERIOR = "exterior"      # Outside edge to outside edge
    INTERIOR = "interior"      # Inside edge to inside edge
    CENTERLINE = "centerline"  # Center of tube to center of tube


@dataclass
class BoxSpecsData:
    """
    In-memory representation of box specifications.

    All dimensions in mm. Use .from_imperial() for inch input.
    """
    # Overall dimensions
    length_mm: float = 2438.4       # 96" default
    height_mm: float = 812.8        # 32" default
    depth_mm: float = 609.6         # 24" default

    # Feet
    foot_height_mm: float = 25.4    # 1" default
    caster_reinforcement: bool = False

    # Support spacing (on-center)
    vertical_oc_front_mm: float = 1219.2   # 48" default
    vertical_oc_back_mm: float = 609.6     # 24" default
    horizontal_oc_top_mm: float = 609.6    # 24" default
    horizontal_oc_bottom_mm: float = 609.6 # 24" default

    # Dimension reference mode
    dimension_reference: DimensionReference = DimensionReference.EXTERIOR

    # Tab/slot settings
    tabs_enabled: bool = True
    caps_enabled: bool = True
    tab_depth_mm: float = 10.0    # Fixed tab depth in mm (10mm default)
    tab_width_mm: float = 3.0     # Fixed tab width in mm (3mm default)
    tab_depth_ratio: float = 1.0  # Multiplier for tab_depth_mm (1.0 = use as-is)

    # Panel settings
    panel_thickness_sides_mm: float = 1.5   # 16ga
    panel_thickness_top_mm: float = 2.0     # 14ga
    panel_offset_mm: float = 0.0            # Inset from frame edge

    # Hole settings
    rivet_hole_diameter_mm: float = 4.0
    rivet_spacing_mm: float = 150.0

    # Tube profile reference
    tube_profile_name: str = "2x2x0.125_A36"

    @classmethod
    def from_imperial(
        cls,
        length_in: float,
        height_in: float,
        depth_in: float,
        foot_height_in: float = 1.0,
        vertical_oc_front_in: float = 48.0,
        vertical_oc_back_in: float = 24.0,
        horizontal_oc_top_in: float = 24.0,
        horizontal_oc_bottom_in: float = 24.0,
        **kwargs
    ) -> "BoxSpecsData":
        """Create from imperial (inch) dimensions."""
        return cls(
            length_mm=length_in * 25.4,
            height_mm=height_in * 25.4,
            depth_mm=depth_in * 25.4,
            foot_height_mm=foot_height_in * 25.4,
            vertical_oc_front_mm=vertical_oc_front_in * 25.4,
            vertical_oc_back_mm=vertical_oc_back_in * 25.4,
            horizontal_oc_top_mm=horizontal_oc_top_in * 25.4,
            horizontal_oc_bottom_mm=horizontal_oc_bottom_in * 25.4,
            **kwargs
        )

    def calc_vertical_count_front(self, tube_width_mm: float) -> int:
        """Calculate number of vertical supports on front face."""
        if self.vertical_oc_front_mm <= 0:
            return 0
        # Available space between corners
        usable = self.length_mm - tube_width_mm
        count = int(usable / self.vertical_oc_front_mm)
        return max(0, count - 1)  # -1 because corners count

    def calc_vertical_count_back(self, tube_width_mm: float) -> int:
        """Calculate number of vertical supports on back face."""
        if self.vertical_oc_back_mm <= 0:
            return 0
        usable = self.length_mm - tube_width_mm
        count = int(usable / self.vertical_oc_back_mm)
        return max(0, count - 1)

    def calc_horizontal_count_top(self, tube_width_mm: float) -> int:
        """Calculate number of horizontal cross members on top."""
        if self.horizontal_oc_top_mm <= 0:
            return 0
        usable = self.depth_mm - tube_width_mm
        count = int(usable / self.horizontal_oc_top_mm)
        return max(0, count - 1)

    def calc_horizontal_count_bottom(self, tube_width_mm: float) -> int:
        """Calculate number of horizontal cross members on bottom."""
        if self.horizontal_oc_bottom_mm <= 0:
            return 0
        usable = self.depth_mm - tube_width_mm
        count = int(usable / self.horizontal_oc_bottom_mm)
        return max(0, count - 1)


# Spreadsheet cell definitions
SPREADSHEET_CELLS = {
    # Row: (CellName, DefaultValue, Unit, Description)
    "A1": ("Parameter", None, None, "Header"),
    "B1": ("Value", None, None, "Header"),
    "C1": ("Unit", None, None, "Header"),
    "D1": ("Notes", None, None, "Header"),

    # Overall Dimensions
    "A3": ("Length", 2438.4, "mm", "Overall box length"),
    "A4": ("Height", 812.8, "mm", "Overall box height (minus feet)"),
    "A5": ("Depth", 609.6, "mm", "Overall box depth"),
    "A6": ("FootHeight", 25.4, "mm", "Height of feet"),
    "A7": ("CasterReinforcement", False, "", "Add reinforcement for casters"),

    # Support Spacing
    "A9": ("VerticalOC_Front", 1219.2, "mm", "Vertical support spacing (front)"),
    "A10": ("VerticalOC_Back", 609.6, "mm", "Vertical support spacing (back)"),
    "A11": ("HorizontalOC_Top", 609.6, "mm", "Horizontal cross member spacing (top)"),
    "A12": ("HorizontalOC_Bottom", 609.6, "mm", "Horizontal cross member spacing (bottom)"),

    # Reference Mode
    "A14": ("DimensionReference", "exterior", "", "exterior | interior | centerline"),

    # Tab/Slot Settings
    "A16": ("TabsEnabled", True, "", "Generate tab/slot joints"),
    "A17": ("CapsEnabled", True, "", "Generate end caps"),
    "A18": ("TabDepthRatio", 0.6, "", "Tab depth as fraction of mating depth"),

    # Panel Settings
    "A20": ("PanelThickness_Sides", 1.5, "mm", "Side panel thickness (16ga)"),
    "A21": ("PanelThickness_Top", 2.0, "mm", "Top panel thickness (14ga)"),
    "A22": ("PanelOffset", 0.0, "mm", "Panel inset from frame edge"),

    # Hole Settings
    "A24": ("RivetHoleDiameter", 4.0, "mm", "Rivet hole diameter"),
    "A25": ("RivetSpacing", 150.0, "mm", "Rivet hole spacing"),

    # Profile Reference
    "A27": ("TubeProfile", "2x2x0.125_A36", "", "Tube profile name"),
}


def create_box_specs_spreadsheet(
    doc: "App.Document",
    name: str = "BoxSpecs",
    specs: Optional[BoxSpecsData] = None
) -> "App.DocumentObject":
    """
    Create a BoxSpecs spreadsheet in the FreeCAD document.

    Args:
        doc: FreeCAD document.
        name: Spreadsheet name.
        specs: Initial specifications (uses defaults if None).

    Returns:
        Spreadsheet object.
    """
    if not HAS_FREECAD:
        raise RuntimeError("FreeCAD not available")

    # Create spreadsheet
    sheet = doc.addObject("Spreadsheet::Sheet", name)

    # Set up headers
    sheet.set("A1", "Parameter")
    sheet.set("B1", "Value")
    sheet.set("C1", "Unit")
    sheet.set("D1", "Notes")

    # Use provided specs or defaults
    if specs is None:
        specs = BoxSpecsData()

    # Populate cells
    row = 3

    def set_row(param_name: str, value: Any, unit: str, notes: str):
        nonlocal row
        sheet.set(f"A{row}", param_name)
        if isinstance(value, bool):
            sheet.set(f"B{row}", "true" if value else "false")
        else:
            sheet.set(f"B{row}", str(value))
        sheet.set(f"C{row}", unit)
        sheet.set(f"D{row}", notes)
        # Set alias for the value cell
        sheet.setAlias(f"B{row}", param_name)
        row += 1

    # Overall Dimensions
    set_row("Length", specs.length_mm, "mm", "Overall box length")
    set_row("Height", specs.height_mm, "mm", "Overall box height (minus feet)")
    set_row("Depth", specs.depth_mm, "mm", "Overall box depth")
    set_row("FootHeight", specs.foot_height_mm, "mm", "Height of feet")
    set_row("CasterReinforcement", specs.caster_reinforcement, "", "Add caster reinforcement")

    row += 1  # Blank row

    # Support Spacing
    set_row("VerticalOC_Front", specs.vertical_oc_front_mm, "mm", "Vertical support OC (front)")
    set_row("VerticalOC_Back", specs.vertical_oc_back_mm, "mm", "Vertical support OC (back)")
    set_row("HorizontalOC_Top", specs.horizontal_oc_top_mm, "mm", "Horizontal cross OC (top)")
    set_row("HorizontalOC_Bottom", specs.horizontal_oc_bottom_mm, "mm", "Horizontal cross OC (bottom)")

    row += 1

    # Reference Mode
    set_row("DimensionReference", specs.dimension_reference.value, "", "exterior|interior|centerline")

    row += 1

    # Tab/Slot Settings
    set_row("TabsEnabled", specs.tabs_enabled, "", "Generate tab/slot joints")
    set_row("CapsEnabled", specs.caps_enabled, "", "Generate end caps")
    set_row("TabDepthRatio", specs.tab_depth_ratio, "", "Tab depth ratio (0.5-0.75)")

    row += 1

    # Panel Settings
    set_row("PanelThickness_Sides", specs.panel_thickness_sides_mm, "mm", "Side panel thickness")
    set_row("PanelThickness_Top", specs.panel_thickness_top_mm, "mm", "Top panel thickness")
    set_row("PanelOffset", specs.panel_offset_mm, "mm", "Panel inset from frame")

    row += 1

    # Hole Settings
    set_row("RivetHoleDiameter", specs.rivet_hole_diameter_mm, "mm", "Rivet hole diameter")
    set_row("RivetSpacing", specs.rivet_spacing_mm, "mm", "Rivet hole spacing")

    row += 1

    # Profile Reference
    set_row("TubeProfile", specs.tube_profile_name, "", "Tube profile name")

    doc.recompute()
    return sheet


def read_box_specs(sheet: "App.DocumentObject") -> BoxSpecsData:
    """
    Read box specifications from a spreadsheet.

    Args:
        sheet: BoxSpecs spreadsheet object.

    Returns:
        BoxSpecsData populated from spreadsheet values.
    """
    if not HAS_FREECAD:
        raise RuntimeError("FreeCAD not available")

    def get_float(alias: str, default: float = 0.0) -> float:
        try:
            return float(sheet.get(alias))
        except (ValueError, AttributeError):
            return default

    def get_bool(alias: str, default: bool = False) -> bool:
        try:
            val = sheet.get(alias)
            if isinstance(val, bool):
                return val
            return str(val).lower() in ("true", "1", "yes")
        except (ValueError, AttributeError):
            return default

    def get_str(alias: str, default: str = "") -> str:
        try:
            return str(sheet.get(alias))
        except (ValueError, AttributeError):
            return default

    dim_ref_str = get_str("DimensionReference", "exterior")
    try:
        dim_ref = DimensionReference(dim_ref_str)
    except ValueError:
        dim_ref = DimensionReference.EXTERIOR

    return BoxSpecsData(
        length_mm=get_float("Length", 2438.4),
        height_mm=get_float("Height", 812.8),
        depth_mm=get_float("Depth", 609.6),
        foot_height_mm=get_float("FootHeight", 25.4),
        caster_reinforcement=get_bool("CasterReinforcement", False),
        vertical_oc_front_mm=get_float("VerticalOC_Front", 1219.2),
        vertical_oc_back_mm=get_float("VerticalOC_Back", 609.6),
        horizontal_oc_top_mm=get_float("HorizontalOC_Top", 609.6),
        horizontal_oc_bottom_mm=get_float("HorizontalOC_Bottom", 609.6),
        dimension_reference=dim_ref,
        tabs_enabled=get_bool("TabsEnabled", True),
        caps_enabled=get_bool("CapsEnabled", True),
        tab_depth_ratio=get_float("TabDepthRatio", 0.6),
        panel_thickness_sides_mm=get_float("PanelThickness_Sides", 1.5),
        panel_thickness_top_mm=get_float("PanelThickness_Top", 2.0),
        panel_offset_mm=get_float("PanelOffset", 0.0),
        rivet_hole_diameter_mm=get_float("RivetHoleDiameter", 4.0),
        rivet_spacing_mm=get_float("RivetSpacing", 150.0),
        tube_profile_name=get_str("TubeProfile", "2x2x0.125_A36"),
    )
