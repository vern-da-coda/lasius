#!/usr/bin/env python3
"""
Generate Lasius Bionic Monocoque Tibia v2 & Service Cover (Option 2c-V2)
========================================================================
Builds BOTH canonical Tibia v2 parts from pure parametric Hardware-as-Code:
1. hardware/mechanics/models/custom/v2/parts/tibia/tibia.FCStd        (Tibia_Body)
2. hardware/mechanics/models/custom/v2/parts/tibia/tibia_cover.FCStd  (Tibia_Cover)

Design Highlights (Option 2c-V2):
- Organic swooping bionic Tibia silhouette (G1-continuous B-splines honoring the
  user's elegant curved ant-tibia sketch, replacing the blocky Warren-truss blade)
- Repositioned bionic teardrop window in the upper-middle dorsal arch
  (X in [22, 57], Y in [36.5, 48.0]) guaranteeing >= 4.8..6.0 mm PETG ribs all around
- Deeply embedded Tarsus Pivot Axis at (109.00, 20.50) — 15.0 mm inside the distal
  fork mouth with >= 7.1 mm radial wall below the Ø3.0 mm ISO 2338 dowel pin
- Fail-Safe NC-Öffner Microswitch Bay (Omron D2FC-F-K at -5.0 deg) with:
  * 2x integrated Ø1.96 mm mounting locating pins
  * Full open bay for ALL 3 STRAIGHT UNBENT 3.3 mm solder pins + >= 5.5 mm free
    solder/heatshrink/wire room + >= 4.0 mm solid PETG dorsal roof above
- Deep Belly Vertical Compression Spring Bay at X = 67.50 mm (r = 41.5 mm lever arm!)
  with integral Ø2.80 x 2.50 mm lower locating boss & >= 4.9 mm solid PETG floor
- Broad flat Ruhe-Anschlag (0 deg) + broad flat Overload Hard-Stop (+5 deg, 0 N on switch)
- Exact Coxa-matched Twin Servo Cage (Z in [-14.50, +32.50]) for Torcster NR-645
  with 6x 45 deg bionic truss windows, 4x M2.5 mounting holes, and inverted
  M4 DIN 439 counter-bearing hex nut pocket at (18.20, 15.25, Z in [29.45, 31.80])
- Flush form-fitting 2.00 mm removable Service Cover (Tibia_Cover) with blind
  encapsulated pivot cap and 3x M2 DIN 7991 countersinks into blind M2 Ruthex bosses.
"""

import math
import os
import sys
import FreeCAD as App
import Part

# =============================================================================
# Centralized Engineering Constants (Style Guide §7)
# =============================================================================
REPO_ROOT = "/home/bjoern/Workspace/Hexapods/lasius"
MODELS_DIR = f"{REPO_ROOT}/hardware/mechanics/models"
PARTS_TIBIA_DIR = f"{MODELS_DIR}/custom/v2/parts/tibia"
DO_EXPORT = ("--export" in sys.argv)

EXPORT_STEP_PARTS = f"{REPO_ROOT}/hardware/mechanics/export/step/custom/v2/parts/tibia"
EXPORT_STL_PARTS = f"{REPO_ROOT}/hardware/mechanics/export/stl/custom/v2/parts/tibia"

os.makedirs(PARTS_TIBIA_DIR, exist_ok=True)
if DO_EXPORT:
    for d in [EXPORT_STEP_PARTS, EXPORT_STL_PARTS]:
        os.makedirs(d, exist_ok=True)

# Material / Visual Identity Colors (Style Guide §6)
COLOR_CFRP = (0.20, 0.22, 0.25)        # Anthracite / Carbon PETG body
COLOR_COVER = (0.15, 0.15, 0.18)       # Graphite service cover

# Fixed Knee Servo & Pivot Interfaces (100% compatible with Femur_Assembly & leg_assembly)
KNEE_X = 18.20
KNEE_Y = 15.25
Z_MID = 9.00                           # Central plane of Tibia blade, Tarsus, Switch & Spring
Z_CAGE_MIN = -14.50                    # Lower Servo Cage cheek Z extent
Z_CAGE_MAX = +32.50                    # Upper Servo Cage cheek Z extent (counter-bearing side)
SERVO_X_MIN = 9.00                     # Servo body pocket X in [9.00, 49.80]
SERVO_X_MAX = 49.80
SERVO_Y_MIN = 5.00                     # Servo body pocket Y in [5.00, 25.50]
SERVO_Y_MAX = 25.50
CHEEK_Y_BOT_MIN = 0.00                 # Lower cheek Y in [0.00, 5.00] (5.00 mm)
CHEEK_Y_TOP_MAX = 31.70                # Upper cheek Y in [25.50, 31.70] (6.20 mm)
EAR_PAD_Z_MIN = 2.75                   # Flush with NR-645 ears at Z = 2.70 (0.05 mm clearance)
EAR_PAD_Z_MAX = 15.25

# Central Blade & Distal Fork Z-Stack (Centered at Z_MID = 9.00 mm)
BLADE_Z_MIN = 5.50                     # 7.00 mm outer bionic claw & dorsal sickle arch thickness
BLADE_Z_MAX = 12.50
WEB_Z_MIN = 7.75                       # 2.50 mm lower web under teardrop (100% flush with cheek Mittelsteg!)
WEB_Z_MAX = 10.25
FORK_Z_MIN = 3.80                      # 2.00 mm Fixed Cheek A (Z in [3.80, 5.80])
BAY_Z_MIN = 5.80                       # 6.40 mm internal mechanism bay (Z in [5.80, 12.20])
BAY_Z_MAX = 12.20
COVER_Z_MIN = 12.24                    # 0.04 mm axial clearance to bay step
COVER_Z_MAX = 14.24                    # 2.00 mm Service Cover Cheek B
X_FORK_RAMP_START = 54.00              # Smooth C2 flare 7.00 -> 10.44 mm into distal fork housing
X_FORK_RAMP_END = 62.00
X_COVER_SPLIT = 59.00                  # Contoured cover starts cleanly behind spring bay (with Bayonet Tab #1!)

# Option 2c-V2 Mechanism Coordinates (Shared with generate_tibia_assembly.py & generate_leg_assembly.py!)
TARSUS_PIV_X = 109.00                  # Deeply embedded 15.0 mm inside distal fork mouth (X=124.0)
TARSUS_PIV_Y = 20.50                   # >= 7.1 mm solid radial wall below Ø3.1 mm pin bore!
PIVOT_BORE_R = 1.55                    # Ø3.10 mm bore for Ø3.00 mm ISO 2338 dowel pin

SPRING_X = TARSUS_PIV_X - 41.50        # 67.50 mm (r = 41.50 mm lever arm in deep Tibia belly!)
SPRING_FLOOR_Y = 4.90                  # >= 4.90 mm solid PETG wall above Y = 0.00!
SPRING_PIN_R = 1.40                    # Ø2.80 mm lower locating boss
SPRING_PIN_L = 2.50

