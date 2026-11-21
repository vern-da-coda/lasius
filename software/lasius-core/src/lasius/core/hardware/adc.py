"""
I2C Multiplexer (PCA9548A 0x71) & 16-Bit ADC (ADS1115 V280 0x48) Drivers (`lasius.core.hardware.adc`).

Purpose & Role:
    Implements the closed-loop sensor acquisition layer for the Lasius Hexapod:
    - 1x PCA9548A/TCA9548A 8-channel I2C multiplexer at address `0x71` (`A0` bridged to 3.3V
      to avoid colliding with the PCA9685 `0x70` All-Call address).
    - 6x ADS1115 16-bit 4-channel delta-sigma ADCs at address `0x48` on multiplexer
      channels `CH0..CH5` (`LF=0, LM=1, LR=2, RF=3, RM=4, RR=5`):
        * `A0`: Coxa potentiometer wiper voltage
        * `A1`: Femur potentiometer wiper voltage
        * `A2`: Tibia potentiometer wiper voltage
        * `A3`: Tarsus foot microswitch (Omron D2F-L with 10 kOhm pull-up to 3.3V, COM -> GND)

Concurrency & Non-Blocking Guarantee:
    - Shares the module-level `_BUS_LOCKS[id(bus)]` (`threading.RLock`) with `RealPCA9685Driver`
      so I2C bus transactions never collide across threads.
    - Releases the I2C bus lock during the ~1.3 ms ADS1115 860 SPS conversion window so
      50 Hz PWM actuation in `Hexapod.tick()` is never blocked by ADC waits.
"""

import math
import threading
import time
from typing import Dict, Optional, Protocol, Tuple, Any

try:
    import smbus2
except ImportError:
    smbus2 = None

from .driver import _BUS_LOCKS

# Default I2C Addresses
DEFAULT_MUX_ADDRESS = 0x71
DEFAULT_ADC_ADDRESS = 0x48

# ADS1115 Register Map
_ADS_REG_CONVERSION = 0x00
_ADS_REG_CONFIG = 0x01

# ADS1115 Config Register Bitmasks
_ADS_OS_SINGLE = 0x8000       # Start single-shot conversion
_ADS_MUX_A0 = 0x4000          # AINP = AIN0, AINN = GND
_ADS_MUX_A1 = 0x5000          # AINP = AIN1, AINN = GND
_ADS_MUX_A2 = 0x6000          # AINP = AIN2, AINN = GND
_ADS_MUX_A3 = 0x7000          # AINP = AIN3, AINN = GND
_ADS_PGA_4_096V = 0x0200      # +/-4.096V full-scale range (1 LSB = 0.125 mV)
_ADS_MODE_SINGLE = 0x0100     # Power-down single-shot mode
_ADS_DR_860SPS = 0x00E0       # 860 samples per second (~1.16 ms conversion time)
_ADS_CQUE_NONE = 0x0003       # Disable comparator

_ADS_CHANNEL_MUX: Dict[int, int] = {
    0: _ADS_MUX_A0,
    1: _ADS_MUX_A1,
    2: _ADS_MUX_A2,
    3: _ADS_MUX_A3,
}

# Empirical pre-first-PWM-pulse voltage of Reely NR-645 MG BB internal ASIC
PRE_PULSE_INVALID_VOLTAGE_V = 0.2660


class ADCDriverProtocol(Protocol):
    """
    Protocol for reading the 4 analog channels (A0..A3) of a leg's ADS1115 ADC
    behind a specific PCA9548A multiplexer sub-bus channel (0..5).
    """
    def read_leg_channels(self, mux_channel: int) -> Dict[int, Optional[float]]:
        """
        Reads analog voltages [V] for channels `{0: A0_coxa, 1: A1_femur, 2: A2_tibia, 3: A3_foot}`
        on the given multiplexer channel `mux_channel` (0..5).
        Returns `None` for any channel that is unpopulated or fails to respond.
        """
        ...

    def close(self) -> None:
        """Releases underlying hardware resources."""
        ...


