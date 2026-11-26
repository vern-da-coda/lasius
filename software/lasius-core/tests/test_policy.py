"""
Unit Tests for Pure-NumPy Sim-to-Real Residual RL Policy Runner (`test_policy.py`).
"""

import math
from pathlib import Path

import pytest

try:
    import numpy as np
    from lasius.core.sim.policy import (
        AdaptiveGateConfig,
        ResidualPolicyRunner,
        build_proprioceptive_observation,
    )
    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    AdaptiveGateConfig = None
    ResidualPolicyRunner = None
    build_proprioceptive_observation = None
    NUMPY_AVAILABLE = False


def _make_dummy_runner(gate_config=None):
    rng = np.random.default_rng(123)
    w0 = rng.normal(0.0, 0.1, size=(71, 32)).astype(np.float32)
    b0 = np.zeros(32, dtype=np.float32)
    w1 = rng.normal(0.0, 0.1, size=(32, 18)).astype(np.float32)
    b1 = np.zeros(18, dtype=np.float32)
    return ResidualPolicyRunner(
        weights=[w0, w1],
        biases=[b0, b1],
        activation="tanh",
        obs_mean=np.linspace(-0.5, 0.5, 71, dtype=np.float32),
        obs_var=np.full(71, 2.0, dtype=np.float32),
        clip_obs=10.0,
        residual_joint_limit_rad=0.20,
        metadata={"test": True},
        gate_config=gate_config,
    )


@pytest.mark.skipif(not NUMPY_AVAILABLE, reason="numpy not installed")
class TestResidualPolicyRunner:
    def test_npz_roundtrip_bit_exact(self, tmp_path: Path):
        runner = _make_dummy_runner()
        npz_path = runner.save_npz(tmp_path / "policy.npz")
        loaded = ResidualPolicyRunner.load(npz_path)

        obs = np.random.default_rng(7).normal(0.0, 1.5, size=(71,)).astype(np.float32)
        act_orig = runner.predict_action(obs)
        act_load = loaded.predict_action(obs)

        assert act_orig.shape == (18,)
        assert np.all(act_orig >= -1.0) and np.all(act_orig <= 1.0)
        assert np.allclose(act_orig, act_load, atol=1e-6)
        assert loaded.metadata.get("test") is True

    def test_vecnormalize_clipping(self):
        runner = _make_dummy_runner()
        extreme_obs = np.full(71, 1e4, dtype=np.float32)
        normed = runner.normalize_obs(extreme_obs)
        assert float(np.max(normed)) == pytest.approx(10.0)
        assert float(np.min(normed)) == pytest.approx(10.0)

    def test_adaptive_gate_damps_flat_and_opens_on_slope(self):
        gate_cfg = AdaptiveGateConfig(
            enabled=True,
            min_gain=0.0,
            tilt_low_rad=math.radians(2.0),
            tilt_high_rad=math.radians(6.0),
            smoothing_alpha=1.0,  # Immediate response for deterministic unit test
        )
        runner = _make_dummy_runner(gate_config=gate_cfg)

        flat_obs = build_proprioceptive_observation(
            proj_gravity=[0.0, 0.0, -1.0],
            ang_vel_base=[0.0, 0.0, 0.0],
            joint_pos_diff_rad=np.zeros(18),
            joint_vel_rad_s=np.zeros(18),
            foot_contacts=[1, 1, 1, 1, 1, 1],
            gait_phase=0.25,
            cmd_vel=[0.05, 0.0, 0.0],
            prev_action=np.zeros(18),
        )
        assert flat_obs.shape == (71,)
        act_flat = runner.predict_action(flat_obs)
        assert np.allclose(act_flat, 0.0), "Flat terrain with 0 tilt must damp residual to 0"

        # 10 deg slope -> full gate = 1.0
        tilt = math.radians(10.0)
        slope_obs = flat_obs.copy()
        slope_obs[0] = math.sin(tilt)
        slope_obs[2] = -math.cos(tilt)
        gate_val = runner.compute_adaptive_gate(slope_obs)
        assert gate_val == pytest.approx(1.0, abs=1e-5)
        act_slope = runner.predict_action(slope_obs)
        assert float(np.linalg.norm(act_slope)) > 0.0

    def test_observation_builder_with_tof_grid(self):
        obs = build_proprioceptive_observation(
            proj_gravity=[0.0, 0.0, -1.0],
            ang_vel_base=[0.0, 0.0, 0.0],
            joint_pos_diff_rad=np.zeros(18),
            joint_vel_rad_s=np.zeros(18),
            foot_contacts=[1, 0, 1, 0, 1, 0],
            gait_phase=0.5,
            cmd_vel=[0.06, 0.0, 0.0],
            prev_action=np.zeros(18),
            belly_tof_grid=np.full(9, 0.09),
        )
        assert obs.shape == (80,)
        assert obs[48] == pytest.approx(math.sin(math.pi), abs=1e-5)
        assert obs[49] == pytest.approx(math.cos(math.pi), abs=1e-5)
