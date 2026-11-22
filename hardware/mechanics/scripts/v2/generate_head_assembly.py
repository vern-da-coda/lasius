#!/usr/bin/env python3
"""
Generate Authentic 5-DoF Lynxmotion A-Pod Style Head & Mandibles Assembly for Lasius v2
(custom/v2/head_assembly.FCStd & custom/v2/parts/apod_head_*.FCStd)
================================================================================
Original Zenta A-Pod Architecture adapted to Lasius Spacer Bores:
  1. apod_head_mount.FCStd (Chassis Standoff Interface Block):
     - Spans the 51.30 mm vertical gap between Body_Bottom (Z = 2.00 mm) and
       Body_Top (Z = 53.30 mm) at the front of Lasius.
     - Rigidly clamped by the 2 front M3 spacer bores at X = 128.0 mm, Y = ±12.0 mm
       (inter-bore distance 24.0 mm) with top & bottom Ruthex M3 pockets.
     - Houses the vertical Pan Servo (Joint 1: Head Pan / Yaw).
  2. apod_neck_bracket.FCStd (SES Style 3-DoF Neck Gimbal):
     - Heavy-duty SES-style aluminum gimbal connecting Pan output, Tilt Servo
       (Joint 2: Head Tilt / Pitch, horizontal Y-axis at X = 175.0 mm), and
       Roll Servo (Joint 3: Head Roll / Rotation, longitudinal X-axis at X = 208.0 mm).
  3. apod_head_platform.FCStd (Insect Head Chassis Platform):
     - Attaches to the Roll servo horn at X = 215.0 mm.
     - Houses TWO standard servos (Joint 4: Left Mandible, Joint 5: Right Mandible)
       mounted side-by-side at Y = ±26.0 mm (inter-axis distance 52.0 mm).
     - Compound eye sensor ports and top faceted carapace.
  4. apod_mandible_left.FCStd & apod_mandible_right.FCStd (Authentic 3D-Sandwich Ant Mandibles):
     - Massive ant pincer jaws extending from pivot at X = 258.0 mm forward to
       sharp interlocking tips at X = 378.0 mm (120 mm reach!).
     - Lateral spread sweeping outward to Y = ±68.0 mm.
     - 3D-Sandwich structure: Top & Bottom 2.5 mm Carbon plates, 4x hexagonal
       standoff pillars, 4 aggressive serrated teeth, and inner friction grip pads.
  5. head_assembly.FCStd:
     - Master assembly container linking all parts and 5x COTS standard servos (servo_nr645.FCStd).
"""

import math
import os
import sys
import zipfile
import FreeCAD as App
import Part

