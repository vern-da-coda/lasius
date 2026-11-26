#!/usr/bin/env python3
"""
Generate Lasius Hexapod Monolithic Draped Canopy v2 FreeCAD Model
(hardware/mechanics/models/custom/v2/parts/chassis/chassis_canopy.FCStd)
========================================================================
Design Concept (Einteilige Magnet-Haube mit integrierter Kaminbelüftung):
  1. Single-Piece Monolithic Shell (t = 1.50 mm):
     - Drapes smoothly and continuously over the centered Raspberry Pi 4 and
       the dual rear Hobbywing BEC 10A V2-Car UBECs (rising to Z = 81.50 mm at
       the apex) and flows organically down onto Body_Top (Z = 55.30 mm).
     - Eliminates the redundant two-piece service cover / rebate seam for higher
       shell stiffness, zero rattle, and clean tool-free magnetic removal as one
       unit (neodymium magnets onto the 4 outward-offset pillars at ±48, ±36 mm).
  2. 100% Flush Cut to Body_Top Perimeter:
     - All overhangs around the entire robot perimeter are trimmed flush with
       the exact outer silhouette of body_top.FCStd
       (X in [-132.0, +135.0 mm], Y in [-88.5, +88.5 mm]).
  3. Integrated Bionic Thermal Convection Louvers:
     - 5x 45-degree forward-pointing rounded '>>>' chevron louvers directly over
       the Raspberry Pi 4 BCM2711 SoC (X in [-15.0, +15.0 mm], matching Femur Cover).
     - 2x 4 rounded exhaust slots directly over both rear Hobbywing 10A UBEC
       anodized aluminum heatsinks (X in [-88.0, -64.0 mm], Y = ±21.5 mm).
"""

import math
import os
import sys
import FreeCAD as App
import Part

