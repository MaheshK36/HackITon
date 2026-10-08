#!/usr/bin/env python
"""Build archive dataset with robust memory handling."""
import glob
import os
import sys
import pandas as pd
from pathlib import Path

def main():
    base_dir = Path(__file__).resolve().parent
    os.chdir(base_dir)
    os.makedirs('data', exist_ok=True)
    
    archive_dir = os.environ.get("ARCHIVE_DIR", str(base_dir / 'archive'))
    archive_files = sorted(glob.glob(os.path.join(archive_dir, '*.csv')))
    if not archive_files:
        print("ERROR: No archive files found")
        return False
    
    print(f"Found {len(archive_files)} archive files")
    all_data = []
    
    for file_path in archive_files:
        file_name = Path(file_path).name
        print(f"\nProcessing {file_name}...")
        
        try:
            # Read ONLY first 5000 rows to avoid memory crash
            print(f"  Reading (limited to 5000 rows)...")
            df = pd.read_csv(file_path, nrows=5000, low_memory=False)
            print(f"  Loaded {len(df)} rows")
            
            if df.empty:
                print(f"  SKIP: Empty")
                continue
            
            # Build canonical schema
            print(f"  Mapping to canonical schema...")
            data = {}
            data['src_ip'] = ['10.0.0.1'] * len(df)
            data['dst_ip'] = ['10.0.0.2'] * len(df)
            data['src_port'] = [0] * len(df)
            data['dst_port'] = pd.to_numeric(df.get('Dst Port', 0), errors='coerce').fillna(0).tolist()
            data['protocol'] = pd.to_numeric(df.get('Protocol', 0), errors='coerce').fillna(0).tolist()
            data['tcp_flags'] = pd.to_numeric(df.get('SYN Flag Cnt', 0), errors='coerce').fillna(0).tolist()
            data['bytes_per_flow'] = pd.to_numeric(df.get('Flow Byts/s', 0), errors='coerce').fillna(0).tolist()
            data['packets_per_flow'] = pd.to_numeric(df.get('Tot Fwd Pkts', 0), errors='coerce').fillna(0).tolist()
            data['flow_duration'] = pd.to_numeric(df.get('Flow Duration', 0), errors='coerce').fillna(0).tolist()
            data['iat_mean'] = pd.to_numeric(df.get('Flow IAT Mean', 0), errors='coerce').fillna(0).tolist()
            data['iat_variance'] = pd.to_numeric(df.get('Flow IAT Std', 0), errors='coerce').fillna(0).tolist()
            data['iat_max'] = pd.to_numeric(df.get('Flow IAT Max', 0), errors='coerce').fillna(0).tolist()
            data['bidirectional_flow_ratio'] = [0.0] * len(df)
            data['ttl'] = [0.0] * len(df)
            data['ttl_variance'] = [0.0] * len(df)
            data['tcp_window_size'] = pd.to_numeric(df.get('Init Fwd Win Byts', 0), errors='coerce').fillna(0).tolist()
            data['ip_fragment_flags'] = [0.0] * len(df)
            data['payload_size'] = pd.to_numeric(df.get('Pkt Len Mean', 0), errors='coerce').fillna(0).tolist()
            data['port_scan_signature'] = [0.0] * len(df)
            data['retransmission_count'] = [0.0] * len(df)
            data['label'] = df['Label'].map({'Benign': 'BENIGN', 'DoS attacks-GoldenEye': 'DOS', 'DoS attacks-Slowloris': 'DOS'}).fillna('BENIGN').tolist()
            data['timestamp'] = pd.to_datetime(df['Timestamp'], dayfirst=True, errors='coerce').tolist()
            
            out_df = pd.DataFrame(data)
            out_df = out_df.dropna(subset=['timestamp'])
            
            if len(out_df) > 0:
                print(f"  Processed {len(out_df)} rows with valid timestamps")
                all_data.append(out_df)
            else:
                print(f"  SKIP: No valid timestamps")
                
        except Exception as e:
            print(f"  ERROR: {e}")
            continue
    
    if not all_data:
        print("\nERROR: No data was processed")
        return False
    
    print(f"\n{'='*60}")
    print(f"Combining {len(all_data)} file datasets...")
    combined = pd.concat(all_data, ignore_index=True)
    
    print(f"Total rows: {len(combined):,}")
    print(f"Label distribution:")
    for label, count in combined['label'].value_counts().items():
        print(f"  {label}: {count:,}")
    
    out_file = Path('data/archive_combined.csv')
    print(f"\nWriting to {out_file}...")
    combined.to_csv(out_file, index=False)
    file_size = out_file.stat().st_size / (1024*1024)
    print(f"SUCCESS: Wrote {len(combined):,} rows ({file_size:.1f} MB)")
    print(f"{'='*60}\n")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