class RealADS1115MuxDriver:
    """
    Thread-safe SMBus driver for the PCA9548A I2C multiplexer (0x71) and 6x ADS1115 ADCs (0x48).
    Shares `_BUS_LOCKS` with `RealPCA9685Driver` to guarantee atomic I2C access.
    """
    def __init__(
        self,
        mux_address: int = DEFAULT_MUX_ADDRESS,
        adc_address: int = DEFAULT_ADC_ADDRESS,
        bus_number: int = 1,
        bus_instance: Optional[Any] = None,
        conversion_delay_s: float = 0.0014,
    ):
        self.mux_address = mux_address
        self.adc_address = adc_address
        self.conversion_delay_s = conversion_delay_s
        self._owns_bus = bus_instance is None

        if bus_instance is not None:
            self.bus = bus_instance
        else:
            if smbus2 is None:
                raise ImportError("The 'smbus2' library is required for RealADS1115MuxDriver.")
            self.bus = smbus2.SMBus(bus_number)

        bus_id = id(self.bus)
        if bus_id not in _BUS_LOCKS:
            _BUS_LOCKS[bus_id] = threading.RLock()
        self._bus_lock = _BUS_LOCKS[bus_id]
        self._lock = self._bus_lock

    def _select_mux_channel_unlocked(self, mux_channel: Optional[int]) -> None:
        """Writes the channel selection mask to the PCA9548A multiplexer (caller holds lock)."""
        mask = (1 << mux_channel) if (mux_channel is not None and 0 <= mux_channel <= 7) else 0x00
        self.bus.write_byte(self.mux_address, mask)

    def read_single_channel(self, mux_channel: int, adc_channel: int) -> Optional[float]:
        """
        Performs a single-ended conversion on `(mux_channel, adc_channel)` at 860 SPS.
        Releases the shared I2C bus lock during the conversion wait so 50 Hz PWM writes
        are never stalled.
        """
        if adc_channel not in _ADS_CHANNEL_MUX:
            raise ValueError(f"ADC channel must be 0-3, got {adc_channel}.")
        if not (0 <= mux_channel <= 7):
            raise ValueError(f"Multiplexer channel must be 0-7, got {mux_channel}.")

        config_word = (
            _ADS_OS_SINGLE
            | _ADS_CHANNEL_MUX[adc_channel]
            | _ADS_PGA_4_096V
            | _ADS_MODE_SINGLE
            | _ADS_DR_860SPS
            | _ADS_CQUE_NONE
        )
        cfg_bytes = [(config_word >> 8) & 0xFF, config_word & 0xFF]

        try:
            # Phase 1: Select mux sub-bus and trigger single-shot conversion
            with self._lock:
                self._select_mux_channel_unlocked(mux_channel)
                self.bus.write_i2c_block_data(self.adc_address, _ADS_REG_CONFIG, cfg_bytes)

            # Wait for conversion OUTSIDE the I2C bus lock (~1.4 ms at 860 SPS)
            if self.conversion_delay_s > 0:
                time.sleep(self.conversion_delay_s)

            # Phase 2: Re-acquire lock, ensure mux sub-bus is selected, and read 16-bit result
            with self._lock:
                self._select_mux_channel_unlocked(mux_channel)
                for _ in range(5):
                    status = self.bus.read_i2c_block_data(self.adc_address, _ADS_REG_CONFIG, 2)
                    if (status[0] & 0x80) != 0:
                        break
                raw_bytes = self.bus.read_i2c_block_data(self.adc_address, _ADS_REG_CONVERSION, 2)

            raw = (raw_bytes[0] << 8) | raw_bytes[1]
            if raw > 32767:
                raw -= 65536
            # +/- 4.096 V range: 1 LSB = 0.125 mV = 0.000125 V
            return max(0.0, raw * 0.000125)
        except OSError:
            return None

    def read_leg_channels(self, mux_channel: int) -> Dict[int, Optional[float]]:
        """
        Reads all 4 channels (A0=Coxa, A1=Femur, A2=Tibia, A3=FootSwitch) for a leg.
        If channel A0 NACKs (e.g., ADS1115 board not connected on this leg), aborts early
        for this leg to avoid wasting bus time.
        """
        results: Dict[int, Optional[float]] = {0: None, 1: None, 2: None, 3: None}
        v0 = self.read_single_channel(mux_channel, 0)
        if v0 is None:
            # Disable mux channel cleanly before returning
            try:
                with self._lock:
                    self._select_mux_channel_unlocked(None)
            except OSError:
                pass
            return results

        results[0] = v0
        for adc_ch in (1, 2, 3):
            results[adc_ch] = self.read_single_channel(mux_channel, adc_ch)

        try:
            with self._lock:
                self._select_mux_channel_unlocked(None)
        except OSError:
            pass
        return results

    def close(self) -> None:
        try:
            with self._lock:
                self._select_mux_channel_unlocked(None)
        except Exception:
            pass
        if self._owns_bus and hasattr(self.bus, "close"):
            try:
                self.bus.close()
            except Exception:
                pass


