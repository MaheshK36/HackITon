# Threat model

| Item | Assessment |
|---|---|
| Assets | telemetry, model artifacts, audit evidence, API credentials, operational dashboard. |
| Actors | unauthenticated internet client, compromised telemetry source, insider, supply-chain attacker. |
| Boundaries | browser/API; source/API; API/model artifact; API/audit persistence; optional chain adapter. |
| Abuse cases | malformed/oversized telemetry, forged sources, API key theft, model substitution, dashboard XSS, audit tampering. |
| Current mitigations | typed validation, bounded route values, configurable CORS, optional API-key write guard, no public-chain raw telemetry. |
| Required mitigations | TLS, RBAC/OIDC, rate/body limits, signed model registry, durable append-only audit store, source authentication, monitoring and incident response. |

No input alone is proof that an attack occurred. Telemetry identity and integrity require trusted collectors and authenticated transport.
