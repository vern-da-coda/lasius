#!/usr/bin/env python3
"""
Generate Lasius Hexapod Coxa Bracket v2 (for Monolithic Femur v2 Assembly)
- Inherits the base geometry of v1 coxa_bracket.FCStd
- Adapts the Femur pivot counter-bearing seat at local (X = 18.20, Y = 15.25, Z in [-14.50, -11.50])
  to Option A (inverted counter-bearing fastener):
  * Heals the old internal countersunk screw cone
  * Cuts an internal anti-rotation M4 hex nut pocket (SW 7.10 mm, depth 2.40 mm, Z in [-13.90, -11.50])
    with a 0.60 mm solid retaining shoulder (Z in [-14.50, -13.90]) and coaxial D = 4.10 mm M4 bore
  * Allows the Coxa_Bracket + Femur_Servo subassembly to slide radially into the monolithic
    v2 Femur U-jaw with zero rear screw protrusion
"""

import math
import os
import FreeCAD as App
import Part

print("--- Generating Lasius Coxa Bracket v2 (with Internal M4 Hex Nut Seat for Monolithic Femur) ---")

models_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/models"
v1_coxa_path = f"{models_dir}/custom/v1/parts/coxa_bracket.FCStd"
v2_coxa_path = f"{models_dir}/custom/v2/parts/coxa_bracket.FCStd"

export_step_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/step/custom/v2/parts"
export_stl_dir = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/stl/custom/v2/parts"
step_coxa_path = f"{export_step_dir}/coxa_bracket.step"
stl_coxa_path = f"{export_stl_dir}/coxa_bracket.stl"


def make_hex_nut_pocket_z(cx, cy, z_bottom, z_top, sw=7.10):
    r_circum = sw / math.sqrt(3.0)
    pts = []
    for i in range(6):
        ang = math.radians(60.0 * i)
        pts.append(App.Vector(cx + r_circum * math.cos(ang), cy + r_circum * math.sin(ang), z_bottom))
    pts.append(pts[0])
    wire = Part.makePolygon(pts)
    return Part.Face(wire).extrude(App.Vector(0, 0, z_top - z_bottom))


def build_coxa_bracket_v2_shape():
    doc_v1 = App.openDocument(v1_coxa_path)
    shape_v1 = doc_v1.getObject("Coxa_Bracket").Shape.copy()
    App.closeDocument(doc_v1.Name)

    # Femur pivot axis in Coxa_Bracket local coordinates is at (X = 18.20, Y = 15.25),
    # with the floor spanning Z_local in [-14.50, -11.50] mm (where Z = -11.50 is inside
    # the Femur_Servo pocket and Z = -14.50 is the outer bearing/washer face).
    cx, cy = 18.20, 15.25

    # 1. Heal old countersunk screw seat in Z in [-14.50, -11.50]:
    heal_plug = Part.makeCylinder(4.50, 3.00, App.Vector(cx, cy, -14.50))
    shape_v2 = shape_v1.fuse(heal_plug)

    # 2. Cut coaxial M4 screw through-bore (D = 4.10 mm, R = 2.05 mm):
    screw_bore = Part.makeCylinder(2.05, 5.00, App.Vector(cx, cy, -15.50))

    # 3. Cut internal M4 hex nut pocket (SW = 7.10 mm) from Z = -13.90 to Z = -11.00
    #    (depth = 2.40 mm inside the 3.00 mm floor, leaving a 0.60 mm solid retaining shoulder
    #     at Z in [-14.50, -13.90] mm):
    nut_pocket = make_hex_nut_pocket_z(cx, cy, -13.90, -11.00, sw=7.10)

    shape_v2 = shape_v2.cut(screw_bore).cut(nut_pocket).removeSplitter()
    return shape_v2


if __name__ == "__main__":
    shape_v2 = build_coxa_bracket_v2_shape()
    print(
        f"Coxa_Bracket v2 Valid: {shape_v2.isValid()}, Solids: {len(shape_v2.Solids)}, "
        f"Volume: {shape_v2.Volume:.1f} mm^3, BB: {shape_v2.BoundBox}"
    )

    os.makedirs(os.path.dirname(v2_coxa_path), exist_ok=True)
    os.makedirs(export_step_dir, exist_ok=True)
    os.makedirs(export_stl_dir, exist_ok=True)

    doc = App.newDocument("coxa_bracket")
    obj = doc.addObject("Part::Feature", "Coxa_Bracket")
    obj.Label = "Coxa Bracket v2 (Internal M4 Nut Seat)"
    obj.Shape = shape_v2

    doc.recompute()
    doc.saveAs(v2_coxa_path)
    print(f"Saved FreeCAD model: {v2_coxa_path}")

    shape_v2.exportStep(step_coxa_path)
    shape_v2.exportStl(stl_coxa_path)
    print(f"Exported STEP & STL: {step_coxa_path}, {stl_coxa_path}")

    App.closeDocument("coxa_bracket")
