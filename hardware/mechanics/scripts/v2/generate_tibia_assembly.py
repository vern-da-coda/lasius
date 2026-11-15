#!/usr/bin/env python3
"""
Generate Lasius Tibia v2 Canonical Parts & Subsystem Assembly
=============================================================
Canonical Output Paths (Hardware-as-Code 3-Tier Architecture):
- COTS Parts:
  * hardware/mechanics/models/cots/microswitch_subminiature.FCStd
  * hardware/mechanics/models/cots/compression_spring_4x12.FCStd
- Custom v2 Tibia Parts:
  * hardware/mechanics/models/custom/v2/parts/tibia/tibia.FCStd        (Tibia_Body)
  * hardware/mechanics/models/custom/v2/parts/tibia/tibia_cover.FCStd  (Tibia_Cover)
  * hardware/mechanics/models/custom/v2/parts/tibia/tibia_rocker.FCStd (Tibia_Rocker)
- Custom v2 Tibia Subassembly:
  * hardware/mechanics/models/custom/v2/tibia_assembly.FCStd           (Tibia_Assembly)
- Mirrored 1:1 in hardware/mechanics/export/{step,stl}/custom/v2/
"""

import math
import os
import sys
import zipfile
import FreeCAD as App
import Part

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
sys.path.append(f"{repo_root}/hardware/mechanics/scripts/v2")
import generate_tibia

print("--- Generating Lasius Tibia v2 Canonical Parts & Assembly ---")

models_dir = f"{repo_root}/hardware/mechanics/models"
cots_dir = f"{models_dir}/cots"
v2_dir = f"{models_dir}/custom/v2"
parts_tibia_dir = f"{v2_dir}/parts/tibia"

export_step_v2 = f"{repo_root}/hardware/mechanics/export/step/custom/v2"
export_stl_v2 = f"{repo_root}/hardware/mechanics/export/stl/custom/v2"
export_step_parts = f"{export_step_v2}/parts/tibia"
export_stl_parts = f"{export_stl_v2}/parts/tibia"

for d in [cots_dir, v2_dir, parts_tibia_dir, export_step_v2, export_stl_v2, export_step_parts, export_stl_parts]:
    os.makedirs(d, exist_ok=True)

# Colors
COLOR_CFRP = (0.22, 0.22, 0.24)        # Dark carbon anthracite
COLOR_COVER = (0.28, 0.28, 0.32)       # Contrasting carbon cover
COLOR_SERVO = (0.12, 0.12, 0.12)       # Matte black servo
COLOR_ORANGE = (0.92, 0.45, 0.10)      # Anodized orange rocker
COLOR_SWITCH = (0.15, 0.15, 0.15)      # Matte black switch
COLOR_SPRING = (0.85, 0.85, 0.88)      # Stainless spring
COLOR_BRASS = (0.85, 0.70, 0.20)       # Brass hardware
COLOR_STEEL = (0.80, 0.80, 0.82)       # Steel fasteners

# =============================================================================
# 1. Build COTS: microswitch_subminiature.FCStd & compression_spring_4x12.FCStd
# =============================================================================
print("1. Building COTS: microswitch_subminiature.FCStd & compression_spring_4x12.FCStd...")
for dname in ["microswitch_subminiature", "compression_spring_4x12"]:
    try:
        App.closeDocument(dname)
    except Exception:
        pass

doc_sw = App.newDocument("microswitch_subminiature")
fcstd_sw_path = f"{cots_dir}/microswitch_subminiature.FCStd"

# Switch body: 6.5 x 12.8 x 5.8 mm (Z in [-2.9, +2.9])
sw_body = Part.makeBox(6.5, 12.8, 5.8, App.Vector(0.0, 0.0, -2.9))
h1 = Part.makeCylinder(1.05, 10.0, App.Vector(4.5, 2.5, -5.0), App.Vector(0, 0, 1))
h2 = Part.makeCylinder(1.05, 10.0, App.Vector(4.5, 9.0, -5.0), App.Vector(0, 0, 1))
sw_body = sw_body.cut(h1).cut(h2)

