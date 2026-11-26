"""
Realistic Servo Actuator Dynamics Model (`lasius.core.sim.actuator`).

Purpose & Role:
    Models the physical dynamics of the 18x Reely / Torcster NR-645 MG BB
    analog metal-gear servos powered at 6.0 V, closing the Sim-to-Real gap
    between PyBullet position control and physical robot hardware:
    - First-order transit lag (tau = 0.075 s default, matching `config.yaml` / `servo.py`)
    - Rate-limited slew speed (omega_max = 350 deg/s ≈ 6.11 rad/s)
    - Realistic stall torque limit (1.1 N·m nominal at 6.0 V, randomized in DR)
    - Collision-verified mechanical soft joint limits from `config.yaml`
    - Optional potentiometer sensor noise, 12-bit ADS1115 quantization (0.26°),
      and per-joint zero-point trim offset randomization.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Dict, List, Optional, Tuple

import numpy as np


# Collision-verified mechanical soft limits in URDF joint radians.
# Derived directly from `software/lasius-core/src/lasius/core/config.yaml`
# using the PyBullet URDF convention:
#   q_coxa_urdf  = radians(-c_deg)
#   q_femur_urdf = radians(-f_deg)
#   q_tibia_urdf = radians(t_deg + 90.0)
_COXA_MIN_STD = math.radians(-25.0)
_COXA_MAX_STD = math.radians(25.0)
_COXA_FRONT_EXT = math.radians(35.0)
_FEMUR_MIN = math.radians(-90.0)
_FEMUR_MAX = math.radians(90.0)
# config.yaml tibia logical limits [-68°, +29°] -> URDF [+22°, +119°]
_TIBIA_MIN_URDF = math.radians(22.0)
_TIBIA_MAX_URDF = math.radians(119.0)


def build_joint_limits_rad(joint_names: List[str]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Returns `(lower_limits, upper_limits)` in URDF radians for the canonical 18 joints.
    Respects the 3D B-Rep collision-verified soft limits from `config.yaml`.
    """
    lows = np.zeros(len(joint_names), dtype=np.float32)
    highs = np.zeros(len(joint_names), dtype=np.float32)

    for idx, name in enumerate(joint_names):
        if name.endswith("_coxa"):
            if name == "left_front_coxa":
                # Logical c_deg in [-25°, +35°] -> URDF (-c_deg) in [-35°, +25°]
                lows[idx], highs[idx] = -_COXA_FRONT_EXT, _COXA_MAX_STD
            elif name == "right_front_coxa":
                # Logical forward swing is negative c_deg -> URDF in [-25°, +35°]
                lows[idx], highs[idx] = _COXA_MIN_STD, _COXA_FRONT_EXT
            else:
                lows[idx], highs[idx] = _COXA_MIN_STD, _COXA_MAX_STD
        elif name.endswith("_femur"):
            lows[idx], highs[idx] = _FEMUR_MIN, _FEMUR_MAX
        elif name.endswith("_tibia"):
            lows[idx], highs[idx] = _TIBIA_MIN_URDF, _TIBIA_MAX_URDF
        else:
            lows[idx], highs[idx] = -math.pi, math.pi

    return lows, highs


@dataclass
class ActuatorConfig:
    """Nominal physical parameters for Reely / Torcster NR-645 MG BB servos at 6.0 V."""
    # Dynamic lag & slew rate (matches `config.yaml` telemetry section)
    tau_lag_s: float = 0.075              # First-order transit lag constant [s]
    max_speed_rad_s: float = math.radians(350.0)  # ~6.11 rad/s (0.17 s / 60 deg)
    max_torque_nm: float = 1.10           # Stall torque at 6.0 V (~11 kg·cm)

    # PD gains for PyBullet POSITION_CONTROL (soft hobby-servo compliance)
    position_gain: float = 0.35
    velocity_gain: float = 0.85

    # Potentiometer feedback fidelity (ADS1115 V280 12-bit: 2.0 mV ≈ 0.26 deg)
    pot_quantization_rad: float = math.radians(0.26)
    pot_noise_std_rad: float = math.radians(0.50)

    # Domain Randomization bounds (active when domain_randomization=True)
    tau_lag_range: Tuple[float, float] = (0.055, 0.095)
    torque_range: Tuple[float, float] = (0.95, 1.25)
    speed_scale_range: Tuple[float, float] = (0.90, 1.10)
    zero_offset_std_rad: float = math.radians(1.0)


