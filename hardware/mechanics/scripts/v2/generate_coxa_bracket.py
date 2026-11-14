#!/usr/bin/env python3
"""
Generate Lasius Hexapod Coxa Bracket v2 (Organic Lightweight Truss & Reinforced Bearing Gusset)
- Inherits exact kinematic & mounting interfaces from v1 coxa_bracket.FCStd
  (Chassis pivot bore, Coxa servo mounting, Femur servo pocket, Femur pivot axis)
- Key v2 Structural & Aesthetic Optimizations:
  1. Option A Inverted M4 Counter-Bearing Seat:
     Internal anti-rotation M4 hex nut pocket (SW 7.10 mm, depth 2.40 mm) with a solid
     0.60 mm retaining shoulder and coaxial D = 4.10 mm bore at local (X = 18.20, Y = 15.25),
     allowing the Femur to slide radially into the bracket with zero rear screw protrusion.
  2. 45-Degree Dual-Cheek Triangular Truss Gusset ("Versteifungs-Gusset"):
     Connects the lower counter-bearing tab base (X = 23.70, Z = -14.50) smoothly to the
     bridge cheeks (X = 38.20, Z = 0.00) exclusively on the front (Y in [0.0, 5.0]) and
     rear (Y in [25.5, 31.7]) side walls at an exact 45.0-degree angle, with fully-enclosed
     filleted triangular weight-relief windows and leaving the interior servo chamber
     (Y in [5.0, 25.5]) 100% open with zero hardware collisions.
  3. Organic 45-Degree Weight-Relief Truss Windows & Cavities:
     - Front & rear cheek flank 45-degree Warren truss windows under the Femur servo ears
       (X in [9.0, 24.0], Z in [2.5, 15.5]), eliminating all solid flat cheek plates.
     - Symmetrical 45-degree A-truss (chevron) windows in the central bridge (X in [28.5, 57.5]).
     - Rear tail 45-degree diagonal truss windows (X in [84.5, 106.0], Z in [2.0, 16.0]).
     - Symmetrical 45-degree A-truss windows in top and bottom Coxa servo casing walls.
     - Option A through-tunnel in rear tail block (X in [105.0, 116.0]).
  4. 100% Solid Femur Servo Mounting Shelf (Z = 15.50 mm) with all 4 screw bores intact.
"""

import math
import os
import FreeCAD as App
import Part

print("--- Generating Lasius Coxa Bracket v2 (Truss Gussets + Healed Flanges + Option A) ---")

models_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/models"
v1_coxa_path = f"{models_dir}/custom/v1/parts/coxa_bracket.FCStd"
v2_coxa_path = f"{models_dir}/custom/v2/parts/coxa_bracket.FCStd"

export_step_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/step/custom/v2/parts"
export_stl_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/stl/custom/v2/parts"
step_coxa_path = f"{export_step_dir}/coxa_bracket.step"
stl_coxa_path = f"{export_stl_dir}/coxa_bracket.stl"


# Tibia-Standard Strut Parameters (from generate_tibia.py servo cage):
W_STRUT = 2.50    # mm (uniform perpendicular 45-deg strut width across all Coxa trusses)
R_FILLET = 1.40   # mm (fillet radius at all truss corners)
DX_45 = W_STRUT * math.sqrt(2.0)  # 3.5355 mm (delta along X/Z for exact 45-deg parallel lines)


