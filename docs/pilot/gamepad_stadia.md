# Lasius Hexapod – Google Stadia Controller & Architecture Guide

> **Status:** October 2026  
> **Affected Packages:** `lasius-pilot`, `lasius-core`, `lasius-dashboard`

This document details the configuration and button mapping for the **Google Stadia Controller** (`lasius-pilot`), along with architectural and code quality improvements implemented across the monorepo.

---

## 1. Google Stadia Controller – Pairing & Setup

The Google Stadia Controller operates via **USB-C cable** or wirelessly via **Bluetooth Low Energy (BLE)** on Raspberry Pi 4 or Linux workstations. Under Linux, it exposes a native joystick interface at `/dev/input/js0`.

### 1.1 Bluetooth Pairing on Raspberry Pi (One-Time Setup)

1. **Enable BlueZ Userspace HID (Required for Stadia BLE under Linux):**
   Ensure the following option is set in `/etc/bluetooth/input.conf`:
   ```ini
   UserspaceHID=true
   ```
   Restart the Bluetooth service:
   ```bash
   sudo systemctl restart bluetooth
   ```

2. **Activate Pairing Mode on Stadia Controller:**
   - Press and hold **`Y` + `Stadia Button`** simultaneously for **2 seconds** until the status ring flashes **orange**.

3. **Pair and Connect using `bluetoothctl`:**
   ```bash
   bluetoothctl
   [bluetooth]# scan on
   # Wait until "StadiaXXXX-..." appears in scan list
   [bluetooth]# pair <MAC_ADDRESS>
   [bluetooth]# trust <MAC_ADDRESS>
   [bluetooth]# connect <MAC_ADDRESS>
   [bluetooth]# exit
   ```

4. **Verify Device Creation at `/dev/input/js0`:**
   ```bash
   ls -l /dev/input/js*
   cat /sys/class/input/js0/device/name
   ```

---

## 2. Button & Axis Mapping (`lasius-pilot`)

[`GamepadController`](../../lasius-pilot/src/lasius/pilot/gamepad.py) detects the Google Stadia Controller automatically from `/sys/class/input/js0/device/name` (`active_profile == "stadia"`), or can be launched explicitly with `--profile stadia`.

### 2.1 Analog Sticks & Directional Pad (D-Pad)

| Control Element | Linux Axis (`/dev/input/js0`) | WebSocket Command | Lasius Hexapod Function |
| :--- | :---: | :--- | :--- |
| **Left Stick (Left / Right)** | `Axis 0` (`ABS_X`) | `set_velocity` (`walk_x`) | **Lateral Strafe** (`-1.0` Left .. `+1.0` Right) |
| **Left Stick (Forward / Backward)** | `Axis 1` (`ABS_Y`) | `set_velocity` (`walk_y`) | **Forward / Backward Translation** (`+1.0` Forward .. `-1.0` Backward) |
| **Right Stick (Left / Right)** | `Axis 2` (`ABS_Z`) | `set_velocity` (`turn_z`) | **Continuous Yaw Turn in Place** (`+1.0` Left .. `-1.0` Right; vertical `Axis 3` is ignored) |
| **D-Pad Up / Down** | `Axis 7` (`ABS_HAT0Y`) | `set_height` | **Incremental Chassis Height Adjustment** (`±5 mm` per click, range `-40 mm` to `-120 mm`) |

### 2.2 Action Buttons & Safety Controls

| Stadia Controller Button | Linux Button | WebSocket Command | Lasius Hexapod Function |
| :--- | :---: | :--- | :--- |
| **Button `A`** (Bottom) | `Button 0` | `set_gait_type: "tripod"` | Switch to **Tripod Gait** (fast, dynamic, 3 legs grounded) |
| **Button `X`** (Left) | `Button 2` | `set_gait_type: "ripple"` | Switch to **Ripple Gait** (smooth, 4 legs grounded) |
| **Button `Y`** (Top) | `Button 3` | `set_gait_type: "wave"` | Switch to **Wave Gait** (maximum stability/power, 5 legs grounded) |
| **Button `B`** (Right) | `Button 1` | `emergency_stop` | **⛔ EMERGENCY STOP** (immediate motion halt & all 18 servos relaxed) |
| **Stadia Button** (Center) | `Button 8` | `emergency_stop` | **⛔ EMERGENCY STOP** (immediate motion halt & all 18 servos relaxed) |
| **Shoulder Button `L1`** | `Button 4` | `set_speed` | **Decrease Speed** (`-0.25x`, minimum `0.25x`) |
| **Shoulder Button `R1`** | `Button 5` | `set_speed` | **Increase Speed** (`+0.25x`, maximum `3.00x`) |
| **Options Button (`...`)** | `Button 6` | `reset_pose` | **Reset Body Pose** (`-80 mm` height, `0°` roll, `0°` pitch) |
| **Menu Button (`≡`)** | `Button 7` | `toggle_pause` | **Toggle Motion Pause / Resume** |

