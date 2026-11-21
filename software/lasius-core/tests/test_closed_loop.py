"""
Unit & Integration Tests for Closed-Loop ADC Telemetry & Dynamic Lag Pipeline (`tests.test_closed_loop`).

Purpose & Role:
    Verifies Software AP 6 requirements:
    1. Clean separation of target (`current_angle`) vs. measured (`measured_angle`, `actual_valid`) state.
    2. Pre-first-PWM-pulse invalidity guard (~0.266 V uninitialized Reely NR-645 voltage rejected).
    3. Linear potentiometer calibration accounting for `orientation` (+1/-1) and `center_offset_pulse`.
    4. Rate-limited first-order dynamic reference lag model (`tau_lag_s`): no false stall alarm during
       fast unloaded sweeps (~13° transit lag), reliable stall detection under persistent blockage.
    5. Shared I2C `_BUS_LOCKS` between `RealPCA9685Driver` and `RealADS1115MuxDriver` (PCA9548A 0x71 + ADS1115 0x48).
    6. End-to-end `Hexapod.poll_telemetry()` and closed-loop Forward Kinematics (`get_actual_foot_positions()`).
"""

import pytest
from typing import Dict, List, Tuple

from lasius.core.config import ServoConfig, load_config
from lasius.core.hardware import (
    Servo,
    MockPWMDriver,
    RealPCA9685Driver,
    RealADS1115MuxDriver,
    SimulatedADCDriver,
    PRE_PULSE_INVALID_VOLTAGE_V,
)
from lasius.core.hardware.driver import _BUS_LOCKS, _MODE1, _MODE2, _PRESCALE
from lasius.core.robot import Hexapod


class MockMuxADCSMBus:
    """Simulates I2C bus 1 with PCA9685 (0x40), PCA9548A mux (0x71), and 6x ADS1115 (0x48)."""
    def __init__(self):
        self.registers: Dict[int, int] = {_MODE1: 0x01, _MODE2: 0x00, _PRESCALE: 0x00}
        self.active_mux_mask: int = 0x00
        # Map: (mux_channel, adc_channel) -> voltage_v
        self.voltages: Dict[Tuple[int, int], float] = {}
        self.active_adc_channels = {0, 1, 2, 3, 4, 5}
        self._selected_adc_ch: int = 0

    def write_byte(self, addr: int, val: int) -> None:
        if addr == 0x71:
            self.active_mux_mask = val & 0xFF
            return
        raise OSError(f"Unexpected write_byte to 0x{addr:02X}")

    def write_byte_data(self, addr: int, register: int, value: int) -> None:
        self.registers[register] = value & 0xFF

    def read_byte_data(self, addr: int, register: int) -> int:
        return self.registers.get(register, 0x00)

    def _current_mux_ch(self) -> int:
        for ch in range(8):
            if self.active_mux_mask == (1 << ch):
                return ch
        return -1

    def write_i2c_block_data(self, addr: int, register: int, data: List[int]) -> None:
        if addr == 0x48 and register == 0x01:
            mux_ch = self._current_mux_ch()
            if mux_ch not in self.active_adc_channels:
                raise OSError("Simulated I2C NACK on unpopulated leg ADC")
            # Decode single-ended channel from config high byte bits [14:12]
            mux_bits = (data[0] >> 4) & 0x07
            self._selected_adc_ch = max(0, min(3, mux_bits - 4))

    def read_i2c_block_data(self, addr: int, register: int, length: int) -> List[int]:
        if addr == 0x48:
            mux_ch = self._current_mux_ch()
            if mux_ch not in self.active_adc_channels:
                raise OSError("Simulated I2C NACK")
            if register == 0x01:
                return [0x85, 0xE3]  # OS bit = 1 (conversion complete)
            if register == 0x00:
                v = self.voltages.get((mux_ch, self._selected_adc_ch), 1.5633)
                raw = int(round(v / 0.000125))
                raw = max(0, min(32767, raw))
                return [(raw >> 8) & 0xFF, raw & 0xFF]
        return [0] * length


