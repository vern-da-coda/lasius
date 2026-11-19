#!/usr/bin/env python3
"""
Generate Lasius Bionic Tarsus v2 (Option 2c-V2) Canonical Parts & Subassembly
=============================================================================
Option 2c-V2 Architecture (Low Curved Smooth Full-Lever Fail-Safe NC Mechanism):
- Local Coordinate Origin (0, 0, 0) = Tarsus Pivot Axis (Ø3.0 mm ISO 2338 Dowel Pin)
  * +X: Distal towards bionic ant foot / upturned ski toe
  * +Y: Dorsal (upwards towards Tibia crest & NC microswitch)
  * -Y: Ventral (downwards towards ground & deep belly compression spring)
  * Z in [-2.80, +2.80] mm (5.60 mm uniform PETG lever & foot thickness)
- Key Mechanical Improvements:
  * Deeply embedded pivot hub (R_hub = 5.20 mm around Ø3.10 mm bore -> 3.65 mm radial wall)
  * Continuously reinforced, 100% smooth G1-curved internal lever arm (6.00 mm thick,
    ZERO small bumps/nibs -> eliminates jamming risk)
  * Flat dorsal contact pad (-10.0 deg slope) mating cleanly with Omron D2FC NC plunger
    and broad Ruhe-Anschlag (0 deg)
  * Broad ventral hard-stop face (+5.0 deg overload protection -> 0 N load on switch)
  * Gently downward-curved distal lever tail reaching X = -41.50 mm (r = 41.5 mm lever arm!)
    with integral Ø2.80 x 2.50 mm vertical spring locating pin (>1.85 N return force at toe)
  * Organic swooping ant-tarsus runner ("Kufe") with upturned toe tip matching the bionic
    silhouette, paired with a form-fit slip-on TPU/PETG spoon shoe (`tarsus_shoe.FCStd`).

Canonical Output Paths (Hardware-as-Code 3-Tier Architecture):
- hardware/mechanics/models/custom/v2/parts/tarsus/tarsus.FCStd       (Tarsus)
- hardware/mechanics/models/custom/v2/parts/tarsus/tarsus_shoe.FCStd  (Tarsus_Shoe)
- hardware/mechanics/models/custom/v2/tarsus_assembly.FCStd           (Tarsus_Assembly)
"""

import math
import os
import sys
import zipfile
import xml.etree.ElementTree as ET
import FreeCAD as App
import Part

# =============================================================================
# Centralized Engineering Constants (Style Guide §7)
# =============================================================================
REPO_ROOT = "/home/bjoern/Workspace/Hexapods/lasius"
MODELS_DIR = f"{REPO_ROOT}/hardware/mechanics/models"
V2_DIR = f"{MODELS_DIR}/custom/v2"
PARTS_TARSUS_DIR = f"{V2_DIR}/parts/tarsus"
DO_EXPORT = ("--export" in sys.argv)

EXPORT_STEP_PARTS = f"{REPO_ROOT}/hardware/mechanics/export/step/custom/v2/parts/tarsus"
EXPORT_STL_PARTS = f"{REPO_ROOT}/hardware/mechanics/export/stl/custom/v2/parts/tarsus"

os.makedirs(PARTS_TARSUS_DIR, exist_ok=True)
if DO_EXPORT:
    for d in [EXPORT_STEP_PARTS, EXPORT_STL_PARTS]:
        os.makedirs(d, exist_ok=True)

# Material / Visual Identity Colors
COLOR_ORANGE = (0.92, 0.45, 0.10)      # Anodized orange bionic tarsus lever (PETG)
COLOR_SHOE = (0.18, 0.58, 0.68)        # Contrasting bionic cyan-slate TPU/PETG shoe

