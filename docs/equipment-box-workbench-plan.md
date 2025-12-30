# Equipment Box Workbench Plan
## Fork of Quetzal for Parametric Metal Cabinet Design

---

## 1. Project Overview

**Name Suggestion:** `SteelBox` or `CabinetForge` (fork of Quetzal)

**Core Purpose:** Parametric generation of laser-cut tube steel frames with tab/slot joinery, end caps, sheet metal panels, and rivet/riv-nut hole patterns for welded equipment enclosures.

---

## 2. Architecture Decision: Fork vs. New Workbench

### Recommendation: **Fork Quetzal, but significantly restructure**

**Why fork Quetzal:**
- Existing FreeCAD 1.0 compatibility fixes
- Profile management infrastructure (CSV tables, custom sketch profiles)
- Frame-line concept (beams along paths)
- Cut list generation already exists
- LGPL-3.0 license allows forking

**What to keep from Quetzal:**
- `fCmd.py` - Frame command utilities
- `CFrame.py` - Core frame structure classes
- `tablez/` - CSV profile table system
- `cut_list/` - BOM/cut list generation
- Basic UI dialog infrastructure

**What to replace/extend:**
- Profile system → Support DXF import for tube profiles
- Frame generation → Parametric box generator with OC support
- Add entirely new: Tab/slot joinery system
- Add entirely new: Cap generation with interference checking
- Add entirely new: Sheet metal panel system
- Add entirely new: Hole pattern distribution
- Export system → STEP per-part + BOM spreadsheet

---

## 3. Data Model / Core Classes

```
EquipmentBox (FeaturePython)
├── BoxSpecs (PropertyGroup - links to Spreadsheet)
│   ├── TubeProfile (Link to Sketch or DXF)
│   ├── Length, Height, Depth
│   ├── FootHeight, CasterReinforcement
│   ├── VerticalOC_Front, VerticalOC_Back
│   ├── HorizontalOC_Top, HorizontalOC_Bottom
│   ├── DimensionReference (Exterior/Interior/CenterLine)
│   └── MaterialThickness
│
├── FrameMembers[] (Collection)
│   ├── TubeMember (extends Arch.Structure)
│   │   ├── TabFeatures[] (notches at intersections)
│   │   ├── HolePatterns[] (rivet/riv-nut)
│   │   └── CapSlots[] (for end caps)
│   │
│   └── EndCap (new FeaturePython)
│       ├── Profile (derived from tube interior)
│       ├── Tabs[] (with middle notch for clearance)
│       └── ParentMember (link)
│
├── SheetPanels[] (Collection)
│   ├── Panel (extends Part::Feature)
│   │   ├── Face (which box face)
│   │   ├── Thickness
│   │   ├── Offset (from frame edge)
│   │   ├── HolePatterns[] (matching frame)
│   │   └── BendFeatures[] (if applicable)
│   │
│   └── PanelAttachment
│       ├── FastenerType (rivet, riv-nut, bolt)
│       └── MatchingFrameHoles (link)
│
└── ExportConfig
    ├── OutputDirectory
    ├── FileFormat (STEP, DXF)
    └── BOMFormat (CSV, XLSX)
```

---

## 4. Feature Specifications

### 4.1 Tube Profile System

```yaml
Profile Input:
  - DXF Import: Parse closed polyline, store as FreeCAD Sketch
  - Library Selection: Dropdown from saved profiles
  - Custom Sketch: Allow user-drawn profile in Sketcher

Profile Properties (ALL stored with profile):
  Geometry:
    - Outer dimensions (from DXF or manual)
    - Wall thickness
    - Corner radii
    - Orientation reference (which edge is "top" for tab placement)
  
  Tolerances (from manufacturer for THIS specific profile):
    - SlotClearance: mm added to slot width
    - TabUndersize: mm removed from tab width
    - KerfCompensation: mm (half kerf width)
    - CornerReliefRadius: mm for slot corner relief
    - FinishAllowance: mm per side (if powder coating)
  
  Metadata:
    - Name / Description
    - Material (A36, A500, etc.)
    - Manufacturer (Oshcut, SendCutSend, etc.)
    - Notes (date verified, any quirks)

Profile Import Workflow:
  1. User uploads DXF of tube cross-section
  2. System extracts geometry (outer dims, wall thickness)
  3. User inputs tolerance values from their manufacturer
  4. Profile saved with all properties bundled together

Storage:
  - profiles/custom/*.json (user profiles with embedded tolerances)
  - Each profile is self-contained - no external tolerance lookups
```

