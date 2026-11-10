"""
CLI Client for Lasius Gamepad Teleoperation (`lasius.pilot.cli`).

Purpose & Role:
    Connects `GamepadController` (`/dev/input/js0`) to the `LasiusServer`
    WebSocket API (`ws://<host>:8765`) and streams atomic `set_velocity`
    commands as well as discrete button actions (Google Stadia Controller
    layout: E-Stop, Gait Switch, Speed, Body Height, Pose Reset, Pause).

Functions:
    - `run_teleop(host, port, device, profile)`: Async 33 Hz event loop reading
      joystick axes and buttons and transmitting commands over WebSocket.
    - `main()`: CLI entry point registered as `lasius-pilot` in `pyproject.toml`.
"""

import argparse
import asyncio
import json
import sys

try:
    import websockets
except ImportError:
    websockets = None

try:
    from lasius.pilot.gamepad import GamepadController, load_all_gamepad_profiles
except ImportError:
    from .gamepad import GamepadController, load_all_gamepad_profiles


async def run_teleop(
    host: str,
    port: int,
    device: str,
    profile: str = "auto",
    enable_imu: bool = True,
    imu_device: Optional[str] = None,
    invert_pitch: bool = True,
    invert_roll: bool = True,
    swap_imu_axes: bool = False,
):
    print(
        r"""
 _              _                      
| |    __ _ ___(_)_   _ ___            
| |   / _` / __| | | | / __|           
| |__| (_| \__ \ | |_| \__ \           
|_____\__,_|___/_|\__,_|___/         _ 
| | | | _____  ____ _|  _ \ ___   __| |
| |_| |/ _ \ \/ / _` | |_) / _ \ / _` |
|  _  |  __/>  < (_| |  __/ (_) | (_| |
|_| |_|\___/_/\_\__,_|_|   \___/ \__,_|
"""
    )
    controller = GamepadController(
        device_path=device,
        profile=profile,
        enable_imu=enable_imu,
        imu_device=imu_device,
        invert_pitch=invert_pitch,
        invert_roll=invert_roll,
        swap_imu_axes=swap_imu_axes,
    )
    if not controller.connect():
        print(f"[ERROR] Could not open joystick device at '{device}'. Is the controller connected?")
        print("Tip (Google Stadia Bluetooth): Hold [Y + Stadia] for 2s to pair via 'bluetoothctl'.")
        print("Tip (BlueZ BLE): Ensure 'UserspaceHID=true' is set in /etc/bluetooth/input.conf.")
        sys.exit(1)

    print(
        f"✔ Controller connected at {device}: {controller.device_name} "
        f"(Profile: {controller.active_profile_config.name} [{controller.active_profile}])"
    )
    if controller.imu and controller.imu.fd is not None:
        print(f"✔ Motion Sensors active at {controller.imu.device_path}: {controller.imu.device_name}")
        print("  [Tilt Controller] : Dynamic Body Roll (Left/Right) & Pitch (Nose Up/Down)")
    else:
        print("ℹ Motion Sensors: None detected (tilt control disabled)")

    uri = f"ws://{host}:{port}"
    print(f"Connecting to Lasius-Server at {uri}...")

    try:
        async with websockets.connect(uri, ping_interval=None) as ws:
            labels = controller.active_profile_config.labels
            print("✔ Connected to Lasius Telemetry & Command API!")
            print("-" * 68)
            print("  [Left Stick]  : Walk Forward/Back & Strafe Left/Right")
            print("  [Right Stick] : Turn Left/Right in place")
            if controller.imu and controller.imu.fd is not None:
                print("  [Tilt IMU]    : Tilt DualSense -> Body Roll & Pitch (Tare: Options)")
            print(f"  {labels.cli_gait_hint}")
            print(f"  {labels.cli_estop_hint}")
            print("  [L1 / R1]     : Speed -0.25x / +0.25x")
            print("  [D-Pad Up/Dn] : Body Height +/- 5 mm")
            print(f"  {labels.cli_pose_hint}")
            print("-" * 68)

            # Consume incoming server telemetry asynchronously to prevent socket buffer stall
            async def _drain_telemetry():
                try:
                    async for _ in ws:
                        pass
                except asyncio.CancelledError:
                    pass
                except Exception:
                    pass

            drain_task = asyncio.create_task(_drain_telemetry())

            last_cmd = {}
            last_roll = 0.0
            last_pitch = 0.0
            try:
                while True:
                    events = controller.read_events()

                    # 1. Dispatch discrete button / D-Pad actions immediately
                    for action_msg in controller.translate_events_to_actions(events):
                        if action_msg.get("action") == "reset_pose":
                            controller.tare_imu()
                        await ws.send(json.dumps(action_msg))

                    # 2. Dispatch continuous stick velocity on change
                    cmd = controller.get_locomotion_command()
                    if cmd != last_cmd:
                        last_cmd = cmd.copy()
                        msg = {
                            "type": "command",
                            "action": "set_velocity",
                            "walk_x": cmd["walk_x"],
                            "walk_y": cmd["walk_y"],
                            "turn_z": cmd["turn_z"],
                        }
                        await ws.send(json.dumps(msg))

                    # 3. Dispatch IMU tilt attitude (body roll & pitch)
                    tilt = controller.get_tilt()
                    if tilt is not None:
                        roll, pitch = tilt
                        if abs(roll - last_roll) >= 0.3 or abs(pitch - last_pitch) >= 0.3:
                            last_roll = roll
                            last_pitch = pitch
                            pose_msg = {
                                "type": "command",
                                "action": "set_pose",
                                "params": {
                                    "roll": roll,
                                    "pitch": pitch,
                                }
                            }
                            await ws.send(json.dumps(pose_msg))

                    await asyncio.sleep(0.030)  # ~33 Hz update rate
            finally:
                drain_task.cancel()
    except Exception as e:
        print(f"[ERROR] Connection to Lasius-Server failed: {e}")
    finally:
        controller.close()


