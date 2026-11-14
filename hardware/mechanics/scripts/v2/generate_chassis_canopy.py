#!/usr/bin/env python3
"""
Generate Lasius Hexapod Thermoformed Plexiglas Canopy v2 FreeCAD Model
(hardware/mechanics/models/custom/v2/parts/chassis_canopy.FCStd)
========================================================================
Design Concept (Vakuum-Tiefzieh-Haube / Draped Plexiglas Sheet):
  1. Draped Thermoformed Thin Acrylic Sheet (t = 1.50 mm):
     - Drapes smoothly and continuously over the central chassis top cover
       (rising to Z = 81.50 mm at the apex) and flows organically down onto
       the upper carbon plate (body_top at Z = 55.30 mm).
     - Smooth double-curved aerodynamic canopy without steps or kinks.
  2. 100% Flush Cut to Body_Top Perimeter:
     - All overhangs around the entire robot perimeter are trimmed bündig
       (flush) with the exact outer silhouette of body_top.FCStd
       (X in [-132.0, +135.0 mm], Y in [-88.5, +88.5 mm]).
  3. Clearance & Fit:
     - Apex centered symmetrically around X = 0.0, Y = 0.0 mm.
     - Inner cavity conforms precisely to the central components and clears
       the 6 Coxa pivot axes.
  4. Fastening Pattern:
     - Coaxial through-holes (Ø3.4 mm) for M3 screws at (±45.0, ±30.0 mm),
       rear (-90.0, 0.0 mm), and front (128.0, ±12.0 mm).
  5. Service Hatch Aperture & Rebate:
     - Aperture centered directly over the Raspberry Pi 4 Model B at X = 0, Y = 0
       (X in [-41.8, +43.8 mm], Y in [-26.8, +26.8 mm]).
     - Recessed rebate at Z = 80.20 mm (X in [-43.8, +45.8 mm], Y in [-28.8, +28.8 mm])
       providing a flush seating lip for the service cover.
"""

import math
import os
import sys
import zipfile
import FreeCAD as App
import Part

