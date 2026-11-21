# Lasius Hexapod: Mechanics & CAD

---

[Index](../../README.md) | [Software](../../software/README.md) | [Hardware](../../hardware/README.md) | [Docs](../../docs/README.md) | [Data](../../data/README.md) | [Scripts](../../scripts/README.md) |<br>
[Mechanics](../../hardware/mechanics/README.md) | [Style-Guide](STYLE_GUIDE.md) | [Electronics / Wiring](../../hardware/electronics/wiring/README.md) |

---

CAD engineering, digital fabrication exports, and assembly models for the **Lasius** 18-DOF Hexapod robot. All parts are reverse-engineered from calibrated 1200 DPI flatbed scans and physical reference templates into native, parametric OpenCASCADE B-Rep solid geometry in FreeCAD.

## Parametric 3D CAD Models (`models/`)

### 1. COTS & Standard Components (`models/cots/`)
- **Servo Actuator ([`servo_nr645.FCStd`](models/cots/servo_nr645.FCStd)):** Torcster / Reely NR-645 MG BB standard actuator with output horn and mounting tabs.
- **Fasteners & Bearings:** [`bearing_684_6x3.FCStd`](models/cots/bearing_684_6x3.FCStd), [`screw_m4_countersunk.FCStd`](models/cots/screw_m4_countersunk.FCStd), [`nut_m4_hex.FCStd`](models/cots/nut_m4_hex.FCStd), [`nut_m4_din439.FCStd`](models/cots/nut_m4_din439.FCStd), and [`washer_m4_shim.FCStd`](models/cots/washer_m4_shim.FCStd).
- **Electronics & Power:**
  - **Raspberry Pi 4 Model B ([`rpi4_model_b.FCStd`](models/cots/rpi4_model_b.FCStd)):** Main SBC with BCM2711 SoC, dual USB 3.0/2.0 ports, Gigabit Ethernet, 40-pin GPIO header, USB-C, dual Micro-HDMI, and MicroSD slot.
  - **PCA9685 16-Channel PWM Servo Controller ([`pca9685_board.FCStd`](models/cots/pca9685_board.FCStd)):** Dual I²C servo drivers (left and right chassis banks) with 16× 3-pin servo headers and high-current power terminal.
  - **TCA9548A 8-Channel I²C Multiplexer ([`tca9548a_board.FCStd`](models/cots/tca9548a_board.FCStd)):** Central I²C bus multiplexer breakout with dual 12-pin header rows.
  - **VL53L5CX 9-Zone Time-of-Flight Distance Sensor ([`vl53l5cx_board.FCStd`](models/cots/vl53l5cx_board.FCStd)):** Downward-facing $3 \times 3$ multizone laser distance sensor for dynamic ground clearance and terrain mapping.
  - **ADS1115 16-Bit 4-Channel ADC Breakout ([`ads1115_board.FCStd`](models/cots/ads1115_board.FCStd)):** Precision I²C ADC breakout (Adafruit Blue) for closed-loop potentiometer feedback.
  - **2S 7.4V LiPo Battery Pack ([`battery_lipo_2s.FCStd`](models/cots/battery_lipo_2s.FCStd)):** Slim 2S flat pack ($88.0 \times 35.0 \times 14.0\,\text{mm}$) with 12AWG silicone leads, Amass XT60 connector, and JST-XH balance lead.

### 2. Custom Generation v1 (`models/custom/v1/` & `models/custom/v1/parts/`)
- **Chassis Bottom Plate ([`body_bottom.FCStd`](models/custom/v1/parts/body_bottom.FCStd)):**
  - **Material & Thickness:** 2.0 mm solid plate (CFRP carbon fiber / aluminum).
  - **Geometry:** Pure analytic OpenCASCADE B-Rep geometry (44 smooth faces, 126 edges; zero faceted polygon segments).
  - **Contour:** Exact $G^1$-continuous concave fillets ($R_f = 4.5\,\text{mm}$) transitioning into leg mounts. Fully protruding circular pivot ears ($R = 13.5\,\text{mm}$), $35.5^\circ$ flank line to tapered rear with $R = 7.0\,\text{mm}$ corner fillet.
  - **Bores:** 6× coxa counter-bearing holes ($\varnothing 8.0\,\text{mm}$), 8× M3 standoff mounting holes ($\varnothing 3.0\,\text{mm}$), and central electronics cutout window ($50.0 \times 160.0\,\text{mm}$).
