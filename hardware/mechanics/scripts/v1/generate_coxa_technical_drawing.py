#!/usr/bin/env python3
"""
Generate Fully Dimensioned Technical Drawing (DIN EN ISO)
for Lasius Hexapod Coxa Bracket.
Calibrated for DIN A4 Landscape printing at 100% true scale.
"""

import subprocess
import os

def create_technische_zeichnung_svg():
    width_mm = 297.0
    height_mm = 210.0
    
    svg = []
    svg.append(f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" 
     width="{width_mm}mm" height="{height_mm}mm" 
     viewBox="0 0 {width_mm} {height_mm}">
  <defs>
    <!-- Arrowhead markers for dimension lines -->
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
      .part-hidden {{ fill: none; stroke: #718096; stroke-width: 0.25; stroke-dasharray: 1.2,0.8; }}
      .centerline {{ stroke: #e53e3e; stroke-width: 0.2; stroke-dasharray: 4,0.8,0.8,0.8; }}
      .crosshair {{ stroke: #e53e3e; stroke-width: 0.22; }}
      .hole {{ fill: #ffffff; stroke: #000000; stroke-width: 0.35; }}
      .dim-line {{ stroke: #000000; stroke-width: 0.22; }}
      .dim-ext {{ stroke: #000000; stroke-width: 0.18; }}
      .dim-text {{ font-family: 'Liberation Sans', Arial, sans-serif; font-size: 2.1px; fill: #000000; text-anchor: middle; }}
      .dim-text-sm {{ font-family: 'Liberation Sans', Arial, sans-serif; font-size: 1.8px; fill: #000000; text-anchor: middle; }}
      .table-text {{ font-family: 'Liberation Sans', Arial, sans-serif; font-size: 2.0px; fill: #222; }}
      .table-text-bold {{ font-family: 'Liberation Sans', Arial, sans-serif; font-size: 2.0px; font-weight: bold; fill: #000; }}
    </style>
  </defs>

  <!-- Background -->
  <rect x="0" y="0" width="{width_mm}" height="{height_mm}" fill="#ffffff"/>

  <!-- Standard Drawing Border: 20 mm left (binding margin), 7 mm top, right, bottom -->
  <rect x="20" y="7" width="270" height="196" class="border-outer"/>
  <rect x="20" y="7" width="270" height="196" class="border-inner"/>

  <!-- Grid References: Letters A-D vertically, Numbers 1-6 horizontally -->
''')

    col_w = 270 / 6.0  # 45 mm per column
    row_h = 196 / 4.0  # 49 mm per row

    for i, num in enumerate(["1", "2", "3", "4", "5", "6"]):
        cx = 20 + i * col_w + col_w / 2
        svg.append(f'  <text x="{cx}" y="5.2" class="grid-text">{num}</text>\n')
        svg.append(f'  <text x="{cx}" y="206.0" class="grid-text">{num}</text>\n')
    for j, letter in enumerate(["A", "B", "C", "D"]):
        cy = 7 + j * row_h + row_h / 2 + 0.8
        svg.append(f'  <text x="17.5" y="{cy}" class="grid-text">{letter}</text>\n')
        svg.append(f'  <text x="292.5" y="{cy}" class="grid-text">{letter}</text>\n')

    # Helper function for horizontal dimensions
    def draw_dim_h(x1, x2, y, text, ext_y1=None, ext_y2=None, is_inner=False, text_above=True):
        res = []
        if ext_y1 is not None and ext_y2 is not None:
            res.append(f'<line x1="{x1}" y1="{ext_y1}" x2="{x1}" y2="{ext_y2}" class="dim-ext"/>')
            res.append(f'<line x1="{x2}" y1="{ext_y1}" x2="{x2}" y2="{ext_y2}" class="dim-ext"/>')
        
        mid_x = (x1 + x2) / 2
        text_y = y - 0.9 if text_above else y + 2.4
        
        if not is_inner:
            res.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" class="dim-line" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)"/>')
        else:
            res.append(f'<line x1="{x1 - 4}" y1="{y}" x2="{x1}" y2="{y}" class="dim-line" marker-end="url(#arrow-end)"/>')
            res.append(f'<line x1="{x2 + 4}" y1="{y}" x2="{x2}" y2="{y}" class="dim-line" marker-end="url(#arrow-start)"/>')
            res.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" class="dim-line"/>')
        
        res.append(f'<text x="{mid_x}" y="{text_y}" class="dim-text">{text}</text>')
        return "\n    ".join(res)

    # Helper function for vertical dimensions (CORRECTED y1, y2 attributes!)
    def draw_dim_v(y1, y2, x, text, ext_x1=None, ext_x2=None, is_inner=False, text_left=True):
        res = []
        if ext_x1 is not None and ext_x2 is not None:
            res.append(f'<line x1="{ext_x1}" y1="{y1}" x2="{ext_x2}" y2="{y1}" class="dim-ext"/>')
            res.append(f'<line x1="{ext_x1}" y1="{y2}" x2="{ext_x2}" y2="{y2}" class="dim-ext"/>')
        
        mid_y = (y1 + y2) / 2
        text_x = x - 1.2 if text_left else x + 1.2
        anchor = "end" if text_left else "start"
        
        if not is_inner:
            res.append(f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" class="dim-line" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)"/>')
        else:
            res.append(f'<line x1="{x}" y1="{y1 - 3}" x2="{x}" y2="{y1}" class="dim-line" marker-end="url(#arrow-end)"/>')
            res.append(f'<line x1="{x}" y1="{y2 + 3}" x2="{x}" y2="{y2}" class="dim-line" marker-end="url(#arrow-start)"/>')
            res.append(f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" class="dim-line"/>')
        
        res.append(f'<text x="{text_x}" y="{mid_y + 0.8}" class="dim-text" text-anchor="{anchor}">{text}</text>')
        return "\n    ".join(res)

    # ==========================================
    # VIEW 1: DRAUFSICHT (M 1:1)
    # Origin: (38, 34)
    # Dimensions: 115 x 30.5
    # ==========================================
    v1_x = 38.0
    v1_y = 34.0
    svg.append(f'''
  <!-- VIEW 1: DRAUFSICHT (M 1:1) -->
  <g transform="translate({v1_x}, {v1_y})">
    <text x="0" y="-15" class="title" font-size="3.2">DRAUFSICHT (M 1:1)</text>

    <!-- Outer Part Contour with U-Fork cutout -->
    <path d="M 0,0 L 115,0 L 115,30.5 L 107.3,30.5 L 107.3,5.0 L 66.0,5.0 L 66.0,30.5 L 0,30.5 Z" class="part-solid"/>

    <!-- Servo Recess (X=0..57.4, Y=5.0..25.5) -->
    <rect x="0" y="5.0" width="57.4" height="20.5" class="part-hidden"/>

    <!-- Servo Window Cutout (X=8.0..48.5, Y=5.0..25.5) -->
    <rect x="8.0" y="5.0" width="40.5" height="20.5" class="part-solid"/>

    <!-- Centerlines -->
    <line x1="-3" y1="15.25" x2="60" y2="15.25" class="centerline"/>
    <line x1="74.7" y1="-3" x2="74.7" y2="33.5" class="centerline"/>
    <line x1="18.2" y1="-3" x2="18.2" y2="33.5" class="centerline"/>

    <!-- Tab Bearing Hole Ø3.5 (coaxial with Servo 1 shaft) -->
    <circle cx="18.2" cy="15.25" r="1.75" class="hole"/>
    <line x1="15.0" y1="15.25" x2="21.4" y2="15.25" class="crosshair"/>
    <line x1="18.2" y1="12.0" x2="18.2" y2="18.5" class="crosshair"/>

    <!-- 4x Servo 1 Mounting Holes (Ø2.2) -->
''')
    for sx in [4.65, 53.15]:
        for sy in [10.25, 20.25]:
            svg.append(f'    <circle cx="{sx}" cy="{sy}" r="1.1" class="hole"/>\n')
            svg.append(f'    <line x1="{sx - 1.8}" y1="{sy}" x2="{sx + 1.8}" y2="{sy}" class="crosshair"/>\n')
            svg.append(f'    <line x1="{sx}" y1="{sy - 1.8}" x2="{sx}" y2="{sy + 1.8}" class="crosshair"/>\n')

    # Dimensions for View 1
    dim1 = draw_dim_h(0, 115, -11.5, "115.0 ±0.2", -13.0, 2)
    dim2 = draw_dim_h(8.0, 48.5, -6.8, "40.5 (Servo Window)", -8.0, 6.0)
    dim3 = draw_dim_h(4.65, 53.15, -2.2, "48.50 ±0.1 (Hole Spacing)", -3.5, 11)
    dim4 = draw_dim_h(66.0, 107.3, -6.8, "41.3 (U-Fork Opening)", -8.0, 6.0)
    
    # Left Dimensions (Y):
    dim_w1 = draw_dim_v(0, 30.5, -8.5, "30.5", 0, -10.0)
    dim_w2 = draw_dim_v(5.0, 25.5, -3.0, "20.5", 4.0, -4.5)
    dim_pitch_y = draw_dim_v(10.25, 20.25, 55.5, "10.0 ±0.1", 52.0, 57.0, text_left=False)

    # Bottom Dimensions:
    dim_pivot_x = draw_dim_h(0, 74.7, 34.5, "74.70 (Pivot Axis Pos)", 28, 36.0, text_above=False)
    dim_steg_y = draw_dim_v(0, 5.0, 118.5, "5.0 (Rib)", 114, 120, text_left=False)

    svg.append(f'''
    <!-- View 1 Dimension Lines -->
    {dim1}
    {dim2}
    {dim3}
    {dim4}
    {dim_w1}
    {dim_w2}
    {dim_pitch_y}
    {dim_pivot_x}
    {dim_steg_y}

    <!-- Wall thicknesses annotations -->
    <text x="61.7" y="3.5" class="dim-text-sm">8.6</text>
    <text x="111.15" y="3.5" class="dim-text-sm">7.7</text>
    <text x="18.2" y="8.0" class="dim-text-sm">Ø3.5 (Counter-Bearing)</text>
    <text x="4.65" y="27.5" class="dim-text-sm">4x Ø2.2 (M2/M2.2)</text>
  </g>
''')

    # ==========================================
    # VIEW 2: FRONT VIEW (Scale 1:1)
    # Origin: (38, 96)
    # Dimensions: 115 x 34
    # ==========================================
    v2_x = 38.0
    v2_y = 96.0
    svg.append(f'''
  <!-- VIEW 2: FRONT VIEW (Scale 1:1) -->
  <g transform="translate({v2_x}, {v2_y})">
    <text x="0" y="-7" class="title" font-size="3.2">FRONT VIEW (Scale 1:1)</text>

    <!-- Contour with lower tab -->
    <path d="M 0,0 L 115,0 L 115,19.0 L 25.7,19.0 L 25.7,34.0 L 7.2,34.0 L 7.2,19.0 L 0,19.0 Z" class="part-solid"/>

    <!-- Tab solid bottom base (Z=31..34, thickness 3.0) -->
    <rect x="7.2" y="31.0" width="18.5" height="3.0" fill="#edf2f7" stroke="#000000" stroke-width="0.35"/>

    <!-- Open Cable Outlet on left of tab -->
    <line x1="7.2" y1="19.0" x2="7.2" y2="31.0" stroke="#e53e3e" stroke-width="0.5" stroke-dasharray="1.5,1"/>
    <text x="5.5" y="25.5" class="dim-text-sm" text-anchor="end" fill="#e53e3e">Cable Outlet (Open)</text>

    <!-- Centerlines -->
    <line x1="60" y1="9.5" x2="90" y2="9.5" class="centerline"/>
    <line x1="74.7" y1="3" x2="74.7" y2="16" class="centerline"/>

    <!-- Coxa Pivot Hole Ø4.2 continuous through-hole at X=74.7, Z=9.5 -->
    <circle cx="74.7" cy="9.5" r="2.1" class="hole"/>
    <line x1="71.2" y1="9.5" x2="78.2" y2="9.5" class="crosshair"/>
    <line x1="74.7" y1="6.0" x2="74.7" y2="13.0" class="crosshair"/>

    <!-- Tab Counter-bearing hole axis (X=18.2) -->
    <line x1="18.2" y1="28.0" x2="18.2" y2="36.0" class="centerline"/>

    <!-- Dimensions in View 2 -->
''')
    dim_h_body = draw_dim_v(0, 19.0, -4.5, "19.0", 0, -6.0)
    dim_h_tab = draw_dim_v(19.0, 34.0, -4.5, "15.0", 7.2, -6.0)
    dim_h_tot = draw_dim_v(0, 34.0, -9.5, "34.0 ±0.2", 0, -11.0)
    dim_tab_len = draw_dim_h(7.2, 25.7, 37.5, "18.5 (Tab)", 33.0, 39.5, text_above=True)
    dim_tab_thick = draw_dim_v(31.0, 34.0, 28.5, "3.0", 25.7, 30.5, text_left=False)
    dim_pivot_z = draw_dim_v(0, 9.5, 118.5, "9.5", 114, 120, text_left=False)

    svg.append(f'''
    <!-- View 2 Dimension Lines -->
    {dim_h_body}
    {dim_h_tab}
    {dim_h_tot}
    {dim_tab_len}
    {dim_tab_thick}
    {dim_pivot_z}

    <!-- Leader Line to Pivot Hole -->
    <text x="74.7" y="-2.0" class="dim-text">Ø4.2 Through-Hole (Pivot)</text>
    <line x1="74.7" y1="-1.0" x2="74.7" y2="6.8" stroke="#000" stroke-width="0.2"/>

    <text x="18.2" y="42.5" class="dim-text-sm">Ø3.5 Counter-Bearing Bore</text>
  </g>
''')

    # ==========================================
    # VIEW 3: REAR VIEW (Scale 1:1) — SERVO 2
    # Origin: (166, 32)
    # Dimensions: 115 x 34
    # ==========================================
    v3_x = 166.0
    v3_y = 32.0
    svg.append(f'''
  <!-- VIEW 3: REAR VIEW (Scale 1:1) — SERVO 2 MOUNT -->
  <g transform="translate({v3_x}, {v3_y})">
    <text x="0" y="-12" class="title" font-size="3.2">REAR VIEW (Scale 1:1) — SERVO 2 (COXA)</text>
    <text x="0" y="-8.5" class="subtitle" font-size="2.1">View of rear face (Y=30.5). Calibrated for NR-645 MG BB (48.5 x 10.0 mm pattern).</text>

    <!-- Solid Back Face with U-fork opening cutout -->
    <path d="M 0,0 L 66.0,0 L 66.0,19.0 L 25.7,19.0 L 25.7,34.0 L 7.2,34.0 L 7.2,19.0 L 0,19.0 Z" class="part-solid"/>
    <rect x="66.0" y="0" width="41.3" height="19.0" fill="#f8fafc" stroke="#718096" stroke-width="0.3"/>
    <rect x="107.3" y="0" width="7.7" height="19.0" class="part-solid"/>

    <!-- Coxa Pivot Hole visible in background (X=74.7, Z=9.5) -->
    <circle cx="74.7" cy="9.5" r="2.1" fill="none" stroke="#718096" stroke-width="0.3" stroke-dasharray="1.2,0.8"/>
    <line x1="71.0" y1="9.5" x2="78.4" y2="9.5" class="centerline"/>
    <line x1="74.7" y1="6.0" x2="74.7" y2="13.0" class="centerline"/>

    <!-- 4x Servo 2 Mounting Holes (X=60.55, 109.05; Z=4.5, 14.5; dia=2.8) -->
''')
    for hx in [60.55, 109.05]:
        for hz in [4.5, 14.5]:
            svg.append(f'    <circle cx="{hx}" cy="{hz}" r="1.4" class="hole"/>\n')
            svg.append(f'    <line x1="{hx - 2.0}" y1="{hz}" x2="{hx + 2.0}" y2="{hz}" class="crosshair"/>\n')
            svg.append(f'    <line x1="{hx}" y1="{hz - 2.0}" x2="{hx}" y2="{hz + 2.0}" class="crosshair"/>\n')

    dim_s2_x = draw_dim_h(60.55, 109.05, -3.5, "48.50 ±0.1 (Hole Spacing)", -5.0, 5.0)
    dim_s2_lever = draw_dim_h(60.55, 74.70, 22.0, "14.15 (Output Offset)", 15.5, 23.5, text_above=False)
    dim_s2_z = draw_dim_v(4.5, 14.5, 118.5, "10.0 ±0.1", 108, 120, text_left=False)

    svg.append(f'''
    <!-- View 3 Dimensions -->
    {dim_s2_x}
    {dim_s2_lever}
    {dim_s2_z}

    <text x="60.55" y="2.5" class="dim-text-sm">X=60.55</text>
    <text x="109.05" y="2.5" class="dim-text-sm">X=109.05</text>
    <text x="84.8" y="16.5" class="dim-text-sm" fill="#b7791f">Coaxial Alignment:</text>
    <text x="84.8" y="19.0" class="dim-text-sm" fill="#b7791f">60.55 + 14.15 = 74.70 mm (Pivot Axis)</text>
    <text x="109.05" y="28.0" class="dim-text-sm">4x Ø2.8 (M3 Core Hole)</text>
  </g>
''')

    # ==========================================
    # VIEW 4: 3D ISOMETRIC DETAIL
    # Origin: (166, 78)
    # ==========================================
    v4_x = 166.0
    v4_y = 78.0
    svg.append(f'''
  <!-- VIEW 4: 3D ISOMETRIC (Scale 0.75:1) -->
  <g transform="translate({v4_x}, {v4_y})">
    <text x="0" y="-2" class="title" font-size="3.2">3D ISOMETRIC (Scale 0.75:1)</text>

    <g transform="translate(18, 10) scale(0.72)">
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

    <!-- Key Design Highlights Box -->
    <rect x="0" y="38" width="117" height="15" fill="#f0fff4" stroke="#9ae6b4" stroke-width="0.3" rx="1"/>
    <text x="3" y="42" class="table-text-bold" fill="#22543d">Design Highlights (Rev 3):</text>
    <text x="3" y="45.5" class="table-text" fill="#276749">• Stress-relief: Solid 5.0 mm rib &amp; reinforced base</text>
    <text x="3" y="48.5" class="table-text" fill="#276749">• Servo 1 cable outlet open to left (unobstructed routing)</text>
    <text x="3" y="51.5" class="table-text" fill="#276749">• Coaxial alignment: Coxa servo shaft &amp; pivot axis at X = 74.70 mm</text>
  </g>
''')

    # ==========================================
    # CALIPER CHECK MEASUREMENT TABLE
    # Bottom Left: (28, 142)
    # ==========================================
    svg.append('''
  <!-- CALIPER CHECK TABLE -->
  <g transform="translate(28, 142)">
    <rect x="0" y="0" width="128" height="58" fill="#f8fafc" stroke="#cbd5e0" stroke-width="0.4" rx="1"/>
    
    <!-- Table Header -->
    <rect x="0" y="0" width="128" height="6.5" fill="#2d3748" rx="1"/>
    <text x="4" y="4.5" class="table-text-bold" fill="#ffffff" font-size="2.4">VERIFICATION DIMENSIONS (CALIPER INSPECTION)</text>

    <!-- Sub-headers -->
    <rect x="0" y="6.5" width="128" height="5.0" fill="#edf2f7"/>
    <text x="4" y="10.0" class="table-text-bold">No.</text>
    <text x="12" y="10.0" class="table-text-bold">Feature / Dimension</text>
    <text x="75" y="10.0" class="table-text-bold">Target</text>
    <text x="96" y="10.0" class="table-text-bold">Tolerance</text>
    <line x1="0" y1="11.5" x2="128" y2="11.5" stroke="#cbd5e0" stroke-width="0.3"/>
''')

    measurements = [
        ("1", "Overall Part Length (X)", "115.00 mm", "±0.20 mm"),
        ("2", "Main Body Width (Y)", "30.50 mm", "±0.20 mm"),
        ("3", "Base Body Height (Z)", "19.00 mm", "±0.15 mm"),
        ("4", "Total Height with Tab (Z)", "34.00 mm", "±0.20 mm"),
        ("5", "Servo 1 Cavity (X × Y)", "40.5 × 20.5 mm", "±0.20 mm"),
        ("6", "Servo 1 Hole Spacing (X × Y)", "48.50 × 10.00 mm", "±0.10 mm"),
        ("7", "Servo 2 Hole Spacing (X × Z)", "48.50 × 10.00 mm", "±0.10 mm"),
        ("8", "U-Fork Inner Span (X)", "41.30 mm", "±0.20 mm"),
        ("9", "U-Fork Rib Thickness (Y)", "5.00 mm", "±0.15 mm"),
        ("10", "Pivot Axis Pos from Edge", "74.70 mm", "±0.15 mm"),
        ("11", "Pivot Bore Ø", "4.20 mm", "+0.15 mm"),
        ("12", "Tab Counter-Bearing Bore Ø", "3.50 mm", "+0.15 mm"),
    ]

    for idx, (nr, desc, val, tol) in enumerate(measurements):
        y_pos = 15.0 + idx * 3.5
        bg_col = "#ffffff" if idx % 2 == 0 else "#f7fafc"
        svg.append(f'''    <rect x="0.5" y="{y_pos - 3.0}" width="127" height="3.5" fill="{bg_col}"/>
    <text x="4" y="{y_pos - 0.5}" class="table-text">{nr}</text>
    <text x="12" y="{y_pos - 0.5}" class="table-text">{desc}</text>
    <text x="75" y="{y_pos - 0.5}" class="table-text-bold">{val}</text>
    <text x="96" y="{y_pos - 0.5}" class="table-text" fill="#4a5568">{tol}</text>
''')

    svg.append('  </g>\n')

    # ==========================================
    # TITLE BLOCK (DIN EN ISO 7200)
    # Bottom Right: (162, 142)
    # Dimensions: 126 x 58
    # ==========================================
    svg.append('''
  <!-- TITLE BLOCK (DIN EN ISO 7200) -->
  <g transform="translate(162, 142)">
    <rect x="0" y="0" width="126" height="58" fill="#ffffff" stroke="#000000" stroke-width="0.5"/>

    <!-- Horizontal Dividers -->
    <line x1="0" y1="12" x2="126" y2="12" stroke="#000" stroke-width="0.35"/>
    <line x1="0" y1="24" x2="126" y2="24" stroke="#000" stroke-width="0.35"/>
    <line x1="0" y1="38" x2="126" y2="38" stroke="#000" stroke-width="0.35"/>
    <line x1="0" y1="48" x2="126" y2="48" stroke="#000" stroke-width="0.35"/>

    <!-- Vertical Dividers -->
    <line x1="63" y1="0" x2="63" y2="24" stroke="#000" stroke-width="0.35"/>
    <line x1="86" y1="24" x2="86" y2="48" stroke="#000" stroke-width="0.35"/>
    <line x1="42" y1="48" x2="42" y2="58" stroke="#000" stroke-width="0.35"/>
    <line x1="84" y1="48" x2="84" y2="58" stroke="#000" stroke-width="0.35"/>

    <!-- Field Contents -->
    <text x="4" y="4.5" class="dim-text-sm" text-anchor="start" fill="#718096">Project / Assembly:</text>
    <text x="4" y="9.5" class="title" font-size="3.2">LASIUS HEXAPOD</text>

    <text x="67" y="4.5" class="dim-text-sm" text-anchor="start" fill="#718096">Drawing No. / Rev:</text>
    <text x="67" y="9.5" class="title" font-size="3.2">LH-COX-001-REV3</text>

    <text x="4" y="16.5" class="dim-text-sm" text-anchor="start" fill="#718096">Part Name:</text>
    <text x="4" y="21.5" class="title" font-size="3.8">COXA BRACKET</text>

    <text x="67" y="16.5" class="dim-text-sm" text-anchor="start" fill="#718096">Servo Model:</text>
    <text x="67" y="21.5" class="title" font-size="2.6" fill="#2b6cb0">Torcster / Reely NR-645 MG BB</text>

    <text x="4" y="28.5" class="dim-text-sm" text-anchor="start" fill="#718096">Material / Process:</text>
    <text x="4" y="33.5" class="subtitle" font-weight="bold" font-size="2.6">3D Print (PETG / ABS)</text>
    <text x="4" y="36.5" class="dim-text-sm" text-anchor="start" fill="#4a5568">Infill ≥ 40%, Perimeters ≥ 4</text>

    <text x="89" y="28.5" class="dim-text-sm" text-anchor="start" fill="#718096">Scale:</text>
    <text x="89" y="34.5" class="title" font-size="4.0">1:1</text>
    <text x="89" y="37.0" class="dim-text-sm" text-anchor="start" fill="#718096">(Isometric 0.75:1)</text>

    <text x="4" y="42.5" class="dim-text-sm" text-anchor="start" fill="#718096">General Tolerance:</text>
    <text x="4" y="46.5" class="subtitle" font-weight="bold" font-size="2.4">DIN ISO 2768-m (±0.2 mm)</text>

    <text x="89" y="42.5" class="dim-text-sm" text-anchor="start" fill="#718096">Sheet Size:</text>
    <text x="89" y="46.5" class="subtitle" font-weight="bold" font-size="2.6">DIN A4 Landscape</text>

    <text x="4" y="52.0" class="dim-text-sm" text-anchor="start" fill="#718096">Author / Date:</text>
    <text x="4" y="56.0" class="subtitle" font-size="2.2">2026-11-05 / Antigravity</text>

    <text x="46" y="52.0" class="dim-text-sm" text-anchor="start" fill="#718096">CAD Source:</text>
    <text x="46" y="56.0" class="subtitle" font-size="2.2">coxa_bracket.FCStd</text>

    <text x="88" y="52.0" class="dim-text-sm" text-anchor="start" fill="#718096">Status:</text>
    <text x="88" y="56.0" class="subtitle" font-weight="bold" font-size="2.2" fill="#22543d">APPROVED</text>
  </g>
''')

    svg.append('</svg>\n')
    return "".join(svg)

if __name__ == "__main__":
    svg_content = create_technische_zeichnung_svg()
    svg_path = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/drawings/templates/coxa_bracket_technical_drawing.svg"
    html_path = "/tmp/coxa_zeichnung_wrapper.html"
    pdf_path = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/drawings/templates/coxa_bracket_technical_drawing.pdf"
    
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
