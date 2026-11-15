#!/usr/bin/env python3
"""
Generate Lasius Tibia Foot Sensor Concept (custom/v2/concepts/tibia_foot/)
==========================================================================
Parametric Generator for:
1. COTS: microswitch_subminiature.FCStd (12.8 x 6.5 x 5.8 mm with leaf lever)
2. COTS: compression_spring_4x12.FCStd (Da = 4.5 mm, L = 12.0 mm)
3. Concept Shank: tibia_foot_shank.FCStd (11.0 mm clevis fork, 6.0 mm internal slot,
   switch pocket, spring pocket, M3 Ruthex pivot)
4. Concept Rocker: tibia_foot_rocker.FCStd (5.6 mm thick bionic tarsus wippe,
   M3 pivot, M2 set screw seat, compression spring boss, curved claw sole)
5. Assembly: tibia_foot_assembly.FCStd (Kinematic assembly linking all components)
"""

import math
import os
import sys
import zipfile
import FreeCAD as App
import Part

print("--- Generating Lasius Tibia Foot Sensor Concept ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models"
cots_dir = f"{models_dir}/cots"
concept_dir = f"{models_dir}/custom/v2/concepts/tibia_foot"
export_step_dir = f"{repo_root}/hardware/mechanics/export/step/custom/v2/concepts/tibia_foot"
export_stl_dir = f"{repo_root}/hardware/mechanics/export/stl/custom/v2/concepts/tibia_foot"
renders_dir = f"{repo_root}/hardware/mechanics/drawings/renders"

os.makedirs(cots_dir, exist_ok=True)
os.makedirs(concept_dir, exist_ok=True)
os.makedirs(export_step_dir, exist_ok=True)
os.makedirs(export_stl_dir, exist_ok=True)
os.makedirs(renders_dir, exist_ok=True)

# Colors
COLOR_CFRP = (0.16, 0.16, 0.18)      # Dark carbon / PETG shank
COLOR_ALU_ORANGE = (0.88, 0.45, 0.10) # Orange anodized aluminum / PETG foot rocker
COLOR_SWITCH = (0.12, 0.12, 0.12)    # Black switch body
COLOR_LEVER = (0.80, 0.80, 0.82)     # Stainless steel lever
COLOR_SPRING = (0.75, 0.75, 0.78)    # Steel spring
COLOR_BRASS = (0.85, 0.70, 0.20)     # Brass Ruthex insert & pins

# =============================================================================
# 1. Build COTS: microswitch_subminiature.FCStd
# =============================================================================
print("1. Building COTS: microswitch_subminiature.FCStd...")
doc_sw_name = "microswitch_subminiature"
try:
    App.closeDocument(doc_sw_name)
except Exception:
    pass
doc_sw = App.newDocument(doc_sw_name)
fcstd_sw_path = f"{cots_dir}/microswitch_subminiature.FCStd"

# Main rectangular body: 12.8 mm length (X), 5.8 mm width (Y), 6.5 mm height (Z)
# Centered in Y around 0 (Y in [-2.9, +2.9]), X in [0, 12.8], Z in [0, 6.5]
sw_body = Part.makeBox(12.8, 5.8, 6.5, App.Vector(0.0, -2.9, 0.0))

# 2x Mounting holes: D = 2.1 mm at X = 2.5 and X = 9.0 mm, Z = 2.0 mm
h1 = Part.makeCylinder(1.05, 10.0, App.Vector(2.5, -5.0, 2.0), App.Vector(0, 1, 0))
h2 = Part.makeCylinder(1.05, 10.0, App.Vector(9.0, -5.0, 2.0), App.Vector(0, 1, 0))
sw_body = sw_body.cut(h1).cut(h2)

# Little push button pin at X = 9.5 mm, Z = 6.5 mm
pin_button = Part.makeCylinder(1.20, 1.2, App.Vector(9.5, 0.0, 6.5), App.Vector(0, 0, 1))

# Stainless steel leaf lever (pinned at X = 2.0, extending to X = 15.0 at an angle)
lever_box = Part.makeBox(14.0, 4.0, 0.4, App.Vector(1.5, -2.0, 6.8))
lever_box.rotate(App.Vector(1.5, 0.0, 6.8), App.Vector(0, 1, 0), -6.0)

sw_solid = sw_body.fuse(pin_button).fuse(lever_box)

obj_sw = doc_sw.addObject("Part::Feature", "Microswitch_Subminiature")
obj_sw.Label = "Subminiature Microswitch (12.8x6.5x5.8 mm with Leaf Lever)"
obj_sw.Shape = sw_solid
doc_sw.recompute()
doc_sw.saveAs(fcstd_sw_path)
print(f"✔ Saved: {fcstd_sw_path}")

# =============================================================================
# 2. Build COTS: compression_spring_4x12.FCStd
# =============================================================================
print("2. Building COTS: compression_spring_4x12.FCStd...")
doc_sp_name = "compression_spring_4x12"
try:
    App.closeDocument(doc_sp_name)
except Exception:
    pass
doc_sp = App.newDocument(doc_sp_name)
fcstd_sp_path = f"{cots_dir}/compression_spring_4x12.FCStd"

# Simplified aesthetic model of compression spring: Da = 4.5 mm, Di = 3.3 mm, L = 12.0 mm
sp_outer = Part.makeCylinder(2.25, 12.0, App.Vector(0, 0, 0), App.Vector(0, 0, 1))
sp_inner = Part.makeCylinder(1.65, 14.0, App.Vector(0, 0, -1.0), App.Vector(0, 0, 1))
sp_tube = sp_outer.cut(sp_inner)

# Cut 6 helical pitch slots to create a visible spring coil appearance
for i in range(5):
    z_slot = 1.5 + i * 2.0
    slot_cutter = Part.makeBox(6.0, 1.0, 1.0, App.Vector(-3.0, -0.5, z_slot))
    slot_cutter.rotate(App.Vector(0, 0, z_slot), App.Vector(0, 0, 1), i * 45.0)
    sp_tube = sp_tube.cut(slot_cutter)

obj_sp = doc_sp.addObject("Part::Feature", "Compression_Spring")
obj_sp.Label = "Stainless Compression Spring (Da=4.5 mm, L=12 mm)"
obj_sp.Shape = sp_tube
doc_sp.recompute()
doc_sp.saveAs(fcstd_sp_path)
print(f"✔ Saved: {fcstd_sp_path}")

# =============================================================================
# 3. Build Concept Part: tibia_foot_shank.FCStd
# =============================================================================
print("3. Building Concept: tibia_foot_shank.FCStd...")
doc_shank_name = "tibia_foot_shank"
try:
    App.closeDocument(doc_shank_name)
except Exception:
    pass
doc_shank = App.newDocument(doc_shank_name)
fcstd_shank_path = f"{concept_dir}/tibia_foot_shank.FCStd"

# Geometry Frame:
# We model the distal ~75 mm segment of the Tibia shank oriented with:
# Shank axis running along Y (approx length 75 mm from Y = 0 to Y = 75 mm)
# Thickness along Z = 11.0 mm (Z in [-5.5, +5.5] mm)
# Width along X = 16.0 .. 22.0 mm
# Clevis slot is 6.0 mm wide (Z in [-3.0, +3.0] mm) spanning from Y = 0 to Y = 50 mm.

# 3.1 Outer Shank Solid
pts_shank_profile = [
    App.Vector(0.0, 0.0, 0.0),      # Tip lower corner
    App.Vector(18.0, 5.0, 0.0),     # Lower heel
    App.Vector(22.0, 35.0, 0.0),    # Mid dorsal bulge
    App.Vector(20.0, 75.0, 0.0),    # Upper shank rear
    App.Vector(2.0, 75.0, 0.0),     # Upper shank front
    App.Vector(3.0, 35.0, 0.0),     # Mid ventral arch
    App.Vector(0.0, 0.0, 0.0),
]
shank_wire = Part.makePolygon(pts_shank_profile)
shank_face = Part.Face(shank_wire)
shank_solid = shank_face.extrude(App.Vector(0.0, 0.0, 11.0))
shank_solid.translate(App.Vector(0.0, 0.0, -5.5))

# 3.2 Cut Clevis Fork Slot (Z in [-3.0, +3.0] mm, length Y in [-2.0, 52.0] mm)
clevis_cutter = Part.makeBox(30.0, 54.0, 6.0, App.Vector(-2.0, -2.0, -3.0))
shank_solid = shank_solid.cut(clevis_cutter)

# 3.3 Pivot Pin Bore (D = 3.2 mm) at (X = 9.0, Y = 12.0 mm)
pivot_x, pivot_y = 9.0, 12.0
pivot_bore = Part.makeCylinder(1.60, 20.0, App.Vector(pivot_x, pivot_y, -10.0), App.Vector(0, 0, 1))
# M3 Screw head counterbore on front cheek (Z in [3.0, 5.5]): D = 6.0 mm, depth = 2.0 mm
pivot_cbore = Part.makeCylinder(3.00, 3.0, App.Vector(pivot_x, pivot_y, 3.5), App.Vector(0, 0, 1))
# M3 Ruthex insert pocket on rear cheek (Z in [-5.5, -3.0]): D = 4.2 mm, depth = 4.0 mm
pivot_ruthex = Part.makeCylinder(2.10, 4.0, App.Vector(pivot_x, pivot_y, -5.5), App.Vector(0, 0, 1))
shank_solid = shank_solid.cut(pivot_bore).cut(pivot_cbore).cut(pivot_ruthex)

# 3.4 Microswitch Chamber (X in [5.0, 18.0], Y in [28.0, 41.5], Z in [-3.0, +3.0])
# 2x M2 screw holes through cheek (Z in [-6, +6]) at (X = 7.5, Y = 30.5) and (X = 14.0, Y = 30.5)
sw_mount_h1 = Part.makeCylinder(1.10, 20.0, App.Vector(7.5, 30.5, -10.0), App.Vector(0, 0, 1))
sw_mount_h2 = Part.makeCylinder(1.10, 20.0, App.Vector(14.0, 30.5, -10.0), App.Vector(0, 0, 1))
shank_solid = shank_solid.cut(sw_mount_h1).cut(sw_mount_h2)

# 3.5 Spring Blind Hole Pocket behind the Upper Lever Arm
# At X = 16.5, Y = 22.0, drilling towards -X into the rear spine
spring_pocket = Part.makeCylinder(2.40, 8.0, App.Vector(18.5, 22.0, 0.0), App.Vector(-1, 0, 0))
shank_solid = shank_solid.cut(spring_pocket)

# 3.6 Cable Exit Conduit running from switch bay up to shank top (Y = 75)
cable_tunnel = Part.makeCylinder(1.80, 40.0, App.Vector(10.0, 40.0, 0.0), App.Vector(0.1, 1.0, 0.0))
shank_solid = shank_solid.cut(cable_tunnel)

# 3.7 Outer Chamfers & Fillets on Cheek Tips for smooth terrain deflection
tip_chamfer1 = Part.makeBox(10.0, 10.0, 3.0, App.Vector(-2.0, -2.0, 4.0))
tip_chamfer2 = Part.makeBox(10.0, 10.0, 3.0, App.Vector(-2.0, -2.0, -7.0))
shank_solid = shank_solid.cut(tip_chamfer1).cut(tip_chamfer2)

obj_shank = doc_shank.addObject("Part::Feature", "Tibia_Foot_Shank")
obj_shank.Label = "Tibia Foot Clevis Shank (11 mm Monocoque Fork with Sensor Bay)"
obj_shank.Shape = shank_solid
doc_shank.recompute()
doc_shank.saveAs(fcstd_shank_path)
print(f"✔ Saved: {fcstd_shank_path}")

# =============================================================================
# 4. Build Concept Part: tibia_foot_rocker.FCStd
# =============================================================================
print("4. Building Concept: tibia_foot_rocker.FCStd...")
doc_rocker_name = "tibia_foot_rocker"
try:
    App.closeDocument(doc_rocker_name)
except Exception:
    pass
doc_rocker = App.newDocument(doc_rocker_name)
fcstd_rocker_path = f"{concept_dir}/tibia_foot_rocker.FCStd"

# Foot Rocker (Tarsus Wippe):
# Thickness = 5.6 mm (Z in [-2.8, +2.8]), fits inside the 6.0 mm clevis slot.
# Pinned at (X = 9.0, Y = 12.0).
# Lower arm: Sickle-curved ground contact claw extending from pivot to (X = -12.0, Y = -25.0)
# Upper arm: Actuator lever extending from pivot up to (X = 7.5, Y = 25.0) under the switch lever.

pts_rocker_2d = [
    # Pivot hub region
    App.Vector(12.5, 12.0, 0.0),
    # Upper lever arm leading to switch
    App.Vector(12.0, 22.0, 0.0),    # Rear face with spring seat
    App.Vector(8.5, 25.5, 0.0),     # Switch actuator tip
    App.Vector(6.0, 24.5, 0.0),     # Forward switch strike pad
    App.Vector(6.5, 16.0, 0.0),     # Front throat
    # Lower claw arm leading down to ground sole
    App.Vector(4.0, 5.0, 0.0),
    App.Vector(-3.0, -10.0, 0.0),
    App.Vector(-10.0, -22.0, 0.0),   # Ground contact apex
    App.Vector(-8.0, -25.0, 0.0),    # Tip rear
    App.Vector(0.0, -16.0, 0.0),
    App.Vector(8.0, -2.0, 0.0),
    App.Vector(12.5, 12.0, 0.0),
]
rocker_wire = Part.makePolygon(pts_rocker_2d)
rocker_face = Part.Face(rocker_wire)
rocker_solid = rocker_face.extrude(App.Vector(0.0, 0.0, 5.6))
rocker_solid.translate(App.Vector(0.0, 0.0, -2.8))

# 4.1 Pivot Bore (D = 3.1 mm) at (pivot_x, pivot_y)
r_bore = Part.makeCylinder(1.55, 10.0, App.Vector(pivot_x, pivot_y, -5.0), App.Vector(0, 0, 1))
rocker_solid = rocker_solid.cut(r_bore)

# 4.2 Spring Guide Boss on rear of upper arm at (X = 12.0, Y = 22.0)
spring_boss = Part.makeCylinder(1.50, 2.5, App.Vector(12.0, 22.0, 0.0), App.Vector(1, 0, 0))
rocker_solid = rocker_solid.fuse(spring_boss)

# 4.3 M2 Set Screw Pocket at Switch Actuator Tip (X = 7.5, Y = 25.0)
m2_screw_pocket = Part.makeCylinder(1.00, 6.0, App.Vector(7.5, 23.0, 0.0), App.Vector(0, 1, 0))
rocker_solid = rocker_solid.cut(m2_screw_pocket)

obj_rocker = doc_rocker.addObject("Part::Feature", "Tibia_Foot_Rocker")
obj_rocker.Label = "Tibia Foot Rocker Lever (Bionic Tarsus Wippe)"
obj_rocker.Shape = rocker_solid
doc_rocker.recompute()
doc_rocker.saveAs(fcstd_rocker_path)
print(f"✔ Saved: {fcstd_rocker_path}")

# =============================================================================
# 5. Build Concept Assembly: tibia_foot_assembly.FCStd
# =============================================================================
print("5. Building Concept Assembly: tibia_foot_assembly.FCStd...")
doc_asm_name = "tibia_foot_assembly"
try:
    App.closeDocument(doc_asm_name)
except Exception:
    pass
doc_asm = App.newDocument(doc_asm_name)
fcstd_asm_path = f"{concept_dir}/tibia_foot_assembly.FCStd"
doc_asm.saveAs(fcstd_asm_path)

# Main Assembly Part
asm_part = doc_asm.addObject("App::Part", "Tibia_Foot_Assembly")
asm_part.Label = "Lasius Tibia Foot Contact Sensor Assembly (Concept v2)"

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

# 1. Shank
p_shank = App.Placement(App.Vector(0, 0, 0), App.Rotation())
make_link("Tibia_Foot_Shank", "1. Tibia Foot Clevis Shank", obj_shank, p_shank, COLOR_CFRP)

# 2. Rocker Foot
p_rocker = App.Placement(App.Vector(0, 0, 0), App.Rotation())
make_link("Tibia_Foot_Rocker", "2. Bionic Tarsus Rocker Foot", obj_rocker, p_rocker, COLOR_ALU_ORANGE)

# 3. Microswitch
# Positioned at X = 5.0, Y = 28.0, Z = 0.0 with pins facing up
p_sw = App.Placement(App.Vector(5.0, 28.0, 0.0), App.Rotation(App.Vector(1, 0, 0), 90.0))
make_link("Microswitch", "3. Subminiature Microswitch (COTS)", obj_sw, p_sw, COLOR_SWITCH)

# 4. Compression Spring
# Positioned between spring boss (X=12) and shank blind hole (X=18.5) at Y = 22.0
p_sp = App.Placement(App.Vector(12.0, 22.0, 0.0), App.Rotation(App.Vector(0, 1, 0), 90.0))
make_link("Compression_Spring", "4. Stainless Preload Spring (COTS)", obj_sp, p_sp, COLOR_SPRING)

# 5. M3 Pivot Pin & Ruthex Hardware
pin_solid = Part.makeCylinder(1.50, 12.0, App.Vector(pivot_x, pivot_y, -5.5), App.Vector(0, 0, 1))
obj_pin = doc_asm.addObject("Part::Feature", "Pivot_Pin_M3")
obj_pin.Label = "5. M3 Hardened Pivot Pin & Ruthex"
obj_pin.Shape = pin_solid
asm_part.addObject(obj_pin)
if hasattr(obj_pin, "ViewObject") and obj_pin.ViewObject:
    try:
        obj_pin.ViewObject.ShapeColor = COLOR_BRASS
    except Exception:
        pass

doc_asm.recompute()
doc_asm.saveAs(fcstd_asm_path)
print(f"✔ Saved Assembly: {fcstd_asm_path}")

# Build compound shape for digital export
shapes = []
for obj in asm_part.Group:
    if hasattr(obj, "Shape") and not obj.Shape.isNull():
        shapes.append(obj.Shape)

step_path = f"{export_step_dir}/tibia_foot_assembly.step"
stl_path = f"{export_stl_dir}/tibia_foot_assembly.stl"

if shapes:
    compound = Part.makeCompound(shapes)
    compound.exportStep(step_path)
    compound.exportStl(stl_path)
    print(f"✔ Exported STEP: {step_path}")
    print(f"✔ Exported STL:  {stl_path}")

# Also build a Cross-Section model (half shank cut away to display internal kinematics)
print("6. Building Section View Concept...")
shank_section_solid = shank_solid.cut(Part.makeBox(50.0, 100.0, 10.0, App.Vector(-10.0, -10.0, 0.0)))
obj_shank_sec = doc_asm.addObject("Part::Feature", "Tibia_Shank_Cutaway")
obj_shank_sec.Label = "6. Shank Cutaway (Internal Kinematics Display)"
obj_shank_sec.Shape = shank_section_solid
obj_shank_sec.Visibility = False

doc_asm.recompute()
doc_asm.save()

# Close sub-documents
for d in [doc_sw, doc_sp, doc_shank, doc_rocker, doc_asm]:
    try:
        App.closeDocument(d.Name)
    except Exception:
        pass

# Ensure GuiDocument.xml has Visibility="true"
def patch_fcstd_visibility(filepath):
    temp_zip = filepath + ".tmp"
    with zipfile.ZipFile(filepath, "r") as zin:
        has_gui = "GuiDocument.xml" in zin.namelist()
        with zipfile.ZipFile(temp_zip, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "GuiDocument.xml":
                    xml_str = data.decode("utf-8")
                    xml_str = xml_str.replace('<Bool value="false"/>', '<Bool value="true"/>')
                    data = xml_str.encode("utf-8")
                zout.writestr(item, data)
    os.replace(temp_zip, filepath)

for pth in [fcstd_sw_path, fcstd_sp_path, fcstd_shank_path, fcstd_rocker_path, fcstd_asm_path]:
    if os.path.exists(pth):
        patch_fcstd_visibility(pth)

print("--- Tibia Foot Concept Models Generation Complete ---")
sys.exit(0)
