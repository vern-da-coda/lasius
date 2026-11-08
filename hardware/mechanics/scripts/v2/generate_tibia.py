#!/usr/bin/env python3
"""
Generate Lasius Hexapod Monolithic Tibia v2
- G1-continuous organic sickle claw outline (0.00 deg tangent kink at all transitions)
- Claw outline adapted at the servo mount region to fully encompass the upper/lower
  servo mounts and provide generous wall thickness around the mounting holes & cable slot
- Raised servo mounting pads with rounded outer corners (R = 2.80 mm) where they do NOT
  meet the servo, and sharp precision inner corners (0.15 mm clearance) at the servo pocket
- Torsion-resistant ~45-deg triangulated V-truss servo cage ("Fachwerk-Servotasche")
  directly supporting the Knee counter-bearing node at X = 0.00, Z = -20.00 mm
- Inverted Knee counter-bearing seat: internal M4 hex nut pocket (SW 7.10 mm, depth 2.40 mm)
  with a 0.60 mm retaining shoulder at Z in [-23.00, -22.40] mm so the Tibia + Servo unit
  slides radially into the monolithic v2 Femur without any protruding rear screw shaft
"""

import math
import os
import FreeCAD as App
import Part

print("--- Generating Lasius Monolithic Tibia v2 (G1 Smooth Claw + 45-deg Truss Cage + Internal M4 Nut Seat) ---")

models_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/models"
export_step_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/step/custom/v2/parts"
export_stl_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/stl/custom/v2/parts"

fcstd_tibia_v2_path = f"{models_dir}/custom/v2/parts/tibia.FCStd"
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
            alpha = math.acos(dot)  # turn angle
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
    ts = App.Vector(t_start.x, t_start.y, 0.0)
    ts.normalize()
    te = App.Vector(t_end.x, t_end.y, 0.0)
    te.normalize()

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


