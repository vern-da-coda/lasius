# Lasius Hexapod Control Software
Modular control software, 3D Digital Twin, REST/WebSocket control API, and teleoperation system for an 18-DOF, 6-legged (hexapod) biomimetic walking robot.

<p align="center">
  <img src="hardware/mechanics/drawings/renders/body_assembly.png" alt="Lasius Hexapod Full Body Assembly" width="750">
</p>

## Repository Structure (Monorepo)

The repository is organized into four main functional pillars:

```text
lasius
├── lasius-core/                     # Embedded Python backend & locomotion engine
│   ├── src/lasius/core/             # 4-Layer Architecture (hardware, motion, control, server)
│   │   ├── hardware/                # Thread-safe Dual PCA9685 I2C driver & servo models
│   │   ├── motion/                  # 3-DOF closed-form IK & 50 Hz Harmonic Gait engine
│   │   ├── control/                 # Command pipeline, OrderDispatcher & arbitration
│   │   └── server/                  # HTTP REST, WebSocket server & system_stats.py
│   ├── tests/                       # Unit & integration tests (Kinematics, Gaits, Drivers, Orders, REST)
│   ├── openapi.yaml                 # Canonical OpenAPI 3.1.0 specification
│   ├── lasius-rest-control-api.http # PyCharm / IntelliJ / VS Code REST Client test collection
│   ├── lasius.service               # Systemd daemon autostart unit for Raspberry Pi
│   ├── calibrate.py                 # Interactive CLI & 3D calibration tool
│   ├── check_hardware.py            # Hardware diagnostic & I2C bus scanner
│   ├── run_server.py                # Persistent HTTP REST & WebSocket telemetry daemon
│   └── pyproject.toml               # Core package dependencies & CLI entry point (lasius-server)
├── lasius-dashboard/                # Vue 3 + TypeScript + Pinia 3D Digital Twin & browser interface
│   ├── src/                         # Modular Single-File Components (<script setup lang="ts">)
│   │   ├── components/              # AppHeader, DigitalTwin3D, OrthogonalStrip2D, sidebar tabs & JointCard.vue
│   │   ├── engine/                  # Three.js LasiusGraphicsEngine & 2D CAD projection math
│   │   ├── stores/                  # Pinia dashboardStore (WebSocket telemetry & order dispatch)
│   │   ├── types/                   # Shared TypeScript interfaces & domain types
│   │   └── styles/                  # Cleaned CSS design system & typography
│   ├── dist/                        # Production assets served statically by robot daemon
│   ├── index.html                   # Single-page application root
│   ├── package.json                 # Vue 3, Pinia, TypeScript, Three.js & Vite toolchain
│   └── vite.config.ts               # Vite configuration (relative base URL)
├── lasius-pilot/                    # Teleoperation client
│   ├── src/lasius/pilot/            # Gamepad controller (/dev/input/js0 event reader) & CLI
│   ├── tests/                       # Controller unit tests
│   ├── cli.py                       # Bluetooth gamepad CLI launcher
│   └── pyproject.toml               # Pilot package dependencies & CLI entry point (lasius-pilot)
├── hardware/                        # Physical robot engineering (Mechanics & Electronics)
│   ├── mechanics/                   # Mechanical CAD & digital fabrication
│   │   ├── models/                  # Parametric FreeCAD models (.FCStd, hardware/, legacy_scad/)
│   │   ├── export/                  # Digital fabrication exports (step/, stl/, dxf/)
│   │   ├── drawings/                # Renders (.png) & 1:1 fabrication templates (.svg)
│   │   ├── scripts/                 # FreeCAD model generator & scan calibration scripts
│   │   └── scans/                   # 1200 DPI reference flatbed scans
│   └── electronics/                 # Electrical wiring & harness planning
│       └── wiring/                  # WireViz definitions (.yml), renders (.svg, .png), & BOMs (.tsv)
├── docs/                            # Central project specifications & architectural guides
│   ├── hardware/                    # Hardware decisions & closed-loop feedback wiring plan
│   ├── pilot/                       # Gamepad controller mapping (Google Stadia)
│   └── roadmap.md                   # Project backlog, task list & feature roadmap
├── data/                            # Runtime telemetry & calibration snapshots
│   ├── bench/                       # Experimental potentiometer benchmark measurements
│   └── calibration_backups/         # Local timestamped calibration snapshots (.gitignore)
├── scripts/                         # Development, simulation, deployment & bench helper tools
│   ├── dev/                         # Local development & testing (dev_sim.sh, run_tests.sh)
│   ├── deploy/                      # Raspberry Pi deployment & status (deploy_pi.sh, status_pi.sh)
│   ├── bench/                       # Potentiometer calibration wizard & servo sweeps
│   └── banner.txt                   # Shared ASCII CLI header banner
├── pyproject.toml                   # Top-level workspace & dev dependencies (pytest, wireviz)
└── uv.lock                          # Pinned dependency lockfile
```

