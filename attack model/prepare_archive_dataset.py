from __future__ import annotations

import glob
from pathlib import Path

import pandas as pd

from data_pipeline import FEATURE_COLUMNS, STAGE_MAPPING

ARCHIVE_GLOB = r"C:/Users/mahes/Downloads/archive/*.csv"
OUTPUT_PATH = Path("data/archive_combined.csv")


def _find_column(frame: pd.DataFrame, aliases: list[str]) -> str | None:
    normalized = {str(c).strip().lower(): c for c in frame.columns}
    for alias in aliases:
        if alias.strip().lower() in normalized:
            return normalized[alias.strip().lower()]
    return None


def _coerce_feature(df: pd.DataFrame, target_name: str, aliases: list[str]) -> pd.Series:
    source = _find_column(df, aliases)
    if source is None:
        return pd.Series(0.0, index=df.index, dtype=float)
    return pd.to_numeric(df[source], errors="coerce").fillna(0.0)


def normalize_row(row: pd.Series) -> dict[str, object]:
    feature_map = {
        "src_ip": "10.0.0.1",
        "dst_ip": "10.0.0.2",
        "timestamp": pd.to_datetime(row.get("Timestamp"), errors="coerce") if "Timestamp" in row.index else pd.Timestamp.now(),
        "label": str(row.get("Label", "BENIGN")).strip(),
    }
    for name in FEATURE_COLUMNS:
        if name in {"src_ip", "dst_ip", "label", "timestamp"}:
            continue
        alias_map = {
            "src_port": ["src_port", "Source Port", "Src Port"],
            "dst_port": ["dst_port", "Destination Port", "Dst Port"],
            "protocol": ["protocol", "Protocol"],
            "tcp_flags": ["tcp_flags", "TCP Flags", "Flag", "Flags"],
            "bytes_per_flow": ["bytes_per_flow", "Total Length of Fwd Packets", "TotLen Fwd Pkts"],
            "packets_per_flow": ["packets_per_flow", "Total Fwd Packets", "Tot Fwd Pkts"],
            "flow_duration": ["flow_duration", "Flow Duration"],
            "iat_mean": ["iat_mean", "Flow IAT Mean"],
            "iat_variance": ["iat_variance", "Flow IAT Std"],
            "iat_max": ["iat_max", "Flow IAT Max"],
            "bidirectional_flow_ratio": ["bidirectional_flow_ratio", "Flow Byts/s", "Bwd Pkts/s"],
            "ttl": ["ttl", "TTL", "Average Packet TTL"],
            "ttl_variance": ["ttl_variance", "TTL Variance"],
            "tcp_window_size": ["tcp_window_size", "Init Fwd Win Byts", "TCP Window Size"],
            "ip_fragment_flags": ["ip_fragment_flags", "IP Fragment Flags"],
            "payload_size": ["payload_size", "Pkt Len Mean", "Average Packet Size"],
            "port_scan_signature": ["port_scan_signature", "Port Scan Signature", "SYN Flag Cnt"],
            "retransmission_count": ["retransmission_count", "Retransmission Count"],
        }
        value = row.get(_find_column(pd.DataFrame([row]), alias_map.get(name, [])), 0.0) if _find_column(pd.DataFrame([row]), alias_map.get(name, [])) is not None else 0.0
        feature_map[name] = pd.to_numeric(value, errors="coerce") if pd.notna(value) else 0.0
    return feature_map


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    records = [normalize_row(row) for _, row in df.iterrows()]
    return pd.DataFrame(records)


def main() -> None:
    files = sorted(glob.glob(ARCHIVE_GLOB))
    if not files:
        raise FileNotFoundError(f"No archive CSV files found under {ARCHIVE_GLOB}")

    rows: list[dict[str, object]] = []
    for path in files:
        raw = pd.read_csv(path, low_memory=False)
        for _, row in raw.iterrows():
            row_record = normalize_row(row)
            rows.append(row_record)

    output = pd.DataFrame(rows)
    for missing in [col for col in FEATURE_COLUMNS if col not in output.columns]:
        output[missing] = 0.0
    output["src_ip"] = output.get("src_ip", "10.0.0.1")
    output["dst_ip"] = output.get("dst_ip", "10.0.0.2")
    output["timestamp"] = pd.to_datetime(output.get("timestamp"), errors="coerce")
    output["label"] = output.get("label", "BENIGN").astype(str).str.strip()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {len(output):,} rows to {OUTPUT_PATH}")
    print(output["label"].value_counts().head().to_dict())


if __name__ == "__main__":
    main()
