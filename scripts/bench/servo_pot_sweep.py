#!/usr/bin/env python3
"""
Servo Potentiometer Sweep & Calibration Tool (`scripts/servo_pot_sweep.py`).

Purpose & Role:
    Drives a single servo on PCA9685 Board 1 (0x40) through automated angle profiles
    so you have your hands completely free to measure the internal potentiometer
    voltage with a multimeter, probe, or oscilloscope.

Features:
    - Step-and-Hold Mode: Stops at discrete angles (-60° to +60°) for N seconds.
    - Continuous Harmonic Sweep Mode: Smooth sinusoidal oscillation back and forth.
    - Interactive Calibration Table: Prompts for measured voltage and outputs CSV.
    - Safety: Automatically relaxes servo channel on exit / Ctrl+C.
"""

import argparse
import math
import sys
import time
from typing import List, Tuple

try:
    import smbus2
except ImportError:
    print("Error: smbus2 is required. Run 'pip install smbus2' or use uv.")
    sys.exit(1)


# PCA9685 Registers & Constants
_MODE1 = 0x00
_MODE2 = 0x01
_LED0_ON_L = 0x06
_PRESCALE = 0xFE
_RESTART = 0x80
_SLEEP = 0x10
_AI = 0x20
_OUTDRV = 0x04


class SimplePCA9685:
    """Minimal, self-contained PCA9685 controller for standalone bench testing."""

    def __init__(self, address: int = 0x40, bus_num: int = 1):
        self.address = address
        self.bus = smbus2.SMBus(bus_num)
        self._init_pca9685()

    def _init_pca9685(self):
        # Configure MODE2: Totem pole output
        self.bus.write_byte_data(self.address, _MODE2, _OUTDRV)
        # Enable Auto-Increment & wake up
        self.bus.write_byte_data(self.address, _MODE1, _AI)
        time.sleep(0.005)
        # Set 50 Hz PWM frequency (prescale ~121 for 25 MHz osc)
        freq = 50.0
        prescaleval = 25000000.0 / (4096.0 * freq) - 1.0
        prescale = int(round(prescaleval))
        oldmode = self.bus.read_byte_data(self.address, _MODE1) & 0x7F
        self.bus.write_byte_data(self.address, _MODE1, (oldmode & ~_RESTART) | _SLEEP)
        self.bus.write_byte_data(self.address, _PRESCALE, prescale)
        self.bus.write_byte_data(self.address, _MODE1, oldmode)
        time.sleep(0.005)
        self.bus.write_byte_data(self.address, _MODE1, oldmode | _RESTART | _AI)

    def set_pulse(self, channel: int, pulse_us: float):
        """Sets pulse width in microseconds (e.g. 1000 - 2000 µs)."""
        # 50 Hz -> period = 20,000 µs -> 4096 ticks -> ~4.8828 µs/tick
        ticks = int(pulse_us / (20000.0 / 4096.0))
        ticks = max(0, min(4095, ticks))
        reg = _LED0_ON_L + 4 * channel
        data = [0, 0, ticks & 0xFF, (ticks >> 8) & 0x0F]
        self.bus.write_i2c_block_data(self.address, reg, data)

    def set_angle(self, channel: int, angle_deg: float, pulse_range: float = 1000.0, center_us: float = 1500.0):
        """Converts angle in degrees (-90° to +90°) to pulse width."""
        pulse_us = center_us + (angle_deg / 90.0) * (pulse_range / 2.0)
        self.set_pulse(channel, pulse_us)
        return pulse_us

    def relax_channel(self, channel: int):
        """Disables PWM output completely on channel to relax servo."""
        reg = _LED0_ON_L + 4 * channel
        self.bus.write_i2c_block_data(self.address, reg, [0, 0, 0, 0x10])

    def close(self):
        try:
            self.bus.close()
        except Exception:
            pass


def run_step_mode(pca: SimplePCA9685, channel: int, min_deg: float, max_deg: float, step_deg: float, hold_sec: float, loop: bool):
    """Steps through angles with a hold pause at each step."""
    angles = []
    curr = min_deg
    while curr <= max_deg + 1e-6:
        angles.append(round(curr, 2))
        curr += step_deg

    print("\n" + "=" * 65)
    print(f"🔬 STEP-AND-HOLD MESSMODUS: Kanal {channel} auf 0x40")
    print(f"Bereich: {min_deg:.1f}° bis {max_deg:.1f}° | Schrittweite: {step_deg:.1f}° | Haltezeit: {hold_sec}s")
    print("Drücke Strg+C zum sauberen Beenden (Servo wird stromlos geschaltet).")
    print("=" * 65 + "\n")

    iteration = 1
    while True:
        print(f"--- Durchlauf #{iteration} ---")
        for i, angle in enumerate(angles, 1):
            pulse_us = pca.set_angle(channel, angle)
            print(f"[{i:02d}/{len(angles):02d}] 👉 Winkel: {angle:+6.1f}° | Puls: {pulse_us:6.1f} µs | ⏱  HALTEN ({hold_sec:.1f}s) -> [JETZT MESSEN]")
            
            # Countdown
            start_t = time.time()
            while time.time() - start_t < hold_sec:
                time.sleep(0.05)

        if not loop:
            print("\n✔ Durchlauf abgeschlossen.")
            break
        iteration += 1
        time.sleep(1.0)


