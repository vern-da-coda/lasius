#!/usr/bin/env python3
"""
Generate COTS Models for Lasius Head Assembly (FreeCAD 1.1+)
============================================================
Components:
  1. TowerPro MG90S Micro Servo (cots/servo_mg90s.FCStd)
  2. Raspberry Pi Camera Module 3 (cots/rpi_camera_v3.FCStd)
  3. MG90S Single-Arm Servo Horn R=15 mm (cots/servo_mg90s_horn.FCStd)
  4. M2 RC Ball-Link Pushrod L=43.81 mm (cots/pushrod_m2_ball_link.FCStd)
"""

import math
import os
import sys
import FreeCAD as App
import Part

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
cots_dir = f"{repo_root}/hardware/mechanics/models/cots"
os.makedirs(cots_dir, exist_ok=True)

# -----------------------------------------------------------------------------
# 1. TowerPro MG90S Micro-Servo (22.8 x 12.2 x 28.5 mm)
# -----------------------------------------------------------------------------
def build_mg90s():
    doc_name = "servo_mg90s"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)
    fcstd_path = f"{cots_dir}/servo_mg90s.FCStd"

    # Main servo body centered in Y, base at Z = 0
    # Length = 22.8 mm (X in [-11.4, 11.4]), Width = 12.2 mm (Y in [-6.1, 6.1]), Height = 22.5 mm (Z in [0, 22.5])
    body = Part.makeBox(22.8, 12.2, 22.5, App.Vector(-11.4, -6.1, 0.0))

    # Mounting Flange Tabs (Z in [16.0, 18.5] mm, Length = 32.5 mm -> X in [-16.25, 16.25])
    flange = Part.makeBox(32.5, 12.2, 2.5, App.Vector(-16.25, -6.1, 16.0))
    # Cut 2x M2 mounting slots at X = ±13.8 mm
    slot_front = Part.makeCylinder(1.1, 4.0, App.Vector(13.8, 0.0, 15.0), App.Vector(0, 0, 1))
    slot_rear = Part.makeCylinder(1.1, 4.0, App.Vector(-13.8, 0.0, 15.0), App.Vector(0, 0, 1))
    flange = flange.cut(slot_front).cut(slot_rear)

    # Top Gearhead Turret (Cylindrical boss, dia 12.0 mm, height 4.5 mm at X = 5.5 mm)
    turret = Part.makeCylinder(6.0, 4.5, App.Vector(5.5, 0.0, 22.5), App.Vector(0, 0, 1))
    # Secondary idler gear boss (dia 6.0 mm, height 2.5 mm at X = -4.5 mm)
    idler = Part.makeCylinder(3.0, 2.5, App.Vector(-4.5, 0.0, 22.5), App.Vector(0, 0, 1))

    # Brass Output Spline (dia 4.8 mm, height 4.0 mm at X = 5.5 mm, Z = 27.0 .. 31.0 mm)
    spline = Part.makeCylinder(2.4, 4.0, App.Vector(5.5, 0.0, 27.0), App.Vector(0, 0, 1))

    # Cable exit boss (lower -X edge)
    cable_collar = Part.makeBox(2.5, 5.0, 4.0, App.Vector(-13.9, -2.5, 2.0))

    servo_solid = body.fuse(flange).fuse(turret).fuse(idler).fuse(spline).fuse(cable_collar)

    obj = doc.addObject("Part::Feature", "Servo_MG90S")
    obj.Label = "TowerPro MG90S Micro Servo (COTS)"
    obj.Shape = servo_solid
    doc.recompute()
    doc.saveAs(fcstd_path)
    App.closeDocument(doc_name)
    print(f"✔ Generated MG90S Micro Servo -> {fcstd_path}")


