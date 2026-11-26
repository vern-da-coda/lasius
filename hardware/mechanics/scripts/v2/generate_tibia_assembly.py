#!/usr/bin/env python3
"""
Generate Lasius Tibia v2 Canonical Subsystem Assembly (Option 2c-V2)
====================================================================
Canonical Output Paths (Hardware-as-Code 3-Tier Architecture):
- COTS Parts:
  * hardware/mechanics/models/cots/microswitch_subminiature.FCStd
  * hardware/mechanics/models/cots/compression_spring_4x12.FCStd
- Custom v2 Tibia Parts:
  * hardware/mechanics/models/custom/v2/parts/tibia/tibia.FCStd        (Tibia_Body)
  * hardware/mechanics/models/custom/v2/parts/tibia/tibia_cover.FCStd  (Tibia_Cover)
- Subassemblies referenced:
  * hardware/mechanics/models/custom/v2/tarsus_assembly.FCStd         (Tarsus_Assembly)
- Custom v2 Tibia Subassembly:
  * hardware/mechanics/models/custom/v2/tibia_assembly.FCStd           (Tibia_Assembly)
"""

import math
import os
import sys
import FreeCAD as App
import Part

DO_EXPORT = ("--export" in sys.argv)

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
sys.path.append(f"{repo_root}/hardware/mechanics/scripts/v2")
import generate_tibia as gt

print("--- Generating Lasius Tibia v2 Canonical Subsystem Assembly (Option 2c-V2) ---")

models_dir = f"{repo_root}/hardware/mechanics/models"
cots_dir = f"{models_dir}/cots"
v2_dir = f"{models_dir}/custom/v2"
parts_tibia_dir = f"{v2_dir}/parts/tibia"

export_step_parts = f"{repo_root}/hardware/mechanics/export/step/custom/v2/parts/tibia"
export_stl_parts = f"{repo_root}/hardware/mechanics/export/stl/custom/v2/parts/tibia"

os.makedirs(cots_dir, exist_ok=True)
os.makedirs(v2_dir, exist_ok=True)
os.makedirs(parts_tibia_dir, exist_ok=True)
if DO_EXPORT:
    os.makedirs(export_step_parts, exist_ok=True)
    os.makedirs(export_stl_parts, exist_ok=True)

# Colors (Style Guide §6)
COLOR_CFRP = (0.20, 0.22, 0.25)        # Anthracite / Carbon PETG body
COLOR_COVER = (0.15, 0.15, 0.18)       # Graphite service cover
COLOR_SERVO = (0.12, 0.12, 0.12)       # Matte black servo
COLOR_ORANGE = (0.92, 0.45, 0.10)      # Anodized orange tarsus lever
COLOR_SWITCH = (0.15, 0.15, 0.15)      # Matte black switch
COLOR_SPRING = (0.85, 0.85, 0.88)      # Stainless spring
COLOR_BRASS = (0.85, 0.70, 0.20)       # Brass / hardened dowel pin
COLOR_STEEL = (0.80, 0.80, 0.82)       # Steel fasteners

# =============================================================================
# 1. Load/Verify COTS: microswitch_subminiature.FCStd & compression_spring_4x12.FCStd
# =============================================================================
print("1. Loading COTS: microswitch_subminiature.FCStd & compression_spring_4x12.FCStd...")
for dname in ["microswitch_subminiature", "compression_spring_4x12"]:
    try:
        App.closeDocument(dname)
    except Exception:
        pass

fcstd_sw_path = f"{cots_dir}/microswitch_subminiature.FCStd"
fcstd_sp_path = f"{cots_dir}/compression_spring_4x12.FCStd"
doc_sw = App.openDocument(fcstd_sw_path)
obj_sw = doc_sw.Microswitch_Subminiature
doc_sp = App.openDocument(fcstd_sp_path)
obj_sp = doc_sp.Compression_Spring