# Plunger button behind leaf lever (X in [6.2, 6.7])
pin_button = Part.makeCylinder(1.00, 0.5, App.Vector(6.2, 9.5, 0.0), App.Vector(1, 0, 0))
# Leaf lever (X in [6.7, 7.1], Y in [1.5, 13.0], Z in [-2.0, +2.0])
lever_box = Part.makeBox(0.4, 11.5, 4.0, App.Vector(6.7, 1.5, -2.0))

lug1 = Part.makeBox(2.5, 0.6, 2.0, App.Vector(-2.5, 1.5, -1.0))
lug2 = Part.makeBox(2.5, 0.6, 2.0, App.Vector(-2.5, 6.4, -1.0))
lug3 = Part.makeBox(2.5, 0.6, 2.0, App.Vector(-2.5, 11.3, -1.0))

sw_solid = sw_body.fuse(pin_button).fuse(lever_box).fuse(lug1).fuse(lug2).fuse(lug3)
obj_sw = doc_sw.addObject("Part::Feature", "Microswitch_Subminiature")
obj_sw.Label = "Subminiature Microswitch (12.8x6.5x5.8 mm with Leaf Lever)"
obj_sw.Shape = sw_solid
doc_sw.recompute()
doc_sw.saveAs(fcstd_sw_path)

doc_sp = App.newDocument("compression_spring_4x12")
fcstd_sp_path = f"{cots_dir}/compression_spring_4x12.FCStd"
sp_outer = Part.makeCylinder(2.25, 12.0, App.Vector(0, 0, 0), App.Vector(0, 1, 0))
sp_inner = Part.makeCylinder(1.65, 14.0, App.Vector(0, -1.0, 0), App.Vector(0, 1, 0))
sp_tube = sp_outer.cut(sp_inner)
for i in range(5):
    y_slot = 1.5 + i * 2.0
    slot_cutter = Part.makeBox(6.0, 1.0, 1.0, App.Vector(-3.0, y_slot - 0.5, -0.5))
    slot_cutter.rotate(App.Vector(0, y_slot, 0), App.Vector(0, 1, 0), i * 45.0)
    sp_tube = sp_tube.cut(slot_cutter)

obj_sp = doc_sp.addObject("Part::Feature", "Compression_Spring")
obj_sp.Label = "Stainless Compression Spring (Da=4.5 mm, L=12 mm)"
obj_sp.Shape = sp_tube
doc_sp.recompute()
doc_sp.saveAs(fcstd_sp_path)

# =============================================================================
# 2. Build Canonical Rocker: custom/v2/parts/tibia/tibia_rocker.FCStd
# =============================================================================
print("2. Building Canonical Part: tibia_rocker.FCStd...")
try:
    App.closeDocument("tibia_rocker")
except Exception:
    pass
doc_rocker = App.newDocument("tibia_rocker")
fcstd_rocker_path = f"{parts_tibia_dir}/tibia_rocker.FCStd"

p_hub_bot = App.Vector(1.16, 5.20, 0.0)
p_spring_end = App.Vector(-14.02, 8.50, 0.0)

loc_sole = [
    p_hub_bot,
    App.Vector(-0.50, -1.69, 0.0),
    App.Vector(-3.46, -10.21, 0.0),
    App.Vector(-7.82, -18.14, 0.0),
    App.Vector(-12.42, -22.74, 0.0),
    App.Vector(-17.37, -25.56, 0.0),
    App.Vector(-21.83, -25.89, 0.0),
]
loc_tip = [
    App.Vector(-21.83, -25.89, 0.0),
    App.Vector(-23.41, -25.78, 0.0),
    App.Vector(-24.22, -23.82, 0.0),
]
loc_top = [
    App.Vector(-24.22, -23.82, 0.0),
    App.Vector(-20.66, -20.42, 0.0),
    App.Vector(-16.60, -14.52, 0.0),
    App.Vector(-14.48, -6.75, 0.0),
    App.Vector(-13.74, 1.60, 0.0),
    p_spring_end,
]