# -----------------------------------------------------------------------------
# 2. Raspberry Pi Camera Module 3 (25.0 x 24.0 x 11.5 mm)
# -----------------------------------------------------------------------------
def build_rpi_camera_v3():
    doc_name = "rpi_camera_v3"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)
    fcstd_path = f"{cots_dir}/rpi_camera_v3.FCStd"

    # PCB: 25.0 x 24.0 x 1.2 mm (X in [-12.5, 12.5], Y in [-12.0, 12.0], Z in [0, 1.2])
    pcb = Part.makeBox(25.0, 24.0, 1.2, App.Vector(-12.5, -12.0, 0.0))
    # 4x M2 mounting holes (Pattern: 21.0 x 12.5 mm -> X = ±10.5 mm, Y = ±6.25 mm)
    for hx in [-10.5, 10.5]:
        for hy in [-6.25, 6.25]:
            hole = Part.makeCylinder(1.1, 3.0, App.Vector(hx, hy, -1.0), App.Vector(0, 0, 1))
            pcb = pcb.cut(hole)

    # Sony IMX708 Optical Sensor Module (11.5 x 11.5 x 6.5 mm on +Z face)
    sensor_box = Part.makeBox(11.5, 11.5, 6.5, App.Vector(-5.75, -5.75, 1.2))
    # Lens Barrel (dia 8.5 mm, height 3.5 mm on top of sensor box)
    lens = Part.makeCylinder(4.25, 3.5, App.Vector(0.0, 0.0, 7.7), App.Vector(0, 0, 1))

    # FFC Cable Connector (18.0 x 3.5 x 1.5 mm on -Y edge)
    ffc_conn = Part.makeBox(18.0, 3.5, 1.5, App.Vector(-9.0, -12.0, 1.2))

    cam_solid = pcb.fuse(sensor_box).fuse(lens).fuse(ffc_conn)

    obj = doc.addObject("Part::Feature", "RPi_Camera_v3")
    obj.Label = "Raspberry Pi Camera Module 3 (COTS)"
    obj.Shape = cam_solid
    doc.recompute()
    doc.saveAs(fcstd_path)
    App.closeDocument(doc_name)
    print(f"✔ Generated RPi Camera Module 3 -> {fcstd_path}")


# -----------------------------------------------------------------------------
# 3. MG90S Single-Arm Servo Horn (R_HORN = 15.0 mm along +X, hub base at Z = 0)
# -----------------------------------------------------------------------------
def build_mg90s_horn():
    doc_name = "servo_mg90s_horn"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)
    fcstd_path = f"{cots_dir}/servo_mg90s_horn.FCStd"

    # Spline hub: OD 7.2 mm (R=3.6), Z in [0.0, 4.3], bottom spline bore R=2.45 depth 3.85 (clear of 2.40 spline!)
    hub = Part.makeCylinder(3.60, 4.30, App.Vector(0, 0, 0), App.Vector(0, 0, 1))
    spline_bore = Part.makeCylinder(2.45, 3.95, App.Vector(0, 0, -0.10), App.Vector(0, 0, 1))
    screw_bore = Part.makeCylinder(1.05, 5.50, App.Vector(0, 0, -0.50), App.Vector(0, 0, 1))

    # Tapered lever arm extending along +X from X=0 to X=15.0 mm (Z in [1.80, 3.60])
    r0, r1, L = 3.20, 2.00, 15.00
    # Tangent trapezoid + end circles
    ang = math.asin((r0 - r1) / L)
    p0 = App.Vector(r0 * math.sin(ang), r0 * math.cos(ang), 1.80)
    p1 = App.Vector(L + r1 * math.sin(ang), r1 * math.cos(ang), 1.80)
    p2 = App.Vector(L + r1 * math.sin(ang), -r1 * math.cos(ang), 1.80)
    p3 = App.Vector(r0 * math.sin(ang), -r0 * math.cos(ang), 1.80)
    poly = Part.Face(Part.makePolygon([p0, p1, p2, p3, p0])).extrude(App.Vector(0, 0, 1.80))
    tip = Part.makeCylinder(r1, 1.80, App.Vector(L, 0, 1.80), App.Vector(0, 0, 1))

    horn = hub.fuse(poly).fuse(tip).cut(spline_bore).cut(screw_bore)
    for hx in [9.0, 11.0, 13.0, 15.0]:
        hb = Part.makeCylinder(0.85, 4.00, App.Vector(hx, 0, 0.50), App.Vector(0, 0, 1))
        horn = horn.cut(hb)

    horn = horn.removeSplitter()

    obj = doc.addObject("Part::Feature", "Servo_MG90S_Horn")
    obj.Label = "MG90S Single-Arm Servo Horn R=15 mm (COTS)"
    obj.Shape = horn
    doc.recompute()
    doc.saveAs(fcstd_path)
    App.closeDocument(doc_name)
    print(f"✔ Generated MG90S Servo Horn -> {fcstd_path}")


