#!/usr/bin/env python3
"""
Generate Lasius Hexapod Full Body Assembly v2 FreeCAD Model (custom/v2/body_assembly.FCStd)
Assembles:
1. Chassis bottom plate (../v1/parts/body_bottom.FCStd) at Z = 0.00 .. 2.00 mm
2. 8x Chassis standoff spacers (../v1/parts/spacer_14x50.FCStd, D14 x 51.3 mm) at Z = 2.00 .. 53.30 mm
3. Chassis top plate (../v1/parts/body_top.FCStd) at Z = 53.30 .. 55.30 mm
4. Six modular v2 legs (custom/v2/leg_assembly.FCStd with monolithic Femur + encapsulated ADS1115 & monolithic Tibia):
   - All 6 servo horns face forward towards the robot front (-X direction)
   - Left side legs (FL, ML, RL): standard orientation (ScaleVector = 1, 1, 1)
   - Right side legs (FR, MR, RR): mirrored across sagittal plane (ScaleVector = 1, -1, 1)
"""

import math
import os
import FreeCAD as App
import Part

print("--- Generating Lasius Full Body Assembly v2 (custom/v2/body_assembly.FCStd) ---")

doc_name = "body_assembly"
models_base = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/models"
v1_parts_dir = f"{models_base}/custom/v1/parts"
v2_asm_dir = f"{models_base}/custom/v2"
export_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export"

fcstd_path = f"{v2_asm_dir}/body_assembly.FCStd"
step_path = f"{export_dir}/step/custom/v2/body_assembly.step"
stl_path = f"{export_dir}/stl/custom/v2/body_assembly.stl"

# Close any open document with same name
try:
    App.closeDocument(doc_name)
except Exception:
    pass

# Create and immediately save new assembly document (required for App::Link resolution)
doc = App.newDocument(doc_name)
os.makedirs(v2_asm_dir, exist_ok=True)
os.makedirs(f"{export_dir}/step/custom/v2", exist_ok=True)
os.makedirs(f"{export_dir}/stl/custom/v2", exist_ok=True)
doc.saveAs(fcstd_path)

# Open source master documents
cots_dir = f"{models_base}/cots"
doc_bottom = App.openDocument(f"{v1_parts_dir}/body_bottom.FCStd")
doc_top = App.openDocument(f"{v1_parts_dir}/body_top.FCStd")
doc_spacer = App.openDocument(f"{v1_parts_dir}/spacer_14x50.FCStd")
doc_leg = App.openDocument(f"{v2_asm_dir}/leg_assembly.FCStd")
doc_tray_asm = App.openDocument(f"{v2_asm_dir}/electronics_tray_assembly.FCStd")
doc_belly = App.openDocument(f"{models_base}/custom/v2/parts/chassis/chassis_belly_pan.FCStd")
doc_rpi_mount = App.openDocument(f"{models_base}/custom/v2/parts/chassis/chassis_rpi_mount.FCStd")
doc_service_cover = App.openDocument(f"{models_base}/custom/v2/parts/chassis/chassis_service_cover.FCStd")
doc_canopy = App.openDocument(f"{models_base}/custom/v2/parts/chassis/chassis_canopy.FCStd")
doc_tof = App.openDocument(f"{cots_dir}/vl53l5cx_board.FCStd")
doc_rpi = App.openDocument(f"{cots_dir}/rpi4_model_b.FCStd")

# Main Assembly Container
asm_part = doc.addObject("App::Part", "Body_Assembly_v2")
asm_part.Label = "Lasius Full Body Assembly v2 (Monolithic Legs + Encapsulated ADCs)"
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


# Colors
COLOR_CARBON = (0.16, 0.16, 0.18)        # Dark graphite / carbon fiber plates
COLOR_SPACER = (0.78, 0.78, 0.80)        # Technical plastic standoff spacers (POM/PA / Nylon)
COLOR_BELLY_PAN = (0.26, 0.26, 0.30)     # Rugged anthracite PETG skid plate
COLOR_RPI_MOUNT = (0.24, 0.24, 0.28)     # Anthracite technical mounting plate
COLOR_SERVICE_COVER = (0.20, 0.20, 0.23) # Dark anthracite service cover with '>>>' louvers
COLOR_CANOPY = (0.85, 0.92, 0.98)        # Transparent Plexiglas / acrylic
COLOR_PCB_RED = (0.75, 0.15, 0.15)       # VL53L5CX ToF Distance Sensor (SparkFun red)
COLOR_RPI_GREEN = (0.08, 0.52, 0.24)     # Raspberry Pi 4 Model B (Raspberry Green PCB)

