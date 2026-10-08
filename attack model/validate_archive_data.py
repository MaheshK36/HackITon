from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from data_pipeline import load_csv, make_windows

OUT_PATH = Path('data/archive_combined.csv')


def main() -> None:
    os.makedirs('data', exist_ok=True)
    files = sorted(Path(r'C:/Users/mahes/Downloads/archive').glob('*.csv'))
    if not files:
        raise FileNotFoundError('No archive CSVs found')

    frames = []
    for path in files:
        df = pd.read_csv(path, low_memory=False)
        if df.empty:
            continue
        row = df[['Label', 'Timestamp', 'Dst Port', 'Protocol', 'Flow Duration', 'Tot Fwd Pkts', 'Tot Bwd Pkts', 'TotLen Fwd Pkts', 'TotLen Bwd Pkts', 'Flow Byts/s', 'Flow IAT Mean', 'Flow IAT Std', 'Flow IAT Max', 'Init Fwd Win Byts', 'Pkt Len Mean', 'SYN Flag Cnt']].copy()
        row['label'] = row['Label'].map({'Benign': 'BENIGN', 'DoS attacks-GoldenEye': 'DOS', 'DoS attacks-Slowloris': 'DOS'}).fillna('BENIGN')
        row['timestamp'] = pd.to_datetime(row['Timestamp'], dayfirst=True, errors='coerce')
        row['src_ip'] = ['10.0.0.1'] * len(row)
        row['dst_ip'] = ['10.0.0.2'] * len(row)
        row['src_port'] = 0
        row['protocol'] = row['Protocol']
        row['tcp_flags'] = row['SYN Flag Cnt']
        row['bytes_per_flow'] = row['Flow Byts/s']
        row['packets_per_flow'] = row['Tot Fwd Pkts']
        row['flow_duration'] = row['Flow Duration']
        row['iat_mean'] = row['Flow IAT Mean']
        row['iat_variance'] = row['Flow IAT Std']
        row['iat_max'] = row['Flow IAT Max']
        row['bidirectional_flow_ratio'] = 0.0
        row['ttl'] = 0.0
        row['ttl_variance'] = 0.0
        row['tcp_window_size'] = row['Init Fwd Win Byts']
        row['ip_fragment_flags'] = 0.0
        row['payload_size'] = row['Pkt Len Mean']
        row['port_scan_signature'] = 0.0
        row['retransmission_count'] = 0.0
        row = row[['src_ip', 'dst_ip', 'src_port', 'protocol', 'tcp_flags', 'bytes_per_flow', 'packets_per_flow', 'flow_duration', 'iat_mean', 'iat_variance', 'iat_max', 'bidirectional_flow_ratio', 'ttl', 'ttl_variance', 'tcp_window_size', 'ip_fragment_flags', 'payload_size', 'port_scan_signature', 'retransmission_count', 'label', 'timestamp']].dropna(subset=['timestamp']).head(5000)
        frames.append(row)

    if not frames:
        raise RuntimeError('No rows created from archive')
    out = pd.concat(frames, ignore_index=True)
    out.to_csv(OUT_PATH, index=False)
    print(f'archive_rows={len(out):,}')
    print(out['label'].value_counts().to_dict())

    frame = load_csv(OUT_PATH)
    print(f'canonical_rows={len(frame):,}')
    print(frame['stage'].value_counts().to_dict())

    windowed = make_windows(frame, 30.0, 10)
    print(f'sequences={windowed.sequences.shape[0]}')
    print(f'groups={len(set(windowed.groups))}')
    print(f'window_stages={pd.Series(windowed.stages).value_counts().to_dict()}')


if __name__ == '__main__':
    main()
