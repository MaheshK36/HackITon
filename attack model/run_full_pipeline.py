#!/usr/bin/env python
"""Build and validate archive dataset, then train the model."""
import glob
import os
import sys
from pathlib import Path

import pandas as pd

def main():
    os.chdir(r'C:/Users/mahes/Downloads/attack model')
    os.makedirs('data', exist_ok=True)
    
    # ===== BUILD ARCHIVE DATASET =====
    archive_glob = r'C:/Users/mahes/Downloads/archive/*.csv'
    files = sorted(glob.glob(archive_glob))
    print(f"[1] Found {len(files)} archive files", file=sys.stderr, flush=True)
    
    if not files:
        print("ERROR: No archive files found", file=sys.stderr, flush=True)
        return 1
    
    frames = []
    for file in files:
        try:
            df = pd.read_csv(file, low_memory=False)
            print(f"[2] Read {Path(file).name}: shape={df.shape}", file=sys.stderr, flush=True)
            
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
            out['label'] = df['Label'].map({'Benign':'BENIGN', 'DoS attacks-GoldenEye':'DOS', 'DoS attacks-Slowloris':'DOS'}).fillna('BENIGN')
            out['timestamp'] = pd.to_datetime(df['Timestamp'], dayfirst=True, errors='coerce')
            
            out = out.dropna(subset=['timestamp']).head(5000)
            if not out.empty:
                frames.append(out)
                print(f"[3] Processed: {len(out)} rows", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"[ERROR] {file}: {e}", file=sys.stderr, flush=True)
    
    if not frames:
        print("ERROR: No valid frames", file=sys.stderr, flush=True)
        return 1
    
    combined = pd.concat(frames, ignore_index=True)
    print(f"[4] Combined: {len(combined)} rows, labels={combined['label'].value_counts().to_dict()}", file=sys.stderr, flush=True)
    
    out_path = Path('data/archive_combined.csv')
    combined.to_csv(out_path, index=False)
    print(f"[5] Wrote to {out_path}", file=sys.stderr, flush=True)
    
    # ===== VALIDATE WITH CANONICAL PIPELINE =====
    try:
        from data_pipeline import load_csv, make_windows
        frame = load_csv(out_path)
        print(f"[6] Canonical load: {len(frame)} rows, stages={frame['stage'].value_counts().to_dict()}", file=sys.stderr, flush=True)
        
        windowed = make_windows(frame, 30.0, 10)
        print(f"[7] Windowed: {windowed.sequences.shape[0]} sequences, groups={len(set(windowed.groups))}", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"[ERROR] Validation failed: {e}", file=sys.stderr, flush=True)
        return 1
    
    print("[SUCCESS] Archive dataset ready", file=sys.stderr, flush=True)
    return 0

if __name__ == '__main__':
    sys.exit(main())
