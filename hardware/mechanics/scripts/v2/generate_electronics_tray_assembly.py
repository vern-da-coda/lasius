#!/usr/bin/env python3
"""
Generate Lasius Hexapod Electronics Tray Subassembly v2 (custom/v2/electronics_tray_assembly.FCStd)
Assembles:
  1. Electronics Mounting Tray (custom/v2/parts/electronics_tray.FCStd)
  2. Raspberry Pi 4 Model B (cots/rpi4_model_b.FCStd)
  3. PCA9685 16-Channel PWM Servo Controller - Left (cots/pca9685_board.FCStd)
  4. PCA9685 16-Channel PWM Servo Controller - Right (cots/pca9685_board.FCStd)
  5. TCA9548A 8-Channel I2C Multiplexer (cots/tca9548a_board.FCStd)
  6. 2S 7.4V LiPo Battery Pack (cots/battery_lipo_2s.FCStd) situated underneath the tray deck
"""

import math
import os
import FreeCAD as App
import Part

print("--- Generating Lasius Electronics Tray Assembly v2 (custom/v2/electronics_tray_assembly.FCStd) ---")

doc_name = "electronics_tray_assembly"
models_base = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/models"
v2_asm_dir = f"{models_base}/custom/v2"
parts_dir = f"{v2_asm_dir}/parts"
cots_dir = f"{models_base}/cots"
export_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export"

fcstd_path = f"{v2_asm_dir}/electronics_tray_assembly.FCStd"
step_path = f"{export_dir}/step/custom/v2/electronics_tray_assembly.step"
stl_path = f"{export_dir}/stl/custom/v2/electronics_tray_assembly.stl"

# Close any open document with same name
try:
    App.closeDocument(doc_name)
except Exception:
    pass

# Create and immediately save new assembly document
doc = App.newDocument(doc_name)
os.makedirs(v2_asm_dir, exist_ok=True)
os.makedirs(f"{export_dir}/step/custom/v2", exist_ok=True)
os.makedirs(f"{export_dir}/stl/custom/v2", exist_ok=True)
doc.saveAs(fcstd_path)

# Open source master documents
doc_tray = App.openDocument(f"{parts_dir}/electronics_tray/electronics_tray.FCStd")
doc_pca = App.openDocument(f"{cots_dir}/pca9685_board.FCStd")
doc_tca = App.openDocument(f"{cots_dir}/tca9548a_board.FCStd")
doc_bat = App.openDocument(f"{cots_dir}/battery_lipo_2s.FCStd")

# Main Assembly Container
asm_part = doc.addObject("App::Part", "Electronics_Tray_Assembly")
asm_part.Label = "Lasius Electronics Tray & Power Assembly v2"
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


# High-contrast distinctive colors for structural parts vs electronics vs power
COLOR_TRAY = (0.22, 0.42, 0.65)         # Technical blue PETG 3D print
COLOR_ADAFRUIT_BLUE = (0.04, 0.38, 0.88)# PCA9685 PWM Servo Drivers (Adafruit typical blue)
COLOR_MUX_PURPLE = (0.58, 0.15, 0.75)   # TCA9548A I2C Multiplexer (Purple PCB)
COLOR_BATTERY_LIPO = (0.95, 0.75, 0.10) # 2S LiPo Battery Pack (Vivid LiPo Yellow / Gold)

# -------------------------------------------------------------
# 1. Electronics Mounting Tray Deck (Local Z = 0.00 .. 2.40 mm)
# -------------------------------------------------------------
p_tray = App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation())
make_link("Electronics_Tray", "1. Electronics Mounting Tray (v2)", doc_tray.Electronics_Tray, p_tray, COLOR_TRAY)

# -------------------------------------------------------------
# 2. Dual PCA9685 16-Channel PWM Servo Controllers (Central Bay on 3.0 mm Bosses)
# -------------------------------------------------------------
# Left Board: Y = +14.5 mm, 90° Servo Headers facing +Y (left legs: FL, ML, RL)
# Lateral plug insertion from the left flank with 2.0 mm clearance to ML Coxa Servo.
p_pca_l = App.Placement(App.Vector(0.0, 14.50, 5.40), App.Rotation(App.Vector(0, 0, 1), 0.0))
make_link("Board_PCA9685_Left", "2. PCA9685 PWM Controller Left (COTS)", doc_pca.PCA9685_Board, p_pca_l, COLOR_ADAFRUIT_BLUE)

# Right Board: Y = -14.5 mm, 90° Servo Headers facing -Y (right legs: FR, MR, RR)
# Rotated 180° so servo headers face lateral right flank with 2.0 mm clearance to MR Coxa Servo.
p_pca_r = App.Placement(App.Vector(0.0, -14.50, 5.40), App.Rotation(App.Vector(0, 0, 1), 180.0))
make_link("Board_PCA9685_Right", "3. PCA9685 PWM Controller Right (COTS)", doc_pca.PCA9685_Board, p_pca_r, COLOR_ADAFRUIT_BLUE)

# -------------------------------------------------------------
# 3. TCA9548A 8-Channel I2C Multiplexer Breakout (Rear Centerline Spine on 3.0 mm Bosses)
# -------------------------------------------------------------
# Situated cleanly between the two rear spacers at X = -52.0, Y = 0.0 mm
p_tca = App.Placement(App.Vector(-52.0, 0.0, 5.40), App.Rotation())
make_link("Board_TCA9548A", "4. TCA9548A I2C Multiplexer (COTS)", doc_tca.TCA9548A_Board, p_tca, COLOR_MUX_PURPLE)

# -------------------------------------------------------------
# 4. 2S 7.4V LiPo Battery Pack (Under Tray Deck: Z = -15.00 .. -1.00 mm)
# -------------------------------------------------------------
# Situated in the lower chassis chamber between bottom plate and tray deck.
# XT60 power leads exit in -X direction towards rear chassis XT60BE-M inlet.
p_bat = App.Placement(App.Vector(5.0, 0.0, -15.00), App.Rotation())
make_link("Battery_LiPo_2S", "5. 2S 7.4V LiPo Battery Pack (COTS)", doc_bat.Battery_LiPo_2S, p_bat, COLOR_BATTERY_LIPO)

# -------------------------------------------------------------
# 6. Recompute, Save & Export
# -------------------------------------------------------------
doc.recompute()
doc.save()
print(f"Saved FreeCAD Model: {fcstd_path}")

bbox = asm_part.Shape.BoundBox
print(f"Assembly Compound Valid: {asm_part.Shape.isValid()}")
print(f"Bounding Box: X=[{bbox.XMin:.2f}, {bbox.XMax:.2f}], Y=[{bbox.YMin:.2f}, {bbox.YMax:.2f}], Z=[{bbox.ZMin:.2f}, {bbox.ZMax:.2f}]")
print(f"Total Width (Y): {bbox.YLength:.2f} mm, Length (X): {bbox.XLength:.2f} mm, Height (Z): {bbox.ZLength:.2f} mm")

try:
    asm_part.Shape.exportStep(step_path)
    print(f"Exported STEP: {step_path}")
except Exception as e:
    print(f"STEP export error: {e}")

# Assembly STL omitted (assemblies use STEP for CAD; STL is reserved for 3D-printable parts)

for d in list(App.listDocuments().values()):
    try:
        App.closeDocument(d.Name)
    except Exception:
        pass

print("--- Electronics Tray Assembly Generated Successfully ---")
import sys
sys.exit(0)
