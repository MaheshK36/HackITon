"""
run_sentinel.py - Sentinel-WM

Standalone Command-Line Demonstration & End-to-End Validation Script for Sentinel-WM.
Runs seed loading, autoregressive rollout, dynamic narration generation, static chart plotting,
and twin fidelity validation checks.
"""

import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import torch

DT_DIR = Path(__file__).resolve().parent
if str(DT_DIR) not in sys.path:
    sys.path.insert(0, str(DT_DIR))

from world_model import WorldModel
from state import NetworkGraphState, DEFAULT_FLOW_FEATURES, DEFAULT_MITRE_STAGES
from twin_engine import DigitalTwin
from narration import generate_explanation
from visualize import plot_trajectory_matplotlib
from validation import validate_twin_fidelity


def main() -> None:
    print("\n" + "=" * 76)
    print("        [SENTINEL-WM DIGITAL TWIN - END-TO-END PIPELINE DEMO]")
    print("=" * 76)

    # 1. Initialize Topology & Seed State
    feature_dim = len(DEFAULT_FLOW_FEATURES)
    seed_state = NetworkGraphState(feature_cols=DEFAULT_FLOW_FEATURES)
    print(f"[Sentinel-WM] Loaded enterprise topology with {len(seed_state.hosts)} hosts.")

    # 2. Instantiate World Model Architecture
    model = WorldModel(feature_dim=feature_dim, hidden_dim=64, num_stages=len(DEFAULT_MITRE_STAGES))
    print("[Sentinel-WM] Instantiated WorldModel architecture with .step(x_t, hidden) interface.")

    # 3. Instantiate Digital Twin & Execute Autoregressive Rollout
    twin = DigitalTwin(model=model, stage_names=DEFAULT_MITRE_STAGES)
    k_horizon = 10
    print(f"[Sentinel-WM] Rolling forward {k_horizon} steps (free-running autoregressive rollout)...")

    trajectory = twin.rollout(
        seed_state=seed_state,
        k_steps=k_horizon,
        stop_on_terminal=False,
    )
    print(f"[Sentinel-WM] Simulation complete: {len(trajectory)} steps recorded.")

    # 4. Generate Dynamic Model-Driven Narration Report
    report_text = generate_explanation(trajectory, stage_names=DEFAULT_MITRE_STAGES, min_confidence=0.4)
    print("\n" + report_text + "\n")

    # 5. Generate Matplotlib Plot
    plot_path = str(DT_DIR / "sentinel_trajectory.png")
    plot_trajectory_matplotlib(
        trajectory=trajectory,
        stage_names=DEFAULT_MITRE_STAGES,
        output_path=plot_path,
        title="Sentinel-WM Attack Trajectory & Infiltration Rollout",
    )

    # 6. Run Twin Fidelity Validation Check
    print("\n[Sentinel-WM] Running Twin Fidelity Benchmark against ground-truth sequences...")
    gt_sequence = [seed_state]
    for step_i in range(1, k_horizon + 1):
        gt_g = seed_state.clone()
        target_ip = "192.168.1.30" if step_i > 2 else "192.168.1.20"
        gt_g.update_host_state(
            target_ip,
            stage_idx=min(step_i, 6),
            stage_name=DEFAULT_MITRE_STAGES[min(step_i, 6)],
            infiltration_prob=min(0.1 + step_i * 0.15, 0.95),
        )
        gt_sequence.append(gt_g)

    fidelity_report = validate_twin_fidelity(twin=twin, ground_truth_sequences=[gt_sequence], k_steps=k_horizon)

    print("=" * 76)
    print("                  [TWIN FIDELITY BENCHMARK RESULTS]")
    print("=" * 76)
    print(f"Overall Feature State MSE:     {fidelity_report['overall_state_mse']:.6f}")
    print(f"Overall Feature State MAE:     {fidelity_report['overall_state_mae']:.6f}")
    print(f"Stage Classification Accuracy: {fidelity_report['stage_accuracy_percent']}%")
    print(f"Infiltration Prob MAE:        {fidelity_report['infiltration_prob_mae']:.4f}")
    print("-" * 76)
    print("HORIZON DRIFT CURVE (MSE per step t):")
    for t_key, mse_val in fidelity_report["horizon_drift_curve_mse"].items():
        print(f"  - {t_key}: {mse_val:.6f}")
    print("=" * 76 + "\n")


if __name__ == "__main__":
    main()
