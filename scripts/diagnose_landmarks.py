# scripts/diagnose_landmarks.py
import pandas as pd
df = pd.read_csv("processed/landmarks/body_landmarks.csv")

print("Sample raw x coordinates (should NOT be 0–1920 or 0–1080):")
print(df[[f"x_11", f"x_12", f"x_23", f"x_24"]].head(10))

print("\nMax x values in your dataset:")
print(df[[col for col in df.columns if col.startswith("x_")]].max().max())
print(df[[col for col in df.columns if col.startswith("y_")]].max().max())