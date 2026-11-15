#!/usr/bin/env python3
"""
Generate Lasius Tibia Foot Sensor Concept v2 (Organic Bionic Tarsus)
=====================================================================
Parametric Generator for:
1. COTS: microswitch_subminiature.FCStd (12.8 x 6.5 x 5.8 mm with leaf lever)
2. COTS: compression_spring_4x12.FCStd (Da = 4.5 mm, L = 12.0 mm)
3. Concept Shank: tibia_foot_shank.FCStd (11.0 mm clevis fork, 6.0 mm internal slot,
   switch pocket, spring pocket, M3 Ruthex pivot)
4. Concept Rocker: tibia_foot_rocker.FCStd (5.6 mm thick bionic tarsus wippe with
   slender, organically smoothed claw sole that continues the Tibia dorsal sweep
   monotonically to the ground without any hump or snout)
5. Assembly: tibia_foot_assembly.FCStd (Kinematic assembly linking all components)
"""

import math
import os
import sys
import FreeCAD as App
import Part

print("--- Generating Lasius Tibia Foot Sensor Concept (Organic Bionic Tarsus) ---")

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
COLOR_CFRP = (0.22, 0.22, 0.24)        # Dark carbon / PETG shank
COLOR_ALU_ORANGE = (0.92, 0.45, 0.10)   # Anodized orange aluminum / PETG foot rocker
COLOR_SWITCH = (0.15, 0.15, 0.15)      # Black switch body
COLOR_LEVER = (0.80, 0.80, 0.82)       # Stainless steel lever
COLOR_SPRING = (0.85, 0.85, 0.88)      # Steel spring
COLOR_BRASS = (0.85, 0.70, 0.20)       # Brass Ruthex insert & pins

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

# Switch body: 12.8 x 6.5 x 5.8 mm
sw_body = Part.makeBox(6.5, 12.8, 5.8, App.Vector(0.0, 0.0, -2.9))
h1 = Part.makeCylinder(1.05, 10.0, App.Vector(4.5, 2.5, -5.0), App.Vector(0, 0, 1))
h2 = Part.makeCylinder(1.05, 10.0, App.Vector(4.5, 9.0, -5.0), App.Vector(0, 0, 1))
sw_body = sw_body.cut(h1).cut(h2)

pin_button = Part.makeCylinder(1.10, 1.2, App.Vector(6.5, 9.5, 0.0), App.Vector(1, 0, 0))
lever_box = Part.makeBox(0.4, 13.5, 4.0, App.Vector(6.7, 1.5, -2.0))

lug1 = Part.makeBox(2.5, 0.6, 2.0, App.Vector(-2.5, 1.5, -1.0))
lug2 = Part.makeBox(2.5, 0.6, 2.0, App.Vector(-2.5, 6.4, -1.0))
lug3 = Part.makeBox(2.5, 0.6, 2.0, App.Vector(-2.5, 11.3, -1.0))

sw_solid = sw_body.fuse(pin_button).fuse(lever_box).fuse(lug1).fuse(lug2).fuse(lug3)

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

sp_outer = Part.makeCylinder(2.25, 12.0, App.Vector(0, 0, 0), App.Vector(0, 1, 0))
sp_inner = Part.makeCylinder(1.65, 14.0, App.Vector(0, -1.0, 0), App.Vector(0, 1, 0))
sp_tube = sp_outer.cut(sp_inner)

for i in range(5):
    y_slot = 1.5 + i * 2.0
    slot_cutter = Part.makeBox(6.0, 1.0, 1.0, App.Vector(-3.0, y_slot - 0.5, -0.5))
    slot_cutter.rotate(App.Vector(0, y_slot, 0), App.Vector(0, 1, 0), i * 45.0)
    sp_tube = sp_tube.cut(slot_cutter)

obj_sp = doc_sp.addObject("Part::Feature", "Compression_Spring")
obj_sp.Label = "Stainless Compression Spring (Da=4.5 mm, L=12 mm)"
obj_sp.Shape = sp_tube
doc_sp.recompute()
doc_sp.saveAs(fcstd_sp_path)
print(f"✔ Saved: {fcstd_sp_path}")

