#!/usr/bin/env python3
"""
Generate Lasius Hexapod Two-Piece Chassis Belly Pan & Hinged Battery Hatch v2
(hardware/mechanics/models/custom/v2/parts/chassis/chassis_belly_pan.FCStd & chassis_battery_hatch.FCStd)
=========================================================================================================
Two-Piece CoG-Balanced Protective Skid-Plate Architecture (All UBECs on Body_Top):
  1. Chassis_Belly_Pan (Fixed Protective Boat-Hull Skid Plate):
     - Smooth, completely closed & dust-sealed underside hull (no obsolete UBEC louvers or
       protruding UBEC cradle ribs!).
     - Attaches via 4x M3 countersunk screws at (±45.0, ±30.0 mm) directly into Chassis_Core.
     - Rear fixed ToF bridge (X in [-88.0, -40.5 mm]): mounts downward-facing VL53L5CX
       9-zone ToF terrain sensor at X = -58.5 mm, Y = 0.0 mm with protective bezel, 4x M2
       mounting bosses, I2C wire pass-through slot, and dual flanking glide runners.
  2. Chassis_Battery_Hatch (Front-Center Hinged Battery Service Hatch, X in [-40.0, +76.0 mm]):
     - Generous 116 mm long front-center battery bay balancing the 2x rear Top-Deck Hobbywing
       UBECs (72 g at X = -79.5 mm) by placing the 2S LiPo forward at X = +36.0 mm
       (CoG offset < 1 mm from X = 0!) while also accommodating larger 2S 3000-5000 mAh packs.
     - Direct tool-free access to both the 2S LiPo and its rearward-exiting XT60 connector
       (X in [-19.5, 0.0 mm]) for battery swap or bench power supply hookup.
     - Interlocking 3D-printable 7-knuckle filament hinge (+Y rail, Ø2.1 mm bore for 1.75 mm
       PETG/nylon axis) + ergonomic cantilever snap-latch along -Y rail (X = +18.0 mm).
"""

import math
import os
import sys
import zipfile
import FreeCAD as App
import Part

