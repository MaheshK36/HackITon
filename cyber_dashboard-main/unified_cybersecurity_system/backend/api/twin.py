"""Telemetry-derived digital-twin state endpoints."""
from fastapi import APIRouter, HTTPException

from backend.services.platform import platform

router = APIRouter(prefix="/api/v1/twin", tags=["Digital twin"])


@router.get("/state")
async def get_current_twin_state():
    return {"status": "active", **platform.snapshot()}


@router.post("/rollout")
async def run_digital_twin_rollout():
    raise HTTPException(
        status_code=501,
        detail="Autoregressive rollout is disabled: no compatible trained checkpoint and model metadata are registered. Use /api/v1/forecast/propagation for the labelled topology heuristic.",
    )


@router.post("/fidelity")
async def run_twin_fidelity_benchmark():
    raise HTTPException(
        status_code=501,
        detail="Fidelity evaluation requires held-out ground-truth sequences and a registered trained model artifact; neither is currently available.",
    )