c_sole = Part.BSplineCurve()
c_sole.interpolate(loc_sole)
e_sole = c_sole.toShape()
e_tip = Part.Arc(loc_tip[0], loc_tip[1], loc_tip[2]).toShape()
c_top = Part.BSplineCurve()
c_top.interpolate(loc_top)
e_top = c_top.toShape()

# Upper lever contact face at X = +0.25 mm (0.05 mm rest clearance to microswitch lever at X = +0.20 mm)
pts_upper = [
    p_hub_bot,
    App.Vector(2.0, 12.0, 0.0),
    App.Vector(2.5, 18.0, 0.0),
    App.Vector(2.5, 26.0, 0.0),
    App.Vector(2.5, 34.5, 0.0),
    App.Vector(0.25, 34.5, 0.0),
    App.Vector(0.25, 24.0, 0.0),
    App.Vector(-2.0, 16.0, 0.0),
    App.Vector(-5.0, 13.5, 0.0),
    App.Vector(-11.0, 8.50, 0.0),
    p_spring_end,
]
edges_upper = [Part.makeLine(pts_upper[i], pts_upper[i + 1]) for i in range(len(pts_upper) - 1)]

all_edges = edges_upper + [e_top, e_tip, e_sole]
rocker_wire = Part.Wire(all_edges)
rocker_face = Part.Face(rocker_wire)
rocker_solid = rocker_face.extrude(App.Vector(0.0, 0.0, 5.6)).translate(App.Vector(0.0, 0.0, -2.8))

# Pivot Bore (D = 3.10 mm, R = 1.55 mm) at (0.0, 10.0)
rocker_solid = rocker_solid.cut(Part.makeCylinder(1.55, 10.0, App.Vector(0.0, 10.0, -5.0), App.Vector(0, 0, 1)))
# Spring Boss at (-14.0, 8.50) (D = 3.00 mm, L = 2.50 mm up to Y = 11.00 mm)
rocker_solid = rocker_solid.fuse(Part.makeCylinder(1.50, 2.50, App.Vector(-14.0, 8.50, 0.0), App.Vector(0, 1, 0)))
# M2 Set Screw Pocket at (0.25..2.50, 32.5)
rocker_solid = rocker_solid.cut(Part.makeCylinder(1.00, 2.35, App.Vector(2.55, 32.5, 0.0), App.Vector(-1, 0, 0)))
rocker_solid = rocker_solid.removeSplitter()

obj_rocker = doc_rocker.addObject("Part::Feature", "Tibia_Rocker")
obj_rocker.Label = "Tibia Foot Rocker Lever (Organic Bionic Tarsus Wippe, PETG)"
obj_rocker.Shape = rocker_solid
if hasattr(obj_rocker, "ViewObject") and obj_rocker.ViewObject is not None:
    obj_rocker.ViewObject.Visibility = True
    obj_rocker.ViewObject.ShapeColor = COLOR_ORANGE
doc_rocker.recompute()
doc_rocker.saveAs(fcstd_rocker_path)
rocker_solid.exportStep(f"{export_step_parts}/tibia_rocker.step")
rocker_solid.exportStl(f"{export_stl_parts}/tibia_rocker.stl")
print(f"✔ Saved: {fcstd_rocker_path} (Valid={rocker_solid.isValid()}, Volume={rocker_solid.Volume:.1f} mm3)")

# =============================================================================
# 3. Build Canonical Monolithic Tibia Body & Removable Cover
# =============================================================================
print("3. Building Canonical Parts: tibia.FCStd & tibia_cover.FCStd...")


