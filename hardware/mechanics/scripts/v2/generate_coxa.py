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

print("--- Generating Lasius Coxa v2 (Monolithic Joint Segment & Lightweight Truss) ---")

models_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/models"
v1_coxa_path = f"{models_dir}/custom/v1/parts/coxa_bracket.FCStd"
v2_coxa_path = f"{models_dir}/custom/v2/parts/coxa/coxa.FCStd"

export_step_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/step/custom/v2/parts/coxa"
export_stl_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/stl/custom/v2/parts/coxa"
step_coxa_path = f"{export_step_dir}/coxa.step"
stl_coxa_path = f"{export_stl_dir}/coxa.stl"


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
    # 0b. Front-Bottom Nose Corner: Update Middle Core (Y in [5.0, 25.5]) from R = 2.0 to R = 4.50 mm
    # -------------------------------------------------------------
    # In v1, the bottom nose edge was filleted with R = 2.0 mm.
    # To match the front and rear cheeks (which have R_FRONT = 4.50 mm),
    # cut away the corner material outside the R = 4.50 mm cylinder centered at (4.50, Y, 4.50).
    R_FRONT = 4.50
    box_nose_cut = Part.makeBox(R_FRONT + 1.0, 33.7, R_FRONT + 1.0, App.Vector(-1.0, -1.0, -1.0))
    cyl_nose_round = Part.makeCylinder(R_FRONT, 35.7, App.Vector(R_FRONT, -2.0, R_FRONT), App.Vector(0, 1, 0))
    cutter_nose = box_nose_cut.cut(cyl_nose_round)
    core = core.cut(cutter_nose)

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
    # 4. Coxa Servo Pocket Clearance & Pivot Axis M4 Countersink
    # -------------------------------------------------------------
    # A. Lower Coxa servo ear mounting shelf by 0.75 mm to Y = 30.90 mm so Coxa_Servo
    #    at Y = 42.75 mm sits with its horn at Y = 51.25 mm (Z_world = 53.25 mm,
    #    0.05 mm below Body_Top at Z_world = 53.30 mm -> zero collision!)
    servo_ear_recess = Part.makeBox(56.00, 5.00, 21.00, App.Vector(58.00, 30.90, -1.50))
    # B. Clear Coxa servo body pocket (X in [65.50, 106.40], Z in [-1.15, 19.15], Y in [3.85, 32.00])
    #    plus wire grommet relief at X in [58.50, 66.00], Z in [5.40, 12.60], Y in [3.85, 12.00]
    servo_body_clear = Part.makeBox(40.90, 28.15, 20.30, App.Vector(65.50, 3.85, -1.15))
    servo_wire_clear = Part.makeBox(7.50, 8.15, 7.20, App.Vector(58.50, 3.85, 5.40))
    shape = shape.cut(servo_ear_recess).cut(servo_body_clear).cut(servo_wire_clear)

    # Re-drill 4x Coxa servo mounting screw holes (X = 66.30 and 109.70, Z = 4.00 and 14.00)
    for sx_c in [66.30, 109.70]:
        for sz_c in [4.00, 14.00]:
            shape = shape.cut(Part.makeCylinder(1.10, 20.00, App.Vector(sx_c, 15.00, sz_c), App.Vector(0, 1, 0)))

    # C. Coxa Pivot Axis (X = 74.70, Z = 9.00):
    #    - Coaxial M4 through-bore (D = 4.10 mm, R = 2.05 mm)
    #    - Internal 90-deg M4 countersink cone on inside floor (Y in [1.70, 3.80], R = 2.05..4.15 mm)
    #      so Chassis_Screw at Z_leg = -11.45 mm (Y = 3.80 mm) seats flush below Coxa_Servo (Y = 3.95 mm)
    #    - Underside shim washer recess (D = 6.20 mm, Y in [-0.10, +0.35 mm]) for 0.30 mm Passscheibe
    #    - 0.05 mm underside axial relief (Y in [-0.10, +0.05 mm] for X > 58.0) so Coxa clears Body_Bottom
    bore_pivot_m4 = Part.makeCylinder(2.05, 6.00, App.Vector(74.70, -1.00, 9.00), App.Vector(0, 1, 0))
    csink_pivot_m4 = Part.makeCone(2.05, 4.15, 2.10, App.Vector(74.70, 1.70, 9.00), App.Vector(0, 1, 0))
    head_clear_m4 = Part.makeCylinder(4.15, 1.00, App.Vector(74.70, 3.80, 9.00), App.Vector(0, 1, 0))
    washer_recess_m4 = Part.makeCylinder(3.10, 0.45, App.Vector(74.70, -0.10, 9.00), App.Vector(0, 1, 0))
    bottom_relief = Part.makeBox(65.00, 0.15, 40.00, App.Vector(58.00, -0.10, -10.00))
    shape = (
        shape.cut(bore_pivot_m4)
        .cut(csink_pivot_m4)
        .cut(head_clear_m4)
        .cut(washer_recess_m4)
        .cut(bottom_relief)
    )

    # -------------------------------------------------------------
    # 5. Cheek 45-Degree Bionic Truss Windows (Konzept 1: Symmetrical A-Truss & Flank Windows)
    # -------------------------------------------------------------
    # Implements Style-Guide Section 3 compliant 45-degree Warren and A-truss windows
    # across the front cheek (Y in [0.00, 5.00]) and rear cheek (Y in [25.50, 31.70]),
    # perfectly mirrored about the horizontal midline Z = 9.00 mm (Z_top(x) = 18.00 - Z_bot(x)).
    # Interior hardware chamber (Y in [5.00, 25.50]) is left 100% untouched.

    # A. Flank Windows (Zone 1: X in [9.70, 21.20])
    # Upper flank window above Femur servo mounting belt (Z in [20.50, 30.00]):
    p_flank_top = [
        App.Vector(9.70, 20.50, 0.0),
        App.Vector(21.20, 20.50, 0.0),
        App.Vector(21.20, 30.00, 0.0),
        App.Vector(19.20, 30.00, 0.0),
    ]
    f_fl_t = make_filleted_polygon_2d(p_flank_top, R_FILLET)

    # Lower flank window flanking counter-bearing tab (Z in [-12.00, -2.50]):
    p_flank_bot = [
        App.Vector(9.70, -2.50, 0.0),
        App.Vector(19.20, -12.00, 0.0),
        App.Vector(21.20, -12.00, 0.0),
        App.Vector(21.20, -2.50, 0.0),
    ]
    f_fl_b = make_filleted_polygon_2d(p_flank_bot, R_FILLET)

    # B. Central Bridge Windows (Zone 2: X in [27.00, 51.50])
    # 1. Inner Upper Triangle (Chevron half, hypotenuse at -45 deg, bottom at Z = 10.25):
    p_chev_sp_t = [
        App.Vector(27.00, 10.25, 0.0),
        App.Vector(44.75, 10.25, 0.0),
        App.Vector(27.00, 28.00, 0.0),
    ]
    f_chev_sp_t = make_filleted_polygon_2d(p_chev_sp_t, R_FILLET)

    # 2. Inner Lower Triangle (mirror across Z = 9.00 mm, hypotenuse at +45 deg, top at Z = 7.75):
    p_chev_sp_b = [
        App.Vector(27.00, -10.00, 0.0),
        App.Vector(44.75, 7.75, 0.0),
        App.Vector(27.00, 7.75, 0.0),
    ]
    f_chev_sp_b = make_filleted_polygon_2d(p_chev_sp_b, R_FILLET)

    # 3. Outer Upper Trapezoid (parallel 45-deg strut, S-curve chord margin >= 2.50 mm):
    p_br_top = [
        App.Vector(29.00, 29.54, 0.0),
        App.Vector(48.29, 10.25, 0.0),
        App.Vector(51.50, 10.25, 0.0),
        App.Vector(51.50, 19.80, 0.0),
    ]
    f_br_t = make_filleted_polygon_2d(p_br_top, R_FILLET)

    # 4. Outer Lower Trapezoid (mirror across Z = 9.00 mm):
    p_br_bot = [
        App.Vector(29.00, -11.54, 0.0),
        App.Vector(51.50, -1.80, 0.0),
        App.Vector(51.50, 6.50, 0.0),
        App.Vector(48.29, 6.50, 0.0),
    ]
    f_br_b = make_filleted_polygon_2d(p_br_bot, R_FILLET)

    # Cut both Front Cheek (Y in [0.00, 5.00]) and Rear Cheek (Y in [25.50, 31.70])
    for f in [f_fl_t, f_fl_b, f_chev_sp_t, f_chev_sp_b, f_br_t, f_br_b]:
        cut_f = extrude_face_xz(f, -1.0, 7.0)
        cut_r = extrude_face_xz(f, 24.5, 8.5)
        shape = shape.cut(cut_f).cut(cut_r)

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


if __name__ in ("__main__", "generate_coxa"):
    shape_v2 = build_coxa_bracket_v2_shape()
    print(
        f"Coxa v2 Valid: {shape_v2.isValid()}, Solids: {len(shape_v2.Solids)}, "
        f"Volume: {shape_v2.Volume:.1f} mm^3, Mass (PETG): {shape_v2.Volume * 1.27 / 1000.0:.1f} g"
    )

    os.makedirs(os.path.dirname(v2_coxa_path), exist_ok=True)
    os.makedirs(export_step_dir, exist_ok=True)
    os.makedirs(export_stl_dir, exist_ok=True)

    doc = App.newDocument("coxa")
    obj = doc.addObject("Part::Feature", "Coxa")
    obj.Label = "Coxa v2 (Monolithic Joint Segment & Lightweight Truss)"
    obj.Shape = shape_v2

    doc.recompute()
    doc.saveAs(v2_coxa_path)
    print(f"Saved FreeCAD model: {v2_coxa_path}")

    shape_v2.exportStep(step_coxa_path)
    shape_v2.exportStl(stl_coxa_path)
    print(f"Exported STEP & STL: {step_coxa_path}, {stl_coxa_path}")

    App.closeDocument("coxa")
    import sys
    sys.exit(0)
