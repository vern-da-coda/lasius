#!/usr/bin/env python3
"""
Generate Lasius Hexapod Full Body Assembly v2 FreeCAD Model (custom/v2/body_assembly.FCStd)
Assembles the complete 18-DOF Hexapod robot from modular L1 subassemblies:
1. Chassis Assembly (custom/v2/chassis_assembly.FCStd):
   - CFRP bottom & top plates (../v1/parts/body_{bottom,top}.FCStd)
   - Monocoque Central Core Assembly (chassis_core_assembly.FCStd: core + 2x PCA9685 + TCA9548A + 2S LiPo)
   - Belly Pan skid plate + VL53L5CX 9-zone ToF sensor
   - Raspberry Pi 4 mounting plate + Raspberry Pi 4 Model B
   - Draped Plexiglas canopy + louvered service cover
2. Six modular v2 legs:
   - Left side legs (FL, ML, RL): custom/v2/leg_assembly.FCStd
   - Right side legs (FR, MR, RR): custom/v2/leg_right_assembly.FCStd
"""

import os
import sys
import FreeCAD as App

print("--- Generating Lasius Full Body Assembly v2 (custom/v2/body_assembly.FCStd) ---")

doc_name = "body_assembly"
models_base = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/models"
v2_asm_dir = f"{models_base}/custom/v2"
fcstd_path = f"{v2_asm_dir}/body_assembly.FCStd"


def build_body_assembly():
    if doc_name in App.listDocuments():
        try:
            App.closeDocument(doc_name)
        except Exception:
            pass

    doc = App.newDocument(doc_name)
    os.makedirs(v2_asm_dir, exist_ok=True)
    doc.saveAs(fcstd_path)

    doc_chassis = App.openDocument(f"{v2_asm_dir}/chassis_assembly.FCStd")
    doc_leg = App.openDocument(f"{v2_asm_dir}/leg_assembly.FCStd")
    doc_leg_r = App.openDocument(f"{v2_asm_dir}/leg_right_assembly.FCStd")

    asm_part = doc.addObject("App::Part", "Body_Assembly_v2")
    asm_part.Label = "Lasius Full Body Assembly v2 (Chassis Assembly + 6x Modular Legs)"
    for o in asm_part.Origin.OutList:
        if hasattr(o, "Visibility"):
            o.Visibility = False
        if hasattr(o, "ViewObject") and o.ViewObject:
            o.ViewObject.Visibility = False
    asm_part.Origin.Visibility = False
    if hasattr(asm_part.Origin, "ViewObject") and asm_part.Origin.ViewObject:
        asm_part.Origin.ViewObject.Visibility = False
    asm_part.Visibility = True

    def make_link(name, label, target_obj, placement, parent=asm_part):
        lnk = doc.addObject("App::Link", name)
        lnk.setLink(target_obj)
        lnk.Label = label
        lnk.Placement = placement
        parent.addObject(lnk)
        lnk.Visibility = True
        if hasattr(lnk, "ViewObject") and lnk.ViewObject is not None:
            lnk.ViewObject.Visibility = True
        return lnk

    # -------------------------------------------------------------
    # 1. Complete Chassis Subassembly (L1)
    # -------------------------------------------------------------
    chassis_target = doc_chassis.getObject("Chassis_Assembly")
    make_link(
        "Chassis_Assembly",
        "1. Chassis Assembly (CFRP Plates + Monocoque Core + Torso Electronics, v2)",
        chassis_target,
        App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation()),
    )

    # -------------------------------------------------------------
    # 2. Six Modular v2 Legs (L1)
    # -------------------------------------------------------------
    z_leg_offset = 17.25

    def get_leg_placement(x_hole, y_hole, z_offset, yaw_deg, is_mirrored):
        if is_mirrored:
            p_local_shift = App.Placement(App.Vector(0.0, 2.50, 0.0), App.Rotation())
        else:
            p_local_shift = App.Placement(App.Vector(0.0, -2.50, 0.0), App.Rotation())
        p_world = App.Placement(App.Vector(x_hole, y_hole, z_offset), App.Rotation(App.Vector(0, 0, 1), yaw_deg))
        return p_world.multiply(p_local_shift)

    leg_mounts = [
        ("Leg_Front_Left",   "2. Leg Front Left (FL, v2)",                 86.0,  65.0,   45.0, False),
        ("Leg_Middle_Left",  "3. Leg Middle Left (ML, v2)",                 0.0,  75.0,   90.0, False),
        ("Leg_Rear_Left",    "4. Leg Rear Left (RL, v2)",                 -86.0,  65.0,  135.0, False),
        ("Leg_Front_Right",  "5. Leg Front Right (FR, v2) [Mirrored]",     86.0, -65.0,  -45.0, True),
        ("Leg_Middle_Right", "6. Leg Middle Right (MR, v2) [Mirrored]",     0.0, -75.0,  -90.0, True),
        ("Leg_Rear_Right",   "7. Leg Rear Right (RR, v2) [Mirrored]",     -86.0, -65.0, -135.0, True),
    ]

    leg_target_left = getattr(doc_leg, "Leg_Assembly_v2", getattr(doc_leg, "Leg_Assembly", None))
    leg_target_right = getattr(doc_leg_r, "Leg_Right_Assembly_v2", getattr(doc_leg_r, "Leg_Right_Assembly", None))

    for l_name, l_label, lx, ly, l_yaw, l_mirrored in leg_mounts:
        p_leg = get_leg_placement(lx, ly, z_leg_offset, l_yaw, l_mirrored)
        target_obj = leg_target_right if l_mirrored else leg_target_left
        make_link(l_name, l_label, target_obj, p_leg)

    doc.recompute()
    doc.save()
    bbox = asm_part.Shape.BoundBox
    print(f"✔ Saved Body Assembly: {fcstd_path}")
    print(f"  Valid: {asm_part.Shape.isValid()}, BB: X=[{bbox.XMin:.2f}, {bbox.XMax:.2f}], Y=[{bbox.YMin:.2f}, {bbox.YMax:.2f}], Z=[{bbox.ZMin:.2f}, {bbox.ZMax:.2f}]")
    return doc


if __name__ in ("__main__", "generate_body_assembly"):
    build_body_assembly()
    if __name__ == "__main__":
        sys.exit(0)
