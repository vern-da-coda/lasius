#!/usr/bin/env python3
"""
Process 600 DPI Scan of Lasius Hexapod Tibia,
Extract precise millimeter polygon contours,
Align with Knee Pivot Axis (0, 0),
and output OpenSCAD and FreeCAD script.
"""

from PIL import Image
import math
import json

def rdp(points, epsilon):
    if len(points) < 3:
        return points
    first = points[0]
    last = points[-1]
    dx = last[0] - first[0]
    dy = last[1] - first[1]
    dist_sq = dx*dx + dy*dy
    max_d = 0.0
    index = 0
    if dist_sq > 1e-9:
        for i in range(1, len(points) - 1):
            p = points[i]
            d = abs((p[0] - first[0]) * dy - (p[1] - first[1]) * dx) / (dist_sq**0.5)
            if d > max_d:
                max_d = d
                index = i
    if max_d > epsilon:
        left = rdp(points[:index+1], epsilon)
        right = rdp(points[index:], epsilon)
        return left[:-1] + right
    else:
        return [first, last]

# Load and segment
im = Image.open('/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/scans/tibia/scan_20260520212913669.jpeg').transpose(Image.ROTATE_270).convert('L')
im_sub = im.resize((im.width // 2, im.height // 2), Image.Resampling.BILINEAR)
crop2 = im_sub.crop((350, 1300, 2600, 2050))
w, h = crop2.size

im_seg = Image.open('/home/bjoern/.gemini/antigravity-cli/brain/573b876a-e2e9-418d-b68d-88e20c56db98/segmented.png').convert('RGB')
raw_bytes = im_seg.tobytes()

is_part_area = bytearray(w * h)
for i in range(w * h):
    r, g, b = raw_bytes[i*3], raw_bytes[i*3+1], raw_bytes[i*3+2]
    # Filter exterior grey AND bottom ruler noise (Y > 620, X > 1500)
    y = i // w
    x = i % w
    if y > 620 and x > 1550:
        is_part_area[i] = 0
    elif r > 200 and g > 200 and b > 200:
        is_part_area[i] = 0
    else:
        is_part_area[i] = 1

DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]

def trace(grid, start_x, start_y):
    pts = [(start_x, start_y)]
    curr = (start_x, start_y)
    curr_dir = 7
    visited = set()
    while True:
        visited.add(curr)
        found = False
        for d in range(8):
            cd = (curr_dir + d) % 8
            nx, ny = curr[0] + DIRS[cd][0], curr[1] + DIRS[cd][1]
            if 0 <= nx < w and 0 <= ny < h and grid[ny * w + nx]:
                curr = (nx, ny)
                curr_dir = (cd + 5) % 8
                pts.append(curr)
                found = True
                break
        if not found or curr == pts[0] or len(pts) > 25000:
            break
    return pts

def rdp_closed(points, epsilon):
    first = points[0]
    max_d = 0.0
    split_idx = len(points) // 2
    for i, p in enumerate(points):
        d = (p[0] - first[0])**2 + (p[1] - first[1])**2
        if d > max_d:
            max_d = d
            split_idx = i
    h1 = rdp(points[:split_idx+1], epsilon)
    h2 = rdp(points[split_idx:], epsilon)
    return h1[:-1] + h2

# Trace outer boundary
for x in range(w):
    for y in range(h):
        if is_part_area[y * w + x]:
            outer_raw = trace(is_part_area, x, y)
            break
    else: continue
    break

# Trace slot
is_slot = bytearray(w * h)
for i in range(w * h):
    r, g, b = raw_bytes[i*3], raw_bytes[i*3+1], raw_bytes[i*3+2]
    is_slot[i] = 1 if (g > 180 and r < 50) else 0

for x in range(w):
    for y in range(h):
        if is_slot[y * w + x]:
            slot_raw = trace(is_slot, x, y)
            break
    else: continue
    break

print(f'Raw points: Outer={len(outer_raw)}, Slot={len(slot_raw)}')

# Simplify with RDP (epsilon in 2x pixels = 1.0 px approx 0.08 mm)
outer_simp = rdp_closed(outer_raw, 1.0)
slot_simp = rdp_closed(slot_raw, 1.0)
print(f'Simplified points: Outer={len(outer_simp)}, Slot={len(slot_simp)}')

# Coordinate transformation:
# Knee shaft center in crop2 (2x):
shaft_x = 1588.65
shaft_y = 561.20
scale = 11.98 # px per mm

# Tilt angle alignment: rotate by -tilt_rad to align servo horizontal
tilt_rad = math.radians(-2.43)
cos_a = math.cos(-tilt_rad)
sin_a = math.sin(-tilt_rad)

def to_mm(px, py):
    rx = px - shaft_x
    ry = -(py - shaft_y) # +Y is up
    x_rot = rx * cos_a - ry * sin_a
    y_rot = rx * sin_a + ry * cos_a
    return round(x_rot / scale, 2), round(y_rot / scale, 2)

outer_mm = [to_mm(*pt) for pt in outer_simp]
slot_mm = [to_mm(*pt) for pt in slot_simp]

# Save as JSON for OpenSCAD / FreeCAD
tibia_geom = {
    "outer_polygon": outer_mm,
    "slot_polygon": slot_mm,
    "knee_shaft": [0.0, 0.0],
    "servo_pitch_x": 48.50,
    "servo_pitch_y": 10.00,
    "right_holes_x": 14.15,
    "left_holes_x": -34.35, # 14.15 - 48.50
    "holes_y": [5.00, -5.00],
    "servo_win_x": [-30.25, 10.25], # 40.5 mm window
    "servo_win_y": [-10.25, 10.25], # 20.5 mm window
    "cable_notch_x": [10.25, 16.00],
    "cable_notch_y": [-7.50, 7.50],
    "foot_hole": [-93.00, -11.50],
    "foot_hole_dia": 3.0,
    "servo_hole_dia": 2.2,
    "servo_counterbore_dia": 4.5,
    "servo_counterbore_depth": 1.0,
    "plate_thickness": 2.2
}

with open('/home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/scripts/tibia_geom.json', 'w') as f:
    json.dump(tibia_geom, f, indent=2)

print('Saved /home/bjoern/Workspace/Hexapods/lasius/hardware/mechanics/scripts/tibia_geom.json!')
