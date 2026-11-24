#!/usr/bin/env python3
"""
Generate Lasius Two-Level Segmented Monocoque Central Core & Assembly v2 (FreeCAD 1.1+)
=======================================================================================
Architecture (Option 1 — Form-Fit 2-Level Split + 4x M3 x 50 mm Metal Tie-Rod Standoffs):
  - Pure analytical G1-continuous 3D-printed monocoque central core spanning the 51.30 mm
    vertical gap between Body_Bottom (Z = 2.00 mm) and Body_Top (Z = 53.30 mm), 100%
    symmetric across X in [-84.5, +84.5 mm] with both Front (Head/Neck) and Rear
    (Gaster / Power-Gaster G2) vertical dovetail sockets.
  - Horizontally segmented at parametric Z_SPLIT = 24.00 mm (underside of Intermediate Deck)
    so Level 1 (battery bay) can be iterated & reprinted independently (~52 g, ~1.5 h)
    without disturbing Level 2's bolted electronics — while eliminating 100% of interior
    3D-printing supports under the floating Intermediate Deck!
    * Level 1 — chassis_core_lower.FCStd (Z = 0.02 .. 23.99 mm + male alignment features):
      - Flush sharp-cornered lower plug (Z = 0.02 .. 2.00 mm, 159.8 x 49.8 mm) sealing
        Body_Bottom's 160 x 50 mm cutout with zero protrusion above Z = 2.00 mm.
      - CoG-balanced Front-Center Battery & XT60 Bay (X in [-40.0, +76.0 mm]) with
        support-free 45° corbelled LiPo stop shoulders and arched rear bulkhead wall.
      - Closed Rear ToF & Power-Riser Zone (X in [-82.5, -42.5 mm]) above Belly Pan ToF.
      - Triple form-fit male interface (preserving full 1.60 mm outer hull wall thickness!):
        1) 4x concentric pillar centering collars (Ø8.30 x 2.26 mm, 45° top chamfer) at (±45, ±30)
        2) 5x segmented internal perimeter alignment tongues (1.80 mm wide, Z = 23.99..25.85 mm,
           45° support-free underside gusset ramps inside Lower wall: 1x Front, 2x Rear flanking
           rear_pwr_slot, 2x Middle-Waist curves)
        3) External 0.35 mm 45° bionic V-shadow-groove bevel + dovetail seam lead-in chamfers.
    * Level 2 — chassis_core_upper.FCStd (Z = 24.01 .. 53.28 mm — prints 100% support-free!):
      - Solid Intermediate Deck (Zwischenboden, Z = 24.01 .. 26.00 mm) flat on build plate!
      - 4x recessed pillar centering sockets (Ø8.60 x 2.49 mm + support-free 45° conical roof)
        + 5x through-deck perimeter tongue notches (0.15 mm slip clearance, zero overhang!).
      - 10x integrated M2.5 PCB mounting bosses (2x PCA9685 + central Sensor Hub / TCA9548A).
      - 3x Intermediate Deck pass-through slots (ToF I2C, mid XT60 riser, rear power riser).
      - 4x organic bionic inter-leg cable ports (Z = 28.5..40.0 mm) with micro-zip-tie saddles.
      - 100% solid & seamless outer waist walls (all controls unified on Body_Top RPi_Mount).
    * Vertical Z-Clamping (Option 1):
      - 4x COTS M3 x 50.0 mm round metal female-female standoff sleeves (Ø5.0 mm OD,
        standoff_m3x50_round.FCStd) seated inside continuous Ø5.25 mm pillar bores at
        (±45.0, ±30.0 mm), Z = 2.65 .. 52.65 mm (0.65 mm preload margin to both CFRP plates).
      - Existing Belly_Pan (4x M3x10/12 up) and RPi_Mount (4x M3x10/12 down) thread directly
        into the metal sleeves: zero changes to Belly_Pan/RPi_Mount, zero Ruthex M3 inserts
        needed in Core, 100% metal tensile load path across the Z-seam!
"""

import math
import os
import sys
import FreeCAD as App
import Part

print("--- Generating Lasius Segmented 2-Level Monocoque Central Core (Lower + Upper + Assembly) ---")

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = f"{repo_root}/hardware/mechanics/models/custom/v2/parts/chassis"
asm_dir = f"{repo_root}/hardware/mechanics/models/custom/v2"
cots_dir = f"{repo_root}/hardware/mechanics/models/cots"
export_step_dir = f"{repo_root}/hardware/mechanics/export/step/custom/v2"
export_stl_dir = f"{repo_root}/hardware/mechanics/export/stl/custom/v2"

os.makedirs(models_dir, exist_ok=True)
os.makedirs(asm_dir, exist_ok=True)
if "--export" in sys.argv:
    os.makedirs(f"{export_step_dir}/parts/chassis", exist_ok=True)
    os.makedirs(f"{export_stl_dir}/parts/chassis", exist_ok=True)

# -----------------------------------------------------------------------------
# Master Parametric Constants (adjust Z_SPLIT to resize Level 1 height cleanly)
# -----------------------------------------------------------------------------
Z_BASE = 2.02             # Top of Body_Bottom CFRP plate (Z = 2.00) + 0.02 mm CAD clearance
Z_TOP = 53.28             # Bottom of Body_Top CFRP plate (Z = 53.30) - 0.02 mm CAD clearance
Z_SPLIT = 24.00           # Horizontal segmentation plane (underside of Intermediate Deck)
SEAM_HALF_GAP = 0.01      # 0.02 mm nominal CAD Z-gap for clean 0.0000 mm^3 B-Rep contact check
Z_LOWER_TOP = Z_SPLIT - SEAM_HALF_GAP   # 23.99 mm
Z_UPPER_BOT = Z_SPLIT + SEAM_HALF_GAP   # 24.01 mm
DECK_THICKNESS = 2.00
Z_DECK_TOP = Z_SPLIT + DECK_THICKNESS   # 26.00 mm

T_WALL = 1.60             # Full outer hull wall thickness (never thinned at the seam!)
R_PILLAR = 5.00           # Structural corner pillar radius (Ø10.0 mm -> >= 2.38 mm radial wall)
R_STANDOFF_BORE = 2.625   # Ø5.25 mm through-bore for COTS Ø5.0 mm M3 x 50 mm metal standoff sleeve

# Pillar Centering Collars (Male on Lower -> Female socket with 45° roof in Upper)
R_COLLAR_MALE = 4.15      # Ø8.30 mm -> 1.525 mm solid ring wall (4 perimeters around Ø5.25 bore!)
Z_COLLAR_MALE_TOP = Z_SPLIT + 2.25      # 26.25 mm (protrudes 2.26 mm into Upper)
COLLAR_CHAMFER = 0.50     # 45° lead-in chamfer on top of male collar
R_COLLAR_FEMALE = 4.30    # Ø8.60 mm -> 0.15 mm radial slip-fit clearance
Z_COLLAR_FEMALE_TOP = Z_SPLIT + 2.50    # 26.50 mm (0.25 mm axial top clearance + 45° roof to bore)

