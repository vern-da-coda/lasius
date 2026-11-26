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
  7. Adafruit BNO085 9-DOF Orientation IMU Fusion Breakout (`bno085_board.FCStd`, PID 4754):
     - 25.6 x 22.7 x 1.6 mm matte-black PCB with 4x M2.5 mounting holes (20.32 x 17.78 mm pitch).
     - Hillcrest/CEVA BNO085 LGA-28 IC, 32.768 kHz SMD crystal, and dual opposing STEMMA QT JST-SH sockets.
     - 6-pin 90° right-angle header referenced via App::Link to `header_pin_1x6_ra.FCStd`.
  8. Neodymium Disc Magnet Ø5 x 2 mm (`magnet_5x2.FCStd`):
     - Ø5.00 x 2.00 mm brushed nickel-silver N52 disc magnet (0.20 mm top/bottom bevels) for tool-free
       self-centering Canopy attachment on the 4 pillars (±48, ±36 mm).
  9. ISO 7380 M2 x 5 mm Button-Head Socket Screw (`screw_m2_button_head.FCStd`):
     - Stainless A2 low-profile domed button head (Ø3.50 x 1.15 mm, 1.3 mm hex socket) + Ø1.92 x 5.00 mm
       shank extending along -Z for all 18 servo horns (72x total: 24x Coxa on Body_Top + 48x Hip/Knee on Femur).

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
COLOR_PCB_BLACK = (0.09, 0.10, 0.13)   # Adafruit Matte Black (BNO085 STEMMA QT)
COLOR_IC_BLACK  = (0.15, 0.15, 0.15)   # Epoxy IC packaging
COLOR_JST_WHITE = (0.90, 0.88, 0.82)   # JST-SH STEMMA QT connector housing
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
# 5. 2S 7.4V LiPo Battery Pack (Ovonic 2200mAh 35C: 72.0 x 33.0 x 18.0 mm)
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

    # Ovonic 2S 2200mAh: 72.0 x 33.0 x 18.0 mm Softcase
    pack = make_rounded_rect_solid(-36.0, 36.0, -16.5, 16.5, 3.5, 0.0, 18.0)
    collar = Part.makeBox(4.0, 12.0, 8.0, App.Vector(-40.0, -6.0, 5.0))
    # Flexible silicone leads folded compactly into central distribution bay (X in [-54.0, -36.0])
    cable_pos = Part.makeCylinder(1.75, 8.0, App.Vector(-40.0, -2.0, 9.0), App.Vector(-1, -0.4, 0))
    cable_neg = Part.makeCylinder(1.75, 8.0, App.Vector(-40.0, -6.0, 9.0), App.Vector(-1, -0.4, 0))
    xt60 = Part.makeBox(15.5, 16.0, 8.0, App.Vector(-55.5, -16.0, 5.0))
    jst_xh = Part.makeBox(5.5, 9.8, 6.0, App.Vector(-45.5, 5.0, 6.0))

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
# 5b. 3A-6S UBEC Step-Down Voltage Regulator (34.0 x 17.08 x 6.35 mm, Jumper 10 mm)
# =============================================================================
def build_ubec_3a():
    doc_name = "ubec_3a"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)
    fcstd_path = f"{cots_models_dir}/ubec_3a.FCStd"
    doc.saveAs(fcstd_path)

    # 1. Main PCB Substrate: 34.0 x 17.08 x 1.60 mm
    pcb = make_rounded_rect_solid(-17.0, 17.0, -8.54, 8.54, 1.2, 0.0, 1.6)

    # 2. Onboard Power Inductor & Capacitors (height up to 6.35 mm)
    inductor = Part.makeCylinder(4.2, 4.75, App.Vector(-4.0, 0.0, 1.6), App.Vector(0, 0, 1))
    cap1 = Part.makeCylinder(2.8, 4.75, App.Vector(5.5, -3.5, 1.6), App.Vector(0, 0, 1))

    # 3. 3-Pin Jumper Header + Blue Shunt at +X end (height 10.0 mm)
    jumper_block = Part.makeBox(4.5, 7.5, 8.4, App.Vector(11.5, -3.75, 1.6))

    # 4. Input Leads (-X side, 1.2 mm silicone, length 12 mm)
    w_in1 = Part.makeCylinder(0.8, 12.0, App.Vector(-17.0, 3.0, 0.8), App.Vector(-1, 0, 0))
    w_in2 = Part.makeCylinder(0.8, 12.0, App.Vector(-17.0, -3.0, 0.8), App.Vector(-1, 0, 0))

    # 5. Output Leads (+X side, 1.0 mm silicone, length 6 mm inside power bay)
    w_out1 = Part.makeCylinder(0.7, 6.0, App.Vector(17.0, 5.0, 0.8), App.Vector(1, 0, 0))
    w_out2 = Part.makeCylinder(0.7, 6.0, App.Vector(17.0, -5.0, 0.8), App.Vector(1, 0, 0))

    ubec_solid = pcb.fuse(inductor).fuse(cap1).fuse(jumper_block).fuse(w_in1).fuse(w_in2).fuse(w_out1).fuse(w_out2).removeSplitter()

    obj = doc.addObject("Part::Feature", "UBEC_3A")
    obj.Label = "3A-6S UBEC 5V/6V Step-Down (COTS)"
    obj.Shape = ubec_solid
    if hasattr(obj, "ViewObject") and obj.ViewObject:
        obj.ViewObject.ShapeColor = (0.12, 0.58, 0.32)  # Green PCB

    doc.recompute()
    doc.save()
    App.closeDocument(doc_name)
    print(f"✔ Generated 3A UBEC -> {fcstd_path}")


