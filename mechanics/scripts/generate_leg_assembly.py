import math
import FreeCAD as App
import Part

print("--- Generating Clean Modular Leg Assembly with Hardware Library Links ---")

doc_name = "leg_assembly"
models_dir = "/home/bjoern/Workspace/Hexapods/lasius/mechanics/models"
hw_dir = f"{models_dir}/hardware"
fcstd_path = f"{models_dir}/leg_assembly.FCStd"
step_path = "/home/bjoern/Workspace/Hexapods/lasius/mechanics/export/step/leg_assembly.step"
stl_path = "/home/bjoern/Workspace/Hexapods/lasius/mechanics/export/stl/leg_assembly.stl"

try:
    App.closeDocument(doc_name)
except Exception:
    pass

doc = App.newDocument(doc_name)
doc.saveAs(fcstd_path)

# Open all master part documents
doc_coxa = App.openDocument(f"{models_dir}/coxa_bracket.FCStd")
doc_femur = App.openDocument(f"{models_dir}/femur_plate.FCStd")
doc_tibia = App.openDocument(f"{models_dir}/tibia.FCStd")
doc_spacer = App.openDocument(f"{models_dir}/spacer_14x50.FCStd")
doc_servo = App.openDocument(f"{models_dir}/servo_nr645.FCStd")
doc_foot = App.openDocument(f"{models_dir}/tibia_servo_foot.FCStd")

# Open hardware library documents
doc_b = App.openDocument(f"{hw_dir}/bearing_684_6x3.FCStd")
doc_w = App.openDocument(f"{hw_dir}/washer_m4_shim.FCStd")
doc_n = App.openDocument(f"{hw_dir}/nut_m4_hex.FCStd")
doc_s = App.openDocument(f"{hw_dir}/screw_m4_countersunk.FCStd")

# Main Assembly Container
asm_part = doc.addObject("App::Part", "Leg_Assembly")
asm_part.Label = "Lasius Leg Assembly (Modular Subassembly)"
for o in asm_part.Origin.OutList:
    if hasattr(o, "Visibility"):
        o.Visibility = False
asm_part.Origin.Visibility = False
asm_part.Visibility = True

# Helper function
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

# Femur Side Plates (2x Links to femur_plate.FCStd, 51.3 mm inner spacing)
femur_1_mat = App.Matrix(1, 0, 0, 56.50,  0, 0, -1, 31.30,  0, 1, 0, 0.00,  0, 0, 0, 1.0)
make_link("Femur_Plate_Front", "4a. Femur Plate Front (2mm)", doc_femur.FemurPlate, App.Placement(femur_1_mat), (0.10, 0.45, 0.85))

femur_2_mat = App.Matrix(1, 0, 0, 56.50,  0, 0, 1, -24.00,  0, -1, 0, 0.00,  0, 0, 0, 1.0)
make_link("Femur_Plate_Rear", "4b. Femur Plate Rear (2mm)", doc_femur.FemurPlate, App.Placement(femur_2_mat), (0.10, 0.45, 0.85))

# Femur Spacers (2x Links to spacer_14x50.FCStd, L = 51.3 mm from Y = -22.00 to +29.30)
rot_spacer = App.Rotation(App.Vector(1, 0, 0), -90.0)
make_link("Femur_Spacer_1", "5a. Standoff Pillar 1 (D14 L51.3)", doc_spacer.SpacerRod, App.Placement(App.Vector(91.50, -22.00, 0.00), rot_spacer), (0.08, 0.35, 0.68))
make_link("Femur_Spacer_2", "5b. Standoff Pillar 2 (D14 L51.3)", doc_spacer.SpacerRod, App.Placement(App.Vector(121.50, -22.00, 0.00), rot_spacer), (0.08, 0.35, 0.68))

# Tibia Servo Foot (Links to tibia_servo_foot.FCStd, outer bottom at Y = -21.00)
theta = math.radians(50.0)
c = math.cos(theta)
s = math.sin(theta)
foot_mat = App.Matrix(c, -s, 0, 156.50,  0, 0, 1, -21.00,  -s, -c, 0, 0.00,  0, 0, 0, 1.0)
make_link("Tibia_Servo_Foot", "7. Tibia Servo Foot (3D Printed)", doc_foot.Servo_Foot, App.Placement(foot_mat), (0.78, 0.36, 0.05))

