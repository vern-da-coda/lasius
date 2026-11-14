#!/usr/bin/env python3
"""
Generate Lasius Full Body Extended Assembly with Gaster v2 (FreeCAD 1.1+)
==========================================================================
Architecture:
  Extended variant of the Lasius hexapod master assembly (custom/v2/body_gaster_assembly.FCStd).
  Assembles:
    1. Chassis bottom plate (custom/v1/parts/body_bottom.FCStd) at Z = 0.0 .. 2.0 mm
    2. Chassis top plate (custom/v1/parts/body_top.FCStd) at Z = 53.3 .. 55.3 mm
    3. Monocoque Central Core Assembly (custom/v2/chassis_core_assembly.FCStd)
       replacing the 4 central window spacers (Spacer_Window_FL, FR, RL, RR)
    4. Head & Mandibles Modular Assembly (custom/v2/head_assembly.FCStd)
       replacing the 2 front spacers (Spacer_Front_L, Spacer_Front_R)
    5. Rear Petiolus & Gaster Modular Assembly (custom/v2/gaster_assembly.FCStd)
       replacing the 2 rear centerline spacers (Spacer_Rear_1, Spacer_Rear_2)
    6. Six modular v2 legs (custom/v2/leg_assembly.FCStd) with monolithic femurs & tibias
    7. Chassis Belly Pan (custom/v2/parts/chassis_belly_pan.FCStd)
    8. VL53L5CX 9-zone ToF terrain distance sensor (cots/vl53l5cx_board.FCStd)
    9. Raspberry Pi 4 Model B (cots/rpi4_model_b.FCStd) on top plate
"""

import math
import os
import sys
import FreeCAD as App
import FreeCADGui as Gui

print("--- Generating Lasius Full Body Extended Assembly with Gaster (custom/v2/body_gaster_assembly.FCStd) ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_base = f"{repo_root}/hardware/mechanics/models"
v1_parts_dir = f"{models_base}/custom/v1/parts"
v2_asm_dir = f"{models_base}/custom/v2"
v2_parts_dir = f"{models_base}/custom/v2/parts"
cots_dir = f"{models_base}/cots"

fcstd_path = f"{v2_asm_dir}/body_gaster_assembly.FCStd"

doc_name = "body_gaster_assembly"
try:
    App.closeDocument(doc_name)
except Exception:
    pass

# Close all existing documents to avoid stale object references
for doc_k in list(App.listDocuments().keys()):
    try:
        App.closeDocument(doc_k)
    except Exception:
        pass

# Create and save document immediately
doc = App.newDocument(doc_name)
doc.saveAs(fcstd_path)

# Open sub-documents cleanly
doc_bottom = App.openDocument(f"{v1_parts_dir}/body_bottom.FCStd")
doc_top = App.openDocument(f"{v1_parts_dir}/body_top.FCStd")
doc_core_asm = App.openDocument(f"{v2_asm_dir}/chassis_core_assembly.FCStd")
doc_head_asm = App.openDocument(f"{v2_asm_dir}/head_assembly.FCStd")
doc_gaster_asm = App.openDocument(f"{v2_asm_dir}/gaster_assembly.FCStd")
doc_leg = App.openDocument(f"{v2_asm_dir}/leg_assembly.FCStd")
doc_belly = App.openDocument(f"{v2_parts_dir}/chassis_belly_pan.FCStd")
doc_rpi_mount = App.openDocument(f"{v2_parts_dir}/chassis_rpi_mount.FCStd")
doc_service_cover = App.openDocument(f"{v2_parts_dir}/chassis_service_cover.FCStd")
doc_canopy = App.openDocument(f"{v2_parts_dir}/chassis_canopy.FCStd")
doc_tof = App.openDocument(f"{cots_dir}/vl53l5cx_board.FCStd")
doc_rpi = App.openDocument(f"{cots_dir}/rpi4_model_b.FCStd")

# Assembly Part Container
asm_part = doc.addObject("App::Part", "Body_Gaster_Assembly_v2")
asm_part.Label = "Lasius Extended Body Assembly with Articulated Gaster (v2)"
asm_part.Visibility = True

def make_link(name, label, target_obj, placement, color=None, parent=asm_part):
    lnk = doc.addObject("App::Link", name)
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

COLOR_CARBON = (0.16, 0.16, 0.18)        # Dark carbon plates
COLOR_BELLY_PAN = (0.26, 0.26, 0.30)     # Anthracite skid plate
COLOR_RPI_MOUNT = (0.24, 0.24, 0.28)     # Anthracite mounting plate
COLOR_SERVICE_COVER = (0.20, 0.20, 0.23) # Dark anthracite service cover with '>>>' louvers
COLOR_CANOPY = (0.85, 0.92, 0.98)        # Transparent Plexiglas / acrylic
COLOR_PCB_RED = (0.75, 0.15, 0.15)       # VL53L5CX SparkFun red
COLOR_RPI_GREEN = (0.08, 0.52, 0.24)     # Raspberry Pi 4 Model B

# 1. Chassis Bottom Plate (Z = 0.0 .. 2.0 mm)
p_bottom = App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation())
make_link("Body_Bottom", "1. Chassis Bottom Plate (2mm CFRP)", doc_bottom.getObject("BodyBottom"), p_bottom, COLOR_CARBON)