# =============================================================================
# 2. Load Canonical Monolithic Tibia Body & Removable Service Cover
# =============================================================================
print("2. Loading Canonical Parts: tibia.FCStd & tibia_cover.FCStd...")
fcstd_mono_path = f"{parts_tibia_dir}/tibia.FCStd"
fcstd_cover_path = f"{parts_tibia_dir}/tibia_cover.FCStd"

for dname in ["tibia", "tibia_cover", "tarsus_assembly", "servo_nr645"]:
    try:
        App.closeDocument(dname)
    except Exception:
        pass

doc_mono = App.openDocument(fcstd_mono_path)
obj_mono = doc_mono.Tibia_Body
print(f"✔ Verified: {fcstd_mono_path} (Valid={obj_mono.Shape.isValid()}, Volume={obj_mono.Shape.Volume:.1f} mm3)")

doc_cover = App.openDocument(fcstd_cover_path)
obj_cover = doc_cover.Tibia_Cover
print(f"✔ Verified: {fcstd_cover_path} (Valid={obj_cover.Shape.isValid()}, Volume={obj_cover.Shape.Volume:.1f} mm3)")

# =============================================================================
# 3. Build Canonical Subsystem Assembly: custom/v2/tibia_assembly.FCStd
# =============================================================================
print("3. Building Canonical Subsystem Assembly: custom/v2/tibia_assembly.FCStd...")
doc_asm_name = "tibia_assembly"
try:
    App.closeDocument(doc_asm_name)
except Exception:
    pass
fcstd_asm_path = f"{v2_dir}/tibia_assembly.FCStd"
doc_asm = App.newDocument(doc_asm_name)
doc_asm.saveAs(fcstd_asm_path)

doc_servo = App.openDocument(f"{cots_dir}/servo_nr645.FCStd")
doc_tarsus_asm = App.openDocument(f"{v2_dir}/tarsus_assembly.FCStd")
doc_ins_m2 = App.openDocument(f"{cots_dir}/insert_m2_ruthex.FCStd")
doc_scr_m2 = App.openDocument(f"{cots_dir}/screw_m2_countersunk.FCStd")
doc_dowel = App.openDocument(f"{cots_dir}/dowel_pin_3x12.FCStd")

asm_part = doc_asm.addObject("App::Part", "Tibia_Assembly")
asm_part.Label = "Lasius Tibia v2 Subsystem Assembly (Option 2c-V2 Bionic NC Foot Sensor)"
for o in asm_part.Origin.OutList:
    if hasattr(o, "Visibility"):
        o.Visibility = False
asm_part.Origin.Visibility = False
asm_part.Visibility = True


def make_link(name, label, target_obj, placement, color=None, parent=asm_part):
    lnk = doc_asm.addObject("App::Link", name)
    lnk.setLink(target_obj)
    lnk.Label = label
    lnk.Placement = placement
    parent.addObject(lnk)
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


# 1. Monolithic Bionic Tibia Body
make_link("Tibia_Body", "1. Tibia v2 Bionic Monocoque (Option 2c-V2, PETG)", obj_mono, App.Placement(), COLOR_CFRP)

# 2. Knee Servo (Torcster NR-645) — Body fixed in Tibia cage + Horn clocked -80° to align BCD16 holes with Femur!
p_servo = App.Placement(App.Vector(gt.KNEE_X, gt.KNEE_Y, -9.30), App.Rotation(App.Vector(1, 0, 0), 180.0))
p_servo_horn = p_servo.multiply(App.Placement(App.Vector(0, 0, 0), App.Rotation(App.Vector(0, 0, 1), -80.0)))
make_link("Knee_Servo_Body", "2a. Knee Servo Body (Torcster NR-645 COTS)", doc_servo.Servo_Body, p_servo, COLOR_SERVO)
make_link("Knee_Servo_Horn", "2b. Knee Servo Horn (D25 BCD16, aligned to Femur)", doc_servo.Servo_Horn, p_servo_horn, (0.75, 0.76, 0.78))

