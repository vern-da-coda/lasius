#!/usr/bin/env python3
"""
Generate Lasius Electronics Tray & Assembly - Option B: 45° V-Cradle Mounting
============================================================================
Architecture Option B:
  - Both PCA9685 16-channel servo controllers are mounted at a 45° angle in a 3D-printed
    V-cradle structure on the electronics tray deck.
  - Left Board (Y_center = +16.0 mm) is tilted 45° with 90° Dupont pins pointing 45°
    diagonally UPWARD and INWARD towards the top chassis hatch.
  - Right Board (Y_center = -16.0 mm) is tilted -45° with 90° Dupont pins pointing 45°
    diagonally UPWARD and INWARD towards the top chassis hatch.
  - Clearance to middle coxa servos (ML/MR at Y = ±36.0 mm): >= 16.0 mm on each side!
  - Pin tips are positioned at Y = ±10.0 mm under the 58x58 mm central cutout of Body_Top.
  - Servo connectors (14.0 mm Dupont female plugs) plug in diagonally from above through
    the open carapace hatch with generous 20.0 mm corridor between plug banks.
  - TCA9548A I2C multiplexer sits on rear spine at X = -52.0, Y = 0.0 mm.
  - 2S LiPo battery pack is encapsulated in the underside cradle (Z = -15.0 .. 0.0 mm).
"""

import math
import os
import FreeCAD as App
import Part

