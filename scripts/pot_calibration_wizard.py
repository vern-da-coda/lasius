#!/usr/bin/env python3
"""
Interactive Servo Potentiometer Calibration Wizard (`scripts/pot_calibration_wizard.py`).

Purpose & Role:
    Guides the user through an interactive calibration wizard:
    1. Smoothly drives the servo from neutral to the minimum limit (Step 0).
    2. Prompts the user for the measured voltage at each discrete angle step.
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
import sys
import time
from typing import List, Dict, Any, Tuple

try:
    import smbus2
except ImportError:
    print("Error: smbus2 is required. Run 'pip install smbus2' or use uv.")
    sys.exit(1)


# PCA9685 Registers
_MODE1 = 0x00
_MODE2 = 0x01
_LED0_ON_L = 0x06
_PRESCALE = 0xFE
_RESTART = 0x80
_SLEEP = 0x10
_AI = 0x20
_OUTDRV = 0x04


class WizardPCA9685:
    """Minimal PCA9685 driver with smooth transitions and safety relax."""

    def __init__(self, address: int = 0x40, bus_num: int = 1):
        self.address = address
        self.bus = smbus2.SMBus(bus_num)
        self.current_angle: float = 0.0
        self._init_pca9685()

    def _init_pca9685(self):
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

    def set_pulse(self, channel: int, pulse_us: float):
        ticks = int(pulse_us / (20000.0 / 4096.0))
        ticks = max(0, min(4095, ticks))
        reg = _LED0_ON_L + 4 * channel
        data = [0, 0, ticks & 0xFF, (ticks >> 8) & 0x0F]
        self.bus.write_i2c_block_data(self.address, reg, data)

    def angle_to_pulse(self, angle_deg: float, pulse_range: float = 1000.0, center_us: float = 1500.0) -> float:
        return center_us + (angle_deg / 90.0) * (pulse_range / 2.0)

    def move_smooth(self, channel: int, target_angle: float, speed_deg_per_sec: float = 60.0):
        """Smoothly interpolates to the target angle to prevent sudden mechanical jumps."""
        start_angle = self.current_angle
        delta = target_angle - start_angle
        distance = abs(delta)
        if distance < 0.5:
            self.set_pulse(channel, self.angle_to_pulse(target_angle))
            self.current_angle = target_angle
            return

        duration = max(0.1, distance / speed_deg_per_sec)
        steps = int(duration * 40)  # 40 Hz interpolation
        for step in range(1, steps + 1):
            t = step / steps
            # Smooth cosine interpolation
            smooth_t = (1.0 - math.cos(math.pi * t)) / 2.0
            angle = start_angle + delta * smooth_t
            self.set_pulse(channel, self.angle_to_pulse(angle))
            time.sleep(duration / steps)

        self.set_pulse(channel, self.angle_to_pulse(target_angle))
        self.current_angle = target_angle

    def relax_channel(self, channel: int):
        reg = _LED0_ON_L + 4 * channel
        self.bus.write_i2c_block_data(self.address, reg, [0, 0, 0, 0x10])

    def close(self):
        try:
            self.bus.close()
        except Exception:
            pass


def compute_linear_regression(points: List[Tuple[float, float, float]]) -> Dict[str, Any]:
    """
    Computes linear regression on (angle_deg, voltage_v) pairs.
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
    ss_yy = sum((y - mean_y) ** 2 for y in xs)

    if ss_xx == 0:
        return {}

    slope_v_per_deg = ss_xy / ss_xx
    intercept_v = mean_y - slope_v_per_deg * mean_x
    deg_per_volt = 1.0 / slope_v_per_deg if slope_v_per_deg != 0 else 0.0

    # R-squared
    ss_res = sum((y - (slope_v_per_deg * x + intercept_v)) ** 2 for x, y in zip(xs, ys))
    r_squared = 1.0 - (ss_res / ss_yy) if ss_yy > 0 else 1.0

    # Maximum angular reconstruction error
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
    parser.add_argument("--channel", "-c", type=int, default=15, help="Servo channel (default: 15).")
    parser.add_argument("--min", type=float, default=-60.0, help="Min angle in degrees (default: -60.0°).")
    parser.add_argument("--max", type=float, default=60.0, help="Max angle in degrees (default: +60.0°).")
    parser.add_argument("--step", type=float, default=15.0, help="Angle step size in degrees (default: 15.0°).")
    parser.add_argument("--name", type=str, default="servo_ch15", help="Identifier name for servo (default: servo_ch15).")
    parser.add_argument("--outdir", type=str, default="calibration_data", help="Output directory for reports.")
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("      🧙  LASIUS SERVO POTENTIOMETER CALIBRATION WIZARD  🧙")
    print("=" * 70)
    print(f"  • Servo:           Kanal {args.channel} (PCA9685 Board 1, 0x40)")
    print(f"  • Messbereich:     {args.min:+.1f}° bis {args.max:+.1f}° (Schrittweite: {args.step:.1f}°)")
    print(f"  • Kennung:         {args.name}")
    print("=" * 70)
    print("Drücke Strg+C jederzeit zum Abbruch (der Servo wird sicher stromlos geschaltet).\n")

    input("👉 Prüfe, ob die Messspitzen sitzen. Drücke [Enter] zum Starten...")

    pca = WizardPCA9685(address=0x40, bus_num=1)

    try:
        # Build angles list
        angles = []
        curr = args.min
        while curr <= args.max + 1e-6:
            angles.append(round(curr, 2))
            curr += args.step

        total_steps = len(angles)
        measurements: List[Tuple[float, float, float]] = []

        print(f"\n🚀 Fahre sanft zur Startposition (Schritt 0 / {args.min:+.1f}°)...")
        pca.move_smooth(args.channel, args.min, speed_deg_per_sec=40.0)
        time.sleep(0.5)

        for idx, angle in enumerate(angles):
            pulse_us = pca.angle_to_pulse(angle)
            if idx > 0:
                print(f"\n⏳ Fahre zu Schritt {idx + 1}/{total_steps} ({angle:+.1f}°)...")
                pca.move_smooth(args.channel, angle, speed_deg_per_sec=45.0)
                time.sleep(0.3)

            while True:
                prompt = (
                    f"[{idx + 1:02d}/{total_steps:02d}] 📍 Winkel: {angle:+6.1f}° | Puls: {pulse_us:6.1f} µs\n"
                    f"       👉 Gemessene Spannung am Multimeter in Volt (z.B. 1.45, 'r'=wiederholen, 'q'=abbrechen): "
                )
                val_str = input(prompt).strip()
                if val_str.lower() == 'q':
                    print("\n⏹ Wizard vorzeitig abgebrochen.")
                    return
                if val_str.lower() == 'r':
                    pca.move_smooth(args.channel, angle, speed_deg_per_sec=30.0)
                    continue

                val_clean = val_str.replace(',', '.')
                try:
                    voltage = float(val_clean)
                    if voltage < 0 or voltage > 10.0:
                        print("   ⚠️  Warnung: Ungewöhnliche Spannung. Bitte prüfen (0 bis 5V erwartet).")
                    measurements.append((angle, pulse_us, voltage))
                    break
                except ValueError:
                    print("   ❌ Ungültige Eingabe! Bitte eine Zahl eingeben (z. B. '1.45').")

        # Auswertung & Regression
        print("\n" + "=" * 70)
        print("🎉 Alle Messpunkte erfasst! Berechne lineare Kennlinie...")
        print("=" * 70)

        reg = compute_linear_regression(measurements)

        print("\n📊 ERGEBNIS-TABELLE:")
        print(" Schritt |  Winkel [°]  |  Puls [µs]  |  Gemessen [V]  |  Modell [V]  |  Fehler [mV]")
        print("-" * 76)
        for idx, (a, p, v) in enumerate(measurements, 1):
            v_model = reg["slope_v_per_deg"] * a + reg["intercept_v_0deg"]
            diff_mv = (v - v_model) * 1000.0
            print(f"  {idx:02d}/{total_steps:02d}  |   {a:+7.1f}    |   {p:7.1f}   |    {v:6.3f} V   |   {v_model:6.3f} V   |  {diff_mv:+6.1f} mV")
        print("-" * 76)

        print("\n📐 KINEMATISCHE KENNLINIEN-PARAMETER:")
        print(f"  • Steigung (Empfindlichkeit):     {reg['slope_mv_per_deg']:+.3f} mV / °  ({reg['slope_v_per_deg']:+.6f} V/°)")
        print(f"  • Umrechnungsfaktor:              {reg['deg_per_volt']:+.2f} ° / V")
        print(f"  • Nullpunkt-Spannung (bei 0°):    {reg['intercept_v_0deg']:.4f} V")
        print(f"  • Linearitätsgüte (R²):           {reg['r_squared']:.5f}  (1.00000 = perfekt)")
        print(f"  • Max. Winkel-Abweichung:         ±{reg['max_error_deg']:.2f}°")

        formula_str = f"Winkel [°] = (Spannung [V] - {reg['intercept_v_0deg']:.4f}) * {reg['deg_per_volt']:+.2f}"
        print(f"\n💡 FORMEL FÜR CLOSED-LOOP REGELUNG:\n   👉 {formula_str}")

        # Save to disk
        out_dir = Path(args.outdir)
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_base = f"{args.name}_calib_{ts}"

        # JSON Export
        export_payload = {
            "servo_name": args.name,
            "channel": args.channel,
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

        # CSV Export
        csv_path = out_dir / f"{filename_base}.csv"
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("step,angle_deg,pulse_us,measured_voltage_v,model_voltage_v,error_mv\n")
            for idx, (a, p, v) in enumerate(measurements, 1):
                v_model = reg["slope_v_per_deg"] * a + reg["intercept_v_0deg"]
                err_mv = (v - v_model) * 1000.0
                f.write(f"{idx},{a},{p},{v},{v_model:.4f},{err_mv:.2f}\n")

        print(f"\n💾 Kalibrierdaten gespeichert:")
        print(f"   • JSON: {json_path}")
        print(f"   • CSV:  {csv_path}")
        print("=" * 70)

        # Sanft zurück zu Neutral und Relax
        print("\n🏁 Fahre sanft zurück auf Neutral (0.0°)...")
        pca.move_smooth(args.channel, 0.0, speed_deg_per_sec=50.0)
        time.sleep(0.4)

    except KeyboardInterrupt:
        print("\n\n⏹ Abbruch durch Benutzer (Strg+C).")
    finally:
        print(f"💤 Schalte Servo auf Kanal {args.channel} stromlos (Relax)...")
        pca.relax_channel(args.channel)
        pca.close()
        print("✔ Abgeschlossen & Servo entspannt.\n")


if __name__ == "__main__":
    main()