# =============================================================================
# 5c. Amass XT60E-M Panel Mount Connector (27.0 x 16.0 x 12.0 mm, 20.5 mm M2.5 pitch)
# =============================================================================
def build_xt60e_m():
    doc_name = "xt60e_m"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)
    fcstd_path = f"{cots_models_dir}/xt60e_m.FCStd"
    doc.saveAs(fcstd_path)

    # 1. Main Flange: 27.0 mm wide (Y), 16.0 mm high (Z), 2.5 mm thick (X)
    flange = make_rounded_rect_solid(-1.25, 1.25, -13.5, 13.5, 2.5, -8.0, 8.0)
    for hy in [-10.25, 10.25]:
        hole = Part.makeCylinder(1.35, 10.0, App.Vector(0.0, hy, -5.0), App.Vector(1, 0, 0))
        flange = flange.cut(hole)

    # 2. Main Body entering panel: 16.0 mm wide (Y), 8.5 mm high (Z), 9.5 mm deep (+X)
    body = make_rounded_rect_solid(1.25, 10.75, -8.0, 8.0, 2.0, -4.25, 4.25)

    # 3. Outer shroud on -X side (depth 5.5 mm)
    shroud = make_rounded_rect_solid(-6.75, -1.25, -7.75, 7.75, 2.0, -4.0, 4.0)
    cavity = make_rounded_rect_solid(-7.00, -1.00, -6.50, 6.50, 1.5, -3.25, 3.25)
    shroud = shroud.cut(cavity)

    # 4. Gold male contact pins inside cavity (diameter 3.5 mm)
    pin1 = Part.makeCylinder(1.75, 4.5, App.Vector(-6.0, 3.6, 0.0), App.Vector(1, 0, 0))
    pin2 = Part.makeCylinder(1.75, 4.5, App.Vector(-6.0, -3.6, 0.0), App.Vector(1, 0, 0))

    # 5. Rear solder pigtail leads (+X side, 12AWG silicone, length 20 mm)
    w_pos = Part.makeCylinder(1.75, 20.0, App.Vector(10.75, 3.6, 0.0), App.Vector(1, 0, 0))
    w_neg = Part.makeCylinder(1.75, 20.0, App.Vector(10.75, -3.6, 0.0), App.Vector(1, 0, 0))

    xt60_solid = flange.fuse(body).fuse(shroud).fuse(pin1).fuse(pin2).fuse(w_pos).fuse(w_neg).removeSplitter()

    obj = doc.addObject("Part::Feature", "Inlet_XT60E_M")
    obj.Label = "Amass XT60E-M Panel Mount Connector (COTS)"
    obj.Shape = xt60_solid
    if hasattr(obj, "ViewObject") and obj.ViewObject:
        obj.ViewObject.ShapeColor = (0.95, 0.80, 0.15)  # Amass Yellow

    doc.recompute()
    doc.save()
    App.closeDocument(doc_name)
    print(f"✔ Generated Amass XT60E-M Connector -> {fcstd_path}")


# =============================================================================
# 5d. Hobbywing BEC 10A V2-Car UBEC (HW30603003: 45.0 x 20.0 x 16.2 mm, IP67)
# =============================================================================
def build_ubec_hobbywing_10a():
    doc_name = "ubec_hobbywing_10a"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)
    fcstd_path = f"{cots_models_dir}/ubec_hobbywing_10a.FCStd"
    doc.saveAs(fcstd_path)

    # 1. CNC Anodized Aluminum Heatsink Casing: 45.0 x 20.0 x 16.2 mm (centered X/Y, Z in [0, 16.2])
    casing = make_rounded_rect_solid(-22.5, 22.5, -10.0, 10.0, 1.8, 0.0, 16.2)

    # 2. Input Silicone Leads (-X side, 16AWG, 7.0 mm straight exit) & 2-pin SW socket boss
    w_in_p = Part.makeCylinder(1.05, 7.0, App.Vector(-22.5, 3.5, 7.0), App.Vector(-1, 0, 0))
    w_in_n = Part.makeCylinder(1.05, 7.0, App.Vector(-22.5, -3.5, 7.0), App.Vector(-1, 0, 0))
    sw_plug = Part.makeBox(4.5, 5.5, 4.0, App.Vector(-27.0, -2.75, 10.5))

    # 3. Output Silicone Leads (+X side, 18AWG, 5.0 mm exit) + Green Toroidal Ferrite Ring (OD 11.0, ID 6.0, H 4.5 mm)
    w_out_p = Part.makeCylinder(0.90, 5.5, App.Vector(22.5, 2.5, 8.1), App.Vector(1, 0, 0))
    w_out_n = Part.makeCylinder(0.90, 5.5, App.Vector(22.5, -2.5, 8.1), App.Vector(1, 0, 0))
    ferrite_out = Part.makeCylinder(5.5, 4.8, App.Vector(29.0, 0.0, 5.7), App.Vector(0, 0, 1))
    ferrite_in = Part.makeCylinder(2.8, 6.0, App.Vector(29.0, 0.0, 5.1), App.Vector(0, 0, 1))
    ferrite = ferrite_out.cut(ferrite_in)

    ubec_solid = (
        casing.fuse(w_in_p).fuse(w_in_n).fuse(sw_plug)
        .fuse(w_out_p).fuse(w_out_n).fuse(ferrite)
        .removeSplitter()
    )

    obj = doc.addObject("Part::Feature", "UBEC_Hobbywing_10A")
    obj.Label = "Hobbywing BEC 10A V2-Car UBEC 6.0V (HW30603003, COTS)"
    obj.Shape = ubec_solid
    if hasattr(obj, "ViewObject") and obj.ViewObject:
        obj.ViewObject.ShapeColor = (0.10, 0.11, 0.14)  # Matte Black Anodized Aluminum

    doc.recompute()
    doc.save()
    App.closeDocument(doc_name)
    print(f"✔ Generated Hobbywing BEC 10A V2-Car UBEC -> {fcstd_path}")


