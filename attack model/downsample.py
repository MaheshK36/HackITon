import pandas as pd
import os

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

print("Loading archive_combined.csv...")
df = pd.read_csv('data/archive_combined.csv', low_memory=False)
print(f"Loaded {len(df):,} rows")

# Downsample to 50K rows total for CPU-safe training
print("Downsampling to 50,000 rows...")
sampled = df.sample(n=50000, random_state=42)

print(f"Final dataset: {len(sampled):,} rows")
print(f"Label distribution: {sampled['label'].value_counts().to_dict()}")

# Save downsampled version
sampled.to_csv('data/archive_combined.csv', index=False)
print(f"Saved downsampled dataset to data/archive_combined.csv")
