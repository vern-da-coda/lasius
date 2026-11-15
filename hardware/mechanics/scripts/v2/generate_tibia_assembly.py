#!/usr/bin/env python3
"""
Generate Lasius Tibia v2 Subsystem Assembly with Integrated Foot Sensor
========================================================================
Organic Bionic Monocoque with Formschluss-Schraub-Hybrid (Option C):
- Seamless G1-continuous bionic silhouette flowing gracefully from the knee servo cage
  down through the beam and directly onto the foot rocker claw sole
- Slender organic foot joint terminal wrapping closely around the pivot hub (R = 6.5 mm)
  and spring pocket, completely eliminating any bulbous snout or awkward steps
- 45-degree smooth transition between the 11.0 mm fork cheek and the 7.0 mm claw blade
- Split clevis fork:
  1. Monolithic Cheek A (Fixed, -Z side): Integrates open sensor bay, spring pocket,
     conduit channel, M3 and M2 Ruthex brass insert seats, and interlocking retaining groove
  2. Removable Cheek B (Cover, +Z side): Form-fit tongue, 1x flush M2 countersunk screw,
     and counterbore for M3 pivot pin
  3. Bionic Foot Rocker (Tarsus): Slender claw sole continuing the dorsal curvature
     monotonically to the ground contact patch
"""

import math
import os
import sys
import FreeCAD as App
import Part

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
sys.path.append(f"{repo_root}/hardware/mechanics/scripts/v2")
import generate_tibia

print("--- Generating Lasius Tibia v2 Organic Bionic Assembly ---")

cots_dir = f"{repo_root}/hardware/mechanics/models/cots"
concept_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/concepts/tibia_foot"
export_step_dir = f"{repo_root}/hardware/mechanics/export/step/custom/v2/concepts/tibia_foot"
export_stl_dir = f"{repo_root}/hardware/mechanics/export/stl/custom/v2/concepts/tibia_foot"
renders_dir = f"{repo_root}/hardware/mechanics/drawings/renders"

os.makedirs(concept_dir, exist_ok=True)
os.makedirs(export_step_dir, exist_ok=True)
os.makedirs(export_stl_dir, exist_ok=True)
os.makedirs(renders_dir, exist_ok=True)

# Colors
COLOR_CFRP = (0.22, 0.22, 0.24)        # Dark carbon anthracite
COLOR_COVER = (0.28, 0.28, 0.32)       # Contrasting carbon cover
COLOR_SERVO = (0.12, 0.12, 0.12)       # Matte black servo
COLOR_ORANGE = (0.92, 0.45, 0.10)      # Anodized orange rocker
COLOR_SWITCH = (0.15, 0.15, 0.15)      # Matte black switch
COLOR_SPRING = (0.85, 0.85, 0.88)      # Stainless spring
COLOR_BRASS = (0.85, 0.70, 0.20)       # Brass hardware
COLOR_STEEL = (0.80, 0.80, 0.82)       # Steel fasteners
COLOR_TOP_CAGE = (0.20, 0.48, 0.68)    # Anodized metallic blue top cage accent

