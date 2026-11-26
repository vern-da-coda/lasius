#!/usr/bin/env python3
"""
Automated 2nd-Order Verification Finite Element Analysis (FEA) of Lasius v2:
  - Part A: Monolithic Bionic Coxa (`coxa.FCStd`, 54.2 g PETG, Dorsal Sickle Crest + 45° A-Truss Gusset)
  - Part B: Segmented 2-Level Monocoque Chassis Core (`chassis_core_lower.FCStd` + `chassis_core_upper.FCStd`)

Uses FreeCAD FEM + Gmsh (`C3D10` 2nd-order tets) + CalculiX (`ccx`) with the identical
PETG material baseline as Femur & Tibia/Tarsus FEA:
  - Material: PETG (E = 2100 MPa, nu = 0.38, rho = 1270 kg/m^3)
  - Isotropic Yield: Re = 45.0 MPa
  - Conservative FDM Interlayer Yield: Re_fdm = 30.0 MPa
"""

import json
import math
import os
import subprocess
import tempfile
import time

import FreeCAD as App
import Part
import Fem
import ObjectsFem
from femtools.ccxtools import CcxTools
import feminout.importCcxFrdResults as importCcxFrdResults

REPO_ROOT = "/home/bjoern/Workspace/Hexapods/lasius"
V2_PARTS = os.path.join(REPO_ROOT, "hardware/mechanics/models/custom/v2/parts")
WORK_DIR = os.path.join(REPO_ROOT, "hardware/mechanics/export/fea/coxa_chassis_v2")

RE_PETG = 45.0
RE_FDM = 30.0


def setup_petg(doc, analysis):
    mat = ObjectsFem.makeMaterialSolid(doc, "PETG_Material")
    md = mat.Material
    md["Name"] = "PETG"
    md["YoungsModulus"] = "2100 MPa"
    md["PoissonRatio"] = "0.38"
    md["Density"] = "1270 kg/m^3"
    mat.Material = md
    analysis.addObject(mat)
    return mat


def add_force_vec(doc, analysis, obj, faces, vec_n, name):
    mag = vec_n.Length
    if mag < 1e-6:
        return None
    unit = App.Vector(vec_n.x / mag, vec_n.y / mag, vec_n.z / mag)
    dir_obj = doc.addObject("Part::Feature", f"Dir_{name}")
    dir_obj.Shape = Part.makeLine(App.Vector(0.0, 0.0, 0.0), unit * 10.0)
    doc.recompute()

    f = ObjectsFem.makeConstraintForce(doc, name)
    f.References = [(obj, tuple(faces))]
    f.Force = App.Units.Quantity(f"{mag:.4f} N")
    f.Direction = (dir_obj, ["Edge1"])
    f.Reversed = False
    analysis.addObject(f)
    doc.recompute()
    if f.DirectionVector.dot(unit) < 0.0:
        f.Reversed = True
        doc.recompute()
    assert f.DirectionVector.dot(unit) > 0.999, (
        f"Direction mismatch for {name}: got {f.DirectionVector}, expected {unit}"
    )
    return f


def audit_cload_vector(inp_file, expected_total_vec):
    """Verify exact sum of CalculiX *CLOAD nodal forces (Fx, Fy, Fz) against expected vector."""
    sums = [0.0, 0.0, 0.0]
    in_cload = False
    with open(inp_file, "r") as fh:
        for line in fh:
            s = line.strip()
            if s.upper().startswith("*CLOAD"):
                in_cload = True
                continue
            if s.startswith("*") and not s.startswith("**"):
                in_cload = False
                continue
            if in_cload and s and not s.startswith("**"):
                parts = s.split(",")
                if len(parts) >= 3:
                    dof = int(parts[1])
                    val = float(parts[2])
                    if dof in (1, 2, 3):
                        sums[dof - 1] += val
    applied = App.Vector(sums[0], sums[1], sums[2])
    rel_err = (applied - expected_total_vec).Length / max(1.0, expected_total_vec.Length)
    ang_deg = math.degrees(applied.getAngle(expected_total_vec)) if applied.Length > 1e-6 else 180.0
    print(
        f"  [CLOAD Audit] Applied F=({sums[0]:+.2f}, {sums[1]:+.2f}, {sums[2]:+.2f}) N "
        f"vs Target ({expected_total_vec.x:+.2f}, {expected_total_vec.y:+.2f}, {expected_total_vec.z:+.2f}) N "
        f"(rel_err={rel_err*100:.2f}%, angle={ang_deg:.2f}°)"
    )
    assert rel_err < 0.10 and ang_deg < 2.0, f"CLOAD mismatch! Applied={sums}, Expected={expected_total_vec}"


