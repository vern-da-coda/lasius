# Lasius Hexapod: Mechanics & CAD

---

[Index](../../README.md) | [Software](../../software/README.md) | [Hardware](../../hardware/README.md) | [Docs](../../docs/README.md) | [Data](../../data/README.md) | [Scripts](../../scripts/README.md) |<br>
[Mechanics](../../hardware/mechanics/README.md) | [Electronics / Wiring](../../hardware/electronics/wiring/README.md) |

---

CAD engineering, digital fabrication exports, and assembly models for the **Lasius** 18-DOF Hexapod robot. All parts are reverse-engineered from calibrated 1200 DPI flatbed scans and physical reference templates into native, parametric OpenCASCADE B-Rep solid geometry in FreeCAD.

## Parametric 3D CAD Models (`models/`)

- **Chassis Bottom Plate ([`body_bottom.FCStd`](models/body_bottom.FCStd)):**
  - **Material & Thickness:** 2.0 mm solid plate (CFRP carbon fiber / aluminum).
  - **Geometry:** Pure analytic OpenCASCADE B-Rep geometry (44 smooth faces, 126 edges; zero faceted polygon segments).
  - **Contour:** Exact $G^1$-continuous concave fillets ($R_f = 4.5\,\text{mm}$) transitioning into leg mounts. Fully protruding circular pivot ears ($R = 13.5\,\text{mm}$), $35.5^\circ$ flank line to tapered rear with $R = 7.0\,\text{mm}$ corner fillet.
  - **Bores:** 6× coxa counter-bearing holes ($\varnothing 8.0\,\text{mm}$), 8× M3 standoff mounting holes ($\varnothing 3.0\,\text{mm}$), and central electronics cutout window ($50.0 \times 160.0\,\text{mm}$).
- **Chassis Top Plate ([`body_top.FCStd`](models/body_top.FCStd)):**
  - Upper chassis plate (2.0 mm solid), matching outer contour and mounting hole pattern as `body_bottom`.
- **Coxa Bracket ([`coxa_bracket.FCStd`](models/coxa_bracket.FCStd)):**
  - **Structural Reinforcement:** Dual 3.0 mm lateral reinforcement cheeks fully enclose the Body-to-Coxa servo casing, eliminating shear failure at the pivot axis.
  - **Cable Outlet:** Filleted wiring channel for the Coxa servo ($R = 2.0\,\text{mm}$ outer corner radius).
  - **Counter-Bearing:** Coaxial pivot bore aligned at $Y = 15.25\,\text{mm}$ ($Z_{\text{world}} = 0.00\,\text{mm}$).
- **Femur Plate Cage ([`femur_plate.FCStd`](models/femur_plate.FCStd)):**
  - Dual-plate beam cage ($L = 100.0\,\text{mm}$ inter-axis spacing, $W = 31.6\,\text{mm}$) with flush-mounted ball bearings ($\varnothing 8 \times 3\,\text{mm}$), standoff spacers (51.3 mm), and 1.0 mm servo clearance with flush M4 fasteners.
- **Tibia Limb ([`tibia.FCStd`](models/tibia.FCStd)):**
  - High-rigidity, weight-optimized lower limb ($L = 130.0\,\text{mm}$, $X = -129.15 \dots +41.15\,\text{mm}$).
  - Pure analytic circular arcs and B-splines (26 faces, 72 edges) replacing previous 229 polygon steps while preserving the exact profile.
- **Tibia Servo Foot ([`tibia_servo_foot.FCStd`](models/tibia_servo_foot.FCStd)):**
  - Integrated servo mount and rounded foot tip with internal wire routing.
- **Chassis Standoff Pillars ([`spacer_14x50.FCStd`](models/spacer_14x50.FCStd)):**
  - $\varnothing 14.0\,\text{mm}$ standoff pillars ($L = 51.3\,\text{mm}$) with M3 threaded bores spanning the internal gap between chassis plates.
- **Complete Modular Leg Assembly ([`leg_assembly.FCStd`](models/leg_assembly.FCStd)):**
  - Fully linked 22-part kinematic subassembly consisting of 3 servos (NR-645), brackets, bearings, M4 countersunk screws, shims, lock nuts, and standoffs.
- **Complete Full-Body Assembly ([`body_assembly.FCStd`](models/body_assembly.FCStd)):**
  - Master full-robot assembly (142 components) linking bottom plate (`body_bottom`), top plate (`body_top`), 8× standoff pillars (`spacer_14x50`), and 6× modular leg assemblies (`leg_assembly`). Right-side legs (FR, MR, RR) are mirrored across the sagittal plane ($Y = 0$) so that all 6 servo horn outputs consistently face forward ($-X$).

---

## Directory Organization

```text
hardware/mechanics/
├── models/                  # FreeCAD CAD documents
│   ├── hardware/            # Standard parts (bearings, screws, nuts, washers)
│   ├── legacy_scad/         # Archived OpenSCAD (.scad, .csg) reference models
│   └── *.FCStd              # Native FreeCAD part & assembly files
├── export/                  # Digital fabrication outputs
│   ├── step/                # ISO 10303 CAD exchange format (CNC milling & waterjet)
│   ├── stl/                 # High-resolution meshes for 3D printing (PETG, SLA)
│   └── dxf/                 # 2D vector profiles for laser cutting / sheet processing
├── drawings/
│   ├── renders/             # High-resolution CAD 3D renders (.png)
│   └── templates/           # 1:1 true-to-scale SVG drill & fabrication templates
├── scripts/                 # Parametric Python FreeCAD generators & scan math
└── scans/                   # 1200 DPI reference flatbed scans of physical parts
```

---

## Running Headless FreeCAD Scripts

Parametric geometry and assembly exports can be generated headlessly using FreeCAD:

```bash
# Generate bottom plate model and export STEP/STL/DXF:
/snap/bin/freecad.cmd hardware/mechanics/scripts/generate_body_bottom.py

# Generate top plate model:
/snap/bin/freecad.cmd hardware/mechanics/scripts/generate_body_top.py

# Rebuild full robot assembly:
/snap/bin/freecad.cmd hardware/mechanics/scripts/generate_body_assembly.py
```