# =============================================================================
# 1. Build Slender Organic Outer Contour of Unified Tibia Body
# =============================================================================
def build_organic_tibia_outer_wire():
    """
    Construct the slender, organic G1-continuous outer silhouette of the Tibia.
    Tapers gracefully over the spring pocket down to the pivot hub (R = 6.5 mm at (-122, -14)),
    forming a completely natural joint transition for the foot rocker.
    """
    c2 = App.Vector(17.271, 36.152, 0.0)
    r2 = 1.489
    a2_s = math.atan2(37.610 - c2.y, 17.570 - c2.x)
    a2_m = 0.05
    a2_e = math.atan2(34.780 - c2.y, 17.850 - c2.x)
    p2_s = App.Vector(c2.x + r2 * math.cos(a2_s), c2.y + r2 * math.sin(a2_s), 0.0)
    p2_m = App.Vector(c2.x + r2 * math.cos(a2_m), c2.y + r2 * math.sin(a2_m), 0.0)
    p2_e = App.Vector(c2.x + r2 * math.cos(a2_e), c2.y + r2 * math.sin(a2_e), 0.0)
    e2 = Part.Arc(p2_s, p2_m, p2_e).toShape()

    c4 = App.Vector(38.692, 19.268, 0.0)
    r4 = 2.458
    a4_s = math.atan2(21.650 - c4.y, 39.300 - c4.x)
    a4_m = 0.15
    a4_e = math.atan2(17.350 - c4.y, 40.230 - c4.x)
    p4_s = App.Vector(c4.x + r4 * math.cos(a4_s), c4.y + r4 * math.sin(a4_s), 0.0)
    p4_m = App.Vector(c4.x + r4 * math.cos(a4_m), c4.y + r4 * math.sin(a4_m), 0.0)
    p4_e = App.Vector(c4.x + r4 * math.cos(a4_e), c4.y + r4 * math.sin(a4_e), 0.0)
    e4 = Part.Arc(p4_s, p4_m, p4_e).toShape()

    c56 = App.Vector(15.00, -10.00, 0.0)
    r56 = 4.25
    a56_s = 0.06 * math.pi
    a56_m = -0.22 * math.pi
    a56_e = -0.50 * math.pi
    p56_s = App.Vector(c56.x + r56 * math.cos(a56_s), c56.y + r56 * math.sin(a56_s), 0.0)
    p56_m = App.Vector(c56.x + r56 * math.cos(a56_m), c56.y + r56 * math.sin(a56_m), 0.0)
    p56_e = App.Vector(c56.x + r56 * math.cos(a56_e), c56.y + r56 * math.sin(a56_e), 0.0)
    e5b = Part.Arc(p56_s, p56_m, p56_e).toShape()

    poles3 = [
        p2_e,
        (17.012, 34.366),
        (13.720, 32.826),
        (9.038, 30.847),
        (5.089, 28.080),
        (2.350, 25.600),
        (2.433, 22.498),
        (2.550, 19.300),
        (3.400, 16.800),
        (6.685, 15.880),
        (10.500, 16.100),
        (16.500, 16.900),
        (23.500, 18.100),
        (30.500, 19.800),
        (36.800, 21.300),
        p4_s,
    ]
    e3 = generate_tibia.make_g1_cubic_bspline(poles3, generate_tibia.circle_tangent_cw(c2, p2_e), generate_tibia.circle_tangent_cw(c4, p4_s))

    poles5 = [
        p4_e,
        (38.50, 16.20),
        (33.50, 12.80),
        (27.20, 7.80),
        (22.40, 2.20),
        (20.10, -2.80),
        (19.50, -6.50),
        p56_s,
    ]
    e5 = generate_tibia.make_g1_cubic_bspline(poles5, generate_tibia.circle_tangent_cw(c4, p4_e), generate_tibia.circle_tangent_cw(c56, p56_s))

    p6_e = App.Vector(-36.50, -14.25, 0.0)
    e6 = Part.makeLine(p56_e, p6_e)

    # Distal joint terminal points around spring pocket and pivot hub:
    p_spring_cheek = App.Vector(-130.0, -1.5, 0.0)
    p_hub_left = App.Vector(-128.5, -14.0, 0.0)
    p_hub_bot = App.Vector(-122.0, -20.5, 0.0)

    arc_cheek_tip = Part.Arc(p_spring_cheek, App.Vector(-131.0, -8.0, 0.0), p_hub_left).toShape()
    arc_pivot_bot = Part.Arc(p_hub_left, App.Vector(-126.5, -19.0, 0.0), p_hub_bot).toShape()

    # Dorsal arch
    poles1 = [
        p_spring_cheek,
        (-128.0, 0.0),
        (-124.0, 2.5),
        (-116.0, 5.5),
        (-106.0, 8.5),
        (-92.0, 12.5),
        (-78.200, 16.948),
        (-62.257, 22.984),
        (-49.101, 28.027),
        (-35.845, 31.870),
        (-23.493, 34.775),
        (-10.498, 36.789),
        (-0.008, 37.954),
        (7.477, 38.458),
        (12.888, 38.362),
        (15.874, 37.981),
        p2_s,
    ]
    t_dorsal_start = App.Vector(1.0, 0.5, 0.0)
    e1 = generate_tibia.make_g1_cubic_bspline(poles1, t_dorsal_start, generate_tibia.circle_tangent_cw(c2, p2_s))

    # Ventral arch
    poles7 = [
        p6_e,
        (-39.50, -14.25),
        (-44.00, -12.80),
        (-52.50, -9.40),
        (-61.50, -6.80),
        (-69.50, -5.75),
        (-77.50, -6.10),
        (-87.00, -8.00),
        (-96.50, -10.50),
        (-106.50, -14.00),
        (-115.00, -17.50),
        p_hub_bot,
    ]
    t_ventral_end = App.Vector(-1.0, -0.2, 0.0)
    e7 = generate_tibia.make_g1_cubic_bspline(poles7, App.Vector(-1.0, 0.0, 0.0), t_ventral_end)

    wire = Part.Wire([arc_cheek_tip, arc_pivot_bot, e7, e6, e5b, e5, e4, e3, e2, e1])
    return wire