# =============================================================================
# 5e. 25A Mini Automotive Blade Fuse (ATM: 10.9 x 3.8 x 16.3 mm) in Panel Socket
#     Panel convention: X = 0.00 outer wall surface, -X = exterior, +X = interior
# =============================================================================
def build_fuse_mini_atm():
    doc_name = "fuse_mini_atm"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)
    fcstd_path = f"{cots_models_dir}/fuse_mini_atm.FCStd"
    doc.saveAs(fcstd_path)

    # Outer bezel flange (15.0 x 8.0 mm, sits 0.02 mm outside wall)
    flange = make_rounded_rect_solid(-1.82, -0.02, -7.5, 7.5, 1.2, -4.0, 4.0)
    # 25A Mini-ATM blade fuse head protruding slightly outward for tool-free pull
    fuse_cap = make_rounded_rect_solid(-4.00, -1.82, -5.45, 5.45, 0.8, -1.9, 1.9)
    # Socket body entering panel (+X)
    body = make_rounded_rect_solid(-0.02, 13.50, -6.2, 6.2, 1.0, -3.2, 3.2)
    # Dual rear 4.8 mm quick-disconnect tabs
    tab1 = Part.makeBox(4.5, 4.8, 0.8, App.Vector(13.50, 0.8, -0.4))
    tab2 = Part.makeBox(4.5, 4.8, 0.8, App.Vector(13.50, -5.6, -0.4))

    fuse_solid = flange.fuse(fuse_cap).fuse(body).fuse(tab1).fuse(tab2).removeSplitter()

    obj = doc.addObject("Part::Feature", "Fuse_Mini_ATM")
    obj.Label = "25A Mini Automotive Blade Fuse ATM + Panel Socket (COTS)"
    obj.Shape = fuse_solid
    if hasattr(obj, "ViewObject") and obj.ViewObject:
        obj.ViewObject.ShapeColor = (0.90, 0.90, 0.92)  # 25A Clear/White ATM standard color

    doc.recompute()
    doc.save()
    App.closeDocument(doc_name)
    print(f"✔ Generated 25A Mini-ATM Fuse & Panel Socket -> {fcstd_path}")


# =============================================================================
# 5f. Panel-Mount Mini Slide Switch (19.0 x 6.5 mm flange, 15.0 mm M2 pitch)
#     Covers SPST (Pi Logic) & DPST (Dual Hobbywing SW) in identical footprint.
#     Panel convention: X = 0.00 outer wall surface, -X = exterior, +X = interior
# =============================================================================
def build_switch_mini_slide():
    doc_name = "switch_mini_slide"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)
    fcstd_path = f"{cots_models_dir}/switch_mini_slide.FCStd"
    doc.saveAs(fcstd_path)

    # Outer mounting flange with 2x M2 screw holes at Y = ±7.50 mm
    flange = make_rounded_rect_solid(-1.22, -0.02, -9.5, 9.5, 1.2, -3.25, 3.25)
    for hy in [-7.5, 7.5]:
        hole = Part.makeCylinder(1.10, 4.0, App.Vector(-2.0, hy, 0.0), App.Vector(1, 0, 0))
        flange = flange.cut(hole)

    # Slider actuator knob protruding outward (-X)
    knob = Part.makeBox(3.0, 4.0, 3.0, App.Vector(-4.22, -2.0, -1.5))

    # Switch housing entering panel (+X)
    body = Part.makeBox(7.52, 11.5, 5.8, App.Vector(-0.02, -5.75, -2.9))

    # Solder pins exiting rear (+X)
    pins = None
    for py in [-3.5, 0.0, 3.5]:
        for pz in [-1.2, 1.2]:
            p = Part.makeBox(3.5, 0.6, 0.6, App.Vector(7.50, py - 0.3, pz - 0.3))
            pins = p if pins is None else pins.fuse(p)

    sw_solid = flange.fuse(knob).fuse(body).fuse(pins).removeSplitter()

    obj = doc.addObject("Part::Feature", "Switch_Mini_Slide")
    obj.Label = "Mini Panel-Mount Slide Switch (SPST / DPST, COTS)"
    obj.Shape = sw_solid
    if hasattr(obj, "ViewObject") and obj.ViewObject:
        obj.ViewObject.ShapeColor = (0.18, 0.18, 0.20)  # Dark technical black

    doc.recompute()
    doc.save()
    App.closeDocument(doc_name)
    print(f"✔ Generated Panel-Mount Mini Slide Switch -> {fcstd_path}")


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


# =============================================================================
# 7. Adafruit BNO085 9-DOF Orientation IMU Fusion Breakout (PID 4754)
# =============================================================================
def build_bno085():
    doc_name = "bno085_board"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)
    fcstd_path = f"{cots_models_dir}/bno085_board.FCStd"
    doc.saveAs(fcstd_path)

    # 1. PCB Substrate (25.6 x 22.7 x 1.6 mm, matte black, R = 2.5 mm corners)
    #    4x M2.5 mounting holes at official Adafruit 0.8" x 0.7" (20.32 x 17.78 mm) pitch:
    #    X = ±10.16 mm, Y = ±8.89 mm (Ø2.50 mm bores).
    pcb = make_rounded_rect_solid(-12.80, 12.80, -11.35, 11.35, 2.50, 0.0, 1.60)
    for hx in [-10.16, 10.16]:
        for hy in [-8.89, 8.89]:
            hole = Part.makeCylinder(1.25, 5.0, App.Vector(hx, hy, -1.0), App.Vector(0, 0, 1))
            pcb = pcb.cut(hole)
    # Unpopulated secondary 6-pin header through-holes on -Y edge (2.54 mm pitch, Ø1.0 mm)
    for i in range(6):
        px = (-2.5 + i) * 2.54
        pad_hole = Part.makeCylinder(0.50, 5.0, App.Vector(px, -8.89, -1.0), App.Vector(0, 0, 1))
        pcb = pcb.cut(pad_hole)
    pcb = pcb.removeSplitter()

    # 2. Onboard Hillcrest/CEVA BNO085 28-Pin LGA IC (5.2 x 3.8 x 1.0 mm) + 32.768 kHz Crystal + LDO
    ic_bno = Part.makeBox(5.20, 3.80, 1.00, App.Vector(-2.60, -1.90, 1.60))
    xtal = Part.makeBox(3.20, 1.50, 0.80, App.Vector(-1.60, 3.00, 1.60))
    ldo = Part.makeBox(2.90, 1.60, 1.10, App.Vector(-6.20, -4.50, 1.60))
    ic_solid = ic_bno.fuse(xtal).fuse(ldo).removeSplitter()

    # 3. Dual Opposing 4-Pin JST-SH 1.0 mm STEMMA QT / Qwiic Sockets on ±X edges
    #    Each housing: 4.30 mm deep (X) x 6.00 mm wide (Y) x 2.95 mm high (Z = 1.60..4.55 mm -> 4.55 mm total)
    jst_l = Part.makeBox(4.30, 6.00, 2.95, App.Vector(-12.80, -3.00, 1.60))
    jst_l_cav = Part.makeBox(3.20, 4.60, 1.90, App.Vector(-13.00, -2.30, 2.15))
    jst_l = jst_l.cut(jst_l_cav)

    jst_r = Part.makeBox(4.30, 6.00, 2.95, App.Vector(8.50, -3.00, 1.60))
    jst_r_cav = Part.makeBox(3.20, 4.60, 1.90, App.Vector(9.80, -2.30, 2.15))
    jst_r = jst_r.cut(jst_r_cav)
    jst_solid = jst_l.fuse(jst_r).removeSplitter()

    part = doc.addObject("App::Part", "BNO085_Board")
    part.Label = "Adafruit BNO085 9-DOF Orientation IMU (PID 4754, COTS)"

    obj_pcb = doc.addObject("Part::Feature", "BNO085_PCB")
    obj_pcb.Label = "BNO085 PCB Substrate (Matte Black)"
    obj_pcb.Shape = pcb
    if hasattr(obj_pcb, "ViewObject") and obj_pcb.ViewObject:
        obj_pcb.ViewObject.ShapeColor = COLOR_PCB_BLACK
    part.addObject(obj_pcb)

    obj_ic = doc.addObject("Part::Feature", "BNO085_IC")
    obj_ic.Label = "BNO085 28-Pin LGA IMU & Crystal"
    obj_ic.Shape = ic_solid
    if hasattr(obj_ic, "ViewObject") and obj_ic.ViewObject:
        obj_ic.ViewObject.ShapeColor = COLOR_IC_BLACK
    part.addObject(obj_ic)

    obj_jst = doc.addObject("Part::Feature", "STEMMA_QT_Sockets")
    obj_jst.Label = "Dual 4-Pin JST-SH STEMMA QT Connectors"
    obj_jst.Shape = jst_solid
    if hasattr(obj_jst, "ViewObject") and obj_jst.ViewObject:
        obj_jst.ViewObject.ShapeColor = COLOR_JST_WHITE
    part.addObject(obj_jst)

    # 4. 6-Pin 90° Right-Angle Header on Primary Signal Row (Y = +8.89 mm, pins extending +Y)
    #    via App::Link to `header_pin_1x6_ra.FCStd` (Z = 1.60 mm -> pins at Z = 2.85 mm, solder tails down to Z = -1.40 mm)
    doc_ra = App.openDocument(f"{cots_models_dir}/header_pin_1x6_ra.FCStd")
    lnk_hdr = doc.addObject("App::Link", "Header_6Pin_RA")
    lnk_hdr.Label = "6-Pin Primary Signal Header (90° Right-Angle, COTS)"
    lnk_hdr.setLink(doc_ra.Header)
    lnk_hdr.Placement = App.Placement(App.Vector(0.00, 8.89, 1.60), App.Rotation())
    part.addObject(lnk_hdr)

    doc.recompute()
    doc.save()
    App.closeDocument(doc_ra.Name)
    App.closeDocument(doc_name)
    print(f"✔ Generated Adafruit BNO085 9-DOF IMU Breakout -> {fcstd_path}")


