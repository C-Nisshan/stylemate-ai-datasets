#!/usr/bin/env python3
"""
scrape_pexels.py

Legal, API-based downloader for Pexels images.
Saves images into:
  - ../raw/body/
  - ../raw/skin/

Usage:
  1) Get a PEXELS_API_KEY from https://www.pexels.com/api/
  2) Export as environment variable:
       export PEXELS_API_KEY="your_key_here"
  3) Run:
       python3 scrape_pexels.py

Notes:
  - This script uses the official Pexels API and respects simple rate-limiting behaviour.
  - Do NOT use it to download copyrighted images for commercial use unless license permits.
"""

import os
import time
import requests
import json
from pathlib import Path
from typing import Dict, Any

# -----------------------
# Configuration
# -----------------------
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "YOUR_PEXELS_API_KEY")
BASE_URL = "https://api.pexels.com/v1/search"
HEADERS = {"Authorization": PEXELS_API_KEY}

ROOT = Path(__file__).resolve().parent.parent

BODY_DIR = ROOT / "raw" / "body"
SKIN_DIR = ROOT / "raw" / "skin"
META_FILE = ROOT / "scripts" / "pexels_metadata.json"

# Create directories if they don't exist
for d in (BODY_DIR, SKIN_DIR, META_FILE.parent):
    d.mkdir(parents=True, exist_ok=True)

# Pexels API limits: free tier is generous but avoid aggressive fetching.
# Use small per_page and sleep between pages.
DEFAULT_PER_PAGE = 15
DEFAULT_SLEEP_SECONDS = 2
MAX_RETRIES = 3

# -----------------------
# Helpers
# -----------------------
def _request_with_retries(url: str, params: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=20)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_err = e
            wait = attempt * 2
            print(f"[WARN] Request failed (attempt {attempt}/{MAX_RETRIES}): {e}. Retrying in {wait}s...")
            time.sleep(wait)
    raise last_err

def download_file(url: str, dest: Path):
    """Download binary file to dest (overwrites if exists)."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, stream=True, timeout=30)
            resp.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return
        except Exception as e:
            wait = attempt * 2
            print(f"[WARN] Download failed (attempt {attempt}/{MAX_RETRIES}): {e}. Retrying in {wait}s...")
            time.sleep(wait)
    raise RuntimeError(f"Failed to download {url} after {MAX_RETRIES} attempts")

# -----------------------
# Core functions
# -----------------------
def search_and_download(query: str, output_dir: Path, pages: int = 2, per_page: int = DEFAULT_PER_PAGE, orientation: str = None):
    """
    Query Pexels and download images.
     - query: search term
     - output_dir: Path to save images
     - pages: number of result pages to fetch
     - orientation: optional Pexels parameter (landscape, portrait, square)
    """
    saved_meta = {}
    for page in range(1, pages + 1):
        print(f"\n[INFO] Searching page {page} for '{query}' (per_page={per_page})")
        params = {
            "query": query,
            "per_page": per_page,
            "page": page,
        }
        if orientation:
            params["orientation"] = orientation

        data = _request_with_retries(BASE_URL, params=params, headers=HEADERS)
        photos = data.get("photos", [])
        if not photos:
            print("[INFO] No photos on this page; stopping.")
            break

        for p in photos:
            photo_id = p.get("id")
            src = p.get("src", {})
            # Pexels provides multiple sizes; prefer 'original' or 'large'
            img_url = src.get("original") or src.get("large") or src.get("medium")
            if not img_url:
                continue

            filename = f"pexels_{photo_id}.jpg"
            dest = output_dir / filename
            if dest.exists():
                print(f"[SKIP] {filename} already exists.")
                saved_meta[filename] = {"id": photo_id, "url": img_url, "skipped": True}
                continue

            print(f"[DOWN] {filename} from {img_url}")
            try:
                download_file(img_url, dest)
                saved_meta[filename] = {
                    "id": photo_id,
                    "url": img_url,
                    "photographer": p.get("photographer"),
                    "photographer_url": p.get("photographer_url"),
                    "page_url": p.get("url"),
                }
            except Exception as e:
                print(f"[ERROR] Failed to download {img_url}: {e}")
        # Respectful pause between pages
        print(f"[INFO] Sleeping {DEFAULT_SLEEP_SECONDS}s to be polite to the API.")
        time.sleep(DEFAULT_SLEEP_SECONDS)

    # Append metadata to file
    if META_FILE.exists():
        try:
            with open(META_FILE, "r", encoding="utf-8") as f:
                merged = json.load(f)
        except Exception:
            merged = {}
        merged.update(saved_meta)
    else:
        merged = saved_meta

    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Saved metadata entries: {len(saved_meta)} -> {META_FILE}")

def download_body_images(pages: int = 3):
    """
    Download full-body fashion images that are likely to contain standing/whole-body shots.
    Query ideas: "full body fashion model", "full body portrait", "street style full body"
    """
    queries = [
        "full body fashion model",
        "full body portrait",
        "full length portrait",
        "street style full body"
    ]
    for q in queries:
        search_and_download(q, BODY_DIR, pages=pages)

def download_skin_images(pages: int = 2):
    """
    Download close-up skin/texture/forearm/skin images.
    Query ideas: "forearm close up", "skin texture closeup", "skin care close up"
    """
    queries = [
        "forearm close up",
        "skin texture close up",
        "skin care close up",
        "close up skin texture"
    ]
    for q in queries:
        # orientation portrait may help for closeups
        search_and_download(q, SKIN_DIR, pages=pages, orientation="portrait")

# -----------------------
# CLI
# -----------------------
def main():
    if PEXELS_API_KEY == "YOUR_PEXELS_API_KEY" or not PEXELS_API_KEY:
        print("[ERROR] Please set your PEXELS_API_KEY environment variable. Get a key from https://www.pexels.com/api/")
        return

    print("=== Pexels downloader started ===")
    download_body_images(pages=3)
    download_skin_images(pages=2)
    print("=== Done ===")

if __name__ == "__main__":
    main()
