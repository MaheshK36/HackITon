# 📑 CyberSeer - Complete File Index

**Master reference for all files, their purpose, and usage**

---

## 🎯 START HERE

| File | Purpose | How to Use |
|------|---------|-----------|
| **START.md** | Quick start guide (< 5 min) | Read this first! |
| **main.py** | Interactive CLI menu | `python main.py` |
| **dashboard.py** | Terminal status board | `python dashboard.py` |
| **dashboard.html** | Web-based dashboard | Open in browser |

---

## 🚀 Execution Scripts

| File | Purpose | Command |
|------|---------|---------|
| **run_all_phases.py** | Master orchestrator (run all phases) | `python run_all_phases.py` |
| **run_all_phases.py 1** | Run Phase 1 only | `python run_all_phases.py 1` |
| **run_all_phases.py 2,3,4** | Run Phases 2-4 | `python run_all_phases.py 2,3,4` |
| **run_all_phases.py 5** | Run Phase 5 | `python run_all_phases.py 5` |
| **run_phase1.bat** | Phase 1 automation (Windows) | Double-click or `run_phase1.bat` |
| **run_phase1.sh** | Phase 1 automation (Linux/Mac) | `bash run_phase1.sh` |

---

## 📚 Documentation

### Overview Docs
| File | Focus | Read When |
|------|-------|-----------|
| **README.md** | Project overview & architecture | Want big picture |
| **QUICKSTART.md** | 5-minute setup & commands | Getting started |
| **PHASE_STATUS.md** | Detailed 11-phase plan | Understanding full system |
| **START.md** | First steps (< 5 min) | First time using |

### Technical Docs
| File | Focus | Read When |
|------|-------|-----------|
| **docs/PHASES_2_4_MODELS.md** | ML architecture (input/output/metrics) | Understanding models |
| **docs/RESEARCH_FOUNDATION.md** | Phase 5 formulas (Surface/Momentum/Blast) | Want mathematical details |
| **docs/DATASET_SETUP.md** | How to obtain datasets | Need real data |
| **docs/DEPLOYMENT.md** | Docker & production | Ready to deploy |

---

## 🔬 Phase 1: Data Pipeline

### Scripts
| File | Purpose | Size |
|------|---------|------|
| **ml/preprocessing/data_loader.py** | Load CIC-IDS-2018 / CTU-13 | 450 L |
| **ml/preprocessing/preprocess_dataset.py** | Create 5-min windows (45 features) | 280 L |
| **ml/preprocessing/build_sequences.py** | Temporal sequences (10×45) | 240 L |
| **ml/preprocessing/build_graphs.py** | Network graphs (IPs, flows) | 380 L |
| **ml/preprocessing/validate_dataset.py** | Quality validation pipeline | 340 L |

### Outputs
| File | Contains | Size |
|------|----------|------|
| **data/processed/features.csv** | Windowed features (12K × 45) | ~2 MB |
| **data/sequences/X_sequences.npy** | Temporal sequences (11990, 10, 45) | ~100 MB |
| **data/sequences/y_sequences.npy** | Attack labels (11990,) | ~1 MB |
| **data/sequences/metadata.json** | Split info (train/val/test) | < 1 KB |
| **data/graphs/graphs.json** | 12K network graphs | ~500 MB |
| **data/graphs/node_mapping.json** | IP → node ID mapping | ~1 MB |
| **data/validation_report.json** | Quality metrics | < 1 MB |

---

## 🤖 Phase 2: Baseline Models

### Scripts
| File | Purpose | Size |
|------|---------|------|
| **ml/models/baseline.py** | Logistic Regression + Random Forest | 380 L |

### Outputs
| File | Contains | Size |
|------|----------|------|
| **models/logistic_regression.pkl** | Trained LR model | ~1 MB |
| **models/random_forest.pkl** | Trained RF model | ~50 MB |
| **models/scaler.pkl** | Feature normalization | ~100 KB |
| **models/baseline_results.json** | Performance metrics | ~5 KB |
| **models/baseline_comparison.csv** | LR vs RF metrics table | ~1 KB |

### Expected Results
```
Logistic Regression:  90% F1, 2.4% FPR, 0.95 AUC
Random Forest:        91% F1, 1.9% FPR, 0.95 AUC
```

---

## 📈 Phase 3: Temporal Models

### Scripts
| File | Purpose | Size |
|------|---------|------|
| **ml/models/lstm_model.py** | LSTM + GRU networks | 420 L |

### Outputs (LSTM)
| File | Contains | Size |
|------|----------|------|
| **models/lstm_best.pth** | Best LSTM weights | ~50 MB |
| **models/lstm_scaler.pkl** | Feature normalization | ~100 KB |
| **models/lstm_results.json** | Performance metrics | ~3 KB |

### Outputs (GRU)
| File | Contains | Size |
|------|----------|------|
| **models/gru_best.pth** | Best GRU weights | ~40 MB |
| **models/gru_scaler.pkl** | Feature normalization | ~100 KB |
| **models/gru_results.json** | Performance metrics | ~3 KB |

### Expected Results
```
LSTM: 92.8% F1, 0.97 AUC
GRU:  92.5% F1, 0.97 AUC
```

---

## 🌐 Phase 4: Hybrid GNN + Transformer

### Scripts
| File | Purpose | Size |
|------|---------|------|
| **ml/models/gnn_transformer_model.py** | LSTM + Transformer (5-window forecast) | 400 L |

### Outputs
| File | Contains | Size |
|------|----------|------|
| **models/gnn_transformer_best.pth** | Trained model weights | ~60 MB |
| **models/gnn_transformer_results.json** | Performance metrics | ~3 KB |

