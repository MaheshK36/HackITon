"""60-second window aggregation into a shared feature schema."""

from __future__ import annotations

import numpy as np
import pandas as pd


WINDOW_SEC = 60
FEATURE_COLS = [
    "n_flows",
    "duration_sum",
    "duration_mean",
    "duration_std",
    "duration_max",
    "packets_sum",
    "packets_mean",
    "bytes_sum",
    "bytes_mean",
    "tcp_ratio",
    "udp_ratio",
    "dst_port_nunique_approx",
    "src_port_nunique_approx",
    "syn_mean",
    "ack_mean",
    "fin_mean",
    "rst_mean",
    "psh_mean",
    "urg_mean",
    "bytes_per_packet",
    "short_flow_ratio",
]


def _is_tcp(s: pd.Series) -> pd.Series:
    x = s.astype(str).str.lower().str.strip()
    return x.isin({"6", "tcp", "6.0"})


def _is_udp(s: pd.Series) -> pd.Series:
    x = s.astype(str).str.lower().str.strip()
    return x.isin({"17", "udp", "17.0"})


def _vectorized_labels(df: pd.DataFrame) -> pd.Series:
    raw = df["label_raw"].astype(str).str.strip()
    ds = df["dataset"].astype(str)
    cic = raw.mask(raw.str.lower().eq("benign"), "Benign")
    cic = cic.mask(raw.str.lower().isin({"nan", "none", "", "label"}), "UNKNOWN")
    low = raw.str.lower()
    ctu = raw.copy()
    ctu = ctu.mask(low.str.contains("botnet", na=False), "Botnet")
    benign_ctu = low.str.contains("normal", na=False) | low.str.contains("legitimate", na=False) | low.str.contains("background", na=False)
    ctu = ctu.mask(benign_ctu, "Benign")
    return pd.Series(np.where(ds.eq("ctu13"), ctu, cic), index=df.index)


def flows_to_partial_windows(flows: pd.DataFrame) -> pd.DataFrame:
    df = flows.copy()
    df["label"] = _vectorized_labels(df)
    df["window_start"] = df["timestamp"].dt.floor(f"{WINDOW_SEC}s")
    df["is_tcp"] = _is_tcp(df["protocol"]).astype(float)
    df["is_udp"] = _is_udp(df["protocol"]).astype(float)
    df["is_short"] = (df["duration_sec"] < 1.0).astype(float)
    df["dst_port"] = pd.to_numeric(df["dst_port"], errors="coerce")
    df["src_port"] = pd.to_numeric(df["src_port"], errors="coerce")

    g = df.groupby(["dataset", "source_file", "window_start"], sort=False)
    agg = g.agg(
        n_flows=("timestamp", "size"),
        duration_sum=("duration_sec", "sum"),
        duration_mean=("duration_sec", "mean"),
        duration_std=("duration_sec", "std"),
        duration_max=("duration_sec", "max"),
        packets_sum=("packets", "sum"),
        packets_mean=("packets", "mean"),
        bytes_sum=("bytes", "sum"),
        bytes_mean=("bytes", "mean"),
        tcp_ratio=("is_tcp", "mean"),
        udp_ratio=("is_udp", "mean"),
        dst_port_nunique_approx=("dst_port", "nunique"),
        src_port_nunique_approx=("src_port", "nunique"),
        syn_mean=("syn", "mean"),
        ack_mean=("ack", "mean"),
        fin_mean=("fin", "mean"),
        rst_mean=("rst", "mean"),
        psh_mean=("psh", "mean"),
        urg_mean=("urg", "mean"),
        short_flow_ratio=("is_short", "mean"),
    ).reset_index()
    agg["duration_std"] = agg["duration_std"].fillna(0.0)
    agg["bytes_per_packet"] = agg["bytes_sum"] / agg["packets_sum"].replace(0, np.nan)
    agg["bytes_per_packet"] = agg["bytes_per_packet"].fillna(0.0)

    # majority label + attack fraction per window (from this partial chunk)
    maj = (
        df.groupby(["dataset", "source_file", "window_start"])["label"]
        .agg(lambda s: s.value_counts().index[0])
        .rename("label")
        .reset_index()
    )
    attack_frac = (
        df.assign(is_atk=(df["label"] != "Benign").astype(float))
        .groupby(["dataset", "source_file", "window_start"])["is_atk"]
        .mean()
        .rename("attack_frac")
        .reset_index()
    )
    n_classes = (
        df.groupby(["dataset", "source_file", "window_start"])["label"]
        .nunique()
        .rename("n_labels_in_window")
        .reset_index()
    )
    out = agg.merge(maj, on=["dataset", "source_file", "window_start"]).merge(
        attack_frac, on=["dataset", "source_file", "window_start"]
    ).merge(n_classes, on=["dataset", "source_file", "window_start"])
    return out


