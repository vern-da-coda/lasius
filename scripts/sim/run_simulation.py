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
from http.server import ThreadingHTTPServer
import json
import math
import os
from pathlib import Path
import sys
import threading
import time

REPO_ROOT = "/home/bjoern/Workspace/Hexapods/lasius"
URDF_PATH = f"{REPO_ROOT}/hardware/mechanics/export/urdf/lasius.urdf"

# Add lasius-core package to path for kinematic and gait imports
sys.path.insert(0, os.path.join(REPO_ROOT, "software/lasius-core/src"))

DEFAULT_ROBOT_LAYOUT = {
    "body": {
        "width_front_rear": 130.0,
        "width_middle": 150.0,
        "axis_distance_longitudinal": 90.0,
        "vertices": [
            {"x": 75.0, "y": 0.0},
            {"x": 65.0, "y": 90.0},
            {"x": -65.0, "y": 90.0},
            {"x": -75.0, "y": 0.0},
            {"x": -65.0, "y": -90.0},
            {"x": 65.0, "y": -90.0},
        ],
    },
    "legs": {
        "right_middle": {"mount_point": {"x": 75.0, "y": 0.0}, "base_angle": 0.0, "coxa": {"name": "right_middle_coxa", "length": 56.5}, "femur": {"name": "right_middle_femur", "length": 100.0}, "tibia": {"name": "right_middle_tibia", "length": 130.0}},
        "right_rear": {"mount_point": {"x": 65.0, "y": 90.0}, "base_angle": 0.0, "coxa": {"name": "right_rear_coxa", "length": 56.5}, "femur": {"name": "right_rear_femur", "length": 100.0}, "tibia": {"name": "right_rear_tibia", "length": 130.0}},
        "left_rear": {"mount_point": {"x": -65.0, "y": 90.0}, "base_angle": 3.141592653589793, "coxa": {"name": "left_rear_coxa", "length": 56.5}, "femur": {"name": "left_rear_femur", "length": 100.0}, "tibia": {"name": "left_rear_tibia", "length": 130.0}},
        "left_middle": {"mount_point": {"x": -75.0, "y": 0.0}, "base_angle": 3.141592653589793, "coxa": {"name": "left_middle_coxa", "length": 56.5}, "femur": {"name": "left_middle_femur", "length": 100.0}, "tibia": {"name": "left_middle_tibia", "length": 130.0}},
        "left_front": {"mount_point": {"x": -65.0, "y": -90.0}, "base_angle": 3.141592653589793, "coxa": {"name": "left_front_coxa", "length": 56.5}, "femur": {"name": "left_front_femur", "length": 100.0}, "tibia": {"name": "left_front_tibia", "length": 130.0}},
        "right_front": {"mount_point": {"x": 65.0, "y": -90.0}, "base_angle": 0.0, "coxa": {"name": "right_front_coxa", "length": 56.5}, "femur": {"name": "right_front_femur", "length": 100.0}, "tibia": {"name": "right_front_tibia", "length": 130.0}},
    },
}