### 2.3 Launch Command

```bash
# Locally on the Raspberry Pi:
uv run lasius-pilot --profile stadia

# From remote workstation over Wi-Fi to Raspberry Pi:
uv run lasius-pilot --host 192.168.0.123 --port 8765 --profile stadia
```

---

## 3. Monorepo Architecture Highlights

### 3.1 `lasius-core` (Backend, HAL, Kinematics & Server)
- **`OmniGait` & `locomotion_active` State Machine ([`run_server.py`](../../lasius-core/run_server.py), [`robot.py`](../../lasius-core/src/lasius/core/robot.py), [`dispatcher.py`](../../lasius-core/src/lasius/core/control/dispatcher.py), [`app.py`](../../lasius-core/src/lasius/core/server/app.py)):**
  - Upon server boot, `OmniGait` initializes in a disengaged state (`engage=False`, zero velocities) and `robot.relax_all()` is executed so no servos draw idle holding current.
  - Locomotion orders (`SET_VELOCITY`, `SET_WALK`, `SET_TURN`, `SET_POSE`, `SET_HEIGHT`, `SET_ROLL`, `SET_PITCH`, `RESET_POSE`, `RESUME`) engage the 50 Hz gait loop (`locomotion_active = True`).
  - Isolated joint and leg orders (`SET_JOINT_ANGLE`, `SET_LEG_JOINTS`, `RELAX_LEG`, `RELAX_ALL`, `EMERGENCY_STOP`) and test sequences (`TEST_LEG`, `STANCE_LEG`, `SWEEP_JOINT`) disengage the full-body gait loop (`locomotion_active = False`) so single-leg calibration is never overwritten.
- **I2C Thread Safety & Bus Address Protection ([`driver.py`](../../lasius-core/src/lasius/core/hardware/driver.py)):**
  - All `RealPCA9685Driver` instances on the same I2C bus share a `threading.RLock` to eliminate race conditions between the 50 Hz loop and async `OrderDispatcher` worker threads.
  - The `_ALLCALL` bit (`0x70`) in the PCA9685 `MODE1` register is explicitly disabled to avoid address collisions with the **Adafruit PCA9548 I2C multiplexer (`0x70`)**.
- **Geometry Configuration ([`config.py`](../../lasius-core/src/lasius/core/config.py), [`config.yaml`](../../lasius-core/src/lasius/core/config.yaml)):**
  - Parameterized `default_x: 160.0` and `ground_clearance: 80.0` defined centrally in `config.geometry.default_stance`.

### 3.2 `lasius-dashboard` (Vue 3 + TypeScript + Three.js Digital Twin)
- **Key-Up Stop Detection ([`App.vue`](../../lasius-dashboard/src/App.vue)):**
  - `handleKeyUp` triggers `store.dpadStop()` immediately when movement hotkeys are released; keyboard auto-repeat events (`e.repeat`) are filtered out.
- **50 Hz WebGL Memory Optimization ([`lasiusGraphics.ts`](../../lasius-dashboard/src/engine/lasiusGraphics.ts)):**
  - `updateFanGeometry()` mutates existing `Float32BufferAttribute` arrays in-place (`needsUpdate = true`), eliminating per-frame GPU buffer reallocation.
  - `disposeObject3D()` recursively deallocates WebGL geometries and materials during scene rebuilds.

### 3.3 `lasius-pilot` (Gamepad Teleoperation)
- **Atomic Locomotion Dispatch:**
  - Dispatches `action: "set_velocity"` for simultaneous atomic updates to `walk_x`, `walk_y`, and `turn_z`, preventing lingering angular rotation upon stick release.
  - Native axis mapping for the Google Stadia Controller (`Axis 2` for `turn_z` plus dedicated action buttons).