# Internal Perimeter Alignment Tongues (Full outer 1.60 mm wall preserved!)
TONGUE_W = 1.80           # Radial thickness inward from inner_face_valid
TONGUE_CLEAR_XY = 0.15    # Slip-fit clearance around tongue in Upper's deck notch
Z_TONGUE_TOP = Z_DECK_TOP - 0.15        # 25.85 mm (strictly recessed below Z = 26.00 deck!)
Z_TONGUE_RAMP_BOT = Z_LOWER_TOP - TONGUE_W  # 22.19 mm (exact 45° support-free underside ramp!)

# External Bionic V-Shadow-Groove Bevel along Z_SPLIT
SHADOW_BEVEL = 0.35       # 0.35 x 0.35 mm 45° bevel -> 1.25 mm min outer wall, zero elephant-foot!

STANDOFFS = [
    (45.0, 30.0),
    (45.0, -30.0),
    (-45.0, 30.0),
    (-45.0, -30.0),
]


# -----------------------------------------------------------------------------
# Geometry Helpers
# -----------------------------------------------------------------------------
def make_rounded_rect_solid(x_min, x_max, y_min, y_max, r_corner, z_min, z_max):
    """Constructs a filleted 3D solid prism in the X-Y plane extruded along Z."""
    dx = x_max - x_min
    dy = y_max - y_min
    r = min(r_corner, dx / 2.0 - 0.1, dy / 2.0 - 0.1)
    k = r * (1.0 - 1.0 / math.sqrt(2.0))
    pts = [
        (x_min + r, y_max),
        (x_max - r, y_max),
        (x_max - k, y_max - k),
        (x_max, y_max - r),
        (x_max, y_min + r),
        (x_max - k, y_min + k),
        (x_max - r, y_min),
        (x_min + r, y_min),
        (x_min + k, y_min + k),
        (x_min, y_min + r),
        (x_min, y_max - r),
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


def make_dovetail_prism(x_throat, x_base, w_throat, w_base, z_min, z_max, x_overshoot=0.0):
    """Constructs a dovetail prism in the X-Y plane extruded along Z."""
    if abs(x_overshoot) > 1e-4:
        pts = [
            (x_throat + x_overshoot,  w_throat / 2.0),
            (x_throat,                w_throat / 2.0),
            (x_base,                  w_base / 2.0),
            (x_base,                 -w_base / 2.0),
            (x_throat,               -w_throat / 2.0),
            (x_throat + x_overshoot, -w_throat / 2.0),
        ]
    else:
        pts = [
            (x_throat,  w_throat / 2.0),
            (x_base,    w_base / 2.0),
            (x_base,   -w_base / 2.0),
            (x_throat, -w_throat / 2.0),
        ]
    v = [App.Vector(px, py, z_min) for px, py in pts]
    edges = [Part.makeLine(v[i], v[(i + 1) % len(v)]) for i in range(len(v))]
    face = Part.Face(Part.Wire(edges))
    return face.extrude(App.Vector(0.0, 0.0, z_max - z_min))


def make_filleted_boss(x_start, x_end, y_half, r_corner, z_min, z_max):
    """Constructs a filleted rectangular boss in X-Y extruded along Z."""
    dx = abs(x_end - x_start)
    xmin = min(x_start, x_end)
    xmax = max(x_start, x_end)
    ymin = -y_half
    ymax = y_half
    r = min(r_corner, dx / 2.0 - 0.1, y_half - 0.1)
    k = r * (1.0 - 1.0 / math.sqrt(2.0))
    if x_end > x_start:  # Front boss
        pts = [
            (xmin, ymax),
            (xmax - r, ymax),
            (xmax - k, ymax - k),
            (xmax, ymax - r),
            (xmax, ymin + r),
            (xmax - k, ymin + k),
            (xmax - r, ymin),
            (xmin, ymin),
        ]
    else:  # Rear boss
        pts = [
            (xmax, ymin),
            (xmin + r, ymin),
            (xmin + k, ymin + k),
            (xmin, ymin + r),
            (xmin, ymax - r),
            (xmin + k, ymax - k),
            (xmin + r, ymax),
            (xmax, ymax),
        ]
    v = [App.Vector(px, py, z_min) for px, py in pts]
    wire = Part.Wire(Part.makePolygon(v + [v[0]]))
    face = Part.Face(wire)
    return face.extrude(App.Vector(0.0, 0.0, z_max - z_min))


def make_organic_port_cutter(x_center, z_center, width, height, r_corner, y_min, y_max):
    """Constructs an organic, corner-filleted bionic aperture cutter in the X-Z plane, extruded along Y."""
    dx = width
    dz = height
    r = min(r_corner, dx / 2.0 - 0.1, dz / 2.0 - 0.1)
    x1, x2 = x_center - dx / 2.0, x_center + dx / 2.0
    z1, z2 = z_center - dz / 2.0, z_center + dz / 2.0
    k = r * (1.0 - 1.0 / math.sqrt(2.0))
    pts = [
        (x1 + r, z2),
        (x2 - r, z2),
        (x2 - k, z2 - k),
        (x2, z2 - r),
        (x2, z1 + r),
        (x2 - k, z1 + k),
        (x2 - r, z1),
        (x1 + r, z1),
        (x1 + k, z1 + k),
        (x1, z1 + r),
        (x1, z2 - r),
        (x1 + k, z2 - k),
    ]
    v = [App.Vector(px, y_min, pz) for px, pz in pts]
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
    return face.extrude(App.Vector(0.0, y_max - y_min, 0.0))


def make_loft_ring_band(outer_2d_lo, inner_2d_lo, z_lo, outer_2d_hi, inner_2d_hi, z_hi):
    """Creates a clean annular loft/cut solid between two concentric 2D profiles (e.g., 45° perimeter bevel)."""
    w_o_lo = outer_2d_lo.OuterWire.copy()
    w_o_lo.translate(App.Vector(0, 0, z_lo))
    w_o_hi = outer_2d_hi.OuterWire.copy()
    w_o_hi.translate(App.Vector(0, 0, z_hi))
    solid_outer = Part.makeLoft([w_o_lo, w_o_hi], True, True)

    w_i_lo = inner_2d_lo.OuterWire.copy()
    w_i_lo.translate(App.Vector(0, 0, z_lo))
    w_i_hi = inner_2d_hi.OuterWire.copy()
    w_i_hi.translate(App.Vector(0, 0, z_hi))
    solid_inner = Part.makeLoft([w_i_lo, w_i_hi], True, True)
    return solid_outer.cut(solid_inner)


# -----------------------------------------------------------------------------
# 0. Shared Pure Analytical G1-Continuous 2D Bionic Hull Profile
# -----------------------------------------------------------------------------
def arc_mid_by_angle(cx, cy, r, p1, p2, ccw=True):
    a1 = math.atan2(p1.y - cy, p1.x - cx)
    a2 = math.atan2(p2.y - cy, p2.x - cx)
    da = (a2 - a1) % (2.0 * math.pi)
    if not ccw:
        da = da - 2.0 * math.pi
    am = a1 + 0.5 * da
    return App.Vector(cx + r * math.cos(am), cy + r * math.sin(am), 0.0)


d_fc = math.hypot(86.0 - 45.0, 65.0 - 30.0)
R_ear = d_fc - 45.0  # 8.9073 mm -> exact G1 tangency with R = 45.00 mm front/rear coxa swing circles
ux_fc, uy_fc = (86.0 - 45.0) / d_fc, (65.0 - 30.0) / d_fc
T_fc_x, T_fc_y = 45.0 + R_ear * ux_fc, 30.0 + R_ear * uy_fc

a_w = 29.0 - R_ear
Yw = (45.0**2 + 30.0**2 - a_w**2) / (60.0 - 2.0 * a_w)  # 127.2434 mm
Rw = Yw - 29.0  # 98.2434 mm
d_we = math.hypot(45.0, Yw - 30.0)
T_we_x = 45.0 * (1.0 - R_ear / d_we)
T_we_y = 30.0 + (Yw - 30.0) * (R_ear / d_we)
y_f84 = 65.0 - math.sqrt(45.0**2 - (86.0 - 84.5)**2)

p_f0    = App.Vector( 84.50, 0.0, 0.0)
p_f1    = App.Vector( 84.50, y_f84, 0.0)
p_tfc   = App.Vector( T_fc_x, T_fc_y, 0.0)
p_twe   = App.Vector( T_we_x, T_we_y, 0.0)
p_twe_r = App.Vector(-T_we_x, T_we_y, 0.0)
p_tfc_r = App.Vector(-T_fc_x, T_fc_y, 0.0)
p_r1    = App.Vector(-84.50, y_f84, 0.0)
p_r0    = App.Vector(-84.50, 0.0, 0.0)

upper_edges = [
    Part.makeLine(p_f0, p_f1),
    Part.Edge(Part.ArcOfCircle(p_f1, arc_mid_by_angle(86.0, 65.0, 45.0, p_f1, p_tfc, ccw=False), p_tfc)),
    Part.Edge(Part.ArcOfCircle(p_tfc, arc_mid_by_angle(45.0, 30.0, R_ear, p_tfc, p_twe, ccw=True), p_twe)),
    Part.Edge(Part.ArcOfCircle(p_twe, arc_mid_by_angle(0.0, Yw, Rw, p_twe, p_twe_r, ccw=False), p_twe_r)),
    Part.Edge(Part.ArcOfCircle(p_twe_r, arc_mid_by_angle(-45.0, 30.0, R_ear, p_twe_r, p_tfc_r, ccw=True), p_tfc_r)),
    Part.Edge(Part.ArcOfCircle(p_tfc_r, arc_mid_by_angle(-86.0, 65.0, 45.0, p_tfc_r, p_r1, ccw=False), p_r1)),
    Part.makeLine(p_r1, p_r0),
]

lower_edges = []
for e in reversed(upper_edges):
    c = e.Curve
    v0 = e.Vertexes[0].Point
    v1 = e.Vertexes[-1].Point
    m0 = App.Vector(v1.x, -v1.y, 0.0)
    m1 = App.Vector(v0.x, -v0.y, 0.0)
    if isinstance(c, Part.Line):
        lower_edges.append(Part.makeLine(m0, m1))
    else:
        pm = c.value(0.5 * (e.FirstParameter + e.LastParameter))
        lower_edges.append(Part.Edge(Part.ArcOfCircle(m0, App.Vector(pm.x, -pm.y, 0.0), m1)))

outer_2d_face = Part.Face(Part.Wire(Part.__sortEdges__(upper_edges + lower_edges)))
inner_2d_face = outer_2d_face.Faces[0].makeOffset2D(-T_WALL).Faces[0]
skin_trim_2d = outer_2d_face.Faces[0].makeOffset2D(-0.80).Faces[0]

# Exact concentric inner perimeter band for segmented alignment tongues (follows analytical G1 wall!):
# - Male tongue strip:   inside inner_2d_face, width TONGUE_W (1.80 mm), with 0.15 mm clearance to Upper wall!
#   Wait: leaving 0.15 mm radial clearance between male tongue OUTER face and Upper inner_2d_face makes
#   assembly silky-smooth on FDM without scraping — wait: let's seat male tongue flush against Lower's
#   inner wall (outer = inner_2d_face - 0.15 mm? No, if Lower inner wall IS inner_2d_face, stepping tongue
#   inward by 0.15 mm from inner_2d_face at Z > Z_LOWER_TOP OR keeping Upper's notch cut from
#   inner_2d_face_plus_0.00? Even cleaner:
#   - On Lower: tongue sits strictly flush inside inner_2d_face, outer face offset -0.15 mm from inner_2d_face
#     above Z_LOWER_TOP so Upper's 1.60 mm inner wall clears by 0.15 mm on the outside AND 0.15 mm on the inside!
#   Let's check widths:
#     * Male tongue radial band:  offset -(T_WALL + 0.15) to -(T_WALL + 0.15 + TONGUE_W) -> width 1.80 mm (4.5 perimeters!)
#     * Female deck notch band:   offset -(T_WALL - 0.05) to -(T_WALL + 0.15 + TONGUE_W + 0.15) -> cut into Upper's
#       Intermediate Deck (Z = 24.01..26.05), preserving full 1.60 mm outer wall (only touches inner_2d_face)!
#     * Below Z_LOWER_TOP, the 45° underside support-free ramp blends from inner_2d_face (at Z = Z_LOWER_TOP - 1.95)
#       inward to -(T_WALL + 0.15 + TONGUE_W) (at Z = Z_LOWER_TOP), solidly fused into Lower's 1.60 mm wall!
tongue_outer_2d = outer_2d_face.Faces[0].makeOffset2D(-(T_WALL + TONGUE_CLEAR_XY)).Faces[0]
tongue_inner_2d = outer_2d_face.Faces[0].makeOffset2D(-(T_WALL + TONGUE_CLEAR_XY + TONGUE_W)).Faces[0]
tongue_band_2d = tongue_outer_2d.cut(tongue_inner_2d)

notch_inner_2d = outer_2d_face.Faces[0].makeOffset2D(-(T_WALL + TONGUE_CLEAR_XY + TONGUE_W + TONGUE_CLEAR_XY)).Faces[0]
notch_band_2d = inner_2d_face.cut(notch_inner_2d)

# 5x Strategic Perimeter Alignment Tongue Windows (100% clear of LiPo, PCA9685, Sensor Hub, deck slots, saddles):
#   1. Front Bulkhead:       X in [+78.0, +84.5], Y in [-13.5, +13.5] (27.0 mm span)
#   2. Rear Left Flanking:   X in [-84.5, -78.0], Y in [+11.0, +16.5] (clear of rear_pwr_slot |Y|<=9.0)
#   3. Rear Right Flanking:  X in [-84.5, -78.0], Y in [-16.5, -11.0]
#   4. Left Middle Waist:    X in [-11.0, +11.0], Y in [+22.0, +32.0] (22.0 mm curved span bracing waist!)
#   5. Right Middle Waist:   X in [-11.0, +11.0], Y in [-32.0, -22.0]
TONGUE_WINDOWS = [
    ( 78.00,  84.50, -13.50,  13.50),   # 1. Front Bulkhead
    (-84.50, -78.00,  11.00,  16.50),   # 2. Rear Left Flanking
    (-84.50, -78.00, -16.50, -11.00),   # 3. Rear Right Flanking
    (-11.00,  11.00,  22.00,  32.00),   # 4. Left Middle Waist
    (-11.00,  11.00, -32.00, -22.00),   # 5. Right Middle Waist
]


def build_tongue_window_mask(z_min, z_max, pad_xy=0.0):
    """Builds the union of the 5 perimeter alignment window boxes (expanded by pad_xy for female notches)."""
    boxes = []
    for x1, x2, y1, y2 in TONGUE_WINDOWS:
        # Expand along the tangent direction (Y for front/rear bulkheads, X for waist walls)
        if abs(x1) > 70.0:  # Front / Rear bulkhead -> expand Y
            b = Part.makeBox(x2 - x1 + 2.0, (y2 - y1) + 2.0 * pad_xy, z_max - z_min,
                             App.Vector(x1 - 1.0, y1 - pad_xy, z_min))
        else:  # Middle waist -> expand X
            b = Part.makeBox((x2 - x1) + 2.0 * pad_xy, y2 - y1 + 2.0, z_max - z_min,
                             App.Vector(x1 - pad_xy, y1 - 1.0, z_min))
        boxes.append(b)
    mask = boxes[0]
    for b in boxes[1:]:
        mask = mask.fuse(b)
    return mask


# External 0.35 mm 45° Bionic V-Shadow-Groove Bevel Cutters around Z_SPLIT
outer_bevel_expand_2d = outer_2d_face.Faces[0].makeOffset2D(+1.00).Faces[0]
outer_bevel_in_2d = outer_2d_face.Faces[0].makeOffset2D(-SHADOW_BEVEL).Faces[0]
# Lower top bevel: cuts outer rim from offset 0.0 at Z_LOWER_TOP - SHADOW_BEVEL to -SHADOW_BEVEL at Z_LOWER_TOP
bevel_cut_lower = make_loft_ring_band(
    outer_bevel_expand_2d, outer_2d_face, Z_LOWER_TOP - SHADOW_BEVEL,
    outer_bevel_expand_2d, outer_bevel_in_2d, Z_LOWER_TOP + 0.05,
)
# Upper bottom bevel: cuts outer rim from -SHADOW_BEVEL at Z_UPPER_BOT to 0.0 at Z_UPPER_BOT + SHADOW_BEVEL
bevel_cut_upper = make_loft_ring_band(
    outer_bevel_expand_2d, outer_bevel_in_2d, Z_UPPER_BOT - 0.05,
    outer_bevel_expand_2d, outer_2d_face, Z_UPPER_BOT + SHADOW_BEVEL,
)


# =============================================================================
# 1. Build Part 1: chassis_core_lower.FCStd (Level 1 — Battery & ToF Tub)
# =============================================================================
def build_chassis_core_lower():
    doc_name = "chassis_core_lower"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)
    fcstd_path = f"{models_dir}/chassis_core_lower.FCStd"

    h_lower = Z_LOWER_TOP - Z_BASE  # 21.97 mm

    # 1.1 Outer G1 Hull (Z = 2.02 .. 23.99 mm) + Flush Body_Bottom Sealing Plug (Z = 0.02 .. 2.00 mm)
    hull = outer_2d_face.extrude(App.Vector(0.0, 0.0, h_lower))
    hull.translate(App.Vector(0.0, 0.0, Z_BASE))

    win_plug_lower = Part.makeBox(159.80, 49.80, 1.98, App.Vector(-79.90, -24.90, 0.02))
    hull_z_bridge = outer_2d_face.extrude(App.Vector(0.0, 0.0, 1.70))
    hull_z_bridge.translate(App.Vector(0.0, 0.0, 1.96))
    win_plug_bridge = Part.makeBox(159.80, 49.80, 1.64, App.Vector(-79.90, -24.90, 1.98)).common(hull_z_bridge)
    solid = hull.fuse(win_plug_bridge).fuse(win_plug_lower)

    # 1.2 Open-Top Level 1 Tub Cavity (Z = 3.62 .. 25.00 mm)
    inner_tub = inner_2d_face.extrude(App.Vector(0.0, 0.0, Z_LOWER_TOP - 3.62 + 1.0))
    inner_tub.translate(App.Vector(0.0, 0.0, 3.62))
    solid = solid.cut(inner_tub)

    # 1.3 4x Corner Standoff Pillars (Z = 2.02 .. 23.99 mm) + Male Centering Collars (Z = 23.99 .. 26.25 mm)
    inner_skin_trim_lo = skin_trim_2d.extrude(App.Vector(0.0, 0.0, h_lower))
    inner_skin_trim_lo.translate(App.Vector(0.0, 0.0, Z_BASE))
    for sx, sy in STANDOFFS:
        cyl = Part.makeCylinder(R_PILLAR, h_lower, App.Vector(sx, sy, Z_BASE), App.Vector(0, 0, 1))
        if sy > 0:
            bridge = Part.makeBox(2.0 * R_PILLAR, 9.50, h_lower, App.Vector(sx - R_PILLAR, sy, Z_BASE))
        else:
            bridge = Part.makeBox(2.0 * R_PILLAR, 9.50, h_lower, App.Vector(sx - R_PILLAR, sy - 9.50, Z_BASE))
        pillar = cyl.fuse(bridge).common(inner_skin_trim_lo)

        # Male concentric alignment collar with 45° top lead-in chamfer (4 perimeters thick!)
        h_collar_cyl = (Z_COLLAR_MALE_TOP - COLLAR_CHAMFER) - (Z_LOWER_TOP - 0.50)
        collar_cyl = Part.makeCylinder(
            R_COLLAR_MALE, h_collar_cyl,
            App.Vector(sx, sy, Z_LOWER_TOP - 0.50), App.Vector(0, 0, 1),
        )
        collar_chamf = Part.makeCone(
            R_COLLAR_MALE, R_COLLAR_MALE - COLLAR_CHAMFER, COLLAR_CHAMFER,
            App.Vector(sx, sy, Z_COLLAR_MALE_TOP - COLLAR_CHAMFER), App.Vector(0, 0, 1),
        )
        solid = solid.fuse(pillar).fuse(collar_cyl).fuse(collar_chamf)

    # 1.4 5x Segmented Internal Perimeter Alignment Tongues (with 45° support-free underside ramps!)
    #     Ramp rises from inner_2d_face at Z_RAMP_BOT (22.04) to tongue_inner_2d at Z_LOWER_TOP (23.99),
    #     then the straight tongue rises from Z_LOWER_TOP to Z_TONGUE_TOP (25.85) with 0.40 mm 45° top inner bevel!
    z_ramp_bot = Z_LOWER_TOP - (TONGUE_W + TONGUE_CLEAR_XY)  # 22.04 mm -> exact 45° print angle!
    ramp_ring = make_loft_ring_band(
        skin_trim_2d, inner_2d_face, z_ramp_bot,
        skin_trim_2d, tongue_inner_2d, Z_LOWER_TOP,
    )
    tongue_straight_h = (Z_TONGUE_TOP - 0.40) - (Z_LOWER_TOP - 0.05)
    tongue_ring_straight = tongue_band_2d.extrude(App.Vector(0.0, 0.0, tongue_straight_h))
    tongue_ring_straight.translate(App.Vector(0.0, 0.0, Z_LOWER_TOP - 0.05))
    tongue_top_inner_2d = outer_2d_face.Faces[0].makeOffset2D(-(T_WALL + TONGUE_CLEAR_XY + TONGUE_W - 0.40)).Faces[0]
    tongue_ring_chamf = make_loft_ring_band(
        tongue_outer_2d, tongue_inner_2d, Z_TONGUE_TOP - 0.40,
        tongue_outer_2d, tongue_top_inner_2d, Z_TONGUE_TOP,
    )
    tongue_mask = build_tongue_window_mask(z_ramp_bot - 0.50, Z_TONGUE_TOP + 0.50, pad_xy=0.0)
    tongues_solid = ramp_ring.fuse(tongue_ring_straight).fuse(tongue_ring_chamf).common(tongue_mask)
    solid = solid.fuse(tongues_solid)

    # 1.5 CoG-Balanced Level 1 Interior (Battery & XT60 Bay + Rear ToF/Riser Zone):
    # 1.5a Rear Battery-Bay Bulkhead Wall at X = -42.5 .. -40.5 mm with 45° support-free arched wireway!
    part1 = Part.makeBox(2.00, 58.00, Z_LOWER_TOP - 3.62, App.Vector(-42.50, -29.00, 3.62)).common(inner_tub)
    arch_pts = [
        App.Vector(-43.50, -12.00, 3.50),
        App.Vector(-43.50,  12.00, 3.50),
        App.Vector(-43.50,  12.00, 14.50),
        App.Vector(-43.50,   5.50, 21.00),
        App.Vector(-43.50,  -5.50, 21.00),
        App.Vector(-43.50, -12.00, 14.50),
    ]
    arch_face = Part.Face(Part.makePolygon(arch_pts + [arch_pts[0]]))
    part1_arch_cut = arch_face.extrude(App.Vector(4.00, 0.0, 0.0))
    solid = solid.fuse(part1.cut(part1_arch_cut))

    # 1.5b Support-Free 45° Corbelled LiPo Shoulder Retention Stop Ribs (X = -2.2 .. -0.6 mm):
    #      Anchored solidly to Lower's side floor ledges (|Y| >= 19.2 mm) & side walls so Lower is
    #      1 single manifold solid and prints 100% support-free, while positively blocking the 72 mm
    #      2S LiPo (Y in [-16.5, +16.5], X in [0, +72]) and leaving a 20 mm wide central lead archway!
    for sy_sign in (+1.0, -1.0):
        rib_pts = [
            App.Vector(-2.20, sy_sign * 29.00, 3.62),
            App.Vector(-2.20, sy_sign * 19.20, 3.62),
            App.Vector(-2.20, sy_sign * 19.20, 8.20),
            App.Vector(-2.20, sy_sign * 10.00, 17.40),
            App.Vector(-2.20, sy_sign * 10.00, Z_LOWER_TOP),
            App.Vector(-2.20, sy_sign * 29.00, Z_LOWER_TOP),
        ]
        rib_face = Part.Face(Part.makePolygon(rib_pts + [rib_pts[0]]))
        rib_solid = rib_face.extrude(App.Vector(1.60, 0.0, 0.0)).common(inner_tub)
        solid = solid.fuse(rib_solid)

    # 1.6 Floor Apertures through Bottom Sealing Plate (Battery Hatch + Rear ToF Cable Slot)
    bat_service_cut = make_rounded_rect_solid(-40.0, 76.0, -19.0, 19.0, 4.5, -0.50, 4.50)
    tof_ch = make_rounded_rect_solid(-67.5, -49.5, -10.0, -5.0, 1.5, -0.50, 4.50)
    solid = solid.cut(bat_service_cut).cut(tof_ch)

    # 1.7 Front & Rear Vertical Dovetail Bosses (Lower segment: Z = 2.02 .. 23.99 mm, pocket Z >= 6.00)
    f_boss = make_filleted_boss(84.00, 92.50, 14.00, 2.50, Z_BASE, Z_LOWER_TOP)
    r_boss = make_filleted_boss(-84.00, -92.50, 14.00, 2.50, Z_BASE, Z_LOWER_TOP)
    solid = solid.fuse(f_boss).fuse(r_boss)

    f_cut = make_dovetail_prism(92.50, 85.50, 14.00, 22.00, 6.00, Z_LOWER_TOP + 1.0, x_overshoot=2.0)
    r_cut = make_dovetail_prism(-92.50, -85.50, 14.00, 22.00, 6.00, Z_LOWER_TOP + 1.0, x_overshoot=-2.0)
    # 0.25 mm anti-snag relief step at seam top of Lower dovetail socket (Z = 23.74 .. 23.99 mm)
    f_chamf = make_dovetail_prism(92.50, 85.25, 14.50, 22.50, Z_LOWER_TOP - 0.25, Z_LOWER_TOP + 0.10, x_overshoot=2.0)
    r_chamf = make_dovetail_prism(-92.50, -85.25, 14.50, 22.50, Z_LOWER_TOP - 0.25, Z_LOWER_TOP + 0.10, x_overshoot=-2.0)
    solid = solid.cut(f_cut).cut(r_cut).cut(f_chamf).cut(r_chamf)

    # 1.8 External 0.35 mm 45° Bionic V-Shadow-Groove Bevel around Outer Hull Rim
    solid = solid.cut(bevel_cut_lower)

    # 1.9 Cut 4x Continuous Ø5.25 mm Through-Bores for M3 x 50 mm Metal Standoff Sleeves (LAST!)
    for sx, sy in STANDOFFS:
        bore = Part.makeCylinder(R_STANDOFF_BORE, 32.0, App.Vector(sx, sy, 0.0), App.Vector(0, 0, 1))
        solid = solid.cut(bore)

    solid = solid.removeSplitter()

    part_obj = doc.addObject("Part::Feature", "Chassis_Core_Lower")
    part_obj.Label = "Chassis Monocoque Core — Level 1 Lower Tub (v2)"
    part_obj.Shape = solid
    if hasattr(part_obj, "ViewObject") and part_obj.ViewObject is not None:
        part_obj.ViewObject.Visibility = True
        part_obj.ViewObject.ShapeColor = (0.20, 0.22, 0.25)
    doc.recompute()
    doc.saveAs(fcstd_path)

    if "--export" in sys.argv:
        solid.exportStep(f"{export_step_dir}/parts/chassis/chassis_core_lower.step")
        solid.exportStl(f"{export_stl_dir}/parts/chassis/chassis_core_lower.stl")

    vol_cm3 = solid.Volume / 1000.0
    print(f"✔ Saved Lower Core -> {fcstd_path} | Valid={solid.isValid()}, Solids={len(solid.Solids)}, Vol={vol_cm3:.1f} cm^3 ({vol_cm3*1.27:.1f} g solid)")
    App.closeDocument(doc_name)
    return solid, fcstd_path


