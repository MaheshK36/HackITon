"""CSV loading, stage mapping, time-windowing, scaling, and leakage-safe splits."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.preprocessing import StandardScaler

# Edit these paths and aliases for the local CIC-IDS-2018 or CTU-13 export.
DEFAULT_DATA_PATHS = ["data/CIC-IDS-2018.csv", "data/CTU-13.csv"]
TIME_WINDOW_SECONDS = 30.0
SEQUENCE_LENGTH = 10  # Documented default; revisit this choice during experiments.
GROUP_BY_DESTINATION = True

# Dataset attack labels -> ordinal MITRE ATT&CK stage. Keep this mapping editable.
STAGE_MAPPING = {
    "BENIGN": 0, "NORMAL": 0,
    "RECONNAISSANCE": 1, "PORTSCAN": 1, "PORT SCAN": 1, "NETWORK SCAN": 1,
    "BRUTE FORCE": 2, "BRUTEFORCE": 2, "WEB ATTACK": 2, "INITIAL ACCESS": 2,
    "EXPLOITATION": 2, "INFILTRATION": 2,
    "LATERAL MOVEMENT": 3, "LATERALMOVEMENT": 3,
    "BOT": 4, "C2": 4, "COMMAND AND CONTROL": 4, "COMMAND&CONTROL": 4,
    "INFILTRATION": 2,
    "EXFILTRATION": 5, "DATA EXFILTRATION": 5,
    "DDOS": 6, "DOS": 6, "DDoS": 6, "IMPACT": 6,
}

# Canonical feature names and common CSV aliases.
FEATURE_ALIASES = {
    "src_ip": ["src_ip", "Source IP", "Src IP", "source_ip"],
    "dst_ip": ["dst_ip", "Destination IP", "Dst IP", "destination_ip"],
    "src_port": ["src_port", "Source Port", "Src Port"],
    "dst_port": ["dst_port", "Destination Port", "Dst Port"],
    "protocol": ["protocol", "Protocol"],
    "tcp_flags": ["tcp_flags", "TCP Flags", "Flag", "Flags"],
    "bytes_per_flow": ["bytes_per_flow", "Total Length of Fwd Packets", "Flow Bytes/s", "TotLen Fwd Pkts"],
    "packets_per_flow": ["packets_per_flow", "Total Fwd Packets", "Tot Fwd Pkts"],
    "flow_duration": ["flow_duration", "Flow Duration"],
    "iat_mean": ["iat_mean", "Flow IAT Mean", "Fwd IAT Mean"],
    "iat_variance": ["iat_variance", "Flow IAT Std", "Fwd IAT Std"],
    "iat_max": ["iat_max", "Flow IAT Max", "Fwd IAT Max"],
    "bidirectional_flow_ratio": ["bidirectional_flow_ratio", "Bwd Packets/s", "Bwd Pkts/s"],
    "ttl": ["ttl", "TTL", "Average Packet TTL"],
    "ttl_variance": ["ttl_variance", "TTL Variance"],
    "tcp_window_size": ["tcp_window_size", "Init_Win_bytes_forward", "TCP Window Size"],
    "ip_fragment_flags": ["ip_fragment_flags", "IP Fragment Flags"],
    "payload_size": ["payload_size", "Average Packet Size", "Packet Length Mean"],
    "port_scan_signature": ["port_scan_signature", "Port Scan Signature"],
    "retransmission_count": ["retransmission_count", "Retransmission Count"],
}
FEATURE_COLUMNS = list(FEATURE_ALIASES)


def _find_column(frame: pd.DataFrame, aliases: Iterable[str]) -> str | None:
    normalized = {str(c).strip().lower(): c for c in frame.columns}
    for alias in aliases:
        if alias.lower() in normalized:
            return normalized[alias.lower()]
    return None


def _canonicalize(frame: pd.DataFrame) -> pd.DataFrame:
    result = pd.DataFrame(index=frame.index)
    missing = []
    for name, aliases in FEATURE_ALIASES.items():
        column = _find_column(frame, aliases)
        if column is None:
            if name in {"src_ip", "dst_ip", "protocol"}:
                missing.append(f"{name} (aliases: {aliases})")
            result[name] = 0.0
        else:
            result[name] = frame[column]
    label_column = _find_column(frame, ["label", "Label", "attack_type", "Attack", "Activity"])
    time_column = _find_column(frame, ["timestamp", "Timestamp", "time", "Flow Start", "Date first seen"])
    if label_column is None:
        raise ValueError("CSV needs a label/attack-type column.")
    if time_column is None:
        raise ValueError("CSV needs a timestamp/time column for temporal windowing.")
    if missing:
        raise ValueError("CSV is missing required identity columns: " + "; ".join(missing))
    result["label_raw"] = frame[label_column].astype(str).str.strip()
    result["timestamp"] = pd.to_datetime(frame[time_column], errors="coerce")
    if result["timestamp"].isna().all():
        result["timestamp"] = pd.to_numeric(frame[time_column], errors="coerce")
    result["stage"] = result["label_raw"].str.upper().map({k.upper(): v for k, v in STAGE_MAPPING.items()})
    result["stage"] = result["stage"].fillna((result["label_raw"].str.upper() != "BENIGN").astype(int))
    result["infiltration"] = (result["stage"].isin([2, 3, 4, 5, 6])).astype(np.float32)
    return result


def load_csv(path: str | Path) -> pd.DataFrame:
    return _canonicalize(pd.read_csv(path))


def load_frame(frame: pd.DataFrame) -> pd.DataFrame:
    return _canonicalize(frame.copy())


@dataclass
class WindowedData:
    sequences: np.ndarray
    next_states: np.ndarray
    infiltration: np.ndarray
    stages: np.ndarray
    groups: np.ndarray
    scaler: StandardScaler
    feature_names: list[str]

    def __len__(self) -> int:
        return len(self.sequences)


def _time_seconds(values: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(values):
        return (values - values.min()).dt.total_seconds()
    return pd.to_numeric(values, errors="coerce").fillna(0.0)


def make_windows(frame: pd.DataFrame, window_seconds: float = TIME_WINDOW_SECONDS,
                 sequence_length: int = SEQUENCE_LENGTH, scaler: StandardScaler | None = None) -> WindowedData:
    if sequence_length < 1 or window_seconds <= 0:
        raise ValueError("window_seconds must be positive and sequence_length must be at least 1.")
    data = frame.copy().sort_values("timestamp")
    numeric = data[FEATURE_COLUMNS].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)
    data["window_id"] = np.floor(_time_seconds(data["timestamp"]) / window_seconds).astype(int)
    group_cols = ["src_ip"] + (["dst_ip"] if GROUP_BY_DESTINATION else [])
    # Ensure group columns are strings and handle NaN values
    data["src_ip"] = data["src_ip"].fillna("0.0.0.0").astype(str)
    if GROUP_BY_DESTINATION and "dst_ip" in data.columns:
        data["dst_ip"] = data["dst_ip"].fillna("0.0.0.0").astype(str)
    data["group_key"] = data[group_cols].astype(str).agg("|".join, axis=1)
    window_rows = []
    for group_key, group in data.groupby("group_key", sort=False):
        for window_id, rows in group.groupby("window_id", sort=True):
            values = numeric.loc[rows.index].mean(axis=0).to_numpy(dtype=np.float32)
            window_rows.append((group_key, window_id, values, int(rows["stage"].mode().iloc[0]), float(rows["infiltration"].max()), len(rows)))
    if not window_rows:
        raise ValueError("No time windows were produced; check timestamp and identity columns.")
    raw_states = np.stack([r[2] for r in window_rows])
    fitted_scaler = scaler or StandardScaler().fit(raw_states)
    scaled_states = fitted_scaler.transform(raw_states).astype(np.float32)
    sequences, next_states, infiltrations, stages, groups = [], [], [], [], []
    by_group = {}
    for index, row in enumerate(window_rows):
        by_group.setdefault(row[0], []).append((index, row))
    for group_key, rows in by_group.items():
        rows.sort(key=lambda item: item[1][1])
        for end in range(sequence_length - 1, len(rows) - 1):
            history = [item[0] for item in rows[end - sequence_length + 1:end + 1]]
            next_index, target = rows[end + 1]
            sequences.append(scaled_states[history])
            next_states.append(raw_states[next_index])
            infiltrations.append(target[4])
            stages.append(target[3])
            groups.append(group_key)
    if not sequences:
        raise ValueError("Not enough windows for the requested sequence length and next-state target.")
    return WindowedData(np.asarray(sequences, dtype=np.float32), np.asarray(next_states, dtype=np.float32),
                        np.asarray(infiltrations, dtype=np.float32), np.asarray(stages, dtype=np.int64),
                        np.asarray(groups), fitted_scaler, FEATURE_COLUMNS)


def split_by_group(data: WindowedData, seed: int = 42) -> dict[str, WindowedData]:
    unique_groups = np.unique(data.groups)
    if len(unique_groups) < 3:
        raise ValueError("Need at least 3 distinct source/session groups for train/val/test splitting.")
    group_stages = np.asarray([data.stages[data.groups == group].min() for group in unique_groups])
    splitter = StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=seed)
    folds = list(splitter.split(unique_groups, group_stages, groups=unique_groups))
    test_indices = folds[0][1]
    val_indices = folds[1][1]
    train_indices = np.setdiff1d(np.arange(len(unique_groups)), np.concatenate([test_indices, val_indices]))
    train_groups = unique_groups[train_indices]
    val_groups, test_groups = unique_groups[val_indices], unique_groups[test_indices]
    return {name: _subset(data, selected) for name, selected in [("train", train_groups), ("val", val_groups), ("test", test_groups)]}


def _subset(data: WindowedData, selected: np.ndarray) -> WindowedData:
    mask = np.isin(data.groups, selected)
    return WindowedData(data.sequences[mask], data.next_states[mask], data.infiltration[mask], data.stages[mask], data.groups[mask], data.scaler, data.feature_names)


def window_report(frame: pd.DataFrame, window_sizes: Iterable[float], sequence_length: int = SEQUENCE_LENGTH) -> pd.DataFrame:
    records = []
    for seconds in window_sizes:
        try:
            windows = make_windows(frame, seconds, sequence_length)
            counts = np.bincount(windows.stages, minlength=7)
            sequence_count = len(windows)
        except ValueError as error:
            if "Not enough windows" not in str(error):
                raise
            counts = np.zeros(7, dtype=int)
            sequence_count = 0
        mean_rows = float(np.mean([row[2] for row in _build_window_rows(frame, seconds)]))
        records.append({"window_seconds": seconds, "sequence_count": sequence_count, "mean_features_per_window": mean_rows, **{f"stage_{i}_count": int(counts[i]) for i in range(7)}})
    return pd.DataFrame(records)


def _build_window_rows(frame: pd.DataFrame, window_seconds: float) -> list[tuple]:
    data = frame.copy().sort_values("timestamp")
    data["window_id"] = np.floor(_time_seconds(data["timestamp"]) / window_seconds).astype(int)
    group_cols = ["src_ip"] + (["dst_ip"] if GROUP_BY_DESTINATION else [])
    data["group_key"] = data[group_cols].astype(str).agg("|".join, axis=1)
    return [(group_key, window_id, len(rows)) for (group_key, window_id), rows in data.groupby(["group_key", "window_id"], sort=False)]
