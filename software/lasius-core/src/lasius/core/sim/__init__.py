"""
Lasius Simulation & Reinforcement Learning Package (`lasius.core.sim`).
"""

try:
    from .gym_env import LasiusGymEnv
except ImportError:
    # Optional dependency: gymnasium / pybullet might not be present on physical robot Pi
    pass

__all__ = ["LasiusGymEnv"]
