# Lasius Hexapod – Task List, Backlog & Roadmap

This document serves as the centralized task list, roadmap, and backlog for the continuous development of the Lasius Hexapod robot (setup guides, developer workflows, and helper scripts are documented in [`README.md`](../README.md)).

---

## 1. Current Project Status (Status: October 2026)

### Mechanical Status
* **Status:** ⚠️ **Full physical locomotion temporarily paused.**
* **Root Cause:** Several 3D-printed Coxa brackets (hip joints) fractured under load and must be reprinted.
* **Consequence:** Physical walking and payload tests on desk/floor are temporarily paused until reinforced PETG reprints are mounted.

### Software & Digital Twin Status
* **Status:** ✔ **100% operational, modular, and fully simulatable.**
* **Backend (`lasius-core`):**
  * 4-layer decoupled architecture (HAL, kinematics/motion, OrderDispatcher, HTTP REST & WebSocket server).
  * 50 Hz harmonic cosine locomotion engine ($C^1$-continuous, $>5\times$ acceleration jerk reduction) with `engage=False` on startup (servos unpowered at boot) and explicit [`locomotion_active`](../software/lasius-core/src/lasius/core/robot.py) arbitration state machine.
  * Thread-safe I2C bus (`threading.RLock`) and disabled PCA9685 `_ALLCALL` bit (`0x70`) in [`driver.py`](../software/lasius-core/src/lasius/core/hardware/driver.py) in preparation for the PCA9548 I2C multiplexer.
  * Jerk-free cosine trajectory entry/exit interpolation in [`dispatcher.py`](../software/lasius-core/src/lasius/core/control/dispatcher.py): starting angles calculated from live servo positions or neutral stance height ($z = -80\,\text{mm}$), preventing sudden 0° sag.
* **Frontend (`lasius-dashboard`):**
  * Modern Vue 3 + TypeScript + Pinia Single-Page Application (SFCs, reusable `JointCard.vue`).
  * 3D Digital Twin (Three.js WebGL via `shallowRef` & zero-leak buffer updates in [`updateFanGeometry`](../software/lasius-dashboard/src/engine/lasiusGraphics.ts) / [`disposeObject3D`](../software/lasius-dashboard/src/engine/lasiusGraphics.ts)): dual-plate sandwich chassis, inward-extended coxa brackets (30 mm), unified PBR material (`#343746`), forward orientation chevron.
  * 2D CAD orthographic projections: straight vectors (`ctx.lineTo`) without curved distortion.
* **Teleoperation (`lasius-pilot`):**
  * Native support for **Google Stadia Controller** (including auto-profiling `--profile auto | stadia | standard`; see [`docs/pilot/gamepad_stadia.md`](pilot/gamepad_stadia.md)), as well as PS4/PS5, Xbox, and 8BitDo via Linux `/dev/input/js0`.
* **Automated Tests:**
  * **61 tests** (55 in `lasius-core`, 6 in `lasius-pilot`), 100% passing.

---

## 2. Task Backlog & Milestones

Because the entire system can be simulated independently of physical hardware using [`MockPWMDriver`](../software/lasius-core/src/lasius/core/hardware/driver.py) and the 3D Digital Twin, development proceeds seamlessly:

