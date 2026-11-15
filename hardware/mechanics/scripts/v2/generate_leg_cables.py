#!/usr/bin/env python3
"""
Generate Lasius 3D Leg Cable Harness & Kinematic Service Loops v2 (Left & Right)
=================================================================================
Hardware-as-Code 3-Tier Architecture:
- Custom v2 Parts:
  * hardware/mechanics/models/custom/v2/parts/cables/leg_cable_harness.FCStd (Left Legs: FL, ML, RL)
  * hardware/mechanics/models/custom/v2/parts/cables/leg_cable_harness_right.FCStd (Right Legs: FR, MR, RR)
  * hardware/mechanics/export/{step,stl}/custom/v2/parts/cables/leg_cable_harness*
Features:
- Models complete physical wire runs with high-visibility colors:
  1. Rocker_Switch_Cable: 2-wire twin lead (Signal yellow, D = 1.80 mm)
     from internal Tibia switch -> Station 1 -> Knee loop -> Femur chamber -> Femur loop -> Coxa -> Chassis.
  2. Knee_Servo_Cable: 3-wire bundled servo lead (D = 2.20 mm, bright orange)
     from Knee Servo -> Station 1 -> Knee loop -> Femur chamber -> Femur loop -> Coxa -> Chassis.
  3. Femur_Servo_Cable: 3-wire bundled servo lead (D = 2.20 mm, crimson red) from Femur Servo in Coxa bracket -> Coxa -> Chassis.
  4. 5x Modeled Nylon Zip-Ties (2.5 mm width, dark charcoal) clamped around the integrated saddles at:
     - Station 1: Tibia Knee Exit (X_leg = 144.85, Y_leg = ±2.50, Z_leg = 19.33)
     - Station 2a: Femur Distal Tunnel (X_leg = 126.50, Y_leg = ±3.65, Z_leg = -1.00)
     - Station 2b: Femur Proximal Tunnel (X_leg = 86.50, Y_leg = ±3.65, Z_leg = -1.00)
     - Station 3: Coxa Bridge Saddle (X_leg = 25.00, Y_leg = ±12.00, Z_leg = -10.00)
     - Station 4: Chassis Entry Saddle (X_leg = 0.00, Y_leg = ±2.50, Z_leg = 8.00)
- Right leg harness is generated directly with mirrored Y-coordinates (Y -> -Y) to ensure 100% clean
  geometry without any OpenCASCADE Frenet-trihedron distortion.
"""

import math
import os
import sys
import FreeCAD as App
import Part

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts/cables"
export_step_dir = f"{repo_root}/hardware/mechanics/export/step/custom/v2/parts/cables"
export_stl_dir = f"{repo_root}/hardware/mechanics/export/stl/custom/v2/parts/cables"

for d in [models_dir, export_step_dir, export_stl_dir]:
    os.makedirs(d, exist_ok=True)

print("--- Generating Lasius Leg Cable Harnesses v2 (Left & Right) ---")


def make_bspline_pipe(points, radius):
    """Generate a smooth cylindrical pipe swept along an interpolated B-spline spine."""
    bs = Part.BSplineCurve()
    bs.interpolate(points)
    wire_spine = Part.Wire([bs.toShape()])
    t0 = bs.tangent(bs.FirstParameter)[0]
    circ = Part.makeCircle(radius, points[0], t0)
    return wire_spine.makePipeShell([Part.Wire([circ])], True, False)


def make_zip_tie_ring(center, axis, radius, width=2.5, thickness=1.2):
    """Generate a small realistic nylon zip-tie ring clamped around a bundle."""
    outer = Part.makeCylinder(radius + thickness, width, center - axis * (0.5 * width), axis)
    inner = Part.makeCylinder(radius, width + 1.0, center - axis * (0.5 * width + 0.5), axis)
    ring = outer.cut(inner)
    head = Part.makeBox(thickness * 1.8, width * 1.2, thickness * 1.8,
                         center + App.Vector(radius * 0.7, -0.6 * width, radius * 0.7))
    return Part.Compound([ring, head])


