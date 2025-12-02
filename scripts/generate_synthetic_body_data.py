#!/usr/bin/env python3
"""
generate_synthetic_body_data.py
Generates 1000+ realistic, balanced, torso-normalized body shape rows
"""
import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)

def generate_filenames(n):
    templates = [
        "img_{:06d}.jpg", "photo_{}.jpeg", "{}.jpg",
        "stand_{:05d}.jpg", "model_{}.jpg", "person_{:04d}.jpg",
        "fullbody_{}.jpg", "pose_{:03d}.jpeg", "{:012d}.jpg",
        "user_upload_{}.jpg", "pic_{:07d}.jpg", "body_{:05d}.png"
    ]
    import random
    import string
    files = set()
    while len(files) < n:
        tmpl = random.choice(templates)
        if "{}" in tmpl:
            name = tmpl.format(np.random.randint(1, 999999))
        elif "{:0" in tmpl:
            name = tmpl.format(np.random.randint(1, 999999))
        else:
            name = ''.join(random.choices(string.hexdigits.lower(), k=16)) + ".jpg"
        files.add(name)
    return sorted(list(files))

def generate_class(shape, n=200):
    data = []
    filenames = generate_filenames(n)
    
    for i, fname in enumerate(filenames):
        if shape == "Hourglass":
            SHR = np.random.normal(1.00, 0.08)   # 0.85 – 1.15
            WHR = np.random.normal(0.72, 0.05)   # 0.62 – 0.82
        elif shape == "Rectangle":
            SHR = np.random.normal(1.02, 0.10)
            WHR = np.random.normal(0.88, 0.06)   # 0.78 – 0.98
        elif shape == "Pear":
            SHR = np.random.normal(0.82, 0.07)   # 0.68 – 0.95
            WHR = np.random.normal(0.85, 0.07)
        elif shape == "Apple":
            SHR = np.random.normal(1.05, 0.12)
            WHR = np.random.normal(0.95, 0.08)   # waist dominant
        elif shape == "Inverted Triangle":
            SHR = np.random.normal(1.35, 0.15)   # 1.15 – 1.80
            WHR = np.random.normal(1.10, 0.12)   # wider waist too
        
        # Clip to realistic bounds
        SHR = np.clip(SHR, 0.65, 2.4)
        WHR = np.clip(WHR, 0.60, 1.8)
        
        # Add natural measurement noise
        SHR += np.random.normal(0, 0.03)
        WHR += np.random.normal(0, 0.04)
        
        # Compute absolute widths (torso-height normalized)
        hip_width = np.random.normal(0.62, 0.08)
        shoulder_width = hip_width * SHR
        waist_width = hip_width * WHR
        
        # Reason string
        if shape == "Hourglass":
            reason = f"Balanced shoulders/hips, defined waist (W/H={WHR:.2f})"
        elif shape == "Rectangle":
            reason = f"Straight silhouette (W/H={WHR:.2f})"
        elif shape == "Pear":
            reason = f"Hips significantly wider (S/H={SHR:.2f})"
        elif shape == "Apple":
            reason = f"Waist dominant (W/H={WHR:.2f})"
        else:
            reason = f"Shoulders much wider (S/H={SHR:.2f})"
            
        data.append({
            "filename": fname,
            "body_shape": shape,
            "shoulder_width": round(shoulder_width, 4),
            "hip_width": round(hip_width, 4),
            "waist_width": round(waist_width, 4),
            "SHR": round(SHR, 4),
            "WHR": round(WHR, 4),
            "shape_reason": f"SHR={SHR:.3f}, WHR={WHR:.3f} | {reason}"
        })
    return data

# Generate balanced dataset
all_data = []
for shape in ["Hourglass", "Rectangle", "Pear", "Apple", "Inverted Triangle"]:
    all_data += generate_class(shape, n=220)  # 220 × 5 = 1100

df = pd.DataFrame(all_data)
df = df.sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle

OUT = Path("labels") / "body_shapes_synthetic_balanced_1100.csv"
OUT.parent.mkdir(exist_ok=True)
df.to_csv(OUT, index=False)

# Print distribution
print(df["body_shape"].value_counts().sort_index())
print(f"\nSaved {len(df)} realistic synthetic samples → {OUT}")