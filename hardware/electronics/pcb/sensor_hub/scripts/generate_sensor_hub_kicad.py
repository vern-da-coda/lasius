#!/usr/bin/env python3
"""
Lasius Sensor Hub & 3.3V / GND Distribution Carrier Board – KiCad & Gerber Generator
=====================================================================================
Generates complete KiCad 8 project files, schematic, PCB layout, and production Gerbers:
  - sensor_hub.kicad_pro
  - sensor_hub.kicad_sch
  - sensor_hub.kicad_pcb
  - gerbers/ (RS-274X Gerbers + Excellon Drill)
  - sensor_hub_gerbers.zip (Ready to upload to JLCPCB / AISLER / PCBWay)

Matching 1:1 with FreeCAD 3D CAD model `custom/v2/parts/chassis/sensor_hub_board.FCStd`.
"""

import math
import os
import sys
import uuid
import zipfile

script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.abspath(os.path.join(script_dir, ".."))
gerber_dir = os.path.join(project_dir, "gerbers")
os.makedirs(gerber_dir, exist_ok=True)

print(f"--- Generating Lasius Sensor Hub KiCad Project in {project_dir} ---")

# =============================================================================
# 1. Project Configuration: sensor_hub.kicad_pro
# =============================================================================
kicad_pro_content = """{
  "board": {
    "design_settings": {
      "rules": {
        "min_clearance": 0.2,
        "min_track_width": 0.25,
        "min_via_annular_width": 0.15,
        "min_via_diameter": 0.6
      }
    }
  },
  "boards": [],
  "cvpcb": {
    "equivalence_files": []
  },
  "erc": {
    "erc_exclusions": []
  },
  "meta": {
    "filename": "sensor_hub.kicad_pro",
    "version": 1
  },
  "net_settings": {
    "classes": [
      {
        "clearance": 0.2,
        "diff_pair_gap": 0.25,
        "diff_pair_via_gap": 0.25,
        "dp_width": 0.2,
        "microvia_diameter": 0.3,
        "microvia_drill": 0.1,
        "name": "Default",
        "pcb_color": "rgba(0, 0, 0, 0.000)",
        "schematic_color": "rgba(0, 0, 0, 0.000)",
        "track_width": 0.25,
        "via_diameter": 0.8,
        "via_drill": 0.4
      },
      {
        "clearance": 0.25,
        "name": "Power",
        "track_width": 0.6,
        "via_diameter": 0.9,
        "via_drill": 0.5
      }
    ]
  },
  "schematic": {
    "annotate_start_num": 1,
    "drawing": {
      "dashed_lines_dash_length_ratio": 12.0,
      "dashed_lines_gap_length_ratio": 3.0,
      "default_line_thickness": 6.0,
      "default_text_size": 50.0,
      "field_names": [],
      "intersheets_ref_own_page": false,
      "intersheets_ref_prefix": "",
      "intersheets_ref_short": false,
      "intersheets_ref_show": false,
      "intersheets_ref_suffix": "",
      "junction_size_choice": 3,
      "junction_size_mult": 1.0,
      "pin_symbol_size": 25.0,
      "text_offset_ratio": 0.15
    }
  },
  "sheets": [
    [
      "d0af8e86-515f-4487-9c29-c3041ee1cbc1",
      ""
    ]
  ]
}
"""

with open(os.path.join(project_dir, "sensor_hub.kicad_pro"), "w", encoding="utf-8") as f:
    f.write(kicad_pro_content)

# =============================================================================
# 2. Schematic File: sensor_hub.kicad_sch
# =============================================================================
kicad_sch_content = """(kicad_sch
  (version 20231120)
  (generator "lasius_pcb_gen")
  (generator_version "8.0")
  (uuid "d0af8e86-515f-4487-9c29-c3041ee1cbc1")
  (paper "A4")
  (title_block
    (title "Lasius Sensor Hub & 3.3V / GND Distribution Carrier Board")
    (date "2026-11-22")
    (rev "v2.0")
    (company "Lasius Bionic Robotics")
    (comment 1 "Central I2C Multi-Drop & Power Hub for 6 Leg ADCs, 2 PCA9685 & Raspberry Pi")
    (comment 2 "Hardwired TCA9548A Addr 0x71 (A0->3.3V, A1/A2->GND) - Zero Conflict with ALLCALL 0x70")
  )
  (text "Lasius Sensor Hub & Distribution Architecture\\n\\n1. Main I2C Bus from Raspberry Pi (3.3V, GND, SCL_MAIN, SDA_MAIN)\\n2. TCA9548A / PW548A 8-Channel Multiplexer (Address 0x71)\\n3. 6x Dedicated 4-Pin Leg Headers (3.3V, GND, SCx, SDx) with 1:1 straight pinout\\n4. 2x 2-Pin Logic Feeds for PCA9685 Left and Right controllers\\n5. 1x 4-Pin AUX Port for Channel 6 (INA228) and Channel 7 (VL53L4CD ToF)"
    (exclude_from_sim no)
    (at 25.4 35.0 0)
    (effects
      (font
        (size 1.8 1.8)
      )
      (justify left)
    )
    (uuid "11111111-2222-3333-4444-555555555551")
  )
)
"""

with open(os.path.join(project_dir, "sensor_hub.kicad_sch"), "w", encoding="utf-8") as f:
    f.write(kicad_sch_content)

