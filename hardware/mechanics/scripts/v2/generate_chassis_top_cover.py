#!/usr/bin/env python3
"""
Generate Lasius Hexapod Chassis Top Cover v2 FreeCAD Model (chassis_top_cover.FCStd)
===================================================================================
Purpose & Role:
  Parametric exoskeletal protective canopy / carapace (3D printed in lightweight PETG/ABS)
  mounted to the top surface of the chassis top plate (Z = 55.30 mm).

Key Functions & Features:
  1. Organic Insect Carapace (Chitinpanzer-Haube):
     - Aerodynamic, double-curved domed canopy enclosing the central chassis window
       (X in [-80, +80], Y in [-25, +25]) with an internal height clearance of 13.6 mm
       above the top plate (reaching Z = 71.30 mm).
     - Protects the Raspberry Pi 4 SoC, GPIO wiring, and internal electronics from dust,
       impact, and accidental touching.
  2. Thermal Convection Ventilation (Chevron-Louvers):
     - Array of 5x 45-degree forward-pointing chevron louvers directly above the Pi 4
       SoC/RAM (X in [25.0, 55.0], Y in [-14.0, +14.0]).
     - Direct chimney-effect thermal dissipation preventing heat accumulation.
  3. CSI Camera Ribbon Pass-through (Neck Interface):
     - Forward-facing horizontal cable slot (20.0 x 3.0 mm) at the front snout
       (X = 85.0 mm) guiding the camera ribbon cable directly to the head assembly.
  4. Four Flush M3 Standoff Mounts (X = ±45.0 mm, Y = ±30.0 mm):
     - Coaxial with the central chassis standoffs (spacer_14x50.FCStd).
     - Deepened counterbored screw pockets (Ø6.5 mm) for M3 socket-head / button-head screws.
"""

import math
import os
import FreeCAD as App
import Part

print("--- Generating Lasius Chassis Top Cover v2 (FreeCAD 1.1+) ---")

models_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/models/custom/v2/parts"
export_step_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/step/custom/v2/parts"
export_stl_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/stl/custom/v2/parts"

fcstd_cover_path = f"{models_dir}/chassis_top_cover.FCStd"
step_cover_path = f"{export_step_dir}/chassis_top_cover.step"
stl_cover_path = f"{export_stl_dir}/chassis_top_cover.stl"


def make_rounded_rect_solid(x_min, x_max, y_min, y_max, r_corner, z_min, z_max):
    """Constructs a filleted 3D solid prism."""
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
    """
    Creates a 45-degree forward-pointing chevron ventilation slot through the cover.
    """
    w = slot_width / 2.0
    d = arm_len / math.sqrt(2.0)
    # Chevron outline vertices (CCW)
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


