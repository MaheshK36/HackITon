# CyberSeer: Predictive Cyber-Defense Platform

**"Today's tools tell defenders what is happening. This system models what the network is becoming."**

A real, working, deployable platform that forecasts how a cyber attack will propagate through a network and evaluates defensive interventions BEFORE compromise occurs.

## Core Philosophy

- **No hardcoded predictions** — Every number shown comes from actual computation on real data
- **Transparent uncertainty** — All predictions show confidence and evidence
- **Simulated scenarios are labeled** — Never silently mix synthetic with real output
- **Chronological validation** — Time-series splits prevent future leakage
- **Honest limitations** — Clearly documented constraints on detection capabilities

## What CyberSeer Does

```
Network Traffic Stream
         ↓
    [Data Pipeline]
         ↓
    [ML Models]
    - Baseline (LR, RF)
    - Temporal (LSTM/GRU)
    - Hybrid (GNN + Transformer)
         ↓
    [Forecasting]
    - Next 5 time windows (25 minutes)
    - Attack probability per window
    - Predicted attack stage (Reconnaissance → C2 → Exfiltration)
    - Confidence intervals
         ↓
    [Risk Assessment]
    - Future Attack Surface (exposed assets)
    - Attack Momentum (rate of propagation)
    - Blast Radius (affected hosts)
    - Time-to-Critical-Asset (ETA to high-value target)
         ↓
    [Intervention Simulation]
    - "What if we isolate this host?"
    - "What if we block this port?"
    - Compare before/after outcomes
         ↓
    [Real-time Dashboard]
    - Current state + predicted trajectory
    - Recommended interventions
    - Attack path explanation
    - Explainability (what evidence drove the prediction?)
```

## Project Structure

```
cyberseer/
├── data/
│   ├── raw/
│   │   ├── cicids2018/         ← Place CIC-IDS-2018 CSVs here
│   │   └── ctu13/              ← Place CTU-13 .binetflow files here
│   ├── processed/
│   ├── sequences/
│   ├── graphs/
│   └── README.md               ← Exact data placement & preprocessing steps
│
├── ml/
│   ├── preprocessing/
│   │   ├── data_loader.py      ← Load CIC-IDS-2018, CTU-13
│   │   ├── preprocess_dataset.py ← Window flows, compute features
│   │   ├── build_sequences.py  ← Create temporal sequences for LSTM
│   │   ├── build_graphs.py     ← Create network graphs for GNN
│   │   └── validate_dataset.py ← Validate all pipeline stages
│   │
│   ├── models/
│   │   ├── baseline.py         ← Logistic Regression, Random Forest
│   │   ├── lstm_model.py       ← LSTM/GRU temporal model
│   │   └── gnn_transformer.py  ← GNN + Transformer hybrid
│   │
│   ├── training/
│   ├── evaluation/
│   ├── inference/
│   ├── simulation/
│   └── explainability/
│
├── backend/
│   ├── api/
│   │   └── main.py             ← FastAPI server
│   ├── ingestion/              ← Real-time flow ingestion
│   ├── forecasting/            ← Multi-step prediction
│   ├── simulation/             ← Attack simulation engine
│   ├── explainability/         ← Attention + SHAP explanations
│   ├── decision/               ← Recommendation engine
│   └── database/               ← Asset & prediction storage
│
├── frontend/
│   └── (React + Vite + Tailwind)
│
├── configs/
│   ├── dataset.yaml
│   ├── model.yaml
│   ├── training.yaml
│   └── deployment.yaml
│
├── models/                     ← Saved trained model artifacts
│   └── registry.json
│
├── docs/
│   ├── DATASET_SETUP.md        ← How to download & place data
│   ├── RESEARCH_FOUNDATION.md  ← Attack progression, formulas
│   └── LIMITATIONS.md          ← Honest constraints
│
├── docker-compose.yml
├── .env.example
└── README.md                   ← You are here
```

## Phase-by-Phase Development

### PHASE 1 ✓ Dataset Pipeline (COMPLETE)
- ✓ `data_loader.py` — Load CIC-IDS-2018 & CTU-13
- ✓ `preprocess_dataset.py` — Bucket into 5-min windows, compute features
- ✓ `build_sequences.py` — Temporal sequences for LSTM
- ✓ `build_graphs.py` — Network graphs per window
- ✓ `validate_dataset.py` — Full pipeline validation
- ✓ Documentation: `data/README.md`, `docs/DATASET_SETUP.md`

### PHASE 2 Baseline Models (NEXT)
- Logistic Regression + Random Forest on flat flow features
- Chronological train/val/test split (no data leakage)
- Metrics: Precision, Recall, F1, False Positive Rate
- Benchmark to beat in later phases