# NC Microswitch Placement (Omron D2FC-F-K, 0.0 deg HORIZONTAL, parallel to dead-straight Tarsus top flank)
# Tarsus dead-straight horizontal upper flank is at Y_t = +3.20 (Y_tibia = 23.70) from X_t = -44.0 to -12.0.
# Directly above the spring (X_tibia in [61.0, 79.9]), the massive solid Tibia housing ceiling sits flush at
# Y_tibia = 23.76 mm -> absorbs 100% of upward spring force! Microswitch sits horizontally at X_plunger = 83.50
# and is gently actuated purely as a side effect (0 N stop force on switch!), while X in [93.4, 115.5] between
# switch and pivot opens wide (Y = 28.0..28.8 -> 3.5..4.3 mm open air gap!).
# Switch rotated by RotZ(-90 deg) * RotX(180 deg):
#   local +X (plunger) -> (0, -1, 0)
#   local -X (3 straight pins) -> (0, +1, 0)
#   local +Y (length 0..12.8) -> (-1, 0, 0)
# Plunger tip in local coords is (7.10, 9.50, 0) -> placed at (83.50, 23.76, Z_MID) (0.06 mm CAD tangent clearance!)
SW_ANGLE_DEG = 0.0
SW_ROT = App.Rotation(App.Vector(0, 0, 1), -90.0 + SW_ANGLE_DEG).multiply(App.Rotation(App.Vector(1, 0, 0), 180.0))
_v_plunger = SW_ROT.multVec(App.Vector(7.10, 9.50, 0.0))
SW_ORIGIN = App.Vector(83.50 - _v_plunger.x, 23.76 - _v_plunger.y, Z_MID)
SW_PLACEMENT = App.Placement(SW_ORIGIN, SW_ROT)

# 2x M2 Service Cover Retaining Screws / Blind Ruthex Inserts + 2x Integrated Form-Fit Bayonet Locking Tabs!
# (Former upper-left Screw #1 at (66.0, 42.5) removed so the SVG-matched teardrop window sits 100% monolithic!)
COVER_SCREW_PTS = [
    (104.50, 33.10),   # 1. Distal fork top boss (>= 3.23 mm below roof Y=37.93, >= 4.5 mm above dust-baffle!)
    (79.50, 9.00),     # 2. Ventral belly boss (>= 3.60 mm above outer curve, >= 3.05 mm below +5 deg hard-stop)
]
M2_RUTHEX_R = 1.60                     # Ø3.20 mm Ruthex M2 heat-set insert bore
M2_THROUGH_R = 1.05                    # Ø2.10 mm M2 clearance hole


# =============================================================================
# Modular Geometry Helpers (Style Guide §7)
# =============================================================================
def make_bspline_interp(pts_2d, periodic=False):
    vecs = [App.Vector(p[0], p[1], 0.0) for p in pts_2d]
    bs = Part.BSplineCurve()
    bs.interpolate(vecs, PeriodicFlag=periodic)
    return bs.toShape()


def make_rounded_polygon_wire_2d(pts_radii, map_fn):
    """Build a closed 3D Part.Wire from (u, v, radius) 2D vertices mapped via map_fn."""
    n = len(pts_radii)
    pts = [App.Vector(p[0], p[1], 0.0) for p in pts_radii]
    radii = [p[2] for p in pts_radii]
    t_in, t_out, t_mid = [], [], []
    for i in range(n):
        p_prev = pts[(i - 1) % n]
        p_curr = pts[i]
        p_next = pts[(i + 1) % n]
        r = radii[i]
        v_in = (p_curr - p_prev)
        v_out = (p_next - p_curr)
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


def make_s_curve_edges_xz(p1, p2):
    """Harmonic G1 S-curve between p1 and p2 in the X-Z plane (Y = 0)."""
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
        p1.x + sign_x * r * math.sin(0.5 * (math.pi / 2.0 - ang)),
        0.0,
        p1.z + sign_z * (r - r * math.cos(0.5 * (math.pi / 2.0 - ang))),
    )
    pm2 = App.Vector(
        p2.x - sign_x * r * math.sin(0.5 * (math.pi / 2.0 - ang)),
        0.0,
        p2.z - sign_z * (r - r * math.cos(0.5 * (math.pi / 2.0 - ang))),
    )
    return [Part.Edge(Part.Arc(p1, pm1, p_inf)), Part.Edge(Part.Arc(p_inf, pm2, p2))]


def make_hex_nut_pocket_z(cx, cy, z_bottom, z_top, sw=7.10):
    """Hexagonal prism (across flats = sw) aligned with Z for DIN 439 M4 nut."""
    r_circum = sw / math.sqrt(3.0)
    pts = [
        App.Vector(cx + r_circum * math.cos(math.radians(60.0 * i)),
                   cy + r_circum * math.sin(math.radians(60.0 * i)),
                   z_bottom)
        for i in range(6)
    ]
    pts.append(pts[0])
    return Part.Face(Part.makePolygon(pts)).extrude(App.Vector(0, 0, z_top - z_bottom))


# =============================================================================
# 1. Bionic Swooping Outer Silhouette & Teardrop Window (XY Plane)
# =============================================================================
def build_bionic_tibia_outer_wire():
    """
    Smooth G1-continuous swooping organic Tibia silhouette (at Z = 0) honoring
    the user's SVG sketch with generous structural walls around every feature:
      - Upper knee horn at (-5.0, 51.5) sweeping into dorsal peak (16.0, 54.5)
      - Graceful bionic dorsal curve tapering to distal fork mouth (124.0, 31.2)
      - Lower knee beak at (-24.5, 29.0) curving cleanly into flat servo belly Y = 0.0
      - Deep ventral belly (X in [2.0, 69.5], Y = 0.0) housing the vertical spring
      - Sweeping ventral S-curve up to distal fork mouth (124.0, 12.6)
    """
    # Exact concentric R = 17.50 mm circular arc centered on Tarsus Pivot (109.00, 20.50)
    # mates seamlessly across a constant 1.00 mm bionic joint gap with Tarsus shoulder R = 18.50 mm
    # across the entire 0.0 deg .. +5.0 deg rocker swing!
    R_MOUTH = 17.50
    a_top = math.radians(34.5)
    a_bot = math.radians(-26.8)
    p_mouth_top = App.Vector(TARSUS_PIV_X + R_MOUTH * math.cos(a_top), TARSUS_PIV_Y + R_MOUTH * math.sin(a_top), 0.0)
    p_mouth_mid = App.Vector(TARSUS_PIV_X + R_MOUTH, TARSUS_PIV_Y, 0.0)
    p_mouth_bot = App.Vector(TARSUS_PIV_X + R_MOUTH * math.cos(a_bot), TARSUS_PIV_Y + R_MOUTH * math.sin(a_bot), 0.0)
    e_mouth = Part.Arc(p_mouth_top, p_mouth_mid, p_mouth_bot).toShape()

    # Ventral curve from distal mouth (124.0, 12.6) back to flat servo floor (69.5, 0.0)
    # Fuller belly sweep at X=76..85 gives >= 3.6 mm solid wall below ventral M2 boss (79.5, 9.0)!
    p_belly_end = App.Vector(69.50, 0.00, 0.0)
    e_ventral_curve = make_bspline_interp([
        (p_mouth_bot.x, p_mouth_bot.y),
        (114.00, 12.00),
        (104.00, 11.40),
        (93.50, 10.00),
        (84.00, 6.00),
        (76.00, 2.00),
        (p_belly_end.x, p_belly_end.y),
    ])

    # Flat ventral base supporting servo cage & deep spring chamber (X in [2.0, 69.5], Y = 0.0)
    p_belly_start = App.Vector(2.00, 0.00, 0.0)
    e_belly_flat = Part.makeLine(p_belly_end, p_belly_start)

    # Sweeping lower knee beak (curves out-left to (-24.5, 29.0), matching SVG silhouette & clearing Femur!)
    p_beak_tip = App.Vector(-24.20, 29.50, 0.0)
    e_beak_bot = make_bspline_interp([
        (p_belly_start.x, p_belly_start.y),
        (-1.20, 6.50),
        (-5.80, 14.50),
        (-13.50, 21.50),
        (-21.20, 26.20),
        (p_beak_tip.x, p_beak_tip.y),
    ])

    # Rounded nose of lower knee beak
    p_beak_top = App.Vector(-22.20, 33.40, 0.0)
    e_beak_nose = Part.Arc(p_beak_tip, App.Vector(-25.40, 31.80, 0.0), p_beak_top).toShape()

    # Concave U-throat between lower knee beak and upper dorsal knee horn (SVG-matched deep claw X=13.9!)
    p_horn_bot = App.Vector(-2.80, 49.40, 0.0)
    e_throat = make_bspline_interp([
        (p_beak_top.x, p_beak_top.y),
        (-12.50, 32.10),
        (-2.00, 31.80),
        (6.50, 31.80),
        (11.80, 32.30),
        (13.90, 34.80),
        (13.90, 38.60),
        (12.20, 42.30),
        (8.60, 45.00),
        (3.20, 47.25),
        (p_horn_bot.x, p_horn_bot.y),
    ])

    # Rounded nose of upper dorsal knee horn (sleek SVG-matched sickle claw tip)
    p_horn_top = App.Vector(-2.50, 52.60, 0.0)
    e_horn_nose = Part.Arc(p_horn_bot, App.Vector(-4.20, 51.00, 0.0), p_horn_top).toShape()

    # Sweeping continuous bionic dorsal crest from upper horn (-2.5, 52.6) to distal mouth (124.0, 31.0)
    e_dorsal = make_bspline_interp([
        (p_horn_top.x, p_horn_top.y),
        (5.50, 54.15),
        (16.00, 54.60),
        (30.00, 53.80),
        (46.00, 51.80),
        (62.00, 49.00),
        (78.00, 45.40),
        (94.00, 41.00),
        (109.00, 36.50),
        (p_mouth_top.x, p_mouth_top.y),
    ])

    wire = Part.Wire([
        e_mouth, e_ventral_curve, e_belly_flat, e_beak_bot,
        e_beak_nose, e_throat, e_horn_nose, e_dorsal
    ])
    assert wire.isClosed(), "Bionic Tibia outer wire is not closed!"
    return wire


