#!/usr/bin/env python3
"""
Automated Verification Finite Element Analysis (FEA) of Lasius v2 Tibia & Reinforced Tarsus.
Uses FreeCAD FEM + Gmsh + CalculiX (ccx) with identical PETG material baseline as Femur FEA:
  - Material: PETG (E = 2100 MPa, nu = 0.38, rho = 1270 kg/m^3)
  - Isotropic Yield: Re = 45.0 MPa (matching Femur FEA baseline)
  - Conservative FDM Interlayer Yield: Re_fdm = 30.0 MPa

Part A — Reinforced Bionic Tarsus (`tarsus.FCStd`, +20% shin profile):
  Boundary conditions (statically determinate 2-support rocker at +5 deg hard-stop):
    - Pivot Bore (0, 0): Fixed X, Y, Z (Ø3.0 mm steel dowel pin)
    - Internal Hard-Stop Face (Y = -4.20, X in [-44, -10.5]): Fixed Y (frictionless contact on Tibia hard-stop)
  Load cases applied at Kufe shoe lock bore (X = +56.2, Y = +3.6):
    1. TARSUS_LF1: Tripod Gait 56 deg Ant Stance Impact (F = 20.0 N, k_dyn = 2.0 -> Fx = -16.58 N, Fy = +11.18 N)
    2. TARSUS_LF2: Severe Transverse Overload Shock (Fy = +35.0 N pure bending, ~4.5x knee stall force!)
    3. TARSUS_LF3: Lateral Slope / Turning Side Load (Fz = +12.0 N transverse across 5.60 mm thickness)

Part B — Monolithic Bionic Tibia v2 (`tibia.FCStd`, SVG teardrop window & 2-screw bayonet cover):
  Boundary conditions (Knee Servo Cage fixed):
    - 4x M2.5 Servo Mounting Bores + Servo Ear Pads + Knee Counter-Bearing M4 Bore/Nut Seat
  Load cases with TRUE internal lever force amplification (r_foot / r_stop ~ 56.2 / 20.7 = 2.71x!):
    1. TIBIA_LF1: Tripod Gait 56 deg Impact (F_foot = 20 N -> F_piv = (-16.6, +41.5, 0) N, F_stop = (0, -30.3, 0) N)
    2. TIBIA_LF2: Knee Servo Stall Torque M = 1.2 N*m (F_foot = 7.9 N pure bend -> F_piv = +29.3 N, F_stop = -21.4 N)
    3. TIBIA_LF3: Severe Impact Overload (F_foot = 25.0 N pure bend -> F_piv = +92.8 N, F_stop = -67.8 N)
    4. TIBIA_LF4: Lateral Slope Traction (Fz = +12.0 N transverse at distal pivot fork)
"""

import json
import math
import os
import subprocess
import sys
import tempfile
import time

import FreeCAD as App
import Part
import Fem
import ObjectsFem
from femmesh.gmshtools import GmshTools
from femtools.ccxtools import CcxTools
import feminout.importCcxFrdResults as importCcxFrdResults

REPO_ROOT = "/home/bjoern/Workspace/Hexapods/lasius"
V2_PARTS = os.path.join(REPO_ROOT, "hardware/mechanics/models/custom/v2/parts")
WORK_DIR = os.path.join(REPO_ROOT, "hardware/mechanics/export/fea/tibia_tarsus_v2")

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
    # Create an explicit reference edge so FreeCAD FEM writes the EXACT 3D direction vector to *CLOAD!
    # (Assigning ConstraintForce.DirectionVector directly is overwritten by FreeCAD on recompute!)
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
    # Verify FreeCAD resolved the direction correctly (flip Reversed if sign inverted)
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
    assert rel_err < 0.05 and ang_deg < 2.0, f"CLOAD mismatch! Applied={sums}, Expected={expected_total_vec}"


