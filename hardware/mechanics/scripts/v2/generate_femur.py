#!/usr/bin/env python3
"""
Generate Lasius Hexapod Organic Monolithic Femur & Encapsulated ADS1115 Housing
- Double-ended open-end wrench ("zweiseitiger Maulschlüssel") topology
- Preserves exact kinematic & mounting dimensions:
  * Pivot-to-pivot length: L = 100.00 mm (X = 0.00 to X = 100.00 mm)
  * End head radius: R = 15.80 mm (Total length = 131.60 mm, End height = 31.60 mm)
  * Inner U-jaw span: 51.30 mm (Y = -22.00 mm rear to Y = +29.30 mm front)
  * Bearing & Horn interface planes: Y = -24.00 mm (rear nut seat) and Y = +31.30 mm (front horn seat)
  * Pivot bores: 2x Ø8.00 mm hub/bearing holes + 2x 4 Ø2.00 mm horn holes on Ø16.00 mm BCD
- Tibia-inspired organic hourglass curvature (G1-continuous R = 277.05 mm waist arcs)
  with smooth rounded kidney relief windows in the 4 U-fork cheeks
- Hollow central core encapsulating the leg's ADS1115 16-bit ADC breakout + RC filter
- Flush curved removable top cover (Femur_Cover) with 4x M2 corner bosses
- Integrated internal cable channels (Kabelkanäle) to both U-openings
"""

import math
import os
import FreeCAD as App
import Part

print("--- Generating Lasius Organic Femur with Encapsulated ADS1115 Chamber ---")

models_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/models/custom/v2/parts"
export_step_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/step/custom/v2/parts"
export_stl_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/stl/custom/v2/parts"

fcstd_femur_path = f"{models_dir}/femur.FCStd"
step_femur_path = f"{export_step_dir}/femur.step"
stl_femur_path = f"{export_stl_dir}/femur.stl"
stl_cover_path = f"{export_stl_dir}/femur_cover.stl"


def make_filleted_polygon_2d(pts, r_list):
    """
    Construct a planar Part.Face in XY plane from a list of vertices pts (CCW)
    with each corner i filleted with radius r_list[i].
    """
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
    """
    Map an XY face to XZ plane at Y = y_pos and extrude by y_extrude along Y.
    """
    edges = []
    for e in face_xy.OuterWire.Edges:
        pts = [App.Vector(v.Point.x, y_pos, v.Point.y) for v in e.Vertexes]
        if "Line" in str(type(e.Curve)):
            edges.append(Part.makeLine(pts[0], pts[1]))
        else:
            pm = e.valueAt(0.5 * (e.FirstParameter + e.LastParameter))
            edges.append(Part.Arc(pts[0], App.Vector(pm.x, y_pos, pm.y), pts[1]).toShape())
    return Part.Face(Part.Wire(edges)).extrude(App.Vector(0.0, y_extrude, 0.0))


def make_chevron_slot(cx, cy, arm_len, width, angle_deg=45.0, z_min=7.0, z_max=20.0):
    """
    Construct a 45-degree chevron inspection/ventilation slot in the cover.
    """
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


