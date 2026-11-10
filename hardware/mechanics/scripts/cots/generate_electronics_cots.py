#!/usr/bin/env python3
"""
Generate Lasius Hexapod COTS Electronics CAD Models
===================================================
Generates high-fidelity commercial off-the-shelf (COTS) solid CAD models in `models/cots/`:
  1. Raspberry Pi 4 Model B (`rpi4_model_b.FCStd`):
     - 85.0 x 56.0 x 1.4 mm green PCB with R = 3.0 mm filleted corners.
     - 4x M2.5 mounting holes (58.0 x 49.0 mm pattern, centered at origin).
     - BCM2711 SoC metal heatspreader, USB 3.0/2.0 dual blocks, RJ45 Ethernet,
       40-pin GPIO header, USB-C, dual Micro-HDMI, and MicroSD slot.
  2. PCA9685 16-Channel 12-Bit PWM Servo Driver Board (`pca9685_board.FCStd`):
     - 62.5 x 25.4 x 1.6 mm blue PCB with 4x M2.5 mounting holes (56.0 x 19.0 mm pattern).
     - PCA9685 TSSOP chip, power capacitor, 2-pin screw terminal block,
       16x 3-pin servo headers (3x16 pins), and I2C headers.
  3. TCA9548A 8-Channel I2C Multiplexer Breakout (`tca9548a_board.FCStd`):
     - 31.5 x 21.0 x 1.6 mm purple PCB with 2x M2.5 mounting holes (26.0 mm spacing).
     - TCA9548A TSSOP-24 chip and dual 12-pin headers.
  4. VL53L5CX 9-Zone Time-of-Flight Terrain Distance Sensor (`vl53l5cx_board.FCStd`):
     - 24.0 x 18.0 x 1.6 mm red PCB with 4x M2 mounting holes (21.0 x 13.0 mm pattern).
     - Optical sensor module (6.4 x 3.0 x 1.2 mm) with dual emitter/receiver lenses,
       and 6-pin I2C header.

Exports:
  - Models:  `hardware/mechanics/models/cots/*.FCStd`
  - STEP:    `hardware/mechanics/export/step/cots/*.step`
  - STL:     `hardware/mechanics/export/stl/cots/*.stl`
"""

import math
import os
import FreeCAD as App
import Part

print("--- Generating Lasius COTS Electronics Models (FreeCAD 1.1+) ---")

cots_models_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/models/cots"
cots_step_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/step/cots"
cots_stl_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/stl/cots"

os.makedirs(cots_models_dir, exist_ok=True)
os.makedirs(cots_step_dir, exist_ok=True)
os.makedirs(cots_stl_dir, exist_ok=True)


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


