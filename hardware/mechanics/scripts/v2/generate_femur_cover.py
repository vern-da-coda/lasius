#!/usr/bin/env python3
"""
Generate Lasius Femur Service Cover / Canopy (v2)
(hardware/mechanics/models/custom/v2/parts/femur/femur_cover.FCStd)
- Two-piece modular cockpit architecture:
  1. Femur_Cover_Frame: Graphitschwarz PETG bezel & sealing frame with 4x M2 countersunk screws
  2. Femur_Canopy: Translucent Ice-Blue 55% Alpha aerodynamic dome with Option C hold-down sleeves
  3. Femur_Cover: Compound of Frame + Canopy
- Matches the bionic design language of chassis_canopy.FCStd and chassis_service_cover.FCStd
"""

import math
import os
import sys
import zipfile
import FreeCAD as App
import Part

print("--- Generating Lasius Femur Service Cover (custom/v2/parts/femur/femur_cover.FCStd) ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts/femur"
export_step_dir = f"{repo_root}/hardware/mechanics/export/step/custom/v2/parts/femur"
export_stl_dir = f"{repo_root}/hardware/mechanics/export/stl/custom/v2/parts/femur"

fcstd_cover_path = f"{models_dir}/femur_cover.FCStd"
step_cover_path = f"{export_step_dir}/femur_cover.step"
stl_cover_path = f"{export_stl_dir}/femur_cover.stl"
stl_frame_path = f"{export_stl_dir}/femur_cover_frame.stl"
stl_canopy_path = f"{export_stl_dir}/femur_canopy.stl"

os.makedirs(models_dir, exist_ok=True)
os.makedirs(export_step_dir, exist_ok=True)
os.makedirs(export_stl_dir, exist_ok=True)

# Femur reference parameters
Y_mid = 3.65
lid_z_floor = 9.00
cover_z_base = lid_z_floor + 0.05

screw_coords = [
    (31.8, Y_mid - 13.8),
    (31.8, Y_mid + 13.8),
    (68.2, Y_mid - 13.8),
    (68.2, Y_mid + 13.8),
]

pin_coords = [
    (39.90, Y_mid + 5.30),
    (60.10, Y_mid + 5.30),
]


def make_rounded_rect_wire_z(x_min, x_max, y_min, y_max, r_corner, z_val):
    k = r_corner * (1.0 - 1.0 / math.sqrt(2.0))
    pts = [
        (x_min + r_corner, y_max),
        (x_max - r_corner, y_max),
        (x_max - k, y_max - k),
        (x_max, y_max - r_corner),
        (x_max, y_min + r_corner),
        (x_max - k, y_min + k),
        (x_max - r_corner, y_min),
        (x_min + r_corner, y_min),
        (x_min + k, y_min + k),
        (x_min, y_min + r_corner),
        (x_min, y_max - r_corner),
        (x_min + k, y_max - k),
    ]
    v = [App.Vector(px, py, z_val) for px, py in pts]
    edges = [
        Part.makeLine(v[0], v[1]),
        Part.Edge(Part.ArcOfCircle(v[1], v[2], v[3])),
        Part.makeLine(v[3], v[4]),
        Part.Edge(Part.ArcOfCircle(v[4], v[5], v[6])),
        Part.makeLine(v[6], v[7]),
        Part.Edge(Part.ArcOfCircle(v[7], v[8], v[9])),
        Part.makeLine(v[9], v[10]),
        Part.Edge(Part.ArcOfCircle(v[10], v[11], v[0])),
    ]
    return Part.Wire(edges)


def make_rounded_rect_z(x_min, x_max, y_min, y_max, r_corner, z_min, z_max):
    wire = make_rounded_rect_wire_z(x_min, x_max, y_min, y_max, r_corner, z_min)
    return Part.Face(wire).extrude(App.Vector(0.0, 0.0, z_max - z_min))


def make_chevron_slot(cx, cy, arm_len, width, angle_deg=45.0, z_min=7.0, z_max=20.0):
    rad = math.radians(angle_deg)
    dx = arm_len * math.cos(rad)
    dy = arm_len * math.sin(rad)
    r = 0.5 * width
    p_tip_front = App.Vector(cx + r, cy, z_min)
    p_left_out = App.Vector(cx - dx, cy + dy, z_min)
    p_left_in = App.Vector(cx - dx + width, cy + dy, z_min)
    p_tip_inner = App.Vector(cx - r, cy, z_min)
    p_right_in = App.Vector(cx - dx + width, cy - dy, z_min)
    p_right_out = App.Vector(cx - dx, cy - dy, z_min)
    wire = Part.Wire([
        Part.makeLine(p_tip_front, p_left_out),
        Part.makeLine(p_left_out, p_left_in),
        Part.makeLine(p_left_in, p_tip_inner),
        Part.makeLine(p_tip_inner, p_right_in),
        Part.makeLine(p_right_in, p_right_out),
        Part.makeLine(p_right_out, p_tip_front),
    ])
    return Part.Face(wire).extrude(App.Vector(0.0, 0.0, z_max - z_min))


# Outer envelope XZ matching femur hourglass profile
p_tl = App.Vector(0.0, 0.0, 15.80)
p_tr = App.Vector(100.0, 0.0, 15.80)
p_br = App.Vector(100.0, 0.0, -15.80)
p_bl = App.Vector(0.0, 0.0, -15.80)
p_top_mid = App.Vector(50.0, 0.0, 11.80)
p_bot_mid = App.Vector(50.0, 0.0, -11.80)
p_left_mid = App.Vector(-15.80, 0.0, 0.0)
p_right_mid = App.Vector(115.80, 0.0, 0.0)

e_xz_left = Part.Edge(Part.ArcOfCircle(p_tl, p_left_mid, p_bl))
e_xz_bot = Part.Edge(Part.ArcOfCircle(p_bl, p_bot_mid, p_br))
e_xz_right = Part.Edge(Part.ArcOfCircle(p_br, p_right_mid, p_tr))
e_xz_top = Part.Edge(Part.ArcOfCircle(p_tr, p_top_mid, p_tl))
xz_face = Part.Face(Part.Wire([e_xz_left, e_xz_bot, e_xz_right, e_xz_top]))
envelope_xz = xz_face.extrude(App.Vector(0.0, 72.0, 0.0))
envelope_xz.translate(App.Vector(0.0, -32.0, 0.0))

# -------------------------------------------------------------------------
# 1. Femur_Cover_Frame (Bezel / Clamping Ring in Graphitschwarz PETG)
# -------------------------------------------------------------------------
frame_outer = make_rounded_rect_z(28.65, 71.35, Y_mid - 17.35, Y_mid + 17.35, 3.85, cover_z_base, 20.0)
frame_solid = frame_outer.common(envelope_xz)

# Downward sealing / alignment lip ring:
lip_outer = make_rounded_rect_z(33.70, 66.30, Y_mid - 13.30, Y_mid + 13.30, 3.30, lid_z_floor - 1.50, cover_z_base + 0.10)
lip_inner = make_rounded_rect_z(35.30, 64.70, Y_mid - 11.70, Y_mid + 11.70, 2.00, lid_z_floor - 1.60, cover_z_base + 0.20)
frame_solid = frame_solid.fuse(lip_outer.cut(lip_inner))

# 4x M2 countersunk screws:
for sx, sy in screw_coords:
    sh_through = Part.makeCylinder(1.10, 10.0, App.Vector(sx, sy, cover_z_base - 1.0))
    sh_csink = Part.makeCone(1.10, 2.10, 1.0, App.Vector(sx, sy, cover_z_base + 1.80))
    sh_head = Part.makeCylinder(2.10, 10.0, App.Vector(sx, sy, cover_z_base + 2.80))
    frame_solid = frame_solid.cut(sh_through).cut(sh_csink).cut(sh_head)

# Flange pocket for canopy base:
flange_pocket = make_rounded_rect_z(33.60, 66.40, Y_mid - 11.80, Y_mid + 11.80, 3.30, cover_z_base - 0.50, 10.50)
frame_solid = frame_solid.cut(flange_pocket)

# Window opening:
frame_opening = make_rounded_rect_z(34.80, 65.20, Y_mid - 11.00, Y_mid + 11.00, 4.00, cover_z_base - 2.0, 25.0)
frame_solid = frame_solid.cut(frame_opening).removeSplitter()

# -------------------------------------------------------------------------
# 2. Femur_Canopy (Translucent Aerodynamic Canopy)
# -------------------------------------------------------------------------
canopy_base = make_rounded_rect_z(33.70, 66.30, Y_mid - 11.70, Y_mid + 11.70, 3.20, cover_z_base, 10.50)

w_c_out_0 = make_rounded_rect_wire_z(35.00, 65.00, Y_mid - 10.80, Y_mid + 10.80, 3.80, 10.50)
w_c_out_1 = make_rounded_rect_wire_z(35.20, 64.80, Y_mid - 10.50, Y_mid + 10.50, 3.50, 13.50)
w_c_out_2 = make_rounded_rect_wire_z(36.80, 63.20, Y_mid - 9.50, Y_mid + 9.50, 3.20, 17.00)
w_c_out_3 = make_rounded_rect_wire_z(39.80, 60.20, Y_mid - 8.00, Y_mid + 8.00, 2.80, 20.00)
w_c_out_4 = make_rounded_rect_wire_z(44.00, 56.00, Y_mid - 5.50, Y_mid + 5.50, 2.50, 22.00)
canopy_outer_dome = Part.makeLoft([w_c_out_0, w_c_out_1, w_c_out_2, w_c_out_3, w_c_out_4], True)
canopy_solid = canopy_base.fuse(canopy_outer_dome)

# Inner hollow cavity:
w_c_in_0 = make_rounded_rect_wire_z(35.50, 64.50, Y_mid - 9.50, Y_mid + 9.50, 2.50, cover_z_base - 0.10)
w_c_in_1 = make_rounded_rect_wire_z(36.50, 63.50, Y_mid - 8.80, Y_mid + 8.80, 2.20, 13.50)
w_c_in_2 = make_rounded_rect_wire_z(38.00, 62.00, Y_mid - 7.60, Y_mid + 7.60, 2.00, 17.00)
w_c_in_3 = make_rounded_rect_wire_z(41.00, 59.00, Y_mid - 6.00, Y_mid + 6.00, 1.80, 19.80)
canopy_inner_void = Part.makeLoft([w_c_in_0, w_c_in_1, w_c_in_2, w_c_in_3], True)
canopy_solid = canopy_solid.cut(canopy_inner_void)

# Option C Hold-Down Sleeves:
for px_pin, py_pin in pin_coords:
    hd_outer = Part.makeCylinder(2.10, 15.55, App.Vector(px_pin, py_pin, -3.05))
    hd_rib = Part.makeBox(2.40, 5.60, 5.00, App.Vector(px_pin - 1.20, py_pin, 7.60))
    hd_pin_clear = Part.makeCylinder(1.30, 4.00, App.Vector(px_pin, py_pin, -3.50))
    canopy_solid = canopy_solid.fuse(hd_outer).fuse(hd_rib).cut(hd_pin_clear)

# 3 subtle rounded 45-degree chevron louvers:
for dx_slot in [-7.0, 0.0, 7.0]:
    slot = make_chevron_slot(50.0 + dx_slot, Y_mid, 5.5, 2.0, 45.0, 19.0, 24.0)
    canopy_solid = canopy_solid.cut(slot)

canopy_solid = canopy_solid.removeSplitter()
cover_compound = Part.makeCompound([frame_solid, canopy_solid])

# -------------------------------------------------------------------------
# Save FreeCAD Document
# -------------------------------------------------------------------------
try:
    App.closeDocument("femur_cover")
except Exception:
    pass

doc = App.newDocument("femur_cover")

obj_frame = doc.addObject("Part::Feature", "Femur_Cover_Frame")
obj_frame.Label = "Femur ADC Chamber Cover Frame (PETG)"
obj_frame.Shape = frame_solid

obj_canopy = doc.addObject("Part::Feature", "Femur_Canopy")
obj_canopy.Label = "Femur ADC Chamber Canopy (Plexiglas Transluzent)"
obj_canopy.Shape = canopy_solid

obj_cover = doc.addObject("Part::Feature", "Femur_Cover")
obj_cover.Label = "Femur ADC Chamber Cover Assembly (Frame + Canopy)"
obj_cover.Shape = cover_compound

if hasattr(obj_frame, "ViewObject") and obj_frame.ViewObject is not None:
    obj_frame.ViewObject.Visibility = True
    obj_frame.ViewObject.ShapeColor = (0.15, 0.15, 0.18)

if hasattr(obj_canopy, "ViewObject") and obj_canopy.ViewObject is not None:
    obj_canopy.ViewObject.Visibility = True
    obj_canopy.ViewObject.ShapeColor = (0.85, 0.92, 0.98)
    obj_canopy.ViewObject.Transparency = 55

if hasattr(obj_cover, "ViewObject") and obj_cover.ViewObject is not None:
    obj_cover.ViewObject.Visibility = False

doc.recompute()
doc.saveAs(fcstd_cover_path)
print(f"✔ Saved FreeCAD Model: {fcstd_cover_path}")

cover_compound.exportStep(step_cover_path)
cover_compound.exportStl(stl_cover_path)
frame_solid.exportStl(stl_frame_path)
canopy_solid.exportStl(stl_canopy_path)

print(f"✔ Exported STEP: {step_cover_path}")
print(f"✔ Exported STLs: {stl_cover_path}, {stl_frame_path}, {stl_canopy_path}")

App.closeDocument("femur_cover")

# Patch GuiDocument.xml for Plexiglas transparency
temp_zip = fcstd_cover_path + ".tmp"
with zipfile.ZipFile(fcstd_cover_path, "r") as zin:
    with zipfile.ZipFile(temp_zip, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "GuiDocument.xml":
                xml_str = data.decode("utf-8")
                pos_canopy = xml_str.find('<ViewProvider name="Femur_Canopy"')
                if pos_canopy != -1:
                    end_vp = xml_str.find("</ViewProvider>", pos_canopy)
                    vp_chunk = xml_str[pos_canopy:end_vp]
                    if 'name="Transparency"' not in vp_chunk:
                        ins_pos = vp_chunk.find("</Properties>")
                        if ins_pos != -1:
                            transp_prop = '                <Property name="Transparency" type="App::PropertyPercent"><Integer value="55"/></Property>\n'
                            diffuse_prop = '                <Property name="ShapeColor" type="App::PropertyColor"><PropertyColor value="4042322175"/></Property>\n'
                            vp_chunk = vp_chunk[:ins_pos] + transp_prop + diffuse_prop + vp_chunk[ins_pos:]
                            xml_str = xml_str[:pos_canopy] + vp_chunk + xml_str[end_vp:]
                data = xml_str.encode("utf-8")
            zout.writestr(item, data)
os.replace(temp_zip, fcstd_cover_path)

print("--- Femur Cover Generated Successfully ---")
