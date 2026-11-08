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
doc_bottom = App.openDocument(f"{v1_parts_dir}/body_bottom.FCStd")
doc_top = App.openDocument(f"{v1_parts_dir}/body_top.FCStd")
doc_spacer = App.openDocument(f"{v1_parts_dir}/spacer_14x50.FCStd")
doc_leg = App.openDocument(f"{v2_asm_dir}/leg_assembly.FCStd")

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
COLOR_CARBON = (0.16, 0.16, 0.18)      # Dark graphite / carbon fiber plates
COLOR_ALU_SPACER = (0.75, 0.77, 0.82)  # Anodized aluminum spacers

# -------------------------------------------------------------
# 1. Chassis Plates (Inherited from v1)
# -------------------------------------------------------------
# Bottom plate at Z = 0.00 .. 2.00 mm
p_bottom = App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation())
make_link("Body_Bottom", "1. Chassis Bottom Plate (2mm)", doc_bottom.BodyBottom, p_bottom, COLOR_CARBON)

# Top plate at Z = 53.30 .. 55.30 mm (gap 51.30 mm spanned by spacers)
p_top = App.Placement(App.Vector(0.0, 0.0, 53.30), App.Rotation())
make_link("Body_Top", "2. Chassis Top Plate (2mm)", doc_top.BodyTop, p_top, COLOR_CARBON)

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
    make_link(s_name, s_label, doc_spacer.SpacerRod, p_sp, COLOR_ALU_SPACER)

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

try:
    asm_part.Shape.exportStep(step_path)
    print(f"Exported STEP: {step_path}")
except Exception as e:
    print(f"STEP export error: {e}")

if __name__ == "__main__":
    for d in [doc_bottom, doc_top, doc_spacer, doc_leg]:
        try:
            App.closeDocument(d.Name)
        except Exception:
            pass
    print("--- Done ---")
