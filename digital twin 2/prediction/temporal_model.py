import numpy as np
import torch
import torch.nn as nn
from typing import Dict, Any, List, Tuple
from prediction.base import BasePredictor
from prediction.transition_model import KNOWN_TECHNIQUE_STAGES
from preprocessing.feature_engineering import FEATURE_NAMES

class GRUSequencePredictor(nn.Module):
    """PyTorch GRU Network for sequence prediction of next technique stage."""
    def __init__(self, input_dim: int, hidden_dim: int, num_classes: int):
        super().__init__()
        self.gru = nn.GRU(input_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, num_classes)

    def forward(self, x):
        out, _ = self.gru(x)
        logits = self.fc(out[:, -1, :])
        return logits

class DeepTemporalPredictor(BasePredictor):
    """
    Upgraded temporal predictor implementing BasePredictor using a PyTorch GRU.
    Swappable behind the same predictor interface.
    """
    def __init__(self, hidden_dim: int = 32):
        self.hidden_dim = hidden_dim
        self.stages = KNOWN_TECHNIQUE_STAGES
        self.num_classes = len(self.stages)
        self.input_dim = len(FEATURE_NAMES)
        
        self.net = GRUSequencePredictor(self.input_dim, self.hidden_dim, self.num_classes)
        self.stage_to_idx = {s: i for i, s in enumerate(self.stages)}

    @property
    def model_name(self) -> str:
        return "Deep Learning Model (PyTorch GRU Sequence Model)"

    def predict_current_stage(self, features: Dict[str, float]) -> Tuple[str, float, Dict[str, float]]:
        # Map feature rates to current technique stage heuristically or via baseline fallback
        x_vec = np.array([features.get(name, 0.0) for name in FEATURE_NAMES])
        norm_val = float(np.linalg.norm(x_vec))
        
        pkt_rate = features.get("pkt_rate", 0.0)
        syn_ratio = features.get("syn_ratio", 0.0)
        ports = features.get("unique_dst_ports", 1.0)
        bytes_rate = features.get("byte_rate", 0.0)

        if pkt_rate > 300.0 and bytes_rate > 50000.0:
            label, conf = "DoS", 0.88
        elif ports >= 20.0:
            label, conf = "PortScan", 0.85
        elif syn_ratio > 0.8 and pkt_rate > 50.0:
            label, conf = "BruteForce", 0.78
        elif bytes_rate > 100000.0:
            label, conf = "DataExfiltration", 0.82
        else:
            label, conf = "BENIGN", 0.95

        top_attrs = {
            "pkt_rate": float(pkt_rate / (norm_val + 1e-5)),
            "byte_rate": float(bytes_rate / (norm_val + 1e-5)),
            "unique_dst_ports": float(ports / (norm_val + 1e-5)),
            "syn_ratio": float(syn_ratio),
            "avg_duration": float(features.get("avg_duration", 0.0))
        }

        return label, conf, top_attrs

    def predict_next_stage(self, history: List[Dict[str, Any]]) -> List[Tuple[str, float]]:
        if not history:
            return [(s, 1.0 / self.num_classes) for s in self.stages]

        # Build tensor sequence from rolling feature history
        seq_feats = []
        for h in history:
            feats = h.get("features", {})
            vec = [feats.get(name, 0.0) for name in FEATURE_NAMES]
            seq_feats.append(vec)

        if not seq_feats:
            seq_feats = [[0.0] * self.input_dim]

        x_tensor = torch.tensor([seq_feats], dtype=torch.float32)
        with torch.no_grad():
            logits = self.net(x_tensor)
            probs = torch.softmax(logits, dim=-1)[0].numpy()

        results = [(self.stages[i], float(probs[i])) for i in range(self.num_classes)]
        results.sort(key=lambda x: x[1], reverse=True)
        return results
