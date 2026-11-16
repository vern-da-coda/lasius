#!/usr/bin/env python3
"""
Generate Lasius Monolithic Femur Service Cover & Canopy v2
(hardware/mechanics/models/custom/v2/parts/femur/femur_cover.FCStd)
==================================================================
Design Architecture:
- Single monolithic translucent Eisblau 55% canopy component fusing cover & dome.
- Fließend-konvexe Drapierung direkt vom Außenflansch (Z = 9.05 mm) zum Scheitelpunkt
  (Z = 22.00 mm), exakt angeglichen an die bionische Formensprache von chassis_canopy.FCStd.
- Keine Kanten, keine Absätze und keine künstliche Rahmen-Segmentierung.
- 3 dezente 45°-Chevron-Kühllamellen entlang des Rückgrats für Konvektionskühlung.
- Integrierte Option C Niederhalte-Hülsen (Z = -3.05 mm) zur spielfreien Fixierung
  des ADS1115 I2C ADC Boards.
- Integrierte umlaufende Zentrier-/Dichtlippe (Z = 7.50 .. 9.05 mm).
- 4x M2 Senkkopfbohrungen direkt in den abfallenden Flanken versenkt.
- > 20.2 mm lichte Höhe über PCB (reichlich Freigang für 14 mm DuPont-Stecker + Kabelbogen).
"""

import math
import os
import sys
import zipfile
import FreeCAD as App
import Part

print("--- Generating Lasius Monolithic Femur Service Cover (custom/v2/parts/femur/femur_cover.FCStd) ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts/femur"
export_step_dir = f"{repo_root}/hardware/mechanics/export/step/custom/v2/parts/femur"
export_stl_dir = f"{repo_root}/hardware/mechanics/export/stl/custom/v2/parts/femur"

fcstd_cover_path = f"{models_dir}/femur_cover.FCStd"
step_cover_path = f"{export_step_dir}/femur_cover.step"
stl_cover_path = f"{export_stl_dir}/femur_cover.stl"

os.makedirs(models_dir, exist_ok=True)
os.makedirs(export_step_dir, exist_ok=True)
os.makedirs(export_stl_dir, exist_ok=True)

# Femur reference parameters
Y_mid = 2.50
lid_z_floor = 9.00
cover_z_base = lid_z_floor + 0.05  # 9.05 mm

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
        Part.Edge(Part.ArcOfCircle(pts[1], App.Vector(x_min + r * (1 - 1 / math.sqrt(2)), y_max - r * (1 - 1 / math.sqrt(2)), z), pts[2])),
        Part.makeLine(pts[2], pts[3]),
        Part.Edge(Part.ArcOfCircle(pts[3], App.Vector(x_min + r * (1 - 1 / math.sqrt(2)), y_min + r * (1 - 1 / math.sqrt(2)), z), pts[4])),
        Part.makeLine(pts[4], pts[5]),
        Part.Edge(Part.ArcOfCircle(pts[5], App.Vector(x_max - r * (1 - 1 / math.sqrt(2)), y_min + r * (1 - 1 / math.sqrt(2)), z), pts[6])),
        Part.makeLine(pts[6], pts[7]),
        Part.Edge(Part.ArcOfCircle(pts[7], App.Vector(x_max - r * (1 - 1 / math.sqrt(2)), y_max - r * (1 - 1 / math.sqrt(2)), z), pts[0])),
    ]
    return Part.Wire(edges)


def make_rounded_rect_z(x_min, x_max, y_min, y_max, r_corner, z_min, z_max):
    wire = make_filleted_wire(x_min, x_max, y_min, y_max, r_corner, z_min)
    return Part.Face(wire).extrude(App.Vector(0.0, 0.0, z_max - z_min))


def make_chevron_slot(cx, cy, arm_len, width, angle_deg=45.0, z_min=17.0, z_max=25.0):
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


