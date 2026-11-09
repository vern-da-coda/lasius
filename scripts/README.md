# Lasius Hexapod: Helper Scripts

---

[Index](../README.md) | [Software](../software/README.md) | [Hardware](../hardware/README.md) | [Docs](../docs/README.md) | [Data](../data/README.md) | [Scripts](../scripts/README.md) |<br>
[Script Index](#script-index) | [Dev & Test](#1-installation--local-simulation-workstation) | [Deploy](#2-physical-deployment-to-raspberry-pi) | [Bench](#3-analog-potentiometer-calibration-bench) |

---

Automation, simulation, deployment, testing, and benchmark tools for the **Lasius** 18-DOF Hexapod robot.

## Script Index

| Category | Script | Description | Usage |
| :--- | :--- | :--- | :--- |
| **Dev & Test** | [`dev/dev_sim.sh`](dev/dev_sim.sh) | Starts local simulation daemon (Mock HAL) and builds dashboard if missing. | `./scripts/dev/dev_sim.sh` |
| **Dev & Test** | [`dev/run_tests.sh`](dev/run_tests.sh) | Executes the complete test suite across `lasius-core` and `lasius-pilot` (61 tests). | `./scripts/dev/run_tests.sh` |
| **Dev & Test** | [`dev/check_links.py`](dev/check_links.py) | Validates internal hyperlink and documentation integrity across all Markdown files. | `python3 scripts/dev/check_links.py` |
| **Deploy** | [`deploy/deploy_pi.sh`](deploy/deploy_pi.sh) | Builds Vite dashboard, syncs files via `rsync` to the Raspberry Pi, and reloads daemon. | `./scripts/deploy/deploy_pi.sh [PI_IP]` |
| **Deploy** | [`deploy/status_pi.sh`](deploy/status_pi.sh) | Queries live telemetry, Raspberry Pi KPIs, SoC temperature, power health, and gaits. | `./scripts/deploy/status_pi.sh [PI_IP]` |
| **Deploy** | [`deploy/backup_calibration.sh`](deploy/backup_calibration.sh) | Downloads and validates `calibration.json` with a timestamp into `data/calibration_backups/`. | `./scripts/deploy/backup_calibration.sh [PI_IP]` |
| **Bench** | [`bench/pot_calibration_wizard.py`](bench/pot_calibration_wizard.py) | Interactive CLI wizard for closed-loop potentiometer calibration & regression curves. | `uv run scripts/bench/pot_calibration_wizard.py` |
| **Bench** | [`bench/servo_pot_sweep.py`](bench/servo_pot_sweep.py) | Hardware servo sweep and live potentiometer voltage measurement tool. | `uv run scripts/bench/servo_pot_sweep.py` |
| **Simulation** | [`sim/sim_pilot.sh`](sim/sim_pilot.sh) | Orchestrates PyBullet 3D physics simulation and `lasius-pilot` gamepad teleoperation. | `./scripts/sim/sim_pilot.sh` |
| **Simulation** | [`sim/export_urdf.py`](sim/export_urdf.py) | Generates Lasius URDF model from `config.yaml`, CAD STL meshes, and inertias. | `python3 scripts/sim/export_urdf.py` |
| **Simulation** | [`sim/validate_urdf.py`](sim/validate_urdf.py) | Validates URDF kinematic tree connectivity, 18-DOF revolute joints, and mesh links. | `python3 scripts/sim/validate_urdf.py` |
| **Simulation** | [`sim/run_simulation.py`](sim/run_simulation.py) | Executes headless or interactive 3D physics verification in PyBullet or MuJoCo. | `python3 scripts/sim/run_simulation.py [--gui]` |
| **Simulation** | [`sim/extract_inertias.py`](sim/extract_inertias.py) | Headless FreeCAD script extracting exact mass, CoM, and inertia tensors from CAD solids. | `/snap/bin/freecad.cmd scripts/sim/extract_inertias.py` |
| **CLI Asset** | [`banner.txt`](banner.txt) | Centralized ASCII header banner displayed by development and deployment scripts. | `cat scripts/banner.txt` |

---

## Developer Workflows

### 1. Installation & Local Simulation (Workstation)

1. **Install Python dependencies with uv or pip:**
   ```bash
   uv sync --extra dev
   # or manually:
   pip install -e software/lasius-core -e software/lasius-pilot
   ```

2. **Build the Vue 3 Dashboard:**
   ```bash
   cd software/lasius-dashboard
   npm install
   npm run build
   cd ../..
   ```

3. **Run the Automated Test Suite:**
   ```bash
   ./scripts/dev/run_tests.sh
   ```

4. **Launch the Simulation Daemon & 3D Digital Twin:**
   ```bash
   ./scripts/dev/dev_sim.sh
   ```
   - REST API & 3D Web Dashboard: `http://127.0.0.1:8000`
   - WebSocket Telemetry Stream: `ws://127.0.0.1:8765`

5. **Launch 3D Physics Digital Twin & Gamepad Teleoperation (PyBullet + lasius-pilot):**
   ```bash
   # Start with Sony PlayStation 5 DualSense (default) or Google Stadia / Xbox
   ./scripts/sim/sim_pilot.sh
   # Or with explicit controller profile:
   ./scripts/sim/sim_pilot.sh --profile ps5
   ```


---

### 2. Raspberry Pi Deployment & Autostart (`systemd`)

Deploy updated code and dashboard assets from your workstation or configure the `systemd` daemon:

```bash
# 1. Deploy from workstation (pings Pi, builds dashboard, syncs via rsync, reloads systemd)
./scripts/deploy/deploy_pi.sh 192.168.0.123

# 2. Run directly on the Raspberry Pi with physical PCA9685 hardware
python3 software/lasius-core/run_server.py --hardware

# 3. Configure systemd autostart on the Raspberry Pi
sudo cp software/lasius-core/lasius.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now lasius.service

# 4. View live daemon logs
journalctl -u lasius -f
```

---

### 3. Live Status, Calibration Backup & Emergency Handling

```bash
# Query Raspberry Pi KPIs and locomotion status
./scripts/deploy/status_pi.sh 192.168.0.123

# Download timestamped calibration backup to data/calibration_backups/
./scripts/deploy/backup_calibration.sh 192.168.0.123

# Emergency Stop (halts motion & relaxes all 18 servos)
curl -s -X POST http://192.168.0.123:8000/api/v1/emergency_stop

# Relax PWM on all servos
curl -s -X POST http://192.168.0.123:8000/api/v1/relax
```
