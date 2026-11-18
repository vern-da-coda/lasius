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
  * hardware/mechanics/models/custom/v2/parts/tibia/tibia_rocker.FCStd (Tibia_Rocker)
  * hardware/mechanics/models/custom/v2/parts/tibia/tibia_shoe.FCStd   (Tibia_Shoe)
- Custom v2 Tibia Subassembly:
  * hardware/mechanics/models/custom/v2/tibia_assembly.FCStd           (Tibia_Assembly)
- Mirrored 1:1 in hardware/mechanics/export/{step,stl}/custom/v2/
"""

import math
import os
import sys
import zipfile
import xml.etree.ElementTree as ET
import FreeCAD as App
import Part

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
sys.path.append(f"{repo_root}/hardware/mechanics/scripts/v2")
import generate_tibia

print("--- Generating Lasius Tibia v2 Canonical Parts & Assembly ---")

models_dir = f"{repo_root}/hardware/mechanics/models"
cots_dir = f"{models_dir}/cots"
v2_dir = f"{models_dir}/custom/v2"
parts_tibia_dir = f"{v2_dir}/parts/tibia"

export_step_v2 = f"{repo_root}/hardware/mechanics/export/step/custom/v2"
export_stl_v2 = f"{repo_root}/hardware/mechanics/export/stl/custom/v2"
export_step_parts = f"{export_step_v2}/parts/tibia"
export_stl_parts = f"{export_stl_v2}/parts/tibia"

for d in [cots_dir, v2_dir, parts_tibia_dir, export_step_v2, export_stl_v2, export_step_parts, export_stl_parts]:
    os.makedirs(d, exist_ok=True)

# Colors
COLOR_CFRP = (0.22, 0.22, 0.24)        # Dark carbon anthracite
COLOR_COVER = (0.28, 0.28, 0.32)       # Contrasting carbon cover
COLOR_SERVO = (0.12, 0.12, 0.12)       # Matte black servo
COLOR_ORANGE = (0.92, 0.45, 0.10)      # Anodized orange rocker
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
# 2. Build Canonical Rocker: custom/v2/parts/tibia/tibia_rocker.FCStd
# =============================================================================
print("2. Building Canonical Part: tibia_rocker.FCStd...")
try:
    App.closeDocument("tibia_rocker")
except Exception:
    pass
doc_rocker = App.newDocument("tibia_rocker")
fcstd_rocker_path = f"{parts_tibia_dir}/tibia_rocker.FCStd"

p_hub_bot = App.Vector(3.60, 5.20, 0.0)
p_neck_top = App.Vector(-6.60, 3.60, 0.0)

# Structurally reinforced bionic Tarsus runner:
# - Neck width increased from 7.3 mm to 10.5 mm
# - Belly cross-section increased from 4.9 mm to 7.9 mm (+160% section modulus W_b)
# - Fore-foot cross-section increased from 3.4 mm to 5.6 mm (+170% section modulus W_b)
# - Distal tip increased from 2.1 mm to 3.4 mm (+165% section modulus W_b)
loc_sole = [
    p_hub_bot,
    App.Vector(2.20, -2.20, 0.0),
    App.Vector(-1.20, -10.50, 0.0),
    App.Vector(-6.20, -16.80, 0.0),
    App.Vector(-12.60, -19.60, 0.0),
    App.Vector(-19.80, -19.20, 0.0),
    App.Vector(-26.40, -17.00, 0.0),
]
loc_tip = [
    App.Vector(-26.40, -17.00, 0.0),
    App.Vector(-28.20, -15.30, 0.0),
    App.Vector(-26.80, -13.60, 0.0),
]
loc_top = [
    App.Vector(-26.80, -13.60, 0.0),
    App.Vector(-20.40, -13.60, 0.0),
    App.Vector(-14.20, -11.80, 0.0),
    App.Vector(-9.40, -7.50, 0.0),
    App.Vector(-7.00, -1.80, 0.0),
    p_neck_top,
]

c_sole = Part.BSplineCurve()
c_sole.interpolate(loc_sole)
e_sole = c_sole.toShape()
e_tip = Part.Arc(loc_tip[0], loc_tip[1], loc_tip[2]).toShape()
c_top = Part.BSplineCurve()
c_top.interpolate(loc_top)
e_top = c_top.toShape()

# Reinforced upper lever arm (h = 2.75 mm, X in [0.25, 3.00] for full 5 deg / 2.2 mm NC switch release travel),
# massive M3 pivot eye (R_hub = 4.60 mm -> 3.05 mm wall),
# and thickened internal spring arm (h = 3.8..4.5 mm, Y in [6.90, 10.60]) with notch-free transition to neck
pts_upper = [
    p_hub_bot,
    App.Vector(4.60, 9.20, 0.0),
    App.Vector(4.40, 12.50, 0.0),
    App.Vector(3.00, 18.0, 0.0),
    App.Vector(3.00, 34.5, 0.0),
    App.Vector(0.25, 34.5, 0.0),
    App.Vector(0.25, 30.2, 0.0),
    App.Vector(0.55, 29.0, 0.0),
    App.Vector(0.55, 24.0, 0.0),
    App.Vector(-2.0, 16.5, 0.0),
    App.Vector(-4.8, 13.8, 0.0),
    App.Vector(-7.5, 10.60, 0.0),
    App.Vector(-12.2, 10.60, 0.0),
    App.Vector(-12.2, 8.60, 0.0),
    App.Vector(-9.5, 7.00, 0.0),
    App.Vector(-7.2, 6.50, 0.0),
    p_neck_top,
]
edges_upper = [Part.makeLine(pts_upper[i], pts_upper[i + 1]) for i in range(len(pts_upper) - 1)]

all_edges = edges_upper + [e_top, e_tip, e_sole]
rocker_wire = Part.Wire(all_edges)
rocker_face = Part.Face(rocker_wire)
rocker_solid = rocker_face.extrude(App.Vector(0.0, 0.0, 5.6)).translate(App.Vector(0.0, 0.0, -2.8))

# Pivot Bore (D = 3.10 mm, R = 1.55 mm) at (0.0, 10.0)
rocker_solid = rocker_solid.cut(Part.makeCylinder(1.55, 10.0, App.Vector(0.0, 10.0, -5.0), App.Vector(0, 0, 1)))
# Coaxial Retaining Bore (D = 2.00 mm, R = 1.00 mm) at (-8.50, -13.00) for locking Tibia_Shoe
rocker_solid = rocker_solid.cut(Part.makeCylinder(1.00, 10.0, App.Vector(-8.50, -13.00, -5.0), App.Vector(0, 0, 1)))
# Enclosed Spring Boss at (-10.2, 10.60) (D = 2.80 mm, L = 2.50 mm up to Y = 13.10 mm; fits both 4.0 mm and 4.5 mm springs)
rocker_solid = rocker_solid.fuse(Part.makeCylinder(1.40, 2.50, App.Vector(-10.2, 10.60, 0.0), App.Vector(0, 1, 0)))
# Solid integrated actuation pad at Y_s in [30.2, 34.5], X_s = +0.25 mm directly presses the 1.2 mm wide D2FC-F-K(50M) plunger at Y_s = 32.5 mm
rocker_solid = rocker_solid.removeSplitter()

obj_rocker = doc_rocker.addObject("Part::Feature", "Tibia_Rocker")
obj_rocker.Label = "Tibia Foot Rocker Lever (Organic Bionic Tarsus Wippe, PETG)"
obj_rocker.Shape = rocker_solid
if hasattr(obj_rocker, "ViewObject") and obj_rocker.ViewObject is not None:
    obj_rocker.ViewObject.Visibility = True
    obj_rocker.ViewObject.ShapeColor = COLOR_ORANGE
doc_rocker.recompute()
doc_rocker.saveAs(fcstd_rocker_path)
rocker_solid.exportStep(f"{export_step_parts}/tibia_rocker.step")
rocker_solid.exportStl(f"{export_stl_parts}/tibia_rocker.stl")
print(f"✔ Saved: {fcstd_rocker_path} (Valid={rocker_solid.isValid()}, Volume={rocker_solid.Volume:.1f} mm3)")

# =============================================================================
# 2b. Build Canonical Slip-On Spoon Shoe: custom/v2/parts/tibia/tibia_shoe.FCStd
# =============================================================================
print("2b. Building Canonical Part: tibia_shoe.FCStd...")
try:
    App.closeDocument("tibia_shoe")
except Exception:
    pass
doc_shoe = App.newDocument("tibia_shoe")
fcstd_shoe_path = f"{parts_tibia_dir}/tibia_shoe.FCStd"

# 1. Side profile of the bionic spoon shoe (in X_s, Y_s plane, extruded along Z_s in [-7.0, +7.0]):
pts_shoe_sole = [
    App.Vector(-2.20, -12.60, 0.0),
    App.Vector(-6.40, -18.80, 0.0),
    App.Vector(-12.60, -21.60, 0.0),
    App.Vector(-19.80, -21.20, 0.0),
    App.Vector(-26.60, -19.00, 0.0),
]
pts_shoe_tip = [
    App.Vector(-26.60, -19.00, 0.0),
    App.Vector(-30.00, -15.30, 0.0),
    App.Vector(-27.00, -11.80, 0.0),
]
pts_shoe_top = [
    App.Vector(-27.00, -11.80, 0.0),
    App.Vector(-20.40, -11.80, 0.0),
    App.Vector(-14.20, -10.00, 0.0),
    App.Vector(-9.20, -6.80, 0.0),
    App.Vector(-5.80, -6.80, 0.0),
]
c_sh_sole = Part.BSplineCurve()
c_sh_sole.interpolate(pts_shoe_sole)
e_sh_sole = c_sh_sole.toShape()
e_sh_tip = Part.Arc(pts_shoe_tip[0], pts_shoe_tip[1], pts_shoe_tip[2]).toShape()
c_sh_top = Part.BSplineCurve()
c_sh_top.interpolate(pts_shoe_top)
e_sh_top = c_sh_top.toShape()
e_sh_heel = Part.makeLine(pts_shoe_top[-1], pts_shoe_sole[0])

shoe_side_wire = Part.Wire([e_sh_sole, e_sh_tip, e_sh_top, e_sh_heel])
shoe_side_solid = Part.Face(shoe_side_wire).extrude(App.Vector(0.0, 0.0, 14.0)).translate(App.Vector(0.0, 0.0, -7.0))

# 2. Top-view spoon / teardrop contour (in X_s, Z_s plane, extruded along Y_s in [-25.0, -4.0]):
#    Flares from 8.40 mm at the ankle entry (-1.80) to 11.60 mm across the spoon bowl (-17.00)
#    and rounds smoothly around the toe tip (-30.20)!
pts_spoon_pos = [
    App.Vector(-1.80, -25.0, 4.20),
    App.Vector(-6.00, -25.0, 4.65),
    App.Vector(-11.50, -25.0, 5.45),
    App.Vector(-17.00, -25.0, 5.80),
    App.Vector(-22.50, -25.0, 5.35),
    App.Vector(-27.00, -25.0, 4.10),
]
pts_spoon_neg = [App.Vector(p.x, p.y, -p.z) for p in reversed(pts_spoon_pos)]
c_sp_pos = Part.BSplineCurve()
c_sp_pos.interpolate(pts_spoon_pos)
c_sp_neg = Part.BSplineCurve()
c_sp_neg.interpolate(pts_spoon_neg)
e_sp_nose = Part.Arc(pts_spoon_pos[-1], App.Vector(-30.20, -25.0, 0.0), pts_spoon_neg[0]).toShape()
e_sp_back = Part.makeLine(pts_spoon_neg[-1], pts_spoon_pos[0])

spoon_plan_wire = Part.Wire([c_sp_pos.toShape(), e_sp_nose, c_sp_neg.toShape(), e_sp_back])
spoon_plan_solid = Part.Face(spoon_plan_wire).extrude(App.Vector(0.0, 22.0, 0.0))

shoe_outer = shoe_side_solid.common(spoon_plan_solid)

# 3. Form-fit internal cavity for the 5.60 mm flat Tibia_Rocker (with 0.06 mm clearance per face -> 5.72 mm slot):
#    - Closed toe cap in front of X_s = -14.20 wraps around the upturned Rocker tip
#    - Open top entry behind X_s = -14.20 allows sliding the Rocker into the toe cap and pivoting down to lock
rocker_offset_wire = rocker_wire.makeOffset2D(0.06)
cavity_core = Part.Face(rocker_offset_wire).extrude(App.Vector(0.0, 0.0, 5.72)).translate(App.Vector(0.0, 0.0, -2.86))
entry_slot = Part.makeBox(14.50, 10.00, 5.72, App.Vector(-14.20, -11.80, -2.86))
rocker_cavity = cavity_core.fuse(entry_slot)

# 4. Recessed 1.00 mm deep Spoon Pad Pocket on the underside (framed by a 1.50 mm protective rim for gluing a rubber/TPU pad):
pts_rec_sole_top = [
    App.Vector(-5.20, -16.70, 0.0),
    App.Vector(-8.50, -19.20, 0.0),
    App.Vector(-12.60, -20.60, 0.0),
    App.Vector(-19.80, -20.20, 0.0),
    App.Vector(-25.20, -18.30, 0.0),
]
c_rec_top = Part.BSplineCurve()
c_rec_top.interpolate(pts_rec_sole_top)
rec_side_wire = Part.Wire([
    c_rec_top.toShape(),
    Part.makeLine(pts_rec_sole_top[-1], App.Vector(-25.20, -25.0, 0.0)),
    Part.makeLine(App.Vector(-25.20, -25.0, 0.0), App.Vector(-5.20, -25.0, 0.0)),
    Part.makeLine(App.Vector(-5.20, -25.0, 0.0), pts_rec_sole_top[0]),
])
rec_side_solid = Part.Face(rec_side_wire).extrude(App.Vector(0.0, 0.0, 12.0)).translate(App.Vector(0.0, 0.0, -6.0))

pts_rec_pos = [
    App.Vector(-5.50, -25.0, 3.00),
    App.Vector(-11.50, -25.0, 3.95),
    App.Vector(-17.00, -25.0, 4.30),
    App.Vector(-22.00, -25.0, 3.85),
    App.Vector(-24.80, -25.0, 2.80),
]
pts_rec_neg = [App.Vector(p.x, p.y, -p.z) for p in reversed(pts_rec_pos)]
c_rp_pos = Part.BSplineCurve()
c_rp_pos.interpolate(pts_rec_pos)
c_rp_neg = Part.BSplineCurve()
c_rp_neg.interpolate(pts_rec_neg)
e_rp_nose = Part.Arc(pts_rec_pos[-1], App.Vector(-26.60, -25.0, 0.0), pts_rec_neg[0]).toShape()
e_rp_back = Part.Arc(pts_rec_neg[-1], App.Vector(-4.20, -25.0, 0.0), pts_rec_pos[0]).toShape()

rec_plan_wire = Part.Wire([c_rp_pos.toShape(), e_rp_nose, c_rp_neg.toShape(), e_rp_back])
rec_plan_solid = Part.Face(rec_plan_wire).extrude(App.Vector(0.0, 15.0, 0.0))
pad_recess = rec_side_solid.common(rec_plan_solid)

# 5. Coaxial D = 2.00 mm retaining pin hole at (-8.50, -13.00)
shoe_pin_bore = Part.makeCylinder(1.00, 14.0, App.Vector(-8.50, -13.00, -7.0), App.Vector(0, 0, 1))

shoe_solid = shoe_outer.cut(rocker_cavity).cut(pad_recess).cut(shoe_pin_bore)
try:
    shoe_solid = shoe_solid.removeSplitter()
except Exception:
    pass

obj_shoe = doc_shoe.addObject("Part::Feature", "Tibia_Shoe")
obj_shoe.Label = "Tibia Slip-On Bionic Spoon Shoe (11.6 mm Width, Sole Pad Recess, TPU/PETG)"
obj_shoe.Shape = shoe_solid
if hasattr(obj_shoe, "ViewObject") and obj_shoe.ViewObject is not None:
    obj_shoe.ViewObject.Visibility = True
    obj_shoe.ViewObject.ShapeColor = COLOR_COVER
doc_shoe.recompute()
doc_shoe.saveAs(fcstd_shoe_path)
shoe_solid.exportStep(f"{export_step_parts}/tibia_shoe.step")
shoe_solid.exportStl(f"{export_stl_parts}/tibia_shoe.stl")
print(f"✔ Saved: {fcstd_shoe_path} (Valid={shoe_solid.isValid()}, Volume={shoe_solid.Volume:.1f} mm3)")

# =============================================================================
# 3. Canonical Monolithic Tibia Body & Removable Cover
# =============================================================================
print("3. Loading Canonical Parts: tibia.FCStd & tibia_cover.FCStd...")
fcstd_mono_path = f"{parts_tibia_dir}/tibia.FCStd"
fcstd_cover_path = f"{parts_tibia_dir}/tibia_cover.FCStd"

doc_mono = App.openDocument(fcstd_mono_path)
obj_mono = doc_mono.Tibia_Body
obj_mono.Shape.exportStep(f"{export_step_parts}/tibia.step")
obj_mono.Shape.exportStl(f"{export_stl_parts}/tibia.stl")
print(f"✔ Verified & Exported: {fcstd_mono_path} (Valid={obj_mono.Shape.isValid()}, Volume={obj_mono.Shape.Volume:.1f} mm3)")

doc_cover = App.openDocument(fcstd_cover_path)
obj_cover = doc_cover.Tibia_Cover
obj_cover.Shape.exportStep(f"{export_step_parts}/tibia_cover.step")
obj_cover.Shape.exportStl(f"{export_stl_parts}/tibia_cover.stl")
print(f"✔ Verified & Exported: {fcstd_cover_path} (Valid={obj_cover.Shape.isValid()}, Volume={obj_cover.Shape.Volume:.1f} mm3)")

# =============================================================================
# 4. Build Canonical Subsystem Assembly: custom/v2/tibia_assembly.FCStd
# =============================================================================
print("4. Building Canonical Subsystem Assembly: custom/v2/tibia_assembly.FCStd...")
doc_asm_name = "tibia_assembly"
try:
    App.closeDocument(doc_asm_name)
except Exception:
    pass
fcstd_asm_path = f"{v2_dir}/tibia_assembly.FCStd"
doc_asm = App.newDocument(doc_asm_name)
doc_asm.saveAs(fcstd_asm_path)

doc_servo = App.openDocument(f"{cots_dir}/servo_nr645.FCStd")

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
p_servo = App.Placement(App.Vector(18.20, 15.25, -9.30), App.Rotation(App.Vector(0, 0, 1), 180.0))
make_link("Knee_Servo", "2. Knee Servo (Torcster NR-645 COTS)", doc_servo.Servo_Body, p_servo, COLOR_SERVO)

# 3. Bionic Foot Rocker & Shoe
# Exact verified foot placement in Tibia coordinate frame
p_shank = App.Placement(
    App.Vector(149.445, -2.56232, 9.0),
    App.Rotation(App.Vector(0, 0, 1), -112.4100084) * App.Rotation(App.Vector(1, 0, 0), 180.0),
)
make_link("Tibia_Rocker", "3. Bionic Tarsus Rocker Foot (+52% Lever, 5.6 mm Flat)", obj_rocker, p_shank, COLOR_ORANGE)
make_link("Tibia_Shoe", "3b. Slip-On Bionic Spoon Shoe (11.6 mm Width, Sole Pad Recess)", obj_shoe, p_shank, COLOR_COVER)

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
# 5. Pairwise 3D B-Rep Collision Verification
# =============================================================================
print("5. Running Pairwise 3D B-Rep Collision Check on tibia_assembly.FCStd...")
items = []
for obj in asm_part.Group:
    if hasattr(obj, "Shape") and not obj.Shape.isNull():
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

print("6. Running Kinematic Rocker + Spoon Shoe Stroke Sweep (0.0 deg to -5.0 deg ground compression)...")
s_body = doc_asm.getObject("Tibia_Body").Shape
s_cover = doc_asm.getObject("Tibia_Cover").Shape
s_sw = doc_asm.getObject("Microswitch").Shape
for deg in [0.0, -1.0, -2.0, -3.0, -4.0, -5.0]:
    r_local = App.Placement(App.Vector(0, 10, 0), App.Rotation(App.Vector(0, 0, 1), deg)).multiply(
        App.Placement(App.Vector(0, -10, 0), App.Rotation())
    )
    rk = rocker_solid.copy()
    rk.Placement = p_shank.multiply(r_local)
    sh = shoe_solid.copy()
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

def patch_fcstd_visibility(filepath):
    temp_zip = filepath + ".tmp"
    with zipfile.ZipFile(filepath, "r") as zin:
        names = zin.namelist()
        if "GuiDocument.xml" in names:
            xml_str = zin.read("GuiDocument.xml").decode("utf-8")
            xml_str = xml_str.replace('<Bool value="false"/>', '<Bool value="true"/>')
            gui_xml = xml_str.encode("utf-8")
        else:
            root = ET.fromstring(zin.read("Document.xml"))
            objs = []
            for obj in root.find("Objects"):
                name = obj.attrib.get("name") or obj.attrib.get("Name")
                if name and name not in objs:
                    objs.append(name)
            doc_elem = ET.Element("Document", SchemaVersion="1", HasExpansion="1")
            vp_data = ET.SubElement(doc_elem, "ViewProviderData", Count=str(len(objs)))
            for name in objs:
                vp = ET.SubElement(vp_data, "ViewProvider", name=name)
                props = ET.SubElement(vp, "Properties", Count="1")
                is_hidden = any(h in name for h in ["Origin", "Axis", "Plane"])
                val = "false" if is_hidden else "true"
                prop = ET.SubElement(props, "Property", name="Visibility", type="App::PropertyBool", status="1")
                ET.SubElement(prop, "Bool", value=val)
            gui_xml = ET.tostring(doc_elem, encoding="utf-8", xml_declaration=True)

        with zipfile.ZipFile(temp_zip, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename != "GuiDocument.xml":
                    zout.writestr(item, zin.read(item.filename))
            zout.writestr("GuiDocument.xml", gui_xml)
    os.replace(temp_zip, filepath)

patch_fcstd_visibility(fcstd_asm_path)
for p_path in [fcstd_mono_path, fcstd_cover_path, fcstd_rocker_path, fcstd_shoe_path]:
    if os.path.exists(p_path):
        patch_fcstd_visibility(p_path)
print("✔ Patched GuiDocument.xml for full visibility (Tibia Assembly & Parts)")

sys.exit(0)
