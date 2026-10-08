"""
validation.py - Sentinel-WM Twin Fidelity Check

Twin Fidelity Validation module for measuring Digital Twin simulation accuracy and state drift.
Compares free-running autoregressive rollouts against actual ground-truth test sequences.
"""

from typing import List, Dict, Any, Optional
import numpy as np
import torch

from state import NetworkGraphState
from twin_engine import DigitalTwin


def validate_twin_fidelity(
    twin: DigitalTwin,
    ground_truth_sequences: List[List[NetworkGraphState]],
    k_steps: int = 10,
) -> Dict[str, Any]:
    """
    Evaluate empirical simulation realism and degradation drift of the Digital Twin.

    Args:
        twin: Initialized DigitalTwin simulation engine.
        ground_truth_sequences: List of temporal ground-truth NetworkGraphState sequences.
        k_steps: Maximum evaluation rollout horizon steps.

    Returns:
        Dict[str, Any]: Quantitative fidelity metrics dictionary.
    """
    if not ground_truth_sequences:
        raise ValueError("Ground-truth sequences list cannot be empty for fidelity validation.")

    total_sequences = len(ground_truth_sequences)
    step_feature_errors: Dict[int, List[float]] = {t: [] for t in range(1, k_steps + 1)}
    stage_correct: List[bool] = []
    inf_prob_errors: List[float] = []

    all_pred_states: List[np.ndarray] = []
    all_true_states: List[np.ndarray] = []

    for seq in ground_truth_sequences:
        if len(seq) < 2:
            continue

        seed_state = seq[0]
        actual_horizon = min(k_steps, len(seq) - 1)

        # Run rollout without early stopping for full benchmark horizon
        trajectory = twin.rollout(
            seed_state=seed_state,
            k_steps=actual_horizon,
            stop_on_terminal=False,
        )

        for t_idx, step_pred in enumerate(trajectory):
            t_num = step_pred["step"]
            gt_graph = seq[t_num]

            pred_feat = step_pred["raw_state"].flatten()
            
            # Extract ground truth target node features
            target_ip = step_pred.get("target_ip", "192.168.1.20")
            gt_host = gt_graph.get_host(target_ip)
            if not gt_host:
                first_ip = list(gt_graph.hosts.keys())[0]
                gt_host = gt_graph.hosts[first_ip]

            gt_feat = gt_host.features.flatten()

            min_dim = min(len(pred_feat), len(gt_feat))
            pred_feat = pred_feat[:min_dim]
            gt_feat = gt_feat[:min_dim]

            feat_mse = float(np.mean((pred_feat - gt_feat) ** 2))
            step_feature_errors[t_num].append(feat_mse)

            all_pred_states.append(pred_feat)
            all_true_states.append(gt_feat)

            # Stage Accuracy
            is_correct = (step_pred["stage_idx"] == gt_host.stage_idx)
            stage_correct.append(is_correct)

            # Infiltration MAE
            inf_err = abs(step_pred["infiltration_probability"] - gt_host.infiltration_prob)
            inf_prob_errors.append(inf_err)

    if all_pred_states:
        overall_pred_np = np.vstack(all_pred_states)
        overall_true_np = np.vstack(all_true_states)
        overall_mse = float(np.mean((overall_pred_np - overall_true_np) ** 2))
        overall_mae = float(np.mean(np.abs(overall_pred_np - overall_true_np)))
    else:
        overall_mse = 0.0
        overall_mae = 0.0

    drift_curve = {
        f"step_{t}": float(np.mean(errs)) if errs else 0.0
        for t, errs in step_feature_errors.items()
    }

    stage_acc = float(np.mean(stage_correct)) if stage_correct else 0.0
    inf_prob_mae = float(np.mean(inf_prob_errors)) if inf_prob_errors else 0.0

    fidelity_report: Dict[str, Any] = {
        "num_sequences_evaluated": total_sequences,
        "horizon_k_steps": k_steps,
        "overall_state_mse": overall_mse,
        "overall_state_mae": overall_mae,
        "stage_accuracy": stage_acc,
        "stage_accuracy_percent": round(stage_acc * 100, 2),
        "infiltration_prob_mae": inf_prob_mae,
        "horizon_drift_curve_mse": drift_curve,
    }

    return fidelity_report
