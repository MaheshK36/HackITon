import networkx as nx
from typing import List, Dict, Any, Tuple
from preprocessing.flow_extractor import FlowRecord
from digital_twin.network_model import HostNode, FlowEdge

STATE_COLOR_MAP = {
    "OBSERVED": "#E63946",   # Crimson Red
    "SUSPECTED": "#F4A261",  # Amber Orange
    "PREDICTED": "#9D4EDD",  # Violet / Purple
    "BENIGN": "#2A9D8F"      # Cyan / Emerald
}

class DigitalTwinStateManager:
    """
    Maintains network topology and node threat states.
    Updates strictly as a deterministic function of:
      (a) flows observed in the current window
      (b) model inferences for those flows/hosts in this window.
    """
    def __init__(self):
        self.graph = nx.DiGraph()
        self.hosts: Dict[str, HostNode] = {}
        self.edges: Dict[Tuple[str, str], FlowEdge] = {}

    def update_window_state(
        self,
        window_flows: List[FlowRecord],
        current_detection: Dict[str, Any],
        per_host_detections: Dict[str, Dict[str, Any]],
        predictions: List[Dict[str, Any]],
        window_timestamp: float
    ):
        """Deterministically update Digital Twin graph strictly from window data."""
        # 1. Update Edges & Active Hosts from flows observed in current window
        current_active_hosts = set()
        self.edges.clear()

        for flow in window_flows:
            src = flow.src_ip
            dst = flow.dst_ip
            current_active_hosts.add(src)
            current_active_hosts.add(dst)

            edge_key = (src, dst)
            if edge_key not in self.edges:
                self.edges[edge_key] = FlowEdge(src_ip=src, dst_ip=dst)
            
            edge = self.edges[edge_key]
            edge.flow_count += 1
            edge.total_bytes += flow.tot_bytes
            edge.dst_ports.add(flow.dst_port)

        # Ensure all active IPs exist in host dictionary
        for ip in current_active_hosts:
            if ip not in self.hosts:
                self.hosts[ip] = HostNode(ip=ip, last_updated=window_timestamp)

        # 2. Reset host states to BENIGN default, then apply per-host / global model inferences
        for ip, host in self.hosts.items():
            if ip in current_active_hosts:
                host.last_updated = window_timestamp

            # Default to BENIGN
            host.state = "BENIGN"
            host.technique_id = "T0000"
            host.technique_name = "Benign Activity"
            host.confidence = 1.0

        # Apply per-host detector outputs
        for host_ip, det in per_host_detections.items():
            if host_ip in self.hosts:
                host = self.hosts[host_ip]
                host.state = det["state"]
                host.technique_id = det["technique_id"]
                host.technique_name = det["name"]
                host.confidence = det["confidence"]

        # If global detection is non-benign and per-host wasn't set, assign to top source host
        global_state = current_detection.get("state", "BENIGN")
        if global_state in ["OBSERVED", "SUSPECTED"]:
            top_src = max(
                (f.src_ip for f in window_flows),
                key=lambda ip: sum(1 for f in window_flows if f.src_ip == ip),
                default=None
            )
            if top_src and top_src in self.hosts:
                host = self.hosts[top_src]
                if host.state == "BENIGN" or det_priority(global_state) > det_priority(host.state):
                    host.state = global_state
                    host.technique_id = current_detection["technique_id"]
                    host.technique_name = current_detection["name"]
                    host.confidence = current_detection["confidence"]

        # Apply predictions (PREDICTED state) to candidate target nodes or source nodes
        if predictions:
            top_pred = predictions[0]
            pred_prob = top_pred.get("probability", 0.0)
            pred_tech = top_pred.get("name", "Unknown")

            for ip, host in self.hosts.items():
                if host.state in ["OBSERVED", "SUSPECTED"]:
                    host.predicted_next_technique = pred_tech
                    host.predicted_probability = pred_prob

        # 3. Rebuild NetworkX Graph
        self.graph.clear()
        for ip, host in self.hosts.items():
            self.graph.add_node(
                ip,
                state=host.state,
                color=STATE_COLOR_MAP.get(host.state, STATE_COLOR_MAP["BENIGN"]),
                technique_id=host.technique_id,
                technique_name=host.technique_name,
                confidence=host.confidence,
                predicted_next_technique=host.predicted_next_technique,
                predicted_probability=host.predicted_probability,
                last_updated=host.last_updated
            )

        for (src, dst), edge in self.edges.items():
            self.graph.add_edge(
                src,
                dst,
                flow_count=edge.flow_count,
                total_bytes=edge.total_bytes,
                dst_ports=list(edge.dst_ports)
            )

    def get_summary(self) -> Dict[str, Any]:
        return {
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "hosts": {ip: h.to_dict() for ip, h in self.hosts.items()}
        }

def det_priority(state: str) -> int:
    priorities = {"OBSERVED": 3, "SUSPECTED": 2, "PREDICTED": 1, "BENIGN": 0}
    return priorities.get(state, 0)
