"""
Unit Tests for Sensor HAL (`BNO085`, `INA260`, `VL53L5CX`) & Bench I2C Diagnostics (`test_sensors.py`).
"""

import importlib.util
import math
from pathlib import Path
import struct

import pytest

from lasius.core.hardware import (
    HUDTelemetrySnapshot,
    SimulatedIMUDriver,
    SimulatedOLEDHUD,
    SimulatedPowerMonitor,
    SimulatedToFSensor,
    parse_bno085_rvc_frame,
    rpy_deg_to_projected_gravity,
)
from lasius.core.motion import LegIdentifier, WalknetGait


def _build_rvc_packet(
    yaw_deg: float,
    pitch_deg: float,
    roll_deg: float,
    ax_mg: int = 0,
    ay_mg: int = 0,
    az_mg: int = 1000,
    seq: int = 1,
) -> bytes:
    body = struct.pack(
        "<Bhhhhhh3B",
        seq & 0xFF,
        int(round(yaw_deg * 100)),
        int(round(pitch_deg * 100)),
        int(round(roll_deg * 100)),
        ax_mg,
        ay_mg,
        az_mg,
        0,
        0,
        0,
    )
    csum = sum(body) & 0xFF
    return b"\xaa\xaa" + body + bytes([csum])


class TestSensorHAL:
    def test_bno085_uart_rvc_frame_parsing_and_checksum(self):
        pkt = _build_rvc_packet(yaw_deg=45.25, pitch_deg=-8.50, roll_deg=12.10)
        reading = parse_bno085_rvc_frame(pkt)
        assert reading is not None
        assert reading.valid is True
        assert reading.yaw_deg == pytest.approx(45.25, abs=0.01)
        assert reading.pitch_deg == pytest.approx(-8.50, abs=0.01)
        assert reading.roll_deg == pytest.approx(12.10, abs=0.01)
        assert reading.accel_m_s2[2] == pytest.approx(9.80665, abs=0.01)

        # Corrupted checksum must be rejected
        bad_pkt = pkt[:-1] + bytes([(pkt[-1] ^ 0xFF)])
        assert parse_bno085_rvc_frame(bad_pkt) is None

        # Wrong header must be rejected
        assert parse_bno085_rvc_frame(b"\x55\xaa" + pkt[2:]) is None

    def test_projected_gravity_unit_norm_and_direction(self):
        gx, gy, gz = rpy_deg_to_projected_gravity(0.0, 0.0)
        assert (gx, gy, gz) == pytest.approx((0.0, 0.0, -1.0), abs=1e-6)

        gx, gy, gz = rpy_deg_to_projected_gravity(15.0, -10.0)
        assert math.sqrt(gx**2 + gy**2 + gz**2) == pytest.approx(1.0, abs=1e-6)
        assert gx < 0.0  # Nose down tilts gravity forward (-X)

    def test_simulated_imu_power_and_tof_with_walknet(self):
        imu = SimulatedIMUDriver()
        imu.set_attitude(roll_deg=5.0, pitch_deg=-4.0, yaw_deg=90.0)
        r_imu = imu.read()
        assert r_imu.valid and r_imu.roll_deg == pytest.approx(5.0)

        pwr = SimulatedPowerMonitor(bus_voltage_v=6.7, current_a=5.0)
        r_pwr = pwr.read()
        assert r_pwr.low_voltage_warning is True
        assert r_pwr.critical_cutoff is False
        assert r_pwr.power_w == pytest.approx(33.5)

        pwr.bus_voltage_v = 6.3
        assert pwr.read().critical_cutoff is True

        tof = SimulatedToFSensor(nominal_distance_m=0.095)
        tof.set_grid([0.09, 0.09, 0.09, 0.09, 0.055, 0.09, 0.09, 0.09, 0.09])
        r_tof = tof.read()
        assert r_tof.min_distance_m == pytest.approx(0.055)

        gait = WalknetGait()
        boost = gait.set_belly_tof_distance_m(r_tof.min_distance_m)
        assert boost > 0.0

    def test_rear_oled_hud_bus_isolation_and_dual_zone_format(self):
        # Must refuse real-time servo/ADC bus i2c-1
        with pytest.raises(ValueError, match="i2c-1"):
            SimulatedOLEDHUD(bus_num=1)

        hud = SimulatedOLEDHUD(bus_num=3, address=0x3C)
        lines = hud.render(
            HUDTelemetrySnapshot(
                battery_v=7.8,
                current_a=3.4,
                gait_mode="walknet",
                servos_armed=True,
                ip_address="192.168.0.42",
                cpu_temp_c=51.2,
            )
        )
        assert len(lines) == 5
        assert all(len(line) <= 21 for line in lines)
        assert "7.8V" in lines[0] and "[ARM]" in lines[0]
        assert "WALKNET" in lines[1]
        assert hud.render_count == 1


class TestBenchDiagnosticsScript:
    def test_subbus_filtering_and_v280_resolution_detection(self):
        repo_root = Path(__file__).resolve().parents[3]
        script_path = repo_root / "scripts/bench/test_electronics.py"
        spec = importlib.util.spec_from_file_location("test_electronics", script_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Sub-bus filter strips primary addresses (0x40, 0x42, 0x71)
        filtered = mod.filter_subbus_addresses([0x40, 0x42, 0x48, 0x71], [0x40, 0x42, 0x71])
        assert filtered == [0x48]
        assert mod.filter_subbus_addresses([0x40, 0x48, 0x71], [0x40, 0x71], include_primary=True) == [0x40, 0x48, 0x71]

        # 12-bit V280 detection on MockI2CBus
        bus_12 = mod.MockI2CBus(simulate_12bit_v280=True)
        mod.set_tca9548a_channel(bus_12, mod.DEFAULT_MUX_ADDR, 0)
        assert mod.detect_adc_resolution_bits(bus_12, mod.DEFAULT_ADC_ADDR) == (12, 2.0)

        # True 16-bit ADS1115 detection
        bus_16 = mod.MockI2CBus(simulate_12bit_v280=False)
        bus_16.mock_voltages[0] = 1.5633  # produces non-zero low nibble in 16-bit counts
        mod.set_tca9548a_channel(bus_16, mod.DEFAULT_MUX_ADDR, 0)
        assert mod.detect_adc_resolution_bits(bus_16, mod.DEFAULT_ADC_ADDR) == (16, 0.125)
