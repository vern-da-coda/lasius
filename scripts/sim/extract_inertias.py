#!/usr/bin/env python3
"""
Extract physical mass, Center of Mass (CoM), Inertia Tensors, and PyBullet-ready
Binary STL visual meshes directly from Lasius v2 FreeCAD CAD models (`body_assembly.FCStd`).

Outputs:
- hardware/mechanics/export/inertias.json
- hardware/mechanics/export/urdf/meshes/*.stl  (Binary STL in meters, link-local frames, outward normals)
"""

import json
import math
import os
import struct
import sys
import FreeCAD as App
import MeshPart
import Part

REPO_ROOT = "/home/bjoern/Workspace/Hexapods/lasius"
MODELS_DIR = f"{REPO_ROOT}/hardware/mechanics/models"
URDF_MESH_DIR = f"{REPO_ROOT}/hardware/mechanics/export/urdf/meshes"
OUT_JSON = f"{REPO_ROOT}/hardware/mechanics/export/inertias.json"

sys.path.insert(0, f"{REPO_ROOT}/hardware/mechanics/scripts/v2")
import generate_tibia as gt

# Material densities in g / mm^3:
DENSITY_PETG = 1.27e-3      # 1270 kg/m^3
DENSITY_TPU = 1.21e-3       # 1210 kg/m^3
DENSITY_PMMA = 1.18e-3      # 1180 kg/m^3 (Plexiglas canopy)
DENSITY_CARBON = 1.60e-3    # 1600 kg/m^3
SERVO_MASS_G = 56.0         # Torcster NR-645 MG BB (56 g)
RPI4_MASS_G = 46.0          # Raspberry Pi 4 Model B
BATTERY_MASS_G = 165.0      # 2S LiPo Battery Pack
ELECTRONICS_EXTRA_G = 95.0  # 2x PCA9685, TCA9548A, UBECs, wiring, fasteners


def analyze_shape(shape, density_g_per_mm3):
    """
    Compute volume (mm^3), mass (kg), Center of Mass (m), and Inertia Tensor (kg*m^2)
    in SI units (m, kg) for a TopoShape (Solid or Compound).
    """
    solids = shape.Solids if hasattr(shape, "Solids") and len(shape.Solids) > 0 else (
        [shape] if shape.ShapeType == "Solid" else []
    )
    total_vol_mm3 = 0.0
    weighted_com_mm = App.Vector(0, 0, 0)
    for s in solids:
        v = s.Volume
        total_vol_mm3 += v
        weighted_com_mm = weighted_com_mm.add(s.CenterOfMass.multiply(v))

    if total_vol_mm3 <= 0:
        return None

    com_mm = weighted_com_mm.multiply(1.0 / total_vol_mm3)
    total_mass_g = total_vol_mm3 * density_g_per_mm3
    total_mass_kg = total_mass_g * 1e-3

    density_kg_per_m3 = density_g_per_mm3 * 1e6
    scale_factor = 1e-15 * density_kg_per_m3

    ixx = iyy = izz = ixy = ixz = iyz = 0.0
    com_m = com_mm.multiply(1e-3)
    for s in solids:
        m_solid_kg = s.Volume * density_g_per_mm3 * 1e-3
        s_com_m = s.CenterOfMass.multiply(1e-3)
        dx = s_com_m.x - com_m.x
        dy = s_com_m.y - com_m.y
        dz = s_com_m.z - com_m.z

        mat = s.MatrixOfInertia
        s_ixx = mat.A11 * scale_factor
        s_iyy = mat.A22 * scale_factor
        s_izz = mat.A33 * scale_factor
        s_ixy = -mat.A12 * scale_factor
        s_ixz = -mat.A13 * scale_factor
        s_iyz = -mat.A23 * scale_factor

        ixx += s_ixx + m_solid_kg * (dy * dy + dz * dz)
        iyy += s_iyy + m_solid_kg * (dx * dx + dz * dz)
        izz += s_izz + m_solid_kg * (dx * dx + dy * dy)
        ixy += s_ixy - m_solid_kg * (dx * dy)
        ixz += s_ixz - m_solid_kg * (dx * dz)
        iyz += s_iyz - m_solid_kg * (dy * dz)

    return {
        "volume_mm3": total_vol_mm3,
        "mass_g": total_mass_g,
        "mass_kg": total_mass_kg,
        "com_mm": [com_mm.x, com_mm.y, com_mm.z],
        "com_m": [com_m.x, com_m.y, com_m.z],
        "inertia_kg_m2": {
            "ixx": ixx, "iyy": iyy, "izz": izz,
            "ixy": ixy, "ixz": ixz, "iyz": iyz,
        },
    }