def build_teardrop_window_wire():
    """
    Concentric bionic Claw-Sickle Teardrop Window extending deep into the upper Knee Claw:
      - Upper edge runs mathematically concentric (~7.45 mm offset) beneath the outer dorsal crest e_dorsal,
        echoing & reinforcing the outer claw silhouette from X = 15.5 mm to X = 76.0 mm
      - Curved sleek proximal sickle tip at (15.5, 46.15) tucked cleanly inside the upper claw arch
        (>= 4.78 mm solid bridge to deepened SVG claw throat X=13.9!)
      - Generous round distal bulb at X = 76.0 (3.03 mm clear of Bayonet #2, 3.56 mm clear of switch bay)
      - Flowing crescent lower sweep dipping deeply to (67.6, 25.95) (>= 2.19 mm above spring stop Y=23.76,
        >= 3.26 mm clear of servo pocket/rear ear Y<=25.5!)
      - Enclosed Ø2.40 mm cable conduit runs dead-center inside the 7.45 mm dorsal sickle rib (>= 2.33 mm PETG both sides)
    """
    pts = [
        (15.50, 46.15),   # Curved sickle tip extending deep into the upper knee claw!
        (17.87, 47.06),   # Exact 7.45 mm concentric offset of dorsal crest peak
        (23.55, 46.85),   # Concentric dorsal sickle arch
        (31.27, 46.19),   # Concentric dorsal sickle arch
        (41.04, 44.99),   # Concentric dorsal sickle arch
        (50.83, 43.48),   # Concentric dorsal sickle arch
        (60.55, 41.59),   # Concentric dorsal sickle arch
        (68.20, 39.25),   # Smooth entry toward distal bulb
        (73.10, 37.05),   # Upper bulb shoulder (3.03 mm clear of Bayonet #2 Y>=39.15!)
        (76.00, 33.10),   # Full circular distal bulb apex (3.56 mm clear of switch bay X>=79.6!)
        (74.20, 28.40),   # Lower bulb curve
        (67.60, 25.95),   # Deep rounded teardrop belly (2.19 mm solid bridge above spring stop Y=23.76!)
        (60.50, 27.90),   # Smooth crescent belly sweeping up past servo rear ear
        (52.00, 32.80),   # Concave crescent underside echoing outer dorsal curve!
        (42.00, 38.45),   # Flowing bionic sickle taper
        (31.50, 42.90),   # Graceful sweep into knee claw arch
        (22.50, 45.25),   # Concentric curve into claw tip
        (17.50, 45.55),   # Sleek rounded underside into tip
    ]
    return Part.Wire([make_bspline_interp(pts, periodic=True)])


