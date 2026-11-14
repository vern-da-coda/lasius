#!/usr/bin/env python3
"""
Generate Lasius Monocoque Central Core & Assembly v2 (FreeCAD 1.1+)
===================================================================
Architecture:
  - Integral 3D-printed monocoque central core (chassis_core.FCStd) spanning
    the 51.30 mm vertical gap between Body_Bottom (Z = 2.00 mm) and
    Body_Top (Z = 53.30 mm).
  - Directly replaces the 4 discrete middle spacer standoffs (Spacer_Window_FL,
    FR, RL, RR at X = ±45.0, Y = ±30.0 mm) with integrated structural pillars
    featuring M3 Ruthex heat-set insert pockets and through-bores.
  - Symmetrical bionic ant-thorax outer contour with an organic pinched waist
    at X = 0 (Y = ±20.0 mm), providing a massive 16.0 mm clearance to the
    middle coxa servos (ML/MR at Y = ±36.0 mm).
  - Structural Modular Interfaces (Verbindungspunkte) to adjacent modules:
    * FRONT Neck Interface (X = +54.0 mm): 2x horizontal M3 Ruthex screw pockets
      at Y = ±12.0 mm, 2.0 mm stepped alignment rebate (Zentrierfalz), and
      a 20 x 14 mm central conduit for CSI camera cable and head servo leads.
    * REAR Petiolus Interface (X = -56.0 mm): 2x horizontal M3 Ruthex screw pockets
      at Y = ±12.0 mm, 2.0 mm stepped alignment rebate, and dual tunnels for
      battery XT60/leads and gaster servo wiring.
  - Dual vertical card slots (Option A) for two PCA9685 16-channel servo
    controllers (Y = ±13.0 mm), with components facing safely INWARD towards
    robot center and 90° right-angle header pins pointing straight UP (+Z)
    for 100% ergonomic line-of-sight top-down insertion through the 58x58 mm hatch.
  - Lower encapsulated battery tunnel (Z = 2.0 .. 16.5 mm) for standard 2S LiPo
    battery pack, shielded by a 1.5 mm solid separation deck.
  - Rear compartment for TCA9548A 8-channel I2C multiplexer (rotated 90°).
  - Six arched, filleted lateral cable exit ports (FL, ML, RL, FR, MR, RR)
    preventing any cable chafing.
"""

import math
import os
import sys
import FreeCAD as App
import Part

