# 🛡️ Unified AI Cybersecurity Defense Platform

A single, fully-integrated cybersecurity command center uniting **Blockchain Access Audit Trails**, **PyTorch Network Digital Twin Rollouts**, **CyberSeer GNN Attack Propagation**, and **Live Flow Telemetry Ingestion**.

---

## 📁 Unified Directory Structure

```
unified_cybersecurity_system/
├── backend/                  # FastAPI REST API Backend
│   ├── adapters/             # Schema Normalization & Adapter Layer
│   │   └── normalization.py  # 42-feature CIC-IDS-2018 vector adapter
│   ├── api/                  # Modular REST API Routers
│   │   ├── audit.py          # /api/audit-logs, /api/anomalies, /api/verify-hash
│   │   ├── twin.py           # /api/v1/twin/state, /api/v1/twin/rollout, /api/v1/twin/fidelity
│   │   ├── forecast.py       # /api/v1/forecast/propagation
│   │   └── live_ingest.py    # /api/v1/flows/ingest
│   └── server.py             # FastAPI App & Static React Server Mounting
├── blockchain/               # Immutable Audit Ledger & Multi-Confirm Gate
│   ├── audit_agent.py        # SHA-256 Hashing & Anomaly Gate (Z-Score + IsoForest + Rules)
│   └── CyberAuditLog.sol     # Ethereum Solidity Smart Contract
├── digital_twin/             # Digital Twin Simulation & Rollout Engine
│   ├── state.py              # Topology Network Graph State (Plotly / SVG)
│   ├── twin_engine.py        # Free-running autoregressive rollout simulator
│   ├── narration.py          # Natural language trajectory analyst narrator
│   └── validation.py         # Multi-step horizon drift & RMSE fidelity benchmark
├── models/                   # Neural Network Models
│   ├── attack_world_model.py # Multi-task PyTorch LSTM/GRU Attack World Model
│   └── graph_encoder.py      # PyTorch Geometric 2-layer Graph Attention Network (GAT)
├── ingestion/                # Telemetry Stream Ingestion
│   └── stream.py             # CSV / PCAP Telemetry Stream Reader
├── preprocessing/            # Feature Extraction & Windowing
│   └── windowing.py          # WindowEngine for temporal flow aggregation
├── frontend/                 # React 18 + Vite + Tailwind CSS UI
│   ├── src/
│   │   ├── components/       # LiveIngestTab, DigitalTwinTab, CyberSeerTab, AuditTab, AnalyticsTab
│   │   ├── App.jsx           # Main Command Center Layout
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.ts
├── tests/                    # End-to-End Test Suite
│   └── test_end_to_end.py    # 6-step integration test suite
├── main.py                   # Single-Command Application Launcher
├── requirements.txt          # Unified Python Dependencies
└── README.md                 # Project Documentation
```

---

## 🔀 What Was Merged & Integration Mapping

1. **Digital Twin Integration**:
   - Merged PyTorch `WorldModel` single-step rollout cell and trajectory narrator (`digital twin`) with windowed telemetry flow ingestion and MITRE ATT&CK technique mapping (`digital twin 2`).
2. **Models Integration**:
   - Merged sequence prediction (`attack model`) with GNN graph attention propagation modeling (`network model`).
3. **Blockchain Integration**:
   - Integrated SHA-256 cryptographic access event hashing and 3-algorithm Multi-Confirm Anomaly Detection Gate (`BLOCKCHAIN--main`).
4. **Schema Adapter**:
   - Implemented `backend/adapters/normalization.py` to translate arbitrary flow dict inputs into standard 42-feature CIC-IDS-2018 model inputs.

---

## 🚀 How to Run End-to-End

### 1. Requirements
- **Python**: 3.10+
- **Node.js**: 18+

### 2. Launch Server
```bash
# Navigate to the unified system folder
cd cyber_dashboard-main/unified_cybersecurity_system

# Launch backend and serve frontend
python main.py
```

### 3. Open Dashboards & APIs
- **Command Center Dashboard**: [http://localhost:5173](http://localhost:5173) (or `http://localhost:8000`)
- **FastAPI OpenAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Blockchain Audit Dashboard**: [http://localhost:5174](http://localhost:5174)
- **Digital Twin Simulator**: [http://localhost:8501](http://localhost:8501)
- **CyberSeer Static Dashboard**: [http://localhost:8080/dashboard.html](http://localhost:8080/dashboard.html)

---

## 🧪 Running Automated Tests

To execute the end-to-end verification test suite:
```bash
python tests/test_end_to_end.py
```
Outputs: `Ran 6 tests in 0.093s - OK`.
