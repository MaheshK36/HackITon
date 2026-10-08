import pandas as pd
from pathlib import Path

os.chdir(Path(__file__).resolve().parent)
print("Reading archive_combined.csv in chunks...", flush=True)

# Read only first 50K rows efficiently
chunks = []
for i, chunk in enumerate(pd.read_csv('data/archive_combined.csv', chunksize=10000, low_memory=False)):
    print(f"  Read chunk {i+1}...", flush=True)
    chunks.append(chunk)
    if len(chunks) >= 5:  # 5 chunks * 10K = 50K rows
        break

result = pd.concat(chunks, ignore_index=True)
print(f"Combined {len(result):,} rows", flush=True)
print(f"Labels: {result['label'].value_counts().to_dict()}", flush=True)

result.to_csv('data/archive_combined.csv', index=False)
print(f"Saved to data/archive_combined.csv", flush=True)