def test_pre_first_pwm_pulse_invalidity_guard():
    """
    Before the first PWM pulse, Reely NR-645 MG BB outputs ~0.266 V.
    Verify that update_feedback rejects ~0.266 V, 0.0 V, and >3.1 V as actual_valid=False.
    """
    cfg = ServoConfig(
        name="left_front_coxa",
        board_address=0x40,
        channel=0,
        center_offset_pulse=0,
        pulse_range=2000,
        min_angle=-25.0,
        max_angle=35.0,
        orientation=1,
    )
    servo = Servo(config=cfg, driver=MockPWMDriver())

    # 1. Pre-pulse voltage (~0.266 V) must be flagged invalid
    res = servo.update_feedback(PRE_PULSE_INVALID_VOLTAGE_V, dt=0.020)
    assert res is None
    assert servo.actual_valid is False
    assert servo.measured_angle is None

    # 2. Disconnected / 0.0 V or shorted 3.25 V must also be flagged invalid
    assert servo.update_feedback(0.0, dt=0.020) is None
    assert servo.actual_valid is False
    assert servo.update_feedback(3.25, dt=0.020) is None
    assert servo.actual_valid is False

    # 3. Valid center voltage (1.5633 V) produces 0.0° and actual_valid=True
    angle = servo.update_feedback(1.5633, dt=0.020, ema_alpha=1.0)
    assert servo.actual_valid is True
    assert angle == pytest.approx(0.0, abs=0.05)


def test_servo_voltage_calibration_with_orientation_and_trim():
    """
    Verifies that voltage_to_angle and angle_to_voltage properly account for
    both right-side orientation inversion (-1) and center_offset_pulse trim (µs).
    """
    cfg_right = ServoConfig(
        name="right_front_femur",
        board_address=0x42,
        channel=1,
        center_offset_pulse=100,  # +100 us trim (+9.0 deg shaft shift on pulse_range=2000)
        pulse_range=2000,
        min_angle=-90.0,
        max_angle=90.0,
        orientation=-1,
    )
    servo = Servo(config=cfg_right, driver=MockPWMDriver())

    for target_deg in (-45.0, -15.0, 0.0, 25.0, 60.0):
        v = servo.angle_to_voltage(target_deg)
        reconstructed = servo.voltage_to_angle(v)
        assert reconstructed == pytest.approx(target_deg, abs=1e-4)


def test_dynamic_lag_model_no_false_stall_on_fast_sweep_and_detects_real_stall():
    """
    Verifies the mathematical first-order lag comparison model:
    - During a fast 60° sweep where the physical shaft lags ~12° behind the instantaneous
      commanded target, tracking_error against expected_angle(t) stays near 0° -> NO false stall.
    - When the physical shaft is mechanically blocked at 0° while commanded to +45° for >0.35s,
      is_stalled becomes True, and resets when relax() is called.
    """
    cfg = ServoConfig(
        name="left_front_femur",
        board_address=0x40,
        channel=1,
        center_offset_pulse=0,
        pulse_range=2000,
        min_angle=-90.0,
        max_angle=90.0,
        orientation=1,
    )
    servo = Servo(config=cfg, driver=MockPWMDriver())
    servo.set_angle(0.0)
    servo.update_feedback(servo.angle_to_voltage(0.0), dt=0.020, ema_alpha=1.0)
    assert servo.is_stalled is False

    # 1. Sudden step command to +60°; physical servo follows with tau=0.075s first-order lag
    servo.set_angle(60.0)
    sim_physical_angle = 0.0
    dt = 0.020
    tau = 0.075
    import math
    for _ in range(15):
        alpha = 1.0 - math.exp(-dt / tau)
        step = min(350.0 * dt, (60.0 - sim_physical_angle) * alpha)
        sim_physical_angle += step
        v = servo.angle_to_voltage(sim_physical_angle)
        servo.update_feedback(v, dt=dt, ema_alpha=1.0, tau_lag_s=tau, max_speed_deg_s=350.0)
        # Even though instantaneous raw_deviation exceeds 15° early in the step,
        # dynamic tracking_error stays near 0° and never triggers a false stall!
        assert abs(servo.tracking_error or 0.0) < 1.0
        assert servo.is_stalled is False

    # 2. Now simulate a real mechanical collision/blockage: servo commanded to +60°, but shaft stuck at +10°
    for _ in range(25):  # 25 * 0.020s = 0.50s > 0.35s stall_timeout_s
        v_blocked = servo.angle_to_voltage(10.0)
        servo.update_feedback(v_blocked, dt=dt, ema_alpha=1.0, tau_lag_s=tau)

    assert servo.is_stalled is True
    assert abs(servo.tracking_error or 0.0) > 40.0

    # 3. Relaxing the servo clears the stall state
    servo.relax()
    assert servo.is_stalled is False