---

## Physical & Hardware Specifications

All physical dimensions and servo configurations are maintained in [`lasius-core/src/lasius/core/config.yaml`](lasius-core/src/lasius/core/config.yaml):

- **Leg Limb Lengths (inter-axis distances):**
  - **Coxa:** 6 cm (60 mm) — bracket extends an additional 3 cm (30 mm) inwards from the vertical pivot axis towards the chassis interior
  - **Femur:** 10 cm (100 mm)
  - **Tibia:** 13 cm (130 mm)
- **Chassis Dimensions & Dual-Plate Construction:**
  - **Dual Sandwich Plates:** Two distinct 2 mm chassis plates (carbon fiber / aluminum) sandwiching and supporting the 6 coxa rotation axes from top and bottom.
  - **Plate Clearance & Standoffs:** 51.3 mm internal vertical gap spanned by 8 cylindrical standoff spacer pillars (Ø 14 mm).
  - **Front & Rear width:** 13 cm (130 mm, $Y = \pm 65\,\text{mm}$)
  - **Middle width:** 15 cm (150 mm, $Y = \pm 75\,\text{mm}$)
  - **Axis distance along body:** 8.6 cm (86 mm, $X = +86\,\text{mm}$ front, $0\,\text{mm}$ middle, $-86\,\text{mm}$ rear)
  - **Default Stance:** $X = 160\,\text{mm}$ radial reach, $Z = -80\,\text{mm}$ ground clearance.
- **Actuation & Planned Sensor Expansion:**
  - **Servos (18×):** Standard 25T spline metal-gear servos (Hitec HS-645MG / NR-645).
  - **PWM Drivers (2×):** PCA9685 on I2C Bus 1 at `0x40` (left 9 servos) and `0x42` (right 9 servos, A1 bridged), powered by a 6.0 V high-current UBEC. PCA9685 `ALLCALL` (`0x70`) is explicitly disabled in software to avoid address collision with the I2C multiplexer.
  - **Planned STEMMA QT / Qwiic Sensor Bus (I2C):**
    - `0x70`: Adafruit PCA9548 8-Channel I2C Multiplexer
    - `0x4A`: Adafruit BNO085 9-DOF Orientation IMU
    - `0x41` & `0x44`: 2× Adafruit INA260 High-Side Voltage/Current/Power Monitors (left & right servo banks)
    - `CH0–CH2` (`0x29`): 3× Adafruit VL53L4CD Time-of-Flight laser distance sensors (1–1300 mm, front left/center/right)
    - `0x20`: Adafruit MCP23017 16-pin I2C GPIO expander reading 6× foot contact microswitches

---

## Mechanical CAD & Digital Fabrication (`hardware/mechanics/`)

All robot components are engineered as parametric CAD models in FreeCAD and reverse-engineered from calibrated 1200 DPI flatbed scans and original templates:

