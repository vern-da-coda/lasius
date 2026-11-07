# Lasius Hardware: Mechanics & Electronics

Physical robot engineering, mechanical CAD models, digital fabrication exports, power distribution, and electrical sensor bus harnesses for the **Lasius** 18-DOF Hexapod robot.

---

## Physical Specifications

All dimensions and physical kinematics are defined in [`lasius-core/src/lasius/core/config.yaml`](../lasius-core/src/lasius/core/config.yaml):

- **Leg Limb Lengths (inter-axis distances):**
  - **Coxa:** 60 mm ($6\,\text{cm}$) — bracket extends an additional 30 mm inwards from the vertical pivot axis towards the chassis interior.
  - **Femur:** 100 mm ($10\,\text{cm}$).
  - **Tibia:** 130 mm ($13\,\text{cm}$).
- **Chassis Dimensions & Dual-Plate Construction:**
  - **Dual Sandwich Plates:** Two distinct 2 mm chassis plates (carbon fiber CFRP / aluminum) sandwiching and supporting the 6 coxa rotation axes from top and bottom.
  - **Plate Clearance & Standoffs:** 51.3 mm internal vertical gap spanned by 8 cylindrical standoff spacer pillars ($\varnothing 14\,\text{mm}$).
  - **Front & Rear Width:** 130 mm ($Y = \pm 65\,\text{mm}$).
  - **Middle Width:** 150 mm ($Y = \pm 75\,\text{mm}$).
  - **Axis Distance along Body:** 86 mm ($X = +86\,\text{mm}$ front, $0\,\text{mm}$ middle, $-86\,\text{mm}$ rear).
  - **Default Stance:** $X = 160\,\text{mm}$ radial reach, $Z = -80\,\text{mm}$ ground clearance.
- **Actuation & Drivers:**
  - **Servos (18×):** Standard 25T spline metal-gear servos (Hitec HS-645MG / NR-645).
  - **PWM Drivers (2×):** PCA9685 on I2C Bus 1 at `0x40` (left 9 servos) and `0x42` (right 9 servos, A1 bridged), powered by a 6.0 V high-current UBEC (20A). PCA9685 `ALLCALL` (`0x70`) is disabled in software.
- **Sensor Bus Architecture (STEMMA QT / Qwiic I2C):**
  - `0x70`: Adafruit PCA9548 8-Channel I2C Multiplexer
  - `0x4A`: Adafruit BNO085 9-DOF Orientation IMU
  - `0x41` & `0x44`: 2× Adafruit INA260 High-Side Voltage/Current/Power Monitors (left & right servo banks)
  - `CH0–CH2` (`0x29`): 3× Adafruit VL53L4CD Time-of-Flight laser distance sensors (1–1300 mm, front left/center/right)
  - `0x20`: Adafruit MCP23017 16-pin I2C GPIO expander reading 6× foot contact microswitches
  - `CH3–CH7` (`0x48`): 6× ADS1115 16-Bit ADCs reading internal servo potentiometers for closed-loop angle feedback

---

## Subdirectories

- [**`mechanics/`**](mechanics/README.md): Parametric FreeCAD 3D CAD models (`.FCStd`), headless generation scripts (`scripts/`), fabrication exports (`export/` in STEP, STL, DXF), 1:1 SVG drill templates, and 1200 DPI reference flatbed scans.
- [**`electronics/`**](electronics/wiring/README.md): WireViz wiring definitions (`.yml`), electrical harness diagrams (`.svg`, `.png`), and automated Bills of Materials (`.bom.tsv`).

---

## Related Documentation

- [Hardware Decisions & 3D Printing Guide](../docs/hardware/decisions.md): Power architecture, UBEC, STEMMA QT sensor bus, and slicer/material specifications for PETG leg parts.
- [18-DOF Closed-Loop Potentiometer Feedback Plan](../docs/hardware/closed_loop_plan.md): ADS1115 ADC tapping, RC filtering, and angle calibration.
- [Wiring & Connection Plan](../docs/hardware/wiring_anschlussplan.md): Detailed electrical pinout and power rails.
