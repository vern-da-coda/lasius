#!/usr/bin/env python3
"""
Generate Lynxmotion A-Pod Style Gaster (Abdomen) Modular Assembly for Lasius v2
(custom/v2/gaster_assembly.FCStd & custom/v2/parts/apod_gaster*.FCStd)
================================================================================
Design Architecture (Lynxmotion A-Pod Style adapted to Lasius Spacer Bores):
  1. apod_tail_mount.FCStd (Chassis Standoff Interface Block):
     - Spans the 51.30 mm vertical gap between Body_Bottom (Z = 2.00 mm) and
       Body_Top (Z = 53.30 mm) at the rear of Lasius.
     - Rigidly clamped by the 2 rear centerline M3 spacer bores at X = -90.0 mm
       and X = -120.0 mm (Y = 0.0 mm, inter-bore distance 30.0 mm).
     - Incorporates top and bottom Ruthex M3 pockets and M3 through-bores.
     - Extends rearward to X = -136.0 mm with an integrated clevis yoke for the
       standard HS-645MG Pan servo (yaw left/right).
  2. apod_tail_bracket.FCStd (SES Style 2-DoF Gimbal Bracket):
     - Heavy-duty SES-style dual-axis gimbal:
       * Vertical yaw/pan axis (Z-axis at X = -138.0 mm)
       * Horizontal pitch/tilt axis (Y-axis at X = -146.0 mm, Z = 27.65 mm)
     - Houses the standard HS-645MG Tilt servo with opposing ball-bearing support.
  3. apod_gaster.FCStd (A-Pod Plate-and-Spacer Sandwich Abdomen):
     - Iconic A-Pod ant abdomen contour:
       * Elongated teardrop profile (length 117 mm, X in [-148.0, -265.0 mm],
         max width 96.0 mm at X = -195.0 mm).
       * Top plate (Z = 38.0 .. 40.5 mm) & Bottom plate (Z = 15.0 .. 17.5 mm)
         made of 2.5 mm dark carbon / precision PVC.
       * Spaced by 4x hexagonal standoff pillars (L = 20.5 mm) and 2x vertical
         T-slot cross-ribs creating a rigid torsion-box chassis.
       * Spacious internal equipment bay for auxiliary battery, telemetry,
         or payload electronics.
       * Front clevis tongue with pivot bore mating to the Tilt servo horn.
  4. gaster_assembly.FCStd:
     - Master assembly container linking mount block, gimbal bracket, sandwich gaster,
       and COTS standard servos (servo_nr645.FCStd).
"""

import math
import os
import sys
import zipfile
import FreeCAD as App
import Part

