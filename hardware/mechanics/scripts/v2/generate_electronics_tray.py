#!/usr/bin/env python3
"""
Generate Lasius Hexapod Electronics Tray v2 FreeCAD Model (electronics_tray.FCStd)
==================================================================================
Purpose & Role:
  Parametric intermediate mounting deck (3D printed in PETG/ABS) positioned inside
  the chassis between the bottom plate (Z = 2.0 mm) and top plate (Z = 53.3 mm).

Mounts and organizes all central brain and servo driver electronics:
  1. 1x Raspberry Pi 4 Model B (Front compartment, X in [-3.5, 81.5], Y in [-28, +28]):
     - Standard 58.0 x 49.0 mm M2.5 hole pattern on raised 3.5 mm standoffs.
     - Bottom ventilation & microSD card access window.
     - USB/Ethernet ports facing forward (+X) towards the open robot head.
  2. 2x PCA9685 16-Channel 12-Bit PWM Servo Drivers (Rear compartment, X in [-76, -14]):
     - Left Board (FL, ML, RL legs) at Y = +18.5 mm (56.0 x 19.0 mm M2.5 pattern).
     - Right Board (FR, MR, RR legs) at Y = -18.5 mm (56.0 x 19.0 mm M2.5 pattern).
     - Directly faces the respective chassis side openings for shortest cable runs.
  3. 1x TCA9548A 8-Channel I2C Multiplexer (Rear central spine, X in [-48, -22], Y in [-10.5, +10.5]):
     - Dedicated central placement connecting Pi 4 I2C bus to both PCA9685s and 6 leg ADCs.
  4. 4x Chassis Standoff Collar Mounts (X = ±45.0 mm, Y = ±30.0 mm):
     - Slides onto the 4 central Ø14.0 mm aluminum standoffs (spacer_14x50.FCStd) with
       anti-vibration snap-collars holding the tray rigidly at Z = 18.0 mm.
  5. Integrated Cable Routing & Zip-Tie Anchor Slots:
     - 4x Lateral servo wire comb slots (20.0 x 5.0 mm) with filleted lead-ins.
     - 6x Miniature zip-tie bridge loops (4.0 x 2.2 mm).
"""

import math
import os
import FreeCAD as App
import Part

print("--- Generating Lasius Electronics Tray v2 (FreeCAD 1.1+) ---")

models_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/models/custom/v2/parts"
export_step_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/step/custom/v2/parts"
export_stl_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/stl/custom/v2/parts"

fcstd_tray_path = f"{models_dir}/electronics_tray.FCStd"
step_tray_path = f"{export_step_dir}/electronics_tray.step"
stl_tray_path = f"{export_stl_dir}/electronics_tray.stl"


def make_rounded_rect_solid(x_min, x_max, y_min, y_max, r_corner, z_min, z_max):
    """Creates a 3D solid prism with filleted vertical corners."""
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