def mirror_pts(pts):
    """Mirror points across sagittal plane Y -> -Y."""
    return [App.Vector(p.x, -p.y, p.z) for p in pts]


def build_harness(is_right=False):
    pts_switch_l = [
        App.Vector(225.0, 2.5, -95.0),
        App.Vector(180.0, 2.5, -45.0),
        App.Vector(155.0, 2.5, 0.0),
        App.Vector(145.69, 2.50, 16.77),
        App.Vector(144.85, 2.50, 19.33),
        App.Vector(152.00, 3.20, 24.00),
        App.Vector(164.00, 3.40, 18.00),
        App.Vector(166.00, 3.50, 6.00),
        App.Vector(158.00, 3.60, -4.00),
        App.Vector(142.00, 3.65, -5.50),
        App.Vector(126.50, 3.65, -1.00),
        App.Vector(106.50, 3.65, -2.50),
        App.Vector(86.50, 3.65, -1.00),
        App.Vector(72.00, 5.50, -4.50),
        App.Vector(58.00, 7.50, -6.00),
        App.Vector(42.00, 9.50, -8.00),
        App.Vector(25.00, 12.00, -10.00),
        App.Vector(12.00, 8.00, -6.00),
        App.Vector(2.00, 4.00, 0.00),
        App.Vector(-12.00, 2.50, 6.00),
        App.Vector(-24.00, 2.00, 12.00),
    ]

    pts_knee_l = [
        App.Vector(148.30, -15.50, 9.77),
        App.Vector(147.00, -8.00, 14.50),
        App.Vector(145.50, -1.00, 18.00),
        App.Vector(144.85, 2.50, 19.33),
        App.Vector(152.00, 4.80, 24.50),
        App.Vector(164.00, 5.00, 18.50),
        App.Vector(166.00, 5.10, 6.50),
        App.Vector(158.00, 5.20, -3.50),
        App.Vector(142.00, 5.25, -5.00),
        App.Vector(126.50, 3.65, -1.00),
        App.Vector(106.50, 3.65, -1.50),
        App.Vector(86.50, 3.65, -1.00),
        App.Vector(72.00, 6.50, -4.00),
        App.Vector(58.00, 8.50, -5.50),
        App.Vector(42.00, 10.50, -7.50),
        App.Vector(25.00, 12.00, -10.00),
        App.Vector(12.00, 9.20, -5.50),
        App.Vector(2.00, 5.20, 0.50),
        App.Vector(-12.00, 3.50, 6.50),
        App.Vector(-24.00, 3.00, 12.50),
    ]

    pts_femur_l = [
        App.Vector(45.00, 2.50, -14.00),
        App.Vector(35.00, 7.50, -12.50),
        App.Vector(25.00, 12.00, -10.00),
        App.Vector(12.00, 10.40, -5.00),
        App.Vector(2.00, 6.40, 1.00),
        App.Vector(-12.00, 4.50, 7.00),
        App.Vector(-24.00, 4.00, 13.00),
    ]

    if is_right:
        pts_switch = mirror_pts(pts_switch_l)
        pts_knee = mirror_pts(pts_knee_l)
        pts_femur = mirror_pts(pts_femur_l)
        sy = -1.0
    else:
        pts_switch = pts_switch_l
        pts_knee = pts_knee_l
        pts_femur = pts_femur_l
        sy = 1.0

    cable_switch = make_bspline_pipe(pts_switch, 0.90)
    cable_knee = make_bspline_pipe(pts_knee, 1.10)
    cable_femur = make_bspline_pipe(pts_femur, 1.10)

    zt1 = make_zip_tie_ring(App.Vector(144.85, 2.50 * sy, 19.33), App.Vector(0.0, sy, 0.0), 3.20)
    zt2a = make_zip_tie_ring(App.Vector(126.50, 3.65 * sy, -1.00), App.Vector(1.0, 0.0, 0.0), 3.40)
    zt2b = make_zip_tie_ring(App.Vector(86.50, 3.65 * sy, -1.00), App.Vector(1.0, 0.0, 0.0), 3.40)
    zt3 = make_zip_tie_ring(App.Vector(25.00, 12.00 * sy, -10.00), App.Vector(0.7, 0.0, 0.7), 4.20)
    zt4 = make_zip_tie_ring(App.Vector(-12.00, 3.50 * sy, 6.50), App.Vector(1.0, 0.0, 0.0), 4.50)
    zip_ties = Part.Compound([zt1, zt2a, zt2b, zt3, zt4])

    return cable_switch, cable_knee, cable_femur, zip_ties


