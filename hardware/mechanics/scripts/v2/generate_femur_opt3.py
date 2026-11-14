#!/usr/bin/env python3
"""
Generate Lasius Femur Concept Option 3: Stealth-Facetten-Canopy
(hardware/mechanics/models/custom/v2/concepts/femur_opt3.FCStd)

Design Specification (Option 3):
- 45-degree faceted canopy structure inspired by aerospace stealth geometry
  and the 45-degree Warren truss lattice of Coxa and Tibia.
- Horizontal spine crest (Firstgrat) at Z = 21.80 mm running along the X-axis (X = 45.5 .. 54.5 mm).
- 45-degree sloping hip facets on the front, rear, and lateral flanks.
- Soft rounded edge fillets (R = 1.50 mm) for FDM printability and bionic chitin feel.
- Forward-pointing 45-degree chevron ventilation louvers along the spine.
- Preserves all critical functional interfaces:
  * 4x M2 countersunk screws at (31.8, Y_mid ± 13.8) and (68.2, Y_mid ± 13.8)
  * Downward sealing / alignment lip ring (Z = 7.50 .. 9.05 mm)
  * Option C hold-down sleeves descending onto the ADS1115 at Z = -3.05 mm
    with internal bores clearing the centering pins.
"""

import math
import os
import sys
import FreeCAD as App
import Part

