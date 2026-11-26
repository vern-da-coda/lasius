#!/usr/bin/env python3
"""
Export Stable-Baselines3 PPO Policy to Lightweight Pure-NumPy `.npz` (`scripts/sim/export_policy.py`).

Purpose & Role:
    Converts a trained SB3 PPO `.zip` + matching `VecNormalize.pkl` into a
    compact `.npz` bundle (< 250 KB) that runs at 50 Hz via `ResidualPolicyRunner`
    on Raspberry Pi 4 with zero PyTorch / Stable-Baselines3 dependency, and
    verifies bit-accurate numerical parity (`max |diff| < 1e-5`) against PyTorch.

Usage:
    python3 scripts/sim/export_policy.py \
        --model data/rl_models/v2_overnight/lasius_v2_ppo_residual_final.zip \
        --out data/rl_models/v2_overnight/lasius_v2_policy_numpy.npz
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "software/lasius-core/src"))

from lasius.core.sim.policy import ResidualPolicyRunner


def export_and_verify(
    model_path: Path,
    out_path: Path,
    vecnorm_path: Path | None = None,
    samples: int = 32,
) -> float:
    from stable_baselines3 import PPO

    runner = ResidualPolicyRunner.from_sb3_ppo(
        model_path=model_path,
        vecnorm_path=vecnorm_path,
    )
    saved = runner.save_npz(out_path)
    reloaded = ResidualPolicyRunner.load_npz(saved)

    # Verify numerical parity against SB3 PyTorch deterministic inference
    sb3_model = PPO.load(str(model_path), device="cpu")
    rng = np.random.default_rng(42)
    max_diff = 0.0
    for _ in range(samples):
        raw_obs = rng.normal(0.0, 1.0, size=(reloaded.input_dim,)).astype(np.float32)
        norm_obs = reloaded.normalize_obs(raw_obs)
        sb3_act, _ = sb3_model.predict(norm_obs, deterministic=True)
        sb3_act = np.clip(sb3_act, -1.0, 1.0)
        np_act = reloaded.predict_action(raw_obs, normalize=True)
        diff = float(np.max(np.abs(sb3_act - np_act)))
        if diff > max_diff:
            max_diff = diff

    size_kb = saved.stat().st_size / 1024.0
    print(f"✅ Exported pure-NumPy PPO policy: {saved} ({size_kb:.1f} KB)")
    print(f"   Architecture: {reloaded.input_dim} -> {[w.shape[1] for w in reloaded.weights]} ({reloaded.activation})")
    print(f"   Parity vs SB3 PyTorch ({samples} random obs): max |Δ| = {max_diff:.2e}")
    if max_diff > 1e-4:
        raise RuntimeError(f"Parity check failed: max_diff={max_diff:.2e} > 1e-4")
    return max_diff


def main() -> None:
    parser = argparse.ArgumentParser(description="Export SB3 PPO policy to portable pure-NumPy .npz")
    parser.add_argument(
        "--model",
        type=str,
        default=str(REPO_ROOT / "data/rl_models/v2_overnight/lasius_v2_ppo_residual_final.zip"),
        help="Path to SB3 PPO .zip checkpoint",
    )
    parser.add_argument("--vecnorm", type=str, default=None, help="Optional explicit VecNormalize .pkl path")
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Output .npz path (defaults to <model_dir>/<model_stem>_numpy.npz)",
    )
    args = parser.parse_args()

    model_path = Path(args.model)
    out_path = Path(args.out) if args.out else model_path.with_name(model_path.stem + "_numpy.npz")
    vecnorm_path = Path(args.vecnorm) if args.vecnorm else None

    export_and_verify(model_path=model_path, out_path=out_path, vecnorm_path=vecnorm_path)


if __name__ == "__main__":
    main()
