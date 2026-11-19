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
- Subassemblies referenced:
  * hardware/mechanics/models/custom/v2/tarsus_assembly.FCStd         (Tarsus_Assembly)
- Custom v2 Tibia Subassembly:
  * hardware/mechanics/models/custom/v2/tibia_assembly.FCStd           (Tibia_Assembly)
"""

import math
import os
import sys
import zipfile
import xml.etree.ElementTree as ET
import FreeCAD as App
import Part

DO_EXPORT = ("--export" in sys.argv)

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
sys.path.append(f"{repo_root}/hardware/mechanics/scripts/v2")

print("--- Generating Lasius Tibia v2 Canonical Parts & Assembly ---")

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

# Colors
COLOR_CFRP = (0.22, 0.22, 0.24)        # Dark carbon anthracite
COLOR_COVER = (0.28, 0.28, 0.32)       # Contrasting carbon cover
COLOR_SERVO = (0.12, 0.12, 0.12)       # Matte black servo
COLOR_ORANGE = (0.92, 0.45, 0.10)      # Anodized orange tarsus lever
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

# Direct rectangular pin plunger of Omron D2FC-F-K(50M) (X in [6.2, 7.1], Y in [8.55, 10.45], Z in [-0.6, +0.6])
pin_button = Part.makeBox(0.90, 1.90, 1.20, App.Vector(6.20, 8.55, -0.60))

lug1 = Part.makeBox(3.3, 0.6, 1.2, App.Vector(-3.3, 1.5, -0.6))
lug2 = Part.makeBox(3.3, 0.6, 1.2, App.Vector(-3.3, 6.4, -0.6))
lug3 = Part.makeBox(3.3, 0.6, 1.2, App.Vector(-3.3, 11.3, -0.6))

sw_solid = sw_body.fuse(pin_button).fuse(lug1).fuse(lug2).fuse(lug3)
obj_sw = doc_sw.addObject("Part::Feature", "Microswitch_Subminiature")
obj_sw.Label = "Omron D2FC-F-K(50M) Subminiature Microswitch (12.8x6.5x5.8 mm, Direct Plunger)"
obj_sw.Shape = sw_solid
doc_sw.recompute()
doc_sw.saveAs(fcstd_sw_path)
if DO_EXPORT:
    sw_solid.exportStep(f"{repo_root}/hardware/mechanics/export/step/cots/microswitch_subminiature.step")

doc_sp = App.newDocument("compression_spring_4x12")
fcstd_sp_path = f"{cots_dir}/compression_spring_4x12.FCStd"
sp_outer = Part.makeCylinder(2.25, 11.3, App.Vector(0, 0, 0), App.Vector(0, 1, 0))
sp_inner = Part.makeCylinder(1.65, 13.3, App.Vector(0, -1.0, 0), App.Vector(0, 1, 0))
sp_tube = sp_outer.cut(sp_inner)
for i in range(5):
    y_slot = 1.4 + i * 1.85
    slot_cutter = Part.makeBox(6.0, 0.9, 1.0, App.Vector(-3.0, y_slot - 0.45, -0.5))
    slot_cutter.rotate(App.Vector(0, y_slot, 0), App.Vector(0, 1, 0), i * 45.0)
    sp_tube = sp_tube.cut(slot_cutter)

obj_sp = doc_sp.addObject("Part::Feature", "Compression_Spring")
obj_sp.Label = "Stainless Compression Spring (Da=4.5 mm, L=12 mm)"
obj_sp.Shape = sp_tube
doc_sp.recompute()
doc_sp.saveAs(fcstd_sp_path)

# =============================================================================
# 2. Canonical Monolithic Tibia Body & Removable Cover
# =============================================================================
print("2. Loading Canonical Parts: tibia.FCStd & tibia_cover.FCStd...")
fcstd_mono_path = f"{parts_tibia_dir}/tibia.FCStd"
fcstd_cover_path = f"{parts_tibia_dir}/tibia_cover.FCStd"

doc_mono = App.openDocument(fcstd_mono_path)
obj_mono = doc_mono.Tibia_Body
if DO_EXPORT:
    obj_mono.Shape.exportStep(f"{export_step_parts}/tibia.step")
    obj_mono.Shape.exportStl(f"{export_stl_parts}/tibia.stl")
print(f"✔ Verified: {fcstd_mono_path} (Valid={obj_mono.Shape.isValid()}, Volume={obj_mono.Shape.Volume:.1f} mm3)")

doc_cover = App.openDocument(fcstd_cover_path)
obj_cover = doc_cover.Tibia_Cover
if DO_EXPORT:
    obj_cover.Shape.exportStep(f"{export_step_parts}/tibia_cover.step")
    obj_cover.Shape.exportStl(f"{export_stl_parts}/tibia_cover.stl")
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
p_servo = App.Placement(App.Vector(18.20, 15.25, -9.30), App.Rotation(App.Vector(1, 0, 0), 180.0))
make_link("Knee_Servo", "2. Knee Servo (Torcster NR-645 COTS)", doc_servo.Servo_Complete, p_servo, COLOR_SERVO)

# 3. Tarsus Subsystem Assembly (incorporating Tarsus Rocker Lever and Spoon Shoe)
# Exact verified foot placement in Tibia coordinate frame
p_shank = App.Placement(
    App.Vector(149.445, -2.56232, 9.0),
    App.Rotation(App.Vector(0, 0, 1), -112.4100084) * App.Rotation(App.Vector(1, 0, 0), 180.0),
)
make_link("Tarsus_Assembly", "3. Tarsus Subsystem Assembly (Rocker + Spoon Shoe)", doc_tarsus_asm.Tarsus_Assembly, p_shank)

# 4. Microswitch
p_sw_local = App.Placement(App.Vector(-6.9, 23.0, 0.0), App.Rotation())
make_link("Microswitch", "4. Subminiature Microswitch (COTS)", obj_sw, p_shank.multiply(p_sw_local), COLOR_SWITCH)

# 5. Compression Spring
p_sp_local = App.Placement(App.Vector(-10.2, 10.65, 0.0), App.Rotation())
make_link("Compression_Spring", "5. Stainless Preload Spring (COTS)", obj_sp, p_shank.multiply(p_sp_local), COLOR_SPRING)

# 6. Removable Service Cover
make_link("Tibia_Cover", "6. Removable Service Cover (Cheek B Form-Fit)", obj_cover, App.Placement(), COLOR_COVER)

# 7. Encapsulated 3x8 mm Hardened Stainless Dowel Pin (ISO 2338)
pin_obj = doc_asm.addObject("Part::Feature", "Pivot_Pin_Assembly")
pin_obj.Label = "7. Encapsulated 3x8 mm Hardened Dowel Pin (ISO 2338)"
pin_shaft = Part.makeCylinder(1.50, 8.00, App.Vector(140.20, 1.25, 4.50), App.Vector(0, 0, 1))
pin_obj.Shape = pin_shaft
asm_part.addObject(pin_obj)
if hasattr(pin_obj, "ViewObject") and pin_obj.ViewObject:
    try:
        pin_obj.ViewObject.ShapeColor = COLOR_BRASS
    except Exception:
        pass

# 8. 3x M2 DIN 7991 Flush Countersunk Retaining Screws
screws = []
for pt in [App.Vector(111.5, 8.5, 12.4), App.Vector(127.0, 20.5, 12.4), App.Vector(135.0, -4.0, 12.4)]:
    cone = Part.makeCone(1.00, 2.00, 1.00, App.Vector(pt.x, pt.y, 13.30))
    shank = Part.makeCylinder(1.00, 4.00, App.Vector(pt.x, pt.y, 9.30))
    screws.append(cone.fuse(shank))

screw_m2 = doc_asm.addObject("Part::Feature", "Cover_Retaining_Screw_M2")
screw_m2.Label = "8. 3x M2x5 Flush Countersunk Retaining Screws (DIN 7991)"
screw_m2.Shape = Part.Compound(screws)
asm_part.addObject(screw_m2)
if hasattr(screw_m2, "ViewObject") and screw_m2.ViewObject:
    try:
        screw_m2.ViewObject.ShapeColor = COLOR_STEEL
    except Exception:
        pass

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
        # Check subcomponents of tarsus assembly
        for sub in doc_tarsus_asm.Tarsus_Assembly.Group:
            if hasattr(sub, "Shape") and not sub.Shape.isNull():
                sh = sub.Shape.copy()
                sh.Placement = p_shank.multiply(sh.Placement)
                items.append((f"Tarsus_Assembly.{sub.Name}", sh))
    elif hasattr(obj, "Shape") and not obj.Shape.isNull():
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
    print(f"  ✅ ZERO COLLISIONS across all {len(items)} components in tibia_assembly.FCStd (0.0000 mm^3)!")

print("5. Running Kinematic Tarsus Rocker + Spoon Shoe Stroke Sweep (0.0 deg to -5.0 deg ground compression)...")
s_body = doc_asm.getObject("Tibia_Body").Shape
s_cover = doc_asm.getObject("Tibia_Cover").Shape
s_sw = doc_asm.getObject("Microswitch").Shape
tarsus_raw = doc_tarsus_asm.getObject("Tarsus").Shape
shoe_raw = doc_tarsus_asm.getObject("Tarsus_Shoe").Shape
for deg in [0.0, -1.0, -2.0, -3.0, -4.0, -5.0]:
    r_local = App.Placement(App.Vector(0, 10, 0), App.Rotation(App.Vector(0, 0, 1), deg)).multiply(
        App.Placement(App.Vector(0, -10, 0), App.Rotation())
    )
    rk = tarsus_raw.copy()
    rk.Placement = p_shank.multiply(r_local)
    sh = shoe_raw.copy()
    sh.Placement = p_shank.multiply(r_local)
    vb = rk.common(s_body).Volume + sh.common(s_body).Volume
    vc = rk.common(s_cover).Volume + sh.common(s_cover).Volume
    vs = rk.common(s_sw).Volume
    arm_p = r_local.multVec(App.Vector(0.25, 32.5, 0))
    gap_sw = arm_p.x - 0.20
    print(f"  Stroke {deg:+4.1f}°: Switch Release Gap = {gap_sw:+.2f} mm | vs Body={vb:.4f} mm3, Cover={vc:.4f} mm3, Switch={vs:.4f} mm3")

for d in list(App.listDocuments().values()):
    try:
        App.closeDocument(d.Name)
    except Exception:
        pass


sys.exit(0)