# 2. Chassis Top Plate (Z = 53.30 .. 55.30 mm)
p_top = App.Placement(App.Vector(0.0, 0.0, 53.30), App.Rotation())
make_link("Body_Top", "2. Chassis Top Plate (2mm CFRP)", doc_top.getObject("BodyTop"), p_top, COLOR_CARBON)

# 3. Monocoque Central Core Assembly (replaces 4 window spacers at ±45, ±30 mm)
p_core = App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation())
make_link("Monocoque_Core_Assembly", "3. Monocoque Central Core Assembly (v2)", doc_core_asm.getObject("Chassis_Core_Assembly"), p_core)

# 4. Head & Mandibles Modular Assembly (replaces 2 front spacers at X = 128, Y = ±12 mm)
p_head = App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation())
make_link("Head_Assembly", "4. Head & Mandibles Modular Assembly (v2)", doc_head_asm.getObject("Head_Assembly"), p_head)

# 5. Rear Petiolus & Gaster Modular Assembly (replaces 2 rear spacers at X = -90, -120 mm)
p_gaster = App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation())
make_link("Gaster_Assembly", "5. Rear Petiolus & Gaster Assembly (v2)", doc_gaster_asm.getObject("Gaster_Assembly"), p_gaster)

# 6. Chassis Belly Pan Skid Plate at Z = 0.00 mm
p_belly = App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation())
make_link("Chassis_Belly_Pan", "6. Chassis Belly Pan (v2)", doc_belly.getObject("Chassis_Belly_Pan"), p_belly, COLOR_BELLY_PAN)

# 7. Raspberry Pi 4 Mounting Plate on Body_Top (Z = 55.30 .. 59.80 mm)
p_mount = App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation())
make_link("Chassis_RPi_Mount", "7. Raspberry Pi 4 Mounting Plate (v2)", doc_rpi_mount.getObject("Chassis_RPi_Mount"), p_mount, COLOR_RPI_MOUNT)

# 8. Raspberry Pi 4 Model B elevated on Mount Bosses (X = 0.0, Y = 0.0, Z = 59.80 mm)
p_rpi = App.Placement(App.Vector(0.0, 0.0, 59.80), App.Rotation())
make_link("Board_RPi4", "8. Raspberry Pi 4 Model B (Elevated Deck, COTS)", doc_rpi.getObject("Raspberry_Pi_4"), p_rpi, COLOR_RPI_GREEN)