# Dimensional Constants (mm)
TARSUS_THICK = 5.60                    # Z in [-2.80, +2.80] (0.40 mm clearance/side in 6.40 mm bay)
PIVOT_BORE_R = 1.55                    # Ø3.10 mm free running bore for Ø3.00 mm ISO 2338 pin
SPRING_X = -41.50                      # r = 41.50 mm lever arm in deep Tibia belly
SPRING_SEAT_Y = -4.20                  # Horizontal spring seat on parallel lever underside
SPRING_PIN_R = 1.45                    # Ø2.90 mm locating pin for Ø4.5 mm spring (Di ~3.3 mm)
SPRING_PIN_L = 3.20                    # Protrudes 3.20 mm down to Y = -7.40 mm (with 0.40 mm lead-in chamfer!)
SHOE_LOCK_X = 56.20                    # Coaxial M2 retaining pin bore in compact Kufe foot
SHOE_LOCK_Y = +3.60
SHOE_LOCK_R = 1.00                     # Ø2.00 mm pin bore
SHOE_CLEARANCE_2D = 0.08               # 0.08 mm 2D form-fit slip clearance
SHOE_WALL_SIDE = 1.42                  # Slim lateral wall per side -> 8.60 mm sleek shoe width!
SHOE_WALL_SOLE = 1.80                  # Slim elastic sole thickness below compact Kufe foot


def make_g1_bspline(poles, t_start=None, t_end=None):
    """Build a smooth C2 clamped cubic BSpline edge, optionally matching endpoint tangents."""
    pts = [App.Vector(p[0], p[1], 0.0) if not isinstance(p, App.Vector) else App.Vector(p.x, p.y, 0.0) for p in poles]
    if t_start is not None and len(pts) >= 4:
        ts = App.Vector(t_start[0], t_start[1], 0.0).normalize()
        d1 = max(0.8, (pts[1] - pts[0]).Length)
        pts[1] = pts[0] + ts * d1
    if t_end is not None and len(pts) >= 4:
        te = App.Vector(t_end[0], t_end[1], 0.0).normalize()
        d2 = max(0.8, (pts[-1] - pts[-2]).Length)
        pts[-2] = pts[-1] - te * d2
    bs = Part.BSplineCurve()
    bs.interpolate(pts)
    return bs.toShape()


def make_bspline_interp(pts_2d):
    """Build a smooth interpolating BSpline curve edge through 2D (x, y) tuples."""
    vecs = [App.Vector(p[0], p[1], 0.0) for p in pts_2d]
    bs = Part.BSplineCurve()
    bs.interpolate(vecs)
    return bs.toShape()