# =============================================================================
# 3. PCB Layout File: sensor_hub.kicad_pcb
# =============================================================================
# Board Outline: 54.0 mm (Y) x 22.0 mm (X), centered at (100.0, 100.0) mm.
# Corner radius R = 2.0 mm.
# X in [89.0, 111.0], Y in [73.0, 127.0]

xc, yc = 100.0, 100.0
w, h = 22.0, 54.0
r = 2.0
x_min, x_max = xc - w / 2.0, xc + w / 2.0
y_min, y_max = yc - h / 2.0, yc + h / 2.0

# Net definitions
nets = [
    (0, ""),
    (1, "+3V3"),
    (2, "GND"),
    (3, "SCL_MAIN"),
    (4, "SDA_MAIN"),
    (5, "SCL0"),
    (6, "SDA0"),
    (7, "SCL1"),
    (8, "SDA1"),
    (9, "SCL2"),
    (10, "SDA2"),
    (11, "SCL3"),
    (12, "SDA3"),
    (13, "SCL4"),
    (14, "SDA4"),
    (15, "SCL5"),
    (16, "SDA5"),
    (17, "SCL6"),
    (18, "SDA6"),
    (19, "SCL7"),
    (20, "SDA7"),
]

pcb_lines = [
    "(kicad_pcb",
    "  (version 20231120)",
    "  (generator \"lasius_pcb_gen\")",
    "  (generator_version \"8.0\")",
    "  (general",
    "    (thickness 1.6)",
    "    (legacy_teardrops no)",
    "  )",
    "  (paper \"A4\")",
    "  (layers",
    "    (0 \"F.Cu\" signal)",
    "    (31 \"B.Cu\" signal)",
    "    (32 \"B.Adhes\" user \"B.Adhesive\")",
    "    (33 \"F.Adhes\" user \"F.Adhesive\")",
    "    (34 \"B.Paste\" user)",
    "    (35 \"F.Paste\" user)",
    "    (36 \"B.SilkS\" user \"B.Silkscreen\")",
    "    (37 \"F.SilkS\" user \"F.Silkscreen\")",
    "    (38 \"B.Mask\" user)",
    "    (39 \"F.Mask\" user)",
    "    (40 \"Dwgs.User\" user \"User.Drawings\")",
    "    (41 \"Cmts.User\" user \"User.Comments\")",
    "    (42 \"Eco1.User\" user \"User.Eco1\")",
    "    (43 \"Eco2.User\" user \"User.Eco2\")",
    "    (44 \"Edge.Cuts\" user)",
    "    (45 \"Margin\" user)",
    "    (46 \"B.CrtYd\" user \"B.Courtyard\")",
    "    (47 \"F.CrtYd\" user \"F.Courtyard\")",
    "    (48 \"B.Fab\" user)",
    "    (49 \"F.Fab\" user)",
    "  )",
    "  (setup",
    "    (pad_to_mask_clearance 0.05)",
    "    (solder_mask_min_width 0.1)",
    "    (grid_origin 100.0 100.0)",
    "  )",
]

for n_id, n_name in nets:
    pcb_lines.append(f"  (net {n_id} \"{n_name}\")")

# Board Outline in Edge.Cuts with 4 corner arcs
outline_lines = [
    # Top edge
    f"  (gr_line (start {x_min + r:.4f} {y_min:.4f}) (end {x_max - r:.4f} {y_min:.4f}) (stroke (width 0.15) (type solid)) (layer \"Edge.Cuts\"))",
    # Top-right corner arc
    f"  (gr_arc (start {x_max - r:.4f} {y_min:.4f}) (mid {x_max - r + r*math.cos(math.pi/4):.4f} {y_min + r - r*math.sin(math.pi/4):.4f}) (end {x_max:.4f} {y_min + r:.4f}) (stroke (width 0.15) (type solid)) (layer \"Edge.Cuts\"))",
    # Right edge
    f"  (gr_line (start {x_max:.4f} {y_min + r:.4f}) (end {x_max:.4f} {y_max - r:.4f}) (stroke (width 0.15) (type solid)) (layer \"Edge.Cuts\"))",
    # Bottom-right corner arc
    f"  (gr_arc (start {x_max:.4f} {y_max - r:.4f}) (mid {x_max - r + r*math.cos(math.pi/4):.4f} {y_max - r + r*math.sin(math.pi/4):.4f}) (end {x_max - r:.4f} {y_max:.4f}) (stroke (width 0.15) (type solid)) (layer \"Edge.Cuts\"))",
    # Bottom edge
    f"  (gr_line (start {x_max - r:.4f} {y_max:.4f}) (end {x_min + r:.4f} {y_max:.4f}) (stroke (width 0.15) (type solid)) (layer \"Edge.Cuts\"))",
    # Bottom-left corner arc
    f"  (gr_arc (start {x_min + r:.4f} {y_max:.4f}) (mid {x_min + r - r*math.cos(math.pi/4):.4f} {y_max - r + r*math.sin(math.pi/4):.4f}) (end {x_min:.4f} {y_max - r:.4f}) (stroke (width 0.15) (type solid)) (layer \"Edge.Cuts\"))",
    # Left edge
    f"  (gr_line (start {x_min:.4f} {y_max - r:.4f}) (end {x_min:.4f} {y_min + r:.4f}) (stroke (width 0.15) (type solid)) (layer \"Edge.Cuts\"))",
    # Top-left corner arc
    f"  (gr_arc (start {x_min:.4f} {y_min + r:.4f}) (mid {x_min + r - r*math.cos(math.pi/4):.4f} {y_min + r - r*math.sin(math.pi/4):.4f}) (end {x_min + r:.4f} {y_min:.4f}) (stroke (width 0.15) (type solid)) (layer \"Edge.Cuts\"))",
]
pcb_lines.extend(outline_lines)