# 9. Draped Plexiglas Canopy with Service Hatch Aperture (Z = 55.30 .. 76.00 mm)
p_canopy = App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation())
make_link("Chassis_Canopy", "9. Draped Plexiglas Canopy with Service Aperture (v2)", doc_canopy.getObject("Chassis_Canopy"), p_canopy, COLOR_CANOPY)

# 10. Service Cover with '>>>' Chevron Louvers (Z = 74.80 .. 79.50 mm)
p_cover = App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation())
make_link("Chassis_Service_Cover", "10. Service Cover with '>>>' Chevron Louvers (v2)", doc_service_cover.getObject("Chassis_Service_Cover"), p_cover, COLOR_SERVICE_COVER)

# 11. VL53L5CX ToF Terrain Distance Sensor
p_tof = App.Placement(App.Vector(0.0, 0.0, -4.40), App.Rotation(App.Vector(0, 1, 0), 180.0))
make_link("Sensor_VL53L5CX_ToF", "11. VL53L5CX 9-Zone ToF Sensor (COTS)", doc_tof.getObject("VL53L5CX_Board"), p_tof, COLOR_PCB_RED)

# 12. Six Modular v2 Legs
z_leg_offset = 17.25

def get_leg_placement(x_hole, y_hole, z_offset, yaw_deg, is_mirrored):
    if is_mirrored:
        p_local_shift = App.Placement(App.Vector(0.0, 2.50, 0.0), App.Rotation())
    else:
        p_local_shift = App.Placement(App.Vector(0.0, -2.50, 0.0), App.Rotation())
    p_world = App.Placement(App.Vector(x_hole, y_hole, z_offset), App.Rotation(App.Vector(0, 0, 1), yaw_deg))
    return p_world.multiply(p_local_shift)

leg_mounts = [
    ("Leg_Front_Left",   "11.1 Leg Front Left (FL, v2)",                 86.0,  65.0,   45.0, False),
    ("Leg_Middle_Left",  "11.2 Leg Middle Left (ML, v2)",                 0.0,  75.0,   90.0, False),
    ("Leg_Rear_Left",    "11.3 Leg Rear Left (RL, v2)",                 -86.0,  65.0,  135.0, False),
    ("Leg_Front_Right",  "11.4 Leg Front Right (FR, v2) [Mirrored]",     86.0, -65.0,  -45.0, True),
    ("Leg_Middle_Right", "11.5 Leg Middle Right (MR, v2) [Mirrored]",     0.0, -75.0,  -90.0, True),
    ("Leg_Rear_Right",   "11.6 Leg Rear Right (RR, v2) [Mirrored]",     -86.0, -65.0, -135.0, True),
]

leg_target_obj = getattr(doc_leg, "Leg_Assembly_v2", getattr(doc_leg, "Leg_Assembly", None))

for l_name, l_label, lx, ly, l_yaw, l_mirrored in leg_mounts:
    p_leg = get_leg_placement(lx, ly, z_leg_offset, l_yaw, l_mirrored)
    lnk = make_link(l_name, l_label, leg_target_obj, p_leg)
    if l_mirrored:
        lnk.ScaleVector = App.Vector(1.0, -1.0, 1.0)

doc.recompute()
doc.save()
print(f"✔ Saved Extended Body Assembly with Gaster -> {fcstd_path}")

# Close sub-documents
for d in [doc_bottom, doc_top, doc_core_asm, doc_head_asm, doc_gaster_asm, doc_leg, doc_belly, doc_rpi_mount, doc_service_cover, doc_canopy, doc_tof, doc_rpi]:
    try:
        App.closeDocument(d.Name)
    except Exception:
        pass

App.closeDocument(doc_name)

# Ensure GuiDocument.xml has Visibility="true"
import zipfile
def patch_fcstd_visibility(filepath):
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

patch_fcstd_visibility(fcstd_path)
print("✔ Patched GuiDocument.xml for full visibility")

print("--- Extended Body Assembly with Gaster Generation Complete (All files visible) ---")
sys.exit(0)
