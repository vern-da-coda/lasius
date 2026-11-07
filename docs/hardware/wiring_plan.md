# Hexapod:Lasius – Wiring Plan: Electrical & Sensor Architecture

Complete electrical connection plans, I2C sensor bus topology, single leg feedback harnesses, and power distribution for Hexapod:Lasius.

Detailed hardware specifications and formulas:
- Master Specification: [`closed_loop_plan.md`](closed_loop_plan.md)
- WireViz Harness Sources & BOMs: [`../../hardware/electronics/wiring/README.md`](../../hardware/electronics/wiring/README.md)

---

## 1. I2C Sensor Bus Topology

Master I2C routing from Raspberry Pi 4 through the TCA9548A multiplexer (address `0x71`) to 6× ADS1115 16-bit ADC boards (address `0x48`), INA228 power monitors, and ToF distance sensors:

<p align="center">
  <img src="../../hardware/electronics/wiring/01_i2c_sensor_bus_topology.svg" alt="I2C Sensor Bus Topology" width="850">
</p>

---

## 2. Single Leg Feedback Harness (3-DOF + Contact Switch)

Modular wiring harness per leg connecting Coxa, Femur, and Tibia internal servo potentiometers and the tactile foot switch to the dedicated leg ADS1115 board with 100 nF RC low-pass filtering:

<p align="center">
  <img src="../../hardware/electronics/wiring/02_single_leg_feedback_harness.svg" alt="Single Leg Feedback Harness" width="850">
</p>

---

## 3. Power Distribution & Star Ground Scheme

Dual-rail power distribution with high-current UBEC (6.0V 15A Peak) for servos, buck converter (5.1V 4A) for Raspberry Pi 4 logic, and centralized star ground:

<p align="center">
  <img src="../../hardware/electronics/wiring/03_power_distribution.svg" alt="Power Distribution Rails" width="850">
</p>
