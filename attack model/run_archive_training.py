from __future__ import annotations

import glob
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

ARCHIVE_GLOB = r"C:/Users/mahes/Downloads/archive/*.csv"
OUTPUT_PATH = Path("data/archive_combined.csv")


def build_archive_dataset() -> Path:
    files = sorted(glob.glob(ARCHIVE_GLOB))
    if not files:
        raise FileNotFoundError(f"No archive CSVs found in {ARCHIVE_GLOB}")

    frames = [pd.read_csv(path, low_memory=False) for path in files]
    combined = pd.concat(frames, ignore_index=True)

    if "Timestamp" not in combined.columns:
        raise ValueError("Archive CSVs do not include the required Timestamp column")
    if "Label" not in combined.columns:
        raise ValueError("Archive CSVs do not include the required Label column")

    combined = combined.copy()
    combined["src_ip"] = [f"10.0.0.{i % 1000}" for i in range(len(combined))]
    combined["dst_ip"] = "10.0.0.2"
    combined["timestamp"] = pd.to_datetime(combined["Timestamp"], errors="coerce")
    combined["label"] = combined["Label"].astype(str).str.strip()
    combined["protocol"] = combined.get("Protocol", 0)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(OUTPUT_PATH, index=False)
    print(f"Created {OUTPUT_PATH} with {len(combined):,} rows")
    print(combined["label"].value_counts().head().to_dict())
    return OUTPUT_PATH


def main() -> None:
    dataset_path = build_archive_dataset()
    subprocess.run(
        [
            sys.executable,
            "train.py",
            "--data",
            str(dataset_path),
            "--window-seconds",
            "30",
            "--sequence-length",
            "10",
            "--backbone",
            "lstm",
            "--epochs",
            "5",
            "--patience",
            "2",
        ],
        check=False,
    )


if __name__ == "__main__":
    main()
