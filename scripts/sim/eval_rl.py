#!/usr/bin/env python3
"""
Lasius Hexapod v2 RL Policy Evaluator & A/B Benchmark (`scripts/sim/eval_rl.py`).

Purpose & Role:
    Loads a trained PPO locomotion policy (plus matching `VecNormalize` stats
    and `training_meta.json` if available) and executes it in PyBullet 3D GUI
    or headless benchmark mode. Supports direct A/B comparison against the
    analytical OmniGait baseline (zero residual) across flat, rough, sloped,
    and stepped terrains.

Usage:
    python3 scripts/sim/eval_rl.py --model data/rl_models/v2_sim2real/best_model.zip
    python3 scripts/sim/eval_rl.py --model data/rl_models/v2_sim2real/best_model.zip --compare --headless
    python3 scripts/sim/eval_rl.py --baseline --terrain rough --difficulty 0.6
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "software/lasius-core/src"))

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from lasius.core.sim.gym_env import LasiusGymEnv
from lasius.core.sim.policy import AdaptiveGateConfig, ResidualPolicyRunner


def find_vecnormalize_path(model_path: Path) -> Optional[Path]:
    """Finds the matching VecNormalize pickle next to a saved PPO model."""
    candidates = [
        model_path.parent / "best_vecnormalize.pkl" if model_path.name == "best_model.zip" else None,
        model_path.with_name(model_path.stem + "_vecnormalize.pkl"),
        model_path.parent / "vecnormalize.pkl",
        model_path.parent / "lasius_v2_ppo_residual_final_vecnormalize.pkl",
    ]
    for cand in candidates:
        if cand is not None and cand.is_file():
            return cand
    return None


def load_training_meta(model_path: Path) -> Dict[str, Any]:
    """Loads `training_meta.json` from the model directory if present."""
    for p_meta in [model_path.parent / "training_meta.json", model_path.parent.parent / "training_meta.json"]:
        if p_meta.is_file():
            try:
                return json.loads(p_meta.read_text(encoding="utf-8"))
            except Exception:
                pass
    return {}


def run_episode(
    model: Optional[Any],
    vecnorm_path: Optional[Path],
    action_mode: str,
    terrain: str,
    difficulty: float,
    command: Tuple[float, float, float],
    max_steps: int,
    seed: int,
    realistic_servos: bool,
    domain_randomization: bool,
    enable_pushes: bool,
    use_tof_grid: bool,
    headless: bool,
    verbose: bool = True,
) -> Dict[str, Any]:
    """Executes one evaluation episode and returns structured telemetry metrics."""
    is_numpy_runner = isinstance(model, ResidualPolicyRunner)

    def _make():
        return LasiusGymEnv(
            render_mode=None if headless else "human",
            action_mode=action_mode,
            fixed_command=command,
            max_episode_steps=max_steps,
            terrain_type=terrain,
            terrain_difficulty=difficulty,
            realistic_servos=realistic_servos,
            domain_randomization=domain_randomization,
            enable_pushes=enable_pushes,
            use_tof_grid=use_tof_grid,
        )

    venv = DummyVecEnv([_make])
    if model is not None and not is_numpy_runner and vecnorm_path is not None:
        venv = VecNormalize.load(str(vecnorm_path), venv)
        venv.training = False
        venv.norm_reward = False

    # Seed underlying env cleanly
    venv.envs[0].reset(seed=seed)
    obs = venv.reset()
    # Re-apply deterministic reset with requested seed so Baseline and PPO see identical terrain
    raw_obs, _ = venv.envs[0].reset(seed=seed)
    if is_numpy_runner:
        model.reset()
        obs = raw_obs[None, :]
    elif isinstance(venv, VecNormalize):
        obs = venv.normalize_obs(raw_obs[None, :])
    else:
        obs = raw_obs[None, :]

    ep_reward = 0.0
    vx_vals: List[float] = []
    vy_vals: List[float] = []
    wz_vals: List[float] = []
    z_rel_vals: List[float] = []
    tilt_vals: List[float] = []
    contact_vals: List[int] = []
    action_rms_vals: List[float] = []
    terminated = False
    step = 0

    try:
        for step in range(1, max_steps + 1):
            if is_numpy_runner:
                act = model.predict_action(obs[0], normalize=True)
                action = act[None, :]
            elif model is not None:
                action, _ = model.predict(obs, deterministic=True)
            else:
                action = np.zeros((1, 18), dtype=np.float32)

            obs, rewards, dones, infos = venv.step(action)
            info = infos[0]
            r = float(info.get("reward_total", rewards[0]))
            ep_reward += r

            vx_vals.append(float(info.get("vx_base", 0.0)))
            vy_vals.append(float(info.get("vy_base", 0.0)))
            wz_vals.append(float(info.get("wz_base", 0.0)))
            z_rel_vals.append(float(info.get("z_rel", 0.0)))
            tilt_vals.append(float(info.get("max_tilt_deg", 0.0)))
            contact_vals.append(int(info.get("foot_contact_count", 0)))
            action_rms_vals.append(float(np.sqrt(np.mean(action ** 2))))

            if verbose and step % 50 == 0:
                print(
                    f"  [Step {step:04d}] R={ep_reward:7.2f} | "
                    f"z_rel={z_rel_vals[-1]:.3f}m | tilt={tilt_vals[-1]:4.1f}° | "
                    f"vx={vx_vals[-1]:+.3f} (soll {command[0]:+.2f}) | "
                    f"contacts={contact_vals[-1]}/6"
                )

            if not headless:
                time.sleep(1.0 / venv.envs[0].control_freq)

            if bool(dones[0]):
                terminated = bool(
                    info.get("term_chassis_drop", False)
                    or info.get("term_excessive_tilt", False)
                )
                break
    finally:
        venv.close()

    # Compute steady-state tracking error (skip first 25 steps / 0.5s settling)
    s0 = min(25, max(0, len(vx_vals) - 1))
    mean_vx = float(np.mean(vx_vals[s0:])) if vx_vals else 0.0
    mean_vy = float(np.mean(vy_vals[s0:])) if vy_vals else 0.0
    mean_wz = float(np.mean(wz_vals[s0:])) if wz_vals else 0.0
    vel_err = float(np.hypot(mean_vx - command[0], mean_vy - command[1]))

    return {
        "steps": step,
        "survived": not terminated,
        "total_reward": ep_reward,
        "reward_per_step": ep_reward / max(step, 1),
        "mean_vx": mean_vx,
        "mean_vy": mean_vy,
        "mean_wz": mean_wz,
        "vel_err": vel_err,
        "mean_z_rel": float(np.mean(z_rel_vals)) if z_rel_vals else 0.0,
        "mean_tilt_deg": float(np.mean(tilt_vals)) if tilt_vals else 0.0,
        "max_tilt_deg": float(np.max(tilt_vals)) if tilt_vals else 0.0,
        "mean_contacts": float(np.mean(contact_vals)) if contact_vals else 0.0,
        "action_rms": float(np.mean(action_rms_vals)) if action_rms_vals else 0.0,
    }


def run_ab_benchmark(
    model: PPO,
    vecnorm_path: Optional[Path],
    action_mode: str,
    realistic_servos: bool,
    use_tof_grid: bool,
    max_steps: int,
    seed: int,
) -> None:
    """Runs a reproducible A/B benchmark suite comparing Baseline OmniGait vs. PPO v2."""
    scenarios = [
        ("Flat Forward",       "flat",   0.00, (0.06, 0.00, 0.00), False),
        ("Flat Strafe+Yaw",    "flat",   0.00, (0.04, 0.03, 0.15), False),
        ("Rough d=0.50",       "rough",  0.50, (0.06, 0.00, 0.00), False),
        ("Rough d=1.00",       "rough",  1.00, (0.06, 0.00, 0.00), False),
        ("Slopes d=0.80",      "slopes", 0.80, (0.06, 0.00, 0.00), False),
        ("Steps d=0.70",       "steps",  0.70, (0.06, 0.00, 0.00), False),
        ("Rough+Pushes d=0.8", "rough",  0.80, (0.06, 0.00, 0.00), True),
    ]

    print("\n=========================================================================================================")
    print("🧪 Lasius v2 A/B Benchmark: Analytical OmniGait Baseline vs. Trained PPO Policy")
    print("=========================================================================================================")
    header = (
        f"{'Scenario':20s} | {'Mode':8s} | {'Steps':>5s} | {'Reward':>8s} | "
        f"{'R/Step':>6s} | {'vx (m/s)':>8s} | {'VelErr':>6s} | {'z_rel':>6s} | {'Mean/Max Tilt':>13s}"
    )
    print(header)
    print("-" * len(header))

    base_rewards, ppo_rewards = [], []
    base_surv, ppo_surv = 0, 0

    for idx, (label, terrain, diff, cmd, pushes) in enumerate(scenarios):
        sc_seed = seed + idx * 17
        res_base = run_episode(
            model=None,
            vecnorm_path=None,
            action_mode=action_mode,
            terrain=terrain,
            difficulty=diff,
            command=cmd,
            max_steps=max_steps,
            seed=sc_seed,
            realistic_servos=realistic_servos,
            domain_randomization=False,
            enable_pushes=pushes,
            use_tof_grid=use_tof_grid,
            headless=True,
            verbose=False,
        )
        res_ppo = run_episode(
            model=model,
            vecnorm_path=vecnorm_path,
            action_mode=action_mode,
            terrain=terrain,
            difficulty=diff,
            command=cmd,
            max_steps=max_steps,
            seed=sc_seed,
            realistic_servos=realistic_servos,
            domain_randomization=False,
            enable_pushes=pushes,
            use_tof_grid=use_tof_grid,
            headless=True,
            verbose=False,
        )

        base_rewards.append(res_base["total_reward"])
        ppo_rewards.append(res_ppo["total_reward"])
        base_surv += int(res_base["survived"])
        ppo_surv += int(res_ppo["survived"])

        for tag, r in [("Baseline", res_base), ("PPO v2", res_ppo)]:
            print(
                f"{label if tag == 'Baseline' else '':20s} | {tag:8s} | "
                f"{r['steps']:5d} | {r['total_reward']:8.1f} | {r['reward_per_step']:6.3f} | "
                f"{r['mean_vx']:+8.4f} | {r['vel_err']:6.4f} | {r['mean_z_rel']:6.3f} | "
                f"{r['mean_tilt_deg']:5.1f}° / {r['max_tilt_deg']:4.1f}°"
            )
        delta = res_ppo["total_reward"] - res_base["total_reward"]
        pct = 100.0 * delta / max(abs(res_base["total_reward"]), 1e-6)
        print(f"{'':20s} | {'Δ PPO':8s} | {'':>5s} | {delta:+8.1f} ({pct:+5.1f}%) | action_rms={res_ppo['action_rms']:.3f}")
        print("-" * len(header))

    print(
        f"SUMMARY ({len(scenarios)} scenarios): "
        f"Baseline mean={np.mean(base_rewards):.1f} ({base_surv}/{len(scenarios)} survived) | "
        f"PPO v2 mean={np.mean(ppo_rewards):.1f} ({ppo_surv}/{len(scenarios)} survived) | "
        f"Delta={np.mean(ppo_rewards) - np.mean(base_rewards):+.1f}"
    )
    print("=========================================================================================================\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Trained Lasius v2 RL Locomotion Policy")
    parser.add_argument("--model", type=str, default=None, help="Path to trained PPO model .zip file")
    parser.add_argument("--baseline", action="store_true", help="Run analytical baseline (zero residual)")
    parser.add_argument("--compare", action="store_true", help="Run full A/B benchmark (Baseline vs. PPO across terrains)")
    parser.add_argument("--action-mode", choices=["residual", "direct"], default=None)
    parser.add_argument("--terrain", choices=["flat", "rough", "slopes", "steps", "mixed"], default="rough")
    parser.add_argument("--difficulty", type=float, default=0.6, help="Terrain difficulty [0..1] (default: 0.6)")
    parser.add_argument("--vx", type=float, default=0.06, help="Forward velocity command (m/s, default: 0.06)")
    parser.add_argument("--vy", type=float, default=0.0, help="Lateral velocity command (m/s, default: 0.0)")
    parser.add_argument("--wz", type=float, default=0.0, help="Yaw angular velocity command (rad/s, default: 0.0)")
    parser.add_argument("--episodes", type=int, default=3, help="Number of episodes (default: 3)")
    parser.add_argument("--max-steps", type=int, default=400, help="Steps per episode (default: 400 = 8s)")
    parser.add_argument("--dr", action="store_true", help="Enable Domain Randomization during evaluation")
    parser.add_argument("--pushes", action="store_true", help="Enable lateral push perturbations during evaluation")
    parser.add_argument("--ideal-servos", action="store_true", help="Disable realistic NR-645 servo lag/torque model")
    parser.add_argument("--use-tof-grid", action="store_true", help="Include 3x3 belly ToF grid (+9 obs dims)")
    parser.add_argument("--adaptive-gate", action="store_true", help="Enable IMU tilt/rate adaptive residual gate (damps flat-ground jitter)")
    parser.add_argument("--headless", action="store_true", help="Run without PyBullet 3D GUI")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    model: Optional[Any] = None
    vecnorm_path: Optional[Path] = None
    meta: Dict[str, Any] = {}

    if not args.baseline:
        if args.model is None:
            for candidate in [
                REPO_ROOT / "data/rl_models/v2_overnight/lasius_v2_ppo_residual_final.zip",
                REPO_ROOT / "data/rl_models/v2_overnight/best_model.zip",
                REPO_ROOT / "data/rl_models/v2_sim2real/best_model.zip",
                REPO_ROOT / "data/rl_models/v2_sim2real/lasius_v2_ppo_residual_final.zip",
            ]:
                if candidate.is_file():
                    args.model = str(candidate)
                    break

        if args.model is None or not Path(args.model).is_file():
            print("ℹ️ Kein trainiertes v2-Modell gefunden. Starte im Baseline-Modus...")
            args.baseline = True
        else:
            model_path = Path(args.model)
            meta = load_training_meta(model_path)
            vecnorm_path = find_vecnormalize_path(model_path)
            print(f"📦 Lade PPO-Modell: {model_path}")
            if vecnorm_path:
                print(f"📊 Lade VecNormalize: {vecnorm_path}")
            if model_path.suffix.lower() == ".npz" or args.adaptive_gate:
                gate_cfg = AdaptiveGateConfig(enabled=bool(args.adaptive_gate))
                model = ResidualPolicyRunner.load(
                    model_path,
                    vecnorm_path=vecnorm_path,
                    gate_config=gate_cfg,
                )
                meta = {**meta, **model.metadata}
                if args.adaptive_gate:
                    print("🎛️  Adaptive Terrain Gate aktiviert (flache Boden-Dämpfung + volle Hang/Stufen-Kompensation)")
            else:
                model = PPO.load(str(model_path))

    action_mode = args.action_mode or meta.get("action_mode", "residual")
    realistic_servos = (not args.ideal_servos) if args.ideal_servos else bool(meta.get("realistic_servos", True))
    use_tof_grid = args.use_tof_grid or bool(meta.get("use_tof_grid", False))

    if args.compare:
        if model is None:
            print("❌ --compare benötigt ein trainiertes PPO-Modell (--model ...).")
            sys.exit(1)
        run_ab_benchmark(
            model=model,
            vecnorm_path=vecnorm_path,
            action_mode=action_mode,
            realistic_servos=realistic_servos,
            use_tof_grid=use_tof_grid,
            max_steps=args.max_steps,
            seed=args.seed,
        )
        return

    print("==========================================================")
    print("🤖 Lasius Hexapod v2: RL Policy Evaluation")
    print("==========================================================")
    print(f"Modus:        {'Baseline (Zero-Residual)' if args.baseline else 'Trained PPO Policy'}")
    print(f"Terrain:      {args.terrain} (difficulty={args.difficulty:.2f})")
    print(f"Kommando:     vx={args.vx:+.2f} m/s, vy={args.vy:+.2f} m/s, wz={args.wz:+.2f} rad/s")
    print(f"Servos:       {'Realistic NR-645' if realistic_servos else 'Ideal'}")
    print("==========================================================\n")

    try:
        for ep in range(1, args.episodes + 1):
            print(f"\n▶ Episode {ep}/{args.episodes} gestartet...")
            res = run_episode(
                model=model,
                vecnorm_path=vecnorm_path,
                action_mode=action_mode,
                terrain=args.terrain,
                difficulty=args.difficulty,
                command=(args.vx, args.vy, args.wz),
                max_steps=args.max_steps,
                seed=args.seed + ep,
                realistic_servos=realistic_servos,
                domain_randomization=args.dr,
                enable_pushes=args.pushes,
                use_tof_grid=use_tof_grid,
                headless=args.headless,
                verbose=True,
            )
            status = "✔ abgeschlossen" if res["survived"] else "⚠️ instabil/umgekippt"
            print(
                f"  {status}: {res['steps']} Steps | Reward={res['total_reward']:.2f} "
                f"({res['reward_per_step']:.3f}/Step) | vx={res['mean_vx']:+.4f} m/s | "
                f"z_rel={res['mean_z_rel']:.3f}m | max_tilt={res['max_tilt_deg']:.1f}°"
            )
    except KeyboardInterrupt:
        print("\n⏹ Evaluierung durch Benutzer abgebrochen.")


if __name__ == "__main__":
    main()
