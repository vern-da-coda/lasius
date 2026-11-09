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


class SimOrderDispatcher:
    """Lightweight order dispatcher bridging REST and WebSocket orders directly to the simulation."""
    def __init__(self, server):
        self.server = server
        self.active_order = None
        self.order_history = []

    def dispatch(self, order):
        return self.server.handle_order(order)


class SimWebSocketServer:
    """
    Asynchronous WebSocket server bridging lasius-pilot teleoperation
    and lasius-dashboard (Three.js Digital Twin & Single-Leg Direct Drive)
    to the running PyBullet simulation.
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

        # Direct Single-Leg Control and Relaxation Overrides
        self.joint_overrides = {}    # servo_name -> angle_deg
        self.relaxed_servos = set()  # set of relaxed servo_names (force=0 in PyBullet)
        self._cancel_seq = threading.Event()
        self._seq_thread = None

        self.hexapod_layout = DEFAULT_ROBOT_LAYOUT
        self.hexapod = None
        self.dispatcher = SimOrderDispatcher(server=self)

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

    def handle_order(self, order):
        from lasius.core.control.orders import OrderResult, OrderStatus
        action_name = order.action.value if hasattr(order.action, "value") else str(order.action)
        data = {
            "action": action_name,
            "order_id": getattr(order, "order_id", "sim_order"),
            "params": getattr(order, "params", {}) or {},
        }
        res_data = self.handle_command(data)
        msg = res_data.get("message", "Executed in simulation.") if isinstance(res_data, dict) else "Executed in simulation."
        return OrderResult(
            order_id=data["order_id"],
            action=action_name,
            status=OrderStatus.COMPLETED,
            message=msg
        )

    def handle_command(self, data):
        act = data.get("action")
        if not act and "action" in data.get("params", {}):
            act = data["params"]["action"]
        params = data.get("params") or {}

        def get_p(key, default=None):
            if key in data and data[key] is not None:
                return data[key]
            return params.get(key, default)

        # 1. Single Joint / Servo Angle Direct Drive
        if act in ("set_joint_angle", "set_servo_angle"):
            servo = get_p("servo")
            val = get_p("angle")
            if servo and val is not None:
                angle = float(val)
                self.joint_overrides[str(servo)] = angle
                self.relaxed_servos.discard(str(servo))
                self.walk_x = 0.0
                self.walk_y = 0.0
                self.turn_z = 0.0
                self.updated = True
                print(f"🦵 [LegControl] {servo} = {angle:.1f}°")
                return {"status": "ok", "message": f"{servo} = {angle:.1f}°"}

        # 2. Whole Leg Direct Reference (e.g. Align Ref 0°)
        elif act == "set_leg_joints":
            leg = get_p("leg")
            if leg:
                c = float(get_p("coxa", 0.0))
                f = float(get_p("femur", 0.0))
                t = float(get_p("tibia", 0.0))
                self.joint_overrides[f"{leg}_coxa"] = c
                self.joint_overrides[f"{leg}_femur"] = f
                self.joint_overrides[f"{leg}_tibia"] = t
                self.relaxed_servos.discard(f"{leg}_coxa")
                self.relaxed_servos.discard(f"{leg}_femur")
                self.relaxed_servos.discard(f"{leg}_tibia")
                self.walk_x = 0.0
                self.walk_y = 0.0
                self.turn_z = 0.0
                self.updated = True
                print(f"🦵 [LegControl] Leg {leg} -> [{c:.1f}°, {f:.1f}°, {t:.1f}°]")
                return {"status": "ok", "message": f"Leg {leg} joints updated."}

        # 3. Stance Leg (Return single leg to neutral ground stance)
        elif act == "stance_leg":
            leg = get_p("leg")
            if leg:
                self.joint_overrides.pop(f"{leg}_coxa", None)
                self.joint_overrides.pop(f"{leg}_femur", None)
                self.joint_overrides.pop(f"{leg}_tibia", None)
                self.relaxed_servos.discard(f"{leg}_coxa")
                self.relaxed_servos.discard(f"{leg}_femur")
                self.relaxed_servos.discard(f"{leg}_tibia")
                self.updated = True
                print(f"🦵 [LegControl] Leg {leg} zurück in Stance.")
                return {"status": "ok", "message": f"Leg {leg} in stance."}

        # 4. Relax Leg (Disable motor torque on single leg -> limp)
        elif act == "relax_leg":
            leg = get_p("leg")
            if leg:
                for j in ("coxa", "femur", "tibia"):
                    s = f"{leg}_{j}"
                    self.joint_overrides.pop(s, None)
                    self.relaxed_servos.add(s)
                self.updated = True
                print(f"💤 [LegControl] Leg {leg} entspannt (force=0).")
                return {"status": "ok", "message": f"Leg {leg} relaxed."}

        # 5. Relax All Servos (Entire robot limp)
        elif act == "relax_all":
            self.joint_overrides.clear()
            for l_name in ["left_front", "left_middle", "left_rear", "right_front", "right_middle", "right_rear"]:
                for j in ("coxa", "femur", "tibia"):
                    self.relaxed_servos.add(f"{l_name}_{j}")
            self.walk_x = 0.0
            self.walk_y = 0.0
            self.turn_z = 0.0
            self.updated = True
            print("💤 [LegControl] Alle 18 Servos entspannt.")
            return {"status": "ok", "message": "All servos relaxed."}

        # 6. Neutral Stance / Reset Pose (Restore all legs to neutral ground stance)
        elif act in ("all_stance", "reset_pose"):
            self._cancel_seq.set()
            self.joint_overrides.clear()
            self.relaxed_servos.clear()
            self.walk_x = 0.0
            self.walk_y = 0.0
            self.turn_z = 0.0
            self.body_height = -80.0
            self.body_roll = 0.0
            self.body_pitch = 0.0
            self.updated = True
            print("↺ [LegControl] Alle Beine in Neutral-Stance zurückgesetzt.")
            return {"status": "ok", "message": "All legs in stance."}

        # 7. Collision Sweeps
        elif act == "sweep_joint":
            servo = get_p("servo")
            if not servo and get_p("leg") and get_p("joint"):
                servo = f"{get_p('leg')}_{get_p('joint')}"
            if servo:
                min_a = float(get_p("min_angle", -45.0))
                max_a = float(get_p("max_angle", 45.0))
                self._start_sweep(str(servo), min_a, max_a, order_id=data.get("order_id", "sweep"))
                return {"status": "ok", "message": f"Sweep {servo} gestartet."}

        # 8. Step Test Cycle
        elif act == "test_leg":
            leg = get_p("leg", "left_front")
            cycles = int(get_p("cycles", 3))
            stride = float(get_p("stride", 36.0))
            lift = float(get_p("lift", 30.0))
            self._start_test_leg(str(leg), cycles, stride, lift, order_id=data.get("order_id", "test_leg"))
            return {"status": "ok", "message": f"Step Test {leg} gestartet."}

        # 9. Calibration Live Trim
        elif act in ("calibrate_trim", "calibrate_save"):
            servo = get_p("servo")
            offset = float(get_p("offset", 0.0))
            deg_offset = offset / 10.0
            if servo:
                self.joint_overrides[str(servo)] = round(deg_offset, 2)
                self.relaxed_servos.discard(str(servo))
                self.updated = True
                print(f"🔧 [Calibrate] {servo} Trim: {offset:+.0f} µs ({deg_offset:+.1f}°)")
                return {"status": "ok", "message": f"{servo} trimmed."}

        # 10. Locomotion / Velocity Control
        elif act == "set_velocity":
            wx = float(get_p("walk_x", 0.0))
            wy = float(get_p("walk_y", 0.0))
            tz = float(get_p("turn_z", 0.0))
            # If user begins walking via stick/keyboard, clear single-leg direct drive overrides
            if wx != 0.0 or wy != 0.0 or tz != 0.0:
                if self.joint_overrides or self.relaxed_servos:
                    self.joint_overrides.clear()
                    self.relaxed_servos.clear()
                    self._cancel_seq.set()
            self.walk_x = wx
            self.walk_y = wy
            self.turn_z = tz
            self.updated = True
            return {"status": "ok"}

        # 11. Gait Type
        elif act in ("set_gait", "set_gait_type"):
            self.gait_type = str(get_p("value") or get_p("gait", "tripod")).lower()
            self.updated = True
            print(f"⚙️ [WebSocket] Gangart gewechselt zu: {self.gait_type.upper()}")
            return {"status": "ok"}

        # 12. Stop Motion
        elif act == "stop_motion":
            self.walk_x = 0.0
            self.walk_y = 0.0
            self.turn_z = 0.0
            self.updated = True
            print("⏹ [WebSocket] Stopp empfangen.")
            return {"status": "ok"}

        # 13. Speed / Height / Pose
        elif act == "set_speed":
            self.gait_speed = float(get_p("value", 1.0))
            self.updated = True
            return {"status": "ok"}
        elif act == "set_step_height":
            self.step_height = float(get_p("value", 20.0))
            self.updated = True
            return {"status": "ok"}
        elif act == "set_step_length":
            self.step_length = float(get_p("value", 35.0))
            self.updated = True
            return {"status": "ok"}
        elif act == "set_height":
            val = float(get_p("value", -80.0))
            self.body_height = max(-130.0, min(-40.0, val if val < 0 else -val))
            self.updated = True
            return {"status": "ok"}
        elif act == "set_roll":
            self.body_roll = float(get_p("value", 0.0))
            self.updated = True
            return {"status": "ok"}
        elif act == "set_pitch":
            self.body_pitch = float(get_p("value", 0.0))
            self.updated = True
            return {"status": "ok"}
        elif act == "emergency_stop":
            self._cancel_seq.set()
            self.walk_x = 0.0
            self.walk_y = 0.0
            self.turn_z = 0.0
            self.emergency_stop = True
            self.updated = True
            print("🚨 [WebSocket] Not-Aus (E-Stop) empfangen!")
            return {"status": "ok"}
        elif act == "toggle_pause":
            self.is_paused = not self.is_paused
            self.updated = True
            print(f"⏸ [WebSocket] Pause umgeschaltet: {self.is_paused}")
            return {"status": "ok"}

        return {"status": "ignored", "action": act}

    def _start_sweep(self, servo_name, min_a, max_a, order_id="sweep"):
        self._cancel_seq.set()
        time.sleep(0.02)
        self._cancel_seq.clear()
        self.broadcast_order_status(order_id, "sweep_joint", "running")

        def run_sweep():
            steps = 25
            dt = 0.030
            start_a = self.joint_overrides.get(servo_name, 0.0)
            try:
                # 1. Sweep to min_a
                for s in range(steps + 1):
                    if self._cancel_seq.is_set(): return
                    a = start_a + (s / steps) * (min_a - start_a)
                    self.joint_overrides[servo_name] = round(a, 2)
                    self.updated = True
                    time.sleep(dt)
                # 2. Sweep to max_a
                for s in range(steps * 2 + 1):
                    if self._cancel_seq.is_set(): return
                    a = min_a + (s / (steps * 2)) * (max_a - min_a)
                    self.joint_overrides[servo_name] = round(a, 2)
                    self.updated = True
                    time.sleep(dt)
                # 3. Sweep back to neutral 0.0
                for s in range(steps + 1):
                    if self._cancel_seq.is_set(): return
                    a = max_a + (s / steps) * (0.0 - max_a)
                    self.joint_overrides[servo_name] = round(a, 2)
                    self.updated = True
                    time.sleep(dt)
                self.joint_overrides.pop(servo_name, None)
                self.updated = True
                self.broadcast_order_result({"status": "completed", "action": "sweep_joint", "order_id": order_id, "message": f"Sweep {servo_name} abgeschlossen"})
            except Exception as e:
                self.broadcast_order_result({"status": "failed", "action": "sweep_joint", "order_id": order_id, "error": str(e)})

        self._seq_thread = threading.Thread(target=run_sweep, name=f"Sweep-{servo_name}", daemon=True)
        self._seq_thread.start()

    def _start_test_leg(self, leg_name, cycles=3, stride=36.0, lift=30.0, order_id="test_leg"):
        self._cancel_seq.set()
        time.sleep(0.02)
        self._cancel_seq.clear()
        self.broadcast_order_status(order_id, "test_leg", "running")

        from lasius.core.motion.kinematics import calculate_leg_ik

        def run_test():
            steps_per_cycle = 35
            dt = 0.030
            stride_half = stride / 2.0
            try:
                for _ in range(cycles):
                    if self._cancel_seq.is_set(): return
                    for s in range(steps_per_cycle):
                        if self._cancel_seq.is_set(): return
                        phi = 2.0 * math.pi * (s / steps_per_cycle)
                        y = -stride_half * math.cos(phi)
                        z = -80.0 + (lift * math.sin(phi) if math.sin(phi) > 0 else 0.0)
                        x = 150.0
                        c_deg, f_deg, t_deg = calculate_leg_ik(x, y, z, coxa_len=56.5, femur_len=100.0, tibia_len=130.0)
                        self.joint_overrides[f"{leg_name}_coxa"] = round(c_deg, 2)
                        self.joint_overrides[f"{leg_name}_femur"] = round(f_deg, 2)
                        self.joint_overrides[f"{leg_name}_tibia"] = round(t_deg, 2)
                        self.updated = True
                        time.sleep(dt)
                self.joint_overrides.pop(f"{leg_name}_coxa", None)
                self.joint_overrides.pop(f"{leg_name}_femur", None)
                self.joint_overrides.pop(f"{leg_name}_tibia", None)
                self.updated = True
                self.broadcast_order_result({"status": "completed", "action": "test_leg", "order_id": order_id, "message": f"Step Cycle {leg_name} ({cycles}x) abgeschlossen"})
            except Exception as e:
                self.broadcast_order_result({"status": "failed", "action": "test_leg", "order_id": order_id, "error": str(e)})

        self._seq_thread = threading.Thread(target=run_test, name=f"TestLeg-{leg_name}", daemon=True)
        self._seq_thread.start()

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

                    # Execute command directly in simulation
                    self.handle_command(data)
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
                        for j_name, base_deg in [("coxa", c_deg), ("femur", f_deg), ("tibia", t_deg)]:
                            servo_key = f"{prefix}_{j_name}"
                            j_idx = joint_indices[servo_key]

                            if ws_server and servo_key in ws_server.relaxed_servos:
                                # Relaxed joint: 0 motor torque (limp under gravity)
                                p.setJointMotorControl2(robot_id, j_idx, p.VELOCITY_CONTROL, targetVelocity=0, force=0.0)
                                actual_rad = p.getJointState(robot_id, j_idx)[0]
                                angles_dict[servo_key] = round(math.degrees(actual_rad), 2)
                            else:
                                # Controlled joint: check direct override from Leg Control or default gait stance
                                if ws_server and servo_key in ws_server.joint_overrides:
                                    target_deg = ws_server.joint_overrides[servo_key]
                                else:
                                    target_deg = base_deg

                                p.setJointMotorControl2(robot_id, j_idx, p.POSITION_CONTROL, targetPosition=math.radians(target_deg), force=8.0)
                                angles_dict[servo_key] = round(target_deg, 2)
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
                    for j_name, base_deg in [("coxa", c_deg), ("femur", f_deg), ("tibia", t_deg)]:
                        servo_key = f"{prefix}_{j_name}"
                        j_idx = joint_indices[servo_key]

                        if ws_server and servo_key in ws_server.relaxed_servos:
                            p.setJointMotorControl2(robot_id, j_idx, p.VELOCITY_CONTROL, targetVelocity=0, force=0.0)
                            actual_rad = p.getJointState(robot_id, j_idx)[0]
                            angles_dict[servo_key] = round(math.degrees(actual_rad), 2)
                        else:
                            if ws_server and servo_key in ws_server.joint_overrides:
                                target_deg = ws_server.joint_overrides[servo_key]
                            else:
                                target_deg = base_deg

                            p.setJointMotorControl2(robot_id, j_idx, p.POSITION_CONTROL, targetPosition=math.radians(target_deg), force=8.0)
                            angles_dict[servo_key] = round(target_deg, 2)
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
