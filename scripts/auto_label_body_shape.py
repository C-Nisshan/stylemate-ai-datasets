#!/usr/bin/env python3
"""
auto_label_body_shape.py — GOLD STANDARD CLASSIFIER
Uses torso-height normalized landmarks → real ratios
"""
from pathlib import Path
import pandas as pd
import numpy as np
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "processed" / "landmarks" / "body_landmarks_torso_normalized.csv"
OUT_DIR = ROOT / "labels"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUT_DIR / "body_shapes_final.csv"

def dist(p1, p2):
    return np.hypot(p1[0] - p2[0], p1[1] - p2[1])

def get_pt(row, idx):
    return (row[f'x_{idx}'], row[f'y_{idx}'])

def classify(SHR, WHR, bust_hip_diff=0.05):
    if abs(SHR - 1.0) <= 0.10 and WHR <= 0.78:
        return "Hourglass"
    if abs(SHR - 1.0) <= 0.12:
        return "Rectangle"
    if SHR >= 1.15:
        return "Inverted Triangle"
    if SHR <= 0.88:
        return "Pear"  # formerly "Triangle"
    if WHR >= 0.90:
        return "Apple"  # formerly "Oval"
    return "Rectangle"

df = pd.read_csv(CSV)
print(f"Processing {len(df)} torso-normalized images...")

results = []
for _, row in df.iterrows():
    try:
        ls = get_pt(row, 11); rs = get_pt(row, 12)
        lh = get_pt(row, 23); rh = get_pt(row, 24)

        shoulder_w = dist(ls, rs)
        hip_w = dist(lh, rh)

        # Waist: average width at 40%, 50%, 60% down torso
        waist_ws = []
        for t in [0.4, 0.5, 0.6]:
            wx_l = (1-t)*ls[0] + t*lh[0]
            wx_r = (1-t)*rs[0] + t*rh[0]
            wy_l = (1-t)*ls[1] + t*lh[1]
            wy_r = (1-t)*rs[1] + t*rh[1]
            waist_ws.append(dist((wx_l, wy_l), (wx_r, wy_r)))
        waist_w = np.mean(waist_ws)

        SHR = shoulder_w / hip_w
        WHR = waist_w / hip_w

        shape = classify(SHR, WHR)

        results.append({
            "filename": row["filename"],
            "body_shape": shape,
            "shoulder_width": round(shoulder_w, 4),
            "hip_width": round(hip_w, 4),
            "waist_width": round(waist_w, 4),
            "SHR": round(SHR, 4),
            "WHR": round(WHR, 4),
            "shape_reason": f"SHR={SHR:.3f}, WHR={WHR:.3f}"
        })
        print(f"{row['filename']:50} → {shape:18} SHR={SHR:.3f} WHR={WHR:.3f}")
    except:
        continue

pd.DataFrame(results).to_csv(OUT_FILE, index=False)

counts = Counter(r["body_shape"] for r in results)
total = len(results)
print("\n" + "="*80)
print("FINAL BODY SHAPE DISTRIBUTION (TORSO-HEIGHT NORMALIZED)")
print("="*80)
for name in ["Hourglass", "Rectangle", "Pear", "Inverted Triangle", "Apple"]:
    c = counts.get(name, 0)
    p = c/total*100 if total else 0
    bar = "█" * int(p//2)
    print(f"{name:18} → {c:4} ({p:5.1f}%) {bar}")
print(f"\nSaved {total} clean labels → {OUT_FILE}")