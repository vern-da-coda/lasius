#!/usr/bin/env python3
"""
Generate Lasius Monocoque Central Core & Assembly v2 (FreeCAD 1.1+)
===================================================================
Architecture:
  - Integral 3D-printed monocoque central core (chassis_core.FCStd) spanning
    the 51.30 mm vertical gap between Body_Bottom (Z = 2.00 mm) and
    Body_Top (Z = 53.30 mm).
  - Directly replaces the 4 discrete middle spacer standoffs at X = ±45.0, Y = ±30.0 mm
    with integrated structural pillars featuring M3 Ruthex heat-set insert pockets.
  - Symmetrical bionic ant-thorax outer contour with an organic pinched waist at X = 0.
  - Dual vertical slide-in card slots (Option A) for two PCA9685 16-channel servo
    controllers (Y = ±13.0 mm, Z = 31.00 mm -> PCB Z in [18.30, 43.70 mm], pins up to 52.20 mm),
    captively guiding the 62.5 mm PCB edges over 2.25 mm per side with zero collision.
  - Lower encapsulated battery tunnel (Z = 1.5 .. 16.65 mm) with full rear clearance
    for 2S LiPo battery pack and JST-XH balance plug.
  - Rear compartment for TCA9548A 8-channel I2C multiplexer with integrated support
    bosses (Z = 18.0 .. 19.95 mm) and centering pins at (-42.0, ±13.0 mm).
"""

import math
import os
import sys
import FreeCAD as App
import Part

