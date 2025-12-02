#!/usr/bin/env python3
"""
extract_landmarks.py
"""
import cv2
import json
import pandas as pd
from pathlib import Path
import mediapipe as mp

# Paths
ROOT = Path(__file__).resolve().parent.parent
RAW_BODY = ROOT / "raw" / "body"
OUT_DIR = ROOT / "processed" / "landmarks"
OUT_DIR.mkdir(parents=True, exist_ok=True)

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    static_image_mode=True,
    model_complexity=2,                  # Better accuracy
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

def normalize_landmarks(landmarks):
    lm = landmarks
    LS, RS = 11, 12
    LH, RH = 23, 24

    # Midpoints (in image coordinate space 0–1)
    mid_shoulder = ((lm[LS].x + lm[RS].x)/2, (lm[LS].y + lm[RS].y)/2)
    mid_hip = ((lm[LH].x + lm[RH].x)/2, (lm[LH].y + lm[RH].y)/2)

    # TORSO HEIGHT = vertical distance between mid-shoulder and mid-hip
    torso_height = abs(mid_shoulder[1] - mid_hip[1])
    if torso_height < 0.05:
        torso_height = 0.35  # fallback

    # Use torso center as origin
    center_x = (mid_shoulder[0] + mid_hip[0]) / 2
    center_y = (mid_shoulder[1] + mid_hip[1]) / 2

    normalized = []
    for p in lm:
        nx = (p.x - center_x) / torso_height
        ny = (p.y - center_y) / torso_height
        nz = p.z / torso_height
        normalized.append({
            "x": round(nx, 6),
            "y": round(ny, 6),
            "z": round(nz, 6),
            "visibility": round(p.visibility, 4)
        })
    return normalized, torso_height  # return height for debugging

def flatten_landmarks(norm_list, filename):
    flat = {"filename": filename}
    for i, pt in enumerate(norm_list):
        flat[f"x_{i}"] = pt["x"]
        flat[f"y_{i}"] = pt["y"]
        flat[f"z_{i}"] = pt["z"]
        flat[f"v_{i}"] = pt["visibility"]
    return flat

def main():
    print("Extracting landmarks → TORSO-HEIGHT NORMALIZED (Gold Standard)")
    csv_rows = []
    kept = deleted = 0

    for idx, path in enumerate(sorted(RAW_BODY.glob("*.[pj][pn]g")), 1):
        print(f"[{idx:4}] {path.name:50}", end="")
        img = cv2.imread(str(path))
        if img is None:
            path.unlink(); deleted += 1; print(" → DELETED"); continue

        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        if not results.pose_landmarks:
            path.unlink(); deleted += 1; print(" → NO PERSON"); continue

        normalized_lms, _ = normalize_landmarks(results.pose_landmarks.landmark)
        json_path = OUT_DIR / f"{path.stem}.json"
        json_path.write_text(json.dumps(normalized_lms, indent=2))

        csv_rows.append(flatten_landmarks(normalized_lms, path.name))
        kept += 1
        print(" → KEPT")

    if csv_rows:
        pd.DataFrame(csv_rows).to_csv(OUT_DIR / "body_landmarks_torso_normalized.csv", index=False)
    print(f"\nDone! Kept: {kept} | Deleted: {deleted}")

if __name__ == "__main__":
    main()