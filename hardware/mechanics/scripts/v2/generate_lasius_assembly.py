#!/usr/bin/env python3
"""
Generate Lasius Hexapod Robot Master Assembly v2 (custom/v2/lasius_assembly.FCStd)
=================================================================================
Top-level entry point (L0) for the complete 22-DoF Lasius Hexapod Robot.
Assembles:
  1. Body & Legs Assembly (custom/v2/body_assembly.FCStd)
     - CFRP Chassis plates (body_bottom & body_top)
     - Monocoque central core (dual vertical PCA9685, TCA9548A, 2S LiPo)
     - Belly pan skid plate & VL53L5CX ToF sensor
     - Raspberry Pi 4 elevated deck & mount
     - Draped Plexiglas canopy & service cover
     - Six modular 3-DoF legs (monolithic femur + encapsulated ADS1115 & monolithic tibia)
  2. Parallel 2-DoF Bionic Sensor Head Assembly (custom/v2/head_assembly.FCStd)
     - Front dovetail & M3 standoff carrier (X = 85.7..134.5, Z = 2.02..53.28)
     - 2x stationary MG90S servos + M2 ball-link pushrods + true-center spherical Cardan joint
     - Lightweight bionic carapace housing RPi Camera Module 3, Front VL53L5CX ToF & twin eye pods
  3. Rear Petiolus & Gaster Assembly (custom/v2/gaster_assembly.FCStd)
     - Rear standoff mount (clamped between chassis plates at X = -90, -120)
     - 2-DoF SES petiolus gimbal (Pan & Tilt servos)
     - Sandwich plate-and-spacer articulated abdomen
"""

import math
import os
import sys
import zipfile
import FreeCAD as App
import Part

print("--- Generating Lasius Hexapod Master Assembly v2 (custom/v2/lasius_assembly.FCStd) ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_base = f"{repo_root}/hardware/mechanics/models"
v2_asm_dir = f"{models_base}/custom/v2"
export_dir = f"{repo_root}/hardware/mechanics/export"

doc_name = "lasius_assembly"
fcstd_path = f"{v2_asm_dir}/lasius_assembly.FCStd"

os.makedirs(v2_asm_dir, exist_ok=True)

# Backup existing GuiDocument.xml if present to survive headless console saves
fallback_gui_xml = None
if os.path.exists(fcstd_path):
    try:
        with zipfile.ZipFile(fcstd_path, "r") as zin:
            if "GuiDocument.xml" in zin.namelist():
                fallback_gui_xml = zin.read("GuiDocument.xml")
    except Exception:
        pass

# Close any open document with same name
try:
    App.closeDocument(doc_name)
except Exception:
    pass

for doc_k in list(App.listDocuments().keys()):
    try:
        App.closeDocument(doc_k)
    except Exception:
        pass
try:
    from PySide6 import QtCore
    QtCore.QCoreApplication.processEvents()
except Exception:
    pass

# Create and save document immediately (required for App::Link resolution)
doc = App.newDocument(doc_name)
doc.saveAs(fcstd_path)

# Open L1 Subassembly Documents
doc_body = App.openDocument(f"{v2_asm_dir}/body_assembly.FCStd")
doc_head = App.openDocument(f"{v2_asm_dir}/head_assembly.FCStd")
doc_gaster = App.openDocument(f"{v2_asm_dir}/gaster_assembly.FCStd")

# Main Assembly Container
asm_part = doc.addObject("App::Part", "Lasius_Assembly_v2")
asm_part.Label = "Lasius Hexapod Master Assembly (v2, 22-DoF)"
asm_part.Visibility = True
for o in asm_part.Origin.OutList:
    if hasattr(o, "Visibility"):
        o.Visibility = False
asm_part.Origin.Visibility = False

def make_link(name, label, target_obj, placement, parent=asm_part):
    lnk = doc.addObject("App::Link", name)
    lnk.setLink(target_obj)
    lnk.Label = label
    lnk.Placement = placement
    parent.addObject(lnk)
    lnk.Visibility = True
    if hasattr(lnk, "ViewObject") and lnk.ViewObject is not None:
        try:
            lnk.ViewObject.Visibility = True
        except Exception:
            pass
    return lnk

# 1. Body & 6x Legs Subsystem (L1)
body_obj = getattr(doc_body, "Body_Assembly_v2", getattr(doc_body, "Body_Assembly", None))
p_body = App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation())
make_link("Body_Assembly", "1. Body & Legs Assembly (v2, 18-DoF)", body_obj, p_body)

# 2. Parallel 2-DoF Bionic Sensor Head Subsystem (L1)
head_obj = getattr(doc_head, "Head_Assembly", None)
p_head = App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation())
make_link("Head_Assembly", "2. Parallel 2-DoF Bionic Sensor Head Assembly (v2)", head_obj, p_head)

# 3. Rear Petiolus & Gaster Subsystem (L1)
gaster_obj = getattr(doc_gaster, "Gaster_Assembly", None)
p_gaster = App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation())
make_link("Gaster_Assembly", "3. Rear Petiolus & Gaster Assembly (v2, 2-DoF)", gaster_obj, p_gaster)

# Recompute & Save
doc.recompute()
doc.save()
print(f"✔ Saved Lasius Master Assembly -> {fcstd_path}")

bbox = asm_part.Shape.BoundBox
print(f"Assembly Compound Valid: {asm_part.Shape.isValid()}")
print(f"Bounding Box: X=[{bbox.XMin:.2f}, {bbox.XMax:.2f}], Y=[{bbox.YMin:.2f}, {bbox.YMax:.2f}], Z=[{bbox.ZMin:.2f}, {bbox.ZMax:.2f}]")
print(f"Total Width (Y): {bbox.YLength:.2f} mm, Length (X): {bbox.XLength:.2f} mm, Height (Z): {bbox.ZLength:.2f} mm")

# Assemblies are logical structures, not exported to STEP/STL (never manufactured in one piece)
print(f"✔ Saved Master Assembly: {fcstd_path}")

# Close documents
for d in [doc_body, doc_head, doc_gaster, doc]:
    try:
        App.closeDocument(d.Name)
    except Exception:
        pass

print("--- Lasius Master Assembly Generation Complete ---")
sys.exit(0)