### 1. Parametric 3D CAD Models (`hardware/mechanics/models/`)
* **Chassis Bottom Plate ([`body_bottom.FCStd`](hardware/mechanics/models/body_bottom.FCStd)):**
  * **Material & Thickness:** 2.0 mm solid plate (CFRP carbon fiber / aluminum).
  * **Analytic Geometry:** Pure analytic OpenCASCADE B-Rep geometry (44 smooth faces, 126 edges; zero faceted polygon segments).
  * **Contour:** Exact $G^1$-continuous concave fillets ($R_f = 4.5\text{ mm}$) transitioning into all leg mounts towards the nose and tail. Fully protruding circular pivot ears ($R = 13.5\text{ mm}$), $35.5^\circ$ flank line to the tapered rear with $R = 7.0\text{ mm}$ corner fillet.
  * **Bores & Cutouts:** 6× coxa counter-bearing holes ($\varnothing 8.0\text{ mm}$), 8× M3 screw mounting holes ($\varnothing 3.0\text{ mm}$), and a central electronics cutout window ($50.0 \times 160.0\text{ mm}$).
* **Chassis Top Plate ([`body_top.FCStd`](hardware/mechanics/models/body_top.FCStd)):**
  * Upper chassis plate (2.0 mm solid), identical outer contour and mounting hole pattern as `body_bottom`.
* **Coxa Bracket ([`coxa_bracket.FCStd`](hardware/mechanics/models/coxa_bracket.FCStd)):**
  * **Structural Reinforcement:** Dual $3.0\text{ mm}$ lateral reinforcement cheeks fully enclose the Body-to-Coxa servo casing, eliminating shear failure at the pivot axis.
  * **Cable Outlet:** Fully cleared and filleted wiring channel for the Coxa servo ($R = 2.0\text{ mm}$ outer corner radius).
  * **Counter-Bearing:** Coaxial pivot bore aligned at $Y = 15.25\text{ mm}$ ($Z_{\text{world}} = 0.00\text{ mm}$).
* **Femur Plate Cage ([`femur_plate.FCStd`](hardware/mechanics/models/femur_plate.FCStd)):**
  * Dual-plate beam cage ($L = 100.0\text{ mm}$ inter-axis spacing, $W = 31.6\text{ mm}$) with flush-mounted ball bearings ($\varnothing 8 \times 3\text{ mm}$), standoff spacers ($51.3\text{ mm}$), and a $1.0\text{ mm}$ servo clearance gap with flush M4 fasteners.
* **Tibia Limb ([`tibia.FCStd`](hardware/mechanics/models/tibia.FCStd)):**
  * High-rigidity, weight-optimized lower limb ($L = 130.0\text{ mm}$, $X = -129.15 \dots +41.15\text{ mm}$).
  * Pure analytic circular arcs and B-splines (26 faces, 72 edges) replacing the previous 229 polygon steps while preserving the exact profile.
* **Tibia Servo Foot ([`tibia_servo_foot.FCStd`](hardware/mechanics/models/tibia_servo_foot.FCStd)):**
  * Integrated servo mount and rounded foot tip with internal wire routing.
* **Chassis Standoff Pillars ([`spacer_14x50.FCStd`](hardware/mechanics/models/spacer_14x50.FCStd)):**
  * $\varnothing 14.0\text{ mm}$ standoff pillars ($L = 51.3\text{ mm}$) with M3 threaded bores spanning the internal gap between the chassis plates.
* **Complete Modular Leg Assembly ([`leg_assembly.FCStd`](hardware/mechanics/models/leg_assembly.FCStd)):**
  * Fully linked 22-part kinematic subassembly consisting of 3 servos (NR-645), brackets, bearings, M4 countersunk screws, shims, lock nuts, and standoffs.
* **Complete Full-Body Assembly ([`body_assembly.FCStd`](hardware/mechanics/models/body_assembly.FCStd)):**
  * Master full-robot assembly (142 components) linking the bottom plate (`body_bottom`), top plate (`body_top`), 8× standoff pillars (`spacer_14x50`, $\varnothing 14 \times 51.3\text{ mm}$) at all M3 mounting holes, and 6× modular leg assemblies (`leg_assembly`). Right-side legs (FR, MR, RR) are mirrored across the sagittal plane ($Y = 0$) so that all 6 servo horn outputs consistently face forward towards the front of the robot ($-X$), mounted with exact $0.00000\text{ mm}$ coxa pivot axis alignment.

