#!/usr/bin/env python3
"""
Generate Lasius Leg Assemblies v2 (Left & Right Symmetrical Legs)
=================================================================
Generates:
1. custom/v2/leg_assembly.FCStd       (Left Legs: FL, ML, RL)
2. custom/v2/leg_right_assembly.FCStd (Right Legs: FR, MR, RR)
   - Symmetrical layout (all servo horns face forward towards -X in body_assembly)
   - Custom 3D-printed parts (Coxa, Femur_Body, Femur_Cover, Tibia_Body, Tibia_Cover, Tibia_Rocker)
     are mirrored across the leg sagittal plane (Y_leg -> -Y_leg)
   - All COTS parts (Servos, ADS1115, Microswitch, Spring, Bearings, Fasteners) are
     100% unmirrored real COTS parts (ScaleVector = 1, 1, 1)!
"""

import math
import os
import sys
import zipfile
import xml.etree.ElementTree as ET
import FreeCAD as App
import Part

print("--- Generating Lasius Leg Assemblies v2 (Left & Right with Unmirrored COTS) ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
sys.path.append(f"{repo_root}/hardware/mechanics/scripts/v2")
import generate_tibia as gt
models_dir = f"{repo_root}/hardware/mechanics/models"
v2_parts_dir = f"{models_dir}/custom/v2/parts"
v2_asm_dir = f"{models_dir}/custom/v2"
hw_dir = f"{models_dir}/cots"

export_step_dir = f"{repo_root}/hardware/mechanics/export/step/custom/v2"
export_stl_dir = f"{repo_root}/hardware/mechanics/export/stl/custom/v2"
os.makedirs(v2_asm_dir, exist_ok=True)
os.makedirs(export_step_dir, exist_ok=True)
os.makedirs(export_stl_dir, exist_ok=True)

# Open all master part documents
doc_coxa = App.openDocument(f"{v2_parts_dir}/coxa/coxa.FCStd")
doc_femur_asm = App.openDocument(f"{v2_asm_dir}/femur_assembly.FCStd")
doc_tibia_asm = App.openDocument(f"{v2_asm_dir}/tibia_assembly.FCStd")
doc_femur = App.openDocument(f"{v2_parts_dir}/femur/femur.FCStd")
doc_f_cover = App.openDocument(f"{v2_parts_dir}/femur/femur_cover.FCStd")
doc_ads = App.openDocument(f"{hw_dir}/ads1115_board.FCStd")
doc_tibia = App.openDocument(f"{v2_parts_dir}/tibia/tibia.FCStd")
doc_t_cover = App.openDocument(f"{v2_parts_dir}/tibia/tibia_cover.FCStd")
doc_tarsus = App.openDocument(f"{v2_parts_dir}/tarsus/tarsus.FCStd")
doc_tarsus_shoe = App.openDocument(f"{v2_parts_dir}/tarsus/tarsus_shoe.FCStd")
doc_sw = App.openDocument(f"{hw_dir}/microswitch_subminiature.FCStd")
doc_sp = App.openDocument(f"{hw_dir}/compression_spring_4x12.FCStd")
doc_servo = App.openDocument(f"{hw_dir}/servo_nr645.FCStd")

# Open hardware library documents
doc_b = App.openDocument(f"{hw_dir}/bearing_684_6x3.FCStd")
doc_w = App.openDocument(f"{hw_dir}/washer_m4_shim.FCStd")
doc_n = App.openDocument(f"{hw_dir}/nut_m4_hex.FCStd")
doc_n_low = App.openDocument(f"{hw_dir}/nut_m4_din439.FCStd")
doc_s = App.openDocument(f"{hw_dir}/screw_m4_countersunk.FCStd")
doc_s_m2 = App.openDocument(f"{hw_dir}/screw_m2_button_head.FCStd")
doc_s_m2_cs = App.openDocument(f"{hw_dir}/screw_m2_countersunk.FCStd")
doc_ins_m2 = App.openDocument(f"{hw_dir}/insert_m2_ruthex.FCStd")

# Rotations
rot_c = App.Rotation(App.Vector(0, 0, 1), 180.0).multiply(App.Rotation(App.Vector(1, 0, 0), 90.0))
rot_down_posz = App.Rotation(App.Vector(1, 0, 0), 180.0)
rot_down_negz = App.Rotation()
rot_negy_posz = App.Rotation(App.Vector(1, 0, 0), 90.0)
rot_negy_negz = App.Rotation(App.Vector(1, 0, 0), -90.0)

# Standard stance pose: Profil B (Authentic Ant Stance)
# Femur elevated by alpha = 25.0 deg upward, Knee bent down by theta = 80.0 deg relative to Femur
# Effective Tibia descent angle to horizontal: theta_leg = theta - alpha = 55.0 deg
alpha_deg = 25.0
theta_deg = 80.0
theta_leg_deg = theta_deg - alpha_deg  # 55.0 deg

alpha = math.radians(alpha_deg)
theta_leg = math.radians(theta_leg_deg)
c_a = math.cos(alpha)
s_a = math.sin(alpha)

# Femur pivot is at X = 56.50, Y = 0.00, Z = 0.00.
# Femur length is 100.00 mm.
# Knee pivot axis in leg coordinate frame:
kx = 56.50 + 100.00 * c_a  # 147.130779 mm
kz = 100.00 * s_a           # 42.261826 mm


def make_link(doc, parent, name, label, target_obj, placement, color=None, transparency=0, scale=None):
    lnk = doc.addObject("App::Link", name)
    lnk.setLink(target_obj)
    lnk.Label = label
    lnk.Placement = placement
    if scale is not None:
        lnk.ScaleVector = scale
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
        if transparency > 0:
            vo.Transparency = transparency
    return lnk


def check_leg_collisions(asm_part, title):
    print(f"--- Checking Pairwise 3D B-Rep Collisions for {title} ---")
    leaf_items = []

    def collect_leaves(obj, parent_pl=App.Placement()):
        pl = parent_pl.multiply(obj.Placement)
        for child in getattr(obj, "Group", []):
            if child.TypeId == "App::Part":
                collect_leaves(child, pl)
            elif hasattr(child, "Shape") and not child.Shape.isNull():
                sh = child.Shape.copy()
                sh.Placement = pl.multiply(sh.Placement)
                leaf_items.append((f"{obj.Name}.{child.Name}", sh))

    collect_leaves(asm_part)
    max_coll = 0.0
    for i in range(len(leaf_items)):
        for j in range(i + 1, len(leaf_items)):
            n1, s1 = leaf_items[i]
            n2, s2 = leaf_items[j]
            # Skip internal 25T spline press-fit overlap between COTS Servo_Body and Servo_Horn
            base1, leaf1 = n1.rsplit(".", 1)
            base2, leaf2 = n2.rsplit(".", 1)
            if base1 == base2 and (
                {leaf1, leaf2} == {"Femur_Servo_Body", "Femur_Servo_Horn"}
                or {leaf1, leaf2} == {"Knee_Servo_Body", "Knee_Servo_Horn"}
            ):
                continue
            if s1.BoundBox.intersect(s2.BoundBox):
                v = s1.common(s2).Volume
                if v > 1e-4:
                    print(f"  ❌ COLLISION {n1} <-> {n2}: {v:.4f} mm^3")
                    max_coll = max(max_coll, v)
    if max_coll <= 1e-4:
        print(f"  ✅ ZERO COLLISIONS in {title} (0.0000 mm^3)!")
    return max_coll


# =============================================================================
# 1. Generate Left Leg Assembly: custom/v2/leg_assembly.FCStd
# =============================================================================
fcstd_left = f"{v2_asm_dir}/leg_assembly.FCStd"

try:
    App.closeDocument("leg_assembly")
except Exception:
    pass

doc_l = App.newDocument("leg_assembly")
doc_l.saveAs(fcstd_left)

asm_l = doc_l.addObject("App::Part", "Leg_Assembly_v2")
asm_l.Label = "Lasius Leg Assembly v2 Left (FL, ML, RL)"
for o in asm_l.Origin.OutList:
    if hasattr(o, "Visibility"):
        o.Visibility = False
asm_l.Origin.Visibility = False
asm_l.Visibility = True

# 1. Structural Parts & Subassemblies
p_coxa_l = App.Placement(App.Vector(74.70, -6.50, -15.25), rot_c)
make_link(doc_l, asm_l, "Coxa", "1. Coxa (Monolithic Joint Segment, PETG)", doc_coxa.Coxa, p_coxa_l, (0.15, 0.65, 0.45))

rot_femur_l = App.Rotation(App.Vector(0, 1, 0), -alpha_deg)
p_femur_l = App.Placement(App.Vector(56.50, 0.00, 0.00), rot_femur_l)
make_link(
    doc_l,
    asm_l,
    "Femur_Assembly",
    "4. Femur Subassembly v2 (Monolithic Bone + Encapsulated ADC & Canopy)",
    doc_femur_asm.Femur_Assembly_v2,
    p_femur_l,
)

# Knee pivot bore in Tibia_Body is at (18.20, 15.25, 0.00).
# In standard stance (theta_leg = 55 deg downward bend around Y_leg):
rot_tibia_l = App.Rotation(0.0, theta_leg_deg, 90.0)
v_bore_l = rot_tibia_l.multVec(App.Vector(18.20, 15.25, 0.0))
p_tibia_l = App.Placement(App.Vector(kx - v_bore_l.x, 11.50 - v_bore_l.y, kz - v_bore_l.z), rot_tibia_l)
make_link(
    doc_l,
    asm_l,
    "Tibia_Assembly",
    "7. Tibia Subassembly v2 (Monocoque + Kufe Foot Sensor + Knee Servo)",
    doc_tibia_asm.getObject("Tibia_Assembly"),
    p_tibia_l,
)

# 2. Actuators (Coxa Servo at Y_c = 42.75 mm -> Z_leg = 27.50 mm, horn top at Z_leg = 36.00 mm = Z_world 53.25 mm)
rot_servo_in_bracket = App.Rotation(App.Vector(1, 0, 0), -90.0)
local_coxa_servo = App.Placement(App.Vector(74.70, 42.75, 9.00), rot_servo_in_bracket)
p_c_servo_l = p_coxa_l.multiply(local_coxa_servo)
make_link(doc_l, asm_l, "Coxa_Servo", "2. Coxa Servo (Torcster NR-645)", doc_servo.Servo_Complete, p_c_servo_l, (0.28, 0.30, 0.36))

local_f_servo = App.Placement(App.Vector(18.20, 15.25, 27.30), App.Rotation())
p_f_servo_l = p_coxa_l.multiply(local_f_servo)
p_f_horn_l = p_f_servo_l.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation(App.Vector(0, 0, 1), -alpha_deg)))
make_link(doc_l, asm_l, "Femur_Servo_Body", "3a. Femur Servo Body (Torcster NR-645)", doc_servo.Servo_Body, p_f_servo_l, (0.28, 0.30, 0.36))
make_link(doc_l, asm_l, "Femur_Servo_Horn", "3b. Femur Servo Horn (D25 BCD16, aligned to Femur)", doc_servo.Servo_Horn, p_f_horn_l, (0.75, 0.76, 0.78))