outer_wire = build_organic_tibia_outer_wire()

# =============================================================================
# 2. Build Monolithic Tibia Body & Removable Cover
# =============================================================================
print("1. Building Monolithic Tibia Body & Removable Cover...")

# 2.1 Base Tibia Claw Body (Z in [-3.0, +4.0] mm)
claw_base = Part.Face(outer_wire).extrude(App.Vector(0, 0, 7.0)).translate(App.Vector(0, 0, -3.0))
w_cutout = generate_tibia.build_g1_claw_cutout_wire()
cutout_prism = Part.Face(w_cutout).extrude(App.Vector(0, 0, 60.0)).translate(App.Vector(0, 0, -30.0))
claw_base = claw_base.cut(cutout_prism)

# Add raised servo pads & Warren truss servo cage
ear_bosses = generate_tibia.build_servo_ear_bosses().cut(cutout_prism)
claw_base = claw_base.fuse(ear_bosses)
truss_cage = generate_tibia.build_triangulated_truss_servo_cage()
upper_cheeks = generate_tibia.build_upper_truss_cheeks()
tibia_base = claw_base.fuse(truss_cage).fuse(upper_cheeks).cut(cutout_prism)

# Cut servo body pocket, counter bearing, ear holes (solid mounting pads without cutout)
servo_pocket = Part.makeBox(40.80, 20.30, 48.00, App.Vector(-31.65, -10.15, -20.00))
tibia_base = tibia_base.cut(servo_pocket)

screw_bore = Part.makeCylinder(2.05, 6.0, App.Vector(0.0, 0.0, -24.0))
nut_pocket = generate_tibia.make_hex_nut_pocket_z(0.0, 0.0, -22.40, -19.50, sw=7.10)
tibia_base = tibia_base.cut(screw_bore).cut(nut_pocket)

for sx, sy in [(13.00, 5.00), (13.00, -5.00), (-35.50, 5.00), (-35.50, -5.00)]:
    tibia_base = tibia_base.cut(Part.makeCylinder(1.25, 25.0, App.Vector(sx, sy, -3.20)))

# 2.2 Extend Fork Cheeks to 11.0 mm total width (Z in [-5.0, +6.0] mm) at X < -72.0 mm
X_SPLIT = -72.0
DX_TONGUE = 3.0

pad_back = Part.Face(outer_wire).extrude(App.Vector(0, 0, 2.0)).translate(App.Vector(0, 0, -5.0))
clip_back = Part.makeBox(150.0 + X_SPLIT, 80.0, 20.0, App.Vector(-150.0, -40.0, -10.0))
pad_back = pad_back.common(clip_back)

pad_front = Part.Face(outer_wire).extrude(App.Vector(0, 0, 2.0)).translate(App.Vector(0, 0, 4.0))
clip_front = Part.makeBox(150.0 + X_SPLIT, 80.0, 20.0, App.Vector(-150.0, -40.0, -10.0))
pad_front = pad_front.common(clip_front)

tibia_base = tibia_base.fuse(pad_back).fuse(pad_front)

# 2.3 Cut Internal Clevis Slot & Sensor Bays (Transformed from local shank coordinates)
rot_deg = -67.59
rot_rad = math.radians(rot_deg)
rot_foot = App.Rotation(App.Vector(0, 0, 1), rot_deg)
px = -10.0 * math.sin(rot_rad)
py = 10.0 * math.cos(rot_rad)
base_pos = App.Vector(-122.0 - px, -14.0 - py, 0.5)
p_shank = App.Placement(base_pos, rot_foot)

