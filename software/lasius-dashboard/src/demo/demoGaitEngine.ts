/**
 * Standalone Client-Side 50 Hz Gait Simulation & Inverse Kinematics Engine
 * (`lasius-dashboard/src/engine/demoGaitEngine.ts`).
 *
 * Purpose & Role:
 *   High-fidelity TypeScript port of the Python `OmniGait` and `calculate_leg_ik` solver.
 *   Enables the 3D Digital Twin and 2D Orthographic projections to walk, strafe, turn,
 *   and tilt when deployed in standalone mode on static webservers (e.g. Plesk / GitHub Pages)
 *   without an active WebSocket connection to a physical Raspberry Pi backend.
 *
 * Capabilities:
 *   - Omnidirectional translation (walk_x strafe, walk_y forward/backward, turn_z yaw)
 *   - Multi-gait coordination (Tripod, Ripple, Wave)
 *   - Seamless S-curve gait morphing & shortest-arc circular phase interpolation
 *   - Harmonic cosine stance & swing foot trajectories (C^1 continuous zero-velocity liftoff & touchdown)
 *   - Dynamic 6-DOF body attitude posing (ground clearance -120..-40mm, roll ±25°, pitch ±25°)
 *   - Velocity ramping & slew-rate limiting (prevents visual or kinematic jumps)
 *   - Closed-form 3-DOF inverse kinematics (Law of Cosines) for insectoid leg geometry
 */

import type { LegKey, GaitPattern, RobotLayout } from '../types';
import { DEFAULT_ROBOT_LAYOUT } from '../engine/constants';

export interface LegStance {
  x: number;
  y: number;
  z: number;
}

export interface MountPoint {
  x: number;
  y: number;
}

export interface JointAngles {
  coxa: number;
  femur: number;
  tibia: number;
}

/**
 * Default robot chassis mount points (mm) relative to chassis center.
 * Front/Rear: x = ±65 mm, y = ±86 mm. Middle: x = ±75 mm, y = 0 mm.
 */
export const DEFAULT_MOUNT_POINTS: Record<LegKey, MountPoint> = {
  left_front: { x: -65.0, y: -86.0 },
  left_middle: { x: -75.0, y: 0.0 },
  left_rear: { x: -65.0, y: 86.0 },
  right_front: { x: 65.0, y: -86.0 },
  right_middle: { x: 75.0, y: 0.0 },
  right_rear: { x: 65.0, y: 86.0 }
};

/**
 * Natural neutral standing foot coordinates (mm) in local leg frames.
 * Tailored for 60 mm Coxa, 100 mm Femur, 130 mm Tibia at -80 mm ground clearance.
 */
export const DEFAULT_NEUTRAL_STANCES: Record<LegKey, LegStance> = {
  left_front: { x: 140.0, y: 70.0, z: -80.0 },
  left_middle: { x: 160.0, y: 0.0, z: -80.0 },
  left_rear: { x: 160.0, y: 0.0, z: -80.0 },
  right_front: { x: 140.0, y: -70.0, z: -80.0 },
  right_middle: { x: 160.0, y: 0.0, z: -80.0 },
  right_rear: { x: 160.0, y: 0.0, z: -80.0 }
};

interface GaitTimingConfig {
  swingDuration: number;
  phaseOffsets: Record<LegKey, number>;
}

export const GAIT_CONFIGS: Record<GaitPattern, GaitTimingConfig> = {
  tripod: {
    swingDuration: 0.5,
    phaseOffsets: {
      left_front: 0.0,
      right_middle: 0.0,
      left_rear: 0.0,
      right_front: 0.5,
      left_middle: 0.5,
      right_rear: 0.5
    }
  },
  ripple: {
    swingDuration: 1.0 / 3.0,
    phaseOffsets: {
      left_rear: 0.0 / 6.0,
      right_front: 1.0 / 6.0,
      left_middle: 2.0 / 6.0,
      right_rear: 3.0 / 6.0,
      left_front: 4.0 / 6.0,
      right_middle: 5.0 / 6.0
    }
  },
  wave: {
    swingDuration: 1.0 / 6.0,
    phaseOffsets: {
      left_rear: 0.0 / 6.0,
      left_middle: 1.0 / 6.0,
      left_front: 2.0 / 6.0,
      right_rear: 3.0 / 6.0,
      right_middle: 4.0 / 6.0,
      right_front: 5.0 / 6.0
    }
  }
};

