# Tab/Slot Joint System - Visual Reference

## 1. Basic T-Joint (Vertical meets Horizontal)

```
SIDE VIEW (looking at joint from the side)

         ║ Vertical Member
         ║
    ┌────╨────┐  <- Slot cut into vertical
    │  ┌───┐  │
    │  │TAB│  │  <- Tab from horizontal extends into slot
════╪══╧═══╧══╪════ Horizontal Member
    │         │
    └─────────┘
         ║
         ║
```

## 2. Tab Placement Strategy (Your Spec: Top/Bottom, Not Sides)

```
CROSS-SECTION VIEW (looking down the length of horizontal tube)

                    Vertical Member
                         │
     ┌───────────────────┼───────────────────┐
     │                   │                   │
     │    ╔═══════╗      │      ╔═══════╗    │  <- Tabs on TOP face
     │    ║  TAB  ║      │      ║  TAB  ║    │
═════╪════╩═══════╩══════╪══════╩═══════╩════╪═════
     │                   │                   │
     │                   │                   │     Horizontal Member
     │                   │                   │     (square tube)
═════╪═══════════════════╪═══════════════════╪═════
     │    ╔═══════╗      │      ╔═══════╗    │  <- Tabs on BOTTOM face
     │    ║  TAB  ║      │      ║  TAB  ║    │
     └────╩═══════╩──────┼──────╩═══════╩────┘
                         │
                    
BENEFITS:
- Tabs align with gravity during assembly (parts sit on each other)
- Welder has access to top and bottom surfaces
- Sides remain clear for panel attachment
```

## 3. Slot Detail with Corner Relief

```
SLOT OPTIONS (plan view of slot cut into tube face)

A) SQUARE SLOT (accurate but stress risers)
   ┌─────────────┐
   │             │
   │             │  <- Sharp corners can crack under load
   └─────────────┘

B) DOGBONE SLOT (CNC router compatible, very accurate)
   ○─────────────○
   │             │
   │             │  <- Circles at corners allow square tab to seat
   ○─────────────○

C) RADIUS SLOT (laser-friendly, reduced stress)
   ╭─────────────╮
   │             │
   │             │  <- Rounded corners, tab corners must also be rounded
   ╰─────────────╯

RECOMMENDED FOR LASER: Option C with 1.5mm corner radius
```

## 4. Tab Dimensions

```
TAB PROPORTIONS

     ╔══════════════════════════════════════════════╗
     ║                                              ║
     ║   Tab Width = Tube Face Width - (2 × 2mm)    ║
     ║   (leaves welding clearance on sides)        ║
     ║                                              ║
     ╚══════════════════════════════════════════════╝
           │                               │
           │<──── Tab Width (44.8mm) ─────>│
           │                               │
           
     ┌─────┴───────────────────────────────┴─────┐
     │                                           │
     │<───────── Tube Width (50.8mm) ───────────>│
     │                                           │
     
     
TAB DEPTH (how far tab extends into slot):

                    ┌─────────────────┐
                    │                 │
                    │  Mating Member  │
                    │   (slot here)   │  <- Slot depth = tab depth
    ════════════════╪═════════════════╪═══════════════
                    │     ║     ║     │
                    │     ║     ║     │  <- Tab Depth = 0.5-0.75 × wall thickness
                    │     ╠═════╣     │     Example: 3.175mm wall → 1.9-2.4mm tab
    ════════════════╪═════╩═════╩═════╪═══════════════
                    │                 │
                    │  This Member    │
                    │ (tabs extend)   │
                    └─────────────────┘
```

## 5. End Cap System (with interference avoidance)

