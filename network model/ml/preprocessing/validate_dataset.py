"""Validate CIC-IDS-2018 (and optionally CTU-13) in isolation.

Usage:
  python ml/preprocessing/validate_dataset.py --dataset cicids2018
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ml.preprocessing.data_loader import (  # noqa: E402
    CIC_DIR,
    CTU_DIR,
    list_cic_files,
    list_ctu_files,
    normalize_attack_label,
    peek_cic_columns,
)


def _print(msg: str) -> None:
    print(msg, flush=True)


def validate_cicids2018() -> dict:
    files = list_cic_files()
    _print("=" * 80)
    _print("CIC-IDS-2018 RAW VALIDATION (isolated, no CTU-13)")
    _print("=" * 80)
    _print(f"Directory: {CIC_DIR}")
    _print(f"CSV files found: {len(files)}")
    for p in files:
        _print(f"  - {p.name}  ({p.stat().st_size:,} bytes)")

    if not files:
        _print("FAIL: no CSV files in data/raw/cicids2018/")
        return {"status": "FAIL", "reason": "no_files", "raw_row_count": 0}

    label_counts: Counter[str] = Counter()
    raw_rows = 0
    skipped_header_rows = 0
    parse_fail_ts = 0
    tmin = None
    tmax = None
    columns_by_file: dict[str, list[str]] = {}
    files_ok = 0

    for path in files:
        _print("-" * 80)
        _print(f"Scanning {path.name} ...")
        cols = peek_cic_columns(path)
        columns_by_file[path.name] = cols
        _print(f"  Detected columns ({len(cols)}): {cols}")

        cmap = {c.strip().lower(): c for c in cols}
        ts_name = cmap.get("timestamp")
        label_name = cmap.get("label")
        if not ts_name or not label_name:
            _print("  FAIL: missing Timestamp or Label column")
            continue

        raw_header = pd.read_csv(path, nrows=0)
        raw_map = {str(c).strip().replace("\ufeff", ""): c for c in raw_header.columns}
        usecols = [raw_map[ts_name], raw_map[label_name]]

        file_rows = 0
        file_labels: Counter[str] = Counter()
        file_tmin = None
        file_tmax = None

        for chunk in pd.read_csv(path, usecols=usecols, chunksize=400_000, dtype=str, low_memory=False):
            chunk.columns = [str(c).strip().replace("\ufeff", "") for c in chunk.columns]
            ts_s = chunk[ts_name].astype(str).str.strip()
            lab_s = chunk[label_name].astype(str).str.strip()
            header_mask = ts_s.str.lower().eq("timestamp") | lab_s.str.lower().eq("label")
            skipped_header_rows += int(header_mask.sum())
            chunk = chunk.loc[~header_mask]
            if chunk.empty:
                continue
            ts = pd.to_datetime(chunk[ts_name], errors="coerce", dayfirst=True)
            bad_ts = ts.isna()
            parse_fail_ts += int(bad_ts.sum())
            good = chunk.loc[~bad_ts].copy()
            good_ts = ts.loc[~bad_ts]
            n = len(good)
            file_rows += n
            raw_rows += n
            if n == 0:
                continue
            mn, mx = good_ts.min(), good_ts.max()
            file_tmin = mn if file_tmin is None else min(file_tmin, mn)
            file_tmax = mx if file_tmax is None else max(file_tmax, mx)
            tmin = mn if tmin is None else min(tmin, mn)
            tmax = mx if tmax is None else max(tmax, mx)
            labs = good[label_name].map(lambda x: normalize_attack_label(x, "cicids2018"))
            file_labels.update(labs.tolist())
            label_counts.update(labs.tolist())

        files_ok += 1
        _print(f"  Parsed rows: {file_rows:,}")
        if file_tmin is not None:
            _print(f"  Time range: {file_tmin}  ->  {file_tmax}")
        _print("  Class distribution (this file):")
        for k, v in sorted(file_labels.items(), key=lambda kv: (-kv[1], kv[0])):
            pct = 100.0 * v / max(file_rows, 1)
            _print(f"    {k:40s}  {v:12,}  ({pct:6.2f}%)")

    _print("=" * 80)
    _print("CIC-IDS-2018 AGGREGATE")
    _print("=" * 80)
    _print(f"Raw row count (parsed, header-repeats excluded): {raw_rows:,}")
    _print(f"Repeated header rows skipped: {skipped_header_rows:,}")
    _print(f"Timestamp parse failures dropped: {parse_fail_ts:,}")
    _print(f"Union of detected columns: {sorted(set().union(*columns_by_file.values()) if columns_by_file else [])}")
    if tmin is None:
        _print("Time range: EMPTY")
    else:
        _print(f"Time range: {tmin}  ->  {tmax}")
    _print("Class distribution (benign vs each attack type):")
    for k, v in sorted(label_counts.items(), key=lambda kv: (-kv[1], kv[0])):
        pct = 100.0 * v / max(raw_rows, 1)
        _print(f"  {k:40s}  {v:12,}  ({pct:6.2f}%)")

    malformed = raw_rows == 0 or tmin is None or not label_counts
    status = "FAIL" if malformed else "PASS"
    _print("-" * 80)
    _print(f"MALFORMED/EMPTY CHECK: {status}")
    if malformed:
        _print("Do not proceed. Dataset is empty or timestamps/labels could not be parsed.")
    else:
        _print("Dataset is usable. Proceeding is allowed.")

    report = {
        "status": status,
        "raw_row_count": int(raw_rows),
        "skipped_header_rows": int(skipped_header_rows),
        "timestamp_parse_failures": int(parse_fail_ts),
        "time_min": None if tmin is None else str(tmin),
        "time_max": None if tmax is None else str(tmax),
        "class_distribution": dict(label_counts),
        "columns_by_file": columns_by_file,
        "n_files": len(files),
        "files_ok": files_ok,
    }
    out = ROOT / "data" / "processed" / "cicids2018_raw_validation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    _print(f"Wrote {out}")
    return report


def validate_ctu13() -> dict:
    files = list_ctu_files()
    _print("=" * 80)
    _print("CTU-13 RAW VALIDATION")
    _print("=" * 80)
    _print(f"Directory: {CTU_DIR}")
    _print(f"Files found: {len(files)}")
    for p in files:
        _print(f"  - {p}")
    if not files:
        _print("FAIL: no CTU-13 files in data/raw/ctu13/")
        return {"status": "FAIL", "raw_row_count": 0}
    return {"status": "PASS", "n_files": len(files)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="cicids2018", choices=["cicids2018", "ctu13", "all"])
    args = parser.parse_args()
    if args.dataset in {"cicids2018", "all"}:
        report = validate_cicids2018()
        if report.get("status") != "PASS":
            sys.exit(2)
    if args.dataset in {"ctu13", "all"}:
        validate_ctu13()


if __name__ == "__main__":
    main()