print("--- Generating Authentic 5-DoF Lynxmotion A-Pod Head & Mandibles Assembly ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts/head"
asm_dir = f"{repo_root}/hardware/mechanics/models/custom/v2"
cots_dir = f"{repo_root}/hardware/mechanics/models/cots"

os.makedirs(models_dir, exist_ok=True)
os.makedirs(asm_dir, exist_ok=True)

# Colors
COLOR_ALU = (0.75, 0.76, 0.78)         # SES Aluminum bracket finish
COLOR_DARK_PVC = (0.20, 0.20, 0.22)    # Dark technical polymer / PVC
COLOR_SERVO = (0.12, 0.12, 0.14)       # Black standard servo body
COLOR_PINCERS = (0.18, 0.18, 0.20)     # Carbon / precision PVC pincers
COLOR_RUBBER = (0.10, 0.10, 0.10)      # Weather stripping / rubber pad

z_base = 2.00
h_mount = 51.30
z_mid = z_base + 0.5 * h_mount  # Z = 27.65 mm


def make_dovetail_prism(x_throat, x_base, w_throat, w_base, z_min, z_max):
    """Constructs a male dovetail runner prism in the X-Y plane extruded along Z."""
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

# =============================================================================
# 1. Build Part: apod_head_mount.FCStd
# =============================================================================
print("1. Building apod_head_mount.FCStd...")
doc_mount_name = "apod_head_mount"
try:
    App.closeDocument(doc_mount_name)
except Exception:
    pass
doc_mount = App.newDocument(doc_mount_name)
fcstd_mount_path = f"{models_dir}/apod_head_mount.FCStd"

# 1. Male Dovetail Runner at X in [85.68, 92.50 mm], Z in [6.18, 53.10 mm]
#    Mates with 0.18 mm normal clearance into Chassis Core front socket (throat: 13.64, base: 21.64 mm):
male_runner = make_dovetail_prism(92.50, 85.68, 13.64, 21.64, 6.18, 53.10)

# 2. Extension Neck Bridge from Dovetail to Main Block (X in [92.50, 118.00 mm], Y in [-9.0, +9.0 mm], Z in [6.18, 53.10 mm]):
bridge = Part.makeBox(25.50, 18.00, 53.10 - 6.18, App.Vector(92.50, -9.00, 6.18))

# 3. Main Head Standoff Block clamped between body_bottom (Z = 2.0) and body_top (Z = 53.3 mm)
#    Spanning X = 118.0 .. 152.0 mm, Y in [-18.0, 18.0 mm]
box_body = Part.makeBox(34.0, 36.0, h_mount, App.Vector(118.0, -18.0, z_base))
mount_solid = box_body.fuse(bridge).fuse(male_runner)

# 2x Front Standoff Bores & Ruthex M3 Pockets at (128.0, ±12.0 mm)
for hy in [12.0, -12.0]:
    bore = Part.makeCylinder(1.70, h_mount + 10.0, App.Vector(128.0, hy, z_base - 5.0), App.Vector(0, 0, 1))
    top_pocket = Part.makeCylinder(2.10, 8.0, App.Vector(128.0, hy, z_base + h_mount - 7.5), App.Vector(0, 0, 1))
    bot_pocket = Part.makeCylinder(2.10, 8.0, App.Vector(128.0, hy, z_base - 0.5), App.Vector(0, 0, 1))
    mount_solid = mount_solid.cut(bore).cut(top_pocket).cut(bot_pocket)

# Vertical Pan Servo Pocket at X = 142.0, Y = 0.0
# Standard servo body: 42 x 21 x 44 mm
servo_pocket = Part.makeBox(42.0, 21.0, 44.0, App.Vector(126.0, -10.5, z_base + 4.0))
# Top spline bore Ø14 mm at X = 142.0, Y = 0.0
spline_bore = Part.makeCylinder(7.0, 12.0, App.Vector(142.0, 0.0, z_base + h_mount - 8.0), App.Vector(0, 0, 1))
mount_solid = mount_solid.cut(servo_pocket).cut(spline_bore)

# Central Cable Conduit (12.0 x 8.0 mm) through Bridge & Dovetail into Monocoque at Z in [28.00, 36.00 mm]
cable_conduit = Part.makeBox(60.0, 12.0, 8.0, App.Vector(84.0, -6.0, 28.00))
mount_solid = mount_solid.cut(cable_conduit)

obj_m = doc_mount.addObject("Part::Feature", "APod_Head_Mount")
obj_m.Label = "A-Pod Front Chassis Standoff Mount (v2)"
obj_m.Shape = mount_solid
obj_m.Visibility = True
doc_mount.recompute()
doc_mount.saveAs(fcstd_mount_path)
App.closeDocument(doc_mount_name)
print(f"✔ Saved: {fcstd_mount_path}")

# =============================================================================
# 2. Build Part: apod_neck_bracket.FCStd (SES 3-DoF Neck Gimbal)
# =============================================================================
print("2. Building apod_neck_bracket.FCStd...")
doc_neck_name = "apod_neck_bracket"
try:
    App.closeDocument(doc_neck_name)
except Exception:
    pass
doc_neck = App.newDocument(doc_neck_name)
fcstd_neck_path = f"{models_dir}/apod_neck_bracket.FCStd"

# Upper Pan hub plate (attaches to pan servo horn at Z = 54.5 mm)
pan_hub = Part.makeCylinder(12.0, 3.0, App.Vector(142.0, 0.0, z_base + h_mount), App.Vector(0, 0, 1))
pan_arm = Part.makeBox(36.0, 18.0, 3.0, App.Vector(142.0, -9.0, z_base + h_mount))
neck_solid = pan_hub.fuse(pan_arm)

# Vertical drop strut down to z_mid
drop_strut = Part.makeBox(4.0, 18.0, (z_base + h_mount) - (z_mid - 24.0), App.Vector(174.0, -9.0, z_mid - 24.0))
neck_solid = neck_solid.fuse(drop_strut)

# Tilt servo U-bracket at X = 175.0, Z = z_mid
tilt_box_out = Part.makeBox(28.0, 44.0, 48.0, App.Vector(164.0, -22.0, z_mid - 24.0))
tilt_box_in = Part.makeBox(30.0, 38.0, 42.0, App.Vector(162.0, -19.0, z_mid - 21.0))
tilt_u = tilt_box_out.cut(tilt_box_in)
tilt_bore = Part.makeCylinder(1.60, 50.0, App.Vector(175.0, -25.0, z_mid), App.Vector(0, 1, 0))
tilt_u = tilt_u.cut(tilt_bore)
neck_solid = neck_solid.fuse(tilt_u)

# Forward Roll Servo cradle spanning X = 188.0 .. 212.0 mm
roll_cradle_out = Part.makeBox(24.0, 44.0, 26.0, App.Vector(188.0, -22.0, z_mid - 13.0))
roll_cradle_in = Part.makeBox(26.0, 40.0, 21.2, App.Vector(186.0, -20.0, z_mid - 10.6))
roll_cradle = roll_cradle_out.cut(roll_cradle_in)
roll_horn_bore = Part.makeCylinder(7.0, 6.0, App.Vector(208.0, 0.0, z_mid), App.Vector(1, 0, 0))
roll_cradle = roll_cradle.cut(roll_horn_bore)
neck_solid = neck_solid.fuse(roll_cradle)

# Lightening cutouts along neck
light_hole1 = Part.makeCylinder(4.0, 30.0, App.Vector(158.0, 0.0, z_base + h_mount - 5.0), App.Vector(0, 0, 1))
light_hole2 = Part.makeCylinder(5.0, 50.0, App.Vector(175.0, -25.0, z_mid - 16.0), App.Vector(0, 1, 0))
neck_solid = neck_solid.cut(light_hole1).cut(light_hole2)

obj_n = doc_neck.addObject("Part::Feature", "APod_Neck_Bracket")
obj_n.Label = "A-Pod SES 3-DoF Neck Gimbal Bracket (ALU)"
obj_n.Shape = neck_solid
obj_n.Visibility = True
doc_neck.recompute()
doc_neck.saveAs(fcstd_neck_path)
App.closeDocument(doc_neck_name)
print(f"✔ Saved: {fcstd_neck_path}")

# =============================================================================
# 3. Build Part: apod_head_platform.FCStd (Insect Head Chassis Platform)
# =============================================================================
print("3. Building apod_head_platform.FCStd...")
doc_hp_name = "apod_head_platform"
try:
    App.closeDocument(doc_hp_name)
except Exception:
    pass
doc_hp = App.newDocument(doc_hp_name)
fcstd_hp_path = f"{models_dir}/apod_head_platform.FCStd"

# Rear roll attachment boss
roll_boss = Part.makeCylinder(12.0, 4.0, App.Vector(214.0, 0.0, z_mid), App.Vector(1, 0, 0))
roll_bore = Part.makeCylinder(4.0, 10.0, App.Vector(212.0, 0.0, z_mid), App.Vector(1, 0, 0))
head_solid = roll_boss.cut(roll_bore)

# Contoured Head Deck polygon
head_pts = [
    App.Vector(215.0, 16.0, 0.0),
    App.Vector(225.0, 46.0, 0.0),
    App.Vector(248.0, 50.0, 0.0),
    App.Vector(278.0, 38.0, 0.0),
    App.Vector(282.0, 15.0, 0.0),
    App.Vector(282.0, -15.0, 0.0),
    App.Vector(278.0, -38.0, 0.0),
    App.Vector(248.0, -50.0, 0.0),
    App.Vector(225.0, -46.0, 0.0),
    App.Vector(215.0, -16.0, 0.0),
]
h_edges = []
for i in range(len(head_pts)):
    p1 = head_pts[i]
    p2 = head_pts[(i + 1) % len(head_pts)]
    h_edges.append(Part.makeLine(p1, p2))
h_wire = Part.Wire(h_edges)
h_face = Part.Face(h_wire)

# Bottom Deck (Z in [16.0, 18.5])
h_bot = h_face.extrude(App.Vector(0, 0, 2.5))
h_bot.translate(App.Vector(0, 0, z_mid - 12.0))

# Top Carapace Deck (Z in [36.0, 38.5])
h_top = h_face.extrude(App.Vector(0, 0, 2.5))
h_top.translate(App.Vector(0, 0, z_mid + 8.0))

head_solid = head_solid.fuse(h_bot).fuse(h_top)

# Central monocoque spacer bulkhead linking top and bottom decks
mid_bulk = Part.makeBox(48.0, 10.0, 20.0, App.Vector(222.0, -5.0, z_mid - 10.0))
mid_conduit = Part.makeBox(30.0, 14.0, 12.0, App.Vector(226.0, -7.0, z_mid - 6.0))
mid_bulk = mid_bulk.cut(mid_conduit)
head_solid = head_solid.fuse(mid_bulk)

# 2x Mandible Servo Mount Cutouts at Y = ±26.0 mm
for sy in [26.0, -26.0]:
    s_cut = Part.makeBox(42.0, 21.0, 26.0, App.Vector(230.0, sy - 10.5, z_mid - 11.0))
    s_spline = Part.makeCylinder(7.0, 10.0, App.Vector(258.0, sy, z_mid + 5.0), App.Vector(0, 0, 1))
    head_solid = head_solid.cut(s_cut).cut(s_spline)

# Dual compound eye sensor ports (Ø5.0 mm) at (232.0, ±44.0, z_mid)
for ey in [44.0, -44.0]:
    eye_boss = Part.makeCylinder(4.5, 6.0, App.Vector(232.0, ey - 3.0 * (1 if ey>0 else -1), z_mid - 1.0), App.Vector(0, (1 if ey>0 else -1), 0))
    eye_bore = Part.makeCylinder(2.5, 12.0, App.Vector(232.0, ey - 6.0 * (1 if ey>0 else -1), z_mid - 1.0), App.Vector(0, (1 if ey>0 else -1), 0))
    head_solid = head_solid.fuse(eye_boss).cut(eye_bore)

obj_hp = doc_hp.addObject("Part::Feature", "APod_Head_Platform")
obj_hp.Label = "A-Pod Insect Head Platform & Servo Chassis (v2)"
obj_hp.Shape = head_solid
obj_hp.Visibility = True
doc_hp.recompute()
doc_hp.saveAs(fcstd_hp_path)
App.closeDocument(doc_hp_name)
print(f"✔ Saved: {fcstd_hp_path}")

# =============================================================================
# 4. Build Parts: apod_mandible_left.FCStd & apod_mandible_right.FCStd (Massive 3D Sandwich)
# =============================================================================
print("4. Building Massive 3D-Sandwich A-Pod Mandibles...")

def build_authentic_mandible(is_left=True):
    y_sign = 1.0 if is_left else -1.0
    t_plate = 2.50
    z_bot = 20.0
    z_top = 36.5
    h_gap = z_top - (z_bot + t_plate)  # 14.0 mm
    
    pts = [
        App.Vector(246.0, y_sign * 18.0, 0.0),   # rear inner lug
        App.Vector(244.0, y_sign * 32.0, 0.0),   # rear outer lug
        App.Vector(255.0, y_sign * 42.0, 0.0),   # outer shoulder
        App.Vector(280.0, y_sign * 60.0, 0.0),   # outer sweep
        App.Vector(310.0, y_sign * 68.0, 0.0),   # max width flank
        App.Vector(345.0, y_sign * 50.0, 0.0),   # forward curve
        App.Vector(378.0, y_sign * 5.0, 0.0),    # sharp anterior tip
        App.Vector(368.0, y_sign * 12.0, 0.0),   # tooth 1 notch
        App.Vector(360.0, y_sign * 8.0, 0.0),    # tooth 2 tip
        App.Vector(348.0, y_sign * 18.0, 0.0),   # tooth 2 notch
        App.Vector(338.0, y_sign * 16.0, 0.0),   # tooth 3 tip
        App.Vector(322.0, y_sign * 26.0, 0.0),   # tooth 3 notch
        App.Vector(308.0, y_sign * 24.0, 0.0),   # tooth 4 tip
        App.Vector(285.0, y_sign * 32.0, 0.0),   # basal throat
        App.Vector(268.0, y_sign * 22.0, 0.0),   # inner hub
    ]
    
    wire_edges = []
    for i in range(len(pts)):
        p1 = pts[i]
        p2 = pts[(i + 1) % len(pts)]
        wire_edges.append(Part.makeLine(p1, p2))
    wire = Part.Wire(wire_edges)
    face = Part.Face(wire)
    
    # Bottom plate
    plate_bot = face.extrude(App.Vector(0, 0, t_plate))
    plate_bot.translate(App.Vector(0, 0, z_bot))
    
    # Top plate
    plate_top = face.extrude(App.Vector(0, 0, t_plate))
    plate_top.translate(App.Vector(0, 0, z_top))
    
    sandwich = plate_bot.fuse(plate_top)
    
    # 4x Standoff Spacers
    standoff_coords = [
        (265.0, 38.0),
        (295.0, 62.0),
        (330.0, 50.0),
        (355.0, 24.0),
    ]
    for sx, sy in standoff_coords:
        cyl = Part.makeCylinder(2.5, h_gap, App.Vector(sx, y_sign * sy, z_bot + t_plate), App.Vector(0, 0, 1))
        bore = Part.makeCylinder(1.25, h_gap + 2.0 * t_plate + 4.0, App.Vector(sx, y_sign * sy, z_bot - 2.0), App.Vector(0, 0, 1))
        sandwich = sandwich.fuse(cyl).cut(bore)
        
    # Servo Horn Mounting Hub at (258.0, ±26.0)
    horn_hub = Part.makeCylinder(11.0, t_plate + 2.0, App.Vector(258.0, y_sign * 26.0, z_top - 1.0), App.Vector(0, 0, 1))
    horn_bore = Part.makeCylinder(3.5, 20.0, App.Vector(258.0, y_sign * 26.0, z_bot - 2.0), App.Vector(0, 0, 1))
    sandwich = sandwich.fuse(horn_hub).cut(horn_bore)
    
    # 4x Horn screw holes (M2 at radius 8.0 mm)
    for ang in [0, 90, 180, 270]:
        rad = math.radians(ang)
        hx = 258.0 + 8.0 * math.cos(rad)
        hy = y_sign * (26.0 + 8.0 * math.sin(rad))
        hb = Part.makeCylinder(1.1, 20.0, App.Vector(hx, hy, z_bot - 2.0), App.Vector(0, 0, 1))
        sandwich = sandwich.cut(hb)
        
    # Inner friction grip rubber strip (weather stripping) along the inner edge
    grip_pts = [
        App.Vector(372.0, y_sign * 7.0, 0.0),
        App.Vector(360.0, y_sign * 10.0, 0.0),
        App.Vector(338.0, y_sign * 18.0, 0.0),
        App.Vector(308.0, y_sign * 26.0, 0.0),
        App.Vector(285.0, y_sign * 34.0, 0.0),
    ]
    for i in range(len(grip_pts) - 1):
        gp1 = grip_pts[i]
        gp2 = grip_pts[i+1]
        v = gp2 - gp1
        length = v.Length
        angle = math.degrees(math.atan2(v.y, v.x))
        pad = Part.makeBox(length, 1.8, h_gap, App.Vector(0, -0.9, 0))
        pad.rotate(App.Vector(0, 0, 0), App.Vector(0, 0, 1), angle)
        pad.translate(App.Vector(gp1.x, gp1.y, z_bot + t_plate))
        sandwich = sandwich.fuse(pad)
        
    return sandwich

# Left Mandible
doc_ml_name = "apod_mandible_left"
try:
    App.closeDocument(doc_ml_name)
except Exception:
    pass
doc_ml = App.newDocument(doc_ml_name)
obj_ml = doc_ml.addObject("Part::Feature", "APod_Mandible_Left")
obj_ml.Label = "A-Pod Massive 3D-Sandwich Mandible (Left)"
obj_ml.Shape = build_authentic_mandible(is_left=True)
obj_ml.Visibility = True
fcstd_ml_path = f"{models_dir}/apod_mandible_left.FCStd"
doc_ml.recompute()
doc_ml.saveAs(fcstd_ml_path)
App.closeDocument(doc_ml_name)
print(f"✔ Saved: {fcstd_ml_path}")

# Right Mandible
doc_mr_name = "apod_mandible_right"
try:
    App.closeDocument(doc_mr_name)
except Exception:
    pass
doc_mr = App.newDocument(doc_mr_name)
obj_mr = doc_mr.addObject("Part::Feature", "APod_Mandible_Right")
obj_mr.Label = "A-Pod Massive 3D-Sandwich Mandible (Right)"
obj_mr.Shape = build_authentic_mandible(is_left=False)
obj_mr.Visibility = True
fcstd_mr_path = f"{models_dir}/apod_mandible_right.FCStd"
doc_mr.recompute()
doc_mr.saveAs(fcstd_mr_path)
App.closeDocument(doc_mr_name)
print(f"✔ Saved: {fcstd_mr_path}")

# =============================================================================
# 5. Build Master Subassembly: head_assembly.FCStd (5-DoF)
# =============================================================================
print("5. Building 5-DoF head_assembly.FCStd...")
doc_head_name = "head_assembly"
try:
    App.closeDocument(doc_head_name)
except Exception:
    pass
doc_head = App.newDocument(doc_head_name)
fcstd_head_path = f"{asm_dir}/head_assembly.FCStd"
doc_head.saveAs(fcstd_head_path)

# Open docs for linking
d_mount = App.openDocument(fcstd_mount_path)
d_neck = App.openDocument(fcstd_neck_path)
d_hp = App.openDocument(fcstd_hp_path)
d_ml = App.openDocument(fcstd_ml_path)
d_mr = App.openDocument(fcstd_mr_path)
d_servo = App.openDocument(f"{cots_dir}/servo_nr645.FCStd")

head_part = doc_head.addObject("App::Part", "Head_Assembly")
head_part.Label = "Lynxmotion A-Pod 5-DoF Head & Mandibles Assembly (v2)"
head_part.Visibility = True

def make_link(name, label, target_obj, placement, color=None, parent=head_part):
    lnk = doc_head.addObject("App::Link", name)
    lnk.setLink(target_obj)
    lnk.Label = label
    lnk.Placement = placement
    parent.addObject(lnk)
    lnk.Visibility = True
    if hasattr(lnk, "ViewObject") and lnk.ViewObject is not None:
        vo = lnk.ViewObject
        vo.Visibility = True
        if color is not None:
            vo.OverrideMaterial = True
            mat = vo.ShapeMaterial
            mat.DiffuseColor = color
            vo.ShapeMaterial = mat
    return lnk

# 1. Front Standoff Mount Block (X=128, Y=±12)
p_mount = App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation())
make_link("Head_Mount", "1. A-Pod Front Standoff Mount (CFRP/ALU)", d_mount.getObject("APod_Head_Mount"), p_mount, COLOR_DARK_PVC)