def extract_stats(mesh_obj, res_obj):
    stresses = list(res_obj.vonMises)
    disps = list(res_obj.DisplacementLengths)
    node_ids = list(res_obj.NodeNumbers)
    assert len(stresses) > 0, "CalculiX produced no stress results!"
    nodes = mesh_obj.FemMesh.Nodes

    n = len(stresses)
    s_sorted = sorted(stresses)
    sigma_max = s_sorted[-1]
    sigma_p99 = s_sorted[int(0.99 * (n - 1))]
    sigma_p995 = s_sorted[int(0.995 * (n - 1))]
    sigma_mean = sum(stresses) / n
    u_max = max(disps)
    pct_under_5 = 100.0 * sum(1 for s in stresses if s < 5.0) / n

    idx_max = stresses.index(sigma_max)
    nid_max = node_ids[idx_max] if idx_max < len(node_ids) else None
    pt_max = nodes.get(nid_max, App.Vector(0, 0, 0))

    return {
        "nodes": mesh_obj.FemMesh.NodeCount,
        "tets": mesh_obj.FemMesh.VolumeCount,
        "sigma_max": round(sigma_max, 2),
        "sigma_p995": round(sigma_p995, 2),
        "sigma_p99": round(sigma_p99, 2),
        "sigma_mean": round(sigma_mean, 2),
        "pct_under_5mpa": round(pct_under_5, 1),
        "u_max": round(u_max, 4),
        "S_petg": round(RE_PETG / sigma_max, 2) if sigma_max > 0 else 999.0,
        "S_fdm": round(RE_FDM / sigma_max, 2) if sigma_max > 0 else 999.0,
        "S_p995_petg": round(RE_PETG / sigma_p995, 2) if sigma_p995 > 0 else 999.0,
        "hotspot_mm": [round(pt_max.x, 1), round(pt_max.y, 1), round(pt_max.z, 1)],
    }


def build_second_order_mesh(part_shape, max_el, min_el, alg2d="meshadapt", order=2, ho_opt=True):
    """Generate a high-accuracy tetrahedral FemMesh directly via Gmsh."""
    gmsh_bin = "/snap/freecad/2904/usr/bin/gmsh"
    if not os.path.exists(gmsh_bin):
        gmsh_bin = "gmsh"
    with tempfile.TemporaryDirectory(prefix="lasius_fea_") as td:
        brep_path = os.path.join(td, "part.brep")
        unv_path = os.path.join(td, "mesh.unv")
        part_shape.exportBrep(brep_path)
        t0 = time.time()
        attempts = [ho_opt, False] if (order == 2 and ho_opt) else [False]
        last_err = ""
        for use_ho in attempts:
            cmd = [
                gmsh_bin, brep_path, "-3", "-order", str(order),
                "-clmax", str(max_el), "-clmin", str(min_el),
                "-algo", alg2d,
            ]
            if order == 2 and use_ho:
                cmd += ["-setnumber", "Mesh.HighOrderOptimize", "2"]
            elif order == 2:
                # Straight-sided C3D10 guarantees positive Jacobians on tight thin-walled fillets
                cmd += ["-setnumber", "Mesh.SecondOrderLinear", "1"]
            cmd += ["-o", unv_path]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode == 0 and os.path.exists(unv_path):
                fm = Fem.read(unv_path)
                dt = time.time() - t0
                tag = "ho-opt" if use_ho else "linear-midnode"
                print(f"  Gmsh C3D{'10' if order==2 else '4'} ({alg2d}, {tag}, {min_el}..{max_el} mm): {fm.NodeCount} nodes, {fm.VolumeCount} tets in {dt:.2f}s")
                assert fm.VolumeCount > 0, "Gmsh produced 0 volume elements!"
                return fm
            last_err = "\n".join((r.stdout + "\n" + r.stderr).splitlines()[-20:])
        raise RuntimeError(f"Gmsh failed:\n{last_err}")


