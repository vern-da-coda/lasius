#!/usr/bin/env python3
"""
Evaluate 3D printability of all custom parts in Lasius body_assembly for Bambu Lab printers.

Bambu Lab Printer Build Volumes:
- Standard (X1-Carbon, X1E, P1P, P1S, A1): 256 x 256 x 256 mm
- Compact (A1 mini): 180 x 180 x 180 mm
"""

import os
import sys

REPO_ROOT = "/home/bjoern/Workspace/Hexapods/lasius"
FC_MODEL = os.path.join(REPO_ROOT, "hardware/mechanics/models/custom/v2/body_assembly.FCStd")

def analyze():
    import FreeCAD as App

    doc = App.openDocument(FC_MODEL)
    unique_parts = {}

    def walk(obj):
        if obj.isDerivedFrom("App::Link"):
            linked = obj.LinkedObject
            if linked:
                if hasattr(linked, "Group") and len(linked.Group) > 0:
                    for c in linked.Group:
                        walk(c)
                elif hasattr(linked, "Shape") and not linked.Shape.isNull():
                    doc_path = linked.Document.FileName if linked.Document else ""
                    key = linked.Name
                    if key not in unique_parts:
                        bb = linked.Shape.BoundBox
                        unique_parts[key] = {
                            "label": linked.Label,
                            "file": doc_path,
                            "bb": (bb.XLength, bb.YLength, bb.ZLength),
                            "diagonal": bb.DiagonalLength,
                            "volume": linked.Shape.Volume,
                            "shape": linked.Shape
                        }
        elif hasattr(obj, "Group") and len(obj.Group) > 0:
            for c in obj.Group:
                walk(c)
        elif hasattr(obj, "Shape") and not obj.Shape.isNull():
            doc_path = obj.Document.FileName if obj.Document else ""
            key = obj.Name
            if key not in unique_parts:
                bb = obj.Shape.BoundBox
                unique_parts[key] = {
                    "label": obj.Label,
                    "file": doc_path,
                    "bb": (bb.XLength, bb.YLength, bb.ZLength),
                    "diagonal": bb.DiagonalLength,
                    "volume": obj.Shape.Volume,
                    "shape": obj.Shape
                }

    for o in doc.Objects:
        walk(o)

    print("=" * 110)
    print(f"{'Part Name':32s} | {'File / Generation':30s} | {'Dimensions (X x Y x Z) mm':25s} | {'Bambu 256':9s} | {'A1 mini':8s}")
    print("=" * 110)

    bambu_std = (256.0, 256.0, 256.0)
    bambu_mini = (180.0, 180.0, 180.0)

    custom_parts = []
    cots_parts = []

    for name, data in sorted(unique_parts.items()):
        file_path = data["file"]
        rel_file = os.path.relpath(file_path, REPO_ROOT) if file_path and REPO_ROOT in file_path else file_path
        bb = data["bb"]
        dims = sorted(bb, reverse=True) # longest to shortest

        # Check fit allowing 3D rotation (if longest dimension <= diagonal of bed, or sorted dimensions fit)
        # In Bambu Lab, standard bed is 256x256x256. Any part whose bounding box can be rotated to fit:
        # A simple conservative test: sorted dimensions <= (256, 256, 256)
        # Diagonal bed flat: sqrt(256^2 + 256^2) = 362 mm
        fits_std = dims[0] <= 256 and dims[1] <= 256 and dims[2] <= 256
        if not fits_std and dims[0] <= 350 and dims[1] <= 180 and dims[2] <= 256:
            # Can be placed diagonally on the 256x256 build plate!
            fits_std = True

        fits_mini = dims[0] <= 180 and dims[1] <= 180 and dims[2] <= 180
        if not fits_mini and dims[0] <= 245 and dims[1] <= 120 and dims[2] <= 180:
            fits_mini = True # diagonal fit on 180x180

        std_str = "YES" if fits_std else "NO (!)"
        mini_str = "YES" if fits_mini else "NO"

        dim_str = f"{bb[0]:6.1f} x {bb[1]:6.1f} x {bb[2]:6.1f}"
        
        is_custom = "custom" in rel_file or "Body_Assembly" in rel_file or "Leg_Assembly" in rel_file or "Chassis" in name or "Body" in name or "Leg" in name or "Coxa" in name or "Femur" in name or "Tibia" in name

        if is_custom and "cots" not in rel_file.lower():
            custom_parts.append((name, rel_file, dim_str, dims, fits_std, fits_mini, data))
            print(f"{name:32s} | {os.path.basename(rel_file):30s} | {dim_str:25s} | {std_str:9s} | {mini_str:8s}")
        else:
            cots_parts.append((name, rel_file, dim_str, dims, fits_std, fits_mini, data))

    print("=" * 110)
    print(f"\nTotal custom parts analyzed: {len(custom_parts)}")
    print(f"Total COTS/standard parts: {len(cots_parts)}")

if __name__ == "__main__":
    if "FreeCAD" in sys.modules:
        analyze()
    else:
        import subprocess
        cmd = ["/snap/bin/freecad", "-c", f"import sys; sys.path.append('{REPO_ROOT}/scripts/dev'); import check_printability; check_printability.analyze(); sys.exit(0)"]
        subprocess.run(cmd, check=True)
