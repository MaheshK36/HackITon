import os
import sys
from pathlib import Path
import pandas as pd

script_dir = Path(__file__).resolve().parent
data_file = script_dir / "data" / "archive_combined.csv"

if data_file.exists():
    df = pd.read_csv(data_file)
    df = df.sample(n=min(50000, len(df)), random_state=42).reset_index(drop=True)
    df['src_ip'] = ['10.0.' + str(i // 5000) + '.1' for i in range(len(df))]
    df['dst_ip'] = '10.0.0.254'
    df.to_csv(data_file, index=False)
    with open(script_dir / 'downsample_done.txt', 'w') as f:
        f.write(f"OK: {len(df)} rows, {df['src_ip'].nunique()} groups\n")
    print("DONE")
