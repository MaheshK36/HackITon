"""Train/val/test leakage diagnostics."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ml.preprocessing.window_features import FEATURE_COLS


def leakage_check(splits: dict[str, pd.DataFrame]) -> dict:
    train = splits["train"]
    val = splits["val"]
    test = splits["test"]

    def keyset(df):
        return set(zip(df["dataset"].astype(str), df["source_file"].astype(str), df["window_start"].astype(str)))

    tr, va, te = keyset(train), keyset(val), keyset(test)
    overlap_tv = tr & va
    overlap_tt = tr & te
    overlap_vt = va & te

    print("=" * 80, flush=True)
    print("LEAKAGE CHECK", flush=True)
    print("=" * 80, flush=True)
    print(f"Exact window-id overlap train&val : {len(overlap_tv)}", flush=True)
    print(f"Exact window-id overlap train&test: {len(overlap_tt)}", flush=True)
    print(f"Exact window-id overlap val&test  : {len(overlap_vt)}", flush=True)

    # Per-class time order: max(train) should be <= min(val) <= min(test) within class
    order_violations = []
    for cls in sorted(set(train["label"]).union(val["label"]).union(test["label"])):
        t = train.loc[train["label"] == cls, "window_start"]
        v = val.loc[val["label"] == cls, "window_start"]
        s = test.loc[test["label"] == cls, "window_start"]
        if len(t) and len(v) and t.max() > v.min():
            order_violations.append(f"{cls}: train max {t.max()} > val min {v.min()}")
        if len(v) and len(s) and v.max() > s.min():
            order_violations.append(f"{cls}: val max {v.max()} > test min {s.min()}")
        if len(t) and len(s) and t.max() > s.min():
            order_violations.append(f"{cls}: train max {t.max()} > test min {s.min()}")
    print(f"Per-class chronological order violations: {len(order_violations)}", flush=True)
    for msg in order_violations[:20]:
        print(f"  {msg}", flush=True)

    # Global time overlap is EXPECTED with per-class splits
    def span(df, name):
        if df.empty:
            print(f"{name} empty")
            return
        print(f"{name} global time span: {df['window_start'].min()} -> {df['window_start'].max()}", flush=True)

    span(train, "train")
    span(val, "val")
    span(test, "test")
    print(
        "NOTE: global train/val/test time ranges MAY overlap because the split is per-class, not global.",
        flush=True,
    )

    # Duplicate feature vectors across splits
    def feat_keys(df):
        X = df[FEATURE_COLS].to_numpy(dtype=np.float64)
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        # round to reduce float noise
        Xr = np.round(X, 6)
        return {tuple(row) for row in Xr}

    ftr, fva, fte = feat_keys(train), feat_keys(val), feat_keys(test)
    print(f"Identical feature-vector overlap train&val : {len(ftr & fva)}", flush=True)
    print(f"Identical feature-vector overlap train&test: {len(ftr & fte)}", flush=True)
    print(f"Identical feature-vector overlap val&test  : {len(fva & fte)}", flush=True)

    # Label in features? FEATURE_COLS should not include label
    leaked_names = [c for c in FEATURE_COLS if "label" in c.lower() or c in {"is_attack", "attack_frac"}]
    print(f"Label-like names in FEATURE_COLS: {leaked_names or 'none'}", flush=True)

    flag = len(overlap_tv) or len(overlap_tt) or len(overlap_vt) or order_violations or leaked_names
    print(f"LEAKAGE FLAG (exact ids / order / label-in-features): {'FAIL' if flag else 'PASS'}", flush=True)
    if len(ftr & fte) > 0:
        print(
            "SOFT FLAG: some train/test windows have identical numeric feature vectors "
            "(possible duplicate traffic patterns, not necessarily label leakage).",
            flush=True,
        )
    return {
        "overlap_train_val": len(overlap_tv),
        "overlap_train_test": len(overlap_tt),
        "overlap_val_test": len(overlap_vt),
        "order_violations": order_violations,
        "identical_features_train_test": len(ftr & fte),
        "hard_fail": bool(flag),
    }
