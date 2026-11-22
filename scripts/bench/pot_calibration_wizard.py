#!/usr/bin/env python3
"""
Interactive & Automated Servo Potentiometer Calibration Wizard (`scripts/bench/pot_calibration_wizard.py`).

Purpose & Role:
    Guides the user through an interactive or fully automated calibration wizard:
    1. Smoothly drives the servo from neutral to the minimum limit (Step 0).
    2. Reads the potentiometer wiper voltage either:
       - Automatically via TCA9548A Multiplexer + ADS1115 ADC (--adc).
       - Manually via user prompt from a digital multimeter.
    3. Iterates step-by-step up to the maximum limit.
    4. Performs linear regression analysis (Slope, Intercept, R², Max Non-Linearity Error).
    5. Saves calibration curve to JSON and CSV for integration into Lasius closed-loop control.
    6. Automatically relaxes the servo upon completion or Ctrl+C.
"""

import argparse
from datetime import datetime
import json
import math
from pathlib import Path
import random
import sys
import time
from typing import List, Dict, Any, Tuple, Optional

try:
    import smbus2
    HAS_SMBUS = True
except ImportError:
    HAS_SMBUS = False


# PCA9685 Registers
_MODE1 = 0x00
_MODE2 = 0x01
_LED0_ON_L = 0x06
_PRESCALE = 0xFE
_RESTART = 0x80
_SLEEP = 0x10
_AI = 0x20
_OUTDRV = 0x04

# ADS1115 Registers & Bits
ADS_REG_CONVERSION = 0x00
ADS_REG_CONFIG = 0x01
ADS_CONFIG_OS_SINGLE = 0x8000
ADS_CONFIG_MUX_A0 = 0x4000
ADS_CONFIG_MUX_A1 = 0x5000
ADS_CONFIG_MUX_A2 = 0x6000
ADS_CONFIG_MUX_A3 = 0x7000
ADS_CONFIG_PGA_4_096V = 0x0200
ADS_CONFIG_MODE_SINGLE = 0x0100
ADS_CONFIG_DR_128SPS = 0x0080
ADS_CONFIG_CQUE_NONE = 0x0003

DEFAULT_MUX_ADDR = 0x71
DEFAULT_ADC_ADDR = 0x48


class MockI2CBus:
    """Simulates I2C bus behavior for development laptops without physical GPIOs."""

    def __init__(self, bus_num: int = 1):
        self.bus_num = bus_num
        self.mux_channel = 0
        self.current_angle = 0.0

    def write_byte(self, addr: int, val: int):
        if addr in (DEFAULT_MUX_ADDR, 0x70):
            self.mux_channel = val
            return
        raise OSError("Simulated I2C NACK")

    def write_byte_data(self, addr: int, reg: int, val: int):
        pass

    def read_byte_data(self, addr: int, reg: int) -> int:
        return 0x00

    def write_i2c_block_data(self, addr: int, reg: int, data: list):
        pass

    def read_i2c_block_data(self, addr: int, reg: int, length: int) -> list:
        if addr == DEFAULT_ADC_ADDR and reg == ADS_REG_CONVERSION:
            # Characteristic curve of Reely NR-645: ~1.563V at 0°, ~+7.53 mV/°
            jitter = (random.random() - 0.5) * 0.002
            v = 1.5633 + (self.current_angle * 0.007530) + jitter
            v = max(0.0, min(3.3, v))
            raw = int((v / 4.096) * 32767)
            raw = max(0, min(32767, raw))
            return [(raw >> 8) & 0xFF, raw & 0xFF]
        if addr == DEFAULT_ADC_ADDR and reg == ADS_REG_CONFIG:
            return [0x85, 0x83]  # Conversion complete
        return [0] * length

    def close(self):
        pass


def get_i2c_bus(bus_num: int = 1, use_mock: bool = False):
    """Instantiates a real smbus2.SMBus or MockI2CBus."""
    if use_mock:
        return MockI2CBus(bus_num)
    if not HAS_SMBUS:
        print("⚠️  [WARN] Python 'smbus2' ist nicht installiert. Verwende Mock-Modus (--mock).")
        return MockI2CBus(bus_num)
    try:
        return smbus2.SMBus(bus_num)
    except (FileNotFoundError, PermissionError) as e:
        print(f"⚠️  [WARN] /dev/i2c-{bus_num} nicht verfügbar ({e}). Verwende Mock-Modus.")
        return MockI2CBus(bus_num)