- **Chassis Top Plate ([`body_top.FCStd`](models/custom/v1/parts/body_top.FCStd)):**
  - Upper chassis plate (2.0 mm solid), matching outer contour and mounting hole pattern as `body_bottom`.
- **Coxa Bracket ([`coxa_bracket.FCStd`](models/custom/v1/parts/coxa_bracket.FCStd)):**
  - **Structural Reinforcement:** Dual 3.0 mm lateral reinforcement cheeks fully enclose the Body-to-Coxa servo casing, eliminating shear failure at the pivot axis.
  - **Cable Outlet:** Filleted wiring channel for the Coxa servo ($R = 2.0\,\text{mm}$ outer corner radius).
  - **Counter-Bearing:** Coaxial pivot bore aligned at $Y = 15.25\,\text{mm}$ ($Z_{\text{world}} = 0.00\,\text{mm}$).
- **Femur Plate Cage ([`femur_plate.FCStd`](models/custom/v1/parts/femur_plate.FCStd)):**
  - Dual-plate beam cage ($L = 100.0\,\text{mm}$ inter-axis spacing, $W = 31.6\,\text{mm}$) with flush-mounted ball bearings ($\varnothing 8 \times 3\,\text{mm}$), standoff spacers (51.3 mm), and 1.0 mm servo clearance with flush M4 fasteners.
- **Tibia Limb ([`tibia.FCStd`](models/custom/v1/parts/tibia.FCStd)):**
  - High-rigidity, weight-optimized lower limb ($L = 130.0\,\text{mm}$, $X = -129.15 \dots +41.15\,\text{mm}$).
  - Pure analytic circular arcs and B-splines (26 faces, 72 edges) replacing previous 229 polygon steps while preserving the exact profile.
- **Tibia Servo Foot ([`tibia_servo_foot.FCStd`](models/custom/v1/parts/tibia_servo_foot.FCStd)):**
  - Integrated servo mount and rounded foot tip with internal wire routing.
- **Chassis Standoff Pillars ([`spacer_14x50.FCStd`](models/custom/v1/parts/spacer_14x50.FCStd)):**
  - $\varnothing 14.0\,\text{mm}$ standoff pillars ($L = 51.3\,\text{mm}$) with M3 threaded bores spanning the internal gap between chassis plates.
- **Complete Modular Leg Assembly v1 ([`leg_assembly.FCStd`](models/custom/v1/leg_assembly.FCStd)):**
  - Fully linked 22-part kinematic subassembly consisting of 3 servos (NR-645), brackets, bearings, M4 countersunk screws, shims, lock nuts, and standoffs.
- **Complete Full-Body Assembly v1 ([`body_assembly.FCStd`](models/custom/v1/body_assembly.FCStd)):**
  - Master full-robot assembly (142 components) linking bottom plate (`body_bottom`), top plate (`body_top`), 8× standoff pillars (`spacer_14x50`), and 6× modular leg assemblies (`leg_assembly`). Right-side legs (FR, MR, RR) are mirrored across the sagittal plane ($Y = 0$) so that all 6 servo horn outputs consistently face forward ($-X$).

### 3. Custom Generation v2 (`models/custom/v2/` & `models/custom/v2/parts/`)
> [!NOTE]
> For upcoming model tasks and verification steps, see the [**Generation v2 Backlog / TODO List**](models/custom/v2/TODO.md).

- **Monolithic Coxa v2 ([`coxa.FCStd`](models/custom/v2/parts/coxa/coxa.FCStd)):**
  - Monolithic 3D-printed Coxa joint segment replacing the v1 bracket plates, featuring unified bionic 45° A-truss windows ($w = 2.50\,\text{mm}$, $R = 1.40\,\text{mm}$), seamless $G^1$-continuous cheek profiles, an inverted M4 counter-bearing seat (Option A), and an integrated twin-servo mounting cage.
- **Organic Monolithic Femur & ADC Housing ([`femur.FCStd`](models/custom/v2/parts/femur/femur.FCStd)):**
  - Monolithic 3D-printed double-wrench femur ($L = 100.0\,\text{mm}$ pivot-to-pivot) replacing the 2-plate + 2-spacer v1 cage, featuring an internal chamber for the leg's encapsulated ADS1115 16-bit I²C ADC (`0x48`), blind 45° A-truss flank pockets backed by an unbroken $1.60\,\text{mm}$ (4-perimeter) inner dust-protection wall, internal cable channels with $R = 1.50\,\text{mm}$ anti-chafe mouth fillets, Option C vibration-free PCB clamping pins, and a removable service cover ([`femur_cover.FCStd`](models/custom/v2/parts/femur/femur_cover.FCStd)).
  - **FEA Structural Verification:** CalculiX C3D10 finite-element analysis confirms full structural integrity across all operating load cases including knee-servo stall torque ($1.2\,\text{N}\cdot\text{m}$). For full details, see the [**Femur FEA & Topology Optimization Report**](../../docs/hardware/femur_topology_optimization_report.md).
