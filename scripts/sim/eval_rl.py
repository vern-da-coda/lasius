#!/usr/bin/env python3
"""
Lasius Hexapod RL Policy Evaluator & 3D Visualizer (`scripts/sim/eval_rl.py`).

Purpose & Role:
    Loads a trained PPO locomotion policy and executes it in PyBullet 3D GUI
    with real-time telemetry, reward tracking, and interactive keyboard controls.

Usage:
    python3 scripts/sim/eval_rl.py --model data/rl_models/lasius_ppo_residual_final.zip
    python3 scripts/sim/eval_rl.py --baseline   # Run analytical OmniGait baseline (zero residual)
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "software/lasius-core/src"))

import numpy as np
import pybullet as p
from stable_baselines3 import PPO

from lasius.core.sim.gym_env import LasiusGymEnv


def main():
    parser = argparse.ArgumentParser(description="Evaluate Trained Lasius RL Locomotion Policy")
    parser.add_argument("--model", type=str, default=None, help="Path to trained PPO model .zip file")
    parser.add_argument("--baseline", action="store_true", help="Run analytical baseline without RL model (zero action)")
    parser.add_argument("--action-mode", choices=["residual", "direct"], default="residual", help="RL action mode")
    parser.add_argument("--vx", type=float, default=0.10, help="Forward velocity command (m/s, default: 0.10)")
    parser.add_argument("--vy", type=float, default=0.0, help="Lateral velocity command (m/s, default: 0.0)")
    parser.add_argument("--wz", type=float, default=0.0, help="Yaw angular velocity command (rad/s, default: 0.0)")
    parser.add_argument("--episodes", type=int, default=5, help="Number of episodes to run (default: 5)")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode without 3D GUI window")
    args = parser.parse_args()

    model = None
    if not args.baseline:
        if args.model is None:
            # Look for default latest model
            default_path = REPO_ROOT / f"data/rl_models/lasius_ppo_{args.action_mode}_final.zip"
            if default_path.is_file():
                args.model = str(default_path)
            else:
                print(f"ℹ️ Kein trainiertes Modell gefunden unter {default_path}.")
                print("Starte im Baseline-Modus (analytischer OmniGait ohne neuronales Netzwerk)...")
                args.baseline = True

        if not args.baseline and args.model:
            print(f"📦 Lade trainiertes PPO-Modell: {args.model}")
            model = PPO.load(args.model)

    print("==========================================================")
    print("🤖 Lasius Hexapod: 3D RL Policy Evaluation")
    print("==========================================================")
    print(f"Modus:          {'Baseline (Zero-Residual)' if args.baseline else 'Trained PPO Policy'}")
    print(f"Action Mode:    {args.action_mode}")
    print(f"Soll-Kommando:  vx={args.vx:+.2f} m/s, vy={args.vy:+.2f} m/s, wz={args.wz:+.2f} rad/s")
    print("==========================================================\n")

    env = LasiusGymEnv(
        render_mode=None if args.headless else "human",
        action_mode=args.action_mode,
        fixed_command=(args.vx, args.vy, args.wz),
    )

    try:
        for ep in range(1, args.episodes + 1):
            obs, info = env.reset()
            ep_reward = 0.0
            step = 0
            print(f"\n▶ Episode {ep}/{args.episodes} gestartet...")

            while True:
                # Decide action: Model prediction or zero baseline
                if model is not None:
                    action, _ = model.predict(obs, deterministic=True)
                else:
                    action = np.zeros(18, dtype=np.float32)

                obs, reward, terminated, truncated, step_info = env.step(action)
                ep_reward += reward
                step += 1

                # Live status output every 25 steps (~0.5s)
                if step % 25 == 0:
                    pos, orn = p.getBasePositionAndOrientation(env.robot_id, physicsClientId=env.client_id)
                    lin_vel, ang_vel = p.getBaseVelocity(env.robot_id, physicsClientId=env.client_id)
                    print(
                        f"  [Step {step:04d}] Reward: {ep_reward:7.2f} | "
                        f"Pos Z: {pos[2]:.3f} m | Vel X: {lin_vel[0]:+.3f} m/s (Soll: {args.vx:+.2f})"
                    )

                if not args.headless:
                    time.sleep(1.0 / env.control_freq)

                if terminated:
                    print(f"⚠️ Episode {ep} beendet: Roboter instabil oder umgekippt (Step {step}, Reward: {ep_reward:.2f})")
                    break
                if truncated:
                    print(f"✔ Episode {ep} regulär abgeschlossen: {step} Steps erreicht, Gesamtreward: {ep_reward:.2f}")
                    break
    except KeyboardInterrupt:
        print("\n⏹ Evaluierung durch Benutzer abgebrochen.")
    finally:
        env.close()
        print("✔ PyBullet-Sitzung beendet.")


if __name__ == "__main__":
    main()