# 2. Pan Servo (Joint 1: Head Pan/Yaw, vertical Z-axis)
p_s_pan = App.Placement(App.Vector(142.0, 0.0, z_base + h_mount - 4.5), App.Rotation(App.Vector(0, 1, 0), 0.0))
make_link("Servo_Pan", "2. Head Pan Servo (Standard HS-645MG, COTS)", d_servo.getObject("Servo_Complete"), p_s_pan, COLOR_SERVO)

# 3. SES Neck Gimbal Bracket
p_neck = App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation())
make_link("Neck_Bracket", "3. A-Pod SES 3-DoF Neck Gimbal (ALU)", d_neck.getObject("APod_Neck_Bracket"), p_neck, COLOR_ALU)

# 4. Tilt Servo (Joint 2: Head Tilt/Pitch, horizontal Y-axis)
p_s_tilt = App.Placement(App.Vector(175.0, 0.0, z_mid), App.Rotation(App.Vector(1, 0, 0), 90.0))
make_link("Servo_Tilt", "4. Head Tilt Servo (Standard HS-645MG, COTS)", d_servo.getObject("Servo_Complete"), p_s_tilt, COLOR_SERVO)

# 5. Roll Servo (Joint 3: Head Roll/Rotation, longitudinal X-axis)
p_s_roll = App.Placement(App.Vector(208.0, 0.0, z_mid), App.Rotation(App.Vector(0, 1, 0), -90.0))
make_link("Servo_Roll", "5. Head Roll Servo (Standard HS-645MG, COTS)", d_servo.getObject("Servo_Complete"), p_s_roll, COLOR_SERVO)