def build_organic_tibia_outer_wire():
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
    e3 = generate_tibia.make_g1_cubic_bspline(
        poles3, generate_tibia.circle_tangent_cw(c2, p2_e), generate_tibia.circle_tangent_cw(c4, p4_s)
    )

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
    e5 = generate_tibia.make_g1_cubic_bspline(
        poles5, generate_tibia.circle_tangent_cw(c4, p4_e), generate_tibia.circle_tangent_cw(c56, p56_s)
    )

    p6_e = App.Vector(-36.50, -14.25, 0.0)
    e6 = Part.makeLine(p56_e, p6_e)

    p_spring_cheek = App.Vector(-130.0, -0.5, 0.0)
    p_hub_left = App.Vector(-128.5, -14.0, 0.0)
    p_hub_bot = App.Vector(-122.0, -20.5, 0.0)

    arc_cheek_tip = Part.Arc(p_spring_cheek, App.Vector(-131.0, -8.0, 0.0), p_hub_left).toShape()
    arc_pivot_bot = Part.Arc(p_hub_left, App.Vector(-126.5, -19.0, 0.0), p_hub_bot).toShape()

    poles1 = [
        p_spring_cheek,
        (-128.0, 0.5),
        (-124.0, 2.8),
        (-116.0, 5.8),
        (-106.0, 8.8),
        (-92.0, 12.5),
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
    t_dorsal_start = App.Vector(1.0, 0.5, 0.0)
    e1 = generate_tibia.make_g1_cubic_bspline(poles1, t_dorsal_start, generate_tibia.circle_tangent_cw(c2, p2_s))

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
        (-115.00, -18.80),
        p_hub_bot,
    ]
    t_ventral_end = App.Vector(-1.0, -0.2, 0.0)
    e7 = generate_tibia.make_g1_cubic_bspline(poles7, App.Vector(-1.0, 0.0, 0.0), t_ventral_end)

    return Part.Wire([arc_cheek_tip, arc_pivot_bot, e7, e6, e5b, e5, e4, e3, e2, e1])


outer_wire = build_organic_tibia_outer_wire()

# Base Tibia Claw Body (Z in [-3.0, +4.0] mm)
claw_base = Part.Face(outer_wire).extrude(App.Vector(0, 0, 7.0)).translate(App.Vector(0, 0, -3.0))
w_cutout = generate_tibia.build_g1_claw_cutout_wire()
cutout_prism = Part.Face(w_cutout).extrude(App.Vector(0, 0, 60.0)).translate(App.Vector(0, 0, -30.0))
claw_base = claw_base.cut(cutout_prism)

ear_bosses = generate_tibia.build_servo_ear_bosses().cut(cutout_prism)
claw_base = claw_base.fuse(ear_bosses)
truss_cage = generate_tibia.build_triangulated_truss_servo_cage()
upper_cheeks = generate_tibia.build_upper_truss_cheeks()
tibia_base = claw_base.fuse(truss_cage).fuse(upper_cheeks).cut(cutout_prism)

# Servo body pocket + cable exit grommet relief at X in [9.00, 16.50], Y in [-3.60, +3.60], Z in [-20.00, -15.00]
servo_pocket = Part.makeBox(40.80, 20.30, 48.00, App.Vector(-31.65, -10.15, -20.00))
servo_cable_slot = Part.makeBox(7.50, 7.20, 5.00, App.Vector(9.00, -3.60, -20.00))
tibia_base = tibia_base.cut(servo_pocket).cut(servo_cable_slot)

screw_bore = Part.makeCylinder(2.05, 6.0, App.Vector(0.0, 0.0, -24.0))
nut_pocket = generate_tibia.make_hex_nut_pocket_z(0.0, 0.0, -22.40, -19.50, sw=7.10)
tibia_base = tibia_base.cut(screw_bore).cut(nut_pocket)

for sx, sy in [(13.00, 5.00), (13.00, -5.00), (-35.50, 5.00), (-35.50, -5.00)]:
    tibia_base = tibia_base.cut(Part.makeCylinder(1.25, 25.0, App.Vector(sx, sy, -3.20)))

# Extend Fork Cheeks to 11.0 mm total width (Z in [-5.0, +6.0] mm) and taper gently to 7.0 mm body
X_SPLIT = -92.0
X_RAMP_END = -82.0
DX_TONGUE = 3.5

prism_outer = Part.Face(outer_wire).extrude(App.Vector(0, 0, 40.0)).translate(App.Vector(0, 0, -20.0))

