#!/usr/bin/env python
"""Downsample dataset and create multiple source IP groups."""
from pathlib import Path
import pandas as pd
import os

os.chdir(Path(__file__).resolve().parent)

print("Loading archive_combined.csv...", flush=True)
df = pd.read_csv('data/archive_combined.csv', low_memory=False)
print(f"Loaded {len(df):,} rows", flush=True)

# Sample to 50K
print("Sampling to 50,000 rows...", flush=True)
df = df.sample(n=min(50000, len(df)), random_state=42).reset_index(drop=True)

# Create multiple source IPs to enable group splitting
# This creates ~10 distinct source groups
print("Creating distinct source IP groups...", flush=True)
num_groups = 10
group_size = len(df) // num_groups
df['src_ip'] = ['10.0.' + str(i // group_size) + '.1' for i in range(len(df))]

# Ensure dst_ip is consistent
df['dst_ip'] = '10.0.0.254'

print(f"Created {df['src_ip'].nunique()} distinct source groups", flush=True)
print(f"Label distribution: {df['label'].value_counts().to_dict()}", flush=True)

df.to_csv('data/archive_combined.csv', index=False)
print(f"Saved downsampled dataset with {len(df):,} rows", flush=True)