### 4.2 Frame Generator

```yaml
Parameters (Spreadsheet-driven):
  Length: 8ft (2438.4mm)
  Height: 32in (812.8mm) - foot height
  Depth: 24in (609.6mm)
  FootHeight: 1in (25.4mm)
  CasterReinforcement: true/false
  
  VerticalOC_Front: 4ft (1219.2mm)
  VerticalOC_Back: 2ft (609.6mm)
  HorizontalOC_Top: 2ft (609.6mm)
  HorizontalOC_Bottom: 2ft (609.6mm)
  
  DimensionReference: Exterior | Interior | CenterLine
  TabsEnabled: true/false
  CapsEnabled: true/false

Generated Members:
  - 4 corner verticals
  - N vertical supports front (calculated from OC)
  - N vertical supports back (calculated from OC)
  - 4 horizontal rails (top front/back, bottom front/back)
  - N horizontal cross members top (calculated from OC)
  - N horizontal cross members bottom (calculated from OC)
  - 4 depth rails (connecting front to back at corners)
  - Optional: Foot plates + reinforcement tubes
```

### 4.3 Tab/Slot Joinery System

```yaml
Design Principles (from research):
  - Tab length: 0.5-0.75 × mating part depth
  - Corner relief: Dogbone or radius (configurable)
  - Tab placement: Top/bottom faces of horizontal members
                   (not sides - per your spec)

Tolerance System (PER-PROFILE PROPERTIES):
  # Tolerances are stored WITH each tube profile definition
  # User inputs values from their manufacturing partner (Oshcut, etc.)
  # Different profiles can have different tolerances
  
  When importing/creating a tube profile, user specifies:
    SlotClearance:       # mm added to slot width
    TabUndersize:        # mm removed from tab width
    KerfCompensation:    # mm half-kerf width
    CornerReliefRadius:  # mm for radiused slot corners
    FinishAllowance:     # mm per side (if powder coating)
  
  Formulas (use profile's values):
    SlotWidth = WallThickness + SlotClearance + KerfCompensation
    TabWidth  = WallThickness - TabUndersize - KerfCompensation
    TotalGap  = SlotClearance + TabUndersize + (2 × KerfCompensation)
  
  Example profile with tolerances:
    Name: "2x2x0.125_A36_Oshcut"
    DXF: uploaded
    WallThickness: 3.175mm
    SlotClearance: 0.10mm      # Per Oshcut recommendation
    TabUndersize: 0.05mm       # Per Oshcut recommendation
    KerfCompensation: 0.15mm   # Per Oshcut recommendation
    Manufacturer: "Oshcut"
    Notes: "Fiber laser, verified Jan 2024"

Joint Types:
  1. T-Joint (vertical meets horizontal)
     - Slot in vertical member
     - Tab extends from horizontal member into slot
     
  2. Corner Joint (two horizontals meeting)
     - Miter cut with tab/slot alignment
     
  3. Cross Joint (crossing members)
     - Through-slot in one, tabs on other

Tab Parameters:
  - TabWidth: Configurable (default: tube width - 2mm per side)
  - TabDepth: 0.5-0.75 × wall thickness
  - CornerRelief: Dogbone | Radius | Square
  - CornerRadius: From profile's tolerance settings

Interference Checking:
  - Detect when tab positions would conflict
  - Auto-offset or warn user
  - Special handling for cap tabs (middle notch)
```

