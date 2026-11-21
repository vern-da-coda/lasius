"""
Central Hexapod Robot Coordinator (`lasius.core.robot`).

Purpose & Role:
    Provides the `Hexapod` aggregate root class that binds physical configuration
    (`HexapodConfig`), I2C/mock PWM drivers (`PWMDriverProtocol`), closed-loop
    PCA9548A + ADS1115 ADC telemetry (`ADCDriverProtocol`), the six 3-DOF legs
    (`Leg`), the 50 Hz walking gait engine (`GaitProtocol`), and the
    telemetry/control server (`LasiusServer` / `OrderDispatcher`).

Classes:
    - `Hexapod`:
        * Instantiates all 18 `Servo` objects and groups them into 6 `Leg` instances.
        * Executes the 50 Hz locomotion step in `tick()` when `locomotion_active` is True,
          computing inverse kinematics for all 6 legs and streaming live joint angles
          to connected WebSocket clients.
        * Polls closed-loop ADS1115 potentiometer & foot-switch voltages across all
          6 multiplexer sub-buses (`poll_telemetry()`), computing calibrated measured
          angles, first-order dynamic reference lag errors, stall flags, and actual
          forward-kinematics foot positions.
        * Arbitrates safe disengagement (`relax_all()`, `locomotion_active = False`)
          so isolated single-leg calibration and test routines are never overwritten.
"""

import threading
import time
from typing import List, Dict, Type, Tuple, Optional, Any

from lasius.core.config import HexapodConfig, load_config
from lasius.core.hardware import (
    Servo,
    PWMDriverProtocol,
    MockPWMDriver,
    RealPCA9685Driver,
    ADCDriverProtocol,
    RealADS1115MuxDriver,
    SimulatedADCDriver,
)
from lasius.core.motion import (
    Leg,
    Joint,
    BodySide,
    LegRow,
    LegIdentifier,
    GaitProtocol,
    TripodGait,
    OmniGait,
)
from lasius.core.control import OrderDispatcher
from lasius.core.server import VisualizerServer


