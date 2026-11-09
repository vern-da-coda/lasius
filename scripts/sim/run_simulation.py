#!/usr/bin/env python3
"""
Lasius Hexapod Physics Simulation Runner
Supports PyBullet and MuJoCo simulation engines.

Usage:
  python3 scripts/sim/run_simulation.py               # Headless physics sanity test (DIRECT mode)
  python3 scripts/sim/run_simulation.py --gui         # Interactive 3D physics GUI with ground plane
  python3 scripts/sim/run_simulation.py --engine mujoco # MuJoCo simulation
"""

import argparse
import math
import os
import sys
import time

REPO_ROOT = "/home/bjoern/Workspace/Hexapods/lasius"
URDF_PATH = f"{REPO_ROOT}/hardware/mechanics/export/urdf/lasius.urdf"


def run_pybullet(gui=False, steps=240, connect_ws=False):
    try:
        import pybullet as p
        import pybullet_data
    except ImportError:
        print("❌ Error: pybullet not installed. Run: uv pip install pybullet")
        return False

    mode = p.GUI if gui else p.DIRECT
    physics_client = p.connect(mode)
    
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)
    p.setTimeStep(1.0 / 240.0)

    # Load plane
    plane_id = p.loadURDF("plane.urdf")
    
    # Load Lasius URDF with initial drop height z = 0.12 m (120 mm)
    start_pos = [0, 0, 0.12]
    start_orientation = p.getQuaternionFromEuler([0, 0, 0])
    
    print(f"Loading URDF: {URDF_PATH}")
    robot_id = p.loadURDF(
        URDF_PATH,
        start_pos,
        start_orientation,
        flags=p.URDF_USE_INERTIA_FROM_FILE | p.URDF_USE_SELF_COLLISION
    )

    num_joints = p.getNumJoints(robot_id)
    print(f"Loaded Lasius in PyBullet with {num_joints} total joints.")

    joint_indices = {}
    for i in range(num_joints):
        info = p.getJointInfo(robot_id, i)
        j_name = info[1].decode("utf-8")
        j_type = info[2]
        if j_type == p.JOINT_REVOLUTE:
            joint_indices[j_name] = i

    print(f"Found {len(joint_indices)} revolute joints: {list(joint_indices.keys())}")

    # Set initial standing stance joint targets
    # Coxa = 0, Femur = 15 deg, Tibia = -45 deg
    femur_init = math.radians(15.0)
    tibia_init = math.radians(-45.0)
    
    for j_name, j_idx in joint_indices.items():
        target = 0.0
        if "femur" in j_name:
            target = femur_init
        elif "tibia" in j_name:
            target = tibia_init
            
        p.setJointMotorControl2(
            robot_id,
            j_idx,
            p.POSITION_CONTROL,
            targetPosition=target,
            force=2.5,
            maxVelocity=6.0
        )

    # Step simulation
    print(f"Stepping physics simulation ({steps} steps @ 240 Hz = {steps/240.0:.2f}s)...")
    t0 = time.time()
    for step in range(steps):
        p.stepSimulation()
        if gui:
            time.sleep(1.0 / 240.0)

    elapsed = time.time() - t0
    pos, orn = p.getBasePositionAndOrientation(robot_id)
    rpy = p.getEulerFromQuaternion(orn)
    print(f"Simulation completed in {elapsed:.3f}s ({steps / elapsed:.1f} steps/s).")
    print(f"Final Chassis Position: [X={pos[0]:.3f}, Y={pos[1]:.3f}, Z={pos[2]:.3f}] m")
    print(f"Final Chassis Orientation (RPY): [R={math.degrees(rpy[0]):.1f}°, P={math.degrees(rpy[1]):.1f}°, Y={math.degrees(rpy[2]):.1f}°]")

    # Check foot contacts with ground plane
    contacts = p.getContactPoints(robot_id, plane_id)
    print(f"Detected {len(contacts)} active contact points with ground plane.")

    p.disconnect()
    print("✅ PyBullet simulation verification finished successfully.")
    return True


def run_mujoco():
    try:
        import mujoco
    except ImportError:
        print("❌ Error: mujoco not installed. Run: uv pip install mujoco")
        return False
        
    print(f"Loading URDF into MuJoCo: {URDF_PATH}")
    model = mujoco.MjModel.from_xml_path(URDF_PATH)
    data = mujoco.MjData(model)
    print(f"Loaded Lasius in MuJoCo: {model.nq} generalized coordinates, {model.nv} degrees of freedom.")
    
    mujoco.mj_step(model, data)
    print("✅ MuJoCo simulation step executed successfully.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Lasius Hexapod Physics Simulation")
    parser.add_argument("--gui", action="store_true", help="Launch interactive PyBullet GUI")
    parser.add_argument("--steps", type=int, default=240, help="Number of simulation steps")
    parser.add_argument("--engine", choices=["pybullet", "mujoco"], default="pybullet", help="Physics engine")
    args = parser.parse_args()

    if args.engine == "mujoco":
        run_mujoco()
    else:
        run_pybullet(gui=args.gui, steps=args.steps)


if __name__ == "__main__":
    main()
