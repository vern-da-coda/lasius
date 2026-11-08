#!/usr/bin/env python3
"""
Generate Lasius Hexapod Monolithic Tibia v2 (Organic Sickle Claw + Hourglass Foot Connected via 4 Curved Corner Struts / "Eckstege")
- Merges Tibia (tibia.FCStd) and Tibia Servo Foot (tibia_servo_foot.FCStd) into a single
  organic 3D-printed structural component (tibia_v2.FCStd)
- Adopts the flowing hourglass curves of the Femur and Tibia claw:
  * The servo is NOT enclosed in a solid box; instead, 4 double-waisted L-profile corner
    struts ("4 geschwungene Eckstege") connect the hourglass-waisted Foot plate
    (Z_local in [-23.00, -20.00] mm) with the Claw (Z_local in [0.00, +7.00] mm)
  * The teardrop cutout window of the Tibia claw remains 100% open and unobstructed
  * Exact servo fit (0.15 mm clearance around the 4 corners, coaxial M4 counter-bearing
    screw seat at (0, 0), and coaxial 4x servo ear mounting holes)
"""

import math
import os
import shutil
import FreeCAD as App
import Part

print("--- Generating Lasius Organic Monolithic Tibia v2 (Claw + 4 Curved Eckstege + Hourglass Foot) ---")

models_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/models"
export_step_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/step/custom/v2/parts"
export_stl_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/stl/custom/v2/parts"

fcstd_tibia_v1_path = f"{models_dir}/custom/v1/parts/tibia.FCStd"
fcstd_tibia_v2_path = f"{models_dir}/custom/v2/parts/tibia.FCStd"

step_tibia_v2_path = f"{export_step_dir}/tibia.step"
stl_tibia_v2_path = f"{export_stl_dir}/tibia.stl"


def make_hourglass_foot_xy(z_min, z_max, dy_waist=4.60):
    x_min, x_max = -34.60, 12.10
    y_out = 13.10
    r_c = 3.20
    k = r_c * (1.0 - 1.0 / math.sqrt(2.0))

    x_w1, x_w2 = -25.00, 2.50
    x_wm = 0.5 * (x_w1 + x_w2)
    y_mid_top = y_out - dy_waist
    y_mid_bot = -y_out + dy_waist

    v = [
        App.Vector(x_min + r_c, y_out, z_min),
        App.Vector(x_w1, y_out, z_min),
        App.Vector(x_wm, y_mid_top, z_min),
        App.Vector(x_w2, y_out, z_min),
        App.Vector(x_max - r_c, y_out, z_min),
        App.Vector(x_max - k, y_out - k, z_min),
        App.Vector(x_max, y_out - r_c, z_min),
        App.Vector(x_max, -y_out + r_c, z_min),
        App.Vector(x_max - k, -y_out + k, z_min),
        App.Vector(x_max - r_c, -y_out, z_min),
        App.Vector(x_w2, -y_out, z_min),
        App.Vector(x_wm, y_mid_bot, z_min),
        App.Vector(x_w1, -y_out, z_min),
        App.Vector(x_min + r_c, -y_out, z_min),
        App.Vector(x_min + k, -y_out + k, z_min),
        App.Vector(x_min, -y_out + r_c, z_min),
        App.Vector(x_min, y_out - r_c, z_min),
        App.Vector(x_min + k, y_out - k, z_min),
    ]
    edges = [
        Part.makeLine(v[0], v[1]),
        Part.Edge(Part.ArcOfCircle(v[1], v[2], v[3])),
        Part.makeLine(v[3], v[4]),
        Part.Edge(Part.ArcOfCircle(v[4], v[5], v[6])),
        Part.makeLine(v[6], v[7]),
        Part.Edge(Part.ArcOfCircle(v[7], v[8], v[9])),
        Part.makeLine(v[9], v[10]),
        Part.Edge(Part.ArcOfCircle(v[10], v[11], v[12])),
        Part.makeLine(v[12], v[13]),
        Part.Edge(Part.ArcOfCircle(v[13], v[14], v[15])),
        Part.makeLine(v[15], v[16]),
        Part.Edge(Part.ArcOfCircle(v[16], v[17], v[0])),
    ]
    return Part.Face(Part.Wire(edges)).extrude(App.Vector(0, 0, z_max - z_min))


