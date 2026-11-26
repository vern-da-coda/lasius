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
8. Monolithic draped canopy with integrated '>>>' chevron & rear UBEC louvers (custom/v2/parts/chassis/chassis_canopy.FCStd)
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
    doc_canopy = App.openDocument(f"{v2_asm_dir}/parts/chassis/chassis_canopy.FCStd")
    doc_tof = App.openDocument(f"{cots_dir}/vl53l5cx_board.FCStd")
    doc_rpi = App.openDocument(f"{cots_dir}/rpi4_model_b.FCStd")
    doc_ubec = App.openDocument(f"{cots_dir}/ubec_3a.FCStd")
    doc_ubec_hw = App.openDocument(f"{cots_dir}/ubec_hobbywing_10a.FCStd")
    doc_sw = App.openDocument(f"{cots_dir}/switch_mini_slide.FCStd")
    doc_fuse = App.openDocument(f"{cots_dir}/fuse_mini_atm.FCStd")
    doc_oled = App.openDocument(f"{cots_dir}/oled_096_i2c.FCStd")
    doc_btn = App.openDocument(f"{cots_dir}/button_tactile_6x6.FCStd")
    doc_led = App.openDocument(f"{cots_dir}/led_3mm.FCStd")
    doc_imu = App.openDocument(f"{cots_dir}/bno085_board.FCStd")
    doc_mag = App.openDocument(f"{cots_dir}/magnet_5x2.FCStd")
    doc_s_m2 = App.openDocument(f"{cots_dir}/screw_m2_button_head.FCStd")

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
    COLOR_CANOPY = (0.18, 0.22, 0.28)
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

    # 5. VL53L5CX 9-Zone ToF Distance Sensor (Fixed Rear Belly Pan Bridge, X = -58.50 mm)
    make_link(
        "Sensor_VL53L5CX_ToF",
        "5. VL53L5CX 9-Zone ToF Distance Sensor (Fixed Rear Bridge, COTS)",
        doc_tof.VL53L5CX_Board,
        App.Placement(App.Vector(-58.50, 0.0, -2.75), App.Rotation(App.Vector(0, 1, 0), 180.0)),
        None,
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
        None,
    )

    # 7b. 3A-6S UBEC 5V Step-Down Regulator on +Y Port-Free Flank of RPi Mount (X = 0.0, Y = +39.5, Z = 56.52 mm)
    make_link(
        "UBEC_3A_Pi",
        "7b. 3A-6S UBEC 5V Step-Down (Pi Logic Power, +Y Flank, COTS)",
        doc_ubec.UBEC_3A,
        App.Placement(App.Vector(0.00, 39.50, 56.52), App.Rotation()),
        (0.12, 0.58, 0.32),
    )

    # 7c. Dual Hobbywing BEC 10A V2-Car Servo UBECs (6.0V, 45x20x16.2mm) Symmetrically on Rear Deck of RPi Mount
    #     X = -79.50, Y = ±21.50, Z = 56.52 mm -> 100% clear of RPi4 MicroSD (-X center), USB/Eth (+X),
    #     USB-C/HDMI (-Y), GPIO (+Z), all 12 M3 standoffs, and all 6 leg mounting rings!
    make_link(
        "UBEC_Hobbywing_Left",
        "7c. Hobbywing BEC 10A V2-Car Left 6.0V (Rear Deck +Y, HW30603003, COTS)",
        doc_ubec_hw.UBEC_Hobbywing_10A,
        App.Placement(App.Vector(-79.50, +21.50, 56.52), App.Rotation()),
        (0.10, 0.11, 0.14),
    )
    make_link(
        "UBEC_Hobbywing_Right",
        "7d. Hobbywing BEC 10A V2-Car Right 6.0V (Rear Deck -Y, HW30603003, COTS)",
        doc_ubec_hw.UBEC_Hobbywing_10A,
        App.Placement(App.Vector(-79.50, -21.50, 56.52), App.Rotation()),
        (0.10, 0.11, 0.14),
    )

    # 7e. Rear Telemetry Cockpit (Option 3) Controls on Chassis_RPi_Mount 45° rear bevels & rear slope:
    #     - Left (+Y) 45° bevel: 3P3T Master Slide Switch (OFF -> LOGIC -> ARMED)
    #     - Right (-Y) 45° bevel: 6x6 mm Pi Safe-Shutdown Button (GPIO3) + 2x Ø3 mm Status LEDs (Green 5V / Red 6V)
    #     - Center rear slope (-106.5, 0.0, Z = 71.20, tilt -27°): 0.96" I2C OLED Dual-Zone HUD (i2c-3 isolated bus)
    #     - Center UBEC corridor (-76.0, 0.0, Z_flange = 80.20): Upright 25A Mini-ATM Top-Pull Blade Fuse
    make_link(
        "Switch_Master_3P3T",
        "7e. 3P3T Master Slide Switch: OFF -> LOGIC -> ARMED (Rear Left +Y Bevel, COTS)",
        doc_sw.Switch_Mini_Slide,
        App.Placement(App.Vector(-116.00, +14.50, 59.00), App.Rotation(App.Vector(0, 0, 1), -45.0)),
        (0.78, 0.18, 0.18),
    )
    p_bevel_r = App.Placement(App.Vector(-116.00, -14.50, 59.00), App.Rotation(App.Vector(0, 0, 1), +45.0))
    make_link(
        "Button_Safe_Shutdown",
        "7f. 6x6 mm Pi Safe-Shutdown Tactile Button (GPIO3, Rear Right -Y Bevel, COTS)",
        doc_btn.Button_Tactile_6x6,
        p_bevel_r,
        None,
    )
    make_link(
        "LED_Status_5V_Green",
        "7f2. Ø3 mm Status LED Green: 5V Pi Logic Ready (Rear Right -Y Bevel, COTS)",
        doc_led.LED_3mm,
        p_bevel_r.multiply(App.Placement(App.Vector(0.0, -6.80, 0.0), App.Rotation())),
        (0.12, 0.85, 0.30),
    )
    make_link(
        "LED_Status_6V_Red",
        "7f3. Ø3 mm Status LED Red: 6V Servos Armed (Rear Right -Y Bevel, COTS)",
        doc_led.LED_3mm,
        p_bevel_r.multiply(App.Placement(App.Vector(0.0, +6.80, 0.0), App.Rotation())),
        (0.92, 0.16, 0.14),
    )
    # 7g. Upright 25A Mini-ATM Blade Fuse shifted into open UBEC center corridor (X = -76.0, Y = 0.0, Z_flange = 80.20 mm)
    rot_fuse_up = App.Rotation(App.Vector(0, 0, 1), 90.0).multiply(App.Rotation(App.Vector(0, 1, 0), 90.0))
    make_link(
        "Fuse_Mini_ATM_25A",
        "7g. 25A Mini-ATM Blade Fuse & Socket (UBEC Corridor Tower, Tool-Free Top Pull, COTS)",
        doc_fuse.Fuse_Mini_ATM,
        App.Placement(App.Vector(-76.00, 0.00, 80.20), rot_fuse_up),
        (0.90, 0.90, 0.92),
    )
    # 7g2. 0.96" I2C OLED Telemetry HUD (128x64 SSD1306 Dual-Zone Yellow/Blue) on angled rear-slope cradle
    make_link(
        "Display_OLED_096_HUD",
        "7g2. 0.96\" I2C OLED Telemetry HUD 128x64 Dual-Zone (Rear Slope -27°, i2c-3, COTS)",
        doc_oled.OLED_096_I2C,
        App.Placement(App.Vector(-106.50, 0.00, 70.85), App.Rotation(App.Vector(0, 1, 0), -27.0)),
        None,
    )

    # 7h. Adafruit BNO085 9-DOF Orientation IMU (PID 4754) on Front Deck of Chassis_RPi_Mount
    #     X = +75.00, Y = 0.00, Z = 58.32 mm, rot +90° Z:
    #     - Short edge (22.7 mm) along X -> X in [+63.65, +86.35 mm], Long edge (25.6 mm) along Y -> Y in [-12.80, +12.80 mm]
    #     - Primary 6-pin 90° header points rearward (-X) toward RPi 4; dual STEMMA QT sockets face ±Y (+Y toward RPi GPIO)
    make_link(
        "Sensor_BNO085_IMU",
        "7h. Adafruit BNO085 9-DOF Orientation IMU (Front Deck, PID 4754, COTS)",
        doc_imu.BNO085_Board,
        App.Placement(App.Vector(75.00, 0.00, 58.32), App.Rotation(App.Vector(0, 0, 1), 90.0)),
        None,
    )

    # 7i. 8x Neodymium Disc Magnets Ø5 x 2 mm (4x Pillar Lower at Z=70.00..72.00 + 4x Canopy Upper at Z=72.35..74.35)
    mag_corners = [
        ("FL", +48.0, +36.0),
        ("FR", +48.0, -36.0),
        ("RL", -48.0, +36.0),
        ("RR", -48.0, -36.0),
    ]
    for tag, mx, my in mag_corners:
        make_link(
            f"Magnet_Pillar_{tag}",
            f"7i. Neodymium Magnet Ø5x2 Pillar {tag} (COTS)",
            doc_mag.Magnet_5x2,
            App.Placement(App.Vector(mx, my, 70.00), App.Rotation()),
            (0.78, 0.80, 0.84),
        )
        make_link(
            f"Magnet_Canopy_{tag}",
            f"7j. Neodymium Magnet Ø5x2 Canopy {tag} (COTS)",
            doc_mag.Magnet_5x2,
            App.Placement(App.Vector(mx, my, 72.35), App.Rotation()),
            (0.78, 0.80, 0.84),
        )

    # 8. Monolithic Draped Canopy with Integrated '>>>' Chevron & Rear UBEC Louvers
    make_link(
        "Chassis_Canopy",
        "8. Monolithic Draped Canopy with Integrated Louvers (v2)",
        doc_canopy.getObject("Chassis_Canopy"),
        App.Placement(App.Vector(0.0, 0.0, 0.0), App.Rotation()),
        COLOR_CANOPY,
    )

    # 9. 24x ISO 7380 M2 x 5 mm Servo Horn Screws fastening Body_Top (Z = 55.30 mm) to all 6 Coxa Servo Horns
    #    4x M2 on Ø16.00 mm BCD around each Coxa pivot ear (head seated at Z = 55.32 mm, clears Canopy @ (0,±83)!)
    coxa_screws_grp = doc.addObject("App::Part", "Coxa_Horn_Screws")
    coxa_screws_grp.Label = "9. 24x M2x5 Coxa Servo Horn Screws (ISO 7380, 6x Ø16 mm BCD)"
    for o in coxa_screws_grp.Origin.OutList:
        if hasattr(o, "Visibility"):
            o.Visibility = False
    coxa_screws_grp.Origin.Visibility = False
    coxa_screws_grp.Visibility = True
    asm_part.addObject(coxa_screws_grp)

    coxa_ears = [
        ("FL", +86.0, +65.0),
        ("ML",   0.0, +75.0),
        ("RL", -86.0, +65.0),
        ("FR", +86.0, -65.0),
        ("MR",   0.0, -75.0),
        ("RR", -86.0, -65.0),
    ]
    for tag, cx, cy in coxa_ears:
        for idx, (dx, dy) in enumerate([(8.0, 0.0), (-8.0, 0.0), (0.0, 8.0), (0.0, -8.0)], start=1):
            make_link(
                f"Coxa_Horn_M2_{tag}_{idx}",
                f"Coxa Horn Screw {tag} #{idx} (ISO 7380 M2x5)",
                doc_s_m2.M2_Linsenkopfschraube,
                App.Placement(App.Vector(cx + dx, cy + dy, 55.32), App.Rotation()),
                (0.78, 0.80, 0.84),
                parent=coxa_screws_grp,
            )

    doc.recompute()
    doc.save()
    bbox = asm_part.Shape.BoundBox
    print(f"✔ Saved Chassis Assembly: {fcstd_path}")
    print(f"  Valid: {asm_part.Shape.isValid()}, BB: X=[{bbox.XMin:.2f}, {bbox.XMax:.2f}], Y=[{bbox.YMin:.2f}, {bbox.YMax:.2f}], Z=[{bbox.ZMin:.2f}, {bbox.ZMax:.2f}]")

    # Collision Check
    items = [(o.Name, o.Shape) for o in asm_part.Group if hasattr(o, "Shape") and not o.Shape.isNull()]
    max_coll = 0.0
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            n1, s1 = items[i]
            n2, s2 = items[j]
            if s1.BoundBox.intersect(s2.BoundBox):
                v = s1.common(s2).Volume
                if v > 1e-4:
                    print(f"  ❌ COLLISION {n1} <-> {n2}: {v:.4f} mm^3")
                    max_coll = max(max_coll, v)
    if max_coll <= 1e-4:
        print("  ✅ ZERO COLLISIONS in chassis_assembly.FCStd (0.0000 mm^3)!")

    return doc


import os
build_chassis_assembly()
os._exit(0)