def make_scale_matrix(sx, sy, sz):
    m = App.Matrix()
    m.A11 = sx
    m.A22 = sy
    m.A33 = sz
    return m


def export_binary_stl(shape, matrix_mm, out_path, deflection=0.35, angular_deflection=0.50):
    """
    Tessellate a FreeCAD TopoShape via `MeshPart.meshFromShape` (bypassing stale fine
    cached display meshes so total instanced triangles stay well below PyBullet's
    128 MB OpenGL GLInstancingRenderer vertex buffer limit!), transform by `matrix_mm`
    (in mm), scale to meters (x 0.001), flip triangle winding if det(matrix_mm) < 0
    (mirrored right parts!), recompute outward unit normals, and write a clean Binary STL.
    """
    mesh = MeshPart.meshFromShape(
        Shape=shape,
        LinearDeflection=max(float(deflection), 0.30),
        AngularDeflection=float(angular_deflection),
        Relative=False,
    )
    verts, tris = mesh.Topology
    det = matrix_mm.determinant()
    flip = det < 0.0

    # Pre-transform vertices to meters
    tverts = []
    for v in verts:
        tv = matrix_mm.multVec(v)
        tverts.append((tv.x * 1e-3, tv.y * 1e-3, tv.z * 1e-3))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    header = b"Binary STL generated for Lasius v2 PyBullet URDF".ljust(80, b"\x00")
    out_chunks = [header, struct.pack("<I", len(tris))]
    pack_tri = struct.Struct("<12fH").pack

    for i0, i1, i2 in tris:
        if flip:
            i1, i2 = i2, i1
        p0 = tverts[i0]
        p1 = tverts[i1]
        p2 = tverts[i2]
        ux, uy, uz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
        vx, vy, vz = p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]
        nx = uy * vz - uz * vy
        ny = uz * vx - ux * vz
        nz = ux * vy - uy * vx
        nlen = math.sqrt(nx * nx + ny * ny + nz * nz)
        if nlen > 1e-12:
            nx /= nlen
            ny /= nlen
            nz /= nlen
        else:
            nx, ny, nz = 0.0, 0.0, 1.0
        out_chunks.append(pack_tri(
            nx, ny, nz,
            p0[0], p0[1], p0[2],
            p1[0], p1[1], p1[2],
            p2[0], p2[1], p2[2],
            0,
        ))

    with open(out_path, "wb") as f:
        f.write(b"".join(out_chunks))
    print(f"  ✔ Binary STL: {os.path.basename(out_path):28s} ({len(tris):6d} tris, flip={flip})")


def load_shape(rel_path, obj_name):
    full_path = f"{MODELS_DIR}/{rel_path}"
    doc = App.openDocument(full_path, hidden=True)
    obj = doc.getObject(obj_name)
    if obj is None:
        raise RuntimeError(f"Object '{obj_name}' not found in {full_path}")
    shape = obj.Shape.copy()
    App.closeDocument(doc.Name)
    return shape