/**
 * Calculates 3-DOF inverse kinematics for an insectoid leg link chain.
 *
 * Args:
 *   x: Foot tip X-coordinate relative to leg origin (mm).
 *   y: Foot tip Y-coordinate relative to leg origin (mm).
 *   z: Foot tip Z-coordinate relative to leg origin (mm, typically negative when touching ground).
 *   coxaLen: Coxa link length (default 60 mm).
 *   femurLen: Femur link length (default 100 mm).
 *   tibiaLen: Tibia link length (default 130 mm).
 *
 * Returns:
 *   { coxa, femur, tibia } angles in degrees.
 */
export function calculateLegIK(
  x: number,
  y: number,
  z: number,
  coxaLen = 60.0,
  femurLen = 100.0,
  tibiaLen = 130.0
): JointAngles {
  // 1. Coxa Angle (Top-down view)
  const coxa = (Math.atan2(y, x) * 180) / Math.PI;

  // 2. Reduce to 2D planar side-view
  const lHoriz = Math.hypot(x, y);
  const xPrime = lHoriz - coxaLen;
  const yPrime = -z; // positive downwards when z is negative

  let distFemurTip = Math.hypot(xPrime, yPrime);
  const maxReach = femurLen + tibiaLen;

  // Soft reach clamp to prevent domain errors / NaN if outside workspace
  let xp = xPrime;
  let yp = yPrime;
  if (distFemurTip > maxReach - 0.001) {
    const scale = (maxReach - 0.001) / distFemurTip;
    xp *= scale;
    yp *= scale;
    distFemurTip = maxReach - 0.001;
  }

  // 3. Knee bend angle (Law of Cosines)
  let tibiaAngleArg = (femurLen ** 2 + tibiaLen ** 2 - distFemurTip ** 2) / (2.0 * femurLen * tibiaLen);
  tibiaAngleArg = Math.max(-1.0, Math.min(1.0, tibiaAngleArg));
  const alphaRad = Math.acos(tibiaAngleArg);
  const kneeBendDeg = ((Math.PI - alphaRad) * 180) / Math.PI;

  // Tibia servo angle: relative to a 90° mounting horn (0° servo = 90° knee bend)
  const tibia = kneeBendDeg - 90.0;

  // 4. Femur angle: knee is above hip-to-foot line, so (beta1 - beta2) gives angle above horizontal
  let beta1Arg = (femurLen ** 2 + distFemurTip ** 2 - tibiaLen ** 2) / (2.0 * femurLen * distFemurTip);
  beta1Arg = Math.max(-1.0, Math.min(1.0, beta1Arg));
  const beta1Rad = Math.acos(beta1Arg);
  const beta2Rad = Math.atan2(yp, xp);
  const femur = ((beta1Rad - beta2Rad) * 180) / Math.PI;

  return { coxa, femur, tibia };
}

/**
 * 50 Hz Client-Side Simulation Gait Engine.
 */
export class DemoGaitEngine {
  public stepLength = 50.0;
  public stepHeight = 30.0;
  public gaitSpeed = 1.0;
  public harmonicStance = true;
  public smoothTransitions = true;

  // Locomotion command inputs (-1.0 to +1.0)
  public walkX = 0.0;
  public walkY = 0.0;
  public turnZ = 0.0;

  // Filtered / smoothed motion states
  private currWalkX = 0.0;
  private currWalkY = 0.0;
  private currTurnZ = 0.0;

  // Body attitude targets
  public bodyHeight = -80.0;
  public bodyRoll = 0.0;
  public bodyPitch = 0.0;

  // Filtered / smoothed posture states
  private currBodyHeight = -80.0;
  private currBodyRoll = 0.0;
  private currBodyPitch = 0.0;

  // Gait cycle phase [0.0, 1.0)
  public phase = 0.0;

  // Seamless gait morphing state
  private sourceGait: GaitPattern = 'tripod';
  private targetGait: GaitPattern = 'tripod';
  private transitionProgress = 1.0;

  // Slew-rate limiting position history
  private currentPositions: Partial<Record<LegKey, LegStance>> = {};

