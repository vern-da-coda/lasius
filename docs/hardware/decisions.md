# Hexapod:Lasius – Final Hardware, Sensor & CAD Decisions

---

[Index](../../README.md) | [Software](../../software/README.md) | [Hardware](../../hardware/README.md) | [Docs](../../docs/README.md) | [Data](../../data/README.md) | [Scripts](../../scripts/README.md) |<br>
[Decisions](../../docs/hardware/decisions.md) | [Closed Loop](../../docs/hardware/closed_loop_plan.md) | [Wiring](../../docs/hardware/wiring_plan.md) | [Gamepad](../../docs/pilot/gamepad_stadia.md) | [Roadmap](../../docs/roadmap.md) |

---

> **Source:** *GitHub Lasius Project Assistance.pdf* & Iterative Hardware-as-Code Architecture Reviews  
> **Status:** November 2026

This document consolidates all final architectural decisions from the project specification for hardware upgrades, sensor integration (STEMMA QT / I2C), and 3D printing reconstruction (PETG).

---

## 1. Overall Concept & Development Roadmap

1. **Modular Sensor Tray & Femur Integration:**
   - Central electronics (`Raspberry Pi 4`, **Controllers** `0x40`/`0x42`, **Multiplexer** `0x71`, planned **IMU** `BNO085`, power monitors `INA228`/`INA260`) sit inside the chassis core (`electronics_tray`), with **1× Wandler** (`ADS1115 V280`, `0x48`) integrated inside each femur chamber and **ToF** (`VL53L4CD`/`VL53L5CX`) planned at the front.
   - *(Note: Earlier drafts planned a separate `MCP23017 (0x20)` GPIO expander for the 6 foot switches. That was simplified: each leg's **Omron D2F-L** microswitch connects directly to `A3` (with `10 kΩ` pull-up to `3.3V` + `100 nF` RC filter) on that leg's **Wandler**.)*
2. **Decoupled Single-Leg Docking Test Rig:**
   - A 3D-printed / bench **single-leg test setup** accommodates *one* leg (`LF` on `CH0`) along with its **Wandler** (`ADS1115 V280`) and foot switch, verified on `bkhexapod` (`Controller CH0` ↔ `Wandler A0`).
   - Enables isolated validation of **CAD fit, potentiometer calibration, tibia compliance, and stall/lag telemetry** on a single leg before assembling all 6 legs.
   - *(Note: The legacy concept of external AS5600 magnetic encoders on the Coxa axes has been completely abandoned — internal potentiometer feedback provides native 18-DOF telemetry for all 18 joints without mechanical air-gap alignment).*
3. **3.3V Logic Distribution & Real Breakout Ecosystem (`Controller` / `Multiplexer` / `Wandler`):**
   - Because the real purple **`PCA9548A` (`PW548A`)** breakout exposes `SDx / SCx` only on `CH0–CH7` (no integrated `3.3V / GND` pins per sub-channel, and `A0` tied externally to `3.3V`), all logic supplies (`VCC`/`VDD`/`VIN` + `GND`) are fanned out via a central **`3.3V / GND` perfboard distribution rail** tied once to `Star_Ground_Bus` (see [`hardware/electronics/wiring/README.md`](../../hardware/electronics/wiring/README.md) & [`hardware/electronics/TODO.md`](../../hardware/electronics/TODO.md)).

---

## 2. Actuation & Power Distribution (Existing & Specification)

