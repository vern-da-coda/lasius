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
import sys
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


def make_pin_header_1row(x_c, y_c, z_base, pins, orient_x=True, pin_len=8.50, collar_h=2.50):
    """Creates a 1-row Dupont header with thermoplastic collar base and discrete gold square pins."""
    pitch = 2.54
    pin_w = 0.64
    if orient_x:
        len_x = pins * pitch
        len_y = pitch
    else:
        len_x = pitch
        len_y = pins * pitch
    collar = Part.makeBox(len_x, len_y, collar_h, App.Vector(x_c - len_x / 2.0, y_c - len_y / 2.0, z_base))
    compound = collar
    for i in range(pins):
        if orient_x:
            px = x_c - len_x / 2.0 + (i + 0.5) * pitch
            py = y_c
        else:
            px = x_c
            py = y_c - len_y / 2.0 + (i + 0.5) * pitch
        pin = Part.makeBox(pin_w, pin_w, pin_len, App.Vector(px - pin_w / 2.0, py - pin_w / 2.0, z_base - 1.0))
        compound = compound.fuse(pin)
    return compound.removeSplitter()


def make_pin_header_2row(x_c, y_c, z_base, cols, orient_x=True, pin_len=8.50, collar_h=2.50):
    """Creates a 2-row Dupont header (e.g. 2x20 RPi GPIO) with collar base and discrete gold pins."""
    pitch = 2.54
    pin_w = 0.64
    if orient_x:
        len_x = cols * pitch
        len_y = 2.0 * pitch
    else:
        len_x = 2.0 * pitch
        len_y = cols * pitch
    collar = Part.makeBox(len_x, len_y, collar_h, App.Vector(x_c - len_x / 2.0, y_c - len_y / 2.0, z_base))
    compound = collar
    for r in range(2):
        for c in range(cols):
            if orient_x:
                px = x_c - len_x / 2.0 + (c + 0.5) * pitch
                py = y_c - len_y / 2.0 + (r + 0.5) * pitch
            else:
                px = x_c - len_x / 2.0 + (r + 0.5) * pitch
                py = y_c - len_y / 2.0 + (c + 0.5) * pitch
            pin = Part.makeBox(pin_w, pin_w, pin_len, App.Vector(px - pin_w / 2.0, py - pin_w / 2.0, z_base - 1.0))
            compound = compound.fuse(pin)
    return compound.removeSplitter()


def make_right_angle_servo_header_3x16(x_c, y_base, z_base, cols=16):
    """
    Creates a 16x 3-pin (3x16 = 48 pins) 90° right-angle servo header.
    Pins extend from PCB horizontally in +Y direction.
    """
    pitch = 2.54
    pin_w = 0.64
    len_x = cols * pitch  # 40.64 mm
    collar_w = 4.50
    collar_h = 3.00
    collar = Part.makeBox(len_x, collar_w, collar_h, App.Vector(x_c - len_x / 2.0, y_base, z_base))
    compound = collar
    pin_horiz_len = 8.70  # extends horizontally past Y = 12.0 to Y = 20.7 mm
    for row in range(3):
        pz = z_base + 0.90 + row * 2.54
        for col in range(cols):
            px = x_c - len_x / 2.0 + (col + 0.5) * pitch
            # Vertical leg from PCB
            vert_leg = Part.makeBox(pin_w, pin_w, pz - z_base + pin_w, App.Vector(px - pin_w / 2.0, y_base + 1.2, z_base - 0.8))
            # Horizontal leg extending in +Y
            horiz_leg = Part.makeBox(pin_w, pin_horiz_len, pin_w, App.Vector(px - pin_w / 2.0, y_base + 1.2, pz))
            pin_solid = vert_leg.fuse(horiz_leg)
            compound = compound.fuse(pin_solid)
    return compound.removeSplitter()