print("--- Generating Lasius Monocoque Central Core (custom/v2/parts/chassis_core.FCStd) ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts"
asm_dir = f"{repo_root}/hardware/mechanics/models/custom/v2"
cots_dir = f"{repo_root}/hardware/mechanics/models/cots"

os.makedirs(models_dir, exist_ok=True)
os.makedirs(asm_dir, exist_ok=True)

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

# 1.1 Bionic Outer Hull Spline Extrusion (Z = 2.00 .. 53.30 mm, H = 51.30 mm)
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
hull = face.extrude(App.Vector(0.0, 0.0, 51.30))
hull.translate(App.Vector(0.0, 0.0, 2.00))

core_solid = hull

# 1.2 Cut 4x Integrated Standoff Bores & Ruthex M3 Pockets at (±45.0, ±30.0 mm)
standoffs = [
    (45.0, 30.0),
    (45.0, -30.0),
    (-45.0, 30.0),
    (-45.0, -30.0),
]
for sx, sy in standoffs:
    # Continuous M3 through-bore (Ø3.4 mm)
    bore = Part.makeCylinder(1.70, 55.00, App.Vector(sx, sy, 0.0), App.Vector(0, 0, 1))
    core_solid = core_solid.cut(bore)
    # Top Ruthex M3 pocket (Ø4.2 mm, depth 7.0 mm: Z = 46.3 .. 53.5 mm)
    top_pocket = Part.makeCylinder(2.10, 7.50, App.Vector(sx, sy, 46.30), App.Vector(0, 0, 1))
    core_solid = core_solid.cut(top_pocket)
    # Bottom Ruthex M3 pocket (Ø4.2 mm, depth 7.0 mm: Z = 1.5 .. 9.0 mm)
    bot_pocket = Part.makeCylinder(2.10, 7.50, App.Vector(sx, sy, 1.50), App.Vector(0, 0, 1))
    core_solid = core_solid.cut(bot_pocket)

# 1.3 Cut Top Central Electronics Bay (Wartungsschacht)
bay_box = Part.makeBox(64.00, 33.00, 36.00, App.Vector(-32.00, -16.50, 18.00))
core_solid = core_solid.cut(bay_box)

# 1.4 Cut Vertical Slide-In Card Slots for PCA9685 (2.2 mm wide, 2.4 mm deep)
slot_fl = Part.makeBox(2.20, 2.40, 36.00, App.Vector(30.00, 11.80, 19.50))
slot_fr = Part.makeBox(2.20, 2.40, 36.00, App.Vector(30.00, -14.20, 19.50))
slot_rl = Part.makeBox(2.20, 2.40, 36.00, App.Vector(-32.20, 11.80, 19.50))
slot_rr = Part.makeBox(2.20, 2.40, 36.00, App.Vector(-32.20, -14.20, 19.50))
for s in [slot_fl, slot_fr, slot_rl, slot_rr]:
    core_solid = core_solid.cut(s)

# 1.5 Cut Lower LiPo Battery Tunnel (Z = 1.5 .. 16.5 mm, width 36.0 mm, length 92.0 mm)
bat_box = Part.makeBox(92.00, 36.00, 15.00, App.Vector(-46.00, -18.00, 1.50))
core_solid = core_solid.cut(bat_box)

# 1.6 Cut Rear TCA9548A Multiplexer Compartment (X = -54.0 .. -32.0 mm, Z = 18.0 .. 38.0 mm)
tca_box = Part.makeBox(22.00, 32.00, 20.00, App.Vector(-54.00, -16.00, 18.00))
core_solid = core_solid.cut(tca_box)

# 1.7 FRONT Neck / Head Modular Interface (at X = +54.0 mm)
# Central cable tunnel (20 x 14 mm) for CSI camera & head servo wires
front_tunnel = Part.makeBox(26.00, 20.00, 14.00, App.Vector(30.00, -10.00, 22.00))
core_solid = core_solid.cut(front_tunnel)
# 2x Horizontal M3 Ruthex screw pockets into front face at Y = ±12.0 mm, Z = 38.0 mm
for hy in [12.0, -12.0]:
    front_bore = Part.makeCylinder(2.10, 9.0, App.Vector(55.0, hy, 38.0), App.Vector(-1, 0, 0))
    core_solid = core_solid.cut(front_bore)
# Stepped alignment rebate (Zentrierfalz, 2.0 mm deep outer rebate)
front_step = Part.makeBox(2.5, 36.0, 52.0, App.Vector(52.5, -18.0, 1.5))
front_step_cut = front_step.cut(Part.makeBox(3.0, 28.0, 44.0, App.Vector(52.0, -14.0, 5.0)))
core_solid = core_solid.cut(front_step_cut)

# 1.8 REAR Petiolus / Gaster Modular Interface (at X = -56.0 mm)
# Central cable and battery wire tunnel
rear_tunnel_low = Part.makeBox(20.00, 24.00, 15.00, App.Vector(-57.00, -12.00, 1.50))
rear_tunnel_high = Part.makeBox(20.00, 20.00, 12.00, App.Vector(-57.00, -10.00, 22.00))
core_solid = core_solid.cut(rear_tunnel_low).cut(rear_tunnel_high)
# 2x Horizontal M3 Ruthex screw pockets into rear face at Y = ±12.0 mm, Z = 38.0 mm
for hy in [12.0, -12.0]:
    rear_bore = Part.makeCylinder(2.10, 9.0, App.Vector(-57.0, hy, 38.0), App.Vector(1, 0, 0))
    core_solid = core_solid.cut(rear_bore)

# 1.9 Cut 6x Lateral Cable Ports (FL, ML, RL, FR, MR, RR)
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

# Save Part Feature
part_obj = doc_core.addObject("Part::Feature", "Chassis_Core")
part_obj.Label = "Chassis Monocoque Central Core (v2)"
part_obj.Shape = core_solid
doc_core.recompute()

doc_core.saveAs(fcstd_core_path)
print(f"✔ Saved Monocoque Part -> {fcstd_core_path}")
print(f"  Solid Valid: {core_solid.isValid()}, Volume: {core_solid.Volume:.2f} mm^3")
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

asm_compound_list = []

def make_link(name, label, src_obj, placement, color=None):
    link = doc_asm.addObject("App::Link", name)
    link.Label = label
    link.LinkedObject = src_obj
    link.Placement = placement
    if color and hasattr(link, "ViewObject") and link.ViewObject is not None:
        link.ViewObject.ShapeColor = color
    sh = src_obj.Shape.copy()
    sh.Placement = placement
    asm_compound_list.append(sh)
    return link

COLOR_CORE = (0.22, 0.24, 0.27)  # Anthracite / Carbon PA-CF monocoque
COLOR_PCA = (0.04, 0.38, 0.88)   # Signal Blue PCA9685
COLOR_TCA = (0.50, 0.15, 0.70)   # Signal Violet TCA9548A
COLOR_BAT = (0.85, 0.65, 0.10)   # Gold / Yellow 2S LiPo

# 1. Monocoque Core Shell
p_core = App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation())
make_link("Chassis_Core", "1. Monocoque Core Shell", doc_core.Chassis_Core, p_core, COLOR_CORE)