print("--- Generating Lynxmotion A-Pod Gaster (Abdomen) Assembly (v2) ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts"
asm_dir = f"{repo_root}/hardware/mechanics/models/custom/v2"
cots_dir = f"{repo_root}/hardware/mechanics/models/cots"

os.makedirs(models_dir, exist_ok=True)
os.makedirs(asm_dir, exist_ok=True)

# Colors
COLOR_ALU = (0.75, 0.76, 0.78)         # SES Aluminum bracket finish
COLOR_DARK_PVC = (0.20, 0.20, 0.22)    # Dark technical polymer / PVC
COLOR_SERVO = (0.12, 0.12, 0.14)       # Black standard servo body
COLOR_PLATES = (0.16, 0.16, 0.18)      # 2.5mm Carbon fiber plates
COLOR_SPACER = (0.78, 0.78, 0.80)      # Aluminum hex standoff spacers

# =============================================================================
# 1. Build Part: apod_tail_mount.FCStd
# =============================================================================
print("1. Building apod_tail_mount.FCStd...")
doc_m_name = "apod_tail_mount"
try:
    App.closeDocument(doc_m_name)
except Exception:
    pass
doc_m = App.newDocument(doc_m_name)
fcstd_m_path = f"{models_dir}/apod_tail_mount.FCStd"

z_base = 2.00
h_mount = 51.30
z_mid = z_base + 0.5 * h_mount  # Z = 27.65 mm

# Main body block spanning X = -82.0 .. -136.0 mm (length 54.0 mm), Y in [-15.0, 15.0 mm]
body_box = Part.makeBox(54.0, 30.0, h_mount, App.Vector(-136.0, -15.0, z_base))

# 2x Centerline Standoff Bores & Ruthex M3 Pockets at X = -90.0 and X = -120.0 mm (Y = 0)
mount_solid = body_box
for sx in [-90.0, -120.0]:
    bore = Part.makeCylinder(1.70, h_mount + 10.0, App.Vector(sx, 0.0, z_base - 5.0), App.Vector(0, 0, 1))
    top_pocket = Part.makeCylinder(2.10, 8.0, App.Vector(sx, 0.0, z_base + h_mount - 7.5), App.Vector(0, 0, 1))
    bot_pocket = Part.makeCylinder(2.10, 8.0, App.Vector(sx, 0.0, z_base - 0.5), App.Vector(0, 0, 1))
    mount_solid = mount_solid.cut(bore).cut(top_pocket).cut(bot_pocket)

# Rear Clevis Yoke for Standard Pan Servo at X in [-138.0, -126.0]
# Vertical servo ear pocket (width 21.0 mm, height 42.0 mm)
pan_cradle = Part.makeBox(14.0, 21.0, 42.0, App.Vector(-138.0, -10.5, z_mid - 21.0))
mount_solid = mount_solid.cut(pan_cradle)

# Vertical Pan Pivot Bore (Ø3.2 mm) along Z at X = -134.0, Y = 0.0
pan_bore = Part.makeCylinder(1.60, h_mount + 5.0, App.Vector(-134.0, 0.0, z_base - 2.0), App.Vector(0, 0, 1))
mount_solid = mount_solid.cut(pan_bore)

# Weight relief and cable tunnel
tunnel = Part.makeBox(36.0, 16.0, 20.0, App.Vector(-118.0, -8.0, z_mid - 10.0))
mount_solid = mount_solid.cut(tunnel)

obj_tm = doc_m.addObject("Part::Feature", "APod_Tail_Mount")
obj_tm.Label = "A-Pod Rear Chassis Standoff Mount (v2)"
obj_tm.Shape = mount_solid
obj_tm.Visibility = True
doc_m.recompute()
doc_m.saveAs(fcstd_m_path)
App.closeDocument(doc_m_name)
print(f"✔ Saved: {fcstd_m_path}")

# =============================================================================
# 2. Build Part: apod_tail_bracket.FCStd
# =============================================================================
print("2. Building apod_tail_bracket.FCStd...")
doc_tb_name = "apod_tail_bracket"
try:
    App.closeDocument(doc_tb_name)
except Exception:
    pass
doc_tb = App.newDocument(doc_tb_name)
fcstd_tb_path = f"{models_dir}/apod_tail_bracket.FCStd"

# SES 2-DoF Gimbal Bracket linking Pan servo to Tilt servo
# Pan axis: vertical Z at X = -134.0, Y = 0.0
# Tilt axis: horizontal Y at X = -146.0, Z = z_mid
t_alu = 2.50
w_tb = 42.0
h_tb = 48.0
l_tb = 24.0

b_out = Part.makeBox(l_tb, w_tb, h_tb, App.Vector(-150.0, -w_tb / 2.0, z_mid - h_tb / 2.0))
b_in = Part.makeBox(l_tb + 5.0, w_tb - 2.0 * t_alu, h_tb - 2.0 * t_alu, App.Vector(-152.0, -(w_tb - 2.0 * t_alu) / 2.0, z_mid - (h_tb - 2.0 * t_alu) / 2.0))
bracket_solid = b_out.cut(b_in)

# Vertical Pan horn mounting flange at X = -134.0 .. -130.0 mm
pan_ear_top = Part.makeBox(12.0, 28.0, 3.0, App.Vector(-138.0, -14.0, z_mid + h_tb / 2.0 - 3.0))
pan_ear_bot = Part.makeBox(12.0, 28.0, 3.0, App.Vector(-138.0, -14.0, z_mid - h_tb / 2.0))
bracket_solid = bracket_solid.fuse(pan_ear_top).fuse(pan_ear_bot)

# Pan pivot holes (Ø3.2 mm) along Z at X = -134.0, Y = 0.0
p_hole = Part.makeCylinder(1.60, 60.0, App.Vector(-134.0, 0.0, z_mid - 30.0), App.Vector(0, 0, 1))
bracket_solid = bracket_solid.cut(p_hole)

# Horizontal Tilt pivot holes (Ø3.2 mm) along Y at X = -146.0, Z = z_mid
t_hole = Part.makeCylinder(1.60, w_tb + 10.0, App.Vector(-146.0, -(w_tb + 10.0) / 2.0, z_mid), App.Vector(0, 1, 0))
bracket_solid = bracket_solid.cut(t_hole)

obj_tb = doc_tb.addObject("Part::Feature", "APod_Tail_Bracket")
obj_tb.Label = "A-Pod SES 2-DoF Tail Gimbal Bracket (ALU)"
obj_tb.Shape = bracket_solid
obj_tb.Visibility = True
doc_tb.recompute()
doc_tb.saveAs(fcstd_tb_path)
App.closeDocument(doc_tb_name)
print(f"✔ Saved: {fcstd_tb_path}")

# =============================================================================
# 3. Build Part: apod_gaster.FCStd (Plate-and-Spacer Sandwich Abdomen)
# =============================================================================
print("3. Building apod_gaster.FCStd...")
doc_g_name = "apod_gaster"
try:
    App.closeDocument(doc_g_name)
except Exception:
    pass
doc_g = App.newDocument(doc_g_name)
fcstd_g_path = f"{models_dir}/apod_gaster.FCStd"

# A-Pod Teardrop Sandwich Ant Gaster Outline:
# X in [-148.0, -265.0 mm], max width 96.0 mm (Y in [-48.0, +48.0])
pts_gaster_half = [
    App.Vector(-148.0, 16.0, 0.0),    # Petiolus waist
    App.Vector(-162.0, 36.0, 0.0),    # Expanding flank
    App.Vector(-188.0, 48.0, 0.0),    # Max girth flank
    App.Vector(-220.0, 40.0, 0.0),    # Tapering posterior
    App.Vector(-248.0, 22.0, 0.0),    # Sub-apical taper
    App.Vector(-265.0, 0.0, 0.0),     # Posterior stinger tip
]
spline_half = Part.BSplineCurve()
spline_half.interpolate(pts_gaster_half)

pts_lower = [App.Vector(p.x, -p.y, 0.0) for p in reversed(pts_gaster_half[1:-1])]
spline_lower = Part.BSplineCurve()
spline_lower.interpolate([pts_gaster_half[-1]] + pts_lower + [pts_gaster_half[0]])

wire_gaster = Part.Wire([spline_half.toShape(), spline_lower.toShape()])
face_plate = Part.Face(wire_gaster)

# Plates:
# Top Plate: Z = 38.00 .. 40.50 mm (thick = 2.50 mm)
t_plate = 2.50
z_top = 38.00
z_bot = 15.00
plate_top = face_plate.extrude(App.Vector(0.0, 0.0, t_plate))
plate_top.translate(App.Vector(0.0, 0.0, z_top))

# Bottom Plate: Z = 15.00 .. 17.50 mm (thick = 2.50 mm)
plate_bot = face_plate.extrude(App.Vector(0.0, 0.0, t_plate))
plate_bot.translate(App.Vector(0.0, 0.0, z_bot))

gaster_solid = plate_top.fuse(plate_bot)

# 4x Hexagonal Standoff Spacers (Height = z_top - (z_bot + t_plate) = 38.0 - 17.5 = 20.5 mm)
h_sp = z_top - (z_bot + t_plate)
z_sp_bot = z_bot + t_plate
spacer_locs = [
    (-170.0, 22.0),
    (-170.0, -22.0),
    (-225.0, 18.0),
    (-225.0, -18.0),
]
for sx, sy in spacer_locs:
    spacer_cyl = Part.makeCylinder(4.0, h_sp, App.Vector(sx, sy, z_sp_bot), App.Vector(0, 0, 1))
    s_bore = Part.makeCylinder(1.60, 40.0, App.Vector(sx, sy, z_bot - 2.0), App.Vector(0, 0, 1))
    gaster_solid = gaster_solid.fuse(spacer_cyl).cut(s_bore)

# 2x Vertical T-Slot Bulkhead Cross-Ribs (forming internal battery/electronics bay)
rib_front = Part.makeBox(2.5, 52.0, h_sp, App.Vector(-180.0, -26.0, z_sp_bot))
rib_rear = Part.makeBox(2.5, 44.0, h_sp, App.Vector(-215.0, -22.0, z_sp_bot))
gaster_solid = gaster_solid.fuse(rib_front).fuse(rib_rear)

# Front Clevis Tongue at Petiolus for Tilt Axis Connection (X in [-152.0, -144.0], Z in [z_mid - 4.0, z_mid + 4.0])
tongue = Part.makeBox(12.0, 18.0, 8.0, App.Vector(-152.0, -9.0, z_mid - 4.0))
# Tilt pivot hole (Ø3.2 mm) along Y at X = -146.0, Z = z_mid
t_bore = Part.makeCylinder(1.60, 30.0, App.Vector(-146.0, -15.0, z_mid), App.Vector(0, 1, 0))
tongue = tongue.cut(t_bore)
gaster_solid = gaster_solid.fuse(tongue)

obj_g = doc_g.addObject("Part::Feature", "APod_Gaster")
obj_g.Label = "A-Pod Plate-and-Spacer Sandwich Abdomen (v2)"
obj_g.Shape = gaster_solid
obj_g.Visibility = True
doc_g.recompute()
doc_g.saveAs(fcstd_g_path)
App.closeDocument(doc_g_name)
print(f"✔ Saved: {fcstd_g_path}")

# =============================================================================
# 4. Build Master Subassembly: gaster_assembly.FCStd
# =============================================================================
print("4. Building gaster_assembly.FCStd...")
doc_ga_name = "gaster_assembly"
try:
    App.closeDocument(doc_ga_name)
except Exception:
    pass
doc_ga = App.newDocument(doc_ga_name)
fcstd_ga_path = f"{asm_dir}/gaster_assembly.FCStd"
doc_ga.saveAs(fcstd_ga_path)

# Open master docs for linking
d_tm = App.openDocument(fcstd_m_path)
d_tb = App.openDocument(fcstd_tb_path)
d_g = App.openDocument(fcstd_g_path)
d_servo = App.openDocument(f"{cots_dir}/servo_nr645.FCStd")

gaster_part = doc_ga.addObject("App::Part", "Gaster_Assembly")
gaster_part.Label = "Lynxmotion A-Pod 2-DoF Gaster (Abdomen) Assembly (v2)"
gaster_part.Visibility = True

def make_link_ga(name, label, target_obj, placement, color=None, parent=gaster_part):
    lnk = doc_ga.addObject("App::Link", name)
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

# 1. Rear Standoff Mount Block on Chassis Centerline Spacers (X = -90, -120 mm)
p_tm = App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation())
make_link_ga("Tail_Mount", "1. A-Pod Rear Chassis Standoff Mount (CFRP)", d_tm.getObject("APod_Tail_Mount"), p_tm, COLOR_DARK_PVC)