pts_back = [
    App.Vector(-150.0, -40.0, -5.0),
    App.Vector(X_SPLIT, -40.0, -5.0),
    App.Vector(X_RAMP_END, -40.0, -3.0),
    App.Vector(-150.0, -40.0, -3.0),
    App.Vector(-150.0, -40.0, -5.0),
]
wedge_back = Part.Face(Part.makePolygon(pts_back)).extrude(App.Vector(0.0, 80.0, 0.0)).common(prism_outer)
tibia_base = tibia_base.fuse(wedge_back)

pts_front = [
    App.Vector(X_SPLIT, -40.0, 4.0),
    App.Vector(X_SPLIT, -40.0, 6.0),
    App.Vector(X_RAMP_END, -40.0, 4.0),
    App.Vector(X_SPLIT, -40.0, 4.0),
]
ramp_front = Part.Face(Part.makePolygon(pts_front)).extrude(App.Vector(0.0, 80.0, 0.0)).common(prism_outer)
tibia_base = tibia_base.fuse(ramp_front)

# Cut Internal Clevis Slot & Sensor Bays
rot_deg = -67.59
rot_rad = math.radians(rot_deg)
rot_foot = App.Rotation(App.Vector(0, 0, 1), rot_deg)
px = -10.0 * math.sin(rot_rad)
py = 10.0 * math.cos(rot_rad)
base_pos = App.Vector(-122.0 - px, -14.0 - py, 0.5)
p_shank = App.Placement(base_pos, rot_foot)

slot_upper = Part.makeBox(6.5, 30.0, 6.0, App.Vector(-2.5, 8.0, -3.0))
slot_claw = Part.makeBox(45.0, 48.0, 6.0, App.Vector(-40.0, -32.0, -3.0))
sw_pocket = Part.makeBox(10.5, 16.5, 6.0, App.Vector(-10.0, 22.0, -3.0))

# Spring pocket spanning Y_s in [8.50, 20.60] with solid stop pillar (D=2.4 mm) from Y_s = 11.60 to 20.60
pocket_cyl = Part.makeCylinder(2.40, 12.10, App.Vector(-14.0, 8.50, 0.0), App.Vector(0, 1, 0))
stop_pillar = Part.makeCylinder(1.20, 9.00, App.Vector(-14.0, 11.60, 0.0), App.Vector(0, 1, 0))
spring_pocket = pocket_cyl.cut(stop_pillar)

cable_conduit = Part.makeCylinder(1.80, 50.0, App.Vector(-4.5, 35.0, 0.0), App.Vector(-0.15, 1.0, 0.0))

for c in [slot_upper, slot_claw, sw_pocket, spring_pocket, cable_conduit]:
    c.Placement = p_shank.multiply(c.Placement)

# Pivot bores at (-122.0, -14.0): Fixed Cheek A is Z in [-5.00, -2.50]
pivot_bore = Part.makeCylinder(1.55, 20.0, App.Vector(-122.0, -14.0, -10.0), App.Vector(0, 0, 1))
pivot_ruthex = Part.makeCylinder(2.15, 2.50, App.Vector(-122.0, -14.0, -5.00), App.Vector(0, 0, 1))

tibia_cut = (
    tibia_base.cut(slot_upper)
    .cut(slot_claw)
    .cut(sw_pocket)
    .cut(spring_pocket)
    .cut(cable_conduit)
    .cut(pivot_bore)
    .cut(pivot_ruthex)
)

# Formschluss Rebate in Tibia for Removable Cover:
cut_main = Part.makeBox(150.0 + X_SPLIT, 80.0, 3.5, App.Vector(-150.0, -40.0, 3.5))
tongue_pocket = Part.makeBox(DX_TONGUE + 0.10, 80.0, 0.8, App.Vector(X_SPLIT - 0.10, -40.0, 3.0))

# Microswitch Hole 1 (-2.40, 25.50): Integrated locating pin (D = 1.96 mm, Z in [-2.50, +3.30])
p_sw_h1 = p_shank.multVec(App.Vector(-2.40, 25.50, 0.0))
sw_pin1 = Part.makeCylinder(0.98, 5.80, App.Vector(p_sw_h1.x, p_sw_h1.y, -2.50), App.Vector(0, 0, 1))