# =============================================================================
# 8. Neodymium Disc Magnet Ø5.0 x 2.0 mm (Canopy Magnetic Lock, COTS)
# =============================================================================
def build_magnet_5x2():
    doc_name = "magnet_5x2"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)
    fcstd_path = f"{cots_models_dir}/magnet_5x2.FCStd"

    # Ø5.00 x 2.00 mm cylinder centered in XY, Z in [0.00, 2.00 mm], with 0.15 mm edge chamfers
    c_bot = Part.makeCone(2.35, 2.50, 0.15, App.Vector(0.0, 0.0, 0.00), App.Vector(0, 0, 1))
    c_mid = Part.makeCylinder(2.50, 1.70, App.Vector(0.0, 0.0, 0.15), App.Vector(0, 0, 1))
    c_top = Part.makeCone(2.50, 2.35, 0.15, App.Vector(0.0, 0.0, 1.85), App.Vector(0, 0, 1))
    mag_solid = c_bot.fuse(c_mid).fuse(c_top).removeSplitter()

    obj = doc.addObject("Part::Feature", "Magnet_5x2")
    obj.Label = "Neodymium Disc Magnet Ø5 x 2 mm (COTS)"
    obj.Shape = mag_solid
    if hasattr(obj, "ViewObject") and obj.ViewObject:
        obj.ViewObject.ShapeColor = (0.78, 0.80, 0.84)  # Brushed nickel plating

    doc.recompute()
    doc.saveAs(fcstd_path)
    App.closeDocument(doc_name)
    print(f"✔ Generated Neodymium Disc Magnet Ø5x2 mm -> {fcstd_path}")