# -----------------------------------------------------------------------------
# 4. M2 RC Ball-Link Pushrod (Ball centers at (0,0,0) and (L_ROD,0,0), eye axis Y)
# -----------------------------------------------------------------------------
def build_pushrod_m2_ball_link(l_rod=40.9850):
    doc_name = "pushrod_m2_ball_link"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)
    fcstd_path = f"{cots_dir}/pushrod_m2_ball_link.FCStd"

    # Central M2 stainless threaded pushrod shaft (Ø2.0 mm, X in [6.0, l_rod - 6.0])
    shaft = Part.makeCylinder(1.00, l_rod - 12.0, App.Vector(6.00, 0, 0), App.Vector(1, 0, 0))

    # Left & Right Nylon Ball-Link Eye Cups (Ball centers at X=0 and X=l_rod, eye axis along Y)
    # Compact RC Heli M2 ball link: Eye OD = 4.6 mm (R=2.30), thickness Y in [-1.50, +1.50],
    # neck collar Ø3.4 mm tapering into M2 rod from X = 2.0 .. 7.0 mm.
    solids = [shaft]
    for cx, dir_x in [(0.0, +1.0), (l_rod, -1.0)]:
        eye = Part.makeCylinder(2.30, 3.00, App.Vector(cx, -1.50, 0), App.Vector(0, 1, 0))
        neck = Part.makeCylinder(1.70, 5.00, App.Vector(cx + dir_x * 2.00, 0, 0), App.Vector(dir_x, 0, 0))
        # Brass swivel ball inside eye (Ø3.6 mm sphere clipped to Y in [-1.60, +1.60])
        ball = Part.makeSphere(1.80, App.Vector(cx, 0, 0))
        ball_clip = Part.makeBox(6.0, 3.20, 6.0, App.Vector(cx - 3.0, -1.60, -3.0))
        ball = ball.common(ball_clip)
        bore = Part.makeCylinder(1.02, 6.00, App.Vector(cx, -3.00, 0), App.Vector(0, 1, 0))
        cup = eye.fuse(neck).fuse(ball).cut(bore)
        solids.append(cup)

    pushrod = solids[0]
    for s in solids[1:]:
        pushrod = pushrod.fuse(s)
    pushrod = pushrod.removeSplitter()

    obj = doc.addObject("Part::Feature", "Pushrod_M2_Ball_Link")
    obj.Label = f"M2 RC Ball-Link Pushrod L={l_rod:.2f} mm (COTS)"
    obj.Shape = pushrod
    doc.recompute()
    doc.saveAs(fcstd_path)
    App.closeDocument(doc_name)
    print(f"✔ Generated M2 Ball-Link Pushrod (L={l_rod:.4f} mm) -> {fcstd_path}")


if __name__ in ("__main__", "generate_head_cots"):
    build_mg90s()
    build_rpi_camera_v3()
    build_mg90s_horn()
    build_pushrod_m2_ball_link()
    if __name__ == "__main__":
        sys.exit(0)