# 3. Tarsus Subsystem Assembly (Origin at Pivot Axis -> direct clean translation!)
p_tarsus = App.Placement(App.Vector(gt.TARSUS_PIV_X, gt.TARSUS_PIV_Y, gt.Z_MID), App.Rotation())
make_link("Tarsus_Assembly", "3. Tarsus Subsystem Assembly (Curved Rocker + Bionic Shoe)", doc_tarsus_asm.Tarsus_Assembly, p_tarsus)

# 4. NC Microswitch (Omron D2FC-F-K with 100% straight unbent pins + 6 mm open solder room!)
make_link("Microswitch", "4. Subminiature NC Microswitch (Omron D2FC COTS)", obj_sw, gt.SW_PLACEMENT, COLOR_SWITCH)

# 5. Deep Belly Vertical Compression Spring (r = 41.5 mm lever arm!)
#    Spring COTS height is 11.30 mm along +Y; placed at Y = 4.95 -> Y in [4.95, 16.25] (0.05 mm gap to floor 4.90 & seat 16.30!)
p_spring = App.Placement(App.Vector(gt.SPRING_X, gt.SPRING_FLOOR_Y + 0.05, gt.Z_MID), App.Rotation())
make_link("Compression_Spring", "5. Stainless Preload Spring (Da=4.5, L=12 mm, r=41.5 mm)", obj_sp, p_spring, COLOR_SPRING)

# 6. Removable Form-Fit Service Cover
make_link("Tibia_Cover", "6. Removable Service Cover (Cheek B Form-Fit, PETG)", obj_cover, App.Placement(), COLOR_COVER)

# 7. Encapsulated Ø3x12 mm Hardened Stainless Dowel Pin (DIN 7 / ISO 2338, COTS App::Link)
make_link(
    "Pivot_Pin_Dowel",
    "Zylinderstift_3x12",
    doc_dowel.Dowel_Pin_3x12,
    App.Placement(App.Vector(gt.TARSUS_PIV_X, gt.TARSUS_PIV_Y, 9.02), App.Rotation()),
)

# 8. 2x Ruthex M2 Brass Heat-Set Inserts + 2x DIN 7991 M2 x 6 mm Flush Countersunk Screws (COTS App::Link)
grp_ins = doc_asm.addObject("App::Part", "Cover_Inserts")
grp_ins.Label = "8a. 2x Ruthex M2 Brass Heat-Set Inserts (COTS)"
for o in grp_ins.Origin.OutList:
    if hasattr(o, "Visibility"):
        o.Visibility = False
grp_ins.Origin.Visibility = False
grp_ins.Visibility = True
asm_part.addObject(grp_ins)

grp_scr = doc_asm.addObject("App::Part", "Cover_Screws")
grp_scr.Label = "8b. 2x DIN 7991 M2 x 6 mm Flush Countersunk Cover Screws (COTS)"
for o in grp_scr.Origin.OutList:
    if hasattr(o, "Visibility"):
        o.Visibility = False
grp_scr.Origin.Visibility = False
grp_scr.Visibility = True
asm_part.addObject(grp_scr)

for idx, (bx, by) in enumerate(gt.COVER_SCREW_PTS, start=1):
    make_link(
        f"Cover_Insert_M2_{idx}",
        f"Ruthex M2 Insert #{idx} (Brass)",
        doc_ins_m2.Ruthex_M2_Insert,
        App.Placement(App.Vector(bx, by, 12.15), App.Rotation()),
        COLOR_BRASS,
        parent=grp_ins,
    )
    make_link(
        f"Cover_Screw_M2_{idx}",
        f"Cover Screw M2x6 #{idx} (DIN 7991)",
        doc_scr_m2.M2_Senkkopfschraube,
        App.Placement(App.Vector(bx, by, gt.COVER_Z_MAX - 0.02), App.Rotation()),
        COLOR_STEEL,
        parent=grp_scr,
    )

doc_asm.recompute()
doc_asm.save()
print(f"✔ Saved Canonical Assembly: {fcstd_asm_path}")

