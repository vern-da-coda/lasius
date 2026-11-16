#!/usr/bin/env python3
"""
Generate Lasius Monolithic Tibia v2
===================================
- Bionic Tibia-Servo-Käfig created analogously to Coxa's Femur-Servo-Käfig:
  * Two lateral cheeks flanking the Torcster NR-645 Knee Servo (Y in [+10.15, +16.35] and [-16.35, -10.15])
  * Rounded nose apex (R = 4.50 mm) around Knee pivot (0, 0) extending into Femur Knee U-jaw
  * Symmetrical sagittal profile with harmonic G1 S-curves
  * Style Guide Section 3 compliant 45-degree Warren and A-truss windows
  * Inverted Knee counter-bearing seat: internal M4 DIN 439 low-profile hex nut pocket (SW = 7.10 mm)
    with solid retaining shoulder at Z in [-23.00, -22.20] mm
- Centrally mounted Tibia sickle claw (Tibia-Kralle):
  * Central blade thickness 7.00 mm (Z in [-3.00, +4.00] mm), mathematically centered at Z = +0.50 mm
    (Y_leg = +2.50 mm, matching Femur symmetry plane)
  * Teardrop cutout window closed solid for high-torsion shear resistance
  * Monolithic integration between the central claw blade and the flanking servo cage cheeks
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


def build_organic_tibia_outer_wire():
    """
    Build the complete G1-continuous organic sickle claw outline (at Z = 0),
    adapted around the Knee joint and distal foot sensor chamber with 0.00 deg tangent kink.
    """
    c2 = App.Vector(17.271, 36.152, 0.0)
    r2 = 1.489
    a2_s = math.atan2(37.610 - c2.y, 17.570 - c2.x)
    a2_m = 0.05
    a2_e = math.atan2(34.780 - c2.y, 17.850 - c2.x)
    p2_s = App.Vector(c2.x + r2 * math.cos(a2_s), c2.y + r2 * math.sin(a2_s), 0.0)
    p2_m = App.Vector(c2.x + r2 * math.cos(a2_m), c2.y + r2 * math.sin(a2_m), 0.0)
    p2_e = App.Vector(c2.x + r2 * math.cos(a2_e), c2.y + r2 * math.sin(a2_e), 0.0)
    e2 = Part.Arc(p2_s, p2_m, p2_e).toShape()

    c4 = App.Vector(38.692, 19.268, 0.0)
    r4 = 2.458
    a4_s = math.atan2(21.650 - c4.y, 39.300 - c4.x)
    a4_m = 0.15
    a4_e = math.atan2(17.350 - c4.y, 40.230 - c4.x)
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

    poles3 = [
        p2_e, (17.012, 34.366), (13.720, 32.826), (9.038, 30.847), (5.089, 28.080),
        (2.350, 25.600), (2.433, 22.498), (2.550, 19.300), (3.400, 16.800),
        (6.685, 15.880), (10.500, 16.100), (16.500, 16.900), (23.500, 18.100),
        (30.500, 19.800), (36.800, 21.300), p4_s,
    ]
    e3 = make_g1_cubic_bspline(
        poles3, circle_tangent_cw(c2, p2_e), circle_tangent_cw(c4, p4_s)
    )

    poles5 = [
        p4_e, (38.50, 16.20), (33.50, 12.80), (27.20, 7.80), (22.40, 2.20),
        (20.10, -2.80), (19.50, -6.50), p56_s,
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
        p_spring_cheek, (-129.5, -0.2), (-124.5, 2.5), (-116.0, 5.8), (-106.0, 8.8),
        (-92.0, 12.5), (-78.200, 16.948), (-62.257, 22.984), (-49.101, 28.027),
        (-35.845, 31.870), (-23.493, 34.775), (-10.498, 36.789), (-0.008, 37.954),
        (7.477, 38.458), (12.888, 38.362), (15.874, 37.981), p2_s,
    ]
    t_dorsal_start = App.Vector(1.0, 0.5, 0.0)
    e1 = make_g1_cubic_bspline(poles1, t_dorsal_start, circle_tangent_cw(c2, p2_s))

    poles7 = [
        p6_e, (-39.50, -14.25), (-44.00, -12.80), (-52.50, -9.40), (-61.50, -6.80),
        (-69.50, -5.75), (-77.50, -6.50), (-87.00, -9.50), (-96.50, -12.50),
        (-106.50, -16.00), (-115.00, -19.50), p_hub_bot,
    ]
    t_ventral_end = App.Vector(-1.0, -0.2, 0.0)
    e7 = make_g1_cubic_bspline(poles7, App.Vector(-1.0, 0.0, 0.0), t_ventral_end)

    return Part.Wire([arc_cheek_tip, arc_pivot_bot, e7, e6, e5b, e5, e4, e3, e2, e1])


def build_tibia_servo_cage_cheek_wire():
    """
    Construct the bionic symmetrical cheek wire in the X-Z plane of Tibia:
    - Symmetrical around midline Z = +0.50 mm (Y_leg = +2.50 mm).
    - Rounded nose apex (R = 4.50 mm) around Knee pivot (0, 0) extending to X = +18.20 mm.
    - Symmetrical flat crest (Z = +24.00) and tab (Z = -23.00) from X = +9.00 to X = -5.50 mm.
    - Harmonic G1 S-curves transitioning smoothly to the rear bulkhead at X = -36.50 mm.
    """
    R_FRONT = 4.50
    Z_MID = 0.50
    Z_TAB = -23.00
    Z_CREST = +24.00
    X_NOSE = 18.20
    X_REAR = -36.50
    Z_REAR_TOP = 14.50
    Z_REAR_BOT = -13.50

    p_front_top = App.Vector(X_NOSE, 0.0, Z_MID + R_FRONT)
    p_front_bot = App.Vector(X_NOSE, 0.0, Z_MID - R_FRONT)
    e_front_mid = [Part.makeLine(p_front_bot, p_front_top)]

    p_nose_top_end = App.Vector(X_NOSE - R_FRONT, 0.0, Z_MID + 2.0 * R_FRONT)
    p_nose_top_mid = App.Vector(
        X_NOSE - R_FRONT * (1.0 - math.cos(math.pi / 4)),
        0.0,
        Z_MID + R_FRONT + R_FRONT * math.sin(math.pi / 4),
    )
    e_arc_top = Part.Edge(Part.Arc(p_front_top, p_nose_top_mid, p_nose_top_end))

    p_nose_bot_end = App.Vector(X_NOSE - R_FRONT, 0.0, Z_MID - 2.0 * R_FRONT)
    p_nose_bot_mid = App.Vector(
        X_NOSE - R_FRONT * (1.0 - math.cos(math.pi / 4)),
        0.0,
        Z_MID - R_FRONT - R_FRONT * math.sin(math.pi / 4),
    )
    e_arc_bot = Part.Edge(Part.Arc(p_nose_bot_end, p_nose_bot_mid, p_front_bot))

    p_step_top_front = App.Vector(11.00, 0.0, Z_MID + 2.0 * R_FRONT)
    e_step_top_h = [Part.makeLine(p_nose_top_end, p_step_top_front)]

    p_step_bot_front = App.Vector(11.00, 0.0, Z_MID - 2.0 * R_FRONT)
    e_step_bot_h = [Part.makeLine(p_step_bot_front, p_nose_bot_end)]

    p_step_top_up = App.Vector(11.00, 0.0, Z_CREST - 2.0)
    e_step_top_v = [Part.makeLine(p_step_top_front, p_step_top_up)]

    p_step_bot_down = App.Vector(11.00, 0.0, Z_TAB + 2.0)
    e_step_bot_v = [Part.makeLine(p_step_bot_down, p_step_bot_front)]

    p_crest_start = App.Vector(9.00, 0.0, Z_CREST)
    p_crest_f_mid = App.Vector(
        11.00 - 2.0 * (1.0 - math.cos(math.pi / 4)),
        0.0,
        Z_CREST - 2.0 * (1.0 - math.sin(math.pi / 4)),
    )
    e_crest_fillet = [Part.Edge(Part.Arc(p_step_top_up, p_crest_f_mid, p_crest_start))]

    p_tab_start = App.Vector(9.00, 0.0, Z_TAB)
    p_tab_f_mid = App.Vector(
        11.00 - 2.0 * (1.0 - math.cos(math.pi / 4)),
        0.0,
        Z_TAB + 2.0 * (1.0 - math.sin(math.pi / 4)),
    )
    e_tab_fillet = [Part.Edge(Part.Arc(p_tab_start, p_tab_f_mid, p_step_bot_down))]

    p_crest_end = App.Vector(-5.50, 0.0, Z_CREST)
    e_crest_flat = [Part.makeLine(p_crest_start, p_crest_end)]

    p_tab_end = App.Vector(-5.50, 0.0, Z_TAB)
    e_tab_flat = [Part.makeLine(p_tab_end, p_tab_start)]

    p_rear_top = App.Vector(X_REAR, 0.0, Z_REAR_TOP)
    p_rear_bot = App.Vector(X_REAR, 0.0, Z_REAR_BOT)
    e_top_s = make_s_curve_edges_xz(p_crest_end, p_rear_top)
    e_bot_s = make_s_curve_edges_xz(p_rear_bot, p_tab_end)
    e_rear_v = [Part.makeLine(p_rear_top, p_rear_bot)]

    all_edges_cheek = (
        e_front_mid
        + [e_arc_top]
        + e_step_top_h
        + e_step_top_v
        + e_crest_fillet
        + e_crest_flat
        + e_top_s
        + e_rear_v
        + e_bot_s
        + e_tab_flat
        + e_tab_fillet
        + e_step_bot_v
        + e_step_bot_h
        + [e_arc_bot]
    )

    return Part.Wire(all_edges_cheek)


def build_servo_ear_bosses():
    """
    Build raised Servo Mounting Pads (Z in [+3.00, +7.00] mm, mating flush with servo tabs).
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


