/**
 * CAD Geometries & Analytical Profiles (`lasius-dashboard/src/engine/cadGeometries.ts`).
 *
 * Synchronized with FreeCAD v2 Hardware-as-Code models (`body_assembly.FCStd` / `leg_assembly.FCStd`):
 * - Inherited Carbon Fiber Chassis Plates: `body_bottom.FCStd` / `body_top.FCStd` (2.0 mm CFRP, Z = 0..2 & 53.3..55.3 mm)
 * - v2 Bionic Monocoque Chassis Core: `chassis_core.FCStd` (replaces v1 standoff pillars, spans 51.3 mm gap)
 * - v2 Belly Pan & Monolithic Draped Canopy: `chassis_belly_pan.FCStd`, `chassis_battery_hatch.FCStd`, `chassis_canopy.FCStd`
 * - v2 Bionic Twin-Cage Coxa: `coxa.FCStd` (unified 45° A-truss cheeks, 2.50 mm central spine, R_FRONT = 4.50 mm)
 * - v2 Bionic Monocoque Femur & Cover: `femur.FCStd` + `femur_cover.FCStd` (100.0 mm pitch, 45° A-truss box girder waist)
 * - v2 Bionic Tibia + 3D-Exoskeleton Tarsus & Kufe Shoe: `tibia.FCStd` + `tibia_cover.FCStd` + `tarsus.FCStd` + `tarsus_shoe.FCStd`
 *   (152.6 mm effective knee-to-sole length, concentric Krallen-Sichel teardrop window, 2.50 mm lower web taper)
 */

import chassisContourData from './chassis_contour.json';
import tibiaContourData from './tibia_contour.json';

export interface Point2D {
  x: number;
  y: number;
}

/**
 * 125-point analytic outer contour of the chassis carbon plates (body_bottom / body_top).
 * Coordinate system (Dashboard):
 * - X: Lateral axis (Left: -88.4 mm .. Right: +88.4 mm across ears)
 * - Y: Longitudinal axis (Front: -135.0 mm .. Rear: +132.0 mm)
 */
export const CHASSIS_HULL_CONTOUR: Point2D[] = chassisContourData as Point2D[];

/**
 * Central electronics & service aperture window (50.0 mm x 160.0 mm).
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
 * 8x M3 Chassis bolting hole positions connecting Carbon Plates to v2 Monocoque Core / Canopy / Belly Pan.
 */
export const CHASSIS_STANDOFF_POSITIONS: Point2D[] = [
  { x: -30.0, y: -45.0 },
  { x:  30.0, y: -45.0 },
  { x: -30.0, y:  45.0 },
  { x:  30.0, y:  45.0 },
  { x: -12.0, y: -128.0 },
  { x:  12.0, y: -128.0 },
  { x:   0.0, y:   90.0 },
  { x:   0.0, y:  120.0 }
];

/**
 * Physical v2 Chassis stack dimensions relative to the Coxa-Femur hip pivot plane (Y_three = 0, Z_fc = +17.25 mm).
 */
export const CHASSIS_SPECS = {
  plateThickness: 2.0,          // 2.0 mm solid carbon fiber plates (body_bottom & body_top)
  standoffHeight: 51.3,         // 51.3 mm vertical core height between bottom and top plates
  standoffDiameter: 14.0,
  standoffRadius: 7.0,
  hipPivotZ_FC: 17.25,          // Z_fc = +17.25 mm in body_assembly.FCStd corresponds to Y_three = 0
  bottomPlateCenterY: -16.25,   // Z_fc = 1.00 mm -> Y_three = -16.25 mm (spans -17.25 to -15.25 mm)
  topPlateCenterY: 37.05,       // Z_fc = 54.30 mm -> Y_three = +37.05 mm (spans +36.05 to +38.05 mm)
  coreCenterY: 10.40,           // Z_fc = 27.65 mm -> Y_three = +10.40 mm (spans -15.25 to +36.05 mm)
  coreWidth: 74.0,              // X: -37.0 .. +37.0 mm
  coreLength: 110.4,            // Z: -54.35 .. +56.02 mm
  bellyPanDepth: 11.5,          // Z_fc = -11.50 .. 0.00 mm -> Y_three = -28.75 .. -17.25 mm
  bellyPanWidth: 79.0,          // X: -39.5 .. +39.5 mm
  bellyPanLength: 176.0,        // Z: -88.0 .. +88.0 mm
  canopyHeight: 26.2,           // Z_fc = 55.30 .. 81.50 mm -> Y_three = +38.05 .. +64.25 mm
  serviceCoverWidth: 57.0,      // X: -28.5 .. +28.5 mm
  serviceCoverLength: 89.0      // Z: -45.5 .. +43.5 mm
};

/**
 * v2 Bionic Monocoque Femur box-girder dimensions (`femur.FCStd` + `femur_cover.FCStd`).
 */
export const FEMUR_SPECS = {
  length: 100.0,                // 100.0 mm kinematic inter-axis pitch (hip to knee)
  width: 31.6,                  // 31.6 mm end hub height (R = 15.8 mm)
  radius: 15.8,
  waistHeight: 23.6,            // Tapered G1 bionic waist height
  totalLength: 131.6,           // 131.6 mm overall length (-15.8 to +115.8 mm)
  boxDepth: 26.0,               // Monocoque box girder depth
  earSpacing: 47.0              // Outer servo ear-to-bearing yoke span
};

/**
 * v2 Bionic Twin-Cage Coxa dimensions (`coxa.FCStd`).
 */
export const COXA_SPECS = {
  totalLength: 115.0,           // 115.0 mm overall length (-40.3 to +74.7 mm)
  inwardExtension: 40.3,
  outwardExtension: 74.7,
  kinematicLength: 60.0,        // 60.0 mm nominal pivot-to-hip pitch (56.5 mm CAD)
  cadKinematicLength: 56.5,
  width: 31.7,                  // 31.7 mm cheek height (Y_cage in [0, 31.7])
  cageSpan: 47.0,               // Twin-cheek span [-14.5 to +32.5 mm]
  pivotBearingDia: 8.0,
  pivotPinDia: 4.2
};

/**
 * v2 Bionic Tibia + 3D-Exoskeleton Tarsus & Compact Kufe Shoe (`tibia.FCStd` + `tarsus.FCStd` + `tarsus_shoe.FCStd`).
 */
export const TIBIA_SPECS = {
  kinematicLength: 152.6,       // 152.56 mm effective length from knee pivot to compact Kufe sole
  thickness: 7.0,               // 7.0 mm dorsal sickle arch & claw thickness (2.50 mm tapered lower web)
  forkThickness: 10.44,         // 10.44 mm distal fork & tarsus root width tapering to 6.40 mm Kufe
  outerPolygon: (tibiaContourData as any).outer as [number, number][],
  slotPolygon: (tibiaContourData as any).slot as [number, number][],
  footTip: (tibiaContourData as any).tip as [number, number]
};

/**
 * Standard metal-gear servo dimensions (Reely / Torcster NR-645 MG BB).
 */
export const SERVO_SPECS = {
  length: 40.2,
  width: 20.1,
  height: 39.5,
  shaftOffset: 10.0,
  hornDiameter: 22.0
};