def make_xz_side_envelope(y_min=-20.0, y_max=20.0):
    x1, x2 = -34.60, 12.10
    z1, z2 = -23.00, 1.00
    r_b = 3.50
    kb = r_b * (1.0 - 1.0 / math.sqrt(2.0))
    v = [
        App.Vector(x1, z2, 0),
        App.Vector(x2, z2, 0),
        App.Vector(x2, -1.0, 0),
        App.Vector(x2 - 1.1, -10.5, 0),
        App.Vector(x2, -19.0, 0),
        App.Vector(x2, z1 + r_b, 0),
        App.Vector(x2 - kb, z1 + kb, 0),
        App.Vector(x2 - r_b, z1, 0),
        App.Vector(x1 + r_b, z1, 0),
        App.Vector(x1 + kb, z1 + kb, 0),
        App.Vector(x1, z1 + r_b, 0),
        App.Vector(x1, -19.0, 0),
        App.Vector(x1 + 1.1, -10.5, 0),
        App.Vector(x1, -1.0, 0),
    ]
    pts = [App.Vector(p.x, y_min, p.y) for p in v]
    edges = [
        Part.makeLine(pts[0], pts[1]),
        Part.makeLine(pts[1], pts[2]),
        Part.Edge(Part.ArcOfCircle(pts[2], pts[3], pts[4])),
        Part.makeLine(pts[4], pts[5]),
        Part.Edge(Part.ArcOfCircle(pts[5], pts[6], pts[7])),
        Part.makeLine(pts[7], pts[8]),
        Part.Edge(Part.ArcOfCircle(pts[8], pts[9], pts[10])),
        Part.makeLine(pts[10], pts[11]),
        Part.Edge(Part.ArcOfCircle(pts[11], pts[12], pts[13])),
        Part.makeLine(pts[13], pts[0]),
    ]
    return Part.Face(Part.Wire(edges)).extrude(App.Vector(0, y_max - y_min, 0))


def make_yz_end_envelope(x_min=-40.0, x_max=20.0):
    y1, y2 = -13.10, 13.10
    z1, z2 = -23.00, 1.00
    r_b = 2.80
    kb = r_b * (1.0 - 1.0 / math.sqrt(2.0))
    v = [
        App.Vector(y1, z2, 0),
        App.Vector(y2, z2, 0),
        App.Vector(y2, -1.0, 0),
        App.Vector(y2 - 0.9, -10.5, 0),
        App.Vector(y2, -19.5, 0),
        App.Vector(y2, z1 + r_b, 0),
        App.Vector(y2 - kb, z1 + kb, 0),
        App.Vector(y2 - r_b, z1, 0),
        App.Vector(y1 + r_b, z1, 0),
        App.Vector(y1 + kb, z1 + kb, 0),
        App.Vector(y1, z1 + r_b, 0),
        App.Vector(y1, -19.5, 0),
        App.Vector(y1 + 0.9, -10.5, 0),
        App.Vector(y1, -1.0, 0),
    ]
    pts = [App.Vector(x_min, p.x, p.y) for p in v]
    edges = [
        Part.makeLine(pts[0], pts[1]),
        Part.makeLine(pts[1], pts[2]),
        Part.Edge(Part.ArcOfCircle(pts[2], pts[3], pts[4])),
        Part.makeLine(pts[4], pts[5]),
        Part.Edge(Part.ArcOfCircle(pts[5], pts[6], pts[7])),
        Part.makeLine(pts[7], pts[8]),
        Part.Edge(Part.ArcOfCircle(pts[8], pts[9], pts[10])),
        Part.makeLine(pts[10], pts[11]),
        Part.Edge(Part.ArcOfCircle(pts[11], pts[12], pts[13])),
        Part.makeLine(pts[13], pts[0]),
    ]
    return Part.Face(Part.Wire(edges)).extrude(App.Vector(x_max - x_min, 0, 0))


