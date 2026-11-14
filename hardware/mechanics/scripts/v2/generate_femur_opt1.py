#!/usr/bin/env python3
"""
Generate Lasius Femur Concept Option 1: Bionischer Chitin-Panzer
(hardware/mechanics/models/custom/v2/concepts/femur_opt1.FCStd)

Design Specification (Option 1):
- Monolithic smooth aerodynamic carapace dome matching chassis_canopy.FCStd.
- Continuous G1 curvature along X and Y axes, crowning at Z = 22.00 mm.
- 3 bionic rounded 45-degree chevron convection louvers along the spine.
- Option C hold-down sleeves descending onto the ADS1115 PCB at Z = -3.05 mm.
- Graphitschwarz PETG (0.15, 0.15, 0.18).
"""

import math
import os
import sys
import FreeCAD as App
import Part

print("--- Generating Femur Concept Option 1: Bionischer Chitin-Panzer ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts/femur/concepts"
parts_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts/femur"
export_step_dir = f"{repo_root}/hardware/mechanics/export/step/custom/v2/parts/femur/concepts"
export_stl_dir = f"{repo_root}/hardware/mechanics/export/stl/custom/v2/parts/femur/concepts"

fcstd_cover_path = f"{models_dir}/femur_cover_opt1.FCStd"
step_cover_path = f"{export_step_dir}/femur_cover_opt1.step"
stl_cover_path = f"{export_stl_dir}/femur_cover_opt1.stl"

os.makedirs(models_dir, exist_ok=True)
os.makedirs(export_step_dir, exist_ok=True)
os.makedirs(export_stl_dir, exist_ok=True)


def make_chevron_slot(cx, cy, arm_len, width, angle_deg=45.0, z_min=7.0, z_max=25.0):
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
    pill1 = make_pill(p_apex, p_top, r)
    pill2 = make_pill(p_apex, p_bot, r)
    return pill1.fuse(pill2)


def build_femur_shapes_opt1():
    L_femur = 100.00
    R_end = 15.80
    Z_waist = 11.80

    Y_rear_in = -22.00
    Y_front_in = 29.30
    Y_mid = 0.5 * (Y_rear_in + Y_front_in)  # 3.65

    R_vz = (50.0**2 + Z_waist**2 - R_end**2) / (2.0 * (R_end - Z_waist))
    Z_c = R_vz + Z_waist
    xt = R_end * (50.0 / (R_vz + R_end))
    zt = R_end * (Z_c / (R_vz + R_end))

    p_tl = App.Vector(xt, 0.0, zt)
    p_tr = App.Vector(L_femur - xt, 0.0, zt)
    p_bl = App.Vector(xt, 0.0, -zt)
    p_br = App.Vector(L_femur - xt, 0.0, -zt)
    p_left_mid = App.Vector(-R_end, 0.0, 0.0)
    p_right_mid = App.Vector(L_femur + R_end, 0.0, 0.0)
    p_top_mid = App.Vector(50.0, 0.0, Z_waist)
    p_bot_mid = App.Vector(50.0, 0.0, -Z_waist)

    e_xz_left = Part.Edge(Part.ArcOfCircle(p_tl, p_left_mid, p_bl))
    e_xz_bot = Part.Edge(Part.ArcOfCircle(p_bl, p_bot_mid, p_br))
    e_xz_right = Part.Edge(Part.ArcOfCircle(p_br, p_right_mid, p_tr))
    e_xz_top = Part.Edge(Part.ArcOfCircle(p_tr, p_top_mid, p_tl))
    xz_wire = Part.Wire([e_xz_left, e_xz_bot, e_xz_right, e_xz_top])
    envelope_xz = Part.Face(xz_wire).extrude(App.Vector(0.0, 72.0, 0.0))
    envelope_xz.translate(App.Vector(0.0, -32.0, 0.0))

    lid_z_floor = 9.00
    cover_z_base = lid_z_floor + 0.05

    def make_rounded_rect_wire_z(x_min, x_max, y_min, y_max, r_corner, z_val):
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
        v = [App.Vector(px, py, z_val) for px, py in pts]
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
        return Part.Wire(edges)

    def make_rounded_rect_z(x_min, x_max, y_min, y_max, r_corner, z_min, z_max):
        wire = make_rounded_rect_wire_z(x_min, x_max, y_min, y_max, r_corner, z_min)
        return Part.Face(wire).extrude(App.Vector(0.0, 0.0, z_max - z_min))

    # Flange matching femur hourglass silhouette:
    cover_outer = make_rounded_rect_z(28.65, 71.35, Y_mid - 17.35, Y_mid + 17.35, 3.85, cover_z_base, 20.0)
    cover_solid = cover_outer.common(envelope_xz)

    # Downward sealing / alignment lip ring:
    lip_outer = make_rounded_rect_z(33.70, 66.30, Y_mid - 13.30, Y_mid + 13.30, 3.30, lid_z_floor - 1.50, cover_z_base + 0.10)
    lip_inner = make_rounded_rect_z(35.30, 64.70, Y_mid - 11.70, Y_mid + 11.70, 2.00, lid_z_floor - 1.60, cover_z_base + 0.20)
    lip_ring = lip_outer.cut(lip_inner)
    cover_solid = cover_solid.fuse(lip_ring)

    # Option 1: Smooth Bionic Chitin Carapace Dome Loft
    w_dome_out_0 = make_rounded_rect_wire_z(33.80, 66.20, Y_mid - 11.80, Y_mid + 11.80, 4.50, 10.20)
    w_dome_out_1 = make_rounded_rect_wire_z(34.80, 65.20, Y_mid - 11.00, Y_mid + 11.00, 4.00, 13.50)
    w_dome_out_2 = make_rounded_rect_wire_z(36.50, 63.50, Y_mid - 9.80, Y_mid + 9.80, 3.50, 17.00)
    w_dome_out_3 = make_rounded_rect_wire_z(39.50, 60.50, Y_mid - 8.00, Y_mid + 8.00, 3.00, 20.00)
    w_dome_out_4 = make_rounded_rect_wire_z(44.00, 56.00, Y_mid - 5.50, Y_mid + 5.50, 2.50, 22.00)
    dome_outer = Part.makeLoft([w_dome_out_0, w_dome_out_1, w_dome_out_2, w_dome_out_3, w_dome_out_4], True)
    cover_solid = cover_solid.fuse(dome_outer)

    # Carve hollow interior cavity following the aerodynamic canopy loft
    w_dome_in_0 = make_rounded_rect_wire_z(35.50, 64.50, Y_mid - 9.50, Y_mid + 9.50, 2.50, cover_z_base - 0.10)
    w_dome_in_1 = make_rounded_rect_wire_z(36.50, 63.50, Y_mid - 8.80, Y_mid + 8.80, 2.20, 13.50)
    w_dome_in_2 = make_rounded_rect_wire_z(38.00, 62.00, Y_mid - 7.60, Y_mid + 7.60, 2.00, 17.00)
    w_dome_in_3 = make_rounded_rect_wire_z(41.00, 59.00, Y_mid - 6.00, Y_mid + 6.00, 1.80, 19.80)
    dome_inner_void = Part.makeLoft([w_dome_in_0, w_dome_in_1, w_dome_in_2, w_dome_in_3], True)
    cover_solid = cover_solid.cut(dome_inner_void)

    # Option C Hold-Down Sleeves descending from dome ceiling:
    pin_coords = [(39.90, Y_mid + 5.30), (60.10, Y_mid + 5.30)]
    for px_pin, py_pin in pin_coords:
        hd_outer = Part.makeCylinder(2.10, 15.55, App.Vector(px_pin, py_pin, -3.05))
        hd_rib = Part.makeBox(2.40, 5.60, 5.00, App.Vector(px_pin - 1.20, py_pin, 7.60))
        hd_pin_clear = Part.makeCylinder(1.30, 4.00, App.Vector(px_pin, py_pin, -3.50))
        cover_solid = cover_solid.fuse(hd_outer).fuse(hd_rib).cut(hd_pin_clear)

    # 4x M2 countersunk screws:
    screw_coords = [
        (31.8, Y_mid - 13.8),
        (31.8, Y_mid + 13.8),
        (68.2, Y_mid - 13.8),
        (68.2, Y_mid + 13.8),
    ]
    for sx, sy in screw_coords:
        sh_through = Part.makeCylinder(1.10, 10.0, App.Vector(sx, sy, cover_z_base - 1.0))
        sh_csink = Part.makeCone(1.10, 2.10, 1.0, App.Vector(sx, sy, cover_z_base + 1.80))
        sh_head = Part.makeCylinder(2.10, 10.0, App.Vector(sx, sy, cover_z_base + 2.80))
        cover_solid = cover_solid.cut(sh_through).cut(sh_csink).cut(sh_head)

    # 3 subtle rounded 45-degree chevron louvers:
    for dx_slot in [-7.0, 0.0, 7.0]:
        slot = make_chevron_slot(50.0 + dx_slot, Y_mid, 5.5, 2.0, 45.0, 19.0, 24.0)
        cover_solid = cover_solid.cut(slot)

    cover_solid = cover_solid.removeSplitter()
    femur_cover = cover_solid

    print(f"Femur_Cover_Opt1 Valid: {femur_cover.isValid()}, Volume: {femur_cover.Volume:.1f} mm^3, BB: {femur_cover.BoundBox}")

    fcstd_cover_path = f"{models_dir}/femur_cover_opt1.FCStd"
    step_cover_path = f"{export_step_dir}/femur_cover_opt1.step"
    stl_cover_path = f"{export_stl_dir}/femur_cover_opt1.stl"

    doc_name = "femur_cover_opt1"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass

    doc = App.newDocument(doc_name)
    obj_cover = doc.addObject("Part::Feature", "Femur_Cover_Opt1")
    obj_cover.Label = "Femur ADC Chamber Cover Opt 1 (Bionic Chitin-Panzer Dome)"
    obj_cover.Shape = femur_cover

    if hasattr(obj_cover, "ViewObject") and obj_cover.ViewObject is not None:
        obj_cover.ViewObject.Visibility = True
        obj_cover.ViewObject.ShapeColor = (0.15, 0.15, 0.18)

    doc.recompute()
    doc.saveAs(fcstd_cover_path)
    print(f"Saved Concept Model: {fcstd_cover_path}")

    femur_cover.exportStl(stl_cover_path)
    femur_cover.exportStep(step_cover_path)
    print(f"Exported STL: {stl_cover_path}")
    print(f"Exported STEP: {step_cover_path}")

    App.closeDocument(doc_name)


build_femur_shapes_opt1()

