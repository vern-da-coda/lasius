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
  2. 45-Degree Triangular Truss Gusset ("Versteifungs-Gusset"):
     Connects the lower counter-bearing tab (X = 25.70, Z = -14.50) back to the main horizontal
     bridge (X = 40.20, Z = 0.00), eliminating the cantilever notch and abrading bending
     moments as pure tension/compression via a rounded triangular truss window.
  3. Organic Weight-Relief Truss Windows & Cavities:
     Symmetric dual-flange I-beam windows in the front and rear walls of the central bridge
     (X in [28.5, 57.5]) and rear tail wall (X in [84.5, 106.0]) with G1-continuous R = 2.80 mm
     fillet corners, plus vertical cavities in the massive central bulkhead and rear tail block.
  4. Flowing, filleted design language harmonized with Femur v2 and Tibia v2.
"""

import math
import os
import FreeCAD as App
import Part

print("--- Generating Lasius Coxa Bracket v2 (Organic Truss + 45-deg Gusset + Inverted M4 Seat) ---")

models_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/models"
v1_coxa_path = f"{models_dir}/custom/v1/parts/coxa_bracket.FCStd"
v2_coxa_path = f"{models_dir}/custom/v2/parts/coxa_bracket.FCStd"

export_step_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/step/custom/v2/parts"
export_stl_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/stl/custom/v2/parts"
step_coxa_path = f"{export_step_dir}/coxa_bracket.step"
stl_coxa_path = f"{export_stl_dir}/coxa_bracket.stl"


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
    # 1. Option A Inverted M4 Counter-Bearing Seat (X = 18.20, Y = 15.25)
    # -------------------------------------------------------------
    cx, cy = 18.20, 15.25
    heal_plug = Part.makeCylinder(4.50, 3.00, App.Vector(cx, cy, -14.50))
    shape = shape.fuse(heal_plug)

    screw_bore = Part.makeCylinder(2.05, 5.00, App.Vector(cx, cy, -15.50))
    nut_pocket = make_hex_nut_pocket_z(cx, cy, -13.90, -11.00, sw=7.10)
    shape = shape.cut(screw_bore).cut(nut_pocket)

    # -------------------------------------------------------------
    # 2. 45-Degree Triangular Truss Gusset for the Lower Bearing Tab
    # -------------------------------------------------------------
    # Connects (X = 25.70, Z = -14.50) to (X = 40.20, Z = 0.00) across full width Y in [0.00, 31.70]
    pts_g = [
        App.Vector(25.70, 0.00, -14.50),
        App.Vector(40.20, 0.00, 0.00),
        App.Vector(25.70, 0.00, 0.00),
        App.Vector(25.70, 0.00, -14.50),
    ]
    gusset_solid = Part.Face(Part.makePolygon(pts_g)).extrude(App.Vector(0.0, 31.70, 0.0))
    shape = shape.fuse(gusset_solid)

    # Cut filleted triangular weight-relief window through the gusset web:
    r_gt = 1.60
    e_gt = [
        Part.makeLine(App.Vector(28.0, -2.0, -11.0 + r_gt), App.Vector(28.0, -2.0, -2.5 - r_gt)),
        Part.Arc(
            App.Vector(28.0, -2.0, -2.5 - r_gt),
            App.Vector(28.0 + r_gt * (1 - 1 / math.sqrt(2)), -2.0, -2.5 - r_gt * (1 - 1 / math.sqrt(2))),
            App.Vector(28.0 + r_gt, -2.0, -2.5),
        ).toShape(),
        Part.makeLine(App.Vector(28.0 + r_gt, -2.0, -2.5), App.Vector(36.5 - 2 * r_gt, -2.0, -2.5)),
        Part.Arc(
            App.Vector(36.5 - 2 * r_gt, -2.0, -2.5),
            App.Vector(36.5 - r_gt, -2.0, -2.5 - 0.5 * r_gt),
            App.Vector(36.5 - 0.7 * r_gt, -2.0, -2.5 - 1.4 * r_gt),
        ).toShape(),
        Part.makeLine(
            App.Vector(36.5 - 0.7 * r_gt, -2.0, -2.5 - 1.4 * r_gt),
            App.Vector(28.0 + 1.4 * r_gt, -2.0, -11.0 + 0.7 * r_gt),
        ),
        Part.Arc(
            App.Vector(28.0 + 1.4 * r_gt, -2.0, -11.0 + 0.7 * r_gt),
            App.Vector(28.0 + 0.5 * r_gt, -2.0, -11.0),
            App.Vector(28.0, -2.0, -11.0 + r_gt),
        ).toShape(),
    ]
    cut_gw = Part.Face(Part.Wire(e_gt)).extrude(App.Vector(0.0, 36.0, 0.0))
    shape = shape.cut(cut_gw)

    # -------------------------------------------------------------
    # 3. 45-Degree Symmetrical A-Truss (Chevron) Windows in Bridge & Tail
    # -------------------------------------------------------------
    # A. Central Bridge Symmetrical A-Truss (X in [28.5, 57.5], Z in [2.5, 15.5])
    # 45-degree diagonal struts (w_strut = 3.50 mm) meeting at top apex (X = 43.00, Z = 12.50)
    # 1. Central triangle (apex up)
    p_c1 = App.Vector(33.00, 2.50, 0.0)
    p_c2 = App.Vector(53.00, 2.50, 0.0)
    p_c3 = App.Vector(43.00, 12.50, 0.0)
    fc = make_filleted_polygon_2d([p_c1, p_c2, p_c3], 1.60)

    # 2. Left corner triangle (hypotenuse at 45 deg, strut width = 3.50 mm)
    p_l1 = App.Vector(28.50, 3.00, 0.0)
    p_l2 = App.Vector(41.00, 15.50, 0.0)
    p_l3 = App.Vector(28.50, 15.50, 0.0)
    fl = make_filleted_polygon_2d([p_l1, p_l2, p_l3], 1.60)

    # 3. Right corner triangle (mirror of left across X = 43.0)
    p_r1 = App.Vector(45.00, 15.50, 0.0)
    p_r2 = App.Vector(57.50, 3.00, 0.0)
    p_r3 = App.Vector(57.50, 15.50, 0.0)
    fr = make_filleted_polygon_2d([p_r1, p_r2, p_r3], 1.60)

    # Cut A-truss into Bridge Front Wall (Y in [0.0, 5.0]):
    for f in [fc, fl, fr]:
        shape = shape.cut(extrude_face_xz(f, -2.0, 8.0))

    # Cut matching A-truss into Bridge Rear Wall (Y in [25.5, 31.7]):
    for f in [fc, fl, fr]:
        shape = shape.cut(extrude_face_xz(f, 26.0, 8.0))

    # B. Rear Tail Diagonal Truss Window (X in [84.5, 106.0], Z in [2.0, 16.0])
    # Diagonal strut connecting (84.5, 2.0) to (106.0, 16.0)
    p_t_bot = [App.Vector(87.5, 2.0, 0.0), App.Vector(106.0, 2.0, 0.0), App.Vector(106.0, 13.0, 0.0)]
    f_t_bot = make_filleted_polygon_2d(p_t_bot, 1.60)

    p_t_top = [App.Vector(84.5, 5.0, 0.0), App.Vector(103.0, 16.0, 0.0), App.Vector(84.5, 16.0, 0.0)]
    f_t_top = make_filleted_polygon_2d(p_t_top, 1.60)

    shape = shape.cut(extrude_face_xz(f_t_bot, -2.0, 8.0))
    shape = shape.cut(extrude_face_xz(f_t_top, -2.0, 8.0))

    # -------------------------------------------------------------
    # 4. Bulkhead & Tail Block Weight-Relief Cavities
    # -------------------------------------------------------------
    # A. Central Bulkhead Pocket (X in [55.0, 61.5], Y in [7.5, 28.5], Z in [2.0, 16.0]):
    f_bulk = make_rounded_rect_face_2d(7.50, 28.50, 2.00, 16.00, 2.00)
    edges_bulk = []
    for e in f_bulk.OuterWire.Edges:
        pts = [App.Vector(55.0, v.Point.x, v.Point.y) for v in e.Vertexes]
        if "Line" in str(type(e.Curve)):
            edges_bulk.append(Part.makeLine(pts[0], pts[1]))
        else:
            pm = e.valueAt(0.5 * (e.FirstParameter + e.LastParameter))
            edges_bulk.append(Part.Arc(pts[0], App.Vector(55.0, pm.x, pm.y), pts[1]).toShape())
    cut_bulk = Part.Face(Part.Wire(edges_bulk)).extrude(App.Vector(6.5, 0.0, 0.0))
    shape = shape.cut(cut_bulk)

    # B. Rear Tail End-Block Pocket (X in [111.0, 116.0], Y in [7.0, 25.0], Z in [2.0, 16.0]):
    f_tail = make_rounded_rect_face_2d(7.00, 25.00, 2.00, 16.00, 2.00)
    edges_tail = []
    for e in f_tail.OuterWire.Edges:
        pts = [App.Vector(111.0, v.Point.x, v.Point.y) for v in e.Vertexes]
        if "Line" in str(type(e.Curve)):
            edges_tail.append(Part.makeLine(pts[0], pts[1]))
        else:
            pm = e.valueAt(0.5 * (e.FirstParameter + e.LastParameter))
            edges_tail.append(Part.Arc(pts[0], App.Vector(111.0, pm.x, pm.y), pts[1]).toShape())
    cut_tail = Part.Face(Part.Wire(edges_tail)).extrude(App.Vector(5.0, 0.0, 0.0))
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
