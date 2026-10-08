import glob
import os
import pandas as pd
BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)
os.makedirs('data', exist_ok=True)

archive_dir = os.environ.get("ARCHIVE_DIR", str(BASE_DIR / 'archive'))
files = sorted(glob.glob(os.path.join(archive_dir, '*.csv')))
frames = []

for file in files:
    try:
        # Read in chunks to avoid memory error
        chunks = []
        for chunk in pd.read_csv(file, low_memory=False, chunksize=10000):
            if len(chunk) == 0:
                continue
            
            out = pd.DataFrame()
            out['src_ip'] = '10.0.0.1'
            out['dst_ip'] = '10.0.0.2'
            out['src_port'] = 0
            out['dst_port'] = pd.to_numeric(chunk.get('Dst Port', 0), errors='coerce').fillna(0).astype(int)
            out['protocol'] = pd.to_numeric(chunk.get('Protocol', 0), errors='coerce').fillna(0).astype(int)
            out['tcp_flags'] = pd.to_numeric(chunk.get('SYN Flag Cnt', 0), errors='coerce').fillna(0)
            out['bytes_per_flow'] = pd.to_numeric(chunk.get('Flow Byts/s', 0), errors='coerce').fillna(0)
            out['packets_per_flow'] = pd.to_numeric(chunk.get('Tot Fwd Pkts', 0), errors='coerce').fillna(0)
            out['flow_duration'] = pd.to_numeric(chunk.get('Flow Duration', 0), errors='coerce').fillna(0)
            out['iat_mean'] = pd.to_numeric(chunk.get('Flow IAT Mean', 0), errors='coerce').fillna(0)
            out['iat_variance'] = pd.to_numeric(chunk.get('Flow IAT Std', 0), errors='coerce').fillna(0)
            out['iat_max'] = pd.to_numeric(chunk.get('Flow IAT Max', 0), errors='coerce').fillna(0)
            out['bidirectional_flow_ratio'] = 0.0
            out['ttl'] = 0.0
            out['ttl_variance'] = 0.0
            out['tcp_window_size'] = pd.to_numeric(chunk.get('Init Fwd Win Byts', 0), errors='coerce').fillna(0)
            out['ip_fragment_flags'] = 0.0
            out['payload_size'] = pd.to_numeric(chunk.get('Pkt Len Mean', 0), errors='coerce').fillna(0)
            out['port_scan_signature'] = 0.0
            out['retransmission_count'] = 0.0
            out['label'] = chunk['Label'].map({'Benign':'BENIGN','DoS attacks-GoldenEye':'DOS','DoS attacks-Slowloris':'DOS'}).fillna('BENIGN')
            out['timestamp'] = pd.to_datetime(chunk['Timestamp'], dayfirst=True, errors='coerce')
            
            out = out.dropna(subset=['timestamp'])
            if len(out) > 0:
                chunks.append(out)
        
        if chunks:
            file_frame = pd.concat(chunks, ignore_index=True).head(5000)
            frames.append(file_frame)
            print(f"Processed {Path(file).name}: {len(file_frame)} rows")
    except Exception as e:
        print(f"Error reading {file}: {e}")

if len(frames) > 0:
    combined = pd.concat(frames, ignore_index=True)
    combined.to_csv('data/archive_combined.csv', index=False)
    print(f"SUCCESS: Wrote {len(combined)} rows to data/archive_combined.csv")
    print(f"Label distribution: {combined['label'].value_counts().to_dict()}")
    exit(0)
else:
    print("FAILED: No frames to combine")
    exit(1)
