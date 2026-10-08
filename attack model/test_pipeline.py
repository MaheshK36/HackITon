#!/usr/bin/env python
"""Test the data pipeline and windowing."""
import sys
import os
from pathlib import Path

os.chdir(Path(__file__).resolve().parent)

print("[1] Loading data...", flush=True)
from data_pipeline import load_csv, make_windows
frame = load_csv('data/archive_combined.csv')
print(f"[2] Loaded {len(frame):,} rows", flush=True)

print("[3] Creating windows...", flush=True)
windowed = make_windows(frame, 30.0, 10)
print(f"[4] Created {windowed.sequences.shape[0]} sequences", flush=True)

from data_pipeline import split_by_group
print("[5] Splitting by group...", flush=True)
splits = split_by_group(windowed, 42)
print(f"[6] Train: {len(splits['train'])} / Val: {len(splits['val'])} / Test: {len(splits['test'])}", flush=True)

print("\n[SUCCESS] Pipeline validation complete", flush=True)