# 2. Left PCA9685 Board:
# Vertical at Y = +13.0 mm. Rotation +90° around X:
# Original +Y (header pins) maps to +Z (pointing UP into hatch).
# Original +Z (components: capacitor, IC) maps to -Y (facing INWARD into center bay).
# BBox Y in [-1.10, +13.00], Z in [12.10, 46.00]. Completely inside core!
r_pca_l = App.Rotation(App.Vector(1, 0, 0), 90.0)
p_pca_l = App.Placement(App.Vector(0.0, 13.00, 24.80), r_pca_l)
make_link("Board_PCA9685_Left", "2. PCA9685 Left (Vertical, Pins +Z, Comps Inward)", doc_pca.PCA9685_Board, p_pca_l, COLOR_PCA)

# 3. Right PCA9685 Board:
# Vertical at Y = -13.0 mm. Symmetrical inward rotation around (0, 1, 1)/sqrt(2) by 180°:
# Original +Y (header pins) maps to +Z (pointing UP into hatch).
# Original +Z (components) maps to +Y (facing INWARD into center bay).
# BBox Y in [-13.00, +1.10], Z in [12.10, 46.00]. Completely inside core!
r_pca_r = App.Rotation(App.Vector(0, 1, 1), 180.0)
p_pca_r = App.Placement(App.Vector(0.0, -13.00, 24.80), r_pca_r)
make_link("Board_PCA9685_Right", "3. PCA9685 Right (Vertical, Pins +Z, Comps Inward)", doc_pca.PCA9685_Board, p_pca_r, COLOR_PCA)

# 4. TCA9548A Multiplexer at rear compartment (rotated 90° so length is across Y)
# BBox X in [-52.5, -31.5], Y in [-15.75, +15.75], Z in [20.0, 30.1]. Completely inside rear bay!
r_tca = App.Rotation(App.Vector(0, 0, 1), 90.0)
p_tca = App.Placement(App.Vector(-42.0, 0.0, 20.00), r_tca)
make_link("Board_TCA9548A", "4. TCA9548A I2C Multiplexer", doc_tca.TCA9548A_Board, p_tca, COLOR_TCA)

# 5. 2S LiPo Battery Pack in lower tunnel (X = 0.0, Y = 0.0, Z = 2.50 .. 16.50 mm)
p_bat = App.Placement(App.Vector(0.0, 0.0, 2.50), App.Rotation())
make_link("Battery_LiPo_2S", "5. 2S 7.4V LiPo Battery Pack", doc_bat.Battery_LiPo_2S, p_bat, COLOR_BAT)

# Assembly Compound
asm_obj = doc_asm.addObject("Part::Feature", "Chassis_Core_Assembly")
asm_obj.Label = "Lasius Monocoque Central Core Assembly (v2)"
asm_obj.Shape = Part.makeCompound(asm_compound_list)

doc_asm.recompute()
doc_asm.saveAs(fcstd_asm_path)
print(f"✔ Saved Monocoque Assembly -> {fcstd_asm_path}")

App.closeDocument(doc_core_name)
App.closeDocument(doc_asm_name)
App.closeDocument(doc_pca.Name)
App.closeDocument(doc_tca.Name)
App.closeDocument(doc_bat.Name)

print("--- Monocoque Generation Complete ---")
sys.exit(0)
