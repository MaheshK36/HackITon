from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class HostNode:
    ip: str
    state: str = "BENIGN"  # BENIGN, OBSERVED, SUSPECTED, PREDICTED
    technique_id: str = "T0000"
    technique_name: str = "Benign Activity"
    confidence: float = 1.0
    predicted_next_technique: Optional[str] = None
    predicted_probability: float = 0.0
    last_updated: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ip": self.ip,
            "state": self.state,
            "technique_id": self.technique_id,
            "technique_name": self.technique_name,
            "confidence": self.confidence,
            "predicted_next_technique": self.predicted_next_technique,
            "predicted_probability": self.predicted_probability,
            "last_updated": self.last_updated
        }

@dataclass
class FlowEdge:
    src_ip: str
    dst_ip: str
    flow_count: int = 1
    total_bytes: int = 0
    dst_ports: set = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "flow_count": self.flow_count,
            "total_bytes": self.total_bytes,
            "dst_ports": list(self.dst_ports)
        }
