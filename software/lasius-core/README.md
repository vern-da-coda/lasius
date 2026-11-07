# Lasius Hexapod: lasius-core

---

[Index](../../README.md) | [Software](../../software/README.md) | [Hardware](../../hardware/README.md) | [Docs](../../docs/README.md) | [Data](../../data/README.md) | [Scripts](../../scripts/README.md) |<br>
[lasius-core](../../software/lasius-core/README.md) | [lasius-dashboard](../../software/lasius-dashboard/README.md) | [lasius-pilot](../../software/lasius-pilot/README.md) |

---

Embedded Python locomotion engine, Hardware Abstraction Layer (HAL), 3-DOF inverse kinematics, order dispatch pipeline, and HTTP REST / WebSocket server daemon for the **Lasius** 18-DOF Hexapod robot.

## Architecture Overview

`lasius-core` implements a clean 4-layer decoupled architecture under native PEP 420 namespace `lasius.core`:

```text
src/lasius/core/
├── hardware/        # Hardware Abstraction Layer (HAL)
│   ├── driver.py    # PWMDriverProtocol, MockPWMDriver, RealPCA9685Driver (smbus2, I2C lock)
│   └── servo.py     # Servo motor model with software limits, pulse conversion & relax
├── motion/          # Kinematics & Locomotion
│   ├── kinematics.py# 3-DOF closed-form insect inverse kinematics
│   ├── leg.py       # Leg and Joint abstractions with BodySide & LegRow enums
│   └── gait.py      # 50 Hz Harmonic Cosine gait engine (OmniGait, Tripod, Ripple, Wave)
├── control/         # Command & Order Pipeline
│   ├── orders.py    # Order, OrderAction, OrderStatus, OrderPriority, OrderResult
│   └── dispatcher.py# OrderDispatcher: arbitration, async worker, watchdog, E-Stop
└── server/          # Transport & Telemetry
    ├── app.py       # LasiusServer combining HTTP REST and 50 Hz WebSocket server
    ├── handlers.py  # LasiusRestHandler (/api/v1/...) serving static Vite dist/
    └── system_stats.py # Raspberry Pi KPIs: CPU, RAM, Temp, Power Health, Wi-Fi
```

---

## Key Locomotion & Control Features

- **Harmonic Cosine 50 Hz Walking Engine & Safe State Machine:**
  - $C^1$-continuous harmonic cosine trajectories across swing and stance phases with zero-velocity liftoff and touchdown (reducing acceleration jerk by $>5\times$).
  - Continuous duty-cycle and phase morphing between Tripod, Ripple, and Wave gaits.
  - **Safe Boot & Disengagement Arbitration (`locomotion_active`):** The daemon boots with `OmniGait` attached in a disengaged, zero-PWM state (`locomotion_active = False`). Locomotion or pose orders (`SET_VELOCITY`, `SET_WALK`, `SET_TURN`, `SET_POSE`, `SET_HEIGHT`, `SET_ROLL`, `SET_PITCH`, `RESET_POSE`) automatically engage the 50 Hz gait loop, while single-joint/single-leg calibration commands (`SET_JOINT_ANGLE`, `SET_LEG_JOINTS`, `RELAX_LEG`, `RELAX_ALL`, `EMERGENCY_STOP`) and async test sequences (`TEST_LEG`, `STANCE_LEG`, `SWEEP_JOINT`) automatically disengage full-body gait actuation so isolated leg tests are never overwritten.
- **Inverse Kinematics (IK):**
  - 3-DOF insect-leg closed-form kinematics translating Cartesian foot coordinates $(x, y, z)$ into joint angles (Coxa, Femur, Tibia).
- **Thread-Safe Dual PCA9685 Hardware Drivers:**
  - Shared per-bus `threading.RLock` protecting concurrent I2C transactions between the 50 Hz locomotion loop and asynchronous `OrderDispatcher` worker threads.
  - Microsecond-accurate pulse calculation with center offsets, orientation inversion, and software safety limits.
  - PCA9685 `ALLCALL` (`0x70`) is explicitly disabled in software to prevent address conflicts with the PCA9548 I2C multiplexer.
