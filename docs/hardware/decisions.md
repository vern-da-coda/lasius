# Hexapod:Lasius - Final Hardware, Sensor & CAD Decisions

> **Source:** *GitHub Lasius Project Assistance.pdf* (Concept, Electronics & Mechanics Specification)  
> **Status:** October 2026

This document consolidates all final architectural decisions from the project specification for hardware upgrades, sensor integration (STEMMA QT / I2C), and 3D printing reconstruction (PETG).

---

## 1. Overall Concept & Development Roadmap

1. **Modular 6-Arm Sensor Platform ("Underbody Sensor Tray"):**
   - All chassis sensors are consolidated onto a **single removable mounting plate** beneath the lower chassis plate.
   - The center hosts the multiplexer (TCA9548A), IMU (BNO085), current/power sensors (INA228), GPIO expander (MCP23017), and the 6 ADS1115 leg ADC modules; the front nose houses the ToF distance sensor.
   - **Advantage:** Complete pre-wiring outside the robot at the workbench; disconnected during maintenance via a single centralized I2C uplink from the Raspberry Pi 4.
2. **Decoupled Single-Leg Docking Test Rig:**
   - A 3D-printed **single-leg test bench (docking station)** accommodates exactly *one* leg along with its ADS1115 module, INA228, and foot switch, docking directly to the robot's I2C multiplexer or a test Raspberry Pi.
   - Enables isolated validation of **CAD fit, potentiometer calibration, tibia compliance, and stall current shutdown** on a single leg before assembling all 6 legs.
   - *(Note: The legacy concept of external AS5600 magnetic encoders on the Coxa axes has been completely abandoned -- internal potentiometer feedback provides native 18-DOF telemetry for all 18 joints without mechanical air-gap alignment).*
3. **100% Solderless Sensor Ecosystem (Adafruit STEMMA QT / Qwiic):**
   - All I2C sensors use 4-pin JST-SH connectors (3.3V logic level from the Raspberry Pi). No custom carrier boards or solder bridges for pull-up resistors are required.

---

## 2. Actuation & Power Distribution (Existing & Specification)

| Component | Final Selection / Specification | Technical Notes & Implementation |
| :--- | :--- | :--- |
| **Servomotors (18x)** | **Reely NR-645 MG BB** (Standard analog servo, 59 g) | Metal gears, dual ball bearings, **25T spline (Futaba/Savoex compatible)**, dimensions $40.7 \times 20.5 \times 39.5\,\text{mm}$, stall torque ~9.6-11 kg*cm @ 6.0 V, stall current ~1.8-2.5 A per servo. |
| **PWM Drivers (2x)** | **PCA9685 16-Channel I2C** | Board 1 (Left): **`0x40`**, Board 2 (Right): **`0x42`** (A1 bridged). *Important:* `ALLCALL` (`0x70`) is disabled in driver software to prevent address collisions with the PCA9548 multiplexer. |
| **Power UBECs (2x)** | **2x 5V/6V High-Current UBECs (10-15 A each)** | **Strict Dual-Rail Separation:** UBEC 1 powers exclusively Board `0x40` (left 9 servos), UBEC 2 powers exclusively Board `0x42` (right 9 servos). |
| **Logic Power Supply** | **Separate 5V / 3A Buck Converter** | Powers only the Raspberry Pi 4 (prevents brownouts and reboots during servo stall peaks). Common star ground. |
| **Main Power Inlet** | **Amass XT60BE-M** (Panel-mount male plug with flange) | Securely screwed into chassis rear (strain relief for bench power supply or 2S/3S LiPo battery). |

---

## 3. Sensors & I2C Bus Architecture

### 3.1 I2C Address Plan & Multiplexing

To isolate the 6 leg ADC boards (**ADS1115**) and maintain a clean I2C bus hierarchy, an **8-channel multiplexer (TCA9548A)** is used:

- **Primary I2C Bus (`/dev/i2c-1` on Raspberry Pi):**
  - `0x40`: PCA9685 Servo Board Left (PWM drive)
  - `0x42`: PCA9685 Servo Board Right (PWM drive)
  - `0x71`: **TCA9548A 8-Channel I2C Multiplexer** (Solder bridge A0 closed $\rightarrow$ address `0x71`, eliminates boot conflict with PCA9685 default `0x70`)
  - `0x20`: **Adafruit MCP23017 I2C GPIO Expander** (16 digital I/Os with internal pull-ups)
  - `0x4A`: **Adafruit BNO085 9-DOF Orientation IMU** (Quaternions, gravity vector, linear acceleration)