class SimWebSocketServer:
    """
    Asynchronous WebSocket server bridging lasius-pilot teleoperation
    and lasius-dashboard (Three.js Digital Twin) to the running PyBullet simulation.
    """
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        self.stop_event = None
        self.loop = None
        self.thread = None
        self.is_running = False

        self.walk_x = 0.0
        self.walk_y = 0.0
        self.turn_z = 0.0
        self.gait_type = "tripod"
        self.gait_speed = 1.0
        self.step_height = 20.0
        self.step_length = 35.0
        self.body_height = -80.0
        self.body_roll = 0.0
        self.body_pitch = 0.0
        self.is_paused = False
        self.emergency_stop = False
        self.updated = False

        self.hexapod_layout = DEFAULT_ROBOT_LAYOUT
        self.hexapod = None

        # Optional OrderDispatcher integration
        try:
            from lasius.core.control.dispatcher import OrderDispatcher
            self.dispatcher = OrderDispatcher(server=self)
        except Exception:
            self.dispatcher = None

    @property
    def state(self):
        return {
            "walk_x": self.walk_x,
            "walk_y": self.walk_y,
            "turn_z": self.turn_z,
            "gait_type": self.gait_type,
            "gait_speed": self.gait_speed,
            "step_height": self.step_height,
            "step_length": self.step_length,
            "body_height": self.body_height,
            "body_roll": self.body_roll,
            "body_pitch": self.body_pitch,
            "paused": self.is_paused,
            "emergency_stop": self.emergency_stop,
            "updated": self.updated,
        }

    def get_control_state(self):
        return {
            "is_paused": self.is_paused,
            "gait_speed": self.gait_speed,
            "step_height": self.step_height,
            "step_length": self.step_length,
            "walk_x": self.walk_x,
            "walk_y": self.walk_y,
            "turn_z": self.turn_z,
            "body_height": self.body_height,
            "body_roll": self.body_roll,
            "body_pitch": self.body_pitch,
            "gait_type": self.gait_type,
        }

    def broadcast_control_state(self):
        self.broadcast({"type": "state", "data": self.get_control_state()})

    def broadcast_order_result(self, result):
        data = result.to_dict() if hasattr(result, "to_dict") else result
        self.broadcast({"type": "order_result", "data": data})

    def broadcast_order_status(self, order_id, action, status):
        status_val = status.value if hasattr(status, "value") else str(status)
        self.broadcast({"type": "order_status", "data": {"order_id": order_id, "action": action, "status": status_val}})

    async def _handler(self, ws):
        self.clients.add(ws)
        print(f"✔ [WebSocket] Client verbunden: {ws.remote_address}")
        try:
            # Send initial layout and initial state to freshly connected client
            await ws.send(json.dumps({"type": "layout", "data": self.hexapod_layout}))
            await ws.send(json.dumps({"type": "state", "data": self.get_control_state()}))

            async for raw in ws:
                try:
                    data = json.loads(raw)
                    msg_type = data.get("type")

                    if msg_type == "get_system_stats":
                        try:
                            from lasius.core.server.system_stats import get_system_stats
                            stats = get_system_stats(connected_clients=len(self.clients))
                            await ws.send(json.dumps({"type": "system_stats", "data": stats}))
                        except Exception:
                            pass
                        continue

                    # Dispatch via OrderDispatcher if available
                    act = data.get("action")
                    if self.dispatcher and (msg_type in ("command", "order") or act):
                        try:
                            from lasius.core.control.orders import Order
                            order = Order.from_dict(data, default_source="ws")
                            self.dispatcher.dispatch(order)
                            self.updated = True
                            continue
                        except Exception:
                            pass

                    # Direct fallback processing
                    if act == "set_velocity":
                        self.walk_x = float(data.get("walk_x", 0.0))
                        self.walk_y = float(data.get("walk_y", 0.0))
                        self.turn_z = float(data.get("turn_z", 0.0))
                        self.updated = True
                    elif act in ("set_gait", "set_gait_type"):
                        self.gait_type = str(data.get("value") or data.get("gait", "tripod")).lower()
                        self.updated = True
                        print(f"⚙️ [WebSocket] Gangart gewechselt zu: {self.gait_type.upper()}")
                    elif act == "stop_motion":
                        self.walk_x = 0.0
                        self.walk_y = 0.0
                        self.turn_z = 0.0
                        self.updated = True
                        print("⏹ [WebSocket] Stopp empfangen.")
                    elif act == "set_speed":
                        self.gait_speed = float(data.get("value", 1.0))
                        self.updated = True
                    elif act == "set_step_height":
                        self.step_height = float(data.get("value", 20.0))
                        self.updated = True
                    elif act == "set_step_length":
                        self.step_length = float(data.get("value", 35.0))
                        self.updated = True
                    elif act == "set_height":
                        val = float(data.get("value", -80.0))
                        self.body_height = max(-130.0, min(-40.0, val if val < 0 else -val))
                        self.updated = True
                    elif act == "set_roll":
                        self.body_roll = float(data.get("value", 0.0))
                        self.updated = True
                    elif act == "set_pitch":
                        self.body_pitch = float(data.get("value", 0.0))
                        self.updated = True
                    elif act == "emergency_stop":
                        self.walk_x = 0.0
                        self.walk_y = 0.0
                        self.turn_z = 0.0
                        self.emergency_stop = True
                        self.updated = True
                        print("🚨 [WebSocket] Not-Aus (E-Stop) empfangen!")
                    elif act == "reset_pose":
                        self.walk_x = 0.0
                        self.walk_y = 0.0
                        self.turn_z = 0.0
                        self.body_height = -80.0
                        self.body_roll = 0.0
                        self.body_pitch = 0.0
                        self.updated = True
                        print("↺ [WebSocket] Pose auf Neutral zurückgesetzt.")
                    elif act == "toggle_pause":
                        self.is_paused = not self.is_paused
                        self.updated = True
                        print(f"⏸ [WebSocket] Pause umgeschaltet: {self.is_paused}")
                except Exception:
                    pass
        finally:
            self.clients.discard(ws)
            print("ℹ️ [WebSocket] Client getrennt.")

    async def _serve(self):
        import websockets
        self.stop_event = asyncio.Event()
        try:
            async with websockets.serve(self._handler, self.host, self.port, ping_interval=None):
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
        time.sleep(0.15)
        if self.is_running:
            print(f"✔ [WebSocket] Server aktiv auf ws://{self.host}:{self.port} (bereit für lasius-pilot & lasius-dashboard)")

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


