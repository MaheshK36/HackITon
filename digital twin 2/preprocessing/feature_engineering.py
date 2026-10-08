import numpy as np
from typing import List, Dict, Any
from preprocessing.flow_extractor import FlowRecord

FEATURE_NAMES = [
    "flow_count",
    "avg_duration",
    "pkt_rate",
    "byte_rate",
    "syn_ratio",
    "rst_ratio",
    "unique_dst_ports",
    "unique_dst_ips",
    "max_pkt_per_flow",
    "avg_pkt_size"
]

def extract_window_features(flows: List[FlowRecord], window_sec: float = 10.0) -> Dict[str, float]:
    """Extract aggregate feature vector for a time-window of flows."""
    if not flows:
        return {name: 0.0 for name in FEATURE_NAMES}

    flow_count = float(len(flows))
    durations = [f.duration for f in flows]
    avg_duration = float(np.mean(durations))

    total_pkts = sum(f.tot_pkts for f in flows)
    total_bytes = sum(f.tot_bytes for f in flows)

    eff_window = max(window_sec, 0.001)
    pkt_rate = float(total_pkts) / eff_window
    byte_rate = float(total_bytes) / eff_window

    syn_count = sum(1 for f in flows if f.syn_flag_cnt > 0)
    rst_count = sum(1 for f in flows if f.rst_flag_cnt > 0)
    syn_ratio = float(syn_count) / flow_count
    rst_ratio = float(rst_count) / flow_count

    unique_dst_ports = float(len(set(f.dst_port for f in flows)))
    unique_dst_ips = float(len(set(f.dst_ip for f in flows)))
    max_pkt_per_flow = float(max(f.tot_pkts for f in flows))
    avg_pkt_size = float(total_bytes) / max(float(total_pkts), 1.0)

    return {
        "flow_count": flow_count,
        "avg_duration": avg_duration,
        "pkt_rate": pkt_rate,
        "byte_rate": byte_rate,
        "syn_ratio": syn_ratio,
        "rst_ratio": rst_ratio,
        "unique_dst_ports": unique_dst_ports,
        "unique_dst_ips": unique_dst_ips,
        "max_pkt_per_flow": max_pkt_per_flow,
        "avg_pkt_size": avg_pkt_size
    }

def extract_per_host_features(flows: List[FlowRecord], window_sec: float = 10.0) -> Dict[str, Dict[str, float]]:
    """Extract aggregate feature vectors grouped by source host IP."""
    host_flows: Dict[str, List[FlowRecord]] = {}
    for f in flows:
        host_flows.setdefault(f.src_ip, []).append(f)

    host_features = {}
    for host_ip, hflows in host_flows.items():
        host_features[host_ip] = extract_window_features(hflows, window_sec)

    return host_features
