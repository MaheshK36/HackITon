"""
Software Platform Login/Logout Audit & Anomaly Detection System — Main Pipeline
Orchestrates:
  1. EventCollectorAgent  → Ingests platform login/logout events
  2. AnomalyAgent        → Detects behavioral anomalies (Multi-Confirm Gate)
  3. AuditAgent          → Hashes events and records audit trail on-chain
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Callable
import structlog

from agents.collector.collector_agent import CollectorAgent
from agents.anomaly.anomaly_agent import AnomalyAgent, AnomalyFinding
from agents.audit.audit_agent import AuditAgent, AuditRecord
from agents.incident import IncidentManager

logger = structlog.get_logger(__name__)

DASHBOARD_JSON_PATH = "data/dashboard.json"
AUDIT_LOG_PATH = "data/audit_events.jsonl"


class AccessAuditPipeline:
    """Main orchestrator for software platform login/logout access auditing."""

    def __init__(
        self,
        on_incident: Optional[Callable[[Dict[str, Any]], Any]] = None,
        poll_interval: int = 15,
        events_per_cycle: int = 10,
    ):
        self.poll_interval = poll_interval
        self.events_per_cycle = events_per_cycle
        self.on_incident = on_incident
        self.logger = logger.bind(component="pipeline")

        self.collector = CollectorAgent()
        self.anomaly_detector = AnomalyAgent()
        self.audit_agent = AuditAgent()
        self.incident_manager = IncidentManager()

        self._running = False
        self._stats = {
            "cycles_run": 0,
            "events_processed": 0,
            "anomalies_detected": 0,
            "audit_records_submitted": 0,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

        self._load_existing_state()
        self.logger.info("pipeline_initialized", poll_interval=poll_interval)

    def _load_existing_state(self):
        """Recover existing logged findings from JSONL store on restart."""
        if os.path.exists(AUDIT_LOG_PATH):
            try:
                count = 0
                with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            count += 1
                self._stats["audit_records_submitted"] = count
                self.logger.info("state_recovered", previous_records=count)
            except Exception as err:
                self.logger.warning("state_recovery_failed", error=str(err))

    async def run_cycle(self) -> List[Dict[str, Any]]:
        """Run a single audit and anomaly detection cycle."""
        cycle_start = time.time()
        self.logger.info("cycle_start", cycle=self._stats["cycles_run"] + 1)

        # Stage 1: Collect / ingest software platform access events
        events = self.collector.collect_events(count=self.events_per_cycle)
        self._stats["events_processed"] += len(events)

        # Stage 2: Run Multi-Confirm Anomaly Detection
        anomaly_findings = self.anomaly_detector.analyze_events(events)
        self._stats["anomalies_detected"] += len(anomaly_findings)

        # Map findings by user_id
        anomalies_by_user = {f.user_id: f for f in anomaly_findings}

        # Stage 3: Hash and submit on-chain audit records for all events
        new_audit_records: List[AuditRecord] = []
        for evt in events:
            uid = evt.get("user_id", "")
            finding_for_user = anomalies_by_user.get(uid)
            record = self.audit_agent.record_access_event(evt, anomaly_finding=finding_for_user)
            new_audit_records.append(record)
            self._stats["audit_records_submitted"] += 1

        # Process incident alerts for anomalies
        incidents_emitted = []
        for finding in anomaly_findings:
            inc = self.incident_manager.process_finding(finding)
            incidents_emitted.append(inc)
            if self.on_incident:
                try:
                    res = self.on_incident(inc)
                    if asyncio.iscoroutine(res):
                        await res
                except Exception as err:
                    self.logger.warning("on_incident_callback_failed", error=str(err))

        # Save audit logs to disk
        self.audit_agent.save_audit_log(AUDIT_LOG_PATH)

        # Update JSON dashboard state
        self._update_dashboard()

        self._stats["cycles_run"] += 1
        elapsed = time.time() - cycle_start
        self.logger.info("cycle_complete", cycle=self._stats["cycles_run"], events=len(events), anomalies=len(anomaly_findings), elapsed_s=round(elapsed, 2))

        return [f.to_dict() for f in anomaly_findings]

    async def run_continuous(self):
        """Run continuous monitoring loop."""
        self._running = True
        self.logger.info("continuous_monitoring_started", poll_interval=self.poll_interval)
        while self._running:
            try:
                await self.run_cycle()
            except Exception as err:
                self.logger.error("cycle_error", error=str(err))
            await asyncio.sleep(self.poll_interval)

    def stop(self):
        self._running = False
        self.logger.info("pipeline_stopped")

    def get_stats(self) -> Dict[str, Any]:
        return dict(self._stats)

    def _update_dashboard(self):
        """Sync system state to data/dashboard.json for React dashboard UI."""
        os.makedirs(os.path.dirname(DASHBOARD_JSON_PATH), exist_ok=True)
        
        all_events = self.collector.get_event_buffer()
        anomalies = self.incident_manager.get_all_incidents()
        recent_audits = [rec.to_dict() for rec in self.audit_agent.audit_log[-50:]]

        dashboard_state = {
            "summary": {
                "total_events": self._stats["events_processed"],
                "total_anomalies": self._stats["anomalies_detected"],
                "active_sessions": len(self.collector.get_active_sessions()),
                "audit_records_onchain": self._stats["audit_records_submitted"],
                "cycles_run": self._stats["cycles_run"],
                "last_updated": datetime.now(timezone.utc).isoformat(),
            },
            "events": all_events[-100:],
            "anomalies": anomalies,
            "audit_trail": recent_audits,
        }

        try:
            with open(DASHBOARD_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(dashboard_state, f, indent=2)
            # Sync to public static location if exists
            public_dash = "dashboard/public/dashboard.json"
            if os.path.exists("dashboard/public"):
                with open(public_dash, "w", encoding="utf-8") as f:
                    json.dump(dashboard_state, f, indent=2)
        except Exception as err:
            self.logger.warning("dashboard_update_failed", error=str(err))