```mermaid
flowchart TD
    A["Locomotion Paused: Physical Repairs"] --> B["1. Tooling & Helper Scripts [COMPLETED]"]
    A --> C["2. Mechanics, 3D Scans & PETG Reprint"]
    A --> D["3. Dashboard & Teleoperation"]
    A --> E["4. Motion & Choreographies"]
    A --> F["5. STEMMA QT Sensors & Autonomy"]

    B --> B1["Central Scripts & Banner: dev_sim, deploy_pi, run_tests, backup, status"]
    C --> C1["3D Scans in hardware/mechanics/scans/, 4 perimeters, 40% gyroid, PETG, R 2-3mm"]
    D --> D1["Google Stadia Controller in lasius-pilot [COMPLETED]"]
    D --> D2["HTML5 Browser Gamepad API (navigator.getGamepads)"]
    D --> D3["Calibration Profile Manager & 3D Free-Roam Odometry"]
    E --> E1["Gestures: Wave Hello, Push-Ups, Crouch, Body Circle"]
    E --> E2["Arc Walking (Continuous turn trajectories)"]
    F --> F1["PCA9548 Mux (0x70) + BNO085 9-DOF IMU (0x4A) Auto-Leveling"]
    F --> F2["3x VL53L4CD ToF (0x29) + 2x INA260 Power + 6x Foot Switches (MCP23017)"]
```

### Milestone 1: Tooling, Helper Scripts & CI [✔ COMPLETED]
* **Goal:** Standardized scripts for daily development workflows (simulation, deployment, backup, health check) with centralized ASCII banner [`scripts/banner.txt`](../scripts/banner.txt).
* **Location:** [`scripts/`](../scripts/) folder (workflows documented in [`scripts/README.md`](../scripts/README.md)).

### Milestone 2: Mechanical Optimization & CAD Reconstruction (`hardware/mechanics/`)
* **3D Scanning & Reverse Engineering:**
  * Scan broken original parts (Coxa 60 mm, Femur 100 mm, Tibia 130 mm) and store mesh data in [`hardware/mechanics/scans/`](../hardware/mechanics/scans/).
  * Parametric reconstruction as clean OpenCASCADE B-Rep solids with exact inter-axis spacing (**60 mm / 100 mm / 130 mm**).
* **Fabrication & Slicing Specifications:**
  * **Material:** **PETG** (tough-elastic, will not shatter under shock loads).
  * **Print Orientation:** Print parts flat on bed so tensile/bending stresses align with continuous extrusion paths.
  * **Perimeters & Infill:** **4 perimeters (1.6 mm wall thickness)**, **40% gyroid infill**, **5 top/bottom layers (1.0 mm)**, 0.20 mm layer height at 240–245 °C with minimal part cooling (max. 20–30%) for maximum interlayer adhesion.
  * **Structural Reinforcement:** Fillet sharp 90° interior corners ($R \ge 2\text{--}3\,\text{mm}$), increase wall thickness around 25T servo horns to $\ge 3.5\text{--}4.0\,\text{mm}$, and incorporate M3 heat-set brass threaded inserts.

### Milestone 3: Dashboard & Teleoperation (100% Software)
* **Google Stadia & PS5 DualSense Profiles (`lasius-pilot` & `lasius-dashboard`) [✔ COMPLETED]:**
  * Declarative YAML profiles (`profiles/ps5.yaml`, `profiles/stadia.yaml`, `profiles/xbox.yaml`) with auto-detection and manual selector in dashboard (`GET /api/v1/gamepads`) plus browser control via `navigator.getGamepads()`.
* **Calibration Profile Management (Export / Import) [✔ COMPLETED]:**
  * Download `calibration.json` (`⬇ Export JSON`) and upload/restore (`⬆ Import JSON`) directly inside the *Leg Control* sidebar tab.
* **3D Ground Contact Indicators & Foot Trails [✔ COMPLETED]:**
  * Live ground contact glow rings under Tibia tips in stance phase ($z \le -75\,\text{mm}$) and toggleable 3D foot trajectory curves (`Trails: ON/OFF`) in the 3D viewport.
* **Kinematic Ground Coupling (`Ground Lock` vs. `Test Stand`) & Odometry Grid [✔ COMPLETED]:**
  * 2-stage least-squares support plane calculation (`fitSupportPlane` & `computeWorldKinematics`): supporting feet remain grounded ($Z = -80\,\text{mm}$) while chassis dynamically tilts, rolls, pitches, and lifts during *Push-Ups*, *Crouch*, *Body Circle*, and walking.
  * Slip-free ground propulsion: 3D floor grid scrolls and rotates synchronously under grounded stance legs (`Ground: ON`), toggleable to stationary workbench mode (`Test Stand`).
