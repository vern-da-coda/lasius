#!/usr/bin/env python3
"""
Generate Lasius Hexapod Raspberry Pi 4 Mounting Plate v2 FreeCAD Model
(hardware/mechanics/models/custom/v2/parts/chassis_rpi_mount.FCStd)
========================================================================
Design Concept (Zentrierte Befestigungsplatte unter der Service-Abdeckung):
  1. Base Deck on Body_Top:
     - Sits directly on the upper carbon plate (body_top at Z = 55.30 mm).
     - Centered symmetrically around X = 0.0, Y = 0.0 mm.
     - 4x M3 countersunk screw lugs at (±45.0, ±30.0 mm) securing the plate
       rigidly into the central chassis core (chassis_core).
  2. Raspberry Pi 4 Mounting Standoffs:
     - 4x integrated standoff bosses (height 2.50 mm, Ø6.40 mm) at the Pi 4
       hole pattern (58.0 x 49.0 mm at X = ±29.0, Y = ±24.5 mm).
     - M2.5 threaded insert pilot holes (Ø2.10 mm, depth 4.0 mm).
     - Elevates the Pi 4 PCB to Z = 59.80 mm, providing 2.5 mm clearance under the board
       for bottom SMD components, solder joints, and micro-SD card.
  3. Underside Cable & Weight Relief:
     - Large underside central pocket (X in [-22.0, +22.0 mm], Y in [-18.0, +18.0 mm])
       for pass-through wiring, CSI ribbon cables, and cooling airflow from chassis interior.
"""

import math
import os
import sys
import zipfile
import FreeCAD as App
import Part

print("--- Generating Raspberry Pi 4 Mounting Plate v2 (FreeCAD 1.1+) ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts/chassis"
fcstd_plate_path = f"{models_dir}/chassis_rpi_mount.FCStd"

os.makedirs(models_dir, exist_ok=True)


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


def make_filleted_wire(x_min, x_max, y_min, y_max, r, z):
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
        Part.Edge(Part.ArcOfCircle(pts[1], App.Vector(x_min + r * (1 - 1 / math.sqrt(2)), y_max - r * (1 - 1 / math.sqrt(2)), z), pts[2])),
        Part.makeLine(pts[2], pts[3]),
        Part.Edge(Part.ArcOfCircle(pts[3], App.Vector(x_min + r * (1 - 1 / math.sqrt(2)), y_min + r * (1 - 1 / math.sqrt(2)), z), pts[4])),
        Part.makeLine(pts[4], pts[5]),
        Part.Edge(Part.ArcOfCircle(pts[5], App.Vector(x_max - r * (1 - 1 / math.sqrt(2)), y_min + r * (1 - 1 / math.sqrt(2)), z), pts[6])),
        Part.makeLine(pts[6], pts[7]),
        Part.Edge(Part.ArcOfCircle(pts[7], App.Vector(x_max - r * (1 - 1 / math.sqrt(2)), y_max - r * (1 - 1 / math.sqrt(2)), z), pts[0])),
    ]
    return Part.Wire(edges)