# 6. Insect Head Platform & Servo Chassis
p_hp = App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation())
make_link("Head_Platform", "6. A-Pod Head Platform & Chassis (CFRP/ALU)", d_hp.getObject("APod_Head_Platform"), p_hp, COLOR_ALU)

# 7. Left Mandible Servo (Joint 4: Left Jaw drive)
p_s_ml = App.Placement(App.Vector(258.0, 26.0, z_mid + 8.5), App.Rotation(App.Vector(0, 0, 1), 0.0))
make_link("Servo_Mandible_Left", "7. Left Mandible Servo (Standard HS-645MG, COTS)", d_servo.getObject("Servo_Complete"), p_s_ml, COLOR_SERVO)

# 8. Right Mandible Servo (Joint 5: Right Jaw drive)
p_s_mr = App.Placement(App.Vector(258.0, -26.0, z_mid + 8.5), App.Rotation(App.Vector(0, 0, 1), 0.0))
make_link("Servo_Mandible_Right", "8. Right Mandible Servo (Standard HS-645MG, COTS)", d_servo.getObject("Servo_Complete"), p_s_mr, COLOR_SERVO)

# 9. Left Mandible (Massive 3D Sandwich)
p_ml = App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation())
make_link("Mandible_Left", "9. A-Pod 3D-Sandwich Mandible Left (CFRP/ALU)", d_ml.getObject("APod_Mandible_Left"), p_ml, COLOR_PINCERS)

