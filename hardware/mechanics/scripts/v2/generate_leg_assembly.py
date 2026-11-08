#!/usr/bin/env python3
"""
Generate Lasius Leg Assembly v2 (Modular Subassembly with Organic Monolithic Femur & Encapsulated ADS1115)
- Preserves v1 leg_assembly.FCStd untouched and outputs to leg_assembly_v2.FCStd
- Links to femur.FCStd (Femur_Body, Femur_Cover, ADS1115_Board)
"""

import math
import os
import shutil
import FreeCAD as App
import Part

print("--- Generating Lasius Leg Assembly v2 (with Organic Femur & Encapsulated ADS1115) ---")

doc_name = "leg_assembly"
models_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/models"
v1_parts_dir = f"{models_dir}/custom/v1/parts"
v2_parts_dir = f"{models_dir}/custom/v2/parts"
v2_asm_dir = f"{models_dir}/custom/v2"
hw_dir = f"{models_dir}/hardware"
fcstd_path = f"{v2_asm_dir}/leg_assembly.FCStd"
step_path = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/step/custom/v2/leg_assembly.step"
stl_path = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/stl/custom/v2/leg_assembly.stl"

os.makedirs(v2_asm_dir, exist_ok=True)
os.makedirs(os.path.dirname(step_path), exist_ok=True)
os.makedirs(os.path.dirname(stl_path), exist_ok=True)

try:
    App.closeDocument(doc_name)
except Exception:
    pass

doc = App.newDocument(doc_name)
doc.saveAs(fcstd_path)

# Open all master part documents
doc_coxa = App.openDocument(f"{v2_parts_dir}/coxa_bracket.FCStd")
doc_femur = App.openDocument(f"{v2_parts_dir}/femur.FCStd")
doc_tibia = App.openDocument(f"{v2_parts_dir}/tibia.FCStd")
doc_servo = App.openDocument(f"{hw_dir}/servo_nr645.FCStd")

# Open hardware library documents
doc_b = App.openDocument(f"{hw_dir}/bearing_684_6x3.FCStd")
doc_w = App.openDocument(f"{hw_dir}/washer_m4_shim.FCStd")
doc_n = App.openDocument(f"{hw_dir}/nut_m4_hex.FCStd")
doc_s = App.openDocument(f"{hw_dir}/screw_m4_countersunk.FCStd")

# Main Assembly Container
asm_part = doc.addObject("App::Part", "Leg_Assembly_v2")
asm_part.Label = "Lasius Leg Assembly v2 (Organic Femur + Encapsulated ADC)"
for o in asm_part.Origin.OutList:
    if hasattr(o, "Visibility"):
        o.Visibility = False
asm_part.Origin.Visibility = False
asm_part.Visibility = True


def make_link(name, label, target_obj, placement, color=None, parent=asm_part):
    lnk = doc.addObject("App::Link", name)
    lnk.setLink(target_obj)
    lnk.Label = label
    lnk.Placement = placement
    parent.addObject(lnk)
    if color is not None and hasattr(lnk, "ViewObject") and lnk.ViewObject is not None:
        vo = lnk.ViewObject
        vo.Visibility = True
        vo.OverrideMaterial = True
        mat = vo.ShapeMaterial
        mat.DiffuseColor = color
        vo.ShapeMaterial = mat
    return lnk


# -------------------------------------------------------------
# 1. Structural Parts
# -------------------------------------------------------------
# Coxa Bracket:
rot_c = App.Rotation(App.Vector(0, 0, 1), 180.0).multiply(App.Rotation(App.Vector(1, 0, 0), 90.0))
trans_coxa = App.Vector(74.70, -6.50, -15.25)
p_coxa = App.Placement(trans_coxa, rot_c)
make_link("Coxa_Bracket", "1. Coxa Bracket (3D Printed)", doc_coxa.Coxa_Bracket, p_coxa, (0.15, 0.65, 0.45))

# Organic Monolithic Femur with Encapsulated ADS1115 ADC & Cover (Links to femur.FCStd)
p_femur = App.Placement(App.Vector(56.50, 0.00, 0.00), App.Rotation())
make_link("Femur_Body", "4a. Femur Housing (Organic Double-Wrench, PETG)", doc_femur.Femur_Body, p_femur, (0.10, 0.45, 0.85))
make_link("Femur_Cover", "4b. Femur ADC Chamber Cover (PETG)", doc_femur.Femur_Cover, p_femur, (0.18, 0.22, 0.30))
make_link("Femur_ADS1115", "5. Encapsulated Leg ADC (ADS1115 0x48)", doc_femur.ADS1115_Board, p_femur, (0.88, 0.38, 0.10))

# Monolithic Tibia v2 (Claw + Integrated 30 mm Servo Cage & Counter-Bearing Seat, links to tibia_v2.FCStd)
theta = math.radians(50.0)
c = math.cos(theta)
s = math.sin(theta)
tibia_mat = App.Matrix(-c, s, 0, 156.50,  0, 0, 1, 2.00,   s, c, 0, 0.00,  0, 0, 0, 1.0)
make_link("Tibia_v2", "7. Tibia v2 (Monolithic Claw + Servo Cage, PETG)", doc_tibia.Tibia_v2, App.Placement(tibia_mat), (0.95, 0.50, 0.10))