# =============================================================================
# 2. Build Part 2: chassis_core_upper.FCStd (Level 2 — 100% Support-Free Electronics Tub)
# =============================================================================
def build_chassis_core_upper():
    doc_name = "chassis_core_upper"
    try:
        App.closeDocument(doc_name)
    except Exception:
        pass
    doc = App.newDocument(doc_name)
    fcstd_path = f"{models_dir}/chassis_core_upper.FCStd"

    h_upper = Z_TOP - Z_UPPER_BOT  # 29.27 mm

    # 2.1 Outer G1 Hull (Z = 24.01 .. 53.28 mm) + Open-Top Cavity above Intermediate Deck (Z >= 26.00)
    hull = outer_2d_face.extrude(App.Vector(0.0, 0.0, h_upper))
    hull.translate(App.Vector(0.0, 0.0, Z_UPPER_BOT))

    inner_tub = inner_2d_face.extrude(App.Vector(0.0, 0.0, Z_TOP - Z_DECK_TOP + 2.0))
    inner_tub.translate(App.Vector(0.0, 0.0, Z_DECK_TOP))
    solid = hull.cut(inner_tub)

    # 2.2 4x Corner Standoff Pillars (Z = 24.01 .. 53.28 mm) strictly inside inner skin
    inner_skin_trim_hi = skin_trim_2d.extrude(App.Vector(0.0, 0.0, h_upper))
    inner_skin_trim_hi.translate(App.Vector(0.0, 0.0, Z_UPPER_BOT))
    for sx, sy in STANDOFFS:
        cyl = Part.makeCylinder(R_PILLAR, h_upper, App.Vector(sx, sy, Z_UPPER_BOT), App.Vector(0, 0, 1))
        if sy > 0:
            bridge = Part.makeBox(2.0 * R_PILLAR, 9.50, h_upper, App.Vector(sx - R_PILLAR, sy, Z_UPPER_BOT))
        else:
            bridge = Part.makeBox(2.0 * R_PILLAR, 9.50, h_upper, App.Vector(sx - R_PILLAR, sy - 9.50, Z_UPPER_BOT))
        pillar = cyl.fuse(bridge).common(inner_skin_trim_hi)
        solid = solid.fuse(pillar)

    # 2.3 Pass-Through Wire Slots in Intermediate Deck (Z = 23.50 .. 26.50 mm)
    tof_slot = make_rounded_rect_solid(-19.0, -13.0, -23.0, -17.0, 1.5, Z_SPLIT - 0.50, Z_DECK_TOP + 0.50)
    pwr_mid_slot = make_rounded_rect_solid(-21.0, -15.0, 17.0, 23.0, 1.5, Z_SPLIT - 0.50, Z_DECK_TOP + 0.50)
    rear_pwr_slot = make_rounded_rect_solid(-81.0, -76.5, -9.0, 9.0, 1.8, Z_SPLIT - 0.50, Z_DECK_TOP + 0.50)
    solid = solid.cut(tof_slot).cut(pwr_mid_slot).cut(rear_pwr_slot)

    # 2.4 4x Organic Bionic Inter-Leg Bay Cable Ports (Z in [28.50, 40.00 mm]) + Micro-Zip-Tie Saddles
    dz_shift = Z_SPLIT - 24.00
    organic_ports = [
        ( 32.50, 34.25 + dz_shift, 14.00, 11.50, 4.50,  15.00,  45.00),  # Front-Bay Left
        (-32.50, 34.25 + dz_shift, 14.00, 11.50, 4.50,  15.00,  45.00),  # Rear-Bay Left
        ( 32.50, 34.25 + dz_shift, 14.00, 11.50, 4.50, -45.00, -15.00),  # Front-Bay Right
        (-32.50, 34.25 + dz_shift, 14.00, 11.50, 4.50, -45.00, -15.00),  # Rear-Bay Right
    ]
    for x_c, z_c, pw, ph, pr, y_min, y_max in organic_ports:
        p_solid = make_organic_port_cutter(x_c, z_c, pw, ph, pr, y_min, y_max)
        solid = solid.cut(p_solid)
        sign_y = 1.0 if y_min > 0 else -1.0
        ys = 27.0 * sign_y
        for x_sad in [x_c - 3.00, x_c + 3.00]:
            s_ch1 = Part.makeBox(1.30, 2.80, 8.0, App.Vector(x_sad - 1.50, ys - 1.40, Z_SPLIT))
            s_ch2 = Part.makeBox(1.30, 2.80, 8.0, App.Vector(x_sad + 1.50, ys - 1.40, Z_SPLIT))
            solid = solid.cut(s_ch1).cut(s_ch2)

    # 2.5 Integrated M2.5 PCB Screw Bosses on Intermediate Deck (Z = 26.00 .. 27.98 mm)
    boss_h = 1.98
    bosses = [
        # Front PCA9685 (center: 43.25, -3.00, pattern: 56.0 x 19.0)
        (43.25 + 28.00, -3.00 + 9.50),
        (43.25 + 28.00, -3.00 - 9.50),
        (43.25 - 28.00, -3.00 + 9.50),
        (43.25 - 28.00, -3.00 - 9.50),
        # Rear PCA9685 (center: -43.25, +3.00, pattern: 56.0 x 19.0)
        (-43.25 + 28.00, 3.00 + 9.50),
        (-43.25 + 28.00, 3.00 - 9.50),
        (-43.25 - 28.00, 3.00 + 9.50),
        (-43.25 - 28.00, 3.00 - 9.50),
        # Center Sensor Hub / TCA9548A (0.0, ±13.0)
        (0.00,  13.00),
        (0.00, -13.00),
    ]
    for bx, by in bosses:
        boss = Part.makeCylinder(2.60, boss_h, App.Vector(bx, by, Z_DECK_TOP), App.Vector(0, 0, 1))
        bore = Part.makeCylinder(1.025, DECK_THICKNESS + boss_h + 0.5, App.Vector(bx, by, Z_SPLIT), App.Vector(0, 0, 1))
        solid = solid.fuse(boss).cut(bore)

    # 2.6 Front & Rear Vertical Dovetail Sockets (Upper segment: Z = 24.01 .. 53.28 mm) + Cable Tunnels
    f_boss = make_filleted_boss(84.00, 92.50, 14.00, 2.50, Z_UPPER_BOT, Z_TOP)
    r_boss = make_filleted_boss(-84.00, -92.50, 14.00, 2.50, Z_UPPER_BOT, Z_TOP)
    solid = solid.fuse(f_boss).fuse(r_boss)

    f_cut = make_dovetail_prism(92.50, 85.50, 14.00, 22.00, Z_UPPER_BOT - 1.0, Z_TOP + 2.0, x_overshoot=2.0)
    r_cut = make_dovetail_prism(-92.50, -85.50, 14.00, 22.00, Z_UPPER_BOT - 1.0, Z_TOP + 2.0, x_overshoot=-2.0)
    f_chamf = make_dovetail_prism(92.50, 85.25, 14.50, 22.50, Z_UPPER_BOT - 0.10, Z_UPPER_BOT + 0.25, x_overshoot=2.0)
    r_chamf = make_dovetail_prism(-92.50, -85.25, 14.50, 22.50, Z_UPPER_BOT - 0.10, Z_UPPER_BOT + 0.25, x_overshoot=-2.0)
    solid = solid.cut(f_cut).cut(r_cut).cut(f_chamf).cut(r_chamf)

    cable_cut_front = Part.makeBox(20.00, 12.00, 8.00, App.Vector(80.00, -6.00, Z_DECK_TOP + 2.00))
    cable_cut_rear = Part.makeBox(20.00, 16.00, 10.00, App.Vector(-95.00, -8.00, Z_DECK_TOP + 1.00))
    solid = solid.cut(cable_cut_front).cut(cable_cut_rear)

    # 2.7 5x Through-Deck Female Alignment Tongue Notches (Z = 24.01 .. 26.05 mm -> 0.0 mm overhang!)
    #     Preserves full 1.60 mm outer hull wall; 0.15 mm slip-fit clearance on all sides of Lower tongues!
    notch_ring = notch_band_2d.extrude(App.Vector(0.0, 0.0, DECK_THICKNESS + 0.50))
    notch_ring.translate(App.Vector(0.0, 0.0, Z_SPLIT - 0.20))
    notch_mask = build_tongue_window_mask(Z_SPLIT - 0.50, Z_DECK_TOP + 0.60, pad_xy=TONGUE_CLEAR_XY)
    solid = solid.cut(notch_ring.common(notch_mask))

    # 2.8 External 0.35 mm 45° Bionic V-Shadow-Groove Bevel around Outer Hull Bottom Rim (prevents elephant-foot!)
    solid = solid.cut(bevel_cut_upper)

    # 2.9 4x Recessed Pillar Centering Sockets (Ø8.60 x 2.49 mm + support-free 45° conical roof)
    #     + Continuous Ø5.25 mm Standoff Through-Bores (LAST!)
    cone_h = R_COLLAR_FEMALE - R_STANDOFF_BORE  # 1.675 mm -> exact 45° support-free internal ceiling!
    for sx, sy in STANDOFFS:
        socket_cyl = Part.makeCylinder(
            R_COLLAR_FEMALE, Z_COLLAR_FEMALE_TOP - (Z_UPPER_BOT - 0.50),
            App.Vector(sx, sy, Z_UPPER_BOT - 0.50), App.Vector(0, 0, 1),
        )
        socket_roof = Part.makeCone(
            R_COLLAR_FEMALE, R_STANDOFF_BORE, cone_h,
            App.Vector(sx, sy, Z_COLLAR_FEMALE_TOP), App.Vector(0, 0, 1),
        )
        bore = Part.makeCylinder(
            R_STANDOFF_BORE, h_upper + 4.0,
            App.Vector(sx, sy, Z_UPPER_BOT - 1.0), App.Vector(0, 0, 1),
        )
        solid = solid.cut(socket_cyl).cut(socket_roof).cut(bore)

    solid = solid.removeSplitter()

    part_obj = doc.addObject("Part::Feature", "Chassis_Core_Upper")
    part_obj.Label = "Chassis Monocoque Core — Level 2 Upper Electronics Tub (v2)"
    part_obj.Shape = solid
    if hasattr(part_obj, "ViewObject") and part_obj.ViewObject is not None:
        part_obj.ViewObject.Visibility = True
        part_obj.ViewObject.ShapeColor = (0.24, 0.26, 0.30)
    doc.recompute()
    doc.saveAs(fcstd_path)

    if "--export" in sys.argv:
        solid.exportStep(f"{export_step_dir}/parts/chassis/chassis_core_upper.step")
        solid.exportStl(f"{export_stl_dir}/parts/chassis/chassis_core_upper.stl")

    vol_cm3 = solid.Volume / 1000.0
    print(f"✔ Saved Upper Core -> {fcstd_path} | Valid={solid.isValid()}, Solids={len(solid.Solids)}, Vol={vol_cm3:.1f} cm^3 ({vol_cm3*1.27:.1f} g solid)")
    App.closeDocument(doc_name)
    return solid, fcstd_path


