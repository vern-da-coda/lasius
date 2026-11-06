#!/usr/bin/env python3
"""
Generate Lasius Hexapod Full Body Assembly FreeCAD Model (body_assembly.FCStd)
Assembles:
1. Chassis bottom plate (body_bottom.FCStd) at Z = 0.00 .. 2.00 mm
2. 8x Chassis standoff spacers (spacer_14x50.FCStd, D14 x 51.3 mm) at Z = 2.00 .. 53.30 mm
3. Chassis top plate (body_top.FCStd) at Z = 53.30 .. 55.30 mm
4. Six modular legs (leg_assembly.FCStd):
   - All 6 servo horns face forward towards the robot front (-X direction)
   - Left side legs (FL, ML, RL): standard orientation (ScaleVector = 1, 1, 1)
   - Right side legs (FR, MR, RR): mirrored across sagittal plane (ScaleVector = 1, -1, 1)
"""

import math
import os
import FreeCAD as App
import Part

print("--- Generating Lasius Full Body Assembly (body_assembly.FCStd) ---")

doc_name = "body_assembly"
models_dir = "/home/bjoern/Workspace/Hexapods/lasius/mechanics/models"
export_dir = "/home/bjoern/Workspace/Hexapods/lasius/mechanics/export"

fcstd_path = f"{models_dir}/body_assembly.FCStd"
step_path = f"{export_dir}/step/body_assembly.step"
stl_path = f"{export_dir}/stl/body_assembly.stl"

# Close any open document with same name
try:
    App.closeDocument(doc_name)
except Exception:
    pass

# Create and immediately save new assembly document (required for App::Link resolution)
doc = App.newDocument(doc_name)
os.makedirs(models_dir, exist_ok=True)
os.makedirs(f"{export_dir}/step", exist_ok=True)
os.makedirs(f"{export_dir}/stl", exist_ok=True)
doc.saveAs(fcstd_path)

# Open source master documents
doc_bottom = App.openDocument(f"{models_dir}/body_bottom.FCStd")
doc_top = App.openDocument(f"{models_dir}/body_top.FCStd")
doc_spacer = App.openDocument(f"{models_dir}/spacer_14x50.FCStd")
doc_leg = App.openDocument(f"{models_dir}/leg_assembly.FCStd")

# Main Assembly Container
asm_part = doc.addObject("App::Part", "Body_Assembly")
asm_part.Label = "Lasius Full Body Assembly (Master Assembly)"
for o in asm_part.Origin.OutList:
    if hasattr(o, "Visibility"):
        o.Visibility = False
asm_part.Origin.Visibility = False
asm_part.Visibility = True

# Helper function to create links
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

# Colors
COLOR_CARBON = (0.16, 0.16, 0.18)      # Dark graphite / carbon fiber plates
COLOR_ALU_SPACER = (0.75, 0.77, 0.82)  # Anodized aluminum spacers

# -------------------------------------------------------------
# 1. Chassis Plates
# -------------------------------------------------------------
# Bottom plate at Z = 0.00 .. 2.00 mm
p_bottom = App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation())
make_link("Body_Bottom", "1. Chassis Bottom Plate (2mm)", doc_bottom.BodyBottom, p_bottom, COLOR_CARBON)

# Top plate at Z = 53.30 .. 55.30 mm (gap 51.30 mm spanned by spacers)
p_top = App.Placement(App.Vector(0.0, 0.0, 53.30), App.Rotation())
make_link("Body_Top", "2. Chassis Top Plate (2mm)", doc_top.BodyTop, p_top, COLOR_CARBON)

# -------------------------------------------------------------
# 2. Chassis Standoff Spacers (8x at small M3 screw holes)
# -------------------------------------------------------------
# Standoffs rest on top of bottom plate (Z = 2.00) and support top plate (Z = 53.30)
spacer_positions = [
    # 4x Window flanking standoffs
    ("Spacer_Window_FL", "Standoff Pillar Window FL", 45.0, 30.0),
    ("Spacer_Window_FR", "Standoff Pillar Window FR", 45.0, -30.0),
    ("Spacer_Window_RL", "Standoff Pillar Window RL", -45.0, 30.0),
    ("Spacer_Window_RR", "Standoff Pillar Window RR", -45.0, -30.0),
    # 2x Nose centerline standoffs
    ("Spacer_Nose_1", "Standoff Pillar Nose Mid 1", 90.0, 0.0),
    ("Spacer_Nose_2", "Standoff Pillar Nose Tip 2", 120.0, 0.0),
    # 2x Tail standoffs
    ("Spacer_Tail_L", "Standoff Pillar Tail Left", -128.0, 12.0),
    ("Spacer_Tail_R", "Standoff Pillar Tail Right", -128.0, -12.0),
]

