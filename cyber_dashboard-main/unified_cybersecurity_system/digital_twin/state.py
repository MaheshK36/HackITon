"""
state.py - Sentinel-WM Network Graph State

Network Graph State abstraction module for Network Digital Twin.
Represents the network as a graph (nodes = hosts/devices, edges = network connections/flows).
Maintains per-host MITRE ATT&CK stages, infiltration probabilities, compromise status,
and flow feature vectors.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import networkx as nx
import numpy as np

# Standard 42-feature schema matching attack model & digital twin pipelines
DEFAULT_FLOW_FEATURES: List[str] = [
    "flow_duration", "tot_fwd_pkts", "tot_bwd_pkts", "totlen_fwd_pkts", "totlen_bwd_pkts",
    "fwd_pkt_len_max", "fwd_pkt_len_min", "fwd_pkt_len_mean", "fwd_pkt_len_std",
    "bwd_pkt_len_max", "bwd_pkt_len_min", "bwd_pkt_len_mean", "bwd_pkt_len_std",
    "flow_byts_s", "flow_pkts_s", "flow_iat_mean", "flow_iat_std", "flow_iat_max", "flow_iat_min",
    "fwd_iat_tot", "fwd_iat_mean", "fwd_iat_std", "fwd_iat_max", "fwd_iat_min",
    "bwd_iat_tot", "bwd_iat_mean", "bwd_iat_std", "bwd_iat_max", "bwd_iat_min",
    "fwd_header_len", "bwd_header_len", "fwd_pkts_s", "bwd_pkts_s",
    "pkt_len_min", "pkt_len_max", "pkt_len_mean", "pkt_len_std", "pkt_len_var",
    "fin_flag_cnt", "syn_flag_cnt", "rst_flag_cnt", "psh_flag_cnt"
]

# Standard 7-stage MITRE ATT&CK kill-chain progression
DEFAULT_MITRE_STAGES: List[str] = [
    "Reconnaissance",
    "Initial Access",
    "Execution",
    "Persistence",
    "Privilege Escalation",
    "Lateral Movement",
    "Exfiltration",
]


@dataclass
class HostNode:
    """
    Represents an individual network host/device node within the Digital Twin.
    """
    ip_address: str
    hostname: str
    role: str = "Workstation"
    status: str = "normal"  # 'normal', 'target', 'compromised', 'isolated'
    stage_idx: int = 0
    stage_name: str = "Reconnaissance"
    infiltration_prob: float = 0.05
    criticality: float = 0.5
    open_ports: List[int] = field(default_factory=list)
    services: List[str] = field(default_factory=list)
    features: np.ndarray = field(default_factory=lambda: np.zeros(len(DEFAULT_FLOW_FEATURES), dtype=np.float32))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize host node state to a dictionary."""
        return {
            "ip_address": self.ip_address,
            "hostname": self.hostname,
            "role": self.role,
            "status": self.status,
            "stage_idx": self.stage_idx,
            "stage_name": self.stage_name,
            "infiltration_prob": float(self.infiltration_prob),
            "criticality": float(self.criticality),
            "open_ports": list(self.open_ports),
            "services": list(self.services),
        }


