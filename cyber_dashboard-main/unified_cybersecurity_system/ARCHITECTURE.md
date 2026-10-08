# Architecture

The product target is a modular FastAPI application, not a collection of independently embedded demos.

```
Canonical TelemetryEvent
  -> Pydantic validation
  -> normalization (42-feature compatibility vector)
  -> shared PlatformService
  -> telemetry-derived network graph / digital twin
  -> labelled decision method + risk / propagation estimate
  -> local cryptographic audit evidence
  -> snapshot and dashboard
```

`PlatformService` is the only application state owner. API routes no longer construct independent graphs or audit ledgers. `DEMO` events and future replay/live adapters must use the same `ingest` method.

Current inference is explicitly `HEURISTIC_FALLBACK`; an LSTM/GRU model is not enabled until a compatible checkpoint, preprocessing artifact, dataset version and evaluation metadata are registered. The untrained GNN class is also not used for decisions.
