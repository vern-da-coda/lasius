"""
Lasius Hexapod Gymnasium Reinforcement Learning Environment (`LasiusGymEnv`).

Purpose & Role:
    Standard Gymnasium environment wrapping PyBullet physics for training
    locomotion policies (PPO, SAC) on the 18-DOF Lasius Hexapod robot.
    Supports both Residual RL (learning additive offsets on top of analytical
    OmniGait trajectory) and Direct Joint Control.

Observation Space (66 dims):
    - Projected gravity vector in robot base frame: [gx, gy, gz] (3)
    - Base linear velocity in base frame: [vx, vy, vz] (3)
    - Base angular velocity in base frame: [wx, wy, wz] (3)
    - Joint position offsets relative to standing posture: theta - theta_stand (18)
    - Joint angular velocities: theta_dot (18)
    - Velocity commands: [cmd_vx, cmd_vy, cmd_wz] (3)
    - Previous action: a_{t-1} (18)

Action Space (18 dims):
    Continuous Box([-1.0, 1.0], shape=(18,)) representing scaled joint offsets
    (Residual mode, default) or target joint angles (Direct mode).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import gymnasium as gym
from gymnasium import spaces
import numpy as np

try:
    import pybullet as p
    import pybullet_data
except ImportError:
    p = None
    pybullet_data = None

from lasius.core.motion.gait import OmniGait, GaitType, LegIdentifier
from lasius.core.motion.kinematics import calculate_leg_ik


def _find_repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".git").is_dir() or (parent / "hardware" / "mechanics").is_dir():
            return parent
    return current.parents[6]


DEFAULT_URDF_PATH = _find_repo_root() / "hardware" / "mechanics" / "export" / "urdf" / "lasius.urdf"

# Canonical leg and joint ordering (18 joints)
LEG_ORDER = [
    (LegIdentifier.LEFT_FRONT, "left_front"),
    (LegIdentifier.LEFT_MIDDLE, "left_middle"),
    (LegIdentifier.LEFT_REAR, "left_rear"),
    (LegIdentifier.RIGHT_FRONT, "right_front"),
    (LegIdentifier.RIGHT_MIDDLE, "right_middle"),
    (LegIdentifier.RIGHT_REAR, "right_rear"),
]

JOINT_NAMES = []
for _, prefix in LEG_ORDER:
    JOINT_NAMES.extend([f"{prefix}_coxa", f"{prefix}_femur", f"{prefix}_tibia"])


class LasiusGymEnv(gym.Env):
    """
    Gymnasium Environment for Lasius Hexapod Locomotion.
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
    ):
        super().__init__()

        if p is None:
            raise ImportError(
                "PyBullet is required for LasiusGymEnv. Install via 'pip install pybullet'."
            )

        self.urdf_path = str(urdf_path or DEFAULT_URDF_PATH)
        if not Path(self.urdf_path).is_file():
            raise FileNotFoundError(f"Lasius URDF model not found at '{self.urdf_path}'.")

        assert action_mode in ["residual", "direct"], f"Invalid action_mode: {action_mode}"
        self.action_mode = action_mode
        self.render_mode = render_mode
        self.control_freq = control_freq
        self.physics_freq = physics_freq
        self.dt = 1.0 / control_freq
        self.substeps = int(physics_freq / control_freq)
        self.max_episode_steps = max_episode_steps
        self.residual_joint_limit = residual_joint_limit
        self.lateral_friction = lateral_friction
        self.fixed_command = fixed_command

        # Step count & tracking
        self.step_count = 0
        self.prev_action = np.zeros(18, dtype=np.float32)
        self.current_cmd = np.zeros(3, dtype=np.float32)  # [vx, vy, wz]

        # PyBullet Client & IDs
        self.client_id = -1
        self.robot_id = -1
        self.plane_id = -1
        self.joint_indices: Dict[str, int] = {}
        self.nominal_standing_angles = np.zeros(18, dtype=np.float32)

        # Gait Engine
        self.gait = OmniGait(
            gait_type=GaitType.TRIPOD,
            walk_y=0.0,
            step_length=35.0,
            step_height=20.0,
            gait_speed=1.0,
        )

        # Observation Space: 66 continuous features
        # [gx, gy, gz (3), vx, vy, vz (3), wx, wy, wz (3), q_diff (18), q_dot (18), cmd (3), prev_a (18)]
        obs_dim = 3 + 3 + 3 + 18 + 18 + 3 + 18
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

    def _init_pybullet(self):
        """Initializes PyBullet physics client and loads plane & robot."""
        if self.render_mode == "human":
            self.client_id = p.connect(p.GUI)
            p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0, physicsClientId=self.client_id)
            p.resetDebugVisualizerCamera(
                cameraDistance=0.65,
                cameraYaw=45,
                cameraPitch=-25,
                cameraTargetPosition=[0, 0, 0.10],
                physicsClientId=self.client_id,
            )
        else:
            self.client_id = p.connect(p.DIRECT)

        p.setAdditionalSearchPath(pybullet_data.getDataPath(), physicsClientId=self.client_id)
        p.setGravity(0, 0, -9.81, physicsClientId=self.client_id)
        p.setTimeStep(1.0 / self.physics_freq, physicsClientId=self.client_id)

        # Plane
        self.plane_id = p.loadURDF("plane.urdf", physicsClientId=self.client_id)
        p.changeDynamics(
            self.plane_id, -1, lateralFriction=self.lateral_friction, physicsClientId=self.client_id
        )

        # Robot URDF
        start_pos = [0, 0, 0.161]
        start_orn = p.getQuaternionFromEuler([0, 0, 0], physicsClientId=self.client_id)
        self.robot_id = p.loadURDF(
            self.urdf_path,
            start_pos,
            start_orn,
            flags=p.URDF_USE_INERTIA_FROM_FILE,
            physicsClientId=self.client_id,
        )

        # Map revolute joints
        num_joints = p.getNumJoints(self.robot_id, physicsClientId=self.client_id)
        for i in range(num_joints):
            info = p.getJointInfo(self.robot_id, i, physicsClientId=self.client_id)
            j_name = info[1].decode("utf-8")
            if j_name in JOINT_NAMES:
                self.joint_indices[j_name] = i
                # Set joint friction & dynamics
                p.changeDynamics(
                    self.robot_id, i, lateralFriction=self.lateral_friction, physicsClientId=self.client_id
                )

    def _compute_standing_posture(self):
        """Computes reference joint angles for neutral standing posture."""
        self.gait.walk_x = 0.0
        self.gait.walk_y = 0.0
        self.gait.turn_z = 0.0
        coords = self.gait.tick()

        idx = 0
        for leg_id, prefix in LEG_ORDER:
            x, y, z = coords[leg_id]
            c_deg, f_deg, t_deg = calculate_leg_ik(
                x, y, z, coxa_len=56.5, femur_len=100.0, tibia_len=130.0
            )
            self.nominal_standing_angles[idx] = math.radians(c_deg)
            self.nominal_standing_angles[idx + 1] = math.radians(f_deg)
            self.nominal_standing_angles[idx + 2] = math.radians(t_deg)
            idx += 3

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)

        self.step_count = 0
        self.prev_action = np.zeros(18, dtype=np.float32)

        # Sample velocity command [vx, vy, wz]
        if self.fixed_command is not None:
            self.current_cmd = np.array(self.fixed_command, dtype=np.float32)
        else:
            # Sample realistic velocity range:
            # vx in [-0.05, 0.15] m/s, vy in [-0.08, 0.08] m/s, wz in [-0.4, 0.4] rad/s
            self.current_cmd = np.array(
                [
                    self.np_random.uniform(-0.05, 0.15),
                    self.np_random.uniform(-0.08, 0.08),
                    self.np_random.uniform(-0.4, 0.4),
                ],
                dtype=np.float32,
            )

        # Configure gait engine
        self.gait.walk_x = float(self.current_cmd[1]) / 0.10  # Normalized lateral strafe
        self.gait.walk_y = float(self.current_cmd[0]) / 0.15  # Normalized forward walk
        self.gait.turn_z = float(self.current_cmd[2]) / 0.50  # Normalized yaw turn
        self.gait.tick_counter = 0

        # Reset robot position & orientation with slight noise
        pos_noise = self.np_random.uniform(-0.01, 0.01, size=2)
        start_pos = [pos_noise[0], pos_noise[1], 0.161]
        yaw_noise = self.np_random.uniform(-0.1, 0.1)
        start_orn = p.getQuaternionFromEuler([0, 0, yaw_noise], physicsClientId=self.client_id)
        p.resetBasePositionAndOrientation(
            self.robot_id, start_pos, start_orn, physicsClientId=self.client_id
        )
        p.resetBaseVelocity(
            self.robot_id, [0, 0, 0], [0, 0, 0], physicsClientId=self.client_id
        )

        # Reset joint positions to standing stance
        idx = 0
        for name in JOINT_NAMES:
            j_idx = self.joint_indices[name]
            q_ref = float(self.nominal_standing_angles[idx])
            p.resetJointState(self.robot_id, j_idx, q_ref, 0.0, physicsClientId=self.client_id)
            idx += 1

        # Settle robot for a few physics steps
        for _ in range(10):
            p.stepSimulation(physicsClientId=self.client_id)

        obs = self._get_observation()
        info = {"command": self.current_cmd.copy()}
        return obs, info

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        self.step_count += 1
        action = np.clip(action, -1.0, 1.0).astype(np.float32)

        # 1. Compute target joint angles
        if self.action_mode == "residual":
            coords = self.gait.tick()
            nominal_angles = np.zeros(18, dtype=np.float32)
            idx = 0
            for leg_id, prefix in LEG_ORDER:
                x, y, z = coords[leg_id]
                c_deg, f_deg, t_deg = calculate_leg_ik(
                    x, y, z, coxa_len=56.5, femur_len=100.0, tibia_len=130.0
                )
                nominal_angles[idx] = math.radians(c_deg)
                nominal_angles[idx + 1] = math.radians(f_deg)
                nominal_angles[idx + 2] = math.radians(t_deg)
                idx += 3

            # Add scaled residual offsets
            target_angles = nominal_angles + action * self.residual_joint_limit
        else:
            # Direct joint control relative to nominal standing stance
            target_angles = self.nominal_standing_angles + action * 0.40

        # 2. Apply motor commands in PyBullet
        idx = 0
        for name in JOINT_NAMES:
            j_idx = self.joint_indices[name]
            p.setJointMotorControl2(
                self.robot_id,
                j_idx,
                p.POSITION_CONTROL,
                targetPosition=float(target_angles[idx]),
                force=8.0,
                physicsClientId=self.client_id,
            )
            idx += 1

        # 3. Step physics simulation (substeps)
        for _ in range(self.substeps):
            p.stepSimulation(physicsClientId=self.client_id)

        # 4. Get updated state & observation
        obs = self._get_observation()

        # 5. Calculate reward, termination & truncation
        reward, reward_info = self._compute_reward(action)
        terminated, term_info = self._check_termination()
        truncated = self.step_count >= self.max_episode_steps

        self.prev_action = action.copy()

        info = {
            "step": self.step_count,
            "command": self.current_cmd.copy(),
            **reward_info,
            **term_info,
        }

        return obs, reward, terminated, truncated, info

    def _get_observation(self) -> np.ndarray:
        """Constructs the 66-dimensional observation vector."""
        # Base pose & velocity
        pos, orn = p.getBasePositionAndOrientation(self.robot_id, physicsClientId=self.client_id)
        lin_vel_world, ang_vel_world = p.getBaseVelocity(
            self.robot_id, physicsClientId=self.client_id
        )

        rot_matrix = np.array(p.getMatrixFromQuaternion(orn)).reshape(3, 3)

        # Projected gravity in base frame (R^T * [0, 0, -1])
        proj_gravity = rot_matrix.T @ np.array([0.0, 0.0, -1.0])

        # Velocities in base frame
        lin_vel_base = rot_matrix.T @ np.array(lin_vel_world)
        ang_vel_base = rot_matrix.T @ np.array(ang_vel_world)

        # Joint positions and velocities
        joint_positions = np.zeros(18, dtype=np.float32)
        joint_velocities = np.zeros(18, dtype=np.float32)
        idx = 0
        for name in JOINT_NAMES:
            j_idx = self.joint_indices[name]
            state = p.getJointState(self.robot_id, j_idx, physicsClientId=self.client_id)
            joint_positions[idx] = state[0]
            joint_velocities[idx] = state[1]
            idx += 1

        joint_pos_diff = joint_positions - self.nominal_standing_angles

        # Observation concatenation: 3 + 3 + 3 + 18 + 18 + 3 + 18 = 66 dims
        obs = np.concatenate(
            [
                proj_gravity.astype(np.float32),
                lin_vel_base.astype(np.float32),
                ang_vel_base.astype(np.float32),
                joint_pos_diff.astype(np.float32),
                joint_velocities.astype(np.float32),
                self.current_cmd.astype(np.float32),
                self.prev_action.astype(np.float32),
            ]
        )
        return obs

    def _compute_reward(self, action: np.ndarray) -> Tuple[float, Dict[str, float]]:
        """Calculates multi-objective locomotion reward."""
        pos, orn = p.getBasePositionAndOrientation(self.robot_id, physicsClientId=self.client_id)
        rpy = p.getEulerFromQuaternion(orn)
        lin_vel_world, ang_vel_world = p.getBaseVelocity(
            self.robot_id, physicsClientId=self.client_id
        )

        rot_matrix = np.array(p.getMatrixFromQuaternion(orn)).reshape(3, 3)
        lin_vel_base = rot_matrix.T @ np.array(lin_vel_world)
        ang_vel_base = rot_matrix.T @ np.array(ang_vel_world)

        # 1. Linear velocity tracking: vx (forward), vy (lateral)
        cmd_vx, cmd_vy, cmd_wz = self.current_cmd
        vel_err_sq = (lin_vel_base[0] - cmd_vx) ** 2 + (lin_vel_base[1] - cmd_vy) ** 2
        r_lin = math.exp(-vel_err_sq / 0.10)

        # 2. Angular velocity tracking: wz (yaw rate)
        ang_err_sq = (ang_vel_base[2] - cmd_wz) ** 2
        r_ang = math.exp(-ang_err_sq / 0.10)

        # 3. Posture & Upright stability: penalize roll (phi) and pitch (theta)
        tilt_sq = rpy[0] ** 2 + rpy[1] ** 2
        r_upright = math.exp(-tilt_sq / 0.05)

        # 4. Height maintenance: target standing height ~0.161 m
        z_err_sq = (pos[2] - 0.161) ** 2
        r_height = math.exp(-z_err_sq / 0.002)

        # 5. Action smoothness penalty: ||a_t - a_{t-1}||^2
        action_diff_sq = float(np.sum((action - self.prev_action) ** 2))

        # 6. Joint velocity / Energy penalty
        joint_vel_sq = 0.0
        for name in JOINT_NAMES:
            j_idx = self.joint_indices[name]
            state = p.getJointState(self.robot_id, j_idx, physicsClientId=self.client_id)
            joint_vel_sq += state[1] ** 2

        # Weighted total reward
        total_reward = (
            1.2 * r_lin
            + 0.6 * r_ang
            + 0.4 * r_upright
            + 0.4 * r_height
            - 0.05 * action_diff_sq
            - 0.001 * joint_vel_sq
        )

        reward_breakdown = {
            "reward_total": total_reward,
            "reward_lin": r_lin,
            "reward_ang": r_ang,
            "reward_upright": r_upright,
            "reward_height": r_height,
            "penalty_action_diff": action_diff_sq,
            "penalty_joint_vel": joint_vel_sq,
        }
        return float(total_reward), reward_breakdown

    def _check_termination(self) -> Tuple[bool, Dict[str, bool]]:
        """Checks if robot fell over or dropped excessively."""
        pos, orn = p.getBasePositionAndOrientation(self.robot_id, physicsClientId=self.client_id)
        rpy = p.getEulerFromQuaternion(orn)

        chassis_drop = pos[2] < 0.09  # Robot chassis dragging on ground
        excessive_tilt = abs(rpy[0]) > 0.65 or abs(rpy[1]) > 0.65  # ~37 deg tilt

        terminated = chassis_drop or excessive_tilt
        term_info = {
            "term_chassis_drop": chassis_drop,
            "term_excessive_tilt": excessive_tilt,
        }
        return terminated, term_info

    def render(self):
        """Renders frames if rgb_array is requested."""
        if self.render_mode == "rgb_array":
            pos, _ = p.getBasePositionAndOrientation(self.robot_id, physicsClientId=self.client_id)
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
                fov=60, aspect=1.0, nearVal=0.1, farVal=2.0, physicsClientId=self.client_id
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

    def close(self):
        """Disconnects PyBullet physics server."""
        if self.client_id >= 0 and p is not None:
            if p.isConnected(physicsClientId=self.client_id):
                p.disconnect(physicsClientId=self.client_id)
            self.client_id = -1