def make_right_angle_header_1row(x_c, y_base, z_base, pins=6, dir_y=-1.0):
    """Creates a 1-row 90° right-angle Dupont header with discrete pins."""
    pitch = 2.54
    pin_w = 0.64
    len_x = pins * pitch
    collar_w = 2.54
    collar_h = 2.50
    collar = Part.makeBox(len_x, collar_w, collar_h, App.Vector(x_c - len_x / 2.0, y_base, z_base))
    compound = collar
    horiz_len = 5.00
    for i in range(pins):
        px = x_c - len_x / 2.0 + (i + 0.5) * pitch
        py_start = y_base if dir_y < 0 else y_base + collar_w
        py_end = py_start + dir_y * horiz_len
        ymin, ymax = min(py_start, py_end), max(py_start, py_end)
        # Vertical pin leg
        vert_leg = Part.makeBox(pin_w, pin_w, 2.00, App.Vector(px - pin_w / 2.0, y_base + collar_w / 2.0 - pin_w / 2.0, z_base - 0.8))
        # Horizontal pin leg
        horiz_leg = Part.makeBox(pin_w, ymax - ymin, pin_w, App.Vector(px - pin_w / 2.0, ymin, z_base + 1.25 - pin_w / 2.0))
        compound = compound.fuse(vert_leg).fuse(horiz_leg)
    return compound.removeSplitter()


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

    # Broadcom BCM2711 SoC Heatspreader (15.0 x 15.0 x 1.8 mm)
    soc = Part.makeBox(15.0, 15.0, 1.8, App.Vector(-12.5, -7.5, 1.4))

    # Dual USB 3.0 Port Block (Blue, 17.0 x 14.5 x 16.0 mm on +X front edge)
    usb3 = Part.makeBox(17.0, 14.5, 16.0, App.Vector(27.0, -22.5, 1.4))

    # Dual USB 2.0 Port Block (Black, 17.0 x 14.5 x 16.0 mm on +X front edge)
    usb2 = Part.makeBox(17.0, 14.5, 16.0, App.Vector(27.0, -5.5, 1.4))

    # Gigabit Ethernet Port Block (Metal, 21.5 x 16.0 x 14.0 mm on +X front edge)
    eth = Part.makeBox(21.5, 16.0, 14.0, App.Vector(23.5, 10.5, 1.4))

    # 40-Pin GPIO Header (2x20 pins with individual square pins and collar base along +Y edge)
    gpio = make_pin_header_2row(x_c=-10.0, y_c=24.50, z_base=1.4, cols=20, orient_x=True)

    # USB-C Power Port (9.0 x 7.5 x 3.2 mm on -Y edge)
    usbc = Part.makeBox(9.0, 7.5, 3.2, App.Vector(-35.0, -28.0, 1.4))

    # Dual Micro-HDMI Ports (7.5 x 6.5 x 3.0 mm on -Y edge)
    hdmi1 = Part.makeBox(7.5, 6.5, 3.0, App.Vector(-20.0, -28.0, 1.4))
    hdmi2 = Part.makeBox(7.5, 6.5, 3.0, App.Vector(-6.5, -28.0, 1.4))

    # MicroSD Card Slot on Underside (14.0 x 12.0 x 1.2 mm on -X edge)
    sd = Part.makeBox(14.0, 12.0, 1.2, App.Vector(-42.5, -6.0, -1.2))

    rpi_solid = pcb.fuse(soc).fuse(usb3).fuse(usb2).fuse(eth).fuse(gpio).fuse(usbc).fuse(hdmi1).fuse(hdmi2).fuse(sd)
    rpi_solid = rpi_solid.removeSplitter()

    # 4x Official Raspberry Pi 4 M2.5 Mounting Holes (58.0 x 49.0 mm pattern: 3.5 mm from -X/+Y/-Y edges -> X in [-39.0, +19.0], Y in [-24.5, +24.5])
    for hx in [-39.0, 19.0]:
        for hy in [-24.5, 24.5]:
            hole = Part.makeCylinder(1.35, 6.0, App.Vector(hx, hy, -2.0), App.Vector(0, 0, 1))
            rpi_solid = rpi_solid.cut(hole)

    obj = doc.addObject("Part::Feature", "Raspberry_Pi_4")
    obj.Label = "Raspberry Pi 4 Model B (COTS)"
    obj.Shape = rpi_solid
    doc.recompute()

    fcstd_path = f"{cots_models_dir}/rpi4_model_b.FCStd"
    doc.saveAs(fcstd_path)
    if "--export" in sys.argv:
        rpi_solid.exportStep(f"{cots_step_dir}/rpi4_model_b.step")
        rpi_solid.exportStl(f"{cots_stl_dir}/rpi4_model_b.stl")
    App.closeDocument(doc_name)
    print(f"✔ Generated Raspberry Pi 4 Model B -> {fcstd_path}")