# Microswitch Hole 2 (-2.40, 32.00): Coaxial M2 Cover Retaining Screw & Ruthex Insert in Cheek A (Z in [-5.00, -2.50])
p_m2 = p_shank.multVec(App.Vector(-2.40, 32.00, 0.0))
m2_ruthex_mono = Part.makeCylinder(1.65, 2.50, App.Vector(p_m2.x, p_m2.y, -5.00), App.Vector(0, 0, 1))
m2_through_mono = Part.makeCylinder(1.05, 6.00, App.Vector(p_m2.x, p_m2.y, -5.50), App.Vector(0, 0, 1))

tibia_mono_solid = tibia_cut.cut(cut_main).cut(tongue_pocket).fuse(sw_pin1).cut(m2_ruthex_mono).cut(m2_through_mono)
try:
    tibia_mono_solid = tibia_mono_solid.removeSplitter()
except Exception:
    pass

# Build Removable Cover: custom/v2/parts/tibia/tibia_cover.FCStd
# Add 0.04 mm clearance at Z=3.54 and X=X_SPLIT-0.04 to prevent coplanar contact
box_cover = Part.makeBox(150.0 + X_SPLIT - 0.04, 80.0, 3.5, App.Vector(-150.0, -40.0, 3.54))
cover = Part.Face(outer_wire).extrude(App.Vector(0, 0, 2.46)).translate(App.Vector(0, 0, 3.54)).common(box_cover)

tongue_cover = Part.Face(outer_wire).extrude(App.Vector(0, 0, 0.70)).translate(App.Vector(0, 0, 3.05))
tongue_clip = Part.makeBox(DX_TONGUE - 0.10, 80.0, 1.0, App.Vector(X_SPLIT - 0.04, -40.0, 2.95))
tongue_cover = tongue_cover.common(tongue_clip)
cover = cover.fuse(tongue_cover)

# M3 pivot pin through-hole and counterbore
m3_hole_cover = Part.makeCylinder(1.60, 10.0, App.Vector(-122.0, -14.0, 0.0), App.Vector(0, 0, 1))
m3_cbore_cover = Part.makeCylinder(3.10, 1.55, App.Vector(-122.0, -14.0, 4.50), App.Vector(0, 0, 1))
cover = cover.cut(m3_hole_cover).cut(m3_cbore_cover)

# 1x M2 retaining screw countersink at p_m2 (properly oriented cone: R=1.10 at Z=4.85 widening to R=2.25 at Z=6.00)
m2_hole_cover = Part.makeCylinder(1.10, 10.0, App.Vector(p_m2.x, p_m2.y, 0.0), App.Vector(0, 0, 1))
m2_csink_cover = Part.makeCone(1.10, 2.25, 1.15, App.Vector(p_m2.x, p_m2.y, 4.85), App.Vector(0, 0, 1))
cover = cover.cut(m2_hole_cover).cut(m2_csink_cover)

try:
    cover = cover.removeSplitter()
except Exception:
    pass

# Save Canonical Monolithic Body: custom/v2/parts/tibia/tibia.FCStd
fcstd_mono_path = f"{parts_tibia_dir}/tibia.FCStd"
try:
    App.closeDocument("tibia")
except Exception:
    pass
doc_mono = App.newDocument("tibia")
obj_mono = doc_mono.addObject("Part::Feature", "Tibia_Body")
obj_mono.Label = "Tibia v2 Monocoque Body with Integrated Fixed Cheek (PETG)"
obj_mono.Shape = tibia_mono_solid
if hasattr(obj_mono, "ViewObject") and obj_mono.ViewObject is not None:
    obj_mono.ViewObject.Visibility = True
    obj_mono.ViewObject.ShapeColor = COLOR_CFRP