# 2. Pan Servo (Standard HS-645MG) at X = -134.0, Y = 0.0, Z = z_mid
# Vertical yaw axis along Z
p_servo_pan = App.Placement(App.Vector(-134.0, 0.0, z_mid), App.Rotation(App.Vector(0, 1, 0), 90.0))
make_link_ga("Servo_Tail_Pan", "2. Tail Pan/Yaw Servo (Standard HS-645MG, COTS)", d_servo.getObject("Servo_Complete"), p_servo_pan, COLOR_SERVO)

# 3. 2-DoF Gimbal Bracket
p_tb = App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation())
make_link_ga("Tail_Bracket", "3. A-Pod SES Gimbal Bracket (ALU)", d_tb.getObject("APod_Tail_Bracket"), p_tb, COLOR_ALU)

# 4. Tilt Servo (Standard HS-645MG) at X = -146.0, Y = 0.0, Z = z_mid
# Horizontal pitch axis along Y
p_servo_tilt = App.Placement(App.Vector(-146.0, 0.0, z_mid), App.Rotation(App.Vector(1, 0, 0), 90.0))
make_link_ga("Servo_Tail_Tilt", "4. Tail Tilt/Pitch Servo (Standard HS-645MG, COTS)", d_servo.getObject("Servo_Complete"), p_servo_tilt, COLOR_SERVO)

# 5. Sandwich Ant Gaster / Abdomen Body
p_g = App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation())
make_link_ga("Gaster_Body", "5. A-Pod Plate-and-Spacer Sandwich Abdomen (2.5mm CFRP)", d_g.getObject("APod_Gaster"), p_g, COLOR_PLATES)

doc_ga.recompute()
doc_ga.save()
print(f"✔ Saved Gaster Assembly: {fcstd_ga_path}")
print(f"Assembly Valid: {gaster_part.Shape.isValid()}")
bb = gaster_part.Shape.BoundBox
print(f"Gaster Bounding Box: X=[{bb.XMin:.1f}, {bb.XMax:.1f}], Y=[{bb.YMin:.1f}, {bb.YMax:.1f}], Z=[{bb.ZMin:.1f}, {bb.ZMax:.1f}]")

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

patch_gui_visibility(fcstd_ga_path)
patch_gui_visibility(fcstd_m_path)
patch_gui_visibility(fcstd_tb_path)
patch_gui_visibility(fcstd_g_path)

print("✔ Patched GuiDocument.xml for full visibility")
sys.exit(0)