# =============================================================================
# 4. Pairwise 3D B-Rep Collision Verification
# =============================================================================
print("4. Running Pairwise 3D B-Rep Collision Check on tibia_assembly.FCStd...")
items = []
for obj in asm_part.Group:
    if obj.Name == "Tarsus_Assembly":
        for sub in doc_tarsus_asm.Tarsus_Assembly.Group:
            if hasattr(sub, "Shape") and not sub.Shape.isNull():
                sh = sub.Shape.copy()
                sh.Placement = p_tarsus.multiply(sh.Placement)
                items.append((f"Tarsus_Assembly.{sub.Name}", sh))
    elif obj.TypeId == "App::Part":
        for sub in obj.Group:
            if hasattr(sub, "Shape") and not sub.Shape.isNull():
                sh = sub.Shape.copy()
                sh.Placement = obj.Placement.multiply(sh.Placement)
                items.append((f"{obj.Name}.{sub.Name}", sh))
    elif hasattr(obj, "Shape") and not obj.Shape.isNull():
        items.append((obj.Name, obj.Shape))

max_coll = 0.0
for i in range(len(items)):
    for j in range(i + 1, len(items)):
        n1, s1 = items[i]
        n2, s2 = items[j]
        # Skip internal 25T spline press-fit overlap between COTS Servo_Body and Servo_Horn
        if {n1, n2} == {"Knee_Servo_Body", "Knee_Servo_Horn"}:
            continue
        if s1.BoundBox.intersect(s2.BoundBox):
            v = s1.common(s2).Volume
            if v > 1e-4:
                print(f"  ❌ COLLISION {n1} <-> {n2}: {v:.4f} mm^3")
                max_coll = max(max_coll, v)
if max_coll <= 1e-4:
    print(f"  ✅ ZERO COLLISIONS across all {len(items)} components in tibia_assembly.FCStd (0.0000 mm^3)!")

# =============================================================================
# 5. Kinematic Ground Compression Sweep (0.0 deg to +5.0 deg CCW)
# =============================================================================
print("5. Running Kinematic Tarsus Ground-Compression Sweep (0.0 deg to +5.0 deg CCW)...")
s_body = doc_asm.getObject("Tibia_Body").Shape
s_cover = doc_asm.getObject("Tibia_Cover").Shape
s_sw = doc_asm.getObject("Microswitch").Shape
tarsus_raw = doc_tarsus_asm.getObject("Tarsus").Shape
shoe_raw = doc_tarsus_asm.getObject("Tarsus_Shoe").Shape

p_plunger_world = gt.SW_PLACEMENT.multVec(App.Vector(7.10, 9.50, 0.0))
for deg in [0.0, 1.0, 2.0, 3.0, 4.0, 4.5, 5.0]:
    r_local = App.Placement(App.Vector(0, 0, 0), App.Rotation(App.Vector(0, 0, 1), deg))
    rk = tarsus_raw.copy()
    rk.Placement = p_tarsus.multiply(r_local)
    sh = shoe_raw.copy()
    sh.Placement = p_tarsus.multiply(r_local)
    vb = rk.common(s_body).Volume + sh.common(s_body).Volume
    vc = rk.common(s_cover).Volume + sh.common(s_cover).Volume
    vs = rk.common(s_sw).Volume
    # Measure NC switch lift-off gap & spring compression
    p_pad_rot = p_tarsus.multiply(r_local).multVec(App.Vector(-25.5, 3.20, 0.0))
    p_sp_rot = p_tarsus.multiply(r_local).multVec(App.Vector(-41.5, -4.20, 0.0))
    gap_sw = p_plunger_world.y - p_pad_rot.y
    sp_len = p_sp_rot.y - gt.SPRING_FLOOR_Y
    print(
        f"  Stroke +{deg:3.1f}°: NC Release Gap = {gap_sw:+5.2f} mm | Spring L = {sp_len:5.2f} mm | "
        f"vs Body={vb:.4f} mm3, Cover={vc:.4f} mm3, Switch={vs:.4f} mm3"
    )

for d in list(App.listDocuments().values()):
    try:
        App.closeDocument(d.Name)
    except Exception:
        pass

sys.exit(0)