print("--- Generating Electronics Tray Option B (45° V-Cradle Mounting) ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts"
asm_dir = f"{repo_root}/hardware/mechanics/models/custom/v2"
cots_dir = f"{repo_root}/hardware/mechanics/models/cots"
export_step_dir = f"{repo_root}/hardware/mechanics/export/step/custom/v2/parts"
export_stl_dir = f"{repo_root}/hardware/mechanics/export/stl/custom/v2/parts"
export_asm_step_dir = f"{repo_root}/hardware/mechanics/export/step/custom/v2"
export_asm_stl_dir = f"{repo_root}/hardware/mechanics/export/stl/custom/v2"

os.makedirs(models_dir, exist_ok=True)
os.makedirs(export_step_dir, exist_ok=True)
os.makedirs(export_stl_dir, exist_ok=True)
os.makedirs(export_asm_step_dir, exist_ok=True)
os.makedirs(export_asm_stl_dir, exist_ok=True)

# -----------------------------------------------------------------------------
# 1. Build Part: electronics_tray_opt_b.FCStd
# -----------------------------------------------------------------------------
doc_tray_name = "electronics_tray_opt_b"
try:
    App.closeDocument(doc_tray_name)
except Exception:
    pass
doc_tray = App.newDocument(doc_tray_name)

deck_thickness = 2.40  # mm base plate
z_deck = 0.0

def make_rounded_rect_solid(x_min, x_max, y_min, y_max, r_corner, z_min, z_max):
    dx = x_max - x_min
    dy = y_max - y_min
    r_corner = min(r_corner, dx / 2.0 - 0.1, dy / 2.0 - 0.1)
    k = r_corner * (1.0 - 1.0 / math.sqrt(2.0))
    pts = [
        (x_min + r_corner, y_max),
        (x_max - r_corner, y_max),
        (x_max - k, y_max - k),
        (x_max, y_max - r_corner),
        (x_max, y_min + r_corner),
        (x_max - k, y_min + k),
        (x_max - r_corner, y_min),
        (x_min + r_corner, y_min),
        (x_min + k, y_min + k),
        (x_min, y_min + r_corner),
        (x_min, y_max - r_corner),
        (x_min + k, y_max - k),
    ]
    v = [App.Vector(px, py, z_min) for px, py in pts]
    edges = [
        Part.makeLine(v[0], v[1]),
        Part.Edge(Part.ArcOfCircle(v[1], v[2], v[3])),
        Part.makeLine(v[3], v[4]),
        Part.Edge(Part.ArcOfCircle(v[4], v[5], v[6])),
        Part.makeLine(v[6], v[7]),
        Part.Edge(Part.ArcOfCircle(v[7], v[8], v[9])),
        Part.makeLine(v[9], v[10]),
        Part.Edge(Part.ArcOfCircle(v[10], v[11], v[0])),
    ]
    face = Part.Face(Part.Wire(edges))
    return face.extrude(App.Vector(0.0, 0.0, z_max - z_min))

# Base deck footprint (Envelope: X in [-72.0, 58.0], Y in [-25.0, 25.0])
deck_solid = make_rounded_rect_solid(-72.0, 58.0, -25.0, 25.0, 5.0, z_deck, z_deck + deck_thickness)

# Add 4 Standoff Collar Tabs at X = ±45.0 mm, Y = ±30.0 mm
for sx in [-45.0, 45.0]:
    for sy in [-30.0, 30.0]:
        ear_cyl = Part.makeCylinder(9.5, deck_thickness + 3.6, App.Vector(sx, sy, z_deck), App.Vector(0, 0, 1))
        deck_solid = deck_solid.fuse(ear_cyl)

# Bore the 4 Standoff Pass-through Holes (D = 14.2 mm clearance for D = 14.0 mm spacers)
for sx in [-45.0, 45.0]:
    for sy in [-30.0, 30.0]:
        bore = Part.makeCylinder(7.10, deck_thickness + 10.0, App.Vector(sx, sy, z_deck - 2.0), App.Vector(0, 0, 1))
        deck_solid = deck_solid.cut(bore)

# Add 45° V-Cradle Support Wedges:
# Left V-Wedge: tilted +45°, centered along Y = +16.0 mm, X in [-31.5, 31.5] mm
# Right V-Wedge: tilted -45°, centered along Y = -16.0 mm, X in [-31.5, 31.5] mm
# Each board rests on 4 angled mounting bosses (X = ±28.0 mm, Y = ±9.5 mm in local board frame)
for side_sign, y_base in [(+1.0, +16.0), (-1.0, -16.0)]:
    # Longitudinal support wedge
    wedge_box = Part.makeBox(63.0, 18.0, 14.0, App.Vector(-31.5, y_base - 9.0, deck_thickness))
    # Cut angled plane at 45°
    cut_box = Part.makeBox(70.0, 30.0, 30.0, App.Vector(-35.0, y_base - 15.0, deck_thickness + 5.0))
    cut_box.rotate(App.Vector(0.0, y_base, deck_thickness + 5.0), App.Vector(1, 0, 0), side_sign * 45.0)
    # Fuse wedge to deck
    deck_solid = deck_solid.fuse(wedge_box)

    # 4x M2.5 Angled Mounting Holes into the wedge:
    for hx in [-28.0, 28.0]:
        for local_hy in [-9.5, 9.5]:
            # Coordinate in global frame:
            gy = y_base + local_hy * math.cos(math.radians(45.0))
            gz = deck_thickness + 8.0 - side_sign * local_hy * math.sin(math.radians(45.0))
            dir_v = App.Vector(0.0, -side_sign * math.sin(math.radians(45.0)), math.cos(math.radians(45.0)))
            hole_cyl = Part.makeCylinder(1.15, 15.0, App.Vector(hx, gy, gz) - dir_v * 5.0, dir_v)
            deck_solid = deck_solid.cut(hole_cyl)

# Central Wiring Trench (Y in [-5.0, 5.0], X in [-22.0, 22.0]):
center_win = make_rounded_rect_solid(-22.0, 22.0, -5.0, 5.0, 2.0, -2.0, deck_thickness + 18.0)
deck_solid = deck_solid.cut(center_win)

# Add TCA9548A Mounting Bosses at rear spine (X = -52.0, Y = 0.0)
tca_holes = [(-65.0, 0.0), (-39.0, 0.0)]
for tx, ty in tca_holes:
    boss = Part.makeCylinder(2.50, 3.0, App.Vector(tx, ty, deck_thickness), App.Vector(0, 0, 1))
    deck_solid = deck_solid.fuse(boss)
    screw_hole = Part.makeCylinder(1.10, deck_thickness + 5.0, App.Vector(tx, ty, -1.0), App.Vector(0, 0, 1))
    deck_solid = deck_solid.cut(screw_hole)

# Wiring windows:
front_win = make_rounded_rect_solid(15.0, 50.0, -10.0, 10.0, 3.0, -2.0, deck_thickness + 5.0)
deck_solid = deck_solid.cut(front_win)
tca_win = make_rounded_rect_solid(-62.0, -42.0, -5.5, 5.5, 2.0, -2.0, deck_thickness + 5.0)
deck_solid = deck_solid.cut(tca_win)

part_tray_obj = doc_tray.addObject("Part::Feature", "Electronics_Tray_OptB")
part_tray_obj.Label = "Electronics Mounting Tray Opt B (45° V-Cradle)"
part_tray_obj.Shape = deck_solid
doc_tray.recompute()

fcstd_tray = f"{models_dir}/electronics_tray_opt_b.FCStd"
doc_tray.saveAs(fcstd_tray)
deck_solid.exportStep(f"{export_step_dir}/electronics_tray_opt_b.step")
deck_solid.exportStl(f"{export_stl_dir}/electronics_tray_opt_b.stl")
print(f"✔ Saved Electronics Tray Opt B Part -> {fcstd_tray}")
App.closeDocument(doc_tray_name)


# -----------------------------------------------------------------------------
# 2. Build Assembly: electronics_tray_assembly_opt_b.FCStd
# -----------------------------------------------------------------------------
doc_asm_name = "electronics_tray_assembly_opt_b"
try:
    App.closeDocument(doc_asm_name)
except Exception:
    pass
doc_asm = App.newDocument(doc_asm_name)
fcstd_asm = f"{asm_dir}/electronics_tray_assembly_opt_b.FCStd"
doc_asm.saveAs(fcstd_asm)

doc_tray = App.openDocument(fcstd_tray)
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

COLOR_TRAY = (0.22, 0.23, 0.25)
COLOR_PCA = (0.04, 0.38, 0.88)
COLOR_TCA = (0.45, 0.12, 0.65)
COLOR_BAT = (0.85, 0.65, 0.10)

# 1. Tray Deck
p_tray = App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation())
make_link("Electronics_Tray", "1. Electronics Tray Opt B (45° V-Cradle)", doc_tray.Electronics_Tray_OptB, p_tray, COLOR_TRAY)