class SimulatedADCDriver:
    """
    Physics-informed simulated ADS1115 + PCA9548A driver for offline simulation,
    Digital Twin testing, and unit tests.

    Behavior:
      - Before a servo receives its first PWM pulse (`has_received_pwm_pulse == False`),
        returns the empirical Reely NR-645 pre-pulse voltage (`0.2660 V`) so the
        pre-pulse invalidity guard is realistically exercised.
      - Once energized, simulates first-order physical servo dynamics (`tau_lag_s`,
        `max_speed_deg_s`) trailing behind `servo.current_angle` and converts the
        simulated physical shaft angle into potentiometer voltage via `servo.angle_to_voltage()`.
      - Supports explicit voltage overrides and simulated joint stalls for unit testing.
    """
    def __init__(
        self,
        tau_lag_s: float = 0.075,
        max_speed_deg_s: float = 350.0,
        pre_pulse_Invalid_v: float = PRE_PULSE_INVALID_VOLTAGE_V,
    ):
        self.tau_lag_s = tau_lag_s
        self.max_speed_deg_s = max_speed_deg_s
        self.pre_pulse_invalid_v = pre_pulse_Invalid_v
        self._lock = threading.RLock()

        # Mapping: (mux_channel, adc_channel) -> Servo instance
        self._servo_map: Dict[Tuple[int, int], Any] = {}
        # Simulated physical shaft angles in logical degrees: (mux_channel, adc_channel) -> float
        self._sim_angles: Dict[Tuple[int, int], float] = {}
        self._last_time: Dict[Tuple[int, int], float] = {}
        # Explicit voltage overrides for testing: (mux_channel, adc_channel) -> Optional[float]
        self._voltage_overrides: Dict[Tuple[int, int], Optional[float]] = {}
        # Simulated mechanical stall angles: servo_name -> clamped_angle_deg
        self._stalled_servos: Dict[str, float] = {}
        # Simulated foot switch states: mux_channel -> bool (True = ground contact = 0.05V, False = open = 3.28V)
        self._foot_contacts: Dict[int, bool] = {}

    def bind_leg_servos(self, mux_channel: int, coxa_servo: Any, femur_servo: Any, tibia_servo: Any) -> None:
        """Binds the 3 servos of a leg to `(mux_channel, 0..2)`."""
        with self._lock:
            self._servo_map[(mux_channel, 0)] = coxa_servo
            self._servo_map[(mux_channel, 1)] = femur_servo
            self._servo_map[(mux_channel, 2)] = tibia_servo

    def set_voltage_override(self, mux_channel: int, adc_channel: int, voltage_v: Optional[float]) -> None:
        """Overrides a specific `(mux_channel, adc_channel)` with a fixed test voltage (or None)."""
        with self._lock:
            self._voltage_overrides[(mux_channel, adc_channel)] = voltage_v

    def clear_voltage_override(self, mux_channel: int, adc_channel: int) -> None:
        """Removes a voltage override on `(mux_channel, adc_channel)`."""
        with self._lock:
            self._voltage_overrides.pop((mux_channel, adc_channel), None)

    def set_simulated_stall(self, servo_name: str, stalled_angle_deg: Optional[float]) -> None:
        """Pins a simulated servo at `stalled_angle_deg` (or clears stall when `None`)."""
        with self._lock:
            if stalled_angle_deg is None:
                self._stalled_servos.pop(servo_name, None)
            else:
                self._stalled_servos[servo_name] = float(stalled_angle_deg)

    def set_foot_contact(self, mux_channel: int, in_contact: bool) -> None:
        """Sets the simulated Omron D2F-L foot switch state for `mux_channel`."""
        with self._lock:
            self._foot_contacts[mux_channel] = bool(in_contact)

    def advance_dt(self, dt: float) -> None:
        """Explicitly advances all simulated servo physical angles by `dt` seconds."""
        with self._lock:
            dt = max(1e-4, float(dt))
            for key, servo in self._servo_map.items():
                if not getattr(servo, "has_received_pwm_pulse", False) or servo.current_angle is None:
                    continue
                target = float(servo.current_angle)
                if servo.config.name in self._stalled_servos:
                    self._sim_angles[key] = self._stalled_servos[servo.config.name]
                    continue
                cur = self._sim_angles.get(key, target)
                if not getattr(servo, "is_relaxed", False):
                    tau = max(1e-3, self.tau_lag_s)
                    alpha = 1.0 - math.exp(-dt / tau)
                    step = (target - cur) * alpha
                    max_step = self.max_speed_deg_s * dt
                    step = max(-max_step, min(max_step, step))
                    cur += step
                self._sim_angles[key] = cur
                self._last_time[key] = time.perf_counter()

    def read_leg_channels(self, mux_channel: int) -> Dict[int, Optional[float]]:
        """Computes simulated voltages for A0 (Coxa), A1 (Femur), A2 (Tibia), A3 (Foot Switch)."""
        now = time.perf_counter()
        results: Dict[int, Optional[float]] = {0: None, 1: None, 2: None, 3: None}

        with self._lock:
            for adc_ch in (0, 1, 2):
                key = (mux_channel, adc_ch)
                if key in self._voltage_overrides:
                    results[adc_ch] = self._voltage_overrides[key]
                    continue

                servo = self._servo_map.get(key)
                if servo is None:
                    results[adc_ch] = None
                    continue

                # Before first PWM pulse: return ~0.266 V uninitialized voltage
                if not getattr(servo, "has_received_pwm_pulse", False) or servo.current_angle is None:
                    results[adc_ch] = self.pre_pulse_invalid_v
                    continue

                target = float(servo.current_angle)
                last_t = self._last_time.get(key)
                if last_t is None:
                    cur = target
                else:
                    dt = max(0.0, min(0.25, now - last_t))
                    cur = self._sim_angles.get(key, target)
                    if dt > 1e-4 and not getattr(servo, "is_relaxed", False):
                        tau = max(1e-3, self.tau_lag_s)
                        alpha = 1.0 - math.exp(-dt / tau)
                        step = (target - cur) * alpha
                        max_step = self.max_speed_deg_s * dt
                        step = max(-max_step, min(max_step, step))
                        cur += step

                if servo.config.name in self._stalled_servos:
                    cur = self._stalled_servos[servo.config.name]

                self._sim_angles[key] = cur
                self._last_time[key] = now
                results[adc_ch] = servo.angle_to_voltage(cur)

            # Channel A3: Foot switch (10 kOhm pull-up to 3.3V, COM -> GND)
            foot_key = (mux_channel, 3)
            if foot_key in self._voltage_overrides:
                results[3] = self._voltage_overrides[foot_key]
            else:
                in_contact = self._foot_contacts.get(mux_channel, False)
                results[3] = 0.04 if in_contact else 3.28

        return results

    def close(self) -> None:
        pass