### 2. Digital Fabrication & Exchange Formats (`hardware/mechanics/export/`)
* **STEP (`export/step/`):** ISO 10303 CAD exchange format for CNC milling, waterjet cutting, and CAD assembly imports.
* **STL (`export/stl/`):** High-resolution triangulated meshes for 3D printing (SLA, SLS, FDM).
* **DXF (`export/dxf/`):** 2D vector profiles for laser cutting and 2D CNC sheet processing (CFRP / Aluminum).
* **1:1 Technical Drawings & Templates (`drawings/templates/`):** True-to-scale SVG drill and fabrication templates.

---

## Key Features

- **Harmonic Cosine 50 Hz Walking Engine & Safe Locomotion State Machine:**
  - $C^1$-continuous harmonic cosine trajectories across swing and stance phases with zero-velocity liftoff and touchdown (reducing acceleration jerk by $>5\times$).
  - Continuous duty-cycle and phase morphing between Tripod, Ripple, and Wave gaits.
  - **Safe Boot & Disengagement Arbitration (`locomotion_active`):** The daemon boots with `OmniGait` attached in a disengaged, zero-PWM state (`locomotion_active = False`). Locomotion or pose orders (`SET_VELOCITY`, `SET_WALK`, `SET_TURN`, `SET_POSE`, `SET_HEIGHT`, `SET_ROLL`, `SET_PITCH`, `RESET_POSE`) automatically engage the 50 Hz gait loop, while single-joint/single-leg calibration commands (`SET_JOINT_ANGLE`, `SET_LEG_JOINTS`, `RELAX_LEG`, `RELAX_ALL`, `EMERGENCY_STOP`) and async test sequences (`TEST_LEG`, `STANCE_LEG`, `SWEEP_JOINT`) automatically disengage full-body gait actuation so isolated leg tests are never overwritten.
- **Inverse Kinematics (IK):**
  - 3-DOF insect-leg closed-form kinematics translating Cartesian foot coordinates `(x, y, z)` into joint angles (Coxa, Femur, Tibia).
- **Thread-Safe Dual PCA9685 Hardware Drivers:**
  - Shared per-bus `threading.RLock` protecting concurrent I2C transactions between the 50 Hz locomotion loop and asynchronous `OrderDispatcher` worker threads.
  - Microsecond-accurate pulse calculation with center offsets, orientation inversion, and software safety limits.
- **Order Pipeline & REST/WebSocket Control API:**
  - Transport-agnostic `OrderDispatcher` supporting immediate and asynchronous tasks with priority arbitration and cancellation watchdog.
  - Instant joint actuation (`SET_JOINT_ANGLE`, `SET_LEG_JOINTS`) with sub-2ms hardware latency.
  - Full REST API under `/api/v1/...` and reactive 50 Hz WebSocket event streaming.
- **Modular Vue 3 + TypeScript + Pinia Architecture (`lasius-dashboard`):**
  - Modern Single-Page Application built with Vue 3 `<script setup lang="ts">` and Vite.
  - Reusable `JointCard.vue` component for both Direct Drive and Calibration modes.
  - Pinia `dashboardStore.ts` for unified WebSocket streaming, telemetry synchronization, and order dispatching.
  - High-performance Three.js encapsulation using `shallowRef`, in-place `BufferAttribute` updates for 50 Hz motion-range arcs, and proper WebGL geometry/material disposal.
  - Responsive keyboard controls (`WASD`, `QE`, `Arrows`, `Space`) with automatic `keyup` stop detection.
- **Biomimetic 3D Digital Twin & Multi-View Interface:**
  - Real-time Three.js 3D WebGL viewport and 2D orthographic projections (Top XY, Side YZ, Front XZ).
  - Dual 2 mm chassis plates sandwiching the 6 coxa rotation axes with internal standoff spacer pillars.
  - Unified chassis and leg styling using identical PBR material (`#343746`) and a compact blue forward direction indicator triangle (`#3498db`).
  - Clean CAD orthographic projections using strictly straight vectors for all limb segments.
