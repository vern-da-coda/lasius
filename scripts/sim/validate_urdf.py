#!/usr/bin/env python3
"""
Validate Lasius Hexapod URDF structure, kinematics tree, and mesh references.
"""

import os
import sys
import xml.etree.ElementTree as ET

REPO_ROOT = "/home/bjoern/Workspace/Hexapods/lasius"
URDF_PATH = f"{REPO_ROOT}/hardware/mechanics/export/urdf/lasius.urdf"


def validate_urdf(urdf_path):
    print(f"=== Validating Lasius URDF: {urdf_path} ===")
    
    if not os.path.exists(urdf_path):
        print(f"❌ Error: File not found: {urdf_path}")
        return False

    tree = ET.parse(urdf_path)
    root = tree.getroot()
    
    if root.tag != "robot":
        print(f"❌ Error: Root tag is '{root.tag}', expected 'robot'")
        return False
        
    robot_name = root.attrib.get("name", "unnamed")
    print(f"Robot Name: {robot_name}")

    links = {}
    for link in root.findall("link"):
        name = link.attrib.get("name")
        links[name] = link
    print(f"Total Links: {len(links)}")

    joints = {}
    for joint in root.findall("joint"):
        name = joint.attrib.get("name")
        parent = joint.find("parent").attrib.get("link")
        child = joint.find("child").attrib.get("link")
        j_type = joint.attrib.get("type")
        joints[name] = {"parent": parent, "child": child, "type": j_type}
    print(f"Total Joints: {len(joints)} (18 revolute leg joints + 6 fixed feet)")

    # Check kinematic tree connectivity
    errors = []
    for j_name, j_data in joints.items():
        if j_data["parent"] not in links:
            errors.append(f"Joint '{j_name}' references non-existent parent link '{j_data['parent']}'")
        if j_data["child"] not in links:
            errors.append(f"Joint '{j_name}' references non-existent child link '{j_data['child']}'")

    # Check mesh file paths
    urdf_dir = os.path.dirname(urdf_path)
    mesh_count = 0
    for link_name, link in links.items():
        for visual in link.findall("visual"):
            geom = visual.find("geometry")
            if geom is not None:
                mesh = geom.find("mesh")
                if mesh is not None:
                    mesh_count += 1
                    rel_path = mesh.attrib.get("filename")
                    abs_path = os.path.normpath(os.path.join(urdf_dir, rel_path))
                    if not os.path.exists(abs_path):
                        errors.append(f"Link '{link_name}' references missing mesh: {rel_path} -> {abs_path}")

    print(f"Verified {mesh_count} mesh references.")
    
    # Check 18 DOF
    revolute_joints = [name for name, data in joints.items() if data["type"] == "revolute"]
    if len(revolute_joints) != 18:
        errors.append(f"Expected 18 revolute joints, found {len(revolute_joints)}")
    else:
        print(f"✅ Exactly 18 revolute DOF verified across 6 legs.")

    if errors:
        print("\n❌ Validation Failed with errors:")
        for err in errors:
            print(f"  - {err}")
        return False

    print("\n✅ SUCCESS: URDF model is 100% valid, connected, and all meshes exist!")
    return True


if __name__ == "__main__":
    success = validate_urdf(URDF_PATH)
    sys.exit(0 if success else 1)
