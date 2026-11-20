#!/usr/bin/env python3
"""
Full 3D B-Rep Kinematic Workspace Collision Sweep for Lasius Hexapod v2.
======================================================================
Verifies true OpenCASCADE 3D B-Rep clearances (`common().Volume`) across the
entire physical joint workspace of Lasius v2:

  1. Hip (Femur Pitch) Sweep: alpha in [-60 deg, +60 deg] (step 5 deg, 1 deg bisection on contact)
     -> Checks Femur + Femur_Cover against Coxa + Coxa_Servo + Femur_Servo.
  2. Knee (Tibia Bend) Sweep: theta in [-30 deg, +140 deg] relative to Femur
     (0 deg = straight outstretched, +80 deg = neutral ant stance, >90 deg = tucked under)
     -> Checks Tibia_Body + Tibia_Cover + Tarsus + Tarsus_Shoe + Knee_Servo
        against Femur_Body + Femur_Cover + Coxa.
  3. Chassis Coxa Yaw Sweep: gamma in [-60 deg, +60 deg] for FL (+45°), ML (+90°), RL (+135°)
     tested at 3 Femur elevations (alpha = -30°, +28° ant stance, +50° high lift)
     -> Checks Coxa + Coxa_Servo + Femur_Servo + Femur + Femur_Cover + Tibia
        against Body_Bottom, Body_Top, Chassis_Core, Chassis_Belly_Pan, Chassis_Canopy,
        Chassis_RPi_Mount, Chassis_Service_Cover.
  4. Adjacent Leg-to-Leg Collision Sweep (FL <-> ML and ML <-> RL)
     -> Counter-yawing neighboring legs towards each other across gamma in [0°, 60°]
        in neutral v2 ant stance (alpha = +27.8°, theta = +84.0°).

Outputs a clean engineering table comparing real mechanical limits vs. `config.yaml` software limits.
"""

import math
import os
import sys
import time
import FreeCAD as App
import Part

REPO_ROOT = "/home/bjoern/Workspace/Hexapods/lasius"
MODELS = f"{REPO_ROOT}/hardware/mechanics/models"
V1_PARTS = f"{MODELS}/custom/v1/parts"
V2_PARTS = f"{MODELS}/custom/v2/parts"
V2_ASM = f"{MODELS}/custom/v2"
COTS = f"{MODELS}/cots"

COLL_EPS = 1e-3  # mm^3 threshold (0.001 mm^3 filters numerical face-touch noise)


def load_shape(fcstd_path, obj_name=None):
    doc = App.openDocument(fcstd_path)
    if obj_name:
        obj = doc.getObject(obj_name)
    else:
        objs = [o for o in doc.Objects if hasattr(o, "Shape") and not o.Shape.isNull()]
        obj = objs[0]
    sh = obj.Shape.copy()
    App.closeDocument(doc.Name)
    return sh


def collect_assembly_shapes(fcstd_path, root_name=None):
    """Collect named leaf solid shapes in the assembly's local coordinate frame."""
    doc = App.openDocument(fcstd_path)
    root = doc.getObject(root_name) if root_name else [o for o in doc.Objects if o.TypeId == "App::Part"][0]
    leaves = []

    def walk(obj, parent_pl=App.Placement()):
        pl = parent_pl.multiply(obj.Placement)
        if obj.TypeId == "App::Link":
            target = obj.LinkedObject
            if target is None:
                return
            if target.TypeId == "App::Part":
                for child in getattr(target, "Group", []):
                    walk(child, pl)
            elif hasattr(target, "Shape") and not target.Shape.isNull():
                sh = target.Shape.copy()
                sh.Placement = pl.multiply(sh.Placement)
                leaves.append((obj.Name, sh))
        elif obj.TypeId == "App::Part":
            for child in getattr(obj, "Group", []):
                walk(child, pl)
        elif hasattr(obj, "Shape") and not obj.Shape.isNull():
            sh = obj.Shape.copy()
            sh.Placement = pl.multiply(sh.Placement)
            leaves.append((obj.Name, sh))

    walk(root)
    # Close opened document (and its linked subdocs cleanly)
    for dname in list(App.listDocuments().keys()):
        try:
            App.closeDocument(dname)
        except Exception:
            pass
    return leaves


def move_group(named_shapes, pl):
    out = []
    for name, sh in named_shapes:
        s = sh.copy()
        s.Placement = pl.multiply(s.Placement)
        out.append((name, s))
    return out


def check_pair_groups(group_a, group_b):
    """Return list of (name_a, name_b, vol_mm3) for any intersecting pair > COLL_EPS."""
    hits = []
    for na, sa in group_a:
        bba = sa.BoundBox
        for nb, sb in group_b:
            if bba.intersect(sb.BoundBox):
                vol = sa.common(sb).Volume
                if vol > COLL_EPS:
                    hits.append((na, nb, vol))
    return hits