| Component | Final Selection / Specification | Technical Notes & Implementation |
| :--- | :--- | :--- |
| **Servomotors (18×)** | **Reely NR-645 MG BB** (Standard analog servo, 59 g) | Metal gears, dual ball bearings, **25T spline (Futaba/Savöx compatible)**, dimensions $40.7 \times 20.5 \times 39.5\,\text{mm}$, stall torque ~9.6–11 kg·cm @ 6.0 V, stall current ~1.8–2.5 A per servo. |
| **PWM Drivers (2×)** | **PCA9685 16-Channel I2C** | Board 1 (Left): **`0x40`**, Board 2 (Right): **`0x42`** (A1 bridged). *Important:* `ALLCALL` (`0x70`) is disabled in driver software to prevent address collisions with the PCA9548 multiplexer. |
| **Power UBECs (2×)** | **2× Hobbywing BEC 10A V2-Car (`HW30603003`, 6.0 V)** | **Strict Dual-Rail Separation (IP67, 10 A cont / 15 A peak, $45 \times 20 \times 16.2\,\text{mm}$):** Mounted on `Body_Top` inside symmetric rear cooling cradles of [`chassis_rpi_mount.FCStd`](../../hardware/mechanics/models/custom/v2/parts/chassis/chassis_rpi_mount.FCStd) at **`X = -79.5, Y = ±21.5, Z = 56.52 mm`** (45° outer chamfers inside `Body_Top`, 3× bottom vent slots, ventilated via 2×4 rear canopy exhaust slots; outputs/ferrites pointing `+X` toward the central deck cutout). **Optional G2 ([`gaster_power_assembly.FCStd`](../../hardware/mechanics/models/custom/v2/gaster_power_assembly.FCStd)):** Outsourced to the 2-DoF Power-Gaster with 14 AWG battery feed and dual 16 AWG returns. |
| **Logic Power Supply** | **Separate 5V / 3A Buck Converter (`ubec_3a`)** | Mounted symmetrically on the 100 % port-free `+Y` flank of [`chassis_rpi_mount.FCStd`](../../hardware/mechanics/models/custom/v2/parts/chassis/chassis_rpi_mount.FCStd) at **`X = 0.0, Y = +39.5, Z = 56.52 mm`** directly beside the Pi 4 GPIO 5 V header (prevents brownouts/reboots during servo stall peaks; common star ground). |
| **Power Controls & Protection** | **Internal Hatch XT60 + Upright Top-Pull 25 A Mini-ATM Fuse + 2× Recessed Rear Mini Slide Switches** | **Top-Deck Rear Power Cockpit (`X ∈ [-127.0, -86.0 mm]`):** Clamped rigidly via both rear CFRP M3 spacer screws (`(-90.0, 0.0)` and `(-120.0, 0.0)`). **2× Mini Slide Switches** (`Switch_Logic_Pi` left `+Y` green, `Switch_Servos_Armed` right `-Y` red) sit flush-recessed in the 45° rear bevels (`(-116.0, ±14.5, Z = 59.0 mm)`), protected within the `Body_Top` carbon contour; **1× upright 25 A Mini-ATM fuse tower** (`(-105.0, 0.0, Z_flange = 78.8 mm)`) protrudes cleanly through a `17.0 × 11.2 mm` canopy aperture for tool-free top extraction. Battery XT60 is directly accessible via the extended `116 mm` hinged front-center Battery Hatch (`X = +36.0 mm` LiPo position). **Optional G2:** All controls & UBECs housed inside `gaster_power_assembly.FCStd`. |

---

## 3. Sensors & I2C Bus Architecture

### 3.1 I2C Address Plan & Multiplexing

To isolate the 6 leg ADC boards (**ADS1115**) and maintain a clean I2C bus hierarchy, an **8-channel multiplexer (TCA9548A)** is used:

- **Primary I2C Bus (`/dev/i2c-1` on Raspberry Pi, Daisy-Chain):**
  - `0x40`: **Controller Left (`PCA9685`)** (9 PWM leg channels `LF, LM, LR`)
  - `0x42`: **Controller Right (`PCA9685`)** (9 PWM leg channels `RF, RM, RR`, `A1` bridged)
  - `0x71`: **Multiplexer (`PCA9548A` / `PW548A` 8-Channel)** (`A0` wired to `3.3V` $\rightarrow$ `0x71`, eliminates boot conflict with PCA9685 `ALLCALL 0x70`)
  - `0x4A`: **Adafruit BNO085 9-DOF Orientation IMU** *(planned)* (Quaternions, gravity vector, linear acceleration)
