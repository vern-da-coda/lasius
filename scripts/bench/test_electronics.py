#!/usr/bin/env python3
"""
Lasius Hexapod - Electronics Testbench & I2C Sensor Bus Diagnostic Utility.
(`scripts/bench/test_electronics.py`)

Purpose & Role:
    Automated and interactive diagnostic utility for the electronics testbench:
    - Verifies primary I2C bus 1 connectivity (Raspberry Pi 4).
    - Detects TCA9548A 8-channel I2C multiplexer (default address 0x71).
    - Checks for PCA9685 servo drivers (0x40, 0x42) and guards against 0x70 ALLCALL conflict.
    - Switches through TCA9548A sub-channels (CH0 to CH7) and scans child devices.
    - Tests ADS1115 16-bit 4-channel ADCs (address 0x48) on multiplexer channels.
    - Reads analog input channels (A0 to A3) in real-time with voltage calculation.
    - Includes a `--mock` mode for offline dry-run testing on development laptops.

Usage:
    # 1. Full bus and multiplexer diagnostic scan
    python3 scripts/bench/test_electronics.py --scan

    # 2. Step-by-step verification (Steps 1 to 6)
    python3 scripts/bench/test_electronics.py --step 2
    python3 scripts/bench/test_electronics.py --step 3
    python3 scripts/bench/test_electronics.py --step 5
    python3 scripts/bench/test_electronics.py --step 6

    # 3. Live analog voltage monitor on ADS1115 channel A0 (via MUX CH0)
    python3 scripts/bench/test_electronics.py --channel 0 --read-analog 0

    # 4. Offline dry-run simulation
    python3 scripts/bench/test_electronics.py --scan --mock
"""

import argparse
import math
import sys
import time
from typing import Dict, List, Optional, Tuple

try:
    import smbus2
    HAS_SMBUS = True
except ImportError:
    HAS_SMBUS = False


# Default I2C Addresses in Lasius Topology
DEFAULT_MUX_ADDR = 0x71      # TCA9548A with solder bridge A0 closed
FALLBACK_MUX_ADDR = 0x70     # TCA9548A default unbridged (warns of PCA9685 conflict)
DEFAULT_ADC_ADDR = 0x48      # ADS1115 with ADDR connected to GND
PCA9685_BOARD1_ADDR = 0x40   # Left PCA9685
PCA9685_BOARD2_ADDR = 0x42   # Right PCA9685 (A1 closed)

# ADS1115 Register Map
ADS_REG_CONVERSION = 0x00
ADS_REG_CONFIG = 0x01
ADS_REG_LO_THRESH = 0x02
ADS_REG_HI_THRESH = 0x03

# ADS1115 Config Register Bitmasks
ADS_CONFIG_OS_SINGLE = 0x8000   # Start single conversion
ADS_CONFIG_MUX_A0 = 0x4000      # AINP = AIN0, AINN = GND
ADS_CONFIG_MUX_A1 = 0x5000      # AINP = AIN1, AINN = GND
ADS_CONFIG_MUX_A2 = 0x6000      # AINP = AIN2, AINN = GND
ADS_CONFIG_MUX_A3 = 0x7000      # AINP = AIN3, AINN = GND
ADS_CONFIG_PGA_4_096V = 0x0200  # +/-4.096V range (1 LSB = 0.125 mV)
ADS_CONFIG_PGA_2_048V = 0x0400  # +/-2.048V range (1 LSB = 0.0625 mV)
ADS_CONFIG_MODE_SINGLE = 0x0100 # Single-shot mode
ADS_CONFIG_DR_128SPS = 0x0080   # 128 samples per second
ADS_CONFIG_CMODE_TRAD = 0x0000  # Traditional comparator
ADS_CONFIG_CPOL_ACTVLOW = 0x0000# Active low
ADS_CONFIG_CLAT_NONLAT = 0x0000 # Non-latching
ADS_CONFIG_CQUE_NONE = 0x0003   # Disable comparator


