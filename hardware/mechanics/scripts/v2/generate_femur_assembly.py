#!/usr/bin/env python3
"""
Generate Lasius Femur Subassembly v2 (custom/v2/femur_assembly.FCStd)
- Encapsulates:
  1. Femur Monolithic Housing (Femur_Body, Mittelblau PETG)
  2. ADS1115 16-Bit I2C ADC Module (ADS1115_Board, Signalblau)
  3. Femur Cover Frame Bezel (Femur_Cover_Frame, Graphitschwarz PETG)
  4. Femur Mini-Canopy (Femur_Canopy, Eisblau-Transluzent 55%)
- Provides a clean L1 subassembly entry point for leg_assembly.FCStd
"""

import os
import zipfile
import FreeCAD as App
import Part

print("--- Generating Lasius Femur Assembly v2 (custom/v2/femur_assembly.FCStd) ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models"
v2_dir = f"{models_dir}/custom/v2"
parts_femur_dir = f"{v2_dir}/parts/femur"
cots_dir = f"{models_dir}/cots"
export_step_dir = f"{repo_root}/hardware/mechanics/export/step/custom/v2"
export_stl_dir = f"{repo_root}/hardware/mechanics/export/stl/custom/v2"

doc_name = "femur_assembly"
fcstd_path = f"{v2_dir}/femur_assembly.FCStd"

os.makedirs(v2_dir, exist_ok=True)

try:
    App.closeDocument(doc_name)
except Exception:
    pass

# Create and save assembly document immediately to establish relative link base
doc = App.newDocument(doc_name)
doc.saveAs(fcstd_path)

# Open source master documents
doc_femur = App.openDocument(f"{parts_femur_dir}/femur.FCStd")
doc_cover = App.openDocument(f"{parts_femur_dir}/femur_cover.FCStd")
doc_ads = App.openDocument(f"{cots_dir}/ads1115_board.FCStd")
doc_ins_m2 = App.openDocument(f"{cots_dir}/insert_m2_ruthex.FCStd")
doc_scr_m2 = App.openDocument(f"{cots_dir}/screw_m2_countersunk.FCStd")

# Main Assembly Container
asm_part = doc.addObject("App::Part", "Femur_Assembly_v2")
asm_part.Label = "Lasius Femur Assembly v2 (Monolithic Bone + Encapsulated ADC & Canopy)"
for o in asm_part.Origin.OutList:
    if hasattr(o, "Visibility"):
        o.Visibility = False
asm_part.Origin.Visibility = False
asm_part.Visibility = True


def make_link(name, label, target_obj, placement=None, color=None, transparency=0, parent=asm_part):
    lnk = doc.addObject("App::Link", name)
    lnk.setLink(target_obj)
    lnk.Label = label
    if placement is not None:
        lnk.Placement = placement
    parent.addObject(lnk)
    if hasattr(lnk, "ViewObject") and lnk.ViewObject is not None:
        vo = lnk.ViewObject
        vo.Visibility = True
        if color is not None:
            vo.OverrideMaterial = True
            mat = vo.ShapeMaterial
            mat.DiffuseColor = color
            vo.ShapeMaterial = mat
        if transparency > 0:
            vo.Transparency = transparency
    return lnk


# Component Colors & Styles
COLOR_FEMUR_BODY = (0.12, 0.35, 0.65)      # Technical Mittelblau PETG
COLOR_COVER_FRAME = (0.15, 0.15, 0.18)     # Graphitschwarz PETG Bezel
COLOR_CANOPY = (0.85, 0.92, 0.98)          # Eisblau Plexiglas / Acrylic
COLOR_ADC_BLUE = (0.04, 0.38, 0.88)        # Adafruit Signal Blue PCB

# -------------------------------------------------------------
# 1. Add Sub-Components to Femur Subassembly
# -------------------------------------------------------------
# 1. Femur bone structure
make_link("Femur_Body", "1. Femur Monolithic Housing (PETG)", doc_femur.Femur_Body, color=COLOR_FEMUR_BODY)

# 2. Encapsulated COTS ADC board clamped in internal chamber
# Sits at X=50.00, Y=2.50 (Y_mid), Z=-4.80 mm
p_ads = App.Placement(App.Vector(50.00, 2.50, -4.80), App.Rotation())
make_link("ADS1115_Board", "2. Encapsulated Leg ADC (ADS1115 0x48)", doc_ads.ADS1115_Board, placement=p_ads, color=None)

# 3. Monolithic Service Cover & Canopy (Draped Convex Eisblau 55%)
make_link("Femur_Cover", "3. Femur Service Cover & Canopy (Monolithic Eisblau 55%)", doc_cover.Femur_Cover, color=COLOR_CANOPY, transparency=55)

# 4. 4x Ruthex M2 Brass Heat-Set Inserts & 4x DIN 7991 M2 x 6 mm Countersunk Cover Screws (COTS)
COLOR_BRASS = (0.85, 0.70, 0.20)
COLOR_STEEL = (0.78, 0.80, 0.84)
Y_mid = 2.50
cover_screw_coords = [
    (31.8, Y_mid - 13.8),
    (31.8, Y_mid + 13.8),
    (68.2, Y_mid - 13.8),
    (68.2, Y_mid + 13.8),
]

grp_ins = doc.addObject("App::Part", "Cover_Inserts")
grp_ins.Label = "4. 4x Ruthex M2 Brass Heat-Set Inserts (COTS)"
for o in grp_ins.Origin.OutList:
    if hasattr(o, "Visibility"):
        o.Visibility = False
grp_ins.Origin.Visibility = False
grp_ins.Visibility = True
asm_part.addObject(grp_ins)

grp_scr = doc.addObject("App::Part", "Cover_Screws")
grp_scr.Label = "5. 4x DIN 7991 M2 x 6 mm Countersunk Cover Screws (COTS)"
for o in grp_scr.Origin.OutList:
    if hasattr(o, "Visibility"):
        o.Visibility = False
grp_scr.Origin.Visibility = False
grp_scr.Visibility = True
asm_part.addObject(grp_scr)

for idx, (sx, sy) in enumerate(cover_screw_coords, start=1):
    make_link(
        f"Femur_Insert_M2_{idx}",
        f"Ruthex M2 Insert #{idx} (Brass)",
        doc_ins_m2.Ruthex_M2_Insert,
        placement=App.Placement(App.Vector(sx, sy, 8.95), App.Rotation()),
        color=COLOR_BRASS,
        parent=grp_ins,
    )
    make_link(
        f"Femur_Screw_M2_{idx}",
        f"Cover Screw M2x6 #{idx} (DIN 7991)",
        doc_scr_m2.M2_Senkkopfschraube,
        placement=App.Placement(App.Vector(sx, sy, 11.83), App.Rotation()),
        color=COLOR_STEEL,
        parent=grp_scr,
    )

doc.recompute()
doc.save()
# Assemblies are logical structures, not exported to STEP/STL (never manufactured in one piece)
print(f"✔ Saved Femur Assembly: {fcstd_path}")

# Pairwise 3D B-Rep Collision Check
leaf_items = []
def _collect(obj, parent_pl=App.Placement()):
    pl = parent_pl.multiply(obj.Placement)
    for child in getattr(obj, "Group", []):
        if child.TypeId == "App::Part":
            _collect(child, pl)
        elif hasattr(child, "Shape") and not child.Shape.isNull():
            sh = child.Shape.copy()
            sh.Placement = pl.multiply(sh.Placement)
            leaf_items.append((f"{obj.Name}.{child.Name}", sh))

_collect(asm_part)
max_coll = 0.0
for i in range(len(leaf_items)):
    for j in range(i + 1, len(leaf_items)):
        n1, s1 = leaf_items[i]
        n2, s2 = leaf_items[j]
        if s1.BoundBox.intersect(s2.BoundBox):
            v = s1.common(s2).Volume
            if v > 1e-4:
                print(f"  ❌ COLLISION {n1} <-> {n2}: {v:.4f} mm^3")
                max_coll = max(max_coll, v)
if max_coll <= 1e-4:
    print(f"  ✅ ZERO COLLISIONS across all {len(leaf_items)} components in femur_assembly.FCStd (0.0000 mm^3)!")

for d in [doc_femur, doc_cover, doc_ads, doc_ins_m2, doc_scr_m2, doc]:
    try:
        App.closeDocument(d.Name)
    except Exception:
        pass

import sys
sys.exit(0)