lower_solid, fcstd_lower_path = build_chassis_core_lower()
upper_solid, fcstd_upper_path = build_chassis_core_upper()

# Verify direct Lower <-> Upper form-fit clearance (0.0000 mm^3 collision!)
lu_coll = lower_solid.common(upper_solid).Volume
print(f"  Lower <-> Upper Form-Fit Collision Check: {lu_coll:.4f} mm^3")
if lu_coll > 1e-4:
    raise RuntimeError(f"Lower <-> Upper overlap detected: {lu_coll:.4f} mm^3!")

# Export combined visual mesh for Three.js / Web-Dashboard & URDF compatibility
combined_visual = Part.makeCompound([lower_solid, upper_solid])
combined_visual.exportStl(f"{repo_root}/hardware/mechanics/export/urdf/meshes/chassis_core.stl")


# =============================================================================
# 3. Build Assembly: chassis_core_assembly.FCStd
# =============================================================================
doc_asm_name = "chassis_core_assembly"
try:
    App.closeDocument(doc_asm_name)
except Exception:
    pass
doc_asm = App.newDocument(doc_asm_name)
fcstd_asm_path = f"{asm_dir}/chassis_core_assembly.FCStd"
doc_asm.saveAs(fcstd_asm_path)

doc_lo = App.openDocument(fcstd_lower_path)
doc_hi = App.openDocument(fcstd_upper_path)
doc_st = App.openDocument(f"{cots_dir}/standoff_m3x50_round.FCStd")
doc_pca = App.openDocument(f"{cots_dir}/pca9685_board.FCStd")
doc_hub = App.openDocument(f"{models_dir}/sensor_hub_board.FCStd")
doc_tca = App.openDocument(f"{cots_dir}/tca9548a_board.FCStd")
doc_bat = App.openDocument(f"{cots_dir}/battery_lipo_2s.FCStd")

