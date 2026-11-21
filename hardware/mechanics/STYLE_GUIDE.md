# Hexapod:Lasius – Mechanics & Hardware Style Guide

---

[Project Index](../../README.md) | [Hardware Documentation](../README.md) | [Mechanics Documentation](README.md) | [v2 Models Backlog](models/custom/v2/TODO.md) | [Closed Loop Plan](../../docs/hardware/closed_loop_plan.md)

---

This document defines the binding aesthetic, geometric, and design-for-manufacturing (DfAM) guidelines for all mechanical components of **Hexapod:Lasius** (Generation v2 and subsequent generations).

The goal is a **consistent bionic design language**, maximum structural stiffness at minimal moving mass, and reproducible manufacturing quality in FDM 3D printing (PETG).

---

## 1. Bionic Design DNA (*Form Follows Load & Bio-Motion*)

The visual and structural archetype of Lasius is the black garden ant (*Lasius niger*):

* **No purely decorative edges:** Every curvature, stiffening rib, or cutout follows an actual load path or functional requirement (torque reaction, kinematic clearance, wire routing, or passive chimney convection).
* **Flowing transitions ($G^1$ continuity):** Components avoid abrupt 90° steps or sharp cross-sectional jumps. Transitions between functional sections are constructed from tangent-continuous curves ($G^1$).
* **Functional encapsulation:** Sensors (e.g., ADS1115 in the Femur, VL53L5CX in the Belly Pan) and wiring harnesses are form-fitted directly inside the structural shell rather than bolted onto the exterior afterwards.

---

## 2. Limb & Joint Morphology

```
         Joint Apex (Top)
            (X_axis, Z_max)
                /-----\
               /       \  <-- S-Curve 2
  S-Curve 1   /         \____         Waist
    /--------/               \______/-----\
   /                                       \_____  Cage Roof (Z_cage_top)
  (                                              |=========================
   \                                       /-----' Cage Floor (Z_cage_bot)
    \--------\               /------\-----/
              \         /----'
               \       /  <-- S-Curve 4
                \-----/
        Counter-Bearing Apex
            (X_axis, Z_min)
```

### 2.1 Joint Heads & Pivot Axes
* **Apices:** The highest point of the upper cheek ($Z_{\text{max}}$) and the lowest point of the counter-bearing boss ($Z_{\text{min}}$) always lie directly on the geometric rotation axis of the joint ($X_{\text{axis}}$).
* **Tapered tips:** Fork and cheek terminations (such as at $X = 0.0\,\text{mm}$ on the Coxa) must never end as flat 90° chop cuts; instead, they terminate organically via defined radii ($R \ge 3\text{--}5\,\text{mm}$) or tangent semi-circular arcs.

### 2.2 Anatomical Waist Curve
Between two joints, a limb segment does not taper monotonically, but forms an **anatomical waist** (tendon profile):
1. **Upper crest:** Drops gently below the roof height of the following segment behind the joint apex, forms a smooth constriction (waist), and sweeps tangentially up to the connecting roof height.
2. **Lower crest:** Rises behind the counter-bearing apex, forms a corresponding waist constriction, and merges tangentially into the floor of the following segment.
3. **Mathematical definition:**
   * All transitions are constructed from pairs of opposing circular arcs with a tangent-continuous inflection point ($G^1$, `make_s_curve_edges`).

---

## 3. Truss & Weight-Reduction Standards (Truss Architecture)

Where solid walls are not structurally required, standardized bionic truss windows are employed.

| Parameter | Standard Value | Engineering Rationale |
| :--- | :--- | :--- |
| **Strut Width ($w_{\text{strut}}$)** | **$2.50\,\text{mm}$** | Exactly 6 perimeters at a $0.40\,\text{mm}$ nozzle / $0.42\,\text{mm}$ line width; printed 100% solid without infill gaps. |
| **Truss Angle ($\alpha$)** | **$45.0^\circ$** | Guarantees support-free FDM printing and optimal shear/bending stiffness. |
| **Horizontal Strut Delta ($\Delta X_{45}$)** | **$3.536\,\text{mm}$** | $w \cdot \sqrt{2}$; horizontal offset for parallel 45° diagonals. |
| **Corner Fillet Radius ($R_{\text{fillet}}$)** | **$1.40\text{--}2.00\,\text{mm}$** | Eliminates notch stresses (*Notch-Stress Reduction*) at all triangular and trapezoidal corners. |
| **Inner Dust-Protection Backing Wall ($t_{\text{seal}}$)** | **$1.60\,\text{mm}$** | Where truss windows border an internal electronics chamber (e.g., Femur ADS1115 bay), windows are executed as blind pockets backed by an unbroken $1.60\,\text{mm}$ (4-perimeter) inner sealing wall to protect PCBs from dust and debris. |
| **Flank Topology** | **Warren Truss** | Alternating $45^\circ$ triangles for slender bending beams (Tibia, Coxa cheeks). |
| **Central Topology** | **A-Truss / Chevrons** | Arrow-shaped chevrons with a central apex for torsion bridges and body segments. |

---

## 4. Edge, Chamfer & Ventilation Hierarchy

### 4.1 Exterior & Highlight Edges (Tactile Fillets)
* **Standard exterior radius:** Exposed outer edges along cheeks, crests, and body shells receive an **$R = 1.0\text{--}1.5\,\text{mm}$ fillet**.
* **Purpose:** Comfortable handling without sharp burrs, improved interlayer adhesion along edges, and clean specular highlights in renders and physical hardware.

### 4.2 Functional & Protective Chamfers / Fillets
* **Cable pass-throughs:** $R = 1.0\text{--}1.5\,\text{mm}$ lead-in fillets or $45^\circ \times 1.0\text{--}1.5\,\text{mm}$ chamfers at all cable tunnels and apertures to prevent insulation chafing during continuous motion.
* **Connector & lid rebates:** $45^\circ \times 0.5\,\text{mm}$ assembly chamfers for zero-backlash mating of covers and caps.

