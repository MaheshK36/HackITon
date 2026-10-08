from __future__ import annotations

import glob
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

from data_pipeline import FEATURE_COLUMNS

ARCHIVE_GLOB = r"C:/Users/mahes/Downloads/archive/*.csv"
OUTPUT_PATH = Path("data/archive_combined.csv")


def _pick_value(row: pd.Series, aliases: list[str]):
    for alias in aliases:
        key = alias.strip().lower()
        for column in row.index:
            if str(column).strip().lower() == key:
                value = row[column]
                if pd.isna(value):
                    return 0.0
                return value
    return 0.0


def build_archive_dataset() -> Path:
    files = sorted(glob.glob(ARCHIVE_GLOB))
    if not files:
        raise FileNotFoundError(f"No archive CSV files found under {ARCHIVE_GLOB}")

    alias_map = {
        "src_ip": ["src_ip", "Source IP", "Src IP"],
        "dst_ip": ["dst_ip", "Destination IP", "Dst IP"],
        "src_port": ["src_port", "Source Port", "Src Port"],
        "dst_port": ["dst_port", "Destination Port", "Dst Port"],
        "protocol": ["protocol", "Protocol"],
        "tcp_flags": ["tcp_flags", "TCP Flags", "Flag", "Flags"],
        "bytes_per_flow": ["bytes_per_flow", "Total Length of Fwd Packets", "TotLen Fwd Pkts"],
        "packets_per_flow": ["packets_per_flow", "Total Fwd Packets", "Tot Fwd Pkts"],
        "flow_duration": ["flow_duration", "Flow Duration"],
        "iat_mean": ["iat_mean", "Flow IAT Mean", "Fwd IAT Mean"],
        "iat_variance": ["iat_variance", "Flow IAT Std", "Fwd IAT Std"],
        "iat_max": ["iat_max", "Flow IAT Max", "Fwd IAT Max"],
        "bidirectional_flow_ratio": ["bidirectional_flow_ratio", "Flow Byts/s", "Bwd Pkts/s"],
        "ttl": ["ttl", "TTL", "Average Packet TTL"],
        "ttl_variance": ["ttl_variance", "TTL Variance"],
        "tcp_window_size": ["tcp_window_size", "Init Fwd Win Byts", "TCP Window Size"],
        "ip_fragment_flags": ["ip_fragment_flags", "IP Fragment Flags"],
        "payload_size": ["payload_size", "Pkt Len Mean", "Average Packet Size"],
        "port_scan_signature": ["port_scan_signature", "Port Scan Signature", "SYN Flag Cnt"],
        "retransmission_count": ["retransmission_count", "Retransmission Count"],
    }

    rows = []
    for path in files:
        df = pd.read_csv(path, low_memory=False)
        for _, row in df.iterrows():
            record = {
                "src_ip": f"10.0.{len(rows) % 250}.1",
                "dst_ip": "10.0.0.2",
                "timestamp": pd.to_datetime(row.get("Timestamp", row.get("timestamp")), errors="coerce"),
                "label": str(row.get("Label", "BENIGN")).strip() or "BENIGN",
            }
            for feature in FEATURE_COLUMNS:
                if feature in {"src_ip", "dst_ip", "timestamp", "label"}:
                    continue
                value = _pick_value(row, alias_map.get(feature, []))
                record[feature] = pd.to_numeric(value, errors="coerce") if value is not None else 0.0
            rows.append(record)

    output = pd.DataFrame(rows)
    for feature in FEATURE_COLUMNS:
        if feature not in output.columns:
            output[feature] = 0.0
    output = output[[*FEATURE_COLUMNS, "label", "timestamp", "src_ip", "dst_ip"]]
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT_PATH, index=False)
    print(f"Merged archive rows: {len(output):,} -> {OUTPUT_PATH}")
    print(output["label"].value_counts().head().to_dict())
    return OUTPUT_PATH


def main() -> None:
    dataset_path = build_archive_dataset()
    subprocess.run(
        [
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
            "3",
            "--patience",
            "1",
        ],
        check=False,
    )


if __name__ == "__main__":
    main()