### 4.4 End Cap System

```yaml
Cap Generation:
  - Auto-detect open tube ends
  - Generate flat cap matching tube interior profile
  - Add tabs around perimeter (4 or more based on tube size)
  
Cap Tab Design:
  - Tabs extend outward from cap edges
  - Tube ends get matching slots
  - Middle notch in tube slots to clear existing member tabs
  
  Example (square tube):
  ┌─────────────────────┐
  │  ╔═══╗     ╔═══╗    │  <- Cap with tabs
  │  ║TAB║     ║TAB║    │
  ╞══╩═══╩═════╩═══╩════╡
  │                     │  <- Tube end with slots
  │  ▼notch▼   ▼notch▼  │     (notches avoid member tabs)
  └─────────────────────┘

Cap Parameters:
  - CapThickness: Same as tube wall or configurable
  - TabCount: Auto (based on perimeter) or manual
  - TabWidth: Percentage of available edge
  - NotchWidth: Width of existing member tabs + clearance
```

### 4.5 Hole Pattern System

```yaml
Distribution Methods:
  1. By Count: "12 holes evenly distributed"
  2. By Distance: "Every 50mm" or "Every 12 inches"
  3. Manual: Click to place

Hole Types:
  - Rivet: Simple through-hole
  - Riv-nut: Clearance hole for threaded insert
  - Custom: User-specified diameter

UI Workflow:
  1. Select face(s) on tube members
  2. Choose distribution method
  3. Set hole diameter and type
  4. Preview and confirm
  
  Holes auto-propagate to matching sheet metal panels

Hole Parameters:
  - HoleDiameter: 4.0mm (rivet) | 6.5mm (M5 riv-nut) | custom
  - EdgeOffset: Minimum distance from tube edges
  - PatternType: Linear | Grid | Custom
  - Spacing: By count or distance
```

### 4.6 Sheet Metal Panel System

```yaml
Panel Generation:
  - Select box face (Top, Bottom, Front, Back, Left, Right)
  - Auto-calculate panel dimensions from frame
  - Apply offset from frame edges
  
Panel Types:
  - Fixed Panel: Welded or riveted in place
  - Door Panel: Hinged, needs hinge hole pattern
  - Removable Panel: Riv-nut mounting
  
Panel Parameters:
  - Thickness: Per-panel (e.g., 16ga sides, 14ga top)
  - Offset: Inset from frame outer edge
  - HoleMatching: Link to frame hole patterns
  - BendAllowance: For bent flanges (optional)

Cycle Through Options:
  - UI shows current panel config per face
  - Next/Previous buttons to cycle materials/thickness
  - "Apply to all" option
```

### 4.7 Parametric Spreadsheet Integration

```yaml
Spreadsheet Structure (BoxSpecs):
  | Parameter              | Value    | Unit | Notes                    |
  |------------------------|----------|------|--------------------------|
  | Length                 | 2438.4   | mm   |                          |
  | Height                 | 812.8    | mm   |                          |
  | Depth                  | 609.6    | mm   |                          |
  | FootHeight             | 25.4     | mm   |                          |
  | VerticalOC_Front       | 1219.2   | mm   |                          |
  | VerticalOC_Back        | 609.6    | mm   |                          |
  | HorizontalOC_Top       | 609.6    | mm   |                          |
  | HorizontalOC_Bottom    | 609.6    | mm   |                          |
  | PanelThickness_Sides   | 1.5      | mm   |                          |
  | PanelThickness_Top     | 2.0      | mm   |                          |
  | RivetHoleDiameter      | 4.0      | mm   |                          |
  | RivetSpacing           | 150      | mm   |                          |
  | TabDepthRatio          | 0.6      | -    | × mating member depth    |

Profile-Derived Values (read from selected tube profile):
  | Parameter              | Source                                       |
  |------------------------|----------------------------------------------|
  | TubeWidth              | From profile geometry                        |
  | TubeHeight             | From profile geometry                        |
  | WallThickness          | From profile geometry                        |
  | SlotClearance          | From profile tolerances (mfg-specified)      |
  | TabUndersize           | From profile tolerances (mfg-specified)      |
  | KerfCompensation       | From profile tolerances (mfg-specified)      |
  | CornerReliefRadius     | From profile tolerances (mfg-specified)      |
  | FinishAllowance        | From profile tolerances (mfg-specified)      |

Computed Values (formulas use profile tolerances):
  | Parameter              | Formula                                      |
  |------------------------|----------------------------------------------|
  | SlotWidth              | =WallThickness+SlotClearance+KerfCompensation|
  | TabWidth               | =WallThickness-TabUndersize-KerfCompensation |
  | TotalFitGap            | =SlotWidth - TabWidth                        |

Note: Tolerances are locked to the tube profile. To change tolerances,
edit the profile definition (not the spreadsheet). This ensures 
consistency - same profile always produces same tolerances.
```

