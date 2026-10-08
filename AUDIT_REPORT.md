# SIH-MAX Technical Audit

**Audit date:** 2026-08-31  
**Scope:** Every repository source/configuration directory was inventoried from the repository root (276 non-dependency files). Source code, rather than README claims, is the basis of this report.

## Executive assessment

SIH-MAX is a collection of cybersecurity research prototypes, not yet a cohesive product. The closest thing to an integrated application is `cyber_dashboard-main/unified_cybersecurity_system`. It starts successfully and exposes a FastAPI API plus React UI, but it is a **simulation/demo prototype**: it instantiates random PyTorch models when no checkpoint exists, uses a fixed six-host topology, seeds audit data on startup, and maintains disconnected global state per route module. It must not be represented as live enterprise detection or validated predictive ML.

The useful research should be retained:

- `attack model/` contains temporal data-windowing and LSTM/GRU training experiments, but also many duplicate, machine-specific dataset scripts.
- `network model/` contains a more developed CIC-IDS/CTU preprocessing and leakage-checking research track, including baseline evaluation artifacts.
- `digital twin 2/` contains reusable replay, graph, MITRE, and feature-processing concepts.
- `BLOCKCHAIN--main/` contains a separate Mantle on-chain intelligence application and Solidity audit contract. Its purpose is not equivalent to cyber telemetry detection, so it should remain optional evidence/audit work rather than a core detection dependency.

## Current architecture and execution flow

```
React/Vite frontend (port 5173 or build served on 8000)
    -> FastAPI route modules
       -> independent module-level model/state/audit objects
          -> fixed topology + randomly initialized model inference
          -> in-memory SHA-256 audit records
```

The apparent `/api/v1/flows/ingest` pipeline normalizes a loose dictionary, runs an untrained `AttackWorldModel`, updates only `live_ingest.network_state`, and writes only to `live_ingest.audit_agent`. The `/api/v1/twin/*` and `/api/audit-*` routes use different state objects, so the dashboard cannot reliably show the result of ingestion.

## Component inventory

| Area | Source-of-truth status | Key finding |
|---|---|---|
| `cyber_dashboard-main/unified_cybersecurity_system` | Runnable prototype | Best integration target, but insecure and demo-only as currently implemented. |
| `attack model` | Research/training scripts | Duplicate scripts, absolute `C:/Users/mahes/...` paths, synthetic IP assignment and no reusable inference artifact contract. |
| `network model` | Research pipeline | Has useful validation/leakage utilities, but `run_all_phases.py` references missing preprocessing/model files; not connected to API. |
| `digital twin` | Visualization/research | Standalone code and Streamlit-era work; not wired into the application. |
| `digital twin 2` | Replay/research | Useful schema, stream/replay/MITRE concepts but standalone and not API-integrated. |
| `BLOCKCHAIN--main` | Separate product | Separate Python API, React dashboard and Mantle Solidity contract; optional audit evidence work, not integrated into cyber platform. |
| `cyber_dashboard-main/cyber_dashboard-main` | Standalone UI | Separate React app. Its declared Vite `^8.2.2` installation was invalid in this environment; not integrated. |

## API inventory and defects

| Endpoint group | Current behavior | Defect/risk |
|---|---|---|
| `/api/health` | Returns fixed module strings | No readiness, metrics, version or dependency truthfulness. |
| `/api/audit-*` | In-memory seeded SHA-256 records | No persistence; claiming `On-Chain` is unsupported when Web3 is not connected. |
| `/api/v1/flows/ingest` | Dict input -> random model -> isolated graph | No typed validation, auth, request limit, canonical schema or shared state. |
| `/api/v1/twin/*` | Starts a new default topology for read/forecast paths | Not based on ingested telemetry. Fidelity endpoint compares generated states, not held-out evidence. |
| `/api/v1/forecast/propagation` | Handwritten risk diffusion | `GraphEncoder.forward` is unused; output is a heuristic, not a trained GNN forecast. |

