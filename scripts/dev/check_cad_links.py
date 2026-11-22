#!/usr/bin/env python3
"""
Verify FreeCAD App::Link integrity across all assembly models.
"""

import os
import FreeCAD as App

repo_root = "/home/bjoern/Workspace/Hexapods/lasius"
models_dir = os.path.join(repo_root, "hardware/mechanics/models")

assembly_files = [
    os.path.join(models_dir, "custom/v1/leg_assembly.FCStd"),
    os.path.join(models_dir, "custom/v1/body_assembly.FCStd"),
    os.path.join(models_dir, "custom/v2/chassis_core_assembly.FCStd"),
    os.path.join(models_dir, "custom/v2/chassis_assembly.FCStd"),
    os.path.join(models_dir, "custom/v2/electronics_tray_assembly.FCStd"),
    os.path.join(models_dir, "custom/v2/head_assembly.FCStd"),
    os.path.join(models_dir, "custom/v2/gaster_assembly.FCStd"),
    os.path.join(models_dir, "custom/v2/femur_assembly.FCStd"),
    os.path.join(models_dir, "custom/v2/tarsus_assembly.FCStd"),
    os.path.join(models_dir, "custom/v2/tibia_assembly.FCStd"),
    os.path.join(models_dir, "custom/v2/leg_assembly.FCStd"),
    os.path.join(models_dir, "custom/v2/leg_right_assembly.FCStd"),
    os.path.join(models_dir, "custom/v2/body_assembly.FCStd"),
    os.path.join(models_dir, "custom/v2/lasius_assembly.FCStd"),
]

total_links = 0
broken_links = 0

print("=== Verifying CAD Links Across All Assemblies ===")
opened_docs = []
for asm_path in assembly_files:
    if not os.path.exists(asm_path):
        print(f"File not found: {asm_path}")
        continue
    rel_path = os.path.relpath(asm_path, repo_root)
    doc = App.openDocument(asm_path)
    opened_docs.append(doc)
    asm_links = [obj for obj in doc.Objects if obj.isDerivedFrom("App::Link")]
    total_links += len(asm_links)
    asm_broken = 0
    for lnk in asm_links:
        target = lnk.LinkedObject
        if target is None:
            print(f"  ❌ Broken link in {rel_path}: {lnk.Name} ({lnk.Label}) -> None")
            asm_broken += 1
            broken_links += 1
    if asm_broken == 0:
        print(f"  ✅ {rel_path}: {len(asm_links)} links OK")

for d in opened_docs:
    try:
        App.closeDocument(d.Name)
    except Exception:
        pass

print(f"\n============================================================")
print(f"Total Assemblies Checked: {len(assembly_files)}")
print(f"Total Links Checked:      {total_links}")
print(f"Broken Links:             {broken_links}")
print(f"============================================================")

import sys, os
if broken_links > 0:
    print("❌ Broken CAD links detected!")
    os._exit(1)
else:
    print("✅ All CAD links verified successfully!")
    os._exit(0)