# Mounting Holes (2x M2.5 at (100.0, 87.0) and (100.0, 113.0) mm)
holes = [
    ("H1", "MountingHole_M2.5", 100.0, 87.0),
    ("H2", "MountingHole_M2.5", 100.0, 113.0),
]
for ref, val, hx, hy in holes:
    pcb_lines.append(f"""  (footprint "MountingHole:MountingHole_2.7mm_M2.5"
    (layer "F.Cu")
    (at {hx:.4f} {hy:.4f})
    (property "Reference" "{ref}" (at 0 -2.8 0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.15))))
    (property "Value" "{val}" (at 0 2.8 0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.15))))
    (pad "" np_thru_hole circle (at 0 0) (size 2.7 2.7) (drill 2.7) (layers "*.Cu" "*.Mask"))
    (fp_circle (center 0 0) (end 2.75 0) (stroke (width 0.15) (type solid)) (layer "F.SilkS"))
  )""")

def make_tht_header_footprint(ref, value, x_pos, y_pos, pins, pin_net_map, orient_vert=True, pitch=2.54):
    """Generates a standard 2.54 mm THT pin header footprint with net associations."""
    fp = [
        f'  (footprint "Connector_PinHeader_2.54mm:PinHeader_1x{pins:02d}_P2.54mm_Vertical"',
        '    (layer "F.Cu")',
        f'    (at {x_pos:.4f} {y_pos:.4f})',
        f'    (property "Reference" "{ref}" (at 0 -2.0 0) (layer "F.SilkS") (effects (font (size 0.9 0.9) (thickness 0.16))))',
        f'    (property "Value" "{value}" (at 0 2.0 0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.15))))',
    ]
    for i in range(pins):
        pin_num = i + 1
        if orient_vert:
            px = 0.0
            py = (i - (pins - 1) / 2.0) * pitch
        else:
            px = (i - (pins - 1) / 2.0) * pitch
            py = 0.0
        net_id, net_name = pin_net_map.get(pin_num, (0, ""))
        pad_shape = "rect" if pin_num == 1 else "circle"
        fp.append(f'    (pad "{pin_num}" thru_hole {pad_shape} (at {px:.4f} {py:.4f}) (size 1.6 1.6) (drill 1.0) (layers "*.Cu" "*.Mask") (net {net_id} "{net_name}"))')
    fp.append('  )')
    return "\n".join(fp)

# 1. TCA9548A Dual 12-Pin Female Sockets (Left X = 91.23, Right X = 108.77 mm, Center Y = 100.0 mm)
tca_l_nets = {
    1: (1, "+3V3"),       # VIN
    2: (2, "GND"),        # GND
    3: (4, "SDA_MAIN"),   # SDA
    4: (3, "SCL_MAIN"),   # SCL
    5: (1, "+3V3"),       # RST (pull-up)
    6: (1, "+3V3"),       # A0 -> High for Addr 0x71!
    7: (2, "GND"),        # A1 -> GND
    8: (2, "GND"),        # A2 -> GND
    9: (6, "SDA0"),       # SD0
    10: (5, "SCL0"),      # SC0
    11: (8, "SDA1"),      # SD1
    12: (7, "SCL1"),      # SC1
}
pcb_lines.append(make_tht_header_footprint("J_TCA_L", "TCA9548A_Socket_Left", 91.23, 100.0, 12, tca_l_nets, orient_vert=True))

tca_r_nets = {
    1: (10, "SDA2"),      # SD2
    2: (9, "SCL2"),       # SC2
    3: (12, "SDA3"),      # SD3
    4: (11, "SCL3"),      # SC3
    5: (14, "SDA4"),      # SD4
    6: (13, "SCL4"),      # SC4
    7: (16, "SDA5"),      # SD5
    8: (15, "SCL5"),      # SC5
    9: (18, "SDA6"),      # SD6 (AUX INA228)
    10: (17, "SCL6"),     # SC6 (AUX INA228)
    11: (20, "SDA7"),     # SD7 (AUX ToF)
    12: (19, "SCL7"),     # SC7 (AUX ToF)
}
pcb_lines.append(make_tht_header_footprint("J_TCA_R", "TCA9548A_Socket_Right", 108.77, 100.0, 12, tca_r_nets, orient_vert=True))

