#!/usr/bin/env python3
"""
extract_skin_patches.py

Extracts skin patches from:
 - raw/skin/  (already close-up images)
 - raw/body/ (optional, tries to find arm / face area)

Outputs:
 - processed/skin-patches/

Uses:
 - OpenCV Haar cascades (lightweight, device-friendly)
 - fallback cropping when detection fails

Requirements:
    pip install opencv-python
"""

import cv2
import os
import json
from pathlib import Path
from datetime import datetime

# -----------------------------
# Folder Paths
# -----------------------------
ROOT = Path(__file__).resolve().parent.parent

RAW_SKIN = ROOT / "raw" / "skin"
RAW_BODY = ROOT / "raw" / "body"

OUT_DIR = ROOT / "processed" / "skin-patches"
META_FILE = ROOT / "scripts" / "skin_patch_metadata.json"

OUT_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------
# Haar Cascade Files (OpenCV)
# -----------------------------
# OpenCV ships these classifiers
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)
upperbody_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_upperbody.xml"
)

# -----------------------------
# Helper Functions
# -----------------------------

def save_patch(patch, filename, meta, metadata_dict):
    """Save skin patch and store metadata."""
    out_path = OUT_DIR / filename
    cv2.imwrite(str(out_path), patch)
    metadata_dict[filename] = meta


def detect_face(img_gray):
    """Return first face bbox (x, y, w, h) or None."""
    faces = face_cascade.detectMultiScale(img_gray, 1.2, 4)
    if len(faces) > 0:
        return faces[0]
    return None


def detect_upperbody(img_gray):
    """Return upper body bbox. Not perfect but usually finds torso/arms."""
    bodies = upperbody_cascade.detectMultiScale(img_gray, 1.1, 3)
    if len(bodies) > 0:
        return bodies[0]
    return None


def manual_center_crop(img, scale=0.4):
    """Fallback crop from center region."""
    h, w = img.shape[:2]
    crop_w, crop_h = int(w * scale), int(h * scale)

    start_x = w // 2 - crop_w // 2
    start_y = h // 2 - crop_h // 2

    return img[start_y:start_y + crop_h, start_x:start_x + crop_w]


def extract_patch_from_body(img):
    """Try detecting face then upper body; fallback to center crop."""
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Try face crop
    face = detect_face(img_gray)
    if face is not None:
        x, y, w, h = face
        # Expand slightly outward to include cheek & forehead skin
        pad = int(h * 0.2)
        return img[max(0, y-pad):y+h+pad, max(0, x-pad):x+w+pad]

    # Try upper body region (arms included)
    body = detect_upperbody(img_gray)
    if body is not None:
        x, y, w, h = body
        arm_area = img[y:y + int(h * 0.4), x:x + w]  # Upper torso / arms
        return arm_area

    # Fallback: center crop
    return manual_center_crop(img)


def normalize_patch(patch, size=(128, 128)):
    """Resize skin patch to uniform shape."""
    return cv2.resize(patch, size, interpolation=cv2.INTER_AREA)


# -----------------------------
# Main Processing
# -----------------------------
def process_raw_skin(metadata):
    """Directly crop center of close-up skin images."""
    print("\n=== Extracting from raw/skin/ ===")
    
    for file in RAW_SKIN.iterdir():
        if not file.is_file() or not file.suffix.lower() in [".jpg", ".png", ".jpeg"]:
            continue

        img = cv2.imread(str(file))
        if img is None:
            print(f"[WARN] Failed to read {file}")
            continue

        patch = manual_center_crop(img)
        patch = normalize_patch(patch)

        out_name = f"skin_{file.stem}.jpg"
        save_patch(
            patch,
            out_name,
            {
                "source": str(file),
                "method": "manual_center_crop",
                "timestamp": datetime.now().isoformat()
            },
            metadata
        )
        print(f"[OK] Saved patch from {file.name}")


def process_raw_body(metadata):
    """Extract skin regions from full-body images."""
    print("\n=== Extracting from raw/body/ ===")

    for file in RAW_BODY.iterdir():
        if not file.is_file() or not file.suffix.lower() in [".jpg", ".png", ".jpeg"]:
            continue

        img = cv2.imread(str(file))
        if img is None:
            print(f"[WARN] Could not read {file}")
            continue

        patch = extract_patch_from_body(img)
        patch = normalize_patch(patch)

        out_name = f"body_skin_{file.stem}.jpg"
        save_patch(
            patch,
            out_name,
            {
                "source": str(file),
                "method": "face/upperbody/fallback",
                "timestamp": datetime.now().isoformat()
            },
            metadata
        )
        print(f"[OK] Extracted patch from {file.name}")


def main():
    print("=== Skin Patch Extraction Started ===\n")

    metadata = {}

    process_raw_skin(metadata)
    process_raw_body(metadata)

    # Save metadata JSON
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("\n=== Extraction Complete ===")
    print(f"Metadata saved to {META_FILE}")


if __name__ == "__main__":
    main()