---

## 5. Export System

### 5.1 STEP Export (Per Unique Part)

```yaml
Export Logic:
  1. Group identical parts by geometry hash
  2. Export one STEP per unique geometry
  3. Name format: PartType_Dimensions_Material.step
  
Examples:
  - TubeMember_2000x50x50x3.175_A36.step
  - EndCap_50x50_A36.step
  - Panel_Front_1500x800x1.5_A36.step
  
Organization:
  /export/
    /tubes/
    /caps/
    /panels/
    /hardware/
```

### 5.2 DXF Export (For Laser Cutter)

```yaml
DXF Contents:
  - Tube profiles with tab cutouts and hole patterns
  - Flat caps with tabs
  - Flat panel profiles with holes
  - Nested layout option (future enhancement)

Format:
  - 2D projection of each part
  - Layer organization (cut lines, engrave, etc.)
```

### 5.3 BOM Spreadsheet

```yaml
BOM Columns:
  | Part Number | Description          | Material | Qty | Length/Area | Weight |
  |-------------|----------------------|----------|-----|-------------|--------|
  | TB-001      | Vertical Corner 2x2  | A36      | 4   | 812.8mm     | 2.1kg  |
  | TB-002      | Horizontal Rail 2x2  | A36      | 4   | 2438.4mm    | 6.3kg  |
  | CAP-001     | End Cap 2x2          | A36      | 8   | -           | 0.1kg  |
  | PNL-001     | Front Panel 16ga     | A36      | 1   | 1.2m²       | 14.2kg |
  
Additional Sheets:
  - Cut List (grouped by material/thickness)
  - Hardware List (rivets, riv-nuts, hinges)
  - Assembly Order suggestion
```

---

## 6. Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)
- [ ] Fork Quetzal, rename to SteelBox
- [ ] Set up new package structure
- [ ] Implement DXF profile import
- [ ] Create BoxSpecs spreadsheet template
- [ ] Basic frame generator (no tabs yet)

### Phase 2: Tab/Slot System (Week 3-4)
- [ ] Implement T-joint tab/slot generation
- [ ] Add corner relief options
- [ ] Interference detection
- [ ] Tab parameter UI

### Phase 3: Caps & Holes (Week 5-6)
- [ ] End cap generation with smart tabs
- [ ] Hole pattern distribution system
- [ ] Face selection UI
- [ ] Hole-to-panel propagation

### Phase 4: Sheet Metal Panels (Week 7-8)
- [ ] Panel generator per face
- [ ] Thickness per panel
- [ ] Offset/inset controls
- [ ] Panel cycling UI

### Phase 5: Export & Polish (Week 9-10)
- [ ] STEP export per unique part
- [ ] DXF export for laser
- [ ] BOM spreadsheet generation
- [ ] Documentation & examples

---

## 7. File Structure

