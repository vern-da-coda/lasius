"""
Hardware Abstraction Layer (HAL) Package (`lasius.core.hardware`).

Purpose & Role:
    Isolates direct I2C hardware register communication, PWM pulse width math,
    and closed-loop PCA9548A + ADS1115 analog feedback from high-level
    kinematics and gait control.

Exports:
    - `PWMDriverProtocol`: Strategy interface implemented by both mock and physical PWM drivers.
    - `MockPWMDriver`: Thread-safe in-memory PWM simulator for unit tests and Digital Twin streaming.
    - `RealPCA9685Driver`: Thread-safe SMBus driver for the dual PCA9685 boards (`0x40` & `0x42`).
    - `ADCDriverProtocol`: Strategy interface for closed-loop leg potentiometer & foot switch reading.
    - `RealADS1115MuxDriver`: Thread-safe SMBus driver for PCA9548A (`0x71`) + 6x ADS1115 (`0x48`).
    - `SimulatedADCDriver`: First-order physics lag follower for offline simulation and unit tests.
    - `PRE_PULSE_INVALID_VOLTAGE_V`: Empirical pre-first-PWM-pulse Reely NR-645 voltage (`0.266 V`).
    - `Servo`: Logical actuator with closed-loop potentiometer calibration & dynamic lag model.
"""

from .driver import (
    PWMDriverProtocol,
    MockPWMDriver,
    RealPCA9685Driver,
    _MODE1,
    _MODE2,
    _PRESCALE,
    _LED0_ON_L,
    _ALL_LED_ON_L,
)
from .adc import (
    ADCDriverProtocol,
    RealADS1115MuxDriver,
    SimulatedADCDriver,
    DEFAULT_MUX_ADDRESS,
    DEFAULT_ADC_ADDRESS,
    PRE_PULSE_INVALID_VOLTAGE_V,
)
from .servo import Servo
from .sensors import (
    IMUReading,
    IMUDriverProtocol,
    BNO085UARTRVCDriver,
    SimulatedIMUDriver,
    rpy_deg_to_projected_gravity,
    parse_bno085_rvc_frame,
    PowerReading,
    PowerMonitorProtocol,
    SimulatedPowerMonitor,
    ToFReading,
    ToFSensorProtocol,
    SimulatedToFSensor,
)
from .hud import (
    HUDTelemetrySnapshot,
    HUDDisplayProtocol,
    SimulatedOLEDHUD,
    SSD1306I2CHUD,
    format_dual_zone_hud_lines,
)

__all__ = [
    "PWMDriverProtocol",
    "MockPWMDriver",
    "RealPCA9685Driver",
    "ADCDriverProtocol",
    "RealADS1115MuxDriver",
    "SimulatedADCDriver",
    "DEFAULT_MUX_ADDRESS",
    "DEFAULT_ADC_ADDRESS",
    "PRE_PULSE_INVALID_VOLTAGE_V",
    "Servo",
    "IMUReading",
    "IMUDriverProtocol",
    "BNO085UARTRVCDriver",
    "SimulatedIMUDriver",
    "rpy_deg_to_projected_gravity",
    "parse_bno085_rvc_frame",
    "PowerReading",
    "PowerMonitorProtocol",
    "SimulatedPowerMonitor",
    "ToFReading",
    "ToFSensorProtocol",
    "SimulatedToFSensor",
    "HUDTelemetrySnapshot",
    "HUDDisplayProtocol",
    "SimulatedOLEDHUD",
    "SSD1306I2CHUD",
    "format_dual_zone_hud_lines",
    "_MODE1",
    "_MODE2",
    "_PRESCALE",
    "_LED0_ON_L",
    "_ALL_LED_ON_L",
]