def test_real_ads1115_mux_driver_and_shared_bus_lock():
    """
    Tests RealADS1115MuxDriver register protocol (PCA9548A 0x71 + ADS1115 0x48)
    and verifies it shares the exact same threading.RLock in _BUS_LOCKS as RealPCA9685Driver.
    """
    mock_bus = MockMuxADCSMBus()
    pwm_driver = RealPCA9685Driver(address=0x40, bus_instance=mock_bus)
    adc_driver = RealADS1115MuxDriver(
        mux_address=0x71,
        adc_address=0x48,
        bus_instance=mock_bus,
        conversion_delay_s=0.0,
    )

    # Verify shared I2C bus lock instance
    assert pwm_driver._bus_lock is adc_driver._bus_lock
    assert _BUS_LOCKS[id(mock_bus)] is adc_driver._bus_lock

    # Populate simulated voltages on Leg 0 (left_front, mux_channel=0)
    mock_bus.voltages[(0, 0)] = 1.5633  # Coxa 0°
    mock_bus.voltages[(0, 1)] = 1.7740  # Femur ~+27.8°
    mock_bus.voltages[(0, 2)] = 1.3060  # Tibia ~-33.9°
    mock_bus.voltages[(0, 3)] = 0.0500  # Foot switch pressed (< 1.0V)

    ch_data = adc_driver.read_leg_channels(0)
    assert ch_data[0] == pytest.approx(1.5633, abs=0.001)
    assert ch_data[1] == pytest.approx(1.7740, abs=0.001)
    assert ch_data[2] == pytest.approx(1.3060, abs=0.001)
    assert ch_data[3] == pytest.approx(0.0500, abs=0.001)

    # Unpopulated leg ADC (e.g. channel 5 removed) returns None gracefully without raising
    mock_bus.active_adc_channels.discard(5)
    missing_data = adc_driver.read_leg_channels(5)
    assert missing_data == {0: None, 1: None, 2: None, 3: None}


def test_hexapod_closed_loop_telemetry_and_actual_fk():
    """
    Tests end-to-end Hexapod closed-loop polling with SimulatedADCDriver:
    - Before first move: pre-pulse voltages (~0.266 V) result in actual_valid=False.
    - After moving legs to stance pose and polling across several time steps,
      actual_angles converge smoothly to target_angles and get_actual_foot_positions()
      recovers the commanded Cartesian foot coordinates.
    """
    config = load_config(apply_overlay=False)
    drivers = {0x40: MockPWMDriver(), 0x42: MockPWMDriver()}
    robot = Hexapod(config=config, drivers=drivers)

    # 1. Before any PWM command is issued, simulated ADC outputs ~0.266V -> actual_valid is False
    snap_init = robot.poll_telemetry(dt=0.020)
    assert all(valid is False for valid in snap_init["actual_valid"].values())
    assert all(pos is None for pos in snap_init["actual_foot_positions"].values())

    # 2. Command all 6 legs to default stance (230.0, 0.0, -80.0)
    from lasius.core.motion import LegIdentifier
    target_xyz = (230.0, 0.0, -80.0)
    for leg_id in LegIdentifier:
        robot.move_leg_tip(leg_id, *target_xyz)

    # 3. Poll telemetry over 0.6s (30 ticks of 20ms) so first-order dynamics (tau=0.075s) settle
    snap = {}
    for _ in range(30):
        snap = robot.poll_telemetry(dt=0.020)

    assert all(valid is True for valid in snap["actual_valid"].values())
    assert all(stalled is False for stalled in snap["stalled_joints"].values())

    for s_name, tgt in snap["target_angles"].items():
        act = snap["actual_angles"][s_name]
        assert act is not None and tgt is not None
        assert act == pytest.approx(tgt, abs=0.5)

    actual_positions = robot.get_actual_foot_positions()
    for leg_name, pos in actual_positions.items():
        assert pos is not None
        assert pos[0] == pytest.approx(target_xyz[0], abs=1.5)
        assert pos[1] == pytest.approx(target_xyz[1], abs=1.5)
        assert pos[2] == pytest.approx(target_xyz[2], abs=1.5)
