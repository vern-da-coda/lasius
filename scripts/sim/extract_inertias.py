#!/usr/bin/env python3
"""
Extract physical mass, Center of Mass (CoM), and Inertia Tensors
from Lasius FreeCAD models for URDF / MJCF simulation export.
"""

import json
import os
import FreeCAD as App
import Part

MODELS_DIR = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/models"

# Material densities in g / mm^3 (or kg / dm^3):
DENSITY_PETG = 1.27e-3      # 1.27 g/cm^3 -> 1.27e-3 g/mm^3 -> 1270 kg/m^3
DENSITY_CARBON = 1.60e-3    # 1.60 g/cm^3 -> 1.60e-3 g/mm^3 -> 1600 kg/m^3
DENSITY_ALU = 2.70e-3       # 2.70 g/cm^3 -> 2.70e-3 g/mm^3 -> 2700 kg/m^3
SERVO_MASS_G = 56.0         # Reely NR-645 MG BB (56 g)

def analyze_shape(shape, density_g_per_mm3):
    """
    Compute volume (mm^3), mass (kg), Center of Mass (m), and Inertia Tensor (kg*m^2)
    in SI units (m, kg) for a TopoShape (Solid or Compound).
    """
    solids = shape.Solids if hasattr(shape, "Solids") and len(shape.Solids) > 0 else ([shape] if shape.ShapeType == "Solid" else [])
    
    total_vol_mm3 = 0.0
    weighted_com_mm = App.Vector(0, 0, 0)
    
    for s in solids:
        v = s.Volume
        total_vol_mm3 += v
        com = s.CenterOfMass
        weighted_com_mm = weighted_com_mm.add(com.multiply(v))
        
    if total_vol_mm3 <= 0:
        return None
        
    com_mm = weighted_com_mm.multiply(1.0 / total_vol_mm3)
    total_mass_g = total_vol_mm3 * density_g_per_mm3
    total_mass_kg = total_mass_g * 1e-3
    
    # Inertia tensor in SI units (kg * m^2) about CoM
    # FreeCAD MatrixOfInertia assumes density = 1.0 with dimensions in mm (unit: mm^5)
    # To convert to kg*m^2:
    # I_SI = I_mm5 * density_kg_per_m3 * (1e-3)^5 = I_mm5 * (density_g_per_mm3 * 1e6) * 1e-15 = I_mm5 * density_g_per_mm3 * 1e-9
    density_kg_per_m3 = density_g_per_mm3 * 1e6
    scale_factor = 1e-15 * density_kg_per_m3 # 1e-9 * density_g_per_mm3
    
    # Steiner parallel axis shift to combine all solids about overall CoM:
    ixx, iyy, izz = 0.0, 0.0, 0.0
    ixy, ixz, iyz = 0.0, 0.0, 0.0
    
    for s in solids:
        m_solid_kg = s.Volume * density_g_per_mm3 * 1e-3
        s_com_m = s.CenterOfMass.multiply(1e-3)
        com_m = com_mm.multiply(1e-3)
        dx = s_com_m.x - com_m.x
        dy = s_com_m.y - com_m.y
        dz = s_com_m.z - com_m.z
        
        # FreeCAD MatrixOfInertia components (about s.CenterOfMass if calculated on Solid):
        mat = s.MatrixOfInertia
        # FreeCAD matrix: A11=Ixx, A22=Iyy, A33=Izz, A12=-Ixy, A13=-Ixz, A23=-Iyz
        # Note: OpenCASCADE matrix has negative products of inertia
        s_ixx = mat.A11 * scale_factor
        s_iyy = mat.A22 * scale_factor
        s_izz = mat.A33 * scale_factor
        s_ixy = -mat.A12 * scale_factor
        s_ixz = -mat.A13 * scale_factor
        s_iyz = -mat.A23 * scale_factor
        
        # Parallel axis theorem
        ixx += s_ixx + m_solid_kg * (dy*dy + dz*dz)
        iyy += s_iyy + m_solid_kg * (dx*dx + dz*dz)
        izz += s_izz + m_solid_kg * (dx*dx + dy*dy)
        ixy += s_ixy - m_solid_kg * (dx*dy)
        ixz += s_ixz - m_solid_kg * (dx*dz)
        iyz += s_iyz - m_solid_kg * (dy*dz)
        
    return {
        "volume_mm3": total_vol_mm3,
        "mass_g": total_mass_g,
        "mass_kg": total_mass_kg,
        "com_mm": [com_mm.x, com_mm.y, com_mm.z],
        "com_m": [com_mm.x * 1e-3, com_mm.y * 1e-3, com_mm.z * 1e-3],
        "inertia_kg_m2": {
            "ixx": ixx, "iyy": iyy, "izz": izz,
            "ixy": ixy, "ixz": ixz, "iyz": iyz
        }
    }


def main():
    print("=== Extracting Physical Inertia Properties from Lasius CAD Models ===")
    results = {}
    
    parts_to_analyze = [
        ("coxa_bracket", f"{MODELS_DIR}/custom/v2/parts/coxa_bracket.FCStd", "Coxa_Bracket", DENSITY_PETG),
        ("femur_body", f"{MODELS_DIR}/custom/v2/parts/femur.FCStd", "Femur_Body", DENSITY_PETG),
        ("femur_cover", f"{MODELS_DIR}/custom/v2/parts/femur.FCStd", "Femur_Cover", DENSITY_PETG),
        ("tibia", f"{MODELS_DIR}/custom/v2/parts/tibia.FCStd", "Tibia_v2", DENSITY_PETG),
        ("body_bottom", f"{MODELS_DIR}/custom/v1/parts/body_bottom.FCStd", "BodyBottom", DENSITY_CARBON),
        ("body_top", f"{MODELS_DIR}/custom/v1/parts/body_top.FCStd", "BodyTop", DENSITY_CARBON),
        ("spacer", f"{MODELS_DIR}/custom/v1/parts/spacer_14x50.FCStd", "SpacerRod", DENSITY_ALU),
        ("servo_nr645", f"{MODELS_DIR}/cots/servo_nr645.FCStd", "Servo_Complete", None), # Special
    ]
    
    for key, path, obj_name, density in parts_to_analyze:
        if not os.path.exists(path):
            print(f"Skipping {key}: {path} not found")
            continue
        doc = App.openDocument(path)
        obj = getattr(doc, obj_name, None)
        if obj and hasattr(obj, "Shape"):
            if density is None:
                # COTS servo NR-645: Volume from CAD, total mass 56g
                v = obj.Shape.Volume
                d_eff = (SERVO_MASS_G) / v
                data = analyze_shape(obj.Shape, d_eff)
            else:
                data = analyze_shape(obj.Shape, density)
            results[key] = data
            print(f"[{key:15s}] Mass: {data['mass_g']:6.2f} g | CoM (mm): [{data['com_mm'][0]:6.2f}, {data['com_mm'][1]:6.2f}, {data['com_mm'][2]:6.2f}]")
        App.closeDocument(doc.Name)
        
    out_json = "/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/export/inertias.json"
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved inertia data to: {out_json}")

main()