def build_tibia_v2_shape():
    """
    Build the canonical monolithic Tibia body:
    - Twin servo cage analogous to Coxa's Femur-Servo-Käfig
    - Central sickle-claw blade (Z in [-3.00, +4.00], centered at Z = +0.50 mm)
    - Closed teardrop window
    - 45-degree Warren truss cutouts in lateral cheeks
    """
    w_cheek = build_tibia_servo_cage_cheek_wire()
    f_cheek = Part.Face(w_cheek)

    # Upper / Dorsal cheek: Y in [+10.15, +16.35] (6.20 mm)
    s_cheek_upper = f_cheek.extrude(App.Vector(0.0, 6.20, 0.0)).translate(App.Vector(0.0, 10.15, 0.0))
    # Lower / Ventral cheek: Y in [-16.35, -10.15] (6.20 mm)
    s_cheek_lower = f_cheek.extrude(App.Vector(0.0, 6.20, 0.0)).translate(App.Vector(0.0, -16.35, 0.0))

    # Bottom Counter-Bearing Tab Plate connecting the two cheeks at Z in [-23.00, -20.00]
    s_tab_bottom = Part.makeBox(9.00 - (-5.50), 2.0 * 16.35, 3.00, App.Vector(-5.50, -16.35, -23.00))

    # Raised Servo Ear Bosses at Z in [3.00, 7.00] mm
    ear_bosses = build_servo_ear_bosses()

    # Central Claw Blade (Z in [-3.00, +4.00], centered at Z = +0.50 mm)
    outer_wire = build_organic_tibia_outer_wire()
    claw_central = Part.Face(outer_wire).extrude(App.Vector(0, 0, 7.0)).translate(App.Vector(0, 0, -3.0))

    # Cut away legacy beak horns extending forward into the servo cage / knee joint (X > -31.65 mm)
    box_front_cut = Part.makeBox(100.0, 120.0, 30.0, App.Vector(-31.65, -60.0, -15.0))
    claw_central = claw_central.cut(box_front_cut)

    # Fuse base
    tibia_base = claw_central.fuse(s_cheek_upper).fuse(s_cheek_lower).fuse(s_tab_bottom).fuse(ear_bosses)

    # Cut Servo Pocket & Seats
    servo_pocket = Part.makeBox(40.80, 20.30, 48.00, App.Vector(-31.65, -10.15, -20.00))
    servo_cable_slot = Part.makeBox(7.50, 7.20, 5.00, App.Vector(9.00, -3.60, -20.00))
    screw_bore = Part.makeCylinder(2.05, 6.0, App.Vector(0.0, 0.0, -24.0))
    nut_pocket = make_hex_nut_pocket_z(0.0, 0.0, -22.40, -19.50, sw=7.10)
    tibia_base = tibia_base.cut(servo_pocket).cut(servo_cable_slot).cut(screw_bore).cut(nut_pocket)

    for sx, sy in [(13.00, 5.00), (13.00, -5.00), (-35.50, 5.00), (-35.50, -5.00)]:
        tibia_base = tibia_base.cut(Part.makeCylinder(1.25, 25.0, App.Vector(sx, sy, -3.20)))

    # Cheek 45-deg Warren Truss Cutouts (Style Guide compliant)
    map_xz = lambda p: App.Vector(p.x, 0.0, p.y)
    tri1 = [(-5.00, 8.00, 1.40), (7.50, 8.00, 1.40), (-5.00, 20.50, 1.40)]
    tri2 = [(-5.00, -7.00, 1.40), (7.50, -7.00, 1.40), (-5.00, -19.50, 1.40)]
    tri3 = [(-26.00, 8.00, 1.40), (-7.50, 8.00, 1.40), (-26.00, 20.50, 1.40)]
    tri4 = [(-26.00, -7.00, 1.40), (-7.50, -7.00, 1.40), (-26.00, -19.50, 1.40)]

    for tri in (tri1, tri2, tri3, tri4):
        w_t = make_rounded_polygon_wire_2d(tri, map_xz)
        cut_u = Part.Face(w_t).extrude(App.Vector(0.0, 10.0, 0.0)).translate(App.Vector(0.0, 9.0, 0.0))
        cut_l = Part.Face(w_t).extrude(App.Vector(0.0, -10.0, 0.0)).translate(App.Vector(0.0, -9.0, 0.0))
        tibia_base = tibia_base.cut(cut_u).cut(cut_l)

    try:
        tibia_base = tibia_base.removeSplitter()
    except Exception:
        pass

    return tibia_base


is_main = (__name__ == "__main__") or (
    len(sys.argv) > 1 and os.path.basename(sys.argv[1]) == os.path.basename(__file__)
)
if is_main:
    shape_v2 = build_tibia_v2_shape()
    print(
        f"Tibia_v2 Valid: {shape_v2.isValid()}, Solids: {len(shape_v2.Solids)}, "
        f"Volume: {shape_v2.Volume:.1f} mm^3, BB: {shape_v2.BoundBox}"
    )

    os.makedirs(os.path.dirname(fcstd_tibia_v2_path), exist_ok=True)
    os.makedirs(export_step_dir, exist_ok=True)
    os.makedirs(export_stl_dir, exist_ok=True)

    doc = App.newDocument("tibia")
    obj = doc.addObject("Part::Feature", "Tibia_v2")
    obj.Label = "Tibia v2 (Analogous Servo Cage + Central Claw)"
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
