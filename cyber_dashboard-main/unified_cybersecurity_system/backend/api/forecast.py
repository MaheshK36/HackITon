from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.services.platform import platform

router = APIRouter(prefix="/api/v1/forecast", tags=["Prediction"])


class ForecastRequest(BaseModel):
    steps: int = Field(default=5, ge=1, le=20)


@router.post("/propagation")
async def forecast_attack_propagation(payload: ForecastRequest):
    return platform.forecast(payload.steps)