def merge_partial_windows(parts: list[pd.DataFrame]) -> pd.DataFrame:
    if not parts:
        return pd.DataFrame()
    df = pd.concat(parts, ignore_index=True)
    keys = ["dataset", "source_file", "window_start"]

    def _wavg(g, col, wcol="n_flows"):
        w = g[wcol].to_numpy(dtype=float)
        x = g[col].to_numpy(dtype=float)
        s = w.sum()
        return float((x * w).sum() / s) if s else 0.0

    rows = []
    for key, g in df.groupby(keys, sort=False):
        n = float(g["n_flows"].sum())
        dur_sum = float(g["duration_sum"].sum())
        pkt_sum = float(g["packets_sum"].sum())
        byt_sum = float(g["bytes_sum"].sum())
        rows.append(
            {
                "dataset": key[0],
                "source_file": key[1],
                "window_start": key[2],
                "n_flows": n,
                "duration_sum": dur_sum,
                "duration_mean": dur_sum / n if n else 0.0,
                "duration_std": _wavg(g, "duration_std"),
                "duration_max": float(g["duration_max"].max()),
                "packets_sum": pkt_sum,
                "packets_mean": pkt_sum / n if n else 0.0,
                "bytes_sum": byt_sum,
                "bytes_mean": byt_sum / n if n else 0.0,
                "tcp_ratio": _wavg(g, "tcp_ratio"),
                "udp_ratio": _wavg(g, "udp_ratio"),
                "dst_port_nunique_approx": float(g["dst_port_nunique_approx"].max()),
                "src_port_nunique_approx": float(g["src_port_nunique_approx"].max()),
                "syn_mean": _wavg(g, "syn_mean"),
                "ack_mean": _wavg(g, "ack_mean"),
                "fin_mean": _wavg(g, "fin_mean"),
                "rst_mean": _wavg(g, "rst_mean"),
                "psh_mean": _wavg(g, "psh_mean"),
                "urg_mean": _wavg(g, "urg_mean"),
                "bytes_per_packet": (byt_sum / pkt_sum) if pkt_sum else 0.0,
                "short_flow_ratio": _wavg(g, "short_flow_ratio"),
                "attack_frac": _wavg(g, "attack_frac"),
                "label": g.loc[g["n_flows"].idxmax(), "label"],
                "n_labels_in_window": int(g["n_labels_in_window"].max()),
            }
        )
    out = pd.DataFrame(rows)
    out["is_attack"] = (out["label"] != "Benign").astype(int)
    ts = pd.to_datetime(out["window_start"])
    out["t_unix"] = (ts.astype("datetime64[ns]").astype("int64") // 10**9).astype(np.int64)
    return out.sort_values(["dataset", "source_file", "window_start"]).reset_index(drop=True)


def print_window_report(windows: pd.DataFrame, title: str) -> None:
    print("=" * 80, flush=True)
    print(title, flush=True)
    print("=" * 80, flush=True)
    n = len(windows)
    print(f"Window size: {WINDOW_SEC}s", flush=True)
    print(f"Window count: {n:,}", flush=True)
    if n == 0:
        print("EMPTY windows — cannot proceed.", flush=True)
        return
    print(f"Time range: {windows['window_start'].min()}  ->  {windows['window_start'].max()}", flush=True)
    print("Class distribution (majority label per window):", flush=True)
    vc = windows["label"].value_counts()
    for k, v in vc.items():
        print(f"  {str(k):40s}  {v:12,}  ({100.0 * v / n:6.2f}%)", flush=True)
    n_atk = int((windows["is_attack"] == 1).sum())
    print(f"Binary: Benign={n - n_atk:,}  Attack={n_atk:,}  ({100.0 * n_atk / n:.2f}% attack windows)", flush=True)
    print(f"Mean flows/window: {windows['n_flows'].mean():.1f}  median={windows['n_flows'].median():.1f}", flush=True)
    mixed = int((windows["n_labels_in_window"] > 1).sum())
    print(f"Windows with mixed labels (partial chunk estimate / merged max): {mixed:,}", flush=True)