- **Multiplexer Channels (`TCA9548A @ 0x71`):**
  - `CH0`: **ADS1115 #1 (Left Front: Coxa, Femur, Tibia, Foot)** (`0x48`)
  - `CH1`: **ADS1115 #2 (Left Middle: Coxa, Femur, Tibia, Foot)** (`0x48`)
  - `CH2`: **ADS1115 #3 (Left Rear: Coxa, Femur, Tibia, Foot)** (`0x48`)
  - `CH3`: **ADS1115 #4 (Right Front: Coxa, Femur, Tibia, Foot)** (`0x48`)
  - `CH4`: **ADS1115 #5 (Right Middle: Coxa, Femur, Tibia, Foot)** (`0x48`)
  - `CH5`: **ADS1115 #6 (Right Rear: Coxa, Femur, Tibia, Foot)** (`0x48`)
  - `CH6`: **2x INA228** (Current/voltage monitoring for dual servo rails, A0/A1 bridged)
  - `CH7`: **1x VL53L4CD Time-of-Flight (ToF) Distance Sensor (`0x29`)** in front fascia (1 mm - 1300 mm range)

### 3.2 Tactile Ground Contact Detection & Audio Feedback

- **Foot Contact Switches (6x):** **Omron D2F-L** subminiature lever microswitches (Made in Japan, ultra-low actuation force ~0.75 N, ensuring robot self-weight reliably triggers the switch).
- **Interface:** All 6 microswitches are connected with 2 wires (`COM` to `GND`, `NO` to `GPA0`-`GPA5`) to the **MCP23017 (`0x20`)** with internal pull-up resistors enabled in software.
- **Acoustic Status/Warning Buzzer:** **Passive Piezo Buzzer** wired directly to **GPIO 13 (`PWM1`, Pin 33)** and `GND` (Pin 34) on the Raspberry Pi 4 for multi-tone status chimes (boot, calibration confirm, stall/undervoltage alert).

### 3.3 18-DOF Analog Closed-Loop Servo Feedback (Reely NR-645 MG BB)

- **Concept:** Direct tapping of wiper voltage across all 18 internal servo potentiometers for full real-time joint angle measurement, stall detection, and tactile foot contact sensing.
- **Empirical Model Parameters:** $R^2 = 0.99959$ (99.96% linearity), sensitivity $+7.589\,\text{mV}/^\circ$, zero point $1.5633\,\text{V}$ at $0^\circ$ (1500 us), conversion formula: $\theta(V) = (V - 1.5633) \cdot 131.772^\circ$.
- **Architecture & Bus Design (100% Python on Raspberry Pi 4):**
  - **TCA9548A 8-Channel I2C Multiplexer (`0x71` with solder jumper A0 closed):** Prevents address collisions with PCA9685 `ALLCALL` default (`0x70`) during bootup.
  - **6x ADS1115 (16-Bit 4-Channel ADCs, `0x48` each):** Symmetric **1-board-per-leg** architecture on Mux channels `CH0` through `CH5`. Each ADS1115 reads `A0` (Coxa), `A1` (Femur), `A2` (Tibia), and `A3` (Reserve / analog foot sensor).
  - **Noise Suppression:** 18x (or 24x) **100 nF 50V MLCC ceramic capacitors** soldered directly to the bottom of each ADS1115 between analog inputs and GND ($f_c \approx 636\,\text{Hz}$, filters out PWM and motor brush noise).
  - **Complete Schematic Documentation:** See [`closed_loop_plan.md`](closed_loop_plan.md).

---

## 4. Final Bill of Materials (BOM)

### 4.1 Sensors & Electronics

| Qty | Component / Part Number | Role in Hexapod:Lasius |
| :---: | :--- | :--- |
| **6x** | **ADS1115 16-Bit 4-Channel I2C ADC Breakouts** | 1 board per leg: Reads Coxa, Femur & Tibia potentiometer voltages + foot contact (`0x48` on Mux CH0-CH5) |
| **2x** | **TCA9548A 8-Channel I2C Multiplexer Breakouts** | Central sensor hub at `0x71` (1x Torso, 1x Single-Leg Test Rig). Isolates all 6 leg boards |
| **100x**| **100 nF 50V MLCC Monolithic Ceramic Capacitors** | Low-pass filter capacitors soldered directly to ADS1115 pin headers ($f_c \approx 636\,\text{Hz}$) |
| **1x** | **Adafruit VL53L4CD Time of Flight Distance Sensor** (`5396`) | Precision short-range laser distance sensor (1-1300 mm) in front nose (Mux CH7) |
| **2x** | **Adafruit INA228 I2C 85V 20-Bit Power Monitor** (`5832`) | Real-time current (A), voltage (V), and power (W) telemetry for left & right servo rails (Mux CH6) |
| **1x** | **Adafruit 9-DOF Orientation IMU Fusion Breakout - BNO085** (`4754`) | On-chip sensor fusion (Roll/Pitch/Yaw) for active body self-leveling on main I2C bus (`0x4A`) |
| **1x** | **Adafruit MCP23017 I2C GPIO Expander Breakout** (`5346`) | Reads digital foot microswitches over main I2C bus (`0x20`) |
| **8x** | `4210` | **STEMMA QT / Qwiic JST SH 4-Pin Cable - 100mm** | Short I2C patch links in central sensor tray |
| **6x** | `4401` | **STEMMA QT / Qwiic JST SH 4-Pin Cable - 200mm** | Outgoing leads from multiplexer to leg arm segments |
| **1x** | `5385` | **STEMMA QT / Qwiic JST SH 4-Pin Cable - 300mm** | Long uplink harness for external Single-Leg Docking Test Rig |
| **2x** | `4397` | **STEMMA QT to Female Socket Jumper Cable (150mm)** | Main I2C link between Raspberry Pi GPIO header (3.3V, GND, SDA, SCL) and sensor tray |

