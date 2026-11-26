"""
Unit tests for Lasius v2 Sim-to-Real Gymnasium Environment, Servo Actuator Model,
and Procedural Terrain Generator (`lasius.core.sim`).
"""

import math
import pytest

try:
    import numpy as np
    import gymnasium as gym
    import pybullet
    from lasius.core.sim import (
        ActuatorConfig,
        LasiusGymEnv,
        ServoActuatorModel,
        TerrainType,
        build_joint_limits_rad,
    )
    from lasius.core.sim.gym_env import JOINT_NAMES

    RL_AVAILABLE = True
except ImportError:
    RL_AVAILABLE = False
    np = None


@pytest.mark.skipif(not RL_AVAILABLE, reason="Gymnasium or PyBullet not installed")
class TestServoActuatorModel:
    def test_soft_limits_match_config_yaml(self):
        lows, highs = build_joint_limits_rad(JOINT_NAMES)
        assert lows.shape == (18,)
        assert highs.shape == (18,)
        assert np.all(lows < highs)
        # Left front coxa allows +35 deg forward (URDF -35 deg)
        assert math.isclose(math.degrees(lows[0]), -35.0, abs_tol=1e-3)
        assert math.isclose(math.degrees(highs[0]), 25.0, abs_tol=1e-3)
        # Tibia URDF limits [+22 deg, +119 deg] (config.yaml [-68, +29] + 90)
        assert math.isclose(math.degrees(lows[2]), 22.0, abs_tol=1e-3)
        assert math.isclose(math.degrees(highs[2]), 119.0, abs_tol=1e-3)

    def test_first_order_lag_and_slew_limit(self):
        model = ServoActuatorModel(JOINT_NAMES, realistic_dynamics=True)
        init = np.zeros(18, dtype=np.float32)
        init[2::3] = math.radians(84.0)
        model.reset(init)

        # Command large step on femur joint (index 1)
        target = init.copy()
        target[1] = math.radians(40.0)

        dt = 0.004  # 250 Hz substep
        q1 = model.step_substep(target, dt)
        # Must move smoothly toward target without jumping immediately
        assert 0.0 < q1[1] < target[1]
        assert (q1[1] - init[1]) <= model.config.max_speed_rad_s * dt + 1e-6

        # After 0.5 s (~6.7 * tau), should closely approach target
        for _ in range(125):
            q1 = model.step_substep(target, dt)
        assert abs(q1[1] - target[1]) < math.radians(2.0)

    def test_potentiometer_quantization_and_domain_randomization(self):
        rng = np.random.default_rng(123)
        model = ServoActuatorModel(JOINT_NAMES, realistic_dynamics=True)
        init = np.zeros(18, dtype=np.float32)
        init[2::3] = math.radians(84.0)
        model.reset(init, rng=rng, randomize=True)

        # Randomized parameters must remain within physical NR-645 bounds
        assert np.all((model.max_torque_nm >= 0.80) & (model.max_torque_nm <= 1.40))
        assert np.all((model.tau_lag_s >= 0.040) & (model.tau_lag_s <= 0.120))

        q_meas, q_dot = model.measure_joints(init, dt_control=0.02, rng=rng, add_noise=True)
        assert q_meas.shape == (18,)
        assert q_dot.shape == (18,)
        assert np.all(np.isfinite(q_meas))
        assert np.all(np.isfinite(q_dot))