# -------------------------------------------------------------
# 1. Chassis Plates & Modular Assemblies
# -------------------------------------------------------------
# Bottom plate at Z = 0.00 .. 2.00 mm
p_bottom = App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation())
make_link("Body_Bottom", "1. Chassis Bottom Plate (2mm)", doc_bottom.BodyBottom, p_bottom, COLOR_CARBON)

# Top plate at Z = 53.30 .. 55.30 mm (gap 51.30 mm spanned by spacers)
p_top = App.Placement(App.Vector(0.0, 0.0, 53.30), App.Rotation())
make_link("Body_Top", "2. Chassis Top Plate (2mm)", doc_top.BodyTop, p_top, COLOR_CARBON)

# Electronics Tray & Power Assembly at Z = 18.00 mm (held by 4 central standoff collars)
# Encapsulates Tray Deck, dual PCA9685, TCA9548A, and 2S LiPo Battery
p_tray_asm = App.Placement(App.Vector(0.0, 0.0, 18.00), App.Rotation())
make_link("Electronics_Tray_Assembly", "3. Electronics Tray & Power Assembly (v2)", doc_tray_asm.Electronics_Tray_Assembly, p_tray_asm)

# Chassis Belly Pan (Skid Plate) at Z = 0.00 mm (mounted to underside of bottom plate)
p_belly = App.Placement(App.Vector(0.0, 0.0, 0.00), App.Rotation())
make_link("Chassis_Belly_Pan", "4. Chassis Belly Pan (v2)", doc_belly.Chassis_Belly_Pan, p_belly, COLOR_BELLY_PAN)

# VL53L5CX 9-Zone ToF Terrain Distance Sensor inside Belly Pan at X = 0.0, Y = 0.0, Z = -4.40 mm, facing downward
p_tof = App.Placement(App.Vector(0.0, 0.0, -4.40), App.Rotation(App.Vector(0, 1, 0), 180.0))
make_link("Sensor_VL53L5CX_ToF", "5. VL53L5CX 9-Zone ToF Distance Sensor (COTS)", doc_tof.VL53L5CX_Board, p_tof, COLOR_PCB_RED)

# Raspberry Pi 4 Mounting Plate on Body_Top at Z = 55.30 .. 59.80 mm
p_mount = App.Placement(App.Vector(0.0, 0.0, 0.00), App.Rotation())
make_link("Chassis_RPi_Mount", "6. Raspberry Pi 4 Mounting Plate (v2)", doc_rpi_mount.getObject("Chassis_RPi_Mount"), p_mount, COLOR_RPI_MOUNT)

# Raspberry Pi 4 Model B elevated on Mount Bosses at X = 0.0, Y = 0.0, Z = 59.80 mm
p_rpi = App.Placement(App.Vector(0.0, 0.0, 59.80), App.Rotation())
make_link("Board_RPi4", "7. Raspberry Pi 4 Model B (Elevated Deck, COTS)", doc_rpi.Raspberry_Pi_4, p_rpi, COLOR_RPI_GREEN)

# Draped Plexiglas Canopy with Service Aperture at Z = 0.00 mm (Thermoformed & Trimmed Flush)
p_canopy = App.Placement(App.Vector(0.0, 0.0, 0.00), App.Rotation())
make_link("Chassis_Canopy", "8. Draped Plexiglas Canopy with Service Aperture (v2)", doc_canopy.getObject("Chassis_Canopy"), p_canopy, COLOR_CANOPY)

# Removable Service Cover with '>>>' Chevron Louvers at Z = 0.00 mm
p_cover = App.Placement(App.Vector(0.0, 0.0, 0.00), App.Rotation())
make_link("Chassis_Service_Cover", "9. Service Cover with '>>>' Chevron Louvers (v2)", doc_service_cover.getObject("Chassis_Service_Cover"), p_cover, COLOR_SERVICE_COVER)

