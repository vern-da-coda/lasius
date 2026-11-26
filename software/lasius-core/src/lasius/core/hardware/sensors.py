"""
Sensor Hardware Abstraction Layer (`lasius.core.hardware.sensors`).

Purpose & Role:
    Provides Protocol interfaces, hardware parsers/drivers, and deterministic
    simulated implementations for the Lasius v2 exteroceptive & proprioceptive
    sensor suite (`hardware/electronics/TODO.md` AP 5 & Milestone 5):
    - **9-DOF Orientation IMU (`Adafruit BNO085`, PID 4754):**
      Implements the 19-byte **UART-RVC** (`115200 baud`, `100 Hz`) frame parser
      recommended for Raspberry Pi 4 to avoid the BCM2711 `i2c-1` clock-stretching
      errata and keep the real-time servo/ADC bus unloaded.
    - **Power / Current Monitor (`INA260` / `INA228` on Mux CH6):**
      Monitors 2S LiPo bus voltage (`V`), servo bank current (`A`), and power (`W`)
      with automatic low-voltage warning & critical cutoff detection.
    - **Multi-Zone ToF Distance Scanner (`VL53L5CX` on Belly Pan / Head):**
      Provides a downsampled `3x3` distance grid (meters) feeding both
      `WalknetGait.set_belly_tof_distance_m()` and `ResidualPolicyRunner` (`use_tof_grid=True`).
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import struct
from typing import List, Optional, Protocol, Tuple


# ---------------------------------------------------------------------------
# 1. 9-DOF IMU (Adafruit BNO085 UART-RVC & Simulated)
# ---------------------------------------------------------------------------

@dataclass
class IMUReading:
    """Normalized 9-DOF IMU attitude & dynamics sample in robot body frame."""
    roll_deg: float = 0.0
    pitch_deg: float = 0.0
    yaw_deg: float = 0.0
    proj_gravity: Tuple[float, float, float] = (0.0, 0.0, -1.0)
    ang_vel_rad_s: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    accel_m_s2: Tuple[float, float, float] = (0.0, 0.0, 9.81)
    valid: bool = True


class IMUDriverProtocol(Protocol):
    """Strategy interface for 9-DOF orientation IMU sensors."""
    def read(self) -> IMUReading: ...
    def close(self) -> None: ...


def rpy_deg_to_projected_gravity(roll_deg: float, pitch_deg: float) -> Tuple[float, float, float]:
    """
    Computes unit gravity vector `[gx, gy, gz]` projected into the robot base frame
    (`R^T @ [0, 0, -1]`) matching `LasiusGymEnv` and `ResidualPolicyRunner`.
    """
    r = math.radians(roll_deg)
    p = math.radians(pitch_deg)
    gx = math.sin(p)
    gy = -math.cos(p) * math.sin(r)
    gz = -math.cos(p) * math.cos(r)
    return (gx, gy, gz)


def parse_bno085_rvc_frame(frame: bytes) -> Optional[IMUReading]:
    """
    Parses a single 19-byte Adafruit BNO085 UART-RVC packet:
        [0..1]   Header: 0xAA, 0xAA
        [2]      Sequence index (uint8)
        [3..4]   Yaw   (int16 LE, 0.01 deg/LSB)
        [5..6]   Pitch (int16 LE, 0.01 deg/LSB)
        [7..8]   Roll  (int16 LE, 0.01 deg/LSB)
        [9..10]  X-Accel (int16 LE, 1 mg/LSB = 0.00980665 m/s^2)
        [11..12] Y-Accel (int16 LE, 1 mg/LSB)
        [13..14] Z-Accel (int16 LE, 1 mg/LSB)
        [15..17] Reserved (3 bytes)
        [18]     Checksum: sum(frame[2:18]) & 0xFF

    Returns `IMUReading` if header & checksum are valid, else `None`.
    """
    if len(frame) != 19 or frame[0] != 0xAA or frame[1] != 0xAA:
        return None
    checksum = sum(frame[2:18]) & 0xFF
    if checksum != frame[18]:
        return None

    yaw_raw, pitch_raw, roll_raw, ax_raw, ay_raw, az_raw = struct.unpack_from("<hhhhhh", frame, 3)
    yaw_deg = yaw_raw * 0.01
    pitch_deg = pitch_raw * 0.01
    roll_deg = roll_raw * 0.01

    mg_to_ms2 = 0.00980665
    accel = (ax_raw * mg_to_ms2, ay_raw * mg_to_ms2, az_raw * mg_to_ms2)
    proj_g = rpy_deg_to_projected_gravity(roll_deg, pitch_deg)

    return IMUReading(
        roll_deg=roll_deg,
        pitch_deg=pitch_deg,
        yaw_deg=yaw_deg,
        proj_gravity=proj_g,
        ang_vel_rad_s=(0.0, 0.0, 0.0),
        accel_m_s2=accel,
        valid=True,
    )


class BNO085UARTRVCDriver:
    """
    Hardware UART-RVC driver for Adafruit BNO085 (115200 baud, 100 Hz).
    Connects via Raspberry Pi UART (`/dev/serial0` or `/dev/ttyAMA*`) so real-time
    `i2c-1` servo/ADC polling is completely unaffected by BNO085 clock-stretching.
    """

    def __init__(self, port: str = "/dev/serial0", baudrate: int = 115200, timeout: float = 0.05):
        import serial  # Optional dependency only needed on physical Raspberry Pi
        self._serial = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
        self._last_reading = IMUReading(valid=False)
        self._last_rpy: Optional[Tuple[float, float, float]] = None

    def read(self, dt: float = 0.02) -> IMUReading:
        """Reads and parses the newest complete 19-byte RVC packet from UART."""
        buf = self._serial.read(64)
        idx = buf.rfind(b"\xaa\xaa")
        while idx != -1:
            if idx + 19 <= len(buf):
                parsed = parse_bno085_rvc_frame(buf[idx : idx + 19])
                if parsed is not None:
                    if self._last_rpy is not None and dt > 1e-4:
                        dr = math.radians(parsed.roll_deg - self._last_rpy[0]) / dt
                        dp = math.radians(parsed.pitch_deg - self._last_rpy[1]) / dt
                        dy = math.radians(parsed.yaw_deg - self._last_rpy[2]) / dt
                        parsed.ang_vel_rad_s = (dr, dp, dy)
                    self._last_rpy = (parsed.roll_deg, parsed.pitch_deg, parsed.yaw_deg)
                    self._last_reading = parsed
                    return parsed
            idx = buf.rfind(b"\xaa\xaa", 0, idx)
        return self._last_reading

    def close(self) -> None:
        try:
            self._serial.close()
        except Exception:
            pass


class SimulatedIMUDriver:
    """Deterministic in-memory BNO085 simulator for unit tests and offline Digital Twin."""

    def __init__(self, roll_deg: float = 0.0, pitch_deg: float = 0.0, yaw_deg: float = 0.0):
        self.roll_deg = float(roll_deg)
        self.pitch_deg = float(pitch_deg)
        self.yaw_deg = float(yaw_deg)
        self.ang_vel_rad_s: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    def set_attitude(
        self,
        roll_deg: float,
        pitch_deg: float,
        yaw_deg: float = 0.0,
        ang_vel_rad_s: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> None:
        self.roll_deg = float(roll_deg)
        self.pitch_deg = float(pitch_deg)
        self.yaw_deg = float(yaw_deg)
        self.ang_vel_rad_s = ang_vel_rad_s

    def read(self) -> IMUReading:
        return IMUReading(
            roll_deg=self.roll_deg,
            pitch_deg=self.pitch_deg,
            yaw_deg=self.yaw_deg,
            proj_gravity=rpy_deg_to_projected_gravity(self.roll_deg, self.pitch_deg),
            ang_vel_rad_s=self.ang_vel_rad_s,
            accel_m_s2=(0.0, 0.0, 9.81),
            valid=True,
        )

    def close(self) -> None:
        pass


# ---------------------------------------------------------------------------
# 2. Power & Current Monitor (INA260 / INA228 on Mux CH6)
# ---------------------------------------------------------------------------

@dataclass
class PowerReading:
    """2S LiPo power-rail telemetry sample with battery protection flags."""
    bus_voltage_v: float
    current_a: float
    power_w: float
    low_voltage_warning: bool = False
    critical_cutoff: bool = False
    valid: bool = True


class PowerMonitorProtocol(Protocol):
    """Strategy interface for voltage/current power monitors (INA260/INA228)."""
    def read(self) -> PowerReading: ...
    def close(self) -> None: ...


class SimulatedPowerMonitor:
    """Simulated 2S LiPo power monitor with low-voltage cutoff guards."""

    def __init__(
        self,
        bus_voltage_v: float = 7.6,
        current_a: float = 2.4,
        warn_voltage_v: float = 6.8,
        cutoff_voltage_v: float = 6.4,
    ):
        self.bus_voltage_v = float(bus_voltage_v)
        self.current_a = float(current_a)
        self.warn_voltage_v = float(warn_voltage_v)
        self.cutoff_voltage_v = float(cutoff_voltage_v)

    def read(self) -> PowerReading:
        v = self.bus_voltage_v
        i = self.current_a
        return PowerReading(
            bus_voltage_v=v,
            current_a=i,
            power_w=round(v * i, 3),
            low_voltage_warning=v <= self.warn_voltage_v,
            critical_cutoff=v <= self.cutoff_voltage_v,
            valid=True,
        )

    def close(self) -> None:
        pass


# ---------------------------------------------------------------------------
# 3. Multi-Zone Time-of-Flight Distance Sensor (VL53L5CX)
# ---------------------------------------------------------------------------

@dataclass
class ToFReading:
    """Downsampled 3x3 VL53L5CX Time-of-Flight distance matrix (meters)."""
    grid_3x3_m: Tuple[float, ...]
    min_distance_m: float
    mean_distance_m: float
    valid: bool = True


class ToFSensorProtocol(Protocol):
    """Strategy interface for multi-zone ToF terrain/obstacle scanners."""
    def read(self) -> ToFReading: ...
    def close(self) -> None: ...


class SimulatedToFSensor:
    """Simulated 3x3 belly/front VL53L5CX ToF sensor."""

    def __init__(self, nominal_distance_m: float = 0.090):
        self._grid: List[float] = [float(nominal_distance_m)] * 9

    def set_grid(self, distances_m: List[float]) -> None:
        if len(distances_m) != 9:
            raise ValueError(f"Expected 9 zone distances for 3x3 ToF grid, got {len(distances_m)}")
        self._grid = [max(0.0, float(d)) for d in distances_m]

    def read(self) -> ToFReading:
        vals = tuple(self._grid)
        return ToFReading(
            grid_3x3_m=vals,
            min_distance_m=min(vals),
            mean_distance_m=sum(vals) / 9.0,
            valid=True,
        )

    def close(self) -> None:
        pass
