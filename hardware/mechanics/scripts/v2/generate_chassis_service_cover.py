#!/usr/bin/env python3
"""
Generate Lasius Hexapod Service Cover v2 FreeCAD Model
(hardware/mechanics/models/custom/v2/parts/chassis_service_cover.FCStd)
========================================================================
Design Concept (Zentrierte Service-Abdeckung direkt über dem Raspberry Pi 4):
  1. Service Access Lid:
     - Removable maintenance hatch sitting directly over the Raspberry Pi 4 Model B
       at X = 0.0, Y = 0.0 mm.
     - Matches the exact length (89.0 mm, X in [-43.5, +45.5 mm]) and width
       (57.0 mm, Y in [-28.5, +28.5 mm]) of the Pi 4 board footprint directly beneath it.
     - Drops into the service opening rebate of the draped Plexiglas canopy
       (chassis_canopy.FCStd) at Z = 80.20 mm, crowning to Z = 85.00 mm.
     - Allows instant access to the Pi 4 (SD card, GPIO pins, camera cable,
       fan, and ports) without removing the entire robot canopy.
  2. Bionic Rounded '>>>' Thermal Convection Chevron Louvers (Femur Cover Matched):
     - 5x 45-degree forward-pointing chevron ventilation slots across
       X in [-15.0, +15.0 mm] (step 7.5 mm) directly above the BCM2711 quad-core SoC.
     - Modeled with rounded pill/capsule arms matching the exact design and rounded geometry
       from the Femur cover (generate_femur.py).
  3. Internal Headroom:
     - Deep inner clearance cavity (Z = 76.0 .. 83.5 mm) providing 6.3 mm headroom
       over tallest Pi 4 components (USB & Ethernet jacks at Z = 77.20 mm).
"""

import math
import os
import sys
import zipfile
import FreeCAD as App
import Part

