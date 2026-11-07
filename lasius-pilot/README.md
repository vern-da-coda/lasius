# lasius-pilot

Teleoperation client and Linux joystick interface for the **Lasius** 18-DOF Hexapod robot. Provides low-latency gamepad control, radial deadzone filtering, and native support for the **Google Stadia Controller**.

---

## Features

- **Direct Linux Joystick Reader:**
  - Reads raw binary joystick events directly from `/dev/input/js0` using Python's standard `struct` and `select` modules (zero external C-bindings or third-party dependencies).
- **Google Stadia Controller Mapping:**
  - Automatic controller profiling via `/sys/class/input/jsX/device/name`.
  - **Left Stick (`Axis 0/1`):** Holonomic translation (forward, backward, lateral strafe).
  - **Right Stick Horizontal (`Axis 2`):** Continuous yaw rotation in place (vertical `Axis 3` is ignored to prevent unintended cross-axis drift).
  - **Action Buttons:**
    - `A`: Tripod gait
    - `X`: Ripple gait
    - `Y`: Wave gait
    - `B` / `Stadia Button`: Immediate Priority-99 Emergency Stop
  - **Bumpers & Triggers:**
    - `L1` / `R1`: Walking speed adjustment
  - **D-Pad (`Axis 7`):**
    - `Up` / `Down`: Chassis ground clearance / height adjustment
  - **Navigation Buttons:**
    - `Options`: Pose reset
    - `Menu`: Locomotion pause / resume
- **Streaming Client:**
  - Real-time locomotion vector dispatching to `lasius-core` via 50 Hz WebSocket stream (`ws://<robot-ip>:8765`) or REST fallback (`POST /api/v1/orders`).

---

## Detailed Specifications

For complete axis assignments, button code mappings, and controller pairing instructions, refer to:
- [Google Stadia Controller Specification & Teleoperation Guide](../docs/pilot/gamepad_stadia.md)

---

## CLI Usage

```bash
# Launch teleoperation with auto-detected gamepad profile
uv run lasius-pilot --host 192.168.0.123

# Force Google Stadia mapping:
uv run lasius-pilot --host 192.168.0.123 --profile stadia

# Connect to local simulation server:
uv run lasius-pilot --host 127.0.0.1
```

---

## Testing

Run unit tests for joystick packet decoding and radial deadzone calculations:
```bash
pytest tests/
```
