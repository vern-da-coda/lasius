#!/usr/bin/env python3
"""
Convert Lasius Hexapod Body Assembly (excluding Gaster & Head) into Blender.

Pipeline:
1. FreeCAD headless extracts all leaf shapes with their accumulated global placements.
2. Tessellates geometry into a high-fidelity multi-object OBJ with MTL materials.
3. Blender headless imports OBJ, creates structured collections, sets up PBR materials,
   and saves a native .blend file and .glb (glTF 2.0) binary.

Outputs:
- hardware/mechanics/export/blender/body_assembly.obj
- hardware/mechanics/export/blender/body_assembly.mtl
- hardware/mechanics/export/blender/body_assembly.blend
- hardware/mechanics/export/blender/body_assembly.glb
"""

import os
import sys
import time
import subprocess

REPO_ROOT = "/home/bjoern/Workspace/Hexapods/lasius"
FC_MODEL = os.path.join(REPO_ROOT, "hardware/mechanics/models/custom/v2/body_assembly.FCStd")
EXPORT_DIR = os.path.join(REPO_ROOT, "hardware/mechanics/export/blender")
OBJ_FILE = os.path.join(EXPORT_DIR, "body_assembly.obj")
MTL_FILE = os.path.join(EXPORT_DIR, "body_assembly.mtl")
BLEND_FILE = os.path.join(EXPORT_DIR, "body_assembly.blend")
GLB_FILE = os.path.join(EXPORT_DIR, "body_assembly.glb")

