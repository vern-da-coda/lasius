# Lasius Hexapod: Wiring & Harnesses

---

[Index](../../../README.md) | [Software](../../../software/README.md) | [Hardware](../../../hardware/README.md) | [Docs](../../../docs/README.md) | [Data](../../../data/README.md) | [Scripts](../../../scripts/README.md) |<br>
[Mechanics](../../../hardware/mechanics/README.md) | [Electronics / Wiring](../../../hardware/electronics/wiring/README.md) |

---

This directory contains the complete electrical wiring and harness specifications for the **Hexapod:Lasius Robot** documented in **WireViz ("Cabling as Code")** format.

## 1. Hardware Components

| Component | Quantity | Function & Specifications |
| :--- | :---: | :--- |
| **TCA9548A** | 1× | 8-Channel I2C multiplexer (1.8V–5V, logic at 3.3V). Configured to address **`0x71`** via solder bridge on `A0`. |
| **ADS1115** | 6× | 16-Bit 4-channel precision ADCs (1 board per leg). All set to default address **`0x48`** across isolated sub-channels `CH0` to `CH5`. |
| **100 nF MLCC** | 18–24× | 0.1 µF 50V monolithic multi-layer ceramic capacitors as low-pass noise filters soldered directly between `Ax` and `GND`. |
| **Reely NR-645 MG BB** | 18× | Metal-gear servos (3 per leg: Coxa, Femur, Tibia). Internal potentiometer wiper wire exposed for closed-loop telemetry. |
| **PCA9685** | 2× | 16-Channel 12-bit PWM servo drivers on primary I2C bus (`0x40` Left, `0x42` Right). |
| **Omron D2F-L** | 6× | Tactile microswitches in foot tips wired to pin `A3` of each leg ADS1115 board. |

---

## 2. Wiring Plans & Schematics

### Plan 1: `01_i2c_sensor_bus_topology.yml`
* **Purpose:** Visualizes the I2C master hub topology from Raspberry Pi through the TCA9548A multiplexer to the 6 leg ADC boards.
* **Channel Allocation:**
  * `CH0`: Left Front Leg (LF, `0x48`)
  * `CH1`: Left Middle Leg (LM, `0x48`)
  * `CH2`: Left Rear Leg (LR, `0x48`)
  * `CH3`: Right Front Leg (RF, `0x48`)
  * `CH4`: Right Middle Leg (RM, `0x48`)
  * `CH5`: Right Rear Leg (RR, `0x48`)

<p align="center">
  <img src="01_i2c_sensor_bus_topology.svg" alt="I2C Sensor Bus Topology" width="850">
</p>

### Plan 2: `02_single_leg_feedback_harness.yml`
* **Purpose:** Detailed wiring harness for an individual 3-DOF leg assembly.
* **Signals & Filters:**
  * `A0`: Coxa servo potentiometer wiper + 100 nF to GND
  * `A1`: Femur servo potentiometer wiper + 100 nF to GND
  * `A2`: Tibia servo potentiometer wiper + 100 nF to GND
  * `A3`: Foot contact switch + 100 nF to GND
  * 3-pin PWM power and signal leads (Orange/Red/Brown) to PCA9685 driver block
* **Filter Cutoff Frequency:**
  $$f_c = \frac{1}{2 \pi \cdot R_{\text{pot}} \cdot C} \approx \frac{1}{2 \pi \cdot 2500\,\Omega \cdot 100\,\text{nF}} \approx 636\,\text{Hz}$$
  *(Effectively suppresses high-frequency PWM switching transients and motor brush noise).*

<p align="center">
  <img src="02_single_leg_feedback_harness.svg" alt="Single Leg Feedback Harness" width="850">
</p>

### Plan 3: `03_power_distribution.yml`
* **Purpose:** Power distribution rails, dual voltage regulators, and centralized star ground.
* **Branches:**
  * 2S/3S LiPo → 15A master power switch
  * High-Current UBEC (6.0V 15A Peak) → Servo V+ power terminals on both PCA9685 boards
  * Step-Down Converter (5.1V 4A) → Raspberry Pi 4 logic supply
  * Central star ground prevents ground bounces between high-current servo loads and precision ADC telemetry.

<p align="center">
  <img src="03_power_distribution.svg" alt="Power Distribution Rails" width="850">
</p>

---

## 3. Regenerating WireViz Schematics & BOMs

All diagrams can be compiled on demand without manual system packages using `uv`:

```bash
cd hardware/electronics/wiring
uv run wireviz 01_i2c_sensor_bus_topology.yml
uv run wireviz 02_single_leg_feedback_harness.yml
uv run wireviz 03_power_distribution.yml
```

WireViz automatically produces for each YAML definition:
* `.svg`: Scalable vector graphic for web and documentation
* `.png`: High-resolution raster preview
* `.html`: Interactive schematic with clickable component metadata
* `.bom.tsv`: Tabular bill of materials (connectors, wires, lengths, gauges)