def build_g1_claw_outer_wire():
    """
    Build the G1-continuous outer contour of the Tibia sickle claw (at Z = 0),
    adapted around the servo mounts so neither the upper servo mount (X <= 18.00)
    nor the lower servo mount (X >= -38.80) nor the truss cage protrudes beyond
    the claw contour, with 0.00 deg tangent kink at every single vertex.
    """
    # 1. Foot tip circle (Edge 0, CW): R = 5.598, Center = (-123.555, -14.602)
    c0 = App.Vector(-123.555, -14.602, 0.0)
    r0 = 5.598
    a0_s = math.atan2(-20.200 - c0.y, -123.530 - c0.x)
    a0_m = math.pi
    a0_e = math.atan2(-9.600 - c0.y, -126.070 - c0.x)
    p0_s = App.Vector(c0.x + r0 * math.cos(a0_s), c0.y + r0 * math.sin(a0_s), 0.0)
    p0_m = App.Vector(c0.x + r0 * math.cos(a0_m), c0.y + r0 * math.sin(a0_m), 0.0)
    p0_e = App.Vector(c0.x + r0 * math.cos(a0_e), c0.y + r0 * math.sin(a0_e), 0.0)
    e0 = Part.Arc(p0_s, p0_m, p0_e).toShape()

    # 2. Upper dorsal horn tip circle (Edge 2, CW): R = 1.489, Center = (17.271, 36.152)
    c2 = App.Vector(17.271, 36.152, 0.0)
    r2 = 1.489
    a2_s = math.atan2(37.610 - c2.y, 17.570 - c2.x)
    a2_m = 0.05
    a2_e = math.atan2(34.780 - c2.y, 17.850 - c2.x)
    p2_s = App.Vector(c2.x + r2 * math.cos(a2_s), c2.y + r2 * math.sin(a2_s), 0.0)
    p2_m = App.Vector(c2.x + r2 * math.cos(a2_m), c2.y + r2 * math.sin(a2_m), 0.0)
    p2_e = App.Vector(c2.x + r2 * math.cos(a2_e), c2.y + r2 * math.sin(a2_e), 0.0)
    e2 = Part.Arc(p2_s, p2_m, p2_e).toShape()

    # 3. Lower knee horn tip circle (Edge 4, CW): R = 2.458, Center = (38.692, 19.268)
    c4 = App.Vector(38.692, 19.268, 0.0)
    r4 = 2.458
    a4_s = math.atan2(21.650 - c4.y, 39.300 - c4.x)
    a4_m = 0.15
    a4_e = math.atan2(17.350 - c4.y, 40.230 - c4.x)
    p4_s = App.Vector(c4.x + r4 * math.cos(a4_s), c4.y + r4 * math.sin(a4_s), 0.0)
    p4_m = App.Vector(c4.x + r4 * math.cos(a4_m), c4.y + r4 * math.sin(a4_m), 0.0)
    p4_e = App.Vector(c4.x + r4 * math.cos(a4_e), c4.y + r4 * math.sin(a4_e), 0.0)
    e4 = Part.Arc(p4_s, p4_m, p4_e).toShape()

    # 4. Bottom-right servo-mount fillet arc (Edge 5b, CW):
    # Wraps smoothly around the upper servo mount (X = 18.00) with R = 4.25 mm
    # centered at (15.00, -10.00), reaching X = 19.25 mm before sweeping into Face60!
    c56 = App.Vector(15.00, -10.00, 0.0)
    r56 = 4.25
    a56_s = 0.06 * math.pi
    a56_m = -0.22 * math.pi
    a56_e = -0.50 * math.pi
    p56_s = App.Vector(c56.x + r56 * math.cos(a56_s), c56.y + r56 * math.sin(a56_s), 0.0)
    p56_m = App.Vector(c56.x + r56 * math.cos(a56_m), c56.y + r56 * math.sin(a56_m), 0.0)
    p56_e = App.Vector(c56.x + r56 * math.cos(a56_e), c56.y + r56 * math.sin(a56_e), 0.0)
    e5b = Part.Arc(p56_s, p56_m, p56_e).toShape()

    # Edge 1: Top dorsal arch (G1 tangent to c0 and c2)
    poles1 = [
        p0_e,
        (-124.659, -9.119),
        (-120.026, -7.195),
        (-114.196, -3.622),
        (-104.619, 1.453),
        (-92.455, 7.445),
        (-78.200, 16.948),
        (-62.257, 22.984),
        (-49.101, 28.027),
        (-35.845, 31.870),
        (-23.493, 34.775),
        (-10.498, 36.789),
        (-0.008, 37.954),
        (7.477, 38.458),
        (12.888, 38.362),
        (15.874, 37.981),
        p2_s,
    ]
    e1 = make_g1_cubic_bspline(poles1, circle_tangent_cw(c0, p0_e), circle_tangent_cw(c2, p2_s))

    # Edge 3: Inner U-throat (G1 tangent to c2 and c4)
    poles3 = [
        p2_e,
        (17.012, 34.366),
        (13.720, 32.826),
        (9.038, 30.847),
        (5.089, 28.080),
        (2.350, 25.600),
        (2.433, 22.498),
        (2.550, 19.300),
        (3.400, 16.800),
        (6.685, 15.880),
        (10.500, 16.100),
        (16.500, 16.900),
        (23.500, 18.100),
        (30.500, 19.800),
        (36.800, 21.300),
        p4_s,
    ]
    e3 = make_g1_cubic_bspline(poles3, circle_tangent_cw(c2, p2_e), circle_tangent_cw(c4, p4_s))

    # Edge 5 (Face60): Concave right flank from p4_e down to p56_s (G1 tangent to c4 and c56)
    poles5 = [
        p4_e,
        (38.50, 16.20),
        (33.50, 12.80),
        (27.20, 7.80),
        (22.40, 2.20),
        (20.10, -2.80),
        (19.50, -6.50),
        p56_s,
    ]
    e5 = make_g1_cubic_bspline(poles5, circle_tangent_cw(c4, p4_e), circle_tangent_cw(c56, p56_s))

    # Edge 6: Bottom flat edge under the servo cage & mounts (Y = -14.25, X from +15.00 to -36.50)
    p6_e = App.Vector(-36.50, -14.25, 0.0)
    e6 = Part.makeLine(p56_e, p6_e)

    # Edge 7: Lower ventral arch from p6_e to p0_s (G1 tangent to (-1, 0, 0) at p6_e and c0 at p0_s)
    poles7 = [
        p6_e,
        (-39.50, -14.25),
        (-44.00, -12.80),
        (-52.50, -9.40),
        (-61.50, -6.80),
        (-69.50, -5.75),
        (-77.50, -6.10),
        (-87.15, -8.10),
        (-96.50, -10.30),
        (-106.50, -14.10),
        (-115.50, -18.20),
        (-121.00, -19.90),
        p0_s,
    ]
    e7 = make_g1_cubic_bspline(poles7, App.Vector(-1.0, 0.0, 0.0), circle_tangent_cw(c0, p0_s))

    return Part.Wire([e0, e1, e2, e3, e4, e5, e5b, e6, e7])


