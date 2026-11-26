"""
Lasius Simulation & Reinforcement Learning Subpackage (`lasius.core.sim`).

Provides:
- `LasiusGymEnv`: Sim-to-Real Gymnasium environment wrapping PyBullet (`body_assembly` URDF)
- `ServoActuatorModel` & `ActuatorConfig`: Reely NR-645 MG BB servo dynamics & soft limits
- `TerrainGenerator` & `TerrainType`: Procedural flat/rough/slopes/steps/mixed terrain engine
"""

from .policy import AdaptiveGateConfig, ResidualPolicyRunner, build_proprioceptive_observation

try:
    from .actuator import ActuatorConfig, ServoActuatorModel, build_joint_limits_rad
    from .gym_env import LasiusGymEnv
    from .terrain import TerrainGenerator, TerrainType
except ImportError:
    ActuatorConfig = None
    ServoActuatorModel = None
    build_joint_limits_rad = None
    LasiusGymEnv = None
    TerrainGenerator = None
    TerrainType = None

__all__ = [
    "ActuatorConfig",
    "AdaptiveGateConfig",
    "LasiusGymEnv",
    "ResidualPolicyRunner",
    "ServoActuatorModel",
    "TerrainGenerator",
    "TerrainType",
    "build_joint_limits_rad",
    "build_proprioceptive_observation",
]
