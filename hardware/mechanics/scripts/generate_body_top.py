#!/usr/bin/env python3
"""
Generate Lasius Hexapod Body Top Plate FreeCAD Model (body_top.FCStd)
Plate Thickness: 2.0 mm solid
Coordinate origin: (0, 0, 0) at chassis center (midpoint between ML and MR coxa pivots)
Analytic Geometry: Pure G1-continuous circular arcs and lines (matching body_bottom exactly)
"""

import math
import os
import FreeCAD as App
import Part

print("--- Generating Lasius Body Top Model (Pure Analytic Geometry) ---")

doc_name = "body_top"
fcstd_path = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/models/body_top.FCStd"
stl_path = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/stl/body_top.stl"
step_path = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/step/body_top.step"
dxf_path = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/dxf/body_top.dxf"

try:
    doc = App.getDocument(doc_name)
    App.closeDocument(doc_name)
except Exception:
    pass

doc = App.newDocument(doc_name)

# Plate thickness
thickness = 2.0

# -------------------------------------------------------------
# 1. Analytic Geometry Definition (G1-Continuous Arcs & Lines)
# -------------------------------------------------------------

def arc_through_3pts(p1, pmid, p2):
    return Part.Edge(Part.ArcOfCircle(p1, pmid, p2))

def outward_arc_mid(cx, cy, r, p1, p2, outward_direction):
    v1 = (p1.x - cx, p1.y - cy)
    v2 = (p2.x - cx, p2.y - cy)
    bis_x = v1[0] + v2[0]
    bis_y = v1[1] + v2[1]
    bis_len = math.hypot(bis_x, bis_y)
    u_x = bis_x / bis_len
    u_y = bis_y / bis_len
    dot = u_x * outward_direction[0] + u_y * outward_direction[1]
    if dot < 0:
        u_x = -u_x
        u_y = -u_y
    return App.Vector(cx + r * u_x, cy + r * u_y, 0.0)

# 1. Nose apex: Center (120, 0), R=12.0 mm -> Apex tip at X = 132.0 mm
R_nose = 12.0
p_nose_start = App.Vector(120.0 + R_nose, 0.0, 0.0)
p_nose_tan = App.Vector(120.0 + R_nose / math.sqrt(2), R_nose / math.sqrt(2), 0.0)
p_nose_mid = outward_arc_mid(120.0, 0.0, R_nose, p_nose_start, p_nose_tan, (1.0, 1.0))
e_nose_apex = arc_through_3pts(p_nose_start, p_nose_mid, p_nose_tan)

# 2. Nose line at 45 deg + smooth concave neck fillet (Rf_top = 4.5 mm)
C_top = 120.0 + R_nose * math.sqrt(2)
Rf_top = 4.5
R_dist_top = 13.5 + Rf_top
K_top = C_top + Rf_top * math.sqrt(2)
U_top = K_top - 65.0
B_q = -2.0 * (86.0 + U_top)
C_q = 86.0**2 + U_top**2 - R_dist_top**2
disc = B_q**2 - 8.0 * C_q
Xf_top = (-B_q + math.sqrt(disc)) / 4.0
Yf_top = K_top - Xf_top
p_top_line_tan = App.Vector(Xf_top - Rf_top / math.sqrt(2), Yf_top - Rf_top / math.sqrt(2), 0.0)
e_nose_line = Part.makeLine(p_nose_tan, p_top_line_tan)

# 3. Concave Neck Fillet (transition into FL Ear)
vx_f = 86.0 - Xf_top
vy_f = 65.0 - Yf_top
vlen_f = math.hypot(vx_f, vy_f)
p_ear_fl_start = App.Vector(Xf_top + vx_f * (Rf_top / vlen_f), Yf_top + vy_f * (Rf_top / vlen_f), 0.0)
p_f_top_mid = outward_arc_mid(Xf_top, Yf_top, Rf_top, p_top_line_tan, p_ear_fl_start, (-1.0, 0.0))
e_fillet_fl = arc_through_3pts(p_top_line_tan, p_f_top_mid, p_ear_fl_start)

# 4. FL Ear: Center (86, 65), R=13.5 mm
Xw = 44.308
Yw = 81.246
Rw = 31.246
d_fl = math.hypot(86.0 - Xw, 65.0 - Yw)
p_fl_waist = App.Vector(Xw + (86.0 - Xw) * (Rw / d_fl), Yw + (65.0 - Yw) * (Rw / d_fl), 0.0)
p_fl_mid = outward_arc_mid(86.0, 65.0, 13.5, p_ear_fl_start, p_fl_waist, (1.0, 1.0))
e_fl_ear = arc_through_3pts(p_ear_fl_start, p_fl_mid, p_fl_waist)

# 5. Waist 1 (FL to ML): Center (Xw, Yw), Rw=31.246 mm
d_ml = math.hypot(0.0 - Xw, 75.0 - Yw)
p_ml_waist = App.Vector(Xw + (0.0 - Xw) * (Rw / d_ml), Yw + (75.0 - Yw) * (Rw / d_ml), 0.0)
p_w1_mid = outward_arc_mid(Xw, Yw, Rw, p_fl_waist, p_ml_waist, (0.0, -1.0))
e_waist_fm = arc_through_3pts(p_fl_waist, p_w1_mid, p_ml_waist)

