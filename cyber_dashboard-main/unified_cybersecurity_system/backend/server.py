"""
server.py - Unified Cyber Defense Command Center FastAPI Server

Unites Blockchain Audit Logging, Digital Twin Simulation Engine, CyberSeer GNN Forecasting,
Machine Learning Threat Classification, and Telemetry Flow Ingestion into a single REST API platform.
"""

from __future__ import annotations
from datetime import datetime, timezone
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.api.audit import router as audit_router
from backend.api.twin import router as twin_router
from backend.api.forecast import router as forecast_router
from backend.api.live_ingest import router as live_ingest_router
from backend.config import settings
from backend.services.platform import platform
from backend.services.replay_service import replay_service

app = FastAPI(
    title="AI Cyber Defense Command Center API",
    version="2.0.0",
    description="Unified API combining Digital Twin, CyberSeer Forecasting, Machine Learning Threat Models, and Blockchain Audit Logging."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Core API Routers
app.include_router(audit_router)
app.include_router(twin_router)
app.include_router(forecast_router)
app.include_router(live_ingest_router)


@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "service": "unified-cybersecurity-platform",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": platform.mode.value,
        "modules": platform.snapshot()["model_status"],
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    return {"status": "ready", "mode": platform.mode.value}


@app.get("/metrics")
async def metrics():
    snapshot = platform.snapshot()
    return snapshot["metrics"]


@app.get("/api/v1/platform/snapshot")
async def platform_snapshot():
    return platform.snapshot()


@app.get("/api/v1/model/info")
async def model_info():
    """Returns registered machine learning model metadata, version, and genuine evaluation metrics."""
    return {
        "is_model_trained": platform.ml_engine.is_loaded,
        "model_version": platform.ml_engine.model_version,
        "feature_names": platform.ml_engine.feature_names,
        "metrics": platform.ml_engine.metrics,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/v1/replay/scenarios")
async def list_replay_scenarios():
    """Lists available pre-recorded attack and benign telemetry scenarios for replay."""
    return replay_service.list_available_scenarios()


@app.post("/api/v1/replay/start")
async def start_replay(
    scenario: str = Query("scenario_a", description="Scenario identifier (scenario_a, scenario_b, scenario_c)"),
    max_events: int = Query(25, ge=1, le=500, description="Max number of flows to replay")
):
    """Replays flow telemetry from specified scenario through the canonical ingestion pipeline."""
    try:
        results = replay_service.replay_scenario(scenario, max_events=max_events)
        return {
            "status": "replayed",
            "scenario": scenario,
            "replayed_events_count": len(results),
            "platform_snapshot": platform.snapshot()
        }
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=404, detail=str(fnf))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Static React Frontend Serving with Robust Absolute/Relative Path Resolution
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if not frontend_dist.exists():
    frontend_dist = Path("frontend/dist")

if frontend_dist.exists():
    if (frontend_dist / "assets").exists():
        app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