@pytest.mark.skipif(not RL_AVAILABLE, reason="Gymnasium or PyBullet not installed")
class TestLasiusGymEnv:
    def test_env_initialization_proprioceptive(self):
        env = LasiusGymEnv(action_mode="residual", terrain_type="flat")
        try:
            # 3 gravity + 3 ang_vel + 18 q_diff + 18 q_dot + 6 contacts + 2 phase + 3 cmd + 18 prev_a = 71
            assert env.observation_space.shape == (71,)
            assert env.action_space.shape == (18,)
            assert np.all(env.action_space.low == -1.0)
            assert np.all(env.action_space.high == 1.0)
            assert len(env.joint_indices) == 18
            assert len(env.foot_link_indices) == 6
        finally:
            env.close()

    def test_env_initialization_with_tof_grid(self):
        env = LasiusGymEnv(action_mode="residual", use_tof_grid=True)
        try:
            assert env.observation_space.shape == (80,)
            obs, _ = env.reset(seed=7)
            assert obs.shape == (80,)
            assert np.all(np.isfinite(obs))
        finally:
            env.close()

    def test_reset_and_foot_contacts(self):
        env = LasiusGymEnv(action_mode="residual", terrain_type="flat")
        try:
            obs, info = env.reset(seed=42)
            assert isinstance(obs, np.ndarray)
            assert obs.shape == (71,)
            assert obs.dtype == np.float32
            assert np.all(np.isfinite(obs))
            assert "command" in info
            assert info["command"].shape == (3,)
            # Standing on flat ground should register >= 4 settled foot contacts
            foot_contacts = obs[42:48]
            assert np.sum(foot_contacts) >= 4.0
        finally:
            env.close()

    def test_step_residual_and_direct_modes(self):
        for mode in ("residual", "direct"):
            env = LasiusGymEnv(
                action_mode=mode,
                fixed_command=(0.06, 0.0, 0.0),
                terrain_type="flat",
            )
            try:
                obs, _ = env.reset(seed=42)
                action = np.zeros(18, dtype=np.float32)
                next_obs, reward, terminated, truncated, step_info = env.step(action)
                assert next_obs.shape == (71,)
                assert np.all(np.isfinite(next_obs))
                assert isinstance(reward, float)
                assert isinstance(terminated, bool)
                assert isinstance(truncated, bool)
                assert step_info["step"] == 1
                assert "reward_lin" in step_info
                assert "z_rel" in step_info
                assert "foot_contact_count" in step_info
            finally:
                env.close()

    @pytest.mark.parametrize("terrain_mode", ["rough", "slopes", "steps", "mixed"])
    def test_uneven_terrain_and_curriculum(self, terrain_mode):
        env = LasiusGymEnv(
            action_mode="residual",
            terrain_type=terrain_mode,
            terrain_difficulty=0.5,
            domain_randomization=True,
            enable_pushes=True,
            fixed_command=(0.06, 0.0, 0.0),
        )
        try:
            obs, info = env.reset(seed=101)
            assert obs.shape == (71,)
            assert np.all(np.isfinite(obs))
            # Verify curriculum difficulty update works across resets
            assert env.set_difficulty(0.8) == pytest.approx(0.8)
            obs, info = env.reset(seed=102)
            assert info["difficulty"] == pytest.approx(0.8)
            for _ in range(15):
                obs, reward, terminated, truncated, sinfo = env.step(
                    np.zeros(18, dtype=np.float32)
                )
                assert np.all(np.isfinite(obs))
                assert np.isfinite(reward)
                if terminated or truncated:
                    break
        finally:
            env.close()

    def test_velocity_sign_conventions_baseline(self):
        """Verifies that +cmd_vx moves +X, +cmd_vy moves +Y (left), and +cmd_wz turns +Z (CCW)."""
        checks = [
            ((0.06, 0.0, 0.0), "vx_base", 0.015),
            ((0.0, 0.05, 0.0), "vy_base", 0.010),
            ((0.0, 0.0, 0.20), "wz_base", 0.040),
        ]
        for cmd, metric_key, min_expected in checks:
            env = LasiusGymEnv(
                action_mode="residual",
                terrain_type="flat",
                fixed_command=cmd,
                realistic_servos=True,
                domain_randomization=False,
            )
            try:
                env.reset(seed=11)
                vals = []
                for step in range(100):  # 2.0 seconds
                    _, _, terminated, _, sinfo = env.step(np.zeros(18, dtype=np.float32))
                    assert not terminated
                    if step >= 25:
                        vals.append(sinfo[metric_key])
                assert float(np.mean(vals)) > min_expected, (
                    f"Command {cmd} produced mean {metric_key}={np.mean(vals):.4f} "
                    f"(expected > {min_expected})"
                )
            finally:
                env.close()

    @pytest.mark.parametrize("terrain_mode", ["rough", "slopes", "steps"])
    def test_heightfield_raycast_matches_get_height(self, terrain_mode):
        """Verifies PyBullet heightfield collision Z matches `TerrainGenerator.get_height` (< 2 mm)."""
        from lasius.core.sim.terrain import TerrainGenerator

        cid = pybullet.connect(pybullet.DIRECT)
        try:
            tg = TerrainGenerator(cid, terrain_type=terrain_mode)
            rng = np.random.default_rng(77)
            tg.reset(difficulty=1.0, rng=rng)
            for x in (-0.6, -0.2, 0.0, 0.2, 0.6):
                for y in (-0.6, 0.0, 0.6):
                    ray = pybullet.rayTest([x, y, 2.0], [x, y, -2.0], physicsClientId=cid)[0]
                    assert ray[0] == tg.body_id
                    hit_z = ray[3][2]
                    pred_z = tg.get_height(x, y)
                    assert abs(hit_z - pred_z) < 0.002, (
                        f"{terrain_mode} at ({x},{y}): ray_z={hit_z:.4f} vs get_height={pred_z:.4f}"
                    )
        finally:
            pybullet.disconnect(cid)