class SimHttpServer:
    """
    Embedded HTTP server providing the REST API and hosting the Vue 3 + Three.js
    lasius-dashboard web application on port 8000.
    """
    def __init__(self, host="0.0.0.0", port=8000, ws_server=None):
        self.host = host
        self.port = port
        self.ws_server = ws_server
        self.dashboard_dir = Path(REPO_ROOT) / "software" / "lasius-dashboard" / "dist"
        self.httpd = None
        self.thread = None

    def start(self):
        if not self.dashboard_dir.is_dir():
            print(f"⚠️ [HTTP] Dashboard dist-Verzeichnis nicht gefunden ({self.dashboard_dir}).")
            return

        srv_self = self
        try:
            from lasius.core.server.handlers import LasiusRestHandler

            class Handler(LasiusRestHandler):
                server_instance = srv_self.ws_server
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, directory=str(srv_self.dashboard_dir), **kwargs)

            ThreadingHTTPServer.allow_reuse_address = True
            self.httpd = ThreadingHTTPServer((self.host, self.port), Handler)
            self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
            self.thread.start()
            print(f"✔ [HTTP] Lasius-Dashboard aktiv auf http://localhost:{self.port} (oder http://{self.host}:{self.port})")
        except Exception as e:
            print(f"⚠️ [HTTP] Server konnte nicht gestartet werden: {e}")

    def stop(self):
        if self.httpd:
            try:
                self.httpd.shutdown()
                self.httpd.server_close()
            except Exception:
                pass


