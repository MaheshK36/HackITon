# API

Base URL: `http://127.0.0.1:8000`

| Route | Purpose |
|---|---|
| `GET /health`, `GET /ready`, `GET /metrics` | Liveness, readiness, local processing counters. |
| `GET /api/v1/platform/snapshot` | Shared graph, recent events, audit-derived state and explicit model status. |
| `POST /api/v1/flows/ingest` | Validated canonical `TelemetryEvent` ingestion. |
| `POST /api/v1/demo/benign` | Reproducible benign demo through the same pipeline. |
| `POST /api/v1/demo/recon_to_lateral` | Reproducible multi-event attack scenario through the same pipeline. |
| `POST /api/v1/forecast/propagation` | Labelled topology risk-diffusion estimate; requires observed graph data. |
| `GET /api/v1/twin/state` | Telemetry-derived digital twin state. |
| `GET /api/audit-logs`, `GET /api/anomalies` | Local cryptographic evidence records and heuristic alerts. |

`TelemetryEvent` requires `source_ip` and `destination_ip`. IP addresses, ports, non-negative numeric values and timezone-aware timestamps are validated. Write routes require `X-API-Key` when `CYBER_REQUIRE_API_KEY=true`.

The API does not claim trained ML inference, on-chain audit records, or live enterprise telemetry when those components are absent.