- **Multiplexer Channels (`PCA9548A @ 0x71`, `SCx/SDx` + Central `3.3V/GND` Rail):**
  - `CH0`: **Wandler #1 (`ADS1115 V280`, Left Front: Coxa, Femur, Tibia, Foot)** (`0x48`)
  - `CH1`: **Wandler #2 (`ADS1115 V280`, Left Middle: Coxa, Femur, Tibia, Foot)** (`0x48`)
  - `CH2`: **Wandler #3 (`ADS1115 V280`, Left Rear: Coxa, Femur, Tibia, Foot)** (`0x48`)
  - `CH3`: **Wandler #4 (`ADS1115 V280`, Right Front: Coxa, Femur, Tibia, Foot)** (`0x48`)
  - `CH4`: **Wandler #5 (`ADS1115 V280`, Right Middle: Coxa, Femur, Tibia, Foot)** (`0x48`)
  - `CH5`: **Wandler #6 (`ADS1115 V280`, Right Rear: Coxa, Femur, Tibia, Foot)** (`0x48`)
  - `CH6`: **INA228 / INA260** *(planned)* (Current/voltage monitoring for servo rails)
  - `CH7`: **VL53L4CD / VL53L5CX Time-of-Flight (ToF)** *(planned)* in front fascia

### 3.2 Tactile Ground Contact Detection & Audio Feedback

- **Foot Contact Switches (6×):** **Omron D2F-L** subminiature lever microswitches (ultra-low actuation force ~0.75 N).
- **Interface:** Connected directly to pin **`A3`** (**Orange**) and `GND` (**Black**, `COM`) on each leg's **Wandler** (`ADS1115 V280`, `0x48`) with a soldered `10 kΩ` pull-up resistor to `VDD (3.3V)` and `100 nF` RC filter capacitor (eliminates the separate `MCP23017`).
- **Acoustic Status/Warning Buzzer:** **Passive Piezo Buzzer** *(planned)* wired to **GPIO 13 (`PWM1`, Pin 33)** and `GND` (Pin 34) on the Raspberry Pi 4 for multi-tone status chimes.

### 3.3 18-DOF Analog Closed-Loop Servo Feedback (Reely NR-645 MG BB)

- **Concept:** Direct tapping of wiper voltage across all 18 internal servo potentiometers for full real-time joint angle measurement, stall detection, and tactile foot contact sensing.
- **Empirical Model Parameters (`bkhexapod` Stage 3 verified):** `Controller CH0` ↔ `Wandler A0`: $R^2 = 0.999876$, sensitivity $+7.530\,\text{mV}/^\circ$ (`132.802 °/V`), zero point $1.5590\,\text{V}$ at $0^\circ$ (earlier `CH15` multimeter series in [`data/bench/`](../../data/bench/README.md): $R^2 = 0.999591$, $+7.589\,\text{mV}/^\circ$, $1.5633\,\text{V}$).
- **Architecture & Bus Design (100% Python on Raspberry Pi 4):**
  - **Multiplexer (`PCA9548A / PW548A @ 0x71`, `A0 → 3.3V`):** Prevents address collisions with PCA9685 `ALLCALL` (`0x70`) during bootup.
  - **6× Wandler (`ADS1115 V280`, `0x48` each):** Symmetric **1-board-per-leg** architecture on Mux channels `CH0`–`CH5`. Hardware verified: real `V280` pinout has **`SCL` before `SDA`** (`VDD | GND | SCL | SDA | ADDR | ALRT | A0–A3`) and tested silicon yields left-aligned **12-bit** steps (`2.0 mV` / step $\approx 0.26^\circ$). Reads `A0` (Coxa, White), `A1` (Femur, White), `A2` (Tibia, White; servo pot lines always white), and `A3` (Omron foot switch, Orange).
  - **Noise Suppression:** 24× **100 nF 50V MLCC ceramic capacitors** (`A0–A3` to `GND`, $f_c \approx 636\,\text{Hz}$) + 6× `10 kΩ` pull-up resistors (`A3` to `3.3V`) soldered directly at each **Wandler** header.
  - **Complete Schematic Documentation:** See [`closed_loop_plan.md`](closed_loop_plan.md) & [`hardware/electronics/wiring/README.md`](../../hardware/electronics/wiring/README.md).

