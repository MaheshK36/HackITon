"""End-to-end: CIC-IDS-2018 alone -> windows -> combine CTU-13 -> split -> baselines.

Usage (from repo root):
  python ml/preprocessing/run_combined_eval.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ml.models.baseline import looks_suspiciously_perfect, train_and_report  # noqa: E402
from ml.preprocessing.data_loader import (  # noqa: E402
    iter_cic_chunks,
    iter_ctu_chunks,
    list_cic_files,
    list_ctu_files,
)
from ml.preprocessing.leakage_check import leakage_check  # noqa: E402
from ml.preprocessing.split_utils import chronological_split_per_class, print_split_report  # noqa: E402
from ml.preprocessing.validate_dataset import validate_cicids2018  # noqa: E402
from ml.preprocessing.window_features import (  # noqa: E402
    FEATURE_COLS,
    WINDOW_SEC,
    flows_to_partial_windows,
    merge_partial_windows,
    print_window_report,
)

SEQ_LEN = 10
PROCESSED = ROOT / "data" / "processed"
SEQUENCES = ROOT / "data" / "sequences"
MODELS = ROOT / "models"


def extract_windows(files, chunk_iter_fn, title: str) -> pd.DataFrame:
    print("=" * 80, flush=True)
    print(title, flush=True)
    print("=" * 80, flush=True)
    parts = []
    t0 = time.time()
    n_flows = 0
    for path in files:
        print(f"Windowing {path.name} ...", flush=True)
        n_chunks = 0
        for chunk in chunk_iter_fn(path):
            n_chunks += 1
            n_flows += len(chunk)
            if chunk.empty:
                continue
            parts.append(flows_to_partial_windows(chunk))
            if n_chunks % 5 == 0:
                print(f"  {path.name}: {n_chunks} chunks, {n_flows:,} flows so far", flush=True)
        print(f"  done {path.name} ({n_chunks} chunks)", flush=True)
    windows = merge_partial_windows(parts)
    print(f"Flow rows consumed: {n_flows:,}  elapsed={time.time() - t0:.1f}s", flush=True)
    return windows


def build_sequences(windows: pd.DataFrame, seq_len: int = SEQ_LEN) -> pd.DataFrame:
    """Sliding sequences of consecutive 60s windows within each (dataset, source_file).

    Label = last window label. Sequences must be time-contiguous (exactly 60s steps).
    """
    rows = []
    for (dataset, source_file), g in windows.groupby(["dataset", "source_file"], sort=False):
        g = g.sort_values("window_start").reset_index(drop=True)
        starts = pd.to_datetime(g["window_start"])
        feats = g[FEATURE_COLS].to_numpy(float)
        labels = g["label"].to_numpy()
        is_atk = g["is_attack"].to_numpy(int)
        t_unix = (starts.astype("datetime64[ns]").astype("int64") // 10**9).to_numpy()
        for i in range(seq_len - 1, len(g)):
            sl = slice(i - seq_len + 1, i + 1)
            diffs = np.diff(t_unix[sl])
            if diffs.size != seq_len - 1:
                continue
            if not np.all(diffs == WINDOW_SEC):
                continue
            last_label = labels[i]
            rows.append(
                {
                    "dataset": dataset,
                    "source_file": source_file,
                    "window_start": starts.iloc[i],  # label time = last window
                    "seq_end": starts.iloc[i],
                    "seq_start": starts.iloc[i - seq_len + 1],
                    "label": last_label,
                    "is_attack": int(is_atk[i]),
                    **{f: float(feats[i, j]) for j, f in enumerate(FEATURE_COLS)},
                    # sequence uses LAST window features for the flat baseline
                    # (LSTM would use the full matrix; Phase 2 baselines are flat)
                }
            )
    return pd.DataFrame(rows)


def print_gate(baseline_payload: dict, splits: dict[str, pd.DataFrame]) -> None:
    test_n = len(splits["test"])
    rf = baseline_payload["random_forest"]
    lr = baseline_payload["logistic_regression"]
    rf_perf = looks_suspiciously_perfect(rf)
    lr_perf = looks_suspiciously_perfect(lr)
    print("=" * 80, flush=True)
    print("PHASE 3 READINESS GATE", flush=True)
    print("=" * 80, flush=True)
    print(f"Test set size: {test_n:,}", flush=True)
    print(f"RF suspiciously perfect on val/test: {rf_perf}", flush=True)
    print(f"LR suspiciously perfect on val/test: {lr_perf}", flush=True)
    reasonably_sized = test_n >= 200
    non_trivial_lr = (0.55 <= lr["test"]["f1"] <= 0.99) and (lr["test"]["fpr"] > 0.0 or lr["test"]["fn"] > 0)
    ready = (not rf_perf) and reasonably_sized and (not lr_perf) and non_trivial_lr
    if ready:
        print(
            "READY FOR PHASE 3: combined metrics look non-perfect and the test set is reasonably sized.",
            flush=True,
        )
        print("Waiting for confirmation before proceeding to the temporal/world model.", flush=True)
    else:
        print("NOT READY FOR PHASE 3.", flush=True)
        if rf_perf:
            print("  - Random Forest val/test still looks suspiciously perfect. Treat as a remaining red flag.", flush=True)
        if lr_perf:
            print("  - Logistic Regression also looks suspiciously perfect — labels may be trivially encoded in features/time.", flush=True)
        if not reasonably_sized:
            print(f"  - Test set too small ({test_n}).", flush=True)
        if not non_trivial_lr:
            print("  - Logistic Regression test metrics are not in a stable non-trivial band.", flush=True)
        print("Do not start Phase 3 until this is resolved.", flush=True)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-validate", action="store_true")
    parser.add_argument("--from-windows", action="store_true", help="Load combined windows parquet and skip re-windowing")
    parser.add_argument(
        "--stop-after",
        default="all",
        choices=["validate", "cic-windows", "combined", "all"],
    )
    args = parser.parse_args()

    PROCESSED.mkdir(parents=True, exist_ok=True)
    SEQUENCES.mkdir(parents=True, exist_ok=True)

    if args.from_windows:
        comb_path = PROCESSED / "windows_combined.parquet"
        cic_path = PROCESSED / "windows_cicids2018.parquet"
        ctu_path = PROCESSED / "windows_ctu13.parquet"
        cic_windows = pd.read_parquet(cic_path)
        ctu_windows = pd.read_parquet(ctu_path)
        combined = pd.read_parquet(comb_path)
        print_window_report(cic_windows, "CIC-IDS-2018 WINDOW REPORT (loaded, 60s)")
        print_window_report(ctu_windows, "CTU-13 WINDOW REPORT (loaded, 60s)")
        print_window_report(combined, "COMBINED CTU-13 + CIC-IDS-2018 WINDOW REPORT (loaded, 60s)")
        sequences = build_sequences(combined, SEQ_LEN)
        print("=" * 80, flush=True)
        print(f"SEQUENCES (len={SEQ_LEN} contiguous {WINDOW_SEC}s windows; label=last window)")
        print("=" * 80, flush=True)
        print(f"Sequence count: {len(sequences):,}", flush=True)
        if sequences.empty:
            print("No contiguous sequences; falling back to splitting windows directly.", flush=True)
            sequences = combined.copy()
            item_name = "windows (sequence fallback)"
        else:
            item_name = "sequences"
            vc = sequences["label"].value_counts()
            print("Sequence class distribution:")
            for k, v in vc.items():
                print(f"  {str(k):40s}  {v:12,}  ({100.0 * v / len(sequences):6.2f}%)")
        seq_path = SEQUENCES / "sequences_combined.parquet"
        sequences.to_parquet(seq_path, index=False)
        print(f"Wrote {seq_path}", flush=True)
        splits = chronological_split_per_class(sequences)
        print_split_report(splits, item_name=item_name)
        for name in ("train", "val", "test"):
            splits[name].to_parquet(SEQUENCES / f"{name}.parquet", index=False)
        leak = leakage_check(splits)
        baseline_payload = train_and_report(splits, MODELS)
        (PROCESSED / "leakage_report.json").write_text(json.dumps(leak, indent=2, default=str), encoding="utf-8")
        print_gate(baseline_payload, splits)
        return

    # 1. CIC raw validation in isolation
    if not args.skip_validate:
        cic_raw = validate_cicids2018()
        if cic_raw.get("status") != "PASS":
            print("Stopping: CIC-IDS-2018 raw validation failed.", flush=True)
            sys.exit(2)
    if args.stop_after == "validate":
        return

    # 2. CIC windows alone
    cic_path = PROCESSED / "windows_cicids2018.parquet"
    if args.skip_validate and cic_path.exists() and args.stop_after != "cic-windows":
        print(f"Loading existing CIC windows from {cic_path}", flush=True)
        cic_windows = pd.read_parquet(cic_path)
        print_window_report(cic_windows, "CIC-IDS-2018 WINDOW REPORT (loaded, 60s)")
    else:
        cic_files = list_cic_files()
        cic_windows = extract_windows(cic_files, iter_cic_chunks, "CIC-IDS-2018 60s WINDOWING (alone)")
        print_window_report(cic_windows, "CIC-IDS-2018 WINDOW REPORT (alone, 60s)")
        cic_windows.to_parquet(cic_path, index=False)
        print(f"Wrote {cic_path}  rows={len(cic_windows):,}", flush=True)
    if cic_windows.empty:
        print("Stopping: no CIC windows.", flush=True)
        sys.exit(2)
    if args.stop_after == "cic-windows":
        return

    # 3. CTU-13 windows + combine
    ctu_files = list_ctu_files()
    print("=" * 80, flush=True)
    print("CTU-13 FILES FOR COMBINE STEP", flush=True)
    print("=" * 80, flush=True)
    if not ctu_files:
        print("No CTU-13 files found under data/raw/ctu13/. Combined dataset cannot be built.", flush=True)
        sys.exit(2)
    for p in ctu_files:
        print(f"  - {p}  ({p.stat().st_size:,} bytes)", flush=True)

    ctu_windows = extract_windows(ctu_files, iter_ctu_chunks, "CTU-13 60s WINDOWING")
    print_window_report(ctu_windows, "CTU-13 WINDOW REPORT (60s)")
    ctu_path = PROCESSED / "windows_ctu13.parquet"
    ctu_windows.to_parquet(ctu_path, index=False)
    print(f"Wrote {ctu_path}  rows={len(ctu_windows):,}", flush=True)

    combined = pd.concat([cic_windows, ctu_windows], ignore_index=True)
    print_window_report(combined, "COMBINED CTU-13 + CIC-IDS-2018 WINDOW REPORT (60s)")
    comb_path = PROCESSED / "windows_combined.parquet"
    combined.to_parquet(comb_path, index=False)
    print(f"Wrote {comb_path}  rows={len(combined):,}", flush=True)
    if args.stop_after == "combined":
        return

    # 4. Sequences + per-class chronological split
    sequences = build_sequences(combined, SEQ_LEN)
    print("=" * 80, flush=True)
    print(f"SEQUENCES (len={SEQ_LEN} contiguous {WINDOW_SEC}s windows; label=last window)")
    print("=" * 80, flush=True)
    print(f"Sequence count: {len(sequences):,}", flush=True)
    if sequences.empty:
        print("No contiguous sequences; falling back to splitting windows directly.", flush=True)
        sequences = combined.copy()
        item_name = "windows (sequence fallback)"
    else:
        item_name = "sequences"
        vc = sequences["label"].value_counts()
        print("Sequence class distribution:")
        for k, v in vc.items():
            print(f"  {str(k):40s}  {v:12,}  ({100.0 * v / len(sequences):6.2f}%)")

    seq_path = SEQUENCES / "sequences_combined.parquet"
    sequences.to_parquet(seq_path, index=False)
    print(f"Wrote {seq_path}", flush=True)

    splits = chronological_split_per_class(sequences)
    print_split_report(splits, item_name=item_name)
    for name in ("train", "val", "test"):
        splits[name].to_parquet(SEQUENCES / f"{name}.parquet", index=False)

    # 5. Leakage + baselines
    leak = leakage_check(splits)
    baseline_payload = train_and_report(splits, MODELS)
    (PROCESSED / "leakage_report.json").write_text(json.dumps(leak, indent=2, default=str), encoding="utf-8")

    # 6-7. Gate
    print_gate(baseline_payload, splits)


if __name__ == "__main__":
    main()