def main():
    available_profiles = ["auto"] + list(load_all_gamepad_profiles().keys())
    parser = argparse.ArgumentParser(description="Lasius Gamepad Teleoperation Client (YAML-configured profiles)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Lasius Server host (default: 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8765, help="Lasius WebSocket port (default: 8765).")
    parser.add_argument("--device", type=str, default="/dev/input/js0", help="Linux joystick device (default: /dev/input/js0).")
    parser.add_argument(
        "--profile",
        type=str,
        choices=available_profiles,
        default="auto",
        help=f"Controller YAML profile from lasius.pilot/profiles/*.yaml ({', '.join(available_profiles)}).",
    )
    parser.add_argument("--no-imu", action="store_true", help="Disable DualSense IMU motion sensor tilt control.")
    parser.add_argument("--imu-device", type=str, default=None, help="Explicit IMU motion sensor device path (e.g. /dev/input/js1).")
    parser.add_argument("--no-invert-pitch", action="store_true", help="Do not invert IMU pitch axis.")
    parser.add_argument("--no-invert-roll", action="store_true", help="Do not invert IMU roll axis.")
    parser.add_argument("--swap-imu-axes", action="store_true", help="Swap IMU roll and pitch axes.")
    args = parser.parse_args()

    if websockets is None:
        print("[ERROR] 'websockets' package is required. Install via 'pip install websockets'.")
        sys.exit(1)

    try:
        asyncio.run(
            run_teleop(
                args.host,
                args.port,
                args.device,
                args.profile,
                enable_imu=not args.no_imu,
                imu_device=args.imu_device,
                invert_pitch=not args.no_invert_pitch,
                invert_roll=not args.no_invert_roll,
                swap_imu_axes=args.swap_imu_axes,
            )
        )
    except KeyboardInterrupt:
        print("\nGamepad teleoperation stopped.")


if __name__ == "__main__":
    main()
