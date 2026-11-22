#!/usr/bin/env python3
"""
Generate Lasius Hexapod Chassis Belly Pan Frame & Hinged Battery Hatch (custom/v2)
==================================================================================
Purpose & Mechanical Architecture:
  Modular 2-piece protective underbody assembly (3D printed in rugged PETG / PA-CF):
  1. chassis_belly_pan.FCStd (The Fixed Frame):
     - Fastened permanently to the 4 main chassis standoffs (X = ±45.0, Y = ±30.0 mm)
       via M3 DIN 7991 countersunk screws, maintaining 100% structural sandwich prestress
       of the robot chassis during battery maintenance.
     - Smooth boat-hull contoured underside with 30-degree approach ramps front and rear.
     - Rigid front section housing the downward-facing VL53L5CX 9-Zone ToF Terrain Distance
       Sensor at X = +58.0 mm (Look-Ahead Terrain Perception without sensor cable movement).
     - Integrated knuckle hinge lugs along +Y side rail and snap-latch catch along -Y side rail.
  2. chassis_battery_hatch.FCStd (The Swiveling Battery Service Hatch):
     - Fits form-fittingly into the frame aperture (X in [-71.2, +43.2], Y in [-19.0, +19.0 mm]).
     - Interlocking knuckle hinge lugs rotating on a 1.75 mm 3D-printer filament axis.
     - Ergonomic cantilever snap-latch along -Y for completely tool-free, 3-second battery swaps.
     - 4.6 mm deep internal pocket cradling the battery pack from below.
"""

import math
import os
import sys
import FreeCAD as App
import Part

