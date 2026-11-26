"""
Biomimetic Decentralized Walknet Gait Engine & Local Reflexes (`lasius.core.motion.walknet`).

Purpose & Role:
    Implements insect-inspired decentralized locomotion (Walknet / Cruse Rules 1–4)
    and local closed-loop sensory reflex arcs (`software/TODO.md` AP 1 & AP 2):
    - Each of the 6 legs runs an autonomous local ganglion (`LegGanglion`) with
      explicit local states: `STANCE`, `SWING`, `SEARCH`, and `RECOVERY`.
    - Inter-leg coordination emerges locally via Cruse neighborhood rules rather
      than a fixed global phase clock:
      * Rule 1 (Inhibition): Ipsilateral posterior leg is inhibited from liftoff
        while the anterior neighbor is not grounded; contralateral & support-polygon
        guards maintain static stability (>= 3 legs in stance).
      * Rule 2 (Excitation / Facilitation): Touchdown of an anterior leg shifts
        the posterior neighbor's PEP forward, generating emergent metachronal waves
        (Wave -> Ripple -> Tripod as locomotion speed increases).
      * Rule 3 (Position Transfer / Targeting): Posterior leg biases its swing
        landing target (AEP) toward the anterior neighbor's actual foothold.
      * Rule 4 (Load-Based Delay): High stance load / tracking error on a supporting
        leg delays neighboring liftoffs for extra stability margin.
    - Local Sensory Reflexes (closed-loop via ADS1115 pots & Omron D2F-L switches):
      * Elevator Reflex (`SWING` -> `RECOVERY`): Triggered by stall or excessive
        joint tracking error during swing; retracts slightly and lifts over obstacle.
      * Searching Reflex (`SWING` -> `SEARCH`): Triggered at end of swing when
        `use_foot_switches=True` and foot contact is not yet detected; extends
        downward until ground contact is established or reach limit is hit.
      * Terrain-Adaptive Clearance: Optional belly ToF minimum distance adjusts
        effective body clearance automatically over ground obstacles.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple

from .gait import GaitProtocol, OmniGait
from .leg import BodySide, LegIdentifier, LegRow


class LegState(str, Enum):
    """Local state of an individual thoracic leg ganglion."""
    STANCE = "stance"
    SWING = "swing"
    SEARCH = "search"
    RECOVERY = "recovery"


@dataclass
class LegSensoryFeedback:
    """Closed-loop sensory snapshot for a single leg."""
    foot_contact: bool = False
    tracking_error_deg: float = 0.0
    is_stalled: bool = False
    load_estimate: float = 0.0  # Normalized [0.0, 1.0] stance load / lag ratio
    actual_tip: Optional[Tuple[float, float, float]] = None


@dataclass
class WalknetConfig:
    """Parameters governing decentralized Walknet ganglia, Cruse rules, and reflexes."""
    dt: float = 0.02                       # Control period [s] (50 Hz)
    step_length_mm: float = 40.0           # Nominal full stride [mm]
    step_height_mm: float = 28.0           # Nominal swing arch lift [mm]
    body_height_mm: float = -80.0          # Nominal stance Z [mm]
    base_speed_mm_s: float = 70.0          # Stance foot sweep speed at command=1.0 [mm/s]
    swing_duration_s: float = 0.28         # Duration of a single swing arc [s]

    # Cruse local coordination rules (1–4)
    rule1_inhibit_ipsilateral: bool = True
    rule2_excite_fraction: float = 0.28    # Forward PEP shift on anterior touchdown
    rule3_position_transfer: float = 0.30  # AEP blend toward anterior foothold [0..1]
    rule4_load_threshold: float = 0.65     # Load ratio above which neighbor liftoff is delayed
    min_stance_legs: int = 3               # Minimum statically stable supporting legs

    # Local sensory reflexes (AP 2)
    use_foot_switches: bool = False        # Enable Searching Reflex on missing A3 contact
    elevator_error_deg: float = 8.0        # Swing tracking error threshold for Elevator Reflex
    elevator_lift_mm: float = 22.0         # Additional vertical clearance during recovery [mm]
    elevator_retract_mm: float = 8.0       # Brief pullback distance before lifting [mm]
    recovery_duration_s: float = 0.22      # Duration of Elevator recovery arc [s]
    search_speed_mm_s: float = 65.0        # Downward probing rate during SEARCH [mm/s]
    max_search_z_mm: float = -122.0        # Maximum safe downward extension [mm]
    stance_z_relax_rate: float = 0.08      # Return rate toward nominal stance Z per tick
    stance_load_compliance_mm: float = 4.0 # Max Z compliance yield under heavy load

    # Terrain-adaptive belly clearance (AP 3)
    target_belly_clearance_m: float = 0.085
    max_clearance_boost_mm: float = 30.0


# Anatomical neighbor topology for Cruse rules
IPSILATERAL_ANTERIOR: Dict[LegIdentifier, Optional[LegIdentifier]] = {
    LegIdentifier.LEFT_FRONT: None,
    LegIdentifier.LEFT_MIDDLE: LegIdentifier.LEFT_FRONT,
    LegIdentifier.LEFT_REAR: LegIdentifier.LEFT_MIDDLE,
    LegIdentifier.RIGHT_FRONT: None,
    LegIdentifier.RIGHT_MIDDLE: LegIdentifier.RIGHT_FRONT,
    LegIdentifier.RIGHT_REAR: LegIdentifier.RIGHT_MIDDLE,
}

IPSILATERAL_POSTERIOR: Dict[LegIdentifier, Optional[LegIdentifier]] = {
    LegIdentifier.LEFT_FRONT: LegIdentifier.LEFT_MIDDLE,
    LegIdentifier.LEFT_MIDDLE: LegIdentifier.LEFT_REAR,
    LegIdentifier.LEFT_REAR: None,
    LegIdentifier.RIGHT_FRONT: LegIdentifier.RIGHT_MIDDLE,
    LegIdentifier.RIGHT_MIDDLE: LegIdentifier.RIGHT_REAR,
    LegIdentifier.RIGHT_REAR: None,
}

CONTRALATERAL_PAIR: Dict[LegIdentifier, LegIdentifier] = {
    LegIdentifier.LEFT_FRONT: LegIdentifier.RIGHT_FRONT,
    LegIdentifier.LEFT_MIDDLE: LegIdentifier.RIGHT_MIDDLE,
    LegIdentifier.LEFT_REAR: LegIdentifier.RIGHT_REAR,
    LegIdentifier.RIGHT_FRONT: LegIdentifier.LEFT_FRONT,
    LegIdentifier.RIGHT_MIDDLE: LegIdentifier.LEFT_MIDDLE,
    LegIdentifier.RIGHT_REAR: LegIdentifier.LEFT_REAR,
}

# Initial staggered stride offsets (normalized [-0.4, +0.4]) so legs do not
# hit PEP simultaneously on cold start; breaks symmetry cleanly into tripod/wave.
_INITIAL_STRIDE_BIAS: Dict[LegIdentifier, float] = {
    LegIdentifier.LEFT_REAR: -0.35,
    LegIdentifier.RIGHT_FRONT: -0.20,
    LegIdentifier.LEFT_MIDDLE: -0.05,
    LegIdentifier.RIGHT_REAR: 0.10,
    LegIdentifier.LEFT_FRONT: 0.25,
    LegIdentifier.RIGHT_MIDDLE: 0.35,
}


class LegGanglion:
    """
    Autonomous thoracic ganglion controlling one 3-DOF leg.

    Maintains local phase/state (`STANCE`, `SWING`, `SEARCH`, `RECOVERY`),
    applies local reflex arcs (Elevator & Searching), and exposes simple
    local coordination signals for neighboring ganglia.
    """

    def __init__(
        self,
        leg_id: LegIdentifier,
        neutral_pos: Tuple[float, float, float],
        config: WalknetConfig,
    ):
        self.leg_id = leg_id
        self.config = config
        self.neutral_pos = neutral_pos

        self.state: LegState = LegState.STANCE
        self.pos: Tuple[float, float, float] = neutral_pos
        self.stance_z: float = neutral_pos[2]

        # Swing / recovery trajectory endpoints
        self.swing_phase: float = 0.0
        self.swing_start: Tuple[float, float, float] = neutral_pos
        self.swing_target: Tuple[float, float, float] = neutral_pos

        self.recovery_phase: float = 0.0
        self.recovery_start: Tuple[float, float, float] = neutral_pos
        self.recovery_apex_z: float = neutral_pos[2] + config.step_height_mm + config.elevator_lift_mm

        # Inter-leg Cruse signals
        self.pep_excite_bonus_mm: float = 0.0
        self.just_touched_down: bool = False
        self.last_touchdown_offset_xy: Tuple[float, float] = (0.0, 0.0)
        self.feedback: LegSensoryFeedback = LegSensoryFeedback(foot_contact=True)

        # Telemetry / diagnostic counters
        self.elevator_triggers: int = 0
        self.search_triggers: int = 0
        self.swing_count: int = 0

    @property
    def is_grounded(self) -> bool:
        """Returns True when the leg is supporting body weight in STANCE."""
        return self.state == LegState.STANCE

    def start_swing(self, target_xy: Tuple[float, float], target_z: float) -> None:
        """Transitions this ganglion from STANCE into SWING toward target AEP."""
        self.state = LegState.SWING
        self.swing_phase = 0.0
        self.swing_start = self.pos
        self.swing_target = (target_xy[0], target_xy[1], target_z)
        self.pep_excite_bonus_mm = 0.0
        self.just_touched_down = False
        self.swing_count += 1

    def trigger_elevator_reflex(self, retract_dir_xy: Tuple[float, float]) -> None:
        """
        Local Elevator Reflex (`SWING` -> `RECOVERY`):
        Immediately aborts the obstructed swing arc, retracts slightly away
        from the obstacle, and vaults over it with extra vertical clearance.
        """
        self.state = LegState.RECOVERY
        self.recovery_phase = 0.0
        self.recovery_start = (
            self.pos[0] + retract_dir_xy[0] * self.config.elevator_retract_mm,
            self.pos[1] + retract_dir_xy[1] * self.config.elevator_retract_mm,
            self.pos[2],
        )
        self.recovery_apex_z = max(
            self.pos[2] + self.config.elevator_lift_mm,
            self.swing_target[2] + self.config.step_height_mm + self.config.elevator_lift_mm,
        )
        self.elevator_triggers += 1

    def complete_touchdown(self, z_contact: float) -> None:
        """Locks the leg into STANCE at the discovered ground elevation."""
        self.state = LegState.STANCE
        self.stance_z = z_contact
        self.pos = (self.pos[0], self.pos[1], z_contact)
        self.just_touched_down = True
        self.last_touchdown_offset_xy = (
            self.pos[0] - self.neutral_pos[0],
            self.pos[1] - self.neutral_pos[1],
        )

    def step_swing_or_reflex(
        self,
        dt: float,
        nominal_stance_z: float,
        step_height: float,
        stride_dir_leg_xy: Tuple[float, float],
    ) -> None:
        """Advances SWING, RECOVERY, or SEARCH state for one tick."""
        self.just_touched_down = False

        if self.state == LegState.SWING:
            # Check local Elevator Reflex trigger during active swing flight
            if 0.08 <= self.swing_phase <= 0.92:
                obstructed = (
                    self.feedback.is_stalled
                    or abs(self.feedback.tracking_error_deg) >= self.config.elevator_error_deg
                )
                if obstructed:
                    retract = (-stride_dir_leg_xy[0], -stride_dir_leg_xy[1])
                    self.trigger_elevator_reflex(retract)
                    return

            dur = max(0.08, self.config.swing_duration_s)
            self.swing_phase = min(1.0, self.swing_phase + dt / dur)
            # C1-continuous cosine horizontal advance & sin^2 vertical clearance
            s_xy = 0.5 * (1.0 - math.cos(math.pi * self.swing_phase))
            s_z = math.sin(math.pi * self.swing_phase) ** 2

            x = self.swing_start[0] + s_xy * (self.swing_target[0] - self.swing_start[0])
            y = self.swing_start[1] + s_xy * (self.swing_target[1] - self.swing_start[1])
            z_base = self.swing_start[2] + s_xy * (self.swing_target[2] - self.swing_start[2])
            z = z_base + step_height * s_z
            self.pos = (x, y, z)

            # Early touchdown if foot switch closes on final descent (phase > 0.65)
            if (
                self.config.use_foot_switches
                and self.swing_phase >= 0.65
                and self.feedback.foot_contact
            ):
                self.complete_touchdown(z)
                return

            if self.swing_phase >= 1.0:
                if self.config.use_foot_switches and not self.feedback.foot_contact:
                    # Searching Reflex: ground not found at nominal touchdown Z
                    self.state = LegState.SEARCH
                    self.search_triggers += 1
                else:
                    self.complete_touchdown(self.swing_target[2])

        elif self.state == LegState.RECOVERY:
            dur = max(0.08, self.config.recovery_duration_s)
            self.recovery_phase = min(1.0, self.recovery_phase + dt / dur)
            s_xy = 0.5 * (1.0 - math.cos(math.pi * self.recovery_phase))
            # High parabolic vault peaking near recovery_apex_z
            s_z = math.sin(math.pi * self.recovery_phase)

            x = self.recovery_start[0] + s_xy * (self.swing_target[0] - self.recovery_start[0])
            y = self.recovery_start[1] + s_xy * (self.swing_target[1] - self.recovery_start[1])
            z_lin = self.recovery_start[2] + s_xy * (self.swing_target[2] - self.recovery_start[2])
            extra = max(0.0, self.recovery_apex_z - z_lin)
            z = z_lin + extra * s_z
            self.pos = (x, y, z)

            if self.recovery_phase >= 1.0:
                if self.config.use_foot_switches and not self.feedback.foot_contact:
                    self.state = LegState.SEARCH
                    self.search_triggers += 1
                else:
                    self.complete_touchdown(self.swing_target[2])

        elif self.state == LegState.SEARCH:
            # Searching Reflex: probe straight down until switch triggers or reach limit
            if self.feedback.foot_contact:
                self.complete_touchdown(self.pos[2])
                return

            next_z = self.pos[2] - self.config.search_speed_mm_s * dt
            if next_z <= self.config.max_search_z_mm:
                self.pos = (self.pos[0], self.pos[1], self.config.max_search_z_mm)
                self.complete_touchdown(self.config.max_search_z_mm)
            else:
                self.pos = (self.pos[0], self.pos[1], next_z)


class WalknetGait(GaitProtocol):
    """
    Decentralized biomimetic gait engine (`GaitProtocol` drop-in replacement for `OmniGait`).

    Coordinates 6 `LegGanglion` instances via Cruse Rules 1–4 and closed-loop
    local reflexes (`Elevator`, `Searching`, `Stance-Load Compliance`).
    """

    def __init__(
        self,
        config: Optional[WalknetConfig] = None,
        walk_x: float = 0.0,
        walk_y: float = 0.0,
        turn_z: float = 0.0,
        gait_speed: float = 1.0,
        step_length: Optional[float] = None,
        step_height: Optional[float] = None,
        body_height: Optional[float] = None,
        body_roll: float = 0.0,
        body_pitch: float = 0.0,
        use_foot_switches: Optional[bool] = None,
        geometry: Optional[Any] = None,
    ):
        self.config = config or WalknetConfig()
        if step_length is not None:
            self.config.step_length_mm = float(step_length)
        if step_height is not None:
            self.config.step_height_mm = float(step_height)
        if body_height is not None:
            self.config.body_height_mm = float(body_height)
        if use_foot_switches is not None:
            self.config.use_foot_switches = bool(use_foot_switches)

        self.walk_x = float(walk_x)
        self.walk_y = float(walk_y)
        self.turn_z = float(turn_z)
        self.gait_speed = float(gait_speed)
        self.step_length = self.config.step_length_mm
        self.step_height = self.config.step_height_mm

        self.body_height = self.config.body_height_mm
        self.body_roll = float(body_roll)
        self.body_pitch = float(body_pitch)
        self._belly_clearance_boost_mm: float = 0.0

        self.mount_points: Dict[LegIdentifier, Tuple[float, float]] = dict(OmniGait.MOUNT_POINTS)
        self.mount_angles: Dict[LegIdentifier, float] = dict(OmniGait.MOUNT_ANGLES)
        self.neutral_stances: Dict[LegIdentifier, Tuple[float, float, float]] = dict(
            OmniGait.NEUTRAL_STANCES
        )
        if geometry is not None:
            self.apply_geometry(geometry)

        # Instantiate 6 decentralized thoracic ganglia
        self.ganglia: Dict[LegIdentifier, LegGanglion] = {}
        for leg_id in LegIdentifier:
            nx, ny, _ = self.neutral_stances[leg_id]
            sz = self._get_leg_stance_z(leg_id)
            g = LegGanglion(leg_id=leg_id, neutral_pos=(nx, ny, sz), config=self.config)
            self.ganglia[leg_id] = g

        self._stagger_applied: bool = False
        self._tick_count: int = 0

    def apply_geometry(self, geometry: Any) -> None:
        """Applies physical chassis mount coordinates & stance clearance from GeometryConfig."""
        if hasattr(geometry, "chassis") and geometry.chassis:
            chassis = geometry.chassis
            half_w_fr = chassis.width_front_rear / 2.0
            half_w_m = chassis.width_middle / 2.0
            dy = chassis.axis_distance_longitudinal
            self.mount_points = {
                LegIdentifier.LEFT_FRONT: (-half_w_fr, -dy),
                LegIdentifier.LEFT_MIDDLE: (-half_w_m, 0.0),
                LegIdentifier.LEFT_REAR: (-half_w_fr, dy),
                LegIdentifier.RIGHT_FRONT: (half_w_fr, -dy),
                LegIdentifier.RIGHT_MIDDLE: (half_w_m, 0.0),
                LegIdentifier.RIGHT_REAR: (half_w_fr, dy),
            }
        if hasattr(geometry, "default_stance") and geometry.default_stance:
            clearance = getattr(geometry.default_stance, "ground_clearance", 80.0)
            self.body_height = -abs(float(clearance))
            self.config.body_height_mm = self.body_height

    def set_velocity(
        self,
        walk_x: float = 0.0,
        walk_y: float = 0.0,
        turn_z: float = 0.0,
        immediate: bool = False,
    ) -> None:
        """Sets high-level holonomic locomotion intention (no joint angles exposed)."""
        self.walk_x = max(-1.0, min(1.0, float(walk_x)))
        self.walk_y = max(-1.0, min(1.0, float(walk_y)))
        self.turn_z = max(-1.0, min(1.0, float(turn_z)))

    def set_pose(
        self,
        height: float = -80.0,
        roll: float = 0.0,
        pitch: float = 0.0,
        immediate: bool = False,
    ) -> None:
        """Sets target chassis posture (height mm, roll/pitch deg)."""
        self.body_height = max(-120.0, min(-40.0, float(height)))
        self.body_roll = max(-25.0, min(25.0, float(roll)))
        self.body_pitch = max(-25.0, min(25.0, float(pitch)))

    def set_belly_tof_distance_m(self, min_distance_m: Optional[float]) -> float:
        """
        Terrain-adaptive clearance (AP 3):
        When the belly VL53L5CX ToF detects an obstacle closer than
        `target_belly_clearance_m`, automatically increases effective body clearance
        (making stance Z more negative) without pilot intervention.
        """
        if min_distance_m is None or min_distance_m <= 0.0:
            self._belly_clearance_boost_mm *= 0.90
            return self._belly_clearance_boost_mm

        deficit_m = self.config.target_belly_clearance_m - float(min_distance_m)
        if deficit_m > 0.0:
            desired_boost = min(deficit_m * 1000.0, self.config.max_clearance_boost_mm)
            self._belly_clearance_boost_mm += 0.25 * (desired_boost - self._belly_clearance_boost_mm)
        else:
            self._belly_clearance_boost_mm *= 0.92
        return self._belly_clearance_boost_mm

    def update_feedback(self, feedback: Dict[LegIdentifier, LegSensoryFeedback]) -> None:
        """Feeds closed-loop potentiometer lag, stall flags, and A3 foot switches to ganglia."""
        for leg_id, fb in feedback.items():
            if leg_id in self.ganglia:
                self.ganglia[leg_id].feedback = fb

    def _get_leg_stance_z(self, leg_id: LegIdentifier) -> float:
        """Computes desired nominal stance Z (mm) including roll, pitch, and ToF clearance."""
        mx, my = self.mount_points[leg_id]
        eff_height = max(-120.0, self.body_height - self._belly_clearance_boost_mm)
        z_off = mx * math.sin(math.radians(self.body_roll)) + my * math.sin(math.radians(self.body_pitch))
        return max(-122.0, min(-40.0, eff_height + z_off))

    def _leg_stride_vector_body(self, leg_id: LegIdentifier) -> Tuple[float, float]:
        """
        Returns the body-frame velocity vector `(vx_mm_s, vy_mm_s)` of the body
        relative to the ground at this leg's mount point (+X forward, +Y left).
        During STANCE the foot sweeps along `(-vx, -vy)` relative to the chassis.
        """
        speed = self.config.base_speed_mm_s * max(0.1, self.gait_speed)
        vx_trans = self.walk_y * speed
        vy_trans = -self.walk_x * speed

        mx, my = self.mount_points[leg_id]
        bx = -my
        by = -mx
        turn_scale = speed * 0.75 / 100.0
        vx_turn = -by * turn_scale * self.turn_z
        vy_turn = bx * turn_scale * self.turn_z
        return (vx_trans + vx_turn, vy_trans + vy_turn)

    def _body_to_leg_xy(self, leg_id: LegIdentifier, bx: float, by: float) -> Tuple[float, float]:
        """Projects a body-frame XY vector into the leg's local `(radial x, tangential y)` frame."""
        psi = self.mount_angles[leg_id]
        dr = bx * math.cos(psi) + by * math.sin(psi)
        dy = bx * math.sin(psi) - by * math.cos(psi)
        return (dr, dy)

    def _can_start_swing(
        self,
        leg_id: LegIdentifier,
        urgency: float,
        grounded_count: int,
    ) -> bool:
        """
        Evaluates Cruse Rules 1 & 4 plus contralateral/support-polygon static stability.
        `urgency >= 1.35` acts as an emergency mechanical-limit override so a leg
        never overextends past workspace limits.
        """
        # Static stability invariant: preserve at least min_stance_legs supporting the body
        if grounded_count <= self.config.min_stance_legs:
            return False

        # Contralateral safety: avoid lifting opposite leg in the same row simultaneously
        contra = CONTRALATERAL_PAIR[leg_id]
        if not self.ganglia[contra].is_grounded and urgency < 1.40:
            return False

        # Cruse Rule 1 (Inhibition): ipsilateral anterior neighbor suppresses liftoff while swinging
        anterior = IPSILATERAL_ANTERIOR[leg_id]
        if self.config.rule1_inhibit_ipsilateral and anterior is not None:
            if not self.ganglia[anterior].is_grounded and urgency < 1.35:
                return False

        # Avoid adjacent ipsilateral simultaneous lift (posterior neighbor also swinging)
        posterior = IPSILATERAL_POSTERIOR[leg_id]
        if posterior is not None and not self.ganglia[posterior].is_grounded and urgency < 1.35:
            return False

        # Cruse Rule 4 (Load-based inhibition): heavy load on adjacent stance leg delays liftoff
        neighbors = [n for n in (anterior, posterior, contra) if n is not None]
        if any(
            self.ganglia[n].is_grounded
            and self.ganglia[n].feedback.load_estimate >= self.config.rule4_load_threshold
            for n in neighbors
        ):
            if urgency < 1.30:
                return False

        return True

    def tick(self) -> Dict[LegIdentifier, Tuple[float, float, float]]:
        """
        Executes one 50 Hz decentralized Walknet step across all 6 ganglia.

        Returns:
            Mapping `LegIdentifier -> (x, y, z)` in leg-local millimeters.
        """
        dt = self.config.dt
        self._tick_count += 1
        half_stride = 0.5 * max(10.0, self.step_length)

        eff_cmd = math.sqrt(self.walk_x**2 + self.walk_y**2 + (self.turn_z * 0.75) ** 2)
        is_moving = eff_cmd > 0.01

        # Apply tiny symmetry-breaking stride bias once when starting from neutral rest
        if is_moving and not self._stagger_applied:
            self._stagger_applied = True
            for leg_id, g in self.ganglia.items():
                if g.is_grounded:
                    vx_b, vy_b = self._leg_stride_vector_body(leg_id)
                    v_leg = self._body_to_leg_xy(leg_id, vx_b, vy_b)
                    v_mag = math.hypot(v_leg[0], v_leg[1])
                    if v_mag > 1e-4:
                        ux, uy = v_leg[0] / v_mag, v_leg[1] / v_mag
                        bias_mm = _INITIAL_STRIDE_BIAS[leg_id] * half_stride
                        nx, ny, _ = self.neutral_stances[leg_id]
                        g.pos = (nx + ux * bias_mm, ny + uy * bias_mm, g.pos[2])

        # 1. Advance active SWING / RECOVERY / SEARCH legs first
        for leg_id, g in self.ganglia.items():
            if not g.is_grounded:
                vx_b, vy_b = self._leg_stride_vector_body(leg_id)
                v_leg = self._body_to_leg_xy(leg_id, vx_b, vy_b)
                v_mag = math.hypot(v_leg[0], v_leg[1])
                stride_dir = (v_leg[0] / v_mag, v_leg[1] / v_mag) if v_mag > 1e-4 else (0.0, 1.0)
                nom_z = self._get_leg_stance_z(leg_id)
                g.step_swing_or_reflex(
                    dt=dt,
                    nominal_stance_z=nom_z,
                    step_height=self.step_height,
                    stride_dir_leg_xy=stride_dir,
                )

        # 2. Propagate Cruse Rule 2 (Excitation on anterior touchdown)
        for leg_id, g in self.ganglia.items():
            if g.just_touched_down:
                posterior = IPSILATERAL_POSTERIOR[leg_id]
                if posterior is not None and self.ganglia[posterior].is_grounded:
                    self.ganglia[posterior].pep_excite_bonus_mm = (
                        self.config.rule2_excite_fraction * half_stride
                    )

        # 3. Advance STANCE legs and collect PEP liftoff candidates
        candidates: List[Tuple[float, LegIdentifier, Tuple[float, float], float]] = []
        for leg_id, g in self.ganglia.items():
            if not g.is_grounded:
                continue

            nx, ny, _ = self.neutral_stances[leg_id]
            nom_z = self._get_leg_stance_z(leg_id)

            # Smooth stance Z adaptation + load compliance (AP 2)
            load_yield = (
                self.config.stance_load_compliance_mm
                * max(0.0, g.feedback.load_estimate - 0.5)
                * 2.0
            )
            target_z = max(-122.0, min(-40.0, nom_z + load_yield))
            new_z = g.pos[2] + (target_z - g.pos[2]) * self.config.stance_z_relax_rate

            if not is_moving:
                # Gently recenter feet when stationary
                new_x = g.pos[0] + (nx - g.pos[0]) * 0.12
                new_y = g.pos[1] + (ny - g.pos[1]) * 0.12
                g.pos = (new_x, new_y, new_z)
                continue

            vx_b, vy_b = self._leg_stride_vector_body(leg_id)
            v_leg_x, v_leg_y = self._body_to_leg_xy(leg_id, vx_b, vy_b)
            v_mag = math.hypot(v_leg_x, v_leg_y)

            # During stance, foot sweeps opposite to body travel direction
            new_x = g.pos[0] - v_leg_x * dt
            new_y = g.pos[1] - v_leg_y * dt
            g.pos = (new_x, new_y, new_z)

            if v_mag > 1e-4:
                ux, uy = v_leg_x / v_mag, v_leg_y / v_mag
                # Signed progress along travel axis: +half_stride = AEP, -half_stride = PEP
                rel_x = new_x - nx
                rel_y = new_y - ny
                along_travel = rel_x * ux + rel_y * uy
                radial_excursion = math.hypot(rel_x, rel_y)

                # Effective PEP threshold (shortened by Cruse Rule 2 excitation)
                pep_limit = max(0.35 * half_stride, half_stride - g.pep_excite_bonus_mm)
                if along_travel <= -pep_limit or radial_excursion >= half_stride * 1.15:
                    urgency = max(-along_travel / max(half_stride, 1e-3), radial_excursion / max(half_stride, 1e-3))

                    # Target AEP in leg frame + Cruse Rule 3 position transfer from anterior neighbor
                    aep_x = nx + ux * half_stride
                    aep_y = ny + uy * half_stride
                    anterior = IPSILATERAL_ANTERIOR[leg_id]
                    if anterior is not None and self.config.rule3_position_transfer > 0.0:
                        ant_off = self.ganglia[anterior].last_touchdown_offset_xy
                        alpha = self.config.rule3_position_transfer
                        aep_x = (1.0 - alpha) * aep_x + alpha * (nx + max(-half_stride, min(half_stride, ant_off[0])))
                        aep_y = (1.0 - alpha) * aep_y + alpha * (ny + max(-half_stride, min(half_stride, ant_off[1])))

                    candidates.append((urgency, leg_id, (aep_x, aep_y), nom_z))

        # 4. Arbitrate PEP liftoff candidates by highest urgency under Cruse Rules 1 & 4
        candidates.sort(key=lambda item: item[0], reverse=True)
        grounded_count = sum(1 for g in self.ganglia.values() if g.is_grounded)
        for urgency, leg_id, target_xy, target_z in candidates:
            if self._can_start_swing(leg_id, urgency, grounded_count):
                self.ganglia[leg_id].start_swing(target_xy=target_xy, target_z=target_z)
                grounded_count -= 1

        return {leg_id: g.pos for leg_id, g in self.ganglia.items()}

    def get_diagnostics(self) -> Dict[str, Any]:
        """Returns structured diagnostic telemetry for all 6 decentralized ganglia."""
        return {
            "tick": self._tick_count,
            "grounded_count": sum(1 for g in self.ganglia.values() if g.is_grounded),
            "belly_clearance_boost_mm": round(self._belly_clearance_boost_mm, 2),
            "legs": {
                f"{leg_id.value[0].value}_{leg_id.value[1].value}": {
                    "state": g.state.value,
                    "pos_mm": tuple(round(v, 2) for v in g.pos),
                    "swing_count": g.swing_count,
                    "elevator_triggers": g.elevator_triggers,
                    "search_triggers": g.search_triggers,
                }
                for leg_id, g in self.ganglia.items()
            },
        }
