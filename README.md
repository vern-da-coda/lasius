# Hexapod:Lasius

**Breadcrumb:** [Hexapod:Lasius](README.md) / [Software](software/README.md) / [Hardware](hardware/README.md) / [Docs](docs/README.md) / [Data](data/README.md) / [Scripts](scripts/README.md)

<p align="left">
  <a href="software/README.md"><img src="https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white" alt="Python 3.11+"></a>
  <a href="software/lasius-dashboard/README.md"><img src="https://img.shields.io/badge/Vue%203-TypeScript-4FC08D.svg?logo=vuedotjs&logoColor=white" alt="Vue 3 + TypeScript"></a>
  <a href="software/lasius-dashboard/README.md"><img src="https://img.shields.io/badge/3D%20Twin-Three.js%20WebGL-black.svg?logo=threedotjs&logoColor=white" alt="Three.js Digital Twin"></a>
  <a href="software/lasius-core/README.md"><img src="https://img.shields.io/badge/Locomotion-50Hz%20Harmonic%20Cosine-0284c7.svg" alt="50 Hz Harmonic Gait"></a>
  <a href="scripts/README.md"><img src="https://img.shields.io/badge/Tests-61%20Passed-success.svg" alt="61 Tests Passed"></a>
  <a href="software/lasius-core/README.md"><img src="https://img.shields.io/badge/API-OpenAPI%203.1-6BA539.svg?logo=openapiinitiative&logoColor=white" alt="OpenAPI 3.1"></a>
  <a href="hardware/README.md"><img src="https://img.shields.io/badge/Hardware-18%20DOF%20%7C%20CFRP%20Sandwich-orange.svg" alt="18 DOF Robot Hardware"></a>
</p>

Modular control software, 3D Digital Twin, REST/WebSocket control API, and teleoperation system for an 18-DOF, 6-legged (hexapod) biomimetic walking robot.

<p align="center">
  <img src="hardware/mechanics/drawings/renders/body_assembly.png" alt="Hexapod:Lasius Full Body Assembly" width="750">
</p>

Lasius combines embedded locomotion control, real-time 3D visualization, physical CAD engineering, and teleoperation into a single unified monorepo. The robot features a dual carbon-fiber sandwich chassis, 18 metal-gear servos driven by dual PCA9685 PWM controllers, closed-form 3-DOF inverse kinematics, a smooth 50 Hz harmonic cosine walking engine, and an interactive browser-based Digital Twin built with Vue 3 and Three.js.

---

## Folder Architecture

The repository is organized into focused subdomains:

```text
lasius/
|-- software/            # Complete robot software stack & monorepo workspace
|   |-- lasius-core/     # Embedded Python locomotion engine, HAL & REST/WebSocket daemon
|   |-- lasius-dashboard/# Vue 3 + TypeScript + Three.js 3D Digital Twin & browser GUI
|   \-- lasius-pilot/    # Gamepad teleoperation & Linux joystick client
|-- hardware/            # Physical robot engineering
|   |-- mechanics/       # Parametric CAD models, drawings, exports & fabrication
|   \-- electronics/     # Sensor bus topology, harnesses & WireViz diagrams
|-- docs/                # Architecture, hardware decisions, wiring plans & roadmap
|-- data/                # Benchmark measurements & calibration snapshots
\-- scripts/             # Development, testing, deployment & calibration tools
```

---

## Documentation Index & Navigation

Direct links to all distributed technical documentation, specifications, hardware plans, and subsystem guides:

### System Documentation & Specifications (`docs/`)
- [**`docs/README.md`**](docs/README.md) - Documentation overview and navigation guide
- [**`docs/roadmap.md`**](docs/roadmap.md) - Project roadmap, milestone progress (M1-M6), and backlog
- [**`docs/hardware/decisions.md`**](docs/hardware/decisions.md) - Hardware decisions, power architecture (LiPo/UBEC), sensor bus & 3D print specs
- [**`docs/hardware/closed_loop_plan.md`**](docs/hardware/closed_loop_plan.md) - 18-DOF closed-loop feedback plan, ADS1115 ADC pinout & CircuitPython drivers
- [**`docs/hardware/wiring_plan.md`**](docs/hardware/wiring_plan.md) - Raspberry Pi to PCA9685 I2C daisy chain, logic levels & common ground scheme
- [**`docs/pilot/gamepad_stadia.md`**](docs/pilot/gamepad_stadia.md) - Google Stadia Bluetooth/USB controller profile, button mappings & teleoperation

### Software Subsystems (`software/`)
- [**`software/README.md`**](software/README.md) - Software architecture overview and package guide
- [**`software/lasius-core/README.md`**](software/lasius-core/README.md) - Locomotion engine, 50 Hz harmonic gait, 3-DOF IK, HAL, and REST/WebSocket API
- [**`software/lasius-dashboard/README.md`**](software/lasius-dashboard/README.md) - Vue 3 + TypeScript 3D Digital Twin (Three.js WebGL), 2D projections & control GUI
- [**`software/lasius-pilot/README.md`**](software/lasius-pilot/README.md) - Direct Linux joystick driver (`/dev/input/js0`), radial deadzones & teleoperation streaming

### Physical Hardware & Engineering (`hardware/`)
- [**`hardware/README.md`**](hardware/README.md) - Hardware overview, dual-plate chassis dimensions, limb lengths & power distribution
- [**`hardware/mechanics/README.md`**](hardware/mechanics/README.md) - FreeCAD parametric models, fabrication exports (STEP, STL, DXF) & 1:1 SVG drill templates
- [**`hardware/electronics/wiring/README.md`**](hardware/electronics/wiring/README.md) - WireViz cable harnesses (`.yml`), visual harness diagrams & automated BOMs

### Data, Calibration & Tooling (`data/`, `scripts/`)
- [**`data/README.md`**](data/README.md) - Runtime data index, calibration snapshots & benchmark measurements
- [**`data/bench/README.md`**](data/bench/README.md) - Potentiometer sweep calibration data, linear regression parameters & validation results
- [**`scripts/README.md`**](scripts/README.md) - Automation scripts for local simulation (`dev/dev_sim.sh`), testing, and Pi deployment (`deploy/deploy_pi.sh`)
- [**`GEMINI.md`**](GEMINI.md) - AI developer briefing, coding standards, architecture summary & system configuration

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

### 2. Run Test Suite

```bash
./scripts/dev/run_tests.sh
```

### 3. Start Local Simulation Server & Digital Twin

```bash
./scripts/dev/dev_sim.sh
```

Open your browser at:
- **3D Dashboard & Control GUI:** `http://127.0.0.1:8000`
- **Interactive OpenAPI Specification:** `http://127.0.0.1:8000/api/v1/openapi.yaml`
- **Telemetry WebSocket:** `ws://127.0.0.1:8765`

### 4. Deploy to Raspberry Pi

```bash
./scripts/deploy/deploy_pi.sh [PI_IP]
```
