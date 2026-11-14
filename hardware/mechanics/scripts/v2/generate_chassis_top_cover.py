#!/usr/bin/env python3
"""
Generate Lasius Hexapod Central Electronics Top Cover v2 FreeCAD Model
(hardware/mechanics/models/custom/v2/parts/chassis_top_cover.FCStd)
====================================================================
Purpose:
  Central structural electronics enclosure (3D printed in anthracite PETG/ABS)
  protecting the Raspberry Pi 4 Model B, SoC heatsinks, and wiring.
  Docks under the transparent draped Plexiglas canopy (chassis_canopy.FCStd).

Geometry:
  - Footprint: Spans central chassis window (X in [-88.0, 92.0 mm], Y in [-35.0, 35.0 mm])
  - Height: Z = 55.30 mm to 74.50 mm (H = 19.2 mm, internal clearance 17.0 mm)
  - 4x M3 counterbored screw pockets at (±45.0, ±30.0 mm)
  - 4x internal M2.5 mounting bosses for Raspberry Pi 4
  - 5x 45-degree forward-pointing chevron convection louvers over Pi 4 SoC
  - CSI camera ribbon slot at front snout (X = 92.0 mm)
"""

import math
import os
import sys
import FreeCAD as App
import Part

print("--- Generating Central Electronics Top Cover v2 ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts/chassis"
fcstd_cover_path = f"{models_dir}/chassis_top_cover.FCStd"

def make_rounded_rect_solid(x_min, x_max, y_min, y_max, r_corner, z_min, z_max):
    dx = x_max - x_min
    dy = y_max - y_min
    r_corner = min(r_corner, dx / 2.0 - 0.1, dy / 2.0 - 0.1)
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
    v = [App.Vector(px, py, z_min) for px, py in pts]
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
    face = Part.Face(Part.Wire(edges))
    return face.extrude(App.Vector(0.0, 0.0, z_max - z_min))

def make_chevron_slot(x_center, y_center, arm_len, slot_width, z_min, z_max):
    w = slot_width / 2.0
    d = arm_len / math.sqrt(2.0)
    pts = [
        App.Vector(x_center + w, y_center, z_min),
        App.Vector(x_center - d + w, y_center + d, z_min),
        App.Vector(x_center - d - w, y_center + d, z_min),
        App.Vector(x_center - w, y_center, z_min),
        App.Vector(x_center - d - w, y_center - d, z_min),
        App.Vector(x_center - d + w, y_center - d, z_min),
    ]
    edges = [Part.makeLine(pts[i], pts[(i + 1) % 6]) for i in range(6)]
    face = Part.Face(Part.Wire(edges))
    return face.extrude(App.Vector(0.0, 0.0, z_max - z_min))

z_base = 55.30
z_peak = 74.50
z_tier2 = 65.00
wall_thick = 2.20

# 1. Base Mounting Flange (X in [-88, 92], Y in [-35, 35])
flange = make_rounded_rect_solid(-88.0, 92.0, -35.0, 35.0, 8.0, z_base, z_base + 3.20)

# Standoff ear lugs at (±45.0, ±30.0 mm)
for sx in [-45.0, 45.0]:
    for sy in [-30.0, 30.0]:
        lug = Part.makeCylinder(8.5, 3.20, App.Vector(sx, sy, z_base), App.Vector(0, 0, 1))
        flange = flange.fuse(lug)

# 2. Mid and Apex Vaults
mid_vault = make_rounded_rect_solid(-84.0, 88.0, -32.0, 32.0, 7.0, z_base + 3.20, z_tier2)
top_vault = make_rounded_rect_solid(-76.0, 80.0, -28.0, 28.0, 6.0, z_tier2, z_peak)

solid = flange.fuse(mid_vault).fuse(top_vault)

# 3. Internal Cavity (RPi 4 space)
cavity = make_rounded_rect_solid(-82.0, 82.0, -26.5, 26.5, 4.0, z_base - 1.0, z_peak - wall_thick)
solid = solid.cut(cavity)

# 4. M3 Screw Counterbores at (±45.0, ±30.0 mm)
for sx in [-45.0, 45.0]:
    for sy in [-30.0, 30.0]:
        thru = Part.makeCylinder(1.70, 25.0, App.Vector(sx, sy, z_base - 2.0), App.Vector(0, 0, 1))
        cb = Part.makeCylinder(3.30, 25.0, App.Vector(sx, sy, z_base + 3.20), App.Vector(0, 0, 1))
        solid = solid.cut(thru).cut(cb)

# 5. RPi 4 Integrated Mounting Bosses
rpi_bosses = [(6.0, 24.5), (6.0, -24.5), (64.0, 24.5), (64.0, -24.5)]
for bx, by in rpi_bosses:
    boss = Part.makeCylinder(3.0, (z_peak - wall_thick) - 57.50, App.Vector(bx, by, 57.50), App.Vector(0, 0, 1))
    pilot = Part.makeCylinder(1.10, 8.50, App.Vector(bx, by, 56.50), App.Vector(0, 0, 1))
    boss = boss.cut(pilot)
    solid = solid.fuse(boss)

# 6. Thermal Chevron Louvers
for dx in [25.0, 32.5, 40.0, 47.5, 55.0]:
    slot = make_chevron_slot(dx, 0.0, 10.0, 2.20, z_tier2 - 2.0, z_peak + 5.0)
    solid = solid.cut(slot)

# Note: Camera slot removed per user request (clean enclosed front)

doc_name = "chassis_top_cover"
try:
    App.closeDocument(doc_name)
except Exception:
    pass

doc = App.newDocument(doc_name)
obj = doc.addObject("Part::Feature", "Chassis_Top_Cover")
obj.Label = "Central Electronics Top Cover v2"
obj.Shape = solid
obj.Visibility = True

doc.recompute()
doc.saveAs(fcstd_cover_path)
print(f"Saved: {fcstd_cover_path}")
App.closeDocument(doc_name)
sys.exit(0)