# =============================================================================
# 2. PCA9685 16-Channel PWM Servo Driver Board (COTS)
# =============================================================================
def build_pca9685():
    """
    Constructs high-fidelity PCA9685 16-Channel 12-Bit PWM Driver Board (Adafruit).
    Reflects physical reference photo PXL_20261110_220915159.jpg:
      - 62.5 x 25.4 x 1.6 mm blue PCB with 4x M2.5 mounting holes (56.0 x 19.0 mm pattern).
      - 16x 3-pin right-angle servo headers (90-degree bend) extending horizontally
        in +Y direction past the PCB edge for lateral servo connector insertion.
      - Dual 6-pin I2C headers pointing vertically (+Z) on short edges (-X and +X).
      - 2-pin screw terminal block on -Y edge with wire entry facing outward (-Y).
      - Cylindrical electrolytic power capacitor (Ø8.0 x 12.5 mm) at corner.
      - PCA9685 TSSOP-28 chip centered on PCB.
    """
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

    # Power Capacitor (Ø8.0 x 12.5 mm cylinder at -X / -Y corner)
    cap = Part.makeCylinder(4.0, 12.5, App.Vector(-21.0, -7.5, 1.6), App.Vector(0, 0, 1))

    # Blue 2-Pin Screw Terminal Block (10.0 x 8.0 x 10.0 mm on -Y edge)
    # Wire entrances face in -Y direction, clamping screws on top face (+Z)
    term_body = Part.makeBox(10.0, 8.0, 10.0, App.Vector(-14.0, -12.5, 1.6))
    term_cav1 = Part.makeBox(3.0, 4.0, 4.0, App.Vector(-13.0, -13.0, 3.5))
    term_cav2 = Part.makeBox(3.0, 4.0, 4.0, App.Vector(-8.0, -13.0, 3.5))
    term = term_body.cut(term_cav1).cut(term_cav2)

    # 16x 3-Pin Servo Pin Headers (90° Right Angle with 48 discrete pins pointing horizontally in +Y direction)
    headers = make_right_angle_servo_header_3x16(x_c=0.00, y_base=7.50, z_base=1.60, cols=16)

    # Dual 6-Pin I2C Headers (Straight pins pointing vertically +Z on -X and +X edges with discrete square pins)
    i2c_in = make_pin_header_1row(x_c=-28.00, y_c=0.00, z_base=1.60, pins=6, orient_x=False)
    i2c_out = make_pin_header_1row(x_c=28.00, y_c=0.00, z_base=1.60, pins=6, orient_x=False)

    pca_solid = pcb.fuse(ic).fuse(cap).fuse(term).fuse(headers).fuse(i2c_in).fuse(i2c_out)
    pca_solid = pca_solid.removeSplitter()

    obj = doc.addObject("Part::Feature", "PCA9685_Board")
    obj.Label = "PCA9685 16-Channel PWM Servo Controller (COTS)"
    obj.Shape = pca_solid
    doc.recompute()

    fcstd_path = f"{cots_models_dir}/pca9685_board.FCStd"
    doc.saveAs(fcstd_path)
    if "--export" in sys.argv:
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

    # Dual 12-Pin Headers (Straight pins pointing vertically +Z with discrete square pins and collar base)
    h_top = make_pin_header_1row(x_c=0.00, y_c=8.77, z_base=1.60, pins=12, orient_x=True)
    h_bot = make_pin_header_1row(x_c=0.00, y_c=-8.77, z_base=1.60, pins=12, orient_x=True)

    tca_solid = pcb.fuse(ic).fuse(h_top).fuse(h_bot)
    tca_solid = tca_solid.removeSplitter()

    obj = doc.addObject("Part::Feature", "TCA9548A_Board")
    obj.Label = "TCA9548A 8-Channel I2C Multiplexer (COTS)"
    obj.Shape = tca_solid
    doc.recompute()

    fcstd_path = f"{cots_models_dir}/tca9548a_board.FCStd"
    doc.saveAs(fcstd_path)
    if "--export" in sys.argv:
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

    # 6-Pin 90-Degree Right-Angle I2C Header on back side with discrete pins
    header = make_right_angle_header_1row(x_c=0.00, y_base=-8.50, z_base=-2.50, pins=6, dir_y=-1.0)

    tof_solid = pcb.fuse(sensor).fuse(lens1).fuse(lens2).fuse(header)
    tof_solid = tof_solid.removeSplitter()

    obj = doc.addObject("Part::Feature", "VL53L5CX_Board")
    obj.Label = "VL53L5CX 9-Zone ToF Terrain Distance Sensor (COTS)"
    obj.Shape = tof_solid
    doc.recompute()

    fcstd_path = f"{cots_models_dir}/vl53l5cx_board.FCStd"
    doc.saveAs(fcstd_path)
    if "--export" in sys.argv:
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
    bat_solid = bat_solid.removeSplitter()

    obj = doc.addObject("Part::Feature", "Battery_LiPo_2S")
    obj.Label = "2S 7.4V LiPo Battery Pack (COTS)"
    obj.Shape = bat_solid
    doc.recompute()

    fcstd_path = f"{cots_models_dir}/battery_lipo_2s.FCStd"
    doc.saveAs(fcstd_path)
    if "--export" in sys.argv:
        bat_solid.exportStep(f"{cots_step_dir}/battery_lipo_2s.step")
        bat_solid.exportStl(f"{cots_stl_dir}/battery_lipo_2s.stl")
    App.closeDocument(doc_name)
    print(f"✔ Generated 2S LiPo Battery Pack -> {fcstd_path}")