```
THE PROBLEM: Cap tabs would collide with member tabs

    Member Tab Locations (on horizontal member)
              ↓           ↓
         ┌────╪───────────╪────┐
         │    ║           ║    │   Horizontal member end
         │    ║           ║    │
    ═════╪════╩═══════════╩════╪═════
         │                     │
    ═════╪═════════════════════╪═════
         │    ║           ║    │
         │    ║           ║    │
         └────╪───────────╪────┘
              ↑           ↑
         If cap has tabs here, they hit member tabs!


THE SOLUTION: Middle notch in tube slots for cap clearance

    TUBE END (with slots and notches)
         ┌───────────────────────┐
         │  █notch█   █notch█   │  <- Notches allow cap tabs to sit
         │  │     │   │     │   │     without hitting member tabs
    ═════╪──┘     └───┘     └──╪═════
         │                     │
    ═════╪──┐     ┌───┐     ┌──╪═════
         │  │     │   │     │   │
         │  █notch█   █notch█   │
         └───────────────────────┘
                   ↑
              Cap slots here


    CAP (tabs positioned between notches)
         ┌───────────────────────┐
         │                       │
    ╔════╡  ╔═══╗       ╔═══╗   ╞════╗
    ║    │  ║   ║       ║   ║   │    ║
    ║    │  ║TAB║       ║TAB║   │    ║  <- Cap tabs fit in notched areas
    ║    │  ║   ║       ║   ║   │    ║
    ╚════╡  ╚═══╝       ╚═══╝   ╞════╝
         │                       │
         └───────────────────────┘


    ASSEMBLED (cap sits in tube end)
         ┌─────────┬───────┬─────────┐
         │         │ CAP   │         │
         │  member │ fits  │ member  │
         │  tab    │ here  │ tab     │
    ═════╪═════════╪═══════╪═════════╪═════
         │         │       │         │
         │         │cap tab│         │
    ═════╪═════════╪═══════╪═════════╪═════
         │         │       │         │
         └─────────┴───────┴─────────┘
```

## 6. Frame Corner Detail (Where 3 Members Meet)

```
TOP VIEW OF CORNER

    Vertical (going up)
         │
         │      Back Rail
    ═════╪════════════════════>
         │ 
         │
         │
    ═════╪═══════════════════════
         │                      
         │                      
         │     Side Rail
         ├────────────────────>
         │
         │
         │
    
    
3D ISOMETRIC OF CORNER JOINT:

              ↑ Vertical
              │
              │    ╔═══╗ Tab into vertical
         ─────┼────╨───╨────────  Back horizontal
              │
              │
              ╠════╗ Tab into vertical
              ║    ║
         ─────╬────╬────────────  Side horizontal  
              ║    ║
              ╚════╝
              │
              │

KEY: Tabs from both horizontals enter vertical member at 90° to each other
     Slots in vertical must not overlap!
```

## 7. Hole Pattern for Rivet/Riv-nut Attachment

```
TUBE FACE WITH HOLES (for panel attachment)

    ┌──────────────────────────────────────────────────────┐
    │                                                      │
    │    ○        ○        ○        ○        ○        ○    │  <- Holes at 150mm OC
    │                                                      │
    │   12mm    150mm    150mm    150mm    150mm    12mm   │  <- Edge offset
    │  offset                                     offset   │
    │                                                      │
    └──────────────────────────────────────────────────────┘
    
    
HOLE POSITIONING ON PANELS (must match frame!)

    ┌──────────────────────────────────────────────────────┐
    │                                                      │
    │    ●────────●────────●────────●────────●────────●    │
    │    │        │        │        │        │        │    │
    │    │        │        │        │        │        │    │
    │    │        │        │        │        │        │    │  Panel
    │    │        │        │        │        │        │    │
    │    │        │        │        │        │        │    │
    │    │        │        │        │        │        │    │
    │    ●────────●────────●────────●────────●────────●    │
    │                                                      │
    └──────────────────────────────────────────────────────┘
        ↑        ↑        ↑        ↑        ↑        ↑
    Panel holes align with frame holes for rivet attachment
```

## 8. Dimension Reference Options

```
EXTERIOR DIMENSIONS (most common for equipment boxes)

    ←───────────── 96" ──────────────→
    ┌─────────────────────────────────┐
    │█                               █│  <- Tube wall
    │█                               █│
    │█                               █│
    │█                               █│
    └─────────────────────────────────┘
    
    96" = Outside edge to outside edge


INTERIOR DIMENSIONS (for specific internal clearance)

    ←───────────── 96" ──────────────→
      ┌─────────────────────────────┐
    █│                               │█  <- Tube wall excluded
    █│                               │█
    █│                               │█
    █│                               │█
      └─────────────────────────────┘
    
    96" = Inside edge to inside edge


CENTERLINE DIMENSIONS (for structural engineering)

          ←──────── 96" ────────→
    ┌─────────┐           ┌─────────┐
    │    ┼    │           │    ┼    │  <- Centerlines
    │    │    │           │    │    │
    │    │    │           │    │    │
    │    │    │           │    │    │
    └────┴────┘           └────┴────┘
    
    96" = Center of tube to center of tube
```

