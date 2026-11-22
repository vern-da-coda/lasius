#!/usr/bin/env python3
"""
Generate Lasius Hexapod COTS Electronics CAD Models
===================================================
Generates high-fidelity commercial off-the-shelf (COTS) CAD models in `models/cots/`:
  1. Raspberry Pi 4 Model B (`rpi4_model_b.FCStd`):
     - 85.0 x 56.0 x 1.4 mm green PCB with R = 3.0 mm filleted corners.
     - 4x M2.5 mounting holes (58.0 x 49.0 mm pattern, centered at origin).
     - BCM2711 SoC metal heatspreader, USB 3.0/2.0 dual blocks, RJ45 Ethernet,
       USB-C, dual Micro-HDMI, MicroSD slot.
     - 40-Pin GPIO Header referenced via App::Link to `header_pin_2x20.FCStd`.
  2. PCA9685 16-Channel 12-Bit PWM Servo Driver Board (`pca9685_board.FCStd`):
     - 62.5 x 25.4 x 1.6 mm blue PCB with 4x M2.5 mounting holes (56.0 x 19.0 mm pattern).
     - PCA9685 TSSOP chip, power capacitor, 2-pin screw terminal block.
     - 16x 3-pin servo headers referenced via App::Link to `header_pin_3x16_ra.FCStd`.
     - Dual 6-pin I2C headers referenced via App::Link to `header_pin_1x6.FCStd`.
  3. TCA9548A 8-Channel I2C Multiplexer Breakout (`tca9548a_board.FCStd`):
     - 31.5 x 21.0 x 1.6 mm purple PCB with 2x M2.5 mounting holes (26.0 mm spacing).
     - TCA9548A TSSOP-24 chip.
     - Dual 12-pin headers referenced via App::Link to `header_pin_1x12.FCStd`.
  4. VL53L5CX 9-Zone Time-of-Flight Terrain Distance Sensor (`vl53l5cx_board.FCStd`):
     - 24.0 x 18.0 x 1.6 mm red PCB with 4x M2 mounting holes (21.0 x 13.0 mm pattern).
     - Optical sensor module with dual lenses.
     - 6-pin 90° right-angle I2C header referenced via App::Link to `header_pin_1x6_ra.FCStd`.
  5. 2S 7.4V LiPo Battery Pack (`battery_lipo_2s.FCStd`):
     - 88.0 x 35.0 x 14.0 mm slim pack, silicone leads, XT60, JST-XH.
  6. ADS1115 16-Bit 4-Channel I2C ADC Breakout (`ads1115_board.FCStd`):
     - 28.0 x 17.0 x 1.6 mm blue PCB with 2x M2.5 mounting holes.
     - ADS1115 MSOP-10 IC chip.
     - 10-pin header referenced via App::Link to `header_pin_1x10.FCStd`.

Standards:
  - Header Sockets & Collars: Always black thermoplastic (0.12, 0.12, 0.12)
  - Header Pins: Always gold/brass (0.85, 0.70, 0.20)
  - References: App::Link to standard COTS header files
"""

import math
import os
import sys
import FreeCAD as App
import Part

print("=== Generating Lasius COTS Electronics Models with COTS Header References ===")

cots_models_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/models/cots"
cots_step_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/step/cots"
cots_stl_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/stl/cots"

os.makedirs(cots_models_dir, exist_ok=True)

