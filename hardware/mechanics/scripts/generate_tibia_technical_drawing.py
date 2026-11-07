#!/usr/bin/env python3
"""
Generate Fully Dimensioned Technical Drawing (DIN EN ISO)
for Lasius Hexapod Tibia (Unterschenkel / Sichelkralle).
Calibrated for DIN A4 Landscape printing at 100% true scale.
Thickness: 7.0 mm | Standalone Servo holes: 4.0 mm | Centered Cable notch
"""

import json
import subprocess
import os

def create_tibia_technische_zeichnung_svg():
    width_mm = 297.0
    height_mm = 210.0
    
    with open('/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/scripts/tibia_geom.json') as f:
        d = json.load(f)

    outer = d['outer_polygon']
    slot = d['slot_polygon']
    
    ox = 222.0
    oy = 82.0
    
    def tx(x):
        return ox + x
    def ty(y):
        return oy - y

    def pts_to_d(pts):
        cmds = [f"M {tx(pts[0][0]):.2f} {ty(pts[0][1]):.2f}"]
        for p in pts[1:]:
            cmds.append(f"L {tx(p[0]):.2f} {ty(p[1]):.2f}")
        cmds.append("Z")
        return " ".join(cmds)

    outer_d = pts_to_d(outer)
    slot_d = pts_to_d(slot)
    
    sw_x0, sw_x1 = d['servo_win_x']
    sw_y0, sw_y1 = d['servo_win_y']
    cn_x0, cn_x1 = d['cable_notch_x']
    cn_y0, cn_y1 = d['cable_notch_y']
    
    win_pts = [
        [sw_x0, sw_y0],
        [sw_x1, sw_y0],
        [sw_x1, cn_y0],
        [cn_x1, cn_y0],
        [cn_x1, cn_y1],
        [sw_x1, cn_y1],
        [sw_x1, sw_y1],
        [sw_x0, sw_y1]
    ]
    win_d = pts_to_d(win_pts)

    r_x = d['right_holes_x']
    l_x = d['left_holes_x']
    hy0, hy1 = d['holes_y']
    sh_dia = d['servo_hole_dia'] # 4.0 mm
    
    fh_x, fh_y = d['foot_hole']
    fh_dia = d['foot_hole_dia']
    thick = d['plate_thickness'] # 7.0 mm
    
    svg = []
    svg.append(f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" 
     width="{width_mm}mm" height="{height_mm}mm" 
     viewBox="0 0 {width_mm} {height_mm}">
  <defs>
    <!-- Arrowhead markers -->
    <marker id="arrow-start" viewBox="0 0 10 10" refX="0" refY="5" markerWidth="4" markerHeight="4" orient="auto">
      <path d="M 10 2 L 0 5 L 10 8 z" fill="#000000"/>
    </marker>
    <marker id="arrow-end" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="4" markerHeight="4" orient="auto">
      <path d="M 0 2 L 10 5 L 0 8 z" fill="#000000"/>
    </marker>
    <style>
      .border-outer {{ fill: none; stroke: #000; stroke-width: 0.5; }}
      .border-inner {{ fill: none; stroke: #000; stroke-width: 0.35; }}
      .grid-text {{ font-family: 'Liberation Sans', Arial, sans-serif; font-size: 2.2px; fill: #444; text-anchor: middle; }}
      .title {{ font-family: 'Liberation Sans', Arial, sans-serif; font-weight: bold; fill: #111; }}
      .subtitle {{ font-family: 'Liberation Sans', Arial, sans-serif; fill: #333; }}
      .part-solid {{ fill: #ffffff; stroke: #000000; stroke-width: 0.45; stroke-linejoin: round; stroke-linecap: round; }}
      .part-cutout {{ fill: #ffffff; stroke: #000000; stroke-width: 0.35; stroke-linejoin: round; }}
      .centerline {{ stroke: #e53e3e; stroke-width: 0.2; stroke-dasharray: 4,0.8,0.8,0.8; }}
      .crosshair {{ stroke: #e53e3e; stroke-width: 0.25; }}
      .hole {{ fill: #ffffff; stroke: #000000; stroke-width: 0.35; }}
      .dim-line {{ stroke: #000000; stroke-width: 0.22; }}
      .dim-ext {{ stroke: #000000; stroke-width: 0.18; }}
      .dim-text {{ font-family: 'Liberation Sans', Arial, sans-serif; font-size: 2.2px; fill: #000000; text-anchor: middle; }}
      .dim-text-sm {{ font-family: 'Liberation Sans', Arial, sans-serif; font-size: 1.8px; fill: #000000; text-anchor: middle; }}
      .table-text {{ font-family: 'Liberation Sans', Arial, sans-serif; font-size: 2.0px; fill: #222; }}
      .table-text-bold {{ font-family: 'Liberation Sans', Arial, sans-serif; font-size: 2.0px; font-weight: bold; fill: #000; }}
    </style>
  </defs>

  <!-- Background -->
  <rect x="0" y="0" width="{width_mm}" height="{height_mm}" fill="#ffffff"/>

  <!-- DIN Border Outer & Inner -->
  <rect x="5" y="5" width="{width_mm - 10}" height="{height_mm - 10}" class="border-outer"/>
  <rect x="10" y="10" width="{width_mm - 20}" height="{height_mm - 20}" class="border-inner"/>

  <!-- Grid Reference Labels (DIN ISO 5457) -->
  <g transform="translate(0, 8.5)">
    <text x="33" y="0" class="grid-text">1</text>
    <text x="80" y="0" class="grid-text">2</text>
    <text x="127" y="0" class="grid-text">3</text>
    <text x="174" y="0" class="grid-text">4</text>
    <text x="221" y="0" class="grid-text">5</text>
    <text x="268" y="0" class="grid-text">6</text>
  </g>
  <g transform="translate(0, {height_mm - 6.5})">
    <text x="33" y="0" class="grid-text">1</text>
    <text x="80" y="0" class="grid-text">2</text>
    <text x="127" y="0" class="grid-text">3</text>
    <text x="174" y="0" class="grid-text">4</text>
    <text x="221" y="0" class="grid-text">5</text>
    <text x="268" y="0" class="grid-text">6</text>
  </g>
  <g transform="translate(7.5, 0)">
    <text x="0" y="32" class="grid-text">A</text>
    <text x="0" y="80" class="grid-text">B</text>
    <text x="0" y="128" class="grid-text">C</text>
    <text x="0" y="176" class="grid-text">D</text>
  </g>
  <g transform="translate({width_mm - 7.5}, 0)">
    <text x="0" y="32" class="grid-text">A</text>
    <text x="0" y="80" class="grid-text">B</text>
    <text x="0" y="128" class="grid-text">C</text>
    <text x="0" y="176" class="grid-text">D</text>
  </g>

  <!-- ========================================================================= -->
  <!-- ANSICHT A: HAUPTANSICHT (DRAUFSICHT 1:1) -->
  <!-- ========================================================================= -->
  <g id="ansicht-a">
    <text x="15" y="20" class="title" font-size="3.5">ANSICHT A — HAUPTANSICHT (M 1:1)</text>

    <!-- Part Outer Solid -->
    <path d="{outer_d}" class="part-solid"/>

    <!-- Sichelfenster Cutout -->
    <path d="{slot_d}" class="part-cutout"/>

    <!-- Servo Cutout Window with Cable Notch (centered between holes) -->
    <path d="{win_d}" class="part-cutout"/>

    <!-- Knee Shaft Centerline & Crosshair -->
    <line x1="{tx(-8.0):.2f}" y1="{ty(0.0):.2f}" x2="{tx(8.0):.2f}" y2="{ty(0.0):.2f}" class="centerline"/>
    <line x1="{tx(0.0):.2f}" y1="{ty(-8.0):.2f}" x2="{tx(0.0):.2f}" y2="{ty(8.0):.2f}" class="centerline"/>
    <circle cx="{tx(0.0):.2f}" cy="{ty(0.0):.2f}" r="0.7" fill="#e53e3e"/>
    <text x="{tx(0.0) + 1.5:.2f}" y="{ty(0.0) + 5.0:.2f}" class="dim-text-sm" font-weight="bold" fill="#e53e3e" text-anchor="start">Knie-Achse (0,0)</text>

    <!-- 4x Standalone Servo Mounting Holes (Ø 4.0 mm durchgehend) -->
''')

    for x in [r_x, l_x]:
        for y in [hy0, hy1]:
            px = tx(x)
            py = ty(y)
            svg.append(f'    <circle cx="{px:.2f}" cy="{py:.2f}" r="{sh_dia/2.0:.2f}" class="hole"/>\n')
            svg.append(f'    <line x1="{px - 2.8:.2f}" y1="{py:.2f}" x2="{px + 2.8:.2f}" y2="{py:.2f}" class="crosshair"/>\n')
            svg.append(f'    <line x1="{px:.2f}" y1="{py - 2.8:.2f}" x2="{px:.2f}" y2="{py + 2.8:.2f}" class="crosshair"/>\n')

    fh_px = tx(fh_x)
    tip_x, tip_y = d.get('foot_tip', [-129.15, -14.41])
    fh_py = ty(fh_y)
    svg.append(f'''
    <!-- Foot Hole -->
    <circle cx="{fh_px:.2f}" cy="{fh_py:.2f}" r="{fh_dia/2.0:.2f}" class="hole"/>
    <line x1="{fh_px - 3.0:.2f}" y1="{fh_py:.2f}" x2="{fh_px + 3.0:.2f}" y2="{fh_py:.2f}" class="crosshair"/>
    <line x1="{fh_px:.2f}" y1="{fh_py - 3.0:.2f}" x2="{fh_px:.2f}" y2="{fh_py + 3.0:.2f}" class="crosshair"/>

    <!-- Foot Tip Point (Smooth rounded apex) -->
    <circle cx="{tx(tip_x):.2f}" cy="{ty(tip_y):.2f}" r="1.0" fill="#e53e3e"/>

    <!-- Kinematic Reference Dimension (130.00 mm) oriented left-to-right -->
    <line x1="{tx(0.0):.2f}" y1="{ty(0.0):.2f}" x2="{tx(tip_x):.2f}" y2="{ty(tip_y):.2f}" stroke="#38a169" stroke-width="0.3" stroke-dasharray="3,1"/>
    <g transform="translate({tx(tip_x / 2.0):.2f}, {ty(tip_y / 2.0):.2f}) rotate(-6.36)">
      <rect x="-30" y="-4.0" width="60" height="3.5" fill="#ffffff"/>
      <text x="0" y="-1.5" font-family="Liberation Sans, Arial" font-size="2.3" font-weight="bold" fill="#276749" text-anchor="middle">L_DH = 130.00 (Kinematic Nominal Span)</text>
    </g>

    <!-- DIMENSIONS -->
    <!-- Overall Length 170.30 mm -->
    <g transform="translate(0, {ty(38.4) - 9.0:.2f})">
      <line x1="{tx(tip_x):.2f}" y1="0" x2="{tx(41.15):.2f}" y2="0" class="dim-line" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)"/>
      <line x1="{tx(tip_x):.2f}" y1="-1.5" x2="{tx(tip_x):.2f}" y2="{ty(tip_y) - (ty(38.4) - 9.0):.2f}" class="dim-ext"/>
      <line x1="{tx(41.15):.2f}" y1="-1.5" x2="{tx(41.15):.2f}" y2="{ty(19.22) - (ty(38.4) - 9.0):.2f}" class="dim-ext"/>
      <text x="{tx((tip_x + 41.15)/2.0):.2f}" y="-2.0" class="dim-text" font-weight="bold">170.30 (Overall Length)</text>
    </g>

    <!-- Overall Height 57.65 mm -->
    <g transform="translate({tx(41.15) + 12.0:.2f}, 0)">
      <line x1="0" y1="{ty(38.4):.2f}" x2="0" y2="{ty(-19.25):.2f}" class="dim-line" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)"/>
      <line x1="-10.0" y1="{ty(38.4):.2f}" x2="1.5" y2="{ty(38.4):.2f}" class="dim-ext"/>
      <line x1="-15.0" y1="{ty(-19.25):.2f}" x2="1.5" y2="{ty(-19.25):.2f}" class="dim-ext"/>
      <text x="3.0" y="{ty(9.5) + 0.8:.2f}" class="dim-text" font-weight="bold" text-anchor="start">57.65</text>
    </g>

    <!-- Servo Pitch X = 48.50 mm (placed cleanly above) -->
    <g transform="translate(0, {ty(hy0) - 11.0:.2f})">
      <line x1="{tx(l_x):.2f}" y1="0" x2="{tx(r_x):.2f}" y2="0" class="dim-line" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)"/>
      <line x1="{tx(l_x):.2f}" y1="-1.0" x2="{tx(l_x):.2f}" y2="9.0" class="dim-ext"/>
      <line x1="{tx(r_x):.2f}" y1="-1.0" x2="{tx(r_x):.2f}" y2="9.0" class="dim-ext"/>
      <text x="{tx((l_x + r_x)/2.0):.2f}" y="-1.5" class="dim-text" font-weight="bold">48.50 ±0.1 (Pitch X)</text>
    </g>

    <!-- Offset Knee Pivot to Right Servo Holes = 14.15 mm -->
    <g transform="translate(0, {ty(hy0) - 18.0:.2f})">
      <line x1="{tx(0.0):.2f}" y1="0" x2="{tx(r_x):.2f}" y2="0" class="dim-line" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)"/>
      <line x1="{tx(0.0):.2f}" y1="-1.0" x2="{tx(0.0):.2f}" y2="{ty(0.0) - (ty(hy0) - 18.0):.2f}" class="dim-ext"/>
      <line x1="{tx(r_x):.2f}" y1="-1.0" x2="{tx(r_x):.2f}" y2="16.0" class="dim-ext"/>
      <text x="{tx(r_x / 2.0):.2f}" y="-1.5" class="dim-text">14.15</text>
    </g>

    <!-- Servo Pitch Y = 10.00 mm (right servo flange) -->
    <g transform="translate({tx(r_x) + 6.0:.2f}, 0)">
      <line x1="0" y1="{ty(hy0):.2f}" x2="0" y2="{ty(hy1):.2f}" class="dim-line" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)"/>
      <line x1="-4.0" y1="{ty(hy0):.2f}" x2="1.5" y2="{ty(hy0):.2f}" class="dim-ext"/>
      <line x1="-4.0" y1="{ty(hy1):.2f}" x2="1.5" y2="{ty(hy1):.2f}" class="dim-ext"/>
      <text x="3.0" y="{ty(0.0) + 0.8:.2f}" class="dim-text" font-weight="bold" text-anchor="start">10.00 ±0.1</text>
    </g>

    <!-- Servo Cutout Window Dimensions: 40.50 x 20.50 mm (inside window upper half) -->
    <g transform="translate(0, {ty(5.0):.2f})">
      <line x1="{tx(sw_x0):.2f}" y1="0" x2="{tx(sw_x1):.2f}" y2="0" class="dim-line" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)"/>
      <line x1="{tx(sw_x0):.2f}" y1="-1.5" x2="{tx(sw_x0):.2f}" y2="1.5" class="dim-ext"/>
      <line x1="{tx(sw_x1):.2f}" y1="-1.5" x2="{tx(sw_x1):.2f}" y2="1.5" class="dim-ext"/>
      <rect x="{tx((sw_x0 + sw_x1)/2.0) - 18.0:.2f}" y="-3.2" width="36" height="4.5" fill="#ffffff"/>
      <text x="{tx((sw_x0 + sw_x1)/2.0):.2f}" y="0.2" class="dim-text">40.50 (Ausschnitt)</text>
    </g>

    <!-- Window Height 20.50 mm (outside window left side) -->
    <g transform="translate({tx(sw_x0) - 5.0:.2f}, 0)">
      <line x1="0" y1="{ty(sw_y1):.2f}" x2="0" y2="{ty(sw_y0):.2f}" class="dim-line" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)"/>
      <line x1="-1.5" y1="{ty(sw_y1):.2f}" x2="3.5" y2="{ty(sw_y1):.2f}" class="dim-ext"/>
      <line x1="-1.5" y1="{ty(sw_y0):.2f}" x2="3.5" y2="{ty(sw_y0):.2f}" class="dim-ext"/>
      <text x="-3.0" y="{ty(0.0) + 0.8:.2f}" class="dim-text" text-anchor="end">20.50</text>
    </g>

    <!-- Bottom Rail Thickness 4.00 mm (below rail) -->
    <g transform="translate({tx(-15.0):.2f}, 0)">
      <line x1="0" y1="{ty(sw_y0):.2f}" x2="0" y2="{ty(-14.25):.2f}" class="dim-line" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)"/>
      <line x1="-2.0" y1="{ty(sw_y0):.2f}" x2="6.0" y2="{ty(sw_y0):.2f}" class="dim-ext"/>
      <line x1="-2.0" y1="{ty(-14.25):.2f}" x2="6.0" y2="{ty(-14.25):.2f}" class="dim-ext"/>
      <text x="8.0" y="{ty(-12.25) + 0.8:.2f}" class="dim-text-sm" text-anchor="start" font-weight="bold">4.00 Steg</text>
    </g>

    <!-- Cable Notch Dimensions (3.25 x 4.80 mm centered between holes) -->
    <g>
      <line x1="{tx(12.5):.2f}" y1="{ty(0.0):.2f}" x2="{tx(26.0):.2f}" y2="{ty(10.0):.2f}" class="dim-line" marker-start="url(#arrow-start)"/>
      <line x1="{tx(26.0):.2f}" y1="{ty(10.0):.2f}" x2="{tx(49.0):.2f}" y2="{ty(10.0):.2f}" class="dim-line"/>
      <text x="{tx(27.0):.2f}" y="{ty(10.0) - 1.2:.2f}" class="dim-text" text-anchor="start" font-weight="bold">Kabelauslass 3.25 x 4.80</text>
      <text x="{tx(27.0):.2f}" y="{ty(10.0) + 2.2:.2f}" class="dim-text-sm" text-anchor="start">mittig zw. Bohrungen</text>
    </g>

    <!-- Foot Hole Dimension Callout -->
    <g transform="translate({fh_px - 8.0:.2f}, {fh_py + 10.0:.2f})">
      <line x1="0" y1="0" x2="6.0" y2="-7.5" class="dim-line" marker-end="url(#arrow-end)"/>
      <line x1="0" y1="0" x2="-22.0" y2="0" class="dim-line"/>
      <text x="-23.0" y="-1.0" class="dim-text" text-anchor="end" font-weight="bold">Ø 3.00 (M3 Stopper)</text>
      <text x="-23.0" y="2.5" class="dim-text-sm" text-anchor="end">X = -93.00, Y = -11.50</text>
    </g>

    <!-- Servo Hole Callout (4x Ø 4.0 mm durchgehend, freistehend) -->
    <g transform="translate({tx(r_x) + 5.0:.2f}, {ty(hy1) + 12.0:.2f})">
      <line x1="0" y1="0" x2="-3.5" y2="-9.0" class="dim-line" marker-end="url(#arrow-end)"/>
      <line x1="0" y1="0" x2="32.0" y2="0" class="dim-line"/>
      <text x="2.0" y="-1.5" class="dim-text" text-anchor="start" font-weight="bold">4x Ø 4.00 Durchgang</text>
      <text x="2.0" y="2.0" class="dim-text-sm" text-anchor="start">freistehend (Bohrung allein)</text>
    </g>
  </g>

  <!-- ========================================================================= -->
  <!-- ANSICHT B: SEITENANSICHT & SCHNITT (M 1:1, DICKE = 7.00 mm) -->
  <!-- ========================================================================= -->
  <g id="ansicht-b" transform="translate(15, 122)">
    <text x="0" y="0" class="title" font-size="3.2">ANSICHT B — SEITENANSICHT / SCHNITT (M 1:1, DICKE 7.00 mm)</text>

    <!-- Profile Bar 170.26 mm long x 7.0 mm thick -->
    <rect x="0" y="5" width="170.26" height="7.0" fill="#edf2f7" stroke="#000000" stroke-width="0.45"/>
    
    <!-- Cutout representation for window -->
    <rect x="98.86" y="4.8" width="40.50" height="7.4" fill="#ffffff" stroke="#e53e3e" stroke-width="0.3" stroke-dasharray="1.5,1"/>
    
    <!-- 4x Through holes in side view -->
    <g transform="translate(0, 5)">
      <line x1="92.76" y1="0" x2="92.76" y2="7.0" stroke="#718096" stroke-width="0.3" stroke-dasharray="1.2,0.8"/>
      <line x1="96.76" y1="0" x2="96.76" y2="7.0" stroke="#718096" stroke-width="0.3" stroke-dasharray="1.2,0.8"/>
      <line x1="141.26" y1="0" x2="141.26" y2="7.0" stroke="#718096" stroke-width="0.3" stroke-dasharray="1.2,0.8"/>
      <line x1="145.26" y1="0" x2="145.26" y2="7.0" stroke="#718096" stroke-width="0.3" stroke-dasharray="1.2,0.8"/>
    </g>

    <!-- Dimension Plate Thickness 7.00 mm -->
    <g transform="translate(176, 0)">
      <line x1="0" y1="5" x2="0" y2="12" class="dim-line" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)"/>
      <line x1="-3.0" y1="5" x2="1.5" y2="5" class="dim-ext"/>
      <line x1="-3.0" y1="12" x2="1.5" y2="12" class="dim-ext"/>
      <text x="3.0" y="9.2" class="dim-text" font-weight="bold" text-anchor="start">7.00</text>
      <text x="3.0" y="12.2" class="dim-text-sm" text-anchor="start">Plattendicke</text>
    </g>

    <!-- Detail Through Hole Callout -->
    <g transform="translate(20, 18)">
      <text x="0" y="0" font-family="Liberation Sans, Arial" font-size="2.2" font-weight="bold" fill="#2b6cb0">Bore Cross-Section (4x Servo):</text>
      <rect x="0" y="3" width="22" height="7" fill="#edf2f7" stroke="#000000" stroke-width="0.35"/>
      <rect x="9" y="3" width="4.0" height="7" fill="#ffffff" stroke="#718096" stroke-width="0.25"/>
      <line x1="11" y1="1.5" x2="11" y2="11.5" class="centerline"/>
      <text x="28" y="6.0" class="dim-text-sm" text-anchor="start">• Bore Diameter: Ø 4.00 mm</text>
      <text x="28" y="8.8" class="dim-text-sm" text-anchor="start">• Execution: Smooth through-hole</text>
      <text x="28" y="11.6" class="dim-text-sm" text-anchor="start">• Countersink: NONE</text>
    </g>
  </g>

  <!-- ========================================================================= -->
  <!-- INSPECTION DIMENSIONS TABLE -->
  <!-- ========================================================================= -->
  <g id="prueftabelle" transform="translate(15, 158)">
    <rect x="0" y="0" width="128" height="40" fill="#f7fafc" stroke="#cbd5e0" stroke-width="0.3"/>
    
    <rect x="0" y="0" width="128" height="6.5" fill="#edf2f7" stroke="#cbd5e0" stroke-width="0.3"/>
    <text x="4" y="4.5" class="table-text-bold">Inspection Feature</text>
    <text x="56" y="4.5" class="table-text-bold">Target [mm]</text>
    <text x="82" y="4.5" class="table-text-bold">Tolerance</text>
    <text x="105" y="4.5" class="table-text-bold">Actual [mm]</text>

    <line x1="0" y1="13.0" x2="128" y2="13.0" stroke="#e2e8f0" stroke-width="0.25"/>
    <text x="4" y="10.8" class="table-text">1. Servo Hole Spacing X</text>
    <text x="56" y="10.8" class="table-text-bold">48.50 mm</text>
    <text x="82" y="10.8" class="table-text">±0.10 mm</text>
    <text x="105" y="10.8" class="table-text">[       ]</text>

    <line x1="0" y1="19.5" x2="128" y2="19.5" stroke="#e2e8f0" stroke-width="0.25"/>
    <text x="4" y="17.3" class="table-text">2. Servo Hole Spacing Y</text>
    <text x="56" y="17.3" class="table-text-bold">10.00 mm</text>
    <text x="82" y="17.3" class="table-text">±0.10 mm</text>
    <text x="105" y="17.3" class="table-text">[       ]</text>

    <line x1="0" y1="26.0" x2="128" y2="26.0" stroke="#e2e8f0" stroke-width="0.25"/>
    <text x="4" y="23.8" class="table-text">3. Servo Cutout L x W</text>
    <text x="56" y="23.8" class="table-text-bold">40.50 x 20.50 mm</text>
    <text x="82" y="23.8" class="table-text">±0.15 mm</text>
    <text x="105" y="23.8" class="table-text">[       ]</text>

    <line x1="0" y1="32.5" x2="128" y2="32.5" stroke="#e2e8f0" stroke-width="0.25"/>
    <text x="4" y="30.3" class="table-text">4. Knee Axis to Foot Tip (L_DH)</text>
    <text x="56" y="30.3" class="table-text-bold">130.00 mm</text>
    <text x="82" y="30.3" class="table-text">±0.25 mm</text>
    <text x="105" y="30.3" class="table-text">[       ]</text>

    <text x="4" y="36.8" class="table-text">5. Plate Thickness (Material)</text>
    <text x="56" y="36.8" class="table-text-bold">7.00 mm</text>
    <text x="82" y="36.8" class="table-text">±0.15 mm</text>
    <text x="105" y="36.8" class="table-text">[       ]</text>
  </g>

  <!-- ========================================================================= -->
  <!-- DIN ISO 7200 TITLE BLOCK -->
  <!-- ========================================================================= -->
  <g id="schriftfeld" transform="translate(148, 158)">
    <rect x="0" y="0" width="139" height="40" fill="#ffffff" stroke="#000000" stroke-width="0.35"/>
    
    <line x1="0" y1="8" x2="139" y2="8" stroke="#000" stroke-width="0.25"/>
    <line x1="0" y1="18" x2="139" y2="18" stroke="#000" stroke-width="0.25"/>
    <line x1="0" y1="28" x2="139" y2="28" stroke="#000" stroke-width="0.25"/>
    <line x1="0" y1="34" x2="139" y2="34" stroke="#000" stroke-width="0.25"/>

    <line x1="75" y1="0" x2="75" y2="18" stroke="#000" stroke-width="0.25"/>
    <line x1="105" y1="0" x2="105" y2="18" stroke="#000" stroke-width="0.25"/>
    <line x1="45" y1="28" x2="45" y2="40" stroke="#000" stroke-width="0.25"/>
    <line x1="90" y1="28" x2="90" y2="40" stroke="#000" stroke-width="0.25"/>

    <!-- Row 1 -->
    <text x="3" y="3.5" class="dim-text-sm" fill="#718096" text-anchor="start">Title</text>
    <text x="3" y="6.8" class="title" font-size="2.7">TIBIA (LOWER LIMB / SICKLE CLAW)</text>

    <text x="78" y="3.5" class="dim-text-sm" fill="#718096" text-anchor="start">Project / Robot</text>
    <text x="78" y="6.8" class="title" font-size="2.4">LASIUS HEXAPOD</text>

    <text x="108" y="3.5" class="dim-text-sm" fill="#718096" text-anchor="start">Scale</text>
    <text x="108" y="6.8" class="title" font-size="2.5">1:1 (DIN A4)</text>

    <!-- Row 2 -->
    <text x="3" y="11.5" class="dim-text-sm" fill="#718096" text-anchor="start">Drawing No.</text>
    <text x="3" y="15.5" font-family="Liberation Sans, Arial" font-size="2.7" font-weight="bold" fill="#000">LH-CAD-TIB-001</text>

    <text x="78" y="11.5" class="dim-text-sm" fill="#718096" text-anchor="start">Status</text>
    <text x="78" y="15.5" font-family="Liberation Sans, Arial" font-size="2.3" font-weight="bold" fill="#38a169">APPROVED (V1.2)</text>

    <text x="108" y="11.5" class="dim-text-sm" fill="#718096" text-anchor="start">Sheet</text>
    <text x="108" y="15.5" font-family="Liberation Sans, Arial" font-size="2.4" font-weight="bold" fill="#000">1 / 1</text>

    <!-- Row 3 -->
    <text x="3" y="21.5" class="dim-text-sm" fill="#718096" text-anchor="start">Material</text>
    <text x="3" y="25.5" font-family="Liberation Sans, Arial" font-size="2.4" font-weight="bold" fill="#000">CFRP / Aluminum / PETG (Thickness 7.00 mm)</text>

    <!-- Row 4 -->
    <text x="3" y="30.5" class="dim-text-sm" fill="#718096" text-anchor="start">General Tolerance</text>
    <text x="3" y="33.0" class="dim-text-sm" font-weight="bold" text-anchor="start">ISO 2768-m</text>

    <text x="48" y="30.5" class="dim-text-sm" fill="#718096" text-anchor="start">Author</text>
    <text x="48" y="33.0" class="dim-text-sm" font-weight="bold" text-anchor="start">DeepMind / Antigravity CAD</text>

    <text x="93" y="30.5" class="dim-text-sm" fill="#718096" text-anchor="start">Date</text>
    <text x="93" y="33.0" class="dim-text-sm" font-weight="bold" text-anchor="start">2026-11-05</text>

    <!-- Row 5 -->
    <text x="3" y="37.8" font-family="Liberation Sans, Arial" font-size="1.7" fill="#4a5568" text-anchor="start">Deburr edges. All dimensions in millimeters [mm]. ISO 16016 applies.</text>
  </g>

</svg>''')

    return "".join(svg)

def main():
    svg_content = create_tibia_technische_zeichnung_svg()
    
    svg_path = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/drawings/templates/tibia_technical_drawing.svg"
    pdf_path = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/drawings/templates/tibia_technical_drawing.pdf"
    html_path = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/drawings/templates/tibia_technical_drawing.html"
    
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print("Written SVG:", svg_path)
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@page {{
  size: A4 landscape;
  margin: 0;
}}
html, body {{
  margin: 0;
  padding: 0;
  width: 297mm;
  height: 210mm;
  overflow: hidden;
  background: #ffffff;
}}
svg {{
  width: 297mm;
  height: 210mm;
  display: block;
}}
</style>
</head>
<body>
{svg_content}
</body>
</html>"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    cmd = [
        "google-chrome",
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        html_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("Chrome exit code:", res.returncode)
    print("Written PDF:", pdf_path)
    
    png_cmd = ["pdftoppm", "-png", "-r", "150", pdf_path, "/home/bjoern/.gemini/antigravity-cli/brain/573b876a-e2e9-418d-b68d-88e20c56db98/tibia_technische_zeichnung_preview"]
    subprocess.run(png_cmd, check=True)
    print("Rendered PNG preview!")

if __name__ == "__main__":
    main()