# =============================================================================
# 1. Raspberry Pi 4 Model B
# =============================================================================
def build_rpi4():
    doc_name = "rpi4_model_b"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)

    # PCB centered at (0, 0, 0). Length = 85.0 mm (X in [-42.5, 42.5]), Width = 56.0 mm (Y in [-28.0, 28.0])
    pcb = make_rounded_rect_solid(-42.5, 42.5, -28.0, 28.0, 3.0, 0.0, 1.4)

    # 4x M2.5 Mounting Holes (Pattern: 58.0 x 49.0 mm -> X = ±29.0 mm, Y = ±24.5 mm)
    for hx in [-29.0, 29.0]:
        for hy in [-24.5, 24.5]:
            hole = Part.makeCylinder(1.35, 5.0, App.Vector(hx, hy, -1.0), App.Vector(0, 0, 1))
            pcb = pcb.cut(hole)

    # Broadcom BCM2711 SoC Heatspreader (15.0 x 15.0 x 1.8 mm)
    soc = Part.makeBox(15.0, 15.0, 1.8, App.Vector(-2.5, -7.5, 1.4))

    # Dual USB 3.0 Port Block (Blue, 17.0 x 14.5 x 16.0 mm on +X front edge)
    usb3 = Part.makeBox(17.0, 14.5, 16.0, App.Vector(27.0, -22.5, 1.4))

    # Dual USB 2.0 Port Block (Black, 17.0 x 14.5 x 16.0 mm on +X front edge)
    usb2 = Part.makeBox(17.0, 14.5, 16.0, App.Vector(27.0, -5.5, 1.4))

    # Gigabit Ethernet Port Block (Metal, 21.5 x 16.0 x 14.0 mm on +X front edge)
    eth = Part.makeBox(21.5, 16.0, 14.0, App.Vector(23.5, 10.5, 1.4))

    # 40-Pin GPIO Header (51.0 x 5.0 x 8.5 mm along +Y edge)
    gpio = Part.makeBox(51.0, 5.0, 8.5, App.Vector(-28.0, 21.5, 1.4))

    # USB-C Power Port (9.0 x 7.5 x 3.2 mm on -Y edge)
    usbc = Part.makeBox(9.0, 7.5, 3.2, App.Vector(-31.5, -28.0, 1.4))

    # Dual Micro-HDMI Ports (7.5 x 6.5 x 3.0 mm on -Y edge)
    hdmi1 = Part.makeBox(7.5, 6.5, 3.0, App.Vector(-15.0, -28.0, 1.4))
    hdmi2 = Part.makeBox(7.5, 6.5, 3.0, App.Vector(-4.0, -28.0, 1.4))

    # MicroSD Card Slot on Underside (14.0 x 12.0 x 1.2 mm on -X edge)
    sd = Part.makeBox(14.0, 12.0, 1.2, App.Vector(-42.5, -6.0, -1.2))

    rpi_solid = pcb.fuse(soc).fuse(usb3).fuse(usb2).fuse(eth).fuse(gpio).fuse(usbc).fuse(hdmi1).fuse(hdmi2).fuse(sd)

    obj = doc.addObject("Part::Feature", "Raspberry_Pi_4")
    obj.Label = "Raspberry Pi 4 Model B (COTS)"
    obj.Shape = rpi_solid
    doc.recompute()

    fcstd_path = f"{cots_models_dir}/rpi4_model_b.FCStd"
    doc.saveAs(fcstd_path)
    rpi_solid.exportStep(f"{cots_step_dir}/rpi4_model_b.step")
    rpi_solid.exportStl(f"{cots_stl_dir}/rpi4_model_b.stl")
    App.closeDocument(doc_name)
    print(f"✔ Generated Raspberry Pi 4 Model B -> {fcstd_path}")


# =============================================================================
# 2. PCA9685 16-Channel PWM Servo Driver Board
# =============================================================================
def build_pca9685():
    doc_name = "pca9685_board"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)

    # PCB centered at (0, 0, 0). Length = 62.5 mm (X in [-31.25, 31.25]), Width = 25.4 mm (Y in [-12.7, 12.7])
    pcb = make_rounded_rect_solid(-31.25, 31.25, -12.7, 12.7, 2.0, 0.0, 1.6)

    # 4x M2.5 Mounting Holes (Pattern: 56.0 x 19.0 mm -> X = ±28.0 mm, Y = ±9.5 mm)
    for hx in [-28.0, 28.0]:
        for hy in [-9.5, 9.5]:
            hole = Part.makeCylinder(1.25, 5.0, App.Vector(hx, hy, -1.0), App.Vector(0, 0, 1))
            pcb = pcb.cut(hole)

    # PCA9685 TSSOP-28 IC Chip (9.7 x 4.4 x 1.1 mm)
    ic = Part.makeBox(9.7, 4.4, 1.1, App.Vector(-4.85, -2.2, 1.6))

    # Power Capacitor (Ø8.0 x 11.5 mm cylinder)
    cap = Part.makeCylinder(4.0, 11.5, App.Vector(-22.0, -5.0, 1.6), App.Vector(0, 0, 1))

    # Screw Terminal Block (10.0 x 8.0 x 10.0 mm)
    term = Part.makeBox(10.0, 8.0, 10.0, App.Vector(-23.0, 3.5, 1.6))

    # 16x 3-Pin Servo Pin Headers (3 rows of 16 pins, width 7.62 mm, length 40.64 mm, height 11.5 mm)
    headers = Part.makeBox(40.64, 7.62, 11.5, App.Vector(-12.0, -3.81, 1.6))

    # I2C Input Header (6-pin on -X edge) & Cascade Header (6-pin on +X edge)
    i2c_in = Part.makeBox(2.54, 15.24, 8.5, App.Vector(-30.0, -7.62, 1.6))
    i2c_out = Part.makeBox(2.54, 15.24, 8.5, App.Vector(27.46, -7.62, 1.6))

    pca_solid = pcb.fuse(ic).fuse(cap).fuse(term).fuse(headers).fuse(i2c_in).fuse(i2c_out)

    obj = doc.addObject("Part::Feature", "PCA9685_Board")
    obj.Label = "PCA9685 16-Channel PWM Servo Controller (COTS)"
    obj.Shape = pca_solid
    doc.recompute()

    fcstd_path = f"{cots_models_dir}/pca9685_board.FCStd"
    doc.saveAs(fcstd_path)
    pca_solid.exportStep(f"{cots_step_dir}/pca9685_board.step")
    pca_solid.exportStl(f"{cots_stl_dir}/pca9685_board.stl")
    App.closeDocument(doc_name)
    print(f"✔ Generated PCA9685 16-Channel Board -> {fcstd_path}")