print("--- Generating Lasius Monolithic Draped Canopy v2 (FreeCAD 1.1+) ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts/chassis"
body_top_path = f"{repo_root}/hardware/mechanics/models/custom/v1/parts/body_top.FCStd"
fcstd_canopy_path = f"{models_dir}/chassis_canopy.FCStd"

os.makedirs(models_dir, exist_ok=True)


def make_filleted_wire(x_min, x_max, y_min, y_max, r, z):
    """Constructs a smooth 8-edge G1-continuous filleted rectangular wire at height Z."""
    dx = x_max - x_min
    dy = y_max - y_min
    r = min(r, dx / 2.0 - 0.1, dy / 2.0 - 0.1)
    pts = [
        App.Vector(x_max - r, y_max, z),
        App.Vector(x_min + r, y_max, z),
        App.Vector(x_min, y_max - r, z),
        App.Vector(x_min, y_min + r, z),
        App.Vector(x_min + r, y_min, z),
        App.Vector(x_max - r, y_min, z),
        App.Vector(x_max, y_min + r, z),
        App.Vector(x_max, y_max - r, z),
    ]
    edges = [
        Part.makeLine(pts[0], pts[1]),
        Part.Edge(Part.ArcOfCircle(pts[1], App.Vector(x_min + r * (1 - 1 / math.sqrt(2)), y_max - r * (1 - 1 / math.sqrt(2)), z), pts[2])),
        Part.makeLine(pts[2], pts[3]),
        Part.Edge(Part.ArcOfCircle(pts[3], App.Vector(x_min + r * (1 - 1 / math.sqrt(2)), y_min + r * (1 - 1 / math.sqrt(2)), z), pts[4])),
        Part.makeLine(pts[4], pts[5]),
        Part.Edge(Part.ArcOfCircle(pts[5], App.Vector(x_max - r * (1 - 1 / math.sqrt(2)), y_min + r * (1 - 1 / math.sqrt(2)), z), pts[6])),
        Part.makeLine(pts[6], pts[7]),
        Part.Edge(Part.ArcOfCircle(pts[7], App.Vector(x_max - r * (1 - 1 / math.sqrt(2)), y_max - r * (1 - 1 / math.sqrt(2)), z), pts[0])),
    ]
    return Part.Wire(edges)


def make_chevron_slot(cx, cy, arm_len, width, angle_deg=45.0, z_min=75.0, z_max=88.0):
    """Construct a 45-degree forward-pointing '>>>' chevron ventilation slot with rounded pill ends."""
    rad = math.radians(angle_deg)
    dx = arm_len * math.cos(rad)
    dy = arm_len * math.sin(rad)
    p_apex = App.Vector(cx, cy, z_min)
    p_top = App.Vector(cx - dx, cy + dy, z_min)
    p_bot = App.Vector(cx - dx, cy - dy, z_min)

    def make_pill(p1, p2, r):
        v = (p2 - p1).normalize()
        n = App.Vector(-v.y, v.x, 0.0) * r
        c1 = Part.makeCylinder(r, z_max - z_min, p1)
        c2 = Part.makeCylinder(r, z_max - z_min, p2)
        pts = [p1 + n, p2 + n, p2 - n, p1 - n, p1 + n]
        box = Part.Face(Part.makePolygon(pts)).extrude(App.Vector(0, 0, z_max - z_min))
        return box.fuse(c1).fuse(c2)

    r = 0.5 * width
    return make_pill(p_apex, p_top, r).fuse(make_pill(p_apex, p_bot, r))


def build_monolithic_canopy():
    # 1. Load exact Body_Top perimeter wire
    already_open = "body_top" in App.listDocuments()
    doc_plate = App.getDocument("body_top") if already_open else App.openDocument(body_top_path)
    plate_shape = doc_plate.getObject("BodyTop").Shape
    outer_wire = max([w for w in plate_shape.Wires if w.BoundBox.XLength > 200], key=lambda w: w.BoundBox.ZMin).copy()
    doc_plate_name = doc_plate.Name

    z_base = 55.32  # 0.02 mm clearance above Body_Top (55.30 mm)
    thick = 1.50    # 1.50 mm uniform shell wall thickness
    h_apex = 26.18  # Apex at Z = 81.50 mm (2.80 mm headroom above tallest RPi 4 USB/Eth ports at Z=77.20)

    # -------------------------------------------------------------------------
    # 2. Outer Draped Surface Profiles (Apex Z = 81.50 mm down to Z = 55.32 mm)
    #    Rear (-X) dorsal dome extended smoothly to clear dual Hobbywing 10A UBECs
    #    on Chassis_RPi_Mount (X in [-102.0, -57.0], Y in [±11.5, ±31.5], Z_max = 72.72 mm)
    #    while remaining 100% flush-trimmed to Body_Top's outer silhouette.
    # -------------------------------------------------------------------------
    w_out_0 = make_filleted_wire(-140.0, 140.0, -95.0, 95.0, 35.0, z_base)
    w_out_1 = make_filleted_wire(-136.0, 136.0, -90.0, 90.0, 32.0, z_base + thick)
    w_out_2 = make_filleted_wire(-127.5, 115.0, -75.0, 75.0, 26.0, z_base + 6.5)
    w_out_3 = make_filleted_wire(-119.5,  90.0, -58.0, 58.0, 20.0, z_base + 13.5)
    w_out_4 = make_filleted_wire(-112.5,  65.0, -44.0, 44.0, 13.5, z_base + 20.5)
    w_out_5 = make_filleted_wire( -93.5,  49.0, -32.5, 32.5,  8.0, z_base + h_apex)

    loft_outer = Part.makeLoft([w_out_0, w_out_1, w_out_2, w_out_3, w_out_4, w_out_5], True)

    # -------------------------------------------------------------------------
    # 3. Inner Draped Surface Profiles (Offset inward by thick = 1.50 mm)
    # -------------------------------------------------------------------------
    w_in_1 = make_filleted_wire(-134.5, 134.5, -88.5, 88.5, 30.5, z_base - 0.1)
    w_in_2 = make_filleted_wire(-126.0, 113.5, -73.5, 73.5, 24.5, z_base + 5.0)
    w_in_3 = make_filleted_wire(-118.0,  88.5, -56.5, 56.5, 18.5, z_base + 12.0)
    w_in_4 = make_filleted_wire(-111.0,  63.5, -42.5, 42.5, 12.0, z_base + 19.0)
    w_in_5 = make_filleted_wire( -92.0,  47.5, -31.0, 31.0,  6.5, z_base + h_apex - thick)

    loft_inner = Part.makeLoft([w_in_1, w_in_2, w_in_3, w_in_4, w_in_5], True)

    # Hollow monolithic shell (uniform 1.50 mm wall thickness — no service-cover seam!)
    canopy_shell = loft_outer.cut(loft_inner)

    # -------------------------------------------------------------------------
    # 4. Trim All Overhangs Flush Around Body_Top Perimeter
    # -------------------------------------------------------------------------
    face_top = Part.Face(outer_wire)
    face_top.translate(App.Vector(0.0, 0.0, z_base - 1.0 - face_top.BoundBox.ZMin))
    body_top_extruded = face_top.extrude(App.Vector(0.0, 0.0, 42.0))

    canopy_solid = canopy_shell.common(body_top_extruded)

    # -------------------------------------------------------------------------
    # 5a. Integrated Bionic '>>>' Chevron Louvers Directly Over Raspberry Pi 4 SoC
    #     (5x 45-deg rounded pill-arm chevrons, X in [-15.0, +15.0 mm], matching Femur Cover)
    # -------------------------------------------------------------------------
    for dx in [-15.0, -7.5, 0.0, 7.5, 15.0]:
        slot = make_chevron_slot(dx, 0.0, 10.0, 2.40, 45.0, 75.0, z_base + h_apex + 3.0)
        canopy_solid = canopy_solid.cut(slot)

    # -------------------------------------------------------------------------
    # 5b. Rear Dual-UBEC Thermal Convection Vent Slots (4x 2.4mm rounded slots per UBEC
    #     directly over both Hobbywing 10A heatsinks at X in [-88, -64], Y = ±21.5 mm)
    # -------------------------------------------------------------------------
    for sign in (+1.0, -1.0):
        yc = sign * 21.5
        for sx_v in [-88.0, -80.0, -72.0, -64.0]:
            w_slot = make_filleted_wire(sx_v - 1.20, sx_v + 1.20, yc - 7.50, yc + 7.50, 1.10, 68.0)
            vent = Part.Face(w_slot).extrude(App.Vector(0.0, 0.0, 20.0))
            canopy_solid = canopy_solid.cut(vent)

    # -------------------------------------------------------------------------
    # 5c. Rear 45° Bevel Bottom-Open Switch Arch Cutouts (at (-116.0, ±14.5, Z = 54.0..63.8 mm)):
    #     Exposes both recessed Rear Switch Blocks on Chassis_RPi_Mount for tool-free external
    #     actuation while allowing the magnetic canopy to lift straight UP (+Z) without snagging!
    # -------------------------------------------------------------------------
    for p_sw, ang in [(App.Vector(-116.0, +14.5, 59.00), -45.0), (App.Vector(-116.0, -14.5, 59.00), +45.0)]:
        arch = Part.makeBox(16.0, 23.0, 10.5, App.Vector(-10.0, -11.5, -5.5))
        arch.Placement = App.Placement(p_sw, App.Rotation(App.Vector(0, 0, 1), ang))
        canopy_solid = canopy_solid.cut(arch)

    # -------------------------------------------------------------------------
    # 5d. Shifted Central 25A Mini-ATM Fuse Pass-Through Aperture (X in [-84.5, -67.5], Y in [-5.6, +5.6]):
    #     Centered cleanly on the flat Canopy roof between both Hobbywing 10A UBEC vent banks (0.80 mm
    #     uniform slip clearance around the upright fuse tower -> lifts 100% straight UP (+Z)!).
    # -------------------------------------------------------------------------
    w_fuse_cut = make_filleted_wire(-84.50, -67.50, -5.60, 5.60, 2.00, 70.0)
    fuse_aperture = Part.Face(w_fuse_cut).extrude(App.Vector(0.0, 0.0, 18.0))
    canopy_solid = canopy_solid.cut(fuse_aperture)

    # -------------------------------------------------------------------------
    # 5d2. Rear Slope 0.96" OLED Telemetry HUD Viewport Window (X in [-119.2, -98.2], Y in [-14.0, +14.0]):
    #      Vertical (+Z) extruded viewport framing the tilted 0.96" SSD1306 Dual-Zone OLED mounted on
    #      Chassis_RPi_Mount (-106.5, 0.0, Z_pcb = 70.85, tilt -27°). Keeps zero wires on Canopy and
    #      preserves 100% straight vertical (+Z) magnetic canopy lift-off without snagging!
    # -------------------------------------------------------------------------
    w_oled_win = make_filleted_wire(-119.20, -98.20, -14.00, 14.00, 1.40, 62.0)
    oled_viewport = Part.Face(w_oled_win).extrude(App.Vector(0.0, 0.0, 24.0))
    canopy_solid = canopy_solid.cut(oled_viewport)

    # -------------------------------------------------------------------------
    # 5e. 4x Internal Self-Centering Magnetic Bosses & Cup Skirts at (±48.0, ±36.0 mm):
    #     Mates cleanly onto Chassis_RPi_Mount pillars (Z_top = 72.10 mm, Ø8.00 mm + 45° chamfer):
    #     - Outer boss/cup cylinder (r = 5.40 mm) rises from Z = 70.90 mm into the Canopy ceiling,
    #       strictly trimmed inside loft_outer so the outer aerodynamic shell stays 100% seamless!
    #     - Inner centering cup bore (r = 4.20 mm, 0.20 mm radial slip-fit) from Z = 71.40..72.25 mm
    #       with 45° flared lead-in mouth (r = 4.70 -> 4.20 mm across Z = 70.90..71.40 mm) ->
    #       self-aligns X/Y zero-rattle while lifting 100% straight UP (+Z)!
    #     - Downward-facing Ø5.25 x 2.15 mm deep magnet pocket (Z = 72.25..74.40 mm) for Ø5 x 2 mm
    #       Neodymium disc magnet (>= 3.3 mm solid material above pocket ceiling — zero bleed-through!).
    # -------------------------------------------------------------------------
    z_cup_bot = 70.90
    z_cup_cone_top = 71.40
    z_boss_face = 72.25       # 0.15 mm axial clearance above lower pillar top (Z = 72.10 mm)
    r_mag_pocket = 2.625      # Ø5.25 mm for Ø5.00 x 2.00 mm Neodymium disc
    d_mag_pocket = 2.15       # Z = 72.25..74.40 mm
    for px in (-48.0, 48.0):
        for py in (-36.0, 36.0):
            boss_raw = Part.makeCylinder(5.40, 12.00, App.Vector(px, py, z_cup_bot), App.Vector(0, 0, 1))
            # Trim strictly inside outer aerodynamic surface so zero protrusion ever breaks exterior skin!
            boss_trimmed = boss_raw.common(loft_outer)
            cup_cone = Part.makeCone(4.70, 4.20, z_cup_cone_top - z_cup_bot, App.Vector(px, py, z_cup_bot), App.Vector(0, 0, 1))
            cup_cyl = Part.makeCylinder(4.20, z_boss_face - z_cup_cone_top + 0.05, App.Vector(px, py, z_cup_cone_top - 0.05), App.Vector(0, 0, 1))
            mag_cav = Part.makeCylinder(r_mag_pocket, d_mag_pocket + 0.10, App.Vector(px, py, z_boss_face - 0.10), App.Vector(0, 0, 1))
            canopy_solid = canopy_solid.fuse(boss_trimmed).cut(cup_cone).cut(cup_cyl).cut(mag_cav)

    # Note: Perimeter M3 spacer holes (+128, ±12 & -120, 0) intentionally omitted —
    # canopy lifts off tool-free via magnets on the 4 pillars (±48, ±36 mm), keeping
    # the outer aerodynamic shell 100% seamless and clean!

    if not already_open:
        App.closeDocument(doc_plate_name)
    return canopy_solid.removeSplitter()


canopy_solid = build_monolithic_canopy()
print(f"Monolithic Canopy Solid Valid: {canopy_solid.isValid()}")
print(f"Faces: {len(canopy_solid.Faces)}, Edges: {len(canopy_solid.Edges)}")
print(f"Volume: {canopy_solid.Volume:.2f} mm^3 (Area = {canopy_solid.Area:.2f} mm^2)")
xs = [v.X for v in canopy_solid.Vertexes]
ys = [v.Y for v in canopy_solid.Vertexes]
zs = [v.Z for v in canopy_solid.Vertexes]
print(f"Actual Vertex Bounds: X=[{min(xs):.1f}, {max(xs):.1f}], Y=[{min(ys):.1f}, {max(ys):.1f}], Z=[{min(zs):.1f}, {max(zs):.1f}]")

doc_name = "chassis_canopy"
try:
    App.closeDocument(doc_name)
except Exception:
    pass

doc = App.newDocument(doc_name)
obj = doc.addObject("Part::Feature", "Chassis_Canopy")
obj.Label = "Monolithic Draped Canopy with Integrated Chevron Louvers (v2)"
obj.Shape = canopy_solid
obj.Visibility = True
if hasattr(obj, "ViewObject") and obj.ViewObject is not None:
    obj.ViewObject.Visibility = True
    obj.ViewObject.Transparency = 65
    obj.ViewObject.ShapeColor = (0.18, 0.22, 0.28)

doc.recompute()
doc.saveAs(fcstd_canopy_path)
if "--export" in sys.argv:
    export_step_dir = f"{repo_root}/hardware/mechanics/export/step/custom/v2/parts/chassis"
    export_stl_dir = f"{repo_root}/hardware/mechanics/export/stl/custom/v2/parts/chassis"
    os.makedirs(export_step_dir, exist_ok=True)
    os.makedirs(export_stl_dir, exist_ok=True)
    canopy_solid.exportStep(f"{export_step_dir}/chassis_canopy.step")
    canopy_solid.exportStl(f"{export_stl_dir}/chassis_canopy.stl")
print(f"Saved FreeCAD model: {fcstd_canopy_path}")
App.closeDocument(doc_name)

sys.exit(0)