### PHASE 3 Temporal Model (LSTM/GRU)
- LSTM/GRU over windowed sequences
- Predict: infiltration probability + attack stage
- Compare against Phase 2 baselines

### PHASE 4 Hybrid GNN + Transformer
- GNN (Graph Attention Network) on host graph → graph embedding
- Transformer (causal attention) over sequence of embeddings
- Multi-step rollout: predict 5 windows ahead
- **Key metric: Mean warning lead time** (minutes before compromise)

### PHASE 5 Future Attack Surface + Momentum + Blast Radius
- Per-asset exposure probability, criticality, future threat
- Attack Momentum formula (rate + stage + target criticality)
- Blast Radius (which safe hosts become reachable)
- Time-to-Critical-Asset prediction

### PHASE 6 Multi-Future Simulation + Counterfactual Defense
- N plausible rollouts with probability & path
- Intervention simulation: isolate host / block edge / segment network
- Before/after comparison for each intervention
- Recommend best-tradeoff action (always labeled SIMULATED)

### PHASE 7 Explainability
- Transformer attention weights + SHAP on GNN/flow features
- Top contributing ports/flags/edges per prediction
- No explanation references anything model didn't actually use

### PHASE 8 Backend API (FastAPI)
- Endpoints: POST /ingest, POST /forecast, POST /simulate, POST /counterfactual, GET /network-state, GET /attack-paths, GET /risk, etc.
- Real database (SQLite for hackathon, Postgres production path)
- Meaningful errors (never silent failures)

### PHASE 9 Frontend Dashboard (React + Vite + Tailwind)
- White background, high-contrast palette
- Sharp, SOC-console aesthetic (no gradients, no glassmorphism)
- Every predicted/simulated number tagged (OBSERVED / PREDICTED / SIMULATED)
- Pages: Command Center, Attack Trajectory, Multi-Future Simulation, Counterfactual Defense, Explainability, Dataset Status

### PHASE 10 Jury Demo Mode
- 3-5 minute guided flow on real test data
- Normal traffic → deviation → forecast → interventions → success
- Final screen: "We did not wait for the incident. We intervened on the predicted trajectory."
- Separate SYNTHETIC SCENARIO mode for capabilities demo

### PHASE 11 Docker + README
- Dockerfile, docker-compose.yml, .env.example
- Complete setup instructions (Windows, Linux, Mac)
- Dataset download & placement steps
- Preprocessing, training, evaluation, frontend/backend run commands
- Troubleshooting & honest limitations section

## Quick Start

### Prerequisites
- Python 3.9+
- pip
- ~3 GB disk space (for data + processed artifacts)

### Installation

```bash
# Clone repo
git clone <repo-url>
cd cyberseer

# Create venv
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Dataset Setup

1. **Download raw data**
   - CIC-IDS-2018: https://www.unb.ca/cic/datasets/ids-2018.html
   - CTU-13: https://www.stratosphereips.org/datasets-ctu13

2. **Place files**
   ```
   data/raw/cicids2018/ ← 16 CSV files
   data/raw/ctu13/      ← .binetflow files
   ```

3. **See** `docs/DATASET_SETUP.md` for exact steps

### Run Data Pipeline

```bash
# Load raw data
python ml/preprocessing/data_loader.py

# Preprocess (5-min windows, feature extraction)
python ml/preprocessing/preprocess_dataset.py

# Build sequences (for LSTM)
python ml/preprocessing/build_sequences.py

# Build graphs (for GNN)
python ml/preprocessing/build_graphs.py