# Visual colors
COLOR_PCB_GREEN = (0.12, 0.45, 0.22)   # RPi 4 FR4
COLOR_PCB_BLUE  = (0.04, 0.38, 0.88)   # Adafruit Blue (PCA9685, ADS1115)
COLOR_PCB_PURPLE= (0.50, 0.15, 0.70)   # SparkFun / Adafruit Purple (TCA9548A)
COLOR_PCB_RED   = (0.85, 0.15, 0.15)   # SparkFun Red (VL53L5CX)
COLOR_IC_BLACK  = (0.15, 0.15, 0.15)   # Epoxy IC packaging
COLOR_METAL     = (0.75, 0.75, 0.78)   # USB / Ethernet metal shielding
COLOR_USB3_BLUE = (0.05, 0.35, 0.85)   # USB 3.0 insert
COLOR_TERM_BLUE = (0.10, 0.40, 0.80)   # Screw terminal block


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
    fcstd_path = f"{cots_models_dir}/rpi4_model_b.FCStd"
    doc.saveAs(fcstd_path)

    # 1. PCB Substrate (85.0 x 56.0 x 1.4 mm, green)
    pcb = make_rounded_rect_solid(-42.5, 42.5, -28.0, 28.0, 3.0, 0.0, 1.4)
    for hx in [-39.0, 19.0]:
        for hy in [-24.5, 24.5]:
            hole = Part.makeCylinder(1.35, 6.0, App.Vector(hx, hy, -2.0), App.Vector(0, 0, 1))
            pcb = pcb.cut(hole)
    pcb = pcb.removeSplitter()

    # 2. Ports & Components
    soc = Part.makeBox(15.0, 15.0, 1.8, App.Vector(-12.5, -7.5, 1.4))
    usb3 = Part.makeBox(17.0, 14.5, 16.0, App.Vector(27.0, -22.5, 1.4))
    usb2 = Part.makeBox(17.0, 14.5, 16.0, App.Vector(27.0, -5.5, 1.4))
    eth = Part.makeBox(21.5, 16.0, 14.0, App.Vector(23.5, 10.5, 1.4))
    usbc = Part.makeBox(9.0, 7.5, 3.2, App.Vector(-35.0, -28.0, 1.4))
    hdmi1 = Part.makeBox(7.5, 6.5, 3.0, App.Vector(-20.0, -28.0, 1.4))
    hdmi2 = Part.makeBox(7.5, 6.5, 3.0, App.Vector(-6.5, -28.0, 1.4))
    sd = Part.makeBox(14.0, 12.0, 1.2, App.Vector(-42.5, -6.0, -1.2))

    ports = soc.fuse(usb3).fuse(usb2).fuse(eth).fuse(usbc).fuse(hdmi1).fuse(hdmi2).fuse(sd).removeSplitter()

    # Create Assembly Part
    part = doc.addObject("App::Part", "Raspberry_Pi_4")
    part.Label = "Raspberry Pi 4 Model B (COTS)"

    obj_pcb = doc.addObject("Part::Feature", "RPi4_PCB")
    obj_pcb.Label = "Raspberry Pi 4 PCB Substrate (Green)"
    obj_pcb.Shape = pcb
    if hasattr(obj_pcb, "ViewObject") and obj_pcb.ViewObject:
        obj_pcb.ViewObject.ShapeColor = COLOR_PCB_GREEN
    part.addObject(obj_pcb)

    obj_ports = doc.addObject("Part::Feature", "RPi4_Components")
    obj_ports.Label = "Ports & SoC Components"
    obj_ports.Shape = ports
    if hasattr(obj_ports, "ViewObject") and obj_ports.ViewObject:
        obj_ports.ViewObject.ShapeColor = COLOR_METAL
    part.addObject(obj_ports)

    # 3. 40-Pin GPIO Header via App::Link to `header_pin_2x20.FCStd`
    doc_hdr = App.openDocument(f"{cots_models_dir}/header_pin_2x20.FCStd")
    lnk_gpio = doc.addObject("App::Link", "Header_GPIO_40Pin")
    lnk_gpio.Label = "40-Pin GPIO Header (2x20, 2.54 mm, COTS)"
    lnk_gpio.setLink(doc_hdr.Header)
    lnk_gpio.Placement = App.Placement(App.Vector(-10.00, 24.50, 1.40), App.Rotation())
    part.addObject(lnk_gpio)

    doc.recompute()
    doc.save()
    App.closeDocument(doc_hdr.Name)
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
    fcstd_path = f"{cots_models_dir}/pca9685_board.FCStd"
    doc.saveAs(fcstd_path)

    # 1. PCB Substrate (62.5 x 25.4 x 1.6 mm, blue)
    pcb = make_rounded_rect_solid(-31.25, 31.25, -12.7, 12.7, 2.0, 0.0, 1.6)
    for hx in [-28.0, 28.0]:
        for hy in [-9.5, 9.5]:
            hole = Part.makeCylinder(1.25, 5.0, App.Vector(hx, hy, -1.0), App.Vector(0, 0, 1))
            pcb = pcb.cut(hole)
    pcb = pcb.removeSplitter()

    # 2. Onboard Components: IC, Power Cap, Terminal Block
    ic = Part.makeBox(9.7, 4.4, 1.1, App.Vector(-4.85, -2.2, 1.6))
    cap = Part.makeCylinder(4.0, 12.5, App.Vector(-21.0, -7.5, 1.6), App.Vector(0, 0, 1))
    term_body = Part.makeBox(10.0, 8.0, 10.0, App.Vector(-14.0, -12.5, 1.6))
    term_cav1 = Part.makeBox(3.0, 4.0, 4.0, App.Vector(-13.0, -13.0, 3.5))
    term_cav2 = Part.makeBox(3.0, 4.0, 4.0, App.Vector(-8.0, -13.0, 3.5))
    term = term_body.cut(term_cav1).cut(term_cav2)
    comps = ic.fuse(cap).fuse(term).removeSplitter()

    part = doc.addObject("App::Part", "PCA9685_Board")
    part.Label = "PCA9685 16-Channel PWM Servo Controller (COTS)"

    obj_pcb = doc.addObject("Part::Feature", "PCA9685_PCB")
    obj_pcb.Label = "PCA9685 PCB Substrate (Blue)"
    obj_pcb.Shape = pcb
    if hasattr(obj_pcb, "ViewObject") and obj_pcb.ViewObject:
        obj_pcb.ViewObject.ShapeColor = COLOR_PCB_BLUE
    part.addObject(obj_pcb)

    obj_comps = doc.addObject("Part::Feature", "PCA9685_Components")
    obj_comps.Label = "IC, Capacitor & Screw Terminal Block"
    obj_comps.Shape = comps
    if hasattr(obj_comps, "ViewObject") and obj_comps.ViewObject:
        obj_comps.ViewObject.ShapeColor = COLOR_IC_BLACK
    part.addObject(obj_comps)

    # 3. 16x 3-Pin Right-Angle Servo Header via App::Link to `header_pin_3x16_ra.FCStd`
    doc_ra = App.openDocument(f"{cots_models_dir}/header_pin_3x16_ra.FCStd")
    lnk_servos = doc.addObject("App::Link", "Header_Servos_3x16")
    lnk_servos.Label = "16x 3-Pin Servo Headers (90° Right Angle, COTS)"
    lnk_servos.setLink(doc_ra.Header)
    lnk_servos.Placement = App.Placement(App.Vector(0.00, 7.50 + 2.25, 1.60), App.Rotation())
    part.addObject(lnk_servos)

    # 4. Dual 6-Pin I2C Headers via App::Link to `header_pin_1x6.FCStd` (rotated 90° along Y)
    doc_i2c = App.openDocument(f"{cots_models_dir}/header_pin_1x6.FCStd")
    rot_90 = App.Rotation(App.Vector(0, 0, 1), 90.0)

    lnk_i2c_in = doc.addObject("App::Link", "Header_I2C_In")
    lnk_i2c_in.Label = "6-Pin I2C Input Header (2.54 mm, COTS)"
    lnk_i2c_in.setLink(doc_i2c.Header)
    lnk_i2c_in.Placement = App.Placement(App.Vector(-28.00, 0.00, 1.60), rot_90)
    part.addObject(lnk_i2c_in)

    lnk_i2c_out = doc.addObject("App::Link", "Header_I2C_Out")
    lnk_i2c_out.Label = "6-Pin I2C Cascade Header (2.54 mm, COTS)"
    lnk_i2c_out.setLink(doc_i2c.Header)
    lnk_i2c_out.Placement = App.Placement(App.Vector(28.00, 0.00, 1.60), rot_90)
    part.addObject(lnk_i2c_out)

    doc.recompute()
    doc.save()
    App.closeDocument(doc_ra.Name)
    App.closeDocument(doc_i2c.Name)
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
    fcstd_path = f"{cots_models_dir}/tca9548a_board.FCStd"
    doc.saveAs(fcstd_path)

    # 1. PCB Substrate (31.5 x 21.0 x 1.6 mm, purple)
    pcb = make_rounded_rect_solid(-15.75, 15.75, -10.5, 10.5, 1.5, 0.0, 1.6)
    for hx in [-13.0, 13.0]:
        hole = Part.makeCylinder(1.25, 5.0, App.Vector(hx, 0.0, -1.0), App.Vector(0, 0, 1))
        pcb = pcb.cut(hole)
    pcb = pcb.removeSplitter()

    ic = Part.makeBox(7.8, 4.4, 1.1, App.Vector(-3.9, -2.2, 1.6)).removeSplitter()

    part = doc.addObject("App::Part", "TCA9548A_Board")
    part.Label = "TCA9548A 8-Channel I2C Multiplexer (COTS)"

    obj_pcb = doc.addObject("Part::Feature", "TCA9548A_PCB")
    obj_pcb.Label = "TCA9548A PCB Substrate (Purple)"
    obj_pcb.Shape = pcb
    if hasattr(obj_pcb, "ViewObject") and obj_pcb.ViewObject:
        obj_pcb.ViewObject.ShapeColor = COLOR_PCB_PURPLE
    part.addObject(obj_pcb)

    obj_ic = doc.addObject("Part::Feature", "TCA9548A_IC")
    obj_ic.Label = "TCA9548A TSSOP-24 Multiplexer IC"
    obj_ic.Shape = ic
    if hasattr(obj_ic, "ViewObject") and obj_ic.ViewObject:
        obj_ic.ViewObject.ShapeColor = COLOR_IC_BLACK
    part.addObject(obj_ic)

    # 2. Dual 12-Pin Headers via App::Link to `header_pin_1x12.FCStd`
    # Pins point downwards through the PCB into the Hub socket
    # Male header sitting with collar below PCB (Z = -2.50 mm) and pins extending down to Z = -8.50 mm
    doc_hdr = App.openDocument(f"{cots_models_dir}/header_pin_1x12.FCStd")

    # Inverted orientation: header seated under PCB with pins extending downwards into socket
    rot_flip = App.Rotation(App.Vector(1, 0, 0), 180.0)

    lnk_top = doc.addObject("App::Link", "Header_Top_12Pin")
    lnk_top.Label = "12-Pin Header Top (2.54 mm, COTS)"
    lnk_top.setLink(doc_hdr.Header)
    lnk_top.Placement = App.Placement(App.Vector(0.00, 8.77, 0.00), rot_flip)
    part.addObject(lnk_top)

    lnk_bot = doc.addObject("App::Link", "Header_Bottom_12Pin")
    lnk_bot.Label = "12-Pin Header Bottom (2.54 mm, COTS)"
    lnk_bot.setLink(doc_hdr.Header)
    lnk_bot.Placement = App.Placement(App.Vector(0.00, -8.77, 0.00), rot_flip)
    part.addObject(lnk_bot)

    doc.recompute()
    doc.save()
    App.closeDocument(doc_hdr.Name)
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
    fcstd_path = f"{cots_models_dir}/vl53l5cx_board.FCStd"
    doc.saveAs(fcstd_path)

    # 1. PCB Substrate (24.0 x 18.0 x 1.6 mm, red)
    pcb = make_rounded_rect_solid(-12.0, 12.0, -9.0, 9.0, 1.5, 0.0, 1.6)
    for hx in [-10.5, 10.5]:
        for hy in [-6.5, 6.5]:
            hole = Part.makeCylinder(1.05, 5.0, App.Vector(hx, hy, -1.0), App.Vector(0, 0, 1))
            pcb = pcb.cut(hole)
    pcb = pcb.removeSplitter()

    # 2. Optical Sensor Package & Dual Lenses
    sensor = Part.makeBox(6.4, 3.0, 1.2, App.Vector(-3.2, -1.5, 1.6))
    lens1 = Part.makeCylinder(0.55, 0.4, App.Vector(-1.5, 0.0, 2.8), App.Vector(0, 0, 1))
    lens2 = Part.makeCylinder(0.55, 0.4, App.Vector(1.5, 0.0, 2.8), App.Vector(0, 0, 1))
    optics = sensor.fuse(lens1).fuse(lens2).removeSplitter()

    part = doc.addObject("App::Part", "VL53L5CX_Board")
    part.Label = "VL53L5CX 9-Zone ToF Terrain Distance Sensor (COTS)"

    obj_pcb = doc.addObject("Part::Feature", "VL53L5CX_PCB")
    obj_pcb.Label = "VL53L5CX PCB Substrate (Red)"
    obj_pcb.Shape = pcb
    if hasattr(obj_pcb, "ViewObject") and obj_pcb.ViewObject:
        obj_pcb.ViewObject.ShapeColor = COLOR_PCB_RED
    part.addObject(obj_pcb)

    obj_opt = doc.addObject("Part::Feature", "Optical_Package")
    obj_opt.Label = "VL53L5CX Optical Sensor & Lenses"
    obj_opt.Shape = optics
    if hasattr(obj_opt, "ViewObject") and obj_opt.ViewObject:
        obj_opt.ViewObject.ShapeColor = COLOR_IC_BLACK
    part.addObject(obj_opt)

    # 3. 6-Pin 90° Right-Angle Header via App::Link to `header_pin_1x6_ra.FCStd`
    doc_ra = App.openDocument(f"{cots_models_dir}/header_pin_1x6_ra.FCStd")
    # Seated on back side with horizontal pins extending in -Y direction into Belly Pan slot
    rot_flip = App.Rotation(App.Vector(1, 0, 0), 180.0)
    lnk_hdr = doc.addObject("App::Link", "Header_I2C_6Pin_RA")
    lnk_hdr.Label = "6-Pin I2C Header (90° Right-Angle, COTS)"
    lnk_hdr.setLink(doc_ra.Header)
    lnk_hdr.Placement = App.Placement(App.Vector(0.00, -8.50, 0.00), rot_flip)
    part.addObject(lnk_hdr)

    doc.recompute()
    doc.save()
    App.closeDocument(doc_ra.Name)
    App.closeDocument(doc_name)
    print(f"✔ Generated VL53L5CX ToF Sensor -> {fcstd_path}")