# 3. Hardware (Fasteners & Bearings)
# A. Chassis Pivot Bearing Set (Vertical axis at X=0.00, Y=+2.50 along -Z):
#    - Screw starts inside Coxa foot at Z_leg = -11.45 mm
#    - Shim washer in Coxa underside recess at Z_leg in [-15.25, -14.95]
#    - Ball bearing inside Body_Bottom bore at Z_leg in [-18.25, -15.25] (Z_world in [-1.00, +2.00])
#    - Counter-locked from below by M4 DIN 439 nut at Z_leg in [-20.50, -18.30]
make_link(doc_l, asm_l, "Chassis_Washer",  "Chassis Shim Washer (s0.3)",          doc_w.Passscheibe_M4,       App.Placement(App.Vector(0, 2.50, -14.95), rot_down_posz))
make_link(doc_l, asm_l, "Chassis_Bearing", "Chassis Ball Bearing (D8 H3)",        doc_b.Kugellager_6x3x4,     App.Placement(App.Vector(0, 2.50, -15.25), rot_down_posz))
make_link(doc_l, asm_l, "Chassis_Nut",     "Chassis M4 Counter-Lock Nut (DIN439)", doc_n_low.M4_Mutter_DIN439, App.Placement(App.Vector(0, 2.50, -18.30), rot_down_posz))
make_link(doc_l, asm_l, "Chassis_Screw",   "Chassis M4 Countersunk Screw",        doc_s.M4_Senkkopfschraube,  App.Placement(App.Vector(0, 2.50, -11.45), rot_down_negz))