- **4-Tab Control Sidebar:**
  - **Tab 1: Gait & Directions:** D-Pad (WASD / QE), Tripod/Ripple/Wave selector, Speed & Stride sliders, 6-DOF Body Attitude (Height, Roll, Pitch).
  - **Tab 2: Leg Control (Direct Drive & Calibration):**
    - Interactive leg selector (`LF`, `LM`, `LR`, `RF`, `RM`, `RR`) synchronized with the 3D viewport.
    - **Direct Drive Mode:** 3 individual joint sliders (Coxa, Femur, Tibia) with live degree readouts; neutral stance, zero, and relax actions.
    - **Calibration Mode (Option C Robotics Overlay):** Isolated reference pose alignment (`🎯 Align Ref Pose (0°)`, relaxing the other 15 servos), live microsecond pulse trim steppers (`[-10µs]`, `[-1µs]`, `[Zero]`, `[+1µs]`, `[+10µs]`), live direction inversion checkbox (`Inverted (-1)`), limit boundaries (`Min/Max Angle`), range motion test sweeps, atomic `calibration.json` persistence (`💾 Save Calibration`), and factory defaults reset (`↺ Reset Leg`).
  - **Tab 3: Tests:** Harmonic step cycles with configurable cycle count, joint collision sweeps, all-stance, relax-all, and live order execution monitor.
  - **Tab 4: System (Raspberry Pi Telemetry & KPIs):** Real-time monitoring of SoC temperature (°C), CPU load average & utilization %, RAM memory & daemon RSS, hardware power health and under-voltage detection (`vcgencmd get_throttled`), Wi-Fi RSSI level (dBm) & link quality, root storage disk space, and system uptime.
- **Global Header Actions:**
  - Global `⛔ E-Stop` button: Immediately halts motion and relaxes all 18 servos.
  - `⟳ Restart Server` button: Safely relaxes PWM and re-executes the server daemon in the background with automated reconnection polling.
  - `⏻ Shutdown` button: Safely relaxes all 18 servos, stops the daemon, and powers off the Raspberry Pi with interactive confirmation and status overlay.
- **Gamepad Teleoperation (`lasius-pilot`, see [`docs/pilot/gamepad_stadia.md`](docs/pilot/gamepad_stadia.md)):**
  - High-performance, zero-external-dependency Linux joystick reader (`/dev/input/js0`) with configurable radial deadzones, atomic `set_velocity` WebSocket streaming, and first-class **Google Stadia Controller** support (`Axis 2` turn mapping + action buttons for E-Stop, gait switching, speed, body height, and pose reset).

---

## REST Control API & OpenAPI 3.1 (`/api/v1/...`)

The daemon serves a clean JSON REST API and OpenAPI 3.1.0 specification on port `8000` (see [`lasius-core/lasius-rest-control-api.http`](lasius-core/lasius-rest-control-api.http) for ready-to-run HTTP requests):

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

## Quickstart & Developer Workflows

### Helper Scripts (`scripts/`)

Pre-configured shell scripts in [`scripts/`](scripts/) automate common development, simulation, deployment, and maintenance tasks:

