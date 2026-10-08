"""Logistic Regression + Random Forest baselines with a suspicious-perfect-score audit."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.preprocessing.window_features import FEATURE_COLS


def _xy(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    X = df[FEATURE_COLS].to_numpy(dtype=np.float64)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    y = df["is_attack"].to_numpy(dtype=int)
    return X, y


def binary_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    y_true = y_true.astype(int)
    y_pred = y_pred.astype(int)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    fpr = fp / (fp + tn + 1e-12)
    return {
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "fpr": float(fpr),
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
        "n": int(len(y_true)),
        "positives": int(y_true.sum()),
    }


def _fmt_row(split: str, m: dict) -> str:
    return (
        f"{split:5s}  P={m['precision']:.4f}  R={m['recall']:.4f}  "
        f"F1={m['f1']:.4f}  FPR={m['fpr']:.4f}  "
        f"n={m['n']}  pos={m['positives']}  tp={m['tp']} fp={m['fp']} tn={m['tn']} fn={m['fn']}"
    )


def eval_model(name: str, model, splits: dict[str, pd.DataFrame]) -> dict:
    print("-" * 80, flush=True)
    print(name, flush=True)
    results = {}
    for split in ("train", "val", "test"):
        X, y = _xy(splits[split])
        pred = model.predict(X)
        m = binary_metrics(y, pred)
        results[split] = m
        print(_fmt_row(split, m), flush=True)
    return results


def looks_suspiciously_perfect(results: dict, threshold: float = 0.995) -> bool:
    for split in ("val", "test"):
        m = results[split]
        if m["n"] < 20:
            continue
        if m["f1"] >= threshold and m["precision"] >= threshold and m["recall"] >= threshold:
            return True
    return False


def investigate_rf(rf: RandomForestClassifier, splits: dict[str, pd.DataFrame]) -> None:
    print("=" * 80, flush=True)
    print("RANDOM FOREST PERFECT-SCORE INVESTIGATION (red flag, not a success)", flush=True)
    print("=" * 80, flush=True)
    imp = sorted(zip(FEATURE_COLS, rf.feature_importances_), key=lambda x: -x[1])
    print("Feature importances (all):", flush=True)
    for name, val in imp:
        print(f"  {name:28s}  {val:.6f}", flush=True)

    # Univariate AUCs via ranking by each feature vs label on val
    val = splits["val"]
    y = val["is_attack"].to_numpy(int)
    print("Univariate separation on VAL (mean feature | attack vs benign):", flush=True)
    for col in FEATURE_COLS:
        a = val.loc[val["is_attack"] == 1, col]
        b = val.loc[val["is_attack"] == 0, col]
        print(
            f"  {col:28s}  attack_mean={a.mean():.4g}  benign_mean={b.mean():.4g}  "
            f"ratio={a.mean() / (b.mean() + 1e-12):.3g}",
            flush=True,
        )

    # Retrain without volume features that DoS windows inflate
    drop = {"n_flows", "packets_sum", "bytes_sum", "duration_sum"}
    keep = [c for c in FEATURE_COLS if c not in drop]
    print(f"Retrain RF without volume features {sorted(drop)} ...", flush=True)
    Xtr = np.nan_to_num(splits["train"][keep].to_numpy(float), nan=0.0, posinf=0.0, neginf=0.0)
    ytr = splits["train"]["is_attack"].to_numpy(int)
    rf2 = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_leaf=5,
        n_jobs=-1,
        random_state=42,
        class_weight="balanced",
    )
    rf2.fit(Xtr, ytr)
    for split in ("train", "val", "test"):
        X = np.nan_to_num(splits[split][keep].to_numpy(float), nan=0.0, posinf=0.0, neginf=0.0)
        y = splits[split]["is_attack"].to_numpy(int)
        pred = rf2.predict(X)
        m = binary_metrics(y, pred)
        print("  ablated " + _fmt_row(split, m), flush=True)

    # Depth-limited RF on full features
    print("Retrain depth-limited RF (max_depth=6, min_samples_leaf=10) on full features ...", flush=True)
    Xtr, ytr = _xy(splits["train"])
    rf3 = RandomForestClassifier(
        n_estimators=200,
        max_depth=6,
        min_samples_leaf=10,
        n_jobs=-1,
        random_state=42,
        class_weight="balanced",
    )
    rf3.fit(Xtr, ytr)
    for split in ("train", "val", "test"):
        X, y = _xy(splits[split])
        m = binary_metrics(y, rf3.predict(X))
        print("  limited " + _fmt_row(split, m), flush=True)


def train_and_report(splits: dict[str, pd.DataFrame], models_dir: Path) -> dict:
    models_dir.mkdir(parents=True, exist_ok=True)
    Xtr, ytr = _xy(splits["train"])
    print("=" * 80, flush=True)
    print("BASELINES (binary attack vs benign) on COMBINED windows", flush=True)
    print(f"Features ({len(FEATURE_COLS)}): {FEATURE_COLS}", flush=True)
    print(f"Train n={len(ytr):,}  positives={int(ytr.sum()):,}", flush=True)
    print("=" * 80, flush=True)

    lr = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    solver="lbfgs",
                ),
            ),
        ]
    )
    lr.fit(Xtr, ytr)
    lr_res = eval_model("Logistic Regression", lr, splits)

    rf = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        min_samples_leaf=1,
        n_jobs=-1,
        random_state=42,
        class_weight="balanced",
    )
    rf.fit(Xtr, ytr)
    rf_res = eval_model("Random Forest", rf, splits)

    print("=" * 80, flush=True)
    print(f"{'Model':22s} {'Split':6s} {'Precision':>10s} {'Recall':>10s} {'F1':>10s} {'FPR':>10s}", flush=True)
    for model_name, res in (("Logistic Regression", lr_res), ("Random Forest", rf_res)):
        for split in ("train", "val", "test"):
            m = res[split]
            print(
                f"{model_name:22s} {split:6s} {m['precision']:10.4f} {m['recall']:10.4f} {m['f1']:10.4f} {m['fpr']:10.4f}",
                flush=True,
            )

    rf_perfect = looks_suspiciously_perfect(rf_res)
    print("-" * 80, flush=True)
    print(f"RF val/test suspiciously perfect (>=0.995 F1/P/R)?  {rf_perfect}", flush=True)
    if rf_perfect:
        investigate_rf(rf, splits)

    payload = {"logistic_regression": lr_res, "random_forest": rf_res, "rf_suspiciously_perfect": rf_perfect}
    (models_dir / "baseline_results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {models_dir / 'baseline_results.json'}", flush=True)
    return payload
