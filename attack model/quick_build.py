import pandas as pd
import glob
import os

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)
os.makedirs('data', exist_ok=True)
archive_dir = os.environ.get("ARCHIVE_DIR", str(BASE_DIR / 'archive'))
files = sorted(glob.glob(os.path.join(archive_dir, '*.csv')))
rows = []

for f in files:
    print(f"Processing {f}...", flush=True)
    for chunk in pd.read_csv(f, chunksize=5000, low_memory=False):
        data = pd.DataFrame()
        data['src_ip'] = '10.0.0.1'
        data['dst_ip'] = '10.0.0.2'
        data['src_port'] = 0
        data['dst_port'] = pd.to_numeric(chunk.get('Dst Port', 0), errors='coerce').fillna(0)
        data['protocol'] = pd.to_numeric(chunk.get('Protocol', 0), errors='coerce').fillna(0)
        data['tcp_flags'] = pd.to_numeric(chunk.get('SYN Flag Cnt', 0), errors='coerce').fillna(0)
        data['bytes_per_flow'] = pd.to_numeric(chunk.get('Flow Byts/s', 0), errors='coerce').fillna(0)
        data['packets_per_flow'] = pd.to_numeric(chunk.get('Tot Fwd Pkts', 0), errors='coerce').fillna(0)
        data['flow_duration'] = pd.to_numeric(chunk.get('Flow Duration', 0), errors='coerce').fillna(0)
        data['iat_mean'] = pd.to_numeric(chunk.get('Flow IAT Mean', 0), errors='coerce').fillna(0)
        data['iat_variance'] = pd.to_numeric(chunk.get('Flow IAT Std', 0), errors='coerce').fillna(0)
        data['iat_max'] = pd.to_numeric(chunk.get('Flow IAT Max', 0), errors='coerce').fillna(0)
        data['bidirectional_flow_ratio'] = 0
        data['ttl'] = 0
        data['ttl_variance'] = 0
        data['tcp_window_size'] = pd.to_numeric(chunk.get('Init Fwd Win Byts', 0), errors='coerce').fillna(0)
        data['ip_fragment_flags'] = 0
        data['payload_size'] = pd.to_numeric(chunk.get('Pkt Len Mean', 0), errors='coerce').fillna(0)
        data['port_scan_signature'] = 0
        data['retransmission_count'] = 0
        data['label'] = chunk['Label'].map({'Benign':'BENIGN','DoS attacks-GoldenEye':'DOS','DoS attacks-Slowloris':'DOS'}).fillna('BENIGN')
        data['timestamp'] = pd.to_datetime(chunk['Timestamp'], dayfirst=True, errors='coerce')
        rows.append(data.dropna(subset=['timestamp']))

print(f"Combining {len(rows)} chunks...", flush=True)
combined = pd.concat(rows, ignore_index=True)
combined.to_csv('data/archive_combined.csv', index=False)
print(f"SUCCESS: {len(combined)} rows")
print(combined['label'].value_counts().to_dict())
