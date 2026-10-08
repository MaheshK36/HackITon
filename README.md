# SIH-MAX: Predictive Cyber-Defence Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-2.0.0-009688.svg)](https://fastapi.tiangolo.com)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.4%2B-orange.svg)](https://scikit-learn.org)
[![React](https://img.shields.io/badge/React-18.0%2B-61DAFB.svg)](https://reactjs.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An integrated, end-to-end predictive cybersecurity platform combining **canonical network telemetry ingestion**, **genuine machine learning threat classification**, **autoregressive attack stage forecasting**, **telemetry-derived Digital Twin graph state modeling**, and a **cryptographic tamper-evident audit ledger**.

---

## 1. System Architecture

```
                                  +---------------------------------------------------------+
                                  |                 Repository Root CLI / API               |
                                  |                        (main.py)                        |
                                  +---------------------------------------------------------+
                                                               |
                     +-----------------------------------------+-----------------------------------------+
                     |                                         |                                         |
                     v                                         v                                         v
         +-----------------------+                 +-----------------------+                 +-----------------------+
         |   Telemetry Stream    |                 |    Unified Engine     |                 |  Tamper-Evident Audit |
         |   (Replay / Ingest)   |                 |    (FastAPI Core)     |                 |  (Local Hash-Chain)   |
         +-----------------------+                 +-----------------------+                 +-----------------------+
         | - Scenario A (Recon)  |                 | - Canonical Contracts |                 | - SHA-256 linked log  |
         | - Scenario B (DoS)    |                 | - Feature Extraction  |                 | - Verification API    |
         | - Scenario C (Benign) |                 | - State Management    |                 | - Mantle Bridge (opt) |
         | - Live API Ingest     |                 | - Shared Digital Twin |                 +-----------------------+
         +-----------------------+                 +-----------------------+
                     |                                         |
                     +--------------------+--------------------+
                                          |
                                          v
                               +---------------------+
                               |   Inference Engine  |
                               +---------------------+
                               | - Trained RF Model  |
                               | - Markov Transition |
                               | - MITRE ATT&CK Map  |
                               | - Top-5 Attribution |
                               | - Heuristic Fallback|
                               +---------------------+
                                          |
                                          v
                               +---------------------+
                               |  Unified Frontend   |
                               |  (React Dashboard)  |
                               +---------------------+
                               | - Network Topology  |
                               | - Attack Forecast   |
                               | - Audit Trail View  |
                               | - Replay Controls   |
                               +---------------------+
```

---

## 2. Honest Technical Commitments

To uphold technical integrity and scientific credibility:
1. **Never Hardcoded or Fabricated ML**: Predictions come exclusively from a fitted `RandomForestClassifier` and empirical `MarkovTransitionModel`. If no trained checkpoint is found, the platform transparently reports `HEURISTIC_FALLBACK` with explicit reasoning.
2. **Honest Evaluation Metrics**: Metrics (Accuracy: **78.3%**, Macro F1: **66.7%**) are measured strictly on held-out test splits from standardized flow scenarios.
3. **Transparent Operational Modes**: Every ingested event and API response is explicitly tagged as `DEMO`, `REPLAY`, or `LIVE`.
4. **Honest Cryptographic Audit**: The audit trail is documented as a **Local SHA-256 Tamper-Evident Ledger**. It does not pretend to be an on-chain transaction unless the optional Mantle smart contract bridge is explicitly connected and funded.

---

## 3. Quickstart Guide (Ubuntu / Linux)

### Prerequisites
- Ubuntu 20.04 / 22.04 / 24.04 / 26.04 LTS
- Python 3.10 - 3.12 (with `python3-venv` or `uv`)
- Node.js 18+ & npm (required to build the React Command Center frontend)

### 1. Environment Setup

Clone the repository and set up a Python virtual environment:

```bash
# Recommended: Create virtual environment using python3 venv or uv
python3 -m venv .venv
source .venv/bin/activate

# Or using uv (fast installer):
# uv venv --python 3.12 .venv && source .venv/bin/activate
```

### 2. Install Dependencies

Install the unified platform requirements:

```bash
# On systems without dedicated GPU, install CPU PyTorch first for fast installation:
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Install platform dependencies
pip install -r requirements.txt
```

### 3. Build the Frontend Dashboard

Build the React Cyber Defense Command Center static bundle:

```bash
cd cyber_dashboard-main/unified_cybersecurity_system/frontend
npm install
npm run build
cd ../../..
```

### 4. Configure Environment (Optional)

Create local configuration file from template:

```bash
cp .env.example .env
```

### 5. Train the Baseline ML Model

Trains the Random Forest classifier and Markov transition model on multi-stage attack scenarios, generates held-out evaluation metrics, and saves the artifact to `data/models/baseline_rf.pkl`:

```bash
python main.py train
```

### 6. Run the Verification Test Suite

Executes the automated end-to-end test suite verifying normalization, model inference, digital twin state updates, audit hash chaining, replay pipelines, and API endpoints:

```bash
python main.py test
```

### 7. Check Platform Status

Inspects loaded models, evaluation scores, digital twin status, and scenario availability:

```bash
python main.py status
```

### 8. Stream Scenario Replay

Streams attack scenarios through the canonical ingestion pipeline to observe dynamic node infection states in the Digital Twin:

```bash
python main.py replay --scenario scenario_a --events 25
```

### 9. Launch the Command Center

Starts the unified FastAPI backend server and serves the React Cyber Defense Command Center:

```bash
python main.py serve --port 8000
```

- **Command Center Dashboard**: [http://localhost:8000](http://localhost:8000)
- **Interactive REST Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---


## 4. MITRE ATT&CK Coverage

The ML Inference Engine maps detected flow anomalies directly to MITRE ATT&CK techniques:

| Technique ID | Name | Tactic | Key Flow Indicators |
|---|---|---|---|
| **T1046** | Network Service Discovery | Discovery | High unique destination ports, elevated SYN ratio, low packet count |
| **T1110** | Brute Force Authentication | Credential Access | Repetitive administrative port hits (22, 3389), moderate duration |
| **T1498** | Network Denial of Service | Impact | Excessive packet rate, small flow duration, high SYN count |
| **T1059** | Command and Scripting Interpreter | Execution | Interactive byte exchanges on atypical ports, long duration |
| **T1041** | Exfiltration Over C2 Channel | Exfiltration | Massive outbound byte rate, high packets per flow to external IP |
| **T0000** | Benign Network Activity | Normal Operations | Typical web/DNS traffic patterns, low port dispersion |

---

## 5. REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health, mode, and loaded module status |
| `GET` | `/api/v1/platform/snapshot` | Full state snapshot (nodes, edges, recent events, metrics) |
| `GET` | `/api/v1/model/info` | Registered ML model version, metrics, and feature names |
| `POST` | `/api/v1/flows/ingest` | Canonical flow event ingestion endpoint |
| `GET` | `/api/v1/twin/state` | Digital Twin graph nodes, edges, and infection stages |
| `POST` | `/api/v1/forecast/propagation` | Topology risk diffusion attack propagation forecast |
| `GET` | `/api/v1/replay/scenarios` | List available attack telemetry scenarios for replay |
| `POST` | `/api/v1/replay/start` | Trigger telemetry replay through the live platform |
| `GET` | `/api/audit-logs` | Cryptographic tamper-evident audit ledger entries |

---

## 6. Repository Structure

```
SIH-MAX/
├── main.py                                      # Root CLI & single entrypoint (serve, train, test, replay)
├── requirements.txt                             # Unified platform dependencies
├── AUDIT_REPORT.md                              # Comprehensive repository architectural audit
├── FINAL_AUDIT_REPORT.md                        # Productization milestones and findings
├── README.md                                    # Platform documentation
├── data/
│   ├── models/baseline_rf.pkl                   # Trained Random Forest & Markov transition model artifact
│   └── raw/                                     # Standardized replay scenarios (A, B, C)
├── scripts/
│   └── train_baseline.py                        # Model training and held-out evaluation script
├── cyber_dashboard-main/
│   └── unified_cybersecurity_system/            # Core unified platform application
│       ├── backend/                             # FastAPI server, schemas, normalization, services
│       │   ├── server.py                        # REST API routing & static frontend hosting
│       │   ├── schemas.py                       # Pydantic telemetry contracts
│       │   └── services/
│       │       ├── platform.py                  # Shared telemetry-to-decision service
│       │       ├── ml_engine.py                 # Scikit-learn RF + Markov inference & attribution
│       │       └── replay_service.py            # Telemetry stream replayer
│       ├── blockchain/                          # Local SHA-256 tamper-evident ledger
│       ├── digital_twin/                        # Shared graph state & node threat tracking
│       ├── frontend/                            # React Command Center dashboard
│       └── tests/                               # Comprehensive unit and integration test suite
├── digital twin 2/                              # Replay and baseline research artifacts
├── network model/                               # CIC-IDS / CTU ML research artifacts
└── BLOCKCHAIN--main/                            # Mantle smart contract audit bridge (optional)
```
# HackITon26
# HackITon26
# HackITon26
# HackITon26
# HackITon26