# 6. ML Ear: Center (0, 75), R=13.5 mm
p_ml_rear_waist = App.Vector(-p_ml_waist.x, p_ml_waist.y, 0.0)
p_ml_mid = outward_arc_mid(0.0, 75.0, 13.5, p_ml_waist, p_ml_rear_waist, (0.0, 1.0))
e_ml_ear = arc_through_3pts(p_ml_waist, p_ml_mid, p_ml_rear_waist)

# 7. Waist 2 (ML to RL): Center (-Xw, Yw), Rw=31.246 mm
p_rl_waist = App.Vector(-p_fl_waist.x, p_fl_waist.y, 0.0)
p_w2_mid = outward_arc_mid(-Xw, Yw, Rw, p_ml_rear_waist, p_rl_waist, (0.0, -1.0))
e_waist_mr = arc_through_3pts(p_ml_rear_waist, p_w2_mid, p_rl_waist)

# 8. RL Ear: Center (-86, 65), R=13.5 mm (fully protruding circular ear boss)
Rf_bot = 4.5
Yf_bot = Yf_top
Xf_bot = -86.0 - math.sqrt((13.5 + Rf_bot)**2 - (Yf_bot - 65.0)**2)
vx_b = -86.0 - Xf_bot
vy_b = 65.0 - Yf_bot
vlen_b = math.hypot(vx_b, vy_b)
p_ear_rl_end = App.Vector(Xf_bot + vx_b * (Rf_bot / vlen_b), Yf_bot + vy_b * (Rf_bot / vlen_b), 0.0)
p_rl_mid = outward_arc_mid(-86.0, 65.0, 13.5, p_rl_waist, p_ear_rl_end, (-1.0, 1.0))
e_rl_ear = arc_through_3pts(p_rl_waist, p_rl_mid, p_ear_rl_end)

# 9. Concave Neck Fillet (transition from RL Ear toward Heck)
Cx_t, Cy_t, R_tail = -128.0, 12.0, 7.0
dx_ct = Cx_t - Xf_bot
dy_ct = Cy_t - Yf_bot
D_ct = math.hypot(dx_ct, dy_ct)
theta_ct = math.atan2(dy_ct, dx_ct)
alpha_ct = math.asin((Rf_bot + R_tail) / D_ct)
phi_n = theta_ct - math.pi / 2.0 - alpha_ct
nx_b, ny_b = math.cos(phi_n), math.sin(phi_n)

p_bot_line_start = App.Vector(Xf_bot - Rf_bot * nx_b, Yf_bot - Rf_bot * ny_b, 0.0)
p_tail_tan = App.Vector(Cx_t + R_tail * nx_b, Cy_t + R_tail * ny_b, 0.0)
p_f_bot_mid = outward_arc_mid(Xf_bot, Yf_bot, Rf_bot, p_ear_rl_end, p_bot_line_start, (1.0, 0.0))
e_fillet_rl = arc_through_3pts(p_ear_rl_end, p_f_bot_mid, p_bot_line_start)

# 10. Flank Line (tangent between neck fillet and tail corner)
e_rl_flank = Part.makeLine(p_bot_line_start, p_tail_tan)

# 11. Tail Corner Fillet: Center (-128, 12), R=7.0 mm
p_tail_edge_top = App.Vector(-135.0, 12.0, 0.0)
p_t_mid = outward_arc_mid(Cx_t, Cy_t, R_tail, p_tail_tan, p_tail_edge_top, (-1.0, 1.0))
e_tail_fillet = arc_through_3pts(p_tail_tan, p_t_mid, p_tail_edge_top)

# 12. Tail Flat Line (X = -135.0 mm, Y = 12.0 to 0.0)
p_tail_center = App.Vector(-135.0, 0.0, 0.0)
e_tail_flat = Part.makeLine(p_tail_edge_top, p_tail_center)

left_edges = [
    e_nose_apex, e_nose_line, e_fillet_fl, e_fl_ear, e_waist_fm,
    e_ml_ear, e_waist_mr, e_rl_ear, e_fillet_rl, e_rl_flank, e_tail_fillet, e_tail_flat
]

# Right half (mirror Y)
right_edges = []
for e in reversed(left_edges):
    curve = e.Curve
    if isinstance(curve, Part.Line):
        p1 = App.Vector(e.Vertexes[1].X, -e.Vertexes[1].Y, 0.0)
        p0 = App.Vector(e.Vertexes[0].X, -e.Vertexes[0].Y, 0.0)
        right_edges.append(Part.makeLine(p1, p0))
    elif isinstance(curve, Part.Circle):
        p1 = App.Vector(e.Vertexes[1].X, -e.Vertexes[1].Y, 0.0)
        p0 = App.Vector(e.Vertexes[0].X, -e.Vertexes[0].Y, 0.0)
        pm = curve.value((e.FirstParameter + e.LastParameter) / 2.0)
        pm_mirrored = App.Vector(pm.x, -pm.y, 0.0)
        right_edges.append(Part.Edge(Part.ArcOfCircle(p1, pm_mirrored, p0)))

