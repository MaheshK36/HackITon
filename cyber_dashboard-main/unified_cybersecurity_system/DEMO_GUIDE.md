# Demo guide

The local app is **DEMO mode** by default. It is not a live enterprise feed.

1. Open the Digital Twin view.
2. Select **Run demo scenario**. This submits `recon_to_lateral` events to the ordinary ingestion endpoint.
3. Observe telemetry-derived hosts and communication edges.
4. Open Attack Forecast and run the labelled topology estimate.
5. Open Audit Log to inspect local SHA-256 evidence. It is not a blockchain transaction.

The API equivalent is `POST /api/v1/demo/recon_to_lateral`.