def save_harness_doc(is_right=False):
    suffix = "_right" if is_right else ""
    doc_name = f"leg_cable_harness{suffix}"
    fcstd_out = f"{models_dir}/{doc_name}.FCStd"
    step_out = f"{export_step_dir}/{doc_name}.step"
    stl_out = f"{export_stl_dir}/{doc_name}.stl"

    c_switch, c_knee, c_femur, z_ties = build_harness(is_right)

    try:
        App.closeDocument(doc_name)
    except Exception:
        pass

    doc = App.newDocument(doc_name)

    obj_sw = doc.addObject("Part::Feature", "Rocker_Switch_Cable")
    obj_sw.Label = "1. Rocker Microswitch 2-Wire Cable (AWG28 Signal/GND)"
    obj_sw.Shape = c_switch
    if hasattr(obj_sw, "ViewObject") and obj_sw.ViewObject:
        obj_sw.ViewObject.ShapeColor = (1.00, 0.82, 0.05)  # Signal yellow

    obj_ks = doc.addObject("Part::Feature", "Knee_Servo_Cable")
    obj_ks.Label = "2. Knee Servo 3-Wire Ribbon Cable (Orange/Red/Brown)"
    obj_ks.Shape = c_knee
    if hasattr(obj_ks, "ViewObject") and obj_ks.ViewObject:
        obj_ks.ViewObject.ShapeColor = (0.95, 0.40, 0.05)  # Bright Orange Ribbon

    obj_fs = doc.addObject("Part::Feature", "Femur_Servo_Cable")
    obj_fs.Label = "3. Femur Servo 3-Wire Ribbon Cable"
    obj_fs.Shape = c_femur
    if hasattr(obj_fs, "ViewObject") and obj_fs.ViewObject:
        obj_fs.ViewObject.ShapeColor = (0.85, 0.18, 0.15)  # Crimson Ribbon

    obj_zt = doc.addObject("Part::Feature", "Zip_Ties")
    obj_zt.Label = "4. Clamped Micro-Zip-Ties (2.5 mm Nylon)"
    obj_zt.Shape = z_ties
    if hasattr(obj_zt, "ViewObject") and obj_zt.ViewObject:
        obj_zt.ViewObject.ShapeColor = (0.25, 0.25, 0.25)  # Dark Nylon Ties

    part_harness = doc.addObject("App::Part", "Leg_Cable_Harness")
    label_side = "Right (Mirrored)" if is_right else "Left"
    part_harness.Label = f"Lasius Leg Cable Harness & Strain Reliefs v2 {label_side}"
    for o in part_harness.Origin.OutList:
        if hasattr(o, "Visibility"):
            o.Visibility = False
    part_harness.Origin.Visibility = False
    part_harness.Visibility = True
    part_harness.addObject(obj_sw)
    part_harness.addObject(obj_ks)
    part_harness.addObject(obj_fs)
    part_harness.addObject(obj_zt)

    harness_compound = Part.Compound([c_switch, c_knee, c_femur, z_ties])
    doc.recompute()
    doc.saveAs(fcstd_out)
    harness_compound.exportStep(step_out)
    print(f"✔ Saved & Exported STEP: {fcstd_out} (Valid={harness_compound.isValid()})")

    App.closeDocument(doc_name)


# Generate both
save_harness_doc(is_right=False)
save_harness_doc(is_right=True)
print("--- All Leg Cable Harnesses Generated Successfully ---")