# B. Femur Pivot Bearing Set (Horizontal axis at X=56.50, Z=0.00 along -Y)
make_link(doc_l, asm_l, "Femur_Washer",  "Femur Shim Washer (s0.3)",            doc_w.Passscheibe_M4,       App.Placement(App.Vector(56.50, -21.00, 0.00), rot_negy_posz))
make_link(doc_l, asm_l, "Femur_Bearing", "Femur Ball Bearing (D8 H3)",          doc_b.Kugellager_6x3x4,     App.Placement(App.Vector(56.50, -21.65, 0.00), rot_negy_posz))
make_link(doc_l, asm_l, "Femur_Nut",     "Femur M4 Low-Profile Nut (DIN 439)",  doc_n_low.M4_Mutter_DIN439, App.Placement(App.Vector(56.50, -20.20, 0.00), rot_negy_negz))
make_link(doc_l, asm_l, "Femur_Screw",   "Femur M4 Countersunk Screw",          doc_s.M4_Senkkopfschraube,  App.Placement(App.Vector(56.50, -28.00, 0.00), rot_negy_posz))

# C. Knee Pivot Bearing Set (Horizontal axis at X=kx, Z=kz along -Y)
rot_knee_nut_l = rot_negy_negz.multiply(App.Rotation(App.Vector(0, 0, 1), theta_leg_deg))
make_link(doc_l, asm_l, "Knee_Washer",  "Knee Shim Washer (s0.3)",            doc_w.Passscheibe_M4,       App.Placement(App.Vector(kx, -21.00, kz), rot_negy_posz))
make_link(doc_l, asm_l, "Knee_Bearing", "Knee Ball Bearing (D8 H3)",          doc_b.Kugellager_6x3x4,     App.Placement(App.Vector(kx, -21.65, kz), rot_negy_posz))
make_link(doc_l, asm_l, "Knee_Nut",     "Knee M4 Low-Profile Nut (DIN 439)",  doc_n_low.M4_Mutter_DIN439, App.Placement(App.Vector(kx, -20.20, kz), rot_knee_nut_l))
make_link(doc_l, asm_l, "Knee_Screw",   "Knee M4 Countersunk Screw",          doc_s.M4_Senkkopfschraube,  App.Placement(App.Vector(kx, -28.00, kz), rot_negy_posz))

