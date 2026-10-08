"""
Software Platform Login/Logout Audit & Anomaly Detection System — Incident Manager
Aggregates login access anomaly findings into unified security Incident reports per user session.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

_INCIDENT_COUNTER_PATH = "data/incident_counter.txt"


class IncidentState:
    OPENED = "🟡 Access Alert Opened"
    ESCALATED = "🟠 Access Alert Escalated"
    CRITICAL = "🔴 Critical Access Violation"
    RESOLVED = "✅ Incident Resolved"


class IncidentManager:
    """Groups anomaly findings into user session access incidents."""

    def __init__(self):
        self.active_incidents: Dict[str, dict] = {}
        self.incident_counter = 0
        self._load_counter()

    def _load_counter(self):
        self._counter_date = datetime.now(tz=timezone.utc).strftime("%Y%m%d")
        try:
            if os.path.exists(_INCIDENT_COUNTER_PATH):
                with open(_INCIDENT_COUNTER_PATH, "r", encoding="utf-8") as f:
                    line = f.read().strip()
                    if line:
                        parts = line.split()
                        if len(parts) >= 2 and parts[0] == self._counter_date:
                            self.incident_counter = int(parts[1])
        except (ValueError, OSError):
            self.incident_counter = 0

    def _save_counter(self):
        try:
            os.makedirs(os.path.dirname(_INCIDENT_COUNTER_PATH), exist_ok=True)
            with open(_INCIDENT_COUNTER_PATH, "w", encoding="utf-8") as f:
                f.write(f"{self._counter_date} {self.incident_counter}")
        except OSError:
            pass

    def process_finding(self, finding: Any) -> dict:
        """Process an AnomalyFinding and associate it with a user incident."""
        user_id = getattr(finding, "user_id", "unknown")
        
        # Check if there is an active incident for this user
        if user_id in self.active_incidents:
            inc = self.active_incidents[user_id]
            inc["occurrences"] += 1
            inc["findings"].append(finding.to_dict() if hasattr(finding, "to_dict") else dict(finding))
            inc["peak_confidence"] = max(inc["peak_confidence"], getattr(finding, "confidence", 0.80))
            if inc["occurrences"] >= 3:
                inc["state"] = IncidentState.CRITICAL
            elif inc["occurrences"] >= 2:
                inc["state"] = IncidentState.ESCALATED
            return inc

        # Create new incident
        self.incident_counter += 1
        self._save_counter()
        inc_id = f"INC-{self._counter_date}-{self.incident_counter:04d}"

        inc = {
            "id": inc_id,
            "user_id": user_id,
            "anomaly_type": getattr(finding, "anomaly_type", "multivariate_access_anomaly"),
            "state": IncidentState.OPENED,
            "occurrences": 1,
            "peak_confidence": getattr(finding, "confidence", 0.80),
            "start_time": datetime.now(timezone.utc).isoformat(),
            "description": getattr(finding, "description", ""),
            "findings": [finding.to_dict() if hasattr(finding, "to_dict") else dict(finding)],
        }

        self.active_incidents[user_id] = inc
        return inc

    def get_all_incidents(self) -> List[dict]:
        return list(self.active_incidents.values())
