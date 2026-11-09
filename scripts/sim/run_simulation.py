#!/usr/bin/env python3
"""
Lasius Hexapod Physics Simulation Runner
Supports PyBullet and MuJoCo simulation engines with 50 Hz OmniGait locomotion.

Usage:
  python3 scripts/sim/run_simulation.py               # Headless physics sanity test (DIRECT mode)
  python3 scripts/sim/run_simulation.py --gui         # Interactive 3D physics GUI with keyboard control
  python3 scripts/sim/run_simulation.py --gui --walk  # Interactive 3D physics GUI walking forward
  python3 scripts/sim/run_simulation.py --engine mujoco # MuJoCo simulation
"""

import argparse
import math
import os
import sys
import time

REPO_ROOT = "/home/bjoern/Workspace/Hexapods/lasius"
URDF_PATH = f"{REPO_ROOT}/hardware/mechanics/export/urdf/lasius.urdf"

# Add lasius-core package to path for kinematic and gait imports
sys.path.insert(0, os.path.join(REPO_ROOT, "software/lasius-core/src"))


def run_pybullet(gui=False, steps=240, walk=False):
    try:
        import pybullet as p
        import pybullet_data
    except ImportError:
        print("❌ Error: pybullet not installed. Run: uv pip install pybullet")
        return False

    try:
        from lasius.core.motion.gait import OmniGait, GaitType, LegIdentifier
        from lasius.core.motion.kinematics import calculate_leg_ik
    except ImportError as e:
        print(f"❌ Error importing lasius-core motion modules: {e}")
        return False

    mode = p.GUI if gui else p.DIRECT
    physics_client = p.connect(mode)
    
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)
    p.setTimeStep(1.0 / 240.0)

    # Load plane with realistic friction
    plane_id = p.loadURDF("plane.urdf")
    p.changeDynamics(plane_id, -1, lateralFriction=1.2)
    
    # Load Lasius URDF with initial drop height z = 0.16 m (160 mm)
    start_pos = [0, 0, 0.16]
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
        # High friction on foot tips
        p.changeDynamics(robot_id, i, lateralFriction=1.5)

    print(f"Found {len(joint_indices)} revolute joints: {list(joint_indices.keys())}")

    # Set up OmniGait engine (50 Hz gait update rate)
    init_walk_y = 1.0 if walk else 0.0
    gait = OmniGait(
        gait_type=GaitType.TRIPOD,
        walk_y=init_walk_y,
        step_length=35.0,
        step_height=20.0,
        gait_speed=1.0
    )

    leg_map = {
        LegIdentifier.LEFT_FRONT: "left_front",
        LegIdentifier.LEFT_MIDDLE: "left_middle",
        LegIdentifier.LEFT_REAR: "left_rear",
        LegIdentifier.RIGHT_FRONT: "right_front",
        LegIdentifier.RIGHT_MIDDLE: "right_middle",
        LegIdentifier.RIGHT_REAR: "right_rear",
    }

    # Initialize robot in neutral standing stance
    coords_dict = gait.tick()
    for leg_id, (x, y, z) in coords_dict.items():
        prefix = leg_map[leg_id]
        c_deg, f_deg, t_deg = calculate_leg_ik(x, y, z, coxa_len=56.5, femur_len=100.0, tibia_len=130.0)
        p.resetJointState(robot_id, joint_indices[f"{prefix}_coxa"], math.radians(c_deg))
        p.resetJointState(robot_id, joint_indices[f"{prefix}_femur"], math.radians(f_deg))
        p.resetJointState(robot_id, joint_indices[f"{prefix}_tibia"], math.radians(t_deg))

    # Simulation loop timing: 50 Hz gait ticks, 240 Hz physics (approx. 5 substeps per tick)
    physics_substeps = 240 // 50

    if gui:
        print("\n🎮 Interactive PyBullet 3D Locomotion Simulation:")
        print("  ┌────────────────────────────────────────────────────────┐")
        print("  │  Tastatur-Steuerung:                                   │")
        print("  │  • ↑ (Pfeil oben):   Vorwärts laufen                   │")
        print("  │  • ↓ (Pfeil unten):  Rückwärts laufen                  │")
        print("  │  • ← (Pfeil links):  Links drehen                      │")
        print("  │  • → (Pfeil rechts): Rechts drehen                     │")
        print("  │  • Leertaste:        Stopp / Neutraler Stand           │")
        print("  │  • T / R / W:        Tripod / Ripple / Wave Gangart    │")
        print("  │                                                        │")
        print("  │  Maus-Kamerasteuerung:                                 │")
        print("  │  • Kamera drehen:    Strg + Linke Maustaste            │")
        print("  │  • Verschieben:      Strg + Mittlere Maustaste         │")
        print("  │  • Zoom:             Mausrad                           │")
        print("  │  • Beenden:          Fenster schließen oder Strg+C     │")
        print("  └────────────────────────────────────────────────────────┘\n")
        if walk:
            print("🚀 Modus: Roboter läuft automatisch im Tripod-Gang vorwärts!\n")
        else:
            print("ℹ️  Modus: Roboter steht bereit. Drücke Pfeil-Taste ↑ um vorwärts zu laufen.\n")

        try:
            while p.getConnectionInfo().get("isConnected", 0):
                # Process keyboard events
                keys = p.getKeyboardEvents()
                if keys:
                    if p.B3G_UP_ARROW in keys and (keys[p.B3G_UP_ARROW] & p.KEY_WAS_TRIGGERED):
                        gait.walk_y = 1.0
                        gait.turn_z = 0.0
                        print("▶ Befehl: Vorwärts laufen")
                    elif p.B3G_DOWN_ARROW in keys and (keys[p.B3G_DOWN_ARROW] & p.KEY_WAS_TRIGGERED):
                        gait.walk_y = -1.0
                        gait.turn_z = 0.0
                        print("◀ Befehl: Rückwärts laufen")
                    elif p.B3G_LEFT_ARROW in keys and (keys[p.B3G_LEFT_ARROW] & p.KEY_WAS_TRIGGERED):
                        gait.turn_z = 1.0
                        gait.walk_y = 0.0
                        print("↺ Befehl: Links drehen")
                    elif p.B3G_RIGHT_ARROW in keys and (keys[p.B3G_RIGHT_ARROW] & p.KEY_WAS_TRIGGERED):
                        gait.turn_z = -1.0
                        gait.walk_y = 0.0
                        print("↻ Befehl: Rechts drehen")
                    elif ord(" ") in keys and (keys[ord(" ")] & p.KEY_WAS_TRIGGERED):
                        gait.walk_y = 0.0
                        gait.walk_x = 0.0
                        gait.turn_z = 0.0
                        print("⏹ Befehl: Stopp / Neutraler Stand")
                    elif (ord("t") in keys or ord("T") in keys) and ((keys.get(ord("t"), 0) | keys.get(ord("T"), 0)) & p.KEY_WAS_TRIGGERED):
                        gait.gait_type = GaitType.TRIPOD
                        print("⚙️ Gangart: Tripod Gait (schnell, 3 Beine gleichzeitig)")
                    elif (ord("r") in keys or ord("R") in keys) and ((keys.get(ord("r"), 0) | keys.get(ord("R"), 0)) & p.KEY_WAS_TRIGGERED):
                        gait.gait_type = GaitType.RIPPLE
                        print("⚙️ Gangart: Ripple Gait (flüssig, 2 Beine gleichzeitig)")
                    elif (ord("w") in keys or ord("W") in keys) and ((keys.get(ord("w"), 0) | keys.get(ord("W"), 0)) & p.KEY_WAS_TRIGGERED):
                        gait.gait_type = GaitType.WAVE
                        print("⚙️ Gangart: Wave Gait (statuarisch, 1 Bein gleichzeitig)")

                # Compute next foot coordinates via Gait engine
                coords_dict = gait.tick()
                for leg_id, (x, y, z) in coords_dict.items():
                    prefix = leg_map[leg_id]
                    try:
                        c_deg, f_deg, t_deg = calculate_leg_ik(x, y, z, coxa_len=56.5, femur_len=100.0, tibia_len=130.0)
                        p.setJointMotorControl2(robot_id, joint_indices[f"{prefix}_coxa"], p.POSITION_CONTROL, targetPosition=math.radians(c_deg), force=8.0)
                        p.setJointMotorControl2(robot_id, joint_indices[f"{prefix}_femur"], p.POSITION_CONTROL, targetPosition=math.radians(f_deg), force=8.0)
                        p.setJointMotorControl2(robot_id, joint_indices[f"{prefix}_tibia"], p.POSITION_CONTROL, targetPosition=math.radians(t_deg), force=8.0)
                    except Exception:
                        pass

                for _ in range(physics_substeps):
                    p.stepSimulation()
                    time.sleep(1.0 / 240.0)
        except (KeyboardInterrupt, Exception):
            pass
    else:
        # Headless benchmark mode
        print(f"Stepping physics simulation ({steps} steps @ 240 Hz = {steps/240.0:.2f}s, walk={walk})...")
        t0 = time.time()
        ticks = steps // physics_substeps
        for _ in range(ticks):
            coords_dict = gait.tick()
            for leg_id, (x, y, z) in coords_dict.items():
                prefix = leg_map[leg_id]
                try:
                    c_deg, f_deg, t_deg = calculate_leg_ik(x, y, z, coxa_len=56.5, femur_len=100.0, tibia_len=130.0)
                    p.setJointMotorControl2(robot_id, joint_indices[f"{prefix}_coxa"], p.POSITION_CONTROL, targetPosition=math.radians(c_deg), force=8.0)
                    p.setJointMotorControl2(robot_id, joint_indices[f"{prefix}_femur"], p.POSITION_CONTROL, targetPosition=math.radians(f_deg), force=8.0)
                    p.setJointMotorControl2(robot_id, joint_indices[f"{prefix}_tibia"], p.POSITION_CONTROL, targetPosition=math.radians(t_deg), force=8.0)
                except Exception:
                    pass
            for _ in range(physics_substeps):
                p.stepSimulation()

        elapsed = time.time() - t0
        print(f"Simulation completed in {elapsed:.3f}s ({steps / elapsed:.1f} steps/s).")

    if p.isConnected():
        pos, orn = p.getBasePositionAndOrientation(robot_id)
        rpy = p.getEulerFromQuaternion(orn)
        print(f"Final Chassis Position: [X={pos[0]:.3f}, Y={pos[1]:.3f}, Z={pos[2]:.3f}] m")
        print(f"Final Chassis Orientation (RPY): [R={math.degrees(rpy[0]):.1f}°, P={math.degrees(rpy[1]):.1f}°, Y={math.degrees(rpy[2]):.1f}°]")

        contacts = p.getContactPoints(robot_id, plane_id)
        print(f"Detected {len(contacts)} active contact points with ground plane.")
        p.disconnect()
    print("✅ PyBullet simulation finished successfully.")
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
    parser.add_argument("--walk", action="store_true", help="Start simulation with active walking gait")
    parser.add_argument("--steps", type=int, default=240, help="Number of simulation steps")
    parser.add_argument("--engine", choices=["pybullet", "mujoco"], default="pybullet", help="Physics engine")
    args = parser.parse_args()

    if args.engine == "mujoco":
        run_mujoco()
    else:
        run_pybullet(gui=args.gui, steps=args.steps, walk=args.walk)


if __name__ == "__main__":
    main()