  // Chassis geometry & mount points
  public mountPoints: Record<LegKey, MountPoint> = { ...DEFAULT_MOUNT_POINTS };
  public neutralStances: Record<LegKey, LegStance> = { ...DEFAULT_NEUTRAL_STANCES };
  public coxaLen = 60.0;
  public femurLen = 100.0;
  public tibiaLen = 130.0;
  private layout: RobotLayout = DEFAULT_ROBOT_LAYOUT;

  constructor(layout?: RobotLayout) {
    if (layout) {
      this.applyLayout(layout);
    }
    // Initialize current positions to neutral stance
    this.resetToStance();
  }

  public applyLayout(layout: RobotLayout) {
    this.layout = layout;
    if (layout.legs) {
      const allLegs: LegKey[] = ['left_front', 'left_middle', 'left_rear', 'right_front', 'right_middle', 'right_rear'];
      for (const legKey of allLegs) {
        const def = layout.legs[legKey];
        if (def) {
          if (def.mount_point) {
            this.mountPoints[legKey] = { x: def.mount_point.x, y: def.mount_point.y };
          }
          if (def.coxa?.length) this.coxaLen = def.coxa.length;
          if (def.femur?.length) this.femurLen = def.femur.length;
          if (def.tibia?.length) this.tibiaLen = def.tibia.length;
        }
      }
    }
  }

  public setGait(pattern: GaitPattern, smooth = true) {
    if (pattern === this.targetGait && this.transitionProgress >= 1.0) {
      return;
    }
    if (!smooth || !this.smoothTransitions) {
      this.sourceGait = pattern;
      this.targetGait = pattern;
      this.transitionProgress = 1.0;
    } else {
      this.sourceGait = this.targetGait;
      this.targetGait = pattern;
      this.transitionProgress = 0.0;
    }
  }

  public setVelocity(x: number, y: number, turn = 0, immediate = false) {
    this.walkX = Math.max(-1.0, Math.min(1.0, x));
    this.walkY = Math.max(-1.0, Math.min(1.0, y));
    this.turnZ = Math.max(-1.0, Math.min(1.0, turn));
    if (immediate || !this.smoothTransitions) {
      this.currWalkX = this.walkX;
      this.currWalkY = this.walkY;
      this.currTurnZ = this.turnZ;
    }
  }

  public setPose(height: number, roll: number, pitch: number, immediate = false) {
    this.bodyHeight = Math.max(-120.0, Math.min(-40.0, height));
    this.bodyRoll = Math.max(-25.0, Math.min(25.0, roll));
    this.bodyPitch = Math.max(-25.0, Math.min(25.0, pitch));
    if (immediate || !this.smoothTransitions) {
      this.currBodyHeight = this.bodyHeight;
      this.currBodyRoll = this.bodyRoll;
      this.currBodyPitch = this.bodyPitch;
    }
  }

  public resetToStance() {
    this.walkX = 0.0;
    this.walkY = 0.0;
    this.turnZ = 0.0;
    this.currWalkX = 0.0;
    this.currWalkY = 0.0;
    this.currTurnZ = 0.0;
    this.bodyHeight = -80.0;
    this.bodyRoll = 0.0;
    this.bodyPitch = 0.0;
    this.currBodyHeight = -80.0;
    this.currBodyRoll = 0.0;
    this.currBodyPitch = 0.0;
    this.phase = 0.0;

    const allLegs: LegKey[] = ['left_front', 'left_middle', 'left_rear', 'right_front', 'right_middle', 'right_rear'];
    for (const legKey of allLegs) {
      const neutral = this.neutralStances[legKey] || DEFAULT_NEUTRAL_STANCES[legKey];
      this.currentPositions[legKey] = { x: neutral.x, y: neutral.y, z: -80.0 };
    }
  }

