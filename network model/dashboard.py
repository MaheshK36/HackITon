"""
CyberSeer Dashboard
Visual status board for all 11 phases and system components.
"""

import os
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List


class CyberSeerDashboard:
    """Display system status and metrics."""
    
    def __init__(self, data_root: str = "data", models_root: str = "models"):
        self.data_root = Path(data_root)
        self.models_root = Path(models_root)
        self.workspace = Path(__file__).parent
    
    def clear_screen(self):
        """Clear terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def print_header(self):
        """Print fancy header."""
        header = """
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                  ║
║                           🛡️  CYBERSEER: PREDICTIVE CYBER DEFENSE 🛡️                          ║
║                                                                                                  ║
║                        Forecast attack propagation. Evaluate interventions.                      ║
║                              Defend before compromise occurs.                                    ║
║                                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝
"""
        print(header)
    
    def print_phase_status(self):
        """Print status of all 11 phases."""
        print("\n" + "=" * 100)
        print("SYSTEM STATUS - 11 PHASES")
        print("=" * 100)
        
        phases = [
            {
                'num': 1,
                'name': 'Data Pipeline',
                'status': self._check_phase_1(),
                'tasks': ['Load datasets', 'Create features', 'Build sequences', 'Build graphs']
            },
            {
                'num': 2,
                'name': 'Baseline Models',
                'status': self._check_phase_2(),
                'tasks': ['Logistic Regression', 'Random Forest']
            },
            {
                'num': 3,
                'name': 'Temporal Models',
                'status': self._check_phase_3(),
                'tasks': ['LSTM', 'GRU']
            },
            {
                'num': 4,
                'name': 'Hybrid GNN+Transformer',
                'status': self._check_phase_4(),
                'tasks': ['Encoder (LSTM)', 'Transformer', '5-window forecast']
            },
            {
                'num': 5,
                'name': 'Attack Propagation',
                'status': self._check_phase_5(),
                'tasks': ['Future surface', 'Attack momentum', 'Blast radius']
            },
            {
                'num': 6,
                'name': 'Counterfactual Defense',
                'status': 'PENDING',
                'tasks': ['Intervention simulation', 'Counterfactual engine']
            },
            {
                'num': 7,
                'name': 'Explainability',
                'status': 'PENDING',
                'tasks': ['Attention weights', 'SHAP values']
            },
            {
                'num': 8,
                'name': 'Backend API',
                'status': 'PENDING',
                'tasks': ['FastAPI', 'Endpoints', 'Database']
            },
            {
                'num': 9,
                'name': 'Frontend Dashboard',
                'status': 'PENDING',
                'tasks': ['React', 'Visualization', 'Controls']
            },
            {
                'num': 10,
                'name': 'Demo Mode',
                'status': 'PENDING',
                'tasks': ['Guided walkthrough', 'Jury presentation']
            },
            {
                'num': 11,
                'name': 'Docker + Deployment',
                'status': 'PENDING',
                'tasks': ['Containerization', 'Production setup']
            },
        ]
        
        for phase in phases:
            status_icon = self._get_status_icon(phase['status'])
            print(f"\n{status_icon} Phase {phase['num']}: {phase['name']:<30} [{phase['status']:<10}]")
            for task in phase['tasks']:
                print(f"    → {task}")
    
    def _get_status_icon(self, status: str) -> str:
        """Get icon for status."""
        icons = {
            'COMPLETE': '✅',
            'IN_PROGRESS': '🔄',
            'PENDING': '⏳',
            'ERROR': '❌'
        }
        return icons.get(status, '❓')
    
    def _check_phase_1(self) -> str:
        """Check Phase 1 completion."""
        files = [
            self.data_root / "processed" / "features.csv",
            self.data_root / "sequences" / "X_sequences.npy",
            self.data_root / "graphs" / "graphs.json"
        ]
        return 'COMPLETE' if all(f.exists() for f in files) else 'PENDING'
    
    def _check_phase_2(self) -> str:
        """Check Phase 2 completion."""
        files = [
            self.models_root / "logistic_regression.pkl",
            self.models_root / "random_forest.pkl"
        ]
        return 'COMPLETE' if all(f.exists() for f in files) else 'PENDING'
    
    def _check_phase_3(self) -> str:
        """Check Phase 3 completion."""
        files = [
            self.models_root / "lstm_best.pth",
            self.models_root / "gru_best.pth"
        ]
        return 'COMPLETE' if all(f.exists() for f in files) else 'PENDING'
    
    def _check_phase_4(self) -> str:
        """Check Phase 4 completion."""
        return 'COMPLETE' if (self.models_root / "gnn_transformer_best.pth").exists() else 'PENDING'
    
    def _check_phase_5(self) -> str:
        """Check Phase 5 completion."""
        return 'COMPLETE' if (self.data_root / "phase5_results.json").exists() else 'PENDING'
    
    def print_quick_stats(self):
        """Print quick statistics."""
        print("\n" + "=" * 100)
        print("QUICK STATS")
        print("=" * 100)
        
        stats = {}
        
        # Check data
        if (self.data_root / "processed" / "features.csv").exists():
            try:
                import pandas as pd
                df = pd.read_csv(self.data_root / "processed" / "features.csv")
                stats['Data Windows'] = f"{len(df):,} × {len(df.columns)} columns"
            except:
                pass
        
        # Check sequences
        if (self.data_root / "sequences" / "X_sequences.npy").exists():
            try:
                import numpy as np
                X = np.load(self.data_root / "sequences" / "X_sequences.npy")
                stats['Sequences'] = f"Shape: {X.shape} (samples, windows, features)"
            except:
                pass
        
        # Check graphs
        if (self.data_root / "graphs" / "graphs.json").exists():
            try:
                with open(self.data_root / "graphs" / "graphs.json", 'r') as f:
                    graphs = json.load(f)
                    stats['Graphs'] = f"{len(graphs)} network graphs loaded"
            except:
                pass
        
        # Model metrics
        metrics_file = self.models_root / "full_comparison.csv"
        if metrics_file.exists():
            try:
                import pandas as pd
                df = pd.read_csv(metrics_file)
                if 'F1' in df.columns:
                    best_f1 = df['F1'].max()
                    stats['Best Model F1'] = f"{best_f1:.4f}"
            except:
                pass
        
        for key, value in stats.items():
            print(f"  • {key:<20}: {value}")
    
    def print_quick_commands(self):
        """Print quick reference commands."""
        print("\n" + "=" * 100)
        print("QUICK COMMANDS")
        print("=" * 100)
        
        commands = [
            ("Run all phases", "python run_all_phases.py"),
            ("Run Phase 1 only", "python run_all_phases.py 1"),
            ("Run Phases 2-4", "python run_all_phases.py 2,3,4"),
            ("Run Phase 5 analysis", "python ml/models/phase5_analysis.py"),
            ("View full status", "python PHASE_STATUS.md"),
            ("Quick start guide", "python QUICKSTART.md"),
            ("View docs", "Start with docs/PHASES_2_4_MODELS.md"),
        ]
        
        for description, command in commands:
            print(f"\n  {description}:")
            print(f"    $ {command}")
    
    def print_directory_tree(self):
        """Print project directory structure."""
        print("\n" + "=" * 100)
        print("PROJECT STRUCTURE")
        print("=" * 100)
        
        tree = """