# =============================================================================
# 3. Build Concept Part: tibia_foot_rocker.FCStd (Slender Organic Bionic Tarsus)
# =============================================================================
print("3. Building Concept: tibia_foot_rocker.FCStd...")
doc_rocker_name = "tibia_foot_rocker"
try:
    App.closeDocument(doc_rocker_name)
except Exception:
    pass
doc_rocker = App.newDocument(doc_rocker_name)
fcstd_rocker_path = f"{concept_dir}/tibia_foot_rocker.FCStd"

# Bionic Foot Rocker (Organic Tarsus Wippe):
# Thickness = 5.6 mm (Z in [-2.8, +2.8]), runs inside 6.0 mm slot.
# Pivot at (0.0, 10.0).
# Slender, predatory claw contour that continues the dorsal slope of the Tibia
# monotonically down-left without any upward hump!
p_spring_end = App.Vector(-14.0, 8.5, 0.0)
p_dorsal_1 = App.Vector(-17.7, -0.0, 0.0)
p_dorsal_2 = App.Vector(-20.5, -9.7, 0.0)
p_apex_top = App.Vector(-22.8, -20.0, 0.0)
p_tip_round = App.Vector(-20.3, -28.0, 0.0)
p_apex_bot = App.Vector(-16.3, -28.0, 0.0)
p_ventral_1 = App.Vector(-10.7, -20.0, 0.0)
p_ventral_2 = App.Vector(-5.5, -11.0, 0.0)
p_ventral_throat = App.Vector(-1.3, -3.5, 0.0)
p_hub_bot = App.Vector(1.2, 5.2, 0.0)

curve_dorsal = Part.BSplineCurve()
curve_dorsal.interpolate([p_spring_end, p_dorsal_1, p_dorsal_2, p_apex_top])
edge_dorsal = curve_dorsal.toShape()

arc_tip = Part.Arc(p_apex_top, p_tip_round, p_apex_bot).toShape()

curve_ventral = Part.BSplineCurve()
curve_ventral.interpolate([p_apex_bot, p_ventral_1, p_ventral_2, p_ventral_throat, p_hub_bot])
edge_ventral = curve_ventral.toShape()

pts_upper = [
    p_hub_bot,
    App.Vector(3.5, 12.0, 0.0),
    App.Vector(5.5, 18.0, 0.0),
    App.Vector(7.0, 26.0, 0.0),
    App.Vector(7.0, 35.0, 0.0),
    App.Vector(4.3, 35.0, 0.0),
    App.Vector(4.3, 24.0, 0.0),
    App.Vector(2.0, 16.0, 0.0),
    App.Vector(-2.0, 13.5, 0.0),
    App.Vector(-11.0, 8.5, 0.0),
    p_spring_end,
]
edges_upper = [Part.makeLine(pts_upper[i], pts_upper[i+1]) for i in range(len(pts_upper) - 1)]

all_edges = edges_upper + [edge_dorsal, arc_tip, edge_ventral]
rocker_wire = Part.Wire(all_edges)
rocker_face = Part.Face(rocker_wire)
rocker_solid = rocker_face.extrude(App.Vector(0.0, 0.0, 5.6)).translate(App.Vector(0.0, 0.0, -2.8))

# Pivot Bore (D = 3.1 mm) at (0.0, 10.0)
rocker_solid = rocker_solid.cut(Part.makeCylinder(1.55, 10.0, App.Vector(0.0, 10.0, -5.0), App.Vector(0, 0, 1)))

# Spring Boss at (-14.0, 8.5)
rocker_solid = rocker_solid.fuse(Part.makeCylinder(1.50, 2.5, App.Vector(-14.0, 8.5, 0.0), App.Vector(0, 1, 0)))

# M2 Set Screw Pocket at (4.3, 32.5)
rocker_solid = rocker_solid.cut(Part.makeCylinder(1.00, 6.0, App.Vector(4.3, 32.5, 0.0), App.Vector(-1, 0, 0)))

