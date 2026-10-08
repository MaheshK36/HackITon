"""
normalization.py - Feature Schema Adapter & Normalization Layer

Standardizes incoming network flow dictionaries, packet logs, and login access events
into 42-element model feature vectors and clean audit record structures.
"""

from typing import Dict, Any, List
import numpy as np

from digital_twin.state import DEFAULT_FLOW_FEATURES


def normalize_flow_dict(flow_data: Dict[str, Any]) -> np.ndarray:
    """
    Extracts and standardizes raw flow features into the 42-element numpy float32 vector
    expected by PyTorch AttackWorldModel.

    Handles alias key names (e.g. 'Flow Duration' vs 'flow_duration', 'SYN Flag' vs 'syn_flag_cnt').
    """
    vector = np.zeros(len(DEFAULT_FLOW_FEATURES), dtype=np.float32)

    # Key alias map to accommodate varying flow column naming conventions
    alias_map = {
        "flow_duration": ["flow_duration", "Flow Duration", "duration"],
        "tot_fwd_pkts": ["tot_fwd_pkts", "Total Fwd Packets", "fwd_pkts_count"],
        "tot_bwd_pkts": ["tot_bwd_pkts", "Total Backward Packets", "bwd_pkts_count"],
        "totlen_fwd_pkts": ["totlen_fwd_pkts", "Total Length of Fwd Packets", "fwd_bytes"],
        "totlen_bwd_pkts": ["totlen_bwd_pkts", "Total Length of Bwd Packets", "bwd_bytes"],
        "flow_byts_s": ["flow_byts_s", "Flow Bytes/s", "bytes_per_sec"],
        "flow_pkts_s": ["flow_pkts_s", "Flow Packets/s", "pkts_per_sec"],
        "syn_flag_cnt": ["syn_flag_cnt", "SYN Flag Count", "syn_flag"],
        "fin_flag_cnt": ["fin_flag_cnt", "FIN Flag Count", "fin_flag"],
        "rst_flag_cnt": ["rst_flag_cnt", "RST Flag Count", "rst_flag"],
        "psh_flag_cnt": ["psh_flag_cnt", "PSH Flag Count", "psh_flag"],
    }

    for idx, feature_name in enumerate(DEFAULT_FLOW_FEATURES):
        aliases = alias_map.get(feature_name, [feature_name])
        val = 0.0
        for alias in aliases:
            if alias in flow_data:
                try:
                    val = float(flow_data[alias])
                    break
                except (ValueError, TypeError):
                    pass
        vector[idx] = val

    # Standard scaling normalization (clip extreme outliers)
    vector = np.nan_to_num(vector, nan=0.0, posinf=1000.0, neginf=-1000.0)
    vector = np.clip(vector, -10.0, 10.0)

    return vector


def normalize_access_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Standardizes software access event payloads for audit logging.
    """
    return {
        "event_id": str(event_data.get("event_id", "")),
        "user_id": str(event_data.get("user_id", "usr_unknown")),
        "event_type": str(event_data.get("event_type", "login")).lower(),
        "ip_address": str(event_data.get("ip_address", "127.0.0.1")),
        "location": str(event_data.get("location", "Internal Subnet")),
        "device_info": str(event_data.get("device_info", "Browser Client")),
        "timestamp": str(event_data.get("timestamp", "")),
    }
