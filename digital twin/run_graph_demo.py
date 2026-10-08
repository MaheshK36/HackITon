"""
run_graph_demo.py - Sentinel-WM Live Graph CLI Demo

Runnable CLI demonstration script for real-time live streaming rollouts.
Demonstrates host node state updates, streaming generator execution,
live step narrations, and twin fidelity validation checks.
"""

import time
import sys
from pathlib import Path
import numpy as np
import torch

DT_DIR = Path(__file__).resolve().parent
if str(DT_DIR) not in sys.path:
    sys.path.insert(0, str(DT_DIR))

from world_model import WorldModel
from state import NetworkGraphState, DEFAULT_FLOW_FEATURES, DEFAULT_MITRE_STAGES
from twin_engine import DigitalTwin
from narration import TrajectoryNarrator, generate_explanation
from validation import validate_twin_fidelity


def main() -> None:
    print("\n" + "=" * 78)
    print("      [SENTINEL-WM REAL-TIME DIGITAL TWIN - LIVE STREAMING DEMO]")
    print("=" * 78)

    # 1. Initialize Network Graph State Topology
    feature_dim = len(DEFAULT_FLOW_FEATURES)
    seed_graph = NetworkGraphState(feature_cols=DEFAULT_FLOW_FEATURES)
    print(f"[Digital Twin] Loaded Enterprise Topology with {len(seed_graph.hosts)} host nodes.")

    # 2. Instantiate PyTorch WorldModel Architecture
    model = WorldModel(feature_dim=feature_dim, hidden_dim=64, num_stages=len(DEFAULT_MITRE_STAGES))
    twin = DigitalTwin(model=model, stage_names=DEFAULT_MITRE_STAGES)
    narrator = TrajectoryNarrator(min_confidence=0.4)

    # 3. Execute Live Streaming Generator Rollout
    k_horizon = 8
    print(f"[Digital Twin] Starting live autoregressive rollout stream ({k_horizon} steps)...\n")

    trajectory_history = []
    print(f"{'STEP':<6} | {'TARGET HOST':<20} | {'PREDICTED MITRE STAGE':<22} | {'CONF.':<8} | {'INF. RISK'}")
    print("-" * 78)

    # STREAM ROLLOUT STEP-BY-STEP (CONSUMING GENERATOR)
    for step_data in twin.rollout_stream(seed_state=seed_graph, k_steps=k_horizon, stop_on_terminal=True):
        trajectory_history.append(step_data)

        s_num = step_data["step"]
        target = f"{step_data['target_hostname']} ({step_data['target_ip']})"
        stage = step_data["predicted_stage"]
        conf_str = f"{step_data['stage_confidence'] * 100:5.1f}%"
        inf_str = f"{step_data['infiltration_probability'] * 100:5.1f}%"

        print(f"Step {s_num:<1} | {target:<20} | {stage:<22} | {conf_str:<8} | {inf_str}")
        
        # Live Single-Step Model Alert Narration
        alert_msg = narrator.narrate_step(step_data)
        print(f"       -> {alert_msg}")

        # Simulate real-time streaming delay
        time.sleep(0.3)

    print("-" * 78)
    print("[SUCCESS] Live rollout stream complete.")

    # 4. Generate Full Simulation Summary Report
    print("\n" + generate_explanation(trajectory_history, stage_names=DEFAULT_MITRE_STAGES) + "\n")

    # 5. Execute Twin Fidelity Benchmark
    print("[Digital Twin] Running Twin Fidelity Benchmark on held-out test sequence...")
    gt_sequence = [seed_graph]
    for step_i in range(1, k_horizon + 1):
        gt_g = seed_graph.clone()
        target_ip = "192.168.1.30" if step_i > 2 else "192.168.1.20"
        gt_g.update_host_state(target_ip, stage_idx=min(step_i, 6), stage_name=DEFAULT_MITRE_STAGES[min(step_i, 6)], infiltration_prob=min(0.1 + step_i * 0.15, 0.95))
        gt_sequence.append(gt_g)

    fidelity_report = validate_twin_fidelity(twin=twin, ground_truth_sequences=[gt_sequence], k_steps=k_horizon)

    print("=" * 78)
    print("                  [TWIN FIDELITY BENCHMARK RESULTS]")
    print("=" * 78)
    print(f"Overall Feature State MSE:     {fidelity_report['overall_state_mse']:.6f}")
    print(f"Overall Feature State MAE:     {fidelity_report['overall_state_mae']:.6f}")
    print(f"Stage Classification Accuracy: {fidelity_report['stage_accuracy_percent']}%")
    print(f"Infiltration Prob MAE:        {fidelity_report['infiltration_prob_mae']:.4f}")
    print("-" * 78)
    print("HORIZON DRIFT CURVE (MSE per step t):")
    for t_key, mse_val in fidelity_report["horizon_drift_curve_mse"].items():
        print(f"  - {t_key}: {mse_val:.6f}")
    print("=" * 78 + "\n")


if __name__ == "__main__":
    main()
