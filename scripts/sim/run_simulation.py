#!/usr/bin/env python3
"""
Lasius Hexapod Physics Simulation Runner
Supports PyBullet and MuJoCo physics engines, 50 Hz OmniGait locomotion,
and real-time WebSocket teleoperation for lasius-pilot and lasius-dashboard.

Usage:
  python3 scripts/sim/run_simulation.py               # Headless physics sanity test (DIRECT mode)
  python3 scripts/sim/run_simulation.py --gui         # Interactive 3D GUI with keyboard control
  python3 scripts/sim/run_simulation.py --gui --walk  # Interactive 3D GUI walking forward
  python3 scripts/sim/run_simulation.py --gui --ws    # Interactive 3D GUI with WebSocket server for lasius-pilot
  python3 scripts/sim/run_simulation.py --engine mujoco # MuJoCo simulation
"""

import argparse
import asyncio
import json
import math
import os
import sys
import threading
import time

REPO_ROOT = "/home/bjoern/Workspace/Hexapods/lasius"
URDF_PATH = f"{REPO_ROOT}/hardware/mechanics/export/urdf/lasius.urdf"

# Add lasius-core package to path for kinematic and gait imports
sys.path.insert(0, os.path.join(REPO_ROOT, "software/lasius-core/src"))


class SimWebSocketServer:
    """
    Lightweight asynchronous WebSocket server bridging lasius-pilot teleoperation
    and lasius-dashboard to the running PyBullet physics simulation.
    """
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        self.stop_event = None
        self.loop = None
        self.thread = None
        self.is_running = False
        self.state = {
            "walk_x": 0.0,
            "walk_y": 0.0,
            "turn_z": 0.0,
            "gait_type": "tripod",
            "gait_speed": 1.0,
            "body_height": -80.0,
            "paused": False,
            "emergency_stop": False,
            "updated": False,
        }

    async def _handler(self, ws):
        self.clients.add(ws)
        print(f"✔ [WebSocket] lasius-pilot / Telemetrie-Client verbunden ({ws.remote_address})")
        try:
            await ws.send(json.dumps({"type": "layout", "data": {}}))
            await ws.send(json.dumps({"type": "state", "data": {"status": "sim_active"}}))
            async for raw in ws:
                try:
                    data = json.loads(raw)
                    act = data.get("action")
                    if act == "set_velocity":
                        self.state["walk_x"] = float(data.get("walk_x", 0.0))
                        self.state["walk_y"] = float(data.get("walk_y", 0.0))
                        self.state["turn_z"] = float(data.get("turn_z", 0.0))
                        self.state["updated"] = True
                    elif act == "set_gait_type":
                        self.state["gait_type"] = data.get("value", "tripod")
                        self.state["updated"] = True
                        print(f"⚙️ [WebSocket] Gangart gewechselt zu: {self.state['gait_type'].upper()}")
                    elif act == "set_speed":
                        self.state["gait_speed"] = float(data.get("value", 1.0))
                        self.state["updated"] = True
                    elif act == "set_height":
                        delta = float(data.get("value", 0.0))
                        self.state["body_height"] = max(-130.0, min(-50.0, self.state["body_height"] + delta))
                        self.state["updated"] = True
                    elif act == "emergency_stop":
                        self.state["walk_x"] = 0.0
                        self.state["walk_y"] = 0.0
                        self.state["turn_z"] = 0.0
                        self.state["emergency_stop"] = True
                        self.state["updated"] = True
                        print("🚨 [WebSocket] Not-Aus (E-Stop) empfangen!")
                    elif act == "reset_pose":
                        self.state["walk_x"] = 0.0
                        self.state["walk_y"] = 0.0
                        self.state["turn_z"] = 0.0
                        self.state["body_height"] = -80.0
                        self.state["updated"] = True
                        print("↺ [WebSocket] Pose auf Neutral zurückgesetzt.")
                    elif act == "toggle_pause":
                        self.state["paused"] = not self.state["paused"]
                        self.state["updated"] = True
                except Exception as e:
                    pass
        finally:
            self.clients.discard(ws)
            print("ℹ️ [WebSocket] Client getrennt.")

    async def _serve(self):
        import websockets
        self.stop_event = asyncio.Event()
        try:
            async with websockets.serve(self._handler, self.host, self.port):
                self.is_running = True
                await self.stop_event.wait()
        except OSError as e:
            print(f"⚠️ [WebSocket] Port {self.port} konnte nicht gebunden werden ({e}). Verwende ggf. --ws-port.")
            self.is_running = False

    def start(self):
        def run_thread():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._serve())

        self.thread = threading.Thread(target=run_thread, daemon=True)
        self.thread.start()
        # Give server a moment to bind
        time.sleep(0.15)
        if self.is_running:
            print(f"✔ [WebSocket] Server aktiv auf ws://{self.host}:{self.port} (bereit für lasius-pilot)")

    def broadcast(self, data_dict):
        if not self.clients or not self.loop or not self.is_running:
            return
        msg = json.dumps(data_dict)
        for client in self.clients.copy():
            try:
                asyncio.run_coroutine_threadsafe(client.send(msg), self.loop)
            except Exception:
                pass

    def stop(self):
        if self.loop and self.stop_event:
            self.loop.call_soon_threadsafe(self.stop_event.set)


