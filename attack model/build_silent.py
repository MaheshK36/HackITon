#!/usr/bin/env python
"""Silently build archive CSV without any output."""
import glob
import os
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)
os.makedirs('data', exist_ok=True)

# Read and combine archive files
archive_dir = os.environ.get("ARCHIVE_DIR", str(BASE_DIR / 'archive'))
files = sorted(glob.glob(os.path.join(archive_dir, '*.csv')))
frames = []

for file in files:
    try:
        df = pd.read_csv(file, low_memory=False)
        if df.empty:
            continue
        
        # Build schema
        out = pd.DataFrame()
        out['src_ip'] = '10.0.0.1'
        out['dst_ip'] = '10.0.0.2'
        out['src_port'] = 0
        out['dst_port'] = pd.to_numeric(df.get('Dst Port', 0), errors='coerce').fillna(0).astype(int)
        out['protocol'] = pd.to_numeric(df.get('Protocol', 0), errors='coerce').fillna(0).astype(int)
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
    except:
        pass

if frames:
    combined = pd.concat(frames, ignore_index=True)
    combined.to_csv('data/archive_combined.csv', index=False)