- **Monolithic Tibia & Spring-Loaded Tarsus v2 ([`tibia.FCStd`](models/custom/v2/parts/tibia/tibia.FCStd), [`tarsus.FCStd`](models/custom/v2/parts/tarsus/tarsus.FCStd), [`tarsus_shoe.FCStd`](models/custom/v2/parts/tarsus/tarsus_shoe.FCStd)):**
  - Monolithic lower limb featuring unified 45° A-truss servo-cage cheeks, a concentric Krallen-Sichel teardrop window with a $2.50\,\text{mm}$ tapered lower web, and an internal guide pocket for the spring-loaded 3D-exoskeleton [`tarsus.FCStd`](models/custom/v2/parts/tarsus/tarsus.FCStd), subminiature ground-contact microswitch, and compact [`tarsus_shoe.FCStd`](models/custom/v2/parts/tarsus/tarsus_shoe.FCStd) Kufe.
- **Chassis Draped Canopy & Service Cover v2 ([`chassis_canopy.FCStd`](models/custom/v2/parts/chassis/chassis_canopy.FCStd), [`chassis_service_cover.FCStd`](models/custom/v2/parts/chassis/chassis_service_cover.FCStd)):**
  - Translucent exoskeleton canopy mounted above the upper chassis plate ($Z \ge 55.3\,\text{mm}$) paired with a removable graphite service cover featuring 5× $45^\circ$ thermal convection chevron louvers over the Raspberry Pi 4 SoC.
- **Chassis Belly Pan & Skid Plate v2 ([`chassis_belly_pan.FCStd`](models/custom/v2/parts/chassis/chassis_belly_pan.FCStd)):**
  - Contoured boat-hull skid plate mounted to the chassis underside ($Z \le 0.0\,\text{mm}$) with approach ramps, internal wiring cavity, and an integrated mounting recess with a $45^\circ$-chamfered optical aperture for the downward-facing 9-zone ToF terrain distance sensor (VL53L5CX).
- **Monocoque Central Chassis Core v2 ([`chassis_core.FCStd`](models/custom/v2/parts/chassis/chassis_core.FCStd)):**
  - Monolithic 3D-printed structural core spanning the $51.3\,\text{mm}$ gap between the bottom and top carbon plates, replacing the 8 individual v1 standoff pillars and encapsulating the 2S LiPo battery bay, dual PCA9685 PWM drivers, and TCA9548A I²C multiplexer.
- **Complete Modular Leg Assembly v2 ([`leg_assembly.FCStd`](models/custom/v2/leg_assembly.FCStd) & [`leg_right_assembly.FCStd`](models/custom/v2/leg_right_assembly.FCStd)):**
  - Modular left and right leg subassemblies combining the monolithic v2 [`coxa.FCStd`](models/custom/v2/parts/coxa/coxa.FCStd), [`femur_assembly.FCStd`](models/custom/v2/femur_assembly.FCStd), and [`tibia_assembly.FCStd`](models/custom/v2/tibia_assembly.FCStd) with [`tarsus_assembly.FCStd`](models/custom/v2/tarsus_assembly.FCStd).
