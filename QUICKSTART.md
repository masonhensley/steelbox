# SteelBox Quick Start

## 1. Fork & Clone Quetzal

```bash
# On GitHub: Fork https://github.com/EdgarJRobles/quetzal

# Clone your fork
git clone https://github.com/YOUR_USERNAME/quetzal.git steelbox
cd steelbox
```

## 2. Add These Files

Copy the contents of this starter folder into your repo:

```
steelbox/
├── CLAUDE.md                              # ← Copy this
├── docs/
│   ├── equipment-box-workbench-plan.md    # ← Copy this
│   └── tab-slot-visual-guide.md           # ← Copy this
├── profiles/
│   └── custom/
│       └── EXAMPLE_2x2x125_Oshcut.json    # ← Example profile structure
└── setup-steelbox.sh                      # ← Copy this
```

## 3. Run Setup Script

```bash
chmod +x setup-steelbox.sh
./setup-steelbox.sh
```

This will:
- Rename quetzal → steelbox throughout the codebase
- Create the new directory structure
- Add `__init__.py` files

## 4. Link to FreeCAD

```bash
# Linux
ln -s $(pwd) ~/.local/share/FreeCAD/Mod/SteelBox

# macOS
ln -s $(pwd) ~/Library/Preferences/FreeCAD/Mod/SteelBox

# Windows (run as admin)
mklink /D "%APPDATA%\FreeCAD\Mod\SteelBox" "C:\path\to\steelbox"
```

## 5. Verify in FreeCAD

1. Open FreeCAD
2. Check View → Workbenches → SteelBox appears
3. Switch to SteelBox workbench
4. Verify no errors in Report View

## 6. Start Claude Code

```bash
cd steelbox
claude
```

Then:
```
> Read CLAUDE.md and docs/equipment-box-workbench-plan.md to understand the project.
> Let's start with Phase 1. First, explore the existing CFrame.py and fCmd.py 
> to understand how Quetzal creates frame members.
```

## Tips for Working with Claude Code

### Good first prompts:
- "Show me how Quetzal creates a beam from a profile"
- "What's the structure of the tablez/*.csv profile files?"
- "Create a minimal BoxSpecs spreadsheet template"

### Keep FreeCAD open in parallel:
Claude Code can't run the FreeCAD GUI, so you'll test manually:
```python
# In FreeCAD Python console:
import importlib
import core.box_generator as bg
importlib.reload(bg)  # Reload after code changes
bg.create_box(2000, 800, 600)
```

### Commit often:
```bash
git add -A
git commit -m "Phase 1: Basic frame generator working"
```

## File Reference

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Context for Claude Code - project overview, architecture, conventions |
| `docs/equipment-box-workbench-plan.md` | Detailed feature specs, data model, implementation phases |
| `docs/tab-slot-visual-guide.md` | ASCII diagrams of joint types, dimensions, tolerance system |
| `profiles/custom/EXAMPLE_*.json` | Example profile structure showing how tolerances are stored with each profile |