---

## 4. Final Bill of Materials (BOM)

### 4.1 Sensors & Electronics

| Qty | Component / Part Number | Role in Hexapod:Lasius |
| :---: | :--- | :--- |
| **6×** | **Wandler: ADS1115 (`V280`) 4-Channel I2C ADC Breakouts** | 1 board per leg: Reads Coxa (`A0`), Femur (`A1`), Tibia (`A2`) pot voltages + Omron foot switch (`A3`) (`0x48` on Mux CH0–CH5; effective 12-bit / `2.0 mV` steps) |
| **1–2×** | **Multiplexer: PCA9548A (`PW548A`) / TCA9548A 8-Ch I2C Hub** | Central sensor hub at `0x71` (`A0 → 3.3V`). Isolates all 6 leg boards (`SDx/SCx` only; `3.3V/GND` via central rail) |
| **1×** | **Central `3.3V / GND` Distribution Perfboard** | Fans out Pi `Pin 1/17 (3.3V)` + `GND` (`100 nF + 10 µF` decoupling) to Controllers, Multiplexer & Wandlers (1× tie to `Star-GND`) |
| **100×** | **100 nF 50V MLCC + 10 kΩ Resistors** | Low-pass filter caps (`4×` per Wandler `A0–A3 → GND`, $f_c \approx 636\,\text{Hz}$) + `10 kΩ` pull-up (`A3 → 3.3V`) |
| **1×** | **Adafruit VL53L4CD / VL53L5CX ToF Sensor** *(planned)* | Short-range laser distance sensor in front nose (Mux CH7) |
| **1–2×** | **INA228 / INA260 Power Monitor** *(planned)* | Real-time current/voltage/power telemetry (Mux CH6) |
| **1×** | **Adafruit 9-DOF Orientation IMU – BNO085 (PID 4754)** | On-chip sensor fusion (Roll/Pitch/Yaw). CAD-integrated on Front Deck of [`chassis_rpi_mount.FCStd`](../../hardware/mechanics/models/custom/v2/parts/chassis/chassis_rpi_mount.FCStd) (`X = +75.0, Y = 0.0, Z = 58.32 mm`, [`bno085_board.FCStd`](../../hardware/mechanics/models/cots/bno085_board.FCStd), non-magnetic Nylon/Brass M2.5 screws; prefer `i2c-gpio` / UART-RVC / SPI on Pi 4 to avoid BCM2711 `i2c-1` clock-stretching issues) |
| **Assorted** | **Dupont / JST Wire Harnesses (Master Color Scheme)** | Standardized color coding across `3.3V/GND`, Mux `CH0–CH6`, and `A0–A3` (see [`hardware/electronics/wiring/README.md`](../../hardware/electronics/wiring/README.md)) |

### 4.2 Hardware, Switches & Fasteners

- **6–10× Omron D2F-L** subminiature lever microswitches (fastened with **M2 × 10 mm** screws/nuts inside Tibia).
- **2× Amass XT60BE-M** panel-mount male connectors with flange + **1× XT60H-F** female connector for power supply lead.
- **1× Passive Piezo Buzzer** (5V / 3.3V PWM compatible, 7.6 mm pin pitch / 12 mm diameter with 2-pin Dupont plug).
- **Fastener Assortment (A2 Stainless Steel, Hex Socket DIN 912):**
  - **M2 × 8 mm / 10 mm / 12 mm** (for STEMMA QT breakouts, Omron D2F-L, and servo horns).
  - **M3 × 8 mm / 12 mm / 16 mm / 20 mm** + nylon lock nuts DIN 985 (for C-brackets, clamshell Tibia, and standoffs).