def run_sweep_mode(pca: SimplePCA9685, channel: int, min_deg: float, max_deg: float, period_sec: float):
    """Continuous smooth harmonic oscillation."""
    mid_deg = (min_deg + max_deg) / 2.0
    amplitude = (max_deg - min_deg) / 2.0

    print("\n" + "=" * 65)
    print(f"🌊 KONTINUIERLICHER HARMONISCHER SWEEP: Kanal {channel} auf 0x40")
    print(f"Bereich: {min_deg:.1f}° bis {max_deg:.1f}° | Periode: {period_sec:.1f}s ({1.0/period_sec:.2f} Hz)")
    print("Drücke Strg+C zum Beenden (Servo wird stromlos geschaltet).")
    print("=" * 65 + "\n")

    start_time = time.time()
    last_print = 0.0

    while True:
        elapsed = time.time() - start_time
        # Harmonic Cosine profile
        progress = (elapsed % period_sec) / period_sec
        angle = mid_deg - amplitude * math.cos(2.0 * math.pi * progress)
        pulse_us = pca.set_angle(channel, angle)

        if elapsed - last_print >= 0.2:
            # Bar visualization
            span = max_deg - min_deg
            pos_ratio = max(0.0, min(1.0, (angle - min_deg) / span if span > 0 else 0.5))
            bar_len = 30
            idx = int(pos_ratio * bar_len)
            bar = [" "] * (bar_len + 1)
            bar[idx] = "█"
            bar_str = "[" + "".join(bar) + "]"
            sys.stdout.write(f"\rWinkel: {angle:+6.1f}° | Puls: {pulse_us:6.1f} µs  {bar_str}   ")
            sys.stdout.flush()
            last_print = elapsed

        time.sleep(0.02)


def run_table_mode(pca: SimplePCA9685, channel: int, min_deg: float, max_deg: float, step_deg: float):
    """Interactive table calibration where user inputs measured voltage."""
    angles = []
    curr = min_deg
    while curr <= max_deg + 1e-6:
        angles.append(round(curr, 2))
        curr += step_deg

    print("\n" + "=" * 65)
    print(f"📋 INTERAKTIVE KENNLINIEN-AUFNAHME: Kanal {channel} auf 0x40")
    print("Der Servo fährt jeden Winkel an und wartet auf die Eingabe der")
    print("am Poti gemessenen Spannung (in Volt). [Enter] überspringt den Punkt.")
    print("=" * 65 + "\n")

    results: List[Tuple[float, float, str]] = []

    for i, angle in enumerate(angles, 1):
        pulse_us = pca.set_angle(channel, angle)
        print(f"\n[{i:02d}/{len(angles):02d}] Winkel angefahren: {angle:+6.1f}° (Puls: {pulse_us:6.1f} µs)")
        val = input("   👉 Gemessene Spannung am Poti (in V): ").strip()
        results.append((angle, pulse_us, val if val else "N/A"))

    print("\n" + "=" * 65)
    print("📊 ERGEBNIS-TABELLE (Winkel vs. Poti-Spannung):")
    print("=" * 65)
    print(" Winkel [°] |  Puls [µs]  |  Spannung [V]")
    print("------------------------------------------")
    for angle, pulse_us, volt in results:
        print(f" {angle:+9.1f}  |  {pulse_us:9.1f}  |  {volt:>10}")
    print("=" * 65)


def main():
    parser = argparse.ArgumentParser(description="Servo Potentiometer Sweep & Calibration Tool")
    parser.add_argument("--channel", "-c", type=int, default=0, help="Servo channel on PCA9685 Board 1 (0-15, default: 0).")
    parser.add_argument("--i2c-bus", type=int, default=1, help="I2C bus number (default: 1).")
    parser.add_argument("--address", type=int, default=0x40, help="I2C address (default: 0x40).")
    parser.add_argument("--mode", "-m", choices=["step", "sweep", "table"], default="step",
                        help="Mode: 'step' (hold at discrete angles), 'sweep' (smooth continuous), 'table' (interactive prompt).")
    parser.add_argument("--min", type=float, default=-60.0, help="Min angle in degrees (default: -60.0°).")
    parser.add_argument("--max", type=float, default=60.0, help="Max angle in degrees (default: +60.0°).")
    parser.add_argument("--step", type=float, default=15.0, help="Step size in degrees for step/table mode (default: 15.0°).")
    parser.add_argument("--hold", type=float, default=3.0, help="Hold duration in seconds for step mode (default: 3.0s).")
    parser.add_argument("--period", type=float, default=5.0, help="Period in seconds for continuous sweep mode (default: 5.0s).")
    parser.add_argument("--loop", action="store_true", help="Repeat step mode continuously.")
    args = parser.parse_args()

    print(f"🔌 Verbinde mit PCA9685 auf 0x{args.address:02X} (Bus {args.i2c_bus}), Kanal {args.channel}...")
    try:
        pca = SimplePCA9685(address=args.address, bus_num=args.i2c_bus)
    except Exception as e:
        print(f"❌ Fehler bei Verbindung mit PCA9685: {e}")
        sys.exit(1)

    print(f"✔ PCA9685 bereit. Initialisiere Kanal {args.channel}...")

    try:
        if args.mode == "step":
            run_step_mode(pca, args.channel, args.min, args.max, args.step, args.hold, args.loop)
        elif args.mode == "sweep":
            run_sweep_mode(pca, args.channel, args.min, args.max, args.period)
        elif args.mode == "table":
            run_table_mode(pca, args.channel, args.min, args.max, args.step)
    except KeyboardInterrupt:
        print("\n\n⏹ Abbruch durch Benutzer (Strg+C).")
    finally:
        print(f"💤 Schalte Servo auf Kanal {args.channel} stromlos (Relax)...")
        pca.relax_channel(args.channel)
        pca.close()
        print("✔ Beendet.")


if __name__ == "__main__":
    main()
