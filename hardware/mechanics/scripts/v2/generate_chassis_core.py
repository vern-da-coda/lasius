#!/usr/bin/env python3
"""
Generate Lasius Monocoque Central Core & Assembly v2 (FreeCAD 1.1+)
===================================================================
Architecture:
  - Integral 3D-printed monocoque central core (chassis_core.FCStd) spanning
    the 51.30 mm vertical gap between Body_Bottom (Z = 2.00 mm) and
    Body_Top (Z = 53.30 mm).
  - 2-Level Monocoque Structure separated by a continuous horizontal Intermediate Deck
    (Zwischenboden, Z = 18.00 .. 20.00 mm):
    * Level 1 (Lower Level, Z = 0.02 .. 18.00 mm):
      - 100% flush sealing plug (Z in [0.02, 3.62 mm]) closing Body_Bottom's 160 x 50 mm cutout
        with 6x cylindrical leg-swing clearance scallops (R = 45.0 mm).
      - Lower encapsulated 2S LiPo battery tunnel (Z = 3.62 .. 18.00 mm, X in [-84.5, +44.5 mm])
        with rear insertion/extraction port and front battery stop wall.
      - Dedicated front-floor cable passage for Belly Pan VL53L5CX ToF sensor.
    * Intermediate Deck (Zwischenboden, Z = 18.00 .. 20.00 mm):
      - Continuous 2.00 mm horizontal deck spanning the entire monocoque interior.
      - Integrated M2.5 screw bosses (Z = 20.00 .. 21.98 mm) for rigid horizontal mounting.
      - Dedicated cable pass-through slots (Front ToF slot, Rear LiPo power slot).
    * Level 2 (Upper Level, Z = 20.00 .. 53.28 mm):
      - Open-top electronics tub with uniform 2.00 mm wall thickness.
      - 4 structural corner pillars at (±45.0, ±30.0 mm) with Ruthex M3 insert pockets.
      - 6 lateral cable ports at Z in [23.00, 35.00 mm] with integrated micro zip-tie saddles.
      - Tandem horizontal controller layout (Option 1):
        - Front PCA9685 at X = +43.25 mm (clamping screws face UP +Z, wire entry -Y, pins +Y Left).
        - Rear PCA9685 at X = -43.25 mm (clamping screws face UP +Z, wire entry +Y, pins -Y Right).
        - Center TCA9548A at X = 0.00 mm, Y = 0.00 mm (flat horizontal, 90° rotated).
"""

import math
import os
import sys
import FreeCAD as App
import Part