- **6× Zylinderstifte Ø3 × 12 mm (A2 Edelstahl, DIN 7 / ISO 2338 / COTS `dowel_pin_3x12.FCStd`):** Gelenkdrehachsen für die Tarsus-Wippe im Tibia-Gabelkopf (beidseitig angefast, trockenlaufende Gleitlagerung im PETG).
- **Filament:** **PETG (Black & signal accent color)** — mandatory replacement for brittle PLA for all structural leg joints (layer adhesion and high impact toughness under bending).

---

## 5. Mechanical Redesign (CAD / 3D Printing)

### 5.1 Reinforced Coxa Bracket (Eliminating Stress Points)
- **Root Cause of Prior Failures:** Insufficient wall thickness at the transition between servo horn mount and lower counter-bearing pivot, plus notch sensitivity of PLA.
- **New Design:**
  - Reinforced C-bracket geometry printed in **PETG** (4–5 perimeters, 40–50% gyroid infill, printed flat on bed for optimal filament extrusion along tensile/bending lines).
  - **Mechanical Benefit from Potentiometer Feedback:** Because external AS5600 magnets are no longer required, the structural weakening caused by the magnet pocket is eliminated. The lower pivot pin is formed as a **solid cylinder**, drastically increasing bending stiffness at the pivot axis.

### 5.2 Modular Underbody Sensor Tray
- Mounted from below onto the existing chassis standoff pillars.
- Functions as a centralized, vibration-damped tray for the TCA9548A multiplexer, 6 ADS1115 leg modules, BNO085 IMU, and power monitors.
- **Elimination of Air-Gap Alignment:** No delicate bracket arms with $1.0\text{–}1.5\,\text{mm}$ magnet air-gaps under the rotating axes are required.
- Integrated **wire channels with strain relief** route 4-pin leg cables (PWM + potentiometer) cleanly to the center.

### 5.3 Clamshell Tibia with Compliant Meander Spring & Rocker-Tarsus
- **Clamshell Construction (Left/Right Half-Shells):** Two symmetrical half-shells printed flat on the print bed (maximum longitudinal strength, zero internal support structures) bolted with M3 screws.
- **Integrated Compliant Mechanism:**
  - A **PETG meander leaf spring (S-spring)** in the lower third of the Tibia dampens foot touchdown impacts by ~2–3 mm, protecting servo gears.
- **Rocker-Tarsus Foot Tip:**
  - The foot tip is mounted as a short rocker lever on an M3 pivot.
  - Upon ground contact, the rocker-tarsus tilts upward by ~1.5 mm against the meander spring, depressing the **Omron D2F-L microswitch** (or analog pressure sensor at pin `A3` of the leg ADS1115) against a defined **mechanical hard-stop**.
  - **Overload Protection:** Ground reaction forces are absorbed entirely by the printed hard-stop inside the housing — the microswitch itself is never crushed by the robot's weight.
- **Concealed Wiring:** Both microswitch wires run invisibly inside an internal channel between the two Tibia half-shells.

### 5.4 Single-Leg Docking Test Rig
- Sturdy hollow desktop test stand featuring identical geometry to a single chassis corner segment.
- Equipped with a 2nd TCA9548A multiplexer and ADS1115 breakout for isolated workbench testing and calibration of individual leg assemblies.

### 5.5 CAD Directory & Versioning Architecture (*Hardware-as-Code*)
- **3-Tier Hierarchy (`hardware/mechanics/models/` & `export/`):**
  1. **Origin (`cots/` vs. `custom/`):** Immutable COTS/standard components (`cots/`, including `servo_nr645.FCStd`, bearings, and M4 fasteners) are strictly separated from custom-engineered parts (`custom/`).
  2. **Evolutionary Generations (`custom/v1/`, `custom/v2/`):** `v1` preserves the reverse-engineered multi-plate/spacer baseline (with physical CNC carbon plates `body_bottom.FCStd` & `body_top.FCStd` frozen as hardware invariant); `v2` encapsulates the monolithic 3D-printed redesign with integrated ADS1115 chambers and internal cable routing.
  3. **System Entry Points vs. Components (`v{N}/` vs. `v{N}/parts/`):** Assemblies (`leg_assembly.FCStd`, `body_assembly.FCStd`) reside directly at the root of each generation folder (`custom/v{N}/`), while individual components are encapsulated in `custom/v{N}/parts/`.
