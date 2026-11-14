#!/usr/bin/env python3
"""
Generate Lasius Femur Cover Concept Option 2: Flush Curved Cover with 45° Chevron Louvers
(hardware/mechanics/models/custom/v2/parts/femur/concepts/femur_cover_opt2.FCStd)
"""

import math
import os
import sys
import FreeCAD as App
import Part

print("--- Generating Lasius Femur Cover Option 2: Flush Louver Cover ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
concepts_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts/femur/concepts"
export_step_dir = f"{repo_root}/hardware/mechanics/export/step/custom/v2/parts/femur/concepts"
export_stl_dir = f"{repo_root}/hardware/mechanics/export/stl/custom/v2/parts/femur/concepts"

fcstd_path = f"{concepts_dir}/femur_cover_opt2.FCStd"
step_path = f"{export_step_dir}/femur_cover_opt2.step"
stl_path = f"{export_stl_dir}/femur_cover_opt2.stl"

os.makedirs(concepts_dir, exist_ok=True)
os.makedirs(export_step_dir, exist_ok=True)
os.makedirs(export_stl_dir, exist_ok=True)

Y_mid = 3.65
lid_z_floor = 9.00

screw_coords = [
    (31.8, Y_mid - 13.8),
    (31.8, Y_mid + 13.8),
    (68.2, Y_mid - 13.8),
    (68.2, Y_mid + 13.8),
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


# Outer envelope XZ
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

# Build flush cover solid:
cover_outer = make_rounded_rect_z(30.65, 69.35, Y_mid - 16.35, Y_mid + 16.35, 4.35, lid_z_floor, 20.0)
cover_solid = cover_outer.common(envelope_xz)

lip_outer = make_rounded_rect_z(33.70, 66.30, Y_mid - 13.30, Y_mid + 13.30, 3.30, lid_z_floor - 1.50, lid_z_floor)
lip_inner = make_rounded_rect_z(35.30, 64.70, Y_mid - 11.70, Y_mid + 11.70, 2.00, lid_z_floor - 1.60, lid_z_floor + 0.1)
lip_ring = lip_outer.cut(lip_inner)
for sx, sy in screw_coords:
    boss_clear = Part.makeCylinder(3.35, 2.0, App.Vector(sx, sy, lid_z_floor - 1.60))
    lip_ring = lip_ring.cut(boss_clear)
cover_solid = cover_solid.fuse(lip_ring)

for sx, sy in screw_coords:
    sh_through = Part.makeCylinder(1.10, 10.0, App.Vector(sx, sy, lid_z_floor - 2.0))
    sh_csink = Part.makeCone(1.10, 2.10, 1.0, App.Vector(sx, sy, lid_z_floor + 1.80))
    sh_head = Part.makeCylinder(2.10, 5.0, App.Vector(sx, sy, lid_z_floor + 2.80))
    cover_solid = cover_solid.cut(sh_through).cut(sh_csink).cut(sh_head)

for dx_slot in [-7.0, 0.0, 7.0]:
    slot = make_chevron_slot(50.0 + dx_slot, Y_mid, 5.5, 2.0, 45.0, lid_z_floor - 2.0, 20.0)
    cover_solid = cover_solid.cut(slot)

cover_solid = cover_solid.removeSplitter()

try:
    App.closeDocument("femur_cover_opt2")
except Exception:
    pass

doc = App.newDocument("femur_cover_opt2")
obj_cover = doc.addObject("Part::Feature", "Femur_Cover_Opt2")
obj_cover.Label = "Femur Cover Opt 2 (Flush Chevron Louver Lid, PETG)"
obj_cover.Shape = cover_solid

if hasattr(obj_cover, "ViewObject") and obj_cover.ViewObject is not None:
    obj_cover.ViewObject.Visibility = True
    obj_cover.ViewObject.ShapeColor = (0.15, 0.15, 0.18)

doc.recompute()
doc.saveAs(fcstd_path)
print(f"✔ Saved Concept Model: {fcstd_path}")

cover_solid.exportStep(step_path)
cover_solid.exportStl(stl_path)
print(f"✔ Exported STEP: {step_path}")
print(f"✔ Exported STL:  {stl_path}")

App.closeDocument("femur_cover_opt2")
