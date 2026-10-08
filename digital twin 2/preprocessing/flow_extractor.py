from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class FlowRecord:
    timestamp: float
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    duration: float
    tot_pkts: int
    tot_bytes: int
    syn_flag_cnt: int
    rst_flag_cnt: int
    label: str = "BENIGN"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FlowRecord":
        return cls(
            timestamp=float(data.get("timestamp", 0.0)),
            src_ip=str(data.get("src_ip", "0.0.0.0")),
            dst_ip=str(data.get("dst_ip", "0.0.0.0")),
            src_port=int(data.get("src_port", 0)),
            dst_port=int(data.get("dst_port", 0)),
            protocol=str(data.get("protocol", "TCP")),
            duration=float(data.get("duration", 0.001)),
            tot_pkts=int(data.get("tot_pkts", 1)),
            tot_bytes=int(data.get("tot_bytes", 64)),
            syn_flag_cnt=int(data.get("syn_flag_cnt", 0)),
            rst_flag_cnt=int(data.get("rst_flag_cnt", 0)),
            label=str(data.get("label", "BENIGN"))
        )
