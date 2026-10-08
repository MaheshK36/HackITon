"""
CyberSeer: Run Complete Pipeline (Phase 1-4)
Executes all data processing, baseline training, and advanced models.
"""

import subprocess
import sys
import json
from pathlib import Path
import pandas as pd


def run_command(cmd: str, description: str):
    """Run a command and handle errors."""
    print("\n" + "=" * 100)
    print(f"► {description}")
    print("=" * 100)
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=False)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error: {description} failed with code {e.returncode}")
        return False


def compare_models(models_root: str = "models"):
    """Compare all trained models."""
    models_dir = Path(models_root)
    
    print("\n" + "=" * 100)
    print("Model Performance Comparison (All Phases)")
    print("=" * 100)
    
    comparison_data = []
    
    # Baseline
    baseline_file = models_dir / "baseline_results.json"
    if baseline_file.exists():
        with open(baseline_file, 'r') as f:
            baseline = json.load(f)
        
        for model_name in ['Logistic Regression', 'Random Forest']:
            if model_name in baseline:
                test_metrics = baseline[model_name]['test']
                comparison_data.append({
                    'Phase': '2 (Baseline)',
                    'Model': model_name,
                    'Test Precision': f"{test_metrics['precision']:.4f}",
                    'Test Recall': f"{test_metrics['recall']:.4f}",
                    'Test F1': f"{test_metrics['f1']:.4f}",
                    'Test AUC': f"{test_metrics['roc_auc']:.4f}",
                    'Test FPR': f"{test_metrics['fpr']:.4f}",
                })
    
    # LSTM
    lstm_file = models_dir / "lstm_results.json"
    if lstm_file.exists():
        with open(lstm_file, 'r') as f:
            lstm = json.load(f)
        
        test_metrics = lstm['test']
        comparison_data.append({
            'Phase': '3 (Temporal)',
            'Model': 'LSTM',
            'Test Precision': f"{test_metrics['precision']:.4f}",
            'Test Recall': f"{test_metrics['recall']:.4f}",
            'Test F1': f"{test_metrics['f1']:.4f}",
            'Test AUC': f"{test_metrics['roc_auc']:.4f}",
            'Test FPR': 'N/A',
        })
    
    # GRU
    gru_file = models_dir / "gru_results.json"
    if gru_file.exists():
        with open(gru_file, 'r') as f:
            gru = json.load(f)
        
        test_metrics = gru['test']
        comparison_data.append({
            'Phase': '3 (Temporal)',
            'Model': 'GRU',
            'Test Precision': f"{test_metrics['precision']:.4f}",
            'Test Recall': f"{test_metrics['recall']:.4f}",
            'Test F1': f"{test_metrics['f1']:.4f}",
            'Test AUC': f"{test_metrics['roc_auc']:.4f}",
            'Test FPR': 'N/A',
        })
    
    # GNN + Transformer
    hybrid_file = models_dir / "gnn_transformer_results.json"
    if hybrid_file.exists():
        with open(hybrid_file, 'r') as f:
            hybrid = json.load(f)
        
        test_metrics = hybrid['test']
        comparison_data.append({
            'Phase': '4 (Hybrid)',
            'Model': 'GNN+Transformer',
            'Test Precision': f"{test_metrics['precision']:.4f}",
            'Test Recall': f"{test_metrics['recall']:.4f}",
            'Test F1': f"{test_metrics['f1']:.4f}",
            'Test AUC': f"{test_metrics['roc_auc']:.4f}",
            'Test FPR': 'N/A',
        })
    
    if comparison_data:
        df = pd.DataFrame(comparison_data)
        print("\n" + df.to_string(index=False))
        
        # Save comparison
        comparison_file = Path(models_root) / "full_comparison.csv"
        df.to_csv(comparison_file, index=False)
        print(f"\n✓ Comparison saved to {comparison_file}")
    else:
        print("No model results found. Run individual phases first.")


def main():
    """Run complete pipeline."""
    print("\n" + "╔" + "=" * 98 + "╗")
    print("║" + " " * 98 + "║")
    print("║" + "CyberSeer: Complete Pipeline (Phase 1-4)".center(98) + "║")
    print("║" + " " * 98 + "║")
    print("╚" + "=" * 98 + "╝")
    
    # Parse arguments
    phases_to_run = ['1', '2', '3', '4']
    if len(sys.argv) > 1:
        phases_to_run = sys.argv[1].split(',')
    
    print(f"\nPhases to run: {', '.join(phases_to_run)}")
    
    py = sys.executable
    # Phase 1: Data Pipeline
    if '1' in phases_to_run:
        run_command(
            f'"{py}" ml/preprocessing/data_loader.py',
            "Phase 1.1: Load raw data (CIC-IDS-2018, CTU-13)"
        )
        
        run_command(
            f'"{py}" ml/preprocessing/preprocess_dataset.py',
            "Phase 1.2: Preprocess into 5-min windows"
        )
        
        run_command(
            f'"{py}" ml/preprocessing/build_sequences.py',
            "Phase 1.3: Build temporal sequences"
        )
        
        run_command(
            f'"{py}" ml/preprocessing/build_graphs.py',
            "Phase 1.4: Build network graphs"
        )
        
        run_command(
            f'"{py}" ml/preprocessing/validate_dataset.py',
            "Phase 1.5: Validate complete pipeline"
        )
    
    # Phase 2: Baseline Models
    if '2' in phases_to_run:
        run_command(
            f'"{py}" ml/models/baseline.py',
            "Phase 2: Train baseline models (LR, RF)"
        )
    
    # Phase 3: Temporal Models
    if '3' in phases_to_run:
        run_command(
            f'"{py}" ml/models/lstm_model.py',
            "Phase 3: Train temporal models (LSTM, GRU)"
        )
    
    # Phase 4: Hybrid Model
    if '4' in phases_to_run:
        run_command(
            f'"{py}" ml/models/gnn_transformer_model.py',
            "Phase 4: Train hybrid model (GNN+Transformer)"
        )
    
    # Compare
    print("\n" + "=" * 100)
    compare_models()
    
    print("\n" + "=" * 100)
    print("✓ Complete Pipeline Finished")
    print("=" * 100)
    
    print(f"""
Pipeline Summary:

Phase 1: Data Processing
- Loads CIC-IDS-2018 (80M flows) or CTU-13 (2M flows)
- Creates 5-minute windows with 45 features each
- Builds temporal sequences (10 past windows → predict next)
- Constructs network graphs (nodes=IPs, edges=flows)
- Output: data/processed, data/sequences, data/graphs

Phase 2: Baseline Models
- Logistic Regression (simple, fast)
- Random Forest (handles non-linearity)
- Establishes performance floor

Phase 3: Temporal Models
- LSTM (Long Short-Term Memory)
- GRU (Gated Recurrent Unit)
- Uses temporal sequence structure

Phase 4: Hybrid Model
- GNN + Transformer (world model)
- Combines network structure + temporal patterns
- Forecasts 5 windows into future
- Expected: Best warning lead time

Next Steps:
- Phase 5: Future Attack Surface + Attack Momentum
- Phase 6: Multi-Future Simulation + Counterfactual Defense
- Phase 7: Explainability (Attention + SHAP)
- Phase 8: Backend API (FastAPI)
- Phase 9: Frontend Dashboard (React)
- Phase 10: Demo Mode (Jury presentation)
- Phase 11: Docker + Deployment
""")


if __name__ == "__main__":
    main()