def run_freecad_export():
    """Runs inside FreeCAD console mode to extract tessellated meshes and export OBJ."""
    import FreeCAD as App
    import MeshPart

    print(f"--- Loading FreeCAD Assembly: {FC_MODEL} ---")
    doc = App.openDocument(FC_MODEL)

    def determine_material(name):
        n = name.lower()
        if "canopy" in n:
            return "mat_acrylic_canopy"
        if "body_bottom" in n or "body_top" in n or "carbon" in n:
            return "mat_carbon_plate"
        if "core" in n or "belly" in n or "service_cover" in n or "rpi_mount" in n or "tray" in n:
            return "mat_monocoque_petg"
        if "coxa" in n and "servo" not in n and "bearing" not in n and "washer" not in n and "screw" not in n:
            return "mat_lasius_orange"
        if "femur_body" in n or "femur" in n and "servo" not in n and "cover" not in n and "bearing" not in n and "washer" not in n and "screw" not in n:
            return "mat_lasius_orange"
        if "tibia_body" in n or "tibia" in n and "servo" not in n and "cover" not in n and "shoe" not in n and "bearing" not in n and "washer" not in n and "screw" not in n and "rocker" not in n and "tarsus" not in n:
            return "mat_lasius_orange"
        if "tibia_rocker" in n or "tarsus" in n:
            return "mat_rocker_runner"
        if "cover" in n or "shoe" in n:
            return "mat_petg_dark"
        if "servo_body" in n or ("servo" in n and "horn" not in n and "cable" not in n):
            return "mat_servo_matte"
        if "servo_horn" in n:
            return "mat_servo_horn_alu"
        if "cable" in n or "harness" in n or "wire" in n:
            return "mat_cable_silicone"
        if "zip_tie" in n:
            return "mat_zip_tie"
        if "board" in n or "rpi" in n or "pca" in n or "sensor" in n or "ads" in n or "tca" in n:
            return "mat_pcb_green"
        if "battery" in n:
            return "mat_battery_lipo"
        if "bearing" in n or "washer" in n or "screw" in n or "nut" in n or "spacer" in n or "pin" in n or "spring" in n:
            return "mat_hardware_steel"
        return "mat_default_grey"

    def get_leaves(obj, parent_plc=None, prefix=""):
        if parent_plc is None:
            parent_plc = App.Placement()
        curr_plc = parent_plc.multiply(getattr(obj, "Placement", App.Placement()))
        
        results = []
        if obj.isDerivedFrom("App::Link"):
            linked = obj.LinkedObject
            if linked:
                if hasattr(linked, "Group") and len(linked.Group) > 0:
                    for c in linked.Group:
                        results.extend(get_leaves(c, curr_plc, f"{prefix}{obj.Name}__"))
                elif hasattr(linked, "Shape") and not linked.Shape.isNull():
                    results.append((f"{prefix}{obj.Name}", linked.Shape, curr_plc))
        elif hasattr(obj, "Group") and len(obj.Group) > 0:
            for c in obj.Group:
                results.extend(get_leaves(c, curr_plc, f"{prefix}{obj.Name}__"))
        elif hasattr(obj, "Shape") and not obj.Shape.isNull():
            results.append((f"{prefix}{obj.Name}", obj.Shape, curr_plc))
        return results

    print("Traversing assembly tree...")
    leaves = []
    root_part = doc.getObject("Body_Assembly_v2")
    if root_part and hasattr(root_part, "Group"):
        for o in root_part.Group:
            leaves.extend(get_leaves(o))
    else:
        for o in doc.Objects:
            if any(o.Name.startswith(p) for p in ["Body_", "Chassis_", "Leg_", "Sensor_", "Board_"]):
                leaves.extend(get_leaves(o))

    print(f"Total leaf parts to tessellate: {len(leaves)}")
    os.makedirs(EXPORT_DIR, exist_ok=True)

    # Write MTL file
    mtl_content = """# Lasius Hexapod Material Library (MTL)
newmtl mat_carbon_plate
Kd 0.12 0.12 0.14
Ks 0.25 0.25 0.25
Ns 40.0
d 1.0

newmtl mat_acrylic_canopy
Kd 0.85 0.95 1.00
Ks 0.90 0.90 0.90
Ns 90.0
d 0.45
illum 4

newmtl mat_monocoque_petg
Kd 0.20 0.20 0.22
Ks 0.15 0.15 0.15
Ns 20.0
d 1.0

newmtl mat_lasius_orange
Kd 0.95 0.39 0.10
Ks 0.30 0.30 0.30
Ns 35.0
d 1.0

newmtl mat_petg_dark
Kd 0.15 0.15 0.18
Ks 0.20 0.20 0.20
Ns 25.0
d 1.0

newmtl mat_rocker_runner
Kd 0.95 0.95 0.95
Ks 0.40 0.40 0.40
Ns 50.0
d 1.0

newmtl mat_servo_matte
Kd 0.08 0.08 0.08
Ks 0.10 0.10 0.10
Ns 15.0
d 1.0

newmtl mat_servo_horn_alu
Kd 0.78 0.78 0.80
Ks 0.85 0.85 0.85
Ns 80.0
d 1.0

newmtl mat_cable_silicone
Kd 0.85 0.22 0.12
Ks 0.30 0.30 0.30
Ns 30.0
d 1.0

newmtl mat_zip_tie
Kd 0.10 0.10 0.12
Ks 0.20 0.20 0.20
Ns 20.0
d 1.0

newmtl mat_hardware_steel
Kd 0.72 0.74 0.78
Ks 0.90 0.90 0.90
Ns 85.0
d 1.0

newmtl mat_pcb_green
Kd 0.08 0.35 0.15
Ks 0.40 0.40 0.40
Ns 40.0
d 1.0

newmtl mat_battery_lipo
Kd 0.15 0.32 0.75
Ks 0.25 0.25 0.25
Ns 30.0
d 1.0

newmtl mat_default_grey
Kd 0.50 0.50 0.50
Ks 0.20 0.20 0.20
Ns 20.0
d 1.0
"""
    with open(MTL_FILE, "w") as f:
        f.write(mtl_content)
    print(f"Saved MTL: {MTL_FILE}")

    # Write multi-object OBJ
    v_offset = 1
    total_facets = 0
    with open(OBJ_FILE, "w") as f_obj:
        f_obj.write(f"# Lasius Hexapod Body Assembly OBJ Export\n")
        f_obj.write(f"mtllib {os.path.basename(MTL_FILE)}\n\n")

        for idx, (name, shape, plc) in enumerate(leaves):
            try:
                s = shape.copy()
                s.Placement = plc
                # Tessellate with fine deflection for smooth curves
                mesh = MeshPart.meshFromShape(s, LinearDeflection=0.08, AngularDeflection=0.35)
                if mesh.CountPoints == 0 or mesh.CountFacets == 0:
                    continue

                mat_name = determine_material(name)
                f_obj.write(f"o {name}\n")
                f_obj.write(f"usemtl {mat_name}\n")

                points = mesh.Points
                facets = mesh.Facets

                for pt in points:
                    # pt.Vector in mm, convert to meters for standard Blender units
                    # 1 unit = 1 m
                    f_obj.write(f"v {pt.Vector.x*0.001:.6f} {pt.Vector.y*0.001:.6f} {pt.Vector.z*0.001:.6f}\n")

                for facet in facets:
                    p1 = facet.PointIndices[0] + v_offset
                    p2 = facet.PointIndices[1] + v_offset
                    p3 = facet.PointIndices[2] + v_offset
                    f_obj.write(f"f {p1} {p2} {p3}\n")

                v_offset += len(points)
                total_facets += len(facets)
            except Exception as e:
                print(f"Warning: could not tessellate {name}: {e}")

    print(f"Exported OBJ: {OBJ_FILE} ({total_facets} triangles, {v_offset-1} vertices)")