obj_rocker = doc_rocker.addObject("Part::Feature", "Tibia_Foot_Rocker")
obj_rocker.Label = "Tibia Foot Rocker Lever (Organic Bionic Tarsus Wippe)"
obj_rocker.Shape = rocker_solid
doc_rocker.recompute()
doc_rocker.saveAs(fcstd_rocker_path)
print(f"✔ Saved: {fcstd_rocker_path} (Volume={rocker_solid.Volume:.1f} mm3)")

# =============================================================================
# 4. Build Concept Part: tibia_foot_shank.FCStd
# =============================================================================
print("4. Building Concept: tibia_foot_shank.FCStd...")
doc_shank_name = "tibia_foot_shank"
try:
    App.closeDocument(doc_shank_name)
except Exception:
    pass
doc_shank = App.newDocument(doc_shank_name)
fcstd_shank_path = f"{concept_dir}/tibia_foot_shank.FCStd"

pts_shank = [
    App.Vector(3.0, -3.0, 0.0),
    App.Vector(6.0, 6.0, 0.0),
    App.Vector(8.5, 20.0, 0.0),
    App.Vector(9.0, 36.0, 0.0),
    App.Vector(6.0, 52.0, 0.0),
    App.Vector(4.0, 75.0, 0.0),
    App.Vector(-14.0, 75.0, 0.0),
    App.Vector(-16.0, 52.0, 0.0),
    App.Vector(-20.0, 32.0, 0.0),
    App.Vector(-20.0, 14.0, 0.0),
    App.Vector(-18.0, 2.0, 0.0),
    App.Vector(-14.0, -3.0, 0.0),
    App.Vector(3.0, -3.0, 0.0),
]
shank_wire = Part.makePolygon(pts_shank)
shank_solid = Part.Face(shank_wire).extrude(App.Vector(0.0, 0.0, 11.0)).translate(App.Vector(0.0, 0.0, -5.5))

slot_upper = Part.makeBox(12.0, 35.0, 6.0, App.Vector(-2.0, 8.0, -3.0))
slot_claw = Part.makeBox(45.0, 48.0, 6.0, App.Vector(-40.0, -32.0, -3.0))
sw_pocket = Part.makeBox(10.5, 16.5, 6.0, App.Vector(-5.5, 22.0, -3.0))
spring_pocket = Part.makeCylinder(2.40, 12.0, App.Vector(-14.0, 11.0, 0.0), App.Vector(0, 1, 0))
cable_conduit = Part.makeCylinder(1.80, 45.0, App.Vector(0.0, 35.0, 0.0), App.Vector(-0.15, 1.0, 0.0))
pivot_bore = Part.makeCylinder(1.60, 20.0, App.Vector(0.0, 10.0, -10.0), App.Vector(0, 0, 1))
pivot_cbore = Part.makeCylinder(3.00, 3.0, App.Vector(0.0, 10.0, 3.5), App.Vector(0, 0, 1))
pivot_ruthex = Part.makeCylinder(2.10, 4.0, App.Vector(0.0, 10.0, -5.5), App.Vector(0, 0, 1))
sw_hole1 = Part.makeCylinder(1.10, 20.0, App.Vector(2.1, 25.5, -10.0), App.Vector(0, 0, 1))
sw_hole2 = Part.makeCylinder(1.10, 20.0, App.Vector(2.1, 32.0, -10.0), App.Vector(0, 0, 1))

shank_solid = shank_solid.cut(slot_upper).cut(slot_claw).cut(sw_pocket).cut(spring_pocket).cut(cable_conduit).cut(pivot_bore).cut(pivot_cbore).cut(pivot_ruthex).cut(sw_hole1).cut(sw_hole2)

obj_shank = doc_shank.addObject("Part::Feature", "Tibia_Foot_Shank")
obj_shank.Label = "Tibia Foot Clevis Shank (11 mm Fork)"
obj_shank.Shape = shank_solid
doc_shank.recompute()
doc_shank.saveAs(fcstd_shank_path)
print(f"✔ Saved: {fcstd_shank_path}")

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