class MockI2CBus:
    """Simulates I2C bus behavior for development laptops without physical GPIOs."""

    def __init__(self, bus_num: int = 1):
        self.bus_num = bus_num
        self.mux_channel = 0
        self.mock_voltages = {0: 1.65, 1: 0.82, 2: 2.45, 3: 0.0}

    def write_quick(self, addr: int):
        valid_addrs = {DEFAULT_MUX_ADDR, PCA9685_BOARD1_ADDR, PCA9685_BOARD2_ADDR}
        if addr in valid_addrs:
            return
        if addr == DEFAULT_ADC_ADDR and self.mux_channel in (0, 1, 2, 3, 4, 5):
            return
        raise OSError("Simulated I2C NACK")

    def write_byte(self, addr: int, val: int):
        if addr == DEFAULT_MUX_ADDR:
            self.mux_channel = val
            return
        raise OSError("Simulated I2C NACK")

    def write_i2c_block_data(self, addr: int, reg: int, data: list):
        if addr in (DEFAULT_MUX_ADDR, DEFAULT_ADC_ADDR):
            return
        raise OSError("Simulated I2C NACK")

    def read_i2c_block_data(self, addr: int, reg: int, length: int) -> list:
        if addr == DEFAULT_ADC_ADDR and reg == ADS_REG_CONVERSION:
            v = self.mock_voltages.get(0, 1.65)
            # Add subtle jitter
            raw = int((v / 4.096) * 32767)
            raw = max(0, min(32767, raw))
            return [(raw >> 8) & 0xFF, raw & 0xFF]
        if addr == DEFAULT_ADC_ADDR and reg == ADS_REG_CONFIG:
            return [0x85, 0x83] # Conversion complete
        return [0] * length

    def close(self):
        pass


def get_i2c_bus(bus_num: int = 1, use_mock: bool = False):
    """Instantiates a real smbus2.SMBus or MockI2CBus."""
    if use_mock:
        return MockI2CBus(bus_num)
    if not HAS_SMBUS:
        print("⚠️  [WARN] Python 'smbus2' ist nicht installiert.")
        print("    Verwende simulierten Mock-Modus (--mock) für Testzwecke.")
        return MockI2CBus(bus_num)
    try:
        return smbus2.SMBus(bus_num)
    except FileNotFoundError:
        print(f"⚠️  [ERROR] /dev/i2c-{bus_num} nicht gefunden (kein Raspberry Pi Hardware-Bus).")
        print("    Schalte automatisch auf Mock-Modus um.")
        return MockI2CBus(bus_num)
    except PermissionError:
        print(f"❌ [PERM] Zugriff auf /dev/i2c-{bus_num} verweigert!")
        print("    Führe folgenden Befehl aus: sudo usermod -aG i2c $USER")
        sys.exit(1)


def scan_bus_addresses(bus) -> List[int]:
    """Scans all possible standard I2C addresses (0x08 to 0x77)."""
    found = []
    for addr in range(0x08, 0x78):
        try:
            bus.write_quick(addr)
            found.append(addr)
        except (OSError, Exception):
            pass
    return found


def set_tca9548a_channel(bus, mux_addr: int, channel: Optional[int]) -> bool:
    """Enables a specific multiplexer channel (0-7) or disables all channels (None)."""
    try:
        val = (1 << channel) if channel is not None and 0 <= channel <= 7 else 0x00
        bus.write_byte(mux_addr, val)
        time.sleep(0.005) # Allow bus stabilization
        return True
    except Exception as e:
        return False


