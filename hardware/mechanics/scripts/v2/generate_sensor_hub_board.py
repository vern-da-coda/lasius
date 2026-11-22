#!/usr/bin/env python3
"""
Generate Lasius Sensor Hub & 3.3V / GND Distribution Carrier Board v2
=====================================================================
Model: custom/v2/parts/chassis/sensor_hub_board.FCStd

Architecture:
  - Central distribution carrier board seated on Level 2 Intermediate Deck
    bosses at (0.0, 0.0, 28.00 mm).
  - Integrates the 8-channel TCA9548A I2C Multiplexer (seated in central dual 12-pin sockets)
    with a continuous 3.3V logic rail and common logic Star-GND rail.
  - Exposes 6x dedicated 4-pin polarized leg connectors (2.54 mm pitch):
      Pin 1: 3.3V (Red)
      Pin 2: GND (Black)
      Pin 3: SCx I2C Clock (Yellow)
      Pin 4: SDx I2C Data (Channel color)
    * Left Bank (+Y): LR (CH2 Violet), LM (CH1 Green), LF (CH0 Blue) facing left cable ports.
    * Right Bank (-Y): RR (CH5 Grey), RM (CH4 White), FR (CH3 Orange) facing right cable ports.
  - Dedicated connectors:
    * 1x 4-Pin Main Bus Input from Raspberry Pi (3.3V, GND, SDA, SCL).
    * 1x 4-Pin Auxiliary / Sensor Expansion Port (CH6 INA228 / CH7 ToF).
    * 2x 2-Pin Logic Power Feeds for PCA9685 Left and Right controllers (3.3V, GND).
    * Filter caps: 10 µF electrolytic + 100 nF MLCC ceramic capacitor.
  - Dimensions: 54.0 mm along Y x 22.0 mm along X x 1.60 mm PCB thickness.
    2x M2.5 mounting holes at (0.0, ±13.0 mm) matching monocoque screw bosses.
"""

import math
import os
import sys
import FreeCAD as App
import Part

