"""
Motion, Kinematics, and Locomotion Layer Package (`lasius.core.motion`).

Purpose & Role:
    Provides closed-form 3-DOF inverse kinematics, anatomical leg/joint domain
    models, and the 50 Hz harmonic omnidirectional gait engine.

Exports:
    - `calculate_leg_ik`: Pure trigonometric solver mapping `(x, y, z)` to `(coxa, femur, tibia)` degrees.
    - `BodySide`, `LegRow`, `LegIdentifier`, `Joint`, `Leg`: Anatomical leg representation.
    - `GaitProtocol`, `OmniGait`, `TripodGait`, `RippleGait`, `WaveGait`, `GaitType`: Walking engines.
"""

from .kinematics import calculate_leg_ik, calculate_leg_fk
from .leg import BodySide, LegRow, LegIdentifier, Joint, Leg
from .gait import GaitProtocol, OmniGait, TripodGait, RippleGait, WaveGait, GaitType
from .walknet import (
    LegState,
    LegSensoryFeedback,
    WalknetConfig,
    LegGanglion,
    WalknetGait,
)

__all__ = [
    "calculate_leg_ik",
    "calculate_leg_fk",
    "BodySide",
    "LegRow",
    "LegIdentifier",
    "Joint",
    "Leg",
    "GaitProtocol",
    "OmniGait",
    "TripodGait",
    "RippleGait",
    "WaveGait",
    "GaitType",
    "LegState",
    "LegSensoryFeedback",
    "WalknetConfig",
    "LegGanglion",
    "WalknetGait",
]