doc_mono.recompute()
doc_mono.saveAs(fcstd_mono_path)
tibia_mono_solid.exportStep(f"{export_step_parts}/tibia.step")
tibia_mono_solid.exportStl(f"{export_stl_parts}/tibia.stl")
print(f"✔ Saved: {fcstd_mono_path} (Valid={tibia_mono_solid.isValid()}, Volume={tibia_mono_solid.Volume:.1f} mm3)")

# Save Canonical Removable Cover: custom/v2/parts/tibia/tibia_cover.FCStd
fcstd_cover_path = f"{parts_tibia_dir}/tibia_cover.FCStd"
try:
    App.closeDocument("tibia_cover")
except Exception:
    pass
doc_cover = App.newDocument("tibia_cover")
obj_cover = doc_cover.addObject("Part::Feature", "Tibia_Cover")
obj_cover.Label = "Tibia Foot Service Cover (Cheek B with Form-Fit Tongue, PETG)"
obj_cover.Shape = cover
if hasattr(obj_cover, "ViewObject") and obj_cover.ViewObject is not None:
    obj_cover.ViewObject.Visibility = True
    obj_cover.ViewObject.ShapeColor = COLOR_COVER
doc_cover.recompute()
doc_cover.saveAs(fcstd_cover_path)
cover.exportStep(f"{export_step_parts}/tibia_cover.step")
cover.exportStl(f"{export_stl_parts}/tibia_cover.stl")
print(f"✔ Saved: {fcstd_cover_path} (Valid={cover.isValid()}, Volume={cover.Volume:.1f} mm3)")

# =============================================================================
# 4. Build Canonical Subsystem Assembly: custom/v2/tibia_assembly.FCStd
# =============================================================================
print("4. Building Canonical Subsystem Assembly: custom/v2/tibia_assembly.FCStd...")
doc_asm_name = "tibia_assembly"
try:
    App.closeDocument(doc_asm_name)
except Exception:
    pass
fcstd_asm_path = f"{v2_dir}/tibia_assembly.FCStd"
doc_asm = App.newDocument(doc_asm_name)
doc_asm.saveAs(fcstd_asm_path)

doc_servo = App.openDocument(f"{cots_dir}/servo_nr645.FCStd")

asm_part = doc_asm.addObject("App::Part", "Tibia_Assembly")
asm_part.Label = "Lasius Tibia v2 Subsystem Assembly with Foot Contact Sensor"
for o in asm_part.Origin.OutList:
    if hasattr(o, "Visibility"):
        o.Visibility = False
asm_part.Origin.Visibility = False
asm_part.Visibility = True


def make_link(name, label, target_obj, placement, color=None):
    lnk = doc_asm.addObject("App::Link", name)
    lnk.setLink(target_obj)
    lnk.Label = label
    lnk.Placement = placement
    asm_part.addObject(lnk)
    lnk.Visibility = True
    if hasattr(lnk, "ViewObject") and lnk.ViewObject is not None:
        try:
            lnk.ViewObject.Visibility = True
            if color is not None:
                lnk.ViewObject.OverrideMaterial = True
                mat = lnk.ViewObject.ShapeMaterial
                mat.DiffuseColor = color
                lnk.ViewObject.ShapeMaterial = mat
        except Exception:
            pass
    return lnk


# 1. Monolithic Tibia Body
make_link("Tibia_Body", "1. Tibia v2 Monocoque (Warren Truss + Fixed Cheek A)", obj_mono, App.Placement(), COLOR_CFRP)

# 2. Knee Servo
p_servo = App.Placement(App.Vector(0.0, 0.0, 18.8), App.Rotation(App.Vector(0, 0, 1), 180.0))
make_link("Knee_Servo", "2. Knee Servo (Torcster NR-645 COTS)", doc_servo.Servo_Complete, p_servo, COLOR_SERVO)

# 3. Bionic Foot Rocker
make_link("Tibia_Rocker", "3. Bionic Tarsus Rocker Foot (+52% Lever)", obj_rocker, p_shank, COLOR_ORANGE)

# 4. Microswitch
p_sw_local = App.Placement(App.Vector(-6.9, 23.0, 0.0), App.Rotation())
make_link("Microswitch", "4. Subminiature Microswitch (COTS)", obj_sw, p_shank.multiply(p_sw_local), COLOR_SWITCH)