def run_blender_import():
    """Script executed inside Blender to structure collections, tune shaders, and save .blend & .glb."""
    blender_py = f"""
import bpy
import os

obj_path = "{OBJ_FILE}"
blend_out = "{BLEND_FILE}"
glb_out = "{GLB_FILE}"

# Clear default scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# Import OBJ
bpy.ops.wm.obj_import(filepath=obj_path)

# Organize into Collections
scene = bpy.context.scene
root_coll = scene.collection

collections = {{
    "Chassis": ["Body_", "Chassis_"],
    "Electronics": ["Board_", "Sensor_", "Battery_"],
    "Leg_Front_Left": ["Leg_Front_Left"],
    "Leg_Middle_Left": ["Leg_Middle_Left"],
    "Leg_Rear_Left": ["Leg_Rear_Left"],
    "Leg_Front_Right": ["Leg_Front_Right"],
    "Leg_Middle_Right": ["Leg_Middle_Right"],
    "Leg_Rear_Right": ["Leg_Rear_Right"],
}}

created_colls = {{}}
for coll_name in collections:
    new_coll = bpy.data.collections.new(coll_name)
    root_coll.children.link(new_coll)
    created_colls[coll_name] = new_coll

# Assign objects to collections
for obj in list(scene.objects):
    assigned = False
    for coll_name, prefixes in collections.items():
        if any(prefix in obj.name for prefix in prefixes):
            created_colls[coll_name].objects.link(obj)
            root_coll.objects.unlink(obj)
            assigned = True
            break

# Refine materials (Principled BSDF)
for mat in bpy.data.materials:
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if not bsdf:
        continue
    
    mname = mat.name.lower()
    if "canopy" in mname:
        bsdf.inputs["Roughness"].default_value = 0.05
        bsdf.inputs["Transmission Weight"].default_value = 0.85
        bsdf.inputs["IOR"].default_value = 1.49  # PMMA Acrylic
        mat.blend_method = "BLEND" if hasattr(mat, "blend_method") else None
    elif "carbon" in mname:
        bsdf.inputs["Roughness"].default_value = 0.35
        bsdf.inputs["Metallic"].default_value = 0.2
    elif "steel" in mname or "alu" in mname or "hardware" in mname:
        bsdf.inputs["Metallic"].default_value = 0.9
        bsdf.inputs["Roughness"].default_value = 0.2
    elif "orange" in mname:
        bsdf.inputs["Roughness"].default_value = 0.4
    elif "cable" in mname:
        bsdf.inputs["Roughness"].default_value = 0.3

# Setup Studio Lighting and Camera
cam_data = bpy.data.cameras.new("MainCamera")
cam_obj = bpy.data.objects.new("MainCamera", cam_data)
root_coll.objects.link(cam_obj)
cam_obj.location = (0.35, -0.45, 0.30)
cam_obj.rotation_euler = (1.05, 0.0, 0.65)
scene.camera = cam_obj

light_data = bpy.data.lights.new(name="KeyLight", type='SUN')
light_data.energy = 3.5
light_obj = bpy.data.objects.new(name="KeyLight", object_data=light_data)
root_coll.objects.link(light_obj)
light_obj.rotation_euler = (0.785, 0.35, 0.785)

# Save .blend file
bpy.ops.wm.save_as_mainfile(filepath=blend_out)
print(f"Saved Blender scene: {{blend_out}}")

# Export .glb binary
bpy.ops.export_scene.gltf(filepath=glb_out, export_format='GLB')
print(f"Saved GLTF binary: {{glb_out}}")
"""
    tmp_blender_script = os.path.join(EXPORT_DIR, "import_pipeline.py")
    with open(tmp_blender_script, "w") as f:
        f.write(blender_py)

    cmd = ["/snap/bin/blender", "--background", "--python", tmp_blender_script]
    print(f"Running Blender: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    if os.path.exists(tmp_blender_script):
        os.remove(tmp_blender_script)

if __name__ == "__main__":
    # If run inside FreeCAD
    if "FreeCAD" in sys.modules:
        run_freecad_export()
    else:
        # Step 1: Run FreeCAD export
        print("=== Step 1: Running FreeCAD mesh extraction ===")
        fc_cmd = ["/snap/bin/freecad", "-c", f"import sys; sys.path.append('{REPO_ROOT}/scripts/dev'); import export_to_blender; export_to_blender.run_freecad_export(); sys.exit(0)"]
        subprocess.run(fc_cmd, check=True)

        # Step 2: Run Blender import and scene configuration
        print("\n=== Step 2: Running Blender scene generation ===")
        run_blender_import()
        print("\n=== Complete! Blender scene and GLB ready ===")