print("--- Generating Lasius Chassis Belly Pan & Hinged Battery Hatch v2 ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts/chassis"
export_step_dir = f"{repo_root}/hardware/mechanics/export/step/custom/v2/parts/chassis"
export_stl_dir = f"{repo_root}/hardware/mechanics/export/stl/custom/v2/parts/chassis"
urdf_mesh_dir = f"{repo_root}/hardware/mechanics/export/urdf/meshes"

for d in [models_dir, urdf_mesh_dir]:
    os.makedirs(d, exist_ok=True)


def make_rounded_rect_solid(x_min, x_max, y_min, y_max, r_corner, z_min, z_max):
    """Constructs a filleted 3D solid prism in the X-Y plane extruded along Z."""
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


# Coordinate conventions:
z_top = -0.02
z_floor = -10.00
z_cavity_floor = -7.60  # leaves 2.40 mm bottom floor thickness
y_hinge = 19.50
z_hinge = -7.60
r_knuckle = 2.20
r_bore = 1.05  # Ø2.10 mm bore for 1.75 mm filament axis

# =============================================================================
# 1. Build Part 1: Chassis_Belly_Pan (The Fixed Frame)
# =============================================================================
def build_belly_frame():
    # 1.1 Main Skid Plate Hull (Top Flange: X in [-88, +88], Y in [-34, +34])
    flange_solid = make_rounded_rect_solid(-88.0, 88.0, -34.0, 34.0, 7.0, -2.40, z_top)

    # 4x Standoff Ears (X = ±45.0, Y = ±30.0)
    for sx in [-45.0, 45.0]:
        for sy in [-30.0, 30.0]:
            ear = Part.makeCylinder(9.5, 2.38, App.Vector(sx, sy, -2.40), App.Vector(0, 0, 1))
            flange_solid = flange_solid.fuse(ear)

    # Central Deep Tub (X in [-88.0, +88.0], Y in [-28.0, +28.0], Z in [-10.00, -2.40])
    tub_solid = make_rounded_rect_solid(-88.0, 88.0, -28.0, 28.0, 5.0, z_floor, -2.40)

    # 30-degree Front and Rear Approach Ramps (between X = ±72.0 and X = ±88.0):
    wedge_f = Part.Face(
        Part.makePolygon([
            App.Vector(72.0, -40.0, z_floor - 0.1),
            App.Vector(90.0, -40.0, z_floor - 0.1),
            App.Vector(90.0, -40.0, -2.40),
            App.Vector(72.0, -40.0, z_floor - 0.1),
        ])
    ).extrude(App.Vector(0.0, 80.0, 0.0))
    wedge_r = Part.Face(
        Part.makePolygon([
            App.Vector(-72.0, -40.0, z_floor - 0.1),
            App.Vector(-90.0, -40.0, -2.40),
            App.Vector(-90.0, -40.0, z_floor - 0.1),
            App.Vector(-72.0, -40.0, z_floor - 0.1),
        ])
    ).extrude(App.Vector(0.0, 80.0, 0.0))
    tub_solid = tub_solid.cut(wedge_f).cut(wedge_r)
    frame_solid = flange_solid.fuse(tub_solid)

    # 1.2 Hollow Internal Cavity
    cavity = make_rounded_rect_solid(-80.0, 80.0, -24.0, 24.0, 4.0, z_cavity_floor, z_top + 2.0)
    frame_solid = frame_solid.cut(cavity)

    # 1.3 Four M3 Countersunk Standoff Mounts (X = ±45.0, Y = ±30.0)
    for sx in [-45.0, 45.0]:
        for sy in [-30.0, 30.0]:
            thru_hole = Part.makeCylinder(1.70, 10.0, App.Vector(sx, sy, -5.0), App.Vector(0, 0, 1))
            csk_cone = Part.makeCone(3.30, 1.70, 1.60, App.Vector(sx, sy, -2.40), App.Vector(0, 0, 1))
            frame_solid = frame_solid.cut(thru_hole).cut(csk_cone)

    # 1.4 Downward-Facing ToF Sensor in Fixed Front Section (X = +58.0 mm, Y = 0.0 mm)
    x_tof = 58.0
    aperture_box = make_rounded_rect_solid(x_tof - 5.0, x_tof + 5.0, -4.0, 4.0, 1.5, z_floor - 4.0, z_cavity_floor + 2.0)
    frame_solid = frame_solid.cut(aperture_box)

    bezel_rim = make_rounded_rect_solid(x_tof - 9.0, x_tof + 9.0, -7.5, 7.5, 2.5, z_floor - 1.50, z_floor)
    bezel_cut = make_rounded_rect_solid(x_tof - 7.0, x_tof + 7.0, -5.5, 5.5, 1.5, z_floor - 2.0, z_floor + 1.0)
    frame_solid = frame_solid.fuse(bezel_rim).cut(bezel_cut)

    boss_h, boss_r, hole_r = 3.20, 2.60, 0.90
    for dx_h in [-10.5, 10.5]:
        for dy_h in [-6.5, 6.5]:
            hx, hy = x_tof + dx_h, dy_h
            boss = Part.makeCylinder(boss_r, boss_h, App.Vector(hx, hy, z_cavity_floor), App.Vector(0, 0, 1))
            pilot = Part.makeCylinder(hole_r, boss_h + 3.0, App.Vector(hx, hy, z_cavity_floor - 1.0), App.Vector(0, 0, 1))
            frame_solid = frame_solid.fuse(boss).cut(pilot)

    wire_slot = make_rounded_rect_solid(x_tof - 9.0, x_tof + 9.0, -10.0, -5.0, 1.5, z_cavity_floor, z_top + 2.0)
    frame_solid = frame_solid.cut(wire_slot)

    # 1.5 Service Hatch Aperture in Frame Floor (X in [-72.0, +44.0], Y in [-19.5, +19.5])
    hatch_aperture = make_rounded_rect_solid(-72.0, 44.0, -19.5, 19.5, 5.0, z_floor - 2.0, z_cavity_floor + 0.1)
    frame_solid = frame_solid.cut(hatch_aperture)

    # Cut clearance pockets in frame for the hatch knuckle lugs:
    # Hatch lugs sit at [-41.2, -12.8] and [6.8, 25.2], so pocket is [-41.6, -12.4] and [6.4, 25.6] with R = 2.50 mm
    for x1, x2 in [(-41.6, -12.4), (6.4, 25.6)]:
        pocket = Part.makeCylinder(2.50, x2 - x1, App.Vector(x1, y_hinge, z_hinge), App.Vector(1, 0, 0))
        frame_solid = frame_solid.cut(pocket)

    # 1.6 Knuckle Hinge Lugs on Frame (+Y Rail at Y = 19.5 mm, Z = -7.6 mm)
    # 3x lugs: [-60.0, -42.0], [-12.0, +6.0], [+26.0, +38.0]
    for x1, x2 in [(-60.0, -42.0), (-12.0, 6.0), (26.0, 38.0)]:
        lug = Part.makeCylinder(r_knuckle, x2 - x1, App.Vector(x1, y_hinge, z_hinge), App.Vector(1, 0, 0))
        frame_solid = frame_solid.fuse(lug)

    # Continuous Bore for 1.75 mm Filament Axis
    bore_frame = Part.makeCylinder(r_bore, 110.0, App.Vector(-65.0, y_hinge, z_hinge), App.Vector(1, 0, 0))
    frame_solid = frame_solid.cut(bore_frame)

    # 1.7 Snap-Latch Catch Groove along -Y Rail (Y in [-22.5, -19.5])
    catch_groove = Part.makeBox(22.0, 3.2, 3.5, App.Vector(-11.0, -22.5, -9.20))
    frame_solid = frame_solid.cut(catch_groove)

    # 1.8 Front & Rear Glide Runners on Fixed Frame
    for ry in [-16.0, 16.0]:
        rib_f = make_rounded_rect_solid(46.0, 66.0, ry - 1.5, ry + 1.5, 1.2, z_floor - 1.20, z_floor)
        rib_r = make_rounded_rect_solid(-76.0, -66.0, ry - 1.5, ry + 1.5, 1.2, z_floor - 1.20, z_floor)
        frame_solid = frame_solid.fuse(rib_f).fuse(rib_r)

    frame_solid = frame_solid.removeSplitter()
    return frame_solid


# =============================================================================
# 2. Build Part 2: Chassis_Battery_Hatch (The Hinged Service Hatch)
# =============================================================================
def build_battery_hatch():
    # 2.1 Base Plate matching aperture with 0.8 mm clearance in X, 0.5 mm in Y
    hatch_base = make_rounded_rect_solid(-71.2, 43.2, -19.0, 19.0, 4.5, z_floor, z_cavity_floor)

    # 2.2 Deep Internal Battery Cradle Rim (cradles battery from below)
    hatch_rim = make_rounded_rect_solid(-71.2, 43.2, -19.0, 19.0, 4.5, z_cavity_floor, -3.50)
    hatch_pocket = make_rounded_rect_solid(-69.7, 41.7, -17.5, 17.5, 3.5, z_cavity_floor, -2.50)
    hatch_rim = hatch_rim.cut(hatch_pocket)
    hatch_solid = hatch_base.fuse(hatch_rim)

    # Cut clearance pockets in hatch for the frame knuckle lugs:
    # Frame lugs sit at [-60.0, -42.0], [-12.0, +6.0], [+26.0, +38.0]
    for x1, x2 in [(-60.5, -41.6), (-12.4, 6.4), (25.6, 38.5)]:
        hatch_pocket_hinge = Part.makeCylinder(2.50, x2 - x1, App.Vector(x1, y_hinge, z_hinge), App.Vector(1, 0, 0))
        hatch_solid = hatch_solid.cut(hatch_pocket_hinge)

    # 2.3 Interlocking Knuckle Hinge Lugs on Hatch (+Y Edge at Y = 19.5 mm, Z = -7.6 mm)
    # 2x lugs: [-41.2, -12.8] and [+6.8, +25.2] (perfect 0.8 mm clearance to frame lugs)
    for x1, x2 in [(-41.2, -12.8), (6.8, 25.2)]:
        lug = Part.makeCylinder(r_knuckle, x2 - x1, App.Vector(x1, y_hinge, z_hinge), App.Vector(1, 0, 0))
        hatch_solid = hatch_solid.fuse(lug)

    # Bore for 1.75 mm Filament Axis
    bore_hatch = Part.makeCylinder(r_bore, 110.0, App.Vector(-65.0, y_hinge, z_hinge), App.Vector(1, 0, 0))
    hatch_solid = hatch_solid.cut(bore_hatch)

    # 2.4 Ergonomic Cantilever Snap-Latch along -Y Edge (X in [-9.0, +9.0])
    # Arm sits with 0.3 mm clearance inside frame catch groove
    latch_arm = Part.makeBox(18.0, 2.00, 2.80, App.Vector(-9.0, -21.00, -8.60))
    latch_hook = Part.makeBox(18.0, 1.00, 1.40, App.Vector(-9.0, -22.00, -7.40))
    latch_chamfer = Part.Face(
        Part.makePolygon([
            App.Vector(-10.0, -22.20, -9.00),
            App.Vector(10.0, -22.20, -9.00),
            App.Vector(10.0, -20.80, -7.40),
            App.Vector(-10.0, -20.80, -7.40),
            App.Vector(-10.0, -22.20, -9.00),
        ])
    ).extrude(App.Vector(0.0, 0.0, 3.0))
    latch = latch_arm.fuse(latch_hook).cut(latch_chamfer)
    hatch_solid = hatch_solid.fuse(latch)

    # 2.5 Underside Sled Runners on Hatch (X in [-65, +40], Y = ±14.0 mm)
    for ry in [-14.0, 14.0]:
        rib = make_rounded_rect_solid(-65.0, 38.0, ry - 1.5, ry + 1.5, 1.2, z_floor - 1.20, z_floor)
        hatch_solid = hatch_solid.fuse(rib)

    hatch_solid = hatch_solid.removeSplitter()
    return hatch_solid


# =============================================================================
# 3. Build & Save Both FreeCAD Parts
# =============================================================================
fcstd_frame_path = f"{models_dir}/chassis_belly_pan.FCStd"
fcstd_hatch_path = f"{models_dir}/chassis_battery_hatch.FCStd"

# 1. Frame Part
frame_solid = build_belly_frame()
doc_frame_name = "chassis_belly_pan"
try:
    App.closeDocument(doc_frame_name)
except Exception:
    pass
doc_frame = App.newDocument(doc_frame_name)
obj_frame = doc_frame.addObject("Part::Feature", "Chassis_Belly_Pan")
obj_frame.Label = "Chassis Belly Pan Frame (Fixed Skid Plate + Look-Ahead ToF)"
obj_frame.Shape = frame_solid
if hasattr(obj_frame, "ViewObject") and obj_frame.ViewObject:
    obj_frame.ViewObject.Visibility = True
    obj_frame.ViewObject.ShapeColor = (0.22, 0.24, 0.27)
doc_frame.recompute()
doc_frame.saveAs(fcstd_frame_path)
obj_frame.Shape.exportStl(f"{urdf_mesh_dir}/chassis_belly_pan.stl")
if "--export" in sys.argv:
    os.makedirs(export_step_dir, exist_ok=True)
    os.makedirs(export_stl_dir, exist_ok=True)
    obj_frame.Shape.exportStep(f"{export_step_dir}/chassis_belly_pan.step")
    obj_frame.Shape.exportStl(f"{export_stl_dir}/chassis_belly_pan.stl")
print(f"✔ Saved Belly Pan Frame -> {fcstd_frame_path} (Valid={frame_solid.isValid()}, Volume={frame_solid.Volume:.1f} mm^3)")
App.closeDocument(doc_frame_name)

# 2. Hatch Part
hatch_solid = build_battery_hatch()
doc_hatch_name = "chassis_battery_hatch"
try:
    App.closeDocument(doc_hatch_name)
except Exception:
    pass
doc_hatch = App.newDocument(doc_hatch_name)
obj_hatch = doc_hatch.addObject("Part::Feature", "Chassis_Battery_Hatch")
obj_hatch.Label = "Chassis Battery Service Hatch (Swiveling, Filament-Hinge & Snap-Latch)"
obj_hatch.Shape = hatch_solid
if hasattr(obj_hatch, "ViewObject") and obj_hatch.ViewObject:
    obj_hatch.ViewObject.Visibility = True
    obj_hatch.ViewObject.ShapeColor = (0.30, 0.32, 0.36)
doc_hatch.recompute()
doc_hatch.saveAs(fcstd_hatch_path)
obj_hatch.Shape.exportStl(f"{urdf_mesh_dir}/chassis_battery_hatch.stl")
if "--export" in sys.argv:
    obj_hatch.Shape.exportStep(f"{export_step_dir}/chassis_battery_hatch.step")
    obj_hatch.Shape.exportStl(f"{export_stl_dir}/chassis_battery_hatch.stl")
print(f"✔ Saved Battery Service Hatch -> {fcstd_hatch_path} (Valid={hatch_solid.isValid()}, Volume={hatch_solid.Volume:.1f} mm^3)")
App.closeDocument(doc_hatch_name)

# 3. Collision Check Frame <-> Hatch
coll = frame_solid.common(hatch_solid).Volume
print(f"  Frame <-> Hatch Assembly Collision Volume: {coll:.4f} mm^3")
if coll <= 1e-4:
    print("  ✅ ZERO COLLISIONS between Belly Pan Frame and Battery Hatch!")
else:
    print(f"  ❌ COLLISION DETECTED: {coll:.4f} mm^3")

os._exit(0)