# =============================================================================
# 6. ADS1115 16-Bit 4-Channel I2C ADC Breakout (Adafruit Blue)
# =============================================================================
def build_ads1115():
    doc_name = "ads1115_board"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)

    # 28.0 x 17.0 x 1.6 mm blue PCB with 2x M2.5 mounting holes
    pcb = make_rounded_rect_solid(-14.0, 14.0, -8.5, 8.5, 2.0, 0.0, 1.6)

    # 2x M2.5 mounting holes at X = ±10.1 mm, Y = 5.3 mm
    for hx in [-10.1, 10.1]:
        hole = Part.makeCylinder(1.25, 5.0, App.Vector(hx, 5.3, -1.0), App.Vector(0, 0, 1))
        pcb = pcb.cut(hole)

    # ADS1115 MSOP-10 IC Chip (3.0 x 3.0 x 1.1 mm)
    ic = Part.makeBox(3.0, 3.0, 1.1, App.Vector(-1.5, -1.5, 1.6))

    # 10-Pin Header along bottom edge with discrete gold square pins and collar base
    hdr = make_pin_header_1row(x_c=0.00, y_c=-6.35, z_base=1.60, pins=10, orient_x=True)

    ads_solid = pcb.fuse(ic).fuse(hdr)
    ads_solid = ads_solid.removeSplitter()

    obj = doc.addObject("Part::Feature", "ADS1115_Board")
    obj.Label = "ADS1115 16-Bit 4-Channel ADC (COTS)"
    obj.Shape = ads_solid
    doc.recompute()

    fcstd_path = f"{cots_models_dir}/ads1115_board.FCStd"
    doc.saveAs(fcstd_path)
    if "--export" in sys.argv:
        ads_solid.exportStep(f"{cots_step_dir}/ads1115_board.step")
        ads_solid.exportStl(f"{cots_stl_dir}/ads1115_board.stl")
    App.closeDocument(doc_name)
    print(f"✔ Generated ADS1115 16-Bit ADC Breakout -> {fcstd_path}")


# Execute all builds
build_rpi4()
build_pca9685()
build_tca9548a()
build_vl53l5cx()
build_battery_lipo_2s()
build_ads1115()

print("--- All Electronics & Power COTS Models Generated Successfully ---")
import sys
sys.exit(0)
