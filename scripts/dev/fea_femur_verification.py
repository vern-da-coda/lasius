#!/usr/bin/env python3
"""
Automated Verification Finite Element Analysis (FEA) of Lightweight Optimized Femur v2.
Compares directly against baseline FEA across:
1. LF1 - Tripod Gait Vertical Bending (Fz = -15 N)
2. LF2 - Knee Servo Stall Torque (F_tangential = 120 N)
3. LF3 - Lateral Slope Traction (Fy = +10 N)
"""

import math
import os
import sys
import time

REPO_ROOT = "/home/bjoern/Workspace/Hexapods/lasius"
sys.path.append(os.path.join(REPO_ROOT, "scripts/dev"))

import FreeCAD as App
import Part
import ObjectsFem
from femmesh.gmshtools import GmshTools
from femtools.ccxtools import CcxTools
import feminout.importCcxFrdResults as importCcxFrdResults

import test_femur_lightweight

WORK_DIR = os.path.join(REPO_ROOT, "hardware/mechanics/export/fea/femur_optimized")

def run_verification_fea():
    os.makedirs(WORK_DIR, exist_ok=True)
    print("=" * 80)
    print("--- Lasius Femur v2: Verification FEA of Optimized Lightweight Solid ---")
    print("=" * 80)

    femur_shape = test_femur_lightweight.build_lightweight_femur()

    volume_cm3 = femur_shape.Volume / 1000.0
    mass_g = volume_cm3 * 1.27
    print(f"Optimized Femur Volume: {volume_cm3:.2f} cm^3")
    print(f"Optimized Femur Mass (PETG 1.27 g/cm^3): {mass_g:.2f} g (Delta: {mass_g - 82.02:.2f} g)")

    # Identify hip and knee cylindrical faces
    hip_faces = []
    knee_faces = []
    for i, face in enumerate(femur_shape.Faces):
        c = face.CenterOfMass
        f_name = f"Face{i+1}"
        if abs(c.x) < 5.0 and abs(c.z) < 5.0 and face.Surface.TypeId == "Part::GeomCylinder":
            hip_faces.append(f_name)
        elif abs(c.x - 100.0) < 5.0 and abs(c.z) < 5.0 and face.Surface.TypeId == "Part::GeomCylinder":
            knee_faces.append(f_name)

    print(f"Hip fixed faces: {hip_faces}")
    print(f"Knee loaded faces: {knee_faces}")

    load_cases = [
        {
            "id": "LF1_Tripod_Gait_Bending",
            "name": "LF1: Vertikaler Tripod-Gait (Biegung)",
            "force_val": 15.0,
            "direction": App.Vector(0, 0, -1),
        },
        {
            "id": "LF2_Knee_Stall_Torque",
            "name": "LF2: Servo Stall Torque (Blockiermoment)",
            "force_val": 120.0,
            "direction": App.Vector(0, 0, -1),
        },
        {
            "id": "LF3_Lateral_Slope_Traction",
            "name": "LF3: Laterale Hangquerung (Querlast)",
            "force_val": 10.0,
            "direction": App.Vector(0, 1, 0),
        }
    ]

    results_summary = []

    for lc in load_cases:
        lc_id = lc["id"]
        lc_name = lc["name"]
        print(f"\n>>> Running Verification on {lc_name} ...")
        lc_dir = os.path.join(WORK_DIR, lc_id)
        os.makedirs(lc_dir, exist_ok=True)

        doc = App.newDocument(f"FEA_Opt_{lc_id}")

        femur = doc.addObject("Part::Feature", "Femur")
        femur.Shape = femur_shape
        doc.recompute()

        analysis = ObjectsFem.makeAnalysis(doc, f"Analysis_{lc_id}")

        mat = ObjectsFem.makeMaterialSolid(doc, "PETG_Material")
        mat_dict = mat.Material
        mat_dict["Name"] = "PETG"
        mat_dict["YoungsModulus"] = "2100 MPa"
        mat_dict["PoissonRatio"] = "0.38"
        mat_dict["Density"] = "1270 kg/m^3"
        mat.Material = mat_dict
        analysis.addObject(mat)

        fixed = ObjectsFem.makeConstraintFixed(doc, "Hip_Pivot_Fixed")
        fixed.References = [(femur, tuple(hip_faces))]
        analysis.addObject(fixed)

        force = ObjectsFem.makeConstraintForce(doc, "Knee_Pivot_Force")
        force.References = [(femur, tuple(knee_faces))]
        force.Force = App.Units.Quantity(f"{lc['force_val']} N")
        force.DirectionVector = lc["direction"]
        force.Reversed = False
        analysis.addObject(force)

        mesh = ObjectsFem.makeMeshGmsh(doc, "Femur_Gmsh")
        mesh.Shape = femur
        mesh.CharacteristicLengthMax = 3.5
        mesh.CharacteristicLengthMin = 1.0
        analysis.addObject(mesh)
        doc.recompute()

        t0 = time.time()
        gmsh_tool = GmshTools(mesh)
        gmsh_tool.create_mesh()
        t_mesh = time.time() - t0
        node_cnt = mesh.FemMesh.NodeCount
        tet_cnt = mesh.FemMesh.VolumeCount
        print(f"  Gmsh mesh: {node_cnt} nodes, {tet_cnt} elements in {t_mesh:.2f}s")

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
        fea.ccx_run()
        t_solve = time.time() - t1
        print(f"  CalculiX solved in {t_solve:.2f}s")

        frd_file = os.path.join(lc_dir, "Femur_Gmsh.frd")
        res_obj = importCcxFrdResults.importFrd(frd_file, analysis, "CCX_")
        if not res_obj:
            raise RuntimeError(f"Failed to import results from {frd_file}")

        stresses = res_obj.vonMises
        displacements = res_obj.DisplacementLengths

        sigma_max = max(stresses) if len(stresses) > 0 else 0.0
        sigma_mean = sum(stresses) / len(stresses) if len(stresses) > 0 else 0.0
        u_max = max(displacements) if len(displacements) > 0 else 0.0
        re_petg = 45.0
        safety_factor = re_petg / sigma_max if sigma_max > 0 else 999.0

        low_stress_count = sum(1 for s in stresses if s < 5.0)
        low_stress_ratio = (low_stress_count / len(stresses)) * 100.0 if len(stresses) > 0 else 0.0

        res_data = {
            "id": lc_id,
            "name": lc_name,
            "sigma_max": sigma_max,
            "sigma_mean": sigma_mean,
            "u_max": u_max,
            "safety_factor": safety_factor,
            "low_stress_ratio": low_stress_ratio,
        }
        results_summary.append(res_data)

        print(f"  Max von Mises Stress: {sigma_max:.2f} MPa")
        print(f"  Mean von Mises Stress: {sigma_mean:.2f} MPa")
        print(f"  Max Displacement: {u_max:.4f} mm")
        print(f"  Safety Factor (Re = 45 MPa): S = {safety_factor:.2f}")

        res_fcstd = os.path.join(lc_dir, f"{lc_id}_opt_results.FCStd")
        doc.saveAs(res_fcstd)
        App.closeDocument(doc.Name)

    print("\n" + "=" * 90)
    print("--- OPTIMIZED FEMUR FEA SUMMARY (VERIFICATION) ---")
    print("=" * 90)
    print(f"{'Load Case':35s} | {'Max Stress':12s} | {'Max Deflection':14s} | {'Safety S':10s}")
    print("-" * 90)
    for r in results_summary:
        print(f"{r['name']:35s} | {r['sigma_max']:8.2f} MPa  | {r['u_max']:9.4f} mm    | {r['safety_factor']:6.2f}")
    print("=" * 90)

    return results_summary, mass_g

if __name__ == "__main__":
    run_verification_fea()