def build_rpi_mount():
    z_base = 55.32  # 0.02 mm clearance above Body_Top (55.30 mm)
    t_plate = 1.98  # top of plate at Z = 57.30 mm
    h_boss = 2.48   # top of RPi4 bosses at Z = 59.78 mm (0.02 mm below RPi4 PCB at 59.80 mm)

    # 1. Base Plate Deck (Centered around X = 0, Y = 0)
    plate = make_rounded_rect_solid(-35.0, 35.0, -28.0, 28.0, 4.0, z_base, z_base + t_plate)

    # Construct Canopy inner ceiling envelope (with 0.05 mm vertical clearance) to trim top of support pillars
    z_canopy = 55.25
    w_in_1 = make_filleted_wire(-134.5, 134.5, -88.5, 88.5, 30.5, z_canopy)
    w_in_2 = make_filleted_wire(-113.5, 113.5, -73.5, 73.5, 24.5, z_canopy + 5.0)
    w_in_3 = make_filleted_wire(-88.5, 88.5, -56.5, 56.5, 18.5, z_canopy + 12.0)
    w_in_4 = make_filleted_wire(-63.5, 63.5, -40.5, 40.5, 13.5, z_canopy + 19.0)
    w_in_5 = make_filleted_wire(-45.5, 47.5, -30.5, 30.5, 6.5, z_canopy + 24.68)
    loft_canopy_inner = Part.makeLoft([w_in_1, w_in_2, w_in_3, w_in_4, w_in_5], True)
    # Also ensure pillars clear the service cover aperture/rebate and the RPi4 PCB footprint above the base deck
    rebate_clear = Part.Face(make_filleted_wire(-44.0, 46.0, -29.0, 29.0, 5.2, 79.50)).extrude(App.Vector(0, 0, 10.0))
    rpi_clear = make_rounded_rect_solid(-43.0, 45.5, -28.5, 28.5, 2.5, z_base + t_plate + 0.02, 85.0)
    canopy_ceiling = loft_canopy_inner.cut(rebate_clear).cut(rpi_clear)

    # 2. 4x Core Standoff Mounting Arms & Integrated Canopy Support Pillars at (±45.0, ±30.0 mm)
    for sx in [-45.0, 45.0]:
        for sy in [-30.0, 30.0]:
            cyl = Part.makeCylinder(7.5, t_plate, App.Vector(sx, sy, z_base), App.Vector(0, 0, 1))
            pillar = Part.makeCylinder(4.5, 26.0, App.Vector(sx, sy, z_base), App.Vector(0, 0, 1)).common(canopy_ceiling)
            x1 = min(sx, -35.0 if sx < 0 else 35.0)
            x2 = max(sx, -35.0 if sx < 0 else 35.0)
            y1 = min(sy, -28.0 if sy < 0 else 28.0)
            y2 = max(sy, -28.0 if sy < 0 else 28.0)
            bridge = make_rounded_rect_solid(x1, x2, min(sy - 3.5, y1), max(sy + 3.5, y2), 2.0, z_base, z_base + t_plate)
            plate = plate.fuse(cyl).fuse(bridge).fuse(pillar)

    # Cut 4x M3 coaxial through-holes at (±45.0, ±30.0 mm)
    for sx in [-45.0, 45.0]:
        for sy in [-30.0, 30.0]:
            hole = Part.makeCylinder(1.70, 30.0, App.Vector(sx, sy, z_base - 2.0), App.Vector(0, 0, 1))
            plate = plate.cut(hole)

    # 3. 4x Raspberry Pi 4 Standoff Bosses at X in [±29.0], Y in [±24.5]
    for bx in [-29.0, 29.0]:
        for by in [-24.5, 24.5]:
            boss = Part.makeCylinder(3.20, h_boss, App.Vector(bx, by, z_base + t_plate), App.Vector(0, 0, 1))
            tap = Part.makeCylinder(1.05, 5.0, App.Vector(bx, by, z_base + t_plate + h_boss - 4.0), App.Vector(0, 0, 1))
            boss = boss.cut(tap)
            plate = plate.fuse(boss)

    # 4. Underside Wiring & Weight Relief Pocket
    pocket = make_rounded_rect_solid(-22.0, 22.0, -18.0, 18.0, 3.0, z_base - 1.0, z_base + 1.20)
    plate = plate.cut(pocket)

    return plate


mount_solid = build_rpi_mount()
print(f"RPi Mount Solid Valid: {mount_solid.isValid()}")
print(f"Faces: {len(mount_solid.Faces)}, Edges: {len(mount_solid.Edges)}")
print(f"Volume: {mount_solid.Volume:.2f} mm^3")
bb = mount_solid.BoundBox
print(f"BoundBox: X=[{bb.XMin:.1f}, {bb.XMax:.1f}], Y=[{bb.YMin:.1f}, {bb.YMax:.1f}], Z=[{bb.ZMin:.1f}, {bb.ZMax:.1f}]")

doc_name = "chassis_rpi_mount"
try:
    App.closeDocument(doc_name)
except Exception:
    pass

doc = App.newDocument(doc_name)
obj = doc.addObject("Part::Feature", "Chassis_RPi_Mount")
obj.Label = "Raspberry Pi 4 Mounting Plate (v2)"
obj.Shape = mount_solid
obj.Visibility = True

doc.recompute()
doc.saveAs(fcstd_plate_path)
export_step_dir = f"{repo_root}/hardware/mechanics/export/step/custom/v2/parts/chassis"
export_stl_dir = f"{repo_root}/hardware/mechanics/export/stl/custom/v2/parts/chassis"
os.makedirs(export_step_dir, exist_ok=True)
os.makedirs(export_stl_dir, exist_ok=True)
mount_solid.exportStep(f"{export_step_dir}/chassis_rpi_mount.step")
mount_solid.exportStl(f"{export_stl_dir}/chassis_rpi_mount.stl")
print(f"Saved FreeCAD model: {fcstd_plate_path}")
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


patch_gui_visibility(fcstd_plate_path)
print("✔ Patched GuiDocument.xml for full visibility")
sys.exit(0)