# D. 8x M2 x 5 mm Servo Horn Screws (ISO 7380) fastening Femur Front Jaw to Hip & Knee Servo Horns (Ø16 mm BCD)
#    In Femur local coords: counterbore seat at Y = +31.50 mm, shank enters along -Y into horn (Y = 29.30..26.80).
#    RotX(-90°) maps screw local +Z (head) -> +Y_femur, local -Z (shank) -> -Y_femur!
COLOR_STEEL = (0.78, 0.80, 0.84)
rot_m2_fem_l = App.Rotation(App.Vector(1, 0, 0), -90.0)
for grp_name, grp_lbl, px_fem, prefix in [
    ("Hip_Horn_Screws",  "Hip Servo Horn Screws (4x M2x5 ISO 7380)",  0.00,   "Hip_Horn_M2"),
    ("Knee_Horn_Screws", "Knee Servo Horn Screws (4x M2x5 ISO 7380)", 100.00, "Knee_Horn_M2"),
]:
    grp = doc_l.addObject("App::Part", grp_name)
    grp.Label = grp_lbl
    for o in grp.Origin.OutList:
        if hasattr(o, "Visibility"):
            o.Visibility = False
    grp.Origin.Visibility = False
    grp.Visibility = True
    asm_l.addObject(grp)
    for idx, (dx, dz) in enumerate([(8.0, 0.0), (-8.0, 0.0), (0.0, 8.0), (0.0, -8.0)], start=1):
        p_scr = p_femur_l.multiply(App.Placement(App.Vector(px_fem + dx, 31.52, dz), rot_m2_fem_l))
        make_link(doc_l, grp, f"{prefix}_{idx}", f"{prefix}_{idx} (ISO 7380 M2x5)", doc_s_m2.M2_Linsenkopfschraube, p_scr, COLOR_STEEL)

doc_l.recompute()
doc_l.save()

# Assemblies are logical structures, not exported to STEP/STL (never manufactured in one piece)
print(f"✔ Saved Left Leg Assembly: {fcstd_left}")
check_leg_collisions(asm_l, "leg_assembly.FCStd (Left)")

# =============================================================================
# 2. Generate Right Leg Assembly: custom/v2/leg_right_assembly.FCStd
#    (Mirrored Custom 3D-Printed Parts + Unmirrored Real COTS Parts!)
# =============================================================================
fcstd_right = f"{v2_asm_dir}/leg_right_assembly.FCStd"

try:
    App.closeDocument("leg_right_assembly")
except Exception:
    pass

doc_r = App.newDocument("leg_right_assembly")
doc_r.saveAs(fcstd_right)

asm_r = doc_r.addObject("App::Part", "Leg_Right_Assembly_v2")
asm_r.Label = "Lasius Leg Assembly v2 Right (FR, MR, RR - Mirrored Printed Parts, Unmirrored COTS)"
for o in asm_r.Origin.OutList:
    if hasattr(o, "Visibility"):
        o.Visibility = False
asm_r.Origin.Visibility = False
asm_r.Visibility = True

