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
import sys
import zipfile
import FreeCAD as App
import Part

print("--- Generating Lasius Organic Femur with Encapsulated ADS1115 Chamber ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts/femur"
cots_dir = f"{repo_root}/hardware/mechanics/models/cots"
DO_EXPORT = ("--export" in sys.argv)
export_step_dir = f"{repo_root}/hardware/mechanics/export/step/custom/v2/parts/femur"
export_stl_dir = f"{repo_root}/hardware/mechanics/export/stl/custom/v2/parts/femur"

fcstd_femur_path = f"{models_dir}/femur.FCStd"
step_femur_path = f"{export_step_dir}/femur.step"
stl_femur_path = f"{export_stl_dir}/femur.stl"
stl_cover_path = f"{export_stl_dir}/femur_cover.stl"
stl_frame_path = f"{export_stl_dir}/femur_cover_frame.stl"
stl_canopy_path = f"{export_stl_dir}/femur_canopy.stl"


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
    Y_rear_seat = -25.65   # Bearing seat depth 4.00 mm (Y in [-25.65, -21.65])
    Y_rear_in = -22.00     # Inner rear jaw face
    Y_rear_collar = -21.35 # Integrated inner bearing support collar (clears washer at -21.30)
    Y_front_in = 27.00     # Inner front jaw face (recessed servo horn pocket)
    Y_front_horn_seat = 29.30 # Bottom of circular servo horn pocket (depth 2.30 mm)
    Y_front_seat = 31.50   # M2 counterbore seat plane
    Y_front_out = 33.00    # 6.00 mm solid front jaw outer face
    Y_mid = 0.5 * (Y_rear_in + Y_front_in)  # +2.50 mm symmetry plane in Y

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
    # 5. Bionic 45-Degree A-Truss Lattice (Waist Weight Relief Windows)
    # =========================================================================
    # Implements Style-Guide Section 3 compliant 45.0-degree A-truss windows across
    # the front flank (Y in [16.0, 38.0]) and rear flank (Y in [-38.0, -8.5]),
    # harmonizing the visual signature with Coxa (generate_coxa.py) and Tibia
    # (generate_tibia.py) while cutting moving mass and preserving high stiffness:
    # 1. Non-Design Spaces (Style-Guide 5.1 & 5.2):
    #    - Circular end bosses (R = 15.80 mm at Hip X = 0.0 and Knee X = 100.0) and
    #      jaw cheeks (X in [-15.8, 26.0] and [74.0, 115.8]) remain 100% SOLID.
    #    - Throat bulkheads (X in [26.0, 34.0] and [66.0, 74.0]) remain 100% solid,
    #      housing the 4x M2 cover screw pillars without notches.
    # 2. Continuous Chords:
    #    - Bottom tension/compression flange (Z in [-11.80, -7.50 mm], t >= 4.30 mm)
    #      remains unbroken along the entire span.
    #    - Top chord (Z in [+7.50, +11.80 mm], t >= 4.30 mm) remains solid.
    # 3. 45-Degree A-Truss Geometry:
    #    - Uniform strut width w_strut = 2.50 mm (delta_x_45 = 3.536 mm).
    #    - Exact 45.0-degree diagonal struts meeting at the central apex (X = 50.0, Z = +4.96 mm).
    #    - R = 1.40 mm notch-stress-relief fillets at all window corners.
    R_FILLET = 1.40

    # Window 1: Left Upper 45-deg Right Triangle
    p_w1 = [
        App.Vector(34.00, -7.50, 0.0),
        App.Vector(49.00,  7.50, 0.0),
        App.Vector(34.00,  7.50, 0.0),
    ]
    f_w1 = make_filleted_polygon_2d(p_w1, R_FILLET)

    # Window 2: Center 45-deg Isosceles Triangle (A-truss apex pointing up)
    p_w2 = [
        App.Vector(37.54, -7.50, 0.0),
        App.Vector(62.46, -7.50, 0.0),
        App.Vector(50.00,  4.96, 0.0),
    ]
    f_w2 = make_filleted_polygon_2d(p_w2, R_FILLET)

    # Window 3: Right Upper 45-deg Right Triangle
    p_w3 = [
        App.Vector(51.00,  7.50, 0.0),
        App.Vector(66.00, -7.50, 0.0),
        App.Vector(66.00,  7.50, 0.0),
    ]
    f_w3 = make_filleted_polygon_2d(p_w3, R_FILLET)

    # Blind 45-degree A-truss pockets with an unbroken t_seal = 1.60 mm (4 perimeters @ 0.40 mm nozzle)
    # inner dust/dirt protection wall sealing the ADS1115 chamber (Y in [Y_mid - 13.50, Y_mid + 13.50] = [-11.00, +16.00]):
    # - Front flank pocket: Y from +17.60 mm outward to +35.00 mm (pocket depth 6.90..14.26 mm)
    # - Rear flank pocket:  Y from -35.00 mm inward to -12.60 mm (pocket depth 6.90..14.26 mm)
    t_seal = 1.60
    y_chamber_front = Y_mid + 13.50  # +16.00 mm
    y_chamber_rear = Y_mid - 13.50   # -11.00 mm
    y_pocket_front = y_chamber_front + t_seal  # +17.60 mm
    y_pocket_rear = y_chamber_rear - t_seal    # -12.60 mm

    for fw in [f_w1, f_w2, f_w3]:
        cut_f = extrude_face_xz(fw, y_pocket_front, 35.0 - y_pocket_front)
        cut_r = extrude_face_xz(fw, -35.0, y_pocket_rear - (-35.0))
        base_solid = base_solid.cut(cut_f).cut(cut_r)

    # =========================================================================
    # 6. Pivot Hub Bores (2x Ø8.0 mm), Reinforced Horn Bosses & Bearing Seats
    # =========================================================================
    for px in [0.0, 100.0]:
        # Front Jaw: Ø8.00 mm central bore for servo horn hub & central screw access
        hub_front = Part.makeCylinder(4.00, 20.0, App.Vector(px, 20.0, 0.0), App.Vector(0.0, 1.0, 0.0))
        base_solid = base_solid.cut(hub_front)

        # Front Jaw (Servo Horn Pocket):
        # Circular recess Ø25.30 mm (R = 12.65 mm) from Y = Y_front_in (27.00) to Y = Y_front_horn_seat (29.30)
        # to pocket the servo horn by 2.30 mm into the jaw:
        horn_pocket = Part.makeCylinder(
            12.65,
            Y_front_horn_seat - Y_front_in,
            App.Vector(px, Y_front_in, 0.0),
            App.Vector(0.0, 1.0, 0.0),
        )
        base_solid = base_solid.cut(horn_pocket)

        # Front Jaw (Servo Horn Mount Screws):
        # 4x M2 screw holes on Ø16.0 mm BCD with flush counterbores from outer face
        for dx, dz in [(8.0, 0.0), (-8.0, 0.0), (0.0, 8.0), (0.0, -8.0)]:
            horn_cyl = Part.makeCylinder(1.00, 20.0, App.Vector(px + dx, 20.0, dz), App.Vector(0.0, 1.0, 0.0))
            m2_cbore = Part.makeCylinder(2.15, Y_front_out - Y_front_seat + 0.1, App.Vector(px + dx, Y_front_seat, dz), App.Vector(0.0, 1.0, 0.0))
            base_solid = base_solid.cut(horn_cyl).cut(m2_cbore)

        # Rear Jaw (External-Entry Counter-Bearing Seat for Option A):
        # - Inner retention lip (Y in [-21.65, -21.35], Ø6.60 mm / R=3.30 mm) clears the Ø5.80 mm
        #   shim washer and bearing inner race while stopping the Ø8.00 mm bearing outer race.
        # - Precision Ø8.05 mm bearing seat (Y in [-25.65, -21.65], 4.00 mm deep) pressed from outside.
        # - Outer Ø9.60 mm access counterbore (Y in [-28.00, -25.65], 2.35 mm deep) houses the external M4 screw head
        #   completely recessed inside the rear jaw!
        rear_lip_bore = Part.makeCylinder(3.30, 10.0, App.Vector(px, -30.0, 0.0), App.Vector(0.0, 1.0, 0.0))
        rear_bearing_seat = Part.makeCylinder(4.025, 4.00, App.Vector(px, -21.65, 0.0), App.Vector(0.0, -1.0, 0.0))
        spot_rear = Part.makeCylinder(4.80, Y_rear_seat - Y_rear_out + 0.1, App.Vector(px, Y_rear_seat, 0.0), App.Vector(0.0, -1.0, 0.0))
        base_solid = base_solid.cut(rear_lip_bore).cut(rear_bearing_seat).cut(spot_rear)

    # =========================================================================
    # 7. Encapsulated Central ADS1115 Chamber, Stepped Cover Rebate & Channels
    # =========================================================================
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

    # A. Outer Lid Rebate (Stepped recess in top +Z face for the cover skirt):
    # X in [28.5, 71.5] (43.0 mm), Y in [Y_mid - 17.5, Y_mid + 17.5] (35.0 mm), R=4.0 mm
    lid_z_floor = 9.00
    lid_prism_raw = make_rounded_rect_z(28.5, 71.5, Y_mid - 17.5, Y_mid + 17.5, 4.0, lid_z_floor, 20.0)

    # B. Inner Hollow ADS1115 Chamber Pocket:
    # X in [33.5, 66.5] (33.0 mm), Y in [Y_mid - 13.5, Y_mid + 13.5] (27.0 mm), R=3.5 mm
    # Bottom floor at Z = -8.50 mm leaves a solid 3.30 mm bottom wall at the waist
    # while increasing underside clearance under the Z=-4.80 mm PCB to 3.70 mm
    # for 2.5-3.0 mm vertical header tails, solder fillets & 100 nF MLCCs.
    chamber_z_floor = -8.50
    chamber_pocket = make_rounded_rect_z(33.5, 66.5, Y_mid - 13.5, Y_mid + 13.5, 3.5, chamber_z_floor, 20.0)

    # 4x M2 cover corner screws positioned well clear of chamber pocket & cover perimeter
    # (100% enclosed M2 countersinks with >= 0.99 mm outer cover rim, unbroken lip ring)
    screw_coords = [
        (31.8, Y_mid - 13.8),
        (31.8, Y_mid + 13.8),
        (68.2, Y_mid - 13.8),
        (68.2, Y_mid + 13.8),
    ]
    base_solid = base_solid.cut(lid_prism_raw).cut(chamber_pocket)

    # Option C Support Cradles & Vertical Centering Pins (based on ads1115_board.FCStd):
    # PCB (28.0 x 17.0 x 1.6 mm) sits at X=[36.0, 64.0], Y=[Y_mid-8.5, Y_mid+8.5], Z=[-4.80, -3.20].
    # Mounting holes (Ø2.5 mm COTS / Ø2.35 mm real) at X=39.90 & 60.10, Y=Y_mid+5.30.
    # Support cradles span ONLY the back mounting side (Y in [Y_mid+0.5, Y_mid+8.5]), keeping
    # the entire front pin row (Y=Y_mid-7.62..-5.08) + filter network 100% unobstructed below.
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
        # Ø2.15 mm centering pin (R=1.075 mm): 2.20 mm cylindrical body + 0.40 mm tapered lead-in
        c_pin = Part.makeCylinder(1.075, 2.20, App.Vector(px_pin, py_pin, z_pcb_bot))
        c_tip = Part.makeCone(1.075, 0.72, 0.40, App.Vector(px_pin, py_pin, z_pcb_bot + 2.20))
        base_solid = base_solid.fuse(c_pin).fuse(c_tip)

    # Drill 4x blind Ruthex M2 heat-set insert pockets (Ø3.20 x 4.30 mm) + Ø2.10 mm screw tip clearance bore
    # Matches PRINTING_GUIDE.md (24x Ruthex M2 for Femur covers) & tibia.FCStd!
    for sx, sy in screw_coords:
        m2_ruthex = Part.makeCylinder(1.60, 4.40, App.Vector(sx, sy, lid_z_floor - 4.30))
        m2_clear = Part.makeCylinder(1.05, 5.60, App.Vector(sx, sy, lid_z_floor - 5.50))
        base_solid = base_solid.cut(m2_ruthex).cut(m2_clear)

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

    # Smooth chafe-prevention lead-in fillets (R = 1.50 mm >= 1.0 mm) on ALL 4 cable tunnel mouths
    # (X = 26.00 & 74.00 at Hip/Knee U-openings; X = 33.50 & 66.50 inside the ADS1115 chamber):
    mouth_xs = (26.00, 33.50, 66.50, 74.00)
    tunnel_mouth_edges = []
    for e in base_solid.Edges:
        bb = e.BoundBox
        if abs(bb.XMax - bb.XMin) < 0.05 and any(abs(bb.XMin - mx) < 0.08 for mx in mouth_xs):
            if (bb.YMin >= Y_mid - 7.15 and bb.YMax <= Y_mid + 7.15 and
                    bb.ZMin >= -4.65 and bb.ZMax <= 2.65):
                tunnel_mouth_edges.append(e)
    print(f"  Applying R = 1.50 mm chafe-prevention fillets to {len(tunnel_mouth_edges)} cable tunnel mouth edges...")
    assert len(tunnel_mouth_edges) >= 16, f"Expected >= 16 tunnel mouth edges (4x4 stadium loops), got {len(tunnel_mouth_edges)}"
    filleted = base_solid.makeFillet(1.50, tunnel_mouth_edges)
    assert filleted.isValid() and len(filleted.Solids) == 1, "Cable tunnel mouth fillet produced invalid solid!"
    base_solid = filleted

    # Station 2: Integrated Micro-Zip-Tie Saddles centered in Tunnel Floors (for 2.5 mm cable ties)
    # Centered symmetrically in each 7.50 mm bulkhead (leaving >= 1.70 mm clear of R = 1.50 mm mouth fillets!):
    # Left (proximal Coxa side, X in [26.0, 33.5]): X = 28.0..29.3 & 30.5..31.8 mm
    s_femur_l1 = Part.makeBox(1.30, 2.80, 10.0, App.Vector(28.0, Y_mid - 1.40, -10.0))
    s_femur_l2 = Part.makeBox(1.30, 2.80, 10.0, App.Vector(30.5, Y_mid - 1.40, -10.0))
    # Right (distal Knee side, X in [66.5, 74.0]): X = 68.2..69.5 & 70.7..72.0 mm
    s_femur_r1 = Part.makeBox(1.30, 2.80, 10.0, App.Vector(68.2, Y_mid - 1.40, -10.0))
    s_femur_r2 = Part.makeBox(1.30, 2.80, 10.0, App.Vector(70.7, Y_mid - 1.40, -10.0))
    base_solid = base_solid.cut(s_femur_l1).cut(s_femur_l2).cut(s_femur_r1).cut(s_femur_r2)

    base_solid = base_solid.removeSplitter()
    return base_solid


if __name__ in ("__main__", "generate_femur"):
    femur_body = build_femur_shapes()

    print(f"Femur_Body Valid: {femur_body.isValid()}, Volume: {femur_body.Volume:.1f} mm^3, BB: {femur_body.BoundBox}")

    os.makedirs(models_dir, exist_ok=True)
    if DO_EXPORT:
        os.makedirs(export_step_dir, exist_ok=True)
        os.makedirs(export_stl_dir, exist_ok=True)

    try:
        App.closeDocument("femur")
    except Exception:
        pass

    doc = App.newDocument("femur")
    obj_body = doc.addObject("Part::Feature", "Femur_Body")
    obj_body.Label = "Femur Housing (Organic Double-Wrench, PETG)"
    obj_body.Shape = femur_body

    if hasattr(obj_body, "ViewObject") and obj_body.ViewObject is not None:
        obj_body.ViewObject.Visibility = True
        obj_body.ViewObject.ShapeColor = (0.12, 0.35, 0.65)

    doc.recompute()
    doc.saveAs(fcstd_femur_path)
    print(f"Saved FreeCAD model: {fcstd_femur_path}")

    if DO_EXPORT:
        femur_body.exportStep(step_femur_path)
        femur_body.exportStl(stl_femur_path)
        print(f"Exported STEP: {step_femur_path}")
        print(f"Exported STL:  {stl_femur_path}")

    App.closeDocument("femur")
    print("✔ Femur Monolithic Bone Generation Complete")
