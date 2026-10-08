#!/usr/bin/env python3
"""
CyberSeer Main Entry Point
Central hub for all operations - view status, run phases, view results.
"""

import sys
import subprocess
from pathlib import Path
from typing import List


class CyberSeerCLI:
    """Command-line interface for CyberSeer."""
    
    def __init__(self):
        self.workspace = Path(__file__).parent
    
    def print_banner(self):
        """Print welcome banner."""
        banner = """
╔════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                        ║
║                    🛡️  CYBERSEER - PREDICTIVE CYBER DEFENSE  🛡️                    ║
║                                                                                        ║
║              Forecast network attacks. Evaluate interventions. Defend early.          ║
║                                                                                        ║
╚════════════════════════════════════════════════════════════════════════════════════════╝
"""
        print(banner)
    
    def print_menu(self):
        """Print main menu."""
        menu = """
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              MAIN MENU                                                 │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  📊 VIEW & MANAGE                                                                      │
│  ───────────────────                                                                   │
│   1  📈 Show Dashboard          View system status and metrics                         │
│   2  📋 Show Full Status        Detailed phase-by-phase status                        │
│   3  📚 Show Documentation       List all available docs                               │
│                                                                                        │
│  🚀 RUN PIPELINES                                                                      │
│  ────────────────                                                                      │
│   4  ▶️  Run All Phases (1-5)    Full pipeline: data → models → analysis              │
│   5  ▶️  Run Phase 1 Only        Data preprocessing & validation                      │
│   6  ▶️  Run Phases 2-4          Train baseline + temporal + hybrid models            │
│   7  ▶️  Run Phase 5             Propagation analysis (requires Phase 4)              │
│                                                                                        │
│  📊 VIEW RESULTS                                                                       │
│  ────────────────                                                                      │
│   8  📈 View Model Comparison    Performance metrics (F1, precision, recall)           │
│   9  🔍 View Phase 5 Analysis    Attack surface, momentum, blast radius               │
│  10  📑 View Latest Results      All generated outputs                                │
│                                                                                        │
│  ⚙️  UTILITIES                                                                         │
│  ────────────                                                                          │
│  11  🔧 Check Dependencies       Verify Python packages                               │
│  12  🗑️  Clean Outputs           Remove generated artifacts                           │
│  13  💬 Quick Help               Usage tips & troubleshooting                         │
│                                                                                        │
│  0   ❌ Exit                     Quit CyberSeer CLI                                    │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
"""
        print(menu)
    
    def run_dashboard(self):
        """Run visual dashboard."""
        print("\n📊 Loading dashboard...\n")
        subprocess.run([sys.executable, "dashboard.py"], cwd=self.workspace)
    
    def show_status(self):
        """Show full status document."""
        print("\n📋 Opening PHASE_STATUS.md...\n")
        status_file = self.workspace / "PHASE_STATUS.md"
        if status_file.exists():
            with open(status_file, 'r') as f:
                print(f.read())
        else:
            print("❌ PHASE_STATUS.md not found")
    
    def show_docs(self):
        """Show available documentation."""
        print("\n📚 Available Documentation:\n")
        docs = [
            ("QUICKSTART.md", "5-minute overview + quick commands"),
            ("PHASE_STATUS.md", "Complete 11-phase system status"),
            ("README.md", "Project overview & architecture"),
            ("GETTING_STARTED.md", "Detailed setup instructions"),
            ("docs/PHASES_2_4_MODELS.md", "ML model architectures & theory"),
            ("docs/RESEARCH_FOUNDATION.md", "Phase 5: Future Surface, Momentum, Blast"),
            ("docs/DATASET_SETUP.md", "How to obtain and configure datasets"),
            ("ml/preprocessing/data_loader.py", "Phase 1: Data loading code"),
            ("ml/models/baseline.py", "Phase 2: Baseline models code"),
            ("ml/models/lstm_model.py", "Phase 3: Temporal models code"),
            ("ml/models/gnn_transformer_model.py", "Phase 4: Hybrid model code"),
            ("ml/models/phase5_analysis.py", "Phase 5: Propagation analysis code"),
        ]
        
        for doc, description in docs:
            print(f"  • {doc:<40} - {description}")
    
    def run_all_phases(self):
        """Run complete pipeline."""
        print("\n🚀 Starting complete pipeline (Phases 1-5)...\n")
        print("This will take 30-70 minutes depending on dataset size.\n")
        
        response = input("Continue? (yes/no): ").strip().lower()
        if response == 'yes':
            subprocess.run([sys.executable, "run_all_phases.py"], cwd=self.workspace)
        else:
            print("❌ Cancelled")
    
    def run_phase_1(self):
        """Run Phase 1 only."""
        print("\n🚀 Starting Phase 1 (Data Pipeline)...\n")
        print("This will take 1-40 minutes depending on dataset size.\n")
        
        subprocess.run([sys.executable, "run_all_phases.py", "1"], cwd=self.workspace)
    
    def run_phases_2_4(self):
        """Run Phases 2-4."""
        print("\n🚀 Starting Phases 2-4 (Models)...\n")
        print("Requires Phase 1 data. This will take ~30 minutes.\n")
        
        subprocess.run([sys.executable, "run_all_phases.py", "2,3,4"], cwd=self.workspace)
    
    def run_phase_5(self):
        """Run Phase 5."""
        print("\n🚀 Starting Phase 5 (Propagation Analysis)...\n")
        print("Requires Phase 4 model. This will take ~2 minutes.\n")
        
        subprocess.run([sys.executable, "run_all_phases.py", "5"], cwd=self.workspace)
    
    def view_model_comparison(self):
        """View model comparison results."""
        print("\n📈 Model Performance Comparison:\n")
        
        comparison_file = self.workspace / "models" / "full_comparison.csv"
        if comparison_file.exists():
            try:
                import pandas as pd
                df = pd.read_csv(comparison_file)
                print(df.to_string(index=False))
                print(f"\n✅ Full comparison saved to: {comparison_file}")
            except Exception as e:
                print(f"❌ Error reading comparison: {e}")
        else:
            print("❌ No comparison results yet. Run phases first.")
    
    def view_phase5_results(self):
        """View Phase 5 analysis results."""
        print("\n🔍 Phase 5 Analysis Results:\n")
        
        results_file = self.workspace / "data" / "phase5_results.json"
        if results_file.exists():
            try:
                import json
                with open(results_file, 'r') as f:
                    results = json.load(f)
                
                # Pretty print key metrics
                print("Attack Momentum:")
                momentum = results.get('attack_momentum', {})
                print(f"  Score: {momentum.get('score', 'N/A'):.2f}")
                print(f"  Interpretation: {momentum.get('interpretation', 'N/A')}")
                print(f"  Stage: {momentum.get('stage_name', 'N/A')}")
                
                print("\nFuture Attack Surface:")
                surface = results.get('future_attack_surface', {})
                print(f"  At-risk hosts: {surface.get('total_at_risk', 'N/A')}")
                
                print("\nBlast Radius:")
                blast = results.get('blast_radius', {})
                print(f"  Predicted compromised: {blast.get('predicted_compromised', 'N/A')} hosts")
                print(f"  Severity: {blast.get('blast_severity', 'N/A'):.2f}")
                
                print(f"\n✅ Full results in: {results_file}")
            except Exception as e:
                print(f"❌ Error reading results: {e}")
        else:
            print("❌ No Phase 5 results yet. Run Phase 5 first.")
    
    def view_latest_results(self):
        """View all generated results."""
        print("\n📑 Generated Outputs:\n")
        
        results_dirs = [
            ("Data Outputs", self.workspace / "data"),
            ("Model Artifacts", self.workspace / "models"),
            ("Documentation", self.workspace / "docs"),
        ]
        
        for category, directory in results_dirs:
            print(f"\n{category}:")
            if directory.exists():
                for item in sorted(directory.iterdir())[:10]:  # Show first 10
                    if item.is_file():
                        size = item.stat().st_size / (1024 * 1024)  # MB
                        print(f"  • {item.name} ({size:.1f} MB)")
            else:
                print(f"  (No outputs yet)")
    
    def check_dependencies(self):
        """Check if dependencies are installed."""
        print("\n🔧 Checking dependencies...\n")
        
        required = ['pandas', 'numpy', 'scikit-learn', 'torch', 'matplotlib']
        missing = []
        
        for package in required:
            try:
                __import__(package)
                print(f"  ✅ {package}")
            except ImportError:
                print(f"  ❌ {package} (MISSING)")
                missing.append(package)
        
        if missing:
            print(f"\n⚠️  Missing packages: {', '.join(missing)}")
            print("Run: pip install -r requirements.txt")
        else:
            print("\n✅ All dependencies installed!")
    
    def show_help(self):
        """Show help and troubleshooting."""
        help_text = """
💬 QUICK HELP & TROUBLESHOOTING

1. "I ran a phase but don't see output files"
   → Check the models/ and data/ directories
   → Verify Phase 1 completed (creates data/sequences/)
   → Run: python dashboard.py (to check status)

2. "Phase is running very slowly"
   → Normal for real CIC-IDS-2018 data (~20-40 min for Phase 1)
   → With synthetic data, should complete in 1-2 minutes
   → Monitor with: python dashboard.py

3. "CUDA out of memory error"
   → Models defaulting to CPU if GPU unavailable
   → For large GPU memory, adjust batch size in code

4. "How do I visualize results?"
   → View metrics: models/full_comparison.csv
   → Phase 5 analysis: data/phase5_results.json
   → Run: python dashboard.py

5. "What if I want to run just one model?"
   → Phase 2: python ml/models/baseline.py
   → Phase 3: python ml/models/lstm_model.py
   → Phase 4: python ml/models/gnn_transformer_model.py
   → Phase 5: python ml/models/phase5_analysis.py

6. "Can I use real network data?"
   → Yes! Download CIC-IDS-2018 dataset
   → Place in data/raw/ folder
   → Phase 1 auto-detects and processes
   → Expected time: 20-40 minutes

7. "What are the model metrics?"
   → Precision: % of alerts that are real attacks
   → Recall: % of actual attacks detected
   → F1: Harmonic mean (target >90%)
   → AUC-ROC: Discrimination ability (target >0.95)

8. "Next steps after Phases 1-5?"
   → Phase 6: Counterfactual defense engine
   → Phase 7: Explainability with attention + SHAP
   → Phase 8-11: Backend API, Frontend, Demo, Docker

Need more help? Check docs/:
  • PHASES_2_4_MODELS.md (ML theory)
  • RESEARCH_FOUNDATION.md (Phase 5 formulas)
  • QUICKSTART.md (5-minute overview)
"""
        print(help_text)
    
    def clean_outputs(self):
        """Clean generated artifacts."""
        print("\n⚠️  WARNING: This will delete all trained models and results!\n")
        response = input("Continue? (yes/no): ").strip().lower()
        
        if response == 'yes':
            import shutil
            
            dirs_to_clean = [
                self.workspace / "models",
                self.workspace / "data" / "processed",
                self.workspace / "data" / "sequences",
                self.workspace / "data" / "graphs",
            ]
            
            for d in dirs_to_clean:
                if d.exists():
                    try:
                        shutil.rmtree(d)
                        print(f"  ✅ Cleaned: {d}")
                    except Exception as e:
                        print(f"  ❌ Failed to clean {d}: {e}")
            
            print("\n✅ Cleanup complete!")
        else:
            print("❌ Cancelled")
    
    def run(self):
        """Run interactive menu."""
        while True:
            self.print_banner()
            self.print_menu()
            
            choice = input("\nEnter choice (0-13): ").strip()
            
            if choice == '0':
                print("\n👋 Goodbye!\n")
                sys.exit(0)
            elif choice == '1':
                self.run_dashboard()
            elif choice == '2':
                self.show_status()
            elif choice == '3':
                self.show_docs()
            elif choice == '4':
                self.run_all_phases()
            elif choice == '5':
                self.run_phase_1()
            elif choice == '6':
                self.run_phases_2_4()
            elif choice == '7':
                self.run_phase_5()
            elif choice == '8':
                self.view_model_comparison()
            elif choice == '9':
                self.view_phase5_results()
            elif choice == '10':
                self.view_latest_results()
            elif choice == '11':
                self.check_dependencies()
            elif choice == '12':
                self.clean_outputs()
            elif choice == '13':
                self.show_help()
            else:
                print("\n❌ Invalid choice. Try again.\n")
            
            input("\nPress Enter to continue...")


def main():
    """Main entry point."""
    cli = CyberSeerCLI()
    cli.run()


if __name__ == "__main__":
    main()