# 1. Coxa (Mirrored 3D-Printed Part: ScaleVector = (1, 1, -1) in local Coxa coords -> Y_leg negated!)
p_coxa_r = App.Placement(App.Vector(74.70, 6.50, -15.25), rot_c)
make_link(
    doc_r,
    asm_r,
    "Coxa",
    "1. Coxa Right (Mirrored Monolithic Joint Segment, PETG)",
    doc_coxa.Coxa,
    p_coxa_r,
    (0.15, 0.65, 0.45),
    scale=App.Vector(1.0, 1.0, -1.0),
)

# 2. Femur Subassembly Right (Mirrored Femur_Body & Femur_Cover, Unmirrored ADS1115_Board rotated 180 deg in XY!)
femur_part_r = doc_r.addObject("App::Part", "Femur_Assembly")
femur_part_r.Label = "4. Femur Subassembly v2 Right (Mirrored Bone & Canopy + Unmirrored ADC)"
femur_part_r.Placement = p_femur_l
for o in femur_part_r.Origin.OutList:
    if hasattr(o, "Visibility"):
        o.Visibility = False
femur_part_r.Origin.Visibility = False
femur_part_r.Visibility = True
asm_r.addObject(femur_part_r)

make_link(
    doc_r,
    femur_part_r,
    "Femur_Body",
    "1. Femur Monolithic Housing Right (Mirrored PETG)",
    doc_femur.Femur_Body,
    App.Placement(),
    (0.12, 0.35, 0.65),
    scale=App.Vector(1.0, -1.0, 1.0),
)
p_ads_r = App.Placement(App.Vector(50.00, -2.50, -4.80), App.Rotation(App.Vector(0, 0, 1), 180.0))
make_link(
    doc_r,
    femur_part_r,
    "ADS1115_Board",
    "2. Encapsulated Leg ADC (Unmirrored COTS ADS1115)",
    doc_ads.ADS1115_Board,
    p_ads_r,
    (0.04, 0.38, 0.88),
)
make_link(
    doc_r,
    femur_part_r,
    "Femur_Cover",
    "3. Femur Service Cover & Canopy Right (Mirrored Eisblau 55%)",
    doc_f_cover.Femur_Cover,
    App.Placement(),
    (0.85, 0.92, 0.98),
    transparency=55,
    scale=App.Vector(1.0, -1.0, 1.0),
)

# 4x Unmirrored Ruthex M2 Brass Inserts & 4x DIN 7991 M2x6 Cover Screws on Right Femur (Y mirrored -> Y_mid = -2.50!)
grp_f_ins_r = doc_r.addObject("App::Part", "Femur_Cover_Inserts")
grp_f_ins_r.Label = "4. 4x Ruthex M2 Brass Heat-Set Inserts Right (Unmirrored COTS)"
for o in grp_f_ins_r.Origin.OutList:
    if hasattr(o, "Visibility"):
        o.Visibility = False
grp_f_ins_r.Origin.Visibility = False
grp_f_ins_r.Visibility = True
femur_part_r.addObject(grp_f_ins_r)

grp_f_scr_r = doc_r.addObject("App::Part", "Femur_Cover_Screws")
grp_f_scr_r.Label = "5. 4x DIN 7991 M2 x 6 mm Cover Screws Right (Unmirrored COTS)"
for o in grp_f_scr_r.Origin.OutList:
    if hasattr(o, "Visibility"):
        o.Visibility = False
grp_f_scr_r.Origin.Visibility = False
grp_f_scr_r.Visibility = True
femur_part_r.addObject(grp_f_scr_r)

for idx, (sx, sy) in enumerate([(31.8, +11.3), (31.8, -16.3), (68.2, +11.3), (68.2, -16.3)], start=1):
    make_link(doc_r, grp_f_ins_r, f"Femur_Insert_M2_{idx}", f"Ruthex M2 Insert #{idx} Right (Brass)", doc_ins_m2.Ruthex_M2_Insert, App.Placement(App.Vector(sx, sy, 8.95), App.Rotation()), (0.85, 0.70, 0.20))
    make_link(doc_r, grp_f_scr_r, f"Femur_Screw_M2_{idx}", f"Cover Screw M2x6 #{idx} Right (DIN 7991)", doc_s_m2_cs.M2_Senkkopfschraube, App.Placement(App.Vector(sx, sy, 11.83), App.Rotation()), COLOR_STEEL)

