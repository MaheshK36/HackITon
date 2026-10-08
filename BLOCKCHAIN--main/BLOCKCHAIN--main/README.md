# Software Platform Login/Logout Audit & Anomaly Detection System

> **Autonomous software platform access monitoring pipeline delivering real-time login/logout event capture, SHA-256 cryptographic audit logging on-chain, and multi-confirm behavioral anomaly detection.**

---

## Overview & Scope

The **Software Platform Login/Logout Audit & Anomaly Detection System** is a streamlined 3-stage agent pipeline designed to secure platform access controls and maintain an immutable, tamper-evident audit trail of user sessions.

### Core Capabilities:
1. **Log Capture (`EventCollectorAgent`)** — Ingests user access events (login, logout, failed login attempts) including User ID, Session ID, Timestamp, IP Address, Location, and Device User-Agent.
2. **Multi-Confirm Anomaly Detection (`AnomalyAgent`)** — Evaluates user access behavior using **Z-Score Frequency Spikes**, **Isolation Forest Multivariate Outlier Detection**, and **Rule-Based Heuristics**. Requires **≥ 2 detection algorithms to agree** before flagging a high-confidence access security anomaly (`confidence ≥ 0.80`).
3. **On-Chain Audit Trail (`AuditAgent` + `AccessAuditLog.sol`)** — Computes canonical SHA-256 hashes over access records and records them on-chain to `AccessAuditLog.sol`, creating a tamper-evident audit record verifiable by external auditors.

---

## Architecture

```text
Software Platform User Access Events
  │  User ID · Session ID · Event Type (Login/Logout) · Timestamp · IP · Device
  ▼
EventCollectorAgent (Stage 1)
  │  Ingests live platform API access events & buffers active session states
  ▼
AnomalyAgent (Stage 2)
  │  Multi-Confirm Anomaly Gate (≥ 2 algorithms must confirm):
  │    - Z-Score Frequency Spikes (failed login bursts, volume spikes)
  │    - Isolation Forest (multivariate access behavior outliers)
  │    - Rule-based Heuristics (suspicious geo-shifts, unrecognized devices)
  ▼
AuditAgent & AccessAuditLog.sol (Stage 3)
  │  Computes SHA-256 over canonical access record: {event_id, user_id, event_type, timestamp}
  │  Pushes log hash & anomaly status on-chain to AccessAuditLog.sol
  ▼
React Dashboard & REST API Server
  │  Audit Log View (Filterable access event stream & SHA-256 verifiability)
  │  Analytics View (Flagged user session incidents & detection engine stats)
  │  REST API (Event ingestion, log search, anomaly alerts)
```

---

## Smart Contract

`contracts/src/AccessAuditLog.sol` is an OpenZeppelin-backed Solidity contract deployed on-chain to store immutable software access logs:

- `recordLog(bytes32 logHash, string userId, string eventType, uint8 anomalyScore, bool isAnomaly)`
- `verifyLogHash(bytes32 logHash)` — returns cryptographic verification status for any access event.
- `getPublicLogs(uint256 offset, uint256 limit)` — paginated access log feed.

---

## Quickstart

### 1. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 2. Run Single Audit Cycle (Demo)
```bash
python main.py --cycles 1
```

### 3. Run Continuous Real-Time Access Monitoring
```bash
python main.py --loop
```

### 4. Start REST API Server & Dashboard
```bash
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```
Open `http://localhost:8000` in your browser to view the Audit Log and Anomaly Analytics dashboard.

---

## REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/events` | `POST` | Ingest a new login, logout, or failed login access event |
| `/api/audit-logs` | `GET` | Retrieve recorded audit logs with SHA-256 hashes |
| `/api/anomalies` | `GET` | Retrieve flagged user access anomalies |
| `/api/analytics/summary` | `GET` | Summary statistics (total events, anomalies, active sessions) |
| `/api/health` | `GET` | API health and pipeline status |

### Example Event Ingestion:
```bash
curl -X POST "http://localhost:8000/api/events" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "usr_alice",
    "event_type": "login",
    "ip_address": "192.168.1.105",
    "location": "US-East",
    "device_info": "Chrome/MacOS"
  }'
```

---

## Running Unit Tests

Run the full automated test suite:
```bash
python -m unittest discover -s tests
```