asm_part = doc_asm.addObject("App::Part", "Chassis_Core_Assembly")
asm_part.Label = "Lasius Segmented Monocoque Central Core Assembly (v2)"
for o in asm_part.Origin.OutList:
    if hasattr(o, "Visibility"):
        o.Visibility = False
asm_part.Origin.Visibility = False
asm_part.Visibility = True


def make_link(name, label, src_obj, placement, color=None, parent=asm_part):
    link = doc_asm.addObject("App::Link", name)
    link.Label = label
    link.setLink(src_obj)
    link.Placement = placement
    parent.addObject(link)
    link.Visibility = True
    if hasattr(link, "ViewObject") and link.ViewObject is not None:
        link.ViewObject.Visibility = True
        if color:
            link.ViewObject.OverrideMaterial = True
            mat = link.ViewObject.ShapeMaterial
            mat.DiffuseColor = color
            link.ViewObject.ShapeMaterial = mat
    return link


COLOR_CORE_LO = (0.20, 0.22, 0.25)  # Anthracite Level 1 Lower Tub
COLOR_CORE_HI = (0.25, 0.28, 0.32)  # Slate Grey Level 2 Upper Tub (subtle bionic contrast!)
COLOR_METAL   = (0.76, 0.78, 0.82)  # Anodized Aluminum M3x50 Standoff Sleeves
COLOR_BAT     = (0.85, 0.65, 0.10)  # Gold / Yellow 2S LiPo