### 4.3 Bionic Ventilation Louvers (`>>>`)
Electronics enclosures (BCM2711 SoC service cover, Femur ADC cover) use unified bionic chimney louvers:
* **Shape:** $45^\circ$ forward-swept chevron slots with rounded pill ends.
* **Geometry:** Slot width $2.5\text{--}3.0\,\text{mm}$, louver web $3.0\text{--}4.0\,\text{mm}$, depth angle $45^\circ$ for drip-protected passive convection.

---

## 5. Design for Additive Manufacturing (DfAM for PETG & CFRP Plates)

* **Chassis Plates (Hardware Freeze):** The two $2.0\,\text{mm}$ carbon-fiber plates ([`body_bottom.FCStd`](models/custom/v1/parts/body_bottom.FCStd) and [`body_top.FCStd`](models/custom/v1/parts/body_top.FCStd)) **already exist as physical, CNC-milled CFRP hardware** and are the **only component inherited unchanged from Generation `v1` into `v2`**. They define the immutable geometric reference (hole pattern, outer contour) for all v2 torso components.
* **FDM 3D-Printed Parts:** All other custom mechanical components (legs, monocoque central core, belly pan, canopy, covers, mounting blocks) are optimized for FDM printing in **PETG** (and TPU 95A for damping foot shoes) on standard build plates ($256 \times 256\,\text{mm}$).

### 5.1 Wall-Thickness Classes
* **Class 1 – Lightweight Covers, Canopies & Inner Chamber Seals:** $1.60\text{--}2.00\,\text{mm}$ (4 perimeters; dimensionally rigid and dust-tight).
* **Class 2 – Truss Struts & Ribs:** $2.50\,\text{mm}$ (built solidly from perimeter walls).
* **Class 3 – Joint Cheeks & Primary Structural Beams:** $5.00\text{--}6.20\,\text{mm}$ (maximum torsional and bending stiffness).
* **Class 4 – Servo-Horn Bosses & Torque Introduction:** $\ge 3.50\text{--}4.50\,\text{mm}$ solid material around screw bolt circles.

### 5.2 Standard Hardware Seats & Fits
* **Ball Bearing 684ZZ ($\varnothing 8 \times 3\,\text{mm}$):**
  * Bore: $\varnothing 8.05\,\text{mm}$ (light interference fit for FDM).
  * Retention shoulder collar: $R = 3.30\,\text{mm}$ ($0.30\,\text{mm}$ step over bearing outer ring) so only the inner race is clamped and the joint rotates freely.
* **Thin Hex Nut DIN 439 M4 (Counter-Bearing Thread Seat):**
  * Hex pocket: width across flats $SW = 7.10\,\text{mm}$, pocket depth $2.40\,\text{mm}$.
  * Solid stop shoulder: $0.60\,\text{mm}$ residual wall to through-bore ($\varnothing 4.10\,\text{mm}$).
* **Heat-Set Threaded Inserts (Ruthex M2 / M2.5 / M3):**
  * Bore diameters strictly per manufacturer datasheet with an $8^\circ$ lead-in countersink for clean thermal installation.

---

## 6. Color & Material Coding (Visual Identity in CAD & Digital Twin)

For clear visual identification in FreeCAD and in the Three.js Digital Twin, the following color palette applies:

| Subsystem / Role | Color | RGB Values | Material / Finish |
| :--- | :--- | :--- | :--- |
| **Structural Chassis & Limb Parts** | Anthracite / Slate Grey | `(0.20, 0.22, 0.25)` | Matte PETG / Carbon |
| **Joint Cheeks & Brackets** | Technical Medium Blue | `(0.12, 0.35, 0.65)` | Matte PETG |
| **Service Covers & Caps** | Graphite Black | `(0.15, 0.15, 0.18)` | Fine-texture PETG |
| **Plexiglas Canopy** | Ice-Blue Translucent (55% Alpha) | `(0.85, 0.92, 0.98)` | PMMA Acrylic / Thermoformed |
| **LiPo Battery Pack (COTS)** | Signal Gold / Yellow | `(0.95, 0.75, 0.10)` | Heat-shrink wrap |
| **PWM Servo Driver PCA9685** | Adafruit Signal Blue | `(0.04, 0.38, 0.88)` | PCB |
| **I2C Multiplexer TCA9548A** | Signal Purple | `(0.58, 0.15, 0.75)` | PCB |
| **Raspberry Pi 4 Model B** | Signal Green | `(0.10, 0.55, 0.25)` | PCB |

---

## 7. Parametric Code Standard (Hardware-as-Code)

Every CAD generator script in `hardware/mechanics/scripts/v2/` follows this structure:
1. **Constants block at top of file:** No hardcoded magic numbers inside modeling routines; all dimensions ($W_{\text{STRUT}}$, $R_{\text{FILLET}}$, inter-axis distances) are declared centrally at the top.
2. **Modular geometry helpers:**
   * `make_s_curve_edges(p1, p2)` for $G^1$-continuous S-curves.
   * `make_filleted_polygon_2d(pts, r_list)` for corner-filleted truss windows.
   * `make_hex_nut_pocket_z(cx, cy, z1, z2, sw)` for hex nut seats.
3. **Manufacturing exports exclusively upon explicit user request:** By default, generator scripts output only the parametric `.FCStd` models. STEP, STL, or DXF manufacturing files are **never exported proactively or during iterative development phases**, and the user is **never asked** whether exports should be generated. Manufacturing exports are generated only when explicitly requested by the user. Assemblies (`*_assembly`) never receive manufacturing exports.