def main():
    print("=== Extracting Lasius v2 Inertias & PyBullet Binary STL Meshes (`body_assembly`) ===")
    os.makedirs(URDF_MESH_DIR, exist_ok=True)

    # 1. Load canonical v2 & COTS shapes
    part_specs = [
        ("body_bottom",           "custom/v1/parts/body_bottom.FCStd",               "BodyBottom",            DENSITY_CARBON),
        ("body_top",              "custom/v1/parts/body_top.FCStd",                  "BodyTop",               DENSITY_CARBON),
        ("chassis_core_lower",    "custom/v2/parts/chassis/chassis_core_lower.FCStd","Chassis_Core_Lower",    DENSITY_PETG),
        ("chassis_core_upper",    "custom/v2/parts/chassis/chassis_core_upper.FCStd","Chassis_Core_Upper",    DENSITY_PETG),
        ("chassis_belly_pan",     "custom/v2/parts/chassis/chassis_belly_pan.FCStd", "Chassis_Belly_Pan",     DENSITY_PETG),
        ("chassis_battery_hatch", "custom/v2/parts/chassis/chassis_battery_hatch.FCStd", "Chassis_Battery_Hatch", DENSITY_PETG),
        ("chassis_rpi_mount",     "custom/v2/parts/chassis/chassis_rpi_mount.FCStd", "Chassis_RPi_Mount",     DENSITY_PETG),
        ("chassis_canopy",        "custom/v2/parts/chassis/chassis_canopy.FCStd",    "Chassis_Canopy",        DENSITY_PMMA),
        ("coxa",                  "custom/v2/parts/coxa/coxa.FCStd",                 "Coxa",                  DENSITY_PETG),
        ("femur_body",            "custom/v2/parts/femur/femur.FCStd",               "Femur_Body",            DENSITY_PETG),
        ("femur_cover",           "custom/v2/parts/femur/femur_cover.FCStd",         "Femur_Cover",           DENSITY_PETG),
        ("tibia",                 "custom/v2/parts/tibia/tibia.FCStd",               "Tibia_Body",            DENSITY_PETG),
        ("tibia_cover",           "custom/v2/parts/tibia/tibia_cover.FCStd",         "Tibia_Cover",           DENSITY_PETG),
        ("tarsus",                "custom/v2/parts/tarsus/tarsus.FCStd",             "Tarsus",                DENSITY_PETG),
        ("tarsus_shoe",           "custom/v2/parts/tarsus/tarsus_shoe.FCStd",        "Tarsus_Shoe",           DENSITY_TPU),
        ("servo_nr645",           "cots/servo_nr645.FCStd",                          "Servo_Complete",        None),
        ("rpi4_model_b",          "cots/rpi4_model_b.FCStd",                         "Raspberry_Pi_4",        None),
        ("vl53l5cx_board",        "cots/vl53l5cx_board.FCStd",                       "VL53L5CX_Board",        None),
        ("bno085_board",          "cots/bno085_board.FCStd",                         "BNO085_Board",          None),
    ]

    shapes = {}
    results = {}
    for key, rel_path, obj_name, density in part_specs:
        sh = load_shape(rel_path, obj_name)
        shapes[key] = sh
        if density is None:
            fixed_mass = (
                SERVO_MASS_G if key == "servo_nr645"
                else (RPI4_MASS_G if key == "rpi4_model_b" else (2.5 if key == "bno085_board" else 3.0))
            )
            d_eff = fixed_mass / max(sh.Volume, 1e-6)
            data = analyze_shape(sh, d_eff)
        else:
            data = analyze_shape(sh, density)
        results[key] = data
        print(f"  [{key:22s}] Mass: {data['mass_g']:6.2f} g | CoM (mm): [{data['com_mm'][0]:6.2f}, {data['com_mm'][1]:6.2f}, {data['com_mm'][2]:6.2f}]")

    # Synthesize combined chassis_core compound for URDF/Dashboard visual & inertia compatibility
    shapes["chassis_core"] = Part.makeCompound([shapes["chassis_core_lower"], shapes["chassis_core_upper"]])
    results["chassis_core"] = analyze_shape(shapes["chassis_core"], DENSITY_PETG)

    # 2. Export PyBullet Binary STLs baked in exact URDF link-local frames (meters, outward normals!)
    print("\n--- Exporting PyBullet Binary STL Meshes (Link-Local Meters, Positive Winding) ---")
    I = App.Matrix()

    # A. Base Link (Chassis) meshes in body_assembly.FCStd frame
    export_binary_stl(shapes["body_bottom"],           I, f"{URDF_MESH_DIR}/body_bottom.stl", 0.25)
    export_binary_stl(shapes["body_top"],              App.Placement(App.Vector(0, 0, 53.30), App.Rotation()).toMatrix(), f"{URDF_MESH_DIR}/body_top.stl", 0.25)
    export_binary_stl(shapes["chassis_core"],          I, f"{URDF_MESH_DIR}/chassis_core.stl", 0.25)
    export_binary_stl(shapes["chassis_belly_pan"],     I, f"{URDF_MESH_DIR}/chassis_belly_pan.stl", 0.25)
    export_binary_stl(shapes["chassis_battery_hatch"], I, f"{URDF_MESH_DIR}/chassis_battery_hatch.stl", 0.25)
    export_binary_stl(shapes["chassis_rpi_mount"],     I, f"{URDF_MESH_DIR}/chassis_rpi_mount.stl", 0.25)
    export_binary_stl(shapes["chassis_canopy"],        I, f"{URDF_MESH_DIR}/chassis_canopy.stl", 0.25)
    export_binary_stl(shapes["rpi4_model_b"],          App.Placement(App.Vector(0, 0, 59.80), App.Rotation()).toMatrix(), f"{URDF_MESH_DIR}/rpi4_model_b.stl", 0.30)
    export_binary_stl(shapes["vl53l5cx_board"],        App.Placement(App.Vector(-58.50, 0, -2.75), App.Rotation(App.Vector(0, 1, 0), 180.0)).toMatrix(), f"{URDF_MESH_DIR}/vl53l5cx_board.stl", 0.30)
    export_binary_stl(shapes["bno085_board"],          App.Placement(App.Vector(75.00, 0, 58.32), App.Rotation(App.Vector(0, 0, 1), 90.0)).toMatrix(), f"{URDF_MESH_DIR}/bno085_board.stl", 0.30)

    # B. Coxa Link meshes (origin = Coxa Pivot Axis in body_assembly!)
    #    In body_assembly: leg_assembly is shifted by Y_shift = -2.50 (Left) / +2.50 (Right)
    rot_c = App.Rotation(App.Vector(0, 0, 1), 180.0).multiply(App.Rotation(App.Vector(1, 0, 0), 90.0))
    m_shift_l = App.Placement(App.Vector(0.0, -2.50, 0.0), App.Rotation()).toMatrix()
    m_shift_r = App.Placement(App.Vector(0.0, +2.50, 0.0), App.Rotation()).toMatrix()

    p_coxa_l = App.Placement(App.Vector(74.70, -6.50, -15.25), rot_c)
    p_coxa_r = App.Placement(App.Vector(74.70, +6.50, -15.25), rot_c)
    export_binary_stl(shapes["coxa"], m_shift_l.multiply(p_coxa_l.toMatrix()), f"{URDF_MESH_DIR}/coxa_left.stl", 0.20)
    export_binary_stl(shapes["coxa"], m_shift_r.multiply(p_coxa_r.toMatrix()).multiply(make_scale_matrix(1, 1, -1)), f"{URDF_MESH_DIR}/coxa_right.stl", 0.20)

    # Actuators on Coxa (unmirrored real COTS servos!)
    rot_s_brk = App.Rotation(App.Vector(1, 0, 0), -90.0)
    p_cs_l = p_coxa_l.multiply(App.Placement(App.Vector(74.70, 42.75, 9.00), rot_s_brk))
    p_fs_l = p_coxa_l.multiply(App.Placement(App.Vector(18.20, 15.25, 27.30), App.Rotation()))
    p_cs_r = App.Placement(App.Vector(0.00, -2.50, 27.50), App.Rotation(App.Vector(0, 0, 1), 180.0))
    p_fs_r = App.Placement(App.Vector(56.50, -20.80, 0.00), App.Rotation(App.Vector(0, 0, 1), 180.0).multiply(App.Rotation(App.Vector(1, 0, 0), -90.0)))

    export_binary_stl(shapes["servo_nr645"], m_shift_l.multiply(p_cs_l.toMatrix()), f"{URDF_MESH_DIR}/coxa_servo_left.stl", 0.30)
    export_binary_stl(shapes["servo_nr645"], m_shift_l.multiply(p_fs_l.toMatrix()), f"{URDF_MESH_DIR}/femur_servo_left.stl", 0.30)
    export_binary_stl(shapes["servo_nr645"], m_shift_r.multiply(p_cs_r.toMatrix()), f"{URDF_MESH_DIR}/coxa_servo_right.stl", 0.30)
    export_binary_stl(shapes["servo_nr645"], m_shift_r.multiply(p_fs_r.toMatrix()), f"{URDF_MESH_DIR}/femur_servo_right.stl", 0.30)

    # C. Femur Link meshes (origin = Femur Pivot Axis at q_femur = 0, extending +X to Knee at X = 100 mm)
    export_binary_stl(shapes["femur_body"],  I,                           f"{URDF_MESH_DIR}/femur_left.stl", 0.20)
    export_binary_stl(shapes["femur_cover"], I,                           f"{URDF_MESH_DIR}/femur_cover_left.stl", 0.20)
    export_binary_stl(shapes["femur_body"],  make_scale_matrix(1, -1, 1), f"{URDF_MESH_DIR}/femur_right.stl", 0.20)
    export_binary_stl(shapes["femur_cover"], make_scale_matrix(1, -1, 1), f"{URDF_MESH_DIR}/femur_cover_right.stl", 0.20)

    # D. Tibia + Tarsus + Compact Kufe Shoe meshes (origin = Knee Pivot Axis at q_tibia = 0, extending +X!)
    rot_tib_0 = App.Rotation(0.0, 0.0, 90.0)   # Maps Tibia +X -> +X, +Y -> +Z, +Z -> -Y
    m_tib_l = App.Placement(App.Vector(-gt.KNEE_X, +11.50, -gt.KNEE_Y), rot_tib_0).toMatrix()
    m_tib_r = App.Placement(App.Vector(-gt.KNEE_X, -11.50, -gt.KNEE_Y), rot_tib_0).toMatrix()

    export_binary_stl(shapes["tibia"],       m_tib_l, f"{URDF_MESH_DIR}/tibia_left.stl", 0.18)
    export_binary_stl(shapes["tibia_cover"], m_tib_l, f"{URDF_MESH_DIR}/tibia_cover_left.stl", 0.18)
    export_binary_stl(shapes["tibia"],       m_tib_r.multiply(make_scale_matrix(1, 1, -1)), f"{URDF_MESH_DIR}/tibia_right.stl", 0.18)
    export_binary_stl(shapes["tibia_cover"], m_tib_r.multiply(make_scale_matrix(1, 1, -1)), f"{URDF_MESH_DIR}/tibia_cover_right.stl", 0.18)

    # Knee Servo (unmirrored COTS!)
    m_ks_l = m_tib_l.multiply(App.Placement(App.Vector(gt.KNEE_X, gt.KNEE_Y, -9.30), App.Rotation(App.Vector(1, 0, 0), 180.0)).toMatrix())
    m_ks_r = m_tib_r.multiply(App.Placement(App.Vector(gt.KNEE_X, gt.KNEE_Y, +9.30), App.Rotation()).toMatrix())
    export_binary_stl(shapes["servo_nr645"], m_ks_l, f"{URDF_MESH_DIR}/knee_servo_left.stl", 0.30)
    export_binary_stl(shapes["servo_nr645"], m_ks_r, f"{URDF_MESH_DIR}/knee_servo_right.stl", 0.30)

    # Tarsus & Compact Kufe Shoe (at 0 deg rest pose inside Tibia fork!)
    m_tar_l = m_tib_l.multiply(App.Placement(App.Vector(gt.TARSUS_PIV_X, gt.TARSUS_PIV_Y, +gt.Z_MID), App.Rotation()).toMatrix())
    m_tar_r = m_tib_r.multiply(App.Placement(App.Vector(gt.TARSUS_PIV_X, gt.TARSUS_PIV_Y, -gt.Z_MID), App.Rotation()).toMatrix()).multiply(make_scale_matrix(1, 1, -1))
    export_binary_stl(shapes["tarsus"],      m_tar_l, f"{URDF_MESH_DIR}/tarsus_left.stl", 0.15)
    export_binary_stl(shapes["tarsus_shoe"], m_tar_l, f"{URDF_MESH_DIR}/tarsus_shoe_left.stl", 0.15)
    export_binary_stl(shapes["tarsus"],      m_tar_r, f"{URDF_MESH_DIR}/tarsus_right.stl", 0.15)
    export_binary_stl(shapes["tarsus_shoe"], m_tar_r, f"{URDF_MESH_DIR}/tarsus_shoe_right.stl", 0.15)

    # Record exact foot contact sphere center flush with bottom of compact Kufe sole (R = 4.0 mm -> outer tip at X=65.4!)
    p_sole_l = m_tar_l.multVec(App.Vector(61.40, 5.20, 0.0))
    p_sole_r = m_tar_r.multVec(App.Vector(61.40, 5.20, 0.0))
    results["_geometry"] = {
        "coxa_len_m": 0.0565,
        "femur_len_m": 0.1000,
        "foot_pos_left_m": [p_sole_l.x * 1e-3, p_sole_l.y * 1e-3, p_sole_l.z * 1e-3],
        "foot_pos_right_m": [p_sole_r.x * 1e-3, p_sole_r.y * 1e-3, p_sole_r.z * 1e-3],
        "tibia_eff_len_m": math.sqrt(p_sole_l.x ** 2 + p_sole_l.z ** 2) * 1e-3,
    }

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n✔ Saved inertia & geometry data to: {OUT_JSON}")
    print(f"  Left  Foot Sole Center (link_tibia): {[round(v, 5) for v in results['_geometry']['foot_pos_left_m']]} m")
    print(f"  Right Foot Sole Center (link_tibia): {[round(v, 5) for v in results['_geometry']['foot_pos_right_m']]} m")
    print(f"  Effective Knee-to-Sole Length:       {results['_geometry']['tibia_eff_len_m']*1e3:.2f} mm")


_is_main = (__name__ == "__main__") or (
    len(sys.argv) > 1 and os.path.basename(sys.argv[1]) == os.path.basename(__file__)
)
if _is_main:
    main()
