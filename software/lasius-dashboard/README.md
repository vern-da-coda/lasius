# lasius-dashboard

Modular Vue 3 + TypeScript + Pinia 3D Digital Twin and browser control interface for the **Lasius** 18-DOF Hexapod robot. Built with Vite and Three.js.

---

## Architectural Highlights

- **Modern Vue 3 SPA:** Modular Single-File Components using `<script setup lang="ts">` and strict TypeScript interfaces.
- **Pinia State Management (`dashboardStore.ts`):** Unified store managing 50 Hz WebSocket event streaming, REST order dispatching, and bidirectional parameter synchronization.
- **High-Performance Three.js Engine (`LasiusGraphicsEngine.ts`):**
  - Robust Three.js encapsulation using Vue `shallowRef` to prevent reactive proxy overhead.
  - In-place `BufferAttribute` geometry updates for 50 Hz motion-range arcs and foot trajectory curves (zero per-frame memory allocation or garbage collection spikes).
  - Explicit WebGL resource disposal (`geometry.dispose()`, `material.dispose()`) to prevent memory leaks during view transitions.
- **Keyboard Navigation:** Native hotkeys (`WASD`, `QE`, `Arrows`, `Space`) with debounce and `keyup` stop detection.

---

## Views & Viewport System

- **Interactive 3D WebGL Digital Twin:**
  - Full-mesh 3D representation based on physical CAD geometry: dual carbon-fiber sandwich plates, 8 standoff pillars, Coxa brackets, Femur beam cages, and curved Tibia sickles.
  - Consistent PBR metal-roughness materials (`#343746`) with forward-facing orientation chevron (`#3498db`).
  - Full OrbitControls navigation (Left-drag rotate, Right-drag pan, Wheel zoom).
- **Multi-View 2D Orthographic Projections:**
  - Clean CAD orthographic projections using straight kinematic vectors:
    - **Top View (XY Plane):** Robot heading, lateral reach, and coxa swing arcs.
    - **Side View (YZ Plane):** Chassis pitch, body height clearance, and femur/tibia articulation.
    - **Front View (XZ Plane):** Stance width, body roll, and symmetry.

---

## 4-Tab Control Sidebar

- **Tab 1: Gait & Locomotion:**
  - Direction Pad (WASD forward/backward/strafe, QE turn) and Stop.
  - Gait pattern selector: **Tripod** (fast, dynamic), **Ripple** (stable, 4-leg support), **Wave** (maximum stability, 5-leg support).
  - Gait parameter sliders: Speed, Step Height, Step Length.
  - 6-DOF Body Attitude posing: Chassis Height, Roll, Pitch, and Reset Pose.
- **Tab 2: Leg Control (Direct Drive & Calibration Modes):**
  - Interactive 2D Chassis Minimap: Clickable attachment points on the robot body hull to select any of the 6 legs (`LF`, `LM`, `LR`, `RF`, `RM`, `RR`) with glow highlighting and orientation cues.
  - **Direct Drive Mode:** 3 color-coded joint sliders (Coxa, Femur, Tibia) with live degree readouts; quick buttons for *Stance Position*, *Zero (0°)*, and *Relax Leg*.
  - **Calibration Mode (Option C Robotics Overlay):**
    - Isolated reference pose alignment (`Align Ref Pose (0°)`, relaxing the other 15 servos).
    - Live microsecond pulse trim steppers: `[-10µs]`, `[-1µs]`, `[Zero]`, `[+1µs]`, `[+10µs]`.
    - Direction inversion toggle (`Inverted (-1)`) and safety limits (`Min/Max Angle`).
    - Joint collision sweep testing.
    - Atomic persistence: `Save Calibration` (writes to `calibration.json`) and `Reset Leg` (reverts to `config.yaml` factory defaults).
- **Tab 3: Tests & Diagnostics:**
  - Parametrizable harmonic step cycles (1–10 cycles).
  - Single-joint mechanical collision sweeps (Coxa, Femur, Tibia).
  - System actions: *All in Stance*, *Relax All Servos*.
  - Live Order Monitor with execution latency, duration, and return status logging.
- **Tab 4: System (Raspberry Pi Telemetry & KPIs):**
  - Real-time monitoring of SoC temperature (°C), CPU load average & utilization %, RAM memory & daemon RSS, hardware power health and under-voltage detection (`vcgencmd get_throttled`), Wi-Fi RSSI level (dBm) & link quality, root storage disk space, and system uptime.

---

## Global Header Actions

- **Emergency Stop (E-Stop):** Prominent red header button executing Priority-99 E-Stop: immediately halts motion and de-energizes all 18 servos.
- **Restart Server:** Safely relaxes servos, re-executes the daemon via `os.execv`, and polls for automatic reconnection.
- **Shutdown:** Interactive confirmation dialog, relaxes servos, and cleanly executes `sudo shutdown -h now` on the Raspberry Pi.

---

## Development & Build Workflows

### Install Dependencies
```bash
npm install
```

### Local Development Server (Vite HMR)
```bash
npm run dev
```
Serves the development UI at `http://localhost:5173`. Proxies API and WebSocket requests to `http://localhost:8000`.

### Production Build
```bash
npm run build
```
Compiles and bundles optimized static assets into `dist/` (`index.html`, `assets/index-*.js`, `assets/index-*.css`). The Python server daemon in `lasius-core` automatically serves `dist/` directly on port `8000`.