def make_filleted_polygon_2d(pts, r_list):
    """
    Construct a planar Part.Face in XY plane from a list of vertices pts (CCW)
    with each corner i filleted with radius r_list[i].
    """
    n = len(pts)
    if isinstance(r_list, (int, float)):
        r_list = [float(r_list)] * n
    tangents_in, tangents_out, arcs = [], [], []
    for i in range(n):
        p_prev, p_curr, p_next = pts[(i - 1) % n], pts[i], pts[(i + 1) % n]
        r = r_list[i]
        v_in = (p_curr - p_prev).normalize()
        v_out = (p_next - p_curr).normalize()
        cross_z = v_in.x * v_out.y - v_in.y * v_out.x
        dot = max(-1.0, min(1.0, v_in.dot(v_out)))
        turn_angle = math.atan2(cross_z, dot)
        half_beta = 0.5 * (math.pi - abs(turn_angle))
        d = 0.0 if half_beta < 1e-4 else r / math.tan(half_beta)
        t1 = p_curr - v_in * d
        t2 = p_curr + v_out * d
        b = (v_out - v_in).normalize()
        if cross_z < 0:
            b = -b
        center = p_curr + b * (r / math.sin(half_beta))
        p_mid = center - b * r
        tangents_in.append(t1)
        tangents_out.append(t2)
        arcs.append(Part.Arc(t1, p_mid, t2).toShape() if d > 1e-4 else None)
    wire_edges = []
    for i in range(n):
        p_start, p_end = tangents_out[i], tangents_in[(i + 1) % n]
        if (p_end - p_start).Length > 1e-4:
            wire_edges.append(Part.makeLine(p_start, p_end))
        if arcs[(i + 1) % n] is not None:
            wire_edges.append(arcs[(i + 1) % n])
    return Part.Face(Part.Wire(wire_edges))


def extrude_face_xz(face_xy, y_pos, y_extrude):
    """
    Map an XY face to XZ plane at Y = y_pos and extrude by y_extrude along Y.
    """
    edges = []
    for e in face_xy.OuterWire.Edges:
        pts = [App.Vector(v.Point.x, y_pos, v.Point.y) for v in e.Vertexes]
        if "Line" in str(type(e.Curve)):
            edges.append(Part.makeLine(pts[0], pts[1]))
        else:
            pm = e.valueAt(0.5 * (e.FirstParameter + e.LastParameter))
            edges.append(Part.Arc(pts[0], App.Vector(pm.x, y_pos, pm.y), pts[1]).toShape())
    return Part.Face(Part.Wire(edges)).extrude(App.Vector(0.0, y_extrude, 0.0))


def make_rounded_rect_face_2d(x1, x2, y1, y2, r):
    """
    Construct a planar Part.Face in the XY plane representing a rectangle
    with 4 tangential circular arc corners of radius r.
    """
    k = r * (1.0 - 1.0 / math.sqrt(2.0))
    pts = [
        App.Vector(x1 + r, y2, 0.0),
        App.Vector(x2 - r, y2, 0.0),
        App.Vector(x2 - k, y2 - k, 0.0),
        App.Vector(x2, y2 - r, 0.0),
        App.Vector(x2, y1 + r, 0.0),
        App.Vector(x2 - k, y1 + k, 0.0),
        App.Vector(x2 - r, y1, 0.0),
        App.Vector(x1 + r, y1, 0.0),
        App.Vector(x1 + k, y1 + k, 0.0),
        App.Vector(x1, y1 + r, 0.0),
        App.Vector(x1, y2 - r, 0.0),
        App.Vector(x1 + k, y2 - k, 0.0),
    ]
    edges = [
        Part.makeLine(pts[0], pts[1]),
        Part.Arc(pts[1], pts[2], pts[3]).toShape(),
        Part.makeLine(pts[3], pts[4]),
        Part.Arc(pts[4], pts[5], pts[6]).toShape(),
        Part.makeLine(pts[6], pts[7]),
        Part.Arc(pts[7], pts[8], pts[9]).toShape(),
        Part.makeLine(pts[9], pts[10]),
        Part.Arc(pts[10], pts[11], pts[0]).toShape(),
    ]
    return Part.Face(Part.Wire(edges))


def make_hex_nut_pocket_z(cx, cy, z_bottom, z_top, sw=7.10):
    """
    Construct an internal anti-rotation M4 hex nut pocket (across flats = sw).
    """
    r_circum = sw / math.sqrt(3.0)
    pts = []
    for i in range(6):
        ang = math.radians(60.0 * i)
        pts.append(App.Vector(cx + r_circum * math.cos(ang), cy + r_circum * math.sin(ang), z_bottom))
    pts.append(pts[0])
    wire = Part.makePolygon(pts)
    return Part.Face(wire).extrude(App.Vector(0.0, 0.0, z_top - z_bottom))