def make_side_cutout_xz(y_start=-20.0, y_len=40.0):
    x1, x2 = -25.80, 3.30
    z_bot = -20.00
    z_top = 0.02
    r_b = 4.50
    kb = r_b * (1.0 - 1.0 / math.sqrt(2.0))
    pts = [
        App.Vector(x1 - 1.2, z_top, y_start),
        App.Vector(x2 + 1.2, z_top, y_start),
        App.Vector(x2, -9.5, y_start),
        App.Vector(x2 + 1.0, z_bot + r_b, y_start),
        App.Vector(x2 + 1.0 - kb, z_bot + kb, y_start),
        App.Vector(x2 + 1.0 - r_b, z_bot, y_start),
        App.Vector(x1 - 1.0 + r_b, z_bot, y_start),
        App.Vector(x1 - 1.0 + kb, z_bot + kb, y_start),
        App.Vector(x1 - 1.0, z_bot + r_b, y_start),
        App.Vector(x1, -9.5, y_start),
    ]
    v = [App.Vector(p.x, p.z, p.y) for p in pts]
    edges = [
        Part.makeLine(v[0], v[1]),
        Part.Edge(Part.ArcOfCircle(v[1], v[2], v[3])),
        Part.Edge(Part.ArcOfCircle(v[3], v[4], v[5])),
        Part.makeLine(v[5], v[6]),
        Part.Edge(Part.ArcOfCircle(v[6], v[7], v[8])),
        Part.Edge(Part.ArcOfCircle(v[8], v[9], v[0])),
    ]
    return Part.Face(Part.Wire(edges)).extrude(App.Vector(0, y_len, 0))


def make_lower_end_cutout_yz(x_start=-36.0, x_len=6.0):
    y1, y2 = -4.80, 4.80
    z_bot = -20.00
    z_top = 0.02
    r_b = 3.20
    kb = r_b * (1.0 - 1.0 / math.sqrt(2.0))
    pts = [
        App.Vector(y1 - 0.8, z_top, x_start),
        App.Vector(y2 + 0.8, z_top, x_start),
        App.Vector(y2, -9.5, x_start),
        App.Vector(y2 + 0.8, z_bot + r_b, x_start),
        App.Vector(y2 + 0.8 - kb, z_bot + kb, x_start),
        App.Vector(y2 + 0.8 - r_b, z_bot, x_start),
        App.Vector(y1 - 0.8 + r_b, z_bot, x_start),
        App.Vector(y1 - 0.8 + kb, z_bot + kb, x_start),
        App.Vector(y1 - 0.8, z_bot + r_b, x_start),
        App.Vector(y1, -9.5, x_start),
    ]
    v = [App.Vector(p.z, p.x, p.y) for p in pts]
    edges = [
        Part.makeLine(v[0], v[1]),
        Part.Edge(Part.ArcOfCircle(v[1], v[2], v[3])),
        Part.Edge(Part.ArcOfCircle(v[3], v[4], v[5])),
        Part.makeLine(v[5], v[6]),
        Part.Edge(Part.ArcOfCircle(v[6], v[7], v[8])),
        Part.Edge(Part.ArcOfCircle(v[8], v[9], v[0])),
    ]
    return Part.Face(Part.Wire(edges)).extrude(App.Vector(x_len, 0, 0))