def read_ads1115_channel(bus, adc_addr: int = DEFAULT_ADC_ADDR, channel: int = 0) -> Tuple[int, float]:
    """
    Reads a single-ended conversion from the specified ADS1115 channel (0-3).
    Returns (raw_counts_16bit, voltage_volts).
    """
    mux_bits = {
        0: ADS_CONFIG_MUX_A0,
        1: ADS_CONFIG_MUX_A1,
        2: ADS_CONFIG_MUX_A2,
        3: ADS_CONFIG_MUX_A3,
    }.get(channel, ADS_CONFIG_MUX_A0)

    # 4.096V Range, Single-Shot, 128 SPS
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

    # Read 16-bit conversion register
    res = bus.read_i2c_block_data(adc_addr, ADS_REG_CONVERSION, 2)
    raw = (res[0] << 8) | res[1]
    # Convert two's complement 16-bit signed integer
    if raw > 32767:
        raw -= 65536

    # 4.096V scale: 1 LSB = 0.125 mV = 0.000125 V
    volts = max(0.0, raw * 0.000125)
    return raw, volts


def run_full_scan(bus, mux_addr: int = DEFAULT_MUX_ADDR, adc_addr: int = DEFAULT_ADC_ADDR):
    """Executes a complete scan of the primary bus and all multiplexer sub-busses."""
    print("\n" + "=" * 65)
    print("🔍 Lasius Hexapod - I2C Topologie & Hardware-Scan")
    print("=" * 65)

    # 1. Primary Bus Scan
    primary = scan_bus_addresses(bus)
    print(f"Haupt-Bus (I2C1): {len(primary)} Gerät(e) erkannt")
    for a in primary:
        desc = ""
        if a == 0x40: desc = "✔ PCA9685 Linke Servos (Default)"
        elif a == 0x42: desc = "✔ PCA9685 Rechte Servos (A1 geschlossen)"
        elif a == 0x71: desc = "✔ TCA9548A Multiplexer (A0 geschlossen, konfliktfrei!)"
        elif a == 0x70: desc = "⚠️  TCA9548A auf 0x70 (ACHTUNG: Konflikt mit PCA9685 ALLCALL!)"
        elif a == 0x48: desc = "✔ ADS1115 ADC (Direkt am Hauptbus)"
        print(f"  • Adresse 0x{a:02X} : {desc}")

    # 2. Check Multiplexer
    has_mux = mux_addr in primary or FALLBACK_MUX_ADDR in primary
    active_mux = mux_addr if mux_addr in primary else (FALLBACK_MUX_ADDR if FALLBACK_MUX_ADDR in primary else None)

    if not has_mux:
        print("\n❌ TCA9548A Multiplexer NICHT auf dem Hauptbus gefunden.")
        print("   Troubleshooting:")
        print("   1. 3.3V Versorgungsspannung (Pi Pin 1) und GND prüfen.")
        print("   2. SDA (Pi Pin 3) an SDA und SCL (Pi Pin 5) an SCL prüfen.")
        print("   3. Adress-Jumper prüfen: Ist A0 auf 3.3V / geschlossen (0x71)?")
        print("=" * 65 + "\n")
        return False

    print(f"\n✔ TCA9548A aktiv auf Adresse 0x{active_mux:02X}")
    if active_mux == FALLBACK_MUX_ADDR:
        print("  ⚠️  WARNUNG: Multiplexer läuft auf Basisadresse 0x70.")
        print("      Schließe die Lötbrücke A0, um Konflikte mit dem PCA9685 All-Call zu vermeiden!")

    # 3. Sub-Bus Scanning (CH0 - CH7)
    print("\nScanne Multiplexer-Sub-Kanäle (CH0 bis CH7)...")
    sub_devices = {}
    for ch in range(8):
        set_tca9548a_channel(bus, active_mux, ch)
        devs = [a for a in scan_bus_addresses(bus) if a != active_mux]
        sub_devices[ch] = devs
        dev_str = ", ".join(f"0x{d:02X}" for d in devs) if devs else "(keine Geräte)"
        
        # Identify expected devices per Lasius wiring topology
        leg_names = {0: "Left Front", 1: "Left Middle", 2: "Left Rear", 3: "Right Front", 4: "Right Middle", 5: "Right Rear"}
        role = f"Leg {leg_names.get(ch)} ADC" if ch in leg_names else ("INA228 Power Monitor" if ch == 6 else "VL53L4CD ToF Sensor")
        
        status_icon = "✔" if adc_addr in devs else "•"
        print(f"  {status_icon} CH{ch} ({role:22s}): {dev_str}")

    # Disable all sub-channels
    set_tca9548a_channel(bus, active_mux, None)

    print("-" * 65)
    print("Zusammenfassung:")
    adc_count = sum(1 for ch in range(6) if adc_addr in sub_devices.get(ch, []))
    print(f"• Erkannte Leg-ADCs (ADS1115 auf 0x48): {adc_count} von 6")
    print("=" * 65 + "\n")
    return True