all_edges = left_edges + right_edges

# -------------------------------------------------------------
# 2. Pure Analytical Wire & Face Construction
# -------------------------------------------------------------
outer_wire = Part.Wire(Part.__sortEdges__(all_edges))
outer_face = Part.Face(outer_wire)

# Rotate 180 deg around Z:
# In the physical robot, the 2 side-by-side spacers are FRONT (+X = +128 mm)
# and the 2 centerline spacers are REAR (-X = -90, -120 mm).
outer_face.rotate(App.Vector(0.0, 0.0, 0.0), App.Vector(0.0, 0.0, 1.0), 180.0)

# -------------------------------------------------------------
# 3. Central Window Cutout (50.0 mm x 160.0 mm)
# -------------------------------------------------------------
win_pts = [
    App.Vector(-80.0, -25.0, 0.0),
    App.Vector(80.0, -25.0, 0.0),
    App.Vector(80.0, 25.0, 0.0),
    App.Vector(-80.0, 25.0, 0.0)
]
win_edges = [Part.makeLine(win_pts[i], win_pts[(i+1)%4]) for i in range(4)]
win_wire = Part.Wire(win_edges)
base_face = outer_face.cut(Part.Face(win_wire))

# -------------------------------------------------------------
# 4. Extrude Solid (thickness = 2.0 mm along +Z)
# -------------------------------------------------------------
plate_solid = base_face.extrude(App.Vector(0.0, 0.0, thickness))

# -------------------------------------------------------------
# 5. Drill 6x Coxa Bearing Holes (dia 8.0 mm)
# -------------------------------------------------------------
coxa_holes = [
    (86.0, 65.0), (86.0, -65.0),
    (0.0, 75.0), (0.0, -75.0),
    (-86.0, 65.0), (-86.0, -65.0),
]
for xc, yc in coxa_holes:
    cyl = Part.makeCylinder(4.0, thickness + 4.0, App.Vector(xc, yc, -2.0), App.Vector(0.0, 0.0, 1.0))
    plate_solid = plate_solid.cut(cyl)

# -------------------------------------------------------------
# 6. Drill 8x M3 Screw Holes (dia 3.0 mm)
# -------------------------------------------------------------
screw_holes = [
    # 4x Window flanking screws:
    (45.0, 30.0), (45.0, -30.0), (-45.0, 30.0), (-45.0, -30.0),
    # 2x Front screws (side-by-side):
    (128.0, 12.0), (128.0, -12.0),
    # 2x Rear centerline screws (inline):
    (-90.0, 0.0), (-120.0, 0.0)
]
for xc, yc in screw_holes:
    cyl = Part.makeCylinder(1.5, thickness + 4.0, App.Vector(xc, yc, -2.0), App.Vector(0.0, 0.0, 1.0))
    plate_solid = plate_solid.cut(cyl)

# -------------------------------------------------------------
# 7. FreeCAD Document Setup & Properties
# -------------------------------------------------------------
part_obj = doc.addObject("Part::Feature", "BodyTop")
part_obj.Shape = plate_solid
part_obj.Label = "BodyTop (Chassis Top Plate 2mm)"

doc.recompute()

bbox = plate_solid.BoundBox
print(f"Solid Valid: {plate_solid.isValid()}")
print(f"Faces: {len(plate_solid.Faces)} (pure analytical, no facets)")
print(f"Edges: {len(plate_solid.Edges)}")
print(f"Volume: {plate_solid.Volume:.2f} mm^3 (Area = {plate_solid.Area:.2f} mm^2)")
print(f"Length X: {bbox.XLength:.2f} mm ([{bbox.XMin:.2f}, {bbox.XMax:.2f}])")
print(f"Width Y: {bbox.YLength:.2f} mm ([{bbox.YMin:.2f}, {bbox.YMax:.2f}])")
print(f"Thickness Z: {bbox.ZLength:.2f} mm ([{bbox.ZMin:.2f}, {bbox.ZMax:.2f}])")

# Ensure export directories exist
os.makedirs(os.path.dirname(fcstd_path), exist_ok=True)
os.makedirs(os.path.dirname(stl_path), exist_ok=True)
os.makedirs(os.path.dirname(step_path), exist_ok=True)
os.makedirs(os.path.dirname(dxf_path), exist_ok=True)

# Save FreeCAD Document
doc.saveAs(fcstd_path)
print(f"Saved FreeCAD Model: {fcstd_path}")

# Export STL
part_obj.Shape.exportStl(stl_path)
print(f"Exported STL: {stl_path}")

# Export STEP
part_obj.Shape.exportStep(step_path)
print(f"Exported STEP: {step_path}")

# Export DXF of 2D profile
try:
    import importDXF
    importDXF.export([part_obj], dxf_path)
    print(f"Exported DXF: {dxf_path}")
except Exception as e:
    print(f"DXF export skipped: {e}")

App.closeDocument(doc_name)
print("--- Done ---")
import sys
sys.exit(0)