def build_electronics_tray():
    deck_thickness = 2.40  # mm (rigid 3D printed base plate)
    z_deck = 0.0           # Base level of the tray

    # -------------------------------------------------------------------------
    # 1. Main Tray Deck Footprint (Envelope: X in [-80.0, +82.0], Y in [-34.0, +34.0])
    # -------------------------------------------------------------------------
    deck_solid = make_rounded_rect_solid(-80.0, 82.0, -34.0, 34.0, 6.0, z_deck, z_deck + deck_thickness)

    # Add 4 Standoff Collar Tabs (expanding outward at X = ±45.0 mm, Y = ±30.0 mm)
    for sx in [-45.0, 45.0]:
        for sy in [-30.0, 30.0]:
            ear_cyl = Part.makeCylinder(9.5, deck_thickness + 3.6, App.Vector(sx, sy, z_deck), App.Vector(0, 0, 1))
            deck_solid = deck_solid.fuse(ear_cyl)

    # Bore the 4 Standoff Pass-through Holes (D = 14.2 mm clearance for D = 14.0 mm spacers)
    for sx in [-45.0, 45.0]:
        for sy in [-30.0, 30.0]:
            bore = Part.makeCylinder(7.10, deck_thickness + 10.0, App.Vector(sx, sy, z_deck - 2.0), App.Vector(0, 0, 1))
            deck_solid = deck_solid.cut(bore)

    # -------------------------------------------------------------------------
    # 2. Raspberry Pi 4 Model B Mounting (Front Compartment)
    # -------------------------------------------------------------------------
    pi_boss_height = 3.60  # mm above deck
    pi_boss_radius = 3.20  # mm (D = 6.4 mm)
    pi_hole_radius = 1.25  # mm (D = 2.5 mm for M2.5 screws)

    pi_holes = [
        (10.0, -24.5), (10.0, 24.5),
        (68.0, -24.5), (68.0, 24.5)
    ]

    for px, py in pi_holes:
        boss = Part.makeCylinder(pi_boss_radius, pi_boss_height, App.Vector(px, py, deck_thickness), App.Vector(0, 0, 1))
        deck_solid = deck_solid.fuse(boss)
        screw_hole = Part.makeCylinder(pi_hole_radius, deck_thickness + pi_boss_height + 2.0, App.Vector(px, py, -1.0), App.Vector(0, 0, 1))
        deck_solid = deck_solid.cut(screw_hole)

    # Pi 4 Ventilation & MicroSD Access Window (underneath SoC and RAM)
    pi_window = make_rounded_rect_solid(22.0, 56.0, -14.0, 14.0, 3.5, -2.0, deck_thickness + 5.0)
    deck_solid = deck_solid.cut(pi_window)

    # -------------------------------------------------------------------------
    # 3. Dual PCA9685 16-Channel PWM Servo Controllers (Rear Compartment)
    # -------------------------------------------------------------------------
    pca_boss_height = 3.00
    pca_boss_radius = 2.75  # D = 5.5 mm
    pca_hole_radius = 1.15  # D = 2.3 mm for M2/M2.5

    pca_centers_y = [+19.0, -19.0]
    for pcy in pca_centers_y:
        pca_holes = [
            (-73.0, pcy - 9.5), (-73.0, pcy + 9.5),
            (-17.0, pcy - 9.5), (-17.0, pcy + 9.5)
        ]
        for hx, hy in pca_holes:
            boss = Part.makeCylinder(pca_boss_radius, pca_boss_height, App.Vector(hx, hy, deck_thickness), App.Vector(0, 0, 1))
            deck_solid = deck_solid.fuse(boss)
            screw_hole = Part.makeCylinder(pca_hole_radius, deck_thickness + pca_boss_height + 2.0, App.Vector(hx, hy, -1.0), App.Vector(0, 0, 1))
            deck_solid = deck_solid.cut(screw_hole)

        # Weight relief and connector clearance window under each PCA9685
        pca_win = make_rounded_rect_solid(-66.0, -24.0, pcy - 6.5, pcy + 6.5, 2.5, -2.0, deck_thickness + 5.0)
        deck_solid = deck_solid.cut(pca_win)

    # -------------------------------------------------------------------------
    # 4. TCA9548A I2C Multiplexer Breakout (Rear Central Spine)
    # -------------------------------------------------------------------------
    tca_boss_height = 3.00
    tca_boss_radius = 2.50
    tca_hole_radius = 1.10

    tca_holes = [(-58.0, 0.0), (-32.0, 0.0)]
    for tx, ty in tca_holes:
        boss = Part.makeCylinder(tca_boss_radius, tca_boss_height, App.Vector(tx, ty, deck_thickness), App.Vector(0, 0, 1))
        deck_solid = deck_solid.fuse(boss)
        screw_hole = Part.makeCylinder(tca_hole_radius, deck_thickness + tca_boss_height + 2.0, App.Vector(tx, ty, -1.0), App.Vector(0, 0, 1))
        deck_solid = deck_solid.cut(screw_hole)

    # -------------------------------------------------------------------------
    # 5. Servo Wire Comb Channels & Zip-Tie Anchor Slots
    # -------------------------------------------------------------------------
    # 4x Side cable slots (X in [-75, -55] and [-35, -15], Y = ±31 mm)
    for wx1, wx2 in [(-74.0, -56.0), (-34.0, -16.0)]:
        for wy in [-31.0, 31.0]:
            slot = make_rounded_rect_solid(wx1, wx2, wy - 2.5, wy + 2.5, 2.0, -2.0, deck_thickness + 5.0)
            deck_solid = deck_solid.cut(slot)

    # 6x Zip-tie bridge pairs (4.0 x 2.2 mm slots separated by a 4.0 mm solid bridge)
    zip_tie_coords = [
        (-5.0, 16.0), (-5.0, -16.0),
        (74.0, 16.0), (74.0, -16.0),
        (-76.0, 0.0), (-14.0, 0.0)
    ]
    for zx, zy in zip_tie_coords:
        z1 = make_rounded_rect_solid(zx - 3.5, zx - 1.0, zy - 1.2, zy + 1.2, 0.5, -2.0, deck_thickness + 5.0)
        z2 = make_rounded_rect_solid(zx + 1.0, zx + 3.5, zy - 1.2, zy + 1.2, 0.5, -2.0, deck_thickness + 5.0)
        deck_solid = deck_solid.cut(z1).cut(z2)

    return deck_solid


tray_solid = build_electronics_tray()

print(f"Electronics_Tray Solid Valid: {tray_solid.isValid()}")
print(f"Faces: {len(tray_solid.Faces)}, Edges: {len(tray_solid.Edges)}")
print(f"Volume: {tray_solid.Volume:.2f} mm^3 (Area = {tray_solid.Area:.2f} mm^2)")
bb = tray_solid.BoundBox
print(f"Bounding Box: X=[{bb.XMin:.1f}, {bb.XMax:.1f}], Y=[{bb.YMin:.1f}, {bb.YMax:.1f}], Z=[{bb.ZMin:.1f}, {bb.ZMax:.1f}]")

os.makedirs(models_dir, exist_ok=True)
os.makedirs(export_step_dir, exist_ok=True)
os.makedirs(export_stl_dir, exist_ok=True)

doc_name = "electronics_tray"
try:
    App.closeDocument(doc_name)
except Exception:
    pass

doc = App.newDocument(doc_name)
obj = doc.addObject("Part::Feature", "Electronics_Tray")
obj.Label = "Electronics Mounting Tray v2 (Pi4 + 2x PCA9685 + TCA9548A)"
obj.Shape = tray_solid

doc.recompute()
doc.saveAs(fcstd_tray_path)
print(f"Saved FreeCAD model: {fcstd_tray_path}")

obj.Shape.exportStep(step_tray_path)
obj.Shape.exportStl(stl_tray_path)
print(f"Exported STEP: {step_tray_path}")
print(f"Exported STL:  {stl_tray_path}")

App.closeDocument(doc_name)
import sys
sys.exit(0)