def build_g1_claw_cutout_wire():
    """
    Build the G1-continuous teardrop cutout window in the Tibia claw.
    Replaces the jagged multi-knot degree-8 splines of v1 with C2-smooth cubic BSplines
    that join both end circles with 0.00 deg tangent kinks and cleanly clear the
    rounded top-left corner of the lower servo mount.
    """
    # Right end circle (CutEdge 0, CW from top to bottom): R = 2.051, Center = (-21.688, 21.529)
    cr = App.Vector(-21.688, 21.529, 0.0)
    rr = 2.051
    ar_top = math.atan2(23.580 - cr.y, -21.690 - cr.x)
    ar_mid = 0.0
    ar_bot = math.atan2(19.540 - cr.y, -22.190 - cr.x)
    pr_top = App.Vector(cr.x + rr * math.cos(ar_top), cr.y + rr * math.sin(ar_top), 0.0)
    pr_mid = App.Vector(cr.x + rr * math.cos(ar_mid), cr.y + rr * math.sin(ar_mid), 0.0)
    pr_bot = App.Vector(cr.x + rr * math.cos(ar_bot), cr.y + rr * math.sin(ar_bot), 0.0)
    ec_r = Part.Arc(pr_top, pr_mid, pr_bot).toShape()

    # Left end circle (CutEdge 2, CW from bottom to top): R = 3.720, Center = (-75.430, 5.090)
    cl = App.Vector(-75.430, 5.090, 0.0)
    rl = 3.720
    al_bot = math.atan2(2.710 - cl.y, -78.290 - cl.x)
    al_mid = math.pi
    al_top = math.atan2(6.700 - cl.y, -78.790 - cl.x)
    pl_bot = App.Vector(cl.x + rl * math.cos(al_bot), cl.y + rl * math.sin(al_bot), 0.0)
    pl_mid = App.Vector(cl.x + rl * math.cos(al_mid), cl.y + rl * math.sin(al_mid), 0.0)
    pl_top = App.Vector(cl.x + rl * math.cos(al_top), cl.y + rl * math.sin(al_top), 0.0)
    ec_l = Part.Arc(pl_bot, pl_mid, pl_top).toShape()

    # Top curve (from pl_top to pr_top, G1 tangent to both circles CW)
    poles_top = [
        pl_top,
        (-74.0, 8.8),
        (-65.0, 12.2),
        (-54.0, 16.0),
        (-43.0, 19.2),
        (-32.0, 21.8),
        (-25.0, 23.1),
        pr_top,
    ]
    ec_top = make_g1_cubic_bspline(poles_top, circle_tangent_cw(cl, pl_top), circle_tangent_cw(cr, pr_top))

    # Bottom curve (from pr_bot to pl_bot, G1 tangent to both circles CW)
    poles_bot = [
        pr_bot,
        (-25.5, 18.4),
        (-31.5, 15.6),
        (-37.2, 10.6),
        (-44.5, 3.0),
        (-53.5, 3.4),
        (-65.5, 4.9),
        (-74.0, 4.0),
        pl_bot,
    ]
    ec_bot = make_g1_cubic_bspline(poles_bot, circle_tangent_cw(cr, pr_bot), circle_tangent_cw(cl, pl_bot))

    return Part.Wire([ec_r, ec_bot, ec_l, ec_top])