def run_pybullet(gui=False, steps=240, walk=False, enable_ws=False, ws_port=8765):
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

    # Start WebSocket Server if requested
    ws_server = None
    if enable_ws:
        ws_server = SimWebSocketServer(port=ws_port)
        ws_server.start()

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
        if enable_ws and ws_server and ws_server.is_running:
            print(f"  │  🌐 Gamepad-Steuerung via lasius-pilot (WebSocket):    │")
            print(f"  │  • Server aktiv auf ws://127.0.0.1:{ws_port}            │")
            print(f"  │  • Befehl: uv run lasius-pilot --host 127.0.0.1        │")
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
            print("ℹ️  Modus: Roboter steht bereit. Drücke Pfeil-Taste ↑ oder bewege den Gamepad-Stick.\n")

        tick_count = 0
        try:
            while p.getConnectionInfo().get("isConnected", 0):
                tick_count += 1

                # 1. Process WebSocket commands from lasius-pilot
                if ws_server and ws_server.state["updated"]:
                    ws_server.state["updated"] = False
                    gait.walk_x = ws_server.state["walk_x"]
                    gait.walk_y = ws_server.state["walk_y"]
                    gait.turn_z = ws_server.state["turn_z"]
                    gait.gait_speed = ws_server.state["gait_speed"]
                    gait.body_height = ws_server.state["body_height"]
                    target_gait_str = ws_server.state["gait_type"]
                    if target_gait_str in [g.value for g in GaitType]:
                        gait.gait_type = GaitType(target_gait_str)

                # 2. Process local keyboard events
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

                # 3. Compute next foot coordinates via Gait engine
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

                # 4. Broadcast live telemetry to connected WebSocket clients (10 Hz rate)
                if ws_server and ws_server.clients and tick_count % 5 == 0:
                    pos, orn = p.getBasePositionAndOrientation(robot_id)
                    rpy = p.getEulerFromQuaternion(orn)
                    telemetry = {
                        "type": "state",
                        "data": {
                            "connected": True,
                            "locomotion_active": bool(gait.walk_x or gait.walk_y or gait.turn_z),
                            "gait_type": gait.gait_type.value,
                            "speed": gait.gait_speed,
                            "body_height": gait.body_height,
                            "position": [round(val, 3) for val in pos],
                            "rpy_deg": [round(math.degrees(a), 1) for a in rpy],
                        }
                    }
                    ws_server.broadcast(telemetry)

                for _ in range(physics_substeps):
                    p.stepSimulation()
                    time.sleep(1.0 / 240.0)
        except (KeyboardInterrupt, Exception):
            pass
        finally:
            if ws_server:
                ws_server.stop()
    else:
        # Headless benchmark mode
        print(f"Stepping physics simulation ({steps} steps @ 240 Hz = {steps/240.0:.2f}s, walk={walk})...")
        t0 = time.time()
        ticks = steps // physics_substeps
        for tick_idx in range(ticks):
            if ws_server and ws_server.state["updated"]:
                ws_server.state["updated"] = False
                gait.walk_x = ws_server.state["walk_x"]
                gait.walk_y = ws_server.state["walk_y"]
                gait.turn_z = ws_server.state["turn_z"]
                gait.gait_speed = ws_server.state["gait_speed"]
                gait.body_height = ws_server.state["body_height"]
                target_gait_str = ws_server.state["gait_type"]
                if target_gait_str in [g.value for g in GaitType]:
                    gait.gait_type = GaitType(target_gait_str)

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

            if ws_server and ws_server.clients and tick_idx % 5 == 0:
                pos, orn = p.getBasePositionAndOrientation(robot_id)
                rpy = p.getEulerFromQuaternion(orn)
                telemetry = {
                    "type": "state",
                    "data": {
                        "connected": True,
                        "locomotion_active": bool(gait.walk_x or gait.walk_y or gait.turn_z),
                        "gait_type": gait.gait_type.value,
                        "speed": gait.gait_speed,
                        "body_height": gait.body_height,
                        "position": [round(val, 3) for val in pos],
                        "rpy_deg": [round(math.degrees(a), 1) for a in rpy],
                    }
                }
                ws_server.broadcast(telemetry)

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
    parser.add_argument("--ws", action="store_true", help="Start WebSocket server for lasius-pilot teleoperation")
    parser.add_argument("--ws-port", type=int, default=8765, help="WebSocket port (default: 8765)")
    parser.add_argument("--steps", type=int, default=240, help="Number of simulation steps")
    parser.add_argument("--engine", choices=["pybullet", "mujoco"], default="pybullet", help="Physics engine")
    args = parser.parse_args()

    # Automatically enable WebSocket server in GUI mode if requested or if --ws is set
    enable_ws = args.ws or args.gui

    if args.engine == "mujoco":
        run_mujoco()
    else:
        run_pybullet(gui=args.gui, steps=args.steps, walk=args.walk, enable_ws=enable_ws, ws_port=args.ws_port)


if __name__ == "__main__":
    main()
