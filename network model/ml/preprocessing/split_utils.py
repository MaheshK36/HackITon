"""Chronological per-class 70/15/15 split."""

from __future__ import annotations

import pandas as pd


def chronological_split_per_class(
    df: pd.DataFrame,
    time_col: str = "window_start",
    label_col: str = "label",
    train_frac: float = 0.70,
    val_frac: float = 0.15,
    test_frac: float = 0.15,
) -> dict[str, pd.DataFrame]:
    if abs(train_frac + val_frac + test_frac - 1.0) > 1e-6:
        raise ValueError("fractions must sum to 1")

    parts = {"train": [], "val": [], "test": []}
    notes = []
    for cls, g in df.groupby(label_col, sort=False):
        g = g.sort_values(time_col).reset_index(drop=True)
        n = len(g)
        if n == 0:
            continue
        n_train = int(n * train_frac)
        n_val = int(n * val_frac)
        n_test = n - n_train - n_val
        if n < 3:
            # too small to split honestly — keep in train, flag it
            parts["train"].append(g)
            notes.append(f"class={cls!r} n={n}: too small for 70/15/15, all rows -> train")
            continue
        if n_test == 0:
            n_test = 1
            if n_train > 1:
                n_train -= 1
        if n_val == 0 and n_train > 1:
            n_val = 1
            n_train -= 1
        n_train = max(n_train, 1)
        # recompute leftover
        leftover = n - n_train
        n_val = min(n_val, leftover)
        n_test = leftover - n_val
        parts["train"].append(g.iloc[:n_train])
        parts["val"].append(g.iloc[n_train : n_train + n_val])
        parts["test"].append(g.iloc[n_train + n_val :])
        notes.append(
            f"class={cls!r} n={n}: train={n_train} val={n_val} test={n - n_train - n_val}"
        )

    out = {}
    for k in ("train", "val", "test"):
        out[k] = pd.concat(parts[k], ignore_index=True) if parts[k] else df.iloc[0:0].copy()
        out[k]["split"] = k
    out["_notes"] = notes
    return out


def print_split_report(splits: dict[str, pd.DataFrame], item_name: str = "windows") -> None:
    print("=" * 80, flush=True)
    print(f"PER-CLASS CHRONOLOGICAL SPLIT (70/15/15) — {item_name}")
    print("=" * 80, flush=True)
    for note in splits.get("_notes", []):
        print(f"  {note}", flush=True)
    print("-" * 80, flush=True)
    for name in ("train", "val", "test"):
        df = splits[name]
        n = len(df)
        print(f"{name.upper()} {item_name} count: {n:,}", flush=True)
        if n == 0:
            continue
        print(f"  time range: {df['window_start'].min()} -> {df['window_start'].max()}")
        vc = df["label"].value_counts()
        print("  class distribution:")
        for k, v in vc.items():
            print(f"    {str(k):40s}  {v:12,}  ({100.0 * v / n:6.2f}%)", flush=True)
        n_atk = int((df["is_attack"] == 1).sum()) if "is_attack" in df.columns else int((df["label"] != "Benign").sum())
        print(f"  binary: Benign={n - n_atk:,}  Attack={n_atk:,}", flush=True)
        print("-" * 80, flush=True)
