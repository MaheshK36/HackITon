import glob
import os
import pandas as pd
BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)
os.makedirs('data', exist_ok=True)

archive_dir = os.environ.get("ARCHIVE_DIR", str(BASE_DIR / 'archive'))
files = sorted(glob.glob(os.path.join(archive_dir, '*.csv')))
all_rows = []

for filepath in files:
    fname = Path(filepath).name
    print(f"Reading {fname}...")
    
    # Read only first 5000 rows from each file to avoid memory issues
    try:
        df = pd.read_csv(filepath, nrows=5000, low_memory=False)
    except:
        # If nrows fails, try chunked reading
        chunks = []
        for chunk in pd.read_csv(filepath, chunksize=5000, low_memory=False):
            chunks.append(chunk)
            if len(chunks) >= 1:
                break
        df = chunks[0] if chunks else None
        if df is None:
            print(f"  SKIP: {fname}")
            continue
    
    if df is None or len(df) == 0:
        print(f"  SKIP: {fname}")
        continue
    
    print(f"  Read {len(df)} rows")
    
    # Map to schema
    row = pd.DataFrame()
    row['src_ip'] = '10.0.0.1'
    row['dst_ip'] = '10.0.0.2'
    row['src_port'] = 0
    row['dst_port'] = pd.to_numeric(df.get('Dst Port', 0), errors='coerce').fillna(0)
    row['protocol'] = pd.to_numeric(df.get('Protocol', 0), errors='coerce').fillna(0)
    row['tcp_flags'] = pd.to_numeric(df.get('SYN Flag Cnt', 0), errors='coerce').fillna(0)
    row['bytes_per_flow'] = pd.to_numeric(df.get('Flow Byts/s', 0), errors='coerce').fillna(0)
    row['packets_per_flow'] = pd.to_numeric(df.get('Tot Fwd Pkts', 0), errors='coerce').fillna(0)
    row['flow_duration'] = pd.to_numeric(df.get('Flow Duration', 0), errors='coerce').fillna(0)
    row['iat_mean'] = pd.to_numeric(df.get('Flow IAT Mean', 0), errors='coerce').fillna(0)
    row['iat_variance'] = pd.to_numeric(df.get('Flow IAT Std', 0), errors='coerce').fillna(0)
    row['iat_max'] = pd.to_numeric(df.get('Flow IAT Max', 0), errors='coerce').fillna(0)
    row['bidirectional_flow_ratio'] = 0.0
    row['ttl'] = 0.0
    row['ttl_variance'] = 0.0
    row['tcp_window_size'] = pd.to_numeric(df.get('Init Fwd Win Byts', 0), errors='coerce').fillna(0)
    row['ip_fragment_flags'] = 0.0
    row['payload_size'] = pd.to_numeric(df.get('Pkt Len Mean', 0), errors='coerce').fillna(0)
    row['port_scan_signature'] = 0.0
    row['retransmission_count'] = 0.0
    row['label'] = df['Label'].map({'Benign':'BENIGN','DoS attacks-GoldenEye':'DOS','DoS attacks-Slowloris':'DOS'}).fillna('BENIGN')
    row['timestamp'] = pd.to_datetime(df['Timestamp'], dayfirst=True, errors='coerce')
    
    row = row.dropna(subset=['timestamp'])
    if len(row) > 0:
        all_rows.append(row)
        print(f"  Processed: {len(row)} rows")

print(f"\nCombining {len(all_rows)} files...")
if all_rows:
    combined = pd.concat(all_rows, ignore_index=True)
    print(f"Total rows: {len(combined)}")
    print(f"Labels: {combined['label'].value_counts().to_dict()}")
    
    combined.to_csv('data/archive_combined.csv', index=False)
    print(f"Saved to data/archive_combined.csv")
else:
    print("ERROR: No data")