# 3. Tibia Subassembly Right (Mirrored Tibia_Body, Tibia_Cover, Tibia_Rocker, Tibia_Shoe; Unmirrored Knee_Servo, Microswitch, Spring)
tibia_part_r = doc_r.addObject("App::Part", "Tibia_Assembly")
tibia_part_r.Label = "7. Tibia Subassembly v2 Right (Mirrored Monocoque + Unmirrored COTS)"
rot_tibia_r = App.Rotation(0.0, theta_leg_deg, 90.0)
v_bore_r = rot_tibia_r.multVec(App.Vector(18.20, 15.25, 0.0))
p_tibia_r = App.Placement(App.Vector(kx - v_bore_r.x, -11.50 - v_bore_r.y, kz - v_bore_r.z), rot_tibia_r)
tibia_part_r.Placement = p_tibia_r
for o in tibia_part_r.Origin.OutList:
    if hasattr(o, "Visibility"):
        o.Visibility = False
tibia_part_r.Origin.Visibility = False
tibia_part_r.Visibility = True
asm_r.addObject(tibia_part_r)

make_link(
    doc_r,
    tibia_part_r,
    "Tibia_Body",
    "1. Tibia v2 Monocoque Right (Mirrored PETG)",
    doc_tibia.Tibia_Body,
    App.Placement(),
    (0.22, 0.22, 0.24),
    scale=App.Vector(1.0, 1.0, -1.0),
)
p_k_servo_r = App.Placement(App.Vector(18.20, 15.25, 9.30), App.Rotation())
p_k_horn_r = p_k_servo_r.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation(App.Vector(0, 0, 1), theta_deg)))
make_link(
    doc_r,
    tibia_part_r,
    "Knee_Servo_Body",
    "2a. Knee Servo Body (Unmirrored Torcster NR-645 COTS)",
    doc_servo.Servo_Body,
    p_k_servo_r,
    (0.12, 0.12, 0.12),
)
make_link(
    doc_r,
    tibia_part_r,
    "Knee_Servo_Horn",
    "2b. Knee Servo Horn (D25 BCD16, aligned to Femur)",
    doc_servo.Servo_Horn,
    p_k_horn_r,
    (0.75, 0.76, 0.78),
)

# Foot Contact Sensor Subsystem (Right Mirrored Kinematics across Z=0 — Option 2c-V2)
p_tarsus_r = App.Placement(App.Vector(gt.TARSUS_PIV_X, gt.TARSUS_PIV_Y, -gt.Z_MID), App.Rotation())

make_link(
    doc_r,
    tibia_part_r,
    "Tarsus",
    "3. Bionic Curved Tarsus Lever Right (Mirrored PETG)",
    doc_tarsus.Tarsus,
    p_tarsus_r,
    (0.92, 0.45, 0.10),
    scale=App.Vector(1.0, 1.0, -1.0),
)
make_link(
    doc_r,
    tibia_part_r,
    "Tarsus_Shoe",
    "3b. Slip-On Bionic Spoon Shoe Right (Mirrored TPU/PETG)",
    doc_tarsus_shoe.Tarsus_Shoe,
    p_tarsus_r,
    (0.18, 0.58, 0.68),
    scale=App.Vector(1.0, 1.0, -1.0),
)

p_switch_r = App.Placement(App.Vector(gt.SW_ORIGIN.x, gt.SW_ORIGIN.y, -gt.Z_MID), gt.SW_ROT)
make_link(
    doc_r,
    tibia_part_r,
    "Microswitch",
    "4. Subminiature NC Microswitch (Unmirrored COTS)",
    doc_sw.Microswitch_Subminiature,
    p_switch_r,
    (0.15, 0.15, 0.15),
)

p_spring_r = App.Placement(App.Vector(gt.SPRING_X, gt.SPRING_FLOOR_Y + 0.05, -gt.Z_MID), App.Rotation())
make_link(
    doc_r,
    tibia_part_r,
    "Compression_Spring",
    "5. Stainless Preload Spring (Unmirrored COTS)",
    doc_sp.Compression_Spring,
    p_spring_r,
    (0.85, 0.85, 0.88),
)

make_link(
    doc_r,
    tibia_part_r,
    "Tibia_Cover",
    "6. Removable Service Cover Right (Mirrored PETG)",
    doc_t_cover.Tibia_Cover,
    App.Placement(),
    (0.15, 0.15, 0.18),
    scale=App.Vector(1.0, 1.0, -1.0),
)

# 7. Encapsulated Ø3x8.8 mm Hardened Stainless Dowel Pin (ISO 2338) Right
pin_obj_r = doc_r.addObject("Part::Feature", "Pivot_Pin_Assembly")
pin_obj_r.Label = "7. Encapsulated Ø3x8.8 mm Hardened Dowel Pin (ISO 2338) Right"
pin_obj_r.Shape = Part.makeCylinder(1.50, 8.80, App.Vector(gt.TARSUS_PIV_X, gt.TARSUS_PIV_Y, -13.42), App.Vector(0, 0, 1))
tibia_part_r.addObject(pin_obj_r)
if hasattr(pin_obj_r, "ViewObject") and pin_obj_r.ViewObject:
    try:
        pin_obj_r.ViewObject.ShapeColor = (0.85, 0.70, 0.20)
    except Exception:
        pass

