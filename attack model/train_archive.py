from __future__ import annotations

import glob
import subprocess
import sys
from pathlib import Path

import pandas as pd

from data_pipeline import FEATURE_COLUMNS

ARCHIVE_GLOB = r"C:/Users/mahes/Downloads/archive/*.csv"
OUTPUT_PATH = Path("data/archive_combined.csv")


def normalize_label(raw_value: object) -> str:
    value = str(raw_value).strip()
    if not value:
        return "BENIGN"
    lowered = value.lower()
    if lowered in {"benign", "normal"}:
        return "BENIGN"
    if "goldeneye" in lowered or "slowloris" in lowered or "dos" in lowered or "ddos" in lowered:
        return "DOS"
    if "scan" in lowered:
        return "PORTSCAN"
    if "brute" in lowered:
        return "BRUTE FORCE"
    if "infiltration" in lowered:
        return "INFILTRATION"
    if "lateral" in lowered:
        return "LATERAL MOVEMENT"
    if "c2" in lowered or "bot" in lowered or "command" in lowered:
        return "C2"
    if "exfil" in lowered:
        return "EXFILTRATION"
    return "BENIGN"


def as_numeric(series: pd.Series | None, default: float = 0.0) -> pd.Series:
    if series is None:
        return pd.Series([default] * len(OUTPUT_PATH.parent), dtype=float)
    return pd.to_numeric(series, errors="coerce").fillna(default)


def build_dataset() -> Path:
    files = sorted(glob.glob(ARCHIVE_GLOB))
    if not files:
        raise FileNotFoundError(f"No archive files found under {ARCHIVE_GLOB}")

    frames = []
    for path in files:
        raw = pd.read_csv(path, low_memory=False)
        raw = raw.sample(n=min(len(raw), 20000), random_state=42).reset_index(drop=True)
        if raw.empty:
            continue
        label_source = raw["Label"] if "Label" in raw.columns else raw.iloc[:, -1]
        time_source = raw["Timestamp"] if "Timestamp" in raw.columns else raw.iloc[:, 0]

        record = pd.DataFrame(index=raw.index)
        record["src_ip"] = [f"10.0.{i % 250}.1" for i in range(len(raw))]
        record["dst_ip"] = "10.0.0.2"
        record["src_port"] = pd.to_numeric(raw.get("Src Port", 0), errors="coerce").fillna(0)
        record["dst_port"] = pd.to_numeric(raw.get("Dst Port", 0), errors="coerce").fillna(0)
        record["protocol"] = pd.to_numeric(raw.get("Protocol", 0), errors="coerce").fillna(0)
        record["tcp_flags"] = (
            pd.to_numeric(raw.get("FIN Flag Cnt", 0), errors="coerce").fillna(0)
            + pd.to_numeric(raw.get("SYN Flag Cnt", 0), errors="coerce").fillna(0)
        )
        record["bytes_per_flow"] = pd.to_numeric(raw.get("Flow Bytes/s", raw.get("TotLen Fwd Pkts", 0)), errors="coerce").fillna(0)
        record["packets_per_flow"] = pd.to_numeric(raw.get("Tot Fwd Pkts", 0), errors="coerce").fillna(0)
        record["flow_duration"] = pd.to_numeric(raw.get("Flow Duration", 0), errors="coerce").fillna(0)
        record["iat_mean"] = pd.to_numeric(raw.get("Flow IAT Mean", 0), errors="coerce").fillna(0)
        record["iat_variance"] = pd.to_numeric(raw.get("Flow IAT Std", 0), errors="coerce").fillna(0)
        record["iat_max"] = pd.to_numeric(raw.get("Flow IAT Max", 0), errors="coerce").fillna(0)
        record["bidirectional_flow_ratio"] = pd.to_numeric(raw.get("Bwd Pkts/s", 0), errors="coerce").fillna(0)
        record["ttl"] = pd.to_numeric(raw.get("Idle Mean", 0), errors="coerce").fillna(0)
        record["ttl_variance"] = 0.0
        record["tcp_window_size"] = pd.to_numeric(raw.get("Init Fwd Win Byts", 0), errors="coerce").fillna(0)
        record["ip_fragment_flags"] = 0.0
        record["payload_size"] = pd.to_numeric(raw.get("Pkt Len Mean", raw.get("Average Packet Size", 0)), errors="coerce").fillna(0)
        record["port_scan_signature"] = 0.0
        record["retransmission_count"] = 0.0

        record["label"] = label_source.map(normalize_label).fillna("BENIGN")
        record["timestamp"] = pd.to_datetime(time_source, dayfirst=True, errors="coerce")
        record["timestamp"] = record["timestamp"].fillna(pd.Timestamp("2024-01-01"))
        record = record[[*FEATURE_COLUMNS, "label", "timestamp", "src_ip", "dst_ip"]]
        frames.append(record)

    if not frames:
        raise ValueError("No valid archive rows were produced.")

    output = pd.concat(frames, ignore_index=True)
    output = output.dropna(subset=["timestamp"]).reset_index(drop=True)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote archive dataset to {OUTPUT_PATH} with {len(output):,} rows")
    print(output["label"].value_counts().head().to_dict())
    return OUTPUT_PATH


def main() -> None:
    dataset_path = build_dataset()
    subprocess.run([
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
        "--batch-size",
        "32",
    ], check=False)


if __name__ == "__main__":
    main()
