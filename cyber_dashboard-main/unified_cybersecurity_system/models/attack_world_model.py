"""
attack_world_model.py - PyTorch Attack World Model Neural Network

Multi-task autoregressive PyTorch architecture predicting next-step network flow feature vectors,
MITRE attack stage logits, and infiltration probabilities.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import torch
from torch import nn


@dataclass
class ModelConfig:
    input_size: int = 42
    hidden_size: int = 64
    num_layers: int = 1
    dropout: float = 0.0
    backbone: str = "lstm"
    num_stages: int = 7
    w_mse: float = 1.0
    w_bce: float = 1.0
    w_ce: float = 1.0


class AttackWorldModel(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        if config.backbone.lower() not in {"lstm", "gru"}:
            raise ValueError("backbone must be 'lstm' or 'gru'.")
        self.config = config
        recurrent = nn.LSTM if config.backbone.lower() == "lstm" else nn.GRU
        self.backbone = recurrent(
            config.input_size,
            config.hidden_size,
            config.num_layers,
            batch_first=True,
            dropout=config.dropout if config.num_layers > 1 else 0.0,
        )
        self.next_state_head = nn.Linear(config.hidden_size, config.input_size)
        self.infiltration_head = nn.Linear(config.hidden_size, 1)
        self.stage_head = nn.Linear(config.hidden_size, config.num_stages)

    def forward(self, sequence: torch.Tensor) -> dict[str, torch.Tensor]:
        output, _ = self.backbone(sequence)
        hidden = output[:, -1, :]
        return {
            "next_state_pred": self.next_state_head(hidden),
            "infiltration_logit": self.infiltration_head(hidden).squeeze(-1),
            "stage_logits": self.stage_head(hidden),
        }

    def compute_loss(
        self,
        outputs: dict[str, torch.Tensor],
        next_state: torch.Tensor,
        infiltration: torch.Tensor,
        stage: torch.Tensor,
        class_weights: torch.Tensor | None = None,
    ) -> dict[str, torch.Tensor]:
        mse = nn.functional.mse_loss(outputs["next_state_pred"], next_state)
        bce = nn.functional.binary_cross_entropy_with_logits(
            outputs["infiltration_logit"], infiltration.float()
        )
        ce = nn.functional.cross_entropy(outputs["stage_logits"], stage.long(), weight=class_weights)
        total = self.config.w_mse * mse + self.config.w_bce * bce + self.config.w_ce * ce
        return {"mse": mse, "bce": bce, "cross_entropy": ce, "total": total}

    @torch.no_grad()
    def predict(self, window_sequence: np.ndarray | torch.Tensor) -> dict:
        self.eval()
        tensor = torch.as_tensor(window_sequence, dtype=torch.float32)
        if tensor.ndim == 1:
            tensor = tensor.unsqueeze(0).unsqueeze(0)
        elif tensor.ndim == 2:
            tensor = tensor.unsqueeze(0)
        outputs = self(tensor)
        stage_probabilities = torch.softmax(outputs["stage_logits"], dim=-1)[0]
        infiltration_prob = torch.sigmoid(outputs["infiltration_logit"])[0]
        predicted_stage = int(stage_probabilities.argmax())
        confidence = float(stage_probabilities.max())
        return {
            "next_state_pred": outputs["next_state_pred"][0].cpu().numpy(),
            "infiltration_prob": float(infiltration_prob),
            "stage_probabilities": stage_probabilities.cpu().numpy().tolist(),
            "predicted_stage": predicted_stage,
            "confidence": confidence,
        }