# 1a. Monocoque Core Level 1 (Lower Battery & ToF Tub)
make_link("Chassis_Core_Lower", "1a. Monocoque Core Level 1 — Lower Battery Tub", doc_lo.Chassis_Core_Lower, App.Placement(), COLOR_CORE_LO)

# 1b. Monocoque Core Level 2 (Upper Electronics Tub)
make_link("Chassis_Core_Upper", "1b. Monocoque Core Level 2 — Upper Electronics Tub", doc_hi.Chassis_Core_Upper, App.Placement(), COLOR_CORE_HI)

# 1c. 4x COTS M3 x 50 mm Round Metal Standoff Sleeves (Z = 2.65 .. 52.65 mm, 0.65 mm CFRP preload margin)
st_grp = doc_asm.addObject("App::Part", "Core_Standoffs_M3x50")
st_grp.Label = "1c. 4x M3 x 50 mm Metal Tie-Rod Standoff Sleeves (COTS)"
for o in st_grp.Origin.OutList:
    if hasattr(o, "Visibility"):
        o.Visibility = False
st_grp.Origin.Visibility = False
st_grp.Visibility = True
asm_part.addObject(st_grp)

for tag, (sx, sy) in zip(["FL", "FR", "RL", "RR"], STANDOFFS):
    make_link(
        f"Standoff_M3x50_{tag}",
        f"M3x50 Round Standoff Sleeve {tag} (COTS)",
        doc_st.Standoff_M3x50_Round,
        App.Placement(App.Vector(sx, sy, 2.65), App.Rotation()),
        COLOR_METAL,
        parent=st_grp,
    )

