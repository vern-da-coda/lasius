"""
Lasius Hexapod v2 Sim-to-Real Gymnasium Environment (`LasiusGymEnv`).

Purpose & Role:
    Standard Gymnasium environment wrapping PyBullet rigid-body physics for
    training adaptive locomotion policies (PPO / SAC) on the 18-DOF Lasius v2
    Hexapod (`body_assembly.FCStd` URDF — chassis + 6 legs, no head/gaster).

    Engineered for zero-cheat Sim-to-Real transfer:
    - Realistic Reely NR-645 MG BB servo actuator dynamics (tau = 75 ms lag,
      350 deg/s slew limit, ~1.1 N·m stall torque, collision-verified soft limits)
    - Purely real-sensor-faithful proprioceptive observation space (71 dims):
      * BNO085 IMU: projected gravity vector (3) + base angular velocity (3)
      * ADS1115 Servo Potentiometers: joint offsets (18) + finite-diff velocities (18)
      * Tarsus Foot Microswitches (A3): binary ground contacts (6)
      * OmniGait Cycle Phase: [sin(2πφ), cos(2πφ)] (2)
      * Velocity Commands: [cmd_vx, cmd_vy, cmd_wz] (3)
      * Previous Action: a_{t-1} (18)
      (Optional +9 dims for 3x3 belly VL53L5CX ToF grid when `use_tof_grid=True`)
    - Procedural uneven terrain generator (flat, rough, slopes, steps, mixed)
      with relative belly-clearance tracking and curriculum difficulty [0.0, 1.0]
    - Domain randomization (friction, mass, servo dynamics, sensor noise) and
      lateral push perturbations.

Action Space (18 dims):
    Continuous Box([-1.0, 1.0], shape=(18,)) representing scaled residual joint
    offsets (Residual mode, default: ±11.5 deg on top of 50 Hz OmniGait) or
    direct joint angle offsets relative to neutral stance (Direct mode: ±22.9 deg).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import gymnasium as gym
from gymnasium import spaces
import numpy as np

try:
    import pybullet as p
    import pybullet_data
except ImportError:
    p = None
    pybullet_data = None

from lasius.core.motion.gait import GaitType, LegIdentifier, OmniGait
from lasius.core.motion.kinematics import calculate_leg_ik
from lasius.core.sim.actuator import ActuatorConfig, ServoActuatorModel
from lasius.core.sim.terrain import TerrainGenerator, TerrainType


def _find_repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".git").is_dir() or (parent / "hardware" / "mechanics").is_dir():
            return parent
    return current.parents[6]


DEFAULT_URDF_PATH = (
    _find_repo_root() / "hardware" / "mechanics" / "export" / "urdf" / "lasius.urdf"
)

# Canonical leg ordering (6 legs, 18 revolute joints)
LEG_ORDER: List[Tuple[LegIdentifier, str, str]] = [
    (LegIdentifier.LEFT_FRONT, "left_front", "lf"),
    (LegIdentifier.LEFT_MIDDLE, "left_middle", "lm"),
    (LegIdentifier.LEFT_REAR, "left_rear", "lr"),
    (LegIdentifier.RIGHT_FRONT, "right_front", "rf"),
    (LegIdentifier.RIGHT_MIDDLE, "right_middle", "rm"),
    (LegIdentifier.RIGHT_REAR, "right_rear", "rr"),
]

JOINT_NAMES: List[str] = []
for _, _prefix, _ in LEG_ORDER:
    JOINT_NAMES.extend([f"{_prefix}_coxa", f"{_prefix}_femur", f"{_prefix}_tibia"])

FOOT_LINK_NAMES: List[str] = [f"link_{_short}_foot" for _, _, _short in LEG_ORDER]

# Calibrated kinematic velocity limits for v2 OmniGait (step_length=40 mm, gait_speed=1.0)
MAX_CMD_VX = 0.08   # m/s (+X forward)
MAX_CMD_VY = 0.07   # m/s (+Y left)
MAX_CMD_WZ = 0.28   # rad/s (+Z CCW yaw)

# Nominal standing height of base_link origin above local ground (v2 bionic ant stance)
TARGET_CLEARANCE_M = 0.093
DROP_TERMINATION_CLEARANCE_M = 0.040
TILT_TERMINATION_RAD = 0.65  # ~37.2 deg


class LasiusGymEnv(gym.Env):
    """
    Sim-to-Real Gymnasium Environment for Lasius v2 Hexapod Locomotion.
    """

    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 50}

    def __init__(
        self,
        urdf_path: Optional[str | Path] = None,
        render_mode: Optional[str] = None,
        action_mode: str = "residual",
        control_freq: float = 50.0,
        physics_freq: float = 250.0,
        max_episode_steps: int = 1000,
        residual_joint_limit: float = 0.20,  # ~11.5 deg max additive offset
        lateral_friction: float = 1.2,
        fixed_command: Optional[Tuple[float, float, float]] = None,
        terrain_type: TerrainType | str = TerrainType.FLAT,
        terrain_difficulty: float = 0.0,
        realistic_servos: bool = True,
        domain_randomization: bool = False,
        enable_pushes: bool = False,
        use_tof_grid: bool = False,
        actuator_config: Optional[ActuatorConfig] = None,
        resample_command_steps: int = 250,
    ):
        super().__init__()

        if p is None:
            raise ImportError(
                "PyBullet is required for LasiusGymEnv. Install via 'pip install pybullet'."
            )

        self.urdf_path = str(urdf_path or DEFAULT_URDF_PATH)
        if not Path(self.urdf_path).is_file():
            raise FileNotFoundError(
                f"Lasius URDF model not found at '{self.urdf_path}'."
            )

        if action_mode not in ("residual", "direct"):
            raise ValueError(
                f"Invalid action_mode: '{action_mode}'. Expected 'residual' or 'direct'."
            )

        self.action_mode = action_mode
        self.render_mode = render_mode
        self.control_freq = float(control_freq)
        self.physics_freq = float(physics_freq)
        self.dt = 1.0 / self.control_freq
        self.physics_dt = 1.0 / self.physics_freq
        self.substeps = max(1, int(round(self.physics_freq / self.control_freq)))
        self.max_episode_steps = int(max_episode_steps)
        self.residual_joint_limit = float(residual_joint_limit)
        self.lateral_friction = float(lateral_friction)
        self.fixed_command = fixed_command

        self.terrain_type = (
            TerrainType(terrain_type)
            if isinstance(terrain_type, str)
            else terrain_type
        )
        self.terrain_difficulty = float(np.clip(terrain_difficulty, 0.0, 1.0))
        self.realistic_servos = bool(realistic_servos)
        self.domain_randomization = bool(domain_randomization)
        self.enable_pushes = bool(enable_pushes)
        self.use_tof_grid = bool(use_tof_grid)
        self.resample_command_steps = int(resample_command_steps)

        # Step count & episode tracking
        self.step_count = 0
        self.prev_action = np.zeros(18, dtype=np.float32)
        self.current_cmd = np.zeros(3, dtype=np.float32)  # [vx, vy, wz]
        self._next_push_step = 0
        self._nominal_base_mass = 0.722

        # PyBullet Client & IDs
        self.client_id = -1
        self.robot_id = -1
        self.terrain: Optional[TerrainGenerator] = None
        self.joint_indices: Dict[str, int] = {}
        self.joint_index_list: List[int] = []
        self.foot_link_indices: List[int] = []
        self.nominal_standing_angles = np.zeros(18, dtype=np.float32)

        # Actuator model (Reely NR-645 MG BB)
        self.actuator = ServoActuatorModel(
            joint_names=JOINT_NAMES,
            config=actuator_config,
            realistic_dynamics=self.realistic_servos,
        )

        # Gait Engine (v2 bionic ant stance defaults)
        self.gait = OmniGait(
            gait_type=GaitType.TRIPOD,
            walk_x=0.0,
            walk_y=0.0,
            step_length=40.0,
            step_height=30.0,
            gait_speed=1.0,
            smooth_transitions=True,
        )

        # Observation Space:
        # [proj_gravity(3), ang_vel_base(3), q_diff(18), q_dot_est(18),
        #  foot_contacts(6), gait_phase(2), cmd(3), prev_action(18)] = 71 dims
        # Optional +9 dims for 3x3 belly VL53L5CX ToF distance grid
        obs_dim = 3 + 3 + 18 + 18 + 6 + 2 + 3 + 18 + (9 if self.use_tof_grid else 0)
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32
        )

        # Action Space: 18 continuous outputs in [-1.0, 1.0]
        self.action_space = spaces.Box(
            low=-1.0, high=1.0, shape=(18,), dtype=np.float32
        )

        # Initialize PyBullet simulation
        self._init_pybullet()
        self._compute_standing_posture()

    def set_difficulty(self, difficulty: float) -> float:
        """
        Updates the curriculum difficulty scalar in `[0.0, 1.0]` for subsequent episodes.
        Designed for `VecEnv.env_method("set_difficulty", value)`.
        """
        self.terrain_difficulty = float(np.clip(difficulty, 0.0, 1.0))
        return self.terrain_difficulty

    def _init_pybullet(self) -> None:
        """Initializes PyBullet physics client, procedural terrain, and v2 robot URDF."""
        if self.render_mode == "human":
            self.client_id = p.connect(p.GUI)
            p.configureDebugVisualizer(
                p.COV_ENABLE_GUI, 0, physicsClientId=self.client_id
            )
            p.resetDebugVisualizerCamera(
                cameraDistance=0.65,
                cameraYaw=45,
                cameraPitch=-25,
                cameraTargetPosition=[0, 0, 0.10],
                physicsClientId=self.client_id,
            )
        else:
            self.client_id = p.connect(p.DIRECT)

        p.setAdditionalSearchPath(
            pybullet_data.getDataPath(), physicsClientId=self.client_id
        )
        p.setGravity(0, 0, -9.81, physicsClientId=self.client_id)
        p.setTimeStep(self.physics_dt, physicsClientId=self.client_id)

        # Terrain (plane.urdf for flat, reusable GEOM_HEIGHTFIELD for uneven modes)
        self.terrain = TerrainGenerator(
            client_id=self.client_id,
            terrain_type=self.terrain_type,
            lateral_friction=self.lateral_friction,
        )

        # Robot URDF (body_assembly.FCStd — chassis + 6 legs, no head/gaster)
        start_pos = [0.0, 0.0, 0.098]
        start_orn = p.getQuaternionFromEuler(
            [0.0, 0.0, 0.0], physicsClientId=self.client_id
        )
        self.robot_id = p.loadURDF(
            self.urdf_path,
            start_pos,
            start_orn,
            flags=p.URDF_USE_INERTIA_FROM_FILE,
            physicsClientId=self.client_id,
        )

        # Record nominal base_link mass for mass domain randomization
        base_dyn = p.getDynamicsInfo(self.robot_id, -1, physicsClientId=self.client_id)
        self._nominal_base_mass = float(base_dyn[0])

        # Map revolute joints and foot contact links
        foot_map: Dict[str, int] = {}
        num_joints = p.getNumJoints(self.robot_id, physicsClientId=self.client_id)
        for i in range(num_joints):
            info = p.getJointInfo(self.robot_id, i, physicsClientId=self.client_id)
            j_name = info[1].decode("utf-8")
            link_name = info[12].decode("utf-8")
            if j_name in JOINT_NAMES:
                self.joint_indices[j_name] = i
                p.changeDynamics(
                    self.robot_id,
                    i,
                    lateralFriction=self.lateral_friction,
                    physicsClientId=self.client_id,
                )
            if link_name in FOOT_LINK_NAMES:
                foot_map[link_name] = i
                p.changeDynamics(
                    self.robot_id,
                    i,
                    lateralFriction=1.8,
                    contactStiffness=30000.0,
                    contactDamping=1000.0,
                    physicsClientId=self.client_id,
                )

        self.joint_index_list = [self.joint_indices[name] for name in JOINT_NAMES]
        self.foot_link_indices = [foot_map[name] for name in FOOT_LINK_NAMES]

    def _compute_standing_posture(self) -> None:
        """Computes reference URDF joint angles for neutral v2 bionic ant stance."""
        self.gait.set_velocity(0.0, 0.0, 0.0, immediate=True)
        coords = self.gait.tick()
        self.nominal_standing_angles = self._coords_to_urdf_angles(coords)

    @staticmethod
    def _coords_to_urdf_angles(
        coords: Dict[LegIdentifier, Tuple[float, float, float]],
    ) -> np.ndarray:
        """Converts leg-frame Cartesian foot targets (mm) to 18 URDF radians."""
        angles = np.zeros(18, dtype=np.float32)
        idx = 0
        for leg_id, _, _ in LEG_ORDER:
            x, y, z = coords[leg_id]
            c_deg, f_deg, t_deg = calculate_leg_ik(
                x, y, z, coxa_len=56.5, femur_len=100.0, tibia_len=152.6
            )
            angles[idx] = math.radians(-c_deg)
            angles[idx + 1] = math.radians(-f_deg)
            angles[idx + 2] = math.radians(t_deg + 90.0)
            idx += 3
        return angles

    def _sample_command(self, immediate: bool = False) -> None:
        """Samples or applies the target velocity command [vx, vy, wz] and configures OmniGait."""
        if self.fixed_command is not None:
            self.current_cmd = np.array(self.fixed_command, dtype=np.float32)
        else:
            # 10% standing balance / disturbance rejection episodes
            if float(self.np_random.random()) < 0.10:
                self.current_cmd = np.zeros(3, dtype=np.float32)
            else:
                self.current_cmd = np.array(
                    [
                        self.np_random.uniform(-0.04, MAX_CMD_VX),
                        self.np_random.uniform(-0.045, 0.045),
                        self.np_random.uniform(-0.22, 0.22),
                    ],
                    dtype=np.float32,
                )

        # Calibrated sign-consistent mapping to OmniGait:
        #   URDF +X forward -> OmniGait +walk_y
        #   URDF +Y left    -> OmniGait -walk_x (OmniGait +walk_x strafes right!)
        #   URDF +Z CCW yaw -> OmniGait +turn_z
        walk_y = float(np.clip(self.current_cmd[0] / MAX_CMD_VX, -1.0, 1.0))
        walk_x = float(np.clip(-self.current_cmd[1] / MAX_CMD_VY, -1.0, 1.0))
        turn_z = float(np.clip(self.current_cmd[2] / MAX_CMD_WZ, -1.0, 1.0))
        self.gait.set_velocity(
            walk_x=walk_x, walk_y=walk_y, turn_z=turn_z, immediate=immediate
        )

    def _apply_domain_randomization(self) -> float:
        """Randomizes ground/foot friction and chassis mass for the episode."""
        if not self.domain_randomization:
            p.changeDynamics(
                self.robot_id,
                -1,
                mass=self._nominal_base_mass,
                physicsClientId=self.client_id,
            )
            for f_idx in self.foot_link_indices:
                p.changeDynamics(
                    self.robot_id,
                    f_idx,
                    lateralFriction=1.8,
                    physicsClientId=self.client_id,
                )
            return self.lateral_friction

        ground_friction = float(self.np_random.uniform(0.7, 1.6))
        foot_friction = float(self.np_random.uniform(1.2, 2.2))
        mass_scale = float(self.np_random.uniform(0.85, 1.15))

        p.changeDynamics(
            self.robot_id,
            -1,
            mass=self._nominal_base_mass * mass_scale,
            physicsClientId=self.client_id,
        )
        for f_idx in self.foot_link_indices:
            p.changeDynamics(
                self.robot_id,
                f_idx,
                lateralFriction=foot_friction,
                physicsClientId=self.client_id,
            )
        return ground_friction

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)

        if options and "difficulty" in options:
            self.set_difficulty(float(options["difficulty"]))

        self.step_count = 0
        self.prev_action = np.zeros(18, dtype=np.float32)

        # 1. Domain randomization & terrain generation
        ground_friction = self._apply_domain_randomization()
        active_terrain = self.terrain.reset(
            difficulty=self.terrain_difficulty,
            rng=self.np_random,
            lateral_friction=ground_friction,
        )

        # 2. Sample velocity command and randomize initial gait phase (when not fixed)
        self.gait.phase = (
            0.0 if self.fixed_command is not None else float(self.np_random.uniform(0.0, 1.0))
        )
        self._sample_command(immediate=True)

        # 3. Reset robot pose cleanly above local terrain surface
        if self.fixed_command is not None and not self.domain_randomization:
            start_x, start_y, yaw_noise = 0.0, 0.0, 0.0
        else:
            pos_noise = self.np_random.uniform(-0.02, 0.02, size=2)
            start_x, start_y = float(pos_noise[0]), float(pos_noise[1])
            yaw_noise = float(self.np_random.uniform(-math.pi, math.pi))

        spawn_ground_z = self.terrain.get_local_max_height(start_x, start_y, radius_m=0.22)
        start_pos = [start_x, start_y, spawn_ground_z + TARGET_CLEARANCE_M + 0.005]
        start_orn = p.getQuaternionFromEuler(
            [0.0, 0.0, yaw_noise], physicsClientId=self.client_id
        )
        p.resetBasePositionAndOrientation(
            self.robot_id, start_pos, start_orn, physicsClientId=self.client_id
        )
        p.resetBaseVelocity(
            self.robot_id, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], physicsClientId=self.client_id
        )

        # 4. Reset joints & servo actuator lag state
        self.actuator.reset(
            initial_angles=self.nominal_standing_angles,
            rng=self.np_random,
            randomize=self.domain_randomization,
        )
        for idx, j_idx in enumerate(self.joint_index_list):
            q_ref = float(self.nominal_standing_angles[idx])
            p.resetJointState(
                self.robot_id, j_idx, q_ref, 0.0, physicsClientId=self.client_id
            )

        # Hold standing posture briefly so feet settle cleanly on terrain
        forces, _, kp, kd = self.actuator.get_motor_params()
        p.setJointMotorControlArray(
            self.robot_id,
            self.joint_index_list,
            p.POSITION_CONTROL,
            targetPositions=self.nominal_standing_angles.tolist(),
            forces=forces.tolist(),
            positionGains=[kp] * 18,
            velocityGains=[kd] * 18,
            physicsClientId=self.client_id,
        )
        for _ in range(15):
            p.stepSimulation(physicsClientId=self.client_id)

        # Re-sync finite-difference potentiometer memory to settled joint angles
        true_q = self._read_true_joint_positions()
        self.actuator._last_measured_q = true_q.copy()

        # Schedule next push perturbation
        self._next_push_step = int(self.np_random.integers(120, 220))

        obs = self._get_observation()
        info = {
            "command": self.current_cmd.copy(),
            "terrain_mode": active_terrain.value,
            "difficulty": self.terrain_difficulty,
            **self.actuator.get_summary(),
        }
        return obs, info

    def _maybe_apply_push(self) -> bool:
        """Applies an external lateral disturbance impulse to the chassis for robustness."""
        if not self.enable_pushes:
            return False
        if self.step_count < self._next_push_step:
            return False

        self._next_push_step = self.step_count + int(self.np_random.integers(150, 260))

        # Scale impulse gently with difficulty (minimum baseline push if difficulty == 0)
        strength = 0.35 + 0.65 * self.terrain_difficulty
        lin_vel, ang_vel = p.getBaseVelocity(
            self.robot_id, physicsClientId=self.client_id
        )
        push_dir = float(self.np_random.uniform(0.0, 2.0 * math.pi))
        dv_xy = float(self.np_random.uniform(0.05, 0.14)) * strength
        dw_xy = float(self.np_random.uniform(-0.25, 0.25)) * strength

        new_lin = [
            lin_vel[0] + dv_xy * math.cos(push_dir),
            lin_vel[1] + dv_xy * math.sin(push_dir),
            lin_vel[2],
        ]
        new_ang = [
            ang_vel[0] + dw_xy,
            ang_vel[1] - dw_xy * 0.5,
            ang_vel[2],
        ]
        p.resetBaseVelocity(
            self.robot_id, new_lin, new_ang, physicsClientId=self.client_id
        )
        return True

    def step(
        self, action: np.ndarray
    ) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        self.step_count += 1
        action = np.clip(action, -1.0, 1.0).astype(np.float32)

        # Optional mid-episode command change during training
        if (
            self.fixed_command is None
            and self.resample_command_steps > 0
            and self.step_count % self.resample_command_steps == 0
        ):
            self._sample_command(immediate=False)

        # 1. Compute target joint angles (URDF radians)
        if self.action_mode == "residual":
            coords = self.gait.tick()
            nominal_angles = self._coords_to_urdf_angles(coords)
            target_angles = nominal_angles + action * self.residual_joint_limit
        else:
            # Direct joint control relative to neutral standing posture
            self.gait.tick()
            target_angles = self.nominal_standing_angles + action * 0.40

        # 2. Apply optional lateral push disturbance
        pushed = self._maybe_apply_push()

        # 3. Sub-step physics at 250 Hz with realistic servo lag & torque limits
        forces, _, kp, kd = self.actuator.get_motor_params()
        forces_list = forces.tolist()
        kp_list = [kp] * 18
        kd_list = [kd] * 18

        for _ in range(self.substeps):
            filtered_targets = self.actuator.step_substep(
                target_angles, self.physics_dt
            )
            p.setJointMotorControlArray(
                self.robot_id,
                self.joint_index_list,
                p.POSITION_CONTROL,
                targetPositions=filtered_targets.tolist(),
                forces=forces_list,
                positionGains=kp_list,
                velocityGains=kd_list,
                physicsClientId=self.client_id,
            )
            p.stepSimulation(physicsClientId=self.client_id)

        # 4. Read updated observations (real-sensor-faithful)
        obs = self._get_observation()

        # 5. Compute reward, termination & truncation
        terminated, term_info = self._check_termination()
        reward, reward_info = self._compute_reward(action, terminated=terminated)
        truncated = self.step_count >= self.max_episode_steps

        self.prev_action = action.copy()

        info = {
            "step": self.step_count,
            "command": self.current_cmd.copy(),
            "terrain_mode": self.terrain.active_mode.value,
            "difficulty": self.terrain_difficulty,
            "pushed": pushed,
            **reward_info,
            **term_info,
        }

        return obs, reward, terminated, truncated, info

    def _read_true_joint_positions(self) -> np.ndarray:
        """Reads true joint angles (18,) from PyBullet in one batch call."""
        states = p.getJointStates(
            self.robot_id, self.joint_index_list, physicsClientId=self.client_id
        )
        return np.array([s[0] for s in states], dtype=np.float32)

    def _read_true_joint_velocities(self) -> np.ndarray:
        """Reads true joint angular velocities (18,) from PyBullet in one batch call."""
        states = p.getJointStates(
            self.robot_id, self.joint_index_list, physicsClientId=self.client_id
        )
        return np.array([s[1] for s in states], dtype=np.float32)

    def _read_foot_contacts(self) -> np.ndarray:
        """
        Reads binary ground contact signals `{0.0, 1.0}` for the 6 Tarsus foot links,
        matching the 6 Omron D2F-L foot microswitches (`ADS1115 A3`, trigger > 0.4 N).
        """
        contacts = np.zeros(6, dtype=np.float32)
        pts = p.getContactPoints(
            bodyA=self.robot_id,
            bodyB=self.terrain.body_id,
            physicsClientId=self.client_id,
        )
        if not pts:
            return contacts

        # Map PyBullet linkIndexA -> leg index 0..5
        link_to_leg = {link_idx: i for i, link_idx in enumerate(self.foot_link_indices)}
        for cp in pts:
            link_a = cp[3]
            normal_force = cp[9]
            if link_a in link_to_leg and normal_force > 0.4:
                contacts[link_to_leg[link_a]] = 1.0
        return contacts

    def _read_belly_tof_grid(self, pos: Tuple[float, float, float], rot_matrix: np.ndarray) -> np.ndarray:
        """
        Simulates a 3x3 downsampled VL53L5CX belly-mounted ToF distance sensor (meters, clipped [0, 0.30]).
        Mounted under belly pan at local (-0.0585, 0.0, -0.004) m pointing along base -Z.
        """
        origin_local = np.array([-0.0585, 0.0, -0.004], dtype=np.float64)
        base_pos = np.array(pos, dtype=np.float64)
        ray_from = []
        ray_to = []
        max_range = 0.30
        angles = (-0.28, 0.0, 0.28)  # ~±16 deg FoV
        for ax in angles:
            for ay in angles:
                d_local = np.array([math.sin(ax), math.sin(ay), -1.0], dtype=np.float64)
                d_local /= np.linalg.norm(d_local)
                p0 = base_pos + rot_matrix @ origin_local
                p1 = p0 + (rot_matrix @ d_local) * max_range
                ray_from.append(p0.tolist())
                ray_to.append(p1.tolist())

        results = p.rayTestBatch(ray_from, ray_to, physicsClientId=self.client_id)
        dists = np.array([r[2] * max_range for r in results], dtype=np.float32)
        if self.domain_randomization:
            dists = np.clip(
                dists + self.np_random.normal(0.0, 0.004, size=9).astype(np.float32),
                0.0,
                max_range,
            )
        return dists

    def _get_observation(self) -> np.ndarray:
        """Constructs the real-sensor-faithful observation vector (71 dims, or 80 with ToF)."""
        pos, orn = p.getBasePositionAndOrientation(
            self.robot_id, physicsClientId=self.client_id
        )
        _, ang_vel_world = p.getBaseVelocity(
            self.robot_id, physicsClientId=self.client_id
        )

        rot_matrix = np.array(
            p.getMatrixFromQuaternion(orn), dtype=np.float64
        ).reshape(3, 3)

        # 1. BNO085 IMU: projected gravity (3) + angular velocity in base frame (3)
        proj_gravity = (rot_matrix.T @ np.array([0.0, 0.0, -1.0])).astype(np.float32)
        ang_vel_base = (rot_matrix.T @ np.array(ang_vel_world)).astype(np.float32)

        if self.domain_randomization:
            proj_gravity += self.np_random.normal(0.0, 0.015, size=3).astype(np.float32)
            g_norm = float(np.linalg.norm(proj_gravity))
            if g_norm > 1e-6:
                proj_gravity /= g_norm
            ang_vel_base += self.np_random.normal(0.0, 0.04, size=3).astype(np.float32)

        # 2. ADS1115 Servo Potentiometers: measured joint offsets (18) + estimated velocities (18)
        true_q = self._read_true_joint_positions()
        meas_q, est_q_dot = self.actuator.measure_joints(
            true_positions=true_q,
            dt_control=self.dt,
            rng=self.np_random,
            add_noise=self.domain_randomization,
        )
        joint_pos_diff = meas_q - self.nominal_standing_angles

        # 3. Tarsus Foot Microswitches (6)
        foot_contacts = self._read_foot_contacts()

        # 4. OmniGait Phase Encoding (2)
        phase_rad = 2.0 * math.pi * float(self.gait.phase)
        gait_phase = np.array(
            [math.sin(phase_rad), math.cos(phase_rad)], dtype=np.float32
        )

        parts = [
            proj_gravity,
            ang_vel_base,
            joint_pos_diff,
            est_q_dot,
            foot_contacts,
            gait_phase,
            self.current_cmd.astype(np.float32),
            self.prev_action.astype(np.float32),
        ]
        if self.use_tof_grid:
            parts.append(self._read_belly_tof_grid(pos, rot_matrix))

        return np.concatenate(parts).astype(np.float32)

    def _compute_reward(
        self, action: np.ndarray, terminated: bool = False
    ) -> Tuple[float, Dict[str, float]]:
        """Calculates multi-objective locomotion reward using privileged PyBullet ground truth."""
        pos, orn = p.getBasePositionAndOrientation(
            self.robot_id, physicsClientId=self.client_id
        )
        rpy = p.getEulerFromQuaternion(orn)
        lin_vel_world, ang_vel_world = p.getBaseVelocity(
            self.robot_id, physicsClientId=self.client_id
        )

        rot_matrix = np.array(
            p.getMatrixFromQuaternion(orn), dtype=np.float64
        ).reshape(3, 3)
        lin_vel_base = rot_matrix.T @ np.array(lin_vel_world)
        ang_vel_base = rot_matrix.T @ np.array(ang_vel_world)

        # 1. Linear velocity tracking calibrated to Lasius v2 speed envelope (sigma = 0.05 m/s)
        cmd_vx, cmd_vy, cmd_wz = self.current_cmd
        vel_err_sq = (lin_vel_base[0] - cmd_vx) ** 2 + (lin_vel_base[1] - cmd_vy) ** 2
        r_lin = math.exp(-vel_err_sq / 0.0025)

        # 2. Angular yaw-rate tracking (sigma = 0.20 rad/s)
        ang_err_sq = (ang_vel_base[2] - cmd_wz) ** 2
        r_ang = math.exp(-ang_err_sq / 0.04)

        # 3. Posture & upright stability: penalize roll and pitch (sigma = 0.20 rad ≈ 11.5°)
        tilt_sq = rpy[0] ** 2 + rpy[1] ** 2
        r_upright = math.exp(-tilt_sq / 0.04)

        # 4. Relative height clearance above local terrain surface (target 0.093 m)
        ground_z = self.terrain.get_height(pos[0], pos[1])
        z_rel = pos[2] - ground_z
        z_err_sq = (z_rel - TARGET_CLEARANCE_M) ** 2
        r_height = math.exp(-z_err_sq / 0.001)

        # 5. Stability & Sim-to-Real smoothness penalties
        vz_sq = float(lin_vel_base[2] ** 2)
        rp_rate_sq = float(ang_vel_base[0] ** 2 + ang_vel_base[1] ** 2)
        action_diff_sq = float(np.sum((action - self.prev_action) ** 2))
        action_norm_sq = float(np.sum(action ** 2))
        true_q_dot = self._read_true_joint_velocities()
        joint_vel_sq = float(np.sum(true_q_dot ** 2))

        total_reward = (
            1.4 * r_lin
            + 0.7 * r_ang
            + 0.5 * r_upright
            + 0.4 * r_height
            - 0.40 * vz_sq
            - 0.05 * rp_rate_sq
            - 0.03 * action_diff_sq
            - 0.005 * action_norm_sq
            - 0.0005 * joint_vel_sq
        )

        if terminated:
            total_reward -= 5.0

        contacts = self._read_foot_contacts()
        reward_breakdown = {
            "reward_total": float(total_reward),
            "reward_lin": float(r_lin),
            "reward_ang": float(r_ang),
            "reward_upright": float(r_upright),
            "reward_height": float(r_height),
            "penalty_action_diff": action_diff_sq,
            "penalty_joint_vel": joint_vel_sq,
            "vx_base": float(lin_vel_base[0]),
            "vy_base": float(lin_vel_base[1]),
            "wz_base": float(ang_vel_base[2]),
            "z_rel": float(z_rel),
            "max_tilt_deg": float(math.degrees(max(abs(rpy[0]), abs(rpy[1])))),
            "foot_contact_count": int(np.sum(contacts)),
        }
        return float(total_reward), reward_breakdown

    def _check_termination(self) -> Tuple[bool, Dict[str, bool]]:
        """Checks whether robot belly collapsed onto local terrain or flipped over."""
        pos, orn = p.getBasePositionAndOrientation(
            self.robot_id, physicsClientId=self.client_id
        )
        rpy = p.getEulerFromQuaternion(orn)

        ground_z = self.terrain.get_height(pos[0], pos[1])
        z_rel = pos[2] - ground_z

        chassis_drop = z_rel < DROP_TERMINATION_CLEARANCE_M
        excessive_tilt = (
            abs(rpy[0]) > TILT_TERMINATION_RAD or abs(rpy[1]) > TILT_TERMINATION_RAD
        )

        terminated = bool(chassis_drop or excessive_tilt)
        term_info = {
            "term_chassis_drop": bool(chassis_drop),
            "term_excessive_tilt": bool(excessive_tilt),
        }
        return terminated, term_info

    def render(self):
        """Renders RGB frames when `render_mode='rgb_array'`."""
        if self.render_mode == "rgb_array":
            pos, _ = p.getBasePositionAndOrientation(
                self.robot_id, physicsClientId=self.client_id
            )
            view_matrix = p.computeViewMatrixFromYawPitchRoll(
                cameraTargetPosition=pos,
                distance=0.6,
                yaw=45,
                pitch=-30,
                roll=0,
                upAxisIndex=2,
                physicsClientId=self.client_id,
            )
            proj_matrix = p.computeProjectionMatrixFOV(
                fov=60,
                aspect=1.0,
                nearVal=0.1,
                farVal=2.0,
                physicsClientId=self.client_id,
            )
            (_, _, px, _, _) = p.getCameraImage(
                width=320,
                height=320,
                viewMatrix=view_matrix,
                projectionMatrix=proj_matrix,
                renderer=p.ER_BULLET_HARDWARE_OPENGL,
                physicsClientId=self.client_id,
            )
            rgb_array = np.array(px, dtype=np.uint8).reshape((320, 320, 4))[:, :, :3]
            return rgb_array
        return None

    def close(self) -> None:
        """Disconnects PyBullet physics client."""
        if self.client_id >= 0 and p is not None:
            if p.isConnected(physicsClientId=self.client_id):
                p.disconnect(physicsClientId=self.client_id)
            self.client_id = -1
