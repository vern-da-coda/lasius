#!/usr/bin/env python3
"""
Generate Lasius v2 Separate 2-DoF Power-Gaster Assembly (Option G2)
(custom/v2/gaster_power_assembly.FCStd & custom/v2/parts/gaster/gaster_power_*.FCStd)
====================================================================================
Architecture (Separate Modular Power-Distribution Abdomen — Option G2):
  - Docks directly into the restored rear vertical dovetail socket of chassis_core_lower/upper.FCStd
    (X = -85.5 .. -92.5 mm) and clamps rigidly via the existing rear CFRP M3 spacer bores
    at (-90.0, 0.0) and (-120.0, 0.0) — both top and bottom Ruthex M3 inserts fit cleanly
    above/below the integrated Pan servo!
  - Single 14 AWG battery power feed routes from the torso 2S LiPo through dual flanking
    cable channels in the Tail Mount and the S-loop Petiolus gimbal into the Power-Gaster,
    where power is fused (25A Mini-ATM), switched (Pi Logic SPST + Dual-UBEC DPST), and
    regulated via dual Hobbywing BEC 10A V2-Car (6.0V) UBECs before two twisted 16 AWG
    6.0V rails return forward to PCA9685 Left (0x40) and Right (0x42).

Components:
  1. gaster_power_tail_mount.FCStd:
     - Rear standoff interface block (X in [-157.0, -92.5 mm]) + male dovetail runner
       (X in [-92.50, -85.68 mm], Z in [6.18, 53.10 mm]), M3 Ruthex pockets at (-90, 0) & (-120, 0).
     - Internal NR-645 Pan Servo bay (vertical Yaw spline at X = -146.0, Y = 0.0, Z = 45.80 mm)
       flanked by dual 5.5 x 10.0 mm power-harness side channels (Y = ±14.25 mm).
  2. gaster_power_gimbal.FCStd:
     - True 2-DoF Petiolus Gimbal coupling the vertical Pan disc horn at (-146.0, 0, Z = 54.3)
       & lower counter-pivot to the vertically oriented NR-645 Tilt Servo (Pitch axis along Y
       at X = -179.0, Z = 35.0 mm) with upper S-loop harness guide bridge.
  3. gaster_power_shell.FCStd & gaster_power_cover.FCStd:
     - Bionic 3D-printed PETG ant-abdomen monocoque (X in [-192.0, -300.0 mm], max width 96.0 mm,
       height Z in [12.0, 49.3 mm]) with 5x bottom + 5x top 45-deg Chevron chimney cooling louvers.
     - Houses 2x Hobbywing BEC 10A V2-Car (X = -238.0, Y = ±17.0, Z = 16.5..32.7 mm, 14 mm center
       chimney), 1x 25A Mini-ATM blade fuse (left flank, Z = 38.5), and 2x Mini Slide Switches
       (right flank, Z = 38.5 — fully clear horizontally AND vertically of both UBECs).
  4. gaster_power_assembly.FCStd:
     - Master G2 subassembly linking all 4 custom parts + 2x NR-645 Pan/Tilt Servos +
       2x Hobbywing 10A UBECs + 25A Mini-ATM Fuse + 2x Mini Slide Switches, verified to
       0.0000 mm^3 internal AND chassis-docking collisions.
"""

import math
import os
import sys
import FreeCAD as App
import Part