# 2. Front PCA9685 Board at X = +43.25 mm, Y = -3.00 mm, Z = Z_DECK_TOP + 2.00 mm
z_pcb = Z_DECK_TOP + 2.00
p_pca_front = App.Placement(App.Vector(43.25, -3.00, z_pcb), App.Rotation(App.Vector(0, 0, 1), 0.0))
make_link("Board_PCA9685_Left", "2. PCA9685 Front (Horizontal, Pins +Y Left, Clamps UP)", doc_pca.PCA9685_Board, p_pca_front, None)

# 3. Rear PCA9685 Board at X = -43.25 mm, Y = +3.00 mm, Z = z_pcb
p_pca_rear = App.Placement(App.Vector(-43.25, 3.00, z_pcb), App.Rotation(App.Vector(0, 0, 1), 180.0))
make_link("Board_PCA9685_Right", "3. PCA9685 Rear (Horizontal, Pins -Y Right, Clamps UP)", doc_pca.PCA9685_Board, p_pca_rear, None)

# 4. Sensor Hub & 3.3V/GND Distribution Carrier Board seated on Intermediate Deck bosses
p_hub = App.Placement(App.Vector(0.0, 0.0, z_pcb), App.Rotation())
make_link("Board_Sensor_Hub", "4. Sensor Hub & 3.3V/GND Distribution Carrier Board", doc_hub.Sensor_Hub_Board, p_hub, None)

