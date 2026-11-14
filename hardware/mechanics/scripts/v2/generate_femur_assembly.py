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
step_path = f"{export_step_dir}/femur_assembly.step"
stl_path = f"{export_stl_dir}/femur_assembly.stl"

os.makedirs(v2_dir, exist_ok=True)
os.makedirs(export_step_dir, exist_ok=True)
os.makedirs(export_stl_dir, exist_ok=True)

# Backup existing GuiDocument.xml if present to survive headless console saves
fallback_gui_xml = None
if os.path.exists(fcstd_path):
    try:
        with zipfile.ZipFile(fcstd_path, "r") as zin:
            if "GuiDocument.xml" in zin.namelist():
                fallback_gui_xml = zin.read("GuiDocument.xml")
    except Exception:
        pass

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
# Sits at X=50.00, Y=3.65 (Y_mid), Z=-4.80 mm
p_ads = App.Placement(App.Vector(50.00, 3.65, -4.80), App.Rotation())
make_link("ADS1115_Board", "2. Encapsulated Leg ADC (ADS1115 0x48)", doc_ads.ADS1115_Board, placement=p_ads, color=COLOR_ADC_BLUE)

# 3. Monolithic Service Cover & Canopy (Draped Convex Eisblau 55%)
make_link("Femur_Cover", "3. Femur Service Cover & Canopy (Monolithic Eisblau 55%)", doc_cover.Femur_Cover, color=COLOR_CANOPY, transparency=55)

doc.recompute()
doc.save()

# Build compound shape for digital export
shapes = []
for obj in asm_part.Group:
    if hasattr(obj, "Shape") and not obj.Shape.isNull():
        shapes.append(obj.Shape)

if shapes:
    compound = Part.makeCompound(shapes)
    compound.exportStep(step_path)
    compound.exportStl(stl_path)
    print(f"✔ Exported STEP: {step_path}")
    print(f"✔ Exported STL:  {stl_path}")

App.closeDocument(doc_femur.Name)
App.closeDocument(doc_cover.Name)
App.closeDocument(doc_ads.Name)
App.closeDocument(doc.Name)

# -------------------------------------------------------------
# 2. Patch GuiDocument.xml for full visibility and Plexiglas transparency if present
# -------------------------------------------------------------
gui_xml = None
with zipfile.ZipFile(fcstd_path, "r") as zin:
    has_gui = "GuiDocument.xml" in zin.namelist()
    if has_gui:
        gui_xml = zin.read("GuiDocument.xml").decode("utf-8")
    elif fallback_gui_xml:
        gui_xml = fallback_gui_xml.decode("utf-8")

if gui_xml:
    # Ensure all objects visible
    gui_xml = gui_xml.replace('<Property name="Visibility" type="App::PropertyBool" status="1">\n          <Bool value="false"/>',
                              '<Property name="Visibility" type="App::PropertyBool" status="1">\n          <Bool value="true"/>')
    gui_xml = gui_xml.replace('<Property name="Visibility" type="App::PropertyBool">\n          <Bool value="false"/>',
                              '<Property name="Visibility" type="App::PropertyBool">\n          <Bool value="true"/>')

    # Update cover canopy transparency to 55%
    canopy_view_search = '<ViewProvider name="Femur_Cover"'
    if canopy_view_search in gui_xml:
        idx = gui_xml.find(canopy_view_search)
        end_idx = gui_xml.find("</ViewProvider>", idx)
        block = gui_xml[idx:end_idx]
        if '<Property name="Transparency"' in block:
            block_new = block.replace(
                '<Property name="Transparency" type="App::PropertyPercent">\n          <Integer value="0"/>',
                '<Property name="Transparency" type="App::PropertyPercent">\n          <Integer value="55"/>'
            )
            gui_xml = gui_xml[:idx] + block_new + gui_xml[end_idx:]

    # Rewrite FCStd archive
    tmp_fcstd = fcstd_path + ".tmp"
    with zipfile.ZipFile(fcstd_path, "r") as zin, zipfile.ZipFile(tmp_fcstd, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == "GuiDocument.xml":
                zout.writestr(item, gui_xml.encode("utf-8"))
            else:
                zout.writestr(item, zin.read(item.filename))
        if "GuiDocument.xml" not in zin.namelist():
            zout.writestr("GuiDocument.xml", gui_xml.encode("utf-8"))
    os.replace(tmp_fcstd, fcstd_path)

print(f"✔ Saved Femur Assembly -> {fcstd_path}")