def run_pybullet(gui=False, steps=240, walk=False, enable_ws=False, ws_port=8765, dashboard=True, http_port=8000):
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

    # Start WebSocket and Dashboard HTTP Servers if requested
    ws_server = None
    http_server = None
    if enable_ws:
        ws_server = SimWebSocketServer(port=ws_port)
        ws_server.start()
        if dashboard:
            http_server = SimHttpServer(port=http_port, ws_server=ws_server)
            http_server.start()

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
            print(f"  │  🌐 Teleoperation via lasius-pilot & Web-Dashboard:    │")
            print(f"  │  • WS Telemetrie:    ws://127.0.0.1:{ws_port}           │")
            if http_server and http_server.httpd:
                print(f"  │  • 3D Web-Dashboard: http://localhost:{http_port}          │")
            print(f"  │  • Pilot-Client:     uv run lasius-pilot               │")
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

                # 1. Process WebSocket commands from lasius-pilot / lasius-dashboard
                if ws_server and ws_server.updated:
                    ws_server.updated = False
                    gait.walk_x = ws_server.walk_x
                    gait.walk_y = ws_server.walk_y
                    gait.turn_z = ws_server.turn_z
                    gait.gait_speed = ws_server.gait_speed
                    gait.step_height = ws_server.step_height
                    gait.step_length = ws_server.step_length
                    gait.body_height = ws_server.body_height
                    target_gait_str = ws_server.gait_type
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
                angles_dict = {}
                for leg_id, (x, y, z) in coords_dict.items():
                    prefix = leg_map[leg_id]
                    try:
                        c_deg, f_deg, t_deg = calculate_leg_ik(x, y, z, coxa_len=56.5, femur_len=100.0, tibia_len=130.0)
                        p.setJointMotorControl2(robot_id, joint_indices[f"{prefix}_coxa"], p.POSITION_CONTROL, targetPosition=math.radians(c_deg), force=8.0)
                        p.setJointMotorControl2(robot_id, joint_indices[f"{prefix}_femur"], p.POSITION_CONTROL, targetPosition=math.radians(f_deg), force=8.0)
                        p.setJointMotorControl2(robot_id, joint_indices[f"{prefix}_tibia"], p.POSITION_CONTROL, targetPosition=math.radians(t_deg), force=8.0)
                        angles_dict[f"{prefix}_coxa"] = round(c_deg, 2)
                        angles_dict[f"{prefix}_femur"] = round(f_deg, 2)
                        angles_dict[f"{prefix}_tibia"] = round(t_deg, 2)
                    except Exception:
                        pass

                # 4. Broadcast live angles (~25 Hz) and state telemetry (~10 Hz)
                if ws_server and ws_server.clients:
                    if tick_count % 2 == 0 and angles_dict:
                        ws_server.broadcast({"type": "angles", "data": angles_dict})

                    if tick_count % 5 == 0:
                        pos, orn = p.getBasePositionAndOrientation(robot_id)
                        rpy = p.getEulerFromQuaternion(orn)
                        telemetry = {
                            "type": "state",
                            "data": {
                                "connected": True,
                                "is_paused": ws_server.is_paused,
                                "locomotion_active": bool(gait.walk_x or gait.walk_y or gait.turn_z),
                                "gait_type": gait.gait_type.value,
                                "gait_speed": gait.gait_speed,
                                "step_height": gait.step_height,
                                "step_length": gait.step_length,
                                "walk_x": gait.walk_x,
                                "walk_y": gait.walk_y,
                                "turn_z": gait.turn_z,
                                "body_height": gait.body_height,
                                "body_roll": round(math.degrees(rpy[0]), 1),
                                "body_pitch": round(math.degrees(rpy[1]), 1),
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
            if http_server:
                http_server.stop()
            if ws_server:
                ws_server.stop()
    else:
        # Headless benchmark mode
        print(f"Stepping physics simulation ({steps} steps @ 240 Hz = {steps/240.0:.2f}s, walk={walk})...")
        t0 = time.time()
        ticks = steps // physics_substeps
        for tick_idx in range(ticks):
            if ws_server and ws_server.updated:
                ws_server.updated = False
                gait.walk_x = ws_server.walk_x
                gait.walk_y = ws_server.walk_y
                gait.turn_z = ws_server.turn_z
                gait.gait_speed = ws_server.gait_speed
                gait.step_height = ws_server.step_height
                gait.step_length = ws_server.step_length
                gait.body_height = ws_server.body_height
                target_gait_str = ws_server.gait_type
                if target_gait_str in [g.value for g in GaitType]:
                    gait.gait_type = GaitType(target_gait_str)

            coords_dict = gait.tick()
            angles_dict = {}
            for leg_id, (x, y, z) in coords_dict.items():
                prefix = leg_map[leg_id]
                try:
                    c_deg, f_deg, t_deg = calculate_leg_ik(x, y, z, coxa_len=56.5, femur_len=100.0, tibia_len=130.0)
                    p.setJointMotorControl2(robot_id, joint_indices[f"{prefix}_coxa"], p.POSITION_CONTROL, targetPosition=math.radians(c_deg), force=8.0)
                    p.setJointMotorControl2(robot_id, joint_indices[f"{prefix}_femur"], p.POSITION_CONTROL, targetPosition=math.radians(f_deg), force=8.0)
                    p.setJointMotorControl2(robot_id, joint_indices[f"{prefix}_tibia"], p.POSITION_CONTROL, targetPosition=math.radians(t_deg), force=8.0)
                    angles_dict[f"{prefix}_coxa"] = round(c_deg, 2)
                    angles_dict[f"{prefix}_femur"] = round(f_deg, 2)
                    angles_dict[f"{prefix}_tibia"] = round(t_deg, 2)
                except Exception:
                    pass

            if ws_server and ws_server.clients:
                if tick_idx % 2 == 0 and angles_dict:
                    ws_server.broadcast({"type": "angles", "data": angles_dict})

                if tick_idx % 5 == 0:
                    pos, orn = p.getBasePositionAndOrientation(robot_id)
                    rpy = p.getEulerFromQuaternion(orn)
                    telemetry = {
                        "type": "state",
                        "data": {
                            "connected": True,
                            "is_paused": ws_server.is_paused,
                            "locomotion_active": bool(gait.walk_x or gait.walk_y or gait.turn_z),
                            "gait_type": gait.gait_type.value,
                            "gait_speed": gait.gait_speed,
                            "step_height": gait.step_height,
                            "step_length": gait.step_length,
                            "walk_x": gait.walk_x,
                            "walk_y": gait.walk_y,
                            "turn_z": gait.turn_z,
                            "body_height": gait.body_height,
                            "body_roll": round(math.degrees(rpy[0]), 1),
                            "body_pitch": round(math.degrees(rpy[1]), 1),
                            "position": [round(val, 3) for val in pos],
                            "rpy_deg": [round(math.degrees(a), 1) for a in rpy],
                        }
                    }
                    ws_server.broadcast(telemetry)

            for _ in range(physics_substeps):
                p.stepSimulation()

        elapsed = time.time() - t0
        print(f"Simulation completed in {elapsed:.3f}s ({steps / elapsed:.1f} steps/s).")
        if http_server:
            http_server.stop()
        if ws_server:
            ws_server.stop()

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
    parser.add_argument("--dashboard", action="store_true", default=True, help="Serve web dashboard on HTTP port (default: True with --ws/--gui)")
    parser.add_argument("--no-dashboard", dest="dashboard", action="store_false", help="Disable HTTP web dashboard server")
    parser.add_argument("--http-port", type=int, default=8000, help="HTTP port for Dashboard (default: 8000)")
    parser.add_argument("--steps", type=int, default=240, help="Number of simulation steps")
    parser.add_argument("--engine", choices=["pybullet", "mujoco"], default="pybullet", help="Physics engine")
    args = parser.parse_args()

    # Automatically enable WebSocket server in GUI mode if requested or if --ws is set
    enable_ws = args.ws or args.gui

    if args.engine == "mujoco":
        run_mujoco()
    else:
        run_pybullet(
            gui=args.gui,
            steps=args.steps,
            walk=args.walk,
            enable_ws=enable_ws,
            ws_port=args.ws_port,
            dashboard=args.dashboard,
            http_port=args.http_port
        )


if __name__ == "__main__":
    main()
