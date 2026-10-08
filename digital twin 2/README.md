# 🛡️ Real-Time Cyberattack Digital Twin & Attack-Progression Predictor

A data-driven, modular cyberattack Digital Twin and attack-progression forecasting system built entirely in Python. Every metric, node color, MITRE ATT&CK technique label, and probability forecast is strictly computed from real windowed flow telemetry passed through feature extraction, ML classifiers, sequence prediction models, and transparent mapping layers.

---

## 🌟 Key Features & Core Principles

1. **No Fake Data / No Hardcoded Life Cycles**: If no attack evidence is present in the ingested window, the UI falls back to `BENIGN/UNKNOWN` state.
2. **Deterministic Digital Twin Graph**: The NetworkX + Plotly host graph updates **strictly** via observed flow connections and model inferences in the active time window.
3. **Transparent MITRE ATT&CK Mapping**: Raw detector labels are mapped explicitly to MITRE ATT&CK techniques with 3 distinct state labels:
   - **`OBSERVED`**: Direct high-confidence evidence in current window ($\text{conf} \ge 0.70$).
   - **`SUSPECTED`**: Partial/weak evidence ($0.35 \le \text{conf} < 0.70$).
   - **`PREDICTED`**: Markov/Sequence model forecasts technique may occur next; hasn't occurred yet.
4. **Decision Explanation ("Why")**: Every prediction is accompanied by tree feature attribution importances highlighting top contributing features (packet rate, byte rate, port diversity, SYN ratio).
5. **Timestamp-Driven Clock**: Simulation advances using source dataset timestamps scaled by a user-controlled replay speed multiplier.
6. **Swappable Model Interface**: Predictors inherit from an abstract `BasePredictor` interface. Easily switch between:
   - **`Baseline Predictor`**: Random Forest Classifier + Markov Chain Transition Model.
   - **`Deep Temporal Predictor`**: PyTorch GRU Recurrent Sequence Model.
7. **Ground-Truth Evaluation & Lead Time**: Tracks prediction accuracy, precision, recall, F1, Top-1 / Top-3 accuracy, and average lead time (seconds between first prediction threshold crossing and actual observation).

---

## 📂 Project Structure

```
digital_twin/
├── app.py                            # Streamlit Dashboard UI (Presentation Layer)
├── config/
│   └── config.yaml                   # Configuration parameters
├── requirements.txt                  # Python dependencies
├── README.md                         # Project documentation
├── data/
│   └── raw/                          # Telemetry datasets (CSV / PCAP)
├── ingestion/
│   ├── csv_reader.py                 # CSV flow reader with timestamp clocking
│   ├── pcap_reader.py                # Native PCAP packet reader via Scapy
│   └── stream.py                     # Unified pluggable ingestion stream abstraction
├── preprocessing/
│   ├── flow_extractor.py             # Flow record parser
│   ├── feature_engineering.py        # Statistical feature extraction (window & host)
│   └── windowing.py                  # Sliding window engine & rolling state buffer
├── mitre/
│   ├── attack_mapping.py             # Transparent detector to MITRE ATT&CK mapper
│   └── techniques.json               # MITRE technique metadata database
├── prediction/
│   ├── base.py                       # Abstract Base Class BasePredictor interface
│   ├── baseline.py                   # Random Forest Classifier + feature attribution
│   ├── transition_model.py           # Markov transition matrix for next-stage forecasting
│   ├── temporal_model.py             # PyTorch GRU sequence model implementation
│   └── inference.py                  # Unified inference pipeline coordinator
├── digital_twin/
│   ├── network_model.py              # HostNode and FlowEdge data structures
│   ├── state_manager.py              # Graph state updater driven by window data
│   └── graph.py                      # NetworkX + Plotly graph renderer
├── evaluation/
│   ├── metrics.py                    # Classification metrics & lead-time calculator
│   └── evaluator.py                  # Ground-truth evaluation engine
├── scripts/
│   └── generate_sample_data.py       # Data generator for Scenarios A, B, and Benign C
└── tests/
    └── test_pipeline.py              # Acceptance criteria unit test suite
```

---

## 🚀 Quick Start Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate Sample Telemetry Datasets
Generate multi-stage attack scenarios (Recon → BruteForce → Exfil, PortScan → DoS → CommandExec, and Benign):
```bash
python scripts/generate_sample_data.py
```

### 3. Run Automated Acceptance Tests
```bash
python -m unittest tests/test_pipeline.py
```

### 4. Launch Streamlit Dashboard
```bash
python -m streamlit run app.py
```
*(Using `python -m streamlit` avoids Windows PowerShell PATH issues when `streamlit` executable script is not in the system environment PATH).*

---

## 🛠️ Acceptance Criteria Verification Summary

| Criteria | Verification Method | Status |
|---|---|---|
| **1. Dataset Swapping Changes Output** | `test_criterion_1_swapping_dataset_changes_behavior` in `tests/test_pipeline.py` | ✅ Verified |
| **2. Benign Fallback (No Fake Attacks)** | `test_criterion_2_benign_traffic_no_attack` in `tests/test_pipeline.py` | ✅ Verified |
| **3. Traceable Inference & "Why"** | `test_criterion_3_traceable_inference` (Feature importances logged per window) | ✅ Verified |
| **4. Timestamp Replay Clock** | `ingestion/csv_reader.py` & `ingestion/pcap_reader.py` using dataset timestamps | ✅ Verified |
| **5. Deterministic Digital Twin Graph** | `digital_twin/state_manager.py` driven strictly by window flows & model output | ✅ Verified |
| **6. Transparent MITRE ATT&CK Mapping** | `mitre/attack_mapping.py` with logged rationale & explicit state tags | ✅ Verified |
| **7. 3 Explicit States (`OBSERVED`/`SUSPECTED`/`PREDICTED`)** | Rendered with distinct color badges in Plotly graph & Streamlit sidebar | ✅ Verified |
| **8. Rolling Window Buffer** | `preprocessing/windowing.py` `RollingStateBuffer` buffering last $N$ window states | ✅ Verified |
| **9. Ground-Truth Scoring & Lead Time** | `evaluation/evaluator.py` & `evaluation/metrics.py` | ✅ Verified |
| **10. Swappable Model Interface** | `BasePredictor` implemented by `BaselinePredictor` and `DeepTemporalPredictor` | ✅ Verified |
