#!/usr/bin/env python3
"""
Generate Lasius Monolithic Tibia v2
===================================
- Bionic Tibia-Servo-Käfig created analogously to Coxa's Femur-Servo-Käfig:
  * Two lateral cheeks flanking the Torcster NR-645 Knee Servo (Y in [+10.15, +16.35] and [-16.35, -10.15])
  * Cheek tip overhang removed: front of cheeks terminates flush at X = 9.15 mm and merges directly into the claw
  * Outer cheek walls taper in width (in Y) into the central claw trunk at X in [-31.65, -45.00] mm
  * Exact Knie-Servo mounting pads: 4.0 mm bosses at Z in [3.00, 7.00] mm flush with servo ears (Z = +7.00 mm)
  * Cable exit at Z = -20.00 mm 100% unobstructed
  * 6 bionic truss windows mapped 1:1 from Coxa's Femur-Servo cage:
    1. Upper Flank Window (p_fl_t)
    2. Lower Flank Window (p_fl_b)
    3. Inner Upper Triangle (p_chev_t, 45° Chevron half)
    4. Inner Lower Triangle (p_chev_b, 45° Chevron half)
    5. Outer Upper Trapezoid (p_br_t, parallel 45° Warren strut, w = 2.50 mm, R = 1.40 mm)
    6. Outer Lower Trapezoid (p_br_b, parallel 45° Warren strut, w = 2.50 mm, R = 1.40 mm)
  * Inverted Knee counter-bearing seat: internal M4 DIN 439 low-profile hex nut pocket (SW = 7.10 mm)
    with solid retaining shoulder at Z in [-23.00, -22.20] mm
- Centrally mounted Tibia sickle claw (Tibia-Kralle):
  * Central blade thickness 7.00 mm (Z in [-3.00, +4.00] mm), centered at Z = +0.50 mm
  * Full organic contour restored with both beak horns intact
  * Upper horn and U-throat shifted towards the outside (+Y) for full servo swing clearance
  * Teardrop cutout window closed solid for high-torsion shear resistance
"""

import math
import os
import sys
import FreeCAD as App
import Part