# =========================================================================
# 1. Monolithic Draped Convex Outer Shell (matching chassis_canopy.FCStd)
# =========================================================================
# The loft wires start directly at the mounting flange base (Z = 9.05 mm)
# and flow smoothly, convexly inward and upward to the apex at Z = 22.00 mm.
w_out_0 = make_filleted_wire(28.65, 71.35, Y_mid - 17.35, Y_mid + 17.35, 4.00, 9.05)
w_out_1 = make_filleted_wire(29.80, 70.20, Y_mid - 16.20, Y_mid + 16.20, 3.90, 11.00)
w_out_2 = make_filleted_wire(32.80, 67.20, Y_mid - 13.80, Y_mid + 13.80, 3.60, 14.00)
w_out_3 = make_filleted_wire(36.80, 63.20, Y_mid - 11.00, Y_mid + 11.00, 3.20, 17.00)
w_out_4 = make_filleted_wire(41.00, 59.00, Y_mid - 8.20,  Y_mid + 8.20,  2.80, 19.80)
w_out_5 = make_filleted_wire(45.50, 54.50, Y_mid - 5.50,  Y_mid + 5.50,  2.40, 22.00)

outer_solid = Part.makeLoft([w_out_0, w_out_1, w_out_2, w_out_3, w_out_4, w_out_5], True)

# =========================================================================
# 2. Downward Sealing / Alignment Lip Ring
# =========================================================================
lip_outer = make_rounded_rect_z(33.70, 66.30, Y_mid - 13.30, Y_mid + 13.30, 3.30, lid_z_floor - 1.50, cover_z_base + 0.10)
lip_inner = make_rounded_rect_z(35.30, 64.70, Y_mid - 11.70, Y_mid + 11.70, 2.00, lid_z_floor - 1.60, cover_z_base + 0.20)
lip_ring = lip_outer.cut(lip_inner)
cover_solid = outer_solid.fuse(lip_ring)

# =========================================================================
# 3. Inner Hollow Cavity (Convex Ceiling with > 20.2 mm clearance)
# =========================================================================
w_in_0 = make_filleted_wire(34.20, 65.80, Y_mid - 10.80, Y_mid + 10.80, 2.80, cover_z_base - 0.20)
w_in_1 = make_filleted_wire(35.20, 64.80, Y_mid - 10.00, Y_mid + 10.00, 2.60, 12.00)
w_in_2 = make_filleted_wire(37.20, 62.80, Y_mid - 8.80,  Y_mid + 8.80,  2.40, 15.50)
w_in_3 = make_filleted_wire(40.20, 59.80, Y_mid - 7.00,  Y_mid + 7.00,  2.00, 18.50)
w_in_4 = make_filleted_wire(43.50, 56.50, Y_mid - 4.60,  Y_mid + 4.60,  1.60, 20.40)
inner_void = Part.makeLoft([w_in_0, w_in_1, w_in_2, w_in_3, w_in_4], True)
cover_solid = cover_solid.cut(inner_void)

# =========================================================================
# 4. Option C Hold-Down Sleeves Descending onto ADS1115 PCB
# =========================================================================
for px_pin, py_pin in pin_coords:
    hd_outer = Part.makeCylinder(2.10, 15.55, App.Vector(px_pin, py_pin, -3.05))
    hd_rib = Part.makeBox(2.40, 5.60, 5.00, App.Vector(px_pin - 1.20, py_pin, 7.60))
    hd_pin_clear = Part.makeCylinder(1.30, 4.00, App.Vector(px_pin, py_pin, -3.50))
    cover_solid = cover_solid.fuse(hd_outer).fuse(hd_rib).cut(hd_pin_clear)

# =========================================================================
# 5. 4x M2 Fastening Holes (Countersunk directly into the sloping flanks)
# =========================================================================
for sx, sy in screw_coords:
    sh_through = Part.makeCylinder(1.10, 15.0, App.Vector(sx, sy, cover_z_base - 2.0))
    sh_csink = Part.makeCone(1.10, 2.10, 1.0, App.Vector(sx, sy, cover_z_base + 1.80))
    sh_head = Part.makeCylinder(2.10, 15.0, App.Vector(sx, sy, cover_z_base + 2.80))
    cover_solid = cover_solid.cut(sh_through).cut(sh_csink).cut(sh_head)

