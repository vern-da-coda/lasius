// ============================================================================
// Lasius Hexapod - Coxa Bracket (Original template + reinforcement + fillets)
// ============================================================================
// 1. Exact template (X = 0 .. 115.0 mm, Y = 0 .. 31.7 mm, Z = 0 .. 18.0 mm)
//    incl. Femur servo mount & lower counter-bearing flange (X = 7.2 .. 25.7, Z = -14.5 .. 0).
// 2. Reinforcement for Body-to-Coxa servo (X = 57.4 .. 115.0 mm):
//    Bilateral 3.0 mm side walls (Z = -4.15 .. +22.15 mm) enclose the
//    Body-to-Coxa servo (pocket Z = -1.15 .. +19.15 mm) as a box enclosure and
//    reinforce the failure-prone rotation axis at X = 74.7 mm.
// 3. Outer edges rounded with R = 2.0 mm (inner edges R = 0.8 mm) analogous to the Tibia foot.
// 4. Recessed Ø8x3 mm ball bearing seat at the Coxa axis (X = 74.7, Y = 0..3.0, Z = 9.0)
//    as well as 4x 18.0 mm deep blind holes for the Body-to-Coxa servo.
// ============================================================================

$fn = 64;

module rounded_rect_extrude(x0, x1, z0, z1, y_len, r) {
    translate([0, y_len, 0])
        rotate([90, 0, 0])
            linear_extrude(height = y_len)
                 hull() {
                    for (x = [x0 + r, x1 - r])
                        for (z = [z0 + r, z1 - r])
                            translate([x, z])
                                circle(r = r);
                }
}

module coxa_bracket() {
    difference() {
        union() {
            // 1a. Main body (X = 0..115, Y = 0..31.7, Z = 0..18) with R = 2.0 mm outer edges
            rounded_rect_extrude(0.0, 115.0, 0.0, 18.0, 31.7, 2.0);

            // 1b. Lower counter-bearing flange for Femur servo (X = 7.2..25.7, Y = 0..31.7, Z = -14.5..2.0)
            rounded_rect_extrude(7.2, 25.7, -14.5, 4.0, 31.7, 2.0);

            // 1c. Reinforcing side walls for Body-to-Coxa servo (X = 57.4..115.0, Z = -4.15..22.15)
            rounded_rect_extrude(57.4, 115.0, -4.15, 22.15, 31.7, 2.0);
        }

        // 2a. Flange inner pocket (X = 6.2..25.75, Y = 5.0..25.5, Z = -11.5..0.05)
        translate([6.2, 5.0, -11.5])
            cube([19.55, 20.5, 11.55]);

        // 2b. Flange through-pocket (X = 9.0..25.75, Y = 5.0..25.5, Z = -11.5..19.0)
        translate([9.0, 5.0, -11.5])
            cube([16.75, 20.5, 30.5]);

        // 2c. Cable / relief cutout on flange (X = 7.15..9.05, Y = 12.1..19.6, Z = -1.0..4.5)
        translate([7.15, 12.1, -1.0])
            cube([1.9, 7.5, 5.5]);

        // 2d. Main cutout for Femur servo (X = 25.65..49.80, Y = 5.0..25.5, Z = -1.0..19.0)
        translate([25.65, 5.0, -1.0])
            cube([24.15, 20.5, 20.0]);

        // 2e. Counter-bearing bore + countersink on lower flange (X = 18.2, Y = 15.25, coaxial with Femur servo axis)
        translate([18.2, 15.25, -15.5])
            cylinder(h = 5.0, r = 2.05);
        translate([18.2, 15.25, -13.0])
            cylinder(h = 1.55, r1 = 2.05, r2 = 3.05);

        // 2f. Femur servo flange recess (X = -1.0..57.4, Y = 5.0..25.5, Z = 15.5..19.0)
        translate([-1.0, 5.0, 15.5])
            cube([58.4, 20.5, 3.5]);

        // 2g. 4x Femur servo mounting holes (X = 4.65, 53.15; Y = 10.25, 20.25; Ø2.2 mm)
        for (hx = [4.65, 53.15])
            for (hy = [10.25, 20.25])
                translate([hx, hy, -0.05])
                    cylinder(h = 19.0, r = 1.1);

        // 2h. Body-to-Coxa servo pocket (X = 65.5..106.4, Y = 4.0..32.7, Z = -1.25..19.25, inner radius R = 0.8 mm)
        translate([0, 4.0, 0])
            rounded_rect_extrude(65.5, 106.4, -1.25, 19.25, 28.7, 0.8);

        // 2i. Coxa rotation axis (X = 74.7, Z = 9.0): Through hole Ø4.0 + ball bearing seat Ø8x3 + countersink
        translate([74.7, -1.0, 9.0])
            rotate([-90, 0, 0])
                cylinder(h = 6.0, r = 2.0);
        translate([74.7, -0.05, 9.0])
            rotate([-90, 0, 0])
                cylinder(h = 3.05, r = 4.0);
        translate([74.7, 2.5, 9.0])
            rotate([-90, 0, 0])
                cylinder(h = 1.55, r1 = 2.0, r2 = 3.0);

        // 2j. 4x blind holes (18.0 mm deep downwards from Y = 31.7) for Body-to-Coxa servo
        for (hx = [60.55, 109.05])
            for (hz = [4.0, 14.0])
                translate([hx, 32.7, hz])
                    rotate([90, 0, 0])
                        cylinder(h = 19.0, r = 1.4);

        // 2k. Cable exit for Coxa servo (X = 56.4..66.0, Y = 3.95..12.45, Z = 5.0..23.0 through +Z side wall)
        translate([56.4, 3.95, 5.0])
            cube([9.6, 8.5, 18.0]);
        translate([52.4, 5.1, 5.5])
            cube([4.5, 4.2, 14.0]);
    }
}

coxa_bracket();