def solve_case(doc, analysis, fem_mesh, lc_dir, mesh_name, expected_force):
    mesh = doc.addObject("Fem::FemMeshObject", mesh_name)
    mesh.FemMesh = fem_mesh
    analysis.addObject(mesh)
    doc.recompute()

    solver = ObjectsFem.makeSolverCalculiXCcxTools(doc)
    analysis.addObject(solver)
    doc.recompute()

    fea = CcxTools(solver)
    fea.update_objects()
    fea.setup_working_dir(lc_dir)
    fea.setup_ccx()
    msg = fea.check_prerequisites()
    if msg:
        raise RuntimeError(f"FEA prerequisites error: {msg}")

    t1 = time.time()
    fea.write_inp_file()
    audit_cload_vector(os.path.join(lc_dir, f"{mesh_name}.inp"), expected_force)
    fea.ccx_run()
    print(f"  CalculiX solved in {time.time() - t1:.2f}s")

    frd_file = os.path.join(lc_dir, f"{mesh_name}.frd")
    res_obj = importCcxFrdResults.importFrd(frd_file, analysis, "CCX_")
    if not res_obj:
        raise RuntimeError(f"Failed to import {frd_file}")
    return mesh, res_obj


def run_coxa_fea():
    print("\n" + "=" * 88)
    print("=== PART A: FEA VERIFICATION OF MONOLITHIC BIONIC COXA v2 (SICKLE + 45° GUSSET) ===")
    print("=" * 88)
    doc_src = App.openDocument(os.path.join(V2_PARTS, "coxa/coxa.FCStd"))
    shape = doc_src.getObject("Coxa").Shape.copy()
    App.closeDocument(doc_src.Name)

    mass_g = shape.Volume * 1.27e-3
    print(f"Coxa Solid: Vol={shape.Volume:.1f} mm^3, Mass={mass_g:.2f} g (PETG)")

    chassis_fix_faces, femur_servo_faces, counter_bearing_faces = [], [], []
    for i, f in enumerate(shape.Faces):
        fn = f"Face{i+1}"
        c = f.CenterOfMass
        tid = f.Surface.TypeId
        if tid != "Part::GeomCylinder":
            continue
        r = f.Surface.Radius
        # 1. Fixed: Chassis lower pivot bore (74.7, 1.0, 9.0) + 4x Coxa servo holes (65.3/110.5, 22.9, 4/14)
        if abs(c.x - 74.7) < 1.5 and c.y < 4.5 and 1.5 <= r <= 4.3:
            chassis_fix_faces.append(fn)
        elif abs(r - 1.10) < 0.15 and c.x > 60.0 and abs(c.y - 22.9) < 2.0:
            chassis_fix_faces.append(fn)
        # 2. Load 1: 4x Femur servo mounting holes (4.7/53.1, 10.2/20.2, 7.8)
        elif abs(r - 1.10) < 0.15 and c.x < 56.0 and 8.0 <= c.y <= 22.0:
            femur_servo_faces.append(fn)
        # 3. Load 2: Option A inverted M4 counter-bearing bore (18.2, 15.3, -14.1)
        elif abs(r - 2.05) < 0.20 and abs(c.x - 18.2) < 1.5 and c.z < -12.0:
            counter_bearing_faces.append(fn)

    print(
        f"  Chassis fixed faces: {len(chassis_fix_faces)} | "
        f"Femur servo bores: {len(femur_servo_faces)} | Counter-bearing bore: {counter_bearing_faces}"
    )
    assert chassis_fix_faces and femur_servo_faces and counter_bearing_faces, "Failed to locate Coxa FEA faces!"

    coxa_mesh = build_second_order_mesh(shape, max_el=2.8, min_el=0.6, alg2d="meshadapt")

    load_cases = [
        (
            "COXA_LF1_Tripod20",
            "Tripod Gait 20 N Vertikal- + 8 N Radiallast (50/50 Servo + Gegenlager)",
            App.Vector(-4.0, +10.0, 0.0),
            App.Vector(-4.0, +10.0, 0.0),
        ),
        (
            "COXA_LF2_HipStall",
            "Hüft-Servo Blockierlast (50 N Resultierende auf Servoflansch & Gegenlager)",
            App.Vector(+25.0, +25.0, 0.0),
            App.Vector(-15.0, +15.0, 0.0),
        ),
        (
            "COXA_LF3_CounterBearingGusset",
            "Extrem-Gegenlagerlast (25 N Zug/Axial + 25 N Biegung rein auf 45°-Gusset)",
            App.Vector(0.0, 0.0, 0.0),
            App.Vector(0.0, +25.0, -25.0),
        ),
    ]

    results = []
    for lc_id, label, f_servo, f_cb in load_cases:
        print(f"\n>>> {lc_id}: {label}")
        lc_dir = os.path.join(WORK_DIR, lc_id)
        os.makedirs(lc_dir, exist_ok=True)
        doc = App.newDocument(f"FEA_{lc_id}")
        obj = doc.addObject("Part::Feature", "Coxa")
        obj.Shape = shape
        doc.recompute()

        analysis = ObjectsFem.makeAnalysis(doc, f"Analysis_{lc_id}")
        setup_petg(doc, analysis)

        c_fix = ObjectsFem.makeConstraintFixed(doc, "Chassis_Mount_Fixed")
        c_fix.References = [(obj, tuple(chassis_fix_faces))]
        analysis.addObject(c_fix)

        add_force_vec(doc, analysis, obj, femur_servo_faces, f_servo, "Femur_Servo_Force")
        add_force_vec(doc, analysis, obj, counter_bearing_faces, f_cb, "CounterBearing_Force")

        mesh, res = solve_case(doc, analysis, coxa_mesh, lc_dir, "Coxa_Gmsh", expected_force=f_servo + f_cb)
        stats = extract_stats(mesh, res)
        stats["id"] = lc_id
        stats["label"] = label
        stats["mass_g"] = round(mass_g, 2)
        results.append(stats)
        print(
            f"  -> sigma_max={stats['sigma_max']:.2f} MPa (P99.5={stats['sigma_p995']:.2f}), "
            f"u_max={stats['u_max']:.3f} mm, S_PETG={stats['S_petg']:.2f}, S_FDM={stats['S_fdm']:.2f}, "
            f"<5MPa={stats['pct_under_5mpa']:.1f}% @ {stats['hotspot_mm']}"
        )
        App.closeDocument(doc.Name)

    return results


