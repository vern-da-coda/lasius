# Lasius Hexapod: Mechanics & CAD

---

[Index](../../README.md) | [Software](../../software/README.md) | [Hardware](../../hardware/README.md) | [Docs](../../docs/README.md) | [Data](../../data/README.md) | [Scripts](../../scripts/README.md) |<br>
[Mechanics](../../hardware/mechanics/README.md) | [Electronics / Wiring](../../hardware/electronics/wiring/README.md) |

---

CAD engineering, digital fabrication exports, and assembly models for the **Lasius** 18-DOF Hexapod robot. All parts are reverse-engineered from calibrated 1200 DPI flatbed scans and physical reference templates into native, parametric OpenCASCADE B-Rep solid geometry in FreeCAD.

## Parametric 3D CAD Models (`models/`)

### 1. COTS & Standard Hardware (`models/hardware/`)
- **Servo Actuator ([`servo_nr645.FCStd`](models/hardware/servo_nr645.FCStd)):** Torcster / Reely NR-645 MG BB standard actuator with output horn and mounting tabs.
- **Fasteners & Bearings:** [`bearing_684_6x3.FCStd`](models/hardware/bearing_684_6x3.FCStd), [`screw_m4_countersunk.FCStd`](models/hardware/screw_m4_countersunk.FCStd), [`nut_m4_hex.FCStd`](models/hardware/nut_m4_hex.FCStd), and [`washer_m4_shim.FCStd`](models/hardware/washer_m4_shim.FCStd).

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
- **Organic Monolithic Femur & ADC Housing ([`femur.FCStd`](models/custom/v2/parts/femur.FCStd)):**
  - Monolithic 3D-printed double-wrench femur ($L = 100.0\,\text{mm}$ pivot-to-pivot) replacing the 2-plate + 2-spacer v1 cage, featuring an internal chamber and flush curved lid (`Femur_Cover`) for the leg's encapsulated ADS1115 16-bit I²C ADC (`0x48`) and internal cable channels.
- **Monolithic Tibia v2 ([`tibia.FCStd`](models/custom/v2/parts/tibia.FCStd)):**
  - Merges the sickle claw (`tibia`) and counter-bearing foot (`tibia_servo_foot`) into a single 3D-printed component connected via 4 organic hourglass-waisted corner struts (*Eckstege*).
- **Complete Modular Leg Assembly v2 ([`leg_assembly.FCStd`](models/custom/v2/leg_assembly.FCStd)):**
  - Modular leg subassembly combining the v1 [`coxa_bracket.FCStd`](models/custom/v1/parts/coxa_bracket.FCStd) with the v2 [`femur.FCStd`](models/custom/v2/parts/femur.FCStd) and [`tibia.FCStd`](models/custom/v2/parts/tibia.FCStd).
- **Complete Full-Body Assembly v2 ([`body_assembly.FCStd`](models/custom/v2/body_assembly.FCStd)):**
  - Master full-robot assembly (v2) combining the v1 chassis plates ([`body_bottom.FCStd`](models/custom/v1/parts/body_bottom.FCStd), [`body_top.FCStd`](models/custom/v1/parts/body_top.FCStd)) and 8× standoff pillars ([`spacer_14x50.FCStd`](models/custom/v1/parts/spacer_14x50.FCStd)) with 6× modular v2 leg assemblies ([`leg_assembly.FCStd`](models/custom/v2/leg_assembly.FCStd)).

---

## Directory Organization

```text
hardware/mechanics/
├── models/                  # FreeCAD CAD documents
│   ├── hardware/            # COTS & standard parts (servo_nr645, bearings, screws, nuts, washers)
│   └── custom/              # Custom-engineered robot assemblies & parts (canonical filenames)
│       ├── v1/              # Generation 1 (leg_assembly, body_assembly + parts/)
│       │   └── parts/       # Generation 1 single parts
│       └── v2/              # Generation 2 (leg_assembly, body_assembly + parts/)
│           └── parts/       # Generation 2 single parts
├── export/                  # Digital fabrication outputs (mirrors models/ structure)
│   ├── step/                # ISO 10303 CAD exchange format (custom/{v1,v2}[/parts], hardware/)
│   ├── stl/                 # High-resolution meshes for 3D printing (custom/{v1,v2}[/parts], hardware/)
│   └── dxf/                 # 2D vector profiles for laser/CNC sheet cutting (custom/v1/parts/)
├── drawings/
│   └── renders/             # High-resolution CAD 3D renders (.png)
├── scripts/                 # Parametric Python FreeCAD generators & scan math
│   ├── v1/                  # Generation 1 part, assembly & technical drawing generators
│   └── v2/                  # Generation 2 monolithic part & assembly generators
└── scans/                   # 1200 DPI reference flatbed scans of physical parts
```

---

## Running Headless FreeCAD Scripts

Parametric geometry and assembly exports can be generated headlessly using FreeCAD:

```bash
# Generate v1 bottom/top plates and rebuild v1 assemblies:
/snap/bin/freecad.cmd hardware/mechanics/scripts/v1/generate_body_bottom.py
/snap/bin/freecad.cmd hardware/mechanics/scripts/v1/generate_body_top.py
/snap/bin/freecad.cmd hardware/mechanics/scripts/v1/generate_leg_assembly.py
/snap/bin/freecad.cmd hardware/mechanics/scripts/v1/generate_body_assembly.py

# Generate v2 monolithic femur, tibia, and v2 leg & body assemblies:
/snap/bin/freecad.cmd hardware/mechanics/scripts/v2/generate_femur.py
/snap/bin/freecad.cmd hardware/mechanics/scripts/v2/generate_tibia.py
/snap/bin/freecad.cmd hardware/mechanics/scripts/v2/generate_leg_assembly.py
/snap/bin/freecad.cmd hardware/mechanics/scripts/v2/generate_body_assembly.py
```