# 5. Compression Spring (at Y_s = 8.55 mm -> spans Y_s in [8.55, 20.55])
p_sp_local = App.Placement(App.Vector(-14.0, 8.55, 0.0), App.Rotation())
make_link("Compression_Spring", "5. Stainless Preload Spring (COTS)", obj_sp, p_shank.multiply(p_sp_local), COLOR_SPRING)

# 6. Removable Service Cover (Cheek B)
make_link("Tibia_Cover", "6. Removable Service Cover (Cheek B Form-Fit)", obj_cover, App.Placement(), COLOR_COVER)

# 7. M3 Hardened Pivot Pin & Ruthex (Ruthex height = 2.45 mm inside Cheek A Z in [-5.00, -2.55])
pin_obj = doc_asm.addObject("Part::Feature", "Pivot_Pin_Assembly")
pin_obj.Label = "7. M3 Hardened Pivot Pin & Ruthex"
pin_head = Part.makeCylinder(2.80, 1.45, App.Vector(-122.0, -14.0, 4.55), App.Vector(0, 0, 1))
pin_shaft = Part.makeCylinder(1.50, 9.55, App.Vector(-122.0, -14.0, -5.00), App.Vector(0, 0, 1))
ruthex = Part.makeCylinder(2.10, 2.45, App.Vector(-122.0, -14.0, -5.00), App.Vector(0, 0, 1))
pin_obj.Shape = pin_head.fuse(pin_shaft).fuse(ruthex)
asm_part.addObject(pin_obj)
if hasattr(pin_obj, "ViewObject") and pin_obj.ViewObject:
    try:
        pin_obj.ViewObject.ShapeColor = COLOR_BRASS
    except Exception:
        pass

# 8. M2 DIN 7991 Flush Countersunk Screw & Ruthex at p_m2 (coaxial with Microswitch Hole 2)
screw_m2 = doc_asm.addObject("Part::Feature", "Cover_Retaining_Screw_M2")
screw_m2.Label = "8. M2x10 Flush Countersunk Retaining Screw & Ruthex"
head_m2 = Part.makeCone(1.00, 2.10, 1.10, App.Vector(p_m2.x, p_m2.y, 4.90), App.Vector(0, 0, 1))
shank_m2 = Part.makeCylinder(0.98, 9.90, App.Vector(p_m2.x, p_m2.y, -5.00), App.Vector(0, 0, 1))
ruthex_m2 = Part.makeCylinder(1.60, 2.45, App.Vector(p_m2.x, p_m2.y, -5.00), App.Vector(0, 0, 1))
screw_m2.Shape = head_m2.fuse(shank_m2).fuse(ruthex_m2)
asm_part.addObject(screw_m2)
if hasattr(screw_m2, "ViewObject") and screw_m2.ViewObject:
    try:
        screw_m2.ViewObject.ShapeColor = COLOR_STEEL
    except Exception:
        pass

doc_asm.recompute()
doc_asm.save()
print(f"✔ Saved Canonical Assembly: {fcstd_asm_path}")

# Export STEP
step_asm_path = f"{export_step_v2}/tibia_assembly.step"
asm_part.Shape.exportStep(step_asm_path)
# Assembly STL omitted (assemblies use STEP for CAD; STL is reserved for 3D-printable parts)
print(f"✔ Exported STEP: {step_asm_path}")

# =============================================================================
# 5. Pairwise 3D B-Rep Collision Verification
# =============================================================================
print("5. Running Pairwise 3D B-Rep Collision Check on tibia_assembly.FCStd...")
items = []
for obj in asm_part.Group:
    if hasattr(obj, "Shape") and not obj.Shape.isNull():
        items.append((obj.Name, obj.Shape))

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
    print("  ✅ ZERO COLLISIONS across all 8 components in tibia_assembly.FCStd (0.0000 mm^3)!")

for d in list(App.listDocuments().values()):
    try:
        App.closeDocument(d.Name)
    except Exception:
        pass
sys.exit(0)