# =========================================================================
# 6. 3x 45-Degree Chevron Convection Louvers along Spine
# =========================================================================
for dx_slot in [-6.5, 0.0, 6.5]:
    slot = make_chevron_slot(50.0 + dx_slot, Y_mid, 5.0, 1.8, 45.0, 17.0, 25.0)
    cover_solid = cover_solid.cut(slot)

cover_solid = cover_solid.removeSplitter()
femur_cover = cover_solid

print(f"Monolithic Femur_Cover Valid: {femur_cover.isValid()}")
print(f"Volume: {femur_cover.Volume:.1f} mm^3, BoundBox: {femur_cover.BoundBox}")

# =========================================================================
# 7. Save FreeCAD Model & Export STEP / STL
# =========================================================================
fallback_gui_xml = None
if os.path.exists(fcstd_cover_path):
    try:
        with zipfile.ZipFile(fcstd_cover_path, "r") as zin:
            if "GuiDocument.xml" in zin.namelist():
                fallback_gui_xml = zin.read("GuiDocument.xml")
    except Exception:
        pass

try:
    App.closeDocument("femur_cover")
except Exception:
    pass

doc = App.newDocument("femur_cover")

obj_cover = doc.addObject("Part::Feature", "Femur_Cover")
obj_cover.Label = "Femur ADC Chamber Service Cover & Canopy (Monolithic Transluzent Eisblau 55%)"
obj_cover.Shape = femur_cover

if hasattr(obj_cover, "ViewObject") and obj_cover.ViewObject is not None:
    obj_cover.ViewObject.Visibility = True
    obj_cover.ViewObject.ShapeColor = (0.85, 0.92, 0.98)
    obj_cover.ViewObject.Transparency = 55

doc.recompute()
doc.saveAs(fcstd_cover_path)
print(f"✔ Saved FreeCAD Model: {fcstd_cover_path}")

femur_cover.exportStep(step_cover_path)
femur_cover.exportStl(stl_cover_path)
print(f"✔ Exported STEP: {step_cover_path}")
print(f"✔ Exported STL:  {stl_cover_path}")

App.closeDocument("femur_cover")

# Patch GuiDocument.xml for full visibility and 55% Plexiglas transparency
temp_zip = fcstd_cover_path + ".tmp"
with zipfile.ZipFile(fcstd_cover_path, "r") as zin:
    has_gui = "GuiDocument.xml" in zin.namelist()
    with zipfile.ZipFile(temp_zip, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "GuiDocument.xml":
                xml_str = data.decode("utf-8")
                xml_str = xml_str.replace('<Bool value="false"/>', '<Bool value="true"/>')
                if 'name="Transparency"' not in xml_str:
                    xml_str = xml_str.replace(
                        '</Properties>',
                        '    <Property name="Transparency" type="App::PropertyPercent"><Integer value="55"/></Property>\n'
                        '    <Property name="ShapeColor" type="App::PropertyColor"><PropertyColor value="4042322175"/></Property>\n'
                        '</Properties>'
                    )
                data = xml_str.encode("utf-8")
            zout.writestr(item, data)
        if not has_gui and fallback_gui_xml:
            xml_str = fallback_gui_xml.decode("utf-8")
            xml_str = xml_str.replace('<Bool value="false"/>', '<Bool value="true"/>')
            if 'name="Transparency"' not in xml_str:
                xml_str = xml_str.replace(
                    '</Properties>',
                    '    <Property name="Transparency" type="App::PropertyPercent"><Integer value="55"/></Property>\n'
                    '    <Property name="ShapeColor" type="App::PropertyColor"><PropertyColor value="4042322175"/></Property>\n'
                    '</Properties>'
                )
            zout.writestr("GuiDocument.xml", xml_str.encode("utf-8"))
os.replace(temp_zip, fcstd_cover_path)

print("--- Monolithic Femur Cover Generated Successfully ---")
