from __future__ import annotations

import glob
from pathlib import Path

import pandas as pd

ARCHIVE_GLOB = r"C:/Users/mahes/Downloads/archive/*.csv"
OUT_PATH = Path("data/archive_combined.csv")

FEATURE_COLUMNS = [
    "src_ip",
    "dst_ip",
    "src_port",
    "dst_port",
    "protocol",
    "tcp_flags",
    "bytes_per_flow",
    "packets_per_flow",
    "flow_duration",
    "iat_mean",
    "iat_variance",
    "iat_max",
    "bidirectional_flow_ratio",
    "ttl",
    "ttl_variance",
    "tcp_window_size",
    "ip_fragment_flags",
    "payload_size",
    "port_scan_signature",
    "retransmission_count",
]


def normalize_label(raw: object) -> str:
    value = str(raw).strip()
    if not value:
        return "BENIGN"
    lower = value.lower()
    if lower in {"benign", "normal"}:
        return "BENIGN"
    if "goldeneye" in lower or "slowloris" in lower or "ddos" in lower or "dos" in lower:
        return "DOS"
    if "scan" in lower:
        return "PORTSCAN"
    if "brute" in lower:
        return "BRUTE FORCE"
    if "infiltration" in lower:
        return "INFILTRATION"
    if "lateral" in lower:
        return "LATERAL MOVEMENT"
    if "c2" in lower or "bot" in lower or "command" in lower:
        return "C2"
    if "exfil" in lower:
        return "EXFILTRATION"
    return "BENIGN"


def read_archive_frames() -> list[pd.DataFrame]:
    files = sorted(glob.glob(ARCHIVE_GLOB))
    if not files:
        raise FileNotFoundError(f"No archive CSV files found under {ARCHIVE_GLOB}")

    frames: list[pd.DataFrame] = []
    for file in files:
        raw = pd.read_csv(file, low_memory=False)
        if raw.empty:
            continue
        sample = raw.copy()
        if "Label" in sample.columns:
            sample["label"] = sample["Label"].map(normalize_label)
        else:
            sample["label"] = "BENIGN"
        if "Timestamp" in sample.columns:
            sample["timestamp"] = pd.to_datetime(sample["Timestamp"], dayfirst=True, errors="coerce")
        else:
            sample["timestamp"] = pd.to_datetime("2000-01-01")

        for field in [
            ("src_port", ["Src Port", "Source Port"]),
            ("dst_port", ["Dst Port", "Destination Port"]),
            ("protocol", ["Protocol"]),
            ("tcp_flags", ["FIN Flag Cnt", "SYN Flag Cnt", "TCP Flags"]),
            ("bytes_per_flow", ["Flow Bytes/s", "TotLen Fwd Pkts", "Total Length of Fwd Packets"]),
            ("packets_per_flow", ["Tot Fwd Pkts", "Total Fwd Packets"]),
            ("flow_duration", ["Flow Duration"]),
            ("iat_mean", ["Flow IAT Mean", "Fwd IAT Mean"]),
            ("iat_variance", ["Flow IAT Std", "Fwd IAT Std"]),
            ("iat_max", ["Flow IAT Max", "Fwd IAT Max"]),
            ("bidirectional_flow_ratio", ["Bwd Pkts/s", "Bwd Packets/s"]),
            ("ttl", ["TTL", "Idle Mean"]),
            ("ttl_variance", ["TTL Variance"]),
            ("tcp_window_size", ["Init Fwd Win Byts", "TCP Window Size"]),
            ("ip_fragment_flags", ["IP Fragment Flags"]),
            ("payload_size", ["Pkt Len Mean", "Average Packet Size", "Packet Length Mean"]),
            ("port_scan_signature", ["Port Scan Signature"]),
            ("retransmission_count", ["Retransmission Count"]),
        ]:
            name, aliases = field
            source = None
            for alias in aliases:
                if alias in sample.columns:
                    source = alias
                    break
            if source is None:
                sample[name] = 0.0
            else:
                sample[name] = pd.to_numeric(sample[source], errors="coerce").fillna(0.0)

        sample["src_ip"] = [f"10.0.{idx % 32}.1" for idx in range(len(sample))]
        sample["dst_ip"] = "10.0.0.2"
        sample = sample[[
            "src_ip", "dst_ip",
            "src_port", "dst_port", "protocol", "tcp_flags",
            "bytes_per_flow", "packets_per_flow", "flow_duration",
            "iat_mean", "iat_variance", "iat_max",
            "bidirectional_flow_ratio", "ttl", "ttl_variance",
            "tcp_window_size", "ip_fragment_flags", "payload_size",
            "port_scan_signature", "retransmission_count", "label", "timestamp"
        ]].dropna(subset=["timestamp"]).reset_index(drop=True)

        if sample.empty:
            continue
        # keep a balanced subset for CPU-safe training while preserving both benign and attack windows
        label_counts = sample["label"].value_counts().to_dict()
        max_rows_per_label = 6000
        subset = pd.concat([
            group.head(max_rows_per_label) for _, group in sample.groupby("label", sort=False)
        ], ignore_index=True)
        frames.append(subset)
    return frames


def main() -> None:
    frames = read_archive_frames()
    if not frames:
        raise RuntimeError("No valid archive rows were created.")
    output = pd.concat(frames, ignore_index=True)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUT_PATH, index=False)
    print(f"archive_rows={len(output):,}")
    print(output["label"].value_counts().to_dict())
    print(f"output_path={OUT_PATH}")


if __name__ == "__main__":
    main()
