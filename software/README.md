# Lasius Hexapod: Software Subsystems

---

[Index](../README.md) | [Software](../software/README.md) | [Hardware](../hardware/README.md) | [Docs](../docs/README.md) | [Data](../data/README.md) | [Scripts](../scripts/README.md) |<br>
[lasius-core](lasius-core/README.md) | [lasius-dashboard](lasius-dashboard/README.md) | [lasius-pilot](lasius-pilot/README.md) |

---

The `software/` directory contains the complete software stack for the Hexapod:Lasius robot, structured as an independent monorepo workspace.

## Architecture & Submodules

```text
software/
├── lasius-core/        # Embedded Python locomotion engine, HAL & REST/WebSocket daemon
├── lasius-dashboard/   # Vue 3 + TypeScript + Three.js 3D Digital Twin & browser GUI
└── lasius-pilot/       # Gamepad teleoperation & Linux joystick client
```

### 1. [**`lasius-core/`**](lasius-core/README.md)
The embedded Python robot backend running directly on the Raspberry Pi 4 (or in local simulation mode):
- **4-Layer Architecture:** Hardware abstraction (`MockPWMDriver`, `RealPCA9685Driver`), motion engine, control pipeline (`OrderDispatcher`), and network server.
- **50 Hz Harmonic Gait:** $C^1$-continuous harmonic cosine profiles (>5x jerk reduction) across Tripod, Ripple, and Wave gaits.
- **3-DOF Inverse Kinematics:** Exact closed-form trigonometry for Coxa, Femur, and Tibia joints.
- **REST & Telemetry API:** OpenAPI 3.1 HTTP endpoints (`/api/v1/orders`, `/api/v1/status`) and 50 Hz real-time WebSocket telemetry.
- **Option C Calibration:** Atomically persisted servo calibration overlays (`calibration.json`).

### 2. [**`lasius-dashboard/`**](lasius-dashboard/README.md)
The modern single-page web interface for real-time monitoring and robot control:
- **3D Digital Twin:** High-performance WebGL visualization powered by Three.js and encapsulated with `shallowRef` to eliminate Vue proxy overhead.
- **2D CAD Projections:** Real-time top, front, and side projections with point-to-segment distance picking.
- **Studio Interface:** 4-tab control panel covering Gaits & Directions, Leg Calibration, Test Sequences, and Raspberry Pi System Telemetry.
- **Vite & Vue 3:** Built with TypeScript, Pinia state management, and compiled to static production assets in `dist/`.

### 3. [**`lasius-pilot/`**](lasius-pilot/README.md)
Low-latency teleoperation interface for physical gamepads and joysticks:
- **Direct Linux Event Reader:** Reads raw axis and button events directly from `/dev/input/js0`.
- **Auto-Profile Detection:** Automatic configuration for Google Stadia, PlayStation (PS4/PS5), Xbox, and generic HID controllers.
- **Radial Deadzone Filtering:** Prevents stick drift and maps deflection smoothly to omnidirectional walk and yaw rotation vectors.
- **Stream Dispatching:** Dispatches real-time locomotion orders via WebSocket (`ws://<robot-ip>:8765`) or REST fallback.

---

## Quickstart

### Python Workspace Installation
```bash
# From repository root:
uv sync --extra dev
# or: pip install -e software/lasius-core -e software/lasius-pilot
```

### Dashboard Frontend Compilation
```bash
cd software/lasius-dashboard
npm install
npm run build
```

### Running Tests
```bash
./scripts/dev/run_tests.sh
```