print("--- Generating Lasius 2-DoF Power-Gaster Assembly (Option G2) ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts/gaster"
asm_dir = f"{repo_root}/hardware/mechanics/models/custom/v2"
cots_dir = f"{repo_root}/hardware/mechanics/models/cots"
urdf_mesh_dir = f"{repo_root}/hardware/mechanics/export/urdf/meshes"

for d in [models_dir, asm_dir, urdf_mesh_dir]:
    os.makedirs(d, exist_ok=True)

z_base = 2.00
h_mount = 51.30
z_top_plate = z_base + h_mount  # Z = 53.30 mm

# Kinematic Pivot Coordinates (True 2-DoF Pan/Yaw -> Tilt/Pitch):
X_PAN = -146.00
Z_PAN_ORIGIN = 45.80   # Body Z in [7.0, 45.8], Horn Z in [50.3, 54.3] (clear of Body_Top X=-132 & Canopy Z=55.22)
X_TILT = -181.00       # Clears Pan wire stub (XMin=-168.0) with 0.5 mm gimbal cradle gap
Y_TILT_ORIGIN = 15.00  # Body Y in [-23.8, +15.0], Horn Y in [+19.5, +23.5]
Z_TILT = 35.00         # Body Z in [3.5, 44.0], Tilt axis along world Y at (X=-181, Z=35)

# Exact 90-deg proper right-handed rotation for Tilt Servo:
#   r1 = Rot_Z(+90): (+X -> +Y, +Y -> -X, +Z -> +Z)
#   r2 = Rot_X(-90): (+X -> +X, +Y -> -Z, +Z -> +Y)
#   Combined r2 * r1:
#     local +X (long axis) -> world -Z
#     local +Y (20mm wide) -> world -X
#     local +Z (spline)    -> world +Y
ROT_PAN = App.Rotation()
ROT_TILT = App.Rotation(App.Vector(1, 0, 0), -90.0).multiply(App.Rotation(App.Vector(0, 0, 1), 90.0))
PL_PAN = App.Placement(App.Vector(X_PAN, 0.0, Z_PAN_ORIGIN), ROT_PAN)
PL_TILT = App.Placement(App.Vector(X_TILT, Y_TILT_ORIGIN, Z_TILT), ROT_TILT)


def make_dovetail_prism(x_throat, x_base, w_throat, w_base, z_min, z_max):
    pts = [
        (x_throat,  w_throat / 2.0),
        (x_base,    w_base / 2.0),
        (x_base,   -w_base / 2.0),
        (x_throat, -w_throat / 2.0),
    ]
    v = [App.Vector(px, py, z_min) for px, py in pts]
    edges = [Part.makeLine(v[i], v[(i + 1) % len(v)]) for i in range(len(v))]
    return Part.Face(Part.Wire(edges)).extrude(App.Vector(0.0, 0.0, z_max - z_min))


def make_chevron_slot(cx, cy, arm_len, width, angle_deg=45.0, z_min=8.0, z_max=18.0):
    rad = math.radians(angle_deg)
    dx = arm_len * math.cos(rad)
    dy = arm_len * math.sin(rad)
    r = width / 2.0

    def make_pill(x0, y0, x1, y1):
        vx, vy = x1 - x0, y1 - y0
        L = math.hypot(vx, vy)
        ux, uy = vx / L, vy / L
        nx, ny = -uy * r, ux * r
        p1 = App.Vector(x0 + nx, y0 + ny, z_min)
        p2 = App.Vector(x1 + nx, y1 + ny, z_min)
        p3 = App.Vector(x1 - nx, y1 - ny, z_min)
        p4 = App.Vector(x0 - nx, y0 - ny, z_min)
        m1 = App.Vector(x1 + ux * r, y1 + uy * r, z_min)
        m2 = App.Vector(x0 - ux * r, y0 - uy * r, z_min)
        edges = [
            Part.makeLine(p1, p2),
            Part.Edge(Part.ArcOfCircle(p2, m1, p3)),
            Part.makeLine(p3, p4),
            Part.Edge(Part.ArcOfCircle(p4, m2, p1)),
        ]
        return Part.Face(Part.Wire(edges)).extrude(App.Vector(0.0, 0.0, z_max - z_min))

    return make_pill(cx, cy, cx + dx, cy + dy).fuse(make_pill(cx, cy, cx + dx, cy - dy))


def place_shape(shape, vec, rot):
    s = shape.copy()
    s.Placement = App.Placement(vec, rot)
    return s


# =============================================================================
# 1. Build Part: gaster_power_tail_mount.FCStd
# =============================================================================
print("1. Building gaster_power_tail_mount.FCStd...")
doc_m_name = "gaster_power_tail_mount"
try:
    App.closeDocument(doc_m_name)
except Exception:
    pass
doc_m = App.newDocument(doc_m_name)
fcstd_m_path = f"{models_dir}/gaster_power_tail_mount.FCStd"

# Front interface block clamped between Body_Bottom (Z=2.0) and Body_Top (Z=53.3):
# X in [-132.0, -92.5 mm], Y in [-19.5, +19.5 mm] (16 mm clear of Rear Legs!), Z in [2.02, 53.28 mm]
front_block = Part.makeBox(39.50, 39.00, h_mount - 0.04, App.Vector(-132.00, -19.50, z_base + 0.02))
# Rear Pan-Servo housing extension behind carbon plates (X in [-165.0, -132.0 mm], Z in [6.50, 49.50 mm])
# Leaves bottom clearance below Z=6.50 and top clearance above Z=49.50 for Pan Gimbal upper/lower yokes!
servo_housing = Part.makeBox(33.00, 31.00, 43.00, App.Vector(-165.00, -15.50, 6.50))
# Male dovetail runner mating into Chassis_Core rear socket (0.18 mm nominal clearance)
male_runner = make_dovetail_prism(-92.50, -85.68, 13.64, 21.64, 6.18, 53.10)
# Lower Pan Counter-Pivot Tongue (Z in [2.02, 6.50], X in [-153.0, -131.5], Y in [-11.0, +11.0])
# Wait: gimbal lower arm swings below Z=6.50 -> put fixed lower pivot stub at Z in [2.02, 4.20] so gimbal arm runs at Z in [4.50, 6.80]?
# Even cleaner: gimbal lower arm runs at Z in [2.02, 4.50] underneath housing (Z_min=6.50), engaging a bottom M3 pivot boss at Z=4.80..6.50!
lower_pivot_boss = Part.makeCylinder(6.00, 1.80, App.Vector(X_PAN, 0.0, 4.80), App.Vector(0, 0, 1))
mount_solid = front_block.fuse(servo_housing).fuse(male_runner).fuse(lower_pivot_boss)

# Rear CFRP M3 Standoff Bores + Top/Bottom Ruthex M3 Pockets at (-90.0, 0) & (-120.0, 0)
# Note: at (-120, 0), Pan servo occupies Z in [7.0, 45.8], leaving 5.0 mm bottom (M3S Ruthex) and 7.5 mm top (M3 Ruthex)!
for rx, bot_depth, top_depth in [(-90.0, 7.5, 7.5), (-120.0, 4.5, 6.5)]:
    top_p = Part.makeCylinder(2.10, top_depth, App.Vector(rx, 0.0, z_top_plate - top_depth + 0.5), App.Vector(0, 0, 1))
    bot_p = Part.makeCylinder(2.10, bot_depth, App.Vector(rx, 0.0, z_base - 0.5), App.Vector(0, 0, 1))
    mount_solid = mount_solid.cut(top_p).cut(bot_p)
# Through-bore at (-90, 0)
mount_solid = mount_solid.cut(Part.makeCylinder(1.70, h_mount + 10.0, App.Vector(-90.0, 0.0, z_base - 5.0), App.Vector(0, 0, 1)))

# Exact NR-645 Pan Servo Cavity (Servo_Body local X in [-9.0, +31.5], Y in [-10.0, +10.0], Z in [-38.8, +6.0];
# mounting ears X in [-16.5, +39.0] at Z_local in [-11.5, -8.0]; wire exit X in [-22.0, -9.0] at Z_local in [-39.0, -34.0]):
# World origin at (X_PAN=-146.0, 0.0, Z_PAN_ORIGIN=45.80), 0.30 mm clearance all around
pan_body_cut = Part.makeBox(41.10, 20.60, 45.50, App.Vector(X_PAN - 9.30, -10.30, Z_PAN_ORIGIN - 39.10))
pan_ears_cut = Part.makeBox(56.20, 20.60, 4.50, App.Vector(X_PAN - 16.80, -10.30, Z_PAN_ORIGIN - 11.80))
pan_wire_cut = Part.makeBox(15.00, 12.00, 8.00, App.Vector(X_PAN - 23.00, -6.00, Z_PAN_ORIGIN - 39.30))
# Open top slot for spline & disc horn clearance (Z >= 45.80)
pan_top_open = Part.makeBox(36.00, 28.00, 12.00, App.Vector(X_PAN - 20.00, -14.00, 45.80))
# Lower M3 counter-pivot bore at (X_PAN, 0, Z=4.8..6.8)
pan_bot_bore = Part.makeCylinder(1.60, 6.00, App.Vector(X_PAN, 0.0, 3.00), App.Vector(0, 0, 1))
mount_solid = (
    mount_solid
    .cut(pan_body_cut)
    .cut(pan_ears_cut)
    .cut(pan_wire_cut)
    .cut(pan_top_open)
    .cut(pan_bot_bore)
)

# Dual Flanking Power-Harness Conduits (14AWG battery feed +Y side, 2x 16AWG 6.0V returns -Y side)
# Entry tunnel matching Chassis_Core rear 16x10 mm port (Z in [27.0, 37.0]) branching cleanly around Pan Servo!
conduit_entry = Part.makeBox(14.00, 15.00, 10.00, App.Vector(-98.00, -7.50, 27.00))
conduit_split = Part.makeBox(8.00, 32.00, 10.00, App.Vector(-104.00, -16.00, 27.00))
conduit_l = Part.makeBox(68.00, 4.60, 10.00, App.Vector(-166.00, +11.40, 27.00))
conduit_r = Part.makeBox(68.00, 4.60, 10.00, App.Vector(-166.00, -16.00, 27.00))
mount_solid = mount_solid.cut(conduit_entry).cut(conduit_split).cut(conduit_l).cut(conduit_r).removeSplitter()

obj_tm = doc_m.addObject("Part::Feature", "Gaster_Power_Tail_Mount")
obj_tm.Label = "Power-Gaster Rear Dovetail & Pan-Servo Mount (G2)"
obj_tm.Shape = mount_solid
if hasattr(obj_tm, "ViewObject") and obj_tm.ViewObject:
    obj_tm.ViewObject.ShapeColor = (0.22, 0.24, 0.27)
doc_m.recompute()
doc_m.saveAs(fcstd_m_path)
App.closeDocument(doc_m_name)
print(f"✔ Saved: {fcstd_m_path} (Valid={mount_solid.isValid()}, Vol={mount_solid.Volume:.1f} mm^3)")

# =============================================================================
# 2. Build Part: gaster_power_gimbal.FCStd (True 2-DoF Pan->Tilt Petiolus Frame)
# =============================================================================
print("2. Building gaster_power_gimbal.FCStd...")
doc_tb_name = "gaster_power_gimbal"
try:
    App.closeDocument(doc_tb_name)
except Exception:
    pass
doc_tb = App.newDocument(doc_tb_name)
fcstd_tb_path = f"{models_dir}/gaster_power_gimbal.FCStd"

# Top Pan Horn Bridge (Z in [54.60, 57.60 mm] — sits 0.30 mm above Pan Disc Horn Z_max=54.30,
# spans X in [-192.0, -135.0 mm] with rounded front disc around X_PAN=-146.0; clears Body_Top X=-132.0 by 3.0 mm!)
top_disc = Part.makeCylinder(13.00, 3.00, App.Vector(X_PAN, 0.0, 54.60), App.Vector(0, 0, 1))
top_arm = Part.makeBox(46.00, 24.00, 3.00, App.Vector(-192.00, -12.00, 54.60))
# Bottom Pan Counter-Pivot Bridge (Z in [1.70, 4.50 mm] — sits 0.30 mm below lower_pivot_boss Z=4.80,
# spans X in [-192.0, -139.0 mm] behind Body_Bottom X=-132.0 by 7.0 mm!)
bot_disc = Part.makeCylinder(10.00, 2.80, App.Vector(X_PAN, 0.0, 1.70), App.Vector(0, 0, 1))
bot_arm = Part.makeBox(46.00, 20.00, 2.80, App.Vector(-192.00, -10.00, 1.70))

# Vertical Tilt Servo Cradle (X in [-193.5, -168.5 mm], Y in [-25.5, +17.5 mm], Z in [-5.5, +57.6 mm])
# Holds Servo_Gaster_Tilt vertically at (X=-181, Y=+15, Z=35) with Horn exiting at +Y (Y in [+19.5, +23.5])
# and lower/upper mounting flanges resting cleanly on inner Y=+4.0..+6.5 wall!
cradle_outer = Part.makeBox(25.00, 43.00, 63.10, App.Vector(-193.50, -25.50, -5.50))
# Exact cavity for Servo_Gaster_Tilt (0.30 mm nominal clearance all around)
tilt_body_cut = Part.makeBox(20.60, 46.00, 41.20, App.Vector(X_TILT - 10.30, -24.10, Z_TILT - 31.80))
tilt_ears_cut = Part.makeBox(20.60, 4.60, 56.20, App.Vector(X_TILT - 10.30, +3.20, Z_TILT - 39.30))
tilt_wire_cut = Part.makeBox(16.00, 12.00, 20.00, App.Vector(X_TILT - 8.00, -25.00, Z_TILT + 8.50))
# Side lightening & S-loop cable routing pass-through above Tilt Servo (Z in [45.0, 54.0], Y in [-16, +12])
gimbal_cable_win = Part.makeBox(30.00, 26.00, 9.00, App.Vector(-196.00, -14.00, 45.00))

gimbal_solid = top_disc.fuse(top_arm).fuse(bot_disc).fuse(bot_arm).fuse(cradle_outer)
gimbal_solid = gimbal_solid.cut(tilt_body_cut).cut(tilt_ears_cut).cut(tilt_wire_cut).cut(gimbal_cable_win)

# Pan center bore + 4x BCD16 horn mounting holes (Ø2.2 mm) at X_PAN, lower M3 pivot bore, Tilt right counter-pivot bore
p_center = Part.makeCylinder(1.60, 62.00, App.Vector(X_PAN, 0.0, 0.0), App.Vector(0, 0, 1))
gimbal_solid = gimbal_solid.cut(p_center)
for ang_deg in [45.0, 135.0, 225.0, 315.0]:
    hx = X_PAN + 8.0 * math.cos(math.radians(ang_deg))
    hy = 8.0 * math.sin(math.radians(ang_deg))
    gimbal_solid = gimbal_solid.cut(Part.makeCylinder(1.10, 6.0, App.Vector(hx, hy, 53.0), App.Vector(0, 0, 1)))
# Tilt counter-pivot bore along Y at (X_TILT, Y=-26..-22, Z_TILT)
t_counter = Part.makeCylinder(1.60, 12.00, App.Vector(X_TILT, -28.0, Z_TILT), App.Vector(0, 1, 0))
gimbal_solid = gimbal_solid.cut(t_counter).removeSplitter()

obj_tb = doc_tb.addObject("Part::Feature", "Gaster_Power_Gimbal")
obj_tb.Label = "Power-Gaster 2-DoF Petiolus Gimbal Frame (G2)"
obj_tb.Shape = gimbal_solid
if hasattr(obj_tb, "ViewObject") and obj_tb.ViewObject:
    obj_tb.ViewObject.ShapeColor = (0.32, 0.34, 0.38)
doc_tb.recompute()
doc_tb.saveAs(fcstd_tb_path)
App.closeDocument(doc_tb_name)
print(f"✔ Saved: {fcstd_tb_path} (Valid={gimbal_solid.isValid()}, Vol={gimbal_solid.Volume:.1f} mm^3)")

# =============================================================================
# 3. Build Parts: gaster_power_shell.FCStd & gaster_power_cover.FCStd
# =============================================================================
print("3. Building gaster_power_shell.FCStd & gaster_power_cover.FCStd...")

# Bionic Ant-Abdomen Teardrop Profile (X in [-196.0, -304.0 mm], max width 96.0 mm at X = -240 mm)
pts_g_half = [
    App.Vector(-196.0, 24.0, 0.0),
    App.Vector(-210.0, 39.0, 0.0),
    App.Vector(-240.0, 48.0, 0.0),
    App.Vector(-270.0, 40.0, 0.0),
    App.Vector(-290.0, 22.0, 0.0),
    App.Vector(-304.0,  0.0, 0.0),
]
sp_up = Part.BSplineCurve()
sp_up.interpolate(pts_g_half)
pts_g_low = [App.Vector(p.x, -p.y, 0.0) for p in reversed(pts_g_half[1:-1])]
sp_lo = Part.BSplineCurve()
sp_lo.interpolate([pts_g_half[-1]] + pts_g_low + [App.Vector(-196.0, -24.0, 0.0)])
front_cap = Part.makeLine(pts_g_half[0], App.Vector(-196.0, -24.0, 0.0))
wire_g = Part.Wire(Part.__sortEdges__([sp_up.toShape(), sp_lo.toShape(), front_cap]))
face_g_outer = Part.Face(wire_g)

t_shell = 2.40
face_g_inner = face_g_outer.makeOffset2D(-t_shell).Faces[0]

z_shell_bot = 12.00
z_shell_top = 46.50
z_cover_top = 49.30

# Outer monocoque tub (Z = 12.00 .. 46.50 mm) with hollow cavity (Z = 14.40 .. 47.50 mm)
shell_outer = face_g_outer.extrude(App.Vector(0.0, 0.0, z_shell_top - z_shell_bot))
shell_outer.translate(App.Vector(0.0, 0.0, z_shell_bot))
shell_cav = face_g_inner.extrude(App.Vector(0.0, 0.0, z_shell_top - z_shell_bot + 2.0))
shell_cav.translate(App.Vector(0.0, 0.0, z_shell_bot + t_shell))
shell_solid = shell_outer.cut(shell_cav)

# Front Dual Clevis Arms straddling Gaster_Power_Gimbal & engaging Tilt Servo Disc Horn (Y=+23.5) and Counter-Pivot (Y=-25.5):
arm_l = Part.makeBox(24.00, 3.50, 22.00, App.Vector(-198.00, 23.80, Z_TILT - 11.00))
ear_l = Part.makeCylinder(12.50, 3.50, App.Vector(X_TILT, 23.80, Z_TILT), App.Vector(0, 1, 0))
gus_l = Part.makeBox(6.00, 7.30, 22.00, App.Vector(-200.00, 20.00, Z_TILT - 11.00))

arm_r = Part.makeBox(24.00, 3.50, 18.00, App.Vector(-198.00, -29.30, Z_TILT - 9.00))
ear_r = Part.makeCylinder(9.00, 3.50, App.Vector(X_TILT, -29.30, Z_TILT), App.Vector(0, 1, 0))
gus_r = Part.makeBox(6.00, 9.30, 18.00, App.Vector(-200.00, -29.30, Z_TILT - 9.00))

shell_solid = shell_solid.fuse(arm_l).fuse(ear_l).fuse(gus_l).fuse(arm_r).fuse(ear_r).fuse(gus_r)
# Re-clear interior cavity where gussets entered shell wall
shell_solid = shell_solid.cut(shell_cav)

# Tilt pivot center bore + 4x BCD16 disc-horn bores on Left Arm (+Y)
t_bore = Part.makeCylinder(1.60, 70.00, App.Vector(X_TILT, -35.0, Z_TILT), App.Vector(0, 1, 0))
shell_solid = shell_solid.cut(t_bore)
for ang_deg in [45.0, 135.0, 225.0, 315.0]:
    hx = X_TILT + 8.0 * math.cos(math.radians(ang_deg))
    hz = Z_TILT + 8.0 * math.sin(math.radians(ang_deg))
    shell_solid = shell_solid.cut(Part.makeCylinder(1.10, 10.0, App.Vector(hx, 22.0, hz), App.Vector(0, 1, 0)))

# Front Power-Harness Entry Port (X = -200..-193, Y in [-12, +12], Z in [34.0, 44.0])
port_entry = Part.makeBox(10.00, 24.00, 10.00, App.Vector(-201.00, -12.00, 34.00))
shell_solid = shell_solid.cut(port_entry)

# 2x Cooling Standoff Rails supporting both Hobbywing 10A UBECs at Z = 16.50 mm (2.1 mm floor air plenum)
# UBECs centered at X = -240.0, Y = ±17.0 mm (body X in [-262.5, -217.5], Y in [±7.0, ±27.0], Z in [16.5, 32.7])
for rx_rail in [-256.0, -224.0]:
    r_l = Part.makeBox(2.50, 20.50, 2.08, App.Vector(rx_rail - 1.25, +6.75, z_shell_bot + t_shell))
    r_r = Part.makeBox(2.50, 20.50, 2.08, App.Vector(rx_rail - 1.25, -27.25, z_shell_bot + t_shell))
    shell_solid = shell_solid.fuse(r_l).fuse(r_r)

# Center thermal chimney guide ribs keeping both UBECs captively aligned with 14.0 mm center air channel
for side_y in [+6.40, +27.60, -6.40, -27.60]:
    guide = Part.makeBox(36.00, 1.00, 9.00, App.Vector(-258.00, side_y - 0.50, z_shell_bot + t_shell))
    shell_solid = shell_solid.fuse(guide)

# 5x Bottom 45-deg Chevron Intake Louvers directly under both UBECs (X = -262 .. -218)
for cx_l in [-262.0, -251.0, -240.0, -229.0, -218.0]:
    lv = make_chevron_slot(cx_l, 0.0, 18.0, 2.60, 45.0, z_shell_bot - 2.0, z_shell_bot + t_shell + 1.0)
    shell_solid = shell_solid.cut(lv)

# 4x Internal M2 Ruthex Cover Fastening Bosses around perimeter
cover_bosses = [(-214.0, 32.0), (-214.0, -32.0), (-274.0, 28.0), (-274.0, -28.0)]
for bx, by in cover_bosses:
    b_cyl = Part.makeCylinder(3.20, z_shell_top - (z_shell_bot + t_shell), App.Vector(bx, by, z_shell_bot + t_shell), App.Vector(0, 0, 1))
    b_hole = Part.makeCylinder(1.60, 6.00, App.Vector(bx, by, z_shell_top - 5.5), App.Vector(0, 0, 1))  # Ø3.2 mm Ruthex M2
    shell_solid = shell_solid.fuse(b_cyl).cut(b_hole)

# Flank Control Panel Mounts at Z = 38.50 mm (5.8 mm ABOVE UBEC top Z=32.7 AND >1.9 mm clear horizontally!):
# Right flank (Y = -47.3): Switch_Logic_Pi (X = -227, Z = 38.5) & Switch_Servos_Armed (X = -253, Z = 38.5)
# Left flank  (Y = +47.9): Fuse_Mini_ATM_25A (X = -240, Z = 38.5)
rot_g_right = App.Rotation(App.Vector(0, 0, 1), +90.0)   # local -X -> (0, -1, 0) outward -Y
rot_g_left  = App.Rotation(App.Vector(0, 0, 1), -90.0)   # local -X -> (0, +1, 0) outward +Y

p_g_sw1  = App.Vector(-227.0, -47.30, 38.50)
p_g_sw2  = App.Vector(-253.0, -47.30, 38.50)
p_g_fuse = App.Vector(-240.0, +47.90, 38.50)

for p_sw in [p_g_sw1, p_g_sw2]:
    seat = place_shape(Part.makeBox(4.0, 19.6, 7.1, App.Vector(-3.4, -9.8, -3.55)), p_sw, rot_g_right)
    cut  = place_shape(Part.makeBox(12.0, 12.1, 6.3, App.Vector(-4.0, -6.05, -3.15)), p_sw, rot_g_right)
    m2a  = place_shape(Part.makeCylinder(0.85, 8.0, App.Vector(-2.0, -7.5, 0.0), App.Vector(1, 0, 0)), p_sw, rot_g_right)
    m2b  = place_shape(Part.makeCylinder(0.85, 8.0, App.Vector(-2.0, +7.5, 0.0), App.Vector(1, 0, 0)), p_sw, rot_g_right)
    shell_solid = shell_solid.cut(seat).cut(cut).cut(m2a).cut(m2b)

f_seat = place_shape(Part.makeBox(4.0, 15.6, 8.6, App.Vector(-3.4, -7.8, -4.3)), p_g_fuse, rot_g_left)
f_cut  = place_shape(Part.makeBox(14.0, 13.0, 6.9, App.Vector(-4.0, -6.5, -3.45)), p_g_fuse, rot_g_left)
shell_solid = shell_solid.cut(f_seat).cut(f_cut).removeSplitter()

doc_s_name = "gaster_power_shell"
try:
    App.closeDocument(doc_s_name)
except Exception:
    pass
doc_s = App.newDocument(doc_s_name)
fcstd_s_path = f"{models_dir}/gaster_power_shell.FCStd"
obj_s = doc_s.addObject("Part::Feature", "Gaster_Power_Shell")
obj_s.Label = "Power-Gaster Bionic Monocoque Shell (G2, PETG)"
obj_s.Shape = shell_solid
if hasattr(obj_s, "ViewObject") and obj_s.ViewObject:
    obj_s.ViewObject.ShapeColor = (0.20, 0.22, 0.25)
doc_s.recompute()
doc_s.saveAs(fcstd_s_path)
shell_solid.exportStl(f"{urdf_mesh_dir}/gaster_power_shell.stl")
App.closeDocument(doc_s_name)
print(f"✔ Saved: {fcstd_s_path} (Valid={shell_solid.isValid()}, Vol={shell_solid.Volume:.1f} mm^3)")

# Removable Louvered Top Cover (gaster_power_cover.FCStd, Z = 46.52 .. 49.30 mm)
cover_plate = face_g_outer.extrude(App.Vector(0.0, 0.0, z_cover_top - (z_shell_top + 0.02)))
cover_plate.translate(App.Vector(0.0, 0.0, z_shell_top + 0.02))
for cx_l in [-262.0, -251.0, -240.0, -229.0, -218.0]:
    lv = make_chevron_slot(cx_l, 0.0, 18.0, 2.60, 45.0, z_shell_top - 1.0, z_cover_top + 2.0)
    cover_plate = cover_plate.cut(lv)
for bx, by in cover_bosses:
    m2_thru = Part.makeCylinder(1.15, 8.0, App.Vector(bx, by, z_shell_top - 1.0), App.Vector(0, 0, 1))
    m2_csk = Part.makeCone(1.15, 2.15, 1.10, App.Vector(bx, by, z_cover_top - 1.10), App.Vector(0, 0, 1))
    cover_plate = cover_plate.cut(m2_thru).cut(m2_csk)
cover_plate = cover_plate.removeSplitter()

doc_c_name = "gaster_power_cover"
try:
    App.closeDocument(doc_c_name)
except Exception:
    pass
doc_c = App.newDocument(doc_c_name)
fcstd_c_path = f"{models_dir}/gaster_power_cover.FCStd"
obj_c = doc_c.addObject("Part::Feature", "Gaster_Power_Cover")
obj_c.Label = "Power-Gaster Louvered Service Cover (G2, PETG)"
obj_c.Shape = cover_plate
if hasattr(obj_c, "ViewObject") and obj_c.ViewObject:
    obj_c.ViewObject.ShapeColor = (0.28, 0.30, 0.34)
doc_c.recompute()
doc_c.saveAs(fcstd_c_path)
cover_plate.exportStl(f"{urdf_mesh_dir}/gaster_power_cover.stl")
App.closeDocument(doc_c_name)
print(f"✔ Saved: {fcstd_c_path} (Valid={cover_plate.isValid()}, Vol={cover_plate.Volume:.1f} mm^3)")

# =============================================================================
# 4. Build Master Subassembly: gaster_power_assembly.FCStd
# =============================================================================
print("4. Building gaster_power_assembly.FCStd...")
doc_ga_name = "gaster_power_assembly"
try:
    App.closeDocument(doc_ga_name)
except Exception:
    pass
doc_ga = App.newDocument(doc_ga_name)
fcstd_ga_path = f"{asm_dir}/gaster_power_assembly.FCStd"
doc_ga.saveAs(fcstd_ga_path)

d_tm = App.openDocument(fcstd_m_path)
d_tb = App.openDocument(fcstd_tb_path)
d_sh = App.openDocument(fcstd_s_path)
d_cv = App.openDocument(fcstd_c_path)
d_servo = App.openDocument(f"{cots_dir}/servo_nr645.FCStd")
d_ubec = App.openDocument(f"{cots_dir}/ubec_hobbywing_10a.FCStd")
d_fuse = App.openDocument(f"{cots_dir}/fuse_mini_atm.FCStd")
d_sw = App.openDocument(f"{cots_dir}/switch_mini_slide.FCStd")

gaster_part = doc_ga.addObject("App::Part", "Gaster_Power_Assembly")
gaster_part.Label = "Lasius 2-DoF Power-Gaster Assembly (Option G2 — Dual 10A UBEC + Fuse + Switches)"
for o in gaster_part.Origin.OutList:
    if hasattr(o, "Visibility"):
        o.Visibility = False
gaster_part.Origin.Visibility = False
gaster_part.Visibility = True


def add_lnk(name, label, target_obj, placement, color=None):
    lnk = doc_ga.addObject("App::Link", name)
    lnk.setLink(target_obj)
    lnk.Label = label
    lnk.Placement = placement
    gaster_part.addObject(lnk)
    lnk.Visibility = True
    if hasattr(lnk, "ViewObject") and lnk.ViewObject is not None:
        lnk.ViewObject.Visibility = True
        if color:
            lnk.ViewObject.OverrideMaterial = True
            mat = lnk.ViewObject.ShapeMaterial
            mat.DiffuseColor = color
            lnk.ViewObject.ShapeMaterial = mat
    return lnk


add_lnk("Gaster_Power_Tail_Mount", "1. Rear Dovetail & Pan-Servo Mount (G2)", d_tm.Gaster_Power_Tail_Mount, App.Placement(), (0.22, 0.24, 0.27))
add_lnk("Servo_Gaster_Pan", "2. Petiolus Pan/Yaw Servo (NR-645, COTS)", d_servo.Servo_Complete, PL_PAN, None)
add_lnk("Gaster_Power_Gimbal", "3. 2-DoF Petiolus Gimbal Frame (G2)", d_tb.Gaster_Power_Gimbal, App.Placement(), (0.32, 0.34, 0.38))
add_lnk("Servo_Gaster_Tilt", "4. Petiolus Tilt/Pitch Servo (NR-645, COTS)", d_servo.Servo_Complete, PL_TILT, None)
add_lnk("Gaster_Power_Shell", "5. Bionic Power-Gaster Monocoque Shell (G2)", d_sh.Gaster_Power_Shell, App.Placement(), (0.20, 0.22, 0.25))
add_lnk("Gaster_Power_Cover", "6. Louvered Service Cover (G2)", d_cv.Gaster_Power_Cover, App.Placement(), (0.28, 0.30, 0.34))

# 2x Hobbywing BEC 10A V2-Car UBECs (local +X output ferrite facing forward toward Petiolus!)
add_lnk("UBEC_Hobbywing_Left", "7a. Hobbywing BEC 10A V2-Car Left 6.0V (COTS)", d_ubec.UBEC_Hobbywing_10A, App.Placement(App.Vector(-240.0, +17.0, 16.50), App.Rotation()), (0.10, 0.11, 0.14))
add_lnk("UBEC_Hobbywing_Right", "7b. Hobbywing BEC 10A V2-Car Right 6.0V (COTS)", d_ubec.UBEC_Hobbywing_10A, App.Placement(App.Vector(-240.0, -17.0, 16.50), App.Rotation()), (0.10, 0.11, 0.14))

# 2x Mini Slide Switches on Right Gaster Flank + 25A Mini-ATM Fuse on Left Gaster Flank (Z = 38.50 mm)
def inset_pl(p, rot, d=0.62):
    return App.Placement(p + rot.multVec(App.Vector(1.0, 0.0, 0.0)) * d, rot)

add_lnk("Switch_Logic_Pi", "8a. Mini Slide Switch: Pi Logic (Gaster Right Flank)", d_sw.Switch_Mini_Slide, inset_pl(p_g_sw1, rot_g_right, 0.62), (0.18, 0.18, 0.22))
add_lnk("Switch_Servos_Armed", "8b. Mini Slide Switch DPST: Servos Armed (Gaster Right Flank)", d_sw.Switch_Mini_Slide, inset_pl(p_g_sw2, rot_g_right, 0.62), (0.18, 0.18, 0.22))
add_lnk("Fuse_Mini_ATM_25A", "8c. 25A Mini-ATM Blade Fuse (Gaster Left Flank)", d_fuse.Fuse_Mini_ATM, inset_pl(p_g_fuse, rot_g_left, 0.62), (0.90, 0.90, 0.92))

doc_ga.recompute()
doc_ga.save()
print(f"✔ Saved Power-Gaster Assembly -> {fcstd_ga_path}")

# Pairwise B-Rep collision verification inside gaster_power_assembly.FCStd
items = [(o.Name, o.Shape) for o in gaster_part.Group if hasattr(o, "Shape") and not o.Shape.isNull()]
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
    print("  ✅ ZERO COLLISIONS in gaster_power_assembly.FCStd (0.0000 mm^3)!")

# Cross-Assembly Docking Verification against chassis_assembly.FCStd (Body_Bottom, Body_Top, Chassis_Core, Canopy, RPi_Mount)
d_ca = App.openDocument(f"{asm_dir}/chassis_assembly.FCStd")
dock_max = 0.0
ca_objs = [(o.Name, o.Shape) for o in d_ca.Chassis_Assembly.Group if hasattr(o, "Shape") and not o.Shape.isNull()]
for n1, s1 in items:
    for n2, s2 in ca_objs:
        if s1.BoundBox.intersect(s2.BoundBox):
            v = s1.common(s2).Volume
            if v > 1e-4:
                print(f"  ❌ DOCKING COLLISION {n1} <-> Chassis.{n2}: {v:.4f} mm^3")
                dock_max = max(dock_max, v)
if dock_max <= 1e-4:
    print("  ✅ ZERO DOCKING COLLISIONS between gaster_power_assembly & chassis_assembly (0.0000 mm^3)!")

os._exit(0)