print("--- Generating Lasius Draped Plexiglas Canopy v2 (FreeCAD 1.1+) ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts/chassis"
body_top_path = f"{repo_root}/hardware/mechanics/models/custom/v1/parts/body_top.FCStd"
fcstd_canopy_path = f"{models_dir}/chassis_canopy.FCStd"

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


def build_draped_plexiglas_canopy():
    # 1. Load exact Body_Top perimeter wire
    doc_plate = App.openDocument(body_top_path)
    plate_shape = doc_plate.getObject("BodyTop").Shape
    outer_wire = [w for w in plate_shape.Wires if w.BoundBox.XLength > 200][0]
    doc_plate_name = doc_plate.Name

    z_base = 55.30
    thick = 1.50  # 1.5 mm thin Plexiglas sheet
    h_apex = 26.20  # Apex at Z = 81.50 mm (Elevated to provide generous headroom over Raspberry Pi 4)

    # -------------------------------------------------------------------------
    # 2. Outer Draped Surface Profiles (Apex Z = 81.50 mm down to Z = 55.30 mm)
    # -------------------------------------------------------------------------
    w_out_0 = make_filleted_wire(-140.0, 140.0, -95.0, 95.0, 35.0, z_base)
    w_out_1 = make_filleted_wire(-136.0, 136.0, -90.0, 90.0, 32.0, z_base + thick)
    w_out_2 = make_filleted_wire(-115.0, 115.0, -75.0, 75.0, 26.0, z_base + 6.5)
    w_out_3 = make_filleted_wire(-90.0, 90.0, -58.0, 58.0, 20.0, z_base + 13.5)
    w_out_4 = make_filleted_wire(-65.0, 65.0, -42.0, 42.0, 15.0, z_base + 20.5)
    w_out_5 = make_filleted_wire(-47.0, 49.0, -32.0, 32.0, 8.0, z_base + h_apex)

    loft_outer = Part.makeLoft([w_out_0, w_out_1, w_out_2, w_out_3, w_out_4, w_out_5], True)

    # -------------------------------------------------------------------------
    # 3. Inner Draped Surface Profiles (Offset inward by thick = 1.5 mm)
    # -------------------------------------------------------------------------
    w_in_1 = make_filleted_wire(-134.5, 134.5, -88.5, 88.5, 30.5, z_base)
    w_in_2 = make_filleted_wire(-113.5, 113.5, -73.5, 73.5, 24.5, z_base + 5.0)
    w_in_3 = make_filleted_wire(-88.5, 88.5, -56.5, 56.5, 18.5, z_base + 12.0)
    w_in_4 = make_filleted_wire(-63.5, 63.5, -40.5, 40.5, 13.5, z_base + 19.0)
    w_in_5 = make_filleted_wire(-45.5, 47.5, -30.5, 30.5, 6.5, z_base + h_apex - thick)

    loft_inner = Part.makeLoft([w_in_1, w_in_2, w_in_3, w_in_4, w_in_5], True)

    # Hollow thin Plexiglas canopy shell (uniform 1.50 mm wall thickness)
    canopy_shell = loft_outer.cut(loft_inner)

    # -------------------------------------------------------------------------
    # 4. Trim All Overhangs Flush Around Body_Top Perimeter
    # -------------------------------------------------------------------------
    face_top = Part.Face(outer_wire)
    face_top.translate(App.Vector(0.0, 0.0, z_base - face_top.BoundBox.ZMin))
    body_top_extruded = face_top.extrude(App.Vector(0.0, 0.0, 40.0))

    plexiglas_solid = canopy_shell.common(body_top_extruded)

    # -------------------------------------------------------------------------
    # 5. Service Hatch Aperture & Seating Rebate for Service Cover
    # -------------------------------------------------------------------------
    # Centered aperture directly above Raspberry Pi 4
    w_through = make_filleted_wire(-41.8, 43.8, -26.8, 26.8, 3.7, 50.0)
    through_hole = Part.Face(w_through).extrude(App.Vector(0.0, 0.0, 38.0))

    # Recessed seating rebate (Z = 80.20 mm) for outer flange of service cover
    w_rebate = make_filleted_wire(-43.8, 45.8, -28.8, 28.8, 5.2, 80.20)
    rebate = Part.Face(w_rebate).extrude(App.Vector(0.0, 0.0, 15.0))

    plexiglas_solid = plexiglas_solid.cut(through_hole).cut(rebate)

    # -------------------------------------------------------------------------
    # 6. Fastening Through-Holes (M3 clearance Ø3.4 mm)
    # -------------------------------------------------------------------------
    # 4x Core M3 Holes at (±45.0, ±30.0 mm)
    for sy in [-30.0, 30.0]:
        for sx in [-45.0, 45.0]:
            bore = Part.makeCylinder(1.70, 35.0, App.Vector(sx, sy, z_base - 1.0), App.Vector(0, 0, 1))
            plexiglas_solid = plexiglas_solid.cut(bore)

    # 1x Rear Tail M3 Hole at (-90.0, 0.0 mm)
    bore_rear = Part.makeCylinder(1.70, 35.0, App.Vector(-90.0, 0.0, z_base - 1.0), App.Vector(0, 0, 1))
    plexiglas_solid = plexiglas_solid.cut(bore_rear)

    # 2x Front Neck M3 Holes at (128.0, ±12.0 mm)
    for ny in [12.0, -12.0]:
        bore_neck = Part.makeCylinder(1.70, 35.0, App.Vector(128.0, ny, z_base - 1.0), App.Vector(0, 0, 1))
        plexiglas_solid = plexiglas_solid.cut(bore_neck)

    App.closeDocument(doc_plate_name)
    return plexiglas_solid


canopy_solid = build_draped_plexiglas_canopy()
print(f"Plexiglas Canopy Solid Valid: {canopy_solid.isValid()}")
print(f"Faces: {len(canopy_solid.Faces)}, Edges: {len(canopy_solid.Edges)}")
print(f"Volume: {canopy_solid.Volume:.2f} mm^3 (Area = {canopy_solid.Area:.2f} mm^2)")
xs = [v.X for v in canopy_solid.Vertexes]
ys = [v.Y for v in canopy_solid.Vertexes]
zs = [v.Z for v in canopy_solid.Vertexes]
print(f"Actual Vertex Bounds: X=[{min(xs):.1f}, {max(xs):.1f}], Y=[{min(ys):.1f}, {max(ys):.1f}], Z=[{min(zs):.1f}, {max(zs):.1f}]")

doc_name = "chassis_canopy"
try:
    App.closeDocument(doc_name)
except Exception:
    pass

doc = App.newDocument(doc_name)
obj = doc.addObject("Part::Feature", "Chassis_Canopy")
obj.Label = "Plexiglas Canopy (Draped & Trimmed Flush to Body_Top)"
obj.Shape = canopy_solid
obj.Visibility = True

doc.recompute()
doc.saveAs(fcstd_canopy_path)
print(f"Saved FreeCAD model: {fcstd_canopy_path}")
App.closeDocument(doc_name)


# Ensure GuiDocument.xml has Visibility="true" and Transparent Material
def patch_canopy_view(filepath):
    temp_zip = filepath + ".tmp"
    with zipfile.ZipFile(filepath, "r") as zin:
        with zipfile.ZipFile(temp_zip, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "GuiDocument.xml":
                    xml_str = data.decode("utf-8")
                    xml_str = xml_str.replace('<Bool value="false"/>', '<Bool value="true"/>')
                    # Set transparent Plexiglas material (55% transparency, light cyan tint)
                    if "<Property name=\"Transparency\"" in xml_str:
                        xml_str = xml_str.replace('<Integer value="0"/>', '<Integer value="55"/>')
                    else:
                        insert_pos = xml_str.find("</Properties>")
                        if insert_pos != -1:
                            transp_prop = '<Property name="Transparency" type="App::PropertyPercent"><Integer value="55"/></Property>\n'
                            diffuse_prop = '<Property name="ShapeColor" type="App::PropertyColor"><PropertyColor value="4042322175"/></Property>\n'
                            xml_str = xml_str[:insert_pos] + transp_prop + diffuse_prop + xml_str[insert_pos:]
                    data = xml_str.encode("utf-8")
                zout.writestr(item, data)
    os.replace(temp_zip, filepath)


patch_canopy_view(fcstd_canopy_path)
print("✔ Patched GuiDocument.xml with transparent Plexiglas appearance")

sys.exit(0)
