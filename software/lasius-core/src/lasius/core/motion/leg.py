"""
Anatomical Leg & Joint Domain Model (`lasius.core.motion.leg`).

Purpose & Role:
    Models a single 3-DOF hexapod leg consisting of three `Joint` segments
    (`coxa`, `femur`, `tibia`), each bound to a calibrated `Servo` and physical
    segment length in millimeters.

Classes:
    - `BodySide`: Enum identifying `LEFT` or `RIGHT` chassis side.
    - `LegRow`: Enum identifying `FRONT`, `MIDDLE`, or `REAR` leg axis.
    - `LegIdentifier`: Canonical enum of all 6 legs (`LEFT_FRONT` .. `RIGHT_REAR`).
    - `Joint`: Pairs a `Servo` actuator with its inter-axis link `length` (mm).
    - `Leg`: Coordinates inverse kinematics (`move_tip_to(x, y, z)`) and 3-servo relaxation (`relax()`).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from lasius.core.hardware.servo import Servo
from .kinematics import calculate_leg_ik, calculate_leg_fk


class BodySide(Enum):
    """Defines the body side (left or right)."""
    LEFT = "left"
    RIGHT = "right"


class LegRow(Enum):
    """Defines the leg row (front, middle, or rear)."""
    FRONT = "front"
    MIDDLE = "middle"
    REAR = "rear"


class LegIdentifier(Enum):
    """
    Type-safe, convenient identifier for a specific leg.
    The value is a tuple `(BodySide, LegRow)`.
    """
    LEFT_FRONT = (BodySide.LEFT, LegRow.FRONT)
    LEFT_MIDDLE = (BodySide.LEFT, LegRow.MIDDLE)
    LEFT_REAR = (BodySide.LEFT, LegRow.REAR)
    RIGHT_FRONT = (BodySide.RIGHT, LegRow.FRONT)
    RIGHT_MIDDLE = (BodySide.RIGHT, LegRow.MIDDLE)
    RIGHT_REAR = (BodySide.RIGHT, LegRow.REAR)


@dataclass
class Joint:
    """
    Represents a single joint of a leg, driven by a servo with a physical limb length.
    """
    servo: Servo
    length: float  # Length of the limb in mm

    def set_angle(self, angle: float) -> None:
        """Sets the angle on the joint's servo."""
        self.servo.set_angle(angle)

    def relax(self) -> None:
        """Relaxes the joint's servo."""
        self.servo.relax()


@dataclass
class Leg:
    """
    Represents a complete 3-DOF leg of the hexapod (Coxa, Femur, Tibia)
    with open-loop IK actuation and closed-loop FK & foot contact telemetry.
    """
    side: BodySide
    row: LegRow
    coxa: Joint
    femur: Joint
    tibia: Joint
    foot_contact: bool = False
    foot_voltage: Optional[float] = None

    @property
    def name(self) -> str:
        return f"{self.side.value}_{self.row.value}"

    def move_tip_to(self, x: float, y: float, z: float) -> None:
        """
        Calculates IK and sets joint angles to move the foot tip to (x, y, z).
        """
        try:
            coxa_angle, femur_angle, tibia_angle = self._calculate_inverse_kinematics(x, y, z)
            self.coxa.set_angle(coxa_angle)
            self.femur.set_angle(femur_angle)
            self.tibia.set_angle(tibia_angle)
        except ValueError as e:
            print(f"[IK ERROR] Leg {self.side.value}_{self.row.value}: Could not reach ({x}, {y}, {z}). {e}")

    def _calculate_inverse_kinematics(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
        """Calculates 3-DOF inverse kinematics for this leg's link lengths."""
        return calculate_leg_ik(
            x=x, y=y, z=z,
            coxa_len=self.coxa.length,
            femur_len=self.femur.length,
            tibia_len=self.tibia.length,
        )

    def get_target_tip_position(self) -> Optional[Tuple[float, float, float]]:
        """
        Calculates 3-DOF forward kinematics from the commanded target angles (`current_angle`).
        Returns `None` if any joint has not yet received a target angle.
        """
        c = self.coxa.servo.current_angle
        f = self.femur.servo.current_angle
        t = self.tibia.servo.current_angle
        if c is None or f is None or t is None:
            return None
        return calculate_leg_fk(
            coxa_angle=c,
            femur_angle=f,
            tibia_angle=t,
            coxa_len=self.coxa.length,
            femur_len=self.femur.length,
            tibia_len=self.tibia.length,
        )

    def get_actual_tip_position(self) -> Optional[Tuple[float, float, float]]:
        """
        Calculates 3-DOF forward kinematics from the measured closed-loop potentiometer
        angles (`measured_angle`) when all 3 joints report `actual_valid == True`.
        Returns `None` if any joint lacks valid closed-loop feedback.
        """
        if not (self.coxa.servo.actual_valid and self.femur.servo.actual_valid and self.tibia.servo.actual_valid):
            return None
        c = self.coxa.servo.measured_angle
        f = self.femur.servo.measured_angle
        t = self.tibia.servo.measured_angle
        if c is None or f is None or t is None:
            return None
        return calculate_leg_fk(
            coxa_angle=c,
            femur_angle=f,
            tibia_angle=t,
            coxa_len=self.coxa.length,
            femur_len=self.femur.length,
            tibia_len=self.tibia.length,
        )

    def relax(self) -> None:
        """Relaxes all 3 joints of this leg."""
        self.coxa.relax()
        self.femur.relax()
        self.tibia.relax()