| Script | Description | Usage |
| :--- | :--- | :--- |
| [`scripts/dev_sim.sh`](scripts/dev_sim.sh) | Launches the local simulation server (Mock HAL) on port 8000 (HTTP) & 8765 (WS). | `./scripts/dev_sim.sh` |
| [`scripts/dev/dev_sim.sh`](scripts/dev/dev_sim.sh) | Launches the local simulation server (Mock HAL) on port 8000 (HTTP) & 8765 (WS). | `./scripts/dev/dev_sim.sh` |
| [`scripts/dev/run_tests.sh`](scripts/dev/run_tests.sh) | Runs all unit & integration tests across `lasius-core` and `lasius-pilot`. | `./scripts/dev/run_tests.sh` |
| [`scripts/deploy/deploy_pi.sh`](scripts/deploy/deploy_pi.sh) | Builds the Vue 3 dashboard (Vite), syncs `core`, `pilot`, & `dist/` to the Pi via `rsync`, and gracefully reloads the daemon. | `./scripts/deploy/deploy_pi.sh [PI_IP]` |
| [`scripts/deploy/status_pi.sh`](scripts/deploy/status_pi.sh) | Queries live telemetry, Raspberry Pi KPIs, SoC temperature, power health, and gait vectors. | `./scripts/deploy/status_pi.sh [PI_IP]` |
| [`scripts/deploy/backup_calibration.sh`](scripts/deploy/backup_calibration.sh) | Downloads and validates `calibration.json` with a timestamp into [`data/calibration_backups/`](data/calibration_backups/). | `./scripts/deploy/backup_calibration.sh [PI_IP]` |
| [`scripts/bench/pot_calibration_wizard.py`](scripts/bench/pot_calibration_wizard.py) | Interactive CLI wizard for closed-loop servo potentiometer calibration & regression. | `uv run scripts/bench/pot_calibration_wizard.py` |
| [`scripts/banner.txt`](scripts/banner.txt) | Centralized `Lasius HexaPod` ASCII CLI header banner displayed by all shell scripts. | `cat scripts/banner.txt` |

### 1. Installation & Local Simulation (Workstation without Robot)

1. **Create a virtual environment & install packages in editable mode:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e lasius-core -e lasius-pilot
   ```
2. **Build the Dashboard (Vite):**
   ```bash
   cd lasius-dashboard
   npm install
   npm run build
   cd ..
   ```
3. **Run the Automated Test Suite:**
   ```bash
   ./scripts/dev/run_tests.sh
   # or directly via uv:
   uv run pytest
   ```
4. **Launch the Simulation Daemon & 3D Digital Twin:**
   ```bash
   ./scripts/dev/dev_sim.sh
   # or directly:
   python3 lasius-core/run_server.py
   ```
   - **REST API & 3D Web Dashboard:** `http://127.0.0.1:8000`
   - **WebSocket Telemetry Stream:** `ws://127.0.0.1:8765`

### 2. Raspberry Pi Deployment & Autostart (`systemd`)

Deploy code and pre-built dashboard assets from your workstation or configure `systemd` on the Raspberry Pi:
```bash
# Deploy from workstation (pings Pi, builds dashboard, syncs files via rsync, restarts service)
./scripts/deploy/deploy_pi.sh 192.168.0.123

# Run directly on the Raspberry Pi with physical PCA9685 hardware
python3 lasius-core/run_server.py --hardware

# Copy and enable the systemd service on the Raspberry Pi
sudo cp lasius-core/lasius.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now lasius.service

# Check service status and live logs
sudo systemctl status lasius
journalctl -u lasius -f
```

### 3. Live Robot Status, Calibration Backup & Emergency Handling

- **Query Live Robot Status & Raspberry Pi System Health:**
  ```bash
  ./scripts/deploy/status_pi.sh 192.168.0.123
  ```
- **Backup Servo Calibration (`data/calibration_backups/calibration_YYYYMMDD_HHMMSS.json`):**
  ```bash
  ./scripts/deploy/backup_calibration.sh 192.168.0.123
  ```
- **Emergency Stop (E-Stop) & Relax All 18 Servos via CLI:**
  ```bash
  # Immediate Priority-99 E-Stop (halts motion & de-energizes all servos)
  curl -s -X POST http://192.168.0.123:8000/api/v1/emergency_stop

  # Relax all 18 servos (disable PWM channels)
  curl -s -X POST http://192.168.0.123:8000/api/v1/relax
  ```

### 4. Interactive Leg Calibration & Hardware Diagnostics

Calibrate individual servos in the terminal or scan the I2C bus:
```bash
# Interactive pulse trim tool with 3D twin feedback
python3 lasius-core/calibrate.py --hardware --leg left_rear

# Scan I2C bus for 0x40 and 0x42
python3 lasius-core/check_hardware.py --scan
```