## 9. Assembly Sequence Suggestion

```
RECOMMENDED ORDER:

1. Lay out bottom frame flat
   ┌─────┬─────┬─────┬─────┐
   │     │     │     │     │
   └─────┴─────┴─────┴─────┘

2. Insert vertical corners (tabs down into bottom)
       │           │
   ┌───┼───┬───────┼───┐
   │   │   │       │   │
   └───┴───┴───────┴───┘
       │           │

3. Add top frame (tabs up into verticals)
   ┌─────┬─────┬─────┬─────┐
   │  │  │     │  │  │     │
       │           │
   │  │  │     │  │  │     │
   └──┴──┴─────┴──┴──┴─────┘

4. Add intermediate verticals
5. Add horizontal cross members
6. Weld all joints
7. Install end caps
8. Attach panels

TACK WELD first, check square, then full weld
```

## 10. Tolerance System (Per-Profile)

```
TOLERANCES ARE PROPERTIES OF EACH TUBE PROFILE

When you import a DXF or create a profile, you input tolerances
from your manufacturing partner (Oshcut, SendCutSend, etc.)

┌─────────────────────────────────────────────────────────────────┐
│  PROFILE: 2x2x0.125_A36_Oshcut                                  │
├─────────────────────────────────────────────────────────────────┤
│  GEOMETRY (from DXF)                                            │
│    OuterWidth:  50.8mm                                          │
│    OuterHeight: 50.8mm                                          │
│    WallThickness: 3.175mm                                       │
│    CornerRadius: 2.5mm                                          │
├─────────────────────────────────────────────────────────────────┤
│  TOLERANCES (from Oshcut for this profile)                      │
│    SlotClearance:      0.10mm   (added to slot width)           │
│    TabUndersize:       0.05mm   (removed from tab width)        │
│    KerfCompensation:   0.15mm   (half kerf width)               │
│    CornerReliefRadius: 1.5mm    (for radiused slot corners)     │
│    FinishAllowance:    0.0mm    (per side, for powder coat)     │
├─────────────────────────────────────────────────────────────────┤
│  METADATA                                                       │
│    Manufacturer: Oshcut                                         │
│    Notes: "Fiber laser, tolerances verified Jan 2024"           │
└─────────────────────────────────────────────────────────────────┘


FORMULAS (use this profile's tolerance values):

  SlotWidth = WallThickness + SlotClearance + KerfCompensation
            = 3.175        + 0.10          + 0.15
            = 3.425mm

  TabWidth  = WallThickness - TabUndersize - KerfCompensation
            = 3.175        - 0.05         - 0.15
            = 2.975mm

  TotalGap  = SlotWidth - TabWidth
            = 3.425 - 2.975 = 0.45mm clearance


WHY PER-PROFILE?

  Different profiles from different manufacturers need different
  tolerances. Your Oshcut 2x2x1/8 might need different values than
  their 3x3x3/16, and definitely different than SendCutSend's.

  ┌────────────────────┬─────────┬──────────┬────────┐
  │ Profile            │ SlotClr │ TabUnder │ Kerf   │
  ├────────────────────┼─────────┼──────────┼────────┤
  │ 2x2x1/8 Oshcut     │ 0.10    │ 0.05     │ 0.15   │
  │ 3x3x3/16 Oshcut    │ 0.12    │ 0.06     │ 0.18   │  <- thicker = different
  │ 2x2x1/8 SendCutSend│ 0.08    │ 0.04     │ 0.12   │  <- different mfg
  │ 2x2x1/4 LocalShop  │ 0.25    │ 0.10     │ 0.40   │  <- plasma cut
  └────────────────────┴─────────┴──────────┴────────┘

  Ask your manufacturer what values to use for each profile!


DATUM REFERENCE STRATEGY

Pick ONE corner as the datum (reference point)
All dimensions measure FROM this corner

                ★ DATUM CORNER
                │
                │
    ────────────┼─────────────────────────────→ X
                │
                │
                │
                │
                ↓ Y

Benefits:
- Errors don't accumulate across the frame
- All parts reference same origin
- Easier to check squareness
```