# =============================================================================
# 2. Coxa-Matched Parametric Twin Servo Cage (100% Zero-Collision Knee Interface)
# =============================================================================
def build_knee_servo_cage():
    """
    Build the twin-cheek bionic Knee Servo Cage (Z in [-14.50, +32.50], Y in [0.00, 31.70])
    unified 1:1 with Coxa v2 cheek morphology (R_FRONT = 4.50 mm, Z in [0.00, 18.00],
    crest plateau X in [9.20, 23.70]) and inverted M4 DIN 439 counter-bearing nut pocket
    at (18.20, 15.25). Tapers via G1 S-curves into distal fork Z in [3.80, 14.24] at X = 62.0 mm.
    (Cheek truss windows are cut in build_tibia_and_cover() AFTER fusing blade_central so the
    2.50 mm A-truss central spine is cleanly exposed on both cheeks!)
    """
    R_FRONT = 4.50
    NOSE_Z_MIN = 0.00
    NOSE_Z_MAX = 18.00
    X_CREST_REAR = 23.70
    X_REAR = 62.00
    Z_REAR_BOT = FORK_Z_MIN
    Z_REAR_TOP = COVER_Z_MAX

    # Symmetrical Cheek Profile in X-Z plane (Y = 0) — 100% matched to Coxa v2 front & crest!
    p_nose_bot = App.Vector(R_FRONT, 0.0, NOSE_Z_MIN)
    p_nose_top = App.Vector(R_FRONT, 0.0, NOSE_Z_MAX)
    p_front_b_end = App.Vector(0.0, 0.0, NOSE_Z_MIN + R_FRONT)
    p_front_t_start = App.Vector(0.0, 0.0, NOSE_Z_MAX - R_FRONT)
    k_f = R_FRONT * (1.0 - math.cos(math.pi / 4))
    pm_b = App.Vector(k_f, 0.0, NOSE_Z_MIN + k_f)
    pm_t = App.Vector(k_f, 0.0, NOSE_Z_MAX - k_f)

    p_f_top_in = App.Vector(7.20, 0.0, NOSE_Z_MAX)
    p_f_top_up = App.Vector(7.20, 0.0, Z_CAGE_MAX - 2.0)
    p_f_top_arc = App.Vector(9.20, 0.0, Z_CAGE_MAX)
    k2 = 2.0 * (1.0 - math.cos(math.pi / 4))
    pm_ct = App.Vector(7.20 + k2, 0.0, Z_CAGE_MAX - k2)
    p_crest_r = App.Vector(X_CREST_REAR, 0.0, Z_CAGE_MAX)
    p_rear_top = App.Vector(X_REAR, 0.0, Z_REAR_TOP)

    p_rear_bot = App.Vector(X_REAR, 0.0, Z_REAR_BOT)
    p_tab_r = App.Vector(X_CREST_REAR, 0.0, Z_CAGE_MIN)
    p_f_bot_arc = App.Vector(9.20, 0.0, Z_CAGE_MIN)
    p_f_bot_dn = App.Vector(7.20, 0.0, Z_CAGE_MIN + 2.0)
    pm_cb = App.Vector(7.20 + k2, 0.0, Z_CAGE_MIN + k2)
    p_f_bot_in = App.Vector(7.20, 0.0, NOSE_Z_MIN)

    edges_cheek = [
        Part.makeLine(p_nose_top, p_f_top_in),
        Part.makeLine(p_f_top_in, p_f_top_up),
        Part.Edge(Part.Arc(p_f_top_up, pm_ct, p_f_top_arc)),
        Part.makeLine(p_f_top_arc, p_crest_r),
    ] + make_s_curve_edges_xz(p_crest_r, p_rear_top) + [
        Part.makeLine(p_rear_top, p_rear_bot),
    ] + make_s_curve_edges_xz(p_rear_bot, p_tab_r) + [
        Part.makeLine(p_tab_r, p_f_bot_arc),
        Part.Edge(Part.Arc(p_f_bot_arc, pm_cb, p_f_bot_dn)),
        Part.makeLine(p_f_bot_dn, p_f_bot_in),
        Part.makeLine(p_f_bot_in, p_nose_bot),
        Part.Edge(Part.Arc(p_nose_bot, pm_b, p_front_b_end)),
        Part.makeLine(p_front_b_end, p_front_t_start),
        Part.Edge(Part.Arc(p_front_t_start, pm_t, p_nose_top)),
    ]
    cheek_face = Part.Face(Part.Wire(edges_cheek))

    # Lower cheek (Y in [0.00, 5.00]) & Upper cheek (Y in [25.50, 31.70])
    s_cheek_bot = cheek_face.extrude(App.Vector(0.0, 5.00, 0.0))
    s_cheek_top = cheek_face.extrude(App.Vector(0.0, 6.20, 0.0)).translate(App.Vector(0.0, 25.50, 0.0))

    # Front & Rear Servo Mounting Ear Blocks (Z in [2.75, 15.25], Y in [5.00, 25.50])
    # Front block X in [0.00, 9.00] recessed cleanly inside R_FRONT=4.50 cheeks
    R_EAR_BLK = 3.20
    map_xz = lambda v: App.Vector(v.x, 5.00, v.y)
    w_front_blk = make_rounded_polygon_wire_2d(
        [(0.0, EAR_PAD_Z_MIN, R_EAR_BLK), (9.0, EAR_PAD_Z_MIN, 0.0), (9.0, EAR_PAD_Z_MAX, 0.0), (0.0, EAR_PAD_Z_MAX, R_EAR_BLK)],
        map_xz,
    )
    blk_front = Part.Face(w_front_blk).extrude(App.Vector(0.0, 20.50, 0.0))
    blk_rear = Part.makeBox(8.20, 20.50, EAR_PAD_Z_MAX - EAR_PAD_Z_MIN, App.Vector(49.80, 5.00, EAR_PAD_Z_MIN))

    # Counter-bearing Tab Plate on +Z side (Z in [29.55, 32.50], X in [7.20, 23.70], Y in [0.00, 31.70])
    # Matches Coxa crest end X = 23.70; leaves 0.05 mm axial clearance to Knee_Servo top at Z = 29.50!
    tab_plate = Part.makeBox(X_CREST_REAR - 7.20, 31.70, 2.95, App.Vector(7.20, 0.00, 29.55))

    return s_cheek_bot.fuse(s_cheek_top).fuse(blk_front).fuse(blk_rear).fuse(tab_plate)


def cut_unified_cheek_truss_windows(shape):
    """
    Cut the 6-window Coxa-matched 45-deg A-Truss & Flank Trapezoid schema (Style Guide §3:
    w_strut = 2.50 mm, R_fillet = 1.40 mm, 100% symmetrical about Z = 9.00 mm) into both
    Lower Cheek (Y in [0.00, 5.00]) and Upper Cheek (Y in [25.50, 31.70]):
      - Zone 1 (X in [9.70, 21.20]): 2x 45-deg flank trapezoids (100% identical to Coxa v2!)
      - Zone 2a (X in [27.00, 42.50]): 2x inner 45-deg A-truss triangles (2.50 mm central rib Z in [7.75, 10.25])
      - Zone 2b (X in [30.50, 49.30]): 2x parallel outer 45-deg trapezoids (w = 2.50 mm diagonal, >= 2.50 mm rim)
    """
    R_WIN = 1.40
    map_win = lambda v: App.Vector(v.x, -1.0, v.y)
    truss_polys = [
        # Zone 1: Flank 45-deg trapezoids (100% identical to Coxa v2, 2.50 mm outer rim, zero micro-sliver!)
        [(9.70, 20.50, R_WIN), (21.70, 20.50, R_WIN), (21.70, 30.00, R_WIN), (19.20, 30.00, R_WIN)],
        [(9.70, -2.50, R_WIN), (19.20, -12.00, R_WIN), (21.70, -12.00, R_WIN), (21.70, -2.50, R_WIN)],
        # Zone 2a: Inner 45-deg A-truss triangles (2.50 mm central rib Z in [7.75, 10.25]!)
        [(27.00, 10.25, R_WIN), (42.50, 10.25, R_WIN), (27.00, 25.75, R_WIN)],
        [(27.00, -7.75, R_WIN), (42.50, 7.75, R_WIN), (27.00, 7.75, R_WIN)],
        # Zone 2b: Parallel 45-deg outer trapezoids (exact DX_45 = 3.536 mm -> w = 2.50 mm strut, >= 2.50 mm S-curve rim!)
        [(30.50, 25.79, R_WIN), (46.04, 10.25, R_WIN), (49.30, 10.25, R_WIN), (49.30, 13.85, R_WIN), (38.40, 22.35, R_WIN)],
        [(30.50, -7.79, R_WIN), (38.40, -4.35, R_WIN), (49.30, 4.15, R_WIN), (49.30, 7.75, R_WIN), (46.04, 7.75, R_WIN)],
    ]
    # Lower cheek full through-box (Y in [-1.0, 5.05], strictly inside open servo chamber X in [9.0, 49.8])
    box_bot = Part.makeBox(60.0, 6.05, 60.0, App.Vector(5.0, -1.00, -20.0))
    # Upper cheek full through-box (Y in [25.45, 36.0]):
    # Because the lower web directly above Y = 31.70 across X in [27.0, 49.3] is tapered to exact 2.50 mm
    # (Z in [7.75, 10.25]), all 6 A-truss windows pass cleanly into open air with ZERO hidden ledge!
    box_top = Part.makeBox(60.0, 10.55, 60.0, App.Vector(5.0, 25.45, -20.0))

    for poly in truss_polys:
        w_tr = make_rounded_polygon_wire_2d(poly, map_win)
        cut_tr = Part.Face(w_tr).extrude(App.Vector(0.0, 38.0, 0.0))
        shape = shape.cut(cut_tr.common(box_bot)).cut(cut_tr.common(box_top))
    return shape


def smoothstep5(x, x0, v0, x1, v1):
    """C2-continuous quintic Hermite transition from (x0, v0) to (x1, v1)."""
    if x <= x0:
        return v0
    if x >= x1:
        return v1
    t = (x - x0) / (x1 - x0)
    s = t * t * t * (t * (t * 6.0 - 15.0) + 10.0)
    return v0 + (v1 - v0) * s