for s_name, s_label, sx, sy in spacer_positions:
    p_sp = App.Placement(App.Vector(sx, sy, 2.00), App.Rotation())
    make_link(s_name, s_label, doc_spacer.SpacerRod, p_sp, COLOR_ALU_SPACER)

# -------------------------------------------------------------
# 3. Six Modular Legs (All Servo Horns Forward towards Front -X)
# -------------------------------------------------------------
# In leg_assembly, the vertical coxa axis is at (0.00, 2.50)
# Coxa bracket bottom face is at Z = -15.25.
# With z_offset = 17.25, the coxa bracket sits at Z = 2.00 mm (flush on bottom plate),
# and the coxa servo horn tip reaches Z = 54.00 mm (engaging into top plate Z = 53.30 .. 55.30 mm).
z_leg_offset = 17.25

def get_leg_placement(x_hole, y_hole, z_offset, yaw_deg, is_mirrored):
    if is_mirrored:
        # In mirrored leg (ScaleVector = 1, -1, 1), local coxa axis is at (0.0, -2.50)
        p_local_shift = App.Placement(App.Vector(0.0, 2.50, 0.0), App.Rotation())
    else:
        # In standard unmirrored leg, local coxa axis is at (0.0, +2.50)
        p_local_shift = App.Placement(App.Vector(0.0, -2.50, 0.0), App.Rotation())
    
    p_world = App.Placement(App.Vector(x_hole, y_hole, z_offset), App.Rotation(App.Vector(0, 0, 1), yaw_deg))
    return p_world.multiply(p_local_shift)

leg_mounts = [
    # Name, Label, Hole X, Hole Y, Yaw angle (degrees), is_mirrored
    ("Leg_Front_Left",   "Leg Front Left (FL)",                 86.0,  65.0,   45.0, False),
    ("Leg_Middle_Left",  "Leg Middle Left (ML)",                  0.0,  75.0,   90.0, False),
    ("Leg_Rear_Left",    "Leg Rear Left (RL)",               -86.0,  65.0,  135.0, False),
    ("Leg_Front_Right",  "Leg Front Right (FR) [Mirrored]",   86.0, -65.0,  -45.0, True),
    ("Leg_Middle_Right", "Leg Middle Right (MR) [Mirrored]",    0.0, -75.0,  -90.0, True),
    ("Leg_Rear_Right",   "Leg Rear Right (RR) [Mirrored]", -86.0, -65.0, -135.0, True),
]

for l_name, l_label, lx, ly, l_yaw, l_mirrored in leg_mounts:
    p_leg = get_leg_placement(lx, ly, z_leg_offset, l_yaw, l_mirrored)
    lnk = make_link(l_name, l_label, doc_leg.Leg_Assembly, p_leg)
    if l_mirrored:
        # Mirror right side across sagittal plane so all servo horns face forward (-X)
        lnk.ScaleVector = App.Vector(1.0, -1.0, 1.0)

# -------------------------------------------------------------
# 4. Recompute, Save & Export
# -------------------------------------------------------------
doc.recompute()
doc.save()
print(f"Saved FreeCAD Model: {fcstd_path}")

# Check Bounding Box & Validity
bbox = asm_part.Shape.BoundBox
print(f"Assembly Compound Valid: {asm_part.Shape.isValid()}")
print(f"Bounding Box: X=[{bbox.XMin:.2f}, {bbox.XMax:.2f}], Y=[{bbox.YMin:.2f}, {bbox.YMax:.2f}], Z=[{bbox.ZMin:.2f}, {bbox.ZMax:.2f}]")
print(f"Total Width (Y): {bbox.YLength:.2f} mm, Length (X): {bbox.XLength:.2f} mm, Height (Z): {bbox.ZLength:.2f} mm")

# Export STEP
try:
    asm_part.Shape.exportStep(step_path)
    print(f"Exported STEP: {step_path}")
except Exception as e:
    print(f"STEP export error: {e}")

# Full assembly STL export omitted (exceeds 100 MB GitHub limit; use individual component STLs for manufacturing and STEP for CAD)
# asm_part.Shape.exportStl(stl_path)

# Close helper documents
for d in [doc_bottom, doc_top, doc_spacer, doc_leg]:
    try:
        App.closeDocument(d.Name)
    except Exception:
        pass

print("--- Done ---")
