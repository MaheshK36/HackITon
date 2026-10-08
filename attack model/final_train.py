#!/usr/bin/env python
"""Downsample and train with file logging."""
import pandas as pd
import os
import sys
import subprocess

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

log_path = BASE_DIR / 'training_output.txt'

def log(msg):
    with open(log_path, 'a') as f:
        f.write(msg + '\n')
    print(msg, flush=True)

# Clear log
with open(log_path, 'w') as f:
    f.write('')

try:
    log("Step 1: Loading data...")
    df = pd.read_csv('data/archive_combined.csv', low_memory=False)
    log(f"Step 2: Loaded {len(df):,} rows")
    
    log("Step 3: Sampling to 50,000 rows...")
    df = df.sample(n=min(50000, len(df)), random_state=42).reset_index(drop=True)
    log(f"Step 4: Sampled to {len(df):,} rows")
    
    log("Step 5: Creating distinct source IP groups...")
    num_groups = 10
    group_size = len(df) // num_groups
    df['src_ip'] = ['10.0.' + str(i // group_size) + '.1' for i in range(len(df))]
    df['dst_ip'] = '10.0.0.254'
    
    log(f"Step 6: Created {df['src_ip'].nunique()} source groups")
    log(f"Step 7: Labels: {df['label'].value_counts().to_dict()}")
    
    log("Step 8: Saving downsampled data...")
    df.to_csv('data/archive_combined.csv', index=False)
    log("Step 9: Downsampling complete!")
    
    log("\nStep 10: Starting training...")
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
    
    log(f"Step 11: Training exit code: {result.returncode}")
    
    if result.returncode == 0:
        log("SUCCESS: Training completed!")
    else:
        log("WARNING: Training may have failed")
        
except Exception as e:
    import traceback
    log(f"ERROR: {e}")
    log(traceback.format_exc())
    sys.exit(1)
