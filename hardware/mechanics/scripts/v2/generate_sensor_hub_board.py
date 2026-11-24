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
  - Sockets & Headers referenced via App::Link to standard COTS models:
    * Dual 12-Pin female sockets: `cots/socket_header_1x12.FCStd` (Black body, solder pins)
    * 6x Leg headers (4-pin): `cots/header_pin_1x4.FCStd` (Black collar, gold pins)
    * 1x Pi Main Bus header (4-pin): `cots/header_pin_1x4.FCStd`
    * 1x AUX / Sensor Expansion (4-pin): `cots/header_pin_1x4.FCStd`
    * 2x PCA9685 Logic Power Feeds (2-pin): `cots/header_pin_1x2.FCStd`
  - Dimensions: 54.0 mm along Y x 22.0 mm along X x 1.60 mm PCB thickness.
    2x M2.5 mounting holes at (0.0, ±13.0 mm) matching monocoque screw bosses.
"""

import math
import os
import sys
import FreeCAD as App
import Part

print("--- Generating Lasius Sensor Hub & Distribution Board v2 with COTS References ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts/chassis"
cots_dir = f"{repo_root}/hardware/mechanics/models/cots"
os.makedirs(models_dir, exist_ok=True)
fcstd_path = f"{models_dir}/sensor_hub_board.FCStd"

doc_name = "sensor_hub_board"
try:
    App.closeDocument(doc_name)
except Exception:
    pass
doc = App.newDocument(doc_name)
doc.saveAs(fcstd_path)

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
pcb_solid = pcb_solid.cut(hole1).cut(hole2).removeSplitter()

# 3. Decoupling Capacitors (10 µF electrolytic + 100 nF ceramic)
cap_elec = Part.makeCylinder(2.0, 5.0, App.Vector(-8.80, 18.0, t_pcb), App.Vector(0, 0, 1))
cap_mlcc = Part.makeBox(1.0, 2.5, 1.2, App.Vector(-9.30, -18.75, t_pcb))  # Relocated adjacent to TCA VIN/GND at (-8.80, -17.50)
caps_solid = cap_elec.fuse(cap_mlcc).removeSplitter()

# Create Root App::Part Container
part = doc.addObject("App::Part", "Sensor_Hub_Board")
part.Label = "Sensor Hub & 3.3V/GND Distribution Carrier Board (v2)"

obj_pcb = doc.addObject("Part::Feature", "Carrier_PCB")
obj_pcb.Label = "Carrier FR4 PCB (Green)"
obj_pcb.Shape = pcb_solid
if hasattr(obj_pcb, "ViewObject") and obj_pcb.ViewObject:
    obj_pcb.ViewObject.ShapeColor = (0.12, 0.38, 0.22)  # Dark Forest Green FR4
part.addObject(obj_pcb)

obj_caps = doc.addObject("Part::Feature", "Filter_Capacitors")
obj_caps.Label = "Decoupling Capacitors (10uF + 100nF)"
obj_caps.Shape = caps_solid
if hasattr(obj_caps, "ViewObject") and obj_caps.ViewObject:
    obj_caps.ViewObject.ShapeColor = (0.35, 0.35, 0.38)
part.addObject(obj_caps)

# Open COTS Header documents for linking
doc_sock12 = App.openDocument(f"{cots_dir}/socket_header_1x12.FCStd")
doc_hdr4 = App.openDocument(f"{cots_dir}/header_pin_1x4.FCStd")
doc_hdr2 = App.openDocument(f"{cots_dir}/header_pin_1x2.FCStd")

rot_90 = App.Rotation(App.Vector(0, 0, 1), 90.0)

# 4. Dual 12-Pin Female Sockets for TCA9548A Multiplexer at X = ±8.77 mm (along Y)
lnk_sock1 = doc.addObject("App::Link", "Socket_TCA_Right")
lnk_sock1.Label = "TCA9548A Right Socket (1x12, Female, COTS)"
lnk_sock1.setLink(doc_sock12.Socket)
lnk_sock1.Placement = App.Placement(App.Vector(8.77, 0.00, t_pcb), rot_90)
part.addObject(lnk_sock1)

lnk_sock2 = doc.addObject("App::Link", "Socket_TCA_Left")
lnk_sock2.Label = "TCA9548A Left Socket (1x12, Female, COTS)"
lnk_sock2.setLink(doc_sock12.Socket)
lnk_sock2.Placement = App.Placement(App.Vector(-8.77, 0.00, t_pcb), rot_90)
part.addObject(lnk_sock2)

# 5. Left Bank (+Y): LR, LM, LF (4-pin), Pi Main Bus (4-pin), PCA9685 Left Logic (2-pin)
y_bank_l = 21.28
leg_connectors_l = [
    ("Header_Leg_LR", "Leg LR Connector (CH2, 1x4, COTS)", -5.715),
    ("Header_Leg_LM", "Leg LM Connector (CH1, 1x4, COTS)", -1.905),
    ("Header_Leg_LF", "Leg LF Connector (CH0, 1x4, COTS)", 1.905),
    ("Header_Pi_Bus", "RPi Main I2C Bus Input (1x4, COTS)", 5.715),
]
for name, lbl, px in leg_connectors_l:
    lnk = doc.addObject("App::Link", name)
    lnk.Label = lbl
    lnk.setLink(doc_hdr4.Header)
    lnk.Placement = App.Placement(App.Vector(px, y_bank_l, t_pcb), rot_90)
    part.addObject(lnk)

lnk_pca_l = doc.addObject("App::Link", "Header_PCA_Logic_Left")
lnk_pca_l.Label = "PCA9685 Left Logic Power (1x2, COTS)"
lnk_pca_l.setLink(doc_hdr2.Header)
lnk_pca_l.Placement = App.Placement(App.Vector(8.80, 22.00, t_pcb), rot_90)
part.addObject(lnk_pca_l)

# 6. Right Bank (-Y): RR, RM, FR (4-pin), AUX Expansion (4-pin), PCA9685 Right Logic (2-pin)
y_bank_r = -21.28
leg_connectors_r = [
    ("Header_Leg_RR", "Leg RR Connector (CH5, 1x4, COTS)", -5.715),
    ("Header_Leg_RM", "Leg RM Connector (CH4, 1x4, COTS)", -1.905),
    ("Header_Leg_FR", "Leg FR Connector (CH3, 1x4, COTS)", 1.905),
    ("Header_AUX_Port", "AUX / Sensor Expansion Port (CH6/7, 1x4, COTS)", 5.715),
]
for name, lbl, px in leg_connectors_r:
    lnk = doc.addObject("App::Link", name)
    lnk.Label = lbl
    lnk.setLink(doc_hdr4.Header)
    lnk.Placement = App.Placement(App.Vector(px, y_bank_r, t_pcb), rot_90)
    part.addObject(lnk)

lnk_pca_r = doc.addObject("App::Link", "Header_PCA_Logic_Right")
lnk_pca_r.Label = "PCA9685 Right Logic Power (1x2, COTS)"
lnk_pca_r.setLink(doc_hdr2.Header)
lnk_pca_r.Placement = App.Placement(App.Vector(-8.80, -22.00, t_pcb), rot_90)
part.addObject(lnk_pca_r)

doc.recompute()
doc.save()

App.closeDocument(doc_sock12.Name)
App.closeDocument(doc_hdr4.Name)
App.closeDocument(doc_hdr2.Name)
App.closeDocument(doc_name)

print(f"✔ Generated Sensor Hub Board with COTS References -> {fcstd_path}")
sys.exit(0)
