# SteelBox Workbench

A [FreeCAD](https://freecad.org) workbench for designing parametric tube steel cabinet frames with self-fixturing tab/slot joinery.

SteelBox is a fork of [Quetzal](https://github.com/EdgarJRobles/quetzal) (itself a fork of Dodo), extended with features for laser-cut equipment enclosure design.

## Features

### Core Capabilities (from Quetzal/Dodo)
- Frame and beam structure creation
- Pipe routing and fittings
- Cut list generation for BOM

### SteelBox Additions
- **Parametric Box Generator** - Spreadsheet-driven cabinet dimensions
- **Tab/Slot Joinery System** - Self-fixturing joints for easy welding without jigs
- **Tube Profile Management** - DXF import with manufacturer-specific tolerances
- **Corner Relief Options** - Dogbone or radius relief for laser cutting

## Installation

### Manual Installation

Find your FreeCAD modules directory:

```python
# Run in FreeCAD Python console
App.getUserAppDataDir()
```

Common locations:
- Linux: `/home/user/.local/share/FreeCAD/Mod/`
- macOS: `/Users/user/Library/Preferences/FreeCAD/Mod/`
- Windows: `C:\Users\user\AppData\Roaming\FreeCAD\Mod\`

Clone the repository:

```shell
cd /path/to/FreeCAD/Mod/
git clone https://github.com/gwaihir-io/steelbox SteelBox
```

Restart FreeCAD after installation.

## Quick Start

Generate a basic cabinet frame in FreeCAD's Python console:

```python
import sys
sys.path.insert(0, '/path/to/steelbox')

from core import create_jointed_box_frame, BoxSpecsData

doc = App.newDocument("Cabinet")
specs = BoxSpecsData(
    length_mm=1500,
    height_mm=800,
    depth_mm=600,
    foot_height_mm=100,
)
parts, generator = create_jointed_box_frame(doc, specs)
```

## Requirements

- FreeCAD 1.0+
- Python 3.10+

## Documentation

See `CLAUDE.md` for detailed architecture and implementation notes.

Original Dodo/Quetzal documentation: https://wiki.freecad.org/Dodo_Workbench

## License

LGPL-3.0-or-later (inherited from Quetzal/Dodo)

## Credits

- Original Dodo workbench by [@oddtopus](https://github.com/oddtopus)
- Quetzal fork by [@EdgarJRobles](https://github.com/EdgarJRobles)
- SteelBox extensions by Gwaihir