# =============================================================================
# 9. ISO 7380 M2 x 5 mm Button-Head Hex Socket Screw (Servo Horn Fastener, COTS)
#    Origin (0, 0, 0) at flat bearing underside of head:
#    - Domed button head extends +Z: Z in [0.00, +1.15 mm], Ø3.50 mm (clears Canopy @ (0,±83) & flush in Femur cbore!)
#    - Threaded shank extends -Z: Z in [-5.00, 0.00 mm], Ø1.92 mm (0.04 mm radial CAD clearance in Ø2.00 bores)
# =============================================================================
def build_screw_m2_button_head():
    doc_name = "screw_m2_button_head"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)
    fcstd_path = f"{cots_models_dir}/screw_m2_button_head.FCStd"

    # 1. Domed button head (Z in [0.00, 1.15 mm], outer Ø3.50 mm -> R = 1.75 mm)
    #    Revolved analytical profile: flat bearing face (0..1.75), 0.22 mm cylindrical rim, spherical dome to (0, 1.15)
    r_head = 1.75
    h_rim = 0.22
    h_head = 1.15
    # Circular arc through (r_head, h_rim) and (0, h_head) with horizontal tangent at apex (0, h_head)
    dz_dome = h_head - h_rim
    r_dome = (r_head ** 2 + dz_dome ** 2) / (2.0 * dz_dome)
    zc_dome = h_head - r_dome
    ang_end = math.asin(r_head / r_dome)
    p_mid_dome = App.Vector(r_dome * math.sin(0.5 * ang_end), 0.0, zc_dome + r_dome * math.cos(0.5 * ang_end))

    p0 = App.Vector(0.0, 0.0, 0.0)
    p1 = App.Vector(r_head, 0.0, 0.0)
    p2 = App.Vector(r_head, 0.0, h_rim)
    p3 = App.Vector(0.0, 0.0, h_head)
    prof_wire = Part.Wire([
        Part.makeLine(p0, p1),
        Part.makeLine(p1, p2),
        Part.Arc(p2, p_mid_dome, p3).toShape(),
        Part.makeLine(p3, p0),
    ])
    head = Part.Face(prof_wire).revolve(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 360.0)

    # 2. 1.3 mm Hex Socket Recess in head top (Z in [0.55, 1.40 mm])
    sw_hex = 1.30
    r_hex = sw_hex / math.sqrt(3.0)
    hex_pts = [
        App.Vector(r_hex * math.cos(math.radians(60.0 * i)), r_hex * math.sin(math.radians(60.0 * i)), 0.55)
        for i in range(6)
    ]
    hex_pts.append(hex_pts[0])
    hex_cut = Part.Face(Part.makePolygon(hex_pts)).extrude(App.Vector(0, 0, 1.0))
    head = head.cut(hex_cut)

    # 3. Shank (Ø1.92 mm, Z in [-5.00, 0.00 mm] with 0.18 mm tip chamfer)
    shank_main = Part.makeCylinder(0.96, 4.82, App.Vector(0.0, 0.0, -4.82), App.Vector(0, 0, 1))
    shank_tip = Part.makeCone(0.78, 0.96, 0.18, App.Vector(0.0, 0.0, -5.00), App.Vector(0, 0, 1))
    screw_solid = head.fuse(shank_main).fuse(shank_tip).removeSplitter()

    obj = doc.addObject("Part::Feature", "M2_Linsenkopfschraube")
    obj.Label = "ISO 7380 M2 x 5 mm Button-Head Screw (A2 Stainless, COTS)"
    obj.Shape = screw_solid
    if hasattr(obj, "ViewObject") and obj.ViewObject:
        obj.ViewObject.ShapeColor = (0.78, 0.80, 0.84)  # A2 Stainless steel

    doc.recompute()
    doc.saveAs(fcstd_path)
    App.closeDocument(doc_name)
    print(f"✔ Generated ISO 7380 M2 x 5 mm Button-Head Screw -> {fcstd_path}")


# =============================================================================
# 10. DIN 7991 M2 x 6 mm Countersunk Hex Socket Screw (Tibia & Femur Covers, COTS)
#     Origin (0, 0, 0) at flat top of countersunk head; shank extends along -Z to Z = -6.00 mm.
#     - Head Ø3.90 mm (R = 1.95 mm), 90° countersunk cone, SW 1.30 mm hex socket (depth 0.95 mm)
#     - Shank Ø1.92 mm (R = 0.96 mm -> 0.04 mm clearance in Ø2.00 mm Ruthex M2 insert)
# =============================================================================
def build_screw_m2_countersunk():
    doc_name = "screw_m2_countersunk"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)
    fcstd_path = f"{cots_models_dir}/screw_m2_countersunk.FCStd"

    # 1. Countersunk head: 0.05 mm top micro-rim + 90° cone from R=1.95 down to R=0.96 (dz = 0.99 mm)
    rim = Part.makeCylinder(1.95, 0.05, App.Vector(0.0, 0.0, -0.05), App.Vector(0, 0, 1))
    cone = Part.makeCone(0.96, 1.95, 0.99, App.Vector(0.0, 0.0, -1.04), App.Vector(0, 0, 1))
    shank = Part.makeCylinder(0.96, 4.78, App.Vector(0.0, 0.0, -5.82), App.Vector(0, 0, 1))
    tip = Part.makeCone(0.78, 0.96, 0.18, App.Vector(0.0, 0.0, -6.00), App.Vector(0, 0, 1))
    screw_solid = rim.fuse(cone).fuse(shank).fuse(tip)

    # 2. SW 1.30 mm Hex Socket Recess (Z in [-0.95, +0.10]) + 0.14 mm top entry chamfer
    sw_hex = 1.30
    r_hex = sw_hex / math.sqrt(3.0)
    hex_pts = [
        App.Vector(r_hex * math.cos(math.radians(60.0 * i)), r_hex * math.sin(math.radians(60.0 * i)), -0.95)
        for i in range(6)
    ]
    hex_pts.append(hex_pts[0])
    hex_cut = Part.Face(Part.makePolygon(hex_pts)).extrude(App.Vector(0, 0, 1.10))
    hex_lead = Part.makeCone(r_hex, r_hex + 0.14, 0.14, App.Vector(0.0, 0.0, -0.14), App.Vector(0, 0, 1))
    screw_solid = screw_solid.cut(hex_cut).cut(hex_lead).removeSplitter()

    obj = doc.addObject("Part::Feature", "M2_Senkkopfschraube")
    obj.Label = "DIN 7991 M2 x 6 mm Countersunk Screw (A2 Stainless, COTS)"
    obj.Shape = screw_solid
    if hasattr(obj, "ViewObject") and obj.ViewObject:
        obj.ViewObject.ShapeColor = (0.78, 0.80, 0.84)

    doc.recompute()
    doc.saveAs(fcstd_path)
    App.closeDocument(doc_name)
    print(f"✔ Generated DIN 7991 M2 x 6 mm Countersunk Screw -> {fcstd_path}")


# =============================================================================
# 11. Ruthex M2 x 4.0 mm Heat-Set Brass Threaded Insert (Tibia & Femur Covers, COTS)
#     Origin (0, 0, 0) at top face; insert body extends along -Z to Z = -4.00 mm.
#     - CAD installed OD = Ø3.16 mm (R = 1.58 mm -> 0.02 mm radial clearance in Ø3.20 mm bore)
#     - Dual knurl bands + center waist groove + lower pilot shoulder + Ø2.00 mm through bore
# =============================================================================
def build_insert_m2_ruthex():
    doc_name = "insert_m2_ruthex"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)
    fcstd_path = f"{cots_models_dir}/insert_m2_ruthex.FCStd"

    prof_rz = [
        (1.12,  0.00),
        (1.45,  0.00),
        (1.58, -0.15),
        (1.58, -1.45),
        (1.40, -1.55),
        (1.40, -1.95),
        (1.58, -2.05),
        (1.58, -3.20),
        (1.44, -3.25),
        (1.44, -3.85),
        (1.30, -4.00),
        (1.00, -4.00),
        (1.00, -0.12),
    ]
    pts = [App.Vector(r, 0.0, z) for r, z in prof_rz]
    pts.append(pts[0])
    ins_solid = Part.Face(Part.makePolygon(pts)).revolve(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 360.0).removeSplitter()

    obj = doc.addObject("Part::Feature", "Ruthex_M2_Insert")
    obj.Label = "Ruthex M2 x 4.0 mm Heat-Set Threaded Insert (Brass, COTS)"
    obj.Shape = ins_solid
    if hasattr(obj, "ViewObject") and obj.ViewObject:
        obj.ViewObject.ShapeColor = (0.85, 0.70, 0.20)  # Brass

    doc.recompute()
    doc.saveAs(fcstd_path)
    App.closeDocument(doc_name)
    print(f"✔ Generated Ruthex M2 x 4.0 mm Brass Insert -> {fcstd_path}")


