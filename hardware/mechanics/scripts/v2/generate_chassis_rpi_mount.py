#!/usr/bin/env python3
"""
Generate Lasius Hexapod Raspberry Pi 4 & Triple-UBEC Top-Deck Mounting Plate v2
(hardware/mechanics/models/custom/v2/parts/chassis/chassis_rpi_mount.FCStd)
================================================================================
Unified Single-Solid Top-Deck Carrier seated on Body_Top (Z = 55.32 mm):
  1. Centered Raspberry Pi 4 Model B Deck (X = 0.0, Y = 0.0, PCB at Z = 59.80 mm):
     - 4x M2.5 mounting bosses (58.0 x 49.0 mm at X in [-39.0, +19.0], Y = ±24.5 mm).
     - 8x flat M3 countersunk screw holes (±45, ±30 & ±36.5, ±19 mm) into Chassis_Core.
     - 4x outward-offset Canopy magnetic support pillars at (±48.0, ±36.0 mm) trimmed
       flush to the updated Canopy inner ceiling (0.05 mm clearance).
     - 4x underside PCA9685 hold-down tabs reaching through Body_Top cutout to Z = 43.80 mm.
     - 100% unobstructed access to ALL Raspberry Pi 4 ports:
       * +X Front: USB 3.0, USB 2.0, RJ45 Ethernet (>90 mm clear corridor)
       * -Y Right: USB-C Power, 2x Micro-HDMI, 3.5mm Audio (100% open)
       * -X Rear:  MicroSD card slot (20 mm wide open central channel straight rearward)
       * +Y Left:  40-pin GPIO header unobstructed upward
  2. Symmetric Rear Dual Hobbywing BEC 10A V2-Car Cradles (X = -79.5, Y = ±21.5 mm):
     - Form-fit PETG retention cradles (Z_floor = 56.50 mm, 5.5 mm side walls, open front/rear
       cable exits, bottom convection/zip-tie slots, 45° rear outer corner chamfers matching
       Body_Top's carbon taper with >2.5 mm margin).
     - 100% Y-symmetric mass balance (2x 36 g), 20 mm open center corridor keeping both the
       RPi 4 MicroSD slot and the rear CFRP M3 standoffs (-90, 0) & (-120, 0) fully clear.
     - Ferrite outputs face +X right at Body_Top's central cutout edge (shortest vertical
       6.0 V high-current drop straight down to both PCA9685 screw terminals).
  3. Left-Flank (+Y) 3A-6S Logic UBEC Caddy (X = 0.0, Y = +39.5 mm, rot 0°):
     - Mounted along the completely port-free +Y flank of the Raspberry Pi 4, directly beside
       the 5V/GND GPIO header pins and thermally/EMI-isolated from the rear 10A servo UBECs.
  4. Front-Deck BNO085 9-DOF IMU Carrier Tongue (X = +75.0, Y = 0.0 mm, PCB at Z = 58.32 mm):
     - Rigidly bridged via symmetric side rails (|Y| in [16.0, 21.5 mm]) onto the solid front
       Body_Top carbon deck (X > +60.0 mm), keeping the entire front window cutout unobstructed.
     - 4x M2.5 standoff bosses (17.78 x 20.32 mm rotated Adafruit PID 4754 pattern; use nylon/brass
       screws!) over a 0.80 mm insulating PETG floor relief pocket (clears solder tails & isolates
       from conductive CFRP). Maximizes EMI/magnetic distance to rear UBECs (~156 mm), Pi UBEC (~85 mm),
       front Coxa servos (~72.5 mm), and canopy magnets (~48.5 mm) while leaving >5 mm canopy headroom.
"""

import math
import os
import sys
import zipfile
import FreeCAD as App
import Part