def build_outer_blade_envelope(outer_face):
    """
    Build the full-thickness 7.00 mm outer bionic Tibia blade flaring smoothly (C2) into
    the 10.44 mm distal sensor fork across X in [54.0, 62.0].
    Preserves full 7.00 mm outer claw & dorsal sickle arch thickness everywhere!
    """
    xs_out = [X_FORK_RAMP_START + (X_FORK_RAMP_END - X_FORK_RAMP_START) * i / 8.0 for i in range(9)]

    def xz_bspline(pts_xz):
        bs = Part.BSplineCurve()
        bs.interpolate([App.Vector(x, -10.0, z) for x, z in pts_xz])
        return bs.toShape()

    p_l_lo = App.Vector(-30.0, -10.0, BLADE_Z_MIN)
    p_l_hi = App.Vector(-30.0, -10.0, BLADE_Z_MAX)
    p_r_lo = App.Vector(135.0, -10.0, FORK_Z_MIN)
    p_r_hi = App.Vector(135.0, -10.0, COVER_Z_MAX)

    e_lo_1 = Part.makeLine(p_l_lo, App.Vector(X_FORK_RAMP_START, -10.0, BLADE_Z_MIN))
    e_lo_2 = xz_bspline([(x, smoothstep5(x, X_FORK_RAMP_START, BLADE_Z_MIN, X_FORK_RAMP_END, FORK_Z_MIN)) for x in xs_out])
    e_lo_3 = Part.makeLine(App.Vector(X_FORK_RAMP_END, -10.0, FORK_Z_MIN), p_r_lo)
    e_right = Part.makeLine(p_r_lo, p_r_hi)
    e_hi_3 = Part.makeLine(p_r_hi, App.Vector(X_FORK_RAMP_END, -10.0, COVER_Z_MAX))
    e_hi_2 = xz_bspline([(x, smoothstep5(x, X_FORK_RAMP_START, BLADE_Z_MAX, X_FORK_RAMP_END, COVER_Z_MAX)) for x in reversed(xs_out)])
    e_hi_1 = Part.makeLine(App.Vector(X_FORK_RAMP_START, -10.0, BLADE_Z_MAX), p_l_hi)
    e_left = Part.makeLine(p_l_hi, p_l_lo)

    w_env = Part.Wire([e_lo_1, e_lo_2, e_lo_3, e_right, e_hi_3, e_hi_2, e_hi_1, e_left])
    env_solid = Part.Face(w_env).extrude(App.Vector(0.0, 80.0, 0.0))
    prism_outer = outer_face.extrude(App.Vector(0.0, 0.0, 30.0)).translate(App.Vector(0.0, 0.0, -5.0))
    return env_solid.common(prism_outer)


def cut_lower_web_mittelsteg_taper(shape):
    """
    Harmonize ONLY the lower web of the Tibia Kralle BELOW the teardrop window (Y >= 31.70,
    directly seated on the 2.50 mm upper cheek Mittelsteg) while keeping the entire outer
    dorsal sickle arch & proximal knee claws at full 7.00 mm thickness:
      - Proximal C2 taper (X in [16.0, 27.0]): smoothly narrows 7.00 mm -> 2.50 mm
      - Cheek-parallel zone (X in [27.0, 49.3]): exact 2.50 mm (Z in [7.75, 10.25]),
        100% flush with the 2.50 mm Mittelsteg of the 6-window 45-deg A-truss cheek!
      - Distal C2 flare (X in [49.3, 55.0]): smoothly widens 2.50 mm -> 7.00 mm into rear cheek/fork
      - Top mask runs strictly inside the open teardrop air cavity -> NEVER touches the 7.00 mm dorsal arch!
    """
    X_L0, X_L1 = 16.00, 27.00
    X_R0, X_R1 = 49.30, 55.00

    # XY mask strictly covering the lower web (Y in [CHEEK_Y_TOP_MAX=31.70, midline of open teardrop cavity])
    mask_top_pts = [
        (15.50, 46.15),
        (20.00, 46.20),
        (27.00, 45.30),
        (35.00, 43.60),
        (42.00, 41.60),
        (49.30, 39.00),
        (56.00, 36.20),
    ]
    e_m_top = make_bspline_interp(mask_top_pts)
    p_m_tl = App.Vector(15.50, 46.15, 0.0)
    p_m_tr = App.Vector(56.00, 36.20, 0.0)
    p_m_br = App.Vector(56.00, CHEEK_Y_TOP_MAX, 0.0)
    p_m_bl = App.Vector(15.50, CHEEK_Y_TOP_MAX, 0.0)
    w_mask = Part.Wire([
        e_m_top,
        Part.makeLine(p_m_tr, p_m_br),
        Part.makeLine(p_m_br, p_m_bl),
        Part.makeLine(p_m_bl, p_m_tl),
    ])
    mask_prism = Part.Face(w_mask).extrude(App.Vector(0.0, 0.0, 30.0)).translate(App.Vector(0.0, 0.0, -5.0))

    # Build smooth C2-curved +Z and -Z cheek-side recess cutters (XZ extruded in Y)
    xs_l = [X_L0 + (X_L1 - X_L0) * i / 8.0 for i in range(9)]
    xs_r = [X_R0 + (X_R1 - X_R0) * i / 8.0 for i in range(9)]

    def xz_bs(pts_xz):
        bs = Part.BSplineCurve()
        bs.interpolate([App.Vector(x, 30.0, z) for x, z in pts_xz])
        return bs.toShape()

    # +Z cutter: removes material above Z_cut_hi(x) up to Z = 16.0 (strictly inside mask_prism!)
    Z_HI_OUT = 16.0
    e_hi_l = xz_bs([(x, smoothstep5(x, X_L0, BLADE_Z_MAX, X_L1, WEB_Z_MAX)) for x in xs_l])
    e_hi_m = Part.makeLine(App.Vector(X_L1, 30.0, WEB_Z_MAX), App.Vector(X_R0, 30.0, WEB_Z_MAX))
    e_hi_r = xz_bs([(x, smoothstep5(x, X_R0, WEB_Z_MAX, X_R1, BLADE_Z_MAX + 0.50)) for x in xs_r])
    w_cut_hi = Part.Wire([
        e_hi_l, e_hi_m, e_hi_r,
        Part.makeLine(App.Vector(X_R1, 30.0, BLADE_Z_MAX + 0.50), App.Vector(X_R1, 30.0, Z_HI_OUT)),
        Part.makeLine(App.Vector(X_R1, 30.0, Z_HI_OUT), App.Vector(X_L0, 30.0, Z_HI_OUT)),
        Part.makeLine(App.Vector(X_L0, 30.0, Z_HI_OUT), App.Vector(X_L0, 30.0, BLADE_Z_MAX)),
    ])
    cut_hi = Part.Face(w_cut_hi).extrude(App.Vector(0.0, 22.0, 0.0)).common(mask_prism)

    # -Z cutter: removes material below Z_cut_lo(x) down to Z = 2.0 (strictly inside mask_prism!)
    Z_LO_OUT = 2.0
    e_lo_l = xz_bs([(x, smoothstep5(x, X_L0, BLADE_Z_MIN, X_L1, WEB_Z_MIN)) for x in xs_l])
    e_lo_m = Part.makeLine(App.Vector(X_L1, 30.0, WEB_Z_MIN), App.Vector(X_R0, 30.0, WEB_Z_MIN))
    e_lo_r = xz_bs([(x, smoothstep5(x, X_R0, WEB_Z_MIN, X_R1, BLADE_Z_MIN - 0.50)) for x in xs_r])
    w_cut_lo = Part.Wire([
        e_lo_l, e_lo_m, e_lo_r,
        Part.makeLine(App.Vector(X_R1, 30.0, BLADE_Z_MIN - 0.50), App.Vector(X_R1, 30.0, Z_LO_OUT)),
        Part.makeLine(App.Vector(X_R1, 30.0, Z_LO_OUT), App.Vector(X_L0, 30.0, Z_LO_OUT)),
        Part.makeLine(App.Vector(X_L0, 30.0, Z_LO_OUT), App.Vector(X_L0, 30.0, BLADE_Z_MIN)),
    ])
    cut_lo = Part.Face(w_cut_lo).extrude(App.Vector(0.0, 22.0, 0.0)).common(mask_prism)

    return shape.cut(cut_hi).cut(cut_lo)