- **Complete Full-Body Assembly v2 ([`body_assembly.FCStd`](models/custom/v2/body_assembly.FCStd)):**
  - Master full-robot assembly (v2) integrating:
    - **Chassis Plates (Hardware Freeze):** The two $2.0\,\text{mm}$ CFRP carbon-fiber plates ([`body_bottom.FCStd`](models/custom/v1/parts/body_bottom.FCStd) and [`body_top.FCStd`](models/custom/v1/parts/body_top.FCStd)) **already exist as physical CNC-milled parts** and are the **only component inherited unchanged from v1**. All other v1 custom parts are obsolete.
    - 6× modular v2 leg subassemblies ([`leg_assembly.FCStd`](models/custom/v2/leg_assembly.FCStd) / [`leg_right_assembly.FCStd`](models/custom/v2/leg_right_assembly.FCStd)).
    - 3D-printed torso structure: Monocoque Central Core ([`chassis_core.FCStd`](models/custom/v2/parts/chassis/chassis_core.FCStd)), [`chassis_belly_pan.FCStd`](models/custom/v2/parts/chassis/chassis_belly_pan.FCStd) (with downward-facing VL53L5CX ToF sensor), upper mounting frame ([`chassis_rpi_mount.FCStd`](models/custom/v2/parts/chassis/chassis_rpi_mount.FCStd)), service cover ([`chassis_service_cover.FCStd`](models/custom/v2/parts/chassis/chassis_service_cover.FCStd)), and translucent acrylic canopy ([`chassis_canopy.FCStd`](models/custom/v2/parts/chassis/chassis_canopy.FCStd)).
    - Encapsulated electronics core: 2× PCA9685 + TCA9548A + 2S LiPo battery pack.
    - Compute platform: Raspberry Pi 4 Model B centered on the upper mounting frame beneath the louvered service cover.

---

## Directory Organization

```text
hardware/mechanics/
├── models/                  # FreeCAD CAD documents
│   ├── cots/                # COTS parts (servo_nr645, bearings, screws, nuts, washers, rpi4, pca9685, tca9548a, vl53l5cx, battery_lipo_2s)
│   └── custom/              # Custom-engineered robot assemblies & parts (canonical filenames)
│       ├── v1/              # Generation 1 (leg_assembly, body_assembly + parts/)
│       │   └── parts/       # Generation 1 single parts
│       └── v2/              # Generation 2 (leg_assembly, electronics_tray_assembly, body_assembly + parts/)
│           └── parts/       # Generation 2 components grouped by subsystem (coxa, femur, tibia, chassis, electronics_tray, head, gaster)
├── export/                  # Digital fabrication outputs (mirrors models/ structure)
│   ├── step/                # ISO 10303 CAD exchange format (custom/{v1,v2}[/parts/...], cots/)
│   ├── stl/                 # High-resolution meshes for 3D printing (custom/{v1,v2}[/parts/...], cots/)
│   └── dxf/                 # 2D vector profiles for laser/CNC sheet cutting (custom/v1/parts/)
├── drawings/
│   └── renders/             # High-resolution CAD 3D renders (.png)
├── scripts/                 # Parametric Python FreeCAD generators & scan math
│   ├── cots/                # COTS solid generators (electronics, actuators)
│   ├── v1/                  # Generation 1 part, assembly & technical drawing generators
│   └── v2/                  # Generation 2 monolithic part & assembly generators
└── scans/                   # 1200 DPI reference flatbed scans of physical parts
```

---

## Running Headless FreeCAD Scripts

Parametric geometry and assembly exports can be generated headlessly using FreeCAD:

```bash
# Generate COTS electronics CAD models:
/snap/bin/freecad.cmd -c hardware/mechanics/scripts/cots/generate_electronics_cots.py

# Generate v1 bottom/top plates and rebuild v1 assemblies:
/snap/bin/freecad.cmd hardware/mechanics/scripts/v1/generate_body_bottom.py
/snap/bin/freecad.cmd hardware/mechanics/scripts/v1/generate_body_top.py
/snap/bin/freecad.cmd hardware/mechanics/scripts/v1/generate_leg_assembly.py
/snap/bin/freecad.cmd hardware/mechanics/scripts/v1/generate_body_assembly.py

# Generate v2 monolithic femur, tibia, tray, belly pan, top cover, and v2 assemblies:
/snap/bin/freecad.cmd -c hardware/mechanics/scripts/v2/generate_femur.py
/snap/bin/freecad.cmd -c hardware/mechanics/scripts/v2/generate_tibia.py
/snap/bin/freecad.cmd -c hardware/mechanics/scripts/v2/generate_electronics_tray.py
/snap/bin/freecad.cmd -c hardware/mechanics/scripts/v2/generate_electronics_tray_assembly.py
/snap/bin/freecad.cmd -c hardware/mechanics/scripts/v2/generate_chassis_belly_pan.py
/snap/bin/freecad.cmd -c hardware/mechanics/scripts/v2/generate_chassis_top_cover.py
/snap/bin/freecad.cmd -c hardware/mechanics/scripts/v2/generate_leg_assembly.py
/snap/bin/freecad.cmd -c hardware/mechanics/scripts/v2/generate_body_assembly.py
```
