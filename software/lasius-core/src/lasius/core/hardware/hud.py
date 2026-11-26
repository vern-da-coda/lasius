"""
Rear Telemetry HUD Display Driver (`lasius.core.hardware.hud`).

Purpose & Role:
    Drives the 0.96" 128x64 I2C OLED status HUD (`SSD1306`, Dual-Zone Yellow
    `y=0..15` / Ice-Blue `y=16..63`, address `0x3C`) mounted in the rear
    telemetry cockpit of `chassis_rpi_mount.FCStd` / `chassis_canopy.FCStd`.

    Bus Isolation Rule (Zero Real-Time Impact):
        Must run exclusively on a dedicated auxiliary Raspberry Pi 4 I2C bus
        (e.g., `i2c-3` via `dtoverlay=i2c3,pins_4_5` — NEVER on the 50–100 Hz
        real-time servo/ADC bus `i2c-1`), refreshed asynchronously at <= 2–5 Hz.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Protocol


@dataclass
class HUDTelemetrySnapshot:
    """Compact status summary rendered to the 128x64 Dual-Zone Rear OLED HUD."""
    battery_v: float = 7.6
    current_a: float = 0.0
    gait_mode: str = "TRIPOD"
    servos_armed: bool = False
    ip_address: str = "127.0.0.1"
    cpu_temp_c: float = 45.0
    warning_text: str = ""


class HUDDisplayProtocol(Protocol):
    """Strategy interface for rear OLED status displays."""
    def render(self, snapshot: HUDTelemetrySnapshot) -> List[str]: ...
    def clear(self) -> None: ...
    def close(self) -> None: ...


def format_dual_zone_hud_lines(snapshot: HUDTelemetrySnapshot) -> List[str]:
    """
    Formats a 5-line text layout tailored to the 0.96" 128x64 Dual-Zone SSD1306:
      - Line 0 (Yellow Top Band, y=0..15):  Battery voltage, current & ARM state
      - Lines 1–4 (Ice-Blue Body, y=16..63): Gait mode, IP, CPU temp & alert bar
    Each line fits cleanly in 21 monospace characters (6 px font -> 126 px <= 128 px).
    """
    arm_tag = "ARM" if snapshot.servos_armed else "LOG"
    line0 = f"{snapshot.battery_v:4.1f}V {snapshot.current_a:4.1f}A [{arm_tag}]"
    line1 = f"GAIT: {snapshot.gait_mode[:14].upper()}"
    line2 = f"IP: {snapshot.ip_address[:17]}"
    line3 = f"CPU: {snapshot.cpu_temp_c:4.1f}C"
    line4 = snapshot.warning_text[:21] if snapshot.warning_text else "STATUS: OK"
    return [line0[:21], line1[:21], line2[:21], line3[:21], line4[:21]]


class SimulatedOLEDHUD:
    """In-memory SSD1306 rear telemetry HUD simulator for offline tests & simulation."""

    def __init__(self, bus_num: int = 3, address: int = 0x3C):
        if bus_num == 1:
            raise ValueError(
                "OLED HUD must not use real-time bus i2c-1! Use isolated auxiliary bus (e.g. i2c-3)."
            )
        self.bus_num = int(bus_num)
        self.address = int(address)
        self.last_lines: List[str] = []
        self.render_count: int = 0

    def render(self, snapshot: HUDTelemetrySnapshot) -> List[str]:
        self.last_lines = format_dual_zone_hud_lines(snapshot)
        self.render_count += 1
        return list(self.last_lines)

    def clear(self) -> None:
        self.last_lines = []

    def close(self) -> None:
        pass


class SSD1306I2CHUD:
    """
    Hardware 0.96" 128x64 SSD1306 driver bound strictly to an auxiliary I2C bus
    (`i2c-3` default, rejecting `i2c-1` by design to protect real-time locomotion).
    Uses `luma.oled` or `adafruit-circuitpython-ssd1306` when installed on Raspberry Pi 4.
    """

    def __init__(self, bus_num: int = 3, address: int = 0x3C):
        if bus_num == 1:
            raise ValueError(
                "Refusing to attach SSD1306 OLED to real-time servo/ADC bus i2c-1; use i2c-3/4/5."
            )
        self.bus_num = int(bus_num)
        self.address = int(address)
        self._device = None
        self.last_lines: List[str] = []

        try:
            from luma.core.interface.serial import i2c as luma_i2c
            from luma.oled.device import ssd1306
            serial_if = luma_i2c(port=self.bus_num, address=self.address)
            self._device = ssd1306(serial_if, width=128, height=64)
        except Exception:
            self._device = None

    def render(self, snapshot: HUDTelemetrySnapshot) -> List[str]:
        lines = format_dual_zone_hud_lines(snapshot)
        self.last_lines = lines
        if self._device is not None:
            try:
                from luma.core.render import canvas
                with canvas(self._device) as draw:
                    # Yellow top band (y = 0..15)
                    draw.text((0, 2), lines[0], fill="white")
                    # Ice-blue main telemetry band (y = 16..63)
                    for idx, txt in enumerate(lines[1:]):
                        draw.text((0, 18 + idx * 11), txt, fill="white")
            except Exception:
                pass
        return list(lines)

    def clear(self) -> None:
        self.last_lines = []
        if self._device is not None:
            try:
                self._device.clear()
            except Exception:
                pass

    def close(self) -> None:
        self.clear()