- **Option C Robotics Overlay Pattern (`calibration.json`):**
  - `config.yaml` serves as the clean, immutable baseline geometry (git-tracked).
  - Physical servo variances (center pulse offsets, inversion flags) are persisted atomically in `calibration.json` via `.tmp` staging + `fsync` + `os.replace` to prevent corruption during brownouts.
  - `load_config()` automatically overlays `calibration.json` onto the running `HexapodConfig`.
- **Order Pipeline & Arbitration:**
  - Transport-agnostic `OrderDispatcher` supporting immediate and asynchronous tasks with priority arbitration (Priority 0..99) and a watchdog cancellation timer.
  - Instant joint actuation (`SET_JOINT_ANGLE`, `SET_LEG_JOINTS`) with sub-2ms hardware execution latency.

---

## REST Control API & OpenAPI 3.1 (`/api/v1/...`)

The server exposes a clean JSON REST API and OpenAPI 3.1.0 specification on port `8000` (see [`lasius-rest-control-api.http`](lasius-rest-control-api.http)):

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/openapi.yaml` | `GET` | OpenAPI 3.1.0 specification in YAML format |
| `/api/v1/openapi.json` | `GET` | OpenAPI 3.1.0 specification in JSON format |
| `/api/v1/status` | `GET` | Health status, control vectors, active orders, client count |
| `/api/v1/system/stats` | `GET` | Raspberry Pi KPIs: CPU %, Load Avg, RAM, SoC Temp, Power Health, Wi-Fi |
| `/api/v1/robot` | `GET` | Full kinematic geometry and joint layout definition |
| `/api/v1/calibration` | `GET` | Query runtime calibration parameters and overlay state for all 18 servos |
| `/api/v1/calibration` | `POST` | Atomically save servo calibration overlay to `calibration.json` |
| `/api/v1/calibration/trim` | `POST` | Live in-memory servo trim adjustment (immediate actuation, no disk write) |
| `/api/v1/calibration/reset` | `POST` | Reset target servo, leg, or all servos back to `config.yaml` factory defaults |
| `/api/v1/orders` | `GET` | History of recently executed orders with latency & duration |
| `/api/v1/orders/{order_id}` | `GET` | Status and telemetry of a specific order by ID |
| `/api/v1/orders` | `POST` | Submit any robot order (`SET_JOINT_ANGLE`, `SET_LEG_JOINTS`, `TEST_LEG`, etc.) |
| `/api/v1/emergency_stop` | `POST` | Immediate Priority-99 E-Stop: stops motion and relaxes all 18 servos |
| `/api/v1/relax` | `POST` | Disables PWM output across all PCA9685 channels |
| `/api/v1/server/restart` | `POST` | Safely halts motion, relaxes PWM, and restarts daemon process |
| `/api/v1/server/shutdown` | `POST` | Safely halts motion, relaxes PWM, and powers off the Raspberry Pi |
| `/api/v1/legs/{leg}/test` | `POST` | Launches isolated harmonic step cycle on target leg |
| `/api/v1/legs/{leg}/stance` | `POST` | Moves target leg smoothly into neutral standing position |

---

## Tools & CLI Entry Points

- **`run_server.py`**: Persistent robot daemon.
  ```bash
  python3 run_server.py --hardware   # on Raspberry Pi with dual PCA9685
  python3 run_server.py              # on workstation with Mock HAL simulation
  ```
- **`calibrate.py`**: Interactive CLI and 3D Digital Twin calibration tool for pulse offsets and joint orientation.
  ```bash
  python3 calibrate.py --hardware --leg left_rear
  ```
- **`check_hardware.py`**: Hardware diagnostic scanner for I2C busses (verifies `0x40` and `0x42`).
  ```bash
  python3 check_hardware.py --scan
  ```

---

## Testing

Run unit & integration tests across kinematics, gaits, drivers, orders, and REST endpoints:
```bash
pytest tests/
```
