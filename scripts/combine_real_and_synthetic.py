#!/usr/bin/env python3
"""
combine_real_and_synthetic.py
Merges real (biased) dataset + the balanced synthetic one
→ Produces the final clean, balanced training CSV
"""

import pandas as pd
from pathlib import Path

# ------------------------------------------------------------------
# Update these paths if folder structure is different
# ------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent

REAL_CSV      = ROOT / "labels" / "body_shapes_final.csv"                    # your 250 real rows
SYNTHETIC_CSV = ROOT / "labels" / "body_shapes_synthetic_balanced_1100.csv"  # from previous script
OUTPUT_CSV    = ROOT / "labels" / "FINAL_TRAINING_DATASET_v1.csv"            # ← final file

# ------------------------------------------------------------------
# Load
# ------------------------------------------------------------------
if not REAL_CSV.exists():
    print(f"ERROR: Real dataset not found → {REAL_CSV}")
    exit(1)
if not SYNTHETIC_CSV.exists():
    print(f"ERROR: Synthetic dataset not found → {SYNTHETIC_CSV}")
    print("   Run generate_synthetic_body_data.py first!")
    exit(1)

print("Loading real dataset...")
real_df = pd.read_csv(REAL_CSV)
print(f"   → {len(real_df)} real samples (mostly Inverted Triangle)")

print("Loading synthetic balanced dataset...")
syn_df = pd.read_csv(SYNTHETIC_CSV)
print(f"   → {len(syn_df)} synthetic samples")

# ------------------------------------------------------------------
# Combine (real data has priority if filename collision)
# ------------------------------------------------------------------
combined = pd.concat([real_df, syn_df], ignore_index=True)

print(f"Before deduplication: {len(combined)} rows")
combined.drop_duplicates(subset="filename", keep="first", inplace=True)
print(f"After deduplication : {len(combined)} rows")

# ------------------------------------------------------------------
# Final shuffle (important for training)
# ------------------------------------------------------------------
combined = combined.sample(frac=1, random_state=42).reset_index(drop=True)

# ------------------------------------------------------------------
# Save
# ------------------------------------------------------------------
OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
combined.to_csv(OUTPUT_CSV, index=False)
print(f"\nFINAL DATASET SAVED → {OUTPUT_CSV}")
print(f"Total samples: {len(combined)}")

# ------------------------------------------------------------------
# Show final class distribution (should be nicely balanced now)
# ------------------------------------------------------------------
print("\n" + "="*60)
print("FINAL CLASS DISTRIBUTION")
print("="*60)
dist = combined["body_shape"].value_counts().sort_index()
for shape, count in dist.items():
    perc = count / len(combined) * 100
    bar = "█" * int(perc // 2)
    print(f"{shape:18} → {count:4} ({perc:5.1f}%) {bar}")
print("="*60)