slot_upper = Part.makeBox(12.0, 35.0, 6.0, App.Vector(-2.0, 8.0, -3.0))
slot_claw = Part.makeBox(45.0, 48.0, 6.0, App.Vector(-40.0, -32.0, -3.0))
sw_pocket = Part.makeBox(10.5, 16.5, 6.0, App.Vector(-5.5, 22.0, -3.0))

# Spring pocket with integrated solid stop pillar (D=2.4 mm) leaving exactly 0.60 mm compression travel:
pocket_cyl = Part.makeCylinder(2.40, 8.5, App.Vector(-14.0, 11.0, 0.0), App.Vector(0, 1, 0))
stop_pillar = Part.makeCylinder(1.20, 8.0, App.Vector(-14.0, 11.6, 0.0), App.Vector(0, 1, 0))
spring_pocket = pocket_cyl.cut(stop_pillar)

cable_conduit = Part.makeCylinder(1.80, 50.0, App.Vector(0.0, 35.0, 0.0), App.Vector(-0.15, 1.0, 0.0))

for c in [slot_upper, slot_claw, sw_pocket, spring_pocket, cable_conduit]:
    c.Placement = p_shank.multiply(c.Placement)

# Pivot bores at (-122.0, -14.0)
pivot_bore = Part.makeCylinder(1.60, 20.0, App.Vector(-122.0, -14.0, -10.0), App.Vector(0, 0, 1))
pivot_ruthex = Part.makeCylinder(2.10, 4.0, App.Vector(-122.0, -14.0, -5.0), App.Vector(0, 0, 1))

tibia_cut = tibia_base.cut(slot_upper).cut(slot_claw).cut(sw_pocket).cut(spring_pocket).cut(cable_conduit).cut(pivot_bore).cut(pivot_ruthex)

# 2.4 Formschluss Rebate in Tibia for Removable Cover:
# Cover sits in Z in [3.5, 6.0] mm for X < X_SPLIT
# Interlocking groove at X in [X_SPLIT - DX_TONGUE, X_SPLIT] in Z in [3.5, 4.8] mm
cut_main = Part.makeBox(150.0 + X_SPLIT - DX_TONGUE, 80.0, 3.5, App.Vector(-150.0, -40.0, 3.5))
cut_tongue = Part.makeBox(DX_TONGUE, 80.0, 1.3, App.Vector(X_SPLIT - DX_TONGUE, -40.0, 3.5))
rebate = cut_main.fuse(cut_tongue)

# M2 brass Ruthex pocket in Monolithic Tibia at (-100.0, -3.0)
m2_ruthex_mono = Part.makeCylinder(1.70, 5.0, App.Vector(-100.0, -3.0, 0.0), App.Vector(0, 0, 1))

tibia_mono_solid = tibia_cut.cut(rebate).cut(m2_ruthex_mono)

try:
    tibia_mono_solid = tibia_mono_solid.removeSplitter()
except Exception:
    pass

# 2.5 Build Removable Cover: tibia_foot_cover.FCStd
box_cover = Part.makeBox(150.0 + X_SPLIT, 80.0, 3.5, App.Vector(-150.0, -40.0, 3.5))
cover = Part.Face(outer_wire).extrude(App.Vector(0, 0, 2.5)).translate(App.Vector(0, 0, 3.5)).common(box_cover)

# Stepped tongue at top
step_cut = Part.makeBox(DX_TONGUE, 80.0, 2.0, App.Vector(X_SPLIT - DX_TONGUE, -40.0, 4.8))
cover = cover.cut(step_cut)

# M3 pivot pin through-hole and counterbore
m3_hole_cover = Part.makeCylinder(1.60, 10.0, App.Vector(-122.0, -14.0, 0.0), App.Vector(0, 0, 1))
m3_cbore_cover = Part.makeCylinder(3.10, 1.5, App.Vector(-122.0, -14.0, 4.5), App.Vector(0, 0, 1))
cover = cover.cut(m3_hole_cover).cut(m3_cbore_cover)

# 1x M2 retaining screw countersink at (-100.0, -3.0)
m2_hole_cover = Part.makeCylinder(1.10, 10.0, App.Vector(-100.0, -3.0, 0.0), App.Vector(0, 0, 1))
m2_csink_cover = Part.makeCone(2.2, 1.1, 1.1, App.Vector(-100.0, -3.0, 4.9), App.Vector(0, 0, 1))
cover = cover.cut(m2_hole_cover).cut(m2_csink_cover)