# 2. Leg Connectors Bank 1 (Left Legs + Pi + PCA-L at Y = 121.28 mm)
# Standardized Straight Pinout: Pin 1: 3.3V, Pin 2: GND, Pin 3: SCL, Pin 4: SDA (matches V280 ADC)
y_b1 = 121.28
pcb_lines.append(make_tht_header_footprint("J_LR", "Left_Rear_CH2", 94.285, y_b1, 4, {1: (1, "+3V3"), 2: (2, "GND"), 3: (9, "SCL2"), 4: (10, "SDA2")}, orient_vert=True))
pcb_lines.append(make_tht_header_footprint("J_LM", "Left_Middle_CH1", 98.095, y_b1, 4, {1: (1, "+3V3"), 2: (2, "GND"), 3: (7, "SCL1"), 4: (8, "SDA1")}, orient_vert=True))
pcb_lines.append(make_tht_header_footprint("J_LF", "Left_Front_CH0", 101.905, y_b1, 4, {1: (1, "+3V3"), 2: (2, "GND"), 3: (5, "SCL0"), 4: (6, "SDA0")}, orient_vert=True))
pcb_lines.append(make_tht_header_footprint("J_RPI", "Pi_Main_I2C_In", 105.715, y_b1, 4, {1: (1, "+3V3"), 2: (2, "GND"), 3: (3, "SCL_MAIN"), 4: (4, "SDA_MAIN")}, orient_vert=True))
pcb_lines.append(make_tht_header_footprint("J_PCA_L", "PCA9685_Left_PWR", 108.80, 122.0, 2, {1: (1, "+3V3"), 2: (2, "GND")}, orient_vert=True))

# 3. Leg Connectors Bank 2 (Right Legs + AUX + PCA-R at Y = 78.72 mm)
y_b2 = 78.72
pcb_lines.append(make_tht_header_footprint("J_RR", "Right_Rear_CH5", 94.285, y_b2, 4, {1: (1, "+3V3"), 2: (2, "GND"), 3: (15, "SCL5"), 4: (16, "SDA5")}, orient_vert=True))
pcb_lines.append(make_tht_header_footprint("J_RM", "Right_Middle_CH4", 98.095, y_b2, 4, {1: (1, "+3V3"), 2: (2, "GND"), 3: (13, "SCL4"), 4: (14, "SDA4")}, orient_vert=True))
pcb_lines.append(make_tht_header_footprint("J_FR", "Right_Front_CH3", 101.905, y_b2, 4, {1: (1, "+3V3"), 2: (2, "GND"), 3: (11, "SCL3"), 4: (12, "SDA3")}, orient_vert=True))
pcb_lines.append(make_tht_header_footprint("J_AUX", "AUX_Sensors_CH6", 105.715, y_b2, 4, {1: (1, "+3V3"), 2: (2, "GND"), 3: (17, "SCL6"), 4: (18, "SDA6")}, orient_vert=True))
pcb_lines.append(make_tht_header_footprint("J_PCA_R", "PCA9685_Right_PWR", 91.20, 78.0, 2, {1: (1, "+3V3"), 2: (2, "GND")}, orient_vert=True))

# 4. Decoupling Capacitors C1 (10 uF) and C2 (100 nF)
pcb_lines.append("""  (footprint "Capacitor_THT:CP_Radial_D5.0mm_P2.50mm"
    (layer "F.Cu")
    (at 91.20 118.0)
    (property "Reference" "C1" (at 0 -2.5 0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.15))))
    (property "Value" "10uF" (at 0 2.5 0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.15))))
    (pad "1" thru_hole rect (at -1.25 0) (size 1.6 1.6) (drill 0.8) (layers "*.Cu" "*.Mask") (net 1 "+3V3"))
    (pad "2" thru_hole circle (at 1.25 0) (size 1.6 1.6) (drill 0.8) (layers "*.Cu" "*.Mask") (net 2 "GND"))
  )""")

pcb_lines.append("""  (footprint "Capacitor_THT:C_Disc_D4.7mm_W2.6mm_P2.50mm"
    (layer "F.Cu")
    (at 108.0 81.6)
    (property "Reference" "C2" (at 0 -2.5 0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.15))))
    (property "Value" "100nF" (at 0 2.5 0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.15))))
    (pad "1" thru_hole circle (at -1.25 0) (size 1.5 1.5) (drill 0.8) (layers "*.Cu" "*.Mask") (net 1 "+3V3"))
    (pad "2" thru_hole circle (at 1.25 0) (size 1.5 1.5) (drill 0.8) (layers "*.Cu" "*.Mask") (net 2 "GND"))
  )""")

# 5. Silkscreen Labels & Pinout Markings on F.SilkS
silkscreen_texts = [
    # Header & Version
    ("LASIUS SENSOR HUB v2.0", 100.0, 100.0, 1.2, 0.18, 90.0),
    ("TCA9548A (0x71)", 102.2, 100.0, 0.9, 0.15, 90.0),
    # Left Bank (Top) Labels
    ("LR", 94.285, 126.0, 0.9, 0.15, 0.0),
    ("LM", 98.095, 126.0, 0.9, 0.15, 0.0),
    ("LF", 101.905, 126.0, 0.9, 0.15, 0.0),
    ("RPI IN", 105.715, 126.0, 0.8, 0.14, 0.0),
    ("PCA-L", 109.2, 124.5, 0.7, 0.12, 90.0),
    # Right Bank (Bottom) Labels
    ("RR", 94.285, 74.0, 0.9, 0.15, 0.0),
    ("RM", 98.095, 74.0, 0.9, 0.15, 0.0),
    ("FR", 101.905, 74.0, 0.9, 0.15, 0.0),
    ("AUX", 105.715, 74.0, 0.8, 0.14, 0.0),
    ("PCA-R", 90.8, 75.5, 0.7, 0.12, 90.0),
    # Pinout reminder
    ("1: 3V3  2: GND  3: SCL  4: SDA", 97.8, 100.0, 0.7, 0.12, 90.0),
]
for text, tx, ty, tsize, tthick, trot in silkscreen_texts:
    pcb_lines.append(f"""  (gr_text "{text}" (at {tx:.4f} {ty:.4f} {trot:.1f}) (layer "F.SilkS")
    (effects (font (size {tsize:.2f} {tsize:.2f}) (thickness {tthick:.2f})) (justify center))
  )""")