  /**
   * Returns target joint angles for the standard neutral standing stance.
   */
  public getInitialStanceAngles(): Record<string, number> {
    const allLegs: LegKey[] = ['left_front', 'left_middle', 'left_rear', 'right_front', 'right_middle', 'right_rear'];
    const anglesOut: Record<string, number> = {};
    for (const legKey of allLegs) {
      const neutral = this.neutralStances[legKey] || DEFAULT_NEUTRAL_STANCES[legKey];
      const ik = calculateLegIK(neutral.x, neutral.y, neutral.z, this.coxaLen, this.femurLen, this.tibiaLen);
      const legDef = this.layout.legs?.[legKey];
      const coxaName = legDef?.coxa?.name || `${legKey}_coxa`;
      const femurName = legDef?.femur?.name || `${legKey}_femur`;
      const tibiaName = legDef?.tibia?.name || `${legKey}_tibia`;
      anglesOut[coxaName] = Number(ik.coxa.toFixed(2));
      anglesOut[femurName] = Number(ik.femur.toFixed(2));
      anglesOut[tibiaName] = Number(ik.tibia.toFixed(2));
    }
    return anglesOut;
  }

  private getInterpolatedGaitParameters(): { swingFrac: number; phaseOffsets: Record<LegKey, number> } {
    if (this.transitionProgress >= 1.0) {
      const cfg = GAIT_CONFIGS[this.targetGait] || GAIT_CONFIGS.tripod;
      return { swingFrac: cfg.swingDuration, phaseOffsets: cfg.phaseOffsets };
    }

    // S-curve easing: zero jerk at boundary transitions
    const s = 0.5 * (1.0 - Math.cos(Math.PI * this.transitionProgress));
    const srcCfg = GAIT_CONFIGS[this.sourceGait] || GAIT_CONFIGS.tripod;
    const tgtCfg = GAIT_CONFIGS[this.targetGait] || GAIT_CONFIGS.tripod;

    const swingFrac = srcCfg.swingDuration + s * (tgtCfg.swingDuration - srcCfg.swingDuration);
    const phaseOffsets = {} as Record<LegKey, number>;

    const allLegs: LegKey[] = ['left_front', 'left_middle', 'left_rear', 'right_front', 'right_middle', 'right_rear'];
    for (const leg of allLegs) {
      const srcOff = srcCfg.phaseOffsets[leg] ?? 0.0;
      const tgtOff = tgtCfg.phaseOffsets[leg] ?? 0.0;
      // Shortest difference on unit circle [-0.5, +0.5]
      const diff = ((tgtOff - srcOff + 0.5) % 1.0) - 0.5;
      phaseOffsets[leg] = (srcOff + s * diff + 1.0) % 1.0;
    }

    return { swingFrac, phaseOffsets };
  }

  private getLegStanceZ(legKey: LegKey, roll: number, pitch: number, height: number): number {
    const mp = this.mountPoints[legKey] || DEFAULT_MOUNT_POINTS[legKey];
    const rollRad = (roll * Math.PI) / 180.0;
    const pitchRad = (pitch * Math.PI) / 180.0;
    const zOffset = mp.x * Math.sin(rollRad) + mp.y * Math.sin(pitchRad);
    return height + zOffset;
  }

  /**
   * Advances the simulation by one 50 Hz tick (20 ms).
   * Returns a map of servo names to computed target angles (in degrees).
   */
  public tick(): Record<string, number> {
    // 1. Inertial velocity and attitude smoothing
    if (this.smoothTransitions) {
      const rate = 0.20;
      this.currWalkX += (this.walkX - this.currWalkX) * rate;
      this.currWalkY += (this.walkY - this.currWalkY) * rate;
      this.currTurnZ += (this.turnZ - this.currTurnZ) * rate;

      this.currBodyHeight += (this.bodyHeight - this.currBodyHeight) * rate;
      this.currBodyRoll += (this.bodyRoll - this.currBodyRoll) * rate;
      this.currBodyPitch += (this.bodyPitch - this.currBodyPitch) * rate;

      if (this.transitionProgress < 1.0) {
        this.transitionProgress = Math.min(1.0, this.transitionProgress + 0.02 * this.gaitSpeed);
      }
    } else {
      this.currWalkX = this.walkX;
      this.currWalkY = this.walkY;
      this.currTurnZ = this.turnZ;
      this.currBodyHeight = this.bodyHeight;
      this.currBodyRoll = this.bodyRoll;
      this.currBodyPitch = this.bodyPitch;
      this.transitionProgress = 1.0;
    }

    const { swingFrac, phaseOffsets } = this.getInterpolatedGaitParameters();

    // Check locomotion activity
    const effectiveSpeed = Math.hypot(this.currWalkX, this.currWalkY, this.currTurnZ * 0.75);
    const isMoving = effectiveSpeed > 0.01;

    if (isMoving) {
      this.phase = (this.phase + 0.02 * this.gaitSpeed) % 1.0;
    }

    // World displacement components
    const dxWalkW = this.currWalkX * this.stepLength;
    const dyWalkW = -this.currWalkY * this.stepLength;
    const turnStride = this.stepLength * 0.75;

    const allLegs: LegKey[] = ['left_front', 'left_middle', 'left_rear', 'right_front', 'right_middle', 'right_rear'];
    const jointAnglesOut: Record<string, number> = {};

    for (const legKey of allLegs) {
      const neutral = this.neutralStances[legKey] || DEFAULT_NEUTRAL_STANCES[legKey];
      const stanceZ = this.getLegStanceZ(legKey, this.currBodyRoll, this.currBodyPitch, this.currBodyHeight);

      let rawX: number;
      let rawY: number;
      let rawZ: number;

      if (!isMoving) {
        rawX = neutral.x;
        rawY = neutral.y;
        rawZ = stanceZ;
      } else {
        const mp = this.mountPoints[legKey] || DEFAULT_MOUNT_POINTS[legKey];
        const dxTurnW = this.currTurnZ * turnStride * (mp.y / 100.0);
        const dyTurnW = -this.currTurnZ * turnStride * (mp.x / 100.0);

        const totalDxW = dxWalkW + dxTurnW;
        const totalDyW = dyWalkW + dyTurnW;

        const isLeft = legKey.startsWith('left');
        const strideXLeg = isLeft ? -totalDxW : totalDxW;
        const strideYLeg = isLeft ? -totalDyW : totalDyW;

        const offset = phaseOffsets[legKey] ?? 0.0;
        const legPhase = (this.phase + offset) % 1.0;

        let strideNorm: number;
        if (legPhase < swingFrac) {
          const norm = legPhase / swingFrac; // 0.0 to 1.0
          strideNorm = -0.5 * Math.cos(norm * Math.PI);
          rawZ = stanceZ + this.stepHeight * Math.sin(norm * Math.PI);
        } else {
          const norm = (legPhase - swingFrac) / (1.0 - swingFrac); // 0.0 to 1.0
          if (this.harmonicStance) {
            strideNorm = 0.5 * Math.cos(norm * Math.PI);
          } else {
            strideNorm = 0.5 - norm;
          }
          rawZ = stanceZ;
        }

        rawX = neutral.x + strideNorm * strideXLeg;
        rawY = neutral.y + strideNorm * strideYLeg;
      }

      // Slew-rate limiting: cap maximal coordinate jump per tick to ensure smooth visual rendering
      const prev = this.currentPositions[legKey] || { x: rawX, y: rawY, z: rawZ };
      const dx = rawX - prev.x;
      const dy = rawY - prev.y;
      const dz = rawZ - prev.z;
      const dist = Math.hypot(dx, dy, dz);
      const maxJump = 18.0 * Math.max(0.5, this.gaitSpeed);

      let outX = rawX;
      let outY = rawY;
      let outZ = rawZ;
      if (this.smoothTransitions && dist > maxJump && dist > 0.001) {
        const scale = maxJump / dist;
        outX = prev.x + dx * scale;
        outY = prev.y + dy * scale;
        outZ = prev.z + dz * scale;
      }
      this.currentPositions[legKey] = { x: outX, y: outY, z: outZ };

      // Calculate 3-DOF closed-form inverse kinematics
      const ik = calculateLegIK(outX, outY, outZ, this.coxaLen, this.femurLen, this.tibiaLen);

      // Resolve servo naming from robot layout
      const legDef = this.layout.legs?.[legKey];
      const coxaName = legDef?.coxa?.name || `${legKey}_coxa`;
      const femurName = legDef?.femur?.name || `${legKey}_femur`;
      const tibiaName = legDef?.tibia?.name || `${legKey}_tibia`;

      jointAnglesOut[coxaName] = Number(ik.coxa.toFixed(2));
      jointAnglesOut[femurName] = Number(ik.femur.toFixed(2));
      jointAnglesOut[tibiaName] = Number(ik.tibia.toFixed(2));
    }

    return jointAnglesOut;
  }
}