# Tibia Claw (Links to tibia.FCStd, flush under Tibia_Servo mounting tabs at Y = +2.00 .. +9.00)
tibia_mat = App.Matrix(-c, s, 0, 156.50,  0, 0, 1, 2.00,   s, c, 0, 0.00,  0, 0, 0, 1.0)
make_link("Tibia", "8. Tibia Sickle Claw (7mm)", doc_tibia.Tibia_Plate, App.Placement(tibia_mat), (0.95, 0.50, 0.10))

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
# Bearing (D8 H3) recessed flush inside Coxa_Bracket rail (Z = -12.25 .. -15.25), only Nut outside (Z = -15.25 .. -18.45)
make_link("Chassis_Washer",  "Chassis Shim Washer (s0.3)",      doc_w.Passscheibe_M4,      App.Placement(App.Vector(0, 2.50, -10.95), rot_down_posz))
make_link("Chassis_Bearing", "Chassis Ball Bearing (D8 H3)",    doc_b.Kugellager_6x3x4,    App.Placement(App.Vector(0, 2.50, -12.25), rot_down_posz))
make_link("Chassis_Nut",     "Chassis M4 Hex Nut (SW7)",         doc_n.M4_Mutter,           App.Placement(App.Vector(0, 2.50, -15.25), rot_down_posz))
make_link("Chassis_Screw",   "Chassis M4 Countersunk Screw",     doc_s.M4_Senkkopfschraube, App.Placement(App.Vector(0, 2.50, -9.25),  rot_down_negz))

# B. Femur Pivot Bearing Set (Horizontal axis at X=56.50, Z=0.00 along -Y)
make_link("Femur_Washer",  "Femur Shim Washer (s0.3)",      doc_w.Passscheibe_M4,      App.Placement(App.Vector(56.50, -21.00, 0.00), rot_negy_posz))
make_link("Femur_Bearing", "Femur Ball Bearing (D8 H3)",    doc_b.Kugellager_6x3x4,    App.Placement(App.Vector(56.50, -21.00, 0.00), rot_negy_posz))
make_link("Femur_Nut",     "Femur M4 Hex Nut (SW7)",         doc_n.M4_Mutter,           App.Placement(App.Vector(56.50, -24.00, 0.00), rot_negy_posz))
make_link("Femur_Screw",   "Femur M4 Countersunk Screw",     doc_s.M4_Senkkopfschraube, App.Placement(App.Vector(56.50, -18.00, 0.00), rot_negy_negz))

# C. Knee Pivot Bearing Set (Horizontal axis at X=156.50, Z=0.00 along -Y)
make_link("Knee_Washer",  "Knee Shim Washer (s0.3)",      doc_w.Passscheibe_M4,      App.Placement(App.Vector(156.50, -21.00, 0.00), rot_negy_posz))
make_link("Knee_Bearing", "Knee Ball Bearing (D8 H3)",    doc_b.Kugellager_6x3x4,    App.Placement(App.Vector(156.50, -21.00, 0.00), rot_negy_posz))
make_link("Knee_Nut",     "Knee M4 Hex Nut (SW7)",         doc_n.M4_Mutter,           App.Placement(App.Vector(156.50, -24.00, 0.00), rot_negy_posz))
make_link("Knee_Screw",   "Knee M4 Countersunk Screw",     doc_s.M4_Senkkopfschraube, App.Placement(App.Vector(156.50, -18.00, 0.00), rot_negy_negz))

doc.recompute()
doc.save()

# Export STEP & STL
asm_part.Shape.exportStep(step_path)
asm_part.Shape.exportStl(stl_path)
print("Updated STEP and STL files!")

for d in list(App.listDocuments().values()):
    App.closeDocument(d.Name)

print("--- Modular Leg Assembly with Hardware Library Completed Successfully ---")
