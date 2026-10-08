"""Graph Attention Network (GAT) host-communication graph encoder."""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import GATConv, global_mean_pool


class GraphEncoder(nn.Module):
    """2-layer Graph Attention Network for encoding per-window network graphs into fixed-size vectors."""

    def __init__(
        self,
        in_channels: int = 16,
        hidden_dim: int = 32,
        embedding_dim: int = 32,
        heads: int = 4,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.in_channels = in_channels
        self.hidden_dim = hidden_dim
        self.embedding_dim = embedding_dim
        self.heads = heads

        # Layer 1: GAT layer with multi-head attention
        self.gat1 = GATConv(in_channels, hidden_dim, heads=heads, concat=True, dropout=dropout)

        # Layer 2: GAT layer producing embedding_dim
        self.gat2 = GATConv(hidden_dim * heads, embedding_dim, heads=1, concat=False, dropout=dropout)

        self.fc = nn.Linear(embedding_dim, embedding_dim)

    def forward(self, data: Data, return_attention_weights: bool = False):
        """Forward pass taking a PyG Data graph object.

        Returns:
            torch.Tensor of shape (batch_size, embedding_dim) or (embedding_dim,) if single unbatched graph.
            Optionally returns attention weights if requested.
        """
        x, edge_index = data.x, data.edge_index
        batch = getattr(data, "batch", None)

        if batch is None:
            batch = torch.zeros(x.size(0), dtype=torch.long, device=x.device)

        # Layer 1 with optional attention weight output
        if return_attention_weights:
            x, att1 = self.gat1(x, edge_index, return_attention_weights=True)
        else:
            x = self.gat1(x, edge_index)
        x = F.elu(x)

        # Layer 2
        if return_attention_weights:
            x, att2 = self.gat2(x, edge_index, return_attention_weights=True)
        else:
            x = self.gat2(x, edge_index)
        x = F.elu(x)

        # Global readout pooling
        out = global_mean_pool(x, batch)
        out = self.fc(out)

        is_single = getattr(data, "batch", None) is None and out.size(0) == 1
        res = out.squeeze(0) if is_single else out

        if return_attention_weights:
            return res, (att1, att2)
        return res


if __name__ == "__main__":
    import sys
    from pathlib import Path
    ROOT = Path(__file__).resolve().parents[2]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from ml.graph_builder import build_window_graph

    embedding_dim = 32
    encoder = GraphEncoder(in_channels=16, embedding_dim=embedding_dim)
    encoder.eval()

    sample_graph = build_window_graph(num_nodes=10, in_channels=16)
    with torch.no_grad():
        out = encoder(sample_graph)

    print("=" * 60)
    print("STEP A — Standalone GraphEncoder Test")
    print("=" * 60)
    print(f"Loaded ONE window's graph: {sample_graph}")
    print(f"GraphEncoder output tensor shape: {out.shape}")
    print(f"Matches (embedding_dim={embedding_dim},)? {out.shape == (embedding_dim,)}")
    print("=" * 60)

