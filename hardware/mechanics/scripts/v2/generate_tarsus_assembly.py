#!/usr/bin/env python3
"""
Generate Lasius Tarsus v2 Canonical Parts & Subsystem Assembly
==============================================================
Canonical Output Paths (Hardware-as-Code 3-Tier Architecture):
- Custom v2 Tarsus Parts:
  * hardware/mechanics/models/custom/v2/parts/tarsus/tarsus.FCStd        (Tarsus)
  * hardware/mechanics/models/custom/v2/parts/tarsus/tarsus_shoe.FCStd   (Tarsus_Shoe)
- Custom v2 Tarsus Subassembly:
  * hardware/mechanics/models/custom/v2/tarsus_assembly.FCStd           (Tarsus_Assembly)
- Mirrored 1:1 in hardware/mechanics/export/{step,stl}/custom/v2/parts/tarsus/
"""

import math
import os
import sys
import zipfile
import xml.etree.ElementTree as ET
import FreeCAD as App
import Part

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models"
v2_dir = f"{models_dir}/custom/v2"
parts_tarsus_dir = f"{v2_dir}/parts/tarsus"

DO_EXPORT = ("--export" in sys.argv)

export_step_parts = f"{repo_root}/hardware/mechanics/export/step/custom/v2/parts/tarsus"
export_stl_parts = f"{repo_root}/hardware/mechanics/export/stl/custom/v2/parts/tarsus"

os.makedirs(parts_tarsus_dir, exist_ok=True)
if DO_EXPORT:
    for d in [export_step_parts, export_stl_parts]:
        os.makedirs(d, exist_ok=True)

# Colors
COLOR_ORANGE = (0.92, 0.45, 0.10)      # Anodized orange tarsus lever
COLOR_COVER = (0.28, 0.28, 0.32)       # Contrasting carbon / TPU shoe

print("--- Generating Lasius Tarsus v2 Canonical Parts & Assembly ---")

# =============================================================================
# 1. Build Canonical Tarsus: custom/v2/parts/tarsus/tarsus.FCStd
# =============================================================================
print("1. Building Canonical Part: tarsus.FCStd...")
try:
    App.closeDocument("tarsus")
except Exception:
    pass
doc_tarsus = App.newDocument("tarsus")
fcstd_tarsus_path = f"{parts_tarsus_dir}/tarsus.FCStd"

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
tarsus_wire = Part.Wire(all_edges)
tarsus_face = Part.Face(tarsus_wire)
tarsus_solid = tarsus_face.extrude(App.Vector(0.0, 0.0, 5.6)).translate(App.Vector(0.0, 0.0, -2.8))

# Pivot Bore (D = 3.10 mm, R = 1.55 mm) at (0.0, 10.0)
tarsus_solid = tarsus_solid.cut(Part.makeCylinder(1.55, 10.0, App.Vector(0.0, 10.0, -5.0), App.Vector(0, 0, 1)))
# Coaxial Retaining Bore (D = 2.00 mm, R = 1.00 mm) at (-8.50, -13.00) for locking Tarsus_Shoe
tarsus_solid = tarsus_solid.cut(Part.makeCylinder(1.00, 10.0, App.Vector(-8.50, -13.00, -5.0), App.Vector(0, 0, 1)))
# Enclosed Spring Boss at (-10.2, 10.60) (D = 2.80 mm, L = 2.50 mm up to Y = 13.10 mm; fits both 4.0 mm and 4.5 mm springs)
tarsus_solid = tarsus_solid.fuse(Part.makeCylinder(1.40, 2.50, App.Vector(-10.2, 10.60, 0.0), App.Vector(0, 1, 0)))
tarsus_solid = tarsus_solid.removeSplitter()

obj_tarsus = doc_tarsus.addObject("Part::Feature", "Tarsus")
obj_tarsus.Label = "Tarsus Foot Rocker Lever (Organic Bionic Tarsus, PETG)"
obj_tarsus.Shape = tarsus_solid
if hasattr(obj_tarsus, "ViewObject") and obj_tarsus.ViewObject is not None:
    obj_tarsus.ViewObject.Visibility = True
    obj_tarsus.ViewObject.ShapeColor = COLOR_ORANGE
doc_tarsus.recompute()
doc_tarsus.saveAs(fcstd_tarsus_path)
if DO_EXPORT:
    tarsus_solid.exportStep(f"{export_step_parts}/tarsus.step")
    tarsus_solid.exportStl(f"{export_stl_parts}/tarsus.stl")