def build_chassis_top_cover():
    # Z coordinate convention:
    # Lower mating flange sits on body_top top surface at Z = 55.30 mm.
    # Cover rises upward to Z = 76.00 mm (total height 20.7 mm, internal clearance 18.5 mm).
    z_base = 55.30
    z_peak = 76.00
    z_tier2 = 66.00
    wall_thick = 2.20

    # -------------------------------------------------------------------------
    # 1. Base Mounting Flange (X in [-88, 94], Y in [-36, 36], Z in [55.30, 58.50])
    # -------------------------------------------------------------------------
    flange_solid = make_rounded_rect_solid(-88.0, 94.0, -36.0, 36.0, 7.0, z_base, z_base + 3.20)

    # 4x Standoff Ears (X = ±45.0, Y = ±30.0)
    for sx in [-45.0, 45.0]:
        for sy in [-30.0, 30.0]:
            ear = Part.makeCylinder(9.5, 3.20, App.Vector(sx, sy, z_base), App.Vector(0, 0, 1))
            flange_solid = flange_solid.fuse(ear)

    # -------------------------------------------------------------------------
    # 2. Stepped Domed Carapace Vault (Organic Chitin Shell)
    # -------------------------------------------------------------------------
    # Mid-tier vault (X in [-84, 88], Y in [-33, 33], Z in [58.50, 66.00])
    tier2_solid = make_rounded_rect_solid(-84.0, 88.0, -33.0, 33.0, 6.0, z_base + 3.20, z_tier2)

    # Top-tier apex dome (X in [-76, 83], Y in [-30, 30], Z in [66.00, 76.00])
    tier3_solid = make_rounded_rect_solid(-76.0, 83.0, -30.0, 30.0, 5.0, z_tier2, z_peak)

    cover_solid = flange_solid.fuse(tier2_solid).fuse(tier3_solid)

    # -------------------------------------------------------------------------
    # 3. Hollow Internal Cavity (18.5 mm clearance above top plate, fits RPi 4)
    # -------------------------------------------------------------------------
    # Inner cavity ceiling at Z = 73.80 mm (leaves 2.2 mm solid ceiling at peak)
    cavity = make_rounded_rect_solid(-80.0, 81.0, -28.5, 28.5, 4.0, z_base - 2.0, z_peak - wall_thick)
    cover_solid = cover_solid.cut(cavity)

    # -------------------------------------------------------------------------
    # 4. Four M3 Mounting Holes with Counterbore (X = ±45.0, Y = ±30.0)
    # -------------------------------------------------------------------------
    for sx in [-45.0, 45.0]:
        for sy in [-30.0, 30.0]:
            # M3 through hole (Ø3.4 mm)
            thru_hole = Part.makeCylinder(1.70, 20.0, App.Vector(sx, sy, z_base - 2.0), App.Vector(0, 0, 1))
            # Deepened counterbored pocket (Ø6.6 mm, depth down to Z = 58.50 mm)
            cb_pocket = Part.makeCylinder(3.30, 25.0, App.Vector(sx, sy, z_base + 3.20), App.Vector(0, 0, 1))
            cover_solid = cover_solid.cut(thru_hole).cut(cb_pocket)

    # -------------------------------------------------------------------------
    # 5. Thermal Convection Ventilation Louvers (5x Chevron Slots above Pi 4 SoC)
    # -------------------------------------------------------------------------
    # Placed at X in [25.0, 55.0] (spacing 7.5 mm), span Y = [-13, +13]
    for dx in [25.0, 32.5, 40.0, 47.5, 55.0]:
        slot = make_chevron_slot(dx, 0.0, 10.0, 2.20, z_tier2 - 2.0, z_peak + 5.0)
        cover_solid = cover_solid.cut(slot)

    # -------------------------------------------------------------------------
    # 6. Camera Ribbon Pass-through Slot (Front Snout towards Head Assembly)
    # -------------------------------------------------------------------------
    # Centered at front X in [82.0, 94.0], Y in [-10.0, 10.0] (width 20.0 mm), Z in [57.0, 60.5]
    camera_slot = make_rounded_rect_solid(82.0, 94.0, -10.0, 10.0, 1.5, z_base + 1.80, z_base + 5.00)
    cover_solid = cover_solid.cut(camera_slot)

    return cover_solid


tray_solid = build_chassis_top_cover()

print(f"Chassis_Top_Cover Solid Valid: {tray_solid.isValid()}")
print(f"Faces: {len(tray_solid.Faces)}, Edges: {len(tray_solid.Edges)}")
print(f"Volume: {tray_solid.Volume:.2f} mm^3 (Area = {tray_solid.Area:.2f} mm^2)")
bb = tray_solid.BoundBox
print(f"Bounding Box: X=[{bb.XMin:.1f}, {bb.XMax:.1f}], Y=[{bb.YMin:.1f}, {bb.YMax:.1f}], Z=[{bb.ZMin:.1f}, {bb.ZMax:.1f}]")

os.makedirs(models_dir, exist_ok=True)
os.makedirs(export_step_dir, exist_ok=True)
os.makedirs(export_stl_dir, exist_ok=True)

doc_name = "chassis_top_cover"
try:
    App.closeDocument(doc_name)
except Exception:
    pass

doc = App.newDocument(doc_name)
obj = doc.addObject("Part::Feature", "Chassis_Top_Cover")
obj.Label = "Chassis Top Cover v2 (Exoskeletal Carapace + Thermal Louvers)"
obj.Shape = tray_solid

doc.recompute()
doc.saveAs(fcstd_cover_path)
print(f"Saved FreeCAD model: {fcstd_cover_path}")

obj.Shape.exportStep(step_cover_path)
obj.Shape.exportStl(stl_cover_path)
print(f"Exported STEP: {step_cover_path}")
print(f"Exported STL:  {stl_cover_path}")

App.closeDocument(doc_name)
import sys
sys.exit(0)