def run_chassis_core_fea():
    print("\n" + "=" * 88)
    print("=== PART B: FEA VERIFICATION OF 2-LEVEL CHASSIS CORE (LOWER & UPPER) ===")
    print("=" * 88)
    results = {}

    # 1. Chassis Core Lower (57.45 g)
    doc_l = App.openDocument(os.path.join(V2_PARTS, "chassis/chassis_core_lower.FCStd"))
    sh_l = doc_l.getObject("Chassis_Core_Lower").Shape.copy()
    App.closeDocument(doc_l.Name)
    mass_l = sh_l.Volume * 1.27e-3
    print(f"\nChassis_Core_Lower: Vol={sh_l.Volume:.1f} mm^3, Mass={mass_l:.2f} g (PETG)")

    fix_l, floor_l, dove_l = [], [], []
    for i, f in enumerate(sh_l.Faces):
        fn = f"Face{i+1}"
        c = f.CenterOfMass
        tid = f.Surface.TypeId
        if tid == "Part::GeomCylinder" and abs(f.Surface.Radius - 2.625) < 0.05 and abs(abs(c.x) - 45.0) < 1.5 and abs(abs(c.y) - 30.0) < 1.5:
            fix_l.append(fn)
        elif tid == "Part::GeomPlane" and abs(c.z) < 0.25 and f.Area > 150.0:
            floor_l.append(fn)
        elif tid == "Part::GeomPlane" and abs(c.x) > 84.5 and 3.0 < c.z < 22.0 and f.Area > 30.0:
            dove_l.append(fn)

    print(f"  Lower fixed bores: {len(fix_l)} | Floor faces: {len(floor_l)} | Dovetail faces: {len(dove_l)}")
    assert len(fix_l) == 4 and floor_l and dove_l, "Failed to locate Chassis_Core_Lower FEA faces!"
    mesh_l = build_second_order_mesh(sh_l, max_el=3.2, min_el=0.8, alg2d="meshadapt")

    res_l = []
    for lc_id, label, target_faces, fvec in [
        ("CORE_LOWER_LF1_BellyImpact", "Bauchlandung / Stoß 40 N vertikal auf Bodenwanne", floor_l, App.Vector(0.0, 0.0, +40.0)),
        ("CORE_LOWER_LF2_DovetailLoad", "Front-Kopf + Heck-Gaster Auslegerlast 30 N auf Schwalbenschwänze", dove_l, App.Vector(0.0, 0.0, -30.0)),
    ]:
        print(f"\n>>> {lc_id}: {label}")
        lc_dir = os.path.join(WORK_DIR, lc_id)
        os.makedirs(lc_dir, exist_ok=True)
        doc = App.newDocument(f"FEA_{lc_id}")
        obj = doc.addObject("Part::Feature", "CoreLower")
        obj.Shape = sh_l
        doc.recompute()
        analysis = ObjectsFem.makeAnalysis(doc, f"Analysis_{lc_id}")
        setup_petg(doc, analysis)
        c_fix = ObjectsFem.makeConstraintFixed(doc, "Standoff_Bores_Fixed")
        c_fix.References = [(obj, tuple(fix_l))]
        analysis.addObject(c_fix)
        add_force_vec(doc, analysis, obj, target_faces, fvec, "CoreLower_Load")
        mesh, res = solve_case(doc, analysis, mesh_l, lc_dir, "CoreLower_Gmsh", expected_force=fvec)
        stats = extract_stats(mesh, res)
        stats.update({"id": lc_id, "label": label, "mass_g": round(mass_l, 2)})
        res_l.append(stats)
        print(
            f"  -> sigma_max={stats['sigma_max']:.2f} MPa (P99.5={stats['sigma_p995']:.2f}), "
            f"u_max={stats['u_max']:.3f} mm, S_PETG={stats['S_petg']:.2f}, S_FDM={stats['S_fdm']:.2f}, "
            f"<5MPa={stats['pct_under_5mpa']:.1f}% @ {stats['hotspot_mm']}"
        )
        App.closeDocument(doc.Name)
    results["chassis_core_lower"] = res_l

    # 2. Chassis Core Upper (65.25 g)
    results["chassis_core_upper"] = run_chassis_core_upper_fea()
    return results


