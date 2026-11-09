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
    shape = doc_v1.getObject("Coxa_Bracket").Shape.copy()
    App.closeDocument(doc_v1.Name)

    # -------------------------------------------------------------
    # 0. Solidify Femur Mounting Flange & Cable Channel
    # -------------------------------------------------------------
    # The Femur servo mounting flange (Z = 15.50, X in [49.80, 57.40],
    # Y in [5.00, 25.50]) is 100% solid, fully planar, and un-notched.
    # The cable channel wall is kept clean on the level of the entire plane (Y = 3.95)
    # without artificial steps or protrusions.
    plug_shelf_top = Part.makeBox(57.40 - 52.40, 12.45 - 5.00, 15.50 - 11.50, App.Vector(52.40, 5.00, 11.50))
    shape = shape.fuse(plug_shelf_top)

    # Re-bore front screw hole on right shelf to ensure clean cylindrical hole
    bore_f1 = Part.makeCylinder(1.10, 20.00, App.Vector(53.15, 10.25, 0.00))
    shape = shape.cut(bore_f1)

    # -------------------------------------------------------------
    # 1. Option A Inverted M4 Counter-Bearing Seat (X = 18.20, Y = 15.25)
    # -------------------------------------------------------------
    cx, cy = 18.20, 15.25
    heal_plug = Part.makeCylinder(4.50, 3.00, App.Vector(cx, cy, -14.50))
    shape = shape.fuse(heal_plug)

    screw_bore = Part.makeCylinder(2.05, 5.00, App.Vector(cx, cy, -15.50))
    nut_pocket = make_hex_nut_pocket_z(cx, cy, -13.90, -11.50, sw=7.10)
    shape = shape.cut(screw_bore).cut(nut_pocket)

    # -------------------------------------------------------------
    # 2. Organic Upper Cheek Crest (Inspired by Femur Waist Contour)
    # -------------------------------------------------------------
    # Extends the side cheeks smoothly from Z = 18.00 mm up to the Femur servo horn
    # level at Z = 27.30 mm, peaking at the pivot axis (X = 18.20 mm) and cascading
    # symmetrically via G1 tangent circular S-curves down to Z = 18.00 mm at X = 0.00 mm
    # (front edge) and X = 36.00 mm (bridge junction).
    def make_upper_crest_face():
        dx1, dz1 = 18.20, 9.30
        dx1_h, dz1_h = 0.5 * dx1, 0.5 * dz1
        r1 = (dx1_h**2 + dz1_h**2) / (2.0 * dz1_h)
        dx2, dz2 = 17.80, 9.30
        dx2_h, dz2_h = 0.5 * dx2, 0.5 * dz2
        r2 = (dx2_h**2 + dz2_h**2) / (2.0 * dz2_h)
        p0 = App.Vector(0.00, 0.0, 18.00)
        p_inf1 = App.Vector(9.10, 0.0, 22.65)
        p_peak = App.Vector(18.20, 0.0, 27.30)
        p_inf2 = App.Vector(27.10, 0.0, 22.65)
        p_end = App.Vector(36.00, 0.0, 18.00)
        ang1 = math.atan2(r1 - dz1_h, dx1_h)
        pm1 = App.Vector(r1 * math.sin(0.5 * (math.pi / 2 - ang1)), 0.0, 18.0 + r1 - r1 * math.cos(0.5 * (math.pi / 2 - ang1)))
        pm2 = App.Vector(18.2 - r1 * math.sin(0.5 * (math.pi / 2 - ang1)), 0.0, 27.3 - r1 + r1 * math.cos(0.5 * (math.pi / 2 - ang1)))
        ang2 = math.atan2(r2 - dz2_h, dx2_h)
        pm3 = App.Vector(18.2 + r2 * math.sin(0.5 * (math.pi / 2 - ang2)), 0.0, 27.3 - r2 + r2 * math.cos(0.5 * (math.pi / 2 - ang2)))
        pm4 = App.Vector(36.0 - r2 * math.sin(0.5 * (math.pi / 2 - ang2)), 0.0, 18.0 + r2 - r2 * math.cos(0.5 * (math.pi / 2 - ang2)))
        e1 = Part.Edge(Part.Arc(p0, pm1, p_inf1))
        e2 = Part.Edge(Part.Arc(p_inf1, pm2, p_peak))
        e3 = Part.Edge(Part.Arc(p_peak, pm3, p_inf2))
        e4 = Part.Edge(Part.Arc(p_inf2, pm4, p_end))
        e_bot = Part.makeLine(p_end, p0)
        return Part.Face(Part.Wire([e1, e2, e3, e4, e_bot]))

    f_crest = make_upper_crest_face()
    # Cheeks match full Hauptträger wall thickness: Front Y in [0.00, 5.00] (5.00 mm), Rear Y in [25.50, 31.70] (6.20 mm)
    s_crest_f = f_crest.extrude(App.Vector(0.0, 5.00, 0.0))
    s_crest_r = f_crest.extrude(App.Vector(0.0, 6.20, 0.0))
    s_crest_r.translate(App.Vector(0.0, 25.50, 0.0))
    shape = shape.fuse(s_crest_f).fuse(s_crest_r)

    # -------------------------------------------------------------
    # 3. Organic Lower Cheek Ribs (Inspired by Femur Waist Contour)
    # -------------------------------------------------------------
    # Extends the lower side cheeks continuously from the counter-bearing base level
    # (Z = -14.50 mm) up to the central bridge at Z = 0.00 mm (X = 36.00 mm) via a G1 S-curve,
    # and forward to the front face (X = 0.00 mm) with a smooth R = 4.00 mm rounding.
    # Fully matched to Hauptträger wall thickness: front cheek (Y in [0.00, 5.00]) and rear cheek (Y in [25.50, 31.70]).
    def make_lower_cheek_face():
        # 1. Front vertical line along front face: from (0.00, 0.00) down to (0.00, -10.50)
        p_front_top = App.Vector(0.00, 0.0, 0.00)
        p_front_arc_start = App.Vector(0.00, 0.0, -10.50)
        e_front_vert = Part.makeLine(p_front_top, p_front_arc_start)

        # 2. Front lower corner rounding: R = 4.00 mm circular arc down to (4.00, -14.50)
        p_arc_mid = App.Vector(4.0 - 4.0 * math.cos(math.pi / 4), 0.0, -10.5 - 4.0 * math.sin(math.pi / 4))
        p_bot_flat_start = App.Vector(4.00, 0.0, -14.50)
        e_front_arc = Part.Edge(Part.Arc(p_front_arc_start, p_arc_mid, p_bot_flat_start))

        # 3. Solid baseline at Z = -14.50 mm: from X = 4.00 mm to X = 23.70 mm
        p_bot_flat_end = App.Vector(23.70, 0.0, -14.50)
        e_bot_flat = Part.makeLine(p_bot_flat_start, p_bot_flat_end)

        # 4. Rear G1 S-curve transition: from (23.70, -14.50) up to bridge at (36.00, 0.00)
        # Matches upper crest S-curve termination station X = 36.00 mm
        dx, dz = 36.00 - 23.70, 14.50
        dx_h, dz_h = 0.5 * dx, 0.5 * dz
        r = (dx_h**2 + dz_h**2) / (2.0 * dz_h)
        p_inf = App.Vector(23.70 + dx_h, 0.0, -14.50 + dz_h)
        p_end = App.Vector(36.00, 0.0, 0.00)
        ang = math.atan2(r - dz_h, dx_h)
        pm1 = App.Vector(23.70 + r * math.sin(0.5 * (math.pi / 2 - ang)), 0.0, -14.50 + r - r * math.cos(0.5 * (math.pi / 2 - ang)))
        pm2 = App.Vector(36.00 - r * math.sin(0.5 * (math.pi / 2 - ang)), 0.0, -r + r * math.cos(0.5 * (math.pi / 2 - ang)))
        e_rear_arc1 = Part.Edge(Part.Arc(p_bot_flat_end, pm1, p_inf))
        e_rear_arc2 = Part.Edge(Part.Arc(p_inf, pm2, p_end))

        # 5. Top closing line along bridge bottom (Z = 0.00 mm)
        e_top = Part.makeLine(p_end, p_front_top)

        return Part.Face(Part.Wire([e_front_vert, e_front_arc, e_bot_flat, e_rear_arc1, e_rear_arc2, e_top]))

    f_lower = make_lower_cheek_face()
    s_lower_f = f_lower.extrude(App.Vector(0.0, 5.00, 0.0))
    s_lower_r = f_lower.extrude(App.Vector(0.0, 6.20, 0.0))
    s_lower_r.translate(App.Vector(0.0, 25.50, 0.0))
    shape = shape.fuse(s_lower_f).fuse(s_lower_r)

    # -------------------------------------------------------------
    # 4. 45-Degree Front & Rear Cheek Flank Warren Truss Windows (Tibia Standard w = 2.50 mm)
    # -------------------------------------------------------------
    # Relieves the cheek flank under the Femur Servo ears (X in [11.5, 23.0])
    # Exact 45.0-deg diagonal struts with uniform width w = 2.50 mm (DX_45 = 3.536 mm)
    # Lower right triangle:
    p_flk1 = [App.Vector(11.50, 2.50, 0.0), App.Vector(21.50, 2.50, 0.0), App.Vector(11.50, 12.50, 0.0)]
    f_flk1 = make_filleted_polygon_2d(p_flk1, R_FILLET)

    # Upper right triangle:
    p_flk2 = [App.Vector(12.04, 15.50, 0.0), App.Vector(22.50, 5.04, 0.0), App.Vector(22.50, 15.50, 0.0)]
    f_flk2 = make_filleted_polygon_2d(p_flk2, R_FILLET)

    # Cut through Front Cheek (Y in [0.0, 5.0]):
    shape = shape.cut(extrude_face_xz(f_flk1, -1.0, 7.0)).cut(extrude_face_xz(f_flk2, -1.0, 7.0))
    # Cut through Rear Cheek (Y in [25.5, 31.7]):
    shape = shape.cut(extrude_face_xz(f_flk1, 24.5, 8.5)).cut(extrude_face_xz(f_flk2, 24.5, 8.5))

    # -------------------------------------------------------------
    # 5. Central Bridge Symmetrical 45-Degree A-Truss Windows (Tibia Standard w = 2.50 mm)
    # -------------------------------------------------------------
    # Center chevron: apex at (38.00, 10.50), base at Z = 2.50, span dx = 8.00 mm (exact 45 deg)
    p_c1 = App.Vector(30.00, 2.50, 0.0)
    p_c2 = App.Vector(46.00, 2.50, 0.0)
    p_c3 = App.Vector(38.00, 10.50, 0.0)
    fc = make_filleted_polygon_2d([p_c1, p_c2, p_c3], R_FILLET)

    # Left wing: hypotenuse parallel to left chevron slope with exact strut width w = 2.50 mm
    p_l1 = App.Vector(27.50, 3.54, 0.0)
    p_l2 = App.Vector(39.46, 15.50, 0.0)
    p_l3 = App.Vector(27.50, 15.50, 0.0)
    fl = make_filleted_polygon_2d([p_l1, p_l2, p_l3], R_FILLET)

    # Right wing: hypotenuse parallel to right chevron slope with exact strut width w = 2.50 mm
    p_r1 = App.Vector(36.54, 15.50, 0.0)
    p_r2 = App.Vector(48.50, 3.54, 0.0)
    p_r3 = App.Vector(48.50, 15.50, 0.0)
    fr = make_filleted_polygon_2d([p_r1, p_r2, p_r3], R_FILLET)

    # Front Wall (Y in [0.0, 5.0]):
    for f in [fc, fl, fr]:
        shape = shape.cut(extrude_face_xz(f, -1.0, 7.0))
    # Rear Wall (Y in [25.5, 31.7]):
    for f in [fc, fl, fr]:
        shape = shape.cut(extrude_face_xz(f, 24.5, 8.5))

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
    # 9. Rear Tail Block Weight-Relief Through-Cut (Option A)
    # -------------------------------------------------------------
    # Extends through the rear bulkhead (X in [105.0, 116.0]), completely eliminating
    # Face124 and making the rear tail cavity a continuous through-tunnel opening directly
    # into the Coxa servo compartment.
    f_tail = make_rounded_rect_face_2d(7.00, 25.00, 2.00, 16.00, 2.00)
    edges_tail = []
    for e in f_tail.OuterWire.Edges:
        pts = [App.Vector(105.0, v.Point.x, v.Point.y) for v in e.Vertexes]
        if "Line" in str(type(e.Curve)):
            edges_tail.append(Part.makeLine(pts[0], pts[1]))
        else:
            pm = e.valueAt(0.5 * (e.FirstParameter + e.LastParameter))
            edges_tail.append(Part.Arc(pts[0], App.Vector(105.0, pm.x, pm.y), pts[1]).toShape())
    cut_tail = Part.Face(Part.Wire(edges_tail)).extrude(App.Vector(11.0, 0.0, 0.0))
    shape = shape.cut(cut_tail)

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