print("--- Generating Two-Piece CoG-Balanced Chassis Belly Pan & Battery Hatch v2 ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts/chassis"
urdf_mesh_dir = f"{repo_root}/hardware/mechanics/export/urdf/meshes"
export_step_dir = f"{repo_root}/hardware/mechanics/export/step/custom/v2/parts/chassis"
export_stl_dir = f"{repo_root}/hardware/mechanics/export/stl/custom/v2/parts/chassis"

os.makedirs(models_dir, exist_ok=True)
os.makedirs(urdf_mesh_dir, exist_ok=True)
if "--export" in sys.argv:
    os.makedirs(export_step_dir, exist_ok=True)
    os.makedirs(export_stl_dir, exist_ok=True)


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


# Coordinate conventions:
z_top = -0.02
z_floor = -10.00
z_cavity_floor = -7.60  # leaves 2.40 mm bottom floor thickness
y_hinge = 19.50
z_hinge = -7.60
r_knuckle = 2.20
r_bore = 1.05  # Ø2.10 mm bore for 1.75 mm filament axis

# Interlocking 7-knuckle hinge layout spanning Front-Center Hatch X in [-40.0, +76.0]:
FRAME_LUGS = [(-36.0, -20.0), (-4.0, 12.0), (28.0, 44.0), (60.0, 72.0)]
HATCH_LUGS = [(-19.2, -4.8), (12.8, 27.2), (44.8, 59.2)]  # 0.80 mm axial clearance each side


# =============================================================================
# 1. Build Part 1: Chassis_Belly_Pan (The Fixed Protective Skid Plate Frame)
# =============================================================================
def build_belly_frame():
    # 1.1 Main Skid Plate Hull (Top Flange: X in [-88, +88], Y in [-34, +34])
    flange_solid = make_rounded_rect_solid(-88.0, 88.0, -34.0, 34.0, 7.0, -2.40, z_top)

    # 4x Standoff Ears (X = ±45.0, Y = ±30.0)
    for sx in [-45.0, 45.0]:
        for sy in [-30.0, 30.0]:
            ear = Part.makeCylinder(9.5, 2.38, App.Vector(sx, sy, -2.40), App.Vector(0, 0, 1))
            flange_solid = flange_solid.fuse(ear)

    # Central Deep Tub (X in [-88.0, +88.0], Y in [-28.0, +28.0], Z in [-10.00, -2.40])
    tub_solid = make_rounded_rect_solid(-88.0, 88.0, -28.0, 28.0, 5.0, z_floor, -2.40)

    # 30-degree Front and Rear Approach Ramps (between X = ±72.0 and X = ±88.0):
    wedge_f = Part.Face(
        Part.makePolygon([
            App.Vector(72.0, -40.0, z_floor - 0.1),
            App.Vector(90.0, -40.0, z_floor - 0.1),
            App.Vector(90.0, -40.0, -2.40),
            App.Vector(72.0, -40.0, z_floor - 0.1),
        ])
    ).extrude(App.Vector(0.0, 80.0, 0.0))
    wedge_r = Part.Face(
        Part.makePolygon([
            App.Vector(-72.0, -40.0, z_floor - 0.1),
            App.Vector(-90.0, -40.0, -2.40),
            App.Vector(-90.0, -40.0, z_floor - 0.1),
            App.Vector(-72.0, -40.0, z_floor - 0.1),
        ])
    ).extrude(App.Vector(0.0, 80.0, 0.0))
    tub_solid = tub_solid.cut(wedge_f).cut(wedge_r)
    frame_solid = flange_solid.fuse(tub_solid)

    # 1.2 Hollow Internal Cavity
    cavity = make_rounded_rect_solid(-80.0, 80.0, -24.0, 24.0, 4.0, z_cavity_floor, z_top + 2.0)
    frame_solid = frame_solid.cut(cavity)

    # 1.3 Four M3 Countersunk Standoff Mounts (X = ±45.0, Y = ±30.0)
    for sx in [-45.0, 45.0]:
        for sy in [-30.0, 30.0]:
            thru_hole = Part.makeCylinder(1.70, 10.0, App.Vector(sx, sy, -5.0), App.Vector(0, 0, 1))
            csk_cone = Part.makeCone(3.30, 1.70, 1.60, App.Vector(sx, sy, -2.40), App.Vector(0, 0, 1))
            frame_solid = frame_solid.cut(thru_hole).cut(csk_cone)

    # 1.4 Downward-Facing VL53L5CX ToF Sensor in Fixed Rear Bridge (X = -58.5 mm, Y = 0.0 mm)
    #     Leaves the entire Front-Center bay (X in [-40.0, +76.0]) free for CoG-balanced battery placement!
    x_tof = -58.5
    aperture_box = make_rounded_rect_solid(x_tof - 5.0, x_tof + 5.0, -4.0, 4.0, 1.5, z_floor - 4.0, z_cavity_floor + 2.0)
    frame_solid = frame_solid.cut(aperture_box)

    bezel_rim = make_rounded_rect_solid(x_tof - 9.0, x_tof + 9.0, -7.5, 7.5, 2.5, z_floor - 1.50, z_floor)
    bezel_cut = make_rounded_rect_solid(x_tof - 7.0, x_tof + 7.0, -5.5, 5.5, 1.5, z_floor - 2.0, z_floor + 1.0)
    frame_solid = frame_solid.fuse(bezel_rim).cut(bezel_cut)

    boss_h, boss_r, hole_r = 3.20, 2.60, 0.90
    for dx_h in [-10.5, 10.5]:
        for dy_h in [-6.5, 6.5]:
            hx, hy = x_tof + dx_h, dy_h
            boss = Part.makeCylinder(boss_r, boss_h, App.Vector(hx, hy, z_cavity_floor), App.Vector(0, 0, 1))
            pilot = Part.makeCylinder(hole_r, boss_h + 3.0, App.Vector(hx, hy, z_cavity_floor - 1.0), App.Vector(0, 0, 1))
            frame_solid = frame_solid.fuse(boss).cut(pilot)

    wire_slot = make_rounded_rect_solid(x_tof - 9.0, x_tof + 9.0, -10.0, -5.0, 1.5, z_cavity_floor, z_top + 2.0)
    frame_solid = frame_solid.cut(wire_slot)

    # 1.5 Front-Center Battery Service Hatch Aperture in Frame Floor (X in [-40.0, +76.0], Y in [-19.5, +19.5])
    hatch_aperture = make_rounded_rect_solid(-40.0, 76.0, -19.5, 19.5, 4.5, z_floor - 2.0, z_cavity_floor + 0.1)
    frame_solid = frame_solid.cut(hatch_aperture)

    # Cut clearance pockets in frame for the hatch knuckle lugs:
    for x1, x2 in HATCH_LUGS:
        pocket = Part.makeCylinder(2.50, (x2 - x1) + 0.8, App.Vector(x1 - 0.4, y_hinge, z_hinge), App.Vector(1, 0, 0))
        frame_solid = frame_solid.cut(pocket)

    # 1.6 Knuckle Hinge Lugs on Frame (+Y Rail at Y = 19.5 mm, Z = -7.6 mm)
    for x1, x2 in FRAME_LUGS:
        lug = Part.makeCylinder(r_knuckle, x2 - x1, App.Vector(x1, y_hinge, z_hinge), App.Vector(1, 0, 0))
        frame_solid = frame_solid.fuse(lug)

    # Continuous Bore for 1.75 mm Filament Axis (X in [-38.0, +74.0])
    bore_frame = Part.makeCylinder(r_bore, 114.0, App.Vector(-38.0, y_hinge, z_hinge), App.Vector(1, 0, 0))
    frame_solid = frame_solid.cut(bore_frame)

    # 1.7 Snap-Latch Catch Groove along -Y Rail (centered at X = +18.0, X in [+7.0, +29.0])
    catch_groove = Part.makeBox(22.0, 3.2, 3.5, App.Vector(7.0, -22.5, -9.20))
    frame_solid = frame_solid.cut(catch_groove)

    # 1.8 Rear Glide Runners on Fixed Frame (flanking ToF bezel at Y = ±16.0 mm)
    for ry in [-16.0, 16.0]:
        rib_r = make_rounded_rect_solid(-68.0, -45.0, ry - 1.5, ry + 1.5, 1.2, z_floor - 1.20, z_floor)
        frame_solid = frame_solid.fuse(rib_r)

    # 1.9 Four Symmetrical Dust-Tight Desk-Stand Snap-Fit Docking Sockets at (±58.0, ±26.55 mm)
    #     - Ø8.90 mm boss (R=4.45) stays strictly clear of +Y hinge (Y<=22.0), inside ±34.0 flange (Y<=31.0),
    #       clear of M3 ears (±45, ±30) by >= 5.9 mm, and clear of VL53L5CX (|Y|<=9.1) by 13.0 mm!
    #     - Closed dust-tight ceiling (Z = -2.10..-0.02 mm, 2.08 mm solid PETG) & 45° support-free interior!
    #     - Ø5.30 mm neck -> Ø6.10 mm internal undercut groove locks onto Ø5.96 mm TPU 95A snap sleeves!
    dock_pts = [(-58.0, -26.55), (-58.0, +26.55), (+58.0, -26.55), (+58.0, +26.55)]
    for dx, dy in dock_pts:
        boss = Part.makeCylinder(4.45, z_top - z_floor, App.Vector(dx, dy, z_floor), App.Vector(0, 0, 1))
        frame_solid = frame_solid.fuse(boss)
        # Revolved blind snap-fit socket cavity (45° lead-in, Ø5.30 neck, Ø6.10 undercut, 45° roof!)
        sock_rz = [
            (0.00, z_floor - 0.50),
            (3.75, z_floor - 0.50),
            (3.25, z_floor),
            (2.65, z_floor + 0.85),   # -9.15 mm
            (2.65, z_floor + 3.20),   # -6.80 mm (neck top)
            (3.05, z_floor + 3.70),   # -6.30 mm (45° undercut entry)
            (3.05, z_floor + 5.80),   # -4.20 mm (undercut pocket top)
            (0.95, z_floor + 7.90),   # -2.10 mm (45° support-free ceiling, 2.08 mm dust-tight roof!)
            (0.00, z_floor + 7.90),
        ]
        s_pts = [App.Vector(dx + r, dy, z) for r, z in sock_rz]
        s_pts.append(s_pts[0])
        sock_cav = Part.Face(Part.makePolygon(s_pts)).revolve(App.Vector(dx, dy, 0.0), App.Vector(0, 0, 1), 360.0)
        frame_solid = frame_solid.cut(sock_cav)

    frame_solid = frame_solid.removeSplitter()
    return frame_solid


# =============================================================================
# 2. Build Part 2: Chassis_Battery_Hatch (Front-Center Hinged Battery Hatch)
# =============================================================================
def build_battery_hatch():
    # 2.1 Base Plate matching aperture [-40.0, +76.0] with 0.8 mm clearance in X, 0.5 mm in Y
    hatch_base = make_rounded_rect_solid(-39.2, 75.2, -19.0, 19.0, 4.0, z_floor, z_cavity_floor)

    # 2.2 Internal Battery Cradle Rim (Z = -7.60 .. -3.50 mm)
    hatch_rim = make_rounded_rect_solid(-39.2, 75.2, -19.0, 19.0, 4.0, z_cavity_floor, -3.50)
    hatch_pocket = make_rounded_rect_solid(-37.7, 73.7, -17.5, 17.5, 3.0, z_cavity_floor, -2.50)
    hatch_rim = hatch_rim.cut(hatch_pocket)
    hatch_solid = hatch_base.fuse(hatch_rim)

    # Low transverse LiPo/XT60 divider rib at X = -2.0..-0.4 (cradles 72mm 2S LiPo forward in X in [0..+72],
    # while leaving X in [-37.7, -2.0] wide open for the rearward-exiting XT60 & balancer leads!)
    div_rib = Part.makeBox(1.6, 35.0, 3.2, App.Vector(-2.0, -17.5, z_cavity_floor))
    hatch_solid = hatch_solid.fuse(div_rib)

    # Cut clearance pockets in hatch for the frame knuckle lugs:
    for x1, x2 in FRAME_LUGS:
        hatch_pocket_hinge = Part.makeCylinder(2.50, (x2 - x1) + 0.8, App.Vector(x1 - 0.4, y_hinge, z_hinge), App.Vector(1, 0, 0))
        hatch_solid = hatch_solid.cut(hatch_pocket_hinge)

    # 2.3 Interlocking Knuckle Hinge Lugs on Hatch (+Y Edge at Y = 19.5 mm, Z = -7.6 mm)
    for x1, x2 in HATCH_LUGS:
        lug = Part.makeCylinder(r_knuckle, x2 - x1, App.Vector(x1, y_hinge, z_hinge), App.Vector(1, 0, 0))
        hatch_solid = hatch_solid.fuse(lug)

    # Bore for 1.75 mm Filament Axis
    bore_hatch = Part.makeCylinder(r_bore, 114.0, App.Vector(-38.0, y_hinge, z_hinge), App.Vector(1, 0, 0))
    hatch_solid = hatch_solid.cut(bore_hatch)

    # 2.4 Ergonomic Cantilever Snap-Latch along -Y Edge (centered at X = +18.0, X in [+9.0, +27.0])
    latch_beam = Part.makeBox(18.0, 2.2, 2.0, App.Vector(9.0, -20.8, -8.80))
    latch_lip = Part.makeBox(16.0, 1.4, 1.5, App.Vector(10.0, -21.8, -8.50))
    pull_tab = make_rounded_rect_solid(12.0, 24.0, -21.0, -18.0, 1.2, z_floor - 1.20, z_floor)
    hatch_solid = hatch_solid.fuse(latch_beam).fuse(latch_lip).fuse(pull_tab)

    # 2.5 Protective Bottom Glide Ribs on Hatch (Y = ±12.0 mm, X in [-32.0, +68.0])
    for ry in [-12.0, 12.0]:
        rib = make_rounded_rect_solid(-32.0, 68.0, ry - 1.4, ry + 1.4, 1.2, z_floor - 1.00, z_floor)
        hatch_solid = hatch_solid.fuse(rib)

    hatch_solid = hatch_solid.removeSplitter()
    return hatch_solid


frame_solid = build_belly_frame()
hatch_solid = build_battery_hatch()

print(f"Belly Pan Frame Valid: {frame_solid.isValid()}, Vol: {frame_solid.Volume:.1f} mm^3")
print(f"Battery Hatch Valid:   {hatch_solid.isValid()}, Vol: {hatch_solid.Volume:.1f} mm^3")

coll = frame_solid.common(hatch_solid)
print(f"Frame <-> Hatch Collision Check: {coll.Volume:.4f} mm^3")


def save_part(doc_name, obj_name, label, shape, color, stl_name):
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)
    obj = doc.addObject("Part::Feature", obj_name)
    obj.Label = label
    obj.Shape = shape
    obj.Visibility = True
    if hasattr(obj, "ViewObject") and obj.ViewObject:
        obj.ViewObject.ShapeColor = color
    doc.recompute()
    fcstd_path = f"{models_dir}/{doc_name}.FCStd"
    doc.saveAs(fcstd_path)
    shape.exportStl(f"{urdf_mesh_dir}/{stl_name}.stl")
    if "--export" in sys.argv:
        shape.exportStep(f"{export_step_dir}/{doc_name}.step")
        shape.exportStl(f"{export_stl_dir}/{doc_name}.stl")
    App.closeDocument(doc_name)

    temp_zip = fcstd_path + ".tmp"
    with zipfile.ZipFile(fcstd_path, "r") as zin:
        with zipfile.ZipFile(temp_zip, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "GuiDocument.xml":
                    xml_str = data.decode("utf-8").replace('<Bool value="false"/>', '<Bool value="true"/>')
                    data = xml_str.encode("utf-8")
                zout.writestr(item, data)
    os.replace(temp_zip, fcstd_path)
    print(f"✔ Saved: {fcstd_path}")


save_part(
    "chassis_belly_pan",
    "Chassis_Belly_Pan",
    "Chassis Belly Pan Frame (Closed Skid Plate + Rear ToF Bridge, v2)",
    frame_solid,
    (0.18, 0.20, 0.23),
    "chassis_belly_pan",
)
save_part(
    "chassis_battery_hatch",
    "Chassis_Battery_Hatch",
    "Chassis Battery Service Hatch (Front-Center Hinged, CoG-Balanced, v2)",
    hatch_solid,
    (0.28, 0.30, 0.34),
    "chassis_battery_hatch",
)

sys.exit(0)