print("--- Generating Lasius Sensor Hub & Distribution Board v2 ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts/chassis"
os.makedirs(models_dir, exist_ok=True)
fcstd_path = f"{models_dir}/sensor_hub_board.FCStd"

doc_name = "sensor_hub_board"
try:
    App.closeDocument(doc_name)
except Exception:
    pass
doc = App.newDocument(doc_name)

# 1. Carrier PCB Substrate (54.0 mm along Y, 22.0 mm along X, 1.60 mm thick)
w_x = 22.0
l_y = 54.0
t_pcb = 1.60
r_corner = 2.0

xmin, xmax = -w_x / 2.0, w_x / 2.0
ymin, ymax = -l_y / 2.0, l_y / 2.0
r = r_corner
k = r * (1.0 - 1.0 / math.sqrt(2.0))
pts = [
    (xmin + r, ymax), (xmax - r, ymax), (xmax - k, ymax - k), (xmax, ymax - r),
    (xmax, ymin + r), (xmax - k, ymin + k), (xmax - r, ymin), (xmin + r, ymin),
    (xmin + k, ymin + k), (xmin, ymin + r), (xmin, ymax - r), (xmin + k, ymax - k)
]
v = [App.Vector(px, py, 0.0) for px, py in pts]
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
wire = Part.Wire(edges)
pcb_face = Part.Face(wire)
pcb_solid = pcb_face.extrude(App.Vector(0.0, 0.0, t_pcb))

# 2. Mounting Holes matching Monocoque Intermediate Deck Bosses at (0.0, ±13.0 mm)
hole_r = 1.30  # Ø2.6 mm for M2.5 screw pass-through
hole1 = Part.makeCylinder(hole_r, 5.0, App.Vector(0.0, 13.0, -1.0), App.Vector(0, 0, 1))
hole2 = Part.makeCylinder(hole_r, 5.0, App.Vector(0.0, -13.0, -1.0), App.Vector(0, 0, 1))
pcb_solid = pcb_solid.cut(hole1).cut(hole2)


def make_pin_header(x_c, y_c, z_base, pins, orient_x=False):
    """Creates a black thermoplastic header body with gold pins."""
    pitch = 2.54
    if orient_x:
        len_x = pins * pitch
        len_y = pitch
    else:
        len_x = pitch
        len_y = pins * pitch
    h_box = 2.50
    h_pin = 8.50
    box = Part.makeBox(len_x, len_y, h_box, App.Vector(x_c - len_x / 2.0, y_c - len_y / 2.0, z_base))
    pins_compound = box
    for i in range(pins):
        if orient_x:
            px = x_c - len_x / 2.0 + (i + 0.5) * pitch
            py = y_c
        else:
            px = x_c
            py = y_c - len_y / 2.0 + (i + 0.5) * pitch
        pin = Part.makeBox(0.64, 0.64, h_pin, App.Vector(px - 0.32, py - 0.32, z_base - 1.0))
        pins_compound = pins_compound.fuse(pin)
    return pins_compound


# 3. Dual 12-Pin Female Socket Headers for TCA9548A Multiplexer (Height 4.00 mm)
h_sock = 4.00
sock1 = Part.makeBox(2.54, 30.48, h_sock, App.Vector(8.77 - 1.27, -15.24, t_pcb))
sock2 = Part.makeBox(2.54, 30.48, h_sock, App.Vector(-8.77 - 1.27, -15.24, t_pcb))

# 4. Left Bank (+Y): LR, LM, LF (4-pin), Pi Main Bus (4-pin), PCA9685 Left Logic (2-pin)
y_bank_l = 21.28
h_lr = make_pin_header(-5.715, y_bank_l, t_pcb, 4, orient_x=False)    # Left Rear (CH2)
h_lm = make_pin_header(-1.905, y_bank_l, t_pcb, 4, orient_x=False)    # Left Middle (CH1)
h_lf = make_pin_header(1.905, y_bank_l, t_pcb, 4, orient_x=False)     # Left Front (CH0)
h_pi = make_pin_header(5.715, y_bank_l, t_pcb, 4, orient_x=False)     # Pi Main Bus Input
h_pca_l = make_pin_header(8.80, 22.0, t_pcb, 2, orient_x=False)      # PCA9685 Left Logic Power

# 5. Right Bank (-Y): RR, RM, FR (4-pin), AUX Expansion (4-pin), PCA9685 Right Logic (2-pin)
y_bank_r = -21.28
h_rr = make_pin_header(-5.715, y_bank_r, t_pcb, 4, orient_x=False)    # Right Rear (CH5)
h_mr = make_pin_header(-1.905, y_bank_r, t_pcb, 4, orient_x=False)    # Right Middle (CH4)
h_fr = make_pin_header(1.905, y_bank_r, t_pcb, 4, orient_x=False)     # Right Front (CH3)
h_aux = make_pin_header(5.715, y_bank_r, t_pcb, 4, orient_x=False)    # AUX / Sensor Expansion (CH6/7)
h_pca_r = make_pin_header(-8.80, -22.0, t_pcb, 2, orient_x=False)    # PCA9685 Right Logic Power

# 6. Decoupling Capacitors (10 µF electrolytic + 100 nF ceramic)
cap_elec = Part.makeCylinder(2.0, 5.0, App.Vector(-8.80, 18.0, t_pcb), App.Vector(0, 0, 1))
cap_mlcc = Part.makeBox(1.6, 0.8, 1.2, App.Vector(8.00, -18.4, t_pcb))

# Assemble complete composite solid
hub_solid = pcb_solid.fuse(sock1).fuse(sock2)
hub_solid = hub_solid.fuse(h_lr).fuse(h_lm).fuse(h_lf).fuse(h_pi).fuse(h_pca_l)
hub_solid = hub_solid.fuse(h_rr).fuse(h_mr).fuse(h_fr).fuse(h_aux).fuse(h_pca_r)
hub_solid = hub_solid.fuse(cap_elec).fuse(cap_mlcc)
hub_solid = hub_solid.removeSplitter()

part_obj = doc.addObject("Part::Feature", "Sensor_Hub_Board")
part_obj.Label = "Sensor Hub & 3.3V/GND Distribution Carrier Board (v2)"
part_obj.Shape = hub_solid
if hasattr(part_obj, "ViewObject") and part_obj.ViewObject is not None:
    part_obj.ViewObject.Visibility = True
    part_obj.ViewObject.ShapeColor = (0.12, 0.38, 0.22)  # Dark Forest Green FR4

doc.recompute()
doc.saveAs(fcstd_path)
print(f"✔ Generated Sensor Hub Board -> {fcstd_path} (Valid={hub_solid.isValid()}, Volume={hub_solid.Volume:.1f} mm^3)")
