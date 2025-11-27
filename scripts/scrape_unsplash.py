import os
import time
import requests
from pathlib import Path

# Small test print — to confirm script is running
fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    print(fruit)

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------
UNSPLASH_ACCESS_KEY = "NxCoMUPTyCgGxegAJ5NJWtBw2CXY6cwvNwtHGNC5GEk"
BASE_URL = "https://api.unsplash.com"

# Dataset root (project root)
ROOT = Path(__file__).resolve().parent.parent

# Output folders
BODY_DIR = ROOT / "raw/body"
SKIN_DIR = ROOT / "raw/skin"

BODY_DIR.mkdir(parents=True, exist_ok=True)
SKIN_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------
# Helper: Check API Key Status
# ---------------------------------------------------
def check_api_key():
    print("Checking Unsplash API Key...")
    try:
        test = requests.get(
            f"{BASE_URL}/search/photos",
            params={"query": "test", "client_id": UNSPLASH_ACCESS_KEY},
            timeout=10
        )
    except Exception as e:
        print("Error contacting Unsplash:", e)
        return False

    print("Status:", test.status_code)

    if test.status_code != 200:
        print("API key is invalid or restricted.")
        print("Response:", test.text[:300])
        return False

    print("✔ API Key is valid.")
    return True


# ---------------------------------------------------
# Search Images
# ---------------------------------------------------
def search_unsplash(query, per_page=30, page=1):
    url = f"{BASE_URL}/search/photos"
    params = {
        "query": query,
        "per_page": per_page,
        "page": page,
        "client_id": UNSPLASH_ACCESS_KEY,
    }

    try:
        r = requests.get(url, params=params, timeout=10)
    except Exception as e:
        print("Search request failed:", e)
        return None

    if r.status_code != 200:
        print("\nSearch failed:", r.status_code)
        print(r.text[:300])
        return None

    return r.json()


# ---------------------------------------------------
# Download Image
# ---------------------------------------------------
def download_image(url, filepath):
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(r.content)
            return True
        else:
            print("Download failed:", r.status_code)
            return False
    except Exception as e:
        print("Download error:", e)
        return False


# ---------------------------------------------------
# Fetch Images with Debugging
# ---------------------------------------------------
def fetch_images(query, output_dir, pages=3):
    for page in range(1, pages + 1):

        print(f"\nSearching page {page} for: '{query}'")

        data = search_unsplash(query=query, page=page)

        if not data:
            print("No response — stopping search.")
            return

        results = data.get("results", [])
        print(f"Found {len(results)} images")

        if len(results) == 0:
            print("No more results — stopping.")
            return

        for img in results:
            img_id = img["id"]

            # Legal Unsplash download link
            try:
                download_loc = img["links"]["download_location"]
                log = requests.get(download_loc, params={"client_id": UNSPLASH_ACCESS_KEY}, timeout=10)

                if log.status_code != 200:
                    print(f"Failed to log download for {img_id}")
                    continue

                file_url = log.json().get("url")
            except Exception as e:
                print(f"Error processing {img_id}:", e)
                continue

            filepath = output_dir / f"{img_id}.jpg"
            print(f"Downloading {filepath.name}")

            if not download_image(file_url, filepath):
                print(f"Failed: {filepath.name}")

        print("Sleeping 3 seconds (API rate limit)...")
        time.sleep(3)


# ---------------------------------------------------
# Tasks
# ---------------------------------------------------
def download_body_images():
    fetch_images(
        query="full body fashion model",
        output_dir=BODY_DIR,
        pages=5
    )


def download_skin_images():
    fetch_images(
        query="skin texture close up forearm",
        output_dir=SKIN_DIR,
        pages=3
    )


# ---------------------------------------------------
# MAIN
# ---------------------------------------------------
if __name__ == "__main__":
    print("\n=== Unsplash Scraper Started ===\n")

    if not check_api_key():
        print("Exiting due to invalid API key.")
        exit(1)

    #download_body_images()
    download_skin_images()

    print("\n=== Done ===")