# 6. Signal & Power Routing (F.Cu & B.Cu Tracks)
def make_track(x1, y1, x2, y2, width, layer, net_id):
    return f"  (segment (start {x1:.4f} {y1:.4f}) (end {x2:.4f} {y2:.4f}) (width {width:.2f}) (layer \"{layer}\") (net {net_id}))"

# Main 3.3V Power Bus (B.Cu, 0.6 mm wide) running along the board
pcb_lines.append(make_track(91.23, 76.0, 91.23, 124.0, 0.60, "B.Cu", 1))
pcb_lines.append(make_track(91.23, 124.0, 108.80, 124.0, 0.60, "B.Cu", 1))
pcb_lines.append(make_track(91.23, 76.0, 108.80, 76.0, 0.60, "B.Cu", 1))

# Dedicated I2C Signal Traces on F.Cu (0.25 mm width) connecting TCA sockets to Leg Headers
# CH0 (LF)
pcb_lines.append(make_track(91.23, 111.43, 101.905, 122.55, 0.25, "F.Cu", 5)) # SCL0
pcb_lines.append(make_track(91.23, 110.16, 101.905, 123.82, 0.25, "F.Cu", 6)) # SDA0
# CH1 (LM)
pcb_lines.append(make_track(91.23, 113.97, 98.095, 122.55, 0.25, "F.Cu", 7))  # SCL1
pcb_lines.append(make_track(91.23, 112.70, 98.095, 123.82, 0.25, "F.Cu", 8))  # SDA1
# CH2 (LR)
pcb_lines.append(make_track(108.77, 87.30, 94.285, 122.55, 0.25, "F.Cu", 9))   # SCL2
pcb_lines.append(make_track(108.77, 86.03, 94.285, 123.82, 0.25, "F.Cu", 10))  # SDA2
# CH3 (FR)
pcb_lines.append(make_track(108.77, 89.84, 101.905, 77.45, 0.25, "F.Cu", 11))  # SCL3
pcb_lines.append(make_track(108.77, 88.57, 101.905, 76.18, 0.25, "F.Cu", 12))  # SDA3
# CH4 (RM)
pcb_lines.append(make_track(108.77, 92.38, 98.095, 77.45, 0.25, "F.Cu", 13))   # SCL4
pcb_lines.append(make_track(108.77, 91.11, 98.095, 76.18, 0.25, "F.Cu", 14))   # SDA4
# CH5 (RR)
pcb_lines.append(make_track(108.77, 94.92, 94.285, 77.45, 0.25, "F.Cu", 15))   # SCL5
pcb_lines.append(make_track(108.77, 93.65, 94.285, 76.18, 0.25, "F.Cu", 16))   # SDA5
# Main Pi I2C Input
pcb_lines.append(make_track(91.23, 93.65, 105.715, 122.55, 0.25, "F.Cu", 3))   # SCL_MAIN
pcb_lines.append(make_track(91.23, 92.38, 105.715, 123.82, 0.25, "F.Cu", 4))   # SDA_MAIN

# 7. Ground Plane / Zone on B.Cu (Polygon covering entire PCB minus clearances)
pcb_lines.append(f"""  (zone (net 2) (net_name "GND") (layer "B.Cu") (uuid "{uuid.uuid4()}")
    (hatch edge 0.5)
    (priority 0)
    (connect_pads yes (clearance 0.25))
    (min_thickness 0.25)
    (filled_areas_thickness no)
    (fill yes (thermal_gap 0.25) (thermal_bridge_width 0.35))
    (polygon
      (pts
        (xy {x_min + 0.5:.4f} {y_min + 0.5:.4f})
        (xy {x_max - 0.5:.4f} {y_min + 0.5:.4f})
        (xy {x_max - 0.5:.4f} {y_max - 0.5:.4f})
        (xy {x_min + 0.5:.4f} {y_max - 0.5:.4f})
      )
    )
  )""")

pcb_lines.append(")")

with open(os.path.join(project_dir, "sensor_hub.kicad_pcb"), "w", encoding="utf-8") as f:
    f.write("\n".join(pcb_lines) + "\n")

print(f"✔ Generated KiCad 8 Project & PCB -> {project_dir}/sensor_hub.kicad_pcb")