def build_tibia_v2_shape():
    doc_v1 = App.openDocument(fcstd_tibia_v1_path)
    tibia_v1 = doc_v1.getObject("Tibia_Plate").Shape.copy()

    w_outer = None
    w_cutout = None
    for f in tibia_v1.Faces:
        if abs(f.BoundBox.ZMin - 0.0) < 0.01 and abs(f.BoundBox.ZMax - 0.0) < 0.01:
            w_outer = f.OuterWire
            w_cutout = f.Wires[6]
            break

    # 1. Heal old 1.15 mm shifted servo cutout & 4 mounting holes in tibia_v1 (Z in [0, 7])
    #    while keeping the organic claw cutout window (w_cutout) 100% untouched:
    cutout_prism = Part.Face(w_cutout).extrude(App.Vector(0, 0, 60.0))
    cutout_prism.translate(App.Vector(0, 0, -35.0))
    patch_box = Part.makeBox(52.0, 22.0, 7.0, App.Vector(-36.5, -11.0, 0.0))
    patch_clean = patch_box.common(Part.Face(w_outer).extrude(App.Vector(0, 0, 7.0))).cut(cutout_prism)
    claw_base = tibia_v1.fuse(patch_clean)

    # 2. Build Hourglass Foot + 4 Curved L-Profile Corner Struts ("4 Eckstege"):
    foot_col = make_hourglass_foot_xy(-23.00, 0.50, dy_waist=4.60)
    foot_col = foot_col.common(make_xz_side_envelope()).common(make_yz_end_envelope())
    foot_col = foot_col.cut(make_side_cutout_xz()).cut(make_lower_end_cutout_yz())

    # 3. Organic Teardrop Weight-Relief Window in Foot Bottom Plate (X in [-26.5, -8.5], Y in [-5.0, +5.0], R=4.5):
    k_w = 4.5 * (1.0 - 1.0 / math.sqrt(2.0))
    x1_w, x2_w, y1_w, y2_w, r_w = -26.5, -8.5, -5.0, 5.0, 4.5
    vw = [App.Vector(px, py, -24.0) for px, py in [
        (x1_w + r_w, y2_w), (x2_w - r_w, y2_w), (x2_w - k_w, y2_w - k_w), (x2_w, y2_w - r_w),
        (x2_w, y1_w + r_w), (x2_w - k_w, y1_w + k_w), (x2_w - r_w, y1_w), (x1_w + r_w, y1_w),
        (x1_w + k_w, y1_w + k_w), (x1_w, y1_w + r_w), (x1_w, y2_w - r_w), (x1_w + k_w, y2_w - k_w),
    ]]
    ew = [
        Part.makeLine(vw[0], vw[1]), Part.Edge(Part.ArcOfCircle(vw[1], vw[2], vw[3])),
        Part.makeLine(vw[3], vw[4]), Part.Edge(Part.ArcOfCircle(vw[4], vw[5], vw[6])),
        Part.makeLine(vw[6], vw[7]), Part.Edge(Part.ArcOfCircle(vw[7], vw[8], vw[9])),
        Part.makeLine(vw[9], vw[10]), Part.Edge(Part.ArcOfCircle(vw[10], vw[11], vw[0])),
    ]
    foot_bottom_win = Part.Face(Part.Wire(ew)).extrude(App.Vector(0, 0, 5.0))
    foot_col = foot_col.cut(foot_bottom_win)

    tibia_v2 = claw_base.fuse(foot_col).cut(cutout_prism)

    # 4. Precision Servo Body Pocket (X in [-31.65, +9.15], Y in [-10.15, +10.15], Z in [-20.00, +8.00]):
    servo_pocket = Part.makeBox(40.80, 20.30, 28.00, App.Vector(-31.65, -10.15, -20.00))
    tibia_v2 = tibia_v2.cut(servo_pocket)

    # 5. Servo Cable Exit Slot at upper end (+X in [9.00, 15.00], Y in [-4.50, +4.50], Z in [-20.00, +8.00]):
    cable_slot = Part.makeBox(6.50, 9.00, 28.00, App.Vector(9.00, -4.50, -20.00))
    tibia_v2 = tibia_v2.cut(cable_slot)

    # 6. Coaxial Knee Counter-Bearing M4 Countersunk Screw Seat at (0.00, 0.00):
    screw_shaft = Part.makeCylinder(2.05, 5.0, App.Vector(0.0, 0.0, -24.0))
    screw_cone = Part.makeCone(2.05, 3.10, 1.55, App.Vector(0.0, 0.0, -21.55))
    tibia_v2 = tibia_v2.cut(screw_shaft).cut(screw_cone)

    # 7. 4x Coaxial Servo Mounting Ear Holes at (13.00, +-5.00) and (-35.50, +-5.00):
    for sx, sy in [(13.00, 5.00), (13.00, -5.00), (-35.50, 5.00), (-35.50, -5.00)]:
        ear_hole = Part.makeCylinder(1.25, 12.0, App.Vector(sx, sy, -2.0))
        tibia_v2 = tibia_v2.cut(ear_hole)

    tibia_v2 = tibia_v2.removeSplitter()
    App.closeDocument(doc_v1.Name)
    return tibia_v2


if __name__ in ("__main__", "generate_tibia_v2", "generate_tibia"):
    shape_v2 = build_tibia_v2_shape()
    print(f"Tibia_v2 Valid: {shape_v2.isValid()}, Solids: {len(shape_v2.Solids)}, Volume: {shape_v2.Volume:.1f} mm^3, BB: {shape_v2.BoundBox}")

    os.makedirs(f"{models_dir}/custom/v2/parts", exist_ok=True)
    os.makedirs(export_step_dir, exist_ok=True)
    os.makedirs(export_stl_dir, exist_ok=True)

    doc = App.newDocument("tibia")
    obj = doc.addObject("Part::Feature", "Tibia_v2")
    obj.Label = "Tibia v2 (Monolithic Claw + 4 Curved Eckstege + Hourglass Foot)"
    obj.Shape = shape_v2

    doc.recompute()
    doc.saveAs(fcstd_tibia_v2_path)
    print(f"Saved FreeCAD model: {fcstd_tibia_v2_path}")

    shape_v2.exportStep(step_tibia_v2_path)
    shape_v2.exportStl(stl_tibia_v2_path)
    print(f"Exported STEP & STL: {step_tibia_v2_path}, {stl_tibia_v2_path}")

    App.closeDocument("tibia")
    import sys
    sys.exit(0)
