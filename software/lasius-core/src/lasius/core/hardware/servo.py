"""
Logical Servo Actuator & Closed-Loop Feedback Model (`lasius.core.hardware.servo`).

Purpose & Role:
    Encapsulates a single calibrated hobby servo (`ServoConfig`) paired with a
    `PWMDriverProtocol` output board and closed-loop ADS1115 potentiometer
    telemetry.
    - Open-loop actuation: clamps target angles to `[min_angle, max_angle]`,
      applies `orientation` (`+1` or `-1`) and `center_offset_pulse` (µs), and
      converts the resulting pulse width into 12-bit PCA9685 ticks (0–4095 at 50 Hz).
    - Closed-loop feedback (AP 6):
      * Strictly separates commanded target angle (`current_angle` / `target_angle`)
        from measured potentiometer feedback (`measured_angle`, `measured_voltage`,
        `actual_valid`).
      * Guards against the Reely NR-645 MG BB pre-first-PWM-pulse uninitialized
        voltage (~0.266 V) and disconnected/shorted ADC lines (`[0.50 V, 3.10 V]`
        plausibility window).
      * Implements a rate-limited first-order dynamic reference model
        `expected_angle(t) ≈ target_angle(t - tau)` (tau = 0.075 s, omega_max = 350 deg/s)
        so normal transit lag (~13 deg during fast sweeps) is cleanly distinguished
        from persistent mechanical stall / collision (`is_stalled`).
"""

import math
from typing import Optional
from lasius.core.config import ServoConfig
from .driver import PWMDriverProtocol

# Default constants for standard analog/digital hobby servos
_PWM_FREQUENCY = 50.0  # 50 Hz (20ms period)
_PERIOD_MICROSECONDS = 1_000_000.0 / _PWM_FREQUENCY  # 20,000 us
_MAX_TICKS = 4096.0
_DEFAULT_CENTER_PULSE = 1500  # 1500 us represents 0 degrees


