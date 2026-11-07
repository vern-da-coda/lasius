#!/usr/bin/env python3
"""
Generate 1:1 Scale Checking & Drilling Template (1:1 Papierschablone)
for Lasius Hexapod Tibia (Unterschenkel / Sichelkralle).
Calibrated for DIN A4 Landscape printing at 100% true scale.
Thickness: 7.0 mm | Standalone Servo holes: 4.0 mm | Centered Cable notch
"""

import json
import subprocess
import os

def create_tibia_schablone_svg():
    width_mm = 297.0
    height_mm = 210.0
    
    with open('/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/scripts/tibia_geom.json') as f:
        d = json.load(f)

    outer = d['outer_polygon']
    slot = d['slot_polygon']
    tip_x, tip_y = d.get('foot_tip', [-129.15, -14.41])
    
    ox = 224.0
    oy = 110.0
    
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
      <path d="M 10 2 L 0 5 L 10 8 z" fill="#2b6cb0"/>
    </marker>
    <marker id="arrow-end" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="4" markerHeight="4" orient="auto">
      <path d="M 0 2 L 10 5 L 0 8 z" fill="#2b6cb0"/>
    </marker>
    <style>
      .border {{ fill: none; stroke: #000; stroke-width: 0.35; }}
      .title {{ font-family: 'Liberation Sans', Arial, sans-serif; font-weight: bold; fill: #111; }}
      .subtitle {{ font-family: 'Liberation Sans', Arial, sans-serif; fill: #333; }}
      .note {{ font-family: 'Liberation Sans', Arial, sans-serif; fill: #b00; font-weight: bold; }}
      .part-solid {{ fill: #f8fafc; stroke: #000000; stroke-width: 0.45; stroke-linejoin: round; stroke-linecap: round; }}
      .part-cutout {{ fill: #ffffff; stroke: #000000; stroke-width: 0.35; stroke-linejoin: round; }}
      .centerline {{ stroke: #e53e3e; stroke-width: 0.2; stroke-dasharray: 4,0.8,0.8,0.8; }}
      .crosshair {{ stroke: #e53e3e; stroke-width: 0.25; }}
      .hole {{ fill: #ffffff; stroke: #000000; stroke-width: 0.35; }}
      .dim-line {{ stroke: #2b6cb0; stroke-width: 0.25; }}
      .dim-ext {{ stroke: #2b6cb0; stroke-width: 0.18; }}
      .dim-text {{ font-family: 'Liberation Sans', Arial, sans-serif; font-size: 2.2px; fill: #2b6cb0; text-anchor: middle; }}
      .dim-text-sm {{ font-family: 'Liberation Sans', Arial, sans-serif; font-size: 1.8px; fill: #2b6cb0; text-anchor: middle; }}
      .servo-overlay {{ fill: rgba(49, 130, 206, 0.08); stroke: #3182ce; stroke-width: 0.3; stroke-dasharray: 2,1; }}
      .horn-overlay {{ fill: rgba(221, 107, 32, 0.08); stroke: #dd6b20; stroke-width: 0.3; stroke-dasharray: 2,1; }}
      .kinematic-line {{ stroke: #38a169; stroke-width: 0.35; stroke-dasharray: 3,1; }}
      .kinematic-text {{ font-family: 'Liberation Sans', Arial, sans-serif; font-size: 2.3px; font-weight: bold; fill: #276749; text-anchor: middle; }}
      .ruler-tick {{ stroke: #000; stroke-width: 0.35; }}
      .ruler-text {{ font-family: 'Liberation Sans', Arial, sans-serif; font-size: 2.2px; fill: #000; text-anchor: middle; }}
    </style>
  </defs>

  <!-- Page Background & Margin Border -->
  <rect x="0" y="0" width="{width_mm}" height="{height_mm}" fill="#ffffff"/>
  <rect x="7" y="7" width="{width_mm - 14}" height="{height_mm - 14}" class="border"/>
  <rect x="8" y="8" width="{width_mm - 16}" height="{height_mm - 16}" fill="none" stroke="#e2e8f0" stroke-width="0.15"/>

  <!-- Header Title & Instructions -->
  <g transform="translate(14, 17)">
    <text x="0" y="0" class="title" font-size="5.2">LASIUS HEXAPOD — TIBIA (1:1 PAPIERSCHABLONE)</text>
    <text x="0" y="4.5" class="subtitle" font-size="2.6">Maßstabsgetreue 1:1 Prüf- &amp; Bohrschablone für Unterschenkel / Sichelkralle</text>
    <text x="0" y="8.5" class="subtitle" font-size="2.2">Plattendicke: 7.0 mm | Knie-Servo Torcster NR-645 MG BB (Ø 4.0 mm Bohrungen freistehend) | Kinematik L_DH = 130.0 mm</text>
  </g>

  <!-- Print Scale Warning Notice -->
  <g transform="translate(190, 16)">
    <rect x="-3" y="-3.5" width="96" height="15" fill="#fff5f5" stroke="#feb2b2" stroke-width="0.3" rx="1"/>
    <text x="0" y="0" class="note" font-size="2.4">DRUCKER-EINSTELLUNG: 100% (Tatsächliche Größe)</text>
    <text x="0" y="3.5" font-family="Liberation Sans, Arial" font-size="1.9" fill="#c53030">KEINE Seitenanpassung / "Fit to page" verwenden!</text>
    <text x="0" y="7.0" font-family="Liberation Sans, Arial" font-size="1.9" fill="#4a5568">Vor dem Bohren Kontrollmaßstab unten links mit Messschieber prüfen.</text>
  </g>

  <!-- 100mm Calibration Scale & 50mm Square (Bottom Left) -->
  <g transform="translate(14, 150)">
    <rect x="0" y="0" width="112" height="48" fill="#f7fafc" stroke="#cbd5e0" stroke-width="0.3" rx="1.5"/>
    <text x="5" y="6" class="title" font-size="2.8">1:1 KALIBRIERUNGS-KONTROLLE</text>
    
    <g transform="translate(6, 17)">
      <line x1="0" y1="0" x2="100" y2="0" stroke="#000" stroke-width="0.6"/>
''')

    for mm in range(0, 101):
        if mm % 10 == 0:
            h = 4.5
            svg.append(f'      <line x1="{mm}" y1="-{h}" x2="{mm}" y2="0" class="ruler-tick"/>\n')
            svg.append(f'      <text x="{mm}" y="-{h + 1.2}" class="ruler-text">{mm}</text>\n')
        elif mm % 5 == 0:
            h = 3.0
            svg.append(f'      <line x1="{mm}" y1="-{h}" x2="{mm}" y2="0" class="ruler-tick" stroke-width="0.25"/>\n')
        else:
            h = 1.8
            svg.append(f'      <line x1="{mm}" y1="-{h}" x2="{mm}" y2="0" class="ruler-tick" stroke-width="0.15"/>\n')

    svg.append(f'''      <text x="50" y="5.0" class="ruler-text" font-weight="bold">100.0 mm Referenzstrecke (mit Messschieber abmessen)</text>
    </g>

    <g transform="translate(6, 29)">
      <rect x="0" y="0" width="50" height="15" fill="#edf2f7" stroke="#4a5568" stroke-width="0.35"/>
      <text x="25" y="8" font-family="Liberation Sans, Arial" font-size="2.2" text-anchor="middle" fill="#2d3748">50.0 mm x 15.0 mm</text>
      <text x="25" y="12" font-family="Liberation Sans, Arial" font-size="1.8" text-anchor="middle" fill="#718096">Prüffeld Kontrollbox</text>
    </g>

    <g transform="translate(62, 33)">
      <text x="0" y="0" font-family="Liberation Sans, Arial" font-size="2.1" font-weight="bold" fill="#2d3748">Prüfkriterien:</text>
      <text x="0" y="3.8" font-family="Liberation Sans, Arial" font-size="1.9" fill="#4a5568">• Strecke 0–100 mm = exakt 100.0 mm</text>
      <text x="0" y="7.3" font-family="Liberation Sans, Arial" font-size="1.9" fill="#4a5568">• Boxbreite = exakt 50.0 mm</text>
      <text x="0" y="10.8" font-family="Liberation Sans, Arial" font-size="1.9" fill="#4a5568">• Tibia-Körperdicke = 7.0 mm</text>
    </g>
  </g>

  <!-- Technical Information & Checklist Table (Bottom Right) -->
  <g transform="translate(132, 150)">
    <rect x="0" y="0" width="151" height="48" fill="#f7fafc" stroke="#cbd5e0" stroke-width="0.3" rx="1.5"/>
    <text x="5" y="6" class="title" font-size="2.8">BAUTEIL-DATEN &amp; BOHRANWEISUNG</text>
    
    <g transform="translate(5, 12)">
      <text x="0" y="0" font-family="Liberation Sans, Arial" font-size="2.1" font-weight="bold" fill="#2b6cb0">Positions-Referenz:</text>
      <text x="0" y="3.5" font-family="Liberation Sans, Arial" font-size="1.9" fill="#4a5568">• Knie-Drehachse (Pivot) = Ursprung (0.0, 0.0) mm</text>
      <text x="0" y="7.0" font-family="Liberation Sans, Arial" font-size="1.9" fill="#4a5568">• Fußspitze (Tip) = (-129.15, -14.41) mm | Kinematik: 129.95 mm (nominal 130 mm)</text>
      <text x="0" y="10.5" font-family="Liberation Sans, Arial" font-size="1.9" fill="#4a5568">• Fuß-Schalter-/Stopper-Bohrung = (-93.00, -11.50) mm | Ø 3.0 mm (M3)</text>
      
      <text x="0" y="15.5" font-family="Liberation Sans, Arial" font-size="2.1" font-weight="bold" fill="#2b6cb0">Servo-Ausschnitt &amp; Verschraubung (Torcster NR-645 MG BB):</text>
      <text x="0" y="19.0" font-family="Liberation Sans, Arial" font-size="1.9" fill="#4a5568">• Fenster-Maß: 40.5 mm x 20.5 mm (X: -30.25..10.25, Y: -10.25..10.25)</text>
      <text x="0" y="22.5" font-family="Liberation Sans, Arial" font-size="1.9" fill="#4a5568">• Kabelauslass: 3.25 mm x 4.80 mm (mittig zwischen den beiden Bohrungen)</text>
      <text x="0" y="26.0" font-family="Liberation Sans, Arial" font-size="1.9" fill="#4a5568">• 4x Servo-Bohrungen: Pitch X = 48.50 mm, Pitch Y = 10.00 mm (freistehend)</text>
      <text x="0" y="29.5" font-family="Liberation Sans, Arial" font-size="1.9" fill="#4a5568">• Bohrung: Ø 4.0 mm Durchgang (glatt, ohne Senkung/Vertiefung)</text>
    </g>
  </g>

  <!-- ========================================================================= -->
  <!-- 1:1 TIBIA SCHABLONE (Hauptteil) -->
  <!-- ========================================================================= -->

  <!-- Outer Solid Contour -->
  <path d="{outer_d}" class="part-solid"/>

  <!-- Inner Sichelfenster Slot -->
  <path d="{slot_d}" class="part-cutout"/>
  <text x="{tx(-48.0):.2f}" y="{ty(13.0):.2f}" class="dim-text-sm" fill="#718096">Sichelfenster</text>

  <!-- Servo Window Cutout with Cable Notch -->
  <path d="{win_d}" class="part-cutout"/>

  <!-- Servo Torcster NR-645 MG BB Phantom Outline Overlay -->
  <rect x="{tx(-30.1):.2f}" y="{ty(10.05):.2f}" width="40.2" height="20.1" class="servo-overlay"/>
  <!-- Mounting tabs -->
  <rect x="{tx(-37.0):.2f}" y="{ty(9.5):.2f}" width="6.9" height="19.0" class="servo-overlay"/>
  <rect x="{tx(10.1):.2f}" y="{ty(9.5):.2f}" width="6.9" height="19.0" class="servo-overlay"/>
  <text x="{tx(-18.0):.2f}" y="{ty(-2.0):.2f}" font-family="Liberation Sans, Arial" font-size="2.1" fill="#2b6cb0" text-anchor="middle" font-weight="bold">Torcster NR-645 MG BB</text>

  <!-- Torcster Round Disc Horn Phantom Overlay at Knee Shaft (0, 0) -->
  <circle cx="{tx(0.0):.2f}" cy="{ty(0.0):.2f}" r="10.5" class="horn-overlay"/>
  <circle cx="{tx(0.0):.2f}" cy="{ty(0.0):.2f}" r="7.5" fill="none" stroke="#dd6b20" stroke-width="0.2" stroke-dasharray="1,1"/>
  <circle cx="{tx(0.0):.2f}" cy="{ty(0.0):.2f}" r="1.5" fill="#ffffff" stroke="#dd6b20" stroke-width="0.3"/>
  <text x="{tx(0.0):.2f}" y="{ty(0.0) + 14.5:.2f}" font-family="Liberation Sans, Arial" font-size="2.0" fill="#c05621" text-anchor="middle" font-weight="bold">Ruderscheibe Ø 21 mm</text>

  <!-- Knee Shaft Pivot (0, 0) Crosshairs -->
  <line x1="{tx(-7.0):.2f}" y1="{ty(0.0):.2f}" x2="{tx(7.0):.2f}" y2="{ty(0.0):.2f}" class="crosshair"/>
  <line x1="{tx(0.0):.2f}" y1="{ty(-7.0):.2f}" x2="{tx(0.0):.2f}" y2="{ty(7.0):.2f}" class="crosshair"/>
  <circle cx="{tx(0.0):.2f}" cy="{ty(0.0):.2f}" r="0.8" fill="#e53e3e"/>
  <text x="{tx(0.0):.2f}" y="{ty(0.0) - 7.5:.2f}" font-family="Liberation Sans, Arial" font-size="2.0" fill="#e53e3e" text-anchor="middle" font-weight="bold">Knie-Achse (0, 0)</text>

  <!-- Kinematic Length Line from Knee Pivot (0, 0) to Foot Tip -->
  <line x1="{tx(0.0):.2f}" y1="{ty(0.0):.2f}" x2="{tx(tip_x):.2f}" y2="{ty(tip_y):.2f}" class="kinematic-line"/>
  <g transform="translate({tx(tip_x / 2.0):.2f}, {ty(tip_y / 2.0):.2f}) rotate(-6.36)">
    <rect x="-30" y="-4.0" width="60" height="3.5" fill="rgba(255,255,255,0.9)"/>
    <text x="0" y="-1.5" class="kinematic-text">DH Kinematik-Länge L_tibia = 130.0 mm</text>
  </g>

  <!-- 4x Standalone Servo Mounting Holes (Ø 4.0 mm) -->
''')

    for x in [r_x, l_x]:
        for y in [hy0, hy1]:
            px = tx(x)
            py = ty(y)
            svg.append(f'  <circle cx="{px:.2f}" cy="{py:.2f}" r="{sh_dia/2.0:.2f}" class="hole"/>\n')
            svg.append(f'  <line x1="{px - 2.8:.2f}" y1="{py:.2f}" x2="{px + 2.8:.2f}" y2="{py:.2f}" class="crosshair"/>\n')
            svg.append(f'  <line x1="{px:.2f}" y1="{py - 2.8:.2f}" x2="{px:.2f}" y2="{py + 2.8:.2f}" class="crosshair"/>\n')

    fh_px = tx(fh_x)
    fh_py = ty(fh_y)
    svg.append(f'''
  <!-- Foot Accessory Hole (M3) -->
  <circle cx="{fh_px:.2f}" cy="{fh_py:.2f}" r="{fh_dia/2.0:.2f}" class="hole"/>
  <line x1="{fh_px - 3.0:.2f}" y1="{fh_py:.2f}" x2="{fh_px + 3.0:.2f}" y2="{fh_py:.2f}" class="crosshair"/>
  <line x1="{fh_px:.2f}" y1="{fh_py - 3.0:.2f}" x2="{fh_px:.2f}" y2="{fh_py + 3.0:.2f}" class="crosshair"/>
  <text x="{fh_px:.2f}" y="{fh_py + 5.5:.2f}" class="dim-text-sm" font-weight="bold">Ø 3.0 mm (M3)</text>
  <text x="{fh_px:.2f}" y="{fh_py + 8.0:.2f}" class="dim-text-sm" fill="#718096">Fußschalter</text>

  <!-- Foot Tip Marker -->
  <circle cx="{tx(tip_x):.2f}" cy="{ty(tip_y):.2f}" r="1.2" fill="#e53e3e"/>
  <circle cx="{tx(tip_x):.2f}" cy="{ty(tip_y):.2f}" r="3.0" fill="none" stroke="#e53e3e" stroke-width="0.3" stroke-dasharray="1,1"/>
  <text x="{tx(tip_x) - 2.0:.2f}" y="{ty(tip_y) + 6.5:.2f}" class="dim-text" font-weight="bold" text-anchor="end">Fußspitze</text>
  <text x="{tx(tip_x) - 2.0:.2f}" y="{ty(tip_y) + 9.0:.2f}" class="dim-text-sm" text-anchor="end">X = -129.2, Y = -14.4</text>

  <!-- Key Dimensions -->
  <!-- Servo hole pitch X = 48.50 mm -->
  <g transform="translate(0, {ty(hy0) - 10.0:.2f})">
    <line x1="{tx(l_x):.2f}" y1="0" x2="{tx(r_x):.2f}" y2="0" class="dim-line" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)"/>
    <line x1="{tx(l_x):.2f}" y1="-1.5" x2="{tx(l_x):.2f}" y2="8.0" class="dim-ext"/>
    <line x1="{tx(r_x):.2f}" y1="-1.5" x2="{tx(r_x):.2f}" y2="8.0" class="dim-ext"/>
    <text x="{tx((l_x + r_x)/2.0):.2f}" y="-1.5" class="dim-text" font-weight="bold">48.50 mm (Pitch X)</text>
  </g>

  <!-- Servo Pitch Y = 10.00 mm (right servo flange) -->
  <g transform="translate({tx(r_x) + 6.0:.2f}, 0)">
    <line x1="0" y1="{ty(hy0):.2f}" x2="0" y2="{ty(hy1):.2f}" class="dim-line" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)"/>
    <line x1="-4.0" y1="{ty(hy0):.2f}" x2="1.5" y2="{ty(hy0):.2f}" class="dim-ext"/>
    <line x1="-4.0" y1="{ty(hy1):.2f}" x2="1.5" y2="{ty(hy1):.2f}" class="dim-ext"/>
    <text x="3.0" y="{ty(0.0) + 0.8:.2f}" class="dim-text" text-anchor="start" font-weight="bold">10.00</text>
  </g>

  <!-- Window Length 40.5 mm (inside window upper half) -->
  <g transform="translate(0, {ty(5.0):.2f})">
    <line x1="{tx(sw_x0):.2f}" y1="0" x2="{tx(sw_x1):.2f}" y2="0" class="dim-line" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)"/>
    <line x1="{tx(sw_x0):.2f}" y1="-1.5" x2="{tx(sw_x0):.2f}" y2="1.5" class="dim-ext"/>
    <line x1="{tx(sw_x1):.2f}" y1="-1.5" x2="{tx(sw_x1):.2f}" y2="1.5" class="dim-ext"/>
    <rect x="{tx((sw_x0 + sw_x1)/2.0) - 18.0:.2f}" y="-3.2" width="36" height="4.5" fill="#ffffff"/>
    <text x="{tx((sw_x0 + sw_x1)/2.0):.2f}" y="0.2" class="dim-text">40.50 mm (Ausschnitt)</text>
  </g>

  <!-- Bottom Rail Thickness 4.0 mm -->
  <g transform="translate({tx(-22.0):.2f}, 0)">
    <line x1="0" y1="{ty(sw_y0):.2f}" x2="0" y2="{ty(-14.25):.2f}" class="dim-line" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)"/>
    <line x1="-2.0" y1="{ty(sw_y0):.2f}" x2="2.0" y2="{ty(sw_y0):.2f}" class="dim-ext"/>
    <line x1="-2.0" y1="{ty(-14.25):.2f}" x2="2.0" y2="{ty(-14.25):.2f}" class="dim-ext"/>
    <text x="3.5" y="{ty(-12.25) + 0.8:.2f}" class="dim-text-sm" text-anchor="start" font-weight="bold">4.0 mm Steg</text>
  </g>

  <!-- Callout for 4x Ø 4.0 mm Standalone Holes -->
  <g transform="translate({tx(r_x) + 5.0:.2f}, {ty(hy1) + 12.0:.2f})">
    <line x1="0" y1="0" x2="-3.0" y2="-9.5" class="dim-line" marker-end="url(#arrow-end)"/>
    <line x1="0" y1="0" x2="28.0" y2="0" class="dim-line"/>
    <text x="2.0" y="-1.5" class="dim-text" text-anchor="start" font-weight="bold">4x Ø 4.0 mm</text>
    <text x="2.0" y="2.0" class="dim-text-sm" text-anchor="start">freistehend (Bohrung allein)</text>
  </g>

  <!-- Cable Notch Callout between the two holes -->
  <g>
    <line x1="{tx(12.5):.2f}" y1="{ty(0.0):.2f}" x2="{tx(26.0):.2f}" y2="{ty(10.0):.2f}" class="dim-line" marker-start="url(#arrow-start)"/>
    <line x1="{tx(26.0):.2f}" y1="{ty(10.0):.2f}" x2="{tx(49.0):.2f}" y2="{ty(10.0):.2f}" class="dim-line"/>
    <text x="{tx(27.0):.2f}" y="{ty(10.0) - 1.2:.2f}" class="dim-text" text-anchor="start" font-weight="bold">Kabelauslass 3.25 x 4.8</text>
    <text x="{tx(27.0):.2f}" y="{ty(10.0) + 2.2:.2f}" class="dim-text-sm" text-anchor="start">mittig zw. Bohrungen</text>
  </g>

  <!-- Horns labels -->
  <text x="{tx(41.15) + 3.0:.2f}" y="{ty(19.22) + 0.8:.2f}" class="dim-text-sm" text-anchor="start">Oberer Sporn</text>
  <text x="{tx(22.0) + 3.0:.2f}" y="{ty(-8.0) + 0.8:.2f}" class="dim-text-sm" text-anchor="start">Unterer Sporn</text>

</svg>''')

    return "".join(svg)

def main():
    svg_content = create_tibia_schablone_svg()
    
    svg_path = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/drawings/templates/tibia_1to1_template.svg"
    pdf_path = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/drawings/templates/tibia_1to1_template.pdf"
    html_path = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/drawings/templates/tibia_1to1_template.html"
    
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
    
    png_cmd = ["pdftoppm", "-png", "-r", "150", pdf_path, "/home/bjoern/.gemini/antigravity-cli/brain/573b876a-e2e9-418d-b68d-88e20c56db98/tibia_1zu1_schablone_preview"]
    subprocess.run(png_cmd, check=True)
    print("Rendered PNG preview!")

if __name__ == "__main__":
    main()
