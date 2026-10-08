#!/usr/bin/env python
"""Test and train with file logging."""
import sys
import os
from datetime import datetime

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

log_file = BASE_DIR / 'training.log'

def log(msg):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n"
    print(line, end='')
    with open(log_file, 'a') as f:
        f.write(line)

# Start fresh
with open(log_file, 'w') as f:
    f.write('')

try:
    log("Step 1: Importing modules...")
    import pandas as pd
    import numpy as np
    import torch
    from data_pipeline import load_csv, make_windows, split_by_group
    from models import AttackWorldModel, ModelConfig
    from torch.utils.data import DataLoader, TensorDataset
    log("Step 2: Imports complete")
    
    log("Step 3: Loading data...")
    frame = load_csv('data/archive_combined.csv')
    log(f"Step 4: Loaded {len(frame):,} rows")
    
    log("Step 5: Creating windows...")
    windowed = make_windows(frame, 30.0, 10)
    log(f"Step 6: Created {windowed.sequences.shape[0]} sequences")
    
    log("Step 7: Splitting data...")
    splits = split_by_group(windowed, 42)
    log(f"Step 8: Train={len(splits['train'])} Val={len(splits['val'])} Test={len(splits['test'])}")
    
    log("Step 9: Creating model...")
    model = AttackWorldModel(ModelConfig(input_size=len(windowed.feature_names), backbone='lstm'))
    log("Step 10: Model created")
    
    log("Step 11: Starting training...")
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    
    # Create data loader
    train_data = TensorDataset(
        torch.from_numpy(splits["train"].sequences),
        torch.from_numpy(splits["train"].next_states),
        torch.from_numpy(splits["train"].infiltration),
        torch.from_numpy(splits["train"].stages)
    )
    train_loader = DataLoader(train_data, batch_size=32, shuffle=True)
    
    log(f"Step 12: Training with {len(train_loader)} batches")
    
    # Train for 1 epoch
    model.train()
    total_loss = 0.0
    for batch_idx, (seq, next_state, infiltration, stage) in enumerate(train_loader):
        optimizer.zero_grad()
        output = model(seq)
        # Just do a simple MSE loss for now
        loss = torch.nn.functional.mse_loss(output['next_state_pred'], next_state)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
        
        if (batch_idx + 1) % 5 == 0:
            log(f"  Batch {batch_idx+1}/{len(train_loader)} loss={total_loss/(batch_idx+1):.4f}")
    
    log(f"Step 13: Epoch complete, average loss={total_loss/len(train_loader):.4f}")
    
    log("SUCCESS: Training pipeline works!")
    
except Exception as e:
    import traceback
    log(f"ERROR: {e}")
    log(traceback.format_exc())
    sys.exit(1)