print("--- Generating Raspberry Pi 4 & Triple-UBEC Mounting Plate v2 (FreeCAD 1.1+) ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts/chassis"
fcstd_plate_path = f"{models_dir}/chassis_rpi_mount.FCStd"

os.makedirs(models_dir, exist_ok=True)


def make_rounded_rect_solid(x_min, x_max, y_min, y_max, r_corner, z_min, z_max):
    """Constructs a filleted 3D solid prism."""
    dx = x_max - x_min
    dy = y_max - y_min
    r_corner = min(r_corner, dx / 2.0 - 0.1, dy / 2.0 - 0.1)
    k = r_corner * (1.0 - 1.0 / math.sqrt(2.0))
    pts = [
        (x_min + r_corner, y_max),
        (x_max - r_corner, y_max),
        (x_max - k, y_max - k),
        (x_max, y_max - r_corner),
        (x_max, y_min + r_corner),
        (x_max - k, y_min + k),
        (x_max - r_corner, y_min),
        (x_min + r_corner, y_min),
        (x_min + k, y_min + k),
        (x_min, y_min + r_corner),
        (x_min, y_max - r_corner),
        (x_min + k, y_max - k),
    ]
    v = [App.Vector(px, py, z_min) for px, py in pts]
    edges = [
        Part.makeLine(v[0], v[1]),
        Part.Edge(Part.ArcOfCircle(v[1], v[2], v[3])),
        Part.makeLine(v[3], v[4]),
        Part.Edge(Part.ArcOfCircle(v[4], v[5], v[6])),
        Part.makeLine(v[6], v[7]),
        Part.Edge(Part.ArcOfCircle(v[7], v[8], v[9])),
        Part.makeLine(v[9], v[10]),
        Part.Edge(Part.ArcOfCircle(v[10], v[11], v[0])),
    ]
    face = Part.Face(Part.Wire(edges))
    return face.extrude(App.Vector(0.0, 0.0, z_max - z_min))


def make_filleted_wire(x_min, x_max, y_min, y_max, r, z):
    dx = x_max - x_min
    dy = y_max - y_min
    r = min(r, dx / 2.0 - 0.1, dy / 2.0 - 0.1)
    pts = [
        App.Vector(x_max - r, y_max, z),
        App.Vector(x_min + r, y_max, z),
        App.Vector(x_min, y_max - r, z),
        App.Vector(x_min, y_min + r, z),
        App.Vector(x_min + r, y_min, z),
        App.Vector(x_max - r, y_min, z),
        App.Vector(x_max, y_min + r, z),
        App.Vector(x_max, y_max - r, z),
    ]
    edges = [
        Part.makeLine(pts[0], pts[1]),
        Part.Edge(Part.ArcOfCircle(pts[1], App.Vector(x_min + r * (1 - 1 / math.sqrt(2)), y_max - r * (1 - 1 / math.sqrt(2)), z), pts[2])),
        Part.makeLine(pts[2], pts[3]),
        Part.Edge(Part.ArcOfCircle(pts[3], App.Vector(x_min + r * (1 - 1 / math.sqrt(2)), y_min + r * (1 - 1 / math.sqrt(2)), z), pts[4])),
        Part.makeLine(pts[4], pts[5]),
        Part.Edge(Part.ArcOfCircle(pts[5], App.Vector(x_max - r * (1 - 1 / math.sqrt(2)), y_min + r * (1 - 1 / math.sqrt(2)), z), pts[6])),
        Part.makeLine(pts[6], pts[7]),
        Part.Edge(Part.ArcOfCircle(pts[7], App.Vector(x_max - r * (1 - 1 / math.sqrt(2)), y_max - r * (1 - 1 / math.sqrt(2)), z), pts[0])),
    ]
    return Part.Wire(edges)


def build_rpi_mount():
    z_base = 55.32  # 0.02 mm clearance above Body_Top (55.30 mm)
    t_plate = 1.98  # top of flat base plate at Z = 57.30 mm (2.50 mm below RPi 4 PCB at Z = 59.80 mm)
    h_boss = 2.48   # top of lower RPi 4 bosses at Z = 59.78 mm (0.02 mm below RPi 4 PCB at 59.80 mm)

    # 1. Unified Single-Solid Flat Base Plate Deck (X in [-42.5, +42.5], Y in [-28.0, +28.0])
    plate = make_rounded_rect_solid(-42.5, 42.5, -28.0, 28.0, 4.0, z_base, z_base + t_plate)

    # Synchronized Canopy inner ceiling envelope (0.05 mm vertical clearance below Canopy inner wall)
    z_canopy = 55.25
    w_in_1 = make_filleted_wire(-134.5, 134.5, -88.5, 88.5, 30.5, z_canopy)
    w_in_2 = make_filleted_wire(-126.0, 113.5, -73.5, 73.5, 24.5, z_canopy + 5.0)
    w_in_3 = make_filleted_wire(-118.0,  88.5, -56.5, 56.5, 18.5, z_canopy + 12.0)
    w_in_4 = make_filleted_wire(-111.0,  63.5, -42.5, 42.5, 12.0, z_canopy + 19.0)
    w_in_5 = make_filleted_wire( -92.0,  47.5, -31.0, 31.0,  6.5, z_canopy + 24.68)
    loft_canopy_inner = Part.makeLoft([w_in_1, w_in_2, w_in_3, w_in_4, w_in_5], True)

    # 2. 4x Outrigger Arms to M3 Standoff Lugs (±45.0, ±30.0 mm) & Outward-Offset Canopy Magnetic Pillars (±48.0, ±36.0 mm)
    #    Horizontal self-centering magnetic interface at Z = 72.10 mm (for Ø5 x 2 mm Neodymium discs):
    #    - Shaft Ø8.00 mm (r = 4.00 mm) from Z = 55.32 to Z = 71.30 mm, 45° lead-in chamfer (r = 4.00 -> 3.20 mm)
    #      to flat top face at Z = 72.10 mm -> glides cleanly into Canopy centering cups without snagging!
    #    - Centered Ø5.25 x 2.15 mm deep magnet pocket (Z = 69.95..72.10 mm) + Ø1.80 mm glue/air vent bore below.
    z_mag_top = 72.10
    z_mag_chamf_start = z_mag_top - 0.80  # 71.30 mm
    r_mag_pocket = 2.625                  # Ø5.25 mm slip/CA-glue fit for Ø5.00 x 2.00 mm Neodymium magnet
    d_mag_pocket = 2.15                   # Z = 69.95..72.10 mm (0.15 mm margin for flush/recessed seating)
    for sx in [-45.0, 45.0]:
        for sy in [-30.0, 30.0]:
            px = -48.0 if sx < 0 else 48.0
            py = -36.0 if sy < 0 else 36.0
            lug_cyl = Part.makeCylinder(6.0, t_plate, App.Vector(sx, sy, z_base), App.Vector(0, 0, 1))
            pil_base = Part.makeCylinder(5.0, t_plate, App.Vector(px, py, z_base), App.Vector(0, 0, 1))
            pil_shaft = Part.makeCylinder(4.0, z_mag_chamf_start - z_base, App.Vector(px, py, z_base), App.Vector(0, 0, 1))
            pil_chamf = Part.makeCone(4.0, 3.20, 0.80, App.Vector(px, py, z_mag_chamf_start), App.Vector(0, 0, 1))
            pillar = pil_shaft.fuse(pil_chamf)
            mag_pocket = Part.makeCylinder(r_mag_pocket, d_mag_pocket + 0.50, App.Vector(px, py, z_mag_top - d_mag_pocket), App.Vector(0, 0, 1))
            vent_hole = Part.makeCylinder(0.90, 2.50, App.Vector(px, py, z_mag_top - d_mag_pocket - 2.00), App.Vector(0, 0, 1))
            pillar = pillar.cut(mag_pocket).cut(vent_hole)
            x1 = -52.0 if sx < 0 else 30.0
            x2 = -30.0 if sx < 0 else 52.0
            y1 = -39.0 if sy < 0 else 18.0
            y2 = -18.0 if sy < 0 else 39.0
            bridge = make_rounded_rect_solid(x1, x2, y1, y2, 3.0, z_base, z_base + t_plate)
            plate = plate.fuse(lug_cyl).fuse(pil_base).fuse(bridge).fuse(pillar)

    # 3. Cut Full Through-Opening for Central Wiring / PCA9685 Servo Plugs (X in [-24.0, +24.0], Y in [-16.0, +16.0])
    #    and +Y GPIO ribbon pass-through slot (X in [-24.0, +14.0], Y in [14.0, 21.0]):
    pocket = make_rounded_rect_solid(-24.0, 24.0, -16.0, 16.0, 3.0, z_base - 1.0, z_base + t_plate + 1.0)
    gpio_slot = make_rounded_rect_solid(-24.0, 14.0, 14.0, 21.0, 2.0, z_base - 1.0, z_base + t_plate + 1.0)
    plate = plate.cut(pocket).cut(gpio_slot)

    # 4. 4x Short Lower Raspberry Pi 4 Standoff Bosses (Z = 57.30 .. 59.78 mm, Ø6.00 mm)
    #    at official RPi 4 hole pattern: X in [-39.0, +19.0 mm], Y in [-24.5, +24.5 mm]
    for bx in [-39.0, 19.0]:
        for by in [-24.5, 24.5]:
            lower_boss = Part.makeCylinder(3.00, h_boss, App.Vector(bx, by, z_base + t_plate), App.Vector(0, 0, 1))
            tap = Part.makeCylinder(1.05, 4.0, App.Vector(bx, by, z_base + t_plate + h_boss - 3.5), App.Vector(0, 0, 1))
            lower_boss = lower_boss.cut(tap)
            plate = plate.fuse(lower_boss)

    # 5. 4x Underside PCA9685 PCB Hold-Down Tabs at X = ±25.0 mm, Y = ±12.2 mm
    for tx in [-26.2, 23.8]:
        for ty in [-13.1, 11.3]:
            tab = Part.makeBox(2.40, 1.80, z_base - 43.80, App.Vector(tx, ty, 43.80))
            plate = plate.fuse(tab)

    # 6. Dual Symmetric Rear Hobbywing BEC 10A V2-Car Cradles (X = -79.5, Y = ±21.5, Z_floor = 56.50 mm)
    #    UBEC casing: X in [-102.0, -57.0], Y in [±11.5, ±31.5], Z in [56.52, 72.72]
    #    Leaves 20.0 mm wide open central corridor (Y in [-10.0, +10.0]) for RPi 4 MicroSD access &
    #    rear CFRP M3 standoffs at (-90, 0) & (-120, 0)!
    x_hw = -79.50
    t_floor = 1.18  # floor Z in [55.32, 56.50] (0.02 mm below UBEC at Z=56.52)
    wall_t = 1.50
    wall_h = 6.20   # walls Z in [55.32, 61.52] (cradles lower 5 mm of aluminum heatsink)
    clr = 0.25      # 0.25 mm PETG slip-fit clearance per side

    for sign in (+1.0, -1.0):
        yc = sign * 21.50
        y_lo = yc - 10.0 - clr - wall_t
        y_hi = yc + 10.0 + clr + wall_t
        x_lo = x_hw - 22.5 - clr - wall_t  # -103.75
        x_hi = x_hw + 22.5 + clr + wall_t  # -55.25

        # Outer cradle tub
        cradle = make_rounded_rect_solid(x_lo, x_hi, y_lo, y_hi, 2.0, z_base, z_base + wall_h)
        # Inner UBEC seating cavity (above floor)
        cav = make_rounded_rect_solid(
            x_hw - 22.5 - clr, x_hw + 22.5 + clr,
            yc - 10.0 - clr, yc + 10.0 + clr,
            1.6, z_base + t_floor, z_base + wall_h + 2.0,
        )
        cradle = cradle.cut(cav)

        # Open front (+X, output ferrite leads) and rear (-X, input leads + SW plug) cable channels
        lead_cut = Part.makeBox(54.0, 14.0, wall_h + 2.0, App.Vector(x_hw - 27.0, yc - 7.0, z_base + t_floor))
        cradle = cradle.cut(lead_cut)

        # 3x Bottom cooling / zip-tie slots in floor
        for sx_slot in [-92.0, -79.5, -67.0]:
            slot = make_rounded_rect_solid(sx_slot - 2.5, sx_slot + 2.5, yc - 6.5, yc + 6.5, 1.0, z_base - 1.0, z_base + t_floor + 1.0)
            cradle = cradle.cut(slot)

        # Chamfer outer-rear corner cleanly inside Body_Top's 45° rear taper (Y_edge = 137 + X)
        # Keep |Y| <= 134.5 + X at rear outer corner (2.5 mm margin from Body_Top carbon edge)
        if sign > 0:
            p_ch = [
                App.Vector(-106.0, 35.0, z_base - 1.0),
                App.Vector(-98.0,  35.0, z_base - 1.0),
                App.Vector(-106.0, 27.0, z_base - 1.0),
            ]
        else:
            p_ch = [
                App.Vector(-106.0, -35.0, z_base - 1.0),
                App.Vector(-106.0, -27.0, z_base - 1.0),
                App.Vector(-98.0,  -35.0, z_base - 1.0),
            ]
        ch_wire = Part.makePolygon(p_ch + [p_ch[0]])
        ch_prism = Part.Face(ch_wire).extrude(App.Vector(0, 0, wall_h + 4.0))
        cradle = cradle.cut(ch_prism)

        # Structural bridge arm joining cradle cleanly to main RPi plate (X in [-57.0, -40.0], clear of (-45, ±30) M3 hole!)
        by1 = yc - 7.5 if sign > 0 else yc - 2.5
        by2 = yc + 2.5 if sign > 0 else yc + 7.5
        bridge_arm = make_rounded_rect_solid(-57.0, -40.0, by1, by2, 1.5, z_base, z_base + t_plate)
        plate = plate.fuse(cradle).fuse(bridge_arm)

    # 7. Left-Flank (+Y) 3A-6S Logic UBEC Form-Fit Caddy (X = 0.0, Y = +39.5 mm, rot 0°)
    #    Centered symmetrically at X = 0.0 along the 100% port-free +Y flank of the Raspberry Pi 4,
    #    clear of both (±30..±52) outrigger bridges, directly beside the 5V/GND GPIO header pins,
    #    and thermally/EMI-isolated from the rear 10A servo UBECs.
    #    UBEC_3A PCB: 34.0 x 17.08 mm -> X in [-17.0, +17.0], Y in [+30.96, +48.04], Z in [56.52, 66.52]
    x_u3, y_u3 = 0.00, 39.50
    u3_outer = make_rounded_rect_solid(x_u3 - 18.8, x_u3 + 18.8, y_u3 - 10.2, y_u3 + 10.2, 1.8, z_base, z_base + 3.20)
    u3_cav = make_rounded_rect_solid(x_u3 - 17.3, x_u3 + 17.3, y_u3 - 8.79, y_u3 + 8.79, 1.2, z_base + t_floor, z_base + 5.00)
    u3_leads = Part.makeBox(42.0, 12.5, 4.0, App.Vector(x_u3 - 21.0, y_u3 - 6.25, z_base + t_floor))
    u3_caddy = u3_outer.cut(u3_cav).cut(u3_leads)
    # Bridge ribs joining +Y caddy solidly to main RPi plate along Y in [26.0, 30.5]
    u3_bridge = make_rounded_rect_solid(x_u3 - 17.0, x_u3 + 17.0, 26.0, y_u3 - 9.0, 1.5, z_base, z_base + t_plate)
    plate = plate.fuse(u3_caddy).fuse(u3_bridge)

    # 7b. Rear Telemetry Cockpit (Option 3: 3P3T Master + GPIO3 Safe-Shutdown + 2x LEDs + 0.96" OLED HUD + 25A Fuse):
    #     - Extends cleanly behind both Hobbywing UBEC cradles, clamped via rear CFRP M3 screws (-90, 0) & (-120, 0)
    #       and forward into the 20 mm open UBEC center corridor (X = -65..-86) to carry the shifted 25A fuse tower!
    #     - Left (+Y) 45° rear bevel (-116.0, +14.5, Z = 59.00): 3P3T Master Slide Switch (OFF -> LOGIC -> ARMED)
    #     - Right (-Y) 45° rear bevel (-116.0, -14.5, Z = 59.00): 6x6 mm Pi Safe-Shutdown Button (GPIO3) + 2x Ø3 mm LEDs
    #     - Center rear slope (-106.5, 0.0, Z_pcb = 71.20, tilt -27°): 0.96" I2C OLED (128x64, 4x M2 23x23 mm) cradle
    #     - Center UBEC corridor (-76.0, 0.0, Z_flange = 80.20): Upright 25A Mini-ATM Blade Fuse (tool-free top pull)
    def place_shape(shape, vec, rot):
        s = shape.copy()
        s.Placement = App.Placement(vec, rot)
        return s

    # Tapered flat base tongue spanning from (-86, ±11.5) to (-127, ±5.5) + forward corridor tongue (-65..-86, ±7.5)
    tail_pts = [
        App.Vector(-86.0,  11.5, z_base),
        App.Vector(-103.0, 26.5, z_base),
        App.Vector(-125.0,  8.5, z_base),
        App.Vector(-127.0,  5.5, z_base),
        App.Vector(-127.0, -5.5, z_base),
        App.Vector(-125.0, -8.5, z_base),
        App.Vector(-103.0, -26.5, z_base),
        App.Vector(-86.0, -11.5, z_base),
    ]
    tail_base = Part.Face(Part.makePolygon(tail_pts + [tail_pts[0]])).extrude(App.Vector(0, 0, t_plate))
    # Forward fuse-corridor bridge strictly inside the 19.5 mm open UBEC center gap (leaves X > -65 open for RPi4 MicroSD!)
    fuse_corridor_base = make_rounded_rect_solid(-88.0, -65.0, -8.5, 8.5, 2.0, z_base, z_base + t_plate)
    plate = plate.fuse(tail_base).fuse(fuse_corridor_base)

    # Re-clear both Hobbywing UBEC seating cavities above Z = 56.50 so tail_base never intrudes under UBECs!
    for sign in (+1.0, -1.0):
        yc = sign * 21.50
        ubec_clr_cut = make_rounded_rect_solid(
            x_hw - 22.5 - clr, x_hw + 22.5 + clr,
            yc - 10.0 - clr, yc + 10.0 + clr,
            1.6, z_base + t_floor, z_base + wall_h + 2.0,
        )
        plate = plate.cut(ubec_clr_cut)

    # Dual 45°-bevel recessed control housings at (-116.0, ±14.5, Z = 59.00 mm):
    # Panel convention: local -X = outward (actuator/LEDs), local +X = inward (body + pins)
    p_sw_l = App.Vector(-116.0, +14.5, 59.00)
    p_sw_r = App.Vector(-116.0, -14.5, 59.00)
    rot_sw_l = App.Rotation(App.Vector(0, 0, 1), -45.0)  # local -X -> (-0.707, +0.707, 0)
    rot_sw_r = App.Rotation(App.Vector(0, 0, 1), +45.0)  # local -X -> (-0.707, -0.707, 0)

    for p_sw, r_sw in [(p_sw_l, rot_sw_l), (p_sw_r, rot_sw_r)]:
        sw_blk = place_shape(
            Part.makeBox(4.20, 22.00, 7.08, App.Vector(0.00, -11.00, -3.68)),
            p_sw,
            r_sw,
        )
        plate = plate.fuse(sw_blk)

    # Left (+Y) Bevel: 3P3T Master Slide Switch (OFF -> LOGIC -> ARMED)
    sw_cut_l = place_shape(Part.makeBox(15.00, 12.10, 6.30, App.Vector(-2.00, -6.05, -3.15)), p_sw_l, rot_sw_l)
    sw_front_l = place_shape(Part.makeBox(5.00, 20.00, 8.00, App.Vector(-5.00, -10.00, -3.70)), p_sw_l, rot_sw_l)
    sw_m2_la = place_shape(Part.makeCylinder(0.85, 8.00, App.Vector(-1.00, -7.50, 0.00), App.Vector(1, 0, 0)), p_sw_l, rot_sw_l)
    sw_m2_lb = place_shape(Part.makeCylinder(0.85, 8.00, App.Vector(-1.00, +7.50, 0.00), App.Vector(1, 0, 0)), p_sw_l, rot_sw_l)
    plate = plate.cut(sw_cut_l).cut(sw_front_l).cut(sw_m2_la).cut(sw_m2_lb)

    # Right (-Y) Bevel: Pi Safe-Shutdown Button (6x6 mm GPIO3, center) + 2x Ø3 mm Status LEDs (Y_loc = ±6.8 mm)
    btn_front_r = place_shape(Part.makeBox(5.00, 20.00, 8.00, App.Vector(-5.00, -10.00, -3.70)), p_sw_r, rot_sw_r)
    btn_bore_r = place_shape(Part.makeCylinder(2.05, 5.00, App.Vector(-2.00, 0.00, 0.00), App.Vector(1, 0, 0)), p_sw_r, rot_sw_r)
    btn_cav_r = place_shape(Part.makeBox(12.00, 6.40, 6.40, App.Vector(0.36, -3.20, -3.20)), p_sw_r, rot_sw_r)
    plate = plate.cut(btn_front_r).cut(btn_bore_r).cut(btn_cav_r)
    for ly in (-6.80, +6.80):
        led_bore = place_shape(Part.makeCylinder(1.58, 8.00, App.Vector(-2.00, ly, 0.00), App.Vector(1, 0, 0)), p_sw_r, rot_sw_r)
        led_seat = place_shape(Part.makeCylinder(2.08, 6.00, App.Vector(1.94, ly, 0.00), App.Vector(1, 0, 0)), p_sw_r, rot_sw_r)
        plate = plate.cut(led_bore).cut(led_seat)

    # 7c. Shifted Central Upright 25A Mini-ATM Fuse Tower in Open UBEC Corridor (X = -76.0, Y = 0.0):
    #     Centered cleanly between both Hobbywing 10A UBEC cradles (|Y| >= 9.75 -> 4.95 mm air gap per side!),
    #     protruding cleanly through the flat Canopy roof (Z = 80.00..81.50 mm) at Z_flange = 80.20 mm!
    x_fuse = -76.00
    fuse_tower = make_rounded_rect_solid(x_fuse - 7.70, x_fuse + 7.70, -4.80, 4.80, 1.50, z_base + t_plate - 0.50, 80.18)
    fuse_socket_cav = Part.makeBox(12.80, 6.80, 16.50, App.Vector(x_fuse - 6.40, -3.40, 65.50))
    fuse_wire_arch_x = Part.makeBox(20.00, 6.80, 8.50, App.Vector(x_fuse - 10.00, -3.40, z_base + t_plate))
    fuse_wire_arch_y = Part.makeBox(12.20, 14.00, 6.80, App.Vector(x_fuse - 6.10, -7.00, z_base + t_plate))
    fuse_tower = fuse_tower.cut(fuse_socket_cav).cut(fuse_wire_arch_x).cut(fuse_wire_arch_y)
    plate = plate.fuse(fuse_tower)

    # 7c2. Tilted 0.96" I2C OLED Telemetry HUD Cradle on Rear Slope (X_c = -106.5, Y = 0.0, Z_pcb = 70.85, tilt -27°):
    #      Two forward side stanchions at X in [-104.5, -96.0], |Y| in [4.2, 6.8] sit strictly forward of ALL
    #      rear 45° switch/button/LED pins, clear of (-90, 0) & (-120, 0) M3 screws, and clear of both Hobbywing
    #      UBEC cradles (|Y| >= 9.75), carrying the tilted 4x M2 (23x23 mm) OLED frame cleanly above the switches!
    p_oled = App.Vector(-106.50, 0.00, 70.85)
    rot_oled = App.Rotation(App.Vector(0, 1, 0), -27.0)  # local +Z -> (-sin27, 0, +cos27) rearward/upward!

    # Open-center tilted PCB frame (local Z in [-1.80, -0.02] below PCB bottom at Z_loc = 0.00)
    oled_frame_out = make_rounded_rect_solid(-14.00, 14.00, -13.80, 13.80, 1.80, -1.80, -0.02)
    oled_frame_in = make_rounded_rect_solid(-9.20, 9.20, -9.20, 9.20, 1.50, -3.00, 1.00)
    # Rear 4-pin header clearance notch at +X_local edge (X_loc in [+9.0, +14.5], Y_loc in [-6.2, +6.2])
    oled_hdr_notch = Part.makeBox(6.00, 12.40, 5.00, App.Vector(8.80, -6.20, -3.00))
    oled_frame = oled_frame_out.cut(oled_frame_in).cut(oled_hdr_notch)
    # 4x M2 pilot holes at ±11.50, ±11.50 mm (23.0 x 23.0 mm pitch)
    for hx in (-11.50, 11.50):
        for hy in (-11.50, 11.50):
            oled_frame = oled_frame.cut(Part.makeCylinder(0.85, 4.0, App.Vector(hx, hy, -2.50), App.Vector(0, 0, 1)))
    oled_frame_w = place_shape(oled_frame, p_oled, rot_oled)

    oled_clip_top = place_shape(
        Part.makeBox(36.0, 32.0, 20.0, App.Vector(-18.0, -16.0, -0.02)),
        p_oled,
        rot_oled,
    )
    oled_hdr_keepout = place_shape(
        Part.makeBox(8.0, 12.6, 5.0, App.Vector(8.5, -6.3, -4.5)),
        p_oled,
        rot_oled,
    )
    for sign in (+1.0, -1.0):
        y1 = 5.80 if sign > 0 else -8.20
        y2 = 8.20 if sign > 0 else -5.80
        # Forward stanchion foot (X in [-104.5, -96.0], strictly clear of rear bevel controls, OLED header & UBEC cradles!)
        pylon_raw = make_rounded_rect_solid(-104.50, -96.00, y1, y2, 1.0, z_base + t_plate - 0.30, 82.0)
        # Upper cantilevered support rail (Z >= 63.0 -> strictly above all rear switch/button/LED pins!)
        upper_rail = make_rounded_rect_solid(-117.50, -96.00, y1, y2, 0.8, 63.00, 82.0)
        pylon_trimmed = pylon_raw.fuse(upper_rail).cut(oled_clip_top).cut(oled_hdr_keepout)
        plate = plate.fuse(pylon_trimmed)
    plate = plate.fuse(oled_frame_w)

    # Re-clear Hobbywing UBEC cavities & inner switch pockets after adding OLED cradle (guaranteed 0.0000 mm^3 collision!)
    for sign in (+1.0, -1.0):
        yc = sign * 21.50
        ubec_clr_cut2 = make_rounded_rect_solid(
            x_hw - 22.5 - clr, x_hw + 22.5 + clr,
            yc - 10.0 - clr, yc + 10.0 + clr,
            1.6, z_base + t_floor, z_base + wall_h + 14.0,
        )
        plate = plate.cut(ubec_clr_cut2)

    # 7d. Front-Deck Adafruit BNO085 9-DOF IMU Carrier Platform (X = +75.0, Y = 0.0, PCB at Z = 58.32 mm):
    #     - Symmetric twin longitudinal side-rails (X in [+42.0, +70.0], |Y| in [16.0, 21.5 mm]) rest
    #       strictly on solid Body_Top carbon flanking the front cutout (|Y| <= 15.0 mm) and tie cleanly
    #       into the main RPi plate & front outrigger bridges without touching the M3 bores at (36.5, ±19)
    #       or (45.0, ±30) and staying completely below the RPi 4 USB/Ethernet ports (Z >= 61.2 mm).
    #     - Platform deck (X in [+61.5, +88.5], Y in [-18.5, +18.5], Z in [55.32, 57.30 mm]) sits 100%
    #       on solid front Body_Top carbon (X > +60.0 mm).
    #     - Recessed solder-tail relief pocket (X in [+63.5, +86.5], Y in [-9.0, +9.0], floor at Z = 56.12 mm)
    #       leaves a 0.80 mm insulating PETG barrier above conductive CFRP Body_Top AND 0.80 mm air clearance
    #       below the BNO085 6-pin header solder tails (Z_tail = 56.92 mm).
    #     - 4x M2.5 standoff bosses (Ø4.80 mm, top at Z = 58.30 mm -> 0.02 mm below PCB at Z = 58.32 mm)
    #       at rotated Adafruit PID 4754 pitch: X = 75.0 ± 8.89 mm (66.11 / 83.89), Y = ±10.16 mm.
    x_imu = 75.00
    z_imu_boss_top = 58.30  # 0.02 mm below BNO085 PCB bottom at Z = 58.32 mm
    for sign in (+1.0, -1.0):
        y_rail_lo = 16.00 if sign > 0 else -21.50
        y_rail_hi = 21.50 if sign > 0 else -16.00
        side_rail = make_rounded_rect_solid(42.00, 70.00, y_rail_lo, y_rail_hi, 1.80, z_base, z_base + t_plate)
        plate = plate.fuse(side_rail)

    imu_deck = make_rounded_rect_solid(x_imu - 13.50, x_imu + 13.50, -18.50, 18.50, 3.00, z_base, z_base + t_plate)
    # Relief pocket for header solder tails & under-PCB SMD clearance (keeps 0.80 mm insulating PETG floor!)
    imu_relief = make_rounded_rect_solid(x_imu - 11.50, x_imu + 11.50, -8.20, 8.20, 1.80, z_base + 0.80, z_base + t_plate + 1.00)
    imu_deck = imu_deck.cut(imu_relief)
    plate = plate.fuse(imu_deck)

    for dx_b in (-8.89, +8.89):
        for dy_b in (-10.16, +10.16):
            bx_i = x_imu + dx_b
            by_i = dy_b
            imu_boss = Part.makeCylinder(2.40, z_imu_boss_top - z_base, App.Vector(bx_i, by_i, z_base), App.Vector(0, 0, 1))
            # Ø2.10 mm M2.5 self-tapping pilot bore (for non-magnetic Nylon/Brass M2.5 screws; closed bottom above CFRP)
            imu_tap = Part.makeCylinder(1.05, z_imu_boss_top - (z_base + 0.80) + 0.50, App.Vector(bx_i, by_i, z_base + 0.80), App.Vector(0, 0, 1))
            imu_boss = imu_boss.cut(imu_tap)
            plate = plate.fuse(imu_boss)

    # 8. Drill 10x Flat M3 Countersunk Mounting Holes LAST so bridges never occlude screw seats:
    #    - 4x Outer holes at (±45.0, ±30.0 mm) into Chassis_Core M3 Ruthex inserts
    #    - 4x Inner scanned throat holes at (±36.5, ±19.0 mm) through Body_Top into Chassis_Core
    #    - 2x Rear CFRP spacer clamping holes at (-90.0, 0.0) & (-120.0, 0.0) securing the Rear Switch Tail!
    mount_holes = [
        (45.0, 30.0), (45.0, -30.0), (-45.0, 30.0), (-45.0, -30.0),
        (36.5, 19.0), (36.5, -19.0), (-36.5, 19.0), (-36.5, -19.0),
        (-90.0, 0.0), (-120.0, 0.0),
    ]
    for mx, my in mount_holes:
        hole = Part.makeCylinder(1.65, 10.0, App.Vector(mx, my, z_base - 1.0), App.Vector(0, 0, 1))
        csink = Part.makeCone(1.65, 3.10, 1.45, App.Vector(mx, my, z_base + t_plate - 1.45), App.Vector(0, 0, 1))
        plate = plate.cut(hole).cut(csink)

    return plate.removeSplitter()


mount_solid = build_rpi_mount()
print(f"RPi & Triple-UBEC Mount Solid Valid: {mount_solid.isValid()}")
print(f"Faces: {len(mount_solid.Faces)}, Edges: {len(mount_solid.Edges)}")
print(f"Volume: {mount_solid.Volume:.2f} mm^3")
bb = mount_solid.BoundBox
print(f"BoundBox: X=[{bb.XMin:.1f}, {bb.XMax:.1f}], Y=[{bb.YMin:.1f}, {bb.YMax:.1f}], Z=[{bb.ZMin:.1f}, {bb.ZMax:.1f}]")

doc_name = "chassis_rpi_mount"
try:
    App.closeDocument(doc_name)
except Exception:
    pass

doc = App.newDocument(doc_name)
obj = doc.addObject("Part::Feature", "Chassis_RPi_Mount")
obj.Label = "Raspberry Pi 4 & Triple-UBEC Top-Deck Mounting Plate (v2)"
obj.Shape = mount_solid
obj.Visibility = True
if hasattr(obj, "ViewObject") and obj.ViewObject:
    obj.ViewObject.ShapeColor = (0.24, 0.24, 0.28)

doc.recompute()
doc.saveAs(fcstd_plate_path)
mount_solid.exportStl(f"{repo_root}/hardware/mechanics/export/urdf/meshes/chassis_rpi_mount.stl")
if "--export" in sys.argv:
    export_step_dir = f"{repo_root}/hardware/mechanics/export/step/custom/v2/parts/chassis"
    export_stl_dir = f"{repo_root}/hardware/mechanics/export/stl/custom/v2/parts/chassis"
    os.makedirs(export_step_dir, exist_ok=True)
    os.makedirs(export_stl_dir, exist_ok=True)
    mount_solid.exportStep(f"{export_step_dir}/chassis_rpi_mount.step")
    mount_solid.exportStl(f"{export_stl_dir}/chassis_rpi_mount.stl")
print(f"Saved FreeCAD model: {fcstd_plate_path}")
App.closeDocument(doc_name)


def patch_gui_visibility(filepath):
    temp_zip = filepath + ".tmp"
    with zipfile.ZipFile(filepath, "r") as zin:
        with zipfile.ZipFile(temp_zip, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "GuiDocument.xml":
                    xml_str = data.decode("utf-8")
                    xml_str = xml_str.replace('<Bool value="false"/>', '<Bool value="true"/>')
                    data = xml_str.encode("utf-8")
                zout.writestr(item, data)
    os.replace(temp_zip, filepath)


patch_gui_visibility(fcstd_plate_path)
print("✔ Patched GuiDocument.xml for full visibility")
sys.exit(0)