# =============================================================================
# 12. DIN 7991 M4 x 20 mm Countersunk Hex Socket Screw (Desk Stand Flanges, COTS)
#     Origin (0, 0, 0) at flat head top; extends along -Z to Z = -20.00 mm.
#     - Head Ø7.90 mm (R = 3.95 mm), 90° cone, SW 2.50 mm hex socket
#     - Shank Ø3.20 mm minor CAD clearance (0.0000 mm^3 collision inside M4 nuts & Ø4.2 bores)
# =============================================================================
def build_screw_m4x20_countersunk():
    doc_name = "screw_m4x20_countersunk"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)
    fcstd_path = f"{cots_models_dir}/screw_m4x20_countersunk.FCStd"

    rim = Part.makeCylinder(3.95, 0.15, App.Vector(0.0, 0.0, -0.15), App.Vector(0, 0, 1))
    cone = Part.makeCone(1.60, 3.95, 2.35, App.Vector(0.0, 0.0, -2.50), App.Vector(0, 0, 1))
    shank = Part.makeCylinder(1.60, 17.15, App.Vector(0.0, 0.0, -19.65), App.Vector(0, 0, 1))
    tip = Part.makeCone(1.25, 1.60, 0.35, App.Vector(0.0, 0.0, -20.00), App.Vector(0, 0, 1))
    solid = rim.fuse(cone).fuse(shank).fuse(tip)

    sw_hex = 2.50
    r_hex = sw_hex / math.sqrt(3.0)
    hex_pts = [
        App.Vector(r_hex * math.cos(math.radians(60.0 * i)), r_hex * math.sin(math.radians(60.0 * i)), -1.80)
        for i in range(6)
    ]
    hex_pts.append(hex_pts[0])
    hex_cut = Part.Face(Part.makePolygon(hex_pts)).extrude(App.Vector(0, 0, 1.95))
    solid = solid.cut(hex_cut).removeSplitter()

    obj = doc.addObject("Part::Feature", "M4x20_Senkkopfschraube")
    obj.Label = "DIN 7991 M4 x 20 mm Countersunk Screw (A2 Stainless, COTS)"
    obj.Shape = solid
    if hasattr(obj, "ViewObject") and obj.ViewObject:
        obj.ViewObject.ShapeColor = (0.78, 0.80, 0.84)

    doc.recompute()
    doc.saveAs(fcstd_path)
    App.closeDocument(doc_name)
    print(f"✔ Generated DIN 7991 M4 x 20 mm Countersunk Screw -> {fcstd_path}")


# =============================================================================
# 13. DIN 933 M8 x 40 mm Hex Bolt & DIN 934 M8 Hex Nut (Desk Clamp Spindle, COTS)
#     - Bolt origin (0, 0, 0) at under-head bearing face:
#       * Hex head SW 13.0 mm extends -Z: Z in [-5.30, 0.00]
#       * Threaded shank Ø7.84 mm extends +Z: Z in [0.00, +40.00]
#     - Nut origin (0, 0, 0) at bottom face:
#       * Hex body SW 13.0 mm extends +Z: Z in [0.00, +6.50], Ø8.00 mm bore
# =============================================================================
def build_bolt_m8x40_hex():
    doc_name = "bolt_m8x40_hex"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)
    fcstd_path = f"{cots_models_dir}/bolt_m8x40_hex.FCStd"

    r_hex = 13.0 / math.sqrt(3.0)
    pts = [
        App.Vector(r_hex * math.cos(math.radians(60.0 * i)), r_hex * math.sin(math.radians(60.0 * i)), -5.30)
        for i in range(6)
    ]
    pts.append(pts[0])
    head = Part.Face(Part.makePolygon(pts)).extrude(App.Vector(0, 0, 5.30))
    shank = Part.makeCylinder(3.92, 39.20, App.Vector(0.0, 0.0, 0.0), App.Vector(0, 0, 1))
    tip = Part.makeCone(3.92, 3.20, 0.80, App.Vector(0.0, 0.0, 39.20), App.Vector(0, 0, 1))
    solid = head.fuse(shank).fuse(tip).removeSplitter()

    obj = doc.addObject("Part::Feature", "M8x40_Sechskantschraube")
    obj.Label = "DIN 933 M8 x 40 mm Hex Bolt (A2 Stainless, COTS)"
    obj.Shape = solid
    if hasattr(obj, "ViewObject") and obj.ViewObject:
        obj.ViewObject.ShapeColor = (0.76, 0.78, 0.82)

    doc.recompute()
    doc.saveAs(fcstd_path)
    App.closeDocument(doc_name)
    print(f"✔ Generated DIN 933 M8 x 40 mm Hex Bolt -> {fcstd_path}")


def build_nut_m8_hex():
    doc_name = "nut_m8_hex"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)
    fcstd_path = f"{cots_models_dir}/nut_m8_hex.FCStd"

    r_hex = 13.0 / math.sqrt(3.0)
    pts = [
        App.Vector(r_hex * math.cos(math.radians(60.0 * i)), r_hex * math.sin(math.radians(60.0 * i)), 0.0)
        for i in range(6)
    ]
    pts.append(pts[0])
    nut = Part.Face(Part.makePolygon(pts)).extrude(App.Vector(0, 0, 6.50))
    bore = Part.makeCylinder(4.00, 8.0, App.Vector(0.0, 0.0, -0.5), App.Vector(0, 0, 1))
    solid = nut.cut(bore).removeSplitter()

    obj = doc.addObject("Part::Feature", "M8_Mutter_DIN934")
    obj.Label = "DIN 934 M8 Hex Nut (A2 Stainless, COTS)"
    obj.Shape = solid
    if hasattr(obj, "ViewObject") and obj.ViewObject:
        obj.ViewObject.ShapeColor = (0.76, 0.78, 0.82)

    doc.recompute()
    doc.saveAs(fcstd_path)
    App.closeDocument(doc_name)
    print(f"✔ Generated DIN 934 M8 Hex Nut -> {fcstd_path}")


