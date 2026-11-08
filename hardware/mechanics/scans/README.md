# Lasius Hexapod: 3D Reference Scans

---

[Index](../../../README.md) | [Software](../../../software/README.md) | [Hardware](../../../hardware/README.md) | [Docs](../../../docs/README.md) | [Data](../../../data/README.md) | [Scripts](../../../scripts/README.md) |<br>
[Mechanics](../../../hardware/mechanics/README.md) | [Electronics / Wiring](../../../hardware/electronics/wiring/README.md) |

---

Raw reverse-engineering reference data, calibrated flatbed scans, and dimensional measurement photographs for the mechanical parts of the **Lasius** 18-DOF Hexapod robot.

## Purpose & Organization

To reconstruct broken or worn original mechanical parts (such as the 3D-printed Coxa servo brackets) into clean parametric CAD models, physical parts were digitized using high-resolution 1200 DPI flatbed optical scanners and macro photography with calibrated metric reference rulers.

The directory is organized into component-specific subfolders:

- **`body_bottom/`**: Scans and pixel-aligned alignment overlays for the chassis lower mounting plate (2.0 mm carbon/aluminum plate, standoff spacings, and 6 Coxa rotation axes).
- **`coxa/`**: Reference photographs, flatbed scans, and fracture-point analyses of the original Coxa servo bracket (60 mm axis-to-axis spacing, 30 mm inboard bracket extension).
- **`femur/`**: Dimensional flatbed scans of the upper leg segment (100 mm axis-to-axis spacing, dual-plate carbon layout).
- **`tibia/`**: High-resolution scans of the curved lower leg sickle claw (130 mm knee-to-tip effective reach, integrated spur and window cutouts).
- **`servo/`**: Dimensional reference scans of the 25T standard digital servo casing, mounting flange hole patterns, and spline geometries.

## Storage Policy

Due to repository performance and size limits, raw high-resolution scan archives (uncompressed multi-megapixel JPEG/PNG files) are maintained locally and in design backups. Parametric 3D reconstructions, STEP exports, and STL meshes derived from these scans are versioned in:

- Parametric Models: [`../models/`](../models/)
- Fabrication Exports (STEP, STL, DXF): [`../export/`](../export/)
- 3D CAD Renders: [`../drawings/renders/`](../drawings/renders/)
