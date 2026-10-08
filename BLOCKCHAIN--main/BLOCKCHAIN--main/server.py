"""
Software Platform Login/Logout Audit & Anomaly Detection System — FastAPI Server
Exposes REST API endpoints for event ingestion, audit log retrieval, and anomaly analytics.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, BackgroundTasks, Request, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

import structlog
structlog.configure(processors=[structlog.dev.ConsoleRenderer(colors=True)])

from agents.pipeline import AccessAuditPipeline, DASHBOARD_JSON_PATH, AUDIT_LOG_PATH

app = FastAPI(
    title="Software Platform Login/Logout Audit & Anomaly Detection API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline_instance: Optional[AccessAuditPipeline] = None


@app.on_event("startup")
async def startup_event():
    global pipeline_instance
    pipeline_instance = AccessAuditPipeline(poll_interval=15, events_per_cycle=10)
    # Run initial cycle to populate dashboard data
    await pipeline_instance.run_cycle()


@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "service": "access-audit-anomaly-system",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pipeline_running": pipeline_instance._running if pipeline_instance else False,
    }


@app.post("/api/events")
async def ingest_access_event(event: Dict[str, Any] = Body(...)):
    """API Endpoint: Ingest a software platform login, logout, or failed_login event."""
    if not pipeline_instance:
        raise HTTPException(status_code=500, detail="Pipeline not initialized")
    try:
        recorded_evt = pipeline_instance.collector.add_event(event)
        # Trigger an anomaly check cycle
        anomalies = pipeline_instance.anomaly_detector.analyze_events([recorded_evt])
        finding = anomalies[0] if anomalies else None
        audit_rec = pipeline_instance.audit_agent.record_access_event(recorded_evt, anomaly_finding=finding)
        pipeline_instance.audit_agent.save_audit_log(AUDIT_LOG_PATH)
        pipeline_instance._update_dashboard()

        return {
            "status": "success",
            "event": recorded_evt,
            "anomaly_detected": len(anomalies) > 0,
            "audit_record": audit_rec.to_dict(),
        }
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Failed to ingest event: {str(err)}")


@app.get("/api/audit-logs")
async def get_audit_logs(limit: int = 100):
    """API Endpoint: Fetch software access audit event stream with SHA-256 hashes."""
    records = []
    if os.path.exists(AUDIT_LOG_PATH):
        try:
            with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line.strip()))
        except Exception:
            pass
    return {
        "total_records": len(records),
        "audit_logs": records[-limit:],
    }


@app.get("/api/anomalies")
async def get_anomalies():
    """API Endpoint: Fetch detected login access anomalies."""
    if not pipeline_instance:
        return {"anomalies": []}
    incidents = pipeline_instance.incident_manager.get_all_incidents()
    return {
        "count": len(incidents),
        "anomalies": incidents,
    }


@app.get("/api/analytics/summary")
async def get_analytics_summary():
    """API Endpoint: Summary metrics for dashboard analytics."""
    if os.path.exists(DASHBOARD_JSON_PATH):
        try:
            with open(DASHBOARD_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("summary", {})
        except Exception:
            pass

    if pipeline_instance:
        return pipeline_instance.get_stats()
    return {}


# Serve React Frontend Static Files if built
frontend_dist = Path("dashboard/dist")
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