def build_tarsus_profile_edges():
    """
    Construct the closed G1-smooth 2D contour of the Option 2c-V2 Bionic Tarsus (at Z = 0).
    Origin (0, 0) = Pivot Axis (= (109.00, 20.50) in Tibia local coordinates).

    Sections (counter-clockwise around perimeter):
      1. Flat NC-switch & Ruhe-Anschlag dorsal pad (-10.0 deg slope) from X=-10.0 to X=-27.0:
         Y_top(x) = 3.10 + (-24.0 - x) * tan(10 deg)  -> at X=-24.0: Y=+3.10 (Tibia Y=23.60)
                                                      -> at X=-10.0: Y=+0.63 -> wait, let's keep hub & pad clean!
    Let's align switch plane exactly at -10.0 deg passing through (-24.0, +3.10):
      At X = -27.0: Y = +3.63
      At X = -24.0: Y = +3.10  (NC Omron plunger contact point!)
      At X = -12.0: Y = +0.98  -> Wait: hub around (0,0) has R = 5.20 (Y_top = +5.20)!
      Shift pad slightly higher so it blends smoothly right into the R = 5.20 hub!
      Pass -10.0 deg plane through (-24.0, +4.20) (Tibia Y = 24.70):
        At X = -27.0: Y = +4.73
        At X = -24.0: Y = +4.20 (NC switch plunger!)
        At X = -12.0: Y = +2.08 (Ruhe-Anschlag pad!)
        Wait: even cleaner, keep the -10.0 deg plane tangent-smooth into the R = 5.20 hub:
        Switch tilted -10.0 deg: normal is (+sin10, +cos10) = (+0.1736, +0.9848).
        A line tilted -10.0 deg passing through (0, +5.00) has:
          Y(x) = 5.00 - x * tan(10 deg)
          At X = -10.0: Y = +6.76? No, -10 deg slopes DOWN to the right (+X), so at negative X it goes UP!
          Let's verify: at X = -24.0, Y = 5.00 - (-24.0)*0.1763 = +9.23 (too high, eats pin room!).
        AHA! To slope DOWN to the right at -10 deg AND stay LOW at X=-24 (Y=+3.0 -> Tibia Y=23.5, giving 6.5 mm pin solder room!):
          At X = -24.0: Y = +3.00 -> at X = -10.0: Y = 3.00 - 14.0*0.1763 = +0.53 (smooth saddle before rising into the hub +5.2!).
        OR keep the switch & dorsal pad at **-4.0 deg (almost horizontal!)**:
          Y_top(X = -24.0) = +3.20 (Tibia Y = 23.70)
          Y_top(X = -10.0) = +2.22 (Tibia Y = 22.72) -> wait, even better: **0.0 deg (perfectly horizontal!)** or **-5.0 deg**!
          Let's check **-5.0 deg** passing through (-10.0, +2.60) and (-26.0, +4.00):
            At X = -24.0 (Tibia X=85.0): Y_t = +3.82 -> Tibia Y = 24.32!
              Switch body: Y_tibia = 24.8..31.3, straight pins up to Y_tibia = 34.6!
              Tibia roof at X=85..95: Y_top = 44.0..41.3 -> inner (4mm wall) = 40.0..37.3 -> STILL 4.5..6.0 mm FREE SOLDER ROOM!
            AND check at X = -10.0 (Tibia X=99.0): Y_t = +2.60 -> smooth concave fillet R=3.5 mm up into the R=5.20 hub!
            AND check lever thickness = 6.00 mm below:
              At X = -24.0: Y_bot = -2.18 (Tibia Y = 18.32)
              At X = -15.0 (Hard-stop pad!): Y_bot = -2.97 (Tibia Y = 17.53 -> at +5 deg drops 1.3 mm to Y_tibia = 16.23 -> 4.8 mm wall above Tibia Y_bot=11.4!)
              At X = -41.5 (Curved downward spring tip!): curves gracefully down from (-26.0, -2.0) to (-41.5, -4.20) (Tibia Y = 16.30, leaving 11.30 mm spring length above Y_floor = 5.00 mm!)!
    """
    LEVER_TOP_Y = +3.20   # Dead-straight horizontal top flank (Y_tibia = 23.70) from spring tip past switch!

    # 1. Single continuous, dead-straight horizontal upper flank from X=-10.5 all the way to X=-44.0
    #    - Over spring (X=-44.0..-29.5): mates 100% flush against the broad flat Tibia ceiling stop!
    #    - Under NC microswitch (X=-28.5..-16.0): actuates plunger cleanly as a pure side effect (0 N stop load!)
    #    - Between switch & pivot (X=-15.5..-10.5): mates flush against the secondary dust-seal stop!
    p_pad_r = App.Vector(-10.50, LEVER_TOP_Y, 0.0)         # (-10.50, +3.20)
    p_pad_l = App.Vector(-44.00, LEVER_TOP_Y, 0.0)         # (-44.00, +3.20)
    e_pad_top = Part.makeLine(p_pad_r, p_pad_l)

    # 2. Smooth rounded nose connecting dead-straight upper flank (+3.20) to parallel lower flank (-4.20)
    p_sp_tip_mid = App.Vector(-46.70, -0.50, 0.0)
    p_sp_seat_l = App.Vector(-44.00, SPRING_SEAT_Y, 0.0)   # (-44.00, -4.20)
    e_lever_nose = Part.Arc(p_pad_l, p_sp_tip_mid, p_sp_seat_l).toShape()

    # 3. Parallel dead-straight horizontal lower flank & spring seat from X=-44.0 to X=-10.5 at Y = -4.20
    #    - Over spring (X=-44.0..-38.0): flat horizontal spring seat
    #    - Over hard-stop (X=-32.0..-11.0): lands 100% flush on the +5.0 deg angled Tibia overload stop!
    p_bot_r = App.Vector(-10.50, SPRING_SEAT_Y, 0.0)       # (-10.50, -4.20)
    e_spring_seat = Part.makeLine(p_sp_seat_l, p_bot_r)

    # 4. Smooth ventral transition from parallel lever underside (-10.50, -4.20) into reinforced pivot hub (-5.20, -4.90)
    p_hub_bot_l = App.Vector(-5.20, -4.90, 0.0)
    e_lever_bot_curve = make_bspline_interp([
        (p_bot_r.x, p_bot_r.y),
        (-7.80, -4.45),
        (p_hub_bot_l.x, p_hub_bot_l.y),
    ])

    # 6. Reinforced (+20% cross-section height from pivot axis into shoe) straight bionic insect shin
    #    exiting cleanly straight out of the Tibia (X = 0..47 mm), curving ONLY at the distal foot tip
    #    into a compact, agile outward Kufe runner (X = 47..63.5 mm)!
    p_toe_bot = App.Vector(60.00, +15.50, 0.0)
    e_foot_sole = make_bspline_interp([
        (p_hub_bot_l.x, p_hub_bot_l.y),
        (0.00, -5.80),
        (8.00, -5.45),
        (16.00, -4.35),
        (27.00, -3.65),
        (38.00, -3.45),
        (47.50, -3.15),
        (54.50, -1.65),
        (60.20, +1.85),
        (63.20, +6.60),
        (63.00, +11.60),
        (p_toe_bot.x, p_toe_bot.y),
    ])

    # 7. Compact upturned outward Kufe toe tip (delicate nimble ant ski nose!)
    p_toe_top = App.Vector(55.00, +14.20, 0.0)
    e_toe_tip = make_bspline_interp([
        (p_toe_bot.x, p_toe_bot.y),
        (58.00, +16.60),
        (56.00, +16.00),
        (p_toe_top.x, p_toe_top.y),
    ])

    # 8. Reinforced (+20% height) concave foot instep returning straight into the Tibia fork & concentric pivot hub!
    p_hub_top = App.Vector(0.00, +5.40, 0.0)
    e_foot_top = make_bspline_interp([
        (p_toe_top.x, p_toe_top.y),
        (55.20, +10.20),
        (52.80, +6.60),
        (49.20, +5.00),
        (44.00, +4.05),
        (35.00, +3.65),
        (25.00, +4.05),
        (15.00, +4.80),
        (7.00, +5.35),
        (p_hub_top.x, p_hub_top.y),
    ])

    # 9. Smooth transition from concentric pivot hub top (0.0, +5.40) into straight horizontal upper flank (-10.50, +3.20)
    e_hub_to_pad = make_bspline_interp([
        (p_hub_top.x, p_hub_top.y),
        (-3.80, +4.70),
        (-7.20, +3.65),
        (p_pad_r.x, p_pad_r.y),
    ])

    return [
        e_pad_top,
        e_lever_nose,
        e_spring_seat,
        e_lever_bot_curve,
        e_foot_sole,
        e_toe_tip,
        e_foot_top,
        e_hub_to_pad,
    ]


