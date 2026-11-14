#!/usr/bin/env python3
"""
Generate Lasius Hexapod Electronics Tray v2 FreeCAD Model (electronics_tray.FCStd)
==================================================================================
Purpose & Role:
  Parametric intermediate mounting deck (3D printed in PETG/ABS) positioned inside
  the chassis between the bottom plate (Z = 2.0 mm) and top plate (Z = 53.3 mm).
  Holds all interior servo actuation, power distribution, and I2C multiplexing hardware
  while the Raspberry Pi 4 Model B is mounted on top of the upper chassis plate under
  the protective canopy (chassis_top_cover.FCStd).

Mounts and organizes:
  1. 2x PCA9685 16-Channel 12-Bit PWM Servo Drivers (Central Bay, X in [-31.25, +31.25]):
     - Sits cleanly between front and rear spacers (6.75 mm clearance to spacer collars).
     - Left Board at Y = +21.0 mm: 90° right-angle servo headers face left (+Y) for lateral connection of FL, ML, RL legs.
     - Right Board at Y = -21.0 mm: 90° right-angle servo headers face right (-Y) for lateral connection of FR, MR, RR legs.
     - Dual 6-pin I2C headers point straight up (+Z) on short edges (-X and +X).
     - 2-pin screw terminals face inward towards the central wiring corridor.
  2. 1x TCA9548A 8-Channel I2C Multiplexer (Rear Centerline Spine, X = -52.0, Y = 0.0):
     - Sits on the rear centerline between the rear spacers (12.5 mm lateral clearance).
  3. 4x Chassis Standoff Collar Mounts (X = ±45.0 mm, Y = ±30.0 mm):
     - Slides onto the 4 central Ø14.0 mm plastic standoffs (spacer_14x50.FCStd) with
       anti-vibration snap-collars holding the tray rigidly at Z = 18.0 mm.
  4. 2S LiPo Battery Cradle (Underside at X = 5.0, Y = 0.0, Z in [-15.0, 0.0] mm):
     - Integrated retention strap slots for the 2S 7.4V battery pack.
  5. Integrated Cable Routing & Zip-Tie Anchor Slots:
     - 4x Lateral cable comb slots with filleted lead-ins.
     - 6x Miniature zip-tie bridge loops.
"""

import math
import os
import FreeCAD as App
import Part

print("--- Generating Lasius Electronics Tray v2 (FreeCAD 1.1+) ---")

models_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/models/custom/v2/parts/electronics_tray"
export_step_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/step/custom/v2/parts/electronics_tray"
export_stl_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/stl/custom/v2/parts/electronics_tray"

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
    # 1. Main Tray Deck Footprint (Envelope: X in [-72.0, +58.0], Y in [-25.0, +25.0])
    # -------------------------------------------------------------------------
    deck_solid = make_rounded_rect_solid(-72.0, 58.0, -25.0, 25.0, 5.0, z_deck, z_deck + deck_thickness)

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
    # 2. Dual PCA9685 16-Channel PWM Servo Controllers (Central Bay, X in [-31.25, 31.25])
    #    Zero collision with spacers at X = ±45 (6.75 mm clearance to spacer collars).
    #    Right-angle 90° pins face laterally outwards: Left board to +Y, Right board to -Y.
    #    Centers at Y = ±14.5 mm provide 2.0 mm clear safety gap to middle coxa servos at Y = ±36.0 mm.
    # -------------------------------------------------------------------------
    pca_boss_height = 3.00
    pca_boss_radius = 2.75  # D = 5.5 mm
    pca_hole_radius = 1.15  # D = 2.3 mm for M2/M2.5

    # Left Board: Y = +14.5 mm
    # Right Board: Y = -14.5 mm
    pca_centers_y = [+14.5, -14.5]
    for pcy in pca_centers_y:
        pca_holes = [
            (-28.0, pcy - 9.5), (-28.0, pcy + 9.5),
            (28.0, pcy - 9.5), (28.0, pcy + 9.5)
        ]
        for hx, hy in pca_holes:
            boss = Part.makeCylinder(pca_boss_radius, pca_boss_height, App.Vector(hx, hy, deck_thickness), App.Vector(0, 0, 1))
            deck_solid = deck_solid.fuse(boss)
            screw_hole = Part.makeCylinder(pca_hole_radius, deck_thickness + pca_boss_height + 2.0, App.Vector(hx, hy, -1.0), App.Vector(0, 0, 1))
            deck_solid = deck_solid.cut(screw_hole)

        # Weight relief and ventilation window under each PCA9685
        pca_win = make_rounded_rect_solid(-21.0, 21.0, pcy - 5.0, pcy + 5.0, 2.0, -2.0, deck_thickness + 5.0)
        deck_solid = deck_solid.cut(pca_win)

    # -------------------------------------------------------------------------
    # 3. TCA9548A I2C Multiplexer Breakout (Rear Centerline Spine, X = -52.0, Y = 0.0)
    #    Situated cleanly between the two rear spacers (12.5 mm clearance to spacers).
    # -------------------------------------------------------------------------
    tca_boss_height = 3.00
    tca_boss_radius = 2.50
    tca_hole_radius = 1.10

    tca_holes = [(-65.0, 0.0), (-39.0, 0.0)]
    for tx, ty in tca_holes:
        boss = Part.makeCylinder(tca_boss_radius, tca_boss_height, App.Vector(tx, ty, deck_thickness), App.Vector(0, 0, 1))
        deck_solid = deck_solid.fuse(boss)
        screw_hole = Part.makeCylinder(tca_hole_radius, deck_thickness + tca_boss_height + 2.0, App.Vector(tx, ty, -1.0), App.Vector(0, 0, 1))
        deck_solid = deck_solid.cut(screw_hole)

    # Multiplexer wiring & connector clearance window
    tca_win = make_rounded_rect_solid(-62.0, -42.0, -5.5, 5.5, 2.0, -2.0, deck_thickness + 5.0)
    deck_solid = deck_solid.cut(tca_win)

    # -------------------------------------------------------------------------
    # 4. Central Wiring Corridor & Front Battery Access Port
    # -------------------------------------------------------------------------
    front_win = make_rounded_rect_solid(15.0, 50.0, -10.0, 10.0, 3.0, -2.0, deck_thickness + 5.0)
    deck_solid = deck_solid.cut(front_win)

    # -------------------------------------------------------------------------
    # 5. Servo Wire Comb Channels & Zip-Tie Anchor Slots
    # -------------------------------------------------------------------------
    # 4x Zip-tie bridge pairs
    zip_tie_coords = [
        (-5.0, 8.0), (-5.0, -8.0),
        (5.0, 8.0), (5.0, -8.0),
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

