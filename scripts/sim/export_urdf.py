#!/usr/bin/env python3
"""
Generate Lasius Hexapod URDF (Unified Robot Description Format) model
for physics simulation (PyBullet, MuJoCo, Webots, ROS/Gazebo).

Reads:
- Robot geometry & joint parameters: software/lasius-core/src/lasius/core/config.yaml
- Physical inertias & masses: hardware/mechanics/export/inertias.json
- 3D CAD meshes: hardware/mechanics/export/stl/

Outputs:
- hardware/mechanics/export/urdf/lasius.urdf
"""

import json
import math
import os
import xml.dom.minidom
import xml.etree.ElementTree as ET
import yaml

REPO_ROOT = "/home/bjoern/Workspace/Hexapods/lasius"
CONFIG_PATH = f"{REPO_ROOT}/software/lasius-core/src/lasius/core/config.yaml"
INERTIAS_PATH = f"{REPO_ROOT}/hardware/mechanics/export/inertias.json"
URDF_OUT_DIR = f"{REPO_ROOT}/hardware/mechanics/export/urdf"
URDF_OUT_PATH = f"{URDF_OUT_DIR}/lasius.urdf"

# Meshes base path relative to the URDF directory
MESH_REL_DIR = "../stl"


def format_vec3(v):
    return f"{v[0]:.6f} {v[1]:.6f} {v[2]:.6f}"


def format_rpy(r, p, y):
    return f"{r:.6f} {p:.6f} {y:.6f}"


def create_inertial(parent_elem, mass_kg, com_m, inertia_dict):
    inertial = ET.SubElement(parent_elem, "inertial")
    ET.SubElement(inertial, "origin", xyz=format_vec3(com_m), rpy="0 0 0")
    ET.SubElement(inertial, "mass", value=f"{mass_kg:.6f}")
    ET.SubElement(
        inertial,
        "inertia",
        ixx=f"{inertia_dict.get('ixx', 1e-5):.8e}",
        iyy=f"{inertia_dict.get('iyy', 1e-5):.8e}",
        izz=f"{inertia_dict.get('izz', 1e-5):.8e}",
        ixy=f"{inertia_dict.get('ixy', 0.0):.8e}",
        ixz=f"{inertia_dict.get('ixz', 0.0):.8e}",
        iyz=f"{inertia_dict.get('iyz', 0.0):.8e}",
    )


def create_mesh_visual(parent_elem, mesh_path, origin_xyz, origin_rpy, scale_xyz, material_name):
    visual = ET.SubElement(parent_elem, "visual")
    ET.SubElement(visual, "origin", xyz=format_vec3(origin_xyz), rpy=format_rpy(*origin_rpy))
    geom = ET.SubElement(visual, "geometry")
    ET.SubElement(geom, "mesh", filename=mesh_path, scale=format_vec3(scale_xyz))
    ET.SubElement(visual, "material", name=material_name)


def create_collision_box(parent_elem, origin_xyz, origin_rpy, size_xyz):
    collision = ET.SubElement(parent_elem, "collision")
    ET.SubElement(collision, "origin", xyz=format_vec3(origin_xyz), rpy=format_rpy(*origin_rpy))
    geom = ET.SubElement(collision, "geometry")
    ET.SubElement(geom, "box", size=format_vec3(size_xyz))


def create_collision_sphere(parent_elem, origin_xyz, radius):
    collision = ET.SubElement(parent_elem, "collision")
    ET.SubElement(collision, "origin", xyz=format_vec3(origin_xyz), rpy="0 0 0")
    geom = ET.SubElement(collision, "geometry")
    ET.SubElement(geom, "sphere", radius=f"{radius:.6f}")


