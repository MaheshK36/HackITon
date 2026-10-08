#!/usr/bin/env python
"""Complete pipeline: downsample + train on archive data."""
import sys
import subprocess
import pandas as pd
from pathlib import Path

os.chdir(Path(__file__).resolve().parent)

# Step 1: Downsample
print("[1/2] Downsampling dataset...", file=sys.stderr, flush=True)
df = pd.read_csv('data/archive_combined.csv', low_memory=False)
print(f"  Original: {len(df):,} rows", file=sys.stderr, flush=True)

sampled = df.sample(n=min(50000, len(df)), random_state=42)
sampled.to_csv('data/archive_combined.csv', index=False)
print(f"  Downsampled: {len(sampled):,} rows", file=sys.stderr, flush=True)
print(f"  Labels: {sampled['label'].value_counts().to_dict()}", file=sys.stderr, flush=True)

# Step 2: Train
print("\n[2/2] Starting training...", file=sys.stderr, flush=True)
result = subprocess.run([
    sys.executable, 'train.py',
    '--data', 'data/archive_combined.csv',
    '--window-seconds', '30',
    '--sequence-length', '10',
    '--backbone', 'lstm',
    '--epochs', '5',
    '--patience', '2',
    '--batch-size', '32'
], capture_output=False)

print(f"\nTraining exit code: {result.returncode}", file=sys.stderr, flush=True)
sys.exit(result.returncode)