# 2. Left PCA9685 Board:
# Tilted 45° around X: pins point 45° UPWARD and INWARD towards Y=0
# Rotation around X by -135°:
r_pca_l = App.Rotation(App.Vector(1, 0, 0), -135.0)
p_pca_l = App.Placement(App.Vector(0.0, 16.00, 14.50), r_pca_l)
make_link("Board_PCA9685_Left", "2. PCA9685 Left (45° V-Cradle, Pins In/Up)", doc_pca.PCA9685_Board, p_pca_l, COLOR_PCA)

# 3. Right PCA9685 Board:
# Tilted -45° around X: pins point 45° UPWARD and INWARD towards Y=0
# Rotation around (0, cos 22.5°, sin 22.5°) by 180° or Euler:
# Initial +Y -> target Y' = +0.707, Z' = +0.707
# Initial +Z -> target Y' = -0.707, Z' = +0.707
r_pca_r = App.Rotation(App.Vector(1, 0, 0), 135.0).multiply(App.Rotation(App.Vector(0, 0, 1), 180.0))
p_pca_r = App.Placement(App.Vector(0.0, -16.00, 14.50), r_pca_r)
make_link("Board_PCA9685_Right", "3. PCA9685 Right (45° V-Cradle, Pins In/Up)", doc_pca.PCA9685_Board, p_pca_r, COLOR_PCA)

# 4. TCA9548A Multiplexer at X = -52.0, Y = 0.0, Z = 5.40 mm
p_tca = App.Placement(App.Vector(-52.0, 0.0, 5.40), App.Rotation())
make_link("Board_TCA9548A", "4. TCA9548A I2C Multiplexer", doc_tca.TCA9548A_Board, p_tca, COLOR_TCA)

# 5. 2S LiPo Battery Pack underneath (Z = -15.0 .. -1.0 mm)
p_bat = App.Placement(App.Vector(5.0, 0.0, -15.00), App.Rotation())
make_link("Battery_LiPo_2S", "5. 2S 7.4V LiPo Battery Pack", doc_bat.Battery_LiPo_2S, p_bat, COLOR_BAT)

# Assembly Compound
asm_obj = doc_asm.addObject("Part::Feature", "Electronics_Tray_Assembly_OptB")
asm_obj.Label = "Electronics Tray Assembly Opt B (45° V-Cradle)"
asm_obj.Shape = Part.makeCompound(asm_compound_list)

doc_asm.recompute()
fcstd_asm = f"{asm_dir}/electronics_tray_assembly_opt_b.FCStd"
doc_asm.saveAs(fcstd_asm)
asm_obj.Shape.exportStep(f"{export_asm_step_dir}/electronics_tray_assembly_opt_b.step")
asm_obj.Shape.exportStl(f"{export_asm_stl_dir}/electronics_tray_assembly_opt_b.stl")
print(f"✔ Saved Electronics Tray Assembly Opt B -> {fcstd_asm}")

App.closeDocument(doc_tray_name)
App.closeDocument(doc_asm_name)
App.closeDocument(doc_pca.Name)
App.closeDocument(doc_tca.Name)
App.closeDocument(doc_bat.Name)
print("--- Option B Complete ---")