def set_tca9548a_channel(bus, mux_addr: int, channel: Optional[int]) -> bool:
    """Enables a specific multiplexer channel (0-7) or disables all channels (None)."""
    try:
        val = (1 << channel) if channel is not None and 0 <= channel <= 7 else 0x00
        bus.write_byte(mux_addr, val)
        time.sleep(0.005)
        return True
    except Exception:
        return False


def read_ads1115_channel(bus, adc_addr: int = DEFAULT_ADC_ADDR, channel: int = 0) -> Tuple[int, float]:
    """Reads a single-ended conversion from the specified ADS1115 channel (0-3)."""
    mux_bits = {
        0: ADS_CONFIG_MUX_A0,
        1: ADS_CONFIG_MUX_A1,
        2: ADS_CONFIG_MUX_A2,
        3: ADS_CONFIG_MUX_A3,
    }.get(channel, ADS_CONFIG_MUX_A0)

    config = (
        ADS_CONFIG_OS_SINGLE
        | mux_bits
        | ADS_CONFIG_PGA_4_096V
        | ADS_CONFIG_MODE_SINGLE
        | ADS_CONFIG_DR_128SPS
        | ADS_CONFIG_CQUE_NONE
    )

    data = [(config >> 8) & 0xFF, config & 0xFF]
    bus.write_i2c_block_data(adc_addr, ADS_REG_CONFIG, data)

    # Wait for conversion complete (~8ms at 128 SPS)
    for _ in range(25):
        time.sleep(0.002)
        cfg = bus.read_i2c_block_data(adc_addr, ADS_REG_CONFIG, 2)
        if (cfg[0] & 0x80) != 0:
            break

    res = bus.read_i2c_block_data(adc_addr, ADS_REG_CONVERSION, 2)
    raw = (res[0] << 8) | res[1]
    if raw > 32767:
        raw -= 65536

    volts = max(0.0, raw * 0.000125)
    return raw, volts


class WizardPCA9685:
    """PCA9685 driver with smooth transitions and safety relax."""

    def __init__(self, bus, address: int = 0x40):
        self.address = address
        self.bus = bus
        self.current_angle: float = 0.0
        self._init_pca9685()

    def _init_pca9685(self):
        try:
            self.bus.write_byte_data(self.address, _MODE2, _OUTDRV)
            self.bus.write_byte_data(self.address, _MODE1, _AI)
            time.sleep(0.005)
            freq = 50.0
            prescaleval = 25000000.0 / (4096.0 * freq) - 1.0
            prescale = max(3, min(255, int(round(prescaleval))))
            oldmode = self.bus.read_byte_data(self.address, _MODE1) & 0x7F
            self.bus.write_byte_data(self.address, _MODE1, (oldmode & ~_RESTART) | _SLEEP)
            self.bus.write_byte_data(self.address, _PRESCALE, prescale)
            self.bus.write_byte_data(self.address, _MODE1, oldmode)
            time.sleep(0.005)
            self.bus.write_byte_data(self.address, _MODE1, oldmode | _RESTART | _AI)
        except Exception:
            pass

    def set_pulse(self, channel: int, pulse_us: float):
        ticks = int(pulse_us / (20000.0 / 4096.0))
        ticks = max(0, min(4095, ticks))
        reg = _LED0_ON_L + 4 * channel
        data = [0, 0, ticks & 0xFF, (ticks >> 8) & 0x0F]
        try:
            self.bus.write_i2c_block_data(self.address, reg, data)
        except Exception:
            pass

    def angle_to_pulse(self, angle_deg: float, pulse_range: float = 1000.0, center_us: float = 1500.0) -> float:
        return center_us + (angle_deg / 90.0) * (pulse_range / 2.0)

    def move_smooth(self, channel: int, target_angle: float, speed_deg_per_sec: float = 60.0):
        """Smoothly interpolates to the target angle to prevent sudden mechanical jumps."""
        start_angle = self.current_angle
        delta = target_angle - start_angle
        distance = abs(delta)

        # Update mock bus if applicable
        if hasattr(self.bus, "current_angle"):
            self.bus.current_angle = target_angle

        if distance < 0.5:
            self.set_pulse(channel, self.angle_to_pulse(target_angle))
            self.current_angle = target_angle
            return

        duration = max(0.1, distance / speed_deg_per_sec)
        steps = int(duration * 40)
        for step in range(1, steps + 1):
            t = step / steps
            smooth_t = (1.0 - math.cos(math.pi * t)) / 2.0
            angle = start_angle + delta * smooth_t
            self.set_pulse(channel, self.angle_to_pulse(angle))
            if hasattr(self.bus, "current_angle"):
                self.bus.current_angle = angle
            time.sleep(duration / steps)

        self.set_pulse(channel, self.angle_to_pulse(target_angle))
        self.current_angle = target_angle

    def relax_channel(self, channel: int):
        reg = _LED0_ON_L + 4 * channel
        try:
            self.bus.write_i2c_block_data(self.address, reg, [0, 0, 0, 0x10])
        except Exception:
            pass


