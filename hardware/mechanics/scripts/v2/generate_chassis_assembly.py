#!/usr/bin/env python3
"""
Generate Lasius Hexapod Chassis Assembly v2 FreeCAD Model (custom/v2/chassis_assembly.FCStd)
Assembles the complete self-contained torso / base_link structure (without legs):
1. Chassis bottom plate (../v1/parts/body_bottom.FCStd) at Z = 0.00 .. 2.00 mm
2. Chassis top plate (../v1/parts/body_top.FCStd) at Z = 53.30 .. 55.30 mm
3. Monocoque Central Core Assembly (custom/v2/chassis_core_assembly.FCStd) at Z = 2.00 .. 53.30 mm
   (encapsulating dual vertical PCA9685 PWM drivers, TCA9548A I2C mux, and 2S LiPo battery)
4. Chassis Belly Pan skid plate (custom/v2/parts/chassis/chassis_belly_pan.FCStd)
5. VL53L5CX 9-Zone ToF distance sensor (cots/vl53l5cx_board.FCStd) at Z = -2.75 mm
6. Raspberry Pi 4 mounting frame (custom/v2/parts/chassis/chassis_rpi_mount.FCStd)
7. Raspberry Pi 4 Model B (cots/rpi4_model_b.FCStd) at Z = 59.80 mm
8. Draped Plexiglas canopy (custom/v2/parts/chassis/chassis_canopy.FCStd)
9. Removable service cover with '>>>' chevron louvers (custom/v2/parts/chassis/chassis_service_cover.FCStd)
"""

import os
import sys
import FreeCAD as App

print("--- Generating Lasius Chassis Assembly v2 (custom/v2/chassis_assembly.FCStd) ---")

doc_name = "chassis_assembly"
models_base = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/models"
v1_parts_dir = f"{models_base}/custom/v1/parts"
v2_asm_dir = f"{models_base}/custom/v2"
cots_dir = f"{models_base}/cots"

fcstd_path = f"{v2_asm_dir}/chassis_assembly.FCStd"