def run_chassis_core_upper_fea():
    doc_u = App.openDocument(os.path.join(V2_PARTS, "chassis/chassis_core_upper.FCStd"))
    sh_u = doc_u.getObject("Chassis_Core_Upper").Shape.copy()
    App.closeDocument(doc_u.Name)
    mass_u = sh_u.Volume * 1.27e-3
    print(f"\nChassis_Core_Upper: Vol={sh_u.Volume:.1f} mm^3, Mass={mass_u:.2f} g (PETG)")

    fix_u, deck_u, dove_u = [], [], []
    for i, f in enumerate(sh_u.Faces):
        fn = f"Face{i+1}"
        c = f.CenterOfMass
        tid = f.Surface.TypeId
        if tid == "Part::GeomCylinder" and abs(f.Surface.Radius - 2.625) < 0.05 and abs(abs(c.x) - 45.0) < 1.5 and abs(abs(c.y) - 30.0) < 1.5:
            fix_u.append(fn)
        elif tid == "Part::GeomPlane" and abs(c.z - 26.0) < 0.20 and f.Area > 150.0:
            deck_u.append(fn)
        elif tid == "Part::GeomPlane" and abs(c.x) > 84.5 and 27.0 < c.z < 52.0 and f.Area > 30.0:
            dove_u.append(fn)

    print(f"  Upper fixed bores: {len(fix_u)} | Deck faces: {len(deck_u)} | Dovetail faces: {len(dove_u)}")
    assert len(fix_u) == 4 and deck_u and dove_u, "Failed to locate Chassis_Core_Upper FEA faces!"
    mesh_u = build_second_order_mesh(sh_u, max_el=3.2, min_el=0.8, alg2d="meshadapt")

    res_u = []
    for lc_id, label, target_faces, fvec in [
        ("CORE_UPPER_LF1_DeckPayload", "Zwischenboden Elektronik-Stoßlast 25 N vertikal (>10× Masse)", deck_u, App.Vector(0.0, 0.0, -25.0)),
        ("CORE_UPPER_LF2_DovetailShear", "Kopf-/Gaster-Schwalbenschwanz 30 N vertikal + 10 N Querlast", dove_u, App.Vector(0.0, +10.0, -30.0)),
    ]:
        print(f"\n>>> {lc_id}: {label}")
        lc_dir = os.path.join(WORK_DIR, lc_id)
        os.makedirs(lc_dir, exist_ok=True)
        doc = App.newDocument(f"FEA_{lc_id}")
        obj = doc.addObject("Part::Feature", "CoreUpper")
        obj.Shape = sh_u
        doc.recompute()
        analysis = ObjectsFem.makeAnalysis(doc, f"Analysis_{lc_id}")
        setup_petg(doc, analysis)
        c_fix = ObjectsFem.makeConstraintFixed(doc, "Standoff_Bores_Fixed")
        c_fix.References = [(obj, tuple(fix_u))]
        analysis.addObject(c_fix)
        add_force_vec(doc, analysis, obj, target_faces, fvec, "CoreUpper_Load")
        mesh, res = solve_case(doc, analysis, mesh_u, lc_dir, "CoreUpper_Gmsh", expected_force=fvec)
        stats = extract_stats(mesh, res)
        stats.update({"id": lc_id, "label": label, "mass_g": round(mass_u, 2)})
        res_u.append(stats)
        print(
            f"  -> sigma_max={stats['sigma_max']:.2f} MPa (P99.5={stats['sigma_p995']:.2f}), "
            f"u_max={stats['u_max']:.3f} mm, S_PETG={stats['S_petg']:.2f}, S_FDM={stats['S_fdm']:.2f}, "
            f"<5MPa={stats['pct_under_5mpa']:.1f}% @ {stats['hotspot_mm']}"
        )
        App.closeDocument(doc.Name)
    return res_u


def main():
    os.makedirs(WORK_DIR, exist_ok=True)
    out_json = os.path.join(WORK_DIR, "fea_summary.json")
    if "--only-upper" in sys.argv:
        summary = {}
        if os.path.exists(out_json):
            with open(out_json, "r") as f:
                summary = json.load(f)
        summary["chassis_core_upper"] = run_chassis_core_upper_fea()
    else:
        coxa_res = run_coxa_fea()
        core_res = run_chassis_core_fea()
        summary = {"coxa": coxa_res, **core_res}
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)
    print("\n" + "=" * 96)
    print("SUMMARY SAVED TO:", out_json)
    print("=" * 96)


import sys

_is_main = (__name__ == "__main__") or (
    len(sys.argv) > 1 and os.path.basename(sys.argv[1]) == os.path.basename(__file__)
)
if _is_main and not getattr(sys, "_fea_coxa_chassis_ran", False):
    sys._fea_coxa_chassis_ran = True
    main()
