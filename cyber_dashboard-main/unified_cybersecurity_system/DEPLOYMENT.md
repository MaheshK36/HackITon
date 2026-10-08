# Deployment

## Local

1. Copy `.env.example` to `.env` and set deployment values.
2. Install Python dependencies: `py -3 -m pip install -r requirements.txt`.
3. Build UI: `cd frontend && npm ci && npm run build`.
4. Start: `py -3 main.py`.
5. Open `http://127.0.0.1:8000`.

## Container

`Dockerfile` and `docker-compose.yml` are provided. When Docker is installed:

```text
copy .env.example .env
docker compose up --build
```

This environment did not have Docker installed, so the image was not built here.

## Production prerequisites

Use TLS/reverse proxy, set `CYBER_REQUIRE_API_KEY=true`, inject a strong key through a secret manager, restrict `CYBER_CORS_ORIGINS`, add a durable state/audit store, and register only evaluated model artifacts with compatible preprocessing metadata.
