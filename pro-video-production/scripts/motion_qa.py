#!/usr/bin/env python3
"""Harakat QA: kadrlar orasidagi farq (kichraytirilgan), 0.5 s dan uzun "o'lik" joylar va keskin sakrashlar.
python motion_qa.py video.mp4 [fps]"""
import subprocess, sys
import numpy as np
v = sys.argv[1]
fps = float(sys.argv[2]) if len(sys.argv) > 2 else 30
w, h = 135, 240
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", v, "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)
d = np.abs(np.diff(fr, axis=0)).mean((1, 2))
print(f"frames {len(fr)}  diff median {np.median(d):.3f}  p95 {np.percentile(d, 95):.2f}  max {d.max():.2f}")
still = d < 0.06
run, start, dead = 0, 0, []
for i, s in enumerate(still):
    if s:
        if run == 0: start = i
        run += 1
    else:
        if run / fps > 0.5: dead.append((start / fps, run / fps))
        run = 0
if run / fps > 0.5: dead.append((start / fps, run / fps))
print("dead (>0.5s):", [(round(a, 2), round(b, 2)) for a, b in dead])
jumps = [(round((i + 1) / fps, 2), round(float(x), 1)) for i, x in enumerate(d) if x > max(6.0, np.median(d) * 25)]
print("jumps:", jumps)
