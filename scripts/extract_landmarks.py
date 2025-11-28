#!/usr/bin/env python3
"""
extract_landmarks.py

Extract 33 body pose landmarks using MediaPipe Pose from:
    raw/body/

Outputs:
    processed/landmarks/*.json  (raw landmark arrays)
    processed/landmarks/*.csv   (CSV flattened format)
    scripts/landmarks_metadata.json  (log + status)

Requirements:
    pip install mediapipe opencv-python pandas
"""

import cv2
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import mediapipe as mp

# ---------------------------------------
# Path Setup
# ---------------------------------------
ROOT = Path(__file__).resolve().parent.parent

RAW_BODY = ROOT / "raw" / "body"
OUT_DIR = ROOT / "processed" / "landmarks"
META_FILE = ROOT / "scripts" / "landmarks_metadata.json"

OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------
# MediaPipe Pose Setup
# ---------------------------------------
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

pose = mp_pose.Pose(
    static_image_mode=True,
    model_complexity=1,          # Lightweight for CPU
    enable_segmentation=False,
    min_detection_confidence=0.50
)

# ---------------------------------------
# Helper
# ---------------------------------------
def extract_landmarks_from_image(image_path):
    """Extracts pose landmarks from a single image."""
    img = cv2.imread(str(image_path))
    if img is None:
        return None

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = pose.process(img_rgb)

    if not results.pose_landmarks:
        return None

    lm_list = []
    for lm in results.pose_landmarks.landmark:
        lm_list.append({
            "x": lm.x,
            "y": lm.y,
            "z": lm.z,
            "visibility": lm.visibility
        })

    return lm_list


def flatten_landmarks(landmark_list):
    """Converts list of dicts to one flattened dict for CSV."""
    flat = {}
    for i, lm in enumerate(landmark_list):
        flat[f"x_{i}"] = lm["x"]
        flat[f"y_{i}"] = lm["y"]
        flat[f"z_{i}"] = lm["z"]
        flat[f"v_{i}"] = lm["visibility"]
    return flat


# ---------------------------------------
# Main Processing
# ---------------------------------------
def main():
    print("=== MediaPipe Landmark Extraction Started ===")
    metadata = {}
    csv_rows = []

    for file in RAW_BODY.iterdir():
        if file.suffix.lower() not in [".jpg", ".png", ".jpeg"]:
            continue

        print(f"\n[IMG] Processing: {file.name}")

        land = extract_landmarks_from_image(file)
        entry = {
            "file": file.name,
            "timestamp": datetime.now().isoformat()
        }

        if land is None:
            print("[WARN] No person detected — skipped")
            entry["status"] = "no_person"
            metadata[file.name] = entry
            continue

        # Save JSON landmarks
        json_name = f"{file.stem}.json"
        json_path = OUT_DIR / json_name
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(land, f, indent=2)

        # Add CSV row
        flat = flatten_landmarks(land)
        flat["file"] = file.name
        csv_rows.append(flat)

        entry["status"] = "ok"
        entry["json"] = str(json_path)
        metadata[file.name] = entry
        print(f"[OK] Landmarks saved → {json_name}")

    # Save CSV file
    if csv_rows:
        df = pd.DataFrame(csv_rows)
        csv_path = OUT_DIR / "landmarks.csv"
        df.to_csv(csv_path, index=False)
        print(f"\n[CSV] Saved combined CSV → {csv_path}")

    # Save metadata file
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("\n=== Extraction Completed ===")
    print(f"Metadata written → {META_FILE}")


if __name__ == "__main__":
    main()