print(f"✔ Saved: {fcstd_tarsus_path} (Valid={tarsus_solid.isValid()}, Volume={tarsus_solid.Volume:.1f} mm3)")

# =============================================================================
# 2. Build Canonical Slip-On Spoon Shoe: custom/v2/parts/tarsus/tarsus_shoe.FCStd
# =============================================================================
print("2. Building Canonical Part: tarsus_shoe.FCStd...")
try:
    App.closeDocument("tarsus_shoe")
except Exception:
    pass
doc_shoe = App.newDocument("tarsus_shoe")
fcstd_shoe_path = f"{parts_tarsus_dir}/tarsus_shoe.FCStd"

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

# 3. Form-fit internal cavity for the 5.60 mm flat Tarsus (with 0.06 mm clearance per face -> 5.72 mm slot):
tarsus_offset_wire = tarsus_wire.makeOffset2D(0.06)
cavity_core = Part.Face(tarsus_offset_wire).extrude(App.Vector(0.0, 0.0, 5.72)).translate(App.Vector(0.0, 0.0, -2.86))
entry_slot = Part.makeBox(14.50, 10.00, 5.72, App.Vector(-14.20, -11.80, -2.86))
tarsus_cavity = cavity_core.fuse(entry_slot)

# 4. Recessed 1.00 mm deep Spoon Pad Pocket on the underside:
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

shoe_solid = shoe_outer.cut(tarsus_cavity).cut(pad_recess).cut(shoe_pin_bore)
try:
    shoe_solid = shoe_solid.removeSplitter()
except Exception:
    pass

obj_shoe = doc_shoe.addObject("Part::Feature", "Tarsus_Shoe")
obj_shoe.Label = "Tarsus Slip-On Bionic Spoon Shoe (11.6 mm Width, Sole Pad Recess, TPU/PETG)"
obj_shoe.Shape = shoe_solid
if hasattr(obj_shoe, "ViewObject") and obj_shoe.ViewObject is not None:
    obj_shoe.ViewObject.Visibility = True
    obj_shoe.ViewObject.ShapeColor = COLOR_COVER
doc_shoe.recompute()
doc_shoe.saveAs(fcstd_shoe_path)
if DO_EXPORT:
    shoe_solid.exportStep(f"{export_step_parts}/tarsus_shoe.step")
    shoe_solid.exportStl(f"{export_stl_parts}/tarsus_shoe.stl")
print(f"✔ Saved: {fcstd_shoe_path} (Valid={shoe_solid.isValid()}, Volume={shoe_solid.Volume:.1f} mm3)")

# =============================================================================
# 3. Build Canonical Subsystem Assembly: custom/v2/tarsus_assembly.FCStd
# =============================================================================
print("3. Building Canonical Subsystem Assembly: custom/v2/tarsus_assembly.FCStd...")
doc_asm_name = "tarsus_assembly"
try:
    App.closeDocument(doc_asm_name)
except Exception:
    pass
fcstd_asm_path = f"{v2_dir}/tarsus_assembly.FCStd"
doc_asm = App.newDocument(doc_asm_name)
doc_asm.saveAs(fcstd_asm_path)

asm_part = doc_asm.addObject("App::Part", "Tarsus_Assembly")
asm_part.Label = "Lasius Tarsus v2 Subsystem Assembly"
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


# 1. Tarsus Rocker Lever
make_link("Tarsus", "1. Bionic Tarsus Rocker Lever (PETG)", obj_tarsus, App.Placement(), COLOR_ORANGE)

# 2. Tarsus Slip-On Spoon Shoe
make_link("Tarsus_Shoe", "2. Slip-On Bionic Spoon Shoe (TPU/PETG)", obj_shoe, App.Placement(), COLOR_COVER)

doc_asm.recompute()
doc_asm.save()
print(f"✔ Saved Canonical Assembly: {fcstd_asm_path}")

# =============================================================================
# 4. Pairwise 3D B-Rep Collision Verification
# =============================================================================
print("4. Running Pairwise 3D B-Rep Collision Check on tarsus_assembly.FCStd...")
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
    print(f"  ✅ ZERO COLLISIONS across all {len(items)} components in tarsus_assembly.FCStd (0.0000 mm^3)!")

for d in list(App.listDocuments().values()):
    try:
        App.closeDocument(d.Name)
    except Exception:
        pass


sys.exit(0)