def compute_linear_regression(points: List[Tuple[float, float, float]]) -> Dict[str, Any]:
    """
    Computes linear regression on (angle_deg, pulse_us, voltage_v) tuples.
    Returns slope, intercept, R², and max deviation.
    """
    n = len(points)
    if n < 2:
        return {}

    xs = [p[0] for p in points]  # angles
    ys = [p[2] for p in points]  # voltages

    mean_x = sum(xs) / n
    mean_y = sum(ys) / n

    ss_xx = sum((x - mean_x) ** 2 for x in xs)
    ss_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    ss_yy = sum((y - mean_y) ** 2 for y in ys)

    if ss_xx == 0:
        return {}

    slope_v_per_deg = ss_xy / ss_xx
    intercept_v = mean_y - slope_v_per_deg * mean_x
    deg_per_volt = 1.0 / slope_v_per_deg if slope_v_per_deg != 0 else 0.0

    ss_res = sum((y - (slope_v_per_deg * x + intercept_v)) ** 2 for x, y in zip(xs, ys))
    r_squared = 1.0 - (ss_res / ss_yy) if ss_yy > 0 else 1.0

    max_err_deg = 0.0
    for x, _, y in points:
        calc_angle = (y - intercept_v) * deg_per_volt
        err = abs(calc_angle - x)
        if err > max_err_deg:
            max_err_deg = err

    return {
        "slope_v_per_deg": round(slope_v_per_deg, 6),
        "slope_mv_per_deg": round(slope_v_per_deg * 1000.0, 3),
        "deg_per_volt": round(deg_per_volt, 3),
        "intercept_v_0deg": round(intercept_v, 4),
        "r_squared": round(r_squared, 5),
        "max_error_deg": round(max_err_deg, 2)
    }