class ServoActuatorModel:
    """
    Stateful 18-DOF servo actuator dynamics model.

    Maintains a rate-limited first-order filtered command angle per joint and
    simulates realistic potentiometer readout noise/quantization + zero-trim offsets.
    """

    def __init__(
        self,
        joint_names: List[str],
        config: Optional[ActuatorConfig] = None,
        realistic_dynamics: bool = True,
    ):
        self.joint_names = list(joint_names)
        self.num_joints = len(self.joint_names)
        self.config = config or ActuatorConfig()
        self.realistic_dynamics = realistic_dynamics

        self.joint_low, self.joint_high = build_joint_limits_rad(self.joint_names)

        # Active per-episode randomized parameters
        self.tau_lag_s = np.full(self.num_joints, self.config.tau_lag_s, dtype=np.float32)
        self.max_torque_nm = np.full(self.num_joints, self.config.max_torque_nm, dtype=np.float32)
        self.max_speed_rad_s = np.full(self.num_joints, self.config.max_speed_rad_s, dtype=np.float32)
        self.zero_offsets_rad = np.zeros(self.num_joints, dtype=np.float32)

        # Internal actuator command state (filtered target passed to PyBullet)
        self.filtered_targets = np.zeros(self.num_joints, dtype=np.float32)
        self._last_measured_q = np.zeros(self.num_joints, dtype=np.float32)

    def reset(
        self,
        initial_angles: np.ndarray,
        rng: Optional[np.random.Generator] = None,
        randomize: bool = False,
    ) -> None:
        """Resets internal lag state and optionally samples per-episode servo parameters."""
        clamped = self.clamp_targets(initial_angles)
        self.filtered_targets = clamped.copy()
        self._last_measured_q = clamped.copy()

        if randomize and rng is not None:
            # Sample shared bank drift + slight per-servo spread
            tau_base = float(rng.uniform(*self.config.tau_lag_range))
            self.tau_lag_s = np.clip(
                tau_base + rng.uniform(-0.008, 0.008, size=self.num_joints),
                0.040,
                0.120,
            ).astype(np.float32)

            torque_base = float(rng.uniform(*self.config.torque_range))
            self.max_torque_nm = np.clip(
                torque_base + rng.uniform(-0.08, 0.08, size=self.num_joints),
                0.80,
                1.40,
            ).astype(np.float32)

            speed_scale = float(rng.uniform(*self.config.speed_scale_range))
            self.max_speed_rad_s = (
                self.config.max_speed_rad_s
                * speed_scale
                * rng.uniform(0.95, 1.05, size=self.num_joints)
            ).astype(np.float32)

            self.zero_offsets_rad = rng.normal(
                0.0, self.config.zero_offset_std_rad, size=self.num_joints
            ).astype(np.float32)
        else:
            self.tau_lag_s.fill(self.config.tau_lag_s)
            self.max_torque_nm.fill(self.config.max_torque_nm)
            self.max_speed_rad_s.fill(self.config.max_speed_rad_s)
            self.zero_offsets_rad.fill(0.0)

    def clamp_targets(self, target_angles: np.ndarray) -> np.ndarray:
        """Clamps commanded URDF angles to collision-verified mechanical soft limits."""
        return np.clip(target_angles, self.joint_low, self.joint_high).astype(np.float32)

    def step_substep(self, commanded_targets: np.ndarray, dt: float) -> np.ndarray:
        """
        Advances the internal servo lag/slew model by one physics substep (`dt`).

        Args:
            commanded_targets: Desired joint angles in URDF radians (18,).
            dt: Physics substep duration in seconds (e.g. 1/250 s = 0.004 s).

        Returns:
            Filtered motor target positions in URDF radians (18,) to send to PyBullet.
        """
        # Apply mechanical calibration trim offset and clamp to physical limits
        clamped_cmd = self.clamp_targets(commanded_targets + self.zero_offsets_rad)

        if not self.realistic_dynamics:
            self.filtered_targets = clamped_cmd
            return self.filtered_targets

        # Rate-limited first-order lag: dq/dt = clip((q_cmd - q_filt) / tau, -w_max, +w_max)
        alpha = dt / (self.tau_lag_s + dt)
        desired_delta = (clamped_cmd - self.filtered_targets) * alpha
        max_delta = self.max_speed_rad_s * dt
        stepped_delta = np.clip(desired_delta, -max_delta, max_delta)

        self.filtered_targets = self.clamp_targets(self.filtered_targets + stepped_delta)
        return self.filtered_targets

    def measure_joints(
        self,
        true_positions: np.ndarray,
        dt_control: float,
        rng: Optional[np.random.Generator] = None,
        add_noise: bool = False,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Simulates closed-loop ADS1115 potentiometer readings (12-bit quantized + noise)
        and derives realistic finite-difference joint velocities.

        Returns:
            Tuple `(measured_q, estimated_q_dot)` in radians and rad/s.
        """
        q_meas = true_positions.astype(np.float32).copy()

        if add_noise and rng is not None:
            if self.config.pot_noise_std_rad > 0.0:
                q_meas += rng.normal(
                    0.0, self.config.pot_noise_std_rad, size=self.num_joints
                ).astype(np.float32)
            step = self.config.pot_quantization_rad
            if step > 0.0:
                q_meas = np.round(q_meas / step) * step

        q_dot_est = (q_meas - self._last_measured_q) / max(dt_control, 1e-6)
        # Clip extreme spikes from quantization/reset noise to realistic range
        q_dot_est = np.clip(q_dot_est, -10.0, 10.0).astype(np.float32)
        self._last_measured_q = q_meas
        return q_meas, q_dot_est

    def get_motor_params(self) -> Tuple[np.ndarray, np.ndarray, float, float]:
        """Returns `(forces_nm, max_velocities_rad_s, pos_gain, vel_gain)` for PyBullet."""
        return (
            self.max_torque_nm,
            self.max_speed_rad_s,
            self.config.position_gain,
            self.config.velocity_gain,
        )

    def get_summary(self) -> Dict[str, float]:
        """Returns diagnostic summary of active episode servo parameters."""
        return {
            "servo_tau_mean_s": float(np.mean(self.tau_lag_s)),
            "servo_torque_mean_nm": float(np.mean(self.max_torque_nm)),
            "servo_speed_mean_rad_s": float(np.mean(self.max_speed_rad_s)),
        }
