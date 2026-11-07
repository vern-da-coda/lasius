# Lasius Documentation

Specifications, architectural decisions, wiring schematics, and development roadmaps for the **Lasius** 18-DOF Hexapod robot.

---

## Documentation Index

### Hardware & Electronics
- [**Hardware Decisions & 3D Printing Specifications**](hardware/decisions.md):
  Comprehensive documentation of the physical architecture: 2S LiPo battery, 20A UBEC (6.0V servo bus), 5V/3A buck converter for Raspberry Pi, Adafruit STEMMA QT / Qwiic I2C sensor bus topology, BNO085 9-DOF IMU, INA228 power monitors, VL53L4CD ToF distance sensors, MCP23017 foot switch expander, and slicer/material settings for PETG limb parts.
- [**18-DOF Closed-Loop Feedback Plan**](hardware/closed_loop_plan.md):
  Architecture for closed-loop angle feedback by tapping internal servo potentiometers into 6× ADS1115 16-bit ADCs via a TCA9548A I2C multiplexer with 100 nF RC low-pass filtering.
- [**Electrical Wiring & Connection Plan**](hardware/wiring_plan.md):
  Detailed pinouts, bus addresses, and terminal blocks for the dual PCA9685 PWM drivers, sensor bus, and power distribution rails.

### Teleoperation & Controls
- [**Google Stadia Controller & Teleoperation Guide**](pilot/gamepad_stadia.md):
  Linux joystick driver (`/dev/input/js0`), raw axis mappings, button layouts, deadzone filtering, and Bluetooth pairing instructions for the Google Stadia Controller.

### Project Roadmap
- [**Project Roadmap & Backlog**](roadmap.md):
  Prioritized task list, sprint backlog, mechanical reconstruction goals, and feature milestones.
