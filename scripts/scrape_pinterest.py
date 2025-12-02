#!/usr/bin/env python3
"""
scrape_pinterest.py 
"""
import json
from pathlib import Path
from pinterest_dl import PinterestDL

# ────────────────────────────── Config ──────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
BODY_DIR = ROOT / "raw" / "body"
PROGRESS_FILE = ROOT / "scripts" / "pinterest_progress_v2.json"

BODY_DIR.mkdir(parents=True, exist_ok=True)
PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)  # creates scripts/ if missing

# Targeted queries (all with "standing straight" + "front view")
QUERIES = [
    "hourglass figure woman full body standing straight front view",
    "curvy hourglass body type woman standing straight front view",
    "voluptuous hourglass model standing straight full body front",
    "pear shaped woman full body standing straight front view",
    "wide hips pear shape woman standing straight front view",
    "bottom heavy pear figure woman standing straight full body",
    "rectangle body shape woman full body standing straight front",
    "apple shaped body woman standing straight front view",
    "straight athletic body woman standing straight full body",
    "plus size curvy woman full body standing straight front view",
    "bbw hourglass figure woman standing straight front view",
    "body positive pear shape model standing straight full body",
    "hourglass body woman standing straight white background",
    "pear shaped curvy woman standing straight studio photo",
    "plus size model full body front view standing straight",
]

NUM_IMAGES_PER_QUERY = 30
TIMEOUT = 8
VERBOSE = False

# ──────────────────────── Helper: rename with prefix ────────────────────────
def add_prefix_to_new_files(directory: Path, prefix: str = "pin_stand_"):
    renamed = 0
    for file in directory.iterdir():
        if file.is_file() and not file.name.startswith(prefix):
            new_path = file.parent / f"{prefix}{file.name}"
            if not new_path.exists():
                file.rename(new_path)
                renamed += 1
    return renamed

# ─────────────────────────────── Main ───────────────────────────────
def main():
    print("=== Pinterest Scraper — STANDING STRAIGHT + FRONT VIEW ===")
    print(f"Images → {BODY_DIR}")
    print(f"Progress → {PROGRESS_FILE}\n")

    # Load or create progress
    if PROGRESS_FILE.exists():
        progress = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
    else:
        progress = {}

    dl = PinterestDL.with_api(timeout=TIMEOUT, verbose=VERBOSE, ensure_alt=True)

    total_downloaded = 0
    for query in QUERIES:
        key = query.replace(" ", "_")[:60]  # short unique key
        if progress.get(key, {}).get("done"):
            print(f"[SKIP] {query}")
            continue

        print(f"\n[QUERY] {query}")
        try:
            images = dl.search_and_download(
                query=query,
                output_dir=str(BODY_DIR),
                num=NUM_IMAGES_PER_QUERY,
                download_streams=True
            )
            count = len(images) if images else 0
            print(f"[OK] Downloaded {count} images")

            # Add our nice prefix after download
            renamed = add_prefix_to_new_files(BODY_DIR, "pin_stand_")
            print(f"[RENAME] Prefixed {renamed} files")

            total_downloaded += count
            progress[key] = {"downloaded": count, "done": True}

        except Exception as e:
            print(f"[FAILED] {e}")
            progress[key] = {"error": str(e)}

        # Save progress after every query
        PROGRESS_FILE.write_text(json.dumps(progress, indent=2), encoding="utf-8")

    print(f"\n=== SUCCESS! Downloaded {total_downloaded} high-quality images ===")
    print("Next →")
    print("   python scripts/extract_landmarks.py")
    print("   python scripts/auto_label_body_shape.py")

if __name__ == "__main__":
    main()