import os
import time
import json
import requests
from pathlib import Path

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------

UNSPLASH_ACCESS_KEY = "NxCoMUPTyCgGxegAJ5NJWtBw2CXY6cwvNwtHGNC5GEk"
BASE_URL = "https://api.unsplash.com"

ROOT = Path(__file__).resolve().parent.parent

BODY_DIR = ROOT / "raw/body"
SKIN_DIR = ROOT / "raw/skin"
PROGRESS_FILE = ROOT / "scripts" / "unsplash_progress.json"

BODY_DIR.mkdir(parents=True, exist_ok=True)
SKIN_DIR.mkdir(parents=True, exist_ok=True)
PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)

MAX_PAGES = 3
SLEEP_TIME = 3

# Load progress
if PROGRESS_FILE.exists():
    PROGRESS = json.loads(PROGRESS_FILE.read_text())
else:
    PROGRESS = {}

# ---------------------------------------------------
# Query Lists
# ---------------------------------------------------

BODY_QUERIES = [
    "full body standing woman",
    "full body standing man",
    "person standing full body",
    "full body natural posture",
    "standing portrait full body",
    "full body front view person",
    "full body side view person",
    "full body back view person",
    "side profile full body woman",
    "side profile full body man",
    "woman walking full body",
    "man walking full body",
    "street photography full body",
    "people walking street full body",
    "urban fashion full body",
    "casual outfit full body",
    "street style full body",
    "summer outfit full body",
    "sportswear full body person",
    "fitness model full body",
    "plus size woman full body",
    "curvy woman full body",
    "heavyset man full body",
    "hourglass woman full body",
    "pear shaped woman full body",
    "apple shaped woman full body",
    "rectangle body shape woman",
    "african woman full body",
    "south asian woman full body",
    "asian man full body",
    "latina woman full body"
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
# API Key Check
# ---------------------------------------------------

def check_api_key():
    print("Checking Unsplash API Key...")
    r = requests.get(
        f"{BASE_URL}/search/photos",
        params={"query": "test", "client_id": UNSPLASH_ACCESS_KEY},
        timeout=10
    )
    if r.status_code == 200:
        print("✔ API Key OK")
        return True
    print("❌ Invalid API key:", r.status_code)
    print(r.text[:200])
    return False


# ---------------------------------------------------
# Search
# ---------------------------------------------------

def search_unsplash(query, page):
    try:
        r = requests.get(
            f"{BASE_URL}/search/photos",
            params={
                "query": query,
                "per_page": 30,
                "page": page,
                "client_id": UNSPLASH_ACCESS_KEY
            },
            timeout=10
        )
        if r.status_code == 200:
            return r.json()
        print("Search error:", r.status_code)
        return None
    except:
        return None


# ---------------------------------------------------
# Download
# ---------------------------------------------------

def download_image(url, filepath):
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(r.content)
            return True
    except:
        return False
    return False


# ---------------------------------------------------
# Fetch with resume support
# ---------------------------------------------------

def fetch_images(query, output_dir):

    last_done_page = PROGRESS.get(query, 0)
    print(f"\n=== Query: {query}")
    print(f"Resume: starting from page {last_done_page + 1}")

    for page in range(last_done_page + 1, MAX_PAGES + 1):

        print(f"\n--> Page {page}")

        data = search_unsplash(query, page)
        if not data:
            print("Stopping, no response.")
            return

        results = data.get("results", [])
        if not results:
            print("No more results")
            return

        for img in results:
            img_id = img["id"]
            filepath = output_dir / f"{img_id}.jpg"

            if filepath.exists():
                print(f"Skip {img_id}.jpg (exists)")
                continue

            try:
                download_loc = img["links"]["download_location"]
                log = requests.get(
                    download_loc,
                    params={"client_id": UNSPLASH_ACCESS_KEY},
                    timeout=10
                )
                if log.status_code != 200:
                    print("Failed log:", img_id)
                    continue

                file_url = log.json().get("url")

                print(f"Downloading {img_id}.jpg...")
                download_image(file_url, filepath)

            except Exception as e:
                print("Error:", e)
                continue

        # Save progress after each page
        PROGRESS[query] = page
        PROGRESS_FILE.write_text(json.dumps(PROGRESS, indent=2))

        print(f"[Saved] Progress saved → page {page}")
        print(f"Sleeping {SLEEP_TIME}s")
        time.sleep(SLEEP_TIME)


# ---------------------------------------------------
# MAIN
# ---------------------------------------------------

if __name__ == "__main__":
    print("\n=== Unsplash Scraper Started ===")

    if not check_api_key():
        exit(1)

    #for q in BODY_QUERIES:
        #fetch_images(q, BODY_DIR)

    for q in SKIN_QUERIES:
        fetch_images(q, SKIN_DIR)

    print("\n=== DONE ===")