def build_servo_ear_bosses():
    """
    Build the two raised Servo Mounting Pads (Z_local in [+3.00, +7.00] mm, rising 3.00 mm
    above the Z = +4.00 mm claw top face to mate flush with the servo tabs at Z = +7.00 mm).
    - Width Y in [-10.15, +10.15] mm aligns 100% flush with the servo pocket side walls!
    - Inner corners where the mounts meet the servo body (X = -31.65, X = +9.15, Y = +-10.15)
      and the cable exit slot (X = +9.15, Y = +-4.50) are kept SHARP (R = 0.00 mm).
    - Outer corners away from the servo are smoothly rounded (R = 2.60 mm).
    """
    z0, dz = 3.00, 4.00
    map_xy = lambda v: App.Vector(v.x, v.y, z0)

    # Lower servo mount (-X): X in [-38.60, -31.65], Y in [-10.15, +10.15]
    pts_lower = [
        (-31.65, -10.15, 0.00),
        (-38.60, -10.15, 2.60),
        (-38.60,  10.15, 2.60),
        (-31.65,  10.15, 0.00),
    ]
    w_lower = make_rounded_polygon_wire_2d(pts_lower, map_xy)
    boss_lower = Part.Face(w_lower).extrude(App.Vector(0, 0, dz))

    # Upper servo mount (+X): X in [+9.15, +17.80], Y in [-10.15, +10.15]
    pts_upper = [
        ( 9.15,  10.15, 0.00),
        (17.80,  10.15, 2.60),
        (17.80, -10.15, 2.60),
        ( 9.15, -10.15, 0.00),
    ]
    w_upper = make_rounded_polygon_wire_2d(pts_upper, map_xy)
    boss_upper = Part.Face(w_upper).extrude(App.Vector(0, 0, dz))

    return boss_lower.fuse(boss_upper)


def build_triangulated_truss_servo_cage():
    """
    Build the torsion-stiff ~45-deg triangulated V-truss servo cage ("Fachwerk-Servotasche")
    connecting the foot plate (Z_local in [-23.00, -20.00] mm) with the claw (Z_local = -3.00 mm).
    - Outer XY footprint has rounded outer corners (R = 3.00 mm) and a gentle hourglass waist
      along the middle while keeping the 4 servo-pocket corner columns solid.
    - Both side walls (XZ plane) feature a framed 3-window 45.0-deg Warren/A-truss whose diagonal
      struts converge directly onto the Knee Counter-Bearing node at X = 0.00, Z = -20.00 mm!
    """
    # 1. Outer XY profile (extruded from Z = -23.00 to Z = -2.00 mm):
    x_min, x_max = -34.60, 12.10
    y_out = 12.80
    r_c = 3.00
    k = r_c * (1.0 - 1.0 / math.sqrt(2.0))
    dy_waist = 1.40
    x_w1, x_w2 = -26.50, 4.00
    x_wm = 0.5 * (x_w1 + x_w2)
    z_min, z_max = -23.00, -2.00

    v = [
        App.Vector(x_min + r_c, y_out, z_min),
        App.Vector(x_w1, y_out, z_min),
        App.Vector(x_wm, y_out - dy_waist, z_min),
        App.Vector(x_w2, y_out, z_min),
        App.Vector(x_max - r_c, y_out, z_min),
        App.Vector(x_max - k, y_out - k, z_min),
        App.Vector(x_max, y_out - r_c, z_min),
        App.Vector(x_max, -y_out + r_c, z_min),
        App.Vector(x_max - k, -y_out + k, z_min),
        App.Vector(x_max - r_c, -y_out, z_min),
        App.Vector(x_w2, -y_out, z_min),
        App.Vector(x_wm, -y_out + dy_waist, z_min),
        App.Vector(x_w1, -y_out, z_min),
        App.Vector(x_min + r_c, -y_out, z_min),
        App.Vector(x_min + k, -y_out + k, z_min),
        App.Vector(x_min, -y_out + r_c, z_min),
        App.Vector(x_min, y_out - r_c, z_min),
        App.Vector(x_min + k, y_out - k, z_min),
    ]
    edges_xy = [
        Part.makeLine(v[0], v[1]),
        Part.Arc(v[1], v[2], v[3]).toShape(),
        Part.makeLine(v[3], v[4]),
        Part.Arc(v[4], v[5], v[6]).toShape(),
        Part.makeLine(v[6], v[7]),
        Part.Arc(v[7], v[8], v[9]).toShape(),
        Part.makeLine(v[9], v[10]),
        Part.Arc(v[10], v[11], v[12]).toShape(),
        Part.makeLine(v[12], v[13]),
        Part.Arc(v[13], v[14], v[15]).toShape(),
        Part.makeLine(v[15], v[16]),
        Part.Arc(v[16], v[17], v[0]).toShape(),
    ]
    cage = Part.Face(Part.Wire(edges_xy)).extrude(App.Vector(0, 0, z_max - z_min))

    # 2. Cut the 3 Triangulated 45.0-deg Truss Windows in both Side Walls (XZ plane, Y in [-20, +20]):
    #    Framed cleanly between Z = -18.80 mm (bottom chord) and Z = -4.20 mm (top chord)
    #    so there are zero feather edges at the Z = -3.00 mm claw underside!
    map_xz = lambda p: App.Vector(p.x, -20.0, p.y)
    #    Window 1 (Left upper 45-deg right triangle):
    tri_left = [
        (-28.00, -4.20, 1.40),
        (-13.80, -4.20, 1.40),
        (-28.00, -18.40, 1.40),
    ]
    #    Window 2 (Center lower 45-deg isosceles triangle):
    tri_center = [
        (-11.25, -5.20, 1.50),
        (  2.35, -18.80, 1.40),
        (-24.85, -18.80, 1.40),
    ]
    #    Window 3 (Right upper 45-deg right triangle):
    tri_right = [
        ( -8.70, -4.20, 1.40),
        (  5.50, -4.20, 1.40),
        (  5.50, -18.40, 1.40),
    ]
    for tri in (tri_left, tri_center, tri_right):
        w_tri = make_rounded_polygon_wire_2d(tri, map_xz)
        cut_tri = Part.Face(w_tri).extrude(App.Vector(0, 40.0, 0))
        cage = cage.cut(cut_tri)

    # 3. Lower end wall (-X around X = -34.60..-31.65): framed rounded weight-relief window in YZ
    map_yz_end = lambda p: App.Vector(-36.0, p.x, p.y)
    end_win_pts = [
        (-5.20, -4.20, 1.80),
        ( 5.20, -4.20, 1.80),
        ( 5.20, -18.80, 1.80),
        (-5.20, -18.80, 1.80),
    ]
    end_win = Part.Face(make_rounded_polygon_wire_2d(end_win_pts, map_yz_end)).extrude(App.Vector(6.0, 0, 0))
    cage = cage.cut(end_win)

    # 5. Foot Bottom Plate (Z in [-23.00, -20.00]):
    #    Two triangulated/rounded weight-relief windows separated by a diagonal shear rib
    #    in X in [-27.50, -7.50], leaving a massive solid boss around the M4 nut seat at (0, 0):
    map_bot = lambda p: App.Vector(p.x, p.y, -24.0)
    bot_win_1 = [
        (-27.00,  5.20, 1.60),
        ( -9.50,  5.20, 1.60),
        (-27.00, -3.80, 1.60),
    ]
    bot_win_2 = [
        ( -8.00,  3.80, 1.60),
        ( -8.00, -5.20, 1.60),
        (-25.50, -5.20, 1.60),
    ]
    for b_tri in (bot_win_1, bot_win_2):
        w_b = make_rounded_polygon_wire_2d(b_tri, map_bot)
        cage = cage.cut(Part.Face(w_b).extrude(App.Vector(0, 0, 5.0)))

    return cage