def build_chassis_assembly():
    if doc_name in App.listDocuments():
        try:
            App.closeDocument(doc_name)
        except Exception:
            pass

    doc = App.newDocument(doc_name)
    os.makedirs(v2_asm_dir, exist_ok=True)
    doc.saveAs(fcstd_path)

    doc_bottom = App.openDocument(f"{v1_parts_dir}/body_bottom.FCStd")
    doc_top = App.openDocument(f"{v1_parts_dir}/body_top.FCStd")
    doc_core_asm = App.openDocument(f"{v2_asm_dir}/chassis_core_assembly.FCStd")
    doc_belly = App.openDocument(f"{v2_asm_dir}/parts/chassis/chassis_belly_pan.FCStd")
    doc_hatch = App.openDocument(f"{v2_asm_dir}/parts/chassis/chassis_battery_hatch.FCStd")
    doc_rpi_mount = App.openDocument(f"{v2_asm_dir}/parts/chassis/chassis_rpi_mount.FCStd")
    doc_service_cover = App.openDocument(f"{v2_asm_dir}/parts/chassis/chassis_service_cover.FCStd")
    doc_canopy = App.openDocument(f"{v2_asm_dir}/parts/chassis/chassis_canopy.FCStd")
    doc_tof = App.openDocument(f"{cots_dir}/vl53l5cx_board.FCStd")
    doc_rpi = App.openDocument(f"{cots_dir}/rpi4_model_b.FCStd")

    asm_part = doc.addObject("App::Part", "Chassis_Assembly")
    asm_part.Label = "Lasius Chassis Assembly v2 (CFRP Plates + Monocoque Core + Torso Electronics)"
    for o in asm_part.Origin.OutList:
        if hasattr(o, "Visibility"):
            o.Visibility = False
        if hasattr(o, "ViewObject") and o.ViewObject:
            o.ViewObject.Visibility = False
    asm_part.Origin.Visibility = False
    if hasattr(asm_part.Origin, "ViewObject") and asm_part.Origin.ViewObject:
        asm_part.Origin.ViewObject.Visibility = False
    asm_part.Visibility = True

    def make_link(name, label, target_obj, placement, color=None, transparency=None, parent=asm_part):
        lnk = doc.addObject("App::Link", name)
        lnk.setLink(target_obj)
        lnk.Label = label
        lnk.Placement = placement
        parent.addObject(lnk)
        lnk.Visibility = True
        if hasattr(lnk, "ViewObject") and lnk.ViewObject is not None:
            vo = lnk.ViewObject
            vo.Visibility = True
            if color is not None:
                vo.OverrideMaterial = True
                mat = vo.ShapeMaterial
                mat.DiffuseColor = color
                if transparency is not None:
                    mat.Transparency = float(transparency) / 100.0
                vo.ShapeMaterial = mat
            if transparency is not None and hasattr(target_obj, "ViewObject") and target_obj.ViewObject is not None:
                if hasattr(target_obj.ViewObject, "Transparency"):
                    target_obj.ViewObject.Transparency = transparency
        return lnk

    COLOR_CARBON = (0.16, 0.16, 0.18)
    COLOR_BELLY_PAN = (0.26, 0.26, 0.30)
    COLOR_RPI_MOUNT = (0.24, 0.24, 0.28)
    COLOR_SERVICE_COVER = (0.20, 0.20, 0.23)
    COLOR_CANOPY = COLOR_SERVICE_COVER
    COLOR_PCB_RED = (0.75, 0.15, 0.15)
    COLOR_RPI_GREEN = (0.08, 0.52, 0.24)

    # 1. Bottom CFRP plate at Z = 0.00 .. 2.00 mm
    make_link(
        "Body_Bottom",
        "1. Chassis Bottom Plate (2mm CFRP)",
        doc_bottom.BodyBottom,
        App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation()),
        COLOR_CARBON,
    )

    # 2. Top CFRP plate at Z = 53.30 .. 55.30 mm
    make_link(
        "Body_Top",
        "2. Chassis Top Plate (2mm CFRP)",
        doc_top.BodyTop,
        App.Placement(App.Vector(0.0, 0.0, 53.30), App.Rotation()),
        COLOR_CARBON,
    )

    # 3. Monocoque Central Core Assembly (Z = 2.00 .. 53.30 mm + 2x PCA9685 + TCA9548A + 2S LiPo)
    make_link(
        "Chassis_Core_Assembly",
        "3. Monocoque Central Core Assembly (v2)",
        doc_core_asm.getObject("Chassis_Core_Assembly"),
        App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation()),
    )

    # 4a. Chassis Belly Pan (Fixed Skid Plate Frame)
    make_link(
        "Chassis_Belly_Pan",
        "4a. Chassis Belly Pan Frame (Fixed Skid Plate, v2)",
        doc_belly.Chassis_Belly_Pan,
        App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation()),
        COLOR_BELLY_PAN,
    )

    # 4b. Chassis Battery Service Hatch (Hinged with Filament Axis & Snap-Latch)
    make_link(
        "Chassis_Battery_Hatch",
        "4b. Chassis Battery Service Hatch (Hinged, v2)",
        doc_hatch.Chassis_Battery_Hatch,
        App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation()),
        (0.28, 0.30, 0.34),
    )

    # 5. VL53L5CX 9-Zone ToF Distance Sensor (Look-Ahead, X = +58.00 mm)
    make_link(
        "Sensor_VL53L5CX_ToF",
        "5. VL53L5CX 9-Zone ToF Distance Sensor (Fixed Front, COTS)",
        doc_tof.VL53L5CX_Board,
        App.Placement(App.Vector(58.00, 0.0, -2.75), App.Rotation(App.Vector(0, 1, 0), 180.0)),
        COLOR_PCB_RED,
    )

    # 6. Raspberry Pi 4 Mounting Plate on Body_Top
    make_link(
        "Chassis_RPi_Mount",
        "6. Raspberry Pi 4 Mounting Plate (v2)",
        doc_rpi_mount.getObject("Chassis_RPi_Mount"),
        App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation()),
        COLOR_RPI_MOUNT,
    )

    # 7. Raspberry Pi 4 Model B elevated on Mount Bosses at Z = 59.80 mm
    make_link(
        "Board_RPi4",
        "7. Raspberry Pi 4 Model B (Elevated Deck, COTS)",
        doc_rpi.Raspberry_Pi_4,
        App.Placement(App.Vector(0.0, 0.0, 59.80), App.Rotation()),
        COLOR_RPI_GREEN,
    )

    # 8. Draped Canopy
    make_link(
        "Chassis_Canopy",
        "8. Draped Canopy with Service Aperture (v2)",
        doc_canopy.getObject("Chassis_Canopy"),
        App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation()),
        COLOR_CANOPY,
    )

    # 9. Removable Service Cover with '>>>' Chevron Louvers
    make_link(
        "Chassis_Service_Cover",
        "9. Service Cover with '>>>' Chevron Louvers (v2)",
        doc_service_cover.getObject("Chassis_Service_Cover"),
        App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation()),
        COLOR_SERVICE_COVER,
    )

    doc.recompute()
    doc.save()
    bbox = asm_part.Shape.BoundBox
    print(f"✔ Saved Chassis Assembly: {fcstd_path}")
    print(f"  Valid: {asm_part.Shape.isValid()}, BB: X=[{bbox.XMin:.2f}, {bbox.XMax:.2f}], Y=[{bbox.YMin:.2f}, {bbox.YMax:.2f}], Z=[{bbox.ZMin:.2f}, {bbox.ZMax:.2f}]")
    return doc


import os
build_chassis_assembly()
os._exit(0)
