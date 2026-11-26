#!/usr/bin/env python3
"""
Lasius Hexapod v2 Sim-to-Real PPO Trainer (`scripts/sim/train_rl.py`).

Purpose & Role:
    Trains Sim-to-Real locomotion policies for the 18-DOF Lasius v2 Hexapod
    (`body_assembly.FCStd` URDF — chassis + 6 legs, no head/gaster) using
    Proximal Policy Optimization (PPO) via Stable-Baselines3 and PyBullet.

    Key Sim-to-Real Features:
    - Realistic Reely NR-645 MG BB servo dynamics (tau=75ms lag, 350 deg/s, ~1.1 Nm)
    - Purely proprioceptive 71-dim observations (IMU + ADS1115 pots + 6 foot switches)
    - Procedural uneven terrain (flat/rough/slopes/steps/mixed) + CurriculumCallback
    - Domain randomization (mass, friction, servo lag/torque, sensor noise) + pushes
    - Monitor wrapper, VecNormalize obs/reward normalization, linear LR decay,
      target_kl safeguard, and fixed-benchmark EvalCallback saving best_model + stats.

Usage:
    python3 scripts/sim/train_rl.py
    python3 scripts/sim/train_rl.py --timesteps 400000 --terrain mixed --curriculum
    python3 scripts/sim/train_rl.py --timesteps 200000 --terrain flat --no-curriculum
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "software/lasius-core/src"))

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import (
    BaseCallback,
    CallbackList,
    CheckpointCallback,
    EvalCallback,
)
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import (
    DummyVecEnv,
    SubprocVecEnv,
    VecNormalize,
    sync_envs_normalization,
)

from lasius.core.sim.gym_env import LasiusGymEnv


def linear_schedule(initial_value: float, final_value: float) -> Callable[[float], float]:
    """Linear learning rate schedule from `initial_value` down to `final_value`."""
    def _func(progress_remaining: float) -> float:
        return final_value + progress_remaining * (initial_value - final_value)
    return _func


def make_env_fn(
    action_mode: str,
    terrain: str,
    difficulty: float,
    realistic_servos: bool,
    domain_randomization: bool,
    enable_pushes: bool,
    use_tof_grid: bool,
    max_episode_steps: int,
    seed: int,
    rank: int,
    fixed_command=None,
):
    def _init():
        env = LasiusGymEnv(
            action_mode=action_mode,
            terrain_type=terrain,
            terrain_difficulty=difficulty,
            realistic_servos=realistic_servos,
            domain_randomization=domain_randomization,
            enable_pushes=enable_pushes,
            use_tof_grid=use_tof_grid,
            max_episode_steps=max_episode_steps,
            fixed_command=fixed_command,
        )
        env = Monitor(env)
        env.reset(seed=seed + rank)
        return env
    return _init


class CurriculumCallback(BaseCallback):
    """
    Gradually increases terrain & push difficulty from `start_difficulty` to `1.0`
    across discrete curriculum stages once rollout stability & reward targets are met
    (with a gentle step-budget progression floor so training never stalls).
    """

    def __init__(
        self,
        total_timesteps: int,
        start_difficulty: float = 0.0,
        max_episode_steps: int = 1000,
        check_freq: int = 8192,
        verbose: int = 1,
    ):
        super().__init__(verbose=verbose)
        self.total_timesteps = max(1, int(total_timesteps))
        self.max_episode_steps = max(1, int(max_episode_steps))
        self.check_freq = max(1, int(check_freq))
        self.stages = [0.0, 0.20, 0.40, 0.60, 0.80, 1.00]
        self.stage_idx = 0
        for i, val in enumerate(self.stages):
            if val >= start_difficulty - 1e-6:
                self.stage_idx = i
                break
        self.current_difficulty = self.stages[self.stage_idx]
        self._last_check_step = 0

    def _on_training_start(self) -> None:
        self.training_env.env_method("set_difficulty", self.current_difficulty)
        self.logger.record("curriculum/difficulty", self.current_difficulty)

    def _on_step(self) -> bool:
        if (self.num_timesteps - self._last_check_step) < self.check_freq:
            return True
        self._last_check_step = self.num_timesteps

        self.logger.record("curriculum/difficulty", self.current_difficulty)

        if self.stage_idx >= len(self.stages) - 1:
            return True

        # Check rollout performance buffer
        ep_buf = list(self.model.ep_info_buffer)
        promote = False
        reason = ""

        if len(ep_buf) >= 6:
            mean_rew = float(np.mean([ep["r"] for ep in ep_buf]))
            mean_len = float(np.mean([ep["l"] for ep in ep_buf]))
            rew_per_step = mean_rew / max(mean_len, 1.0)
            # Promote early if robot reliably survives >85% episode with strong tracking reward
            if mean_len >= 0.85 * self.max_episode_steps and rew_per_step >= 2.15:
                promote = True
                reason = f"mastery (mean_len={mean_len:.0f}, r/step={rew_per_step:.2f})"

        # Time-based progression floor: reach stage k at progress >= k / (N + 0.5)
        progress = self.num_timesteps / float(self.total_timesteps)
        expected_stage = int(progress * (len(self.stages) + 0.5))
        if not promote and expected_stage > self.stage_idx:
            promote = True
            reason = f"schedule ({progress * 100:.0f}% progress)"

        if promote:
            self.stage_idx = min(self.stage_idx + 1, len(self.stages) - 1)
            self.current_difficulty = self.stages[self.stage_idx]
            self.training_env.env_method("set_difficulty", self.current_difficulty)
            self.logger.record("curriculum/difficulty", self.current_difficulty)
            if self.verbose >= 1:
                print(
                    f"\n📈 [Curriculum] Step {self.num_timesteps:,}: "
                    f"difficulty -> {self.current_difficulty:.2f} ({reason})"
                )

        return True


class SyncVecNormEvalCallback(EvalCallback):
    """
    EvalCallback extension that:
    1. Synchronizes VecNormalize observation statistics before every evaluation.
    2. Re-seeds the validation environment identically before every evaluation so
       `best_model.zip` is selected on an exact apples-to-apples fixed suite
       (eliminating Monte-Carlo terrain variance).
    3. Saves `best_vecnormalize.pkl` alongside `best_model.zip`.
    """

    def __init__(self, *args, vecnorm_save_path: Path, eval_seed: int = 2026, **kwargs):
        super().__init__(*args, **kwargs)
        self.vecnorm_save_path = Path(vecnorm_save_path)
        self.eval_seed = int(eval_seed)
        self._prev_best = -np.inf

    def _on_step(self) -> bool:
        if self.eval_freq > 0 and self.n_calls % self.eval_freq == 0:
            sync_envs_normalization(self.training_env, self.eval_env)
            # Deterministic fixed terrain/command sequence for fair best-model selection
            self.eval_env.seed(self.eval_seed)

        continue_training = super()._on_step()

        if self.best_mean_reward > self._prev_best:
            self._prev_best = self.best_mean_reward
            if isinstance(self.training_env, VecNormalize):
                self.vecnorm_save_path.parent.mkdir(parents=True, exist_ok=True)
                self.training_env.save(str(self.vecnorm_save_path))
        return continue_training


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train Lasius v2 Sim-to-Real Hexapod Locomotion Policy with PPO"
    )
    parser.add_argument("--timesteps", type=int, default=400_000, help="Total training timesteps (default: 400000)")
    parser.add_argument("--n-envs", type=int, default=4, help="Parallel environments (default: 4)")
    parser.add_argument("--action-mode", choices=["residual", "direct"], default="residual")
    parser.add_argument(
        "--terrain",
        choices=["flat", "rough", "slopes", "steps", "mixed"],
        default="mixed",
        help="Procedural terrain mode (default: mixed)",
    )
    parser.add_argument("--difficulty", type=float, default=0.0, help="Initial terrain difficulty [0..1] (default: 0.0)")
    parser.add_argument("--no-curriculum", action="store_true", help="Disable automatic difficulty curriculum")
    parser.add_argument("--no-dr", action="store_true", help="Disable Domain Randomization")
    parser.add_argument("--no-pushes", action="store_true", help="Disable lateral push perturbations")
    parser.add_argument("--ideal-servos", action="store_true", help="Disable realistic NR-645 servo lag/torque model")
    parser.add_argument("--use-tof-grid", action="store_true", help="Include 3x3 VL53L5CX belly ToF grid (+9 obs dims)")
    parser.add_argument("--max-episode-steps", type=int, default=600, help="Episode horizon in 50 Hz steps (default: 600 = 12s)")
    parser.add_argument("--lr", type=float, default=1.5e-4, help="Initial PPO learning rate (default: 1.5e-4)")
    parser.add_argument("--ent-coef", type=float, default=0.0, help="PPO entropy coefficient (default: 0.0)")
    parser.add_argument("--log-std-init", type=float, default=-1.8, help="Initial log std for residual exploration (default: -1.8 ≈ 0.165)")
    parser.add_argument("--target-kl", type=float, default=0.025, help="PPO target KL early-stop threshold (default: 0.025)")
    parser.add_argument("--n-epochs", type=int, default=8, help="PPO epochs per rollout update (default: 8)")
    parser.add_argument("--batch-size", type=int, default=256, help="PPO mini-batch size (default: 256)")
    parser.add_argument("--n-steps", type=int, default=2048, help="Steps per rollout per env (default: 2048)")
    parser.add_argument("--eval-freq", type=int, default=40_000, help="Eval frequency in total env steps (default: 40000)")
    parser.add_argument("--eval-episodes", type=int, default=12, help="Number of fixed-seed eval episodes (default: 12)")
    parser.add_argument("--checkpoint-freq", type=int, default=100_000, help="Checkpoint interval in total env steps (default: 100000)")
    parser.add_argument("--save-dir", type=str, default=str(REPO_ROOT / "data/rl_models/v2_sim2real"))
    parser.add_argument("--log-dir", type=str, default=str(REPO_ROOT / "data/rl_logs"))
    parser.add_argument("--run-name", type=str, default="PPO_v2_sim2real")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    save_dir = Path(args.save_dir)
    log_dir = Path(args.log_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    use_curriculum = (not args.no_curriculum) and (args.terrain != "flat")
    use_dr = not args.no_dr
    use_pushes = not args.no_pushes
    realistic_servos = not args.ideal_servos
    eval_difficulty = 0.0 if args.terrain == "flat" else (0.60 if use_curriculum else args.difficulty)

    print("==========================================================")
    print("🤖 Lasius Hexapod v2: Sim-to-Real PPO Training")
    print("==========================================================")
    print(f"URDF Basis:          body_assembly (v2, ohne Kopf/Gaster)")
    print(f"Action Mode:         {args.action_mode}")
    print(f"Terrain:             {args.terrain} (start diff={args.difficulty:.2f}, curriculum={use_curriculum})")
    print(f"Realistic Servos:    {realistic_servos} (NR-645: tau=75ms, 350°/s, 1.1 Nm)")
    print(f"Domain Random.:      {use_dr} | Push Perturbations: {use_pushes}")
    print(f"Observation Mode:    {'80-dim (Proprio + 3x3 ToF)' if args.use_tof_grid else '71-dim (Proprio + 6x Foot Contacts)'}")
    print(f"Parallel Envs:       {args.n_envs} | Timesteps: {args.timesteps:,}")
    print(f"Eval Benchmark:      {args.terrain} @ diff={eval_difficulty:.2f} every {args.eval_freq:,} steps")
    print(f"Save Dir:            {save_dir}")
    print("==========================================================\n")

    # Save training metadata so eval_rl.py reproduces the exact environment configuration
    meta = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "urdf_basis": "body_assembly_v2_no_head_gaster",
        "action_mode": args.action_mode,
        "terrain": args.terrain,
        "initial_difficulty": args.difficulty,
        "curriculum": use_curriculum,
        "realistic_servos": realistic_servos,
        "domain_randomization": use_dr,
        "enable_pushes": use_pushes,
        "use_tof_grid": args.use_tof_grid,
        "max_episode_steps": args.max_episode_steps,
        "timesteps": args.timesteps,
        "n_envs": args.n_envs,
        "seed": args.seed,
    }
    (save_dir / "training_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # 1. Vectorized training environments wrapped in VecNormalize
    train_fns = [
        make_env_fn(
            action_mode=args.action_mode,
            terrain=args.terrain,
            difficulty=args.difficulty,
            realistic_servos=realistic_servos,
            domain_randomization=use_dr,
            enable_pushes=use_pushes,
            use_tof_grid=args.use_tof_grid,
            max_episode_steps=args.max_episode_steps,
            seed=args.seed,
            rank=i,
        )
        for i in range(args.n_envs)
    ]
    raw_train_env = DummyVecEnv(train_fns) if args.n_envs == 1 else SubprocVecEnv(train_fns)
    vec_env = VecNormalize(
        raw_train_env,
        norm_obs=True,
        norm_reward=True,
        clip_obs=10.0,
        clip_reward=10.0,
        gamma=0.99,
    )

    # 2. Fixed-difficulty validation environment for apples-to-apples best_model selection
    eval_fn = [
        make_env_fn(
            action_mode=args.action_mode,
            terrain=args.terrain,
            difficulty=eval_difficulty,
            realistic_servos=realistic_servos,
            domain_randomization=False,
            enable_pushes=False,
            use_tof_grid=args.use_tof_grid,
            max_episode_steps=args.max_episode_steps,
            seed=args.seed + 1000,
            rank=0,
        )
    ]
    eval_env = VecNormalize(
        DummyVecEnv(eval_fn),
        training=False,
        norm_obs=True,
        norm_reward=False,
        clip_obs=10.0,
    )

    # Policy Network: [256, 128] MLP with tight residual exploration std
    policy_kwargs = dict(
        net_arch=dict(pi=[256, 128], vf=[256, 128]),
        log_std_init=args.log_std_init if args.action_mode == "residual" else -0.3,
    )

    # Callbacks
    callbacks = [
        CheckpointCallback(
            save_freq=max(args.checkpoint_freq // args.n_envs, 1),
            save_path=str(save_dir / "checkpoints"),
            name_prefix=f"lasius_v2_ppo_{args.action_mode}",
            save_vecnormalize=True,
            save_replay_buffer=False,
        ),
        SyncVecNormEvalCallback(
            eval_env,
            best_model_save_path=str(save_dir),
            log_path=str(save_dir / "eval_logs"),
            eval_freq=max(args.eval_freq // args.n_envs, 1),
            n_eval_episodes=args.eval_episodes,
            deterministic=True,
            render=False,
            vecnorm_save_path=save_dir / "best_vecnormalize.pkl",
            eval_seed=args.seed + 2026,
        ),
    ]
    if use_curriculum:
        callbacks.append(
            CurriculumCallback(
                total_timesteps=args.timesteps,
                start_difficulty=args.difficulty,
                max_episode_steps=args.max_episode_steps,
                check_freq=max(16_384, args.n_steps * args.n_envs),
                verbose=1,
            )
        )

    # Check TensorBoard availability
    try:
        import tensorboard  # noqa: F401
        tb_log = str(log_dir)
    except ImportError:
        tb_log = None
        print("ℹ️ TensorBoard ist nicht installiert. Logging erfolgt über Standard-Ausgabe.")

    model = PPO(
        "MlpPolicy",
        vec_env,
        learning_rate=linear_schedule(args.lr, args.lr * 0.15),
        n_steps=args.n_steps,
        batch_size=args.batch_size,
        n_epochs=args.n_epochs,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=args.ent_coef,
        vf_coef=0.5,
        max_grad_norm=0.5,
        target_kl=args.target_kl,
        policy_kwargs=policy_kwargs,
        tensorboard_log=tb_log,
        verbose=1,
        seed=args.seed,
    )

    # Zero-initialize residual actor output head so step-0 deterministic policy == exact OmniGait baseline
    if args.action_mode == "residual":
        import torch
        with torch.no_grad():
            model.policy.action_net.weight.zero_()
            model.policy.action_net.bias.zero_()

    print("🚀 Starting Lasius v2 Sim-to-Real PPO training...")
    try:
        model.learn(
            total_timesteps=args.timesteps,
            callback=CallbackList(callbacks),
            tb_log_name=args.run_name,
            progress_bar=False,
        )
    except KeyboardInterrupt:
        print("\n⚠️ Training interrupted by user.")

    # Save final trained model + VecNormalize statistics
    final_model_path = save_dir / f"lasius_v2_ppo_{args.action_mode}_final.zip"
    final_vecnorm_path = save_dir / f"lasius_v2_ppo_{args.action_mode}_final_vecnormalize.pkl"
    model.save(str(final_model_path))
    vec_env.save(str(final_vecnorm_path))

    print(f"\n✅ Training complete!")
    print(f"   Final policy:    {final_model_path}")
    print(f"   Best policy:     {save_dir / 'best_model.zip'}")
    print(f"   VecNormalize:    {final_vecnorm_path}")
    print("\nTo run A/B benchmark (Baseline vs. PPO v2):")
    print(f"  python3 scripts/sim/eval_rl.py --model {save_dir / 'best_model.zip'} --compare --headless")

    eval_env.close()
    vec_env.close()


if __name__ == "__main__":
    main()
