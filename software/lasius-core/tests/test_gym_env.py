"""
Unit tests for Lasius Hexapod Gymnasium Environment (`lasius.core.sim.gym_env`).
"""

import numpy as np
import pytest

try:
    import gymnasium as gym
    import pybullet
    from lasius.core.sim.gym_env import LasiusGymEnv
    RL_AVAILABLE = True
except ImportError:
    RL_AVAILABLE = False


@pytest.mark.skipif(not RL_AVAILABLE, reason="Gymnasium or PyBullet not installed")
class TestLasiusGymEnv:
    def test_env_initialization(self):
        env = LasiusGymEnv(action_mode="residual")
        try:
            assert env.observation_space.shape == (66,)
            assert env.action_space.shape == (18,)
            assert np.all(env.action_space.low == -1.0)
            assert np.all(env.action_space.high == 1.0)
            assert len(env.joint_indices) == 18
        finally:
            env.close()

    def test_reset(self):
        env = LasiusGymEnv(action_mode="residual")
        try:
            obs, info = env.reset(seed=42)
            assert isinstance(obs, np.ndarray)
            assert obs.shape == (66,)
            assert obs.dtype == np.float32
            assert np.all(np.isfinite(obs))
            assert "command" in info
            assert info["command"].shape == (3,)
        finally:
            env.close()

    def test_step_residual_mode(self):
        env = LasiusGymEnv(action_mode="residual", fixed_command=(0.10, 0.0, 0.0))
        try:
            obs, info = env.reset(seed=42)
            action = np.zeros(18, dtype=np.float32)
            next_obs, reward, terminated, truncated, step_info = env.step(action)

            assert next_obs.shape == (66,)
            assert isinstance(reward, float)
            assert isinstance(terminated, bool)
            assert isinstance(truncated, bool)
            assert step_info["step"] == 1
            assert "reward_total" in step_info
            assert "reward_lin" in step_info
        finally:
            env.close()

    def test_step_direct_mode(self):
        env = LasiusGymEnv(action_mode="direct")
        try:
            obs, info = env.reset(seed=123)
            random_action = np.random.uniform(-0.5, 0.5, size=18).astype(np.float32)
            next_obs, reward, terminated, truncated, step_info = env.step(random_action)

            assert next_obs.shape == (66,)
            assert isinstance(reward, float)
            assert step_info["step"] == 1
        finally:
            env.close()

    def test_multiple_steps_locomotion(self):
        env = LasiusGymEnv(action_mode="residual", fixed_command=(0.10, 0.0, 0.0))
        try:
            env.reset(seed=99)
            # Step 15 control steps (~0.3 seconds of simulated walking)
            for _ in range(15):
                action = np.zeros(18, dtype=np.float32)
                obs, reward, terminated, truncated, _ = env.step(action)
                assert np.all(np.isfinite(obs))
                if terminated or truncated:
                    break
        finally:
            env.close()
