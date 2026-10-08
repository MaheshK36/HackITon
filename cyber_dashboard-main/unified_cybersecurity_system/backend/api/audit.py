from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.services.platform import platform

router = APIRouter(prefix="/api", tags=["Audit evidence"])


@router.get("/audit-logs")
async def get_audit_logs(limit: int = 100):
    limit = max(1, min(limit, 500))
    recs = [record.to_dict() for record in platform.audit.records[-limit:]]
    return {"total_records": len(recs), "audit_logs": recs, "storage": "in-memory local demo evidence"}


@router.get("/anomalies")
async def get_anomalies():
    return {"count": len(platform.audit.incidents), "anomalies": platform.audit.incidents}


@router.get("/analytics/summary")
async def get_analytics_summary():
    return {**platform.audit.get_summary_metrics(), **platform.snapshot()["metrics"], "mode": platform.mode.value}


class HashCheck(BaseModel):
    event_id: str = Field(min_length=1, max_length=128)
    hash: str = Field(min_length=64, max_length=64)


@router.post("/verify-hash")
async def verify_log_hash(payload: HashCheck):
    return platform.audit.verify_hash(payload.event_id, payload.hash)
