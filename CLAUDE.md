# CLAUDE.md - SteelBox Workbench

> Fork of Quetzal (itself a fork of Dodo) for parametric equipment cabinet design with tab/slot joinery.

## Project Goal

Build a FreeCAD workbench that generates laser-cut tube steel frames for equipment enclosures. Key differentiator: **self-fixturing tab/slot joints** at every intersection for easy welding without jigs.

## Quick Reference

```
FreeCAD version: 1.0+
Python: 3.10+
License: LGPL-3.0 (inherited from Quetzal)
Original repo: https://github.com/EdgarJRobles/quetzal
```

## Architecture Overview

This is a **FreeCAD Workbench**. Key files:
- `Init.py` - Loaded when FreeCAD starts (register workbench)
- `InitGui.py` - GUI initialization (toolbars, menus, commands)
- `package.xml` - Addon manager metadata

Quetzal patterns to preserve:
- `CFrame.py` - Frame/beam structure classes (extend, don't replace)
- `fCmd.py` - Frame command utilities
- `tablez/*.csv` - Profile library tables (CSV with semicolon delimiter)
- `cut_list/` - BOM generation

## Core Features to Implement

### 1. Parametric Box Generator
Spreadsheet-driven dimensions:
- Length, Height, Depth
- Vertical/Horizontal support spacing (OC = on-center)
- Foot height, caster reinforcement option
- Dimension reference: Exterior | Interior | CenterLine

### 2. Tab/Slot Joinery System
- Tabs on TOP/BOTTOM faces of tubes (not sides)
- **Tolerances are properties of each tube profile** (set when importing DXF)
- Tab depth = 0.5-0.75 × mating member depth
- Corner relief: Dogbone or 1.5mm radius

### Tolerance System (Per-Profile Properties)
Tolerances are stored WITH each tube profile, not as separate presets.
When user imports a DXF or creates a profile, they input tolerances from their manufacturer.

```python
# Tube profile includes tolerance properties
tube_profile = {
    "name": "2x2x0.125_A36_Oshcut",
    "dxf_path": "/profiles/custom/2x2x125.dxf",
    
    # Geometry (from DXF or manual)
    "outer_width": 50.8,
    "outer_height": 50.8,
    "wall_thickness": 3.175,
    "corner_radius": 2.5,
    
    # Tolerances (from manufacturer for THIS profile)
    "slot_clearance": 0.10,      # mm added to slot width
    "tab_undersize": 0.05,       # mm removed from tab width  
    "kerf_compensation": 0.15,   # mm (half kerf width)
    "corner_relief_radius": 1.5, # mm for radiused slot corners
    "finish_allowance": 0.0,     # mm per side (powder coat)
    
    # Metadata
    "manufacturer": "Oshcut",
    "notes": "Fiber laser, verified 2024-01"
}

# Formulas use profile's tolerance values:
# Slot width = wall_thickness + slot_clearance + kerf_compensation
# Tab width  = wall_thickness - tab_undersize - kerf_compensation
```

Store profiles in:
- `profiles/custom/` - User DXF imports with tolerance metadata
- `profiles/library/` - Pre-built profiles (optional)

### 3. End Caps
- Auto-generate for open tube ends
- Tabs extend from cap perimeter
- **Critical**: Middle notch in tube slots to avoid interference with member tabs

### 4. Hole Patterns
- Distribution by count OR by distance
- Types: rivet, riv-nut, custom diameter
- Auto-propagate to matching sheet metal panels

### 5. Sheet Metal Panels
- Per-face thickness settings
- Offset from frame edge
- Hole patterns match frame

### 6. Export
- STEP per unique part (deduplicated by geometry hash)
- DXF for laser cutter (2D profiles)
- BOM spreadsheet (CSV/XLSX)

## File Structure Target

```
steelbox/
├── Init.py
├── InitGui.py
├── package.xml
├── CLAUDE.md              # This file
│
├── core/
│   ├── box_generator.py   # Main parametric logic
│   ├── tube_member.py     # Extends CFrame
│   ├── end_cap.py
│   ├── sheet_panel.py
│   └── spreadsheet_link.py
│
├── joinery/
│   ├── tab_slot.py        # Tab/slot generation
│   ├── joint_detector.py  # Find tube intersections
│   ├── interference.py    # Collision detection
│   └── corner_relief.py   # Dogbone/radius
│
├── holes/
│   ├── pattern_generator.py
│   └── hole_types.py
│
├── profiles/
│   ├── dxf_importer.py    # DXF → FreeCAD Sketch
│   └── tables/
│       └── tube_steel.csv
│
├── export/
│   ├── step_exporter.py
│   ├── dxf_exporter.py
│   └── bom_generator.py
│
└── ui/
    ├── commands.py        # FreeCAD command classes
    └── dialogs/
```

## Implementation Phases

### Phase 1: Foundation (Start Here)
- [ ] Rename workbench (quetzal → steelbox everywhere)
- [ ] Update `package.xml` metadata
- [ ] Create new directory structure
- [ ] Implement DXF profile import using `ezdxf`
- [ ] Create BoxSpecs spreadsheet template
- [ ] Basic frame generator (corners + rails, no tabs yet)

### Phase 2: Tab/Slot System
- [ ] Joint detection (find where tubes intersect)
- [ ] Tab geometry generation
- [ ] Slot cutting (boolean subtract from tube)
- [ ] Corner relief options
- [ ] Interference checking

### Phase 3: Caps & Holes
- [ ] End cap generation
- [ ] Cap tab placement with notch avoidance
- [ ] Hole pattern distribution
- [ ] Face selection UI

### Phase 4: Panels
- [ ] Panel generator per box face
- [ ] Thickness per panel
- [ ] Hole matching to frame

### Phase 5: Export
- [ ] STEP export with deduplication
- [ ] DXF flat patterns
- [ ] BOM spreadsheet

## FreeCAD API Notes

```python
# Creating a FeaturePython object
obj = doc.addObject("Part::FeaturePython", "MyObject")
MyObjectClass(obj)  # Attach your class
ViewProviderClass(obj.ViewObject)  # Attach view provider

# Linking to spreadsheet cell
obj.setExpression("Length", "BoxSpecs.Length")

# Boolean cut (for slots)
cut = obj.Shape.cut(slot_shape)

# Get face from shape
for face in obj.Shape.Faces:
    if face.normalAt(0, 0).z > 0.9:  # Top face
        # do something
```

## Key Quetzal Code to Study First

Before implementing new features, understand these:

1. **`CFrame.py`** - How beams are created and positioned
2. **`fCmd.py`** - `placeTheBeam()`, `rotateStruct()` utilities
3. **`tablez/`** - CSV format for profile libraries
4. **`fFeatures.py`** - FeaturePython class patterns
5. **`cut_list/`** - How BOM is generated

## Testing

FreeCAD GUI cannot run headless easily. Testing approach:
- Unit test geometry calculations (tab dimensions, intersections)
- Manual testing in FreeCAD for visual/integration
- Create example files in `examples/` folder

```python
# To run in FreeCAD Python console for testing:
import sys
sys.path.insert(0, '/path/to/steelbox')
from core import box_generator
box_generator.create_box(length=2000, height=800, depth=600)
```

## Common Pitfalls

1. **Sketcher vs Part** - Profiles should be Sketcher objects for parametric updates, not just Part shapes

2. **Topological naming** - FreeCAD faces can renumber after edits. Use named geometry where possible.

3. **Expression syntax** - Spreadsheet references use `<<SpreadsheetName>>.CellName` or just `SpreadsheetName.CellName`

4. **Recompute order** - Call `doc.recompute()` after changes, but avoid calling it excessively

5. **Units** - FreeCAD uses mm internally. Convert user input (inches) early.

## Dependencies to Add

```
ezdxf>=1.0      # DXF parsing
openpyxl>=3.0   # Excel BOM export
```

Add to workbench or document in README for manual install.

## Naming Conventions

- Classes: `PascalCase` (e.g., `TubeMember`, `TabSlotJoint`)
- Functions: `snake_case` (e.g., `create_box`, `generate_tabs`)
- FreeCAD objects: `PascalCase` with underscores (e.g., `Tube_Member_001`)
- Spreadsheet cells: `PascalCase` (e.g., `BoxLength`, `TubeWidth`)

## Commands to Start

```bash
# After forking and cloning:

# Rename references
grep -r "quetzal" --include="*.py" -l | xargs sed -i 's/quetzal/steelbox/g'
grep -r "Quetzal" --include="*.py" -l | xargs sed -i 's/Quetzal/SteelBox/g'

# Update package.xml
# (edit manually - name, description, maintainer)

# Create new directories
mkdir -p core joinery holes profiles/tables export ui/dialogs

# Test load in FreeCAD
# Copy/symlink to ~/.local/share/FreeCAD/Mod/SteelBox
```

## Reference Documents

See `docs/equipment-box-workbench-plan.md` for:
- Detailed feature specifications
- Data model diagram
- Tab/slot dimension formulas
- Visual diagrams of joint types
- Things to watch for (kerf, tolerance stack-up, etc.)

## Questions to Ask the User

If unclear during implementation:
1. Default tube profile dimensions?
2. Preferred corner relief style (dogbone vs radius)?
3. Standard hole sizes for rivets/riv-nuts?
4. Output file naming convention?
5. Support for non-rectangular frames (future)?
