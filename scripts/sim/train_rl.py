#!/usr/bin/env python3
"""
Lasius Hexapod Reinforcement Learning Trainer (`scripts/sim/train_rl.py`).

Purpose & Role:
    Trains continuous locomotion policies for the 18-DOF Lasius Hexapod using
    Proximal Policy Optimization (PPO) via Stable-Baselines3 and PyBullet.
    Supports Residual RL (recommended) and Direct Joint Control.

Usage:
    python3 scripts/sim/train_rl.py                     # Train for 200k steps with Residual RL
    python3 scripts/sim/train_rl.py --timesteps 500000  # Train longer
    python3 scripts/sim/train_rl.py --n-envs 4          # Train with 4 parallel environments
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

# Ensure lasius-core is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "software/lasius-core/src"))

import gymnasium as gym
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv

from lasius.core.sim.gym_env import LasiusGymEnv


def make_env_fn(action_mode: str, seed: int, rank: int):
    def _init():
        env = LasiusGymEnv(action_mode=action_mode)
        env.reset(seed=seed + rank)
        return env
    return _init


def main():
    parser = argparse.ArgumentParser(description="Train Lasius Hexapod Locomotion Policy with PPO")
    parser.add_argument("--timesteps", type=int, default=200_000, help="Total training timesteps (default: 200000)")
    parser.add_argument("--n-envs", type=int, default=4, help="Number of parallel environments (default: 4)")
    parser.add_argument("--action-mode", choices=["residual", "direct"], default="residual", help="RL action mode")
    parser.add_argument("--lr", type=float, default=3e-4, help="Learning rate (default: 3e-4)")
    parser.add_argument("--batch-size", type=int, default=128, help="PPO mini-batch size (default: 128)")
    parser.add_argument("--n-steps", type=int, default=1024, help="Steps per rollout per env (default: 1024)")
    parser.add_argument("--save-dir", type=str, default=str(REPO_ROOT / "data/rl_models"), help="Model checkpoints dir")
    parser.add_argument("--log-dir", type=str, default=str(REPO_ROOT / "data/rl_logs"), help="TensorBoard log dir")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    args = parser.parse_args()

    save_dir = Path(args.save_dir)
    log_dir = Path(args.log_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    print("==========================================================")
    print("🤖 Lasius Hexapod: PPO Locomotion Policy Training")
    print("==========================================================")
    print(f"Action Mode:       {args.action_mode}")
    print(f"Parallel Envs:     {args.n_envs}")
    print(f"Total Timesteps:   {args.timesteps:,}")
    print(f"Rollout Length:    {args.n_steps} steps/env")
    print(f"Batch Size:        {args.batch_size}")
    print(f"Checkpoints Dir:   {save_dir}")
    print(f"TensorBoard Logs:  {log_dir}")
    print("==========================================================\n")

    # Vectorized environments
    env_fns = [make_env_fn(args.action_mode, args.seed, i) for i in range(args.n_envs)]
    vec_env = DummyVecEnv(env_fns) if args.n_envs == 1 else SubprocVecEnv(env_fns)

    # Policy Network Architecture: [256, 128] MLP
    policy_kwargs = dict(
        net_arch=dict(pi=[256, 128], vf=[256, 128])
    )

    # Checkpoint callback: save model every 50,000 steps
    checkpoint_callback = CheckpointCallback(
        save_freq=max(10_000 // args.n_envs, 1),
        save_path=str(save_dir),
        name_prefix=f"lasius_ppo_{args.action_mode}",
        save_replay_buffer=False,
    )

    # Check TensorBoard availability
    try:
        import tensorboard
        tb_log = str(log_dir)
    except ImportError:
        tb_log = None
        print("ℹ️ TensorBoard ist nicht installiert. Logging erfolgt über Standard-Ausgabe.")

    # PPO Agent
    model = PPO(
        "MlpPolicy",
        vec_env,
        learning_rate=args.lr,
        n_steps=args.n_steps,
        batch_size=args.batch_size,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.005,
        vf_coef=0.5,
        max_grad_norm=0.5,
        policy_kwargs=policy_kwargs,
        tensorboard_log=tb_log,
        verbose=1,
        seed=args.seed,
    )

    print("🚀 Starting PPO training...")
    try:
        model.learn(
            total_timesteps=args.timesteps,
            callback=checkpoint_callback,
            progress_bar=True,
        )
    except KeyboardInterrupt:
        print("\n⚠️ Training interrupted by user.")

    # Save final trained model
    final_model_path = save_dir / f"lasius_ppo_{args.action_mode}_final.zip"
    model.save(str(final_model_path))
    print(f"\n✅ Training complete! Final policy saved to: {final_model_path}")
    print(f"To evaluate policy in 3D PyBullet GUI, run:")
    print(f"  python3 scripts/sim/eval_rl.py --model {final_model_path}")

    vec_env.close()


if __name__ == "__main__":
    main()