# -------------------------------------------------------------
# 2. Actuators (3x Servos linked to servo_nr645.FCStd)
# -------------------------------------------------------------
# Coxa Servo:
rot_servo_in_bracket = App.Rotation(App.Vector(1, 0, 0), -90.0)
local_coxa_servo = App.Placement(App.Vector(74.70, 43.50, 9.00), rot_servo_in_bracket)
p_c_servo = p_coxa.multiply(local_coxa_servo)
make_link("Coxa_Servo", "2. Coxa Servo (Torcster NR-645)", doc_servo.Servo_Complete, p_c_servo, (0.28, 0.30, 0.36))

# Femur Servo:
local_f_servo = App.Placement(App.Vector(18.20, 15.25, 27.30), App.Rotation())
p_f_servo = p_coxa.multiply(local_f_servo)
make_link("Femur_Servo", "3. Femur Servo (Torcster NR-645)", doc_servo.Servo_Complete, p_f_servo, (0.28, 0.30, 0.36))

# Tibia Servo:
rot_k1 = App.Rotation(App.Vector(0, 1, 0), 50.0)
rot_k2 = App.Rotation(App.Vector(1, 0, 0), -90.0)
rot_knee = rot_k1.multiply(rot_k2)
p_t_servo = App.Placement(App.Vector(156.50, 20.80, 0.00), rot_knee)
make_link("Tibia_Servo", "6. Tibia Servo (Torcster NR-645)", doc_servo.Servo_Complete, p_t_servo, (0.28, 0.30, 0.36))

# -------------------------------------------------------------
# 3. Hardware (Fasteners & Bearings)
# -------------------------------------------------------------
rot_down_posz = App.Rotation(App.Vector(1, 0, 0), 180.0)
rot_down_negz = App.Rotation()
rot_negy_posz = App.Rotation(App.Vector(1, 0, 0), 90.0)
rot_negy_negz = App.Rotation(App.Vector(1, 0, 0), -90.0)

# A. Chassis Pivot Bearing Set (Vertical axis at X=0.00, Y=2.50 along -Z)
make_link("Chassis_Washer",  "Chassis Shim Washer (s0.3)",      doc_w.Passscheibe_M4,      App.Placement(App.Vector(0, 2.50, -10.95), rot_down_posz))
make_link("Chassis_Bearing", "Chassis Ball Bearing (D8 H3)",    doc_b.Kugellager_6x3x4,    App.Placement(App.Vector(0, 2.50, -12.25), rot_down_posz))
make_link("Chassis_Nut",     "Chassis M4 Hex Nut (SW7)",         doc_n.M4_Mutter,           App.Placement(App.Vector(0, 2.50, -15.25), rot_down_posz))
make_link("Chassis_Screw",   "Chassis M4 Countersunk Screw",     doc_s.M4_Senkkopfschraube, App.Placement(App.Vector(0, 2.50, -9.25),  rot_down_negz))

# B. Femur Pivot Bearing Set (Horizontal axis at X=56.50, Z=0.00 along -Y; Option A: internal M4 nut, external M4 screw)
make_link("Femur_Washer",  "Femur Shim Washer (s0.3)",      doc_w.Passscheibe_M4,      App.Placement(App.Vector(56.50, -21.00, 0.00), rot_negy_posz))
make_link("Femur_Bearing", "Femur Ball Bearing (D8 H3)",    doc_b.Kugellager_6x3x4,    App.Placement(App.Vector(56.50, -21.65, 0.00), rot_negy_posz))
make_link("Femur_Nut",     "Femur M4 Hex Nut (SW7)",         doc_n.M4_Mutter,           App.Placement(App.Vector(56.50, -18.00, 0.00), rot_negy_posz))
make_link("Femur_Screw",   "Femur M4 Countersunk Screw",     doc_s.M4_Senkkopfschraube, App.Placement(App.Vector(56.50, -27.20, 0.00), rot_negy_posz))

# C. Knee Pivot Bearing Set (Horizontal axis at X=156.50, Z=0.00 along -Y; Option A: internal M4 nut, external M4 screw)
make_link("Knee_Washer",  "Knee Shim Washer (s0.3)",      doc_w.Passscheibe_M4,      App.Placement(App.Vector(156.50, -21.00, 0.00), rot_negy_posz))
make_link("Knee_Bearing", "Knee Ball Bearing (D8 H3)",    doc_b.Kugellager_6x3x4,    App.Placement(App.Vector(156.50, -21.65, 0.00), rot_negy_posz))
make_link("Knee_Nut",     "Knee M4 Hex Nut (SW7)",         doc_n.M4_Mutter,           App.Placement(App.Vector(156.50, -18.00, 0.00), rot_negy_posz))
make_link("Knee_Screw",   "Knee M4 Countersunk Screw",     doc_s.M4_Senkkopfschraube, App.Placement(App.Vector(156.50, -27.20, 0.00), rot_negy_posz))

doc.recompute()
doc.save()

# Export STEP & STL
asm_part.Shape.exportStep(step_path)
asm_part.Shape.exportStl(stl_path)
print("Updated STEP and STL files for custom/v2/leg_assembly!")

for d in list(App.listDocuments().values()):
    App.closeDocument(d.Name)

print("--- Leg Assembly v2 Completed Successfully ---")
