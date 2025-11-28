import os
from pathlib import Path

# Root folder
ROOT = Path(__file__).resolve().parent.parent
BODY_DIR = ROOT / "raw/body"
SKIN_DIR = ROOT / "raw/skin"

def count_images(folder: Path):
    if not folder.exists():
        return 0
    # Count common image file extensions
    extensions = [".jpg", ".jpeg", ".png"]
    return sum(1 for f in folder.iterdir() if f.suffix.lower() in extensions)

def main():count_images
    body_count = count_images(BODY_DIR)
    skin_count = count_images(SKIN_DIR)
    total_count = body_count + skin_count

    print("="*40)
    print("Dataset Image Counts")
    print("="*40)
    print(f"Body images: {body_count}")
    print(f"Skin images: {skin_count}")
    print(f"Total images: {total_count}")
    print("="*40)

if __name__ == "__main__":
    main()
