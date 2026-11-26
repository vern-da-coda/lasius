"""
Procedural PyBullet Terrain Generator (`lasius.core.sim.terrain`).

Purpose & Role:
    Generates flat, rough, sloped, stepped, or mixed terrains in PyBullet using
    reusable `GEOM_HEIGHTFIELD` collision shapes (in-place updates via
    `replaceHeightfieldIndex` to prevent memory leaks across thousands of RL
    episodes) and provides fast O(1) bilinear ground-height queries for:
    - Safe robot spawning above local terrain surface
    - Relative belly-clearance reward calculation on hills/ramps/steps
    - Progressive Curriculum Learning via `difficulty in [0.0, 1.0]`.
"""

from __future__ import annotations

from enum import Enum
import math
from typing import Optional

import numpy as np

try:
    import pybullet as p
except ImportError:
    p = None


class TerrainType(str, Enum):
    """Supported procedural terrain modes for LasiusGymEnv."""
    FLAT = "flat"
    ROUGH = "rough"
    SLOPES = "slopes"
    STEPS = "steps"
    MIXED = "mixed"


class TerrainGenerator:
    """
    Manages the PyBullet ground body and local height queries.

    For `TerrainType.FLAT`, loads the lightweight `plane.urdf`.
    For uneven terrain modes (`rough`, `slopes`, `steps`, `mixed`), maintains a
    persistent heightfield shape centered at world `(0, 0)` and updates its
    elevation grid in-place on `reset()` without reallocating physics shapes.
    """

    def __init__(
        self,
        client_id: int,
        terrain_type: TerrainType | str = TerrainType.FLAT,
        grid_size: int = 81,
        cell_size_m: float = 0.04,
        max_rough_amplitude_m: float = 0.032,
        max_slope_deg: float = 11.0,
        max_step_height_m: float = 0.022,
        lateral_friction: float = 1.2,
    ):
        if p is None:
            raise ImportError("PyBullet is required for TerrainGenerator.")

        self.client_id = client_id
        self.terrain_type = (
            TerrainType(terrain_type)
            if isinstance(terrain_type, str)
            else terrain_type
        )
        # Odd grid size guarantees an exact center vertex at world (0, 0)
        self.grid_size = grid_size if grid_size % 2 == 1 else grid_size + 1
        self.cell_size_m = float(cell_size_m)
        self.half_extent_m = 0.5 * (self.grid_size - 1) * self.cell_size_m

        self.max_rough_amplitude_m = float(max_rough_amplitude_m)
        self.max_slope_deg = float(max_slope_deg)
        self.max_step_height_m = float(max_step_height_m)
        self.lateral_friction = float(lateral_friction)

        self.body_id: int = -1
        self.shape_id: int = -1
        self.active_mode: TerrainType = self.terrain_type
        self.current_difficulty: float = 0.0

        # Elevation grid in world meters: shape (rows=Y, cols=X), row 0 = -half_extent
        self.heights = np.zeros((self.grid_size, self.grid_size), dtype=np.float32)

        # Precompute centered grid coordinates in meters
        coords = np.linspace(
            -self.half_extent_m, self.half_extent_m, self.grid_size, dtype=np.float32
        )
        self._grid_x, self._grid_y = np.meshgrid(coords, coords)  # shape (rows, cols)

        self._build_initial_ground()

    def _build_initial_ground(self) -> None:
        """Creates either `plane.urdf` (flat) or the initial reusable heightfield body."""
        if self.terrain_type == TerrainType.FLAT:
            self.body_id = p.loadURDF("plane.urdf", physicsClientId=self.client_id)
            self.set_friction(self.lateral_friction)
            return

        # Create reusable heightfield body initialized to flat zeros
        self.heights.fill(0.0)
        self.shape_id = p.createCollisionShape(
            shapeType=p.GEOM_HEIGHTFIELD,
            meshScale=[self.cell_size_m, self.cell_size_m, 1.0],
            heightfieldTextureScaling=(self.grid_size - 1) / 2.0,
            heightfieldData=self.heights.ravel().tolist(),
            numHeightfieldRows=self.grid_size,
            numHeightfieldColumns=self.grid_size,
            physicsClientId=self.client_id,
        )
        self.body_id = p.createMultiBody(
            baseMass=0.0,
            baseCollisionShapeIndex=self.shape_id,
            basePosition=[0.0, 0.0, 0.0],
            physicsClientId=self.client_id,
        )
        p.changeVisualShape(
            self.body_id,
            -1,
            rgbaColor=[0.42, 0.45, 0.40, 1.0],
            physicsClientId=self.client_id,
        )
        self.set_friction(self.lateral_friction)

    def set_friction(self, lateral_friction: float) -> None:
        """Updates ground Coulomb friction."""
        self.lateral_friction = float(lateral_friction)
        if self.body_id >= 0:
            p.changeDynamics(
                self.body_id,
                -1,
                lateralFriction=self.lateral_friction,
                physicsClientId=self.client_id,
            )

    def reset(
        self,
        difficulty: float,
        rng: np.random.Generator,
        lateral_friction: Optional[float] = None,
    ) -> TerrainType:
        """
        Regenerates the terrain surface for a new episode at the given difficulty [0, 1].

        Returns:
            The concrete `TerrainType` active for this episode.
        """
        self.current_difficulty = float(np.clip(difficulty, 0.0, 1.0))

        if lateral_friction is not None:
            self.set_friction(lateral_friction)

        if self.terrain_type == TerrainType.FLAT:
            self.active_mode = TerrainType.FLAT
            return self.active_mode

        # Choose active sub-mode for mixed terrain
        if self.terrain_type == TerrainType.MIXED:
            if self.current_difficulty <= 0.02:
                mode = TerrainType.FLAT
            else:
                choices = [TerrainType.ROUGH, TerrainType.SLOPES, TerrainType.STEPS]
                mode = choices[int(rng.integers(0, len(choices)))]
        else:
            mode = self.terrain_type

        self.active_mode = mode

        if mode == TerrainType.FLAT or self.current_difficulty <= 1e-4:
            raw_h = np.zeros((self.grid_size, self.grid_size), dtype=np.float32)
        elif mode == TerrainType.ROUGH:
            raw_h = self._generate_rough(self.current_difficulty, rng)
        elif mode == TerrainType.SLOPES:
            raw_h = self._generate_slope(self.current_difficulty, rng)
        elif mode == TerrainType.STEPS:
            raw_h = self._generate_steps(self.current_difficulty, rng)
        else:
            raw_h = np.zeros((self.grid_size, self.grid_size), dtype=np.float32)

        # Shift so the center spawn point (0, 0) is near z = 0.0
        center = self.grid_size // 2
        raw_h = raw_h - float(raw_h[center, center])

        # Apply smooth spawn-pad blending only for steps (keeps robot feet clean at t=0)
        if mode == TerrainType.STEPS:
            dist_center = np.hypot(self._grid_x, self._grid_y)
            blend = np.clip((dist_center - 0.22) / 0.12, 0.0, 1.0).astype(np.float32)
            raw_h = raw_h * blend

        self.heights = raw_h.astype(np.float32)

        # Update PyBullet heightfield in-place.
        # Because the initial heightfield was created centered at z=0 with
        # zero heights, `replaceHeightfieldIndex` keeps the local frame origin
        # at z=0 so `basePosition = [0, 0, 0]` aligns the physical collision
        # surface directly with world elevation `self.heights[r, c]`.
        self.shape_id = p.createCollisionShape(
            shapeType=p.GEOM_HEIGHTFIELD,
            meshScale=[self.cell_size_m, self.cell_size_m, 1.0],
            heightfieldTextureScaling=(self.grid_size - 1) / 2.0,
            heightfieldData=self.heights.ravel().tolist(),
            numHeightfieldRows=self.grid_size,
            numHeightfieldColumns=self.grid_size,
            replaceHeightfieldIndex=self.shape_id,
            physicsClientId=self.client_id,
        )
        p.resetBasePositionAndOrientation(
            self.body_id,
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
            physicsClientId=self.client_id,
        )
        return self.active_mode

    def _generate_rough(
        self, difficulty: float, rng: np.random.Generator
    ) -> np.ndarray:
        """Multi-octave smooth sinusoidal undulations + fine micro-roughness."""
        amp = self.max_rough_amplitude_m * difficulty
        h = np.zeros_like(self._grid_x, dtype=np.float32)

        # Sum 5 random directional wave octaves (wavelengths ~0.35 m to 1.6 m)
        for freq_scale, weight in [
            (0.6, 0.40),
            (1.1, 0.28),
            (1.8, 0.16),
            (2.8, 0.10),
            (4.2, 0.06),
        ]:
            theta = float(rng.uniform(0.0, 2.0 * math.pi))
            phase = float(rng.uniform(0.0, 2.0 * math.pi))
            kx = 2.0 * math.pi * freq_scale * math.cos(theta)
            ky = 2.0 * math.pi * freq_scale * math.sin(theta)
            h += (weight * amp) * np.sin(kx * self._grid_x + ky * self._grid_y + phase)

        # Add light pebble micro-noise (<= 3.5 mm at difficulty=1.0)
        h += rng.uniform(-0.11 * amp, 0.11 * amp, size=h.shape).astype(np.float32)
        return h

    def _generate_slope(
        self, difficulty: float, rng: np.random.Generator
    ) -> np.ndarray:
        """Uniform inclined plane in a random azimuth direction + light texture."""
        slope_deg = float(rng.uniform(0.4, 1.0)) * self.max_slope_deg * difficulty
        tan_slope = math.tan(math.radians(slope_deg))
        azimuth = float(rng.uniform(0.0, 2.0 * math.pi))
        h = tan_slope * (
            math.cos(azimuth) * self._grid_x + math.sin(azimuth) * self._grid_y
        )
        # Tiny surface roughness (<= 3 mm) so flat ramp still feels realistic
        h += rng.uniform(-0.003 * difficulty, 0.003 * difficulty, size=h.shape)
        return h.astype(np.float32)

    def _generate_steps(
        self, difficulty: float, rng: np.random.Generator
    ) -> np.ndarray:
        """Discrete flat stepping stones / terrace tiles scaled by difficulty."""
        step_h = self.max_step_height_m * difficulty
        # Coarse 0.28 m x 0.28 m blocks (~7 cells)
        block_cells = max(4, int(round(0.28 / self.cell_size_m)))
        n_blocks = int(math.ceil(self.grid_size / block_cells))
        levels = rng.choice([-1.0, 0.0, 0.0, 1.0], size=(n_blocks, n_blocks))
        coarse = (levels * step_h).astype(np.float32)
        tiled = np.repeat(np.repeat(coarse, block_cells, axis=0), block_cells, axis=1)
        return tiled[: self.grid_size, : self.grid_size]

    def get_height(self, x: float, y: float) -> float:
        """
        Fast O(1) bilinear interpolation of terrain surface elevation Z (meters) at world `(x, y)`.
        """
        if self.terrain_type == TerrainType.FLAT:
            return 0.0

        fx = (x + self.half_extent_m) / self.cell_size_m
        fy = (y + self.half_extent_m) / self.cell_size_m

        max_idx = self.grid_size - 1
        fx = min(max(fx, 0.0), float(max_idx))
        fy = min(max(fy, 0.0), float(max_idx))

        c0 = int(math.floor(fx))
        r0 = int(math.floor(fy))
        c1 = min(c0 + 1, max_idx)
        r1 = min(r0 + 1, max_idx)

        tx = fx - c0
        ty = fy - r0

        h00 = float(self.heights[r0, c0])
        h10 = float(self.heights[r0, c1])
        h01 = float(self.heights[r1, c0])
        h11 = float(self.heights[r1, c1])

        h0 = h00 * (1.0 - tx) + h10 * tx
        h1 = h01 * (1.0 - tx) + h11 * tx
        return h0 * (1.0 - ty) + h1 * ty

    def get_local_max_height(self, x: float, y: float, radius_m: float = 0.22) -> float:
        """
        Returns maximum terrain elevation across center + 6 surrounding points at `radius_m`,
        ensuring safe non-penetrating robot spawns on uneven ground.
        """
        if self.terrain_type == TerrainType.FLAT:
            return 0.0

        max_z = self.get_height(x, y)
        for k in range(6):
            ang = k * (math.pi / 3.0)
            z_pt = self.get_height(
                x + radius_m * math.cos(ang),
                y + radius_m * math.sin(ang),
            )
            if z_pt > max_z:
                max_z = z_pt
        return max_z