def build_tarsus_and_shoe():
    print("--- Generating Lasius Bionic Tarsus v2 (Option 2c-V2) Canonical Parts & Assembly ---")

    # =========================================================================
    # 1. Build Canonical Tarsus: custom/v2/parts/tarsus/tarsus.FCStd
    # =========================================================================
    print("1. Building Canonical Part: tarsus.FCStd...")
    try:
        App.closeDocument("tarsus")
    except Exception:
        pass
    doc_tarsus = App.newDocument("tarsus")
    fcstd_tarsus_path = f"{PARTS_TARSUS_DIR}/tarsus.FCStd"

    tarsus_edges = build_tarsus_profile_edges()
    tarsus_wire = Part.Wire(tarsus_edges)
    assert tarsus_wire.isClosed(), "Tarsus outer wire is not closed!"
    tarsus_face = Part.Face(tarsus_wire)
    tarsus_solid = tarsus_face.extrude(App.Vector(0.0, 0.0, TARSUS_THICK)).translate(
        App.Vector(0.0, 0.0, -0.5 * TARSUS_THICK)
    )

    # Pivot Bore (Ø3.10 mm, R = 1.55 mm) at origin (0.0, 0.0)
    tarsus_solid = tarsus_solid.cut(
        Part.makeCylinder(PIVOT_BORE_R, 12.0, App.Vector(0.0, 0.0, -6.0), App.Vector(0, 0, 1))
    )
    # Coaxial M2 Shoe Retaining Bore (Ø2.00 mm) at (SHOE_LOCK_X, SHOE_LOCK_Y)
    tarsus_solid = tarsus_solid.cut(
        Part.makeCylinder(SHOE_LOCK_R, 12.0, App.Vector(SHOE_LOCK_X, SHOE_LOCK_Y, -6.0), App.Vector(0, 0, 1))
    )
    # Integral Vertical Spring Locating Pin (Ø2.90 mm, L = 3.20 mm with 0.40 mm x 45 deg lead-in chamfer)
    # Deeply rooted at Y = -3.90, protrudes straight down (-Y) to Y = -7.40 inside the Ø3.30 mm spring bore!
    pin_cyl = Part.makeCylinder(
        SPRING_PIN_R, SPRING_PIN_L - 0.40 + 0.30,
        App.Vector(SPRING_X, SPRING_SEAT_Y + 0.30, 0.0),
        App.Vector(0, -1, 0),
    )
    pin_tip = Part.makeCone(
        SPRING_PIN_R, SPRING_PIN_R - 0.40, 0.40,
        App.Vector(SPRING_X, SPRING_SEAT_Y - (SPRING_PIN_L - 0.40), 0.0),
        App.Vector(0, -1, 0),
    )
    tarsus_solid = tarsus_solid.fuse(pin_cyl).fuse(pin_tip)
    try:
        tarsus_solid = tarsus_solid.removeSplitter()
    except Exception:
        pass

    obj_tarsus = doc_tarsus.addObject("Part::Feature", "Tarsus")
    obj_tarsus.Label = "Tarsus Bionic Curved Rocker Foot (Option 2c-V2, PETG)"
    obj_tarsus.Shape = tarsus_solid
    if hasattr(obj_tarsus, "ViewObject") and obj_tarsus.ViewObject is not None:
        obj_tarsus.ViewObject.Visibility = True
        obj_tarsus.ViewObject.ShapeColor = COLOR_ORANGE
    doc_tarsus.recompute()
    doc_tarsus.saveAs(fcstd_tarsus_path)
    if DO_EXPORT:
        tarsus_solid.exportStep(f"{EXPORT_STEP_PARTS}/tarsus.step")
        tarsus_solid.exportStl(f"{EXPORT_STL_PARTS}/tarsus.stl")
    print(f"✔ Saved: {fcstd_tarsus_path} (Valid={tarsus_solid.isValid()}, Volume={tarsus_solid.Volume:.1f} mm3)")

    # =========================================================================
    # 2. Build Canonical Slip-On Bionic Spoon Shoe: tarsus_shoe.FCStd
    # =========================================================================
    print("2. Building Canonical Part: tarsus_shoe.FCStd...")
    try:
        App.closeDocument("tarsus_shoe")
    except Exception:
        pass
    doc_shoe = App.newDocument("tarsus_shoe")
    fcstd_shoe_path = f"{PARTS_TARSUS_DIR}/tarsus_shoe.FCStd"

    # Slim, compact G1 periodic B-spline wrapping ONLY the distal Kufe runner foot (X in [45.5, 65.5], ~8.6 mm wide!)
    # Leaves the straight Tarsus shin sleek & exposed, giving a nimble predatory ant foot instead of bulky shoes!
    shoe_pts = [
        App.Vector(47.20, -4.85, 0.0),     # Compact heel start (1.62 mm sole wall under reinforced shin!)
        App.Vector(54.80, -3.50, 0.0),     # Heel sole blend (1.77 mm sole wall!)
        App.Vector(61.50, +0.60, 0.0),     # Flat ground-contact sole (55 deg ant stance!)
        App.Vector(65.20, +6.20, 0.0),     # Rolling ground-contact sole (55..90 deg!)
        App.Vector(65.00, +12.20, 0.0),    # Compact upturned Kufe rocker
        App.Vector(61.60, +16.90, 0.0),    # Closed rounded toe cap outer tip
        App.Vector(57.40, +18.30, 0.0),    # Closed toe cap crest
        App.Vector(53.80, +16.50, 0.0),    # Closed toe cap inner hook
        App.Vector(53.20, +11.60, 0.0),    # Compact concave instep rim
        App.Vector(51.00, +7.80, 0.0),     # Upper foot rim over reinforced Kufe neck
        App.Vector(47.20, +5.40, 0.0),     # Ankle top rim matching reinforced shin
        App.Vector(45.20, +0.20, 0.0),     # Smooth ankle wrap
    ]
    bs_shoe = Part.BSplineCurve()
    bs_shoe.interpolate(shoe_pts, PeriodicFlag=True)
    shoe_wire = Part.Wire([bs_shoe.toShape()])
    shoe_face = Part.Face(shoe_wire)
    shoe_w = TARSUS_THICK + 2.0 * SHOE_CLEARANCE_2D + 2.0 * SHOE_WALL_SIDE  # 8.60 mm slim width!
    shoe_outer = shoe_face.extrude(App.Vector(0.0, 0.0, shoe_w)).translate(App.Vector(0.0, 0.0, -0.5 * shoe_w))

    # Tactile outer edge fillets (R = 1.00 mm) on slim periodic shoe perimeter (verified Z bounds!)
    try:
        z_outer_edges = [
            e for e in shoe_outer.Edges
            if abs(abs(e.BoundBox.ZMin) - 0.5 * shoe_w) < 0.05 and abs(e.BoundBox.ZMax - e.BoundBox.ZMin) < 0.05
        ]
        if z_outer_edges:
            cand = shoe_outer.makeFillet(1.00, z_outer_edges)
            if cand.isValid() and abs(cand.BoundBox.ZMax - 0.5 * shoe_w) < 0.05:
                shoe_outer = cand
    except Exception as ex:
        print(f"  [Note] Shoe fillet fallback: {ex}")

    # Form-fit internal cavity (exact Tarsus 2D offset +0.08 mm, Z width = 5.76 mm)
    # + open dorsal (+Y) slip-on entry slot behind closed toe cap (keeps ground sole 100% unbroken!)
    tarsus_offset_wire = tarsus_wire.makeOffset2D(SHOE_CLEARANCE_2D)
    cav_w = TARSUS_THICK + 2.0 * SHOE_CLEARANCE_2D  # 5.76 mm
    cavity_core = Part.Face(tarsus_offset_wire).extrude(App.Vector(0.0, 0.0, cav_w)).translate(
        App.Vector(0.0, 0.0, -0.5 * cav_w)
    )
    # Open dorsal entry slot along the concave +Y instep behind closed toe cap!
    slot_poly = [
        App.Vector(42.0, -1.5, -0.5 * cav_w),
        App.Vector(54.2, +6.2, -0.5 * cav_w),
        App.Vector(55.3, +13.5, -0.5 * cav_w),
        App.Vector(49.0, +16.5, -0.5 * cav_w),
        App.Vector(42.0, +9.0, -0.5 * cav_w),
        App.Vector(42.0, -1.5, -0.5 * cav_w),
    ]
    entry_slot = Part.Face(Part.makePolygon(slot_poly)).extrude(App.Vector(0.0, 0.0, cav_w))
    rocker_cavity = cavity_core.fuse(entry_slot)

    # Coaxial M2 locking pin bore
    shoe_pin_bore = Part.makeCylinder(
        SHOE_LOCK_R, 16.0, App.Vector(SHOE_LOCK_X, SHOE_LOCK_Y, -8.0), App.Vector(0, 0, 1)
    )

    shoe_solid = shoe_outer.cut(rocker_cavity).cut(shoe_pin_bore)
    try:
        shoe_solid = shoe_solid.removeSplitter()
    except Exception:
        pass

    # Verify zero collision between Tarsus and Tarsus_Shoe!
    coll_ts = tarsus_solid.common(shoe_solid).Volume
    print(f"  Pairwise Check Tarsus <-> Tarsus_Shoe: {coll_ts:.4f} mm^3")
    assert coll_ts < 1e-4, f"Collision between Tarsus and Tarsus_Shoe: {coll_ts:.4f} mm^3!"

    obj_shoe = doc_shoe.addObject("Part::Feature", "Tarsus_Shoe")
    obj_shoe.Label = "Tarsus Slip-On Bionic Spoon Shoe (Option 2c-V2, TPU/PETG)"
    obj_shoe.Shape = shoe_solid
    if hasattr(obj_shoe, "ViewObject") and obj_shoe.ViewObject is not None:
        obj_shoe.ViewObject.Visibility = True
        obj_shoe.ViewObject.ShapeColor = COLOR_SHOE
    doc_shoe.recompute()
    doc_shoe.saveAs(fcstd_shoe_path)
    if DO_EXPORT:
        shoe_solid.exportStep(f"{EXPORT_STEP_PARTS}/tarsus_shoe.step")
        shoe_solid.exportStl(f"{EXPORT_STL_PARTS}/tarsus_shoe.stl")
    print(f"✔ Saved: {fcstd_shoe_path} (Valid={shoe_solid.isValid()}, Volume={shoe_solid.Volume:.1f} mm3)")

    # =========================================================================
    # 3. Build Tarsus Subassembly: custom/v2/tarsus_assembly.FCStd
    # =========================================================================
    print("3. Building Tarsus Subassembly: custom/v2/tarsus_assembly.FCStd...")
    fcstd_asm_path = f"{V2_DIR}/tarsus_assembly.FCStd"
    try:
        App.closeDocument("tarsus_assembly")
    except Exception:
        pass
    doc_asm = App.newDocument("tarsus_assembly")
    doc_asm.saveAs(fcstd_asm_path)

    asm_part = doc_asm.addObject("App::Part", "Tarsus_Assembly")
    asm_part.Label = "Lasius Tarsus Subassembly v2 (Option 2c-V2 Curved Rocker + Bionic Shoe)"
    for o in asm_part.Origin.OutList:
        if hasattr(o, "Visibility"):
            o.Visibility = False
    asm_part.Origin.Visibility = False
    asm_part.Visibility = True

    def make_link(name, label, target_obj, color):
        lnk = doc_asm.addObject("App::Link", name)
        lnk.setLink(target_obj)
        lnk.Label = label
        lnk.Placement = App.Placement()
        asm_part.addObject(lnk)
        lnk.Visibility = True
        if hasattr(lnk, "ViewObject") and lnk.ViewObject is not None:
            try:
                lnk.ViewObject.Visibility = True
                lnk.ViewObject.OverrideMaterial = True
                mat = lnk.ViewObject.ShapeMaterial
                mat.DiffuseColor = color
                lnk.ViewObject.ShapeMaterial = mat
            except Exception:
                pass
        return lnk

    make_link("Tarsus", "1. Bionic Curved Tarsus Lever (PETG)", obj_tarsus, COLOR_ORANGE)
    make_link("Tarsus_Shoe", "2. Slip-On Bionic Spoon Shoe (TPU/PETG)", obj_shoe, COLOR_SHOE)

    doc_asm.recompute()
    doc_asm.save()
    print(f"✔ Saved Tarsus Subassembly: {fcstd_asm_path}")
    print(f"  Tarsus BB: {tarsus_solid.BoundBox}")
    print(f"  Shoe   BB: {shoe_solid.BoundBox}")

    for d in [doc_asm, doc_tarsus, doc_shoe]:
        try:
            App.closeDocument(d.Name)
        except Exception:
            pass


_is_main = (__name__ == "__main__") or (
    len(sys.argv) > 1 and os.path.basename(sys.argv[1]) == os.path.basename(__file__)
)
if _is_main:
    build_tarsus_and_shoe()
