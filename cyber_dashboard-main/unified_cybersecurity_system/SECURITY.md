# Security status

Implemented: canonical validation for public telemetry (including IP, port, numeric bounds and timezone-aware timestamps), bounded forecast input, configurable CORS without wildcard credentials, and a deployment-configurable `X-API-Key` guard for write endpoints.

Before production: set `CYBER_REQUIRE_API_KEY=true`, provide `CYBER_API_KEY` through a secret manager, place the API behind TLS/authentication/RBAC, persist audit records atomically, add rate limiting/body-size middleware, and replace in-memory state with an appropriately secured store.

The local SHA-256 ledger is **not blockchain** and must not be called on-chain evidence. Do not store raw telemetry or identities on a public chain.
