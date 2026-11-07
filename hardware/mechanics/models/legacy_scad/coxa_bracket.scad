// ============================================================================
// Lasius Hexapod - Coxa Bracket (Original Vorlage + Stabilisierung + Rundungen)
// ============================================================================
// 1. Exakte Vorlage (X = 0 .. 115.0 mm, Y = 0 .. 31.7 mm, Z = 0 .. 18.0 mm)
//    inkl. Femur-Servo-Aufnahme & unterer Gegenlager-Lasche (X = 7.2 .. 25.7, Z = -14.5 .. 0).
// 2. Stabilisierung für Body-to-Coxa-Servo (X = 57.4 .. 115.0 mm):
//    Beidseitige 3.0 mm Seitenwangen (Z = -4.15 .. +22.15 mm) umschließen den
//    Body-to-Coxa-Servo (Tasche Z = -1.15 .. +19.15 mm) als Kastenwanne und
//    verstärken die bruchgefährdete Drehachse bei X = 74.7 mm.
// 3. Außenkanten analog zum Tibia-Fuß mit R = 2.0 mm (Innenkanten R = 0.8 mm) abgerundet.
// 4. Eingelassener Ø8x3 mm Kugellagersitz an der Coxa-Achse (X = 74.7, Y = 0..3.0, Z = 9.0)
//    sowie 4x 18.0 mm tiefe Sacklochbohrungen für den Body-to-Coxa-Servo.
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
            // 1a. Hauptkörper (X = 0..115, Y = 0..31.7, Z = 0..18) mit R = 2.0 mm Außenkanten
            rounded_rect_extrude(0.0, 115.0, 0.0, 18.0, 31.7, 2.0);

            // 1b. Untere Gegenlager-Lasche für Femur-Servo (X = 7.2..25.7, Y = 0..31.7, Z = -14.5..2.0)
            rounded_rect_extrude(7.2, 25.7, -14.5, 4.0, 31.7, 2.0);

            // 1c. Stabilisierende Seitenwangen für Body-to-Coxa-Servo (X = 57.4..115.0, Z = -4.15..22.15)
            rounded_rect_extrude(57.4, 115.0, -4.15, 22.15, 31.7, 2.0);
        }

        // 2a. Laschen-Innentasche (X = 6.2..25.75, Y = 5.0..25.5, Z = -11.5..0.05)
        translate([6.2, 5.0, -11.5])
            cube([19.55, 20.5, 11.55]);

        // 2b. Durchgangstasche Lasche (X = 9.0..25.75, Y = 5.0..25.5, Z = -11.5..19.0)
        translate([9.0, 5.0, -11.5])
            cube([16.75, 20.5, 30.5]);

        // 2c. Kabel-/Freischnitt an der Lasche (X = 7.15..9.05, Y = 12.1..19.6, Z = -1.0..4.5)
        translate([7.15, 12.1, -1.0])
            cube([1.9, 7.5, 5.5]);

        // 2d. Hauptfenster für Femur-Servo (X = 25.65..49.80, Y = 5.0..25.5, Z = -1.0..19.0)
        translate([25.65, 5.0, -1.0])
            cube([24.15, 20.5, 20.0]);

        // 2e. Gegenlager-Bohrung + Senkung an der unteren Lasche (X = 18.2, Y = 15.25, koaxial zur Femur-Servo-Achse)
        translate([18.2, 15.25, -15.5])
            cylinder(h = 5.0, r = 2.05);
        translate([18.2, 15.25, -13.0])
            cylinder(h = 1.55, r1 = 2.05, r2 = 3.05);

        // 2f. Femur-Servo Flansch-Absatz (X = -1.0..57.4, Y = 5.0..25.5, Z = 15.5..19.0)
        translate([-1.0, 5.0, 15.5])
            cube([58.4, 20.5, 3.5]);

        // 2g. 4x Femur-Servo Befestigungsbohrungen (X = 4.65, 53.15; Y = 10.25, 20.25; Ø2.2 mm)
        for (hx = [4.65, 53.15])
            for (hy = [10.25, 20.25])
                translate([hx, hy, -0.05])
                    cylinder(h = 19.0, r = 1.1);

        // 2h. Body-to-Coxa Servotasche (X = 65.5..106.4, Y = 4.0..32.7, Z = -1.25..19.25, Innenradius R = 0.8 mm)
        translate([0, 4.0, 0])
            rounded_rect_extrude(65.5, 106.4, -1.25, 19.25, 28.7, 0.8);

        // 2i. Coxa-Drehachse (X = 74.7, Z = 9.0): Durchgangsbohrung Ø4.0 + Kugellagersitz Ø8x3 + Senkung
        translate([74.7, -1.0, 9.0])
            rotate([-90, 0, 0])
                cylinder(h = 6.0, r = 2.0);
        translate([74.7, -0.05, 9.0])
            rotate([-90, 0, 0])
                cylinder(h = 3.05, r = 4.0);
        translate([74.7, 2.5, 9.0])
            rotate([-90, 0, 0])
                cylinder(h = 1.55, r1 = 2.0, r2 = 3.0);

        // 2j. 4x Sacklochbohrungen (18.0 mm tief von Y = 31.7 nach unten) für Body-to-Coxa-Servo
        for (hx = [60.55, 109.05])
            for (hz = [4.0, 14.0])
                translate([hx, 32.7, hz])
                    rotate([90, 0, 0])
                        cylinder(h = 19.0, r = 1.4);

        // 2k. Kabelauslass für Coxa-Servo (X = 56.4..66.0, Y = 3.95..12.45, Z = 5.0..23.0 durch die +Z Seitenwange)
        translate([56.4, 3.95, 5.0])
            cube([9.6, 8.5, 18.0]);
        translate([52.4, 5.1, 5.5])
            cube([4.5, 4.2, 14.0]);
    }
}

coxa_bracket();
