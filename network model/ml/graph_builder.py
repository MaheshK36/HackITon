"""Per-window host-communication graph builder for PyTorch Geometric GNN models."""

from __future__ import annotations

import torch
from torch_geometric.data import Data


def build_window_graph(
    window_data: dict | None = None,
    num_nodes: int = 10,
    in_channels: int = 16,
    seed: int = 42,
) -> Data:
    """Build a PyTorch Geometric Data object representing a 60s window host-communication graph.

    Nodes represent network hosts; edges represent communication links.
    Node features are derived from window statistics or initialized host features.
    """
    torch.manual_seed(seed)
    
    if window_data is not None and isinstance(window_data, dict):
        n_flows = int(window_data.get("n_flows", 10))
        num_nodes = max(4, min(30, int(window_data.get("dst_port_nunique_approx", 5)) + 4))
        bytes_per_pkt = float(window_data.get("bytes_per_packet", 100.0))
        tcp_ratio = float(window_data.get("tcp_ratio", 0.8))
        syn_mean = float(window_data.get("syn_mean", 0.1))
        
        # Base node features derived from window attributes
        base_feat = torch.tensor([
            n_flows / 100.0,
            bytes_per_pkt / 1000.0,
            tcp_ratio,
            syn_mean,
        ], dtype=torch.float32)
        
        # Expand base features with host-specific noise/variation
        x = base_feat.repeat(num_nodes, in_channels // 4 + 1)[:, :in_channels]
        x = x + 0.1 * torch.randn(num_nodes, in_channels)
    else:
        x = torch.randn(num_nodes, in_channels)

    # Generate edge connections (communication graph structure)
    edges = []
    for i in range(num_nodes):
        # Connect each host to next host and hub host 0
        edges.append((i, (i + 1) % num_nodes))
        edges.append(((i + 1) % num_nodes, i))
        if i != 0:
            edges.append((0, i))
            edges.append((i, 0))
            
    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
    
    return Data(x=x, edge_index=edge_index)


if __name__ == "__main__":
    g = build_window_graph()
    print(f"Sample window graph: {g}")
    print(f"Node features shape: {g.x.shape}")
    print(f"Edge index shape: {g.edge_index.shape}")
