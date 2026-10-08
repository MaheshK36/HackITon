"""
graph_encoder.py - CyberSeer GNN Attack Propagation & Forecast Engine

Integrates trained Graph Neural Network model (PyG GraphSAGE + GRU recurrent cell)
for blast radius, future attack surface expansion, and multi-step risk propagation.
Falls back transparently to topology risk diffusion when no trained GNN checkpoint is found.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

try:
    from torch_geometric.nn import SAGEConv
    PYG_AVAILABLE = True
except ImportError:
    PYG_AVAILABLE = False


class CyberGNNForecastModel(nn.Module):
    """
    Graph Neural Network model for attack classification and multi-step propagation forecasting.
    """

    def __init__(
        self,
        in_node_channels: int = 16,
        in_edge_channels: int = 10,
        hidden_dim: int = 64,
        num_classes: int = 6,
    ) -> None:
        super().__init__()
        if not PYG_AVAILABLE:
            raise RuntimeError("torch_geometric is required for CyberGNNForecastModel.")

        self.conv1 = SAGEConv(in_node_channels, hidden_dim)
        self.conv2 = SAGEConv(hidden_dim, hidden_dim)
        self.edge_mlp = nn.Sequential(
            nn.Linear(hidden_dim * 2 + in_edge_channels, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, num_classes),
        )
        self.node_risk_head = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid(),
        )
        self.rnn_cell = nn.GRUCell(hidden_dim, hidden_dim)
        self.prop_gate = nn.Sequential(
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid(),
        )

    def encode(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        h1 = F.relu(self.conv1(x, edge_index))
        h2 = F.relu(self.conv2(h1, edge_index))
        return h2

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        edge_attr: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        h = self.encode(x, edge_index)
        u, v = edge_index[0], edge_index[1]
        edge_repr = torch.cat([h[u], h[v], edge_attr], dim=-1)
        edge_logits = self.edge_mlp(edge_repr)
        node_risks = self.node_risk_head(h).squeeze(-1)
        return edge_logits, node_risks, h


class GraphEncoder(nn.Module):
    """
    Unified Graph Forecaster for CyberSeer.
    Loads and runs trained CyberGNNForecastModel when available, or transparently
    falls back to topology risk diffusion heuristic.
    """

    def __init__(
        self,
        in_channels: int = 16,
        hidden_dim: int = 64,
        checkpoint_path: Optional[str | Path] = None,
    ) -> None:
        super().__init__()
        self.in_channels = in_channels
        self.hidden_dim = hidden_dim

        self.is_trained: bool = False
        self.model_version: str = "propagation-heuristic-v1"
        self.metrics: Dict[str, Any] = {}
        self.trained_gnn: Optional[CyberGNNForecastModel] = None

        if checkpoint_path is not None:
            self.load_checkpoint(checkpoint_path)

    def load_checkpoint(self, path: str | Path) -> bool:
        """Attempt loading a trained GNN checkpoint and its metrics."""
        ckpt_path = Path(path)
        if not ckpt_path.exists():
            return False

        if not PYG_AVAILABLE:
            return False

        try:
            ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
            model = CyberGNNForecastModel(
                in_node_channels=ckpt.get("in_node_channels", 16),
                in_edge_channels=ckpt.get("in_edge_channels", 10),
                hidden_dim=ckpt.get("hidden_dim", 64),
                num_classes=ckpt.get("num_classes", 6),
            )
            model.load_state_dict(ckpt["model_state_dict"])
            model.eval()

            self.trained_gnn = model
            self.model_version = ckpt.get("version", "gnn-cyberseer-v1.0")
            self.metrics = ckpt.get("metrics", {})
            self.is_trained = True

            # Also check if metrics json exists next to it
            metrics_json = ckpt_path.parent / f"gnn_metrics_{self.model_version.replace('gnn-cyberseer-', '')}.json"
            if metrics_json.exists():
                with open(metrics_json, "r") as f:
                    self.metrics = json.load(f)

            return True
        except Exception as e:
            print(f"[GraphEncoder] Failed to load checkpoint {path}: {e}")
            self.is_trained = False
            self.trained_gnn = None
            return False

    def predict_propagation(
        self,
        node_states: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        steps: int = 5,
    ) -> Dict[str, Any]:
        """
        Executes propagation forecast using trained GNN if loaded, otherwise falls back
        to topology risk diffusion heuristic.
        """
        if self.is_trained and self.trained_gnn is not None:
            return self._predict_gnn(node_states, edges, steps)
        else:
            return self._predict_topology_fallback(node_states, edges, steps)

    def _predict_gnn(
        self,
        node_states: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        steps: int = 5,
    ) -> Dict[str, Any]:
        num_nodes = len(node_states)
        if num_nodes == 0:
            return {
                "num_nodes": 0,
                "forecast_steps": [],
                "method": f"GNN (trained, {self.model_version})",
                "model_version": self.model_version,
                "is_trained": True,
                "evaluation_metrics": self.metrics,
            }

        ip_to_idx = {node["ip_address"]: i for i, node in enumerate(node_states)}
        src_list, dst_list = [], []
        for edge in edges:
            u_ip, v_ip = edge.get("source"), edge.get("target")
            if u_ip in ip_to_idx and v_ip in ip_to_idx:
                src_list.append(ip_to_idx[u_ip])
                dst_list.append(ip_to_idx[v_ip])
                src_list.append(ip_to_idx[v_ip])
                dst_list.append(ip_to_idx[u_ip])

        if not src_list:
            src_list = list(range(num_nodes))
            dst_list = list(range(num_nodes))

        edge_index = torch.tensor([src_list, dst_list], dtype=torch.long)

        node_feats = np.zeros((num_nodes, 16), dtype=np.float32)
        for i, n in enumerate(node_states):
            node_feats[i, 0] = float(len(n.get("open_ports", [])))
            node_feats[i, 1] = float(n.get("criticality", 0.5))
            node_feats[i, 2] = float(n.get("infiltration_prob", 0.05))
            node_feats[i, 3] = float(n.get("stage_idx", 0))

        x = torch.tensor(node_feats, dtype=torch.float)

        self.trained_gnn.eval()
        with torch.no_grad():
            h0 = self.trained_gnn.encode(x, edge_index)
            base_risk = self.trained_gnn.node_risk_head(h0).squeeze(-1).cpu().numpy()

        current_risks = np.array(
            [max(float(node.get("infiltration_prob", 0.05)), float(base_risk[i])) for i, node in enumerate(node_states)],
            dtype=np.float32,
        )

        adj = np.zeros((num_nodes, num_nodes), dtype=np.float32)
        for u, v in zip(src_list, dst_list):
            adj[u, v] = 1.0

        deg = np.maximum(adj.sum(axis=1, keepdims=True), 1.0)
        norm_adj = adj / deg

        forecast_steps = []
        forecast_risks = np.copy(current_risks)
        h_t = h0

        with torch.no_grad():
            for t in range(1, steps + 1):
                prop_impact = np.dot(norm_adj, forecast_risks)
                alpha = float(self.trained_gnn.prop_gate(h_t).mean().item())
                alpha = float(np.clip(alpha, 0.25, 0.60))

                forecast_risks = np.clip(
                    forecast_risks + alpha * prop_impact * (1.0 - forecast_risks),
                    0.0,
                    0.99,
                )

                agg_h = torch.tensor(np.dot(norm_adj, h_t.numpy()), dtype=torch.float)
                h_t = self.trained_gnn.rnn_cell(agg_h, h_t)

                step_hosts = []
                for i, node in enumerate(node_states):
                    r = float(forecast_risks[i])
                    status = "compromised" if r >= 0.5 else ("target" if r >= 0.25 else "normal")
                    step_hosts.append({
                        "ip_address": node["ip_address"],
                        "hostname": node.get("hostname", node["ip_address"]),
                        "risk_score": round(r, 4),
                        "status": status,
                    })

                forecast_steps.append({
                    "step": t,
                    "hosts": step_hosts,
                    "avg_network_risk": round(float(np.mean(forecast_risks)), 4),
                })

        high_risk_count = int(np.sum(forecast_risks >= 0.5))
        medium_risk_count = int(np.sum((forecast_risks >= 0.25) & (forecast_risks < 0.5)))
        blast_radius_pct = float((high_risk_count + medium_risk_count) / max(num_nodes, 1) * 100)
        attack_momentum = float(np.max(forecast_risks) - np.max(current_risks))

        return {
            "num_nodes": num_nodes,
            "forecast_steps": forecast_steps,
            "blast_radius_percent": round(blast_radius_pct, 2),
            "high_risk_nodes": high_risk_count,
            "medium_risk_nodes": medium_risk_count,
            "attack_momentum": round(attack_momentum, 4),
            "summary_recommendation": (
                "CRITICAL: Immediate micro-segmentation required for core Database & App servers."
                if blast_radius_pct >= 40.0
                else "STABLE: Monitor gateway traffic for early stage recon."
            ),
            "method": f"GNN (trained, {self.model_version})",
            "model_version": self.model_version,
            "is_trained": True,
            "evaluation_metrics": self.metrics,
        }

    def _predict_topology_fallback(
        self,
        node_states: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        steps: int = 5,
    ) -> Dict[str, Any]:
        """Topology diffusion heuristic fallback."""
        num_nodes = len(node_states)
        ip_to_idx = {node["ip_address"]: i for i, node in enumerate(node_states)}

        adj = np.zeros((num_nodes, num_nodes), dtype=np.float32)
        for edge in edges:
            u_ip, v_ip = edge["source"], edge["target"]
            if u_ip in ip_to_idx and v_ip in ip_to_idx:
                u, v = ip_to_idx[u_ip], ip_to_idx[v_ip]
                adj[u, v] = 1.0
                adj[v, u] = 1.0

        current_risks = np.array([node.get("infiltration_prob", 0.05) for node in node_states], dtype=np.float32)

        forecast_steps = []
        forecast_risks = np.copy(current_risks)

        for t in range(1, steps + 1):
            deg = np.maximum(np.sum(adj, axis=1, keepdims=True), 1.0)
            norm_adj = adj / deg
            neighbor_impact = np.dot(norm_adj, forecast_risks)
            forecast_risks = np.clip(forecast_risks + 0.35 * neighbor_impact * (1.0 - forecast_risks), 0.0, 0.99)

            step_hosts = []
            for i, node in enumerate(node_states):
                r = float(forecast_risks[i])
                status = "compromised" if r >= 0.5 else ("target" if r >= 0.25 else "normal")
                step_hosts.append({
                    "ip_address": node["ip_address"],
                    "hostname": node["hostname"],
                    "risk_score": round(r, 4),
                    "status": status,
                })

            forecast_steps.append({
                "step": t,
                "hosts": step_hosts,
                "avg_network_risk": float(np.mean(forecast_risks)),
            })

        high_risk_count = int(np.sum(forecast_risks >= 0.5))
        medium_risk_count = int(np.sum((forecast_risks >= 0.25) & (forecast_risks < 0.5)))
        blast_radius_pct = float((high_risk_count + medium_risk_count) / max(num_nodes, 1) * 100)
        attack_momentum = float(np.max(forecast_risks) - np.max(current_risks))

        return {
            "num_nodes": num_nodes,
            "forecast_steps": forecast_steps,
            "blast_radius_percent": round(blast_radius_pct, 2),
            "high_risk_nodes": high_risk_count,
            "medium_risk_nodes": medium_risk_count,
            "attack_momentum": round(attack_momentum, 4),
            "summary_recommendation": (
                "CRITICAL: Immediate micro-segmentation required for core Database & App servers."
                if blast_radius_pct >= 40.0
                else "STABLE: Monitor gateway traffic for early stage recon."
            ),
            "method": "Topology risk diffusion (fallback)",
            "model_version": "propagation-heuristic-v1",
            "is_trained": False,
            "limitations": "This is an uncalibrated topology heuristic, not a trained GNN forecast.",
        }