# -------------------------------------------------------------
# 2. Chassis Standoff Spacers (8x at small M3 screw holes, inherited from v1)
# -------------------------------------------------------------
spacer_positions = [
    # 4x Window flanking standoffs
    ("Spacer_Window_FL", "Standoff Pillar Window FL", 45.0, 30.0),
    ("Spacer_Window_FR", "Standoff Pillar Window FR", 45.0, -30.0),
    ("Spacer_Window_RL", "Standoff Pillar Window RL", -45.0, 30.0),
    ("Spacer_Window_RR", "Standoff Pillar Window RR", -45.0, -30.0),
    # 2x Front standoffs (side-by-side)
    ("Spacer_Front_L", "Standoff Pillar Front Left", 128.0, 12.0),
    ("Spacer_Front_R", "Standoff Pillar Front Right", 128.0, -12.0),
    # 2x Rear centerline standoffs (inline)
    ("Spacer_Rear_1", "Standoff Pillar Rear Mid 1", -90.0, 0.0),
    ("Spacer_Rear_2", "Standoff Pillar Rear Tip 2", -120.0, 0.0),
]

for s_name, s_label, sx, sy in spacer_positions:
    p_sp = App.Placement(App.Vector(sx, sy, 2.00), App.Rotation())
    make_link(s_name, s_label, doc_spacer.SpacerRod, p_sp, COLOR_SPACER)

# -------------------------------------------------------------
# 3. Six Modular v2 Legs (All Servo Horns Forward towards Front -X)
# -------------------------------------------------------------
z_leg_offset = 17.25


def get_leg_placement(x_hole, y_hole, z_offset, yaw_deg, is_mirrored):
    if is_mirrored:
        p_local_shift = App.Placement(App.Vector(0.0, 2.50, 0.0), App.Rotation())
    else:
        p_local_shift = App.Placement(App.Vector(0.0, -2.50, 0.0), App.Rotation())

    p_world = App.Placement(App.Vector(x_hole, y_hole, z_offset), App.Rotation(App.Vector(0, 0, 1), yaw_deg))
    return p_world.multiply(p_local_shift)


leg_mounts = [
    # Name, Label, Hole X, Hole Y, Yaw angle (degrees), is_mirrored
    ("Leg_Front_Left",   "Leg Front Left (FL, v2)",                 86.0,  65.0,   45.0, False),
    ("Leg_Middle_Left",  "Leg Middle Left (ML, v2)",                 0.0,  75.0,   90.0, False),
    ("Leg_Rear_Left",    "Leg Rear Left (RL, v2)",                 -86.0,  65.0,  135.0, False),
    ("Leg_Front_Right",  "Leg Front Right (FR, v2) [Mirrored]",     86.0, -65.0,  -45.0, True),
    ("Leg_Middle_Right", "Leg Middle Right (MR, v2) [Mirrored]",     0.0, -75.0,  -90.0, True),
    ("Leg_Rear_Right",   "Leg Rear Right (RR, v2) [Mirrored]",     -86.0, -65.0, -135.0, True),
]

leg_target_obj = getattr(doc_leg, "Leg_Assembly_v2", getattr(doc_leg, "Leg_Assembly", None))

for l_name, l_label, lx, ly, l_yaw, l_mirrored in leg_mounts:
    p_leg = get_leg_placement(lx, ly, z_leg_offset, l_yaw, l_mirrored)
    lnk = make_link(l_name, l_label, leg_target_obj, p_leg)
    if l_mirrored:
        lnk.ScaleVector = App.Vector(1.0, -1.0, 1.0)

# -------------------------------------------------------------
# 4. Recompute, Save & Export
# -------------------------------------------------------------
doc.recompute()
doc.save()
print(f"Saved FreeCAD Model: {fcstd_path}")

bbox = asm_part.Shape.BoundBox
print(f"Assembly Compound Valid: {asm_part.Shape.isValid()}")
print(f"Bounding Box: X=[{bbox.XMin:.2f}, {bbox.XMax:.2f}], Y=[{bbox.YMin:.2f}, {bbox.YMax:.2f}], Z=[{bbox.ZMin:.2f}, {bbox.ZMax:.2f}]")
print(f"Total Width (Y): {bbox.YLength:.2f} mm, Length (X): {bbox.XLength:.2f} mm, Height (Z): {bbox.ZLength:.2f} mm")

for d in list(App.listDocuments().values()):
    try:
        App.closeDocument(d.Name)
    except Exception:
        pass

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
print("--- Done ---")
import sys
sys.exit(0)

