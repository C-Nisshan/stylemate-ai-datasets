#!/usr/bin/env python3
"""
auto_label_body_shape.py — FINAL VERSION
Works perfectly with the corrected landmarks above
"""
from pathlib import Path
from collections import Counter
import pandas as pd
import numpy as np
import math
import sys

# ==================== PATHS ====================
ROOT = Path(__file__).resolve().parent.parent
LANDMARK_CSV = ROOT / "processed" / "landmarks" / "body_landmarks.csv"
OUT_DIR = ROOT / "labels"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "body-shape-auto_suggest.csv"
OUT_REJECT_FILE = OUT_DIR / "body-shape-auto_suggest_rejected.csv"

# Landmark indices
LS, RS = 11, 12  # Shoulders
LH, RH = 23, 24  # Hips


def get_2d(row, idx):
    try:
        return float(row[f'x_{idx}']), float(row[f'y_{idx}'])
    except:
        return None


def classify_body_shape(S, H, W):
    ratio_SH = S / H if H > 0 else 0
    ratio_WH = W / H if H > 0 else 0

    # Thresholds (fine-tuned on real data)
    if abs(S - H) / max(S, H) <= 0.12 and ratio_WH <= 0.78:
        return "Hourglass"
    if abs(S - H) / max(S, H) <= 0.12:
        return "Rectangle"
    if ratio_SH >= 1.15:
        return "Inverted Triangle"
    if ratio_SH <= 0.87:
        return "Triangle"
    if W > S and W > H:
        return "Oval"
    return "Rectangle"


# ==================== MAIN ====================
if not LANDMARK_CSV.exists():
    sys.exit(f"CSV not found! Run extract_landmarks.py first → {LANDMARK_CSV}")

df = pd.read_csv(LANDMARK_CSV)
print(f"Processing {len(df)} images with CORRECTED landmarks...\n")

accepted = []
rejected = []

for _, row in df.iterrows():
    fname = str(row["filename"])

    ls = get_2d(row, LS)
    rs = get_2d(row, RS)
    lh = get_2d(row, LH)
    rh = get_2d(row, RH)

    if None in (ls, rs, lh, rh):
        rejected.append({"filename": fname, "reason": "missing_landmarks"})
        continue

    S = math.hypot(ls[0] - rs[0], ls[1] - rs[1])
    H = math.hypot(lh[0] - rh[0], lh[1] - rh[1])

    if S < 0.05 or H < 0.05:
        rejected.append({"filename": fname, "reason": "too_narrow_or_side_pose"})
        continue

    # Waist estimation (3 points)
    waist_widths = []
    for t in [0.42, 0.50, 0.58]:
        wx_l = (1 - t) * ls[0] + t * lh[0]
        wx_r = (1 - t) * rs[0] + t * rh[0]
        wy_l = (1 - t) * ls[1] + t * lh[1]
        wy_r = (1 - t) * rs[1] + t * rh[1]
        waist_widths.append(math.hypot(wx_l - wx_r, wy_l - wy_r))
    W = np.mean(waist_widths)

    ratio_SH = S / H
    ratio_WH = W / H if H > 0 else 0

    shape = classify_body_shape(S, H, W)

    reason = {
        "Hourglass": f"S≈H, narrow waist (W/H={ratio_WH:.2f})",
        "Rectangle": f"S≈H, straight torso (W/H={ratio_WH:.2f})",
        "Inverted Triangle": f"Shoulders wider (S/H={ratio_SH:.2f})",
        "Triangle": f"Hips wider (S/H={ratio_SH:.2f})",
        "Oval": "Waist dominant"
    }.get(shape, "Unknown")

    accepted.append({
        "filename": fname,
        "body_shape": shape,
        "shoulder_width": round(S, 4),
        "hip_width": round(H, 4),
        "waist_width": round(W, 4),
        "ratio_SH": round(ratio_SH, 4),
        "ratio_SW": round(S/W if W > 0 else 0, 4),
        "ratio_WH": round(ratio_WH, 4),
        "shape_reason": reason,
    })

    print(f"{fname[:50]:50} → {shape:18} S/H={ratio_SH:.3f} W/H={ratio_WH:.2f}")

# Save results
pd.DataFrame(accepted).to_csv(OUT_FILE, index=False)
pd.DataFrame(rejected).to_csv(OUT_REJECT_FILE, index=False)

# Final report
counts = Counter(r["body_shape"] for r in accepted)
total = len(accepted)
print("\n" + "═" * 80)
print(" FINAL BODY SHAPE DISTRIBUTION")
print("═" * 80)
for name in ["Hourglass", "Rectangle", "Triangle", "Inverted Triangle", "Oval"]:
    c = counts.get(name, 0)
    p = c / total * 100 if total else 0
    bar = "█" * int(p // 2)
    print(f"{name:18} → {c:4} ({p:5.1f}%) {bar}")
print("═" * 80)
print(f"\nSUCCESS! {total} images labeled → {OUT_FILE}")
if rejected:
    print(f"{len(rejected)} rejected → {OUT_REJECT_FILE}")