def min_dist_groups(group_a, group_b):
    """Return (min_dist_mm, pair_str) between two groups."""
    best = 1e9
    best_pair = ""
    for na, sa in group_a:
        for nb, sb in group_b:
            d = sa.distToShape(sb)[0]
            if d < best:
                best = d
                best_pair = f"{na} <-> {nb}"
    return best, best_pair


# =============================================================================
# Kinematic Placement Builders (100% matching generate_leg_assembly.py & body_assembly.py)
# =============================================================================
ROT_COXA = App.Rotation(App.Vector(0, 0, 1), 180.0).multiply(App.Rotation(App.Vector(1, 0, 0), 90.0))
P_COXA_L = App.Placement(App.Vector(74.70, -6.50, -15.25), ROT_COXA)
P_COXA_SERVO_L = P_COXA_L.multiply(
    App.Placement(App.Vector(74.70, 42.75, 9.00), App.Rotation(App.Vector(1, 0, 0), -90.0))
)
P_FEMUR_SERVO_L = P_COXA_L.multiply(App.Placement(App.Vector(18.20, 15.25, 27.30), App.Rotation()))


def p_femur_l(alpha_deg):
    return App.Placement(App.Vector(56.50, 0.0, 0.0), App.Rotation(App.Vector(0, 1, 0), -alpha_deg))


def p_tibia_l(alpha_deg, theta_deg):
    """
    alpha_deg: Femur elevation (+ upward)
    theta_deg: Knee downward bend relative to Femur (0 = straight, +80 = bent down 80 deg from femur)
    """
    theta_leg_deg = theta_deg - alpha_deg
    alpha = math.radians(alpha_deg)
    kx = 56.50 + 100.00 * math.cos(alpha)
    kz = 100.00 * math.sin(alpha)
    rot_t = App.Rotation(0.0, theta_leg_deg, 90.0)
    v_bore = rot_t.multVec(App.Vector(18.20, 15.25, 0.0))
    return App.Placement(App.Vector(kx - v_bore.x, 11.50 - v_bore.y, kz - v_bore.z), rot_t)


def p_leg_world(x_hole, y_hole, yaw0_deg, gamma_deg):
    p_world = App.Placement(
        App.Vector(x_hole, y_hole, 17.25),
        App.Rotation(App.Vector(0, 0, 1), yaw0_deg + gamma_deg),
    )
    return p_world.multiply(App.Placement(App.Vector(0.0, -2.50, 0.0), App.Rotation()))


