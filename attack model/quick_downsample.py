from pathlib import Path
import pandas as pd

data_path = Path(__file__).resolve().parent / 'data' / 'archive_combined.csv'
df = pd.read_csv(data_path)
s = df.sample(n=50000, random_state=42)
# Create multiple source IP groups for train/val/test splitting
s['src_ip'] = ['10.0.' + str(i//5000) + '.1' for i in range(len(s))]
s['dst_ip'] = '10.0.0.254'
s.to_csv(data_path, index=False)
print(f"OK: {len(s)} rows, {s['src_ip'].nunique()} groups, labels: {s['label'].value_counts().to_dict()}")