def run_analog_monitor(bus, mux_addr: int, channel: int, adc_ch: int):
    """Live streaming console monitor for an ADS1115 analog input channel."""
    print(f"\n📡 Starte Live-Spannungsmessung auf MUX CH{channel} -> ADS1115 A{adc_ch}...")
    print("   Drücke Strg+C zum Beenden.\n")

    set_tca9548a_channel(bus, mux_addr, channel)
    try:
        while True:
            raw, volts = read_ads1115_channel(bus, DEFAULT_ADC_ADDR, adc_ch)
            # Visualize as horizontal bar (0.0V to 3.3V)
            bar_len = 30
            filled = int((min(3.3, volts) / 3.3) * bar_len)
            bar = "█" * filled + "░" * (bar_len - filled)
            sys.stdout.write(f"\r  A{adc_ch}: {volts:6.3f} V | Counts: {raw:6d} | [{bar}]")
            sys.stdout.flush()
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\n\n⏹ Messung beendet.")
    finally:
        set_tca9548a_channel(bus, mux_addr, None)


def run_step_guide(bus, step: int, mux_addr: int = DEFAULT_MUX_ADDR):
    """Executes dedicated verification for a specific Bring-up step (1 to 6)."""
    print("\n" + "=" * 65)
    print(f"🛠 Elektronik-Testbench - Schritt {step} von 6")
    print("=" * 65)

    if step == 1:
        print("Schritt 1: Vorbereitung & Adresskonfiguration")
        print("• TCA9548A Adresse auf 0x71 konfigurieren:")
        print("  Schließe die Lötbrücke 'A0' auf dem TCA9548A Breakout")
        print("  (oder verbinde Pin A0 fest mit 3.3V).")
        print("• Grund: Die Standardadresse 0x70 kollidiert mit dem PCA9685 All-Call-Modus.")
        print("• Prüfe, dass alle Logiksignale strikt auf 3.3V laufen (Raspberry Pi Pin 1).")

    elif step == 2:
        print("Schritt 2: TCA9548A an Raspberry Pi 4 anschließen")
        print("• Pinbelegung Raspberry Pi Header -> TCA9548A:")
        print("  1. Pin 1 (3.3V)  -> VIN / VCC")
        print("  2. Pin 6 (GND)   -> GND")
        print("  3. Pin 3 (SDA1)  -> SDA")
        print("  4. Pin 5 (SCL1)  -> SCL")
        print("  5. Pin A0        -> 3.3V (falls keine Lötbrücke)")
        print("  6. Pins A1, A2   -> GND / unbeschaltet")

    elif step == 3:
        print("Schritt 3: I2C-Bus-Erkennung des Multiplexers prüfen")
        primary = scan_bus_addresses(bus)
        found = mux_addr in primary or FALLBACK_MUX_ADDR in primary
        if found:
            detected_addr = mux_addr if mux_addr in primary else FALLBACK_MUX_ADDR
            print(f"✔ ERFOLG: TCA9548A erkannt auf Adresse 0x{detected_addr:02X}!")
            if detected_addr == 0x70:
                print("⚠️  HINWEIS: Erkannt auf 0x70. Bitte A0 mit 3.3V verbinden für 0x71.")
        else:
            print("✘ FEHLER: Multiplexer nicht gefunden.")
            print("  Prüfe Jumper-Verbindungen (3.3V, GND, SDA Pin 3, SCL Pin 5).")

    elif step == 4:
        print("Schritt 4: ADS1115 ADC an Multiplexer-Kanal 0 (CH0) anbinden")
        print("• Pinbelegung TCA9548A -> ADS1115 (Kanal 0):")
        print("  1. 3.3V  -> VDD")
        print("  2. GND   -> GND")
        print("  3. SD0   -> SDA")
        print("  4. SC0   -> SCL")
        print("  5. ADDR  -> GND (wählt Standardadresse 0x48)")

    elif step == 5:
        print("Schritt 5: I2C-Kanalumschaltung & ADC-Erkennung auf CH0")
        set_tca9548a_channel(bus, mux_addr, 0)
        devs = scan_bus_addresses(bus)
        set_tca9548a_channel(bus, mux_addr, None)
        if DEFAULT_ADC_ADDR in devs:
            print(f"✔ ERFOLG: ADS1115 erkannt auf Sub-Kanal 0 (Adresse 0x{DEFAULT_ADC_ADDR:02X})!")
        else:
            print("✘ FEHLER: Kein ADS1115 auf Kanal 0 erkannt.")
            print(f"  Gefundene Adressen auf CH0: {[f'0x{d:02X}' for d in devs]}")
            print("  Prüfe ADDR-Pin am ADS1115 (muss auf GND liegen für 0x48).")

    elif step == 6:
        print("Schritt 6: Analoge Testspannung an ADS1115 A0 auslesen")
        set_tca9548a_channel(bus, mux_addr, 0)
        try:
            raw, volts = read_ads1115_channel(bus, DEFAULT_ADC_ADDR, 0)
            print(f"✔ ERFOLG: ADS1115 A0 erfolgreich gelesen:")
            print(f"  • Spannung: {volts:.4f} V")
            print(f"  • 16-Bit Raw Counts: {raw} (0 bis 32767)")
            print("\n  Tipp: Schließe ein Potentiometer oder einen Spannungsteiler an A0 an")
            print("  und starte: python3 scripts/bench/test_electronics.py --channel 0 --read-analog 0")
        except Exception as e:
            print(f"✘ FEHLER beim Auslesen des ADC: {e}")
        finally:
            set_tca9548a_channel(bus, mux_addr, None)

    print("=" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Lasius Hexapod - Electronics Testbench Diagnostic Utility")
    parser.add_argument("--scan", action="store_true", help="Führt einen vollständigen Scan des Hauptbusses und aller Sub-Kanäle aus")
    parser.add_argument("--step", type=int, choices=range(1, 7), help="Führt die Prüfung für einen spezifischen Schritt (1-6) aus")
    parser.add_argument("--mux-addr", type=lambda x: int(x, 0), default=DEFAULT_MUX_ADDR, help="I2C-Adresse des TCA9548A (Standard: 0x71)")
    parser.add_argument("--adc-addr", type=lambda x: int(x, 0), default=DEFAULT_ADC_ADDR, help="I2C-Adresse des ADS1115 (Standard: 0x48)")
    parser.add_argument("--channel", type=int, choices=range(0, 8), default=0, help="Multiplexer-Kanal (0-7, Standard: 0)")
    parser.add_argument("--read-analog", type=int, choices=range(0, 4), help="Liest kontinuierlich Analogkanal A0-A3 des ADS1115 aus")
    parser.add_argument("--bus", type=int, default=1, help="I2C-Bus-Nummer (Standard: 1)")
    parser.add_argument("--mock", action="store_true", help="Erzwingt Mock-Modus für Offline-Tests auf Entwicklungs-Laptops")
    args = parser.parse_args()

    bus = get_i2c_bus(args.bus, args.mock)

    try:
        if args.read_analog is not None:
            run_analog_monitor(bus, args.mux_addr, args.channel, args.read_analog)
        elif args.step is not None:
            run_step_guide(bus, args.step, args.mux_addr)
        else:
            # Default to full diagnostic scan
            run_full_scan(bus, args.mux_addr, args.adc_addr)
    finally:
        bus.close()


if __name__ == "__main__":
    main()