# 8. 2x Ruthex M2 Brass Heat-Set Inserts + 2x DIN 7991 M2 x 6 mm Countersunk Cover Screws Right (Unmirrored COTS!)
grp_t_ins_r = doc_r.addObject("App::Part", "Tibia_Cover_Inserts")
grp_t_ins_r.Label = "8a. 2x Ruthex M2 Brass Heat-Set Inserts Right (Unmirrored COTS)"
for o in grp_t_ins_r.Origin.OutList:
    if hasattr(o, "Visibility"):
        o.Visibility = False
grp_t_ins_r.Origin.Visibility = False
grp_t_ins_r.Visibility = True
tibia_part_r.addObject(grp_t_ins_r)

grp_t_scr_r = doc_r.addObject("App::Part", "Tibia_Cover_Screws")
grp_t_scr_r.Label = "8b. 2x DIN 7991 M2 x 6 mm Flush Countersunk Cover Screws Right (Unmirrored COTS)"
for o in grp_t_scr_r.Origin.OutList:
    if hasattr(o, "Visibility"):
        o.Visibility = False
grp_t_scr_r.Origin.Visibility = False
grp_t_scr_r.Visibility = True
tibia_part_r.addObject(grp_t_scr_r)

rot_flip_z = App.Rotation(App.Vector(1, 0, 0), 180.0)
for idx, (bx, by) in enumerate(gt.COVER_SCREW_PTS, start=1):
    make_link(doc_r, grp_t_ins_r, f"Cover_Insert_M2_{idx}", f"Ruthex M2 Insert #{idx} Right (Brass)", doc_ins_m2.Ruthex_M2_Insert, App.Placement(App.Vector(bx, by, -12.15), rot_flip_z), (0.85, 0.70, 0.20))
    make_link(doc_r, grp_t_scr_r, f"Cover_Screw_M2_{idx}", f"Cover Screw M2x6 #{idx} Right (DIN 7991)", doc_s_m2_cs.M2_Senkkopfschraube, App.Placement(App.Vector(bx, by, -(gt.COVER_Z_MAX - 0.02)), rot_flip_z), COLOR_STEEL)

# 4. Actuators in Coxa (Unmirrored Real COTS Servos!)
p_c_servo_r = App.Placement(App.Vector(0.00, -2.50, 27.50), App.Rotation(App.Vector(0, 0, 1), 180.0))
make_link(doc_r, asm_r, "Coxa_Servo", "2. Coxa Servo (Unmirrored Torcster NR-645)", doc_servo.Servo_Complete, p_c_servo_r, (0.28, 0.30, 0.36))

rot_f_servo_r = App.Rotation(App.Vector(0, 0, 1), 180.0).multiply(App.Rotation(App.Vector(1, 0, 0), -90.0))
p_f_servo_r = App.Placement(App.Vector(56.50, -20.80, 0.00), rot_f_servo_r)
p_f_horn_r = p_f_servo_r.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation(App.Vector(0, 0, 1), alpha_deg)))
make_link(doc_r, asm_r, "Femur_Servo_Body", "3a. Femur Servo Body (Unmirrored Torcster NR-645)", doc_servo.Servo_Body, p_f_servo_r, (0.28, 0.30, 0.36))
make_link(doc_r, asm_r, "Femur_Servo_Horn", "3b. Femur Servo Horn (D25 BCD16, aligned to Femur)", doc_servo.Servo_Horn, p_f_horn_r, (0.75, 0.76, 0.78))

# 5. Joint Hardware (All Unmirrored Real COTS Fasteners & Bearings!)
make_link(doc_r, asm_r, "Chassis_Washer",  "Chassis Shim Washer (s0.3)",          doc_w.Passscheibe_M4,       App.Placement(App.Vector(0, -2.50, -14.95), rot_down_posz))
make_link(doc_r, asm_r, "Chassis_Bearing", "Chassis Ball Bearing (D8 H3)",        doc_b.Kugellager_6x3x4,     App.Placement(App.Vector(0, -2.50, -15.25), rot_down_posz))
make_link(doc_r, asm_r, "Chassis_Nut",     "Chassis M4 Counter-Lock Nut (DIN439)", doc_n_low.M4_Mutter_DIN439, App.Placement(App.Vector(0, -2.50, -18.30), rot_down_posz))
make_link(doc_r, asm_r, "Chassis_Screw",   "Chassis M4 Countersunk Screw",        doc_s.M4_Senkkopfschraube,  App.Placement(App.Vector(0, -2.50, -11.45), rot_down_negz))