## ML inventory and validation

- `AttackWorldModel` is a valid PyTorch LSTM/GRU architecture but the integrated service finds no checkpoint in `models/checkpoints`; therefore it uses randomly initialized weights. Its output must not be treated as a prediction.
- `GraphEncoder` is an untrained neural module; its API bypasses it and uses a deterministic propagation heuristic. The code presently calls this “real” forecasting without trained-model evidence.
- `network model/models/baseline_results.json` is an existing result artifact, but no audit here can establish provenance or reuse it for API inference.
- There is no unified dataset manifest, preprocessing artifact, model registry, time-aware train/test enforcement across all projects, or produced ML evaluation report for the integrated system.

## Frontend inventory

The unified React dashboard calls backend routes, but it also embeds multiple independent localhost applications (`5174`, `8501`, `8502`, `8080`, `5175`). Those services are not started by the unified launcher. Several visualizations therefore cannot be considered product views. The dashboard needs one state snapshot API and explicit `DEMO`, `REPLAY`, and `LIVE` labels.

## Blockchain inventory

The integrated `blockchain/audit_agent.py` is a local SHA-256 event ledger; it does not submit to a contract. `tx_hash` is fabricated from the event hash and wording such as “On-Chain Verified” is misleading. The separate Mantle project contains the Solidity work, config and deployment scripts but is disconnected. The correct role is an optional tamper-evident audit/evidence adapter, with raw telemetry excluded from public-chain storage.

## Security findings

1. `allow_origins=["*"]` together with credentials is unsafe and invalid for production use.
2. Every ingestion/audit/simulation endpoint is unauthenticated and un-authorized.
3. Inputs are untyped dictionaries; IPs, ports, timestamps, numeric finiteness and payload size are not validated.
4. In-memory state has no concurrency or persistence model.
5. Audit event identifiers can collide; audit logs are not atomically persisted.
6. Multiple research scripts use `subprocess(..., shell=True)` and hard-coded local paths.
7. The separate blockchain application contains optional external integrations and key configuration; no real secret was found in the committed `.env.example`, but all deployment credentials must remain environment-only.

## Production gaps and technical debt

- No canonical telemetry schema or reusable preprocessing artifact.
- No detection/prediction contract distinguishing observed facts from model estimates.
- No shared graph/twin/audit state.
- No risk engine, attack path algorithm, evidence-backed ETA, counterfactual simulation or explainability service.
- No API auth abstraction, RBAC, rate/request controls, structured logging or metrics.
- No root-level Docker Compose/reproducible deployment path.
- Tests verify response shape and random model execution, not model quality or a real ingestion-to-decision chain.
- Duplicate prototypes and stale documentation make root-level startup ambiguous.

## Recommended architecture and priority

The implementation target is the existing unified FastAPI/React application, retaining research modules only behind explicit interfaces. The immediate architecture is a modular monolith:

```
TelemetryEvent (Pydantic) -> validation/normalization -> feature vector
 -> shared platform service -> graph/twin state -> heuristic or registered model inference
 -> risk + propagation + explainability + audit evidence -> API snapshot -> dashboard
```

1. Create typed canonical telemetry, configuration, shared state and an honest `DEMO/REPLAY/LIVE` execution mode.
2. Replace random-model claims with a clearly identified heuristic fallback; load a registered model only when a compatible artifact and metadata exist.
3. Make graph, digital twin, risk, propagation and audit use one service instance.
4. Add validation, configurable CORS, development API-key authentication, health/readiness/metrics and structured-safe logging.
5. Implement reproducible demo telemetry through this same ingest path, then wire the UI to the shared snapshot.
6. Add targeted unit/API/integration tests, deployment artifacts and an evidence-only ML validation report.

## Audit limitations

This audit did not train models: no suitable canonical dataset/artifact is committed. Existing benchmark artifacts are documented as unverified research artifacts, not product-level metrics. The repository has no Git metadata in the supplied root, so a change-history audit was not possible.