# =============================================================================
# 3. TCA9548A 8-Channel I2C Multiplexer Breakout
# =============================================================================
def build_tca9548a():
    doc_name = "tca9548a_board"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)

    # PCB centered at (0, 0, 0). Length = 31.5 mm (X in [-15.75, 15.75]), Width = 21.0 mm (Y in [-10.5, 10.5])
    pcb = make_rounded_rect_solid(-15.75, 15.75, -10.5, 10.5, 1.5, 0.0, 1.6)

    # 2x M2.5 Mounting Holes (Spacing 26.0 mm -> X = ±13.0 mm, Y = 0.0 mm)
    for hx in [-13.0, 13.0]:
        hole = Part.makeCylinder(1.25, 5.0, App.Vector(hx, 0.0, -1.0), App.Vector(0, 0, 1))
        pcb = pcb.cut(hole)

    # TCA9548A TSSOP-24 IC Chip (7.8 x 4.4 x 1.1 mm)
    ic = Part.makeBox(7.8, 4.4, 1.1, App.Vector(-3.9, -2.2, 1.6))

    # Dual 12-Pin Headers (30.48 x 2.54 x 8.5 mm along long edges)
    h_top = Part.makeBox(30.48, 2.54, 8.5, App.Vector(-15.24, 7.5, 1.6))
    h_bot = Part.makeBox(30.48, 2.54, 8.5, App.Vector(-15.24, -10.04, 1.6))

    tca_solid = pcb.fuse(ic).fuse(h_top).fuse(h_bot)

    obj = doc.addObject("Part::Feature", "TCA9548A_Board")
    obj.Label = "TCA9548A 8-Channel I2C Multiplexer (COTS)"
    obj.Shape = tca_solid
    doc.recompute()

    fcstd_path = f"{cots_models_dir}/tca9548a_board.FCStd"
    doc.saveAs(fcstd_path)
    tca_solid.exportStep(f"{cots_step_dir}/tca9548a_board.step")
    tca_solid.exportStl(f"{cots_stl_dir}/tca9548a_board.stl")
    App.closeDocument(doc_name)
    print(f"✔ Generated TCA9548A 8-Channel Multiplexer -> {fcstd_path}")