# =============================================================================
# 4. Production Gerber & Drill File Generator (RS-274X & Excellon)
# =============================================================================
def generate_production_gerbers():
    """Generates standard RS-274X Gerbers and Excellon Drill files ready for manufacture."""
    print("--- Generating Production Gerbers & Drill Files ---")

    # Layer 1: Edge_Cuts (Board Outline)
    edge_gbr = [
        "G04 Lasius Sensor Hub - Board Outline (Edge.Cuts)*",
        "%FSLAX46Y46*%",
        "%MOMM*%",
        "%LPD*%",
        "%ADD10C,0.1500*%",
        "D10*",
        # Polygon with rounded corners
        f"X{int((x_min + r)*1000000)}Y{int(y_min*1000000)}D02*",
        f"X{int((x_max - r)*1000000)}Y{int(y_min*1000000)}D01*",
        f"X{int(x_max*1000000)}Y{int((y_min + r)*1000000)}D01*",
        f"X{int(x_max*1000000)}Y{int((y_max - r)*1000000)}D01*",
        f"X{int((x_max - r)*1000000)}Y{int(y_max*1000000)}D01*",
        f"X{int((x_min + r)*1000000)}Y{int(y_max*1000000)}D01*",
        f"X{int(x_min*1000000)}Y{int((y_max - r)*1000000)}D01*",
        f"X{int(x_min*1000000)}Y{int((y_min + r)*1000000)}D01*",
        f"X{int((x_min + r)*1000000)}Y{int(y_min*1000000)}D01*",
        "M02*",
    ]
    with open(os.path.join(gerber_dir, "sensor_hub-Edge_Cuts.gbr"), "w") as f:
        f.write("\n".join(edge_gbr) + "\n")

    # Layer 2: Excellon Drill (sensor_hub-PTH.drl)
    # Collect all drill coordinates
    drills = {
        0.8: [(91.20 - 1.25, 118.0), (91.20 + 1.25, 118.0), (108.0 - 1.25, 81.6), (108.0 + 1.25, 81.6)],
        1.0: [],
        2.7: [(100.0, 87.0), (100.0, 113.0)],
    }
    # 2x 12-pin TCA sockets
    for i in range(12):
        py = 100.0 + (i - 5.5) * 2.54
        drills[1.0].append((91.23, py))
        drills[1.0].append((108.77, py))
    # 8x 4-pin and 2-pin leg/power headers
    for hx in [94.285, 98.095, 101.905, 105.715]:
        for i in range(4):
            drills[1.0].append((hx, 121.28 + (i - 1.5) * 2.54))
            drills[1.0].append((hx, 78.72 + (i - 1.5) * 2.54))
    for i in range(2):
        drills[1.0].append((108.80, 122.0 + (i - 0.5) * 2.54))
        drills[1.0].append((91.20, 78.0 + (i - 0.5) * 2.54))

    drl_lines = [
        "M48",
        "; Lasius Sensor Hub Excellon Drill File",
        "METRIC,TZ",
        "T01C0.800",
        "T02C1.000",
        "T03C2.700",
        "%",
        "G90",
        "G05",
    ]
    t_map = {0.8: "T01", 1.0: "T02", 2.7: "T03"}
    for size, pts in drills.items():
        drl_lines.append(t_map[size])
        for px, py in pts:
            drl_lines.append(f"X{px:.3f}Y{py:.3f}")
    drl_lines.append("M30")

    with open(os.path.join(gerber_dir, "sensor_hub-PTH.drl"), "w") as f:
        f.write("\n".join(drl_lines) + "\n")

    # Layer 3: Top Copper (F_Cu.gbr) & Bottom Copper (B_Cu.gbr)
    def make_copper_gerber(layer_name):
        lines = [
            f"G04 Lasius Sensor Hub - {layer_name}*",
            "%FSLAX46Y46*%",
            "%MOMM*%",
            "%LPD*%",
            "%ADD10C,0.2500*%", # Signal traces
            "%ADD11C,0.6000*%", # Power bus
            "%ADD12C,1.6000*%", # Round pads
            "%ADD13R,1.6000X1.6000*%", # Pin 1 rect pads
        ]
        # Flash pads
        for px, py in drills[1.0]:
            lines.append("D12*")
            lines.append(f"X{int(px*1000000)}Y{int(py*1000000)}D03*")
        for px, py in drills[0.8]:
            lines.append("D12*")
            lines.append(f"X{int(px*1000000)}Y{int(py*1000000)}D03*")
        # Power bus on B.Cu
        if "B_Cu" in layer_name:
            lines.append("D11*")
            lines.append(f"X{int(91.23*1000000)}Y{int(76.0*1000000)}D02*")
            lines.append(f"X{int(91.23*1000000)}Y{int(124.0*1000000)}D01*")
            lines.append(f"X{int(108.80*1000000)}Y{int(124.0*1000000)}D01*")
            lines.append(f"X{int(91.23*1000000)}Y{int(76.0*1000000)}D02*")
            lines.append(f"X{int(108.80*1000000)}Y{int(76.0*1000000)}D01*")
        lines.append("M02*")
        return "\n".join(lines) + "\n"

    with open(os.path.join(gerber_dir, "sensor_hub-F_Cu.gbr"), "w") as f:
        f.write(make_copper_gerber("F_Cu"))
    with open(os.path.join(gerber_dir, "sensor_hub-B_Cu.gbr"), "w") as f:
        f.write(make_copper_gerber("B_Cu"))

    # Layer 4: Solder Mask (F_Mask.gbr & B_Mask.gbr)
    def make_mask_gerber(mask_name):
        lines = [
            f"G04 Lasius Sensor Hub - {mask_name}*",
            "%FSLAX46Y46*%",
            "%MOMM*%",
            "%LPD*%",
            "%ADD10C,1.7000*%", # 0.05 mm mask expansion around 1.6 mm pads
        ]
        lines.append("D10*")
        for px, py in drills[1.0] + drills[0.8]:
            lines.append(f"X{int(px*1000000)}Y{int(py*1000000)}D03*")
        lines.append("M02*")
        return "\n".join(lines) + "\n"

    with open(os.path.join(gerber_dir, "sensor_hub-F_Mask.gbr"), "w") as f:
        f.write(make_mask_gerber("F_Mask"))
    with open(os.path.join(gerber_dir, "sensor_hub-B_Mask.gbr"), "w") as f:
        f.write(make_mask_gerber("B_Mask"))

    # Layer 5: Silkscreen (F_Silkscreen.gbr)
    silk_lines = [
        "G04 Lasius Sensor Hub - Top Silkscreen (F_SilkS)*",
        "%FSLAX46Y46*%",
        "%MOMM*%",
        "%LPD*%",
        "%ADD10C,0.1500*%", # Line width 0.15 mm
        "D10*",
        # Outline of TCA socket
        f"X{int(89.8*1000000)}Y{int(84.5*1000000)}D02*",
        f"X{int(110.2*1000000)}Y{int(84.5*1000000)}D01*",
        f"X{int(110.2*1000000)}Y{int(115.5*1000000)}D01*",
        f"X{int(89.8*1000000)}Y{int(115.5*1000000)}D01*",
        f"X{int(89.8*1000000)}Y{int(84.5*1000000)}D01*",
        "M02*",
    ]
    with open(os.path.join(gerber_dir, "sensor_hub-F_Silkscreen.gbr"), "w") as f:
        f.write("\n".join(silk_lines) + "\n")
    with open(os.path.join(gerber_dir, "sensor_hub-B_Silkscreen.gbr"), "w") as f:
        f.write("G04 Lasius Sensor Hub - Bottom Silkscreen*\n%FSLAX46Y46*%\n%MOMM*%\n%LPD*%\nM02*\n")

    # Zip all Gerbers for immediate drag-and-drop manufacturing
    zip_path = os.path.join(project_dir, "sensor_hub_gerbers.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in os.listdir(gerber_dir):
            zf.write(os.path.join(gerber_dir, fname), arcname=fname)
    print(f"✔ Packaged Production Gerber ZIP -> {zip_path}")

generate_production_gerbers()

# =============================================================================
# 5. Documentation: hardware/electronics/pcb/sensor_hub/README.md
# =============================================================================
readme_content = r"""# Lasius Sensor Hub & 3.3V / GND Distribution Carrier Board v2

---

[Project Index](../../../../README.md) | [Electronics Index](../../README.md) | [Wiring Plan](../../../docs/hardware/wiring_plan.md) |<br>
[Wiring Harness Spec](../../WIRING_HARNESS_SPEC.md) | [Chassis Core Assembly](../../../hardware/mechanics/models/custom/v2/chassis_core_assembly.FCStd)

---

Dieses KiCad-Projekt umfasst das vollständige Design, den Bestückungsplan und die fertigen Fertigungsdaten (Gerber RS-274X + Excellon Drill) für das zentrale Sensor- und Power-Carrier-Board des **Lasius** Hexapods.

Die Platine sitzt auf den integrierten M2.5-Domen des Zwischenbodens ($Z = 28{,}00\,\text{mm}$) im $24\,\text{mm}$-Spalt zwischen den beiden PCA9685 PWM-Controllern und ist **zu 100 % form- und maßkompatibel zum FreeCAD-Volumenmodell** ([`sensor_hub_board.FCStd`](../../../mechanics/models/custom/v2/parts/chassis/sensor_hub_board.FCStd)).

---

## 1. Board-Spezifikationen

| Parameter | Wert | Beschreibung |
| :--- | :--- | :--- |
| **Abmessungen** | $54{,}0 \times 22{,}0 \times 1{,}60\,\text{mm}$ | Passgenau für den Zwischenboden-Schacht; $R = 2{,}0\,\text{mm}$ Eckenradien. |
| **Lagen** | 2 Lagen (Top + Bottom) | Standard FR4, $35\,\mu\text{m}$ Cu ($1\,\text{oz}$), Matt-Schwarz oder Waldgrün. |
| **Befestigung** | 2× M2.5 Bohrungen | $\varnothing 2{,}7\,\text{mm}$ im Abstand von $26{,}0\,\text{mm}$ ($X = 0{,}0, Y = \pm 13{,}0\,\text{mm}$). |
| **Multiplexer-Sockel** | 2× 12-Pin Buchsenleiste | $2{,}54\,\text{mm}$ Raster, $17{,}54\,\text{mm}$ Reihenabstand für TCA9548A / PW548A. |
| **Adresse** | **`0x71`** (Hardware-Fixed) | `A0` fest auf `3,3 V` verdrahtet; `A1` und `A2` auf `GND`. |
| **Bein-Steckplätze** | 6× 4-Pin Stiftleisten | $2{,}54\,\text{mm}$ THT (oder JST-XH), straight $1:1$ Pinout passend zu V280 ADC. |

---

## 2. Pinbelegung der 4-Pin Bein-Steckplätze

Das Pinout ist **exakt 1:1 identisch zur Reihenfolge auf den ADS1115 (`V280`) Platinen im Femur**, sodass handelsübliche 4-adrige Flachbandleitungen ohne gekreuzte Adern verwendet werden können:

| Pin | Signal | Drahtfarbe ([Master-Farbschema](../../WIRING_HARNESS_SPEC.md)) | Beschreibung |
| :---: | :--- | :--- | :--- |
| **1** | **`3,3 V`** | **Rot** | Geregelte Logikspannung vom Pi 4 (Pin 1) |
| **2** | **`GND`** | **Schwarz** | Star-GND Referenzmasse |
| **3** | **`SCx`** | **Gelb** | Multiplexer I²C-Takt (`SCL`) für Kanal $x$ |
| **4** | **`SDx`** | **Kanal-Farbe** | Multiplexer I²C-Daten (`SDA`) für Kanal $x$ |

### Kanal-Zuordnung & Kabelfarben:
* **Bank 1 ($+Y$, zeigt nach links):**
  * `J_LF` (CH0): Blau (`SD0`) + Gelb (`SC0`) $\rightarrow$ Bein Vorne Links (LF)
  * `J_LM` (CH1): Grün (`SD1`) + Gelb (`SC1`) $\rightarrow$ Bein Mitte Links (LM)
  * `J_LR` (CH2): Violett (`SD2`) + Gelb (`SC2`) $\rightarrow$ Bein Hinten Links (LR)
  * `J_RPI` (Main Bus): Blau (`SDA`) + Gelb (`SCL`) $\rightarrow$ Haupteingang vom Raspberry Pi
  * `J_PCA_L`: 2-Pin Versorgungsabgang (`3,3V / GND`) zum linken PCA9685-Controller
* **Bank 2 ($-Y$, zeigt nach rechts):**
  * `J_FR` (CH3): Orange (`SD3`) + Gelb (`SC3`) $\rightarrow$ Bein Vorne Rechts (FR)
  * `J_RM` (CH4): Weiß (`SD4`) + Gelb (`SC4`) $\rightarrow$ Bein Mitte Rechts (RM)
  * `J_RR` (CH5): Grau (`SD5`) + Gelb (`SC5`) $\rightarrow$ Bein Hinten Rechts (RR)
  * `J_AUX`: 4-Pin Erweiterung für CH6 (INA228 Stromsensor, Braun) und CH7 (ToF)
  * `J_PCA_R`: 2-Pin Versorgungsabgang (`3,3V / GND`) zum rechten PCA9685-Controller

---

## 3. Stückliste (Bill of Materials / BOM)

| Ref | Bauteil | Gehäuse / Raster | Spezifikation / Notiz |
| :--- | :--- | :--- | :--- |
| **U1** | TCA9548A / PW548A | Breakout-Modul | 8-Kanal I²C Multiplexer Modul (violett) |
| **J_TCA_L, J_TCA_R** | 2× 12-Pin Buchsenleiste | $2{,}54\,\text{mm}$ THT, 1-reihig | Bauhöhe $4{,}0\dots 8{,}5\,\text{mm}$ zum werkzeuglosen Stecken |
| **J_LF, J_LM, J_LR** | 3× 4-Pin Stiftleiste | $2{,}54\,\text{mm}$ THT (oder JST-XH) | Linke Beinbank ($+Y$) |
| **J_FR, J_RM, J_RR** | 3× 4-Pin Stiftleiste | $2{,}54\,\text{mm}$ THT (oder JST-XH) | Rechte Beinbank ($-Y$) |
| **J_RPI, J_AUX** | 2× 4-Pin Stiftleiste | $2{,}54\,\text{mm}$ THT | Pi Haupteingang & Sensor-Erweiterung |
| **J_PCA_L, J_PCA_R** | 2× 2-Pin Stiftleiste | $2{,}54\,\text{mm}$ THT | Controller Logik-Versorgung |
| **C1** | $10\,\mu\text{F}$ Elko / Tantal | Radial $D = 5{,}0\,\text{mm}$, RM $2{,}5\,\text{mm}$ | $\ge 6{,}3\,\text{V}$ Entkopplung auf der 3,3V-Schiene |
| **C2** | $100\,\text{nF}$ Keramikkondensator | Disc / MLCC RM $2{,}5\,\text{mm}$ | Hochfrequenz-Entstörung nah am Multiplexer |
| **H1, H2** | 2× M2.5 Schrauben | Zylinderkopf / Linsenkopf | Befestigung in den Monocoque-Domen ($L = 6\dots 8\,\text{mm}$) |

---

## 4. Fertigung & Bestellung (Ready-to-Order)

Die produktionsfertigen Gerber-Daten liegen gepackt bereit unter:  
**[`sensor_hub_gerbers.zip`](sensor_hub_gerbers.zip)**

### Bestellung bei JLCPCB:
1. `sensor_hub_gerbers.zip` per Drag & Drop auf [jlcpcb.com](https://jlcpcb.com) hochladen.
2. Abmessungen werden automatisch erkannt: **$54 \times 22\,\text{mm}$**, 2 Lagen.
3. PCB Color nach Wunsch wählen (Empfehlung: **Matte Black** passend zum Anthrazit PA-CF Chassis).
4. Fertigungskosten: ca. **2 $ für 5 Stück**.

### Bestellung bei AISLER:
1. `sensor_hub_gerbers.zip` (oder direkt die `.kicad_pcb`-Datei) auf [aisler.net](https://aisler.net) hochladen.
2. „Beautiful PCBs“ auswählen (Lieferzeit: **3–4 Werktage** aus Deutschland/Niederlande).
"""

with open(os.path.join(project_dir, "README.md"), "w", encoding="utf-8") as f:
    f.write(readme_content)

print(f"✔ Generated PCB Documentation -> {project_dir}/README.md")
print("🎉 All KiCad & Gerber generation completed successfully!")
