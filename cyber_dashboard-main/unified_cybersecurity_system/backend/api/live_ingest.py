"""Validated telemetry ingestion and reproducible demo scenarios."""
from fastapi import APIRouter, Depends, HTTPException

from backend.schemas import TelemetryEvent
from backend.services.platform import platform
from backend.server_security import require_write_access

router = APIRouter(prefix="/api/v1", tags=["Telemetry"])


@router.post("/flows/ingest")
async def ingest_live_flow_telemetry(event: TelemetryEvent, _: None = Depends(require_write_access)):
    return platform.ingest(event)


@router.post("/demo/{scenario}")
async def run_demo_scenario(scenario: str, _: None = Depends(require_write_access)):
    try:
        return {"mode": "DEMO", "scenario": scenario, "events": platform.run_demo(scenario), "snapshot": platform.snapshot()}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
