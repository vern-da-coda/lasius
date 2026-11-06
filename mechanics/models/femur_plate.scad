// ============================================================================
// Lasius Hexapod — Parametric Femur Side Plate (OpenSCAD)
// Measured from 300 DPI flatbed scan: cad/scans/scan.jpeg
// Coordinate Origin (0, 0): Left (Hip) Servo Pivot Axis
// ============================================================================

$fn = 72;

// --- Geometric Parameters (mm) ---
femur_length         = 100.0;  // Pivot-to-pivot kinematic length
plate_width          = 31.6;   // Stadium width (End radius R = 15.8 mm, total length = 131.6 mm)
plate_thickness      = 2.2;    // Side plate thickness

hub_hole_dia         = 8.0;    // Main servo shaft / bearing boss hole (2x)
horn_bolt_circle_dia = 16.0;   // 4-hole cross pattern bolt circle diameter (±8.0 mm)
horn_hole_dia        = 2.0;    // M2 servo horn mounting screw holes (2x 4)

standoff_1_x         = 35.0;   // First central M3 standoff hole X
standoff_2_x         = 65.0;   // Second central M3 standoff hole X (30.0 mm spacing)
standoff_hole_dia    = 3.0;    // M3 clearance hole (2x)

module femur_plate_2d() {
    difference() {
        // Outer stadium / capsule contour (131.6 mm x 31.6 mm)
        hull() {
            translate([0, 0])            circle(d = plate_width);
            translate([femur_length, 0]) circle(d = plate_width);
        }

        // Two Servo Pivot Clusters at X = 0 mm and X = 100 mm
        for (px = [0, femur_length]) {
            translate([px, 0]) {
                // Center Ø8.0 mm servo hub hole
                circle(d = hub_hole_dia);

                // 4x Ø2.0 mm servo horn mounting holes at 90° cross (±8.0 mm)
                for (angle = [0, 90, 180, 270]) {
                    rotate([0, 0, angle])
                        translate([horn_bolt_circle_dia / 2, 0])
                            circle(d = horn_hole_dia);
                }
            }
        }

        // Two central Ø3.0 mm M3 standoff holes at X = 35 mm and X = 65 mm
        for (sx = [standoff_1_x, standoff_2_x]) {
            translate([sx, 0])
                circle(d = standoff_hole_dia);
        }
    }
}

module femur_plate_3d(thickness = plate_thickness) {
    linear_extrude(height = thickness, center = true)
        femur_plate_2d();
}

// Render 3D plate by default (switch to femur_plate_2d() for DXF/SVG export)
femur_plate_3d();