# =============================================================================
# 5. 2S 7.4V LiPo Battery Pack
# =============================================================================
def build_battery_lipo_2s():
    doc_name = "battery_lipo_2s"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)
    fcstd_path = f"{cots_models_dir}/battery_lipo_2s.FCStd"
    doc.saveAs(fcstd_path)

    pack = make_rounded_rect_solid(-44.0, 44.0, -17.5, 17.5, 3.5, 0.0, 14.0)
    collar = Part.makeBox(4.0, 12.0, 7.0, App.Vector(-48.0, -6.0, 3.5))
    cable_pos = Part.makeCylinder(1.75, 20.0, App.Vector(-48.0, 3.0, 7.0), App.Vector(-1, 0, 0))
    cable_neg = Part.makeCylinder(1.75, 20.0, App.Vector(-48.0, -3.0, 7.0), App.Vector(-1, 0, 0))
    xt60 = Part.makeBox(15.5, 16.0, 8.0, App.Vector(-83.5, -8.0, 3.0))
    jst_xh = Part.makeBox(5.5, 9.8, 6.0, App.Vector(-55.0, 8.0, 4.0))

    bat_solid = pack.fuse(collar).fuse(cable_pos).fuse(cable_neg).fuse(xt60).fuse(jst_xh).removeSplitter()

    obj = doc.addObject("Part::Feature", "Battery_LiPo_2S")
    obj.Label = "2S 7.4V LiPo Battery Pack (COTS)"
    obj.Shape = bat_solid
    if hasattr(obj, "ViewObject") and obj.ViewObject:
        obj.ViewObject.ShapeColor = (0.85, 0.65, 0.10)  # Gold/Yellow wrap

    doc.recompute()
    doc.save()
    App.closeDocument(doc_name)
    print(f"✔ Generated 2S LiPo Battery Pack -> {fcstd_path}")


