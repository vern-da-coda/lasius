#!/usr/bin/env python3
"""
Generate 1:1 Scale Drilling & Checking Template (1:1 Papierschablone)
for Lasius Hexapod Coxa Bracket.
Calibrated for DIN A4 Landscape printing at 100% true scale.
"""

import subprocess
import os

def create_schablone_svg():
    width_mm = 297.0
    height_mm = 210.0
    
    svg = []
    svg.append(f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" 
     width="{width_mm}mm" height="{height_mm}mm" 
     viewBox="0 0 {width_mm} {height_mm}">
  <defs>
    <style>
      .border {{ fill: none; stroke: #000; stroke-width: 0.35; }}
      .title {{ font-family: 'Liberation Sans', Arial, sans-serif; font-weight: bold; fill: #111; }}
      .subtitle {{ font-family: 'Liberation Sans', Arial, sans-serif; fill: #333; }}
      .note {{ font-family: 'Liberation Sans', Arial, sans-serif; fill: #b00; font-weight: bold; }}
      .part-solid {{ fill: #f8fafc; stroke: #000000; stroke-width: 0.45; stroke-linejoin: round; stroke-linecap: round; }}
      .part-cutout {{ fill: #ffffff; stroke: #000000; stroke-width: 0.35; stroke-linejoin: round; }}
      .part-recess {{ fill: #edf2f7; stroke: #4a5568; stroke-width: 0.25; stroke-dasharray: 1.5,1; }}
      .centerline {{ stroke: #e53e3e; stroke-width: 0.2; stroke-dasharray: 4,0.8,0.8,0.8; }}
      .crosshair {{ stroke: #e53e3e; stroke-width: 0.25; }}
      .hole {{ fill: #ffffff; stroke: #000000; stroke-width: 0.35; }}
      .dim-line {{ stroke: #2b6cb0; stroke-width: 0.25; }}
      .dim-text {{ font-family: 'Liberation Sans', Arial, sans-serif; font-size: 2.2px; fill: #2b6cb0; text-anchor: middle; }}
      .dim-text-sm {{ font-family: 'Liberation Sans', Arial, sans-serif; font-size: 1.9px; fill: #2b6cb0; text-anchor: middle; }}
      .servo-overlay {{ fill: rgba(49, 130, 206, 0.08); stroke: #3182ce; stroke-width: 0.3; stroke-dasharray: 2,1; }}
      .horn-overlay {{ fill: rgba(221, 107, 32, 0.08); stroke: #dd6b20; stroke-width: 0.3; stroke-dasharray: 2,1; }}
      .ruler-tick {{ stroke: #000; stroke-width: 0.35; }}
      .ruler-text {{ font-family: 'Liberation Sans', Arial, sans-serif; font-size: 2.2px; fill: #000; text-anchor: middle; }}
    </style>
  </defs>

  <!-- Page Background & Frame -->
  <rect x="0" y="0" width="{width_mm}" height="{height_mm}" fill="#ffffff"/>
  <rect x="7" y="7" width="{width_mm - 14}" height="{height_mm - 14}" class="border"/>
  <rect x="8" y="8" width="{width_mm - 16}" height="{height_mm - 16}" fill="none" stroke="#ddd" stroke-width="0.15"/>

  <!-- Header Title & Instructions -->
  <g transform="translate(14, 17)">
    <text x="0" y="0" class="title" font-size="5.0">LASIUS HEXAPOD — COXA BRACKET (1:1 PAPIERSCHABLONE)</text>
    <text x="0" y="4.2" class="subtitle" font-size="2.5">Maßstabsgetreue 1:1 Prüf- &amp; Bohrschablone für Torcster NR-645 MG BB (59g) / Hitec HS-645MG</text>
    <rect x="0" y="6.8" width="269" height="11.5" fill="#fff5f5" stroke="#feb2b2" stroke-width="0.3" rx="1"/>
    <text x="3" y="10.5" class="note" font-size="2.4">DRUCKANWEISUNG (WICHTIG FÜR EXAKTE 1:1 GRÖßE):</text>
    <text x="3" y="14.2" class="subtitle" font-size="2.2">1. Im Druckdialog zwingend „Tatsächliche Größe“ oder „Skalierung 100%“ wählen! (Keinesfalls „An Seite anpassen“ / „Fit to Page“!)</text>
    <text x="3" y="17.0" class="subtitle" font-size="2.2">2. Druckkontrolle: Die beiden Kontrollmaßstäbe unten sofort mit dem Messschieber prüfen (Soll: exakt 100,0 mm bzw. 50,0 mm).</text>
  </g>

  <!-- 100 mm & 50 mm Calibration Check Scales (Bottom Left) -->
  <g transform="translate(14, 192)">
    <text x="0" y="-3.5" class="title" font-size="2.5">KONTROLLMASSSTAB 100,0 mm (Mit Messschieber prüfen):</text>
    <line x1="0" y1="0" x2="100" y2="0" stroke="#000" stroke-width="0.6"/>
    <line x1="0" y1="-3" x2="0" y2="3" class="ruler-tick" stroke-width="0.6"/>
    <line x1="100" y1="-3" x2="100" y2="3" class="ruler-tick" stroke-width="0.6"/>
''')
    for tick in range(10, 100, 10):
        h = 2.2 if tick % 50 == 0 else 1.5
        svg.append(f'    <line x1="{tick}" y1="{-h}" x2="{tick}" y2="{h}" class="ruler-tick"/>\n')
        svg.append(f'    <text x="{tick}" y="4.5" class="ruler-text">{tick}</text>\n')
    svg.append('''    <text x="0" y="4.5" class="ruler-text">0</text>
    <text x="100" y="4.5" class="ruler-text" font-weight="bold">100 mm</text>
  </g>

  <g transform="translate(126, 192)">
    <text x="0" y="-3.5" class="title" font-size="2.5">VERTIKALMASSSTAB 50,0 mm:</text>
    <line x1="0" y1="0" x2="50" y2="0" stroke="#000" stroke-width="0.6"/>
    <line x1="0" y1="-3" x2="0" y2="3" class="ruler-tick" stroke-width="0.6"/>
    <line x1="50" y1="-3" x2="50" y2="3" class="ruler-tick" stroke-width="0.6"/>
''')
    for tick in range(10, 50, 10):
        svg.append(f'    <line x1="{tick}" y1="-1.5" x2="{tick}" y2="1.5" class="ruler-tick"/>\n')
        svg.append(f'    <text x="{tick}" y="4.5" class="ruler-text">{tick}</text>\n')
    svg.append('''    <text x="0" y="4.5" class="ruler-text">0</text>
    <text x="50" y="4.5" class="ruler-text" font-weight="bold">50 mm</text>
  </g>

  <!-- Legend Box -->
  <g transform="translate(186, 187)">
    <rect x="0" y="0" width="97" height="15" fill="#f8fafc" stroke="#cbd5e0" stroke-width="0.3" rx="1"/>
    <text x="3" y="4" class="title" font-size="2.3">LEGENDE:</text>
    <line x1="3" y1="7.5" x2="12" y2="7.5" stroke="#000" stroke-width="0.5"/>
    <text x="14" y="8.5" class="subtitle" font-size="2.0">3D-Druck Bauteilkanten</text>
    <line x1="3" y1="12" x2="12" y2="12" stroke="#3182ce" stroke-width="0.4" stroke-dasharray="2,1"/>
    <text x="14" y="13" class="subtitle" font-size="2.0" fill="#2b6cb0">Servo 1 Kontur (Femur)</text>
    <line x1="50" y1="12" x2="59" y2="12" stroke="#dd6b20" stroke-width="0.4" stroke-dasharray="2,1"/>
    <text x="61" y="13" class="subtitle" font-size="2.0" fill="#c05621">Servo 2 / Scheibe (Coxa)</text>
  </g>
''')

    # View 1: TOP VIEW (Draufsicht M 1:1)
    vx1 = 18.0
    vy1 = 50.0
    svg.append(f'''
  <!-- VIEW 1: DRAUFSICHT (1:1) -->
  <g transform="translate({vx1}, {vy1})">
    <text x="0" y="-7" class="title" font-size="3.0">1. DRAUFSICHT (M 1:1) — Servo 1 (Femur) Schacht &amp; U-Gabel</text>
    <text x="0" y="-3.5" class="subtitle" font-size="2.1">Draufsicht von oben (+Z). Zeigt Servo 1 Montagebohrungen, Schacht und U-Gabel Öffnung.</text>

    <!-- Outer contour: 115 x 30.5 -->
    <path d="M 0,0 L 115,0 L 115,30.5 L 107.3,30.5 L 107.3,5.0 L 66.0,5.0 L 66.0,30.5 L 0,30.5 Z" class="part-solid"/>

    <!-- Servo Flange Recess (ear_recess: X=0..57.4, Y=5.0..25.5) -->
    <rect x="0" y="5.0" width="57.4" height="20.5" class="part-recess"/>

    <!-- Servo Window Cutout (servo_win: X=8.0..48.5, Y=5.0..25.5) -->
    <rect x="8.0" y="5.0" width="40.5" height="20.5" class="part-cutout"/>

    <!-- Tab Protrusion under tab (X=7.2..25.7) -->
    <line x1="7.2" y1="0" x2="7.2" y2="5.0" stroke="#a0aec0" stroke-width="0.2" stroke-dasharray="1,1"/>
    <line x1="25.7" y1="0" x2="25.7" y2="5.0" stroke="#a0aec0" stroke-width="0.2" stroke-dasharray="1,1"/>
    <line x1="7.2" y1="25.5" x2="7.2" y2="30.5" stroke="#a0aec0" stroke-width="0.2" stroke-dasharray="1,1"/>
    <line x1="25.7" y1="25.5" x2="25.7" y2="30.5" stroke="#a0aec0" stroke-width="0.2" stroke-dasharray="1,1"/>

    <!-- Coxa Pivot Axis Line (X=74.70) -->
    <line x1="74.7" y1="-2" x2="74.7" y2="33.0" class="centerline"/>
    <text x="74.7" y="35.5" class="dim-text" font-size="2.0">Drehachse X=74.7</text>

    <!-- 4x Servo 1 Mounting Holes (X=4.65, 53.15; Y=10.25, 20.25; dia=2.2) -->
''')
    for sx in [4.65, 53.15]:
        for sy in [10.25, 20.25]:
            svg.append(f'    <circle cx="{sx}" cy="{sy}" r="1.1" class="hole"/>\n')
            svg.append(f'    <line x1="{sx - 2.0}" y1="{sy}" x2="{sx + 2.0}" y2="{sy}" class="crosshair"/>\n')
            svg.append(f'    <line x1="{sx}" y1="{sy - 2.0}" x2="{sx}" y2="{sy + 2.0}" class="crosshair"/>\n')

    svg.append(f'''
    <!-- Tab Pivot Hole / Shaft Axis (X=18.2, Y=15.25, dia=3.5) -->
    <circle cx="18.2" cy="15.25" r="1.75" class="hole" stroke-dasharray="1.5,1"/>
    <line x1="15.0" y1="15.25" x2="21.4" y2="15.25" class="crosshair"/>
    <line x1="18.2" y1="12.0" x2="18.2" y2="18.5" class="crosshair"/>
    <text x="18.2" y="22.5" class="dim-text-sm">Ø3,5 Gegenlager</text>

    <!-- OVERLAY: Torcster NR-645 MG BB Servo 1 Footprint (Cyan/Blue dashed) -->
    <rect x="8.15" y="5.2" width="40.2" height="20.1" class="servo-overlay"/>
    <rect x="1.25" y="5.35" width="54.0" height="19.8" class="servo-overlay" rx="1.5"/>
    <circle cx="18.2" cy="15.25" r="3.0" fill="none" stroke="#3182ce" stroke-width="0.35" stroke-dasharray="1.5,0.8"/>

    <!-- Key Dimension Annotations -->
    <text x="28.9" y="3.2" class="dim-text">Lochabstand: 48,50 mm</text>
    <line x1="4.65" y1="3.8" x2="53.15" y2="3.8" class="dim-line"/>
    <line x1="4.65" y1="2.3" x2="4.65" y2="5.3" class="dim-line"/>
    <line x1="53.15" y1="2.3" x2="53.15" y2="5.3" class="dim-line"/>

    <text x="117" y="15.25" class="dim-text" text-anchor="start">Breite: 30,5 mm</text>
    <text x="86.65" y="15.25" class="dim-text">U-Gabel Weite: 41,3 mm</text>
  </g>
''')

    # View 2: FRONT VIEW (Vorderansicht M 1:1)
    vx2 = 18.0
    vy2 = 116.0
    svg.append(f'''
  <!-- VIEW 2: VORDERANSICHT (1:1) -->
  <g transform="translate({vx2}, {vy2})">
    <text x="0" y="-7" class="title" font-size="3.0">2. VORDERANSICHT (M 1:1) — Lasche &amp; Coxa Pivot Drehachse</text>
    <text x="0" y="-3.5" class="subtitle" font-size="2.1">Blick auf Stegseite (Y=0). Zeigt Gesamthöhe, Laschenüberstand nach unten und Drehachsenbohrung Ø4.2.</text>

    <!-- Front Contour with lower tab -->
    <path d="M 0,0 L 115,0 L 115,19.0 L 25.7,19.0 L 25.7,34.0 L 7.2,34.0 L 7.2,19.0 L 0,19.0 Z" class="part-solid"/>

    <!-- Tab solid bottom thickness (3.0 mm) -->
    <rect x="7.2" y="31.0" width="18.5" height="3.0" fill="#edf2f7" stroke="#718096" stroke-width="0.25"/>

    <!-- Cable Outlet open tunnel on left of tab -->
    <line x1="7.2" y1="19.0" x2="7.2" y2="31.0" stroke="#e53e3e" stroke-width="0.6" stroke-dasharray="1.5,1"/>
    <text x="5.0" y="25.5" class="dim-text-sm" text-anchor="end" fill="#e53e3e">Kabelauslass (offen)</text>

    <!-- Coxa Pivot Hole (X=74.70, Z=9.5; dia=4.2) -->
    <circle cx="74.70" cy="9.5" r="2.1" class="hole"/>
    <line x1="71.0" y1="9.5" x2="78.4" y2="9.5" class="crosshair"/>
    <line x1="74.70" y1="6.0" x2="74.70" y2="13.0" class="crosshair"/>
    <text x="74.70" y="4.5" class="dim-text">Pivot Bohrung Ø4,2</text>

    <!-- Servo 1 Tab counter bearing hole axis (X=18.2) -->
    <line x1="18.2" y1="30.0" x2="18.2" y2="35.5" class="crosshair"/>
    <text x="18.2" y="38.0" class="dim-text-sm">Gegenlager Ø3,5 (X=18.2)</text>

    <!-- Dimensions in Front View -->
    <text x="57.5" y="-1.8" class="dim-text">Gesamtlänge: 115,0 mm</text>
    <line x1="0" y1="-0.8" x2="115" y2="-0.8" class="dim-line"/>
    <line x1="0" y1="-2.0" x2="0" y2="0.5" class="dim-line"/>
    <line x1="115" y1="-2.0" x2="115" y2="0.5" class="dim-line"/>

    <text x="117" y="10.0" class="dim-text" text-anchor="start">Höhe: 19,0 mm</text>
    <text x="28.5" y="27.0" class="dim-text" text-anchor="start">Lasche: 15,0 mm (Gesamt: 34,0 mm)</text>
  </g>
''')

    # View 3: BACK VIEW (Rückansicht M 1:1)
    vx3 = 156.0
    vy3 = 50.0
    svg.append(f'''
  <!-- VIEW 3: RÜCKANSICHT (1:1) — SERVO 2 MONTAGE -->
  <g transform="translate({vx3}, {vy3})">
    <text x="0" y="-7" class="title" font-size="3.0">3. RÜCKANSICHT (M 1:1) — Servo 2 (Coxa) Verschraubung</text>
    <text x="0" y="-3.5" class="subtitle" font-size="2.1">Blick auf Rückseite (Y=30.5). Zeigt die 4x M3-Kernlochbohrungen für den Coxa-Servo.</text>

    <!-- Solid Back Face with U-fork opening cutout -->
    <path d="M 0,0 L 66.0,0 L 66.0,19.0 L 25.7,19.0 L 25.7,34.0 L 7.2,34.0 L 7.2,19.0 L 0,19.0 Z" class="part-solid"/>
    <rect x="66.0" y="0" width="41.3" height="19.0" fill="#f1f5f9" stroke="#cbd5e0" stroke-width="0.3"/>
    <rect x="107.3" y="0" width="7.7" height="19.0" class="part-solid"/>

    <!-- Coxa Pivot Hole visible through U-fork (X=74.70, Z=9.5) -->
    <circle cx="74.70" cy="9.5" r="2.1" fill="none" stroke="#718096" stroke-width="0.3" stroke-dasharray="1,1"/>
    <line x1="71.0" y1="9.5" x2="78.4" y2="9.5" class="crosshair"/>
    <line x1="74.70" y1="6.0" x2="74.70" y2="13.0" class="crosshair"/>

    <!-- 4x Servo 2 Mounting Holes (X=60.55, 109.05; Z=4.5, 14.5; dia=2.8) -->
''')
    for hx in [60.55, 109.05]:
        for hz in [4.5, 14.5]:
            svg.append(f'    <circle cx="{hx}" cy="{hz}" r="1.4" class="hole"/>\n')
            svg.append(f'    <line x1="{hx - 2.0}" y1="{hz}" x2="{hx + 2.0}" y2="{hz}" class="crosshair"/>\n')
            svg.append(f'    <line x1="{hx}" y1="{hz - 2.0}" x2="{hx}" y2="{hz + 2.0}" class="crosshair"/>\n')

    svg.append(f'''
    <!-- Hole Labels -->
    <text x="60.55" y="2.5" class="dim-text-sm">X=60.55</text>
    <text x="109.05" y="2.5" class="dim-text-sm">X=109.05</text>

    <!-- Pitch Dimension 48.5 mm -->
    <text x="84.8" y="-1.8" class="dim-text" font-weight="bold">Lochabstand: 48,50 mm</text>
    <line x1="60.55" y1="-0.8" x2="109.05" y2="-0.8" class="dim-line"/>
    <line x1="60.55" y1="-2.0" x2="60.55" y2="0.5" class="dim-line"/>
    <line x1="109.05" y1="-2.0" x2="109.05" y2="0.5" class="dim-line"/>

    <!-- Vertical Pitch 10.0 mm -->
    <text x="117.0" y="10.0" class="dim-text" text-anchor="start">Raster: 10,0 mm</text>

    <!-- OVERLAY: Torcster Servo 2 Outline & Round Servo Horn (from user photo!) -->
    <rect x="64.8" y="-0.5" width="40.2" height="20.0" class="horn-overlay" rx="1"/>
    <circle cx="74.70" cy="9.5" r="12.25" class="horn-overlay"/>
    <circle cx="74.70" cy="9.5" r="5.5" fill="none" stroke="#dd6b20" stroke-width="0.3" stroke-dasharray="1.5,1"/>
    <circle cx="74.70" cy="9.5" r="1.5" fill="none" stroke="#dd6b20" stroke-width="0.35"/>
    <text x="74.70" y="24.5" class="dim-text" fill="#c05621">Torcster Servoscheibe Ø24,5 mm</text>
  </g>
''')

    # View 4: DETAIL TAB BOTTOM VIEW (Unteransicht Lasche M 1:1)
    vx4 = 150.0
    vy4 = 122.0
    svg.append(f'''
  <!-- VIEW 4: UNTERANSICHT LASCHE (1:1) -->
  <g transform="translate({vx4}, {vy4})">
    <text x="0" y="-7" class="title" font-size="3.0">4. UNTERANSICHT LASCHE (M 1:1)</text>
    <text x="0" y="-3.5" class="subtitle" font-size="2.0">Blick von unten auf geschlossene Lasche (Z=-15).</text>

    <!-- Tab outer footprint: 18.5 x 30.5 -->
    <rect x="0" y="0" width="18.5" height="30.5" class="part-solid"/>

    <!-- Cable Outlet indicator at X=0 (left) -->
    <line x1="0" y1="5.0" x2="0" y2="25.5" stroke="#e53e3e" stroke-width="0.6"/>
    <text x="-1.5" y="16.0" class="dim-text-sm" text-anchor="end" fill="#e53e3e">Kabelauslass</text>

    <!-- Center hole: X=11.0 from left edge of tab, Y=15.25 -->
    <circle cx="11.0" cy="15.25" r="1.75" class="hole"/>
    <line x1="7.0" y1="15.25" x2="15.0" y2="15.25" class="crosshair"/>
    <line x1="11.0" y1="11.25" x2="11.0" y2="19.25" class="crosshair"/>
    <text x="11.0" y="24.0" class="dim-text-sm">Gegenlager Ø3,5 mm</text>
    <text x="9.25" y="34.0" class="dim-text-sm">Länge: 18,5 mm</text>
  </g>
''')

    # View 5: 3D ISOMETRIC PREVIEW
    vx5 = 205.0
    vy5 = 122.0
    svg.append(f'''
  <!-- VIEW 5: 3D-ISOMETRIE ÜBERSICHT -->
  <g transform="translate({vx5}, {vy5})">
    <text x="0" y="-7" class="title" font-size="3.0">5. 3D-ISOMETRIE</text>
    <text x="0" y="-3.5" class="subtitle" font-size="2.0">Räumliche Ansicht der neuen Geometrie</text>

    <!-- Clean Vector Isometric Wireframe -->
    <g transform="translate(10, 4) scale(0.68)">
      <!-- Base Main Outline -->
      <polygon points="10,25 90,-15 110,-5 30,35" fill="#f8fafc" stroke="#000" stroke-width="0.5"/>
      <polygon points="10,25 30,35 30,55 10,45" fill="#e2e8f0" stroke="#000" stroke-width="0.5"/>
      <polygon points="30,35 110,-5 110,15 30,55" fill="#edf2f7" stroke="#000" stroke-width="0.5"/>
      <!-- Lower Tab downwards -->
      <polygon points="16,28 32,20 32,45 16,53" fill="#cbd5e0" stroke="#000" stroke-width="0.5"/>
      <polygon points="16,53 32,45 38,48 22,56" fill="#e2e8f0" stroke="#000" stroke-width="0.5"/>
      <!-- Servo 1 Cutout -->
      <polygon points="18,22 52,5 57,7.5 23,24.5" fill="#ffffff" stroke="#000" stroke-width="0.4"/>
      <!-- U-Fork Cutout -->
      <polygon points="68,-3 98,-18 103,-15.5 73,-0.5" fill="#ffffff" stroke="#000" stroke-width="0.4"/>
      <!-- Pivot Hole on front rail -->
      <ellipse cx="78" cy="22" rx="2.5" ry="3.5" fill="#ffffff" stroke="#000" stroke-width="0.4"/>
    </g>
  </g>
''')

    svg.append('</svg>\n')
    return "".join(svg)

if __name__ == "__main__":
    svg_content = create_schablone_svg()
    svg_path = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/drawings/templates/coxa_bracket_1to1_template.svg"
    html_path = "/tmp/coxa_schablone_wrapper.html"
    pdf_path = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/drawings/templates/coxa_bracket_1to1_template.pdf"
    
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print("Written:", svg_path)

    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@page {{
  size: 297mm 210mm;
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
