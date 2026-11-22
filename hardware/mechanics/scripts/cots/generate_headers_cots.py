#!/usr/bin/env python3
"""
Generate Lasius Standard COTS Pin Headers & Sockets
===================================================
Models in `hardware/mechanics/models/cots/`:
  - header_pin_1x2.FCStd
  - header_pin_1x4.FCStd
  - header_pin_1x6.FCStd
  - header_pin_1x10.FCStd
  - header_pin_1x12.FCStd
  - header_pin_2x20.FCStd
  - header_pin_3x16_ra.FCStd
  - header_pin_1x6_ra.FCStd
  - socket_header_1x12.FCStd

Design & Color Standards:
  - Collars/Sockets: Always black thermoplastic (0.12, 0.12, 0.12)
  - Straight & RA Pins: Gold/brass (0.85, 0.70, 0.20), 0.64 x 0.64 mm square
  - Origin: (0, 0, 0) at header base sitting on top of PCB surface (Z = 0)
"""

import os
import sys
import FreeCAD as App
import Part

print("=== Generating Lasius Standard COTS Pin Headers & Sockets ===")

cots_models_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/models/cots"
os.makedirs(cots_models_dir, exist_ok=True)

COLOR_BLACK = (0.12, 0.12, 0.12)
COLOR_GOLD = (0.85, 0.70, 0.20)
COLOR_TIN = (0.75, 0.75, 0.78)

pitch = 2.54
pin_w = 0.64


def build_straight_header_1row(pins, name, label):
    doc_name = name
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)

    len_x = pins * pitch
    len_y = pitch
    h_collar = 2.50
    h_pin_top = 8.50
    z_pin_bottom = -3.00

    # Base thermoplastic collar centered at (0, 0, 0)
    collar = Part.makeBox(len_x, len_y, h_collar, App.Vector(-len_x / 2.0, -len_y / 2.0, 0.0))

    # Segment divider grooves (0.30 mm wide, 0.35 mm deep) to show individual molded blocks
    for i in range(1, pins):
        gx = -len_x / 2.0 + i * pitch
        groove_x = Part.makeBox(0.30, len_y + 0.2, 0.35, App.Vector(gx - 0.15, -len_y / 2.0 - 0.1, h_collar - 0.35))
        collar = collar.cut(groove_x)
    collar = collar.removeSplitter()

    # Discrete gold square pins
    pins_compound = None
    for i in range(pins):
        px = -len_x / 2.0 + (i + 0.5) * pitch
        py = 0.0
        pin = Part.makeBox(pin_w, pin_w, h_pin_top - z_pin_bottom, App.Vector(px - pin_w / 2.0, py - pin_w / 2.0, z_pin_bottom))
        if pins_compound is None:
            pins_compound = pin
        else:
            pins_compound = pins_compound.fuse(pin)
    pins_compound = pins_compound.removeSplitter()

    # Create App::Part container
    part = doc.addObject("App::Part", "Header")
    part.Label = label

    obj_collar = doc.addObject("Part::Feature", "Collar")
    obj_collar.Label = "Thermoplastic Collar (Black)"
    obj_collar.Shape = collar
    if hasattr(obj_collar, "ViewObject") and obj_collar.ViewObject:
        obj_collar.ViewObject.ShapeColor = COLOR_BLACK

    obj_pins = doc.addObject("Part::Feature", "Pins")
    obj_pins.Label = "Gold Contact Pins"
    obj_pins.Shape = pins_compound
    if hasattr(obj_pins, "ViewObject") and obj_pins.ViewObject:
        obj_pins.ViewObject.ShapeColor = COLOR_GOLD

    part.addObject(obj_collar)
    part.addObject(obj_pins)

    doc.recompute()
    fcstd_path = f"{cots_models_dir}/{name}.FCStd"
    doc.saveAs(fcstd_path)
    App.closeDocument(doc_name)
    print(f"✔ Generated {label} -> {fcstd_path}")


