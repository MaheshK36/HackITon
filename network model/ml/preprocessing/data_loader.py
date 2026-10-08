"""Load CIC-IDS-2018 CSVs and CTU-13 binetflow files into a common flow schema."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Iterator

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CIC_DIR = ROOT / "data" / "raw" / "cicids2018"
CTU_DIR = ROOT / "data" / "raw" / "ctu13"

COMMON_COLS = [
    "timestamp",
    "duration_sec",
    "packets",
    "bytes",
    "protocol",
    "dst_port",
    "src_port",
    "syn",
    "ack",
    "fin",
    "rst",
    "psh",
    "urg",
    "label_raw",
    "source_file",
    "dataset",
]


def _strip_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().replace("\ufeff", "") for c in df.columns]
    return df


def normalize_attack_label(raw: str, dataset: str) -> str:
    s = str(raw).strip()
    if s.lower() in {"nan", "none", "", "label"}:
        return "UNKNOWN"
    if dataset == "ctu13":
        low = s.lower()
        if "botnet" in low:
            return "Botnet"
        if "normal" in low or "legitimate" in low:
            return "Benign"
        if "background" in low:
            return "Benign"
        return s
    # CIC-IDS-2018
    if s.lower() == "benign":
        return "Benign"
    return s


def list_cic_files() -> list[Path]:
    if not CIC_DIR.exists():
        return []
    return sorted(p for p in CIC_DIR.glob("*.csv") if p.is_file())


def list_ctu_files() -> list[Path]:
    if not CTU_DIR.exists():
        return []
    files = []
    for ext in ("*.binetflow", "*.csv", "*.labeled"):
        files.extend(CTU_DIR.rglob(ext))
    return sorted({p.resolve() for p in files if p.is_file()})


def _colmap(columns: Iterable[str]) -> dict[str, str]:
    """Map stripped lower-case names to original stripped names."""
    out = {}
    for c in columns:
        out[c.strip().lower()] = c
    return out


def _pick(cmap: dict[str, str], *candidates: str) -> str | None:
    for name in candidates:
        if name.lower() in cmap:
            return cmap[name.lower()]
    return None


def iter_cic_chunks(path: Path, chunksize: int = 250_000) -> Iterator[pd.DataFrame]:
    header = pd.read_csv(path, nrows=0, low_memory=False)
    header = _strip_cols(header)
    orig_names = list(header.columns)
    cmap = _colmap(orig_names)

    ts_col = _pick(cmap, "timestamp", "flow start")
    label_col = _pick(cmap, "label")
    dur_col = _pick(cmap, "flow duration")
    fwd_p = _pick(cmap, "tot fwd pkts", "total fwd packets")
    bwd_p = _pick(cmap, "tot bwd pkts", "total backward packets")
    fwd_b = _pick(cmap, "totlen fwd pkts", "total length of fwd packets")
    bwd_b = _pick(cmap, "totlen bwd pkts", "total length of bwd packets")
    proto = _pick(cmap, "protocol")
    dport = _pick(cmap, "dst port", "destination port")
    sport = _pick(cmap, "src port", "source port")
    syn = _pick(cmap, "syn flag cnt", "syn flag count")
    ack = _pick(cmap, "ack flag cnt", "ack flag count")
    fin = _pick(cmap, "fin flag cnt", "fin flag count")
    rst = _pick(cmap, "rst flag cnt", "rst flag count")
    psh = _pick(cmap, "psh flag cnt", "psh flag count")
    urg = _pick(cmap, "urg flag cnt", "urg flag count")

    usecols = [c for c in [ts_col, label_col, dur_col, fwd_p, bwd_p, fwd_b, bwd_b, proto, dport, sport, syn, ack, fin, rst, psh, urg] if c]
    # pandas read_csv usecols must match file header including possible spaces
    raw_header = pd.read_csv(path, nrows=0)
    raw_map = {str(c).strip().replace("\ufeff", ""): c for c in raw_header.columns}
    usecols_raw = [raw_map[c] for c in usecols if c in raw_map]

    for chunk in pd.read_csv(
        path,
        usecols=usecols_raw,
        chunksize=chunksize,
        low_memory=False,
        dtype=str,
    ):
        chunk = _strip_cols(chunk)
        if ts_col and ts_col in chunk.columns:
            bad = chunk[ts_col].astype(str).str.strip().str.lower().isin({"timestamp", "nan"})
            chunk = chunk.loc[~bad]
        if label_col and label_col in chunk.columns:
            bad_l = chunk[label_col].astype(str).str.strip().str.lower().eq("label")
            chunk = chunk.loc[~bad_l]
        if chunk.empty:
            continue

        ts = pd.to_datetime(chunk[ts_col], errors="coerce", dayfirst=True) if ts_col else pd.NaT
        dur = pd.to_numeric(chunk[dur_col], errors="coerce") if dur_col else 0.0
        # CIC flow duration is microseconds
        duration_sec = dur.astype(float) / 1_000_000.0
        fwd_pkts = pd.to_numeric(chunk[fwd_p], errors="coerce") if fwd_p else 0.0
        bwd_pkts = pd.to_numeric(chunk[bwd_p], errors="coerce") if bwd_p else 0.0
        fwd_bytes = pd.to_numeric(chunk[fwd_b], errors="coerce") if fwd_b else 0.0
        bwd_bytes = pd.to_numeric(chunk[bwd_b], errors="coerce") if bwd_b else 0.0
        proto_s = chunk[proto].astype(str) if proto else "0"
        dport_v = pd.to_numeric(chunk[dport], errors="coerce") if dport else np.nan
        sport_v = pd.to_numeric(chunk[sport], errors="coerce") if sport else np.nan

        def flag(colname):
            if not colname:
                return 0.0
            return pd.to_numeric(chunk[colname], errors="coerce").fillna(0.0)

        out = pd.DataFrame(
            {
                "timestamp": ts,
                "duration_sec": duration_sec.fillna(0.0).clip(lower=0),
                "packets": (fwd_pkts.fillna(0) + bwd_pkts.fillna(0)).clip(lower=0),
                "bytes": (fwd_bytes.fillna(0) + bwd_bytes.fillna(0)).clip(lower=0),
                "protocol": proto_s,
                "dst_port": dport_v,
                "src_port": sport_v,
                "syn": flag(syn),
                "ack": flag(ack),
                "fin": flag(fin),
                "rst": flag(rst),
                "psh": flag(psh),
                "urg": flag(urg),
                "label_raw": chunk[label_col].astype(str) if label_col else "UNKNOWN",
                "source_file": path.name,
                "dataset": "cicids2018",
            }
        )
        out = out.dropna(subset=["timestamp"])
        years = out["timestamp"].dt.year
        out = out[(years >= 2010) & (years <= 2020)]
        yield out


def iter_ctu_chunks(path: Path, chunksize: int = 250_000) -> Iterator[pd.DataFrame]:
    sep = ","
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        header_line = fh.readline()
    if "StartTime" in header_line and "," not in header_line:
        sep = r"\s+"

    for chunk in pd.read_csv(path, sep=sep, chunksize=chunksize, low_memory=False, dtype=str, engine="python" if sep != "," else "c"):
        chunk = _strip_cols(chunk)
        cmap = _colmap(chunk.columns)
        ts_col = _pick(cmap, "starttime", "stime", "timestamp")
        dur_col = _pick(cmap, "dur", "duration")
        pkts_col = _pick(cmap, "totpkts", "pkts", "packets")
        bytes_col = _pick(cmap, "totbytes", "bytes")
        proto_col = _pick(cmap, "proto", "protocol")
        dport_col = _pick(cmap, "dport", "dstport", "dst_port")
        sport_col = _pick(cmap, "sport", "srcport", "src_port")
        state_col = _pick(cmap, "state")
        label_col = _pick(cmap, "label")
        if ts_col is None or label_col is None:
            continue
        ts = pd.to_datetime(chunk[ts_col], errors="coerce")
        dur = pd.to_numeric(chunk[dur_col], errors="coerce") if dur_col else 0.0
        pkts = pd.to_numeric(chunk[pkts_col], errors="coerce") if pkts_col else 0.0
        by = pd.to_numeric(chunk[bytes_col], errors="coerce") if bytes_col else 0.0
        proto = chunk[proto_col].astype(str) if proto_col else "unknown"
        dport = pd.to_numeric(chunk[dport_col], errors="coerce") if dport_col else np.nan
        sport = pd.to_numeric(chunk[sport_col], errors="coerce") if sport_col else np.nan
        state = chunk[state_col].astype(str).str.upper() if state_col else ""

        out = pd.DataFrame(
            {
                "timestamp": ts,
                "duration_sec": pd.Series(dur).fillna(0.0).clip(lower=0),
                "packets": pd.Series(pkts).fillna(0.0).clip(lower=0),
                "bytes": pd.Series(by).fillna(0.0).clip(lower=0),
                "protocol": proto,
                "dst_port": dport,
                "src_port": sport,
                "syn": state.str.contains("S", regex=False).astype(float) if state_col else 0.0,
                "ack": state.str.contains("A", regex=False).astype(float) if state_col else 0.0,
                "fin": state.str.contains("F", regex=False).astype(float) if state_col else 0.0,
                "rst": state.str.contains("R", regex=False).astype(float) if state_col else 0.0,
                "psh": 0.0,
                "urg": 0.0,
                "label_raw": chunk[label_col].astype(str),
                "source_file": path.name,
                "dataset": "ctu13",
            }
        )
        out = out.dropna(subset=["timestamp"])
        years = out["timestamp"].dt.year
        out = out[(years >= 2010) & (years <= 2020)]
        yield out


def peek_cic_columns(path: Path) -> list[str]:
    df = pd.read_csv(path, nrows=0)
    df = _strip_cols(df)
    return list(df.columns)
