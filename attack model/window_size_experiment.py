"""Compare temporal window sizes before choosing one for training.

Example: python window_size_experiment.py --data data/CIC-IDS-2018.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

from data_pipeline import DEFAULT_DATA_PATHS, SEQUENCE_LENGTH, load_csv, load_frame, window_report
from train import synthetic_frame

WINDOW_SIZES_SECONDS = (10.0, 30.0, 60.0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=next((path for path in DEFAULT_DATA_PATHS if Path(path).exists()), None))
    parser.add_argument("--sequence-length", type=int, default=SEQUENCE_LENGTH)
    parser.add_argument("--synthetic", action="store_true")
    args = parser.parse_args()
    if args.synthetic:
        frame = load_frame(synthetic_frame())
    elif args.data:
        frame = load_csv(args.data)
    else:
        parser.error("Provide --data PATH or use --synthetic.")
    report = window_report(frame, WINDOW_SIZES_SECONDS, args.sequence_length)
    print("Window-size experiment (run this before committing to a training window)\n")
    print(report.to_string(index=False))
    low = report[report["sequence_count"] < 300]
    if not low.empty:
        print("\n!!! WARNING: at least one setting has fewer than 300 sequences. Review this before training. !!!")
        print(low[["window_seconds", "sequence_count"]].to_string(index=False))


if __name__ == "__main__":
    main()