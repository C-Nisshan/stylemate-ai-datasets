#!/usr/bin/env python3
"""
build_skin_npz.py

Creates datasets/skin_patches.npz:
 - X: (N,64,64,3) float32 normalized 0..1
 - y: list of labels (strings) or ints if you map them

Requires: pip install numpy opencv-python pandas
"""
import cv2
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIN_DIR = ROOT / "processed" / "skin-patches"
LABEL_FILE = ROOT / "labels" / "skin-tone-labels.csv"
OUT_DIR = ROOT / "datasets"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "skin_patches.npz"

IMG_SIZE = (64,64)

# Read labels CSV into dict
label_map = {}
if LABEL_FILE.exists():
    df = pd.read_csv(LABEL_FILE, dtype=str)
    if "filename" in df.columns and "skin_tone" in df.columns:
        label_map = dict(zip(df["filename"].astype(str), df["skin_tone"].astype(str)))
    else:
        print("[WARN] skin label CSV columns not found. Expected 'filename','skin_tone'")

X_list = []
y_list = []
filenames = []

for img_path in sorted(SKIN_DIR.glob("*")):
    if img_path.suffix.lower() not in [".jpg",".jpeg",".png"]:
        continue
    img = cv2.imread(str(img_path))
    if img is None:
        print(f"[WARN] Cannot read {img_path.name}")
        continue
    # ensure 3 channels
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    img = cv2.resize(img, IMG_SIZE, interpolation=cv2.INTER_AREA)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # keep RGB
    img = img.astype("float32") / 255.0
    label = label_map.get(img_path.name, "")
    X_list.append(img)
    y_list.append(label)
    filenames.append(img_path.name)

if len(X_list) == 0:
    print("[ERROR] No skin patch images found. Exiting.")
else:
    X = np.stack(X_list, axis=0)
    y = np.array(y_list, dtype=object)
    np.savez_compressed(OUT_FILE, X=X, y=y, filenames=np.array(filenames))
    print(f"[OK] Saved {OUT_FILE} with {X.shape[0]} samples.")