```
steelbox/
├── __init__.py
├── Init.py
├── InitGui.py
├── package.xml
│
├── core/
│   ├── __init__.py
│   ├── box_generator.py      # Main parametric box logic
│   ├── tube_member.py        # Extended from Quetzal's CFrame
│   ├── end_cap.py            # Cap generation
│   ├── sheet_panel.py        # Panel generation
│   └── spreadsheet_link.py   # Parameter binding
│
├── joinery/
│   ├── __init__.py
│   ├── tab_slot.py           # Tab/slot generation
│   ├── joint_detector.py     # Find intersections
│   ├── interference.py       # Collision detection
│   └── corner_relief.py      # Dogbone/radius generation
│
├── holes/
│   ├── __init__.py
│   ├── pattern_generator.py  # Hole distribution
│   ├── hole_types.py         # Rivet, riv-nut specs
│   └── face_selector.py      # UI for face selection
│
├── profiles/
│   ├── __init__.py
│   ├── dxf_importer.py       # DXF → Sketch conversion
│   ├── profile_library.py    # CSV-based library
│   └── tables/
│       ├── tube_steel.csv
│       └── custom/
│
├── export/
│   ├── __init__.py
│   ├── step_exporter.py      # Per-part STEP export
│   ├── dxf_exporter.py       # Laser-ready DXF
│   ├── bom_generator.py      # Spreadsheet BOM
│   └── part_hasher.py        # Identify unique parts
│
├── ui/
│   ├── __init__.py
│   ├── dialogs/
│   │   ├── box_wizard.ui     # Main wizard
│   │   ├── tab_settings.ui
│   │   ├── hole_pattern.ui
│   │   └── panel_config.ui
│   ├── commands.py           # FreeCAD commands
│   └── icons/
│
├── templates/
│   ├── BoxSpecs.FCStd        # Template with spreadsheet
│   └── example_cabinet.FCStd
│
└── tests/
    ├── test_tab_slot.py
    ├── test_interference.py
    └── test_export.py
```

---

## 8. Things You May Have Missed

### 8.1 Kerf Compensation
- Laser cutting removes material (kerf width ~0.1-0.3mm)
- Tab/slot dimensions need kerf adjustment
- **Add:** `KerfCompensation` parameter (default 0.15mm)
- Apply to slot width: `SlotWidth = MaterialThickness + SlotClearance + Kerf`

### 8.2 Corner Relief Strategy
Your tabs on top/bottom of tubes will conflict at corners where tubes meet. Need:
- **Dogbone relief** at slot corners for square tabs
- Or **radius corners** on tabs (easier to weld, less stress concentration)
- Configurable per joint type

### 8.3 Weld Access Considerations
- Tabs that extend fully into slots can be plug-welded
- Consider adding **weld access holes** near joints
- Option for **chamfered tab ends** (45°) for better weld penetration

### 8.4 Miter Joints for Non-90° Angles
- Your spec assumes rectangular box, but future frames might have angles
- Consider abstracting joint angle calculation
- Miter + tab/slot is complex but doable

### 8.5 Tube Orientation Consistency
- Critical that all tubes have consistent "top" face
- Tab placement depends on knowing which face is top
- **Add:** Profile orientation indicator in DXF import

### 8.6 Material Thickness Tolerance Stack-up
- Multiple tabs/slots can accumulate tolerance errors
- Design for "reference surface" assembly strategy
- One corner is datum, everything measures from there

### 8.7 Panel Attachment Method
You mentioned rivet/riv-nut but didn't specify:
- **Inset panels** (flush with frame exterior)
- **Overlay panels** (sit on frame face)
- **Flanged panels** (bent edge sits inside frame)

Suggest adding `PanelMountStyle` parameter.

### 8.8 Powder Coating / Painting Considerations
- Tight tab/slot fits may not work after powder coating
- **Add:** `FinishAllowance` parameter (0.05-0.1mm per side)
- Apply when `FinishType = PowderCoat`

### 8.9 Weight Calculation
- BOM should include weight estimates
- Need material density lookup
- Useful for shipping quotes and structural analysis