make_link(doc_r, asm_r, "Femur_Washer",  "Femur Shim Washer (s0.3)",            doc_w.Passscheibe_M4,       App.Placement(App.Vector(56.50, 21.00, 0.00), rot_negy_negz))
make_link(doc_r, asm_r, "Femur_Bearing", "Femur Ball Bearing (D8 H3)",          doc_b.Kugellager_6x3x4,     App.Placement(App.Vector(56.50, 21.65, 0.00), rot_negy_negz))
make_link(doc_r, asm_r, "Femur_Nut",     "Femur M4 Low-Profile Nut (DIN 439)",  doc_n_low.M4_Mutter_DIN439, App.Placement(App.Vector(56.50, 20.20, 0.00), rot_negy_posz))
make_link(doc_r, asm_r, "Femur_Screw",   "Femur M4 Countersunk Screw",          doc_s.M4_Senkkopfschraube,  App.Placement(App.Vector(56.50, 28.00, 0.00), rot_negy_negz))

rot_knee_nut_r = rot_negy_posz.multiply(App.Rotation(App.Vector(0, 0, 1), -theta_leg_deg))
make_link(doc_r, asm_r, "Knee_Washer",  "Knee Shim Washer (s0.3)",            doc_w.Passscheibe_M4,       App.Placement(App.Vector(kx, 21.00, kz), rot_negy_negz))
make_link(doc_r, asm_r, "Knee_Bearing", "Knee Ball Bearing (D8 H3)",          doc_b.Kugellager_6x3x4,     App.Placement(App.Vector(kx, 21.65, kz), rot_negy_negz))
make_link(doc_r, asm_r, "Knee_Nut",     "Knee M4 Low-Profile Nut (DIN 439)",  doc_n_low.M4_Mutter_DIN439, App.Placement(App.Vector(kx, 20.20, kz), rot_knee_nut_r))
make_link(doc_r, asm_r, "Knee_Screw",   "Knee M4 Countersunk Screw",          doc_s.M4_Senkkopfschraube,  App.Placement(App.Vector(kx, 28.00, kz), rot_negy_negz))

# 6. 8x M2 x 5 mm Servo Horn Screws (ISO 7380) fastening Mirrored Right Femur Front Jaw (Y = -31.52 mm) to Hip & Knee Horns
#    RotX(+90°) maps screw local +Z (head) -> -Y_femur, local -Z (shank) -> +Y_femur (into horn at Y = -29.30..-26.80)!
rot_m2_fem_r = App.Rotation(App.Vector(1, 0, 0), 90.0)
for grp_name, grp_lbl, px_fem, prefix in [
    ("Hip_Horn_Screws",  "Hip Servo Horn Screws Right (4x M2x5 ISO 7380)",  0.00,   "Hip_Horn_M2"),
    ("Knee_Horn_Screws", "Knee Servo Horn Screws Right (4x M2x5 ISO 7380)", 100.00, "Knee_Horn_M2"),
]:
    grp = doc_r.addObject("App::Part", grp_name)
    grp.Label = grp_lbl
    for o in grp.Origin.OutList:
        if hasattr(o, "Visibility"):
            o.Visibility = False
    grp.Origin.Visibility = False
    grp.Visibility = True
    asm_r.addObject(grp)
    for idx, (dx, dz) in enumerate([(8.0, 0.0), (-8.0, 0.0), (0.0, 8.0), (0.0, -8.0)], start=1):
        p_scr = p_femur_l.multiply(App.Placement(App.Vector(px_fem + dx, -31.52, dz), rot_m2_fem_r))
        make_link(doc_r, grp, f"{prefix}_{idx}", f"{prefix}_{idx} (ISO 7380 M2x5)", doc_s_m2.M2_Linsenkopfschraube, p_scr, COLOR_STEEL)

doc_r.recompute()
doc_r.save()

# Assemblies are logical structures, not exported to STEP/STL (never manufactured in one piece)
print(f"✔ Saved Right Leg Assembly: {fcstd_right}")
check_leg_collisions(asm_r, "leg_right_assembly.FCStd (Right)")

for d in list(App.listDocuments().values()):
    try:
        App.closeDocument(d.Name)
    except Exception:
        pass

print("--- Leg Assemblies v2 (Left & Right) Completed Successfully ---")
sys.exit(0)