print("--- Generating Lasius Monolithic Tibia v2 (Analogous Servo Cage + Central Claw) ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models"
export_step_dir = f"{repo_root}/hardware/mechanics/export/step/custom/v2/parts/tibia"
export_stl_dir = f"{repo_root}/hardware/mechanics/export/stl/custom/v2/parts/tibia"

fcstd_tibia_v2_path = f"{models_dir}/custom/v2/parts/tibia/tibia.FCStd"
step_tibia_v2_path = f"{export_step_dir}/tibia.step"
stl_tibia_v2_path = f"{export_stl_dir}/tibia.stl"


def make_rounded_polygon_wire_2d(pts_radii, map_fn):
    """
    Build a closed 3D Part.Wire from a list of (x, y, radius) 2D vertices.
    Corners with radius > 0 are filleted with exact tangent circular arcs;
    corners with radius == 0 remain sharp.
    """
    n = len(pts_radii)
    pts = [App.Vector(p[0], p[1], 0.0) for p in pts_radii]
    radii = [p[2] for p in pts_radii]

    t_in = []
    t_out = []
    t_mid = []

    for i in range(n):
        p_prev = pts[(i - 1) % n]
        p_curr = pts[i]
        p_next = pts[(i + 1) % n]
        r = radii[i]

        v_in = p_curr - p_prev
        v_out = p_next - p_curr
        v_in.normalize()
        v_out.normalize()

        if r <= 1e-6:
            t_in.append(p_curr)
            t_out.append(p_curr)
            t_mid.append(None)
        else:
            dot = max(-0.999999, min(0.999999, v_in.dot(v_out)))
            alpha = math.acos(dot)
            dt = r * math.tan(0.5 * alpha)
            p1 = p_curr - v_in * dt
            p2 = p_curr + v_out * dt

            bis = v_out - v_in
            bis.normalize()
            dm = r * (1.0 / math.cos(0.5 * alpha) - 1.0)
            pm = p_curr + bis * dm

            t_in.append(p1)
            t_out.append(p2)
            t_mid.append(pm)

    edges = []
    for i in range(n):
        if t_mid[i] is not None:
            edges.append(Part.Arc(map_fn(t_in[i]), map_fn(t_mid[i]), map_fn(t_out[i])).toShape())
        p_a = t_out[i]
        p_b = t_in[(i + 1) % n]
        if (p_b - p_a).Length > 1e-5:
            edges.append(Part.makeLine(map_fn(p_a), map_fn(p_b)))

    return Part.Wire(edges)


def make_g1_cubic_bspline(poles, t_start, t_end):
    """
    Construct a C2-continuous clamped cubic BSplineCurve whose endpoint tangents
    at poles[0] and poles[-1] are strictly colinear with t_start and t_end (0.00 deg kink).
    """
    pts = [
        App.Vector(p[0], p[1], 0.0) if not isinstance(p, App.Vector) else App.Vector(p.x, p.y, 0.0)
        for p in poles
    ]
    ts = App.Vector(t_start.x, t_start.y, 0.0).normalize()
    te = App.Vector(t_end.x, t_end.y, 0.0).normalize()

    d1 = max(1.0, (pts[1] - pts[0]).Length)
    pts[1] = pts[0] + ts * d1

    d2 = max(1.0, (pts[-1] - pts[-2]).Length)
    pts[-2] = pts[-1] - te * d2

    n = len(pts)
    degree = 3
    n_knots = n - degree + 1
    knots = tuple(float(i) / float(n_knots - 1) for i in range(n_knots))
    mults = tuple([4] + [1] * (n_knots - 2) + [4])

    bs = Part.BSplineCurve()
    bs.buildFromPolesMultsKnots(pts, mults, knots, False, degree)
    return bs.toShape()


def circle_tangent_cw(center, pt):
    v = App.Vector(pt.y - center.y, -(pt.x - center.x), 0.0)
    v.normalize()
    return v


def circle_tangent_ccw(center, pt):
    v = App.Vector(-(pt.y - center.y), pt.x - center.x, 0.0)
    v.normalize()
    return v


def make_s_curve_edges_xz(p1, p2):
    """
    Construct a harmonic G1 S-curve between p1 and p2 in the X-Z plane (Y = 0).
    """
    dx = p2.x - p1.x
    dz = p2.z - p1.z
    dx_h = 0.5 * abs(dx)
    dz_h = 0.5 * abs(dz)
    if dz_h < 1e-4:
        return [Part.makeLine(p1, p2)]
    r = (dx_h**2 + dz_h**2) / (2.0 * dz_h)
    p_inf = App.Vector(p1.x + 0.5 * dx, 0.0, p1.z + 0.5 * dz)
    ang = math.atan2(r - dz_h, dx_h)
    sign_x = 1.0 if dx > 0 else -1.0
    sign_z = 1.0 if dz > 0 else -1.0
    pm1 = App.Vector(
        p1.x + sign_x * r * math.sin(0.5 * (math.pi / 2 - ang)),
        0.0,
        p1.z + sign_z * (r - r * math.cos(0.5 * (math.pi / 2 - ang))),
    )
    pm2 = App.Vector(
        p2.x - sign_x * r * math.sin(0.5 * (math.pi / 2 - ang)),
        0.0,
        p2.z - sign_z * (r - r * math.cos(0.5 * (math.pi / 2 - ang))),
    )
    return [Part.Edge(Part.Arc(p1, pm1, p_inf)), Part.Edge(Part.Arc(p_inf, pm2, p2))]


def build_organic_tibia_outer_wire(horn_shift_y=5.0, throat_clearance=4.0):
    """
    Build the complete G1-continuous organic sickle claw outline (at Z = 0),
    adapted with upper horn and U-throat shifted towards the outside (+Y) for full
    servo swing clearance, keeping the lower horn and distal foot sensor chamber intact.
    """
    # Upper horn shifted towards the outside (+Y)
    c2 = App.Vector(17.271, 36.152 + horn_shift_y, 0.0)
    r2 = 1.489
    a2_s = math.atan2(37.610 + horn_shift_y - c2.y, 17.570 - c2.x)
    a2_m = 0.05
    a2_e = math.atan2(34.780 + horn_shift_y - c2.y, 17.850 - c2.x)
    p2_s = App.Vector(c2.x + r2 * math.cos(a2_s), c2.y + r2 * math.sin(a2_s), 0.0)
    p2_m = App.Vector(c2.x + r2 * math.cos(a2_m), c2.y + r2 * math.sin(a2_m), 0.0)
    p2_e = App.Vector(c2.x + r2 * math.cos(a2_e), c2.y + r2 * math.sin(a2_e), 0.0)
    e2 = Part.Arc(p2_s, p2_m, p2_e).toShape()

    # Lower knee horn
    c4 = App.Vector(38.692 + 2.0, 19.268 + 2.0, 0.0)
    r4 = 2.458
    a4_s = math.atan2(21.650 + 2.0 - c4.y, 39.300 + 2.0 - c4.x)
    a4_m = 0.15
    a4_e = math.atan2(17.350 + 2.0 - c4.y, 40.230 + 2.0 - c4.x)
    p4_s = App.Vector(c4.x + r4 * math.cos(a4_s), c4.y + r4 * math.sin(a4_s), 0.0)
    p4_m = App.Vector(c4.x + r4 * math.cos(a4_m), c4.y + r4 * math.sin(a4_m), 0.0)
    p4_e = App.Vector(c4.x + r4 * math.cos(a4_e), c4.y + r4 * math.sin(a4_e), 0.0)
    e4 = Part.Arc(p4_s, p4_m, p4_e).toShape()

    c56 = App.Vector(15.00, -10.00, 0.0)
    r56 = 4.25
    a56_s = 0.06 * math.pi
    a56_m = -0.22 * math.pi
    a56_e = -0.50 * math.pi
    p56_s = App.Vector(c56.x + r56 * math.cos(a56_s), c56.y + r56 * math.sin(a56_s), 0.0)
    p56_m = App.Vector(c56.x + r56 * math.cos(a56_m), c56.y + r56 * math.sin(a56_m), 0.0)
    p56_e = App.Vector(c56.x + r56 * math.cos(a56_e), c56.y + r56 * math.sin(a56_e), 0.0)
    e5b = Part.Arc(p56_s, p56_m, p56_e).toShape()

    # Throat poles opened up with throat_clearance along +Y
    poles3 = [
        p2_e,
        (17.012, 34.366 + horn_shift_y),
        (13.720, 32.826 + horn_shift_y),
        (9.038, 30.847 + horn_shift_y * 0.8),
        (5.089, 28.080 + throat_clearance),
        (3.500, 25.600 + throat_clearance),
        (4.000, 22.498 + throat_clearance),
        (4.500, 19.300 + throat_clearance),
        (5.500, 16.800 + throat_clearance * 0.5),
        (7.500, 15.880 + 2.0),
        (11.500, 16.100 + 2.0),
        (17.500, 16.900 + 2.0),
        (24.500, 18.100 + 2.0),
        (31.500, 19.800 + 2.0),
        (37.500, 21.300 + 2.0),
        p4_s,
    ]
    e3 = make_g1_cubic_bspline(
        poles3, circle_tangent_cw(c2, p2_e), circle_tangent_cw(c4, p4_s)
    )

    poles5 = [
        p4_e,
        (39.00, 16.20 + 2.0),
        (34.00, 12.80 + 1.5),
        (27.50, 7.80 + 1.0),
        (22.50, 2.20 + 0.5),
        (20.10, -2.80),
        (19.50, -6.50),
        p56_s,
    ]
    e5 = make_g1_cubic_bspline(
        poles5, circle_tangent_cw(c4, p4_e), circle_tangent_cw(c56, p56_s)
    )

    p6_e = App.Vector(-36.50, -14.25, 0.0)
    e6 = Part.makeLine(p56_e, p6_e)

    p_spring_cheek = App.Vector(-132.0, -1.5, 0.0)
    p_hub_left = App.Vector(-128.5, -14.0, 0.0)
    p_hub_bot = App.Vector(-121.0, -21.5, 0.0)

    arc_cheek_tip = Part.Arc(p_spring_cheek, App.Vector(-132.2, -7.8, 0.0), p_hub_left).toShape()
    arc_pivot_bot = Part.Arc(p_hub_left, App.Vector(-126.0, -20.2, 0.0), p_hub_bot).toShape()

    poles1 = [
        p_spring_cheek,
        (-129.5, -0.2),
        (-124.5, 2.5),
        (-116.0, 5.8),
        (-106.0, 8.8),
        (-92.0, 12.5),
        (-78.200, 16.948),
        (-62.257, 22.984),
        (-49.101, 28.027),
        (-35.845, 31.870),
        (-23.493, 34.775),
        (-10.498, 36.789 + horn_shift_y * 0.3),
        (-0.008, 37.954 + horn_shift_y * 0.5),
        (7.477, 38.458 + horn_shift_y * 0.8),
        (12.888, 38.362 + horn_shift_y),
        (15.874, 37.981 + horn_shift_y),
        p2_s,
    ]
    t_dorsal_start = App.Vector(1.0, 0.5, 0.0)
    e1 = make_g1_cubic_bspline(poles1, t_dorsal_start, circle_tangent_cw(c2, p2_s))

    poles7 = [
        p6_e,
        (-39.50, -14.25),
        (-44.00, -12.80),
        (-52.50, -9.40),
        (-61.50, -6.80),
        (-69.50, -5.75),
        (-77.50, -6.50),
        (-87.00, -9.50),
        (-96.50, -12.50),
        (-106.50, -16.00),
        (-115.00, -19.50),
        p_hub_bot,
    ]
    t_ventral_end = App.Vector(-1.0, -0.2, 0.0)
    e7 = make_g1_cubic_bspline(poles7, App.Vector(-1.0, 0.0, 0.0), t_ventral_end)

    return Part.Wire([arc_cheek_tip, arc_pivot_bot, e7, e6, e5b, e5, e4, e3, e2, e1])


def build_tibia_servo_cage_cheek_wire(x_front=9.15, x_rear=-45.0):
    """
    Construct the bionic symmetrical cheek wire in the X-Z plane:
    - Tip overhang removed: terminates flush at X = x_front (9.15 mm) to merge directly into the claw.
    - Symmetrical flat crest (Z = +24.00) and tab (Z = -23.00) up to X = -5.50 mm.
    - Harmonic G1 S-curves tapering into apex at X = x_rear (-45.00 mm, Z = +0.50 mm).
    """
    Z_MID = 0.50
    Z_TAB = -23.00
    Z_CREST = +24.00
    X_TAB_END = -5.50

    p_front_top = App.Vector(x_front, 0.0, Z_CREST)
    p_front_bot = App.Vector(x_front, 0.0, Z_TAB)
    e_front_v = [Part.makeLine(p_front_bot, p_front_top)]

    p_crest_end = App.Vector(X_TAB_END, 0.0, Z_CREST)
    e_crest_flat = [Part.makeLine(p_front_top, p_crest_end)]

    p_tab_end = App.Vector(X_TAB_END, 0.0, Z_TAB)
    e_tab_flat = [Part.makeLine(p_tab_end, p_front_bot)]

    p_apex = App.Vector(x_rear, 0.0, Z_MID)
    e_top_s = make_s_curve_edges_xz(p_crest_end, p_apex)
    e_bot_s = make_s_curve_edges_xz(p_apex, p_tab_end)

    all_edges = e_front_v + e_crest_flat + e_top_s + e_bot_s + e_tab_flat
    return Part.Wire(all_edges)


def build_servo_ear_bosses():
    """
    Exact Knie-Servo-Käfig geometry:
    Raised Servo Mounting Pads (Z in [+3.00, +7.00] mm, rising 4.00 mm to mate flush with servo tabs).
    Leaves the bottom cable exit at Z = -20.00 mm 100% free and unobstructed.
    """
    z0, dz = 3.00, 4.00
    map_xy = lambda v: App.Vector(v.x, v.y, z0)

    # Lower servo mount (-X): X in [-38.60, -31.65], Y in [-10.15, +10.15]
    pts_lower = [
        (-31.65, -10.15, 0.00),
        (-38.60, -10.15, 2.60),
        (-38.60, 10.15, 2.60),
        (-31.65, 10.15, 0.00),
    ]
    w_lower = make_rounded_polygon_wire_2d(pts_lower, map_xy)
    boss_lower = Part.Face(w_lower).extrude(App.Vector(0, 0, dz))

    # Upper servo mount (+X): X in [+9.15, +17.80], Y in [-10.15, +10.15]
    pts_upper = [
        (9.15, 10.15, 0.00),
        (17.80, 10.15, 2.60),
        (17.80, -10.15, 2.60),
        (9.15, -10.15, 0.00),
    ]
    w_upper = make_rounded_polygon_wire_2d(pts_upper, map_xy)
    boss_upper = Part.Face(w_upper).extrude(App.Vector(0, 0, dz))

    return boss_lower.fuse(boss_upper)


def make_hex_nut_pocket_z(cx, cy, z_bottom, z_top, sw=7.10):
    """
    Create a hexagonal prism (across flats = sw) for an internal M4 hex nut pocket.
    """
    r_circum = sw / math.sqrt(3.0)
    pts = []
    for i in range(6):
        ang = math.radians(60.0 * i)
        pts.append(App.Vector(cx + r_circum * math.cos(ang), cy + r_circum * math.sin(ang), z_bottom))
    pts.append(pts[0])
    wire = Part.makePolygon(pts)
    return Part.Face(wire).extrude(App.Vector(0, 0, z_top - z_bottom))


def make_filleted_polygon_xz(pts, r_val):
    pts_r = [(p.x, p.z, r_val) for p in pts]
    map_fn = lambda v: App.Vector(v.x, 0.0, v.y)
    w = make_rounded_polygon_wire_2d(pts_r, map_fn)
    return Part.Face(w)


def build_tibia_base_shape():
    """
    Build the canonical monolithic Tibia base shape:
    - Twin servo cage analogous to Coxa's Femur-Servo-Käfig
    - Exact Knie-Servo mounting bosses at Z in [3.00, 7.00] mm (bündig mit Servolasche bei Z = +7.00 mm)
    - Cheek nose overhang removed (flush at X = 9.15 mm merging into claw)
    - Cheek outer walls tapered in width (Y) into the claw trunk
    - Full organic claw shape restored with both beak horns and widened U-throat
    - 6 Coxa-mapped bionic truss windows
    """
    w_cheek = build_tibia_servo_cage_cheek_wire(x_front=9.15, x_rear=-45.0)
    f_cheek = Part.Face(w_cheek)

    # Upper / Dorsal cheek: Y in [+10.15, +16.35] (6.20 mm)
    s_cheek_upper = f_cheek.extrude(App.Vector(0.0, 6.20, 0.0)).translate(App.Vector(0.0, 10.15, 0.0))
    # Lower / Ventral cheek: Y in [-16.35, -10.15] (6.20 mm)
    s_cheek_lower = f_cheek.extrude(App.Vector(0.0, 6.20, 0.0)).translate(App.Vector(0.0, -16.35, 0.0))

    # Bottom Counter-Bearing Tab Plate connecting the two cheeks at Z in [-23.00, -20.00]
    s_tab_bottom = Part.makeBox(9.15 - (-5.50), 2.0 * 16.35, 3.00, App.Vector(-5.50, -16.35, -23.00))

    # Exact Knie-Servo mounting bosses at Z in [3.00, 7.00] mm
    ear_bosses = build_servo_ear_bosses()

    # Central Claw Blade (Z in [-3.00, +4.00], centered at Z = +0.50 mm)
    # Full organic contour restored with widened U-throat
    outer_wire = build_organic_tibia_outer_wire(horn_shift_y=5.0, throat_clearance=4.0)
    claw_central = Part.Face(outer_wire).extrude(App.Vector(0, 0, 7.0)).translate(App.Vector(0, 0, -3.0))

    # Fuse base solid
    tibia_base = (
        claw_central
        .fuse(s_cheek_upper)
        .fuse(s_cheek_lower)
        .fuse(s_tab_bottom)
        .fuse(ear_bosses)
    )

    # Cut Servo Pocket & Seats
    servo_pocket = Part.makeBox(40.80, 20.30, 48.00, App.Vector(-31.65, -10.15, -20.00))
    # Cable exit slot along +X guaranteeing full clearance
    servo_cable_slot = Part.makeBox(12.00, 7.20, 5.00, App.Vector(9.00, -3.60, -20.00))
    screw_bore = Part.makeCylinder(2.05, 6.0, App.Vector(0.0, 0.0, -24.0))
    nut_pocket = make_hex_nut_pocket_z(0.0, 0.0, -22.40, -19.50, sw=7.10)
    tibia_base = tibia_base.cut(servo_pocket).cut(servo_cable_slot).cut(screw_bore).cut(nut_pocket)

    # 4x Servo Mounting Holes (M2.5 tap / M2 through: D = 2.20 mm)
    for sx, sy in [(13.55, 5.00), (13.55, -5.00), (-35.50, 5.00), (-35.50, -5.00)]:
        tibia_base = tibia_base.cut(Part.makeCylinder(1.10, 20.0, App.Vector(sx, sy, -5.00)))

    # 6 Bionic Truss Windows (Coxa Exact 1:1 Mapping)
    R_FILLET = 1.40
    p_fl_t = [App.Vector(8.50, 0.0, 12.00), App.Vector(-3.00, 0.0, 12.00), App.Vector(-3.00, 0.0, 21.50), App.Vector(-1.00, 0.0, 21.50)]
    p_fl_b = [App.Vector(8.50, 0.0, -11.00), App.Vector(-1.00, 0.0, -20.50), App.Vector(-3.00, 0.0, -20.50), App.Vector(-3.00, 0.0, -11.00)]
    p_chev_t = [App.Vector(-8.80, 0.0, 1.75), App.Vector(-26.55, 0.0, 1.75), App.Vector(-8.80, 0.0, 19.50)]
    p_chev_b = [App.Vector(-8.80, 0.0, -18.50), App.Vector(-26.55, 0.0, -0.75), App.Vector(-8.80, 0.0, -0.75)]
    p_br_t = [App.Vector(-10.80, 0.0, 21.04), App.Vector(-30.09, 0.0, 1.75), App.Vector(-33.30, 0.0, 1.75), App.Vector(-33.30, 0.0, 11.30)]
    p_br_b = [App.Vector(-10.80, 0.0, -20.04), App.Vector(-33.30, 0.0, -10.30), App.Vector(-33.30, 0.0, -2.00), App.Vector(-30.09, 0.0, -2.00)]

    for pts in [p_fl_t, p_fl_b, p_chev_t, p_chev_b, p_br_t, p_br_b]:
        f_win = make_filleted_polygon_xz(pts, R_FILLET)
        cut_u = f_win.extrude(App.Vector(0.0, 10.0, 0.0)).translate(App.Vector(0.0, 9.0, 0.0))
        cut_l = f_win.extrude(App.Vector(0.0, -10.0, 0.0)).translate(App.Vector(0.0, -9.0, 0.0))
        tibia_base = tibia_base.cut(cut_u).cut(cut_l)

    # Taper cheeks in width (Y) into claw trunk at X in [-31.65, -45.00]
    pts_taper_u = [
        App.Vector(-31.65, 16.35, 0.0),
        App.Vector(-31.65, 25.00, 0.0),
        App.Vector(-50.00, 25.00, 0.0),
        App.Vector(-45.00, 3.50, 0.0),
        App.Vector(-31.65, 16.35, 0.0),
    ]
    w_taper_u = Part.makePolygon(pts_taper_u)
    cut_taper_u_cheek = Part.Face(w_taper_u).extrude(App.Vector(0, 0, 21.0)).translate(App.Vector(0, 0, 4.0))

    pts_taper_l = [
        App.Vector(-31.65, -16.35, 0.0),
        App.Vector(-31.65, -25.00, 0.0),
        App.Vector(-50.00, -25.00, 0.0),
        App.Vector(-45.00, -3.50, 0.0),
        App.Vector(-31.65, -16.35, 0.0),
    ]
    w_taper_l = Part.makePolygon(pts_taper_l)
    cut_taper_l_cheek = Part.Face(w_taper_l).extrude(App.Vector(0, 0, 22.0)).translate(App.Vector(0, 0, -25.0))

    tibia_base = tibia_base.cut(cut_taper_u_cheek).cut(cut_taper_l_cheek)

    try:
        tibia_base = tibia_base.removeSplitter()
    except Exception:
        pass

    return tibia_base


is_main = (__name__ == "__main__") or (
    len(sys.argv) > 1 and os.path.basename(sys.argv[1]) == os.path.basename(__file__)
)
if is_main:
    shape_v2 = build_tibia_base_shape()
    print(
        f"Tibia_Base Valid: {shape_v2.isValid()}, Solids: {len(shape_v2.Solids)}, "
        f"Volume: {shape_v2.Volume:.1f} mm^3, BB: {shape_v2.BoundBox}"
    )