# 5. TCA9548A Multiplexer seated in Hub Female Sockets (elevated +7.00 mm above Hub)
r_tca = App.Rotation(App.Vector(0, 0, 1), 90.0)
p_tca = App.Placement(App.Vector(0.0, 0.0, z_pcb + 7.00), r_tca)
make_link("Board_TCA9548A", "5. TCA9548A I2C Multiplexer (Seated in Hub Sockets)", doc_tca.TCA9548A_Board, p_tca, None)

# 6. 2S LiPo Battery Pack positioned Forward-Center for CoG balance against rear Top-Deck UBECs
p_bat = App.Placement(App.Vector(36.00, 0.0, 3.75), App.Rotation())
make_link("Battery_LiPo_2S", "6. 2S 7.4V LiPo Battery Pack (CoG-Balanced Front-Center, Ovonic 72x33x18mm)", doc_bat.Battery_LiPo_2S, p_bat, COLOR_BAT)

doc_asm.recompute()
doc_asm.save()
print(f"✔ Saved Segmented Monocoque Assembly -> {fcstd_asm_path}")

# Verify 0.0000 mm^3 collisions across ALL components (Lower, Upper, 4x Standoffs, PCBs, LiPo)
mating_pairs = {("Board_Sensor_Hub", "Board_TCA9548A"), ("Board_TCA9548A", "Board_Sensor_Hub")}

items = [(o.Name, o.Shape) for o in asm_part.Group if hasattr(o, "Shape") and not o.Shape.isNull()]
max_coll = 0.0
for i in range(len(items)):
    for j in range(i + 1, len(items)):
        n1, s1 = items[i]
        n2, s2 = items[j]
        if (n1, n2) in mating_pairs:
            continue
        if s1.BoundBox.intersect(s2.BoundBox):
            v = s1.common(s2).Volume
            if v > 1e-4:
                print(f"  ❌ COLLISION {n1} <-> {n2}: {v:.4f} mm^3")
                max_coll = max(max_coll, v)
if max_coll <= 1e-4:
    print("  ✅ ZERO COLLISIONS in chassis_core_assembly.FCStd (0.0000 mm^3)!")

os._exit(0)
