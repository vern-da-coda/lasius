#!/usr/bin/env python3
"""
Generate Lasius Hexapod v2 URDF (`body_assembly.FCStd`) for PyBullet / MuJoCo Physics Simulation.

Reads:
- Physical inertias, masses & geometry: hardware/mechanics/export/inertias.json
- PyBullet-ready Binary STL meshes (in link-local meters): hardware/mechanics/export/urdf/meshes/*.stl

Outputs:
- hardware/mechanics/export/urdf/lasius.urdf
"""

import json
import math
import os
import xml.dom.minidom
import xml.etree.ElementTree as ET

REPO_ROOT = "/home/bjoern/Workspace/Hexapods/lasius"
INERTIAS_PATH = f"{REPO_ROOT}/hardware/mechanics/export/inertias.json"
URDF_OUT_DIR = f"{REPO_ROOT}/hardware/mechanics/export/urdf"
URDF_OUT_PATH = f"{URDF_OUT_DIR}/lasius.urdf"
MESH_REL_DIR = "meshes"


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


def create_mesh_visual(parent_elem, mesh_file, material_name):
    """Attach a link-local meter-scaled Binary STL visual mesh (zero RPY / negative-scale artifacts!)."""
    visual = ET.SubElement(parent_elem, "visual")
    ET.SubElement(visual, "origin", xyz="0 0 0", rpy="0 0 0")
    geom = ET.SubElement(visual, "geometry")
    ET.SubElement(geom, "mesh", filename=f"{MESH_REL_DIR}/{mesh_file}", scale="1 1 1")
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
    print(f"--- Generating Lasius v2 Body Assembly URDF for PyBullet: {URDF_OUT_PATH} ---")

    with open(INERTIAS_PATH, "r") as f:
        inertias = json.load(f)

    geom = inertias["_geometry"]
    coxa_len = geom["coxa_len_m"]            # 0.0565 m
    femur_len = geom["femur_len_m"]          # 0.1000 m
    foot_pos_l = geom["foot_pos_left_m"]     # Exact compact Kufe sole center (Left)
    foot_pos_r = geom["foot_pos_right_m"]    # Exact compact Kufe sole center (Right)

    robot = ET.Element("robot", name="lasius_hexapod_v2")

    # -------------------------------------------------------------
    # Visual Materials (matching FreeCAD v2 Style Guide palette)
    # -------------------------------------------------------------
    materials = [
        ("carbon_dark",      "0.16 0.16 0.18 1.0"),
        ("petg_anthracite",  "0.22 0.24 0.27 1.0"),
        ("petg_graphite",    "0.15 0.17 0.21 1.0"),
        ("canopy_iceblue",   "0.82 0.90 0.98 0.45"),
        ("coxa_teal",        "0.15 0.65 0.45 1.0"),
        ("femur_blue",       "0.12 0.35 0.65 1.0"),
        ("tarsus_orange",    "0.92 0.45 0.10 1.0"),
        ("kufe_cyan",        "0.14 0.56 0.66 1.0"),
        ("servo_matte",      "0.14 0.15 0.18 1.0"),
        ("pcb_green",        "0.08 0.52 0.24 1.0"),
        ("pcb_red",          "0.75 0.15 0.15 1.0"),
        ("pcb_black",        "0.09 0.10 0.13 1.0"),
    ]
    for mat_name, rgba in materials:
        mat_elem = ET.SubElement(robot, "material", name=mat_name)
        ET.SubElement(mat_elem, "color", rgba=rgba)

    # -------------------------------------------------------------
    # 1. Base Link (Full v2 Monocoque Chassis from body_assembly.FCStd)
    # -------------------------------------------------------------
    base_link = ET.SubElement(robot, "link", name="base_link")

    chassis_parts_mass_g = sum(
        inertias[k]["mass_g"]
        for k in [
            "body_bottom", "body_top", "chassis_core", "chassis_belly_pan",
            "chassis_battery_hatch", "chassis_rpi_mount", "chassis_canopy",
            "rpi4_model_b", "vl53l5cx_board", "bno085_board",
        ]
    )
    # Add 2S LiPo (165g) + 2x PCA9685 + TCA9548A + UBECs + fasteners (95g)
    chassis_mass_kg = (chassis_parts_mass_g + 165.0 + 95.0) * 1e-3
    chassis_com = [0.0, 0.0, 0.032]
    chassis_inertia = {
        "ixx": 0.0042, "iyy": 0.0085, "izz": 0.0115,
        "ixy": 0.0, "ixz": 0.0, "iyz": 0.0,
    }
    create_inertial(base_link, chassis_mass_kg, chassis_com, chassis_inertia)

    create_mesh_visual(base_link, "body_bottom.stl",           "carbon_dark")
    create_mesh_visual(base_link, "body_top.stl",              "carbon_dark")
    create_mesh_visual(base_link, "chassis_core.stl",          "petg_anthracite")
    create_mesh_visual(base_link, "chassis_belly_pan.stl",     "petg_graphite")
    create_mesh_visual(base_link, "chassis_battery_hatch.stl", "petg_graphite")
    create_mesh_visual(base_link, "chassis_rpi_mount.stl",     "petg_anthracite")
    create_mesh_visual(base_link, "chassis_canopy.stl",        "canopy_iceblue")
    create_mesh_visual(base_link, "rpi4_model_b.stl",          "pcb_green")
    create_mesh_visual(base_link, "vl53l5cx_board.stl",        "pcb_red")
    create_mesh_visual(base_link, "bno085_board.stl",          "pcb_black")

    # Compact chassis collision volume (strictly inside leg mount radius to avoid false self-collision!)
    create_collision_box(
        base_link,
        [0.0, 0.0, 0.036],
        [0.0, 0.0, 0.0],
        [0.240, 0.120, 0.092],
    )

    # -------------------------------------------------------------
    # 2. Six Modular v2 Legs (Exact body_assembly.FCStd mount points)
    # -------------------------------------------------------------
    legs_info = [
        # id, name, x_m, y_m, z_m, yaw_rad, is_right
        ("lf", "left_front",    0.086,  0.065, 0.01725,  math.radians(45.0),  False),
        ("lm", "left_middle",   0.000,  0.075, 0.01725,  math.radians(90.0),  False),
        ("lr", "left_rear",    -0.086,  0.065, 0.01725,  math.radians(135.0), False),
        ("rf", "right_front",   0.086, -0.065, 0.01725, -math.radians(45.0),  True),
        ("rm", "right_middle",  0.000, -0.075, 0.01725, -math.radians(90.0),  True),
        ("rr", "right_rear",   -0.086, -0.065, 0.01725, -math.radians(135.0), True),
    ]

    # Segment masses & inertias directly from CAD extraction + real COTS servo masses
    coxa_mass = (inertias["coxa"]["mass_g"] + 2.0 * 56.0) * 1e-3  # Coxa + Coxa_Servo + Femur_Servo
    coxa_com = [0.032, 0.0, 0.004]
    coxa_inertia = {
        "ixx": inertias["coxa"]["inertia_kg_m2"]["ixx"] + 3.5e-5,
        "iyy": inertias["coxa"]["inertia_kg_m2"]["iyy"] + 6.5e-5,
        "izz": inertias["coxa"]["inertia_kg_m2"]["izz"] + 6.5e-5,
        "ixy": 0.0, "ixz": 0.0, "iyz": 0.0,
    }

    femur_mass = (inertias["femur_body"]["mass_g"] + inertias["femur_cover"]["mass_g"] + 3.0) * 1e-3
    femur_com = [femur_len * 0.50, 0.0, 0.0]
    femur_inertia = {
        "ixx": inertias["femur_body"]["inertia_kg_m2"]["ixx"] + 1.5e-5,
        "iyy": inertias["femur_body"]["inertia_kg_m2"]["iyy"] + 5.0e-5,
        "izz": inertias["femur_body"]["inertia_kg_m2"]["izz"] + 5.5e-5,
        "ixy": 0.0, "ixz": 0.0, "iyz": 0.0,
    }

    tibia_mass = (
        inertias["tibia"]["mass_g"]
        + inertias["tibia_cover"]["mass_g"]
        + inertias["tarsus"]["mass_g"]
        + inertias["tarsus_shoe"]["mass_g"]
        + 56.0   # Knee Servo (mounted inside Tibia!)
        + 4.0    # Microswitch, spring, dowel pin, 2x M2 screws
    ) * 1e-3
    tibia_com = [0.052, 0.0, 0.005]
    tibia_inertia = {
        "ixx": inertias["tibia"]["inertia_kg_m2"]["ixx"] + 3.5e-5,
        "iyy": inertias["tibia"]["inertia_kg_m2"]["iyy"] + 9.0e-5,
        "izz": inertias["tibia"]["inertia_kg_m2"]["izz"] + 9.0e-5,
        "ixy": 0.0, "ixz": 0.0, "iyz": 0.0,
    }

    total_robot_kg = chassis_mass_kg + 6.0 * (coxa_mass + femur_mass + tibia_mass + 0.002)

    for leg_id, leg_name, lx, ly, lz, lyaw, is_right in legs_info:
        side = "right" if is_right else "left"

        # ---------------------------------------------------------
        # Joint 1: Coxa Joint (Yaw around +Z)
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

        link_coxa = ET.SubElement(robot, "link", name=coxa_link_name)
        create_inertial(link_coxa, coxa_mass, coxa_com, coxa_inertia)
        create_mesh_visual(link_coxa, f"coxa_{side}.stl",        "coxa_teal")
        create_mesh_visual(link_coxa, f"coxa_servo_{side}.stl",  "servo_matte")
        create_mesh_visual(link_coxa, f"femur_servo_{side}.stl", "servo_matte")
        create_collision_box(link_coxa, [coxa_len * 0.5, 0.0, 0.0], [0.0, 0.0, 0.0], [0.044, 0.030, 0.030])

        # ---------------------------------------------------------
        # Joint 2: Femur Joint (Pitch around +Y)
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
        create_mesh_visual(link_femur, f"femur_{side}.stl",       "femur_blue")
        create_mesh_visual(link_femur, f"femur_cover_{side}.stl", "canopy_iceblue")
        create_collision_box(link_femur, [femur_len * 0.5, 0.0, 0.0], [0.0, 0.0, 0.0], [0.072, 0.026, 0.024])

        # ---------------------------------------------------------
        # Joint 3: Tibia Joint (Pitch around +Y)
        # ---------------------------------------------------------
        tibia_joint_name = f"{leg_name}_tibia"
        tibia_link_name = f"link_{leg_id}_tibia"

        j_tibia = ET.SubElement(robot, "joint", name=tibia_joint_name, type="revolute")
        ET.SubElement(j_tibia, "parent", link=femur_link_name)
        ET.SubElement(j_tibia, "child", link=tibia_link_name)
        ET.SubElement(j_tibia, "origin", xyz=f"{femur_len:.6f} 0.000000 0.000000", rpy="0 0 0")
        ET.SubElement(j_tibia, "axis", xyz="0 1 0")
        ET.SubElement(j_tibia, "limit", lower=f"{math.radians(-45.0):.6f}", upper=f"{math.radians(150.0):.6f}", effort="3.0", velocity="6.0")
        ET.SubElement(j_tibia, "dynamics", damping="0.1", friction="0.05")

        link_tibia = ET.SubElement(robot, "link", name=tibia_link_name)
        create_inertial(link_tibia, tibia_mass, tibia_com, tibia_inertia)
        create_mesh_visual(link_tibia, f"tibia_{side}.stl",       "petg_anthracite")
        create_mesh_visual(link_tibia, f"tibia_cover_{side}.stl", "petg_graphite")
        create_mesh_visual(link_tibia, f"knee_servo_{side}.stl",  "servo_matte")
        create_mesh_visual(link_tibia, f"tarsus_{side}.stl",      "tarsus_orange")
        create_mesh_visual(link_tibia, f"tarsus_shoe_{side}.stl", "kufe_cyan")
        # Slim structural collision box along Tibia shaft (well clear of Knee & Foot sphere)
        y_blade = -0.0025 if is_right else 0.0025
        create_collision_box(link_tibia, [0.070, y_blade, 0.005], [0.0, 0.0, 0.0], [0.090, 0.016, 0.022])

        # ---------------------------------------------------------
        # Joint 4: Fixed Foot Contact Point (Flush inside compact Kufe sole)
        # ---------------------------------------------------------
        foot_joint_name = f"{leg_name}_foot_joint"
        foot_link_name = f"link_{leg_id}_foot"
        foot_pos = foot_pos_r if is_right else foot_pos_l

        j_foot = ET.SubElement(robot, "joint", name=foot_joint_name, type="fixed")
        ET.SubElement(j_foot, "parent", link=tibia_link_name)
        ET.SubElement(j_foot, "child", link=foot_link_name)
        ET.SubElement(j_foot, "origin", xyz=format_vec3(foot_pos), rpy="0 0 0")

        link_foot = ET.SubElement(robot, "link", name=foot_link_name)
        create_inertial(link_foot, 0.002, [0, 0, 0], {"ixx": 1e-6, "iyy": 1e-6, "izz": 1e-6})
        # Tiny hidden visual inside Kufe sole suppresses PyBullet's white default collision-sphere proxy!
        vis_f = ET.SubElement(link_foot, "visual")
        ET.SubElement(vis_f, "origin", xyz="0 0 0", rpy="0 0 0")
        ET.SubElement(ET.SubElement(vis_f, "geometry"), "sphere", radius="0.0005")
        ET.SubElement(vis_f, "material", name="kufe_cyan")
        create_collision_sphere(link_foot, [0, 0, 0], radius=0.0040)

    # Write pretty-formatted URDF XML
    os.makedirs(URDF_OUT_DIR, exist_ok=True)
    raw_xml = ET.tostring(robot, encoding="utf-8")
    dom = xml.dom.minidom.parseString(raw_xml)
    pretty_xml = dom.toprettyxml(indent="  ")

    with open(URDF_OUT_PATH, "w", encoding="utf-8") as f:
        f.write(pretty_xml)

    print(f"✅ Successfully exported v2 Body Assembly URDF to: {URDF_OUT_PATH}")
    print(f"   Estimated Total Robot Mass: {total_robot_kg:.3f} kg (Chassis {chassis_mass_kg:.3f} kg + 6x Legs)")


if __name__ == "__main__":
    build_urdf()