try:
    cover = cover.removeSplitter()
except Exception:
    pass

# Save Monolithic Body
fcstd_mono_path = f"{concept_dir}/tibia_sensor_monocoque.FCStd"
try:
    App.closeDocument("tibia_sensor_monocoque")
except Exception:
    pass
doc_mono = App.newDocument("tibia_sensor_monocoque")
obj_mono = doc_mono.addObject("Part::Feature", "Tibia_Sensor_Monocoque")
obj_mono.Label = "Tibia v2 Monocoque Body with Integrated Fixed Cheek"
obj_mono.Shape = tibia_mono_solid
doc_mono.recompute()
doc_mono.saveAs(fcstd_mono_path)
print(f"✔ Saved: {fcstd_mono_path} (Valid={tibia_mono_solid.isValid()}, Volume={tibia_mono_solid.Volume:.1f} mm3)")

# Save Removable Cover
fcstd_cover_path = f"{concept_dir}/tibia_foot_cover.FCStd"
try:
    App.closeDocument("tibia_foot_cover")
except Exception:
    pass
doc_cover = App.newDocument("tibia_foot_cover")
obj_cover = doc_cover.addObject("Part::Feature", "Tibia_Foot_Cover")
obj_cover.Label = "Tibia Foot Service Cover (Cheek B with Form-Fit Tongue)"
obj_cover.Shape = cover
doc_cover.recompute()
doc_cover.saveAs(fcstd_cover_path)
print(f"✔ Saved: {fcstd_cover_path} (Valid={cover.isValid()}, Volume={cover.Volume:.1f} mm3)")

# =============================================================================
# 3. Build Full Subsystem Assembly: tibia_assembly.FCStd
# =============================================================================
print("2. Building Full Subsystem Assembly: tibia_assembly.FCStd...")
doc_asm_name = "tibia_assembly"
try:
    App.closeDocument(doc_asm_name)
except Exception:
    pass
fcstd_asm_path = f"{concept_dir}/tibia_assembly.FCStd"
doc_asm = App.newDocument(doc_asm_name)
doc_asm.saveAs(fcstd_asm_path)

# Open COTS and components
doc_servo = App.openDocument(f"{cots_dir}/servo_nr645.FCStd")
doc_rocker = App.openDocument(f"{concept_dir}/tibia_foot_rocker.FCStd")
doc_sw = App.openDocument(f"{cots_dir}/microswitch_subminiature.FCStd")
doc_sp = App.openDocument(f"{cots_dir}/compression_spring_4x12.FCStd")

asm_part = doc_asm.addObject("App::Part", "Tibia_Assembly")
asm_part.Label = "Lasius Tibia v2 Subsystem Assembly with Foot Contact Sensor"

def make_link(name, label, target_obj, placement, color=None):
    lnk = doc_asm.addObject("App::Link", name)
    lnk.setLink(target_obj)
    lnk.Label = label
    lnk.Placement = placement
    asm_part.addObject(lnk)
    lnk.Visibility = True
    if hasattr(lnk, "ViewObject") and lnk.ViewObject is not None:
        try:
            lnk.ViewObject.Visibility = True
            if color is not None:
                lnk.ViewObject.OverrideMaterial = True
                mat = lnk.ViewObject.ShapeMaterial
                mat.DiffuseColor = color
                lnk.ViewObject.ShapeMaterial = mat
        except Exception:
            pass
    return lnk

# 1. Monolithic Tibia Body (Fixed Cheek A + Integrated Lower & Upper Cage Cheeks)
make_link("Tibia_Body", "1. Tibia v2 Monocoque (Warren Truss + Fixed Cheek A)", obj_mono, App.Placement(), COLOR_CFRP)

# 2. Knee Servo
p_servo = App.Placement(App.Vector(0.0, 0.0, 18.8), App.Rotation(App.Vector(0, 0, 1), 180.0))
make_link("Knee_Servo", "2. Knee Servo (Torcster NR-645 COTS)", doc_servo.Objects[0], p_servo, COLOR_SERVO)

# 3. Bionic Foot Rocker (Outward Tarsus)
make_link("Tibia_Foot_Rocker", "3. Bionic Tarsus Rocker Foot (+52% Lever)", doc_rocker.Objects[0], p_shank, COLOR_ORANGE)

