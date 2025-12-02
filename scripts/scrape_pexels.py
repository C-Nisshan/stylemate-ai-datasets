import os
import time
import json
import requests
from pathlib import Path
from typing import Dict, Any

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------

PEXELS_API_KEY = "GShKntn6aeVJls7SRp8TDU3HQEdaEFFFUQDCItLB84E450GnrFRcNxgU"
BASE_URL = "https://api.pexels.com/v1/search"
HEADERS = {"Authorization": PEXELS_API_KEY}

# Auto-detect repo root (fashion-ai-datasets/)
ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = ROOT / "raw"
BODY_DIR = RAW_DIR / "body"
SKIN_DIR = RAW_DIR / "skin"

PROGRESS_FILE = ROOT / "scripts" / "pexels_progress.json"
METADATA_FILE = ROOT / "scripts" / "pexels_metadata.json"

for d in (BODY_DIR, SKIN_DIR, PROGRESS_FILE.parent):
    d.mkdir(parents=True, exist_ok=True)

DEFAULT_PER_PAGE = 20
SLEEP_BETWEEN_PAGES = 2
MAX_RETRIES = 3

# ---------------------------------------------------
# QUERIES
# ---------------------------------------------------

BODY_QUERIES = [
    "full body standing woman",
    "full body standing man",
    "full body fashion model",
    "street style full body",
    "full length portrait",
    "urban full body portrait",
]

# === TARGETED QUERIES TO BALANCE BODY SHAPES ===
TARGETED_BODY_QUERIES = [
    # Hourglass (X) — missing class 1
    "hourglass figure woman full body",
    "curvy woman full body front view",
    "voluptuous woman standing full body",
    "woman with defined waist full body",
    "marilyn monroe body type full body",
    "kim kardashian body shape full body",

    # Pear shaped (A)
    "pear shaped woman full body",
    "wide hips narrow shoulders woman",
    "bottom heavy woman full body",
    "thick thighs small waist woman",

    # Apple / Rectangle (H) — also rare in fashion photos
    "apple shaped woman full body",
    "rectangle body shape woman standing",
    "straight figure woman full body",
    "athletic straight body woman",

    # Plus-size & curvy (usually X or A)
    "plus size woman full body portrait",
    "curvy plus size model full body",
    "bbw full body standing",
    "thick woman full body front",

    # Real people (not models)
    "average woman full body standing",
    "normal body woman full body",
    "real woman no makeup full body",
    "mom bod full body",
]

SKIN_QUERIES = [
    "forearm skin close up",
    "forearm skin texture macro",
    "arm skin texture close up",
    "hand skin texture close up",
    "palm skin close up",
    "back of hand skin close up",
    "face skin texture close up",
    "cheek skin close up",
    "forehead skin close up",
    "chin skin close up",
    "african skin texture close up",
    "indian skin texture close up",
    "asian skin close up",
    "latino skin texture",
    "fair skin texture close up",
    "skin texture natural light",
    "skin texture harsh light",
    "skin texture indoor lighting",
    "skin texture soft light",
    "male skin texture close up",
    "female skin texture close up"
]

# ---------------------------------------------------
# Load progress (resume mode)
# ---------------------------------------------------

if PROGRESS_FILE.exists():
    PROGRESS = json.loads(PROGRESS_FILE.read_text("utf-8"))
else:
    PROGRESS = {}

# ---------------------------------------------------
# Helpers
# ---------------------------------------------------

def safe_get(url: str, params: Dict[str, Any]):
    """GET request with retry support."""
    last_error = None
    for attempt in range(1, MAX_RETRIES+1):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=25)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_error = e
            wait = attempt * 2
            print(f"[WARN] Request error ({attempt}/{MAX_RETRIES}): {e}. Retrying {wait}s...")
            time.sleep(wait)

    raise last_error


def download(url: str, dest: Path):
    """Download file with retries."""
    for attempt in range(1, MAX_RETRIES+1):
        try:
            r = requests.get(url, stream=True, timeout=30)
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            return True
        except Exception as e:
            wait = attempt * 2
            print(f"[WARN] Download error ({attempt}/{MAX_RETRIES}): {e}. Retrying {wait}s...")
            time.sleep(wait)

    return False

# ---------------------------------------------------
# Core Scraper
# ---------------------------------------------------

def scrape_query(query: str, out_dir: Path, max_pages=5, per_page=DEFAULT_PER_PAGE, orientation=None):
    print(f"\n=== Query: {query} ===")

    # Resume from last successful page
    start_page = PROGRESS.get(query, 0) + 1
    print(f"[INFO] Resuming from page {start_page}")

    # Load old metadata
    if METADATA_FILE.exists():
        metadata = json.loads(METADATA_FILE.read_text("utf-8"))
    else:
        metadata = {}

    for page in range(start_page, max_pages + 1):

        print(f"\n[PAGE] {page}/{max_pages}")

        params = {"query": query, "page": page, "per_page": per_page}
        if orientation:
            params["orientation"] = orientation

        data = safe_get(BASE_URL, params)
        photos = data.get("photos", [])

        # Stop if no more data
        if not photos:
            print("[INFO] No more results. Ending.")
            break

        print(f"[INFO] Found {len(photos)} photos")

        for photo in photos:
            photo_id = photo["id"]
            fname = f"pexels_{photo_id}.jpg"
            dest = out_dir / fname

            # Duplicate check BEFORE API usage
            if dest.exists():
                print(f"[SKIP] Already exists: {fname}")
                continue

            src = photo.get("src", {})
            img_url = src.get("original") or src.get("large") or src.get("medium")

            if not img_url:
                print(f"[WARN] No valid URL for {photo_id}")
                continue

            print(f"[DOWN] {fname}")
            ok = download(img_url, dest)
            if not ok:
                print(f"[ERROR] Failed download: {fname}")
                continue

            # Save metadata
            metadata[fname] = {
                "id": photo_id,
                "url": img_url,
                "photographer": photo.get("photographer"),
                "page_url": photo.get("url"),
            }

        # Save metadata every page
        METADATA_FILE.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        # Update progress
        PROGRESS[query] = page
        PROGRESS_FILE.write_text(json.dumps(PROGRESS, indent=2), encoding="utf-8")

        print(f"[SAVE] Progress updated → page {page}")
        print(f"[INFO] Sleeping {SLEEP_BETWEEN_PAGES}s")
        time.sleep(SLEEP_BETWEEN_PAGES)

# ---------------------------------------------------
# Scrape Tasks
# ---------------------------------------------------

def scrape_body():
    for q in TARGETED_BODY_QUERIES:
        scrape_query(q, BODY_DIR)

def scrape_skin():
    for q in SKIN_QUERIES:
        scrape_query(q, SKIN_DIR, orientation="portrait")

# ---------------------------------------------------
# Main
# ---------------------------------------------------

def main():
    if not PEXELS_API_KEY or PEXELS_API_KEY == "YOUR_HARDCODED_KEY_HERE":
        print("[ERROR] Missing API key.")
        return

    print("\n=== Pexels Scraper Started ===")
    scrape_body()
    #scrape_skin()
    print("\n=== Completed ===")

if __name__ == "__main__":
    main()