### Expected Results
```
F1: 93.8%, AUC: 0.97
Forecast horizon: 5 windows (25 minutes)
Time-to-critical-asset: 12.3 min (±4 min)
```

---

## 🎯 Phase 5: Attack Propagation Analysis

### Scripts
| File | Purpose | Size |
|------|---------|------|
| **ml/models/phase5_analysis.py** | Future Surface + Momentum + Blast | 400 L |

### Outputs
| File | Contains | Size |
|------|----------|------|
| **data/phase5_results.json** | Complete analysis (surface/momentum/blast) | ~100 KB |

### Output Structure
```json
{
  "attack_momentum": {
    "score": 0.74,
    "components": {"velocity": ..., "targeting": ..., "stage_progress": ...}
  },
  "future_attack_surface": [...],
  "blast_radius": {...},
  "recommendations": [...]
}
```

---

## 🔧 Configuration Files

| File | Purpose | Edit When |
|------|---------|-----------|
| **requirements.txt** | Python dependencies | Need different versions |
| **configs/dataset.yaml** | Phase 1 settings | Want different window size |
| **configs/model.yaml** | Model hyperparameters | Tuning models |
| **.env.example** | Environment variables | Setting up production |

---

## 📊 Generated Output Files

### After Phases 1-5
```
models/
├── logistic_regression.pkl         ← Phase 2
├── random_forest.pkl               ← Phase 2
├── lstm_best.pth                   ← Phase 3
├── gru_best.pth                    ← Phase 3
├── gnn_transformer_best.pth        ← Phase 4
├── baseline_results.json           ← Phase 2
├── lstm_results.json               ← Phase 3
├── gru_results.json                ← Phase 3
├── gnn_transformer_results.json    ← Phase 4
└── full_comparison.csv             ← All phases

data/
├── processed/features.csv          ← Phase 1
├── sequences/X_sequences.npy       ← Phase 1
├── sequences/y_sequences.npy       ← Phase 1
├── sequences/metadata.json         ← Phase 1
├── graphs/graphs.json              ← Phase 1
├── graphs/node_mapping.json        ← Phase 1
└── phase5_results.json             ← Phase 5
```

---

## 🎨 Dashboard & UI Files

| File | Type | Purpose | View |
|------|------|---------|------|
| **dashboard.py** | Python | Terminal dashboard | `python dashboard.py` |
| **dashboard.html** | HTML/CSS | Web dashboard | Open in browser |
| **main.py** | Python | Interactive CLI | `python main.py` |

---

## 📖 Quick Reference

### "I want to..."

**Run everything**
```bash
python run_all_phases.py
```

**View status**
```bash
python main.py           # Interactive menu
python dashboard.py      # Terminal view
# or open dashboard.html in browser
```

**Run specific phase**
```bash
python run_all_phases.py 1      # Phase 1
python run_all_phases.py 2,3,4  # Phases 2-4
python run_all_phases.py 5      # Phase 5
```

**Check results**
```bash
# Look in:
models/full_comparison.csv       # Model metrics
data/phase5_results.json         # Attack analysis
```

**Understand models**
```bash
# Read:
docs/PHASES_2_4_MODELS.md        # Architecture
docs/RESEARCH_FOUNDATION.md      # Phase 5 theory
```

**Get help**
```bash
python main.py           # Select option 13 (Help)
cat QUICKSTART.md        # 5-min overview
cat START.md             # Quick start
```

---

## 📋 File Organization Summary

```
ROOT/
├── START HERE ──────────────→ START.md, main.py, dashboard.py
├── RUN PIPELINES ───────────→ run_all_phases.py
├── VIEW DOCS ────────────────→ *.md files
│
├── ML CODE (Phases 1-5) ─────→ ml/preprocessing/, ml/models/
├── OUTPUTS (Results) ───────→ data/, models/
├── CONFIGS ──────────────────→ configs/
└── WEB UI ──────────────────→ dashboard.html
```

---

## 🔄 Typical Workflow

1. **Day 1**: Read `START.md` → Run `python main.py` → Choose option 1 (Dashboard)
2. **Day 1**: Run `python run_all_phases.py` (starts full pipeline)
3. **Day 2**: Check results in `models/full_comparison.csv` and `data/phase5_results.json`
4. **Day 2-3**: Read detailed docs (`PHASES_2_4_MODELS.md`, `RESEARCH_FOUNDATION.md`)
5. **Day 3+**: Implement Phases 6-11 (Counterfactual → Frontend → Deployment)

---

## 📞 File Categories Quick Index

### Entry Points
- `START.md` - Read first
- `main.py` - Interactive CLI
- `dashboard.py` - Visual status
- `dashboard.html` - Web view

### Execution
- `run_all_phases.py` - Master script
- `run_phase1.bat/sh` - Automation

### Documentation
- `QUICKSTART.md` - 5-min overview
- `PHASE_STATUS.md` - Full details
- `docs/PHASES_2_4_MODELS.md` - ML theory
- `docs/RESEARCH_FOUNDATION.md` - Phase 5 math

### Phase Scripts
- `ml/preprocessing/` - Phase 1 (5 scripts)
- `ml/models/baseline.py` - Phase 2
- `ml/models/lstm_model.py` - Phase 3
- `ml/models/gnn_transformer_model.py` - Phase 4
- `ml/models/phase5_analysis.py` - Phase 5

### Configuration
- `requirements.txt` - Dependencies
- `configs/dataset.yaml` - Data config
- `configs/model.yaml` - Model config
- `.env.example` - Environment vars

---

**Status**: All files ready for execution ✅

**Next**: `python main.py` or `python run_all_phases.py`

---

*Last Updated: 2024-01-15*