SIH-ROUND2/
├── 📊 PHASE_STATUS.md              ← Full system status
├── 📋 QUICKSTART.md                ← 5-min overview
├── 🚀 run_all_phases.py            ← Master orchestrator
├── 📁 dashboard.py                 ← This dashboard
│
├── data/                           ← Datasets & processed outputs
│   ├── raw/                        Phase 1: Raw datasets (optional)
│   ├── processed/features.csv      Phase 1: Windowed features
│   ├── sequences/X_sequences.npy   Phase 1: Temporal sequences
│   ├── graphs/graphs.json          Phase 1: Network graphs
│   └── phase5_results.json         Phase 5: Propagation analysis
│
├── ml/                             ← Machine Learning Modules
│   ├── preprocessing/
│   │   ├── data_loader.py          Phase 1: Load raw data
│   │   ├── preprocess_dataset.py   Phase 1: Feature engineering
│   │   ├── build_sequences.py      Phase 1: Temporal sequences
│   │   ├── build_graphs.py         Phase 1: Network graphs
│   │   └── validate_dataset.py     Phase 1: Validation
│   └── models/
│       ├── baseline.py             Phase 2: LR + RF
│       ├── lstm_model.py           Phase 3: LSTM + GRU
│       ├── gnn_transformer_model.py Phase 4: Hybrid model
│       └── phase5_analysis.py      Phase 5: Propagation
│
├── models/                         ← Trained model artifacts
│   ├── *.pkl                       Baseline & scaler files
│   ├── *.pth                       Neural network weights
│   └── *_results.json              Model performance metrics
│
├── docs/                           ← Documentation
│   ├── PHASES_2_4_MODELS.md        ML architectures
│   ├── RESEARCH_FOUNDATION.md      Phase 5 theory
│   ├── DATASET_SETUP.md            How to get data
│   └── DEPLOYMENT.md               Docker setup
│
├── configs/                        ← Configuration files
│   ├── dataset.yaml                Phase 1 config
│   ├── model.yaml                  Model config
│   └── .env.example                Environment variables
│
├── requirements.txt                ← Python dependencies
└── run_phase1.bat/sh               ← Automation scripts
"""
        print(tree)
    
    def print_performance_summary(self):
        """Print model performance summary."""
        print("\n" + "=" * 100)
        print("EXPECTED MODEL PERFORMANCE")
        print("=" * 100)
        
        performance = """