# =============================================================================
# 14. M3 x 50 mm Round Aluminum/Brass Female-Female Standoff Sleeve (Chassis Core Tie-Rods, COTS)
#     Origin (0, 0, 0) at bottom face; extends +Z to Z = 50.00 mm.
#     - Outer Ø4.96 mm CAD (R = 2.48 mm, nominal Ø5.0 mm sleeve inside Ø5.25 mm PETG bore)
#     - Inner Ø2.50 mm M3 tap bore (R = 1.25 mm), 0.30 mm 45° end chamfers
#     - Placed 4x at (±45.0, ±30.0, Z = 2.65 mm) spanning the 51.30 mm Core gap between
#       Body_Bottom (Z = 2.00) and Body_Top (Z = 53.30) with 0.65 mm compression preload margin!
# =============================================================================
def build_standoff_m3x50_round():
    doc_name = "standoff_m3x50_round"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)
    fcstd_path = f"{cots_models_dir}/standoff_m3x50_round.FCStd"

    r_out = 2.48
    r_in = 1.25
    ch = 0.30
    length = 50.00
    prof_rz = [
        (r_in + 0.15, 0.00),
        (r_out - ch,  0.00),
        (r_out,       ch),
        (r_out,       length - ch),
        (r_out - ch,  length),
        (r_in + 0.15, length),
        (r_in,        length - 0.15),
        (r_in,        0.15),
    ]
    pts = [App.Vector(r, 0.0, z) for r, z in prof_rz]
    pts.append(pts[0])
    solid = (
        Part.Face(Part.makePolygon(pts))
        .revolve(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 360.0)
        .removeSplitter()
    )

    obj = doc.addObject("Part::Feature", "Standoff_M3x50_Round")
    obj.Label = "M3 x 50 mm Round Threaded Standoff Sleeve Ø5 mm (Aluminum/Brass, COTS)"
    obj.Shape = solid
    if hasattr(obj, "ViewObject") and obj.ViewObject:
        obj.ViewObject.ShapeColor = (0.76, 0.78, 0.82)  # Anodized Aluminum / Stainless

    doc.recompute()
    doc.saveAs(fcstd_path)
    App.closeDocument(doc_name)
    print(f"✔ Generated M3 x 50 mm Round Threaded Standoff Sleeve -> {fcstd_path}")


# =============================================================================
# 15. 0.96" I2C OLED Display 128x64 SSD1306 (Dual-Zone Yellow/Blue, Rear Telemetry HUD, COTS)
#     Local Frame: Origin at PCB center bottom (Z = 0.00 mm); +Z = display face normal;
#     +X = top of display (4-pin rear header edge, 27.3 mm tall), Y = width (27.0 mm wide).
#     4x Ø2.2 mm M2 mounting holes on standard 23.0 x 23.0 mm pitch (±11.50, ±11.50 mm).
# =============================================================================
def build_oled_096_i2c():
    doc_name = "oled_096_i2c"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)
    fcstd_path = f"{cots_models_dir}/oled_096_i2c.FCStd"
    doc.saveAs(fcstd_path)

    # 1. PCB Substrate (27.30 x 27.00 x 1.20 mm, R = 1.8 mm corners, 4x M2 holes at ±11.5 mm)
    pcb = make_rounded_rect_solid(-13.65, 13.65, -13.50, 13.50, 1.80, 0.00, 1.20)
    for hx in (-11.50, 11.50):
        for hy in (-11.50, 11.50):
            pcb = pcb.cut(Part.makeCylinder(1.10, 4.0, App.Vector(hx, hy, -1.0), App.Vector(0, 0, 1)))
    pcb = pcb.removeSplitter()

    # 2. Black OLED Glass Panel (19.20 mm tall along X [-10.80..+8.40], 26.70 mm wide along Y, Z = 1.20..2.70 mm)
    glass = make_rounded_rect_solid(-10.80, 8.40, -13.35, 13.35, 0.60, 1.20, 2.70).removeSplitter()

    # 3. Dual-Zone Active Display Emissive Bands (Yellow top y=0..15 + Ice-Blue main y=16..63)
    band_yellow = Part.makeBox(2.80, 21.80, 0.06, App.Vector(4.40, -10.90, 2.70))
    band_blue = Part.makeBox(10.20, 21.80, 0.06, App.Vector(-6.60, -10.90, 2.70))

    # 4. Rear-Side 4-Pin Low-Profile Right-Angle Header Block (Z in [-2.60, 0.00], X in [+9.6, +12.4])
    hdr_blk = Part.makeBox(2.60, 10.20, 2.50, App.Vector(9.80, -5.10, -2.50))
    pins = None
    for i in range(4):
        py = (-1.5 + i) * 2.54
        p = Part.makeBox(3.80, 0.64, 0.64, App.Vector(12.20, py - 0.32, -1.57))
        pins = p if pins is None else pins.fuse(p)
    hdr_pins = pins.removeSplitter()

    part = doc.addObject("App::Part", "OLED_096_I2C")
    part.Label = "0.96\" I2C OLED Display 128x64 SSD1306 Dual-Zone (COTS)"

    def add_feat(name, label, shape, color):
        f = doc.addObject("Part::Feature", name)
        f.Label = label
        f.Shape = shape
        if hasattr(f, "ViewObject") and f.ViewObject:
            f.ViewObject.ShapeColor = color
        part.addObject(f)
        return f

    add_feat("OLED_PCB", "0.96\" OLED PCB (27.3 x 27.0 mm, Blue)", pcb, COLOR_PCB_BLUE)
    add_feat("OLED_Glass", "OLED Glass Panel (19.2 x 26.7 mm)", glass, (0.05, 0.06, 0.08))
    add_feat("OLED_Zone_Yellow", "Active OLED Zone Yellow (y=0..15)", band_yellow, (0.96, 0.80, 0.10))
    add_feat("OLED_Zone_Blue", "Active OLED Zone Ice-Blue (y=16..63)", band_blue, (0.14, 0.72, 0.98))
    add_feat("OLED_Header_Body", "4-Pin Rear Header Shroud", hdr_blk, (0.12, 0.12, 0.12))
    add_feat("OLED_Header_Pins", "4-Pin I2C Pins (VCC/GND/SCL/SDA)", hdr_pins, (0.85, 0.70, 0.20))

    doc.recompute()
    doc.save()
    App.closeDocument(doc_name)
    print(f"✔ Generated 0.96\" I2C OLED Display -> {fcstd_path}")


