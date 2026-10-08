#!/usr/bin/env python
"""Complete archive build and training pipeline with file-based logging."""
import glob
import os
import sys
import subprocess
from pathlib import Path

import pandas as pd

LOG_FILE = Path('c:/Users/mahes/Downloads/attack model/pipeline_log.txt')


def log(msg):
    """Write to log file and stdout."""
    line = f"{msg}\n"
    print(line, end='')
    with open(LOG_FILE, 'a') as f:
        f.write(line)


def main():
    # Clear log
    LOG_FILE.write_text('')
    log("="*60)
    log("ATTACK MODEL ARCHIVE TRAINING PIPELINE")
    log("="*60)
    
    os.chdir(r'C:/Users/mahes/Downloads/attack model')
    log(f"Working directory: {os.getcwd()}")
    os.makedirs('data', exist_ok=True)
    
    # ===== STEP 1: BUILD ARCHIVE DATASET =====
    log("\n[STEP 1] Building archive dataset from 9 CSV files...")
    archive_glob = r'C:/Users/mahes/Downloads/archive/*.csv'
    files = sorted(glob.glob(archive_glob))
    log(f"Found {len(files)} archive files")
    
    if not files:
        log("FATAL ERROR: No archive files found")
        return 1
    
    frames = []
    total_rows = 0
    
    for idx, file in enumerate(files, 1):
        try:
            filename = Path(file).name
            df = pd.read_csv(file, low_memory=False)
            log(f"  [{idx}/9] {filename}: shape={df.shape}")
            total_rows += len(df)
            
            if df.empty:
                continue
            
            # Build schema-compatible frame
            out = pd.DataFrame()
            out['src_ip'] = ['10.0.0.1'] * len(df)
            out['dst_ip'] = ['10.0.0.2'] * len(df)
            out['src_port'] = 0
            out['dst_port'] = pd.to_numeric(df.get('Dst Port', 0), errors='coerce').fillna(0)
            out['protocol'] = pd.to_numeric(df.get('Protocol', 0), errors='coerce').fillna(0)
            out['tcp_flags'] = pd.to_numeric(df.get('SYN Flag Cnt', 0), errors='coerce').fillna(0)
            out['bytes_per_flow'] = pd.to_numeric(df.get('Flow Byts/s', 0), errors='coerce').fillna(0)
            out['packets_per_flow'] = pd.to_numeric(df.get('Tot Fwd Pkts', 0), errors='coerce').fillna(0)
            out['flow_duration'] = pd.to_numeric(df.get('Flow Duration', 0), errors='coerce').fillna(0)
            out['iat_mean'] = pd.to_numeric(df.get('Flow IAT Mean', 0), errors='coerce').fillna(0)
            out['iat_variance'] = pd.to_numeric(df.get('Flow IAT Std', 0), errors='coerce').fillna(0)
            out['iat_max'] = pd.to_numeric(df.get('Flow IAT Max', 0), errors='coerce').fillna(0)
            out['bidirectional_flow_ratio'] = 0.0
            out['ttl'] = 0.0
            out['ttl_variance'] = 0.0
            out['tcp_window_size'] = pd.to_numeric(df.get('Init Fwd Win Byts', 0), errors='coerce').fillna(0)
            out['ip_fragment_flags'] = 0.0
            out['payload_size'] = pd.to_numeric(df.get('Pkt Len Mean', 0), errors='coerce').fillna(0)
            out['port_scan_signature'] = 0.0
            out['retransmission_count'] = 0.0
            out['label'] = df['Label'].map({
                'Benign': 'BENIGN',
                'DoS attacks-GoldenEye': 'DOS',
                'DoS attacks-Slowloris': 'DOS'
            }).fillna('BENIGN')
            out['timestamp'] = pd.to_datetime(df['Timestamp'], dayfirst=True, errors='coerce')
            
            out = out.dropna(subset=['timestamp']).head(5000)
            if not out.empty:
                frames.append(out)
        except Exception as e:
            log(f"  ERROR processing {file}: {e}")
    
    log(f"\nTotal archive rows before processing: {total_rows:,}")
    
    if not frames:
        log("FATAL ERROR: No valid frames extracted")
        return 1
    
    combined = pd.concat(frames, ignore_index=True)
    log(f"After processing and combining: {len(combined):,} rows")
    label_dist = combined['label'].value_counts().to_dict()
    log(f"Label distribution: {label_dist}")
    
    # ===== STEP 2: SAVE ARCHIVE COMBINED CSV =====
    log("\n[STEP 2] Saving archive_combined.csv...")
    out_path = Path('data/archive_combined.csv')
    combined.to_csv(out_path, index=False)
    log(f"Saved {len(combined):,} rows to {out_path}")
    log(f"File size: {out_path.stat().st_size / (1024*1024):.2f} MB")
    
    # ===== STEP 3: VALIDATE WITH CANONICAL PIPELINE =====
    log("\n[STEP 3] Validating with canonical data pipeline...")
    try:
        from data_pipeline import load_csv, make_windows
        frame = load_csv(out_path)
        log(f"Canonical load: {len(frame):,} rows")
        log(f"Stage distribution: {frame['stage'].value_counts().to_dict()}")
        log(f"Groups (source IPs): {frame['src_ip'].nunique()}")
        
        windowed = make_windows(frame, 30.0, 10)
        log(f"Windowed sequences: {windowed.sequences.shape}")
        log(f"Unique groups in windows: {len(set(windowed.groups))}")
        log(f"Window stage distribution: {pd.Series(windowed.stages).value_counts().to_dict()}")
    except Exception as e:
        log(f"FATAL ERROR during validation: {e}")
        import traceback
        log(traceback.format_exc())
        return 1
    
    log("\n[STEP 4] Archive dataset validation PASSED")
    log("="*60)
    log("Pipeline preparation complete - ready for training")
    log("="*60)
    return 0


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        log(f"CRITICAL ERROR: {e}")
        import traceback
        log(traceback.format_exc())
        sys.exit(1)
