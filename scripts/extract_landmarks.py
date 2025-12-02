#!/usr/bin/env python3
"""
extract_landmarks.py
"""
import cv2
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import mediapipe as mp

# ─────────────────────────────── Paths ───────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
RAW_BODY = ROOT / "raw" / "body"
OUT_DIR = ROOT / "processed" / "landmarks"
META_FILE = ROOT / "scripts" / "landmarks_metadata.json"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ───────────────────────────── MediaPipe ─────────────────────────────
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    static_image_mode=True,
    model_complexity=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# ────────────────────── Normalization (CORRECT!) ──────────────────────
def normalize_landmarks(landmarks):
    LEFT_HIP, RIGHT_HIP = 23, 24
    LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12
    lm = landmarks

    # Midpoints
    hip_cx = (lm[LEFT_HIP].x + lm[RIGHT_HIP].x) / 2.0
    hip_cy = (lm[LEFT_HIP].y + lm[RIGHT_HIP].y) / 2.0
    shoulder_cx = (lm[LEFT_SHOULDER].x + lm[RIGHT_SHOULDER].x) / 2.0
    shoulder_cy = (lm[LEFT_SHOULDER].y + lm[RIGHT_SHOULDER].y) / 2.0

    # Center of torso
    center_x = (hip_cx + shoulder_cx) / 2
    center_y = (hip_cy + shoulder_cy) / 2

    # Vertical scale only
    torso_height = abs(shoulder_cy - hip_cy)
    if torso_height < 0.01:
        torso_height = 0.4

    normalized = []
    for lm_point in landmarks:
        nx = lm_point.x - center_x                    # ← Raw horizontal (no scaling!)
        ny = (lm_point.y - center_y) / torso_height   # ← Vertical normalized
        nz = lm_point.z / torso_height
        normalized.append({
            "x": round(nx, 6),
            "y": round(ny, 6),
            "z": round(nz, 6),
            "visibility": round(lm_point.visibility, 6)
        })
    return normalized


def flatten_landmarks(landmark_list, filename: str):
    flat = {"filename": filename}
    for i, lm in enumerate(landmark_list):
        flat[f"x_{i}"] = lm["x"]
        flat[f"y_{i}"] = lm["y"]
        flat[f"z_{i}"] = lm["z"]
        flat[f"v_{i}"] = lm["visibility"]
    return flat


# ───────────────────────────── Main ─────────────────────────────
def main():
    print("=== Extracting Landmarks + AUTO-DELETE NO-PERSON IMAGES ===")
    print(f"Source: {RAW_BODY}\n")

    csv_rows = []
    metadata = {}
    deleted_count = kept_count = 0

    images = sorted([
        f for f in RAW_BODY.iterdir()
        if f.suffix.lower() in {".jpg", ".jpeg", ".png"}
    ])

    for idx, img_path in enumerate(images, 1):
        print(f"[{idx:4d}/{len(images)}] {img_path.name}", end="")

        img = cv2.imread(str(img_path))
        if img is None:
            print(" → [BAD FILE] DELETING")
            img_path.unlink()
            deleted_count += 1
            continue

        results = pose.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        if not results.pose_landmarks:
            print(" → [NO PERSON] DELETING")
            img_path.unlink()
            deleted_count += 1
            metadata[img_path.name] = {"status": "deleted_no_person", "when": datetime.now().isoformat()}
            continue

        normalized = normalize_landmarks(results.pose_landmarks.landmark)

        # Save per-image JSON
        json_path = OUT_DIR / f"{img_path.stem}.json"
        json_path.write_text(json.dumps(normalized, indent=2), encoding="utf-8")

        # Add to CSV
        csv_rows.append(flatten_landmarks(normalized, img_path.name))
        metadata[img_path.name] = {"status": "kept", "json": str(json_path)}
        kept_count += 1
        print(" → [KEPT]")

    # Save master CSV
    if csv_rows:
        df = pd.DataFrame(csv_rows)
        csv_path = OUT_DIR / "body_landmarks.csv"
        df.to_csv(csv_path, index=False)
        print(f"\n[CSV] Saved {len(df)} images → {csv_path}")

    # Save metadata
    META_FILE.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"\n[DONE]")
    print(f" Kept: {kept_count} images")
    print(f" Deleted: {deleted_count} junk/no-person images")
    print(" raw/body/ is now 100% clean!")


if __name__ == "__main__":
    main()