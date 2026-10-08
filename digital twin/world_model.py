"""
world_model.py - Sentinel-WM

Defines the PyTorch WorldModel neural network architecture.
Provides a clean .step(x_t, hidden) interface for single-timestep inference during autoregressive rollouts.
"""

from typing import Dict, Any, Tuple, Optional
import torch
import torch.nn as nn


class WorldModel(nn.Module):
    """
    Multi-task recurrent World Model for network flow dynamics prediction.

    Backbone: Recurrent LSTM/GRU cell processing network flow feature vectors.
    Heads:
        1. Infiltration Head: Predicts binary infiltration probability logit.
        2. Stage Head: Predicts multi-class MITRE ATT&CK stage logits.
        3. Next-State Head: Predicts the next-timestep feature vector (dynamics prediction).
    """

    def __init__(
        self,
        feature_dim: int = 24,
        hidden_dim: int = 64,
        num_stages: int = 7,
    ) -> None:
        """
        Initialize the World Model architecture.

        Args:
            feature_dim: Dimension of input flow feature vectors (e.g., CIC-IDS-2018 schema).
            hidden_dim: Dimension of internal recurrent hidden state.
            num_stages: Number of MITRE ATT&CK classification target stages.
        """
        super().__init__()
        self.feature_dim = feature_dim
        self.hidden_dim = hidden_dim
        self.num_stages = num_stages

        # Recurrent Core Cell (LSTM Cell)
        self.lstm_cell = nn.LSTMCell(feature_dim, hidden_dim)

        # Output Head 1: Infiltration Probability (Logit)
        self.infiltration_head = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

        # Output Head 2: MITRE ATT&CK Stage Classification (Logits)
        self.stage_head = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, num_stages),
        )

        # Output Head 3: Next State Feature Vector Prediction
        self.next_state_head = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, feature_dim),
        )

    def step(
        self,
        x_t: torch.Tensor,
        hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
        graph_batch: Any = None,
    ) -> Tuple[Dict[str, torch.Tensor], Tuple[torch.Tensor, torch.Tensor]]:
        """
        Single-step forward pass for free-running autoregressive rollout inference.

        Args:
            x_t: Current network state feature tensor of shape (batch_size, feature_dim).
            hidden: Optional tuple (h_t, c_t) representing current LSTM hidden and cell states.
            graph_batch: Optional graph context batch (e.g. GAT node/edge attributes).

        Returns:
            Tuple[Dict[str, torch.Tensor], Tuple[torch.Tensor, torch.Tensor]]:
                - Dictionary containing:
                    - "infiltration_logit": torch.Tensor (batch_size, 1)
                    - "stage_logits": torch.Tensor (batch_size, num_stages)
                    - "next_state": torch.Tensor (batch_size, feature_dim)
                - Updated recurrent hidden state tuple (h_next, c_next)
        """
        if x_t.ndim == 1:
            x_t = x_t.unsqueeze(0)
        elif x_t.ndim == 3:
            x_t = x_t.squeeze(1)

        batch_size = x_t.shape[0]

        # Initialize zero hidden state if none provided
        if hidden is None:
            h_t = torch.zeros(batch_size, self.hidden_dim, device=x_t.device)
            c_t = torch.zeros(batch_size, self.hidden_dim, device=x_t.device)
        else:
            h_t, c_t = hidden

        # Recurrent state transition
        h_next, c_next = self.lstm_cell(x_t, (h_t, c_t))

        # Predict multi-task outputs from updated recurrent state
        inf_logit = self.infiltration_head(h_next)
        stage_logits = self.stage_head(h_next)
        next_state = self.next_state_head(h_next)

        outputs_dict = {
            "infiltration_logit": inf_logit,
            "stage_logits": stage_logits,
            "next_state": next_state,
        }

        return outputs_dict, (h_next, c_next)