def build_urdf():
    print(f"--- Generating Lasius Hexapod URDF: {URDF_OUT_PATH} ---")
    
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
    geom_cfg = config.get("geometry", {})
    limbs = geom_cfg.get("limbs", {})
    coxa_len = 0.056500                            # Exact FreeCAD axis distance: 56.50 mm (nominal 60.0 mm)
    femur_len = limbs.get("femur", 100.0) * 1e-3   # 100.00 mm
    tibia_len = limbs.get("tibia", 130.0) * 1e-3   # 130.00 mm
    
    with open(INERTIAS_PATH, "r") as f:
        inertias = json.load(f)
        
    robot = ET.Element("robot", name="lasius_hexapod")
    
    # -------------------------------------------------------------
    # Materials Definitions
    # -------------------------------------------------------------
    materials = [
        ("carbon_dark", "0.15 0.15 0.17 1.0"),
        ("lasius_orange", "0.95 0.39 0.10 1.0"),
        ("coxa_teal", "0.11 0.60 0.55 1.0"),
        ("femur_blue", "0.10 0.45 0.85 1.0"),
        ("servo_metal", "0.28 0.30 0.36 1.0"),
        ("foot_rubber", "0.10 0.10 0.10 1.0"),
    ]
    for mat_name, rgba in materials:
        mat_elem = ET.SubElement(robot, "material", name=mat_name)
        ET.SubElement(mat_elem, "color", rgba=rgba)
        
    # -------------------------------------------------------------
    # 1. Base Link (Chassis: Plates, Spacers, Battery & Electronics)
    # -------------------------------------------------------------
    base_link = ET.SubElement(robot, "link", name="base_link")
    
    # Mass calculation for chassis:
    # 2x carbon plates (65.4g each) + 8x aluminum spacers (20.9g each) + Pi4 + 2x PCA + UBECs + Battery (~650g)
    chassis_mass_kg = 0.06545 * 2 + 0.0209 * 8 + 0.650 # ~0.95 kg total
    chassis_com = [0.0, 0.0, 0.027] # Mid-height between plates
    chassis_inertia = {
        "ixx": 0.0035, "iyy": 0.0075, "izz": 0.0105,
        "ixy": 0.0, "ixz": 0.0, "iyz": 0.0
    }
    create_inertial(base_link, chassis_mass_kg, chassis_com, chassis_inertia)
    
    # Visual: Bottom plate
    create_mesh_visual(
        base_link,
        f"{MESH_REL_DIR}/custom/v1/parts/body_bottom.stl",
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.001, 0.001, 0.001],
        "carbon_dark"
    )
    # Visual: Top plate (at Z = 53.3 mm)
    create_mesh_visual(
        base_link,
        f"{MESH_REL_DIR}/custom/v1/parts/body_top.stl",
        [0.0, 0.0, 0.0533],
        [0.0, 0.0, 0.0],
        [0.001, 0.001, 0.001],
        "carbon_dark"
    )
    
    # Visual: 8x Aluminum Standoff Pillars (Spacers D14 x 51.3 mm, spanning Z = 2.0 .. 53.3 mm)
    spacers = [
        (0.045, 0.030), (0.045, -0.030), (-0.045, 0.030), (-0.045, -0.030),
        (0.128, 0.012), (0.128, -0.012), (-0.090, 0.0), (-0.120, 0.0)
    ]
    for sp_x, sp_y in spacers:
        create_mesh_visual(
            base_link,
            f"{MESH_REL_DIR}/custom/v1/parts/spacer_14x50.stl",
            [sp_x, sp_y, 0.002],
            [0.0, 0.0, 0.0],
            [0.001, 0.001, 0.001],
            "servo_metal"
        )
    
    # Collision: Chassis box bounding volume (267 x 177 x 55 mm)
    create_collision_box(
        base_link,
        [0.0, 0.0, 0.027],
        [0.0, 0.0, 0.0],
        [0.267, 0.177, 0.055]
    )

    # -------------------------------------------------------------
    # 2. Six Legs Configuration
    # -------------------------------------------------------------
    # Mount points and mounting yaw angles (radians)
    # Leg indices: LF, LM, LR (left) / RF, RM, RR (right)
    legs_info = [
        # id, name, x_m, y_m, z_m, yaw_rad, is_right
        ("lf", "left_front",   0.086,  0.065, 0.01725,  math.radians(45.0), False),
        ("lm", "left_middle",  0.000,  0.075, 0.01725,  math.radians(90.0), False),
        ("lr", "left_rear",   -0.086,  0.065, 0.01725,  math.radians(135.0), False),
        ("rf", "right_front",  0.086, -0.065, 0.01725, -math.radians(45.0), True),
        ("rm", "right_middle", 0.000, -0.075, 0.01725, -math.radians(90.0), True),
        ("rr", "right_rear",  -0.086, -0.065, 0.01725, -math.radians(135.0), True),
    ]

    # Segment masses & inertias from FreeCAD extraction + Servo masses:
    # Coxa: Bracket (49g) + Coxa Servo (56g) = 105g
    coxa_mass = (inertias["coxa_bracket"]["mass_g"] + 56.0) * 1e-3
    coxa_com = [0.030, 0.0, 0.0]
    coxa_inertia = {
        "ixx": inertias["coxa_bracket"]["inertia_kg_m2"]["ixx"] + 2e-5,
        "iyy": inertias["coxa_bracket"]["inertia_kg_m2"]["iyy"] + 4e-5,
        "izz": inertias["coxa_bracket"]["inertia_kg_m2"]["izz"] + 4e-5,
        "ixy": 0.0, "ixz": 0.0, "iyz": 0.0
    }

    # Femur: Body (83.9g) + Cover (4.7g) + ADS1115 (3g) + Femur Servo (56g) = 147.6g
    femur_mass = (inertias["femur_body"]["mass_g"] + inertias["femur_cover"]["mass_g"] + 3.0 + 56.0) * 1e-3
    femur_com = [femur_len * 0.5, 0.0, 0.0]
    femur_inertia = {
        "ixx": inertias["femur_body"]["inertia_kg_m2"]["ixx"] + 4e-5,
        "iyy": inertias["femur_body"]["inertia_kg_m2"]["iyy"] + 8e-5,
        "izz": inertias["femur_body"]["inertia_kg_m2"]["izz"] + 1.2e-4,
        "ixy": 0.0, "ixz": 0.0, "iyz": 0.0
    }

    # Tibia: Monolithic Tibia v2 (39.5g) + Tibia Servo (56g) + Foot Switch (5g) = 100.5g
    tibia_mass = (inertias["tibia"]["mass_g"] + 56.0 + 5.0) * 1e-3
    tibia_com = [tibia_len * 0.35, 0.0, -tibia_len * 0.35]
    tibia_inertia = {
        "ixx": inertias["tibia"]["inertia_kg_m2"]["ixx"] + 3e-5,
        "iyy": inertias["tibia"]["inertia_kg_m2"]["iyy"] + 7e-5,
        "izz": inertias["tibia"]["inertia_kg_m2"]["izz"] + 7e-5,
        "ixy": 0.0, "ixz": 0.0, "iyz": 0.0
    }

    for leg_id, leg_name, lx, ly, lz, lyaw, is_right in legs_info:
        # ---------------------------------------------------------
        # Joint 1: Coxa Joint (Yaw around Z-axis)
        # ---------------------------------------------------------
        coxa_joint_name = f"{leg_name}_coxa"
        coxa_link_name = f"link_{leg_id}_coxa"
        
        j_coxa = ET.SubElement(robot, "joint", name=coxa_joint_name, type="revolute")
        ET.SubElement(j_coxa, "parent", link="base_link")
        ET.SubElement(j_coxa, "child", link=coxa_link_name)
        ET.SubElement(j_coxa, "origin", xyz=f"{lx:.6f} {ly:.6f} {lz:.6f}", rpy=format_rpy(0.0, 0.0, lyaw))
        ET.SubElement(j_coxa, "axis", xyz="0 0 1")
        ET.SubElement(j_coxa, "limit", lower=f"{math.radians(-45.0):.6f}", upper=f"{math.radians(45.0):.6f}", effort="2.5", velocity="6.0")
        ET.SubElement(j_coxa, "dynamics", damping="0.1", friction="0.05")

        # Relative transform definitions derived directly from FreeCAD leg_assembly.FCStd:
        scale_mesh = [0.001, -0.001 if is_right else 0.001, 0.001]

        # 1. Coxa Bracket mesh relative to Coxa pivot axis (X=0, Y=0, Z=0 in link frame):
        # In FreeCAD: trans = (74.70, +/-9.00, -15.25) mm, rot = Yaw +/-180°, Roll +/-90°
        coxa_pos = [0.074700, 0.009000 if is_right else -0.009000, -0.015250]
        coxa_rpy = [-math.pi / 2.0 if is_right else math.pi / 2.0, 0.0, -math.pi if is_right else math.pi]

        link_coxa = ET.SubElement(robot, "link", name=coxa_link_name)
        create_inertial(link_coxa, coxa_mass, coxa_com, coxa_inertia)
        create_mesh_visual(
            link_coxa,
            f"{MESH_REL_DIR}/custom/v2/parts/coxa_bracket.stl",
            coxa_pos,
            coxa_rpy,
            scale_mesh,
            "coxa_teal"
        )
        create_collision_box(
            link_coxa,
            [coxa_len * 0.5, 0.0, 0.0],
            [0.0, 0.0, 0.0],
            [coxa_len, 0.050, 0.045]
        )

        # ---------------------------------------------------------
        # Joint 2: Femur Joint (Pitch around Y-axis)
        # ---------------------------------------------------------
        femur_joint_name = f"{leg_name}_femur"
        femur_link_name = f"link_{leg_id}_femur"
        femur_offset_y = 0.002500 if is_right else -0.002500
        
        j_femur = ET.SubElement(robot, "joint", name=femur_joint_name, type="revolute")
        ET.SubElement(j_femur, "parent", link=coxa_link_name)
        ET.SubElement(j_femur, "child", link=femur_link_name)
        ET.SubElement(j_femur, "origin", xyz=f"{coxa_len:.6f} {femur_offset_y:.6f} 0.000000", rpy="0 0 0")
        ET.SubElement(j_femur, "axis", xyz="0 1 0")
        ET.SubElement(j_femur, "limit", lower=f"{math.radians(-90.0):.6f}", upper=f"{math.radians(90.0):.6f}", effort="3.0", velocity="6.0")
        ET.SubElement(j_femur, "dynamics", damping="0.1", friction="0.05")

        link_femur = ET.SubElement(robot, "link", name=femur_link_name)
        create_inertial(link_femur, femur_mass, femur_com, femur_inertia)
        
        # 2. Femur mesh sits directly at the hip joint axis (X=56.5 mm), identity rotation
        femur_pos = [0.0, 0.0, 0.0]
        femur_rpy = [0.0, 0.0, 0.0]
        create_mesh_visual(
            link_femur,
            f"{MESH_REL_DIR}/custom/v2/parts/femur.stl",
            femur_pos,
            femur_rpy,
            scale_mesh,
            "femur_blue"
        )
        create_mesh_visual(
            link_femur,
            f"{MESH_REL_DIR}/custom/v2/parts/femur_cover.stl",
            femur_pos,
            femur_rpy,
            scale_mesh,
            "carbon_dark"
        )
        create_collision_box(
            link_femur,
            [femur_len * 0.5, 0.0, 0.0],
            [0.0, 0.0, 0.0],
            [femur_len, 0.045, 0.035]
        )

        # ---------------------------------------------------------
        # Joint 3: Tibia Joint (Pitch around Y-axis)
        # ---------------------------------------------------------
        tibia_joint_name = f"{leg_name}_tibia"
        tibia_link_name = f"link_{leg_id}_tibia"
        
        j_tibia = ET.SubElement(robot, "joint", name=tibia_joint_name, type="revolute")
        ET.SubElement(j_tibia, "parent", link=femur_link_name)
        ET.SubElement(j_tibia, "child", link=tibia_link_name)
        ET.SubElement(j_tibia, "origin", xyz=f"{femur_len:.6f} 0.000000 0.000000", rpy="0 0 0")
        ET.SubElement(j_tibia, "axis", xyz="0 1 0")
        ET.SubElement(j_tibia, "limit", lower=f"{math.radians(-90.0):.6f}", upper=f"{math.radians(90.0):.6f}", effort="3.0", velocity="6.0")
        ET.SubElement(j_tibia, "dynamics", damping="0.1", friction="0.05")

        link_tibia = ET.SubElement(robot, "link", name=tibia_link_name)
        create_inertial(link_tibia, tibia_mass, tibia_com, tibia_inertia)
        
        # 3. Tibia mesh relative to Knee joint axis at theta=0:
        # In FreeCAD leg_assembly: base = (0.0, +/-2.0, 0.0) mm, rot = Yaw +/-180°, Roll +/-90°
        tibia_pos = [0.0, -0.002000 if is_right else 0.002000, 0.0]
        tibia_rpy = [-math.pi / 2.0 if is_right else math.pi / 2.0, 0.0, -math.pi if is_right else math.pi]
        create_mesh_visual(
            link_tibia,
            f"{MESH_REL_DIR}/custom/v2/parts/tibia.stl",
            tibia_pos,
            tibia_rpy,
            scale_mesh,
            "lasius_orange"
        )
        create_collision_box(
            link_tibia,
            [tibia_len * 0.35, 0.0, -tibia_len * 0.35],
            [0.0, math.radians(45.0), 0.0],
            [tibia_len, 0.035, 0.025]
        )

        # ---------------------------------------------------------
        # Joint 4: Fixed Foot Contact Point (Sphere with friction)
        # ---------------------------------------------------------
        foot_joint_name = f"{leg_name}_foot_joint"
        foot_link_name = f"link_{leg_id}_foot"
        
        # Exact claw tip position relative to knee joint at theta=0:
        foot_pos = [0.123555, -0.002000 if is_right else 0.002000, -0.014602]
        
        j_foot = ET.SubElement(robot, "joint", name=foot_joint_name, type="fixed")
        ET.SubElement(j_foot, "parent", link=tibia_link_name)
        ET.SubElement(j_foot, "child", link=foot_link_name)
        ET.SubElement(j_foot, "origin", xyz=format_vec3(foot_pos), rpy="0 0 0")

        link_foot = ET.SubElement(robot, "link", name=foot_link_name)
        create_inertial(link_foot, 0.005, [0, 0, 0], {"ixx": 1e-6, "iyy": 1e-6, "izz": 1e-6})
        create_collision_sphere(link_foot, [0, 0, 0], radius=0.006) # 6mm rubber foot ball

    # -------------------------------------------------------------
    # Write and Pretty-Format XML
    # -------------------------------------------------------------
    os.makedirs(URDF_OUT_DIR, exist_ok=True)
    raw_xml = ET.tostring(robot, encoding="utf-8")
    dom = xml.dom.minidom.parseString(raw_xml)
    pretty_xml = dom.toprettyxml(indent="  ")
    
    with open(URDF_OUT_PATH, "w", encoding="utf-8") as f:
        f.write(pretty_xml)
        
    print(f"✅ Successfully exported URDF to: {URDF_OUT_PATH}")


if __name__ == "__main__":
    build_urdf()