### 4.2 Hardware, Switches & Fasteners

- **6-10x Omron D2F-L** subminiature lever microswitches (fastened with **M2 x 10 mm** screws/nuts inside Tibia).
- **2x Amass XT60BE-M** panel-mount male connectors with flange + **1x XT60H-F** female connector for power supply lead.
- **1x Passive Piezo Buzzer** (5V / 3.3V PWM compatible, 7.6 mm pin pitch / 12 mm diameter with 2-pin Dupont plug).
- **Fastener Assortment (A2 Stainless Steel, Hex Socket DIN 912):**
  - **M2 x 8 mm / 10 mm / 12 mm** (for STEMMA QT breakouts, Omron D2F-L, and servo horns).
  - **M3 x 8 mm / 12 mm / 16 mm / 20 mm** + nylon lock nuts DIN 985 (for C-brackets, clamshell Tibia, and standoffs).
- **Filament:** **PETG (Black & signal accent color)** -- mandatory replacement for brittle PLA for all structural leg joints (layer adhesion and high impact toughness under bending).

---

## 5. Mechanical Redesign (CAD / 3D Printing)

### 5.1 Reinforced Coxa Bracket (Eliminating Stress Points)
- **Root Cause of Prior Failures:** Insufficient wall thickness at the transition between servo horn mount and lower counter-bearing pivot, plus notch sensitivity of PLA.
- **New Design:**
  - Reinforced C-bracket geometry printed in **PETG** (4-5 perimeters, 40-50% gyroid infill, printed flat on bed for optimal filament extrusion along tensile/bending lines).
  - **Mechanical Benefit from Potentiometer Feedback:** Because external AS5600 magnets are no longer required, the structural weakening caused by the magnet pocket is eliminated. The lower pivot pin is formed as a **solid cylinder**, drastically increasing bending stiffness at the pivot axis.

### 5.2 Modular Underbody Sensor Tray
- Mounted from below onto the existing chassis standoff pillars.
- Functions as a centralized, vibration-damped tray for the TCA9548A multiplexer, 6 ADS1115 leg modules, BNO085 IMU, and power monitors.
- **Elimination of Air-Gap Alignment:** No delicate bracket arms with $1.0\text{-}1.5\,\text{mm}$ magnet air-gaps under the rotating axes are required.
- Integrated **wire channels with strain relief** route 4-pin leg cables (PWM + potentiometer) cleanly to the center.

### 5.3 Clamshell Tibia with Compliant Meander Spring & Rocker-Tarsus
- **Clamshell Construction (Left/Right Half-Shells):** Two symmetrical half-shells printed flat on the print bed (maximum longitudinal strength, zero internal support structures) bolted with M3 screws.
- **Integrated Compliant Mechanism:**
  - A **PETG meander leaf spring (S-spring)** in the lower third of the Tibia dampens foot touchdown impacts by ~2-3 mm, protecting servo gears.
- **Rocker-Tarsus Foot Tip:**
  - The foot tip is mounted as a short rocker lever on an M3 pivot.
  - Upon ground contact, the rocker-tarsus tilts upward by ~1.5 mm against the meander spring, depressing the **Omron D2F-L microswitch** (or analog pressure sensor at pin `A3` of the leg ADS1115) against a defined **mechanical hard-stop**.
  - **Overload Protection:** Ground reaction forces are absorbed entirely by the printed hard-stop inside the housing -- the microswitch itself is never crushed by the robot's weight.
- **Concealed Wiring:** Both microswitch wires run invisibly inside an internal channel between the two Tibia half-shells.

### 5.4 Single-Leg Docking Test Rig
- Sturdy hollow desktop test stand featuring identical geometry to a single chassis corner segment.
- Equipped with a 2nd TCA9548A multiplexer and ADS1115 breakout for isolated workbench testing and calibration of individual leg assemblies.