# 10. Right Mandible (Massive 3D Sandwich)
p_mr = App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation())
make_link("Mandible_Right", "10. A-Pod 3D-Sandwich Mandible Right (CFRP/ALU)", d_mr.getObject("APod_Mandible_Right"), p_mr, COLOR_PINCERS)

doc_head.recompute()
doc_head.save()
print(f"✔ Saved Head Assembly: {fcstd_head_path}")
print(f"Assembly Valid: {head_part.Shape.isValid()}")
bb = head_part.Shape.BoundBox
print(f"Head Bounding Box: X=[{bb.XMin:.1f}, {bb.XMax:.1f}], Y=[{bb.YMin:.1f}, {bb.YMax:.1f}], Z=[{bb.ZMin:.1f}, {bb.ZMax:.1f}]")

def patch_gui_visibility(filepath):
    temp_zip = filepath + ".tmp"
    with zipfile.ZipFile(filepath, "r") as zin:
        with zipfile.ZipFile(temp_zip, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "GuiDocument.xml":
                    xml_str = data.decode("utf-8")
                    xml_str = xml_str.replace('<Bool value="false"/>', '<Bool value="true"/>')
                    data = xml_str.encode("utf-8")
                zout.writestr(item, data)
    os.replace(temp_zip, filepath)

patch_gui_visibility(fcstd_head_path)
patch_gui_visibility(fcstd_mount_path)
patch_gui_visibility(fcstd_neck_path)
patch_gui_visibility(fcstd_hp_path)
patch_gui_visibility(fcstd_ml_path)
patch_gui_visibility(fcstd_mr_path)

print("✔ Patched GuiDocument.xml for full visibility")
sys.exit(0)