def main():
    parser = argparse.ArgumentParser(description="Lasius Servo Potentiometer Calibration Wizard")
    parser.add_argument("--channel", "-c", type=int, default=0, help="Servo channel on PCA9685 (default: 0).")
    parser.add_argument("--pca-addr", type=lambda x: int(x, 0), default=0x40, help="PCA9685 address (default: 0x40 Left, 0x42 Right).")
    parser.add_argument("--min", type=float, default=-60.0, help="Min angle in degrees (default: -60.0°).")
    parser.add_argument("--max", type=float, default=60.0, help="Max angle in degrees (default: +60.0°).")
    parser.add_argument("--step", type=float, default=15.0, help="Angle step size in degrees (default: 15.0°).")
    parser.add_argument("--name", type=str, default="servo_ch0", help="Identifier name for servo (default: servo_ch0).")
    parser.add_argument("--outdir", type=str, default="data/bench", help="Output directory for reports.")
    parser.add_argument("--bus", type=int, default=1, help="I2C bus number (default: 1).")
    parser.add_argument("--mock", action="store_true", help="Force mock I2C simulation mode.")

    # Automated ADC Options
    parser.add_argument("--adc", action="store_true", help="Automatically read voltage from ADS1115 via TCA9548A Multiplexer.")
    parser.add_argument("--mux-addr", type=lambda x: int(x, 0), default=DEFAULT_MUX_ADDR, help="TCA9548A multiplexer address (default: 0x71).")
    parser.add_argument("--mux-channel", type=int, default=0, help="TCA9548A sub-channel (0-5 for legs LF-RR, default: 0).")
    parser.add_argument("--adc-addr", type=lambda x: int(x, 0), default=DEFAULT_ADC_ADDR, help="ADS1115 ADC address (default: 0x48).")
    parser.add_argument("--adc-channel", type=int, default=0, choices=[0, 1, 2, 3], help="ADS1115 analog input (0=Coxa, 1=Femur, 2=Tibia, 3=Foot, default: 0).")
    parser.add_argument("--samples", type=int, default=5, help="Number of ADC samples to average per step (default: 5).")
    parser.add_argument("--auto", action="store_true", help="Fully automated sweep without waiting for user confirmation at each step.")

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("      🧙  LASIUS SERVO POTENTIOMETER CALIBRATION WIZARD  🧙")
    print("=" * 70)
    print(f"  • Servo:           Channel {args.channel} on PCA9685 (0x{args.pca_addr:02X})")
    print(f"  • Span:            {args.min:+.1f}° to {args.max:+.1f}° (Step: {args.step:.1f}°)")
    print(f"  • Identifier:      {args.name}")
    if args.adc:
        print(f"  • Mode:            AUTOMATED ADC (TCA9548A CH{args.mux_channel} @ 0x{args.mux_addr:02X} -> ADS1115 A{args.adc_channel} @ 0x{args.adc_addr:02X})")
        print(f"  • Auto-Advance:    {'YES' if args.auto else 'Interactive confirmation'}")
    else:
        print("  • Mode:            MANUAL MULTIMETER PROMPT")
    if args.mock:
        print("  • Hardware:        SIMULATED MOCK MODE")
    print("=" * 70)
    print("Press Ctrl+C at any time to abort (servo will be relaxed safely).\n")

    if not args.auto:
        input("👉 Check probe placement & power. Press [Enter] to start...")

    bus = get_i2c_bus(args.bus, use_mock=args.mock)
    pca = WizardPCA9685(bus=bus, address=args.pca_addr)

    try:
        angles = []
        curr = args.min
        while curr <= args.max + 1e-6:
            angles.append(round(curr, 2))
            curr += args.step

        total_steps = len(angles)
        measurements: List[Tuple[float, float, float]] = []

        print(f"\n🚀 Driving smoothly to starting angle (Step 0 / {args.min:+.1f}°)...")
        pca.move_smooth(args.channel, args.min, speed_deg_per_sec=40.0)
        time.sleep(0.5)

        for idx, angle in enumerate(angles):
            pulse_us = pca.angle_to_pulse(angle)
            if idx > 0:
                if not args.auto:
                    print(f"\n⏳ Moving to step {idx + 1}/{total_steps} ({angle:+.1f}°)...")
                pca.move_smooth(args.channel, angle, speed_deg_per_sec=45.0)
                time.sleep(0.35)

            if args.adc:
                # Automatic ADC reading via Multiplexer + ADS1115
                set_tca9548a_channel(bus, args.mux_addr, args.mux_channel)
                samples = []
                for _ in range(args.samples):
                    _, v_sample = read_ads1115_channel(bus, args.adc_addr, args.adc_channel)
                    samples.append(v_sample)
                    time.sleep(0.015)
                voltage = sum(samples) / len(samples)

                # Hard Limit Safety Check
                if voltage > 3.30:
                    print(f"\n⚠️  CRITICAL: Voltage {voltage:.3f}V exceeds 3.30V limit! Aborting for hardware safety.")
                    return

                bar_len = 24
                filled = int((min(3.3, voltage) / 3.3) * bar_len)
                bar = "█" * filled + "░" * (bar_len - filled)
                status_line = f"[{idx + 1:02d}/{total_steps:02d}] 📍 {angle:+6.1f}° | Pulse: {pulse_us:6.1f} µs | ADC A{args.adc_channel}: {voltage:6.3f} V [{bar}]"

                if args.auto:
                    print(f"  ✔ {status_line}")
                    measurements.append((angle, pulse_us, voltage))
                    time.sleep(0.1)
                else:
                    print(f"\n{status_line}")
                    ans = input("       👉 Press [Enter] to accept, 'r' to re-measure, 'q' to abort: ").strip().lower()
                    if ans == 'q':
                        print("\n⏹ Wizard aborted.")
                        return
                    if ans == 'r':
                        continue
                    measurements.append((angle, pulse_us, voltage))
            else:
                # Manual multimeter input prompt
                while True:
                    prompt = (
                        f"[{idx + 1:02d}/{total_steps:02d}] 📍 Angle: {angle:+6.1f}° | Pulse: {pulse_us:6.1f} µs\n"
                        f"       👉 Measured multimeter voltage in Volts (e.g. 1.45, 'r'=retry, 'q'=abort): "
                    )
                    val_str = input(prompt).strip()
                    if val_str.lower() == 'q':
                        print("\n⏹ Wizard aborted.")
                        return
                    if val_str.lower() == 'r':
                        pca.move_smooth(args.channel, angle, speed_deg_per_sec=30.0)
                        continue

                    val_clean = val_str.replace(',', '.')
                    try:
                        voltage = float(val_clean)
                        if voltage < 0 or voltage > 5.0:
                            print("   ⚠️  Warning: Unusual voltage reading. Please verify (expected 0 to 3.3V).")
                        measurements.append((angle, pulse_us, voltage))
                        break
                    except ValueError:
                        print("   ❌ Invalid input! Please enter a number (e.g. '1.45').")

        # Disable MUX sub-channel after readings
        if args.adc:
            set_tca9548a_channel(bus, args.mux_addr, None)

        # Evaluation & Linear Regression
        print("\n" + "=" * 70)
        print("🎉 All points recorded! Computing linear characteristic curve...")
        print("=" * 70)

        reg = compute_linear_regression(measurements)

        print("\n📊 RESULT TABLE:")
        print(" Step  |  Angle [°]  |  Pulse [µs]  |  Measured [V]  |  Model [V]  |  Error [mV]")
        print("-" * 76)
        for idx, (a, p, v) in enumerate(measurements, 1):
            v_model = reg["slope_v_per_deg"] * a + reg["intercept_v_0deg"]
            diff_mv = (v - v_model) * 1000.0
            print(f"  {idx:02d}/{total_steps:02d} |   {a:+7.1f}   |   {p:7.1f}    |    {v:6.3f} V   |   {v_model:6.3f} V  |  {diff_mv:+6.1f} mV")
        print("-" * 76)

        print("\n📐 KINEMATIC CALIBRATION PARAMETERS:")
        print(f"  • Slope (Sensitivity):            {reg['slope_mv_per_deg']:+.3f} mV / °  ({reg['slope_v_per_deg']:+.6f} V/°)")
        print(f"  • Conversion Scale Factor:        {reg['deg_per_volt']:+.2f} ° / V")
        print(f"  • Zero-Point Voltage (at 0°):     {reg['intercept_v_0deg']:.4f} V")
        print(f"  • Linearity Coefficient (R²):     {reg['r_squared']:.5f}  (1.00000 = ideal)")
        print(f"  • Max Angle Deviation:            ±{reg['max_error_deg']:.2f}°")

        formula_str = f"Angle [°] = (Voltage [V] - {reg['intercept_v_0deg']:.4f}) * {reg['deg_per_volt']:+.2f}"
        print(f"\n💡 CLOSED-LOOP CONVERSION FORMULA:\n   👉 {formula_str}")

        # Save to disk
        out_dir = Path(args.outdir)
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_base = f"{args.name}_calib_{ts}"

        export_payload = {
            "servo_name": args.name,
            "channel": args.channel,
            "pca_address": hex(args.pca_addr),
            "timestamp": datetime.now().isoformat(),
            "angle_range": [args.min, args.max],
            "step_size": args.step,
            "formula": formula_str,
            "fit": reg,
            "points": [
                {"step": i+1, "angle_deg": a, "pulse_us": p, "measured_voltage_v": v}
                for i, (a, p, v) in enumerate(measurements)
            ]
        }
        json_path = out_dir / f"{filename_base}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(export_payload, f, indent=2)

        csv_path = out_dir / f"{filename_base}.csv"
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("step,angle_deg,pulse_us,measured_voltage_v,model_voltage_v,error_mv\n")
            for idx, (a, p, v) in enumerate(measurements, 1):
                v_model = reg["slope_v_per_deg"] * a + reg["intercept_v_0deg"]
                err_mv = (v - v_model) * 1000.0
                f.write(f"{idx},{a},{p},{v},{v_model:.4f},{err_mv:.2f}\n")

        print(f"\n💾 Calibration saved:")
        print(f"   • JSON: {json_path}")
        print(f"   • CSV:  {csv_path}")
        print("=" * 70)

        # Smooth return to neutral and relax
        print("\n🏁 Returning smoothly to neutral (0.0°)...")
        pca.move_smooth(args.channel, 0.0, speed_deg_per_sec=50.0)
        time.sleep(0.4)

    except KeyboardInterrupt:
        print("\n\n⏹ Aborted by user (Ctrl+C).")
    finally:
        print(f"💤 Relaxing servo channel {args.channel} (PWM off)...")
        pca.relax_channel(args.channel)
        bus.close()
        print("✔ Finished & servo relaxed.\n")


if __name__ == "__main__":
    main()
