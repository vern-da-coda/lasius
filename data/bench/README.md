# Lasius – Servo Potentiometer Calibration Data

This directory contains experimental calibration data and linear regression models for analog joint position feedback (internal potentiometer wiper voltage) of Reely NR-645 MG BB servomotors.

---

## 1. Overview & Test Setup

- **Device Under Test (DUT):** Reely NR-645 MG BB standard analog servo
- **Modification:** Wiper wire soldered directly to the feedback potentiometer center tap.
- **Signal:** Analog DC voltage referenced to servo ground (GND).
- **Drive Electronics:** PCA9685 Board 1 (`0x40`), channel slot 15 at 50 Hz PWM.
- **Logic Voltage:** 3.3V (Raspberry Pi 4).
- **Load Supply:** 5.0–6.0V (Bench power supply).
- **Measurement Sweep:** 9 discrete angle steps from $-60.0^\circ$ to $+60.0^\circ$ in $15^\circ$ increments via [`scripts/bench/pot_calibration_wizard.py`](../../scripts/bench/pot_calibration_wizard.py).

---

## 2. Calibration Results (Reely NR-645 MG BB)

### 2.1 Model Parameters (Linear Regression)

| Parameter | Value | Unit | Description |
| :--- | :--- | :--- | :--- |
| **Linearity Coefficient ($R^2$)** | **`0.999591`** | -- | 99.96% linearity across the full calibrated span |
| **Slope / Sensitivity ($m$)** | **`+7.589`** | $\text{mV} / ^\circ$ | Voltage shift per degree of deflection ($0.007589\,\text{V}/^\circ$) |
| **Conversion Scale ($k$)** | **`131.772`** | $^\circ / \text{V}$ | Angular displacement per volt |
| **Neutral Voltage ($V_{0^\circ}$)** | **`1.5633`** | $\text{V}$ | Wiper voltage at $0.0^\circ$ (1500 µs center pulse) |
| **Max Angular Deviation** | **`±1.45`** | $^\circ$ | Maximum angular residual under linear approximation |
| **Max Voltage Residual** | **`±11.0`** | $\text{mV}$ | Maximum residual voltage deviation |

### 2.2 Closed-Loop Conversion Formula

To reconstruct physical joint angle from an ADC voltage sample:

$$\theta(V) = (V_{\text{ADC}} - 1.5633\,\text{V}) \cdot 131.772^\circ$$

Inversely, to predict expected potentiometer voltage for a target angle:

$$V(\theta) = 1.5633\,\text{V} + (\theta \cdot 0.007589\,\text{V}/^\circ)$$

---

## 3. Empirical Measurement Dataset

| Step | Target Angle | PWM Pulse | Measured ($V$) | Model ($V$) | Residual ($\text{mV}$) | Angular Error |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | $-60.0^\circ$ | $1166.7\,\mu\text{s}$ | **1.11 V** | $1.108\,\text{V}$ | $+2.0\,\text{mV}$ | $+0.26^\circ$ |
| 2 | $-45.0^\circ$ | $1250.0\,\mu\text{s}$ | **1.22 V** | $1.222\,\text{V}$ | $-1.8\,\text{mV}$ | $-0.24^\circ$ |
| 3 | $-30.0^\circ$ | $1333.3\,\mu\text{s}$ | **1.34 V** | $1.336\,\text{V}$ | $+4.3\,\text{mV}$ | $+0.57^\circ$ |
| 4 | $-15.0^\circ$ | $1416.7\,\mu\text{s}$ | **1.44 V** | $1.450\,\text{V}$ | $-9.5\,\text{mV}$ | $-1.25^\circ$ |
| 5 | $0.0^\circ$ | $1500.0\,\mu\text{s}$ | **1.57 V** | $1.563\,\text{V}$ | $+6.7\,\text{mV}$ | $+0.88^\circ$ |
| 6 | $+15.0^\circ$ | $1583.3\,\mu\text{s}$ | **1.68 V** | $1.677\,\text{V}$ | $+2.8\,\text{mV}$ | $+0.37^\circ$ |
| 7 | $+30.0^\circ$ | $1666.7\,\mu\text{s}$ | **1.78 V** | $1.791\,\text{V}$ | $-11.0\,\text{mV}$ | $-1.45^\circ$ |
| 8 | $+45.0^\circ$ | $1750.0\,\mu\text{s}$ | **1.91 V** | $1.905\,\text{V}$ | $+5.2\,\text{mV}$ | $+0.68^\circ$ |
| 9 | $+60.0^\circ$ | $1833.3\,\mu\text{s}$ | **2.02 V** | $2.019\,\text{V}$ | $+1.3\,\text{mV}$ | $+0.18^\circ$ |

---

## 4. File Manifest

- [`../../docs/hardware/closed_loop_plan.md`](../../docs/hardware/closed_loop_plan.md): **Master Specification:** Complete 18-channel wiring plan (TCA9548A Mux + 6× ADS1115), solder jumper `A0` (`0x71`), RC low-pass filters & Python telemetry driver.
- [`servo_ch15_pot_calibration.json`](servo_ch15_pot_calibration.json): Machine-readable calibration dataset and regression parameters.
- [`servo_ch15_pot_calibration.csv`](servo_ch15_pot_calibration.csv): CSV tabular export for spreadsheet and data analysis pipelines.
- [`README.md`](README.md): Calibration methodology and equations.