def build_straight_header_2row(cols, name, label):
    doc_name = name
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)

    len_x = cols * pitch
    len_y = 2.0 * pitch
    h_collar = 2.50
    h_pin_top = 8.50
    z_pin_bottom = -3.00

    collar = Part.makeBox(len_x, len_y, h_collar, App.Vector(-len_x / 2.0, -len_y / 2.0, 0.0))

    # Divider grooves along X and Y
    for i in range(1, cols):
        gx = -len_x / 2.0 + i * pitch
        groove_x = Part.makeBox(0.30, len_y + 0.2, 0.35, App.Vector(gx - 0.15, -len_y / 2.0 - 0.1, h_collar - 0.35))
        collar = collar.cut(groove_x)
    groove_y = Part.makeBox(len_x + 0.2, 0.30, 0.35, App.Vector(-len_x / 2.0 - 0.1, -0.15, h_collar - 0.35))
    collar = collar.cut(groove_y)
    collar = collar.removeSplitter()

    pins_compound = None
    for r in range(2):
        for c in range(cols):
            px = -len_x / 2.0 + (c + 0.5) * pitch
            py = -len_y / 2.0 + (r + 0.5) * pitch
            pin = Part.makeBox(pin_w, pin_w, h_pin_top - z_pin_bottom, App.Vector(px - pin_w / 2.0, py - pin_w / 2.0, z_pin_bottom))
            if pins_compound is None:
                pins_compound = pin
            else:
                pins_compound = pins_compound.fuse(pin)
    pins_compound = pins_compound.removeSplitter()

    part = doc.addObject("App::Part", "Header")
    part.Label = label

    obj_collar = doc.addObject("Part::Feature", "Collar")
    obj_collar.Label = "Thermoplastic Collar (Black)"
    obj_collar.Shape = collar
    if hasattr(obj_collar, "ViewObject") and obj_collar.ViewObject:
        obj_collar.ViewObject.ShapeColor = COLOR_BLACK

    obj_pins = doc.addObject("Part::Feature", "Pins")
    obj_pins.Label = "Gold Contact Pins"
    obj_pins.Shape = pins_compound
    if hasattr(obj_pins, "ViewObject") and obj_pins.ViewObject:
        obj_pins.ViewObject.ShapeColor = COLOR_GOLD

    part.addObject(obj_collar)
    part.addObject(obj_pins)

    doc.recompute()
    fcstd_path = f"{cots_models_dir}/{name}.FCStd"
    doc.saveAs(fcstd_path)
    App.closeDocument(doc_name)
    print(f"✔ Generated {label} -> {fcstd_path}")


def build_socket_header_1row(pins, name, label, h_body=4.00):
    doc_name = name
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)

    len_x = pins * pitch
    len_y = pitch
    z_pin_bottom = -2.80

    body = Part.makeBox(len_x, len_y, h_body, App.Vector(-len_x / 2.0, -len_y / 2.0, 0.0))

    # Receptacle pin cavities on top
    for i in range(pins):
        px = -len_x / 2.0 + (i + 0.5) * pitch
        py = 0.0
        cav = Part.makeBox(0.80, 0.80, 3.20, App.Vector(px - 0.40, py - 0.40, h_body - 3.20))
        body = body.cut(cav)
    body = body.removeSplitter()

    # Solder tails below PCB
    pins_compound = None
    for i in range(pins):
        px = -len_x / 2.0 + (i + 0.5) * pitch
        py = 0.0
        tail = Part.makeBox(pin_w, pin_w, -z_pin_bottom, App.Vector(px - pin_w / 2.0, py - pin_w / 2.0, z_pin_bottom))
        if pins_compound is None:
            pins_compound = tail
        else:
            pins_compound = pins_compound.fuse(tail)
    pins_compound = pins_compound.removeSplitter()

    part = doc.addObject("App::Part", "Socket")
    part.Label = label

    obj_body = doc.addObject("Part::Feature", "Socket_Body")
    obj_body.Label = "Thermoplastic Socket Body (Black)"
    obj_body.Shape = body
    if hasattr(obj_body, "ViewObject") and obj_body.ViewObject:
        obj_body.ViewObject.ShapeColor = COLOR_BLACK

    obj_pins = doc.addObject("Part::Feature", "Solder_Pins")
    obj_pins.Label = "Solder Contact Tails"
    obj_pins.Shape = pins_compound
    if hasattr(obj_pins, "ViewObject") and obj_pins.ViewObject:
        obj_pins.ViewObject.ShapeColor = COLOR_TIN

    part.addObject(obj_body)
    part.addObject(obj_pins)

    doc.recompute()
    fcstd_path = f"{cots_models_dir}/{name}.FCStd"
    doc.saveAs(fcstd_path)
    App.closeDocument(doc_name)
    print(f"✔ Generated {label} -> {fcstd_path}")