# =============================================================================
# 3. Build Monolithic Tibia_Body & Form-Fit Tibia_Cover
# =============================================================================
def build_tibia_and_cover():
    print("--- Generating Lasius Bionic Monocoque Tibia v2 & Service Cover (Option 2c-V2) ---")

    outer_wire = build_bionic_tibia_outer_wire()
    outer_face = Part.Face(outer_wire)
    teardrop_wire = build_teardrop_window_wire()

    # A+B. Full-thickness 7.00 mm Outer Bionic Claw + smooth C2 flare into 10.44 mm Distal Fork
    blade_outer = build_outer_blade_envelope(outer_face)

    # C. Fuse Outer Blade + Knee Servo Cage, then cut unified 6-window Coxa-matched cheek trusses
    #    and harmonize ONLY the lower web under the teardrop smoothly to the 2.50 mm cheek Mittelsteg!
    servo_cage = build_knee_servo_cage()
    tibia_raw = blade_outer.fuse(servo_cage)
    tibia_raw = cut_lower_web_mittelsteg_taper(tibia_raw)
    tibia_raw = cut_unified_cheek_truss_windows(tibia_raw)

    # D. Cut Repositioned Organic Teardrop Window (cleanly through central blade!)
    win_cut = Part.Face(teardrop_wire).extrude(App.Vector(0.0, 0.0, 30.0)).translate(App.Vector(0.0, 0.0, -5.0))
    tibia_raw = tibia_raw.cut(win_cut)

    # E. Cut Exact Knee Servo Pocket, Cable Grommet Relief, 4x M2.5 Bores & Counter-Bearing M4 Nut Seat
    servo_pocket = Part.makeBox(SERVO_X_MAX - SERVO_X_MIN, SERVO_Y_MAX - SERVO_Y_MIN, 55.0,
                                App.Vector(SERVO_X_MIN, SERVO_Y_MIN, -20.0))
    servo_ear_clear_f = Part.makeBox(8.50, 20.50, 22.70, App.Vector(0.80, 5.00, -20.0))
    servo_ear_clear_r = Part.makeBox(8.50, 20.50, 22.70, App.Vector(49.50, 5.00, -20.0))
    # Clear Knee Servo horn & top spline zone (X in [4, 32], Y in [2.5, 28], Z in [-20, 0])
    servo_horn_clear = Part.makeBox(26.0, 25.5, 22.7, App.Vector(5.2, 2.5, -20.0))
    # Knee counter-bearing M4 screw bore + DIN 439 hex nut pocket at (18.20, 15.25)
    knee_screw_bore = Part.makeCylinder(2.05, 8.0, App.Vector(KNEE_X, KNEE_Y, 27.0))
    knee_nut_pocket = make_hex_nut_pocket_z(KNEE_X, KNEE_Y, 29.45, 31.80, sw=7.10)

    tibia_raw = (
        tibia_raw.cut(servo_pocket)
        .cut(servo_ear_clear_f)
        .cut(servo_ear_clear_r)
        .cut(knee_screw_bore)
        .cut(knee_nut_pocket)
    )
    # 4x NR-645 Servo Mounting Screw Holes (D = 2.20 mm)
    for sx, sy in [(4.65, 10.25), (4.65, 20.25), (53.15, 10.25), (53.15, 20.25)]:
        tibia_raw = tibia_raw.cut(Part.makeCylinder(1.10, 20.0, App.Vector(sx, sy, 0.0)))

    # =========================================================================
    # F. Cut Option 2c-V2 Internal Mechanism Bay (Z in [5.80, 12.25] -> 6.45 mm clear!)
    # =========================================================================
    BAY_H = 6.45  # Cuts from Z = 5.80 up through Z = 12.25 (open to removable Service Cover!)

    # 1. Straight Parallel Lever Arm + Dual Symmetrical Ceiling Stops + Labyrinth Dust Seal + Square Lower Fork Exit!
    #    - Spring chamber at X in [61.0, 73.5], Y in [SPRING_FLOOR_Y=4.90, 23.76] (>= 4.90 mm solid PETG floor!)
    #    - Primary broad dead-flat Ceiling Stop (0 deg) DIRECTLY ABOVE THE SPRING (X in [61.0, 79.9], Y = 23.76):
    #      absorbs 100% of upward spring force! NC microswitch at X in [80.2, 93.0] is actuated purely as a side effect.
    #    - Secondary flat Ceiling Stop + Labyrinth Dust Baffle BETWEEN MICROSWITCH & PIVOT (X in [93.4, 113.5]):
    #      * X in [93.4, 98.6] at Y = 23.76 frames the microswitch symmetrically (0.06 mm flush seal at 0 deg)
    #      * X in [98.6, 113.5] hugs the circular pivot hub contour with ~0.35 mm concentric dust-labyrinth clearance
    #        across the ENTIRE 0.0 deg..+5.0 deg stroke (blocks grit/dust without ever pinching or blocking motion!)
    #    - Parallel +5.0 deg broad lower Overload Hard-Stop from (77.5, 13.42) to (99.0, 15.29), then drops cleanly
    #      & squarely (90 deg) down through the ventral Tibia edge (Y = 8.0) -> ZERO razor-thin pointed wedge!
    map_bay = lambda v: App.Vector(v.x, v.y, BAY_Z_MIN)
    bay_poly = [
        (61.00, SPRING_FLOOR_Y, 1.50),     # Bottom-left of deep belly spring pocket
        (73.50, SPRING_FLOOR_Y, 1.50),     # Bottom-right of spring pocket
        (77.50, 13.42, 1.80),              # Left start of +5.0 deg parallel Overload Hard-Stop
        (99.00, 15.29, 0.80),              # Right end of +5.0 deg Hard-Stop -> square clean drop to bottom edge!
        (99.00, 8.00, 0.00),               # Cleanly opens down past ventral Tibia edge (no pointy sliver!)
        (128.00, 8.00, 0.00),              # Distal lower fork exit (open to exterior!)
        (128.00, 28.50, 0.00),             # Distal upper fork exit (leaves clean ~2.1 mm solid lip at R=17.5!)
        (113.50, 27.35, 1.50),             # Distal hub shoulder flare (+5 deg outward Tarsus swing room)
        (108.50, 26.35, 2.00),             # Concentric labyrinth dust-seal arch over pivot hub (0.4 mm gap!)
        (103.50, 24.90, 1.50),             # Curved dust-baffle step descending smoothly to secondary stop
        (98.60, 23.76, 0.60),              # Right end of secondary flat Ruhe-Anschlag + dust seal
        (93.40, 23.76, 0.30),              # Left end of secondary stop (meets microswitch pocket wall cleanly!)
        (93.40, 28.00, 0.30),              # Merges seamlessly inside microswitch pocket
        (80.00, 28.00, 0.40),              # Merges seamlessly inside microswitch pocket
        (79.90, 23.76, 0.50),              # Right end of primary broad flat Ceiling Stop directly over spring!
        (61.00, 23.76, 1.20),              # Left end of primary broad flat Ceiling Stop (18.9 mm wide!)
    ]
    bay_lever_cut = Part.Face(make_rounded_polygon_wire_2d(bay_poly, map_bay)).extrude(App.Vector(0.0, 0.0, BAY_H))

    # 2. Horizontal NC Microswitch Body Pocket + Tapered STRAIGHT UNBENT PIN & SOLDER ROOM!
    #    Top ceiling of solder bay tapers parallel to the sloping dorsal roof so the dorsal
    #    structural arch stays >= 3.60 mm thick EVERYWHERE while leaving 4.0..5.9 mm REAL
    #    free solder/heatshrink room above ALL 3 STRAIGHT UNBENT 3.3 mm pins!
    sw_body_cut = Part.makeBox(7.20, 13.40, BAY_H, App.Vector(-0.20, -0.30, -0.5 * BAY_H))
    map_sw = lambda v: App.Vector(v.x, v.y, -0.5 * BAY_H)
    sw_solder_poly = [
        (0.00, -0.80, 0.50),
        (-7.30, -0.80, 1.40),   # Right pin (X=91.2): 4.00 mm free solder room + >= 3.60 mm dorsal roof wall!
        (-9.40, 13.40, 1.40),   # Left pin (X=81.4): 6.10 mm free solder room + >= 4.00 mm dorsal roof wall!
        (0.00, 13.40, 0.50),
    ]
    sw_pins_solder_cut = Part.Face(make_rounded_polygon_wire_2d(sw_solder_poly, map_sw)).extrude(
        App.Vector(0.0, 0.0, BAY_H)
    )
    sw_bay_cut = sw_body_cut.fuse(sw_pins_solder_cut)
    sw_bay_cut.Placement = SW_PLACEMENT

    # 3. Integral Lower Spring Locating Boss (Ø2.80 x 2.50 mm rising from Y = SPRING_FLOOR_Y at X = SPRING_X)
    lower_spring_pin = Part.makeCylinder(
        SPRING_PIN_R, SPRING_PIN_L + 0.30,
        App.Vector(SPRING_X, SPRING_FLOOR_Y - 0.30, Z_MID),
        App.Vector(0, 1, 0),
    )

    # 4. Two Integrated Omron Microswitch Locating Pins (Ø1.96 mm, R = 0.98 mm, Z in [5.60, 11.80])
    p_sw_h1 = SW_PLACEMENT.multVec(App.Vector(4.50, 2.50, 0.0))
    p_sw_h2 = SW_PLACEMENT.multVec(App.Vector(4.50, 9.00, 0.0))
    sw_pin1 = Part.makeCylinder(0.98, 6.20, App.Vector(p_sw_h1.x, p_sw_h1.y, 5.60), App.Vector(0, 0, 1))
    sw_pin2 = Part.makeCylinder(0.98, 6.20, App.Vector(p_sw_h2.x, p_sw_h2.y, 5.60), App.Vector(0, 0, 1))

    # 5. Enclosed Smooth B-Spline Internal Cable Conduit (Ø2.40 mm at Z = 8.20 inside full 7.00 mm dorsal sickle arch!)
    #    From microswitch solder bay top-left -> arches concentrically ABOVE the claw-sickle teardrop -> exits into Knee U-throat!
    Z_CONDUIT = 8.20
    pts_cable = [
        App.Vector(80.80, 39.20, Z_CONDUIT),
        App.Vector(75.80, 42.05, Z_CONDUIT),
        App.Vector(65.31, 44.52, Z_CONDUIT),
        App.Vector(53.47, 46.81, Z_CONDUIT),
        App.Vector(41.56, 48.69, Z_CONDUIT),
        App.Vector(29.62, 50.10, Z_CONDUIT),
        App.Vector(17.97, 50.84, Z_CONDUIT),
        App.Vector(11.50, 49.40, Z_CONDUIT),
        App.Vector(7.20, 43.20, Z_CONDUIT),
    ]
    bs_cable = Part.BSplineCurve()
    bs_cable.interpolate(pts_cable)
    spine_cable = Part.Wire([bs_cable.toShape()])
    t0_cable = bs_cable.tangent(bs_cable.FirstParameter)[0]
    circle_cable = Part.makeCircle(1.20, pts_cable[0], t0_cable)
    cable_conduit = spine_cable.makePipeShell([Part.Wire([circle_cable])], True, False)

    # 6. Encapsulated Blind Pivot Bore in Fixed Cheek A (Z in [4.60, 5.95]; outer wall Z in [3.80, 4.60] 100% closed!)
    pivot_bore_a = Part.makeCylinder(PIVOT_BORE_R, 1.35, App.Vector(TARSUS_PIV_X, TARSUS_PIV_Y, 4.60), App.Vector(0, 0, 1))

    # 7. Contoured Form-Fit Service Cover Rebate in +Z Face (wraps cleanly AROUND the monolithic claw-sickle teardrop!)
    #    Covers spring bay (X>=59, Y<=24.75) + microswitch & Tarsus fork (X>=77.7), leaving teardrop 100% monolithic!
    cover_poly_pts = [
        (X_COVER_SPLIT, -5.00, 0.00),      # Bottom-left behind spring floor
        (135.00, -5.00, 0.00),             # Bottom-right past distal mouth
        (135.00, 52.00, 0.00),             # Top-right
        (77.70, 52.00, 0.00),              # Top-left exit right of teardrop (X<=76.0) & left of switch bay (X>=79.6)
        (77.70, 28.40, 1.80),              # Sweeps down the rib between teardrop & switch
        (74.80, 24.75, 1.80),              # Smooth shoulder below deep teardrop belly (Y>=25.95) & above spring stop (Y<=23.76)
        (X_COVER_SPLIT, 24.75, 0.00),      # Left step above spring chamber (0.99 mm overlap on spring stop ceiling!)
    ]
    cover_rebate_wire = make_rounded_polygon_wire_2d(cover_poly_pts, lambda v: App.Vector(v.x, v.y, BAY_Z_MAX))
    cover_rebate = Part.Face(cover_rebate_wire).extrude(App.Vector(0.0, 0.0, 5.0))

    # 7b. Two Blind Form-Fit Bayonet Locking Pockets in Tibia_Body (positively lock left & top-mid cover edges with 2 screws!)
    #     Pocket #1 (left of spring bay, Y in [9.85, 20.15]): root relief X in [59.0, 60.65], tongue slot X in [56.75, 59.10]
    bayonet_p1_root = Part.makeBox(1.65, 10.30, 2.15, App.Vector(59.00, 9.85, 10.10))
    bayonet_p1_slot = Part.makeBox(2.35, 10.30, 1.70, App.Vector(56.75, 9.85, 10.10))
    #     Pocket #2 (upper-middle rib above teardrop bulb, Y in [39.15, 43.85]): root X in [77.66, 79.25], slot X in [75.35, 77.76]
    bayonet_p2_root = Part.makeBox(1.59, 4.70, 2.15, App.Vector(77.66, 39.15, 10.10))
    bayonet_p2_slot = Part.makeBox(2.41, 4.70, 1.70, App.Vector(75.35, 39.15, 10.10))
    bayonet_pockets = bayonet_p1_root.fuse(bayonet_p1_slot).fuse(bayonet_p2_root).fuse(bayonet_p2_slot)

    # Assemble Monolithic Tibia_Body
    tibia_body = (
        tibia_raw
        .cut(bay_lever_cut)
        .cut(sw_bay_cut)
        .cut(cable_conduit)
        .cut(cover_rebate)
        .cut(bayonet_pockets)
        .fuse(lower_spring_pin)
        .fuse(sw_pin1)
        .fuse(sw_pin2)
        .cut(pivot_bore_a)
    )

    # 8. Cut 2x Blind M2 Ruthex Heat-Set Insert Bores into solid Tibia_Body bosses (Z in [8.00, 12.25])
    for bx, by in COVER_SCREW_PTS:
        tibia_body = tibia_body.cut(Part.makeCylinder(M2_RUTHEX_R, 4.30, App.Vector(bx, by, 8.00), App.Vector(0, 0, 1)))
        tibia_body = tibia_body.cut(Part.makeCylinder(M2_THROUGH_R, 5.50, App.Vector(bx, by, 6.80), App.Vector(0, 0, 1)))

    try:
        tibia_body = tibia_body.removeSplitter()
    except Exception:
        pass

    # =========================================================================
    # G. Build Contoured Removable Service Cover (Tibia_Cover, Z in [12.24, 14.24]) + 2x Bayonet Tabs!
    # =========================================================================
    cover_prism = outer_face.extrude(App.Vector(0.0, 0.0, COVER_Z_MAX - COVER_Z_MIN)).translate(
        App.Vector(0.0, 0.0, COVER_Z_MIN)
    )
    # Inset contoured cover footprint by 0.06 mm for clean 3D-print slip clearance along the entire seam!
    # Note: cover_rebate_wire already lies at Z = BAY_Z_MAX (12.20), so extruding +5.0 covers Z in [12.20, 17.20]!
    cover_inset_wire = cover_rebate_wire.makeOffset2D(-0.06)
    cover_contour_prism = Part.Face(cover_inset_wire).extrude(App.Vector(0.0, 0.0, 5.0))
    # Match outer +Z ramp slope cleanly across X in [X_COVER_SPLIT, X_FORK_RAMP_END] (zero outer ridge!)
    z_ramp_split = BLADE_Z_MAX + (COVER_Z_MAX - BLADE_Z_MAX) * (
        (X_COVER_SPLIT + 0.06 - X_FORK_RAMP_START) / (X_FORK_RAMP_END - X_FORK_RAMP_START)
    )
    pts_cover_env = [
        App.Vector(135.0, -10.0, COVER_Z_MIN),
        App.Vector(X_COVER_SPLIT + 0.06, -10.0, COVER_Z_MIN),
        App.Vector(X_COVER_SPLIT + 0.06, -10.0, z_ramp_split),
        App.Vector(X_FORK_RAMP_END, -10.0, COVER_Z_MAX),
        App.Vector(135.0, -10.0, COVER_Z_MAX),
        App.Vector(135.0, -10.0, COVER_Z_MIN),
    ]
    cover_env = Part.Face(Part.makePolygon(pts_cover_env)).extrude(App.Vector(0.0, 80.0, 0.0))
    cover_base = cover_prism.common(cover_contour_prism).common(cover_env)

    # Fuse 2x Integral Form-Fit Bayonet Locking Tabs onto inner face of Tibia_Cover (0.10 mm clearance in pockets!)
    tab1_neck = Part.makeBox(1.45, 10.00, 2.15, App.Vector(59.10, 10.00, 10.20))
    tab1_tongue = Part.makeBox(3.65, 10.00, 1.50, App.Vector(56.90, 10.00, 10.20))
    tab2_neck = Part.makeBox(1.39, 4.40, 2.15, App.Vector(77.76, 39.30, 10.20))
    tab2_tongue = Part.makeBox(3.65, 4.40, 1.50, App.Vector(75.50, 39.30, 10.20))
    cover_base = cover_base.fuse(tab1_neck).fuse(tab1_tongue).fuse(tab2_neck).fuse(tab2_tongue)

    # Encapsulated Blind Pivot Bore on inner face of Cover (Z in [12.20, 13.45]; outer face Z=14.24 100% closed!)
    pivot_bore_b = Part.makeCylinder(PIVOT_BORE_R, 1.25, App.Vector(TARSUS_PIV_X, TARSUS_PIV_Y, 12.20), App.Vector(0, 0, 1))
    cover_solid = cover_base.cut(pivot_bore_b)

    # 2x M2 DIN 7991 Flush Countersinks (D_bore = 2.20 mm, Cone R=1.10 -> 2.15 mm at Z = 13.19..14.24)
    for bx, by in COVER_SCREW_PTS:
        c_bore = Part.makeCylinder(1.10, 4.0, App.Vector(bx, by, 11.50), App.Vector(0, 0, 1))
        c_cone = Part.makeCone(1.10, 2.15, 1.05, App.Vector(bx, by, COVER_Z_MAX - 1.05), App.Vector(0, 0, 1))
        cover_solid = cover_solid.cut(c_bore).cut(c_cone)

    try:
        cover_solid = cover_solid.removeSplitter()
    except Exception:
        pass

    # Verify ZERO collision between Tibia_Body and Tibia_Cover!
    coll_tc = tibia_body.common(cover_solid).Volume
    print(f"  Pairwise Check Tibia_Body <-> Tibia_Cover: {coll_tc:.4f} mm^3")
    assert coll_tc < 1e-4, f"Collision between Tibia_Body and Tibia_Cover: {coll_tc:.4f} mm^3!"

    # Save Canonical Tibia_Body: custom/v2/parts/tibia/tibia.FCStd
    fcstd_tibia_path = f"{PARTS_TIBIA_DIR}/tibia.FCStd"
    try:
        App.closeDocument("tibia")
    except Exception:
        pass
    doc_tibia = App.newDocument("tibia")
    obj_tibia = doc_tibia.addObject("Part::Feature", "Tibia_Body")
    obj_tibia.Label = "Tibia v2 Bionic Monocoque Body (Option 2c-V2, PETG)"
    obj_tibia.Shape = tibia_body
    if hasattr(obj_tibia, "ViewObject") and obj_tibia.ViewObject is not None:
        obj_tibia.ViewObject.Visibility = True
        obj_tibia.ViewObject.ShapeColor = COLOR_CFRP
    doc_tibia.recompute()
    doc_tibia.saveAs(fcstd_tibia_path)
    if DO_EXPORT:
        tibia_body.exportStep(f"{EXPORT_STEP_PARTS}/tibia.step")
        tibia_body.exportStl(f"{EXPORT_STL_PARTS}/tibia.stl")
    print(f"✔ Saved: {fcstd_tibia_path} (Valid={tibia_body.isValid()}, Solids={len(tibia_body.Solids)}, Volume={tibia_body.Volume:.1f} mm3)")
    print(f"  Tibia_Body BB: {tibia_body.BoundBox}")

    # Save Canonical Tibia_Cover: custom/v2/parts/tibia/tibia_cover.FCStd
    fcstd_cover_path = f"{PARTS_TIBIA_DIR}/tibia_cover.FCStd"
    try:
        App.closeDocument("tibia_cover")
    except Exception:
        pass
    doc_cover = App.newDocument("tibia_cover")
    obj_cover = doc_cover.addObject("Part::Feature", "Tibia_Cover")
    obj_cover.Label = "Tibia v2 Form-Fit Service Cover (Option 2c-V2, PETG)"
    obj_cover.Shape = cover_solid
    if hasattr(obj_cover, "ViewObject") and obj_cover.ViewObject is not None:
        obj_cover.ViewObject.Visibility = True
        obj_cover.ViewObject.ShapeColor = COLOR_COVER
    doc_cover.recompute()
    doc_cover.saveAs(fcstd_cover_path)
    if DO_EXPORT:
        cover_solid.exportStep(f"{EXPORT_STEP_PARTS}/tibia_cover.step")
        cover_solid.exportStl(f"{EXPORT_STL_PARTS}/tibia_cover.stl")
    print(f"✔ Saved: {fcstd_cover_path} (Valid={cover_solid.isValid()}, Solids={len(cover_solid.Solids)}, Volume={cover_solid.Volume:.1f} mm3)")
    print(f"  Tibia_Cover BB: {cover_solid.BoundBox}")

    for d in [doc_tibia, doc_cover]:
        try:
            App.closeDocument(d.Name)
        except Exception:
            pass


_is_main = (__name__ == "__main__") or (
    len(sys.argv) > 1 and os.path.basename(sys.argv[1]) == os.path.basename(__file__)
)
if _is_main:
    build_tibia_and_cover()