### 8.10 Assembly Sequence
- Generate suggested assembly order
- Which parts go together first
- Critical for complex frames with many interlocking tabs

### 8.11 Labeling / Part Marking
- Option to add part numbers as engraved text
- Position labels to survive welding
- Include in DXF export on separate layer

---

## 9. UI Workflow (Wizard-Style)

```
┌─────────────────────────────────────────────────────────────┐
│  SteelBox Cabinet Wizard                              [X]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Step 1: Profile Selection                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ○ Import DXF    ○ Library    ○ Custom Sketch        │   │
│  │                                                     │   │
│  │ Profile: [2x2x0.125 Square Tube ▼]                  │   │
│  │                                                     │   │
│  │ Preview: ┌──┐   Wall: 3.175mm                       │   │
│  │          │  │   Outer: 50.8 x 50.8mm                │   │
│  │          └──┘   Inner: 44.45 x 44.45mm              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Step 2: Overall Dimensions                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Length: [96    ] in  ○ Exterior ○ Interior ○ CL     │   │
│  │ Height: [32    ] in  (minus feet)                   │   │
│  │ Depth:  [24    ] in                                 │   │
│  │                                                     │   │
│  │ Foot Height: [1     ] in                            │   │
│  │ □ Caster Reinforcement Plates                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Step 3: Support Spacing                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Vertical Supports:                                  │   │
│  │   Front OC: [48   ] in    Count: 1                  │   │
│  │   Back OC:  [24   ] in    Count: 3                  │   │
│  │                                                     │   │
│  │ Horizontal Supports:                                │   │
│  │   Top OC:    [24   ] in   Count: 3                  │   │
│  │   Bottom OC: [24   ] in   Count: 3                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [< Back]                              [Next >] [Generate]  │
└─────────────────────────────────────────────────────────────┘
```

(Additional wizard pages for Tabs, Caps, Holes, Panels, Export)

---

## 10. Dependencies

```yaml
Required:
  - FreeCAD 1.0+
  - Python 3.10+
  - ezdxf (DXF parsing)
  - openpyxl (Excel BOM export)

Optional:
  - numpy (geometry calculations)
  - shapely (2D boolean operations for tab/slot)

FreeCAD Modules Used:
  - Part
  - Sketcher
  - Spreadsheet
  - TechDraw (for 2D DXF export)
  - Arch (Structure base class)
```

---

## 11. Testing Strategy

```yaml
Unit Tests:
  - Tab/slot dimension calculations
  - Interference detection
  - OC → member count conversion
  - DXF import parsing

Integration Tests:
  - Generate box, verify all members exist
  - Tab/slot positions match intersections
  - Export produces valid STEP files
  - BOM quantities match model

Visual Tests:
  - Sample cabinet renders
  - Tab closeup screenshots
  - Assembly sequence animations
```

---

## 12. Future Enhancements

1. **Nesting Optimizer** - Arrange flat parts on sheet for minimal waste
2. **Structural Analysis** - Basic FEA to check frame strength
3. **Door Hardware** - Hinges, latches, handles
4. **Cable Management** - Knockout holes, grommet placement
5. **Ventilation** - Louver patterns, fan mount holes
6. **Multi-Section Cabinets** - Vertical/horizontal dividers
7. **Import from Sketch** - Draw frame layout in 2D, extrude to 3D

---

## Summary

This workbench will be a powerful, parametric tool for designing laser-cut tube steel cabinets with self-fixturing joinery. The key differentiators from base Quetzal are:

1. **Purpose-built for cabinets** - Not general framing
2. **Tab/slot first** - Every joint designed for easy welding
3. **Smart caps** - Auto-generated with interference avoidance
4. **Sheet metal integration** - Panels match frame holes
5. **Production-ready export** - STEP, DXF, BOM in one click

Start with Phase 1 (core infrastructure) and iterate. The spreadsheet-driven approach means you can adjust designs without touching code after initial development.
