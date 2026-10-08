"""
train_baseline.py - Reproducible Model Training & Evaluation Pipeline

Trains a Random Forest Classifier and Markov Sequence Transition Model
on multi-stage cyberattack flow scenarios.
Generates genuine held-out evaluation metrics (Accuracy, Macro Precision, Recall, F1).
Saves the serialized artifact to data/models/baseline_rf.pkl.
"""

import os
import sys
from pathlib import Path

# Add project root and unified backend to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
UNIFIED_DIR = ROOT_DIR / "cyber_dashboard-main" / "unified_cybersecurity_system"
DT2_DIR = ROOT_DIR / "digital twin 2"

for p in [str(ROOT_DIR), str(UNIFIED_DIR), str(DT2_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import pandas as pd
from backend.services.ml_engine import MLEngine


def ensure_scenario_datasets(data_dir: Path) -> list[pd.DataFrame]:
    data_dir.mkdir(parents=True, exist_ok=True)
    file_a = data_dir / "scenario_a_recon_bruteforce_exfil.csv"
    file_b = data_dir / "scenario_b_dos_command_exec.csv"
    file_c = data_dir / "scenario_c_benign.csv"

    # If not present in data_dir, try copying from digital twin 2 or generate them
    dt2_raw = DT2_DIR / "data" / "raw"
    if not (file_a.exists() and file_b.exists() and file_c.exists()):
        if dt2_raw.exists() and (dt2_raw / "scenario_a_recon_bruteforce_exfil.csv").exists():
            import shutil
            for name in ["scenario_a_recon_bruteforce_exfil.csv", "scenario_b_dos_command_exec.csv", "scenario_c_benign.csv"]:
                src = dt2_raw / name
                if src.exists():
                    shutil.copy(src, data_dir / name)

    # If still not present, generate them directly
    if not (file_a.exists() and file_b.exists() and file_c.exists()):
        from scripts.generate_sample_data import generate_datasets
        generate_datasets(str(data_dir))

    df_a = pd.read_csv(file_a)
    df_b = pd.read_csv(file_b)
    df_c = pd.read_csv(file_c)
    return [df_a, df_b, df_c]


def run_training() -> dict:
    print("=" * 70)
    print(" TRAINING PREDICTIVE CYBER-DEFENCE BASELINE ML MODEL")
    print("=" * 70)

    raw_dir = ROOT_DIR / "data" / "raw"
    dfs = ensure_scenario_datasets(raw_dir)
    total_flows = sum(len(df) for df in dfs)
    print(f" Loaded {len(dfs)} scenario datasets totaling {total_flows} flow records.")

    engine = MLEngine()
    model_output_path = ROOT_DIR / "data" / "models" / "baseline_rf.pkl"
    unified_model_path = UNIFIED_DIR / "data" / "models" / "baseline_rf.pkl"

    metrics = engine.train_baseline_model(dfs, model_output_path)

    # Copy to unified system data dir as well
    unified_model_path.parent.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy(model_output_path, unified_model_path)

    print("\n--- Genuine Evaluation Metrics on Held-Out Test Data ---")
    print(f" Accuracy:        {metrics['accuracy'] * 100:.2f}%")
    print(f" Macro Precision: {metrics['macro_precision'] * 100:.2f}%")
    print(f" Macro Recall:    {metrics['macro_recall'] * 100:.2f}%")
    print(f" Macro F1 Score:  {metrics['macro_f1'] * 100:.2f}%")
    print(f" Train Samples:   {metrics['train_samples']}")
    print(f" Test Samples:    {metrics['test_samples']}")
    print(f" Classes:         {metrics['classes']}")
    print(f" Model Artifact:  {model_output_path}")
    print("=" * 70)
    return metrics


if __name__ == "__main__":
    run_training()