print("--- Generating Lasius Service Cover v2 (FreeCAD 1.1+) ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts/chassis"
fcstd_cover_path = f"{models_dir}/chassis_service_cover.FCStd"

os.makedirs(models_dir, exist_ok=True)


def make_filleted_wire(x_min, x_max, y_min, y_max, r, z):
    """Constructs a smooth 8-edge G1-continuous filleted rectangular wire at height Z."""
    dx = x_max - x_min
    dy = y_max - y_min
    r = min(r, dx / 2.0 - 0.1, dy / 2.0 - 0.1)
    pts = [
        App.Vector(x_max - r, y_max, z),
        App.Vector(x_min + r, y_max, z),
        App.Vector(x_min, y_max - r, z),
        App.Vector(x_min, y_min + r, z),
        App.Vector(x_min + r, y_min, z),
        App.Vector(x_max - r, y_min, z),
        App.Vector(x_max, y_min + r, z),
        App.Vector(x_max, y_max - r, z),
    ]
    edges = [
        Part.makeLine(pts[0], pts[1]),
        Part.Edge(Part.ArcOfCircle(pts[1], App.Vector(x_min + r * (1 - 1 / math.sqrt(2)), y_max - r * (1 - 1/math.sqrt(2)), z), pts[2])),
        Part.makeLine(pts[2], pts[3]),
        Part.Edge(Part.ArcOfCircle(pts[3], App.Vector(x_min + r * (1 - 1 / math.sqrt(2)), y_min + r * (1 - 1/math.sqrt(2)), z), pts[4])),
        Part.makeLine(pts[4], pts[5]),
        Part.Edge(Part.ArcOfCircle(pts[5], App.Vector(x_max - r * (1 - 1 / math.sqrt(2)), y_min + r * (1 - 1/math.sqrt(2)), z), pts[6])),
        Part.makeLine(pts[6], pts[7]),
        Part.Edge(Part.ArcOfCircle(pts[7], App.Vector(x_max - r * (1 - 1 / math.sqrt(2)), y_max - r * (1 - 1/math.sqrt(2)), z), pts[0])),
    ]
    return Part.Wire(edges)


def make_rounded_rect_solid(x_min, x_max, y_min, y_max, r_corner, z_min, z_max):
    """Constructs a filleted 3D solid prism."""
    wire = make_filleted_wire(x_min, x_max, y_min, y_max, r_corner, z_min)
    return Part.Face(wire).extrude(App.Vector(0.0, 0.0, z_max - z_min))


def make_chevron_slot(cx, cy, arm_len, width, angle_deg=45.0, z_min=75.0, z_max=88.0):
    """
    Construct a 45-degree chevron inspection/ventilation slot with rounded pill ends,
    matching the exact design and rounding from the Femur cover (generate_femur.py).
    """
    rad = math.radians(angle_deg)
    dx = arm_len * math.cos(rad)
    dy = arm_len * math.sin(rad)
    p_apex = App.Vector(cx, cy, z_min)
    p_top = App.Vector(cx - dx, cy + dy, z_min)
    p_bot = App.Vector(cx - dx, cy - dy, z_min)

    def make_pill(p1, p2, r):
        v = (p2 - p1).normalize()
        n = App.Vector(-v.y, v.x, 0.0) * r
        c1 = Part.makeCylinder(r, z_max - z_min, p1)
        c2 = Part.makeCylinder(r, z_max - z_min, p2)
        pts = [p1 + n, p2 + n, p2 - n, p1 - n, p1 + n]
        box = Part.Face(Part.makePolygon(pts)).extrude(App.Vector(0, 0, z_max - z_min))
        return box.fuse(c1).fuse(c2)

    r = 0.5 * width
    pill1 = make_pill(p_apex, p_top, r)
    pill2 = make_pill(p_apex, p_bot, r)
    return pill1.fuse(pill2)


def build_service_cover():
    z_rebate = 80.20
    z_apex = 85.00

    # 1. Outer Overlapping Seating Flange & Domed Crown
    # Directly over the Raspberry Pi 4 in matching length (89.0 mm) and width (57.0 mm)
    lid_top = make_rounded_rect_solid(-43.5, 45.5, -28.5, 28.5, 5.0, z_rebate + 0.05, z_apex)

    # 2. Mating Locating Lip (Slots down into the canopy aperture)
    lid_lip = make_rounded_rect_solid(-41.5, 43.5, -26.5, 26.5, 3.5, z_rebate - 1.70, z_rebate + 0.5)
    hatch = lid_lip.fuse(lid_top)

    # 3. Inner Clearance Cavity (Leaves generous 6.3 mm headroom for USB/Ethernet and SoC heatsink)
    cavity = make_rounded_rect_solid(-39.5, 41.5, -24.5, 24.5, 2.5, 76.0, z_apex - 1.5)
    hatch = hatch.cut(cavity)

    # 4. Bionic Rounded '>>>' Chevron Louvers (5x centered directly over BCM2711 SoC, matching Femur Cover)
    for dx in [-15.0, -7.5, 0.0, 7.5, 15.0]:
        slot = make_chevron_slot(dx, 0.0, 10.0, 2.40, 45.0, 75.0, z_apex + 2.0)
        hatch = hatch.cut(slot)

    return hatch


cover_solid = build_service_cover()
print(f"Service Cover Solid Valid: {cover_solid.isValid()}")
print(f"Faces: {len(cover_solid.Faces)}, Edges: {len(cover_solid.Edges)}")
print(f"Volume: {cover_solid.Volume:.2f} mm^3")
bb = cover_solid.BoundBox
print(f"BoundBox: X=[{bb.XMin:.1f}, {bb.XMax:.1f}], Y=[{bb.YMin:.1f}, {bb.YMax:.1f}], Z=[{bb.ZMin:.1f}, {bb.ZMax:.1f}]")

doc_name = "chassis_service_cover"
try:
    App.closeDocument(doc_name)
except Exception:
    pass

doc = App.newDocument(doc_name)
obj = doc.addObject("Part::Feature", "Chassis_Service_Cover")
obj.Label = "Raspberry Pi 4 Service Cover with Rounded '>>>' Chevron Louvers"
obj.Shape = cover_solid
obj.Visibility = True

doc.recompute()
doc.saveAs(fcstd_cover_path)
print(f"Saved FreeCAD model: {fcstd_cover_path}")
App.closeDocument(doc_name)


def patch_gui_visibility(filepath):
    temp_zip = filepath + ".tmp"
    with zipfile.ZipFile(filepath, "r") as zin:
        with zipfile.ZipFile(temp_zip, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "GuiDocument.xml":
                    xml_str = data.decode("utf-8")
                    xml_str = xml_str.replace('<Bool value="false"/>', '<Bool value="true"/>')
                    data = xml_str.encode("utf-8")
                zout.writestr(item, data)
    os.replace(temp_zip, filepath)


patch_gui_visibility(fcstd_cover_path)
print("✔ Patched GuiDocument.xml for full visibility")
sys.exit(0)