def build_femur_shapes():
    # =========================================================================
    # 1. Core Kinematic & Dimensional Parameters (mm)
    # =========================================================================
    L_femur = 100.00       # Hip (X=0) to Knee (X=100) pivot distance
    R_end = 15.80          # End circle radius (H_end = 31.60 mm, X = -15.8..115.8)
    Z_waist = 11.80        # Half-height at X = 50.0 mm (Waist height = 23.60 mm)

    # Jaw Y coordinates (Reinforced for 3D Printing in PETG/ABS/ASA):
    # - Original milled G10/FR4/CFK plate was 2.00 mm thick (E ~ 20 GPa).
    # - For 3D-printed polymer (E ~ 2.1 GPa), we increase the U-jaw thickness
    #   by 3x to 6.00 mm (and 6.65 mm at the rear bearing collar), giving a
    #   27x higher area moment of inertia (I ~ t^3) and 9x higher section modulus!
    # - Inner U-opening faces remain at exact kinematic planes Y = -22.00 mm
    #   and Y = +29.30 mm (51.30 mm span).
    Y_rear_out = -28.00    # 6.00 mm solid rear jaw outer face
    Y_rear_seat = -24.00   # Bearing / M4 nut seat plane
    Y_rear_in = -22.00     # Inner rear jaw face
    Y_rear_collar = -21.35 # Integrated inner bearing support collar (clears washer at -21.30)
    Y_front_in = 29.30     # Inner front jaw face (mates flush with servo horn)
    Y_front_seat = 33.30   # 4.00 mm clamping thickness under each M2 screw head
    Y_front_out = 35.30    # 6.00 mm solid front jaw outer face
    Y_mid = 0.5 * (Y_rear_in + Y_front_in)  # +3.65 mm symmetry plane in Y

    # =========================================================================
    # 2. Side Silhouette (X-Z Plane): Pure G1-Continuous Hourglass Profile
    # =========================================================================
    # Tangent circle radius R_vz passing through (50, Z_waist) and externally
    # tangent to R_end circles at (0, 0) and (100, 0):
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
    xz_face = Part.Face(xz_wire)
    envelope_xz = xz_face.extrude(App.Vector(0.0, 72.0, 0.0))
    envelope_xz.translate(App.Vector(0.0, -32.0, 0.0))

    # =========================================================================
    # 3. Top Silhouette (X-Y Plane): Double-Ended Wrench ("Maulschlüssel")
    # =========================================================================
    # Full reinforced jaw width Y in [-28.00, +35.30] (63.30 mm) extends from
    # tips past the U-throat up to X = 27.50 mm (left) and X = 72.50 mm (right),
    # giving the U-fork root massive, notch-free shoulders!
    # Between X = 27.50 and X = 72.50 (the central core), the outer profile
    # tapers smoothly inward by dy_taper = 8.50 mm per side to Y in [-19.50, +26.80]
    # (46.30 mm waist width at X = 50.0 mm) via G1 tangent circular arcs.
    def make_xy_outer_face(z_min=-20.0, z_max=20.0):
        x0, x1 = -18.0, 118.0
        x_sh_l = 27.50
        x_sh_r = 72.50
        dx_h = 0.25 * (x_sh_r - x_sh_l)  # 11.25 mm per quarter-wave
        dy_taper = 8.50
        dy_h = 0.5 * dy_taper            # 4.25 mm
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

    # =========================================================================
    # 4. Cut the Two U-Openings ("Maulschlüssel-Mäuler") at Hip & Knee Ends
    # =========================================================================
    # Inner U-opening has parallel jaw faces at Y = -22.00 and Y = +29.30 (51.30 mm)
    # up to X = 20.00 mm (left) and X = 80.00 mm (right), and then sweeps with a
    # generous R = 6.00 mm concave stress-relief fillet into the 7.50 mm thick
    # throat bulkhead at X = 26.00 / 74.00 mm!
    def make_u_cutout(x_throat, x_outer, r_fillet=6.0, z_min=-22.0, z_max=22.0):
        y1 = Y_rear_in   # -22.00
        y2 = Y_front_in  # +29.30
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

    u_cut_left = make_u_cutout(x_throat=26.00, x_outer=-20.0, r_fillet=6.0)
    u_cut_right = make_u_cutout(x_throat=74.00, x_outer=120.0, r_fillet=6.0)
    base_solid = base_solid.cut(u_cut_left).cut(u_cut_right)

    # Add integrated inner bearing support collars (Ø14.0 mm, Y = -22.00 to -21.35 mm)
    # on the inside of both Rear Jaws so the 3.0 mm wide 684 ball bearing is supported
    # across 2.65 mm of its outer race (total rear boss thickness = 6.65 mm!):
    for px in [0.0, 100.0]:
        collar = Part.makeCylinder(
            7.00,
            Y_rear_collar - Y_rear_in,
            App.Vector(px, Y_rear_in, 0.0),
            App.Vector(0.0, 1.0, 0.0),
        )
        base_solid = base_solid.fuse(collar)

    # =========================================================================
    # 5. 45-Degree Truss Pockets in Cheeks & Symmetrical Flank A-Truss Pockets
    # =========================================================================
    # A. 45-Degree Cheek Truss Pockets (Non-Through, 1.80 mm deep):
    # Instead of simple horizontal teardrops, we carve upper and lower triangulated
    # pockets leaving a 45-degree chevron diagonal rib directly connecting the
    # U-throat bulkheads (X = 26 and X = 74) to the bearing/horn bosses (X = 0 and X = 100).
    # Leaves a solid, continuous 4.20 mm structural inner web!
    p_u1 = App.Vector(13.00, 2.50, 0.0)
    p_u2 = App.Vector(24.50, 11.50, 0.0)
    p_u3 = App.Vector(13.00, 11.50, 0.0)
    fu_left = make_filleted_polygon_2d([p_u1, p_u2, p_u3], 1.60)

    p_d1 = App.Vector(13.00, -2.50, 0.0)
    p_d2 = App.Vector(13.00, -11.50, 0.0)
    p_d3 = App.Vector(24.50, -11.50, 0.0)
    fd_left = make_filleted_polygon_2d([p_d1, p_d2, p_d3], 1.60)

    p_ru1 = App.Vector(87.00, 2.50, 0.0)
    p_ru2 = App.Vector(87.00, 11.50, 0.0)
    p_ru3 = App.Vector(75.50, 11.50, 0.0)
    fu_right = make_filleted_polygon_2d([p_ru1, p_ru2, p_ru3], 1.60)

    p_rd1 = App.Vector(87.00, -2.50, 0.0)
    p_rd2 = App.Vector(75.50, -11.50, 0.0)
    p_rd3 = App.Vector(87.00, -11.50, 0.0)
    fd_right = make_filleted_polygon_2d([p_rd1, p_rd2, p_rd3], 1.60)

    # Cut 1.80 mm deep pockets into Front Cheeks (outer face is Y = 35.30):
    for f in [fu_left, fd_left, fu_right, fd_right]:
        base_solid = base_solid.cut(extrude_face_xz(f, 33.50, 5.0))

    # Cut 1.80 mm deep pockets into Rear Cheeks (outer face is Y = -28.00):
    for f in [fu_left, fd_left, fu_right, fd_right]:
        base_solid = base_solid.cut(extrude_face_xz(f, -30.00, 3.80))

    # B. Central Flank Symmetrical 45-Degree A-Truss Pockets:
    # Sculpted into the massive 9.65 mm outer walls flanking the ADS1115 chamber.
    # Leaves a solid 3.35 mm inner chamber wall to keep the ADC chamber 100% sealed.
    # 1. Central triangle (apex up at X = 50.00, Z = 3.80)
    p_c1 = App.Vector(38.00, -8.50, 0.0)
    p_c2 = App.Vector(62.00, -8.50, 0.0)
    p_c3 = App.Vector(50.00, 3.80, 0.0)
    fc_flank = make_filleted_polygon_2d([p_c1, p_c2, p_c3], 1.60)

    # 2. Left corner triangle (hypotenuse at 45 deg, strut width = 3.20 mm)
    p_l1 = App.Vector(34.50, -7.00, 0.0)
    p_l2 = App.Vector(46.00, 5.00, 0.0)
    p_l3 = App.Vector(34.50, 5.00, 0.0)
    fl_flank = make_filleted_polygon_2d([p_l1, p_l2, p_l3], 1.60)

    # 3. Right corner triangle (mirror across X = 50.0)
    p_r1 = App.Vector(54.00, 5.00, 0.0)
    p_r2 = App.Vector(65.50, -7.00, 0.0)
    p_r3 = App.Vector(65.50, 5.00, 0.0)
    fr_flank = make_filleted_polygon_2d([p_r1, p_r2, p_r3], 1.60)

    # Cut Front Flank (pocket floor at Y = +20.50, inner chamber wall remains 3.35 mm solid):
    for f in [fc_flank, fl_flank, fr_flank]:
        base_solid = base_solid.cut(extrude_face_xz(f, 20.50, 20.00))

    # Cut Rear Flank (pocket floor at Y = -13.20, inner chamber wall remains 3.35 mm solid):
    for f in [fc_flank, fl_flank, fr_flank]:
        base_solid = base_solid.cut(extrude_face_xz(f, -35.00, 21.80))

    # =========================================================================
    # 6. Pivot Hub Bores (2x Ø8.0 mm), Reinforced Horn Bosses & Bearing Seats
    # =========================================================================
    for px in [0.0, 100.0]:
        # Front Jaw: Ø8.00 mm central bore for servo horn hub & central screw access
        hub_front = Part.makeCylinder(4.00, 20.0, App.Vector(px, 20.0, 0.0), App.Vector(0.0, 1.0, 0.0))
        base_solid = base_solid.cut(hub_front)

        # Front Jaw (Servo Horn Mount):
        # Keep the ENTIRE Ø31.60 mm boss at full 6.00 mm thickness (Y = +29.30..+35.30),
        # and only counterbore the 4 individual M2 screw heads (Ø4.30 mm to Y = +33.30),
        # leaving 4.00 mm solid clamping material directly under each M2 screw head
        # and 6.00 mm solid webs everywhere between the holes!
        for dx, dz in [(8.0, 0.0), (-8.0, 0.0), (0.0, 8.0), (0.0, -8.0)]:
            horn_cyl = Part.makeCylinder(1.00, 20.0, App.Vector(px + dx, 20.0, dz), App.Vector(0.0, 1.0, 0.0))
            m2_cbore = Part.makeCylinder(2.15, 5.0, App.Vector(px + dx, Y_front_seat, dz), App.Vector(0.0, 1.0, 0.0))
            base_solid = base_solid.cut(horn_cyl).cut(m2_cbore)

        # Rear Jaw (External-Entry Counter-Bearing Seat for Option A):
        # - Inner retention lip (Y in [-21.65, -21.35], Ø6.60 mm / R=3.30 mm) clears the Ø5.80 mm
        #   shim washer and bearing inner race while stopping the Ø8.00 mm bearing outer race.
        # - Precision Ø8.00 mm bearing seat (Y in [-24.65, -21.65], 3.00 mm wide) pressed from outside.
        # - Outer Ø9.60 mm access counterbore (Y in [-28.00, -24.65]) houses the external M4 screw head
        #   completely recessed inside the rear jaw!
        rear_lip_bore = Part.makeCylinder(3.30, 10.0, App.Vector(px, -30.0, 0.0), App.Vector(0.0, 1.0, 0.0))
        rear_bearing_seat = Part.makeCylinder(4.00, 8.35, App.Vector(px, -21.65, 0.0), App.Vector(0.0, -1.0, 0.0))
        spot_rear = Part.makeCylinder(4.80, 5.0, App.Vector(px, -24.65, 0.0), App.Vector(0.0, -1.0, 0.0))
        base_solid = base_solid.cut(rear_lip_bore).cut(rear_bearing_seat).cut(spot_rear)

    # =========================================================================
    # 7. Encapsulated Central ADS1115 Chamber, Stepped Cover Rebate & Channels
    # =========================================================================
    def make_rounded_rect_z(x_min, x_max, y_min, y_max, r_corner, z_min, z_max):
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

    # A. Outer Lid Rebate (Stepped recess in top +Z face for the flush cover):
    # X in [30.5, 69.5] (39.0 mm), Y in [Y_mid - 16.5, Y_mid + 16.5] (33.0 mm), R=4.5 mm
    lid_z_floor = 9.00
    lid_prism_raw = make_rounded_rect_z(30.5, 69.5, Y_mid - 16.5, Y_mid + 16.5, 4.5, lid_z_floor, 20.0)

    # B. Inner Hollow ADS1115 Chamber Pocket:
    # X in [33.5, 66.5] (33.0 mm), Y in [Y_mid - 13.5, Y_mid + 13.5] (27.0 mm), R=3.5 mm
    # Bottom floor at Z = -7.80 mm leaves a solid 4.00 mm structural bottom wall at the waist!
    chamber_z_floor = -7.80
    chamber_pocket = make_rounded_rect_z(33.5, 66.5, Y_mid - 13.5, Y_mid + 13.5, 3.5, chamber_z_floor, 20.0)

    screw_coords = [
        (33.0, Y_mid - 13.7),
        (33.0, Y_mid + 13.7),
        (67.0, Y_mid - 13.7),
        (67.0, Y_mid + 13.7),
    ]
    boss_pillars = []
    for sx, sy in screw_coords:
        boss = Part.makeCylinder(3.1, lid_z_floor - chamber_z_floor, App.Vector(sx, sy, chamber_z_floor))
        boss_pillars.append(boss)

    chamber_void = chamber_pocket
    for b in boss_pillars:
        chamber_void = chamber_void.cut(b)

    base_solid = base_solid.cut(lid_prism_raw).cut(chamber_void)

    # Add 2x ADS1115 PCB Support Cradles / Stand-offs on the chamber floor (Z = -7.80 to -4.80 mm)
    # Spanning Y in [Y_mid - 5.5, Y_mid + 8.5] leaves a full clearance channel along the front
    # edge (Y = Y_mid - 7.2) for the 10-pin header solder joints, 100nF MLCCs & 10k pull-up!
    cradle_1 = Part.makeBox(3.0, 14.0, 3.0, App.Vector(36.0, Y_mid - 5.5, chamber_z_floor))
    cradle_2 = Part.makeBox(3.0, 14.0, 3.0, App.Vector(61.0, Y_mid - 5.5, chamber_z_floor))
    base_solid = base_solid.fuse(cradle_1).fuse(cradle_2)

    # Drill 4x M2 pilot holes (Ø1.8 mm, depth 8.0 mm) into the 4 cover bosses:
    for sx, sy in screw_coords:
        m2_hole = Part.makeCylinder(0.90, 9.0, App.Vector(sx, sy, lid_z_floor - 8.2))
        base_solid = base_solid.cut(m2_hole)

    # =========================================================================
    # 8. Integrated Cable Channels ("Kabelkanäle")
    # =========================================================================
    # Smooth stadium cable ducts through the left (X = 25.0..35.0) and right (X = 65.0..75.0)
    # U-throat walls connecting both U-openings directly into the encapsulated ADC chamber:
    def make_cable_tunnel_x(x_start, x_end, y_center, z_center, width_y=14.0, height_z=7.0):
        r = 0.5 * height_z  # 3.5 mm
        dy_half = 0.5 * width_y - r  # 3.5 mm
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

    # =========================================================================
    # 9. Build the Flush Curved Removable Top Cover (Femur_Cover)
    # =========================================================================
    cover_outer = make_rounded_rect_z(30.65, 69.35, Y_mid - 16.35, Y_mid + 16.35, 4.35, lid_z_floor, 20.0)
    cover_solid = cover_outer.common(envelope_xz)

    lip_outer = make_rounded_rect_z(33.70, 66.30, Y_mid - 13.30, Y_mid + 13.30, 3.30, lid_z_floor - 1.50, lid_z_floor)
    lip_inner = make_rounded_rect_z(35.30, 64.70, Y_mid - 11.70, Y_mid + 11.70, 2.00, lid_z_floor - 1.60, lid_z_floor + 0.1)
    lip_ring = lip_outer.cut(lip_inner)
    for sx, sy in screw_coords:
        boss_clear = Part.makeCylinder(3.35, 2.0, App.Vector(sx, sy, lid_z_floor - 1.60))
        lip_ring = lip_ring.cut(boss_clear)
    cover_solid = cover_solid.fuse(lip_ring)

    # Drill 4x M2 countersunk through-holes in the cover:
    for sx, sy in screw_coords:
        sh_through = Part.makeCylinder(1.10, 10.0, App.Vector(sx, sy, lid_z_floor - 2.0))
        sh_csink = Part.makeCone(1.10, 2.10, 1.0, App.Vector(sx, sy, lid_z_floor + 1.80))
        sh_head = Part.makeCylinder(2.10, 5.0, App.Vector(sx, sy, lid_z_floor + 2.80))
        cover_solid = cover_solid.cut(sh_through).cut(sh_csink).cut(sh_head)

    # 3 subtle 45-degree chevron inspection / ventilation louvers in the cover center:
    for dx_slot in [-7.0, 0.0, 7.0]:
        slot = make_chevron_slot(50.0 + dx_slot, Y_mid, 5.5, 2.0, 45.0, lid_z_floor - 2.0, 20.0)
        cover_solid = cover_solid.cut(slot)

    # =========================================================================
    # 10. Build the Encapsulated ADS1115 Breakout Board Model (for Assembly)
    # =========================================================================
    pcb_box = Part.makeBox(28.0, 17.0, 1.6, App.Vector(36.0, Y_mid - 8.5, -4.8))
    ic_chip = Part.makeBox(5.0, 4.0, 1.2, App.Vector(47.5, Y_mid - 2.0, -3.2))
    ads_shape = pcb_box.fuse(ic_chip)
    for i in range(10):
        px_pin = 37.3 + i * 2.54
        pin = Part.makeCylinder(0.4, 5.8, App.Vector(px_pin, Y_mid - 7.2, -7.2))
        ads_shape = ads_shape.fuse(pin)

    base_solid = base_solid.removeSplitter()
    cover_solid = cover_solid.removeSplitter()

    return base_solid, cover_solid, ads_shape