# =============================================================================
# 16. 6x6 mm Tactile Pushbutton Switch (Pi Safe-Shutdown GPIO3, COTS)
#     Panel convention: X = 0.00 outer bezel surface, -X = exterior plunger, +X = interior body/pins
# =============================================================================
def build_button_tactile_6x6():
    doc_name = "button_tactile_6x6"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)
    fcstd_path = f"{cots_models_dir}/button_tactile_6x6.FCStd"
    doc.saveAs(fcstd_path)

    body = make_rounded_rect_solid(0.40, 4.20, -3.00, 3.00, 0.40, -3.00, 3.00)
    plunger = Part.makeCylinder(1.75, 2.80, App.Vector(-2.20, 0.0, 0.0), App.Vector(1, 0, 0))
    pins = None
    for py in (-2.25, 2.25):
        for pz in (-2.25, 2.25):
            p = Part.makeBox(3.00, 0.65, 0.40, App.Vector(4.20, py - 0.325, pz - 0.20))
            pins = p if pins is None else pins.fuse(p)

    part = doc.addObject("App::Part", "Button_Tactile_6x6")
    part.Label = "6x6 mm Tactile Pushbutton Switch (Pi Safe-Shutdown GPIO3, COTS)"

    for name, label, sh, col in [
        ("Button_Body", "6x6 mm Switch Housing", body, (0.20, 0.22, 0.25)),
        ("Button_Plunger", "Tactile Actuator Plunger", plunger, (0.85, 0.48, 0.10)),
        ("Button_Pins", "4x Solder Leads", pins.removeSplitter(), (0.82, 0.84, 0.86)),
    ]:
        f = doc.addObject("Part::Feature", name)
        f.Label = label
        f.Shape = sh
        if hasattr(f, "ViewObject") and f.ViewObject:
            f.ViewObject.ShapeColor = col
        part.addObject(f)

    doc.recompute()
    doc.save()
    App.closeDocument(doc_name)
    print(f"✔ Generated 6x6 mm Tactile Pushbutton -> {fcstd_path}")


# =============================================================================
# 17. Ø3 mm T1 Status LED (5V Pi Logic Green / 6V Servos Armed Red, COTS)
#     Panel convention: X = 0.00 outer bezel surface, -X = domed lens, +X = flange & leads
# =============================================================================
def build_led_3mm():
    doc_name = "led_3mm"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)
    fcstd_path = f"{cots_models_dir}/led_3mm.FCStd"
    doc.saveAs(fcstd_path)

    # Lens cylinder (X in [-1.0, +2.0], Ø2.95 mm) + front hemisphere dome (center X = -1.0, R = 1.475 -> X_min = -2.475)
    cyl = Part.makeCylinder(1.475, 3.00, App.Vector(-1.00, 0.0, 0.0), App.Vector(1, 0, 0))
    dome = Part.makeSphere(1.475, App.Vector(-1.00, 0.0, 0.0))
    flange = Part.makeCylinder(1.90, 1.00, App.Vector(2.00, 0.0, 0.0), App.Vector(1, 0, 0))
    lens = cyl.fuse(dome).fuse(flange).removeSplitter()

    lead1 = Part.makeBox(4.50, 0.50, 0.50, App.Vector(3.00, -1.27 - 0.25, -0.25))
    lead2 = Part.makeBox(4.50, 0.50, 0.50, App.Vector(3.00, +1.27 - 0.25, -0.25))
    led_solid = lens.fuse(lead1).fuse(lead2).removeSplitter()

    obj = doc.addObject("Part::Feature", "LED_3mm")
    obj.Label = "Ø3 mm T1 Status LED (COTS)"
    obj.Shape = led_solid
    if hasattr(obj, "ViewObject") and obj.ViewObject:
        obj.ViewObject.ShapeColor = (0.12, 0.85, 0.30)

    doc.recompute()
    doc.save()
    App.closeDocument(doc_name)
    print(f"✔ Generated Ø3 mm T1 Status LED -> {fcstd_path}")


# Execute selected or all builds
BUILDERS = {
    "rpi4": build_rpi4,
    "pca9685": build_pca9685,
    "tca9548a": build_tca9548a,
    "vl53l5cx": build_vl53l5cx,
    "battery_lipo_2s": build_battery_lipo_2s,
    "ubec_3a": build_ubec_3a,
    "xt60e_m": build_xt60e_m,
    "ubec_hobbywing_10a": build_ubec_hobbywing_10a,
    "fuse_mini_atm": build_fuse_mini_atm,
    "switch_mini_slide": build_switch_mini_slide,
    "ads1115": build_ads1115,
    "bno085": build_bno085,
    "magnet_5x2": build_magnet_5x2,
    "screw_m2_button_head": build_screw_m2_button_head,
    "screw_m2_countersunk": build_screw_m2_countersunk,
    "insert_m2_ruthex": build_insert_m2_ruthex,
    "screw_m4x20_countersunk": build_screw_m4x20_countersunk,
    "bolt_m8x40_hex": build_bolt_m8x40_hex,
    "nut_m8_hex": build_nut_m8_hex,
    "standoff_m3x50_round": build_standoff_m3x50_round,
    "oled_096_i2c": build_oled_096_i2c,
    "button_tactile_6x6": build_button_tactile_6x6,
    "led_3mm": build_led_3mm,
}

env_only = [k.strip() for k in os.environ.get("ONLY_COTS", "").split(",") if k.strip()]
only_targets = env_only or [a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--only=")]
if only_targets:
    for key in only_targets:
        BUILDERS[key]()
else:
    for fn in BUILDERS.values():
        fn()

print("=== All Electronics & Power COTS Models Generated with References Successfully ===")
sys.exit(0)