# Validate all stages
python ml/preprocessing/validate_dataset.py
```

**Expected output**: `data/validation_report.json` with PASS status

See `docs/DATASET_SETUP.md` for complete walkthrough with expected outputs and troubleshooting.

## Data Characteristics

### CIC-IDS-2018
- **80 million flows**, December 1-31, 2018
- **15 attack types** (DoS, DDoS, Port Scan, Bot, Web Attack, Infiltration, etc.)
- **79 features per flow** (packets, bytes, IAT, TCP flags, duration, ratios, etc.)
- **Class distribution**: ~80% Benign, 20% various attacks

### CTU-13
- **2 million flows**, multiple dates (2010-2011)
- **Botnet traffic** (C&C communication)
- **15 basic features** per flow
- **Class distribution**: ~80% Benign, 20% Botnet

## Key Design Decisions

1. **No random shuffling of time-series data** — Chronological splits only, prevents future leakage
2. **Windowing before modeling** — Models operate on aggregate behavior, not individual flows
3. **Transparent prediction pipeline** — Each stage output is saved and validated
4. **Real data or explicitly synthetic** — No silent mocking; if a capability is simulated, the UI says so
5. **Phase gate**: Don't advance until current phase shows real output on actual data

## Architecture Diagram (Text Form)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React + Vite)                   │
│  Command Center | Attack Timeline | Simulation | Interventions   │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP/WebSocket
┌─────────────────────────▼───────────────────────────────────────┐
│                    Backend (FastAPI)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │   API Routes │  │  Forecasting │  │  Simulation Engine  │   │
│  │ /ingest      │  │  + Explainer │  │  + Counterfactual   │   │
│  └──────────────┘  └──────────────┘  └─────────────────────┘   │
│                          │                                        │
│  ┌──────────────────────▼────────────────────────────────────┐  │
│  │           ML Models (PyTorch)                              │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌────────────────┐    │  │
│  │  │  Baseline   │  │   LSTM/GRU  │  │ GNN + Transformer│  │  │
│  │  │  (LR, RF)   │  │             │  │                │    │  │
│  │  └─────────────┘  └─────────────┘  └────────────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│              Data & Database (SQLite/Postgres)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐      │
│  │    Assets    │  │  Predictions │  │  Simulations     │      │
│  │  (Hosts)     │  │  + Evidence   │  │  + Interventions │      │
│  └──────────────┘  └──────────────┘  └──────────────────┘      │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│              Offline/Real-time Flow Ingestion                    │
│  - Network TAP, Zeek, or historical PCAP files                  │
│  - Flows → 5-min windows → Feature vectors                      │
│  - Feed to forecasting pipeline continuously                    │
└─────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, Vite, Tailwind CSS |
| **Backend** | FastAPI, Uvicorn |
| **ML** | PyTorch, PyTorch Geometric, scikit-learn |
| **Data** | pandas, NumPy, SciPy |
| **Database** | SQLite (dev), PostgreSQL (prod) |
| **Deployment** | Docker, docker-compose |
| **Monitoring** | Prometheus, Grafana (future) |

## Performance Targets

- **Real-time latency**: <500ms from flow arrival to prediction
- **Warning lead time**: Mean 15+ minutes before compromise (Phase 4 target)
- **False positive rate**: <2% on benign traffic
- **Detection rate**: >90% on known attack patterns (baseline)
- **Scalability**: Handle 10k+ flows/second ingestion rate

## Limitations (Honest, Documented)

- **Encrypted traffic**: Model sees only metadata, not payload
- **Concept drift**: Attack techniques evolve; retraining required
- **Zero-day attacks**: Any truly novel attack may not be detected
- **False positives**: Benign anomalies (system backups, scans) can trigger alerts
- **Exact timing**: Predictions give ranges/probabilities, not precise timestamps
- **Limited datasets**: CIC-IDS-2018 & CTU-13 may not represent all real-world networks

See `docs/LIMITATIONS.md` for full details.

## Deployment

### Local / Hackathon

```bash
# Run backend
python backend/api/main.py

# In another terminal, run frontend
cd frontend
npm install
npm run dev
```

### Docker

```bash
docker-compose up
# Access at http://localhost:3000
```

### Production (Postgres)

```bash
# Set environment
export DATABASE_URL=postgresql://user:pass@host:5432/cyberseer
export MODEL_PATH=/models/gnn_transformer.pth

# Run backend
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

## Jury Demo Flow (3-5 minutes)

1. **System State** — Show current network traffic (benign, normal)
2. **Anomaly Detection** — Deviation appears (bot starting C&C communication)
3. **Forecast** — Model predicts attack progression (next 25 minutes)
4. **Future Attack Surface** — Highlighted at-risk assets
5. **Attack Momentum** — Graphic showing rate of propagation
6. **Blast Radius** — Which hosts will be compromised if no action taken
7. **Counterfactual Simulation** — "Isolate this host" → Run simulation live
8. **Impact** — Probability curve visibly drops, time-to-critical-asset extended
9. **Explanation** — Show why model flagged this (top ports, flags, edges)
10. **Conclusion** — "We did not wait for the incident. We intervened on the predicted trajectory."

**Also available**: Synthetic scenario demonstrating capabilities on fictional enterprise topology (Internet → Web → App → DC → Database)

## References

- CIC-IDS-2018: [Dataset Paper](https://www.unb.ca/cic/datasets/ids-2018.html)
- CTU-13: [Botnet Dataset](https://www.stratosphereips.org/datasets-ctu13)
- Graph Attention Networks: [Paper](https://arxiv.org/abs/1710.10903)
- Transformer for Anomaly Detection: [Survey](https://arxiv.org/abs/2106.02818)
- SHAP Explainability: [Paper](https://arxiv.org/abs/1705.07874)

## Contributing

Work in phases. After each phase:
1. Show actual output on real or synthetic data
2. Document what passed validation
3. Do not advance to next phase until current phase runs cleanly

## License

[To be determined]

## Contact

Built for SIH (Smart India Hackathon) 2026 — Round 2  
Product ID: SIH26153

---

**"We modeled what the network is becoming. Now we can defend it before it's compromised."**
