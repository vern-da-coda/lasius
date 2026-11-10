# Lasius Hexapod

---

[Index](README.md) | [Software](software/README.md) | [Hardware](hardware/README.md) | [Docs](docs/README.md) | [Data](data/README.md) | [Scripts](scripts/README.md) |<br>
[Architecture](#folder-architecture) | [Subsystems](#core-subsystems--capabilities) | [Documentation Index](#documentation-index--navigation) | [Quickstart](#quickstart) |

---

<p align="left">
  <a href="software/README.md"><img src="https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white" alt="Python 3.11+"></a>
  <a href="software/lasius-dashboard/README.md"><img src="https://img.shields.io/badge/Vue%203-TypeScript-4FC08D.svg?logo=vuedotjs&logoColor=white" alt="Vue 3 + TypeScript"></a>
  <a href="software/lasius-dashboard/README.md"><img src="https://img.shields.io/badge/3D%20Twin-Three.js%20WebGL-black.svg?logo=threedotjs&logoColor=white" alt="Three.js Digital Twin"></a>
  <a href="scripts/sim/run_simulation.py"><img src="https://img.shields.io/badge/Physics%20Sim-PyBullet%20%26%20MuJoCo-red.svg" alt="PyBullet & MuJoCo Simulation"></a>
  <a href="software/lasius-core/src/lasius/core/sim/gym_env.py"><img src="https://img.shields.io/badge/Gymnasium-Residual%20RL%20(PPO)-blueviolet.svg" alt="Gymnasium Residual RL"></a>
  <a href="software/lasius-core/README.md"><img src="https://img.shields.io/badge/Locomotion-50Hz%20Harmonic%20Cosine-0284c7.svg" alt="50 Hz Harmonic Gait"></a>
  <a href="hardware/README.md"><img src="https://img.shields.io/badge/Hardware-18%20DOF%20%7C%20CFRP%20Sandwich-orange.svg" alt="18 DOF Robot Hardware"></a>
  <a href="software/lasius-core/README.md"><img src="https://img.shields.io/badge/API-OpenAPI%203.1-6BA539.svg?logo=openapiinitiative&logoColor=white" alt="OpenAPI 3.1"></a>
  <a href="scripts/dev/run_tests.sh"><img src="https://img.shields.io/badge/Tests-66%20Passing%20(100%25)-success.svg" alt="66 Passing Tests"></a>
</p>
<p align="left">
  <a href="https://github.com/vern-da-coda/lasius/actions/workflows/ci.yml"><img src="https://github.com/vern-da-coda/lasius/actions/workflows/ci.yml/badge.svg" alt="Continuous Integration"></a>
  <a href="https://github.com/vern-da-coda/lasius/actions/workflows/deploy-demo.yml"><img src="https://img.shields.io/badge/Deploy%20Dashboard%20Demo-passing-success.svg?logo=githubactions&logoColor=white" alt="Deploy Dashboard Demo"></a>
  <a href="https://github.com/vern-da-coda/lasius/commits/main"><img src="https://img.shields.io/github/last-commit/vern-da-coda/lasius?logo=github&color=blue" alt="Last Commit"></a>
</p>

Modular control software, rigid-body physics simulation, 3D Digital Twin, REST/WebSocket teleoperation daemon, and CAD engineering pipeline for an 18-DOF, 6-legged (hexapod) biomimetic walking robot.

**Interactive Web Demo:** [**https://dashboard.lasius.kaemmereit.de/**](https://dashboard.lasius.kaemmereit.de/) – Experience the browser-based 3D Digital Twin and gait engine live.

<p align="center">
  <img src="hardware/mechanics/drawings/renders/body_assembly.png" alt="Hexapod:Lasius Full Body Assembly" width="750">
</p>

Lasius combines embedded locomotion control, 3D physics simulation (PyBullet & MuJoCo), Gymnasium Reinforcement Learning, real-time WebGL visualization, physical CAD engineering, and gamepad teleoperation into a single unified monorepo. The physical robot features a dual carbon-fiber sandwich chassis, 18 high-torque metal-gear servos driven by dual PCA9685 PWM controllers, closed-form 3-DOF inverse kinematics, a smooth 50 Hz harmonic cosine walking engine, and an interactive Digital Twin built with Vue 3 and Three.js.

---

## Core Subsystems & Capabilities

### 1. Embedded Locomotion Engine (`software/lasius-core`)
- **50 Hz Harmonic OmniGait Engine:** $C^1$-continuous trajectory generator with smooth cosine stance/swing transitions, $>5\times$ acceleration jerk reduction, and seamless morphing between **Tripod**, **Ripple**, and **Wave** gaits.
- **Analytical 3-DOF Inverse Kinematics:** Closed-form solver computing joint angles $(\theta_{\text{coxa}}, \theta_{\text{femur}}, \theta_{\text{tibia}})$ from foot Cartesian coordinates $(x, y, z)$.
- **Dynamic 6-DOF Body Attitude:** Real-time adjustment of ground clearance ($z \in [-130, -40]\,\text{mm}$), chassis roll, and pitch without altering foot ground contact.
- **REST & WebSocket API:** OpenAPI 3.1 specification serving high-level locomotion orders (`set_velocity`, `set_gait`, `reset_pose`), 25 Hz joint angle telemetry, and 10 Hz system KPIs.

### 2. 3D Physics Digital Twin & Reinforcement Learning (`scripts/sim/`)
- **Physics Simulation (PyBullet & MuJoCo):** 240 Hz rigid-body simulation with Coulomb ground friction ($\mu = 1.2$), accurate joint limits, and stable insect stance with elevated femur and 90° tibia horn offset.
- **Automated FreeCAD $\to$ URDF Pipeline:** `scripts/sim/extract_inertias.py` analytically computes masses and 3D inertia tensors directly from CAD solid models; `scripts/sim/export_urdf.py` generates [`hardware/mechanics/export/urdf/lasius.urdf`](hardware/mechanics/export/urdf/lasius.urdf).
- **Gymnasium Environment (`LasiusGymEnv`):** Standardized RL interface with 66-dimensional observation space (projected gravity vector, linear/angular velocities, joint errors, action history) and 18-dimensional continuous action space (Residual RL).
- **PPO Policy Training:** Stable-Baselines3 training pipeline (`scripts/sim/train_rl.py`) running at $>420\,\text{FPS}$ on laptop CPUs for residual gait adaptation.

### 3. 3D Web Dashboard (`software/lasius-dashboard`)
- **Vue 3 + TypeScript Single-Page App:** Reactive dashboard with Three.js WebGL 3D Digital Twin, 2D orthographic CAD projections, and real-time state telemetry.
- **Leg Control & Calibration:** Interactive joint inspection (`JointCard.vue`) supporting individual servo angle sliders, 0° reference alignment, automated collision sweeps, and live microsecond trim overlay persistence.
- **Ground Coupling:** Dynamic support plane calculation (`fitSupportPlane`) supporting *Ground Locked* (moving floor grid) and *Test Stand* (bench isolation) modes with active foot contact glow indicators.
- **Standalone Client Simulation:** Runs in browser without robot connection via an additive TypeScript kinematics engine ([`dashboard.lasius.kaemmereit.de`](https://dashboard.lasius.kaemmereit.de/)).

### 4. Gamepad Teleoperation (`software/lasius-pilot`)
- **Multi-Controller Support:** Native Linux joystick driver (`/dev/input/js0`) with auto-detecting YAML profiles for **Sony PS5 DualSense**, **Google Stadia**, and **Xbox** controllers.
- **Unified Orchestration (`scripts/sim/sim_pilot.sh`):** Concurrent startup of PyBullet 3D simulation, HTTP Web Dashboard, WebSocket bridge, and `lasius-pilot` teleoperation with graceful single-signal shutdown.

### 5. I2C Sensor Bus & Testbench (`hardware/electronics/`, `scripts/bench/`)
- **Two-Tier I2C Architecture:** Dual PCA9685 servo drivers (`0x40` left, `0x42` right) on primary I2C bus 1; central **TCA9548A 8-channel multiplexer** (`0x71`) isolating 6× **ADS1115** 16-bit ADCs (`0x48`) for closed-loop potentiometer feedback.
- **Automated Diagnostic Tool (`scripts/bench/test_electronics.py`):** Full topology scan, sub-channel switching, and live analog voltage monitor with offline `--mock` mode.

---

## Folder Architecture

The repository is organized into focused subdomains:

```text
lasius/
├── software/            # Monorepo software packages
│   ├── lasius-core/     # Locomotion engine, HAL, Gymnasium environment & REST/WS daemon
│   ├── lasius-dashboard/# Vue 3 + TypeScript + Three.js 3D Digital Twin & browser GUI
│   └── lasius-pilot/    # Gamepad teleoperation client & Linux joystick driver
├── hardware/            # Physical robot engineering
│   ├── mechanics/       # Parametric FreeCAD models, STL/STEP exports & 1:1 drill templates
│   └── electronics/     # Sensor bus topology, WireViz harness diagrams & BOMs
├── docs/                # Architecture specifications, hardware plans & roadmap
├── data/                # Calibration snapshots, benchmarks & telemetry logs
└── scripts/             # Development, simulation, bench diagnostics & deployment tools
```

---

## Documentation Index & Navigation

Direct links to all distributed technical documentation, specifications, hardware plans, and subsystem guides:

### System & Architecture (`docs/`)
- [**`docs/README.md`**](docs/README.md) – Documentation overview and navigation guide
- [**`docs/domain_architecture.md`**](docs/domain_architecture.md) – Comprehensive system & domain architecture specification (6 Domains, C4 map & sequence workflows)
- [**`docs/roadmap.md`**](docs/roadmap.md) – Project roadmap, milestone progress (M1–M6), and backlog
- [**`docs/audio_briefing_domain.md`**](docs/audio_briefing_domain.md) – Audio podcast briefing script covering mechanics, kinematics, and software architecture

### Hardware & Electronics (`docs/hardware/`, `hardware/`)
- [**`docs/hardware/testbench_bringup_status.md`**](docs/hardware/testbench_bringup_status.md) – **Active Focus:** Step-by-step Bring-Up status and handover for TCA9548A & ADS1115 ADCs
- [**`docs/hardware/electronics_testbench_guide.md`**](docs/hardware/electronics_testbench_guide.md) – Technical reference guide, wiring pinouts, 3.3V logic rules, and I2C address conflict protection
- [**`docs/hardware/decisions.md`**](docs/hardware/decisions.md) – Hardware decisions, power architecture (LiPo/UBEC), sensor bus & PETG 3D print specifications
- [**`docs/hardware/closed_loop_plan.md`**](docs/hardware/closed_loop_plan.md) – 18-DOF closed-loop feedback plan, ADS1115 ADC pinout & CircuitPython drivers
- [**`docs/hardware/wiring_plan.md`**](docs/hardware/wiring_plan.md) – Raspberry Pi to PCA9685 I2C daisy chain, logic levels & common ground scheme
- [**`hardware/README.md`**](hardware/README.md) – Hardware overview, dual-plate chassis dimensions, limb lengths & power distribution
- [**`hardware/mechanics/README.md`**](hardware/mechanics/README.md) – FreeCAD parametric models, fabrication exports (STEP, STL, DXF) & SVG drill templates
- [**`hardware/electronics/wiring/README.md`**](hardware/electronics/wiring/README.md) – WireViz cable harnesses (`.yml`), visual harness diagrams & automated BOMs

### Teleoperation & Controls (`docs/pilot/`)
- [**`docs/pilot/gamepad_stadia.md`**](docs/pilot/gamepad_stadia.md) – Google Stadia Bluetooth/USB controller profile, button mappings & teleoperation

### Software Subsystems (`software/`)
- [**`software/README.md`**](software/README.md) – Software architecture overview and package guide
- [**`software/TODO.md`**](software/TODO.md) – Biomimetic backlog, Walknet ganglia architecture, and active sprint tasks
- [**`software/lasius-core/README.md`**](software/lasius-core/README.md) – Locomotion engine, 50 Hz harmonic gait, 3-DOF IK, HAL, and REST/WebSocket API
- [**`software/lasius-dashboard/README.md`**](software/lasius-dashboard/README.md) – Vue 3 + TypeScript 3D Digital Twin (Three.js WebGL), 2D projections & control GUI
- [**`software/lasius-pilot/README.md`**](software/lasius-pilot/README.md) – Direct Linux joystick driver (`/dev/input/js0`), radial deadzones & teleoperation streaming

### Data, Benchmarks & Tooling (`data/`, `scripts/`)
- [**`data/README.md`**](data/README.md) – Runtime data index, calibration snapshots & benchmark measurements
- [**`data/bench/README.md`**](data/bench/README.md) – Potentiometer sweep calibration data, linear regression parameters & validation results
- [**`scripts/README.md`**](scripts/README.md) – Complete guide to automation, simulation, testing, diagnostic, and deployment scripts

---

## Quickstart

### 1. Installation & Dependencies

```bash
# Set up Python environment and packages in editable mode:
uv sync --extra dev
# or: pip install -e software/lasius-core -e software/lasius-pilot

# Install frontend dependencies and build dashboard:
cd software/lasius-dashboard && npm install && npm run build && cd ../..
```

### 2. Run Automated Test Suite

```bash
./scripts/dev/run_tests.sh
```
*Executes all 66 automated unit and integration tests across `lasius-core` (HAL, kinematics, gait, GymEnv, orders) and `lasius-pilot`.*

### 3. Interactive 3D Physics Simulation & Gamepad Teleoperation

Launch PyBullet rigid-body physics, the 3D Web Dashboard, and Gamepad teleoperation (PS5 DualSense / Stadia / Xbox) concurrently:

```bash
./scripts/sim/sim_pilot.sh
```

Or start the standalone PyBullet 3D simulation directly:
```bash
python3 scripts/sim/run_simulation.py --gui
```

### 4. Local Simulation Server & Web Digital Twin

```bash
./scripts/dev/dev_sim.sh
```

Open your browser at:
- **3D Dashboard & Control GUI:** `http://127.0.0.1:8000`
- **Interactive OpenAPI Specification:** `http://127.0.0.1:8000/api/v1/openapi.yaml`
- **Telemetry WebSocket:** `ws://127.0.0.1:8765`

### 5. Electronics Testbench Diagnostics

Test I2C connectivity and the TCA9548A / ADS1115 sensor bus:

```bash
# On physical Raspberry Pi:
python3 scripts/bench/test_electronics.py --scan

# Offline dry-run on development workstation:
python3 scripts/bench/test_electronics.py --scan --mock
```

### 6. Deploy to Physical Raspberry Pi 4

```bash
./scripts/deploy/deploy_pi.sh [PI_IP]
```
