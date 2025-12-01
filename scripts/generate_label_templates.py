#!/usr/bin/env python3
"""
generate_label_templates.py

Creates CSV label templates for:
 - labels/body-shape-labels_template.csv
 - labels/skin-tone-labels_template.csv

"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LABELS_DIR = ROOT / "labels"
LANDMARKS_DIR = ROOT / "processed" / "landmarks"
SKIN_DIR = ROOT / "processed" / "skin-patches"

LABELS_DIR.mkdir(parents=True, exist_ok=True)

# Body-shape template
body_template = LABELS_DIR / "body-shape-labels_template.csv"
with open(body_template, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["filename", "body_shape"])
    # If JSON files exist, prepopulate filenames
    if LANDMARKS_DIR.exists():
        for j in sorted(LANDMARKS_DIR.glob("*.json")):
            w.writerow([j.name, ""])  # fill label manually

# Skin-tone template
skin_template = LABELS_DIR / "skin-tone-labels_template.csv"
with open(skin_template, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["filename", "skin_tone"])
    if SKIN_DIR.exists():
        for img in sorted(SKIN_DIR.glob("*")):
            if img.suffix.lower() in [".jpg",".png",".jpeg"]:
                w.writerow([img.name, ""])

print(f"Templates written:\n - {body_template}\n - {skin_template}")