# 4. Microswitch
p_sw_local = App.Placement(App.Vector(4.3 - 6.7, 23.0, 0.0), App.Rotation())
make_link("Microswitch", "4. Subminiature Microswitch (COTS)", doc_sw.Objects[0], p_shank.multiply(p_sw_local), COLOR_SWITCH)

# 5. Compression Spring
p_sp_local = App.Placement(App.Vector(-14.0, 8.5, 0.0), App.Rotation())
make_link("Compression_Spring", "5. Stainless Preload Spring (COTS)", doc_sp.Objects[0], p_shank.multiply(p_sp_local), COLOR_SPRING)

# 6. Removable Service Cover (Cheek B)
make_link("Tibia_Foot_Cover", "6. Removable Service Cover (Cheek B Form-Fit)", obj_cover, App.Placement(), COLOR_COVER)

# 7. M3 Hardened Pivot Pin & Ruthex
pin_obj = doc_asm.addObject("Part::Feature", "Pivot_Pin_Assembly")
pin_obj.Label = "7. M3 Hardened Pivot Pin & Ruthex"
pin_head = Part.makeCylinder(2.8, 1.5, App.Vector(-122.0, -14.0, 4.5), App.Vector(0, 0, 1))
pin_shaft = Part.makeCylinder(1.5, 11.0, App.Vector(-122.0, -14.0, -5.0), App.Vector(0, 0, 1))
ruthex = Part.makeCylinder(2.1, 4.0, App.Vector(-122.0, -14.0, -5.0), App.Vector(0, 0, 1))
pin_obj.Shape = pin_head.fuse(pin_shaft).fuse(ruthex)
asm_part.addObject(pin_obj)
if hasattr(pin_obj, "ViewObject") and pin_obj.ViewObject:
    try:
        pin_obj.ViewObject.ShapeColor = COLOR_BRASS
    except Exception:
        pass

# 8. M2 DIN 7991 Flush Countersunk Screw
screw_m2 = doc_asm.addObject("Part::Feature", "Cover_Retaining_Screw_M2")
screw_m2.Label = "8. M2x6 Flush Countersunk Retaining Screw"
head_m2 = Part.makeCone(1.1, 2.2, 1.1, App.Vector(-100.0, -3.0, 4.9), App.Vector(0, 0, 1))
shank_m2 = Part.makeCylinder(1.0, 6.0, App.Vector(-100.0, -3.0, 0.0), App.Vector(0, 0, 1))
ruthex_m2 = Part.makeCylinder(1.7, 4.0, App.Vector(-100.0, -3.0, 0.0), App.Vector(0, 0, 1))
screw_m2.Shape = head_m2.fuse(shank_m2).fuse(ruthex_m2)
asm_part.addObject(screw_m2)
if hasattr(screw_m2, "ViewObject") and screw_m2.ViewObject:
    try:
        screw_m2.ViewObject.ShapeColor = COLOR_STEEL
    except Exception:
        pass

doc_asm.recompute()
doc_asm.save()
print(f"✔ Saved Assembly: {fcstd_asm_path}")

# =============================================================================
# 4. Export STEP & STL
# =============================================================================
print("3. Exporting STEP and STL...")
step_asm_path = f"{export_step_dir}/tibia_assembly.step"
stl_asm_path = f"{export_stl_dir}/tibia_assembly.stl"

export_objs = [obj_mono, obj_cover, doc_servo.Objects[0], doc_rocker.Objects[0], doc_sw.Objects[0], doc_sp.Objects[0], pin_obj, screw_m2]
Part.export(export_objs, step_asm_path)
print(f"✔ Exported STEP: {step_asm_path}")

comp = Part.Compound([o.Shape for o in export_objs])
comp.exportStl(stl_asm_path)
print(f"✔ Exported STL: {stl_asm_path}")

# Also export individual printable components
obj_mono.Shape.exportStep(f"{export_step_dir}/tibia_sensor_monocoque.step")
obj_mono.Shape.exportStl(f"{export_stl_dir}/tibia_sensor_monocoque.stl")
obj_cover.Shape.exportStep(f"{export_step_dir}/tibia_foot_cover.step")
obj_cover.Shape.exportStl(f"{export_stl_dir}/tibia_foot_cover.stl")
print("✔ Exported individual STEP & STL for Monocoque & Cover")

print("=== Tibia Assembly Generation Complete! ===")