# =============================================================================
# 4. VL53L5CX 9-Zone Time-of-Flight Distance Sensor Breakout
# =============================================================================
def build_vl53l5cx():
    doc_name = "vl53l5cx_board"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)

    # PCB centered at (0, 0, 0). Length = 24.0 mm (X in [-12.0, 12.0]), Width = 18.0 mm (Y in [-9.0, 9.0])
    pcb = make_rounded_rect_solid(-12.0, 12.0, -9.0, 9.0, 1.5, 0.0, 1.6)

    # 4x M2 Mounting Holes (Pattern: 21.0 x 13.0 mm -> X = ±10.5 mm, Y = ±6.5 mm)
    for hx in [-10.5, 10.5]:
        for hy in [-6.5, 6.5]:
            hole = Part.makeCylinder(1.05, 5.0, App.Vector(hx, hy, -1.0), App.Vector(0, 0, 1))
            pcb = pcb.cut(hole)

    # VL53L5CX Optical Sensor Package (6.4 x 3.0 x 1.2 mm)
    sensor = Part.makeBox(6.4, 3.0, 1.2, App.Vector(-3.2, -1.5, 1.6))

    # Dual Optical Aperture / Lenses (2x Ø1.0 mm cylinders)
    lens1 = Part.makeCylinder(0.55, 0.4, App.Vector(-1.5, 0.0, 2.8), App.Vector(0, 0, 1))
    lens2 = Part.makeCylinder(0.55, 0.4, App.Vector(1.5, 0.0, 2.8), App.Vector(0, 0, 1))

    # 6-Pin I2C Header (15.24 x 2.54 x 8.5 mm on -Y edge)
    header = Part.makeBox(15.24, 2.54, 8.5, App.Vector(-7.62, -8.5, 1.6))

    tof_solid = pcb.fuse(sensor).fuse(lens1).fuse(lens2).fuse(header)

    obj = doc.addObject("Part::Feature", "VL53L5CX_Board")
    obj.Label = "VL53L5CX 9-Zone ToF Terrain Distance Sensor (COTS)"
    obj.Shape = tof_solid
    doc.recompute()

    fcstd_path = f"{cots_models_dir}/vl53l5cx_board.FCStd"
    doc.saveAs(fcstd_path)
    tof_solid.exportStep(f"{cots_step_dir}/vl53l5cx_board.step")
    tof_solid.exportStl(f"{cots_stl_dir}/vl53l5cx_board.stl")
    App.closeDocument(doc_name)
    print(f"✔ Generated VL53L5CX ToF Sensor -> {fcstd_path}")


# =============================================================================
# 5. 2S 7.4V LiPo Battery Pack (Slim Flat-Pack)
# =============================================================================
def build_battery_lipo_2s():
    doc_name = "battery_lipo_2s"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)

    # Battery main pack centered at (0, 0) in X/Y, Z in [0.0, 14.0 mm].
    # Dimensions: 88.0 x 35.0 x 14.0 mm with filleted corners (R = 3.5 mm)
    pack = make_rounded_rect_solid(-44.0, 44.0, -17.5, 17.5, 3.5, 0.0, 14.0)

    # Output Lead Cable Exit Strain Relief Collar (-X end, centered in Y)
    collar = Part.makeBox(4.0, 12.0, 7.0, App.Vector(-48.0, -6.0, 3.5))

    # 12AWG Silicone Main Leads (Pair of D = 3.5 mm cables extending in -X direction)
    cable_pos = Part.makeCylinder(1.75, 20.0, App.Vector(-48.0, 3.0, 7.0), App.Vector(-1, 0, 0))
    cable_neg = Part.makeCylinder(1.75, 20.0, App.Vector(-48.0, -3.0, 7.0), App.Vector(-1, 0, 0))

    # Amass XT60 Connector Body (15.5 x 16.0 x 8.0 mm) at the end of the cables
    xt60 = Part.makeBox(15.5, 16.0, 8.0, App.Vector(-83.5, -8.0, 3.0))

    # JST-XH 3-Pin Balance Lead (5.5 x 9.8 x 6.0 mm) exiting beside main leads
    jst_xh = Part.makeBox(5.5, 9.8, 6.0, App.Vector(-55.0, 8.0, 4.0))

    bat_solid = pack.fuse(collar).fuse(cable_pos).fuse(cable_neg).fuse(xt60).fuse(jst_xh)

    obj = doc.addObject("Part::Feature", "Battery_LiPo_2S")
    obj.Label = "2S 7.4V LiPo Battery Pack (COTS)"
    obj.Shape = bat_solid
    doc.recompute()

    fcstd_path = f"{cots_models_dir}/battery_lipo_2s.FCStd"
    doc.saveAs(fcstd_path)
    bat_solid.exportStep(f"{cots_step_dir}/battery_lipo_2s.step")
    bat_solid.exportStl(f"{cots_stl_dir}/battery_lipo_2s.stl")
    App.closeDocument(doc_name)
    print(f"✔ Generated 2S LiPo Battery Pack -> {fcstd_path}")


# Execute all builds
build_rpi4()
build_pca9685()
build_tca9548a()
build_vl53l5cx()
build_battery_lipo_2s()

print("--- All Electronics & Power COTS Models Generated Successfully ---")
import sys
sys.exit(0)