Phase 2 - Baseline Models:
  ├─ Logistic Regression:  90% F1, 2.4% FPR, 0.95 AUC
  └─ Random Forest:        91% F1, 1.9% FPR, 0.95 AUC

Phase 3 - Temporal Models:
  ├─ LSTM:                 92.8% F1, 0.97 AUC  (+2% vs baseline)
  └─ GRU:                  92.5% F1, 0.97 AUC

Phase 4 - Hybrid Model:
  └─ GNN + Transformer:    93.8% F1, 0.97 AUC  (+1% vs LSTM, 5-window forecast)

Phase 5 - Propagation:
  ├─ Future Attack Surface: P(compromise) rankings per host
  ├─ Attack Momentum:       Score [0,1] measuring speed, targeting, progression
  └─ Blast Radius:         Predicted damage + chokepoint analysis
"""
        print(performance)
    
    def print_next_steps(self):
        """Print recommended next steps."""
        print("\n" + "=" * 100)
        print("NEXT STEPS")
        print("=" * 100)
        
        steps = """
1. ✅ Review current status above
2. 🚀 Execute the pipeline:
   
   python run_all_phases.py

3. 📊 Monitor training progress (watch console output)
4. 📈 Check generated results:
   
   - models/full_comparison.csv (all model metrics)
   - data/phase5_results.json (propagation analysis)

5. 📚 Deep dive documentation:
   
   - docs/PHASES_2_4_MODELS.md (architecture details)
   - docs/RESEARCH_FOUNDATION.md (Phase 5 formulas)

6. 🎯 Next phases (6-11):
   
   ├─ Phase 6: Counterfactual defense engine
   ├─ Phase 7: Explainability (attention + SHAP)
   ├─ Phase 8: Backend API (FastAPI)
   ├─ Phase 9: Frontend dashboard (React)
   ├─ Phase 10: Demo mode (jury presentation)
   └─ Phase 11: Docker + deployment
"""
        print(steps)
    
    def print_footer(self):
        """Print footer."""
        footer = """
╔══════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                  ║
║  "Today's tools tell defenders what is happening.                                               ║
║   This system models what the network is becoming."                                             ║
║                                                                                                  ║
║  CyberSeer: Predictive Defense, Not Reactive Response                                           ║
║                                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════╝
"""
        print(footer)
        print(f"\nDashboard generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def show(self):
        """Display complete dashboard."""
        self.clear_screen()
        self.print_header()
        self.print_phase_status()
        self.print_quick_stats()
        self.print_performance_summary()
        self.print_directory_tree()
        self.print_quick_commands()
        self.print_next_steps()
        self.print_footer()


def main():
    """Run dashboard."""
    dashboard = CyberSeerDashboard()
    dashboard.show()


if __name__ == "__main__":
    main()