- **Canonical Naming & Cross-Generation Inheritance:** Files use canonical, versionless names (`coxa.FCStd`, `femur.FCStd`, `tibia.FCStd`, `leg_assembly.FCStd`) rather than SemVer filename suffixes to keep FreeCAD `App::Link` references and Git history intact. Components unchanged between generations are linked relatively from the parent generation without file duplication.

---

## 6. Top-Deck Power Architecture, Monolithic Magnet Canopy & Evaluated Upgrade Paths (v2)

### 6.1 Verified Mechanical & Power Baseline (`0.0000 mm³` Collision Across All Assemblies)
- **Unified Top-Deck Power & Control Platform ([`chassis_rpi_mount.FCStd`](../../hardware/mechanics/models/custom/v2/parts/chassis/chassis_rpi_mount.FCStd)):** Consolidates the centered Raspberry Pi 4 (`(0, 0, Z = 59.80)` with 100 % unobstructed ports), 2× Hobbywing 10A V2-Car UBECs (`(-79.5, ±21.5)`), 1× 5V/3A Pi UBEC (`(0.0, +39.5)`), 2× recessed 45° rear slide switches (`(-116.0, ±14.5)`), the upright top-pull 25 A Mini-ATM fuse (`(-105.0, 0.0, Z_flange = 78.8)`), and the front-deck **Adafruit BNO085 9-DOF IMU** (`(+75.0, 0.0, Z_pcb = 58.32)`, [`bno085_board.FCStd`](../../hardware/mechanics/models/cots/bno085_board.FCStd), 4× non-magnetic M2.5 bosses, `> 5 mm` canopy clearance, maximized EMI distance to all UBECs & magnets) on `Body_Top`, rigidly anchored via 10× M3 screws including both rear CFRP spacer screws `(-90, 0)` & `(-120, 0)`.
- **Monolithic Single-Piece Magnet Canopy ([`chassis_canopy.FCStd`](../../hardware/mechanics/models/custom/v2/parts/chassis/chassis_canopy.FCStd)):** The redundant separate `chassis_service_cover` was permanently removed; the single-piece canopy integrates 5× 45° `'>>>'` Chevron louvers over the Pi 4 SoC, 2×4 rear exhaust vents over the Hobbywing heatsinks, 2× bottom-open 45° switch arches, and a `17.0 × 11.2 mm` top-pull fuse opening, lifting straight up (`+Z`) tool-free via magnets on the 4 pillars (`±48, ±36`).
- **Segmented 2-Level Sealed Monocoque Core & Closed Belly Pan ([`chassis_core_lower.FCStd`](../../hardware/mechanics/models/custom/v2/parts/chassis/chassis_core_lower.FCStd), [`chassis_core_upper.FCStd`](../../hardware/mechanics/models/custom/v2/parts/chassis/chassis_core_upper.FCStd), [`chassis_belly_pan.FCStd`](../../hardware/mechanics/models/custom/v2/parts/chassis/chassis_belly_pan.FCStd), [`chassis_battery_hatch.FCStd`](../../hardware/mechanics/models/custom/v2/parts/chassis/chassis_battery_hatch.FCStd)):** Moving all UBECs and controls to `Body_Top` yielded 100 % sealed seamless $G^1$ monocoque waist walls (preserving both Front `X = +85..+135` and Rear `X = -85..-132` dovetails), a dust-sealed skid plate with rear-bridge `VL53L5CX` (`X = -58.5 mm`), and a forward-center 2S LiPo (`X = +36.0 mm`, `116 mm` hinged hatch accepting packs up to `110 mm`) balancing the rear UBECs to `< 1 mm` CoG offset. Horizontally segmented at parametric `Z_SPLIT = 24.00 mm` with triple form-fit alignment and 4× `M3 × 50 mm` metal tie-rod standoffs ([`standoff_m3x50_round.FCStd`](../../hardware/mechanics/models/cots/standoff_m3x50_round.FCStd)) so Level 1 reprints independently and Level 2 prints 100 % support-free.
- **Separate Optional 2-DoF Power-Gaster ([`gaster_power_assembly.FCStd`](../../hardware/mechanics/models/custom/v2/gaster_power_assembly.FCStd)):** Retained as an independent, zero-collision Option G2 docking module with real NR-645 Pan/Tilt servos and full power-train relocation.