def build_ra_header_3x16():
    name = "header_pin_3x16_ra"
    label = "Pin Header 3x16 Right-Angle 90° (2.54 mm, COTS)"
    doc_name = name
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)

    cols = 16
    len_x = cols * pitch  # 40.64 mm
    collar_w = 4.50
    collar_h = 3.00

    # Collar sitting at Y in [-collar_w/2, collar_w/2], Z in [0, collar_h]
    collar = Part.makeBox(len_x, collar_w, collar_h, App.Vector(-len_x / 2.0, -collar_w / 2.0, 0.0))
    collar = collar.removeSplitter()

    # 48 bent pins extending horizontally in +Y direction
    pin_horiz_len = 8.70
    pins_compound = None
    for row in range(3):
        pz = 0.90 + row * 2.54
        for col in range(cols):
            px = -len_x / 2.0 + (col + 0.5) * pitch
            vert_leg = Part.makeBox(pin_w, pin_w, pz + pin_w + 3.0, App.Vector(px - pin_w / 2.0, -collar_w / 2.0 + 1.2, -3.0))
            horiz_leg = Part.makeBox(pin_w, pin_horiz_len, pin_w, App.Vector(px - pin_w / 2.0, -collar_w / 2.0 + 1.2, pz))
            pin_solid = vert_leg.fuse(horiz_leg)
            if pins_compound is None:
                pins_compound = pin_solid
            else:
                pins_compound = pins_compound.fuse(pin_solid)
    pins_compound = pins_compound.removeSplitter()

    part = doc.addObject("App::Part", "Header")
    part.Label = label

    obj_collar = doc.addObject("Part::Feature", "Collar")
    obj_collar.Label = "Thermoplastic Collar (Black)"
    obj_collar.Shape = collar
    if hasattr(obj_collar, "ViewObject") and obj_collar.ViewObject:
        obj_collar.ViewObject.ShapeColor = COLOR_BLACK

    obj_pins = doc.addObject("Part::Feature", "Pins")
    obj_pins.Label = "Gold Contact Pins (90°)"
    obj_pins.Shape = pins_compound
    if hasattr(obj_pins, "ViewObject") and obj_pins.ViewObject:
        obj_pins.ViewObject.ShapeColor = COLOR_GOLD

    part.addObject(obj_collar)
    part.addObject(obj_pins)

    doc.recompute()
    fcstd_path = f"{cots_models_dir}/{name}.FCStd"
    doc.saveAs(fcstd_path)
    App.closeDocument(doc_name)
    print(f"✔ Generated {label} -> {fcstd_path}")


def build_ra_header_1x6():
    name = "header_pin_1x6_ra"
    label = "Pin Header 1x6 Right-Angle 90° (2.54 mm, COTS)"
    doc_name = name
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)

    pins = 6
    len_x = pins * pitch
    collar_w = 2.54
    collar_h = 2.50

    collar = Part.makeBox(len_x, collar_w, collar_h, App.Vector(-len_x / 2.0, -collar_w / 2.0, 0.0))
    collar = collar.removeSplitter()

    horiz_len = 6.00
    pins_compound = None
    for i in range(pins):
        px = -len_x / 2.0 + (i + 0.5) * pitch
        vert_leg = Part.makeBox(pin_w, pin_w, 2.00 + 3.0, App.Vector(px - pin_w / 2.0, -pin_w / 2.0, -3.0))
        horiz_leg = Part.makeBox(pin_w, horiz_len, pin_w, App.Vector(px - pin_w / 2.0, -pin_w / 2.0, 1.25 - pin_w / 2.0))
        pin_solid = vert_leg.fuse(horiz_leg)
        if pins_compound is None:
            pins_compound = pin_solid
        else:
            pins_compound = pins_compound.fuse(pin_solid)
    pins_compound = pins_compound.removeSplitter()

    part = doc.addObject("App::Part", "Header")
    part.Label = label

    obj_collar = doc.addObject("Part::Feature", "Collar")
    obj_collar.Label = "Thermoplastic Collar (Black)"
    obj_collar.Shape = collar
    if hasattr(obj_collar, "ViewObject") and obj_collar.ViewObject:
        obj_collar.ViewObject.ShapeColor = COLOR_BLACK

    obj_pins = doc.addObject("Part::Feature", "Pins")
    obj_pins.Label = "Gold Contact Pins (90°)"
    obj_pins.Shape = pins_compound
    if hasattr(obj_pins, "ViewObject") and obj_pins.ViewObject:
        obj_pins.ViewObject.ShapeColor = COLOR_GOLD

    part.addObject(obj_collar)
    part.addObject(obj_pins)

    doc.recompute()
    fcstd_path = f"{cots_models_dir}/{name}.FCStd"
    doc.saveAs(fcstd_path)
    App.closeDocument(doc_name)
    print(f"✔ Generated {label} -> {fcstd_path}")


# Execute generation of all standard COTS headers
build_straight_header_1row(2, "header_pin_1x2", "Pin Header 1x2 Straight (2.54 mm, COTS)")
build_straight_header_1row(4, "header_pin_1x4", "Pin Header 1x4 Straight (2.54 mm, COTS)")
build_straight_header_1row(6, "header_pin_1x6", "Pin Header 1x6 Straight (2.54 mm, COTS)")
build_straight_header_1row(10, "header_pin_1x10", "Pin Header 1x10 Straight (2.54 mm, COTS)")
build_straight_header_1row(12, "header_pin_1x12", "Pin Header 1x12 Straight (2.54 mm, COTS)")
build_straight_header_2row(20, "header_pin_2x20", "Pin Header 2x20 Straight (2.54 mm, RPi GPIO, COTS)")
build_ra_header_3x16()
build_ra_header_1x6()
build_socket_header_1row(12, "socket_header_1x12", "Socket Header 1x12 Straight (2.54 mm, Female, COTS)")

print("=== All COTS Headers & Sockets Generated Successfully ===")
sys.exit(0)