print("--- Generating Lasius Monocoque Central Core (custom/v2/parts/chassis/chassis_core.FCStd) ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts/chassis"
asm_dir = f"{repo_root}/hardware/mechanics/models/custom/v2"
cots_dir = f"{repo_root}/hardware/mechanics/models/cots"
export_step_dir = f"{repo_root}/hardware/mechanics/export/step/custom/v2"
export_stl_dir = f"{repo_root}/hardware/mechanics/export/stl/custom/v2"

for d in [
    models_dir,
    asm_dir,
    f"{export_step_dir}/parts/chassis",
    f"{export_stl_dir}/parts/chassis",
]:
    os.makedirs(d, exist_ok=True)

# -----------------------------------------------------------------------------
# 1. Build Part: chassis_core.FCStd
# -----------------------------------------------------------------------------
doc_core_name = "chassis_core"
try:
    App.closeDocument(doc_core_name)
except Exception:
    pass
doc_core = App.newDocument(doc_core_name)
fcstd_core_path = f"{models_dir}/chassis_core.FCStd"

# 1.1 Bionic Outer Hull Spline Extrusion (Z = 2.02 .. 53.28 mm, H = 51.26 mm for 0.02 mm plate clearance)
pts_half = [
    App.Vector(54.0, 0.0, 0.0),
    App.Vector(54.0, 16.0, 0.0),
    App.Vector(45.0 + 7.0 * math.cos(math.radians(20)), 30.0 + 7.0 * math.sin(math.radians(20)), 0.0),
    App.Vector(45.0, 37.0, 0.0),
    App.Vector(45.0 - 7.0 * math.cos(math.radians(45)), 30.0 + 7.0 * math.sin(math.radians(45)), 0.0),
    App.Vector(20.0, 22.0, 0.0),
    App.Vector(0.0, 20.0, 0.0),
    App.Vector(-20.0, 22.0, 0.0),
    App.Vector(-45.0 + 7.0 * math.cos(math.radians(45)), 30.0 + 7.0 * math.sin(math.radians(45)), 0.0),
    App.Vector(-45.0, 37.0, 0.0),
    App.Vector(-45.0 - 7.0 * math.cos(math.radians(20)), 30.0 + 7.0 * math.sin(math.radians(20)), 0.0),
    App.Vector(-56.0, 16.0, 0.0),
    App.Vector(-56.0, 0.0, 0.0),
]
spline_half = Part.BSplineCurve()
spline_half.interpolate(pts_half)

pts_lower = [App.Vector(p.x, -p.y, 0.0) for p in reversed(pts_half[1:-1])]
spline_lower = Part.BSplineCurve()
spline_lower.interpolate([pts_half[-1]] + pts_lower + [pts_half[0]])

wire = Part.Wire([spline_half.toShape(), spline_lower.toShape()])
face = Part.Face(wire)
hull = face.extrude(App.Vector(0.0, 0.0, 51.26))
hull.translate(App.Vector(0.0, 0.0, 2.02))

core_solid = hull

# 1.2 Cut 4x Integrated Standoff Bores & Ruthex M3 Pockets at (±45.0, ±30.0 mm)
standoffs = [
    (45.0, 30.0),
    (45.0, -30.0),
    (-45.0, 30.0),
    (-45.0, -30.0),
]
for sx, sy in standoffs:
    bore = Part.makeCylinder(1.70, 55.00, App.Vector(sx, sy, 0.0), App.Vector(0, 0, 1))
    top_pocket = Part.makeCylinder(2.10, 7.50, App.Vector(sx, sy, 46.30), App.Vector(0, 0, 1))
    bot_pocket = Part.makeCylinder(2.10, 7.50, App.Vector(sx, sy, 1.50), App.Vector(0, 0, 1))
    core_solid = core_solid.cut(bore).cut(top_pocket).cut(bot_pocket)

# 1.3 Cut Top Central Electronics Bay & Captive PCA9685 Card Guide Slots
# - Main bay spans X in [-29.00, +29.00], Y in [-16.50, +16.50], Z in [18.00, 54.00]
# - Inner component relief spans X in [-31.00, +31.00], Y in [-11.10, +11.10], Z in [18.00, 54.00]
# - Vertical card guide slots at Y in [11.10, 13.30] and [-13.30, -11.10] span X in [-31.60, +31.60],
#   captively guiding the 62.50 x 1.60 mm PCA9685 PCBs (X in [-31.25, +31.25], Y in [±11.40, ±13.00])
#   over 2.25 mm per side with >= 0.30 mm clearance!
bay_box = Part.makeBox(58.00, 33.00, 36.00, App.Vector(-29.00, -16.50, 18.00))
bay_inner = Part.makeBox(62.00, 22.20, 36.00, App.Vector(-31.00, -11.10, 18.00))
slot_left = Part.makeBox(63.20, 2.20, 36.00, App.Vector(-31.60, 11.10, 18.00))
slot_right = Part.makeBox(63.20, 2.20, 36.00, App.Vector(-31.60, -13.30, 18.00))
core_solid = core_solid.cut(bay_box).cut(bay_inner).cut(slot_left).cut(slot_right)

# 1.4 Cut Lower LiPo Battery Tunnel (Z = 1.50 .. 16.65 mm, X = -55.50 .. +46.00 mm, Y = -18.20 .. +18.20 mm)
bat_box = Part.makeBox(101.50, 36.40, 15.15, App.Vector(-55.50, -18.20, 1.50))
core_solid = core_solid.cut(bat_box)

# 1.5 Cut Rear TCA9548A Multiplexer Compartment - OPEN TO BODY_TOP (Z = 18.00 .. 54.00 mm)
tca_box = Part.makeBox(23.00, 32.00, 36.00, App.Vector(-54.00, -16.00, 18.00))
core_solid = core_solid.cut(tca_box)

# 1.6 FRONT Neck / Head Modular Interface & Wiring Bay - OPEN TO BODY_TOP (Z = 22.00 .. 54.00 mm)
front_tunnel = Part.makeBox(24.00, 20.00, 32.00, App.Vector(30.00, -10.00, 22.00))
core_solid = core_solid.cut(front_tunnel)
for hy in [12.0, -12.0]:
    front_bore = Part.makeCylinder(2.10, 9.0, App.Vector(55.0, hy, 38.0), App.Vector(-1, 0, 0))
    core_solid = core_solid.cut(front_bore)
front_step = Part.makeBox(2.5, 36.0, 52.0, App.Vector(52.5, -18.0, 1.5))
front_step_cut = front_step.cut(Part.makeBox(3.0, 28.0, 44.0, App.Vector(52.0, -14.0, 5.0)))
core_solid = core_solid.cut(front_step_cut)

# 1.7 REAR Petiolus / Gaster Modular Interface (at X = -56.0 mm)
rear_tunnel_low = Part.makeBox(20.00, 24.00, 15.15, App.Vector(-57.00, -12.00, 1.50))
rear_tunnel_high = Part.makeBox(20.00, 20.00, 12.00, App.Vector(-57.00, -10.00, 22.00))
core_solid = core_solid.cut(rear_tunnel_low).cut(rear_tunnel_high)
for hy in [12.0, -12.0]:
    rear_bore = Part.makeCylinder(2.10, 9.0, App.Vector(-57.0, hy, 38.0), App.Vector(1, 0, 0))
    core_solid = core_solid.cut(rear_bore)

# 1.8 Cut 6x Lateral Cable Ports (FL, ML, RL, FR, MR, RR)
port_defs = [
    (34.00, 10.00, 12.00, 22.00, 12.00),    # FL
    (-6.00, 10.00, 12.00, 22.00, 12.00),    # ML
    (-46.00, 10.00, 12.00, 22.00, 12.00),   # RL
    (34.00, -32.00, 12.00, 22.00, 12.00),   # FR
    (-6.00, -32.00, 12.00, 22.00, 12.00),   # MR
    (-46.00, -32.00, 12.00, 22.00, 12.00),  # RR
]
for px, py, pdx, pdy, pdz in port_defs:
    port_box = Part.makeBox(pdx, pdy, pdz, App.Vector(px, py, 23.00))
    core_solid = core_solid.cut(port_box)

    # Station 4: Integrated Micro-Zip-Tie Saddle at Lateral Port Sill (for 2.5 mm cable ties)
    sign_y = 1.0 if py > 0 else -1.0
    ys = 15.0 * sign_y
    s_ch1 = Part.makeBox(1.30, 2.80, 8.0, App.Vector(px + 3.5, ys - 1.40, 16.0))
    s_ch2 = Part.makeBox(1.30, 2.80, 8.0, App.Vector(px + 6.5, ys - 1.40, 16.0))
    core_solid = core_solid.cut(s_ch1).cut(s_ch2)

# 1.9 Add Integrated Support Bosses & Centering Pins for TCA9548A at (-42.0, ±13.0 mm)
for ty in [13.0, -13.0]:
    tca_boss = Part.makeCylinder(2.50, 1.95, App.Vector(-42.0, ty, 18.00), App.Vector(0, 0, 1))
    tca_pin = Part.makeCylinder(1.15, 2.00, App.Vector(-42.0, ty, 19.95), App.Vector(0, 0, 1))
    core_solid = core_solid.fuse(tca_boss).fuse(tca_pin)

core_solid = core_solid.removeSplitter()

part_obj = doc_core.addObject("Part::Feature", "Chassis_Core")
part_obj.Label = "Chassis Monocoque Central Core (v2)"
part_obj.Shape = core_solid
if hasattr(part_obj, "ViewObject") and part_obj.ViewObject is not None:
    part_obj.ViewObject.Visibility = True
    part_obj.ViewObject.ShapeColor = (0.22, 0.24, 0.27)
doc_core.recompute()

doc_core.saveAs(fcstd_core_path)
core_solid.exportStep(f"{export_step_dir}/parts/chassis/chassis_core.step")
core_solid.exportStl(f"{export_stl_dir}/parts/chassis/chassis_core.stl")
print(f"✔ Saved Monocoque Part -> {fcstd_core_path} (Valid={core_solid.isValid()}, Volume={core_solid.Volume:.1f} mm^3)")
App.closeDocument(doc_core_name)

# -----------------------------------------------------------------------------
# 2. Build Assembly: chassis_core_assembly.FCStd
# -----------------------------------------------------------------------------
doc_asm_name = "chassis_core_assembly"
try:
    App.closeDocument(doc_asm_name)
except Exception:
    pass
doc_asm = App.newDocument(doc_asm_name)
fcstd_asm_path = f"{asm_dir}/chassis_core_assembly.FCStd"
doc_asm.saveAs(fcstd_asm_path)

doc_core = App.openDocument(fcstd_core_path)
doc_pca = App.openDocument(f"{cots_dir}/pca9685_board.FCStd")
doc_tca = App.openDocument(f"{cots_dir}/tca9548a_board.FCStd")
doc_bat = App.openDocument(f"{cots_dir}/battery_lipo_2s.FCStd")

asm_part = doc_asm.addObject("App::Part", "Chassis_Core_Assembly")
asm_part.Label = "Lasius Monocoque Central Core Assembly (v2)"
for o in asm_part.Origin.OutList:
    if hasattr(o, "Visibility"):
        o.Visibility = False
asm_part.Origin.Visibility = False
asm_part.Visibility = True


def make_link(name, label, src_obj, placement, color=None):
    link = doc_asm.addObject("App::Link", name)
    link.Label = label
    link.setLink(src_obj)
    link.Placement = placement
    asm_part.addObject(link)
    link.Visibility = True
    if hasattr(link, "ViewObject") and link.ViewObject is not None:
        link.ViewObject.Visibility = True
        if color:
            link.ViewObject.OverrideMaterial = True
            mat = link.ViewObject.ShapeMaterial
            mat.DiffuseColor = color
            link.ViewObject.ShapeMaterial = mat
    return link


COLOR_CORE = (0.22, 0.24, 0.27)  # Anthracite / Carbon PA-CF monocoque
COLOR_PCA = (0.04, 0.38, 0.88)   # Signal Blue PCA9685
COLOR_TCA = (0.50, 0.15, 0.70)   # Signal Violet TCA9548A
COLOR_BAT = (0.85, 0.65, 0.10)   # Gold / Yellow 2S LiPo

# 1. Monocoque Core Shell
make_link("Chassis_Core", "1. Monocoque Core Shell", doc_core.Chassis_Core, App.Placement(), COLOR_CORE)

# 2. Left PCA9685 Board at Y = +13.00 mm, Z = 31.00 mm (PCB Z in [18.30, 43.70], pins up to 52.20 mm)
r_pca_l = App.Rotation(App.Vector(1, 0, 0), 90.0)
p_pca_l = App.Placement(App.Vector(0.0, 13.00, 31.00), r_pca_l)
make_link("Board_PCA9685_Left", "2. PCA9685 Left (Vertical, Pins +Z, Comps Inward)", doc_pca.PCA9685_Board, p_pca_l, COLOR_PCA)

# 3. Right PCA9685 Board at Y = -13.00 mm, Z = 31.00 mm
r_pca_r = App.Rotation(App.Vector(0, 1, 1), 180.0)
p_pca_r = App.Placement(App.Vector(0.0, -13.00, 31.00), r_pca_r)
make_link("Board_PCA9685_Right", "3. PCA9685 Right (Vertical, Pins +Z, Comps Inward)", doc_pca.PCA9685_Board, p_pca_r, COLOR_PCA)

# 4. TCA9548A Multiplexer seated on support bosses at (-42.0, 0.0, 20.00 mm)
r_tca = App.Rotation(App.Vector(0, 0, 1), 90.0)
p_tca = App.Placement(App.Vector(-42.0, 0.0, 20.00), r_tca)
make_link("Board_TCA9548A", "4. TCA9548A I2C Multiplexer", doc_tca.TCA9548A_Board, p_tca, COLOR_TCA)

# 5. 2S LiPo Battery Pack in lower tunnel (Z = 2.45 .. 16.45 mm)
p_bat = App.Placement(App.Vector(0.0, 0.0, 2.45), App.Rotation())
make_link("Battery_LiPo_2S", "5. 2S 7.4V LiPo Battery Pack", doc_bat.Battery_LiPo_2S, p_bat, COLOR_BAT)

doc_asm.recompute()
doc_asm.save()
asm_part.Shape.exportStep(f"{export_step_dir}/chassis_core_assembly.step")
# Assembly STL omitted (assemblies use STEP for CAD; STL is reserved for 3D-printable parts)
print(f"✔ Saved & Exported Monocoque Assembly -> {fcstd_asm_path}")

# Verify 0.0000 mm^3 collisions
items = [(o.Name, o.Shape) for o in asm_part.Group if hasattr(o, "Shape") and not o.Shape.isNull()]
max_coll = 0.0
for i in range(len(items)):
    for j in range(i + 1, len(items)):
        n1, s1 = items[i]
        n2, s2 = items[j]
        if s1.BoundBox.intersect(s2.BoundBox):
            v = s1.common(s2).Volume
            if v > 1e-4:
                print(f"  ❌ COLLISION {n1} <-> {n2}: {v:.4f} mm^3")
                max_coll = max(max_coll, v)
if max_coll <= 1e-4:
    print("  ✅ ZERO COLLISIONS in chassis_core_assembly.FCStd (0.0000 mm^3)!")

for d in list(App.listDocuments().values()):
    try:
        App.closeDocument(d.Name)
    except Exception:
        pass
try:
    from PySide6 import QtCore
    QtCore.QCoreApplication.processEvents()
except Exception:
    pass
sys.exit(0)