### 6.2 Evaluated Next-Iteration Upgrade Options (Non-Destructive Backlog)
The following design studies were evaluated without modifying the verified baseline CAD models (tracked in [`v2/TODO.md`](../../hardware/mechanics/models/custom/v2/TODO.md) & [`electronics/TODO.md`](../../hardware/electronics/TODO.md)):

1. **Rear Control Unit & Master-Switch Options (1–3):**
   - **Option 1 — `3-Stage Master` *(Recommended Low-Complexity)*:** Single `3P3T` mini slide switch (`OFF → LOGIC → ARMED`, mechanically prevents enabling servos before Pi boots; `< 0.5 mA` standby) + `6×6 mm` Pi Safe-Shutdown button (`GPIO3`, protects MicroSD card) + 2× 3 mm status LEDs (Green `5 V` / Red `6 V`) + top-pull `25 A` fuse as true `0.00 mA` galvanic disconnect.
   - **Option 2 — `30 A High-Side MOSFET Master`:** Compact `24×16 mm` 30 A high-side P-MOSFET / Pololu Power Switch board between UBECs (`< 10 µA` off-current, enables automatic Pi self-power-off after `shutdown`) + Master pushbutton + Pi Shutdown button + red `SERVOS ARM/KILL` DPST slide switch + status LEDs + `25 A` fuse.
   - **Option 3 — `Rear Telemetry Cockpit with Display`:** Combines Option 1 or 2 with a flush-mounted rear status display behind a canopy window.
2. **Evaluated Display Modules & Multi-Display Bus Isolation:**
   - **Candidates:**
     - `0.91"` I²C OLED (`128×32`, `38×12 mm`, SSD1306, ~3.90 €/pc): Slim rear visor; fixed `0x3C`, straight header pre-soldered, clip pocket required.
     - `0.96"` I²C OLED (`128×64`, `27.0×27.3 mm`, SSD1306, Mono Blue or fixed Dual-Zone Yellow `y=0..15` / Blue `y=16..63`, ~2.20–2.90 €/pc): Unpopulated header (90° flat solder), 4× M2 holes (`23×23 mm`), `0x3C/0x3D` address jumper. Fits rear slope cleanly if the `25 A` fuse shifts forward into the open `20 mm` UBEC center channel (`X = -76, Y = 0`). Yellow/Blue suits a rear status HUD; monochrome or RGB suits bionic head eyes.
     - `0.96"` SPI IPS TFT (`80×160`, ST7735, `~30×24 mm`, true 65k RGB): Compact full-color rear bevel option.
     - `1.54"` SPI IPS TFT (`240×240`, ST7789, `32×44 mm`, 65k RGB, `CS` pin exposed, ~7.50 €/pc): Too large for the narrow rear tip (`X = -102..-128`), but fits the wide empty front Canopy/deck zone (`X = +52..+98`) or a future bionic Head visor.
   - **Multi-Display Bus Architecture (Zero Real-Time Impact):** Connect all displays exclusively to Raspberry Pi 4's additional dedicated hardware I²C buses (`i2c-3`, `i2c-4`, `i2c-5` via `dtoverlay`) or hardware **SPI0 (`CE0`/`CE1`)** so display frame updates (~20–25 ms on I²C) never block the `50–100 Hz` closed-loop servo/ADC/IMU bus `i2c-1` (`~15–25 mA` per OLED, `~30–50 mA` per IPS TFT).


