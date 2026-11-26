"""
Lightweight Pure-NumPy Sim-to-Real Residual RL Policy Runner (`lasius.core.sim.policy`).

Purpose & Role:
    Executes trained PPO residual locomotion policies at 50 Hz with **zero
    PyTorch / Stable-Baselines3 runtime dependency** (ideal for Raspberry Pi 4
    deployment in `lasius-core` as well as PyBullet simulation & A/B evaluation).

    Features:
    - Loads exported `.npz` MLP bundles (exact float32 weights + `VecNormalize`
      running mean/var/clip statistics + metadata) OR directly loads SB3 `.zip`
      models when Stable-Baselines3 is installed.
    - Pure-NumPy forward pass (`~0.1 ms` per 50 Hz tick on Pi 4).
    - Optional **Adaptive Terrain Gate** (`adaptive_gate=True`): smoothly scales
      residual authority `g in [0, 1]` according to measured IMU tilt and angular
      rate, suppressing flat-ground micro-jitter while preserving 100% PPO
      compensation on slopes, steps, rough terrain, and external pushes.
    - Sensor-faithful observation builder (`build_proprioceptive_observation`)
      matching `LasiusGymEnv` (71-dim proprioceptive + optional 9-dim ToF grid).
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np


@dataclass
class AdaptiveGateConfig:
    """Parameters for tilt/disturbance-aware flat-terrain residual damping."""
    enabled: bool = False
    min_gain: float = 0.0                  # Gain on perfectly flat steady walking
    tilt_low_rad: float = math.radians(2.0)   # Below this tilt -> min_gain
    tilt_high_rad: float = math.radians(6.5)  # Above this tilt -> 1.0 full PPO gain
    rate_low_rad_s: float = 0.25           # Roll/pitch angular velocity lower threshold
    rate_high_rad_s: float = 0.85          # Roll/pitch angular velocity full-gain threshold
    smoothing_alpha: float = 0.35          # EMA smoothing on gate scalar


def _apply_activation(x: np.ndarray, name: str) -> np.ndarray:
    act = name.lower()
    if act == "tanh":
        return np.tanh(x)
    if act == "relu":
        return np.maximum(x, 0.0)
    if act == "elu":
        return np.where(x > 0.0, x, np.expm1(x))
    if act == "silu" or act == "swish":
        return x / (1.0 + np.exp(-x))
    raise ValueError(f"Unsupported MLP activation: {name}")


class ResidualPolicyRunner:
    """
    Pure-NumPy deterministic inference engine for Lasius v2 Residual PPO policies.
    """

    def __init__(
        self,
        weights: List[np.ndarray],
        biases: List[np.ndarray],
        activation: str = "tanh",
        obs_mean: Optional[np.ndarray] = None,
        obs_var: Optional[np.ndarray] = None,
        obs_epsilon: float = 1e-8,
        clip_obs: float = 10.0,
        residual_joint_limit_rad: float = 0.20,
        metadata: Optional[Dict[str, Any]] = None,
        gate_config: Optional[AdaptiveGateConfig] = None,
    ):
        if len(weights) != len(biases) or len(weights) == 0:
            raise ValueError("ResidualPolicyRunner requires matching non-empty weights and biases.")

        self.weights = [np.asarray(w, dtype=np.float32) for w in weights]
        self.biases = [np.asarray(b, dtype=np.float32) for b in biases]
        self.activation = str(activation)
        self.input_dim = int(self.weights[0].shape[0])
        self.output_dim = int(self.weights[-1].shape[1])

        self.obs_mean = (
            np.asarray(obs_mean, dtype=np.float32)
            if obs_mean is not None
            else np.zeros(self.input_dim, dtype=np.float32)
        )
        self.obs_var = (
            np.asarray(obs_var, dtype=np.float32)
            if obs_var is not None
            else np.ones(self.input_dim, dtype=np.float32)
        )
        self.obs_epsilon = float(obs_epsilon)
        self.clip_obs = float(clip_obs)
        self.residual_joint_limit_rad = float(residual_joint_limit_rad)
        self.metadata = dict(metadata or {})
        self.gate_config = gate_config or AdaptiveGateConfig()

        # Precompute inverse std for fast 50 Hz normalization
        self._inv_obs_std = (1.0 / np.sqrt(self.obs_var + self.obs_epsilon)).astype(np.float32)
        self._gate_value: float = 1.0 if not self.gate_config.enabled else self.gate_config.min_gain
        self.last_action: np.ndarray = np.zeros(self.output_dim, dtype=np.float32)

    def reset(self) -> None:
        """Resets internal temporal gate and previous action memory."""
        self._gate_value = 1.0 if not self.gate_config.enabled else self.gate_config.min_gain
        self.last_action.fill(0.0)

    def normalize_obs(self, raw_obs: np.ndarray) -> np.ndarray:
        """Applies `VecNormalize`-identical observation normalization and clipping."""
        obs = np.asarray(raw_obs, dtype=np.float32).reshape(-1)
        if obs.shape[0] != self.input_dim:
            raise ValueError(
                f"Observation dim mismatch: expected {self.input_dim}, got {obs.shape[0]}"
            )
        normed = (obs - self.obs_mean) * self._inv_obs_std
        return np.clip(normed, -self.clip_obs, self.clip_obs).astype(np.float32)

    def compute_adaptive_gate(self, raw_obs: np.ndarray) -> float:
        """
        Computes smooth terrain/disturbance blend factor `g in [min_gain, 1.0]`
        from proprioceptive IMU gravity vector (`obs[0:3]`) and roll/pitch rate (`obs[3:5]`).
        """
        if not self.gate_config.enabled:
            self._gate_value = 1.0
            return 1.0

        obs = np.asarray(raw_obs, dtype=np.float32).reshape(-1)
        # Projected gravity vector in base frame: flat = [0, 0, -1]
        g_xy = float(math.hypot(float(obs[0]), float(obs[1])))
        tilt_rad = math.asin(min(1.0, g_xy))
        rp_rate = float(math.hypot(float(obs[3]), float(obs[4])))

        cfg = self.gate_config
        t_tilt = (tilt_rad - cfg.tilt_low_rad) / max(cfg.tilt_high_rad - cfg.tilt_low_rad, 1e-5)
        t_rate = (rp_rate - cfg.rate_low_rad_s) / max(cfg.rate_high_rad_s - cfg.rate_low_rad_s, 1e-5)
        raw_blend = max(0.0, min(1.0, max(t_tilt, t_rate)))
        # Smoothstep curve for C1-continuous blending
        smooth_blend = raw_blend * raw_blend * (3.0 - 2.0 * raw_blend)
        target_gate = cfg.min_gain + (1.0 - cfg.min_gain) * smooth_blend

        alpha = cfg.smoothing_alpha
        self._gate_value = (1.0 - alpha) * self._gate_value + alpha * target_gate
        return float(self._gate_value)

    def predict_action(self, raw_obs: np.ndarray, normalize: bool = True) -> np.ndarray:
        """
        Runs deterministic actor MLP forward pass and returns clipped action in `[-1, 1]`.
        """
        x = self.normalize_obs(raw_obs) if normalize else np.asarray(raw_obs, dtype=np.float32).reshape(-1)
        for i in range(len(self.weights) - 1):
            x = _apply_activation(x @ self.weights[i] + self.biases[i], self.activation)
        out = x @ self.weights[-1] + self.biases[-1]
        action = np.clip(out, -1.0, 1.0).astype(np.float32)

        if self.gate_config.enabled:
            gate = self.compute_adaptive_gate(raw_obs)
            action = (action * gate).astype(np.float32)

        self.last_action = action
        return action

    def predict_residual_rad(self, raw_obs: np.ndarray, normalize: bool = True) -> np.ndarray:
        """Returns 18-dim additive URDF joint angle offsets in radians."""
        return self.predict_action(raw_obs, normalize=normalize) * self.residual_joint_limit_rad

    def predict_residual_deg(self, raw_obs: np.ndarray, normalize: bool = True) -> np.ndarray:
        """Returns 18-dim additive joint angle offsets in degrees."""
        return np.degrees(self.predict_residual_rad(raw_obs, normalize=normalize)).astype(np.float32)

    def save_npz(self, path: str | Path) -> Path:
        """Saves weights, biases, normalization stats, and metadata into a portable `.npz` file."""
        out_path = Path(path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload: Dict[str, Any] = {
            "num_layers": np.array(len(self.weights), dtype=np.int32),
            "activation": np.array(self.activation),
            "obs_mean": self.obs_mean.astype(np.float32),
            "obs_var": self.obs_var.astype(np.float32),
            "obs_epsilon": np.array(self.obs_epsilon, dtype=np.float32),
            "clip_obs": np.array(self.clip_obs, dtype=np.float32),
            "residual_joint_limit_rad": np.array(self.residual_joint_limit_rad, dtype=np.float32),
            "metadata_json": np.array(json.dumps(self.metadata)),
        }
        for i, (w, b) in enumerate(zip(self.weights, self.biases)):
            payload[f"w_{i}"] = w.astype(np.float32)
            payload[f"b_{i}"] = b.astype(np.float32)
        np.savez_compressed(out_path, **payload)
        return out_path

    @classmethod
    def load_npz(
        cls,
        path: str | Path,
        gate_config: Optional[AdaptiveGateConfig] = None,
    ) -> "ResidualPolicyRunner":
        """Loads a portable pure-NumPy `.npz` policy bundle (no PyTorch/SB3 required)."""
        data = np.load(str(path), allow_pickle=False)
        num_layers = int(data["num_layers"])
        weights = [data[f"w_{i}"].astype(np.float32) for i in range(num_layers)]
        biases = [data[f"b_{i}"].astype(np.float32) for i in range(num_layers)]
        activation = str(data["activation"].item())
        meta = json.loads(str(data["metadata_json"].item())) if "metadata_json" in data else {}
        return cls(
            weights=weights,
            biases=biases,
            activation=activation,
            obs_mean=data["obs_mean"],
            obs_var=data["obs_var"],
            obs_epsilon=float(data["obs_epsilon"]),
            clip_obs=float(data["clip_obs"]),
            residual_joint_limit_rad=float(data["residual_joint_limit_rad"]),
            metadata=meta,
            gate_config=gate_config,
        )

    @classmethod
    def from_sb3_ppo(
        cls,
        model_path: str | Path,
        vecnorm_path: Optional[str | Path] = None,
        residual_joint_limit_rad: float = 0.20,
        gate_config: Optional[AdaptiveGateConfig] = None,
    ) -> "ResidualPolicyRunner":
        """
        Extracts deterministic actor MLP weights & VecNormalize stats directly from
        a Stable-Baselines3 PPO `.zip` checkpoint into a pure-NumPy runner.
        """
        from stable_baselines3 import PPO
        from stable_baselines3.common.vec_env import VecNormalize
        import torch.nn as nn

        model_path = Path(model_path)
        model = PPO.load(str(model_path), device="cpu")
        policy = model.policy

        weights: List[np.ndarray] = []
        biases: List[np.ndarray] = []
        activation = "tanh"

        for module in policy.mlp_extractor.policy_net:
            if isinstance(module, nn.Linear):
                # Transpose from PyTorch (out, in) to NumPy row-vector (in, out)
                weights.append(module.weight.detach().cpu().numpy().T.astype(np.float32))
                biases.append(module.bias.detach().cpu().numpy().astype(np.float32))
            elif isinstance(module, nn.Tanh):
                activation = "tanh"
            elif isinstance(module, nn.ReLU):
                activation = "relu"
            elif isinstance(module, nn.ELU):
                activation = "elu"
            elif isinstance(module, nn.SiLU):
                activation = "silu"

        # Output linear layer (`action_net`)
        weights.append(policy.action_net.weight.detach().cpu().numpy().T.astype(np.float32))
        biases.append(policy.action_net.bias.detach().cpu().numpy().astype(np.float32))

        obs_mean = None
        obs_var = None
        obs_epsilon = 1e-8
        clip_obs = 10.0

        # Auto-discover matching VecNormalize stats if omitted
        if vecnorm_path is None:
            for cand in [
                model_path.parent / "best_vecnormalize.pkl" if model_path.name == "best_model.zip" else None,
                model_path.with_name(model_path.stem + "_vecnormalize.pkl"),
                model_path.parent / "vecnormalize.pkl",
                model_path.parent / "lasius_v2_ppo_residual_final_vecnormalize.pkl",
            ]:
                if cand is not None and cand.is_file():
                    vecnorm_path = cand
                    break

        if vecnorm_path is not None and Path(vecnorm_path).is_file():
            class _MinimalVecEnvStub:
                num_envs = 1
                observation_space = model.observation_space
                action_space = model.action_space
                render_mode = None

            vn = VecNormalize.load(str(vecnorm_path), _MinimalVecEnvStub())
            if getattr(vn, "obs_rms", None) is not None:
                obs_mean = np.asarray(vn.obs_rms.mean, dtype=np.float32)
                obs_var = np.asarray(vn.obs_rms.var, dtype=np.float32)
            obs_epsilon = float(getattr(vn, "epsilon", 1e-8))
            clip_obs = float(getattr(vn, "clip_obs", 10.0))

        meta: Dict[str, Any] = {"source_model": model_path.name}
        for meta_cand in [model_path.parent / "training_meta.json", model_path.parent.parent / "training_meta.json"]:
            if meta_cand.is_file():
                try:
                    meta.update(json.loads(meta_cand.read_text(encoding="utf-8")))
                    break
                except Exception:
                    pass

        return cls(
            weights=weights,
            biases=biases,
            activation=activation,
            obs_mean=obs_mean,
            obs_var=obs_var,
            obs_epsilon=obs_epsilon,
            clip_obs=clip_obs,
            residual_joint_limit_rad=residual_joint_limit_rad,
            metadata=meta,
            gate_config=gate_config,
        )

    @classmethod
    def load(
        cls,
        path: str | Path,
        vecnorm_path: Optional[str | Path] = None,
        gate_config: Optional[AdaptiveGateConfig] = None,
    ) -> "ResidualPolicyRunner":
        """Auto-loads either a `.npz` bundle or an SB3 `.zip` model."""
        p = Path(path)
        if p.suffix.lower() == ".npz":
            return cls.load_npz(p, gate_config=gate_config)
        return cls.from_sb3_ppo(p, vecnorm_path=vecnorm_path, gate_config=gate_config)


def build_proprioceptive_observation(
    proj_gravity: Sequence[float],
    ang_vel_base: Sequence[float],
    joint_pos_diff_rad: Sequence[float],
    joint_vel_rad_s: Sequence[float],
    foot_contacts: Sequence[float],
    gait_phase: float,
    cmd_vel: Sequence[float],
    prev_action: Sequence[float],
    belly_tof_grid: Optional[Sequence[float]] = None,
) -> np.ndarray:
    """
    Constructs the canonical 71-dim (or 80-dim with 3x3 ToF) proprioceptive
    observation vector matching `LasiusGymEnv._get_observation()` for Sim-to-Real
    inference on real robot hardware or PyBullet teleoperation.
    """
    phase_rad = 2.0 * math.pi * float(gait_phase)
    parts = [
        np.asarray(proj_gravity, dtype=np.float32).reshape(3),
        np.asarray(ang_vel_base, dtype=np.float32).reshape(3),
        np.asarray(joint_pos_diff_rad, dtype=np.float32).reshape(18),
        np.asarray(joint_vel_rad_s, dtype=np.float32).reshape(18),
        np.asarray(foot_contacts, dtype=np.float32).reshape(6),
        np.array([math.sin(phase_rad), math.cos(phase_rad)], dtype=np.float32),
        np.asarray(cmd_vel, dtype=np.float32).reshape(3),
        np.asarray(prev_action, dtype=np.float32).reshape(18),
    ]
    if belly_tof_grid is not None:
        parts.append(np.asarray(belly_tof_grid, dtype=np.float32).reshape(9))
    return np.concatenate(parts).astype(np.float32)