class NetworkGraphState:
    """
    Represents the full topological graph state of the Network Digital Twin.
    """

    def __init__(self, feature_cols: Optional[List[str]] = None, demo_topology: bool = True) -> None:
        """Initialize a graph; the fixed topology is available only for explicit demo mode."""
        self.feature_cols: List[str] = feature_cols if feature_cols is not None else DEFAULT_FLOW_FEATURES
        self.graph: nx.Graph = nx.Graph()
        self.hosts: Dict[str, HostNode] = {}
        self.pos_layout: Dict[str, Tuple[float, float]] = {}

        if demo_topology:
            self._build_default_topology()

    def _build_default_topology(self) -> None:
        """Construct a realistic 6-node enterprise network graph topology."""
        nodes_info = [
            ("192.168.1.1", "Ext-Router", "Gateway", 0.4, [80, 22], ["HTTP", "SSH"]),
            ("192.168.1.10", "DMZ-Firewall", "Security Gateway", 0.6, [443, 22], ["HTTPS", "SSH"]),
            ("192.168.1.20", "Web-Server", "Web Infrastructure", 0.7, [80, 443, 8080], ["HTTP", "HTTPS", "Nginx"]),
            ("192.168.1.30", "App-Server", "Application Cluster", 0.8, [8080, 22, 8443], ["Tomcat", "SSH", "API"]),
            ("192.168.1.40", "Core-Database", "Database Server", 0.95, [5432, 445, 1521], ["PostgreSQL", "SMB", "Oracle"]),
            ("192.168.1.50", "Workstation-01", "User Device", 0.3, [445, 3389], ["SMB", "RDP"]),
        ]

        preset_positions = {
            "192.168.1.1": (-2.0, 0.0),
            "192.168.1.10": (-1.0, 0.0),
            "192.168.1.20": (0.0, 1.0),
            "192.168.1.30": (0.0, -1.0),
            "192.168.1.40": (1.5, 0.0),
            "192.168.1.50": (-1.0, -1.5),
        }

        for ip, name, role, crit, ports, svcs in nodes_info:
            # Demo topology must be deterministic and must not imply observed telemetry.
            feat_vec = np.zeros(len(self.feature_cols), dtype=np.float32)
            host = HostNode(
                ip_address=ip,
                hostname=name,
                role=role,
                status="normal",
                stage_idx=0,
                stage_name=DEFAULT_MITRE_STAGES[0],
                infiltration_prob=0.05,
                criticality=crit,
                open_ports=ports,
                services=svcs,
                features=feat_vec,
            )
            self.hosts[ip] = host
            self.graph.add_node(ip, **host.to_dict())
            self.pos_layout[ip] = preset_positions.get(ip, (0.0, 0.0))

        edges = [
            ("192.168.1.1", "192.168.1.10"),
            ("192.168.1.10", "192.168.1.20"),
            ("192.168.1.10", "192.168.1.30"),
            ("192.168.1.10", "192.168.1.50"),
            ("192.168.1.20", "192.168.1.40"),
            ("192.168.1.30", "192.168.1.40"),
        ]

        for u, v in edges:
            self.graph.add_edge(u, v, active_attack=False, weight=1.0)

    def get_host(self, ip_address: str) -> Optional[HostNode]:
        """Retrieve HostNode by IP address."""
        return self.hosts.get(ip_address, None)

    def ensure_host(
        self,
        ip_address: str,
        hostname: Optional[str] = None,
        role: str = "Observed Host",
        criticality: float = 0.5,
    ) -> HostNode:
        """Add an observed host on first telemetry sighting and return it."""
        if ip_address not in self.hosts:
            host = HostNode(
                ip_address=ip_address,
                hostname=hostname or ip_address,
                role=role,
                stage_name=DEFAULT_MITRE_STAGES[0],
                criticality=float(np.clip(criticality, 0.0, 1.0)),
                features=np.zeros(len(self.feature_cols), dtype=np.float32),
            )
            self.hosts[ip_address] = host
            self.graph.add_node(ip_address, **host.to_dict())
        return self.hosts[ip_address]

    def observe_flow(self, source_ip: str, destination_ip: str, destination_port: Optional[int] = None) -> None:
        """Create graph nodes/communication edge directly from validated telemetry."""
        self.ensure_host(source_ip)
        self.ensure_host(destination_ip)
        if not self.graph.has_edge(source_ip, destination_ip):
            self.graph.add_edge(source_ip, destination_ip, active_attack=False, flow_count=0, ports=[])
        edge = self.graph.edges[source_ip, destination_ip]
        edge["flow_count"] = int(edge.get("flow_count", 0)) + 1
        if destination_port is not None and destination_port not in edge["ports"]:
            edge["ports"].append(destination_port)

    def update_host_state(
        self,
        ip_address: str,
        stage_idx: int,
        stage_name: str,
        infiltration_prob: float,
        next_features: Optional[np.ndarray] = None,
    ) -> None:
        """Update host state and graph node attributes."""
        if ip_address not in self.hosts:
            return

        host = self.hosts[ip_address]
        host.stage_idx = stage_idx
        host.stage_name = stage_name
        host.infiltration_prob = float(infiltration_prob)

        if next_features is not None:
            host.features = next_features

        if infiltration_prob >= 0.5 or stage_idx >= 3:
            host.status = "compromised"
        elif infiltration_prob >= 0.25 or stage_idx >= 1:
            host.status = "target"
        else:
            host.status = "normal"

        self.graph.nodes[ip_address].update(host.to_dict())

    def propagate_compromise(
        self,
        source_ip: str,
        target_ip: str,
        stage_idx: int,
        stage_name: str,
        infiltration_prob: float,
    ) -> None:
        """Mark edge as active attack vector and update target host node."""
        if self.graph.has_edge(source_ip, target_ip):
            self.graph.edges[source_ip, target_ip]["active_attack"] = True

        self.update_host_state(
            ip_address=target_ip,
            stage_idx=stage_idx,
            stage_name=stage_name,
            infiltration_prob=infiltration_prob,
        )

    def clone(self) -> "NetworkGraphState":
        """Create a deep copy snapshot of the current network graph state."""
        new_state = NetworkGraphState(feature_cols=list(self.feature_cols), demo_topology=False)
        for ip, host in self.hosts.items():
            new_state.hosts[ip] = HostNode(
                ip_address=host.ip_address,
                hostname=host.hostname,
                role=host.role,
                status=host.status,
                stage_idx=host.stage_idx,
                stage_name=host.stage_name,
                infiltration_prob=host.infiltration_prob,
                criticality=host.criticality,
                open_ports=list(host.open_ports),
                services=list(host.services),
                features=np.copy(host.features),
            )
            new_state.graph.add_node(ip, **new_state.hosts[ip].to_dict())

        for u, v, d in self.graph.edges(data=True):
            new_state.graph.add_edge(u, v, **dict(d))

        return new_state