def extract_stats(mesh_obj, res_obj):
    stresses = list(res_obj.vonMises)
    disps = list(res_obj.DisplacementLengths)
    node_ids = list(res_obj.NodeNumbers)
    assert len(stresses) > 0, "CalculiX produced no stress results (check solver stderr/Jacobians)!"
    nodes = mesh_obj.FemMesh.Nodes

    n = len(stresses)
    s_sorted = sorted(stresses)
    sigma_max = s_sorted[-1] if n else 0.0
    sigma_p99 = s_sorted[int(0.99 * (n - 1))] if n else 0.0
    sigma_p995 = s_sorted[int(0.995 * (n - 1))] if n else 0.0
    sigma_mean = sum(stresses) / n if n else 0.0
    u_max = max(disps) if disps else 0.0

    # Hotspot location
    idx_max = stresses.index(sigma_max) if n else 0
    nid_max = node_ids[idx_max] if idx_max < len(node_ids) else None
    pt_max = nodes.get(nid_max, App.Vector(0, 0, 0))

    # Top stress excluding immediate 3.5 mm neighborhood of tiny singular boundary edges if needed
    return {
        "nodes": mesh_obj.FemMesh.NodeCount,
        "tets": mesh_obj.FemMesh.VolumeCount,
        "sigma_max": round(sigma_max, 2),
        "sigma_p995": round(sigma_p995, 2),
        "sigma_p99": round(sigma_p99, 2),
        "sigma_mean": round(sigma_mean, 2),
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
        cmd = [
            gmsh_bin, brep_path, "-3", "-order", str(order),
            "-clmax", str(max_el), "-clmin", str(min_el),
            "-algo", alg2d, "-optimize",
        ]
        if order == 2 and ho_opt:
            cmd += ["-setnumber", "Mesh.HighOrderOptimize", "2"]
        cmd += ["-o", unv_path]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(unv_path):
            tail = "\n".join((r.stdout + "\n" + r.stderr).splitlines()[-20:])
            raise RuntimeError(f"Gmsh failed (rc={r.returncode}):\n{tail}")
        fm = Fem.read(unv_path)
        dt = time.time() - t0
        print(f"  Gmsh C3D{'10' if order==2 else '4'} ({alg2d}, {min_el}..{max_el} mm): {fm.NodeCount} nodes, {fm.VolumeCount} tets in {dt:.2f}s")
        assert fm.VolumeCount > 0, "Gmsh produced 0 volume elements!"
        return fm


def solve_case(doc, analysis, part_obj, fem_mesh, lc_dir, mesh_name, expected_force):
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


def run_tarsus_fea():
    print("\n" + "=" * 88)
    print("=== PART A: FEA VERIFICATION OF REINFORCED BIONIC TARSUS v2 (+20% SHIN) ===")
    print("=" * 88)
    doc_src = App.openDocument(os.path.join(V2_PARTS, "tarsus/tarsus.FCStd"))
    shape = doc_src.getObject("Tarsus").Shape.copy()
    App.closeDocument(doc_src.Name)

    mass_g = shape.Volume * 1.27e-3
    print(f"Tarsus Solid: Vol={shape.Volume:.1f} mm^3, Mass={mass_g:.2f} g (PETG)")

    # Geometrically identify constraint & load faces
    piv_faces, stop_faces, load_faces = [], [], []
    for i, f in enumerate(shape.Faces):
        fn = f"Face{i+1}"
        c = f.CenterOfMass
        bb = f.BoundBox
        tid = f.Surface.TypeId
        if tid == "Part::GeomCylinder" and abs(c.x) < 1.0 and abs(c.y) < 1.0:
            piv_faces.append(fn)
        elif tid == "Part::GeomPlane" and abs(c.y + 4.20) < 0.15 and bb.XMin < -40.0 and bb.XMax > -12.0:
            stop_faces.append(fn)
        elif tid == "Part::GeomCylinder" and abs(c.x - 56.2) < 1.0 and abs(c.y - 3.6) < 1.0:
            load_faces.append(fn)

    print(f"  Pivot bore faces: {piv_faces} | Hard-stop face: {stop_faces} | Foot load bore: {load_faces}")
    assert piv_faces and stop_faces and load_faces, "Failed to identify Tarsus FEA faces!"

    load_cases = [
        ("TARSUS_LF1_Tripod56", "Tripod 56° Aufsetzlast (20 N, k_dyn=2.0)", App.Vector(-16.58, +11.18, 0.0)),
        ("TARSUS_LF2_Overload35", "Extremstoß quer am Fuß (35 N, 4.5× Stall)", App.Vector(0.0, +35.0, 0.0)),
        ("TARSUS_LF3_Lateral12", "Laterale Hangquerung (12 N quer in Z)", App.Vector(0.0, 0.0, +12.0)),
    ]

    # Build one reusable 2nd-order C3D10 mesh for all Tarsus load cases
    tarsus_fem_mesh = build_second_order_mesh(shape, max_el=1.6, min_el=0.4, alg2d="meshadapt")

    results = []
    for lc_id, label, fvec in load_cases:
        print(f"\n>>> {lc_id}: {label} | F=({fvec.x:+.2f}, {fvec.y:+.2f}, {fvec.z:+.2f}) N")
        lc_dir = os.path.join(WORK_DIR, lc_id)
        os.makedirs(lc_dir, exist_ok=True)
        doc = App.newDocument(f"FEA_{lc_id}")
        obj = doc.addObject("Part::Feature", "Tarsus")
        obj.Shape = shape
        doc.recompute()

        analysis = ObjectsFem.makeAnalysis(doc, f"Analysis_{lc_id}")
        setup_petg(doc, analysis)

        # Pivot dowel pin bore fixed
        c_piv = ObjectsFem.makeConstraintFixed(doc, "Pivot_Fixed")
        c_piv.References = [(obj, tuple(piv_faces))]
        analysis.addObject(c_piv)

        # Hard-stop face: frictionless Y-only support (realistic rocker contact at +5 deg stop!)
        c_stop = ObjectsFem.makeConstraintDisplacement(doc, "HardStop_Y_Support")
        c_stop.References = [(obj, tuple(stop_faces))]
        c_stop.xFree = True
        c_stop.yFree = False
        c_stop.yDisplacement = "0 mm"
        c_stop.zFree = True
        analysis.addObject(c_stop)

        add_force_vec(doc, analysis, obj, load_faces, fvec, "Foot_Force")

        mesh, res = solve_case(doc, analysis, obj, tarsus_fem_mesh, lc_dir, "Tarsus_Gmsh", expected_force=fvec)
        stats = extract_stats(mesh, res)
        stats["id"] = lc_id
        stats["label"] = label
        results.append(stats)
        print(
            f"  -> sigma_max={stats['sigma_max']:.2f} MPa (P99.5={stats['sigma_p995']:.2f}), "
            f"u_max={stats['u_max']:.3f} mm, S_PETG={stats['S_petg']:.2f}, S_FDM={stats['S_fdm']:.2f} "
            f"@ {stats['hotspot_mm']}"
        )
        doc.saveAs(os.path.join(lc_dir, f"{lc_id}_results.FCStd"))
        App.closeDocument(doc.Name)

    return results


def run_tibia_fea():
    print("\n" + "=" * 88)
    print("=== PART B: FEA VERIFICATION OF MONOLITHIC BIONIC TIBIA v2 (TEARDROP + BAYONET) ===")
    print("=" * 88)
    doc_src = App.openDocument(os.path.join(V2_PARTS, "tibia/tibia.FCStd"))
    shape = doc_src.getObject("Tibia_Body").Shape.copy()
    App.closeDocument(doc_src.Name)

    mass_g = shape.Volume * 1.27e-3
    print(f"Tibia_Body Solid: Vol={shape.Volume:.1f} mm^3, Mass={mass_g:.2f} g (PETG)")

    # Geometrically identify Knee fixed faces, Pivot bore, and +5 deg Hard-Stop plane
    knee_fix_faces, piv_faces, stop_faces = [], [], []
    for i, f in enumerate(shape.Faces):
        fn = f"Face{i+1}"
        c = f.CenterOfMass
        bb = f.BoundBox
        tid = f.Surface.TypeId
        # 4x NR-645 mounting holes + ear clamping pads + counter-bearing nut pocket faces at (18.2, 15.25, Z>=29)
        is_sm = (
            tid == "Part::GeomCylinder"
            and (abs(c.x - 4.65) < 1.0 or abs(c.x - 53.15) < 1.0)
            and (abs(c.y - 10.25) < 1.0 or abs(c.y - 20.25) < 1.0)
        )
        is_ear = (
            tid == "Part::GeomPlane"
            and ((0 <= c.x <= 10) or (49 <= c.x <= 59))
            and 5 <= c.y <= 26
            and (abs(c.z - 2.75) < 0.2 or abs(c.z - 15.25) < 0.2)
        )
        is_knee_nut = (
            abs(c.x - 18.20) < 4.5 and abs(c.y - 15.25) < 4.5 and bb.ZMin >= 29.0 and bb.ZMax <= 32.6
        )
        is_piv = (tid == "Part::GeomCylinder" and abs(c.x - 109.0) < 2.0 and abs(c.y - 20.5) < 2.0)
        is_stop = (
            tid == "Part::GeomPlane"
            and 76.0 < c.x < 100.0
            and 13.0 < c.y < 16.5
            and 5.5 < c.z < 12.5
            and f.Area > 40.0
        )
        if is_sm or is_ear or is_knee_nut:
            knee_fix_faces.append(fn)
        elif is_piv:
            piv_faces.append(fn)
        elif is_stop:
            stop_faces.append(fn)

    print(
        f"  Knee fixed faces: {len(knee_fix_faces)} | Pivot bore: {piv_faces} | Hard-stop plane: {stop_faces}"
    )
    assert knee_fix_faces and piv_faces and stop_faces, "Failed to identify Tibia FEA faces!"

    # True internal lever amplification: foot load at r_foot = 56.2 mm vs hard-stop CoM at r_stop = 20.7 mm -> 2.715x!
    # For foot force (Fx, Fy, Fz):
    #   F_stop_y = -Fy * (56.2 / 20.7) = -2.715 * Fy  (pushes DOWN onto Tibia +5 deg hard-stop!)
    #   F_piv_y  = +Fy * (1 + 2.715)   = +3.715 * Fy  (pulls UP on Pivot pin!)
    k_amp = 56.2 / 20.7
    load_cases = [
        (
            "TIBIA_LF1_Tripod56",
            "Tripod 56° Aufsetzlast (20 N am Fuß, echte Hebelkraft)",
            App.Vector(-16.58, +11.18 * (1.0 + k_amp), 0.0),
            App.Vector(0.0, -11.18 * k_amp, 0.0),
        ),
        (
            "TIBIA_LF2_KneeStall",
            "Knie-Servo Blockiermoment 1.2 N·m (7.9 N am Fuß)",
            App.Vector(0.0, +7.86 * (1.0 + k_amp), 0.0),
            App.Vector(0.0, -7.86 * k_amp, 0.0),
        ),
        (
            "TIBIA_LF3_Impact25",
            "Extremstoß quer am Fuß (25 N = 3.2× Stall, Hebelkraft)",
            App.Vector(0.0, +25.0 * (1.0 + k_amp), 0.0),
            App.Vector(0.0, -25.0 * k_amp, 0.0),
        ),
        (
            "TIBIA_LF4_Lateral12",
            "Laterale Hangquerung (12 N quer in Z am Gabelkopf)",
            App.Vector(0.0, 0.0, +12.0),
            App.Vector(0.0, 0.0, 0.0),
        ),
    ]

    # Build one reusable 2nd-order C3D10 mesh for all Tibia load cases
    tibia_fem_mesh = build_second_order_mesh(shape, max_el=2.2, min_el=0.35, alg2d="meshadapt")

    results = []
    for lc_id, label, f_piv, f_stop in load_cases:
        print(
            f"\n>>> {lc_id}: {label}\n"
            f"    F_piv=({f_piv.x:+.1f}, {f_piv.y:+.1f}, {f_piv.z:+.1f}) N | "
            f"F_stop=({f_stop.x:+.1f}, {f_stop.y:+.1f}, {f_stop.z:+.1f}) N"
        )
        lc_dir = os.path.join(WORK_DIR, lc_id)
        os.makedirs(lc_dir, exist_ok=True)
        doc = App.newDocument(f"FEA_{lc_id}")
        obj = doc.addObject("Part::Feature", "Tibia")
        obj.Shape = shape
        doc.recompute()

        analysis = ObjectsFem.makeAnalysis(doc, f"Analysis_{lc_id}")
        setup_petg(doc, analysis)

        c_fix = ObjectsFem.makeConstraintFixed(doc, "Knee_Cage_Fixed")
        c_fix.References = [(obj, tuple(knee_fix_faces))]
        analysis.addObject(c_fix)

        add_force_vec(doc, analysis, obj, piv_faces, f_piv, "Pivot_Pin_Force")
        add_force_vec(doc, analysis, obj, stop_faces, f_stop, "HardStop_Force")

        mesh, res = solve_case(
            doc, analysis, obj, tibia_fem_mesh, lc_dir, "Tibia_Gmsh",
            expected_force=f_piv + f_stop
        )
        stats = extract_stats(mesh, res)

        # Also extract peak stress specifically around the extended Claw-Sickle Teardrop region (X in [12, 79], Y in [24.5, 55])
        # so we can separate structural arch stress from local single-cheek blind pivot bore contact stress!
        nodes = mesh.FemMesh.Nodes
        stresses = list(res.vonMises)
        nids = list(res.NodeNumbers)
        win_stresses = [
            s for s, nid in zip(stresses, nids)
            if 12.0 <= nodes[nid].x <= 79.0 and 24.5 <= nodes[nid].y <= 55.0
        ]
        # Structural stress excluding 4.5 mm radius around the blind single-cheek pivot bore (109, 20.5, 5.2)
        # (remember in assembled Tibia, Tibia_Cover shares 50% of pivot pin load!)
        non_piv_stresses = [
            (s, nodes[nid]) for s, nid in zip(stresses, nids)
            if (nodes[nid] - App.Vector(109.0, 20.5, 5.2)).Length > 4.5
        ]
        s_win = max(win_stresses) if win_stresses else 0.0
        s_struct, pt_struct = max(non_piv_stresses, key=lambda t: t[0]) if non_piv_stresses else (0.0, App.Vector())
        stats["sigma_teardrop_max"] = round(s_win, 2)
        stats["S_teardrop_petg"] = round(RE_PETG / s_win, 2) if s_win > 0 else 999.0
        stats["sigma_struct_max"] = round(s_struct, 2)
        stats["S_struct_petg"] = round(RE_PETG / s_struct, 2) if s_struct > 0 else 999.0
        stats["struct_hotspot_mm"] = [round(pt_struct.x, 1), round(pt_struct.y, 1), round(pt_struct.z, 1)]
        stats["id"] = lc_id
        stats["label"] = label
        results.append(stats)

        print(
            f"  -> Global peak={stats['sigma_max']:.2f} MPa @ {stats['hotspot_mm']} (S={stats['S_petg']:.2f}) | "
            f"Struct(ex-bore)={s_struct:.2f} MPa @ {stats['struct_hotspot_mm']} (S={stats['S_struct_petg']:.2f}) | "
            f"Teardrop rib={s_win:.2f} MPa (S={stats['S_teardrop_petg']:.2f}) | u_max={stats['u_max']:.3f} mm"
        )
        doc.saveAs(os.path.join(lc_dir, f"{lc_id}_results.FCStd"))
        App.closeDocument(doc.Name)

    return results


def main():
    os.makedirs(WORK_DIR, exist_ok=True)
    t_res = run_tarsus_fea()
    tb_res = run_tibia_fea()
    summary = {"tarsus": t_res, "tibia": tb_res}
    out_json = os.path.join(WORK_DIR, "fea_summary.json")
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)
    print("\n" + "=" * 96)
    print("SUMMARY SAVED TO:", out_json)
    print("=" * 96)


if __name__ == "__main__":
    main()