print("--- Generating Femur Concept Option 3: Stealth-Facetten-Canopy ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts/femur/concepts"
parts_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts/femur"
cots_dir = f"{repo_root}/hardware/mechanics/models/cots"
export_step_dir = f"{repo_root}/hardware/mechanics/export/step/custom/v2/parts/femur/concepts"
export_stl_dir = f"{repo_root}/hardware/mechanics/export/stl/custom/v2/parts/femur/concepts"

fcstd_femur_path = f"{models_dir}/femur_opt3.FCStd"
step_femur_path = f"{export_step_dir}/femur_opt3.step"
stl_cover_path = f"{export_stl_dir}/femur_cover_opt3.stl"

os.makedirs(models_dir, exist_ok=True)
os.makedirs(export_step_dir, exist_ok=True)
os.makedirs(export_stl_dir, exist_ok=True)


def make_filleted_polygon_2d(pts, r_list):
    n = len(pts)
    if isinstance(r_list, (int, float)):
        r_list = [float(r_list)] * n
    tangents_in, tangents_out, arcs = [], [], []
    for i in range(n):
        p_prev, p_curr, p_next = pts[(i - 1) % n], pts[i], pts[(i + 1) % n]
        r = r_list[i]
        v_in = (p_curr - p_prev).normalize()
        v_out = (p_next - p_curr).normalize()
        cross_z = v_in.x * v_out.y - v_in.y * v_out.x
        dot = max(-1.0, min(1.0, v_in.dot(v_out)))
        turn_angle = math.atan2(cross_z, dot)
        half_beta = 0.5 * (math.pi - abs(turn_angle))
        d = 0.0 if half_beta < 1e-4 else r / math.tan(half_beta)
        t1 = p_curr - v_in * d
        t2 = p_curr + v_out * d
        b = (v_out - v_in).normalize()
        if cross_z < 0:
            b = -b
        center = p_curr + b * (r / math.sin(half_beta))
        p_mid = center - b * r
        tangents_in.append(t1)
        tangents_out.append(t2)
        arcs.append(Part.Arc(t1, p_mid, t2).toShape() if d > 1e-4 else None)
    wire_edges = []
    for i in range(n):
        p_start, p_end = tangents_out[i], tangents_in[(i + 1) % n]
        if (p_end - p_start).Length > 1e-4:
            wire_edges.append(Part.makeLine(p_start, p_end))
        if arcs[(i + 1) % n] is not None:
            wire_edges.append(arcs[(i + 1) % n])
    return Part.Face(Part.Wire(wire_edges))


def extrude_face_xz(face_xy, y_pos, y_extrude):
    edges = []
    for e in face_xy.OuterWire.Edges:
        pts = [App.Vector(v.Point.x, y_pos, v.Point.y) for v in e.Vertexes]
        if "Line" in str(type(e.Curve)):
            edges.append(Part.makeLine(pts[0], pts[1]))
        else:
            pm = e.valueAt(0.5 * (e.FirstParameter + e.LastParameter))
            edges.append(Part.Arc(pts[0], App.Vector(pm.x, y_pos, pm.y), pts[1]).toShape())
    return Part.Face(Part.Wire(edges)).extrude(App.Vector(0.0, y_extrude, 0.0))


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


def build_femur_shapes_opt3():
    L_femur = 100.00
    R_end = 15.80
    Z_waist = 11.80

    Y_rear_out = -28.00
    Y_rear_seat = -24.00
    Y_rear_in = -22.00
    Y_rear_collar = -21.35
    Y_front_in = 29.30
    Y_front_seat = 33.30
    Y_front_out = 35.30
    Y_mid = 0.5 * (Y_rear_in + Y_front_in)  # 3.65

    # 1. Envelope XZ
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

    # We reuse the master femur_body from femur.FCStd to ensure 100% exact match
    doc_master = App.openDocument(f"{parts_dir}/femur.FCStd")
    base_solid = doc_master.Femur_Body.Shape.copy()
    ads_module = doc_master.ADS1115_Board.Shape.copy()
    App.closeDocument(doc_master.Name)

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

    # -------------------------------------------------------------------------
    # Option 3: Stealth-Facetten-Canopy
    # -------------------------------------------------------------------------
    # Flange matching femur hourglass silhouette:
    cover_outer = make_rounded_rect_z(28.65, 71.35, Y_mid - 17.35, Y_mid + 17.35, 3.85, cover_z_base, 20.0)
    cover_solid = cover_outer.common(envelope_xz)

    # Downward sealing / alignment lip ring:
    lip_outer = make_rounded_rect_z(33.70, 66.30, Y_mid - 13.30, Y_mid + 13.30, 3.30, lid_z_floor - 1.50, cover_z_base + 0.10)
    lip_inner = make_rounded_rect_z(35.30, 64.70, Y_mid - 11.70, Y_mid + 11.70, 2.00, lid_z_floor - 1.60, cover_z_base + 0.20)
    lip_ring = lip_outer.cut(lip_inner)
    cover_solid = cover_solid.fuse(lip_ring)

    # 45-degree faceted canopy superstructure:
    # Modeled as ruled loft with flat planar facet faces:
    w_f_0 = make_rounded_rect_wire_z(34.20, 65.80, Y_mid - 11.20, Y_mid + 11.20, 2.80, 10.50)
    w_f_1 = make_rounded_rect_wire_z(39.50, 60.50, Y_mid - 5.90, Y_mid + 5.90, 2.00, 15.80)
    w_f_2 = make_rounded_rect_wire_z(44.50, 55.50, Y_mid - 1.50, Y_mid + 1.50, 1.20, 20.20)
    w_f_3 = make_rounded_rect_wire_z(45.50, 54.50, Y_mid - 0.60, Y_mid + 0.60, 0.50, 21.80)

    stealth_dome = Part.makeLoft([w_f_0, w_f_1, w_f_2, w_f_3], True, True)  # solid=True, ruled=True
    cover_solid = cover_solid.fuse(stealth_dome)

    # Faceted inner cavity maintaining consistent 2.0 mm wall thickness:
    w_in_0 = make_rounded_rect_wire_z(36.00, 64.00, Y_mid - 9.20, Y_mid + 9.20, 2.00, cover_z_base - 0.20)
    w_in_1 = make_rounded_rect_wire_z(40.50, 59.50, Y_mid - 4.70, Y_mid + 4.70, 1.40, 15.00)
    w_in_2 = make_rounded_rect_wire_z(44.00, 56.00, Y_mid - 1.20, Y_mid + 1.20, 0.80, 19.50)
    inner_void = Part.makeLoft([w_in_0, w_in_1, w_in_2], True, True)
    cover_solid = cover_solid.cut(inner_void)

    # Option C Hold-Down Sleeves descending from interior ceiling:
    pin_coords = [(39.90, Y_mid + 5.30), (60.10, Y_mid + 5.30)]
    for px_pin, py_pin in pin_coords:
        hd_outer = Part.makeCylinder(2.10, 15.55, App.Vector(px_pin, py_pin, -3.05))
        hd_rib = Part.makeBox(2.40, 5.60, 5.00, App.Vector(px_pin - 1.20, py_pin, 7.60))
        hd_pin_clear = Part.makeCylinder(1.30, 4.00, App.Vector(px_pin, py_pin, -3.50))
        cover_solid = cover_solid.fuse(hd_outer).fuse(hd_rib).cut(hd_pin_clear)

    # 4x M2 countersunk screw holes:
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

    # Stealth 45-degree chevron louvers along the faceted spine:
    for dx_slot in [-5.5, 0.0, 5.5]:
        slot = make_chevron_slot(50.0 + dx_slot, Y_mid, 4.5, 1.8, 45.0, 18.0, 24.0)
        cover_solid = cover_solid.cut(slot)

    cover_solid = cover_solid.removeSplitter()
    return base_solid, cover_solid, ads_module


if __name__ in ("__main__", "generate_femur_opt3"):
    femur_body, femur_cover, ads_module = build_femur_shapes_opt3()

    print(f"Femur_Body Valid: {femur_body.isValid()}, Volume: {femur_body.Volume:.1f} mm^3")
    print(f"Femur_Cover_Opt3 Valid: {femur_cover.isValid()}, Volume: {femur_cover.Volume:.1f} mm^3, BB: {femur_cover.BoundBox}")

    doc_name = "femur_opt3"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass

    doc = App.newDocument(doc_name)
    obj_body = doc.addObject("Part::Feature", "Femur_Body")
    obj_body.Label = "Femur Housing (Organic Double-Wrench, PETG)"
    obj_body.Shape = femur_body

    obj_cover = doc.addObject("Part::Feature", "Femur_Cover_Opt3")
    obj_cover.Label = "Femur ADC Chamber Cover (Stealth-Facetten-Canopy)"
    obj_cover.Shape = femur_cover

    obj_ads = doc.addObject("Part::Feature", "ADS1115_Board")
    obj_ads.Label = "Encapsulated ADS1115 16-Bit Leg ADC (0x48)"
    obj_ads.Shape = ads_module

    obj_comp = doc.addObject("Part::Feature", "Femur_Complete")
    obj_comp.Label = "Femur Complete (Body + Cover Opt 3)"
    obj_comp.Shape = Part.makeCompound([femur_body, femur_cover])

    # Colors
    for obj, col, vis in [
        (obj_body, (0.12, 0.35, 0.65), True),
        (obj_cover, (0.15, 0.15, 0.18), True),
        (obj_ads, (0.04, 0.38, 0.88), True),
        (obj_comp, (0.12, 0.35, 0.65), False),
    ]:
        if hasattr(obj, "ViewObject") and obj.ViewObject is not None:
            obj.ViewObject.Visibility = vis
            obj.ViewObject.ShapeColor = col

    doc.recompute()
    doc.saveAs(fcstd_femur_path)
    print(f"Saved Concept Model: {fcstd_femur_path}")

    femur_cover.exportStl(stl_cover_path)
    obj_comp.Shape.exportStep(step_femur_path)
    print(f"Exported STL: {stl_cover_path}")
    print(f"Exported STEP: {step_femur_path}")

    App.closeDocument(doc_name)
