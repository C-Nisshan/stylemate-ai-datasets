#!/usr/bin/env python3
"""
json_to_csv_landmarks.py

Reads processed/landmarks/*.json and optional labels/body-shape-labels.csv
Outputs:
 - datasets/body_landmarks.csv  (flattened numeric features + filename + label_if_available)
"""
import json
import math
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANDMARK_DIR = ROOT / "processed" / "landmarks"
LABEL_FILE = ROOT / "labels" / "body-shape-labels.csv"
OUT_DIR = ROOT / "datasets"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = OUT_DIR / "body_landmarks.csv"

def flatten_landmark_list(lm_list):
    row = {}
    # Expect 33 landmarks; each has x,y,z,visibility
    for i in range(33):
        if i < len(lm_list):
            lm = lm_list[i]
            row[f"x_{i}"] = lm.get("x", float("nan"))
            row[f"y_{i}"] = lm.get("y", float("nan"))
            row[f"z_{i}"] = lm.get("z", float("nan"))
            row[f"v_{i}"] = lm.get("visibility", float("nan"))
        else:
            row[f"x_{i}"] = float("nan")
            row[f"y_{i}"] = float("nan")
            row[f"z_{i}"] = float("nan")
            row[f"v_{i}"] = float("nan")
    return row

# Read label mapping (if exists)
label_map = {}
if LABEL_FILE.exists():
    df_labels = pd.read_csv(LABEL_FILE)
    # make dict: filename -> label (assume column names as in template)
    if "filename" in df_labels.columns and "body_shape" in df_labels.columns:
        label_map = dict(zip(df_labels["filename"].astype(str), df_labels["body_shape"].astype(str)))
    else:
        print("[WARN] label file exists but columns not recognized.")

rows = []
for j in sorted(LANDMARK_DIR.glob("*.json")):
    try:
        with open(j, "r", encoding="utf-8") as f:
            lm_list = json.load(f)
    except Exception as e:
        print(f"[ERR] Failed to read {j.name}: {e}")
        continue

    flat = flatten_landmark_list(lm_list)
    flat["filename"] = j.name
    if j.name in label_map:
        flat["label"] = label_map[j.name]
    else:
        flat["label"] = ""  # unlabeled for now
    rows.append(flat)

if rows:
    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)
    print(f"[OK] Wrote {OUT_CSV} ({len(df)} rows)")
else:
    print("[WARN] No JSON landmarks found. Nothing written.")
