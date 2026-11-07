/**
 * CAD Geometries & Analytical Profiles (`lasius-dashboard/src/engine/cadGeometries.ts`).
 *
 * Reverse-engineered from FreeCAD models and manufacturing specifications:
 * - Chassis Bottom / Top Plates: body_bottom.FCStd / body_top.FCStd (2.0 mm solid)
 * - Standoff Spacer Pillars: spacer_14x50.FCStd (Ø 14.0 mm x 51.3 mm)
 * - Coxa Bracket: coxa_bracket.FCStd (115 mm length, 31.7 mm width, stabilization cheeks)
 * - Femur Side Plates: femur_plate.FCStd (100 mm pitch, 31.6 mm width, 51.3 mm spacing)
 * - Tibia Claw: tibia.FCStd (130 mm pitch, 7.0 mm solid, analytical sickle contour)
 * - Master Assembly: body_assembly.FCStd (142 parts, mirrored right legs)
 */

import chassisContourData from './chassis_contour.json';
import tibiaContourData from './tibia_contour.json';

export interface Point2D {
  x: number;
  y: number;
}

/**
 * 125-point analytic outer contour of the chassis plates (body_bottom / body_top).
 * Coordinate system (Dashboard):
 * - X: Lateral axis (Left: -88.4 mm .. Right: +88.4 mm across ears)
 * - Y: Longitudinal axis (Front: -135.0 mm .. Rear: +132.0 mm)
 */
export const CHASSIS_HULL_CONTOUR: Point2D[] = chassisContourData as Point2D[];

/**
 * Central electronics cutout window (50.0 mm x 160.0 mm).
 */
export const CHASSIS_WINDOW_CUTOUT = {
  width: 50.0,   // x: -25.0 .. +25.0 mm
  length: 160.0, // y: -80.0 .. +80.0 mm
  cornerRadius: 4.0
};

/**
 * 6x Coxa rotation axis mounting hole locations (Ø 8.0 mm).
 */
export const CHASSIS_COXA_HOLES: Point2D[] = [
  { x: -65.0, y: -86.0 }, // Left Front (FL)
  { x:  65.0, y: -86.0 }, // Right Front (FR)
  { x: -75.0, y:   0.0 }, // Left Middle (LM)
  { x:  75.0, y:   0.0 }, // Right Middle (RM)
  { x: -65.0, y:  86.0 }, // Left Rear (RL)
  { x:  65.0, y:  86.0 }  // Right Rear (RR)
];

/**
 * 8x Chassis standoff spacer pillar positions (Ø 14.0 mm, L = 51.3 mm).
 * The 2 front standoffs are placed side-by-side (transverse) at y = -128.0 mm.
 * The 2 rear standoffs are placed inline along the longitudinal centerline at y = +90.0 and +120.0 mm.
 */
export const CHASSIS_STANDOFF_POSITIONS: Point2D[] = [
  // 4x Central electronics window flanking standoffs
  { x: -30.0, y: -45.0 },
  { x:  30.0, y: -45.0 },
  { x: -30.0, y:  45.0 },
  { x:  30.0, y:  45.0 },
  // 2x Front standoffs (side-by-side)
  { x: -12.0, y: -128.0 },
  { x:  12.0, y: -128.0 },
  // 2x Rear centerline standoffs (inline)
  { x:   0.0, y:   90.0 },
  { x:   0.0, y:  120.0 }
];

/**
 * Physical chassis plate sandwich dimensions.
 */
export const CHASSIS_SPECS = {
  plateThickness: 2.0,       // 2.0 mm solid carbon fiber / aluminum
  standoffHeight: 51.3,      // 51.3 mm standoff gap between bottom and top plates
  standoffDiameter: 14.0,    // Ø 14.0 mm standoff spacer rods
  standoffRadius: 7.0,
  topPlateCenterY: 26.65,    // spans +25.65 mm to +27.65 mm
  bottomPlateCenterY: -26.65 // spans -27.65 mm to -25.65 mm
};

/**
 * Femur dual-plate cage dimensions.
 */
export const FEMUR_SPECS = {
  length: 100.0,             // 100.0 mm kinematic inter-axis pitch (hip to knee)
  width: 31.6,               // 31.6 mm stadium width (end radius R = 15.8 mm)
  radius: 15.8,
  totalLength: 131.6,        // 131.6 mm overall plate length
  thickness: 2.2,            // 2.2 mm plate thickness
  plateSpacing: 51.3,        // 51.3 mm inner gap between front and rear plates
  standoffDiameter: 14.0,    // Ø 14.0 mm standoffs connecting femur plates
  standoffRadius: 7.0,
  standoff1_X: 35.0,         // Standoff 1 at x = 35.0 mm
  standoff2_X: 65.0          // Standoff 2 at x = 65.0 mm
};

/**
 * Coxa bracket structural dimensions.
 */
export const COXA_SPECS = {
  totalLength: 115.0,        // 115.0 mm overall length
  inwardExtension: 40.3,     // extends 40.3 mm inward into chassis interior (-x)
  outwardExtension: 74.7,    // extends 74.7 mm outward to outer tip (+x)
  kinematicLength: 60.0,     // 60.0 mm nominal pivot-to-hip pitch
  width: 31.7,               // 31.7 mm outer width across servo casing & side rails
  mainHeight: 18.0,          // 18.0 mm main casing height (y = -9.0 .. +9.0)
  cheekHeight: 26.3,         // 26.3 mm stabilization cheek height (y = -13.15 .. +13.15)
  lowerTabDepth: 14.5,       // extends to y = -14.5 mm for femur counter-bearing
  pivotBearingDia: 8.0,      // Ø 8.0 mm x 3.0 mm ball bearing
  pivotPinDia: 4.2           // Ø 4.2 mm rotation pivot pin
};

/**
 * Tibia sickle limb contour & specs.
 */
export const TIBIA_SPECS = {
  kinematicLength: 130.0,    // 130.0 mm kinematic length from knee pivot to foot tip
  thickness: 7.0,            // 7.0 mm solid limb thickness (spans z = -3.5 .. +3.5 mm)
  outerPolygon: (tibiaContourData as any).outer as [number, number][],
  slotPolygon: (tibiaContourData as any).slot as [number, number][],
  footTip: (tibiaContourData as any).tip as [number, number]
};

/**
 * Standard metal-gear servo dimensions (Torcster NR-645 MG BB / Hitec HS-645MG).
 */
export const SERVO_SPECS = {
  length: 40.2,
  width: 20.1,
  height: 39.5,
  shaftOffset: 10.0,         // shaft center distance from servo end
  hornDiameter: 22.0
};
