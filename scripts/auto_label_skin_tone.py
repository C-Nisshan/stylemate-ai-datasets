#!/usr/bin/env python3
"""
auto_label_skin_tone.py

Auto-suggest skin tone labels using k-means clustering on mean LAB color of processed/skin-patches/

Outputs:
 - labels/skin-tone-auto_suggest.csv
 - labels/skin-tone-clusters.json  (centroids + mapping)
"""
import cv2
import numpy as np
import pandas as pd
import json
from pathlib import Path
from sklearn.cluster import KMeans

ROOT = Path(__file__).resolve().parent.parent
SKIN_DIR = ROOT / "processed" / "skin-patches"
OUT_DIR = ROOT / "labels"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = OUT_DIR / "skin-tone-auto_suggest.csv"
OUT_JSON = OUT_DIR / "skin-tone-clusters.json"

# number of clusters (adjustable)
K = 5

# human-readable labels ordered from darkest -> lightest
DEFAULT_LABELS_BY_BRIGHTNESS = ["dark", "brown", "wheatish", "fair", "very_fair"]

# gather mean LAB colors
rows = []
for p in sorted(SKIN_DIR.glob("*")):
    if p.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
        continue
    img = cv2.imread(str(p))
    if img is None:
        print(f"[WARN] cannot read {p.name}")
        continue
    # ensure 3 channels
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    # convert to LAB
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    mean = lab.reshape(-1, 3).mean(axis=0)  # L,a,b
    rows.append({"filename": p.name, "L": float(mean[0]), "a": float(mean[1]), "b": float(mean[2])})

if len(rows) == 0:
    raise SystemExit("[ERR] No skin patch images found in processed/skin-patches/")

df = pd.DataFrame(rows)

# clustering on L,a,b
X = df[["L", "a", "b"]].values
kmeans = KMeans(n_clusters=K, random_state=42, n_init=10).fit(X)
df["cluster_id"] = kmeans.labels_

# compute cluster centroids and sort by L (brightness)
centroids = kmeans.cluster_centers_
centroid_df = pd.DataFrame(centroids, columns=["L","a","b"])
centroid_df["cluster_id"] = centroid_df.index
centroid_df = centroid_df.sort_values("L").reset_index(drop=True)

# map sorted cluster order to labels_by_brightness
if len(DEFAULT_LABELS_BY_BRIGHTNESS) >= K:
    labels_map = {int(row["cluster_id"]): DEFAULT_LABELS_BY_BRIGHTNESS[i] for i, row in centroid_df.iterrows()}
else:
    # fallback: generate generic names
    labels_map = {int(row["cluster_id"]): f"cluster_{i}" for i, row in centroid_df.iterrows()}

# now assign suggested labels according to mapping
df["suggested_label"] = df["cluster_id"].map(labels_map)

# write CSV and cluster JSON for inspection
df.to_csv(OUT_CSV, index=False)

meta = {
    "k": K,
    "labels_map": labels_map,
    "centroids_sorted_by_L": centroid_df.to_dict(orient="records")
}
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=2)

print(f"[OK] Wrote auto suggestions: {OUT_CSV}")
print(f"[OK] Wrote cluster metadata: {OUT_JSON}")
print("Review suggested labels and edit CSV before using for training.")