if __name__ == "__main__":
    femur_body, femur_cover, ads_module = build_femur_shapes()

    print(f"Femur_Body Valid: {femur_body.isValid()}, Volume: {femur_body.Volume:.1f} mm^3, BB: {femur_body.BoundBox}")
    print(f"Femur_Cover Valid: {femur_cover.isValid()}, Volume: {femur_cover.Volume:.1f} mm^3, BB: {femur_cover.BoundBox}")

    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(export_step_dir, exist_ok=True)
    os.makedirs(export_stl_dir, exist_ok=True)

    doc = App.newDocument("femur")
    obj_body = doc.addObject("Part::Feature", "Femur_Body")
    obj_body.Label = "Femur Housing (Organic Double-Wrench, PETG)"
    obj_body.Shape = femur_body

    obj_cover = doc.addObject("Part::Feature", "Femur_Cover")
    obj_cover.Label = "Femur ADC Chamber Cover (Flush Curved Lid)"
    obj_cover.Shape = femur_cover

    obj_ads = doc.addObject("Part::Feature", "ADS1115_Board")
    obj_ads.Label = "Encapsulated ADS1115 16-Bit Leg ADC (0x48)"
    obj_ads.Shape = ads_module

    obj_comp = doc.addObject("Part::Feature", "Femur_Complete")
    obj_comp.Label = "Femur Complete (Body + Cover)"
    obj_comp.Shape = Part.makeCompound([femur_body, femur_cover])

    doc.recompute()
    doc.saveAs(fcstd_femur_path)
    print(f"Saved FreeCAD model: {fcstd_femur_path}")

    obj_comp.Shape.exportStep(step_femur_path)
    femur_body.exportStl(stl_femur_path)
    femur_cover.exportStl(stl_cover_path)
    print(f"Exported STEP: {step_femur_path}")
    print(f"Exported STL:  {stl_femur_path} & {stl_cover_path}")

    App.closeDocument("femur")