print("--- Generating Lasius Monocoque Central Core (custom/v2/parts/chassis/chassis_core.FCStd) ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts/chassis"
asm_dir = f"{repo_root}/hardware/mechanics/models/custom/v2"
cots_dir = f"{repo_root}/hardware/mechanics/models/cots"
export_step_dir = f"{repo_root}/hardware/mechanics/export/step/custom/v2"
export_stl_dir = f"{repo_root}/hardware/mechanics/export/stl/custom/v2"

for d in [
    models_dir,
    asm_dir,
    f"{export_step_dir}/parts/chassis",
    f"{export_stl_dir}/parts/chassis",
]:
    os.makedirs(d, exist_ok=True)


def make_rounded_rect_solid(x_min, x_max, y_min, y_max, r_corner, z_min, z_max):
    """Constructs a filleted 3D solid prism in the X-Y plane extruded along Z."""
    dx = x_max - x_min
    dy = y_max - y_min
    r = min(r_corner, dx / 2.0 - 0.1, dy / 2.0 - 0.1)
    k = r * (1.0 - 1.0 / math.sqrt(2.0))
    pts = [
        (x_min + r, y_max),
        (x_max - r, y_max),
        (x_max - k, y_max - k),
        (x_max, y_max - r),
        (x_max, y_min + r),
        (x_max - k, y_min + k),
        (x_max - r, y_min),
        (x_min + r, y_min),
        (x_min + k, y_min + k),
        (x_min, y_min + r),
        (x_min, y_max - r),
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


def make_dovetail_prism(x_throat, x_base, w_throat, w_base, z_min, z_max, x_overshoot=0.0):
    """Constructs a dovetail prism in the X-Y plane extruded along Z."""
    if abs(x_overshoot) > 1e-4:
        pts = [
            (x_throat + x_overshoot,  w_throat / 2.0),
            (x_throat,                w_throat / 2.0),
            (x_base,                  w_base / 2.0),
            (x_base,                 -w_base / 2.0),
            (x_throat,               -w_throat / 2.0),
            (x_throat + x_overshoot, -w_throat / 2.0),
        ]
    else:
        pts = [
            (x_throat,  w_throat / 2.0),
            (x_base,    w_base / 2.0),
            (x_base,   -w_base / 2.0),
            (x_throat, -w_throat / 2.0),
        ]
    v = [App.Vector(px, py, z_min) for px, py in pts]
    edges = [Part.makeLine(v[i], v[(i + 1) % len(v)]) for i in range(len(v))]
    face = Part.Face(Part.Wire(edges))
    return face.extrude(App.Vector(0.0, 0.0, z_max - z_min))


def make_filleted_boss(x_start, x_end, y_half, r_corner, z_min, z_max):
    """Constructs a filleted rectangular boss in X-Y extruded along Z."""
    dx = abs(x_end - x_start)
    xmin = min(x_start, x_end)
    xmax = max(x_start, x_end)
    ymin = -y_half
    ymax = y_half
    r = min(r_corner, dx / 2.0 - 0.1, y_half - 0.1)
    k = r * (1.0 - 1.0 / math.sqrt(2.0))
    if x_end > x_start:  # Front boss
        pts = [
            (xmin, ymax),
            (xmax - r, ymax),
            (xmax - k, ymax - k),
            (xmax, ymax - r),
            (xmax, ymin + r),
            (xmax - k, ymin + k),
            (xmax - r, ymin),
            (xmin, ymin),
        ]
    else:  # Rear boss
        pts = [
            (xmax, ymin),
            (xmin + r, ymin),
            (xmin + k, ymin + k),
            (xmin, ymin + r),
            (xmin, ymax - r),
            (xmin + k, ymax - k),
            (xmin + r, ymax),
            (xmax, ymax),
        ]
    v = [App.Vector(px, py, z_min) for px, py in pts]
    wire = Part.Wire(Part.makePolygon(v + [v[0]]))
    face = Part.Face(wire)
    return face.extrude(App.Vector(0.0, 0.0, z_max - z_min))

# -----------------------------------------------------------------------------
# 1. Build Part: chassis_core.FCStd
# -----------------------------------------------------------------------------
doc_core_name = "chassis_core"
try:
    App.closeDocument(doc_core_name)
except Exception:
    pass
doc_core = App.newDocument(doc_core_name)
fcstd_core_path = f"{models_dir}/chassis_core.FCStd"

# 1.1 Extended Bionic Outer Hull Spline Extrusion (X in [-84.5, +84.5 mm], Z = 2.02 .. 53.28 mm)
#     Completely covers and seals the 160 x 50 mm cutout window in Body_Bottom (X in [-80, +80], Y in [-25, +25]),
#     with waist Y = ±29.0 mm (4.0 mm overlap per side) and ends X = ±84.5 mm (4.5 mm overlap per end),
#     plus an integrated flush lower window-sealing plate (Z = 0.02 .. 2.02 mm, X in [-79.9, +79.9], Y in [-24.9, +24.9])
#     and 6x cylindrical leg-swing clearance scallops (R = 43.20 mm around all 6 Coxa pivots for Z >= 1.98 mm).
pts_half = [
    App.Vector(84.5, 0.0, 0.0),
    App.Vector(84.5, 22.0, 0.0),
    App.Vector(78.0, 28.5, 0.0),
    App.Vector(62.0, 29.5, 0.0),
    App.Vector(45.0 + 7.0 * math.cos(math.radians(20)), 30.0 + 7.0 * math.sin(math.radians(20)), 0.0),
    App.Vector(45.0, 37.0, 0.0),
    App.Vector(45.0 - 7.0 * math.cos(math.radians(45)), 30.0 + 7.0 * math.sin(math.radians(45)), 0.0),
    App.Vector(20.0, 29.5, 0.0),
    App.Vector(0.0, 29.0, 0.0),
    App.Vector(-20.0, 29.5, 0.0),
    App.Vector(-45.0 + 7.0 * math.cos(math.radians(45)), 30.0 + 7.0 * math.sin(math.radians(45)), 0.0),
    App.Vector(-45.0, 37.0, 0.0),
    App.Vector(-45.0 - 7.0 * math.cos(math.radians(20)), 30.0 + 7.0 * math.sin(math.radians(20)), 0.0),
    App.Vector(-62.0, 29.5, 0.0),
    App.Vector(-78.0, 28.5, 0.0),
    App.Vector(-84.5, 22.0, 0.0),
    App.Vector(-84.5, 0.0, 0.0),
]
spline_half = Part.BSplineCurve()
spline_half.interpolate(pts_half)

pts_lower = [App.Vector(p.x, -p.y, 0.0) for p in reversed(pts_half[1:-1])]
spline_lower = Part.BSplineCurve()
spline_lower.interpolate([pts_half[-1]] + pts_lower + [pts_half[0]])

wire = Part.Wire([spline_half.toShape(), spline_lower.toShape()])
face = Part.Face(wire)

# Cut 6x Cylindrical Leg-Swing Clearance Envelopes in 2D first so makeOffset2D(-2.00) produces
# an exact, uniform 2.00 mm normal wall thickness along both the spline AND all 6 leg-swing scallops!
coxa_pivots = [
    (86.0, 65.0),
    (0.0, 75.0),
    (-86.0, 65.0),
    (86.0, -65.0),
    (0.0, -75.0),
    (-86.0, -65.0),
]
outer_2d_face = face
for cx, cy in coxa_pivots:
    c_face = Part.Face(Part.Wire(Part.makeCircle(45.00, App.Vector(cx, cy, 0.0))))
    outer_2d_face = outer_2d_face.cut(c_face)

hull = outer_2d_face.extrude(App.Vector(0.0, 0.0, 51.26))
hull.translate(App.Vector(0.0, 0.0, 2.02))

# Flush Window-Sealing Plug (X in [-79.90, +79.90], Y in [-24.90, +24.90], Z in [0.02, 3.62 mm])
# Closes 100% of Body_Bottom's 160.0 x 50.0 mm cutout window (including the 4 corners under the leg swing path):
win_plug = Part.makeBox(159.80, 49.80, 3.60, App.Vector(-79.90, -24.90, 0.02))
for cx, cy in coxa_pivots:
    swing_cyl = Part.makeCylinder(45.00, 52.50, App.Vector(cx, cy, 1.98), App.Vector(0, 0, 1))
    win_plug = win_plug.cut(swing_cyl)

core_solid = hull.fuse(win_plug)

# 1.2 Cut Full Open-Top Monocoque Tub Cavity (Z = 3.62 .. 55.00 mm) via Exact 2D Normal Offset (-1.60 mm)
#     Every outer wall segment (spline + leg-swing scallops) has an exact 1.60 mm (4-perimeter) wall thickness!
t_wall = 1.60
inner_face_valid = outer_2d_face.Faces[0].makeOffset2D(-t_wall).Faces[0]
inner_tub = inner_face_valid.extrude(App.Vector(0.0, 0.0, 52.00))
inner_tub.translate(App.Vector(0.0, 0.0, 3.62))
core_solid = core_solid.cut(inner_tub)

# 1.3 Add Solid Intermediate Deck (Zwischenboden, Z = 24.00 .. 26.00 mm)
#     Spans the entire inner tub (thickness 2.00 mm), cleanly separating the lower battery tunnel
#     (Level 1, Z in [3.62, 24.00 mm], clear height 20.38 mm) from the upper electronics tub
#     (Level 2, Z in [26.00, 53.28 mm]).
deck_solid = inner_face_valid.extrude(App.Vector(0.0, 0.0, 2.00))
deck_solid.translate(App.Vector(0.0, 0.0, 24.00))
core_solid = core_solid.fuse(deck_solid)

# 1.4 Fuse the 4 Main Standoff Pillars at (±45.0, ±30.0 mm) Solidly with the Outer Wall
#     Bridges each pillar directly into the outer hull wall across Z = 2.02 .. 53.28 mm,
#     eliminating the narrow wall-to-pillar gap and maximizing horizontal wall stiffness in the upper section:
standoffs = [
    (45.0, 30.0),
    (45.0, -30.0),
    (-45.0, 30.0),
    (-45.0, -30.0),
]
r_pillar = 4.80
for sx, sy in standoffs:
    sign_y = 1.0 if sy > 0 else -1.0
    cyl = Part.makeCylinder(r_pillar, 51.26, App.Vector(sx, sy, 2.02), App.Vector(0, 0, 1))
    if sy > 0:
        bridge = Part.makeBox(2 * r_pillar, 8.50, 51.26, App.Vector(sx - r_pillar, sy, 2.02))
    else:
        bridge = Part.makeBox(2 * r_pillar, 8.50, 51.26, App.Vector(sx - r_pillar, sy - 8.50, 2.02))
    pillar_solid = cyl.fuse(bridge).common(hull)
    core_solid = core_solid.fuse(pillar_solid)
    bore = Part.makeCylinder(1.70, 55.00, App.Vector(sx, sy, 0.0), App.Vector(0, 0, 1))
    top_pocket = Part.makeCylinder(2.10, 7.50, App.Vector(sx, sy, 46.30), App.Vector(0, 0, 1))
    bot_pocket = Part.makeCylinder(2.10, 7.50, App.Vector(sx, sy, 1.50), App.Vector(0, 0, 1))
    core_solid = core_solid.cut(bore).cut(top_pocket).cut(bot_pocket)

# 1.5 Lower Level Battery Compartment Features (Z in [3.62, 24.00 mm])
# Front battery stop wall at X = +44.5 mm (keeps 2S LiPo securely seated in X in [-83.5, +44.0 mm]):
front_stop = Part.makeBox(2.00, 36.40, 20.38, App.Vector(44.50, -18.20, 3.62))
core_solid = core_solid.fuse(front_stop)

# Battery rear clearance pocket (ensures 0.0000 mm^3 collision with 2S LiPo reaching X = -83.5 mm):
bat_rear_clearance = Part.makeBox(6.00, 36.40, 20.38, App.Vector(-85.00, -18.20, 3.62))
core_solid = core_solid.cut(bat_rear_clearance)

# Cut Battery Service Aperture through the Bottom Plate (Z in [-0.50, 4.50 mm]):
# Preserves all 4 corners of the 160 x 50 mm Body_Bottom window as solid sealing gussets,
# leaves the front floor (X in [44.0, 80.0]) and rear transverse bridge (X in [-80.0, -72.0]) solid,
# and leaves 6.0 mm lateral rims along Y in [-25.0, -19.0] and [19.0, 25.0] mm.
# Provides 100% collision-free downward battery extraction via Belly Pan removal.
bat_service_cut = make_rounded_rect_solid(-72.0, 44.0, -19.0, 19.0, 5.0, -0.50, 4.50)
core_solid = core_solid.cut(bat_service_cut)

# Note: Horizontal rear battery extraction port removed - battery extraction is now 100% downward
# through the Belly Pan service hatch, leaving the rear bulkhead solid and dirt-sealed.

# 1.6 Pass-Through Slots between Levels (Z in [23.50, 28.50 mm]):
# - Front ToF cable slot at X in [46.50, 51.50], Y in [-6.00, +6.00]
tof_slot = Part.makeBox(5.00, 12.00, 5.00, App.Vector(46.50, -6.00, 23.50))
core_solid = core_solid.cut(tof_slot)
# - Front ToF protective floor channel (through bottom plate into belly pan):
tof_ch = Part.makeBox(5.00, 12.00, 5.00, App.Vector(46.50, -6.00, -0.50))
core_solid = core_solid.cut(tof_ch)
# - Rear battery power lead slot (Z in [23.50, 28.50 mm], X in [-79.0, -73.0], Y in [-10.0, +10.0]):
bat_slot = Part.makeBox(6.00, 20.00, 5.00, App.Vector(-79.00, -10.00, 23.50))
core_solid = core_solid.cut(bat_slot)

# 1.7 Cut 4x Organic Bionic Inter-Leg Bay Cable Ports (Vorschlag A) at Z in [28.50, 40.00 mm]
#     Harmonized with the organic ant-thorax morphology: smooth bionic capsule apertures with R = 4.50 mm corner radii,
#     completely replacing sharp rectangular chop cuts with flowing G1-continuous transitions.
#     Placed in the safe inter-leg bays completely clear of all 6 Coxa swing cylinders (R = 45.0 mm):
#     - Front-Bay Left at X = +32.50 mm (X in [25.5, 39.5 mm]) -> > 12.0 mm to FL, > 6.5 mm to ML
#     - Rear-Bay Left at X = -32.50 mm (X in [-39.5, -25.5 mm]) -> > 12.0 mm to RL, > 6.5 mm to ML
#     - Front-Bay Right at X = +32.50 mm
#     - Rear-Bay Right at X = -32.50 mm
def make_organic_port_cutter(x_center, z_center, width, height, r_corner, y_min, y_max):
    """Constructs an organic, corner-filleted bionic aperture cutter in the X-Z plane, extruded through the wall along Y."""
    dx = width
    dz = height
    r = min(r_corner, dx / 2.0 - 0.1, dz / 2.0 - 0.1)
    x1, x2 = x_center - dx / 2.0, x_center + dx / 2.0
    z1, z2 = z_center - dz / 2.0, z_center + dz / 2.0
    k = r * (1.0 - 1.0 / math.sqrt(2.0))
    pts = [
        (x1 + r, z2),
        (x2 - r, z2),
        (x2 - k, z2 - k),
        (x2, z2 - r),
        (x2, z1 + r),
        (x2 - k, z1 + k),
        (x2 - r, z1),
        (x1 + r, z1),
        (x1 + k, z1 + k),
        (x1, z1 + r),
        (x1, z2 - r),
        (x1 + k, z2 - k),
    ]
    v = [App.Vector(px, y_min, pz) for px, pz in pts]
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
    return face.extrude(App.Vector(0.0, y_max - y_min, 0.0))


organic_ports = [
    (32.50, 34.25, 14.00, 11.50, 4.50, 15.00, 45.00),    # Front-Bay Left (FL + ML)
    (-32.50, 34.25, 14.00, 11.50, 4.50, 15.00, 45.00),   # Rear-Bay Left (RL)
    (32.50, 34.25, 14.00, 11.50, 4.50, -45.00, -15.00),  # Front-Bay Right (FR + MR)
    (-32.50, 34.25, 14.00, 11.50, 4.50, -45.00, -15.00), # Rear-Bay Right (RR)
]
for x_c, z_c, pw, ph, pr, y_min, y_max in organic_ports:
    p_solid = make_organic_port_cutter(x_c, z_c, pw, ph, pr, y_min, y_max)
    core_solid = core_solid.cut(p_solid)

    # Dual Micro-Zip-Tie Saddles at Port Sill (for 2.5 mm cable ties):
    sign_y = 1.0 if y_min > 0 else -1.0
    ys = 27.0 * sign_y
    for x_sad in [x_c - 3.00, x_c + 3.00]:
        s_ch1 = Part.makeBox(1.30, 2.80, 8.0, App.Vector(x_sad - 1.50, ys - 1.40, 24.0))
        s_ch2 = Part.makeBox(1.30, 2.80, 8.0, App.Vector(x_sad + 1.50, ys - 1.40, 24.0))
        core_solid = core_solid.cut(s_ch1).cut(s_ch2)

# 1.8 Add Integrated M2.5 Screw Bosses on Intermediate Deck (Z = 26.00 .. 27.98 mm, height 1.98 mm)
# Bosses support PCB bottom at Z = 28.00 mm with 0.02 mm clearance, keeping clamping screw heads
# facing UP (+Z at Z = 39.60 mm) and wire entrances horizontal (+Y / -Y):
boss_h = 1.98
bosses = [
    # Front PCA9685 (center: 43.25, -3.00 mm, pattern: 56.0 x 19.0 mm)
    (43.25 + 28.00, -3.00 + 9.50),
    (43.25 + 28.00, -3.00 - 9.50),
    (43.25 - 28.00, -3.00 + 9.50),
    (43.25 - 28.00, -3.00 - 9.50),
    # Rear PCA9685 (center: -43.25, +3.00 mm, pattern: 56.0 x 19.0 mm)
    (-43.25 + 28.00, 3.00 + 9.50),
    (-43.25 + 28.00, 3.00 - 9.50),
    (-43.25 - 28.00, 3.00 + 9.50),
    (-43.25 - 28.00, 3.00 - 9.50),
    # Center TCA9548A (center: 0.00, 0.00 mm, pattern: 26.0 mm spacing along Y)
    (0.00, 13.00),
    (0.00, -13.00),
]
for bx, by in bosses:
    boss = Part.makeCylinder(2.60, boss_h, App.Vector(bx, by, 26.00), App.Vector(0, 0, 1))
    bore = Part.makeCylinder(1.025, 4.00, App.Vector(bx, by, 24.00), App.Vector(0, 0, 1))
    core_solid = core_solid.fuse(boss).cut(bore)

# 1.9 Add Front & Rear Integrated Vertical Dovetail Sockets for Head & Gaster Mounts (Concept 1)
# Bionic Bosses:
# - Front Boss at X in [84.00, 92.50 mm], Y in [-14.00, +14.00 mm], Z in [2.02, 53.28 mm]
# - Rear Boss at X in [-92.50, -84.00 mm], Y in [-14.00, +14.00 mm], Z in [2.02, 53.28 mm]
f_boss = make_filleted_boss(84.00, 92.50, 14.00, 2.50, 2.02, 53.28)
r_boss = make_filleted_boss(-84.00, -92.50, 14.00, 2.50, 2.02, 53.28)
core_solid = core_solid.fuse(f_boss).fuse(r_boss)

# Dovetail Female Pockets (Cut from Z = 6.00 mm to 55.00 mm, leaving 4.0 mm bottom stop collar at Z in [2.02, 6.00 mm]):
# - Front Dovetail: Throat at X = 92.50 mm (w = 14.0 mm), Base at X = 85.50 mm (w = 22.0 mm)
f_cut = make_dovetail_prism(92.50, 85.50, 14.00, 22.00, 6.00, 55.00, x_overshoot=2.0)
# - Rear Dovetail: Throat at X = -92.50 mm (w = 14.0 mm), Base at X = -85.50 mm (w = 22.0 mm)
r_cut = make_dovetail_prism(-92.50, -85.50, 14.00, 22.00, 6.00, 55.00, x_overshoot=-2.0)
core_solid = core_solid.cut(f_cut).cut(r_cut)

# Central Cable Pass-Through Tunnels (12.0 x 8.0 mm at Z in [28.00, 36.00 mm] leading directly into Level 2):
cable_cut_front = Part.makeBox(20.00, 12.00, 8.00, App.Vector(80.00, -6.00, 28.00))
cable_cut_rear = Part.makeBox(20.00, 12.00, 8.00, App.Vector(-95.00, -6.00, 28.00))
core_solid = core_solid.cut(cable_cut_front).cut(cable_cut_rear)

core_solid = core_solid.removeSplitter()

part_obj = doc_core.addObject("Part::Feature", "Chassis_Core")
part_obj.Label = "Chassis Monocoque Central Core (v2)"
part_obj.Shape = core_solid
if hasattr(part_obj, "ViewObject") and part_obj.ViewObject is not None:
    part_obj.ViewObject.Visibility = True
    part_obj.ViewObject.ShapeColor = (0.22, 0.24, 0.27)
doc_core.recompute()

doc_core.saveAs(fcstd_core_path)
# Export visual mesh for Three.js / Web-Dashboard
core_solid.exportStl(f"{repo_root}/hardware/mechanics/export/urdf/meshes/chassis_core.stl")
if "--export" in sys.argv:
    core_solid.exportStep(f"{export_step_dir}/parts/chassis/chassis_core.step")
    core_solid.exportStl(f"{export_stl_dir}/parts/chassis/chassis_core.stl")
print(f"✔ Saved Monocoque Part -> {fcstd_core_path} (Valid={core_solid.isValid()}, Volume={core_solid.Volume:.1f} mm^3)")
App.closeDocument(doc_core_name)

# -----------------------------------------------------------------------------
# 2. Build Assembly: chassis_core_assembly.FCStd
# -----------------------------------------------------------------------------
doc_asm_name = "chassis_core_assembly"
try:
    App.closeDocument(doc_asm_name)
except Exception:
    pass
doc_asm = App.newDocument(doc_asm_name)
fcstd_asm_path = f"{asm_dir}/chassis_core_assembly.FCStd"
doc_asm.saveAs(fcstd_asm_path)

doc_core = App.openDocument(fcstd_core_path)
doc_pca = App.openDocument(f"{cots_dir}/pca9685_board.FCStd")
doc_tca = App.openDocument(f"{cots_dir}/tca9548a_board.FCStd")
doc_bat = App.openDocument(f"{cots_dir}/battery_lipo_2s.FCStd")

asm_part = doc_asm.addObject("App::Part", "Chassis_Core_Assembly")
asm_part.Label = "Lasius Monocoque Central Core Assembly (v2)"
for o in asm_part.Origin.OutList:
    if hasattr(o, "Visibility"):
        o.Visibility = False
asm_part.Origin.Visibility = False
asm_part.Visibility = True


def make_link(name, label, src_obj, placement, color=None):
    link = doc_asm.addObject("App::Link", name)
    link.Label = label
    link.setLink(src_obj)
    link.Placement = placement
    asm_part.addObject(link)
    link.Visibility = True
    if hasattr(link, "ViewObject") and link.ViewObject is not None:
        link.ViewObject.Visibility = True
        if color:
            link.ViewObject.OverrideMaterial = True
            mat = link.ViewObject.ShapeMaterial
            mat.DiffuseColor = color
            link.ViewObject.ShapeMaterial = mat
    return link


COLOR_CORE = (0.22, 0.24, 0.27)  # Anthracite / Carbon PA-CF monocoque
COLOR_PCA = (0.04, 0.38, 0.88)   # Signal Blue PCA9685
COLOR_TCA = (0.50, 0.15, 0.70)   # Signal Violet TCA9548A
COLOR_BAT = (0.85, 0.65, 0.10)   # Gold / Yellow 2S LiPo

# 1. Monocoque Core Shell
make_link("Chassis_Core", "1. Monocoque Core Shell", doc_core.Chassis_Core, App.Placement(), COLOR_CORE)

# 2. Front PCA9685 Board at X = +43.25 mm, Y = -3.00 mm, Z = 28.00 mm (Horizontal, pins +Y Left, clamps UP)
p_pca_front = App.Placement(App.Vector(43.25, -3.00, 28.00), App.Rotation(App.Vector(0, 0, 1), 0.0))
make_link("Board_PCA9685_Left", "2. PCA9685 Front (Horizontal, Pins +Y Left, Clamps UP)", doc_pca.PCA9685_Board, p_pca_front, COLOR_PCA)

# 3. Rear PCA9685 Board at X = -43.25 mm, Y = +3.00 mm, Z = 28.00 mm (Horizontal, pins -Y Right, clamps UP)
p_pca_rear = App.Placement(App.Vector(-43.25, 3.00, 28.00), App.Rotation(App.Vector(0, 0, 1), 180.0))
make_link("Board_PCA9685_Right", "3. PCA9685 Rear (Horizontal, Pins -Y Right, Clamps UP)", doc_pca.PCA9685_Board, p_pca_rear, COLOR_PCA)

# 4. TCA9548A Multiplexer seated on support bosses at (0.0, 0.0, 28.00 mm)
r_tca = App.Rotation(App.Vector(0, 0, 1), 90.0)
p_tca = App.Placement(App.Vector(0.0, 0.0, 28.00), r_tca)
make_link("Board_TCA9548A", "4. TCA9548A I2C Multiplexer (Horizontal, Center)", doc_tca.TCA9548A_Board, p_tca, COLOR_TCA)

# 5. 2S LiPo Battery Pack in lower tunnel (Z = 3.75 .. 17.75 mm)
p_bat = App.Placement(App.Vector(0.0, 0.0, 3.75), App.Rotation())
make_link("Battery_LiPo_2S", "5. 2S 7.4V LiPo Battery Pack (Lower Level Tunnel)", doc_bat.Battery_LiPo_2S, p_bat, COLOR_BAT)

doc_asm.recompute()
doc_asm.save()
# Assemblies are logical structures, not exported to STEP/STL (never manufactured in one piece)
print(f"✔ Saved Monocoque Assembly -> {fcstd_asm_path}")

# Verify 0.0000 mm^3 collisions
items = [(o.Name, o.Shape) for o in asm_part.Group if hasattr(o, "Shape") and not o.Shape.isNull()]
max_coll = 0.0
for i in range(len(items)):
    for j in range(i + 1, len(items)):
        n1, s1 = items[i]
        n2, s2 = items[j]
        if s1.BoundBox.intersect(s2.BoundBox):
            v = s1.common(s2).Volume
            if v > 1e-4:
                print(f"  ❌ COLLISION {n1} <-> {n2}: {v:.4f} mm^3")
                max_coll = max(max_coll, v)
if max_coll <= 1e-4:
    print("  ✅ ZERO COLLISIONS in chassis_core_assembly.FCStd (0.0000 mm^3)!")

os._exit(0)
