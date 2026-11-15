#!/usr/bin/env python3
"""
Generate Lasius Tibia v2 Subsystem Assembly with Integrated Foot Sensor
========================================================================
Combines:
1. Tibia Monocoque Body: tibia_sensor_monocoque.FCStd
   (Monolithic v2 Tibia with ~45-deg Warren truss servo cage, knee counter-bearing,
    and integrated 11 mm clevis fork with internal microswitch & spring bays)
2. Knee Servo: cots/servo_nr645.FCStd (Torcster NR-645 high-torque metal gear servo)
3. Outward Bionic Rocker Foot: tibia_foot_rocker.FCStd (Extended curved claw sole, +52% lever)
4. Microswitch: cots/microswitch_subminiature.FCStd (IP67 subminiature switch)
5. Compression Spring: cots/compression_spring_4x12.FCStd (Stainless preload spring)
6. Hardware: M3 hardened pivot pin with brass Ruthex threaded insert

Output Assembly:
- hardware/mechanics/models/custom/v2/concepts/tibia_foot/tibia_assembly.FCStd
"""

import math
import os
import sys
import FreeCAD as App
import Part

print("--- Generating Lasius Tibia v2 Assembly with Foot Sensor ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
cots_dir = f"{repo_root}/hardware/mechanics/models/cots"
concept_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/concepts/tibia_foot"
v2_parts_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts"
export_step_dir = f"{repo_root}/hardware/mechanics/export/step/custom/v2/concepts/tibia_foot"
export_stl_dir = f"{repo_root}/hardware/mechanics/export/stl/custom/v2/concepts/tibia_foot"
renders_dir = f"{repo_root}/hardware/mechanics/drawings/renders"

os.makedirs(concept_dir, exist_ok=True)
os.makedirs(export_step_dir, exist_ok=True)
os.makedirs(export_stl_dir, exist_ok=True)
os.makedirs(renders_dir, exist_ok=True)

# Colors
COLOR_CFRP = (0.20, 0.20, 0.22)        # Dark carbon / PETG shank
COLOR_SERVO = (0.15, 0.15, 0.15)       # Black servo casing
COLOR_ORANGE = (0.90, 0.45, 0.10)      # Orange anodized aluminum / PETG foot rocker
COLOR_SWITCH = (0.12, 0.12, 0.12)      # Black switch body
COLOR_SPRING = (0.80, 0.80, 0.85)      # Steel spring
COLOR_BRASS = (0.85, 0.70, 0.20)       # Brass Ruthex insert & pins

# =============================================================================
# 1. Build Monolithic Tibia Body with Integrated Clevis Fork
# =============================================================================
print("1. Building Monolithic Tibia Body with Clevis Fork: tibia_sensor_monocoque.FCStd...")
doc_tibia = App.openDocument(f"{v2_parts_dir}/tibia/tibia.FCStd")
tibia_solid = doc_tibia.Objects[0].Shape.copy()

doc_shank = App.openDocument(f"{concept_dir}/tibia_foot_shank.FCStd")
shank_solid = doc_shank.Objects[0].Shape.copy()

# Shank placement at distal tip of Tibia
rot_deg = -67.59
rot_rad = math.radians(rot_deg)
rot_foot = App.Rotation(App.Vector(0, 0, 1), rot_deg)
px = -10.0 * math.sin(rot_rad)
py = 10.0 * math.cos(rot_rad)
base_pos = App.Vector(-122.0 - px, -14.0 - py, 0.5)
p_shank = App.Placement(base_pos, rot_foot)

shank_placed = shank_solid.copy()
shank_placed.Placement = p_shank

# Cut old rounded distal tip of Tibia at X < -85 mm
cutter = Part.makeBox(60.0, 60.0, 30.0, App.Vector(-150.0, -40.0, -15.0))
tibia_proximal = tibia_solid.cut(cutter)

# Fuse into seamless bionic monocoque body
tibia_monocoque = tibia_proximal.fuse(shank_placed)
try:
    tibia_monocoque = tibia_monocoque.removeSplitter()
except Exception:
    pass

fcstd_mono_path = f"{concept_dir}/tibia_sensor_monocoque.FCStd"
doc_mono_name = "tibia_sensor_monocoque"
try:
    App.closeDocument(doc_mono_name)
except Exception:
    pass
doc_mono = App.newDocument(doc_mono_name)
obj_mono = doc_mono.addObject("Part::Feature", "Tibia_Sensor_Monocoque")
obj_mono.Label = "Tibia v2 Monocoque Body with Integrated Clevis Fork"
obj_mono.Shape = tibia_monocoque
doc_mono.recompute()
doc_mono.saveAs(fcstd_mono_path)
print(f"✔ Saved: {fcstd_mono_path}")

# =============================================================================
# 2. Build Subsystem Assembly: tibia_assembly.FCStd
# =============================================================================
print("2. Building Subsystem Assembly: tibia_assembly.FCStd...")
doc_asm_name = "tibia_assembly"
try:
    App.closeDocument(doc_asm_name)
except Exception:
    pass
fcstd_asm_path = f"{concept_dir}/tibia_assembly.FCStd"
doc_asm = App.newDocument(doc_asm_name)
doc_asm.saveAs(fcstd_asm_path)

# Open COTS and components
doc_servo = App.openDocument(f"{cots_dir}/servo_nr645.FCStd")
doc_rocker = App.openDocument(f"{concept_dir}/tibia_foot_rocker.FCStd")
doc_sw = App.openDocument(f"{cots_dir}/microswitch_subminiature.FCStd")
doc_sp = App.openDocument(f"{cots_dir}/compression_spring_4x12.FCStd")

asm_part = doc_asm.addObject("App::Part", "Tibia_Assembly")
asm_part.Label = "Lasius Tibia v2 Subsystem Assembly with Foot Contact Sensor"

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
make_link("Tibia_Body", "1. Tibia v2 Monocoque (Warren Truss + Clevis Fork)", obj_mono, App.Placement(), COLOR_CFRP)

# 2. Knee Servo in Servo Cage
p_servo = App.Placement(App.Vector(0.0, 0.0, 18.8), App.Rotation(App.Vector(0, 0, 1), 180.0))
make_link("Knee_Servo", "2. Knee Servo (Torcster NR-645 COTS)", doc_servo.Objects[0], p_servo, COLOR_SERVO)

# 3. Bionic Foot Rocker (Outward Tarsus)
make_link("Tibia_Foot_Rocker", "3. Bionic Tarsus Rocker Foot (+52% Lever)", doc_rocker.Objects[0], p_shank, COLOR_ORANGE)

# 4. Microswitch
p_sw_local = App.Placement(App.Vector(4.3 - 6.7, 23.0, 0.0), App.Rotation())
make_link("Microswitch", "4. Subminiature Microswitch (COTS)", doc_sw.Objects[0], p_shank.multiply(p_sw_local), COLOR_SWITCH)

# 5. Compression Spring
p_sp_local = App.Placement(App.Vector(-14.0, 8.5, 0.0), App.Rotation())
make_link("Compression_Spring", "5. Stainless Preload Spring (COTS)", doc_sp.Objects[0], p_shank.multiply(p_sp_local), COLOR_SPRING)

# 6. Pivot Pin & Ruthex
pin_obj = doc_asm.addObject("Part::Feature", "Pivot_Pin_Assembly")
pin_obj.Label = "6. M3 Hardened Pivot Pin & Ruthex"
pin_head = Part.makeCylinder(2.8, 2.0, App.Vector(0.0, 10.0, 3.5), App.Vector(0, 0, 1))
pin_shaft = Part.makeCylinder(1.5, 11.0, App.Vector(0.0, 10.0, -5.5), App.Vector(0, 0, 1))
ruthex = Part.makeCylinder(2.1, 4.0, App.Vector(0.0, 10.0, -5.5), App.Vector(0, 0, 1))
pin_solid = pin_head.fuse(pin_shaft).fuse(ruthex)
pin_solid.Placement = p_shank
pin_obj.Shape = pin_solid
asm_part.addObject(pin_obj)
if hasattr(pin_obj, "ViewObject") and pin_obj.ViewObject:
    try:
        pin_obj.ViewObject.ShapeColor = COLOR_BRASS
    except Exception:
        pass

doc_asm.recompute()
doc_asm.save()
print(f"✔ Saved Assembly: {fcstd_asm_path}")

# =============================================================================
# 3. Export STEP & STL
# =============================================================================
print("3. Exporting STEP and STL...")
step_asm_path = f"{export_step_dir}/tibia_assembly.step"
stl_asm_path = f"{export_stl_dir}/tibia_assembly.stl"

export_objs = [obj_mono, doc_servo.Objects[0], doc_rocker.Objects[0], doc_sw.Objects[0], doc_sp.Objects[0], pin_obj]
Part.export(export_objs, step_asm_path)
print(f"✔ Exported STEP: {step_asm_path}")

comp = Part.Compound([o.Shape for o in export_objs])
comp.exportStl(stl_asm_path)
print(f"✔ Exported STL: {stl_asm_path}")

print("=== Tibia Assembly Generation Complete! ===")