* **Rigid Body Physics Engine Bridge (MuJoCo / PyBullet via URDF/MJCF) [Backlog]:**
  * Export robot geometry as MJCF/URDF for **MuJoCo**, coupled via the 50 Hz WebSocket stream (`ws://...:8765`), to simulate full rigid-body dynamics (gravity, tipping moments, contact friction, rough terrain, servo torque limits).

### Milestone 4: Gestures, Poses & Choreographies (`lasius-core`)
* **Show Poses & Acrobatic Actions [✔ COMPLETED]:**
  * `WAVE_HELLO`: Lifts front leg and waves Tibia/Coxa back and forth while remaining 5 legs maintain balanced stance.
  * `PUSH_UPS`: Rhythmic vertical body pumping via sinusoidal interpolation ($-50\,\text{mm}$ to $-108\,\text{mm}$).
  * `BODY_CIRCLE`: Smooth 6-DOF circular body revolution coupling roll and pitch angles.
  * `CROUCH`: Low lurking stance with tilted nose (`height: -48 mm`, `pitch: -12°`).
* **Arc Walking:**
  * Continuous simultaneous translation ($X/Y$) and yaw rotation ($Z$) for smooth circular path following.

### Milestone 5: Sensors & Autonomy (STEMMA QT / Qwiic Bus)
* **I2C Multiplexer & Architecture:**
  * **Adafruit PCA9548 8-Channel STEMMA QT Multiplexer (`0x70` / `0x71`)** as central sensor hub (bus collision protection with PCA9685 `_ALLCALL` active in software).
* **IMU Driver & Auto-Leveling:**
  * **Adafruit BNO085 9-DOF Orientation IMU (`0x4A`)** with on-chip sensor fusion (quaternions, gravity vector).
  * Closed-loop PID attitude control in `lasius-core`: ground slope angles are automatically compensated by inverse body roll and pitch adjustments.
* **Current & Voltage Telemetry:**
  * **2× Adafruit INA260 (`0x41` Left, `0x44` Right)** for real-time monitoring of voltage (V), current (A), and power (W) per servo bank, including low-voltage cut-off protection.
* **ToF Obstacle Avoidance & Tactile Foot Switches:**
  * **3× Adafruit VL53L4CD ToF Distance Sensors (`0x29` on Mux channels 0, 1, 2)** for proximity sensing (1–1300 mm, front left/center/right).
  * **6× Subminiature Lever Microswitches** at Tibia tips via **Adafruit MCP23017 I2C GPIO Expander (`0x20`)** for reactive ground contact sensing on rough terrain.

### Milestone 6: Analog Servo Potentiometer Feedback (Closed-Loop Telemetry) [✔ Calibration COMPLETED]
* **Potentiometer Feedback:** Tapping internal feedback wiper of Reely NR-645 MG BB servos for direct joint angle telemetry, stall detection, and torque estimation.
* **Calibration Tooling:** Interactive CLI wizard [`scripts/bench/pot_calibration_wizard.py`](../scripts/bench/pot_calibration_wizard.py) with cosine interpolation and linear regression.
* **Calibration Findings ([`data/bench/`](../data/bench/)):** Empirically verified on Channel 15 ($R^2 = 0.9996$, sensitivity $7.59\,\text{mV}/^\circ$, zero point $1.5633\,\text{V}$ at $0^\circ$, max error $\pm 1.45^\circ$).
* **Closed-Loop Formula:** $\theta(V) = (V - 1.5633) \cdot 131.77^\circ$.
* **Hardware Integration:** 6× ADS1115 ADCs over TCA9548A multiplexer with 100 nF low-pass RC filters (see [`docs/hardware/closed_loop_plan.md`](hardware/closed_loop_plan.md)).