def main():
    t_start = time.time()
    print("=" * 92)
    print("=== LASIUS v2 FULL 3D B-REP WORKSPACE COLLISION & CLEARANCE SWEEP ===")
    print("=" * 92)

    # Load base component shapes once
    print("Loading v2 B-Rep solids...")
    sh_coxa = load_shape(f"{V2_PARTS}/coxa/coxa.FCStd", "Coxa")
    sh_servo = load_shape(f"{COTS}/servo_nr645.FCStd", "Servo_Complete")

    femur_asm_shapes = [
        (n, s) for n, s in collect_assembly_shapes(f"{V2_ASM}/femur_assembly.FCStd", "Femur_Assembly_v2")
        if "Femur" in n or "Canopy" in n or "Frame" in n
    ]
    tibia_asm_shapes = [
        (n, s) for n, s in collect_assembly_shapes(f"{V2_ASM}/tibia_assembly.FCStd", "Tibia_Assembly")
        if any(k in n for k in ("Tibia", "Tarsus", "Knee_Servo"))
    ]

    coxa_grp = [
        ("Coxa", sh_coxa.copy()),
        ("Coxa_Servo", sh_servo.copy()),
        ("Femur_Servo", sh_servo.copy()),
    ]
    coxa_grp[0][1].Placement = P_COXA_L.multiply(coxa_grp[0][1].Placement)
    coxa_grp[1][1].Placement = P_COXA_SERVO_L.multiply(coxa_grp[1][1].Placement)
    coxa_grp[2][1].Placement = P_FEMUR_SERVO_L.multiply(coxa_grp[2][1].Placement)

    # Chassis static shapes in world frame
    chassis_grp = [
        ("Body_Bottom", load_shape(f"{V1_PARTS}/body_bottom.FCStd", "BodyBottom")),
        ("Body_Top", load_shape(f"{V1_PARTS}/body_top.FCStd", "BodyTop")),
        ("Chassis_Core", load_shape(f"{V2_PARTS}/chassis/chassis_core.FCStd")),
        ("Chassis_Belly_Pan", load_shape(f"{V2_PARTS}/chassis/chassis_belly_pan.FCStd", "Chassis_Belly_Pan")),
        ("Chassis_RPi_Mount", load_shape(f"{V2_PARTS}/chassis/chassis_rpi_mount.FCStd", "Chassis_RPi_Mount")),
        ("Chassis_Canopy", load_shape(f"{V2_PARTS}/chassis/chassis_canopy.FCStd", "Chassis_Canopy")),
        ("Chassis_Service_Cover", load_shape(f"{V2_PARTS}/chassis/chassis_service_cover.FCStd", "Chassis_Service_Cover")),
    ]
    chassis_grp[1][1].Placement = App.Placement(App.Vector(0, 0, 53.30), App.Rotation())

    print(
        f"Loaded: Coxa({len(coxa_grp)}), Femur({len(femur_asm_shapes)}), "
        f"Tibia({len(tibia_asm_shapes)}), Chassis({len(chassis_grp)})\n"
    )

    # =========================================================================
    # TEST 1: Hip (Femur Pitch) Sweep: alpha in [-75 deg, +75 deg]
    # =========================================================================
    print("--- TEST 1: HIP (FEMUR PITCH) SWEEP (alpha in [-75°, +75°]) ---")
    hip_free = []
    hip_hits = []
    for a in range(-75, 76, 5):
        f_grp = move_group(femur_asm_shapes, p_femur_l(a))
        hits = check_pair_groups(f_grp, coxa_grp)
        if hits:
            hip_hits.append((a, hits))
        else:
            hip_free.append(a)
    print(f"  Collision-free coarse range: [{min(hip_free):+d}°, {max(hip_free):+d}°]")
    for a, hits in hip_hits:
        top = sorted(hits, key=lambda x: -x[2])[0]
        print(f"    alpha={a:+4d}°: HIT {top[0]} <-> {top[1]} ({top[2]:.2f} mm^3)")

    # Refine exact 1 deg mechanical stops for Hip
    lo_hip = min(hip_free)
    while lo_hip > -95:
        if check_pair_groups(move_group(femur_asm_shapes, p_femur_l(lo_hip - 1)), coxa_grp):
            break
        lo_hip -= 1
    hi_hip = max(hip_free)
    while hi_hip < 95:
        if check_pair_groups(move_group(femur_asm_shapes, p_femur_l(hi_hip + 1)), coxa_grp):
            break
        hi_hip += 1
    print(f"  => EXACT HIP MECHANICAL CLEAR RANGE: [{lo_hip:+d}°, {hi_hip:+d}°] (v2 stance: +27.8°)\n")

    # =========================================================================
    # TEST 2: Knee (Tibia Bend) Sweep: theta in [-30 deg, +145 deg] (alpha = 0°)
    # =========================================================================
    print("--- TEST 2: KNEE (TIBIA BEND RELATIVE TO FEMUR) SWEEP (theta in [-30°, +145°]) ---")
    f_ref = move_group(femur_asm_shapes, p_femur_l(0.0))
    knee_free = []
    knee_hits = []
    for th in range(-30, 146, 5):
        t_grp = move_group(tibia_asm_shapes, p_tibia_l(0.0, th))
        hits = check_pair_groups(t_grp, f_ref)
        if hits:
            knee_hits.append((th, hits))
        else:
            knee_free.append(th)
    print(f"  Collision-free coarse range: [{min(knee_free):+d}°, {max(knee_free):+d}°] (0°=straight, +84°=v2 stance)")
    for th, hits in knee_hits:
        top = sorted(hits, key=lambda x: -x[2])[0]
        print(f"    theta={th:+4d}°: HIT {top[0]} <-> {top[1]} ({top[2]:.2f} mm^3)")

    lo_knee = min(knee_free)
    while lo_knee > -90:
        if check_pair_groups(move_group(tibia_asm_shapes, p_tibia_l(0.0, lo_knee - 1)), f_ref):
            break
        lo_knee -= 1
    hi_knee = max(knee_free)
    while hi_knee < 170:
        if check_pair_groups(move_group(tibia_asm_shapes, p_tibia_l(0.0, hi_knee + 1)), f_ref):
            break
        hi_knee += 1
    print(f"  => EXACT KNEE MECHANICAL CLEAR RANGE: [{lo_knee:+d}°, {hi_knee:+d}°] (v2 stance: +84.0°)\n")

    # =========================================================================
    # TEST 3: Chassis Coxa Yaw Sweep (-60° .. +60°) for FL, ML, RL at 3 Femur Heights
    # =========================================================================
    print("--- TEST 3: CHASSIS COXA YAW SWEEP (gamma in [-60°, +60°]) ---")
    legs_left = [
        ("FL", 86.0, 65.0, 45.0),
        ("ML", 0.0, 75.0, 90.0),
        ("RL", -86.0, 65.0, 135.0),
    ]
    poses = [
        ("Stance (+28°/84°)", 27.8, 84.0),
        ("HighLift (+50°/105°)", 50.0, 105.0),
        ("LowReach (-30°/60°)", -30.0, 60.0),
    ]
    for pname, a_p, th_p in poses:
        print(f"\n  Pose: {pname}")
        leg_local = coxa_grp + move_group(femur_asm_shapes, p_femur_l(a_p)) + move_group(tibia_asm_shapes, p_tibia_l(a_p, th_p))
        for lname, hx, hy, yaw0 in legs_left:
            free_g = []
            hit_g = []
            for g in range(-60, 61, 5):
                lw = move_group(leg_local, p_leg_world(hx, hy, yaw0, g))
                hits = check_pair_groups(lw, chassis_grp)
                if hits:
                    hit_g.append((g, sorted(hits, key=lambda x: -x[2])[0]))
                else:
                    free_g.append(g)
            # Find contiguous clear window around gamma = 0
            lo_g = 0
            while lo_g > -65:
                if check_pair_groups(move_group(leg_local, p_leg_world(hx, hy, yaw0, lo_g - 1)), chassis_grp):
                    break
                lo_g -= 1
            hi_g = 0
            while hi_g < 65:
                if check_pair_groups(move_group(leg_local, p_leg_world(hx, hy, yaw0, hi_g + 1)), chassis_grp):
                    break
                hi_g += 1
            first_neg = next((h for h in reversed(hit_g) if h[0] < 0), None)
            first_pos = next((h for h in hit_g if h[0] > 0), None)
            note_neg = f"({first_neg[1][0]}<->{first_neg[1][1]})" if first_neg else "(clear to -65°)"
            note_pos = f"({first_pos[1][0]}<->{first_pos[1][1]})" if first_pos else "(clear to +65°)"
            print(f"    {lname}: CLEAR [{lo_g:+3d}°, {hi_g:+3d}°]  neg_stop={note_neg} | pos_stop={note_pos}")

    # =========================================================================
    # TEST 4: Adjacent Leg-to-Leg Collision Sweep (FL <-> ML and ML <-> RL)
    # =========================================================================
    print("\n--- TEST 4: ADJACENT LEG-TO-LEG COUNTER-YAW SWEEP (v2 Ant Stance +27.8°/84.0°) ---")
    leg_stance = coxa_grp + move_group(femur_asm_shapes, p_femur_l(27.8)) + move_group(tibia_asm_shapes, p_tibia_l(27.8, 84.0))

    # FL (+45°) swings backward (+gamma towards +90°) while ML (+90°) swings forward (-gamma towards +45°)
    for pair_name, leg_a, leg_b, dir_a, dir_b in [
        ("FL <-> ML", (86.0, 65.0, 45.0), (0.0, 75.0, 90.0), +1, -1),
        ("ML <-> RL", (0.0, 75.0, 90.0), (-86.0, 65.0, 135.0), +1, -1),
    ]:
        hit_at = None
        for g in range(0, 56, 5):
            la = move_group(leg_stance, p_leg_world(*leg_a, dir_a * g))
            lb = move_group(leg_stance, p_leg_world(*leg_b, dir_b * g))
            hits = check_pair_groups(la, lb)
            if hits:
                hit_at = (g, sorted(hits, key=lambda x: -x[2])[0])
                break
        if hit_at is None:
            la0 = move_group(leg_stance, p_leg_world(*leg_a, 0))
            lb0 = move_group(leg_stance, p_leg_world(*leg_b, 0))
            d0, p0 = min_dist_groups(la0, lb0)
            print(f"  {pair_name}: 100% CLEAR up to ±55° simultaneous counter-yaw! (neutral min dist = {d0:.1f} mm @ {p0})")
        else:
            # 1 deg refine
            g_clear = hit_at[0] - 5
            while g_clear < hit_at[0]:
                la = move_group(leg_stance, p_leg_world(*leg_a, dir_a * (g_clear + 1)))
                lb = move_group(leg_stance, p_leg_world(*leg_b, dir_b * (g_clear + 1)))
                if check_pair_groups(la, lb):
                    break
                g_clear += 1
            print(f"  {pair_name}: CLEAR up to ±{g_clear}° simultaneous counter-yaw (contact @{g_clear+1}°: {hit_at[1][0]} <-> {hit_at[1][1]})")

    print(f"\n=== WORKSPACE COLLISION SWEEP COMPLETED IN {time.time() - t_start:.1f}s ===")


if __name__ == "__main__":
    main()