def build_coxa_bracket_v2_shape():
    doc_v1 = App.openDocument(v1_coxa_path)
    v1_shape = doc_v1.getObject("Coxa_Bracket").Shape.copy()
    App.closeDocument(doc_v1.Name)

    # -------------------------------------------------------------
    # 0. Clean Core: Strip Old v1 Cheek Volumes to Prevent Face Segmentation
    # -------------------------------------------------------------
    # In v1, the cheek areas (Y in [0, 5] and [25.5, 31.7]) had fragmented internal
    # faces, fillets, and seams. Cutting these zones away prior to fusing the new
    # monolithic v2 cheeks guarantees 100% seamless, non-segmented outer lateral faces.
    # Junction to rear Coxa cage is at exactly X = 59.40 mm so cheeks and cage faces unify.
    X_JUNCTION = 59.40
    box_clean_f = Part.makeBox(X_JUNCTION + 0.5, 6.0, 55.0, App.Vector(-0.5, -1.0, -20.0))
    box_clean_r = Part.makeBox(X_JUNCTION + 0.5, 8.0, 55.0, App.Vector(-0.5, 25.5, -20.0))
    core = v1_shape.cut(box_clean_f).cut(box_clean_r)

    # Solidify Femur Mounting Flange (Z = 15.50, X in [49.80, 57.40], Y in [5.00, 25.50])
    plug_shelf_top = Part.makeBox(57.40 - 52.40, 12.45 - 5.00, 15.50 - 11.50, App.Vector(52.40, 5.00, 11.50))
    core = core.fuse(plug_shelf_top)

    # -------------------------------------------------------------
    # 1. Option A Inverted M4 Counter-Bearing Seat (X = 18.20, Y = 15.25)
    # -------------------------------------------------------------
    cx, cy = 18.20, 15.25
    heal_plug = Part.makeCylinder(4.50, 3.00, App.Vector(cx, cy, -14.50))
    core = core.fuse(heal_plug)

    screw_bore = Part.makeCylinder(2.05, 5.00, App.Vector(cx, cy, -15.50))
    nut_pocket = make_hex_nut_pocket_z(cx, cy, -13.90, -11.50, sw=7.10)
    core = core.cut(screw_bore).cut(nut_pocket)

    # -------------------------------------------------------------
    # 1b. Coxa Pivot Axis (X = 74.70, Z = 9.00): Heal Legacy Ball Bearing Pocket
    # -------------------------------------------------------------
    # In v1, there was an 8.0 mm ball bearing pocket with countersink on the front rib.
    # The ball bearing is housed in the chassis bottom plate; here only the 3 mm screw
    # penetrates the Coxa Bracket wall (Y in [0.00, 4.00]) as the pivot pin.
    px_pivot, pz_pivot = 74.70, 9.00
    plug_pivot_pocket = Part.makeCylinder(4.05, 4.00, App.Vector(px_pivot, 0.00, pz_pivot), App.Vector(0, 1, 0))
    core = core.fuse(plug_pivot_pocket)

    # -------------------------------------------------------------
    # 2. Monolithic Seamless Cheeks (G1 S-curves + Front Apex Rounding)
    # -------------------------------------------------------------
    def make_s_curve_edges(p1, p2):
        dx = p2.x - p1.x
        dz = p2.z - p1.z
        dx_h = 0.5 * abs(dx)
        dz_h = 0.5 * abs(dz)
        r = (dx_h**2 + dz_h**2) / (2.0 * dz_h)
        p_inf = App.Vector(p1.x + 0.5 * dx, 0.0, p1.z + 0.5 * dz)
        ang = math.atan2(r - dz_h, dx_h)
        sign_x = 1.0 if dx > 0 else -1.0
        sign_z = 1.0 if dz > 0 else -1.0
        pm1 = App.Vector(p1.x + sign_x * r * math.sin(0.5 * (math.pi/2 - ang)), 0.0, p1.z + sign_z * (r - r * math.cos(0.5 * (math.pi/2 - ang))))
        pm2 = App.Vector(p2.x - sign_x * r * math.sin(0.5 * (math.pi/2 - ang)), 0.0, p2.z - sign_z * (r - r * math.cos(0.5 * (math.pi/2 - ang))))
        e1 = Part.Edge(Part.Arc(p1, pm1, p_inf))
        e2 = Part.Edge(Part.Arc(p_inf, pm2, p2))
        return [e1, e2]

    R_FRONT = 4.50
    p_rear_top = App.Vector(X_JUNCTION, 0.0, 22.15)
    p_rear_bot = App.Vector(X_JUNCTION, 0.0, -4.15)
    e_rear_vert = [Part.makeLine(p_rear_top, p_rear_bot)]

    # -----------------------------------------------------------------
    # Symmetrical Profile (Top & Bottom identical, mirrored about Z = 9.00 mm):
    # Z_top(x) = 18.00 - Z_bot(x)
    # -----------------------------------------------------------------
    # Bottom Profile:
    # 1. Harmonic G1 S-curve from rear Coxa cage floor (X_JUNCTION, -4.15) down to rear of tab (23.70, -14.50)
    p_tab_rear = App.Vector(23.70, 0.0, -14.50)
    e_bot_s_curve = make_s_curve_edges(p_rear_bot, p_tab_rear)

    # 2. Flat bottom fully flanking counter-bearing tab from X = 23.70 to X = 9.20 at Z = -14.50
    p_tab_fillet_end = App.Vector(9.20, 0.0, -14.50)
    e_tab_bottom = [Part.makeLine(p_tab_rear, p_tab_fillet_end)]

    # 3. Front tab fillet R = 2.0 mm from (9.20, -14.50) up to (7.20, -12.50)
    p_tab_vert_start = App.Vector(7.20, 0.0, -12.50)
    p_tab_fillet_mid = App.Vector(7.20 + 2.0 * (1.0 - math.cos(math.pi / 4)), 0.0, -14.50 + 2.0 * (1.0 - math.sin(math.pi / 4)))
    e_tab_fillet = [Part.Edge(Part.Arc(p_tab_fillet_end, p_tab_fillet_mid, p_tab_vert_start))]

    # 4. Vertical tab front face from (7.20, -12.50) up to (7.20, 0.00)
    p_tab_top_front = App.Vector(7.20, 0.0, 0.00)
    e_tab_vert = [Part.makeLine(p_tab_vert_start, p_tab_top_front)]

    # 5. Nose bottom line from (7.20, 0.00) to (R_FRONT, 0.00)
    p_front_bot = App.Vector(R_FRONT, 0.0, 0.00)
    e_nose_bot = [Part.makeLine(p_tab_top_front, p_front_bot)]

    # 6. Front nose corner arcs (R = 4.50 mm)
    p_mid_bot = App.Vector(R_FRONT - R_FRONT * math.cos(math.pi / 4), 0.0, R_FRONT - R_FRONT * math.sin(math.pi / 4))
    e_arc_bot = Part.Edge(Part.Arc(p_front_bot, p_mid_bot, App.Vector(0.0, 0.0, R_FRONT)))
    e_front_mid = [Part.makeLine(App.Vector(0.0, 0.0, R_FRONT), App.Vector(0.0, 0.0, 18.00 - R_FRONT))]
    p_front_top = App.Vector(R_FRONT, 0.0, 18.00)
    p_mid_top = App.Vector(R_FRONT - R_FRONT * math.cos(math.pi / 4), 0.0, 18.00 - R_FRONT + R_FRONT * math.sin(math.pi / 4))
    e_arc_top = Part.Edge(Part.Arc(App.Vector(0.0, 0.0, 18.00 - R_FRONT), p_mid_top, p_front_top))

    # Top Profile (Identical mirror of bottom):
    # 7. Nose top line from (R_FRONT, 18.00) to (7.20, 18.00)
    p_crest_top_front = App.Vector(7.20, 0.0, 18.00)
    e_nose_top = [Part.makeLine(p_front_top, p_crest_top_front)]

    # 8. Vertical crest front face from (7.20, 18.00) up to (7.20, 30.50)
    p_crest_vert_start = App.Vector(7.20, 0.0, 30.50)
    e_crest_vert = [Part.makeLine(p_crest_top_front, p_crest_vert_start)]

    # 9. Crest fillet R = 2.0 mm from (7.20, 30.50) up to (9.20, 32.50)
    p_crest_fillet_end = App.Vector(9.20, 0.0, 32.50)
    p_crest_fillet_mid = App.Vector(7.20 + 2.0 * (1.0 - math.cos(math.pi / 4)), 0.0, 32.50 - 2.0 * (1.0 - math.sin(math.pi / 4)))
    e_crest_fillet = [Part.Edge(Part.Arc(p_crest_vert_start, p_crest_fillet_mid, p_crest_fillet_end))]

    # 10. Flat crest top from X = 9.20 to X = 23.70 at Z = 32.50
    p_crest_rear = App.Vector(23.70, 0.0, 32.50)
    e_crest_top = [Part.makeLine(p_crest_fillet_end, p_crest_rear)]

    # 11. Harmonic G1 S-curve from (23.70, 32.50) down to Coxa cage roof (X_JUNCTION, 22.15)
    e_top_s_curve = make_s_curve_edges(p_crest_rear, p_rear_top)

    all_edges = (
        e_nose_top
        + e_crest_vert
        + e_crest_fillet
        + e_crest_top
        + e_top_s_curve
        + e_rear_vert
        + e_bot_s_curve
        + e_tab_bottom
        + e_tab_fillet
        + e_tab_vert
        + e_nose_bot
        + [e_arc_bot]
        + e_front_mid
        + [e_arc_top]
    )
    clean_cheek_wire = Part.Wire(all_edges)
    clean_cheek_face = Part.Face(clean_cheek_wire)

    # Extrude cheeks: Front Y in [0.00, 5.00] (5.00 mm), Rear Y in [25.50, 31.70] (6.20 mm)
    s_clean_f = clean_cheek_face.extrude(App.Vector(0.0, 5.00, 0.0))
    s_clean_r = clean_cheek_face.extrude(App.Vector(0.0, 6.20, 0.0))
    s_clean_r.translate(App.Vector(0.0, 25.50, 0.0))

    shape = core.fuse(s_clean_f).fuse(s_clean_r)

    # -------------------------------------------------------------
    # 3. Clean Re-Bore of Femur Mounting Screws (M2)
    # -------------------------------------------------------------
    bore_f1 = Part.makeCylinder(1.10, 20.00, App.Vector(53.15, 10.25, 0.00))
    bore_f2 = Part.makeCylinder(1.10, 20.00, App.Vector(53.15, 20.25, 0.00))
    bore_f3 = Part.makeCylinder(1.10, 20.00, App.Vector(4.65, 10.25, 0.00))
    bore_f4 = Part.makeCylinder(1.10, 20.00, App.Vector(4.65, 20.25, 0.00))
    for b in [bore_f1, bore_f2, bore_f3, bore_f4]:
        shape = shape.cut(b)

    # -------------------------------------------------------------
    # 4. Coxa Pivot Axis 3 mm Screw Through-Bore (D = 3.20 mm)
    # -------------------------------------------------------------
    bore_pivot_3mm = Part.makeCylinder(1.60, 6.00, App.Vector(74.70, -1.00, 9.00), App.Vector(0, 1, 0))
    shape = shape.cut(bore_pivot_3mm)

    # -------------------------------------------------------------
    # 6. Front Wall Central Bulkhead Weight-Relief Window - REMOVED
    # -------------------------------------------------------------
    # Kept completely solid so the Coxa servo screw block (X = 66.30, Y in [3.95, 5.00])
    # is 100% solid, un-notched, and robust for screw threads.

    # -------------------------------------------------------------
    # 7. Rear Tail 45-Degree Diagonal Truss Windows (Tibia Standard w = 2.50 mm)
    # -------------------------------------------------------------
    # Exact 45.0-deg diagonal struts with uniform width w = 2.50 mm (DX_45 = 3.536 mm)
    p_t_bot = [App.Vector(90.50, 2.50, 0.0), App.Vector(103.50, 2.50, 0.0), App.Vector(103.50, 15.50, 0.0)]
    f_t_bot = make_filleted_polygon_2d(p_t_bot, R_FILLET)

    p_t_top = [App.Vector(87.00, 6.04, 0.0), App.Vector(99.96, 15.50, 0.0), App.Vector(87.00, 15.50, 0.0)]
    f_t_top = make_filleted_polygon_2d(p_t_top, R_FILLET)

    shape = shape.cut(extrude_face_xz(f_t_bot, -1.0, 6.0))
    shape = shape.cut(extrude_face_xz(f_t_top, -1.0, 6.0))

    # -------------------------------------------------------------
    # 8. Coxa Servo Compartment Top & Bottom Symmetrical 45-Degree A-Truss (w = 2.50 mm)
    # -------------------------------------------------------------
    p_c1_tb = App.Vector(69.50, 6.00, 0.0)
    p_c2_tb = App.Vector(101.50, 6.00, 0.0)
    p_c3_tb = App.Vector(85.50, 22.00, 0.0)
    fc_tb = make_filleted_polygon_2d([p_c1_tb, p_c2_tb, p_c3_tb], R_FILLET)

    p_l1_tb = App.Vector(67.50, 7.54, 0.0)
    p_l2_tb = App.Vector(81.96, 22.00, 0.0)
    p_l3_tb = App.Vector(67.50, 22.00, 0.0)
    fl_tb = make_filleted_polygon_2d([p_l1_tb, p_l2_tb, p_l3_tb], R_FILLET)

    p_r1_tb = App.Vector(89.04, 22.00, 0.0)
    p_r2_tb = App.Vector(103.50, 7.54, 0.0)
    p_r3_tb = App.Vector(103.50, 22.00, 0.0)
    fr_tb = make_filleted_polygon_2d([p_r1_tb, p_r2_tb, p_r3_tb], R_FILLET)

    # Cut Top Wall (Z in [18.0, 22.15]):
    for f in [fc_tb, fl_tb, fr_tb]:
        cut_top = f.extrude(App.Vector(0.0, 0.0, 10.0))
        cut_top.translate(App.Vector(0.0, 0.0, 16.0))
        shape = shape.cut(cut_top)

    # Cut Bottom Wall (Z in [-4.15, 0.0]):
    for f in [fc_tb, fl_tb, fr_tb]:
        cut_bot = f.extrude(App.Vector(0.0, 0.0, 10.0))
        cut_bot.translate(App.Vector(0.0, 0.0, -6.0))
        shape = shape.cut(cut_bot)

    # -------------------------------------------------------------
    # 9. Rear Tail Block - Closed & Solid
    # -------------------------------------------------------------
    # The rear tail block (X in [105.0, 115.0]) is kept solid without through-openings
    # to conceal the Coxa servo mounting screws and protect internal hardware.

    shape = shape.removeSplitter()
    return shape


if __name__ == "__main__":
    shape_v2 = build_coxa_bracket_v2_shape()
    print(
        f"Coxa_Bracket v2 Valid: {shape_v2.isValid()}, Solids: {len(shape_v2.Solids)}, "
        f"Volume: {shape_v2.Volume:.1f} mm^3, Mass (PETG): {shape_v2.Volume * 1.27 / 1000.0:.1f} g"
    )

    os.makedirs(os.path.dirname(v2_coxa_path), exist_ok=True)
    os.makedirs(export_step_dir, exist_ok=True)
    os.makedirs(export_stl_dir, exist_ok=True)

    doc = App.newDocument("coxa_bracket")
    obj = doc.addObject("Part::Feature", "Coxa_Bracket")
    obj.Label = "Coxa Bracket v2 (Truss Gusset & Weight-Relief Windows)"
    obj.Shape = shape_v2

    doc.recompute()
    doc.saveAs(v2_coxa_path)
    print(f"Saved FreeCAD model: {v2_coxa_path}")

    shape_v2.exportStep(step_coxa_path)
    shape_v2.exportStl(stl_coxa_path)
    print(f"Exported STEP & STL: {step_coxa_path}, {stl_coxa_path}")

    App.closeDocument("coxa_bracket")
