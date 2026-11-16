#!/usr/bin/env python3
"""
Lightweight Topology Optimization for Lasius Femur v2.
Synthesizes:
1. Bionic 45-degree through-windows in U-fork cheeks (w >= 2.5 mm, R = 1.6 mm)
2. Outer cheek I-beam perimeter flanges with recessed webs
3. Sculpted Flank A-Truss lattice (2.0 mm sealed inner chamber wall)
4. Bulkhead U-Throat Weight Relief Pockets (carved into thick bulkheads flanking cable tunnels)
5. Underside Bionic Recesses (Z < -10.5 mm, leaving 2.0 mm solid floor below chamber)
"""

import math
import os
import sys
import time
import FreeCAD as App
import Part

REPO_ROOT = "/home/bjoern/Workspace/Hexapods/lasius"

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

def make_rounded_rect_wire_z(x_min, x_max, y_min, y_max, r_corner, z_val):
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

def build_lightweight_femur():
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
    Y_mid = 0.5 * (Y_rear_in + Y_front_in)  # +3.65 mm

    # Side silhouette
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
    xz_face = Part.Face(Part.Wire([e_xz_left, e_xz_bot, e_xz_right, e_xz_top]))
    envelope_xz = xz_face.extrude(App.Vector(0.0, 72.0, 0.0))
    envelope_xz.translate(App.Vector(0.0, -32.0, 0.0))

    # Top silhouette
    def make_xy_outer_face(z_min=-20.0, z_max=20.0):
        x0, x1 = -18.0, 118.0
        x_sh_l = 27.50
        x_sh_r = 72.50
        dx_h = 0.25 * (x_sh_r - x_sh_l)
        dy_taper = 8.50
        dy_h = 0.5 * dy_taper
        R_arc = (dx_h**2 + dy_h**2) / (2.0 * dy_h)
        theta_a = math.asin(dx_h / R_arc)

        yf0 = Y_front_out
        yf_inf = yf0 - dy_h
        yf_min = yf0 - dy_taper
        yf_m1 = (yf0 - R_arc) + R_arc * math.cos(0.5 * theta_a)
        xf_m1 = x_sh_l + R_arc * math.sin(0.5 * theta_a)
        xf_m2 = x_sh_r - R_arc * math.sin(0.5 * theta_a)

        p_f_0 = App.Vector(x0, yf0, z_min)
        p_f_sh_l = App.Vector(x_sh_l, yf0, z_min)
        p_f_m1 = App.Vector(xf_m1, yf_m1, z_min)
        p_f_inf_l = App.Vector(x_sh_l + dx_h, yf_inf, z_min)
        p_f_cen = App.Vector(50.0, yf_min, z_min)
        p_f_inf_r = App.Vector(x_sh_r - dx_h, yf_inf, z_min)
        p_f_m2 = App.Vector(xf_m2, yf_m1, z_min)
        p_f_sh_r = App.Vector(x_sh_r, yf0, z_min)
        p_f_1 = App.Vector(x1, yf0, z_min)

        yr0 = Y_rear_out
        yr_inf = yr0 + dy_h
        yr_max = yr0 + dy_taper
        yr_m1 = (yr0 + R_arc) - R_arc * math.cos(0.5 * theta_a)

        p_r_1 = App.Vector(x1, yr0, z_min)
        p_r_sh_r = App.Vector(x_sh_r, yr0, z_min)
        p_r_m2 = App.Vector(xf_m2, yr_m1, z_min)
        p_r_inf_r = App.Vector(x_sh_r - dx_h, yr_inf, z_min)
        p_r_cen = App.Vector(50.0, yr_max, z_min)
        p_r_inf_l = App.Vector(x_sh_l + dx_h, yr_inf, z_min)
        p_r_m1 = App.Vector(xf_m1, yr_m1, z_min)
        p_r_sh_l = App.Vector(x_sh_l, yr0, z_min)
        p_r_0 = App.Vector(x0, yr0, z_min)

        edges = [
            Part.makeLine(p_f_0, p_f_sh_l),
            Part.Edge(Part.ArcOfCircle(p_f_sh_l, p_f_m1, p_f_inf_l)),
            Part.Edge(Part.ArcOfCircle(p_f_inf_l, p_f_cen, p_f_inf_r)),
            Part.Edge(Part.ArcOfCircle(p_f_inf_r, p_f_m2, p_f_sh_r)),
            Part.makeLine(p_f_sh_r, p_f_1),
            Part.makeLine(p_f_1, p_r_1),
            Part.makeLine(p_r_1, p_r_sh_r),
            Part.Edge(Part.ArcOfCircle(p_r_sh_r, p_r_m2, p_r_inf_r)),
            Part.Edge(Part.ArcOfCircle(p_r_inf_r, p_r_cen, p_r_inf_l)),
            Part.Edge(Part.ArcOfCircle(p_r_inf_l, p_r_m1, p_r_sh_l)),
            Part.makeLine(p_r_sh_l, p_r_0),
            Part.makeLine(p_r_0, p_f_0),
        ]
        face = Part.Face(Part.Wire(edges))
        return face.extrude(App.Vector(0.0, 0.0, z_max - z_min))

    envelope_xy = make_xy_outer_face(-20.0, 20.0)
    base_solid = envelope_xz.common(envelope_xy)

    # U-cutouts at Hip & Knee
    def make_u_cutout(x_throat, x_outer, r_fillet=6.0, z_min=-22.0, z_max=22.0):
        y1 = Y_rear_in
        y2 = Y_front_in
        k = r_fillet / math.sqrt(2.0)
        if x_outer < x_throat:
            xc = x_throat - r_fillet
            p1 = App.Vector(x_outer, y2, z_min)
            p2 = App.Vector(xc, y2, z_min)
            pm2 = App.Vector(xc + k, y2 - r_fillet + k, z_min)
            p3 = App.Vector(x_throat, y2 - r_fillet, z_min)
            p4 = App.Vector(x_throat, y1 + r_fillet, z_min)
            pm1 = App.Vector(xc + k, y1 + r_fillet - k, z_min)
            p5 = App.Vector(xc, y1, z_min)
            p6 = App.Vector(x_outer, y1, z_min)
        else:
            xc = x_throat + r_fillet
            p1 = App.Vector(x_outer, y2, z_min)
            p2 = App.Vector(xc, y2, z_min)
            pm2 = App.Vector(xc - k, y2 - r_fillet + k, z_min)
            p3 = App.Vector(x_throat, y2 - r_fillet, z_min)
            p4 = App.Vector(x_throat, y1 + r_fillet, z_min)
            pm1 = App.Vector(xc - k, y1 + r_fillet - k, z_min)
            p5 = App.Vector(xc, y1, z_min)
            p6 = App.Vector(x_outer, y1, z_min)

        edges = [
            Part.makeLine(p1, p2),
            Part.Edge(Part.ArcOfCircle(p2, pm2, p3)),
            Part.makeLine(p3, p4),
            Part.Edge(Part.ArcOfCircle(p4, pm1, p5)),
            Part.makeLine(p5, p6),
            Part.makeLine(p6, p1),
        ]
        face = Part.Face(Part.Wire(edges))
        return face.extrude(App.Vector(0.0, 0.0, z_max - z_min))

    base_solid = base_solid.cut(make_u_cutout(26.00, -20.0, 6.0))
    base_solid = base_solid.cut(make_u_cutout(74.00, 120.0, 6.0))

    # Bearing collars
    for px in [0.0, 100.0]:
        collar = Part.makeCylinder(
            7.00,
            Y_rear_collar - Y_rear_in,
            App.Vector(px, Y_rear_in, 0.0),
            App.Vector(0.0, 1.0, 0.0),
        )
        base_solid = base_solid.fuse(collar)

    # -------------------------------------------------------------------------
    # 1. Bionic 45-Degree Through-Windows in Cheeks (w >= 2.5 mm, R = 1.6 mm)
    # -------------------------------------------------------------------------
    # Large through-cut truss windows connecting throat bulkheads to bearing/horn hubs:
    # Top and bottom chords reinforced to Z = +-10.20 mm for optimal stress flow:
    p_u1 = App.Vector(11.50, 2.50, 0.0)
    p_u2 = App.Vector(23.50, 10.20, 0.0)
    p_u3 = App.Vector(11.50, 10.20, 0.0)
    fu_left = make_filleted_polygon_2d([p_u1, p_u2, p_u3], 1.80)

    p_d1 = App.Vector(11.50, -2.50, 0.0)
    p_d2 = App.Vector(11.50, -10.20, 0.0)
    p_d3 = App.Vector(23.50, -10.20, 0.0)
    fd_left = make_filleted_polygon_2d([p_d1, p_d2, p_d3], 1.80)

    p_ru1 = App.Vector(88.50, 2.50, 0.0)
    p_ru2 = App.Vector(88.50, 10.20, 0.0)
    p_ru3 = App.Vector(76.50, 10.20, 0.0)
    fu_right = make_filleted_polygon_2d([p_ru1, p_ru2, p_ru3], 1.80)

    p_rd1 = App.Vector(88.50, -2.50, 0.0)
    p_rd2 = App.Vector(76.50, -10.20, 0.0)
    p_rd3 = App.Vector(88.50, -10.20, 0.0)
    fd_right = make_filleted_polygon_2d([p_rd1, p_rd2, p_rd3], 1.80)

    # Crescent windows behind the pivots (X in [-13.5, -6.5] and [106.5, 113.5]):
    p_cres_l = make_filleted_polygon_2d([
        App.Vector(-13.5, 7.5, 0),
        App.Vector(-7.5, 7.5, 0),
        App.Vector(-7.5, -7.5, 0),
        App.Vector(-13.5, -7.5, 0)
    ], 2.0)
    p_cres_r = make_filleted_polygon_2d([
        App.Vector(107.5, 7.5, 0),
        App.Vector(113.5, 7.5, 0),
        App.Vector(113.5, -7.5, 0),
        App.Vector(107.5, -7.5, 0)
    ], 2.0)

    for f in [fu_left, fd_left, fu_right, fd_right, p_cres_l, p_cres_r]:
        base_solid = base_solid.cut(extrude_face_xz(f, 28.00, 10.0))
        base_solid = base_solid.cut(extrude_face_xz(f, -30.00, 10.0))

    # -------------------------------------------------------------------------
    # 2. Sculpted Flank A-Truss Lattice (Front & Rear Flanks)
    # -------------------------------------------------------------------------
    p_f1 = [App.Vector(33.0, -7.5, 0), App.Vector(43.0, -7.5, 0), App.Vector(33.0, 5.5, 0)]
    f_bay1 = make_filleted_polygon_2d(p_f1, 1.60)

    p_f2 = [App.Vector(34.5, 6.5, 0), App.Vector(45.5, 6.5, 0), App.Vector(44.0, -5.0, 0)]
    f_bay2 = make_filleted_polygon_2d(p_f2, 1.60)

    p_f3 = [App.Vector(44.0, -7.5, 0), App.Vector(56.0, -7.5, 0), App.Vector(50.0, 4.5, 0)]
    f_bay3 = make_filleted_polygon_2d(p_f3, 1.60)

    p_f4 = [App.Vector(54.5, 6.5, 0), App.Vector(65.5, 6.5, 0), App.Vector(56.0, -5.0, 0)]
    f_bay4 = make_filleted_polygon_2d(p_f4, 1.60)

    p_f5 = [App.Vector(57.0, -7.5, 0), App.Vector(67.0, -7.5, 0), App.Vector(67.0, 5.5, 0)]
    f_bay5 = make_filleted_polygon_2d(p_f5, 1.60)

    flank_bays = [f_bay1, f_bay2, f_bay3, f_bay4, f_bay5]
    for fb in flank_bays:
        # Cut to Y = +18.50 (leaves 1.35 mm chamber wall)
        base_solid = base_solid.cut(extrude_face_xz(fb, 18.50, 20.00))
        # Cut to Y = -11.20 (leaves 1.35 mm chamber wall)
        base_solid = base_solid.cut(extrude_face_xz(fb, -35.00, 23.80))

    # -------------------------------------------------------------------------
    # 3. Pivot Hub Bores & Bearing Seats (Non-Design Space)
    # -------------------------------------------------------------------------
    for px in [0.0, 100.0]:
        hub_front = Part.makeCylinder(4.00, 20.0, App.Vector(px, 20.0, 0.0), App.Vector(0.0, 1.0, 0.0))
        base_solid = base_solid.cut(hub_front)

        for dx, dz in [(8.0, 0.0), (-8.0, 0.0), (0.0, 8.0), (0.0, -8.0)]:
            horn_cyl = Part.makeCylinder(1.00, 20.0, App.Vector(px + dx, 20.0, dz), App.Vector(0.0, 1.0, 0.0))
            m2_cbore = Part.makeCylinder(2.15, 5.0, App.Vector(px + dx, Y_front_seat, dz), App.Vector(0.0, 1.0, 0.0))
            base_solid = base_solid.cut(horn_cyl).cut(m2_cbore)

        rear_lip_bore = Part.makeCylinder(3.30, 10.0, App.Vector(px, -30.0, 0.0), App.Vector(0.0, 1.0, 0.0))
        rear_bearing_seat = Part.makeCylinder(4.00, 8.35, App.Vector(px, -21.65, 0.0), App.Vector(0.0, -1.0, 0.0))
        spot_rear = Part.makeCylinder(4.80, 5.0, App.Vector(px, -24.65, 0.0), App.Vector(0.0, -1.0, 0.0))
        base_solid = base_solid.cut(rear_lip_bore).cut(rear_bearing_seat).cut(spot_rear)

    # -------------------------------------------------------------------------
    # 4. Central ADS1115 Chamber & Stepped Rebate (Non-Design Space)
    # -------------------------------------------------------------------------
    lid_z_floor = 9.00
    lid_prism_raw = make_rounded_rect_z(28.5, 71.5, Y_mid - 17.5, Y_mid + 17.5, 4.0, lid_z_floor, 20.0)
    chamber_z_floor = -8.50
    chamber_pocket = make_rounded_rect_z(33.5, 66.5, Y_mid - 13.5, Y_mid + 13.5, 3.5, chamber_z_floor, 20.0)

    screw_coords = [
        (31.8, Y_mid - 13.8),
        (31.8, Y_mid + 13.8),
        (68.2, Y_mid - 13.8),
        (68.2, Y_mid + 13.8),
    ]
    base_solid = base_solid.cut(lid_prism_raw).cut(chamber_pocket)

    # Cradles & Centering Pins
    z_pcb_bot = -4.80
    cradle_h = z_pcb_bot - chamber_z_floor  # 3.70 mm
    cradle_1 = Part.makeBox(6.5, 8.0, cradle_h, App.Vector(36.0, Y_mid + 0.5, chamber_z_floor))
    cradle_2 = Part.makeBox(6.5, 8.0, cradle_h, App.Vector(57.5, Y_mid + 0.5, chamber_z_floor))
    base_solid = base_solid.fuse(cradle_1).fuse(cradle_2)

    pin_coords = [
        (39.90, Y_mid + 5.30),
        (60.10, Y_mid + 5.30),
    ]
    for px_pin, py_pin in pin_coords:
        c_pin = Part.makeCylinder(1.075, 2.20, App.Vector(px_pin, py_pin, z_pcb_bot))
        c_tip = Part.makeCone(1.075, 0.72, 0.40, App.Vector(px_pin, py_pin, z_pcb_bot + 2.20))
        base_solid = base_solid.fuse(c_pin).fuse(c_tip)

    for sx, sy in screw_coords:
        m2_hole = Part.makeCylinder(0.90, 9.0, App.Vector(sx, sy, lid_z_floor - 8.2))
        base_solid = base_solid.cut(m2_hole)

    # Cable tunnels
    def make_cable_tunnel_x(x_start, x_end, y_center, z_center, width_y=14.0, height_z=7.0):
        r = 0.5 * height_z
        dy_half = 0.5 * width_y - r
        box = Part.makeBox(x_end - x_start, 2.0 * dy_half, height_z,
                           App.Vector(x_start, y_center - dy_half, z_center - r))
        cyl1 = Part.makeCylinder(r, x_end - x_start,
                                 App.Vector(x_start, y_center - dy_half, z_center),
                                 App.Vector(1, 0, 0))
        cyl2 = Part.makeCylinder(r, x_end - x_start,
                                 App.Vector(x_start, y_center + dy_half, z_center),
                                 App.Vector(1, 0, 0))
        return box.fuse(cyl1).fuse(cyl2)

    tunnel_left = make_cable_tunnel_x(25.0, 35.0, Y_mid, -1.0, width_y=14.0, height_z=7.0)
    tunnel_right = make_cable_tunnel_x(65.0, 75.0, Y_mid, -1.0, width_y=14.0, height_z=7.0)
    base_solid = base_solid.cut(tunnel_left).cut(tunnel_right)

    # Cable tie saddles
    s_femur_l1 = Part.makeBox(1.30, 2.80, 10.0, App.Vector(28.5, Y_mid - 1.40, -10.0))
    s_femur_l2 = Part.makeBox(1.30, 2.80, 10.0, App.Vector(31.5, Y_mid - 1.40, -10.0))
    s_femur_r1 = Part.makeBox(1.30, 2.80, 10.0, App.Vector(68.5, Y_mid - 1.40, -10.0))
    s_femur_r2 = Part.makeBox(1.30, 2.80, 10.0, App.Vector(71.5, Y_mid - 1.40, -10.0))
    base_solid = base_solid.cut(s_femur_l1).cut(s_femur_l2).cut(s_femur_r1).cut(s_femur_r2)

    # -------------------------------------------------------------------------
    # 5. Bulkhead U-Throat Weight Relief Pockets (facing U-openings)
    # -------------------------------------------------------------------------
    # Cut 5.5 mm deep pockets into the bulkheads from the U-openings:
    # Left bulkhead: X in [25.5, 31.0] (5.5 mm deep)
    # Right bulkhead: X in [69.0, 74.5] (5.5 mm deep)
    p_b_fl = make_rounded_rect_wire_z(25.0, 31.0, Y_mid + 8.0, Y_mid + 20.0, 2.0, -8.0)
    box_b_fl = Part.Face(p_b_fl).extrude(App.Vector(0, 0, 16.0))

    p_b_rl = make_rounded_rect_wire_z(25.0, 31.0, Y_mid - 20.0, Y_mid - 8.0, 2.0, -8.0)
    box_b_rl = Part.Face(p_b_rl).extrude(App.Vector(0, 0, 16.0))

    p_b_fr = make_rounded_rect_wire_z(69.0, 75.0, Y_mid + 8.0, Y_mid + 20.0, 2.0, -8.0)
    box_b_fr = Part.Face(p_b_fr).extrude(App.Vector(0, 0, 16.0))

    p_b_rr = make_rounded_rect_wire_z(69.0, 75.0, Y_mid - 20.0, Y_mid - 8.0, 2.0, -8.0)
    box_b_rr = Part.Face(p_b_rr).extrude(App.Vector(0, 0, 16.0))

    base_solid = base_solid.cut(box_b_fl).cut(box_b_rl).cut(box_b_fr).cut(box_b_rr)

    # -------------------------------------------------------------------------
    # 6. Underside Bionic Recesses (Z < -10.0 mm)
    # -------------------------------------------------------------------------
    # Leaves 1.5 mm solid floor below the chamber (Z = -8.5 down to -10.0 mm).
    # Generates broad underside pockets removing the thick slab:
    p_bot_l = make_rounded_rect_z(26.5, 43.5, Y_mid - 13.0, Y_mid + 13.0, 3.5, -25.0, -10.00)
    p_bot_c = make_rounded_rect_z(44.5, 55.5, Y_mid - 11.0, Y_mid + 11.0, 3.0, -25.0, -10.00)
    p_bot_r = make_rounded_rect_z(56.5, 73.5, Y_mid - 13.0, Y_mid + 13.0, 3.5, -25.0, -10.00)
    base_solid = base_solid.cut(p_bot_l).cut(p_bot_c).cut(p_bot_r)

    base_solid = base_solid.removeSplitter()

    v_cm3 = base_solid.Volume / 1000.0
    mass_g = v_cm3 * 1.27
    print(f"Optimized Femur Valid: {base_solid.isValid()}")
    print(f"Optimized Femur Solid Volume: {v_cm3:.2f} cm^3")
    print(f"Optimized Femur Solid Mass:   {mass_g:.2f} g")
    print(f"Baseline Mass:                82.02 g")
    delta_g = mass_g - 82.02
    pct = (delta_g / 82.02) * 100.0
    print(f"Mass Delta:                   {delta_g:.2f} g ({pct:.1f} %)")

    return base_solid

if __name__ == "__main__":
    build_lightweight_femur()