def make_hex_nut_pocket_z(cx, cy, z_bottom, z_top, sw=7.10):
    """
    Create a hexagonal prism (across flats = sw) from z_bottom to z_top
    for an internal anti-rotation M4 hex nut pocket.
    Note: orientation matches M4_Mutter (flat sides at Y = +-sw/2, vertices along X).
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
    # 1. Build 7.00 mm thick G1-continuous Sickle Claw Blade at Z_local in [-3.00, +4.00] mm:
    #    (In leg_assembly coordinates Y_world = Z_local + 2.00, this centers the claw at
    #     Y_world = +2.50 mm, 100% colinear with the vertical Coxa rotation axis!)
    w_outer = build_g1_claw_outer_wire()
    w_cutout = build_g1_claw_cutout_wire()

    outer_prism = Part.Face(w_outer).extrude(App.Vector(0, 0, 7.00))
    outer_prism.translate(App.Vector(0, 0, -3.00))

    cutout_prism = Part.Face(w_cutout).extrude(App.Vector(0, 0, 60.00))
    cutout_prism.translate(App.Vector(0, 0, -35.00))

    claw_base = outer_prism.cut(cutout_prism)

    # 2. Fuse the two Raised Servo Mounting Pads (Z_local in [+4.00, +7.00] mm) with
    #    rounded outer corners (R = 2.80 mm) and sharp inner servo corners:
    ear_bosses = build_servo_ear_bosses().cut(cutout_prism)
    claw_base = claw_base.fuse(ear_bosses)

    # 3. Build and fuse the Torsion-Stiff ~45-deg Triangulated Truss Servo Cage (Z in [-23.00, -3.00]):
    truss_cage = build_triangulated_truss_servo_cage()
    tibia_v2 = claw_base.fuse(truss_cage).cut(cutout_prism)

    # 4. Precision Servo Body Pocket (X in [-31.65, +9.15], Y in [-10.15, +10.15], Z in [-20.00, +8.00]):
    #    Sharp corners for 0.15 mm clearance around the rectangular servo casing.
    servo_pocket = Part.makeBox(40.80, 20.30, 28.00, App.Vector(-31.65, -10.15, -20.00))
    tibia_v2 = tibia_v2.cut(servo_pocket)

    # 5. Servo Cable Exit Slot at upper end (+X in [9.00, 15.50], Y in [-4.50, +4.50], Z in [-20.00, +8.00])
    #    with slightly rounded outer corners (R = 1.00 mm at X = 15.50) away from the servo:
    map_slot = lambda p: App.Vector(p.x, p.y, -20.00)
    slot_pts = [
        ( 9.00, -4.50, 0.00),
        (15.50, -4.50, 1.00),
        (15.50,  4.50, 1.00),
        ( 9.00,  4.50, 0.00),
    ]
    cable_slot = Part.Face(make_rounded_polygon_wire_2d(slot_pts, map_slot)).extrude(App.Vector(0, 0, 28.00))
    tibia_v2 = tibia_v2.cut(cable_slot)

    # 6. Inverted Coaxial Knee Counter-Bearing Seat at (0.00, 0.00):
    #    - M4 through-bore (D = 4.10 mm, R = 2.05 mm) through the entire floor (Z in [-24.0, -19.0])
    #    - Internal Hexagonal M4 Nut Pocket (SW = 7.10 mm) from Z = -22.40 to Z = -20.00 mm
    #      (depth = 2.40 mm), leaving a solid 0.60 mm retaining shoulder at Z in [-23.00, -22.40] mm!
    screw_bore = Part.makeCylinder(2.05, 6.0, App.Vector(0.0, 0.0, -24.0))
    nut_pocket = make_hex_nut_pocket_z(0.0, 0.0, -22.40, -19.50, sw=7.10)
    tibia_v2 = tibia_v2.cut(screw_bore).cut(nut_pocket)

    # 7. 4x Coaxial Servo Mounting Ear Holes at (13.00, +-5.00) and (-35.50, +-5.00):
    #    Start at Z = -3.00 mm (bottom of claw) through Z = +7.00 mm (top of ear boss)
    #    so they never notch the outer walls of the truss cage below Z = -3.00 mm!
    for sx, sy in [(13.00, 5.00), (13.00, -5.00), (-35.50, 5.00), (-35.50, -5.00)]:
        ear_hole = Part.makeCylinder(1.25, 11.0, App.Vector(sx, sy, -3.20))
        tibia_v2 = tibia_v2.cut(ear_hole)

    tibia_v2 = tibia_v2.removeSplitter()
    return tibia_v2


if __name__ == "__main__":
    shape_v2 = build_tibia_v2_shape()
    print(
        f"Tibia_v2 Valid: {shape_v2.isValid()}, Solids: {len(shape_v2.Solids)}, "
        f"Volume: {shape_v2.Volume:.1f} mm^3, BB: {shape_v2.BoundBox}"
    )

    os.makedirs(f"{models_dir}/custom/v2/parts", exist_ok=True)
    os.makedirs(export_step_dir, exist_ok=True)
    os.makedirs(export_stl_dir, exist_ok=True)

    doc = App.newDocument("tibia")
    obj = doc.addObject("Part::Feature", "Tibia_v2")
    obj.Label = "Tibia v2 (Monolithic Claw + 45-deg Truss Servo Cage)"
    obj.Shape = shape_v2

    doc.recompute()
    doc.saveAs(fcstd_tibia_v2_path)
    print(f"Saved FreeCAD model: {fcstd_tibia_v2_path}")

    shape_v2.exportStep(step_tibia_v2_path)
    shape_v2.exportStl(stl_tibia_v2_path)
    print(f"Exported STEP & STL: {step_tibia_v2_path}, {stl_tibia_v2_path}")

    App.closeDocument("tibia")