class Hexapod:
    """
    The central control class for the hexapod robot.
    """
    def __init__(
        self,
        config: HexapodConfig,
        drivers: Dict[int, PWMDriverProtocol],
        adc_driver: Optional[ADCDriverProtocol] = None,
    ):
        print("Initializing Hexapod...")
        self.config = config
        self.gait_engine: Optional[GaitProtocol] = None
        self.locomotion_active: bool = False
        self.drivers = drivers
        self.visualizer: Optional[VisualizerServer] = self._get_visualizer_from_drivers()
        self._telemetry_lock = threading.RLock()
        self._last_telemetry_ts: Optional[float] = None

        all_servos = [Servo(config=sc, driver=self.drivers[sc.board_address]) for sc in self.config.servos]
        servos_by_leg = self._group_servos_by_leg(all_servos)

        # Physical leg dimensions loaded from config
        coxa_len = self.config.geometry.limbs.coxa
        femur_len = self.config.geometry.limbs.femur
        tibia_len = self.config.geometry.limbs.tibia

        self.legs: Dict[Tuple[BodySide, LegRow], Leg] = {}
        for name, servos in servos_by_leg.items():
            side_str, row_str = name.split("_")
            side = BodySide(side_str)
            row = LegRow(row_str)

            coxa_joint = Joint(servo=servos["coxa"], length=coxa_len)
            femur_joint = Joint(servo=servos["femur"], length=femur_len)
            tibia_joint = Joint(servo=servos["tibia"], length=tibia_len)

            self.legs[(side, row)] = Leg(
                side=side, row=row, coxa=coxa_joint, femur=femur_joint, tibia=tibia_joint
            )

        # Configure closed-loop ADC driver (physical ADS1115 mux or simulated first-order physics follower)
        telem_cfg = getattr(self.config, "telemetry", None)
        if adc_driver is not None:
            self.adc_driver: Optional[ADCDriverProtocol] = adc_driver
        elif telem_cfg and telem_cfg.enabled:
            # Auto-select SimulatedADCDriver when using MockPWMDriver
            is_all_mock = all(isinstance(d, MockPWMDriver) for d in self.drivers.values())
            if is_all_mock:
                self.adc_driver = SimulatedADCDriver(
                    tau_lag_s=telem_cfg.tau_lag_s,
                    max_speed_deg_s=telem_cfg.max_speed_deg_s,
                )
            else:
                self.adc_driver = None
        else:
            self.adc_driver = None

        if isinstance(self.adc_driver, SimulatedADCDriver):
            self._bind_simulated_adc(self.adc_driver)

        print(f"Hexapod initialized with {len(self.legs)} legs (Coxa: {coxa_len}mm, Femur: {femur_len}mm, Tibia: {tibia_len}mm).")

        if self.visualizer:
            self.dispatcher = self.visualizer.dispatcher
            self.dispatcher.set_robot(self)
            self.visualizer.start(self)
        else:
            self.dispatcher = OrderDispatcher(robot=self)

    def _bind_simulated_adc(self, sim_adc: SimulatedADCDriver) -> None:
        """Binds all 6 legs' servos to their configured PCA9548A multiplexer sub-bus channels."""
        mux_map = self.config.telemetry.leg_mux_channels
        for (side, row), leg in self.legs.items():
            leg_name = f"{side.value}_{row.value}"
            mux_ch = mux_map.get(leg_name)
            if mux_ch is not None:
                sim_adc.bind_leg_servos(
                    mux_channel=mux_ch,
                    coxa_servo=leg.coxa.servo,
                    femur_servo=leg.femur.servo,
                    tibia_servo=leg.tibia.servo,
                )

    def _get_visualizer_from_drivers(self) -> Optional[VisualizerServer]:
        for driver in self.drivers.values():
            if hasattr(driver, "visualizer_server") and driver.visualizer_server:
                return driver.visualizer_server
        return None

    def set_gait(self, gait: GaitProtocol, engage: bool = True) -> None:
        print(f"Switching to gait: {gait.__class__.__name__}")
        if hasattr(gait, "apply_geometry"):
            gait.apply_geometry(self.config.geometry)
        self.gait_engine = gait
        self.locomotion_active = engage

    def poll_telemetry(self, dt: Optional[float] = None) -> Dict[str, Any]:
        """
        Polls closed-loop ADS1115 analog feedback across all 6 multiplexer channels,
        updates each servo's measured angle, dynamic lag model, and stall state,
        and returns the current closed-loop telemetry snapshot.
        """
        now = time.perf_counter()
        if dt is None:
            if self._last_telemetry_ts is None:
                dt_val = 0.020
            else:
                dt_val = max(0.001, min(0.25, now - self._last_telemetry_ts))
        else:
            dt_val = max(0.001, float(dt))
        self._last_telemetry_ts = now

        telem_cfg = self.config.telemetry
        if self.adc_driver is not None and telem_cfg.enabled:
            if isinstance(self.adc_driver, SimulatedADCDriver) and dt is not None:
                self.adc_driver.advance_dt(dt_val)

            for (side, row), leg in self.legs.items():
                leg_name = f"{side.value}_{row.value}"
                mux_ch = telem_cfg.leg_mux_channels.get(leg_name)
                if mux_ch is None:
                    continue

                voltages = self.adc_driver.read_leg_channels(mux_ch)
                with self._telemetry_lock:
                    for adc_idx, joint in ((0, leg.coxa), (1, leg.femur), (2, leg.tibia)):
                        joint.servo.update_feedback(
                            voltage_v=voltages.get(adc_idx),
                            dt=dt_val,
                            ema_alpha=telem_cfg.ema_alpha,
                            tau_lag_s=telem_cfg.tau_lag_s,
                            max_speed_deg_s=telem_cfg.max_speed_deg_s,
                            stall_error_deg=telem_cfg.stall_error_deg,
                            stall_timeout_s=telem_cfg.stall_timeout_s,
                        )
                    v_foot = voltages.get(3)
                    leg.foot_voltage = v_foot
                    if v_foot is not None:
                        leg.foot_contact = v_foot < telem_cfg.foot_switch_threshold_v
                    else:
                        leg.foot_contact = False

        snapshot = self.get_telemetry_state()
        if self.visualizer and hasattr(self.visualizer, "send_telemetry_update"):
            self.visualizer.send_telemetry_update(snapshot)
        return snapshot

    def get_telemetry_state(self) -> Dict[str, Any]:
        """
        Returns a thread-safe snapshot of commanded vs. measured joint angles,
        validity flags, dynamic lag tracking errors, stall states, foot switch
        contacts, and actual forward-kinematics foot positions.
        """
        target_angles: Dict[str, Optional[float]] = {}
        actual_angles: Dict[str, Optional[float]] = {}
        actual_valid: Dict[str, bool] = {}
        expected_angles: Dict[str, Optional[float]] = {}
        tracking_errors: Dict[str, Optional[float]] = {}
        raw_deviations: Dict[str, Optional[float]] = {}
        stalled_joints: Dict[str, bool] = {}
        foot_contacts: Dict[str, bool] = {}
        actual_foot_positions: Dict[str, Optional[Tuple[float, float, float]]] = {}

        with self._telemetry_lock:
            for (side, row), leg in self.legs.items():
                leg_name = f"{side.value}_{row.value}"
                foot_contacts[leg_name] = bool(leg.foot_contact)
                fk_pos = leg.get_actual_tip_position()
                actual_foot_positions[leg_name] = (
                    (round(fk_pos[0], 2), round(fk_pos[1], 2), round(fk_pos[2], 2))
                    if fk_pos is not None
                    else None
                )
                for joint in (leg.coxa, leg.femur, leg.tibia):
                    s = joint.servo
                    name = s.config.name
                    target_angles[name] = round(s.current_angle, 2) if s.current_angle is not None else None
                    actual_angles[name] = round(s.measured_angle, 2) if (s.actual_valid and s.measured_angle is not None) else None
                    actual_valid[name] = bool(s.actual_valid)
                    expected_angles[name] = round(s.expected_angle, 2) if s.expected_angle is not None else None
                    tracking_errors[name] = round(s.tracking_error, 2) if (s.actual_valid and s.tracking_error is not None) else None
                    raw_deviations[name] = round(s.raw_deviation, 2) if s.raw_deviation is not None else None
                    stalled_joints[name] = bool(s.is_stalled)

        return {
            "target_angles": target_angles,
            "actual_angles": actual_angles,
            "actual_valid": actual_valid,
            "expected_angles": expected_angles,
            "tracking_errors": tracking_errors,
            "raw_deviations": raw_deviations,
            "stalled_joints": stalled_joints,
            "foot_contacts": foot_contacts,
            "actual_foot_positions": actual_foot_positions,
        }

    def get_actual_foot_positions(self) -> Dict[str, Optional[Tuple[float, float, float]]]:
        """Returns 3-DOF forward-kinematics foot positions `(x, y, z)` in mm from actual servo angles."""
        with self._telemetry_lock:
            return {
                f"{side.value}_{row.value}": leg.get_actual_tip_position()
                for (side, row), leg in self.legs.items()
            }

    def tick(self) -> None:
        if not self.gait_engine or not self.locomotion_active:
            return
        if self.visualizer and self.visualizer.is_paused:
            return
        if self.dispatcher and self.dispatcher.active_order is not None:
            if self.dispatcher.active_order.action.value in (
                "test_leg",
                "stance_leg",
                "sweep_joint",
                "wave_hello",
            ):
                return
        leg_positions = self.gait_engine.tick()

        for leg_id, coords in leg_positions.items():
            self.move_leg_tip(leg_id, *coords)

        if self.visualizer:
            all_updates = {}
            for driver in self.drivers.values():
                if hasattr(driver, "get_and_clear_angle_updates"):
                    all_updates.update(driver.get_and_clear_angle_updates())

            if all_updates:
                self.visualizer.send_angles_update(all_updates)

    @staticmethod
    def _group_servos_by_leg(servos: List[Servo]) -> Dict[str, Dict[str, Servo]]:
        grouped = {}
        for servo in servos:
            parts = servo.config.name.split("_")
            leg_name = f"{parts[0]}_{parts[1]}"
            joint_type = parts[2]
            if leg_name not in grouped:
                grouped[leg_name] = {}
            grouped[leg_name][joint_type] = servo
        return grouped

    def move_leg_tip(self, leg_id: LegIdentifier, x: float, y: float, z: float) -> None:
        key = leg_id.value
        if key in self.legs:
            self.legs[key].move_tip_to(x, y, z)

    def relax_all(self) -> None:
        """Relaxes all servos across all drivers and disengages locomotion."""
        self.locomotion_active = False
        for leg in self.legs.values():
            leg.relax()
        for d in self.drivers.values():
            if hasattr(d, "relax_all"):
                d.relax_all()

    def get_servo(self, servo_name: str) -> Optional[Servo]:
        """Finds and returns the Servo instance by its configured name."""
        for leg in self.legs.values():
            for joint in (leg.coxa, leg.femur, leg.tibia):
                if joint.servo.config.name == servo_name:
                    return joint.servo
        return None

    def get_calibration(self) -> Dict[str, Dict[str, Any]]:
        """Returns the current runtime calibration settings for all 18 servos."""
        res = {}
        for leg in self.legs.values():
            for joint in (leg.coxa, leg.femur, leg.tibia):
                s = joint.servo
                sc = s.config
                res[sc.name] = {
                    "name": sc.name,
                    "channel": sc.channel,
                    "board_address": sc.board_address,
                    "center_offset_pulse": sc.center_offset_pulse,
                    "orientation": sc.orientation,
                    "min_angle": sc.min_angle,
                    "max_angle": sc.max_angle,
                    "pulse_range": sc.pulse_range,
                    "pot_v_zero": sc.pot_v_zero,
                    "pot_v_slope": sc.pot_v_slope,
                    "current_angle": s.current_angle,
                    "measured_angle": round(s.measured_angle, 2) if (s.actual_valid and s.measured_angle is not None) else None,
                    "measured_voltage": round(s.measured_voltage, 4) if s.measured_voltage is not None else None,
                    "actual_valid": s.actual_valid,
                    "tracking_error": round(s.tracking_error, 2) if (s.actual_valid and s.tracking_error is not None) else None,
                    "is_stalled": s.is_stalled,
                }
        return res

    def apply_servo_calibration(
        self,
        servo_name: str,
        updates: Dict[str, Any],
        live_angle: Optional[float] = None,
    ) -> bool:
        """
        Updates calibration parameters on an active servo in memory and immediately re-actuates it.
        """
        servo = self.get_servo(servo_name)
        if not servo:
            return False

        if "center_offset_pulse" in updates and updates["center_offset_pulse"] is not None:
            servo.config.center_offset_pulse = int(updates["center_offset_pulse"])
        elif "offset" in updates and updates["offset"] is not None:
            servo.config.center_offset_pulse = int(updates["offset"])

        if "orientation" in updates and updates["orientation"] is not None:
            servo.config.orientation = int(updates["orientation"])

        if "min_angle" in updates and updates["min_angle"] is not None:
            servo.config.min_angle = float(updates["min_angle"])

        if "max_angle" in updates and updates["max_angle"] is not None:
            servo.config.max_angle = float(updates["max_angle"])

        if "pulse_range" in updates and updates["pulse_range"] is not None:
            servo.config.pulse_range = int(updates["pulse_range"])

        if "pot_v_zero" in updates and updates["pot_v_zero"] is not None:
            servo.config.pot_v_zero = float(updates["pot_v_zero"])

        if "pot_v_slope" in updates and updates["pot_v_slope"] is not None:
            servo.config.pot_v_slope = float(updates["pot_v_slope"])

        # Re-actuate servo so user sees immediate physical movement
        target_angle = live_angle if live_angle is not None else servo.current_angle
        if target_angle is not None:
            servo.set_angle(target_angle)
            if self.visualizer:
                self.visualizer.send_angles_update({servo_name: target_angle})

        return True

    def reset_servo_to_factory(self, servo_name: Optional[str] = None) -> bool:
        """
        Reverts in-memory servo configurations back to factory config.yaml defaults.
        If servo_name is None, reverts all servos.
        """
        base_cfg = load_config(apply_overlay=False)
        base_by_name = {sc.name: sc for sc in base_cfg.servos}
        targets = [servo_name] if servo_name else list(base_by_name.keys())

        for name in targets:
            servo = self.get_servo(name)
            if servo and name in base_by_name:
                orig = base_by_name[name]
                servo.config.center_offset_pulse = orig.center_offset_pulse
                servo.config.orientation = orig.orientation
                servo.config.min_angle = orig.min_angle
                servo.config.max_angle = orig.max_angle
                servo.config.pulse_range = orig.pulse_range
                servo.config.pot_v_zero = orig.pot_v_zero
                servo.config.pot_v_slope = orig.pot_v_slope
                if servo.current_angle is not None:
                    servo.set_angle(servo.current_angle)
                    if self.visualizer:
                        self.visualizer.send_angles_update({name: servo.current_angle})
        return True