class Servo:
    """
    Represents and controls a single physical or simulated servo motor
    with closed-loop potentiometer feedback and dynamic tracking-lag estimation.
    """
    def __init__(self, config: ServoConfig, driver: PWMDriverProtocol):
        self.config = config
        self.driver = driver

        # Commanded target state (Soll)
        self.current_angle: Optional[float] = None
        self.is_relaxed: bool = True
        self.has_received_pwm_pulse: bool = False

        # Measured potentiometer state (Ist)
        self.measured_voltage: Optional[float] = None
        self.measured_angle: Optional[float] = None
        self.actual_valid: bool = False

        # Dynamic first-order lag reference model & stall state
        self.expected_angle: Optional[float] = None
        self.tracking_error: Optional[float] = None
        self.is_stalled: bool = False
        self._stall_accum_s: float = 0.0

    @property
    def target_angle(self) -> Optional[float]:
        """Alias for `current_angle` (commanded Soll angle in degrees)."""
        return self.current_angle

    @property
    def raw_deviation(self) -> Optional[float]:
        """Instantaneous difference `measured_angle - current_angle` in degrees."""
        if not self.actual_valid or self.measured_angle is None or self.current_angle is None:
            return None
        return self.measured_angle - self.current_angle

    def get_effective_start_angle(self, fallback: float = 0.0) -> float:
        """
        Returns the best known starting angle for smooth cosine ramp re-engagement:
        prefers the live measured potentiometer angle (`measured_angle`) when valid
        (even after `relax()`), falling back to `current_angle` or `fallback`.
        """
        if self.actual_valid and self.measured_angle is not None:
            return self.measured_angle
        if self.current_angle is not None:
            return self.current_angle
        return fallback

    def set_angle(self, angle: float) -> None:
        """
        Moves the servo to the desired angle in degrees.
        The angle is automatically clamped to the configured min and max limits.
        """
        clamped_angle = max(self.config.min_angle, min(self.config.max_angle, angle))
        if clamped_angle != angle:
            print(
                f"Warning: Angle {angle:.1f}° for servo '{self.config.name}' "
                f"was clamped to {clamped_angle:.1f}°."
            )

        if self.expected_angle is None:
            self.expected_angle = (
                self.measured_angle
                if (self.actual_valid and self.measured_angle is not None)
                else clamped_angle
            )

        self.current_angle = clamped_angle
        self.is_relaxed = False
        self.has_received_pwm_pulse = True

        final_angle = clamped_angle * self.config.orientation
        ticks = self._angle_to_ticks(final_angle)

        self.driver.set_pwm(
            self.config.channel,
            0,
            ticks,
            angle=self.current_angle,
            servo_name=self.config.name,
        )

    def relax(self) -> None:
        """
        Disables the PWM pulse on this servo channel so the motor relaxes (zero holding torque).
        Note: On Reely NR-645 MG BB, once energized (`has_received_pwm_pulse=True`),
        the internal potentiometer reference remains active even while relaxed.
        """
        self.is_relaxed = True
        self.is_stalled = False
        self._stall_accum_s = 0.0
        if hasattr(self.driver, "relax_channel"):
            self.driver.relax_channel(self.config.channel)
        else:
            self.driver.set_pwm(self.config.channel, 0, 0)

    def _trim_angle_offset_deg(self) -> float:
        """
        Converts `center_offset_pulse` (µs) into the equivalent physical shaft angle
        offset in degrees so potentiometer voltage and logical joint angle stay aligned.
        """
        half_span_us = self.config.pulse_range / 2.0
        if half_span_us <= 0:
            return 0.0
        return (self.config.center_offset_pulse / half_span_us) * 90.0

    def voltage_to_angle(self, voltage_v: float) -> float:
        """
        Converts a valid ADS1115 potentiometer wiper voltage [V] into the logical
        joint angle [°], accounting for per-servo `pot_v_zero`, `pot_v_slope`,
        `center_offset_pulse`, and `orientation` (+1 / -1).
        """
        slope = self.config.pot_v_slope if abs(self.config.pot_v_slope) > 1e-9 else 0.007589
        shaft_angle_deg = (voltage_v - self.config.pot_v_zero) / slope
        untrimmed_deg = shaft_angle_deg - self._trim_angle_offset_deg()
        orient = -1.0 if self.config.orientation < 0 else 1.0
        return untrimmed_deg * orient

    def angle_to_voltage(self, logical_angle_deg: float) -> float:
        """
        Inverse model: computes the expected potentiometer wiper voltage [V]
        for a given logical joint angle [°].
        """
        orient = -1.0 if self.config.orientation < 0 else 1.0
        shaft_angle_deg = (logical_angle_deg * orient) + self._trim_angle_offset_deg()
        return self.config.pot_v_zero + (shaft_angle_deg * self.config.pot_v_slope)

    def is_voltage_plausible(self, voltage_v: Optional[float]) -> bool:
        """
        Checks whether an ADC voltage reading lies within the valid physical window
        `[pot_v_min_valid, pot_v_max_valid]` (default `[0.50 V, 3.10 V]`).
        Filters out the ~0.266 V Reely NR-645 pre-first-PWM-pulse uninitialized state
        as well as disconnected (0.0 V) or shorted (> 3.1 V) lines.
        """
        if voltage_v is None or math.isnan(voltage_v):
            return False
        return self.config.pot_v_min_valid <= voltage_v <= self.config.pot_v_max_valid

    def update_feedback(
        self,
        voltage_v: Optional[float],
        dt: float = 0.020,
        ema_alpha: float = 0.45,
        tau_lag_s: float = 0.075,
        max_speed_deg_s: float = 350.0,
        stall_error_deg: float = 8.0,
        stall_timeout_s: float = 0.35,
    ) -> Optional[float]:
        """
        Ingests a fresh potentiometer voltage measurement from the leg's ADS1115 ADC,
        validates plausibility, applies EMA smoothing, advances the first-order
        dynamic reference lag model `expected_angle(t)`, and evaluates stall status.

        Returns:
            The updated `measured_angle` in degrees, or `None` if reading is invalid.
        """
        dt = max(1e-4, float(dt))

        # 1. Advance dynamic reference trajectory expected_angle(t) toward current_angle
        if self.current_angle is not None:
            if self.expected_angle is None:
                self.expected_angle = self.current_angle
            else:
                tau = max(1e-3, float(tau_lag_s))
                alpha_lag = 1.0 - math.exp(-dt / tau)
                ideal_step = (self.current_angle - self.expected_angle) * alpha_lag
                max_step = max(1.0, float(max_speed_deg_s)) * dt
                clamped_step = max(-max_step, min(max_step, ideal_step))
                self.expected_angle += clamped_step

        # 2. Plausibility & pre-first-PWM-pulse invalidity guard
        if not self.is_voltage_plausible(voltage_v):
            self.measured_voltage = voltage_v
            self.actual_valid = False
            self.measured_angle = None
            self.tracking_error = None
            self.is_stalled = False
            self._stall_accum_s = 0.0
            return None

        assert voltage_v is not None
        alpha = max(0.01, min(1.0, float(ema_alpha)))
        if self.measured_voltage is None or not self.actual_valid:
            self.measured_voltage = float(voltage_v)
        else:
            self.measured_voltage = alpha * float(voltage_v) + (1.0 - alpha) * self.measured_voltage

        self.measured_angle = self.voltage_to_angle(self.measured_voltage)
        self.actual_valid = True

        # If servo has never been commanded yet, align expected_angle with measured_angle
        if self.expected_angle is None:
            self.expected_angle = self.measured_angle

        # 3. Compute dynamic lag-compensated tracking error & persistent stall detection
        if self.current_angle is not None and self.expected_angle is not None:
            self.tracking_error = self.measured_angle - self.expected_angle
            if not self.is_relaxed:
                if abs(self.tracking_error) >= stall_error_deg:
                    self._stall_accum_s += dt
                    if self._stall_accum_s >= stall_timeout_s:
                        self.is_stalled = True
                else:
                    self._stall_accum_s = max(0.0, self._stall_accum_s - 2.0 * dt)
                    if self._stall_accum_s < 0.5 * stall_timeout_s:
                        self.is_stalled = False
            else:
                self.is_stalled = False
                self._stall_accum_s = 0.0
        else:
            self.tracking_error = 0.0
            self.is_stalled = False
            self._stall_accum_s = 0.0

        return self.measured_angle

    def _angle_to_ticks(self, angle: float) -> int:
        """
        Converts an angle (-90° to +90°) into PCA9685 PWM ticks (0 to 4095).
        """
        center_pulse = _DEFAULT_CENTER_PULSE + self.config.center_offset_pulse
        half_range = self.config.pulse_range / 2.0
        pulse = center_pulse + (angle / 90.0) * half_range
        ticks = int(round((pulse / _PERIOD_MICROSECONDS) * _MAX_TICKS))
        return max(0, min(int(_MAX_TICKS) - 1, ticks))