p_shank = App.Placement(App.Vector(0, 0, 0), App.Rotation())
make_link("Tibia_Foot_Shank", "1. Tibia Foot Clevis Shank", obj_shank, p_shank, COLOR_CFRP)
make_link("Tibia_Foot_Rocker", "2. Organic Bionic Rocker Foot", obj_rocker, p_shank, COLOR_ALU_ORANGE)

p_sw = App.Placement(App.Vector(4.3 - 6.7, 23.0, 0.0), App.Rotation())
make_link("Microswitch", "3. Subminiature Microswitch (COTS)", obj_sw, p_sw, COLOR_SWITCH)

p_sp = App.Placement(App.Vector(-14.0, 8.5, 0.0), App.Rotation())
make_link("Compression_Spring", "4. Stainless Preload Spring (COTS)", obj_sp, p_sp, COLOR_SPRING)

pin_obj = doc_asm.addObject("Part::Feature", "Pivot_Pin_Assembly")
pin_obj.Label = "5. M3 Hardened Pivot Pin & Ruthex"
pin_head = Part.makeCylinder(2.8, 2.0, App.Vector(0.0, 10.0, 3.5), App.Vector(0, 0, 1))
pin_shaft = Part.makeCylinder(1.5, 11.0, App.Vector(0.0, 10.0, -5.5), App.Vector(0, 0, 1))
ruthex = Part.makeCylinder(2.1, 4.0, App.Vector(0.0, 10.0, -5.5), App.Vector(0, 0, 1))
pin_solid = pin_head.fuse(pin_shaft).fuse(ruthex)
pin_obj.Shape = pin_solid
asm_part.addObject(pin_obj)

# Section cutaway for display
cutaway_box = Part.makeBox(80.0, 100.0, 10.0, App.Vector(-40.0, -10.0, 0.0))
shank_cutaway_solid = shank_solid.cut(cutaway_box)
shank_cutaway_obj = doc_asm.addObject("Part::Feature", "Tibia_Shank_Cutaway")
shank_cutaway_obj.Label = "6. Shank Cutaway (Internal Kinematics Display)"
shank_cutaway_obj.Shape = shank_cutaway_solid
shank_cutaway_obj.Visibility = False

doc_asm.recompute()
doc_asm.saveAs(fcstd_asm_path)
print(f"✔ Saved: {fcstd_asm_path}")

# =============================================================================
# 6. Verification & Collision Checks
# =============================================================================
print("6. Running Collision and Kinematic Checks...")
sw_shape = obj_sw.Shape.copy()
sw_shape.Placement = p_sw.multiply(sw_shape.Placement)
rocker_shape = obj_rocker.Shape.copy()
rocker_shape.Placement = p_shank.multiply(rocker_shape.Placement)
sp_shape = obj_sp.Shape.copy()
sp_shape.Placement = p_sp.multiply(sp_shape.Placement)
shank_shape = obj_shank.Shape.copy()

coll_shank_rocker = shank_shape.common(rocker_shape).Volume
coll_sw_spring = sw_shape.common(sp_shape).Volume
print(f"  Collision Shank <-> Rocker: {coll_shank_rocker:.4f} mm3")
print(f"  Collision Switch <-> Spring: {coll_sw_spring:.4f} mm3")

# =============================================================================
# 7. Export STEP & STL
# =============================================================================
print("7. Exporting STEP and STL...")
step_asm_path = f"{export_step_dir}/tibia_foot_assembly.step"
stl_asm_path = f"{export_stl_dir}/tibia_foot_assembly.stl"
export_objs = [obj_shank, obj_rocker, obj_sw, obj_sp, pin_obj]
Part.export(export_objs, step_asm_path)
print(f"✔ Exported STEP: {step_asm_path}")

comp = Part.Compound([o.Shape for o in export_objs])
comp.exportStl(stl_asm_path)
print(f"✔ Exported STL: {stl_asm_path}")

print("=== Foot Concept Generation Complete! ===")