# =============================================================================
# 6. ADS1115 16-Bit 4-Channel I2C ADC Breakout
# =============================================================================
def build_ads1115():
    doc_name = "ads1115_board"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)
    fcstd_path = f"{cots_models_dir}/ads1115_board.FCStd"
    doc.saveAs(fcstd_path)

    # 1. PCB Substrate (28.0 x 17.0 x 1.6 mm, blue)
    pcb = make_rounded_rect_solid(-14.0, 14.0, -8.5, 8.5, 2.0, 0.0, 1.6)
    for hx in [-10.1, 10.1]:
        hole = Part.makeCylinder(1.25, 5.0, App.Vector(hx, 5.3, -1.0), App.Vector(0, 0, 1))
        pcb = pcb.cut(hole)
    pcb = pcb.removeSplitter()

    ic = Part.makeBox(3.0, 3.0, 1.1, App.Vector(-1.5, -1.5, 1.6)).removeSplitter()

    part = doc.addObject("App::Part", "ADS1115_Board")
    part.Label = "ADS1115 16-Bit 4-Channel ADC (COTS)"

    obj_pcb = doc.addObject("Part::Feature", "ADS1115_PCB")
    obj_pcb.Label = "ADS1115 PCB Substrate (Blue)"
    obj_pcb.Shape = pcb
    if hasattr(obj_pcb, "ViewObject") and obj_pcb.ViewObject:
        obj_pcb.ViewObject.ShapeColor = COLOR_PCB_BLUE
    part.addObject(obj_pcb)

    obj_ic = doc.addObject("Part::Feature", "ADS1115_IC")
    obj_ic.Label = "ADS1115 MSOP-10 ADC IC"
    obj_ic.Shape = ic
    if hasattr(obj_ic, "ViewObject") and obj_ic.ViewObject:
        obj_ic.ViewObject.ShapeColor = COLOR_IC_BLACK
    part.addObject(obj_ic)

    # 2. 10-Pin Header via App::Link to `header_pin_1x10.FCStd`
    doc_hdr = App.openDocument(f"{cots_models_dir}/header_pin_1x10.FCStd")
    lnk_hdr = doc.addObject("App::Link", "Header_10Pin")
    lnk_hdr.Label = "10-Pin Header (2.54 mm, COTS)"
    lnk_hdr.setLink(doc_hdr.Header)
    lnk_hdr.Placement = App.Placement(App.Vector(0.00, -6.35, 1.60), App.Rotation())
    part.addObject(lnk_hdr)

    doc.recompute()
    doc.save()
    App.closeDocument(doc_hdr.Name)
    App.closeDocument(doc_name)
    print(f"✔ Generated ADS1115 16-Bit ADC Breakout -> {fcstd_path}")


# Execute all builds
build_rpi4()
build_pca9685()
build_tca9548a()
build_vl53l5cx()
build_battery_lipo_2s()
build_ads1115()

print("=== All Electronics & Power COTS Models Generated with References Successfully ===")
sys.exit(0)
