"""
Software Platform Login/Logout Audit & Anomaly Detection System — Collector Agent (Stage 1)
Ingests and buffers user session access events: logins, logouts, and failed login attempts.
Supports both live API event ingestion and realistic event stream simulation for continuous monitoring.
"""
from __future__ import annotations

import random
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import structlog

logger = structlog.get_logger(__name__)

# Sample platform users for simulated access logs
PLATFORM_USERS = [
    {"user_id": "usr_alice", "role": "engineer", "normal_ip": "192.168.1.105", "location": "US-East", "device": "Chrome/MacOS"},
    {"user_id": "usr_bob", "role": "product_mgr", "normal_ip": "192.168.1.110", "location": "US-West", "device": "Firefox/Windows"},
    {"user_id": "usr_charlie", "role": "devops", "normal_ip": "10.0.4.15", "location": "US-East", "device": "Terminal/Linux"},
    {"user_id": "usr_admin", "role": "sys_admin", "normal_ip": "10.0.1.1", "location": "US-Central", "device": "Chrome/Windows"},
    {"user_id": "usr_dev_lead", "role": "tech_lead", "normal_ip": "192.168.2.88", "location": "EU-West", "device": "Safari/MacOS"},
    {"user_id": "usr_guest", "role": "contractor", "normal_ip": "172.16.0.42", "location": "US-East", "device": "Edge/Windows"},
]

SUSPICIOUS_LOCATIONS = ["RU-Moscow", "CN-Shanghai", "KP-Pyongyang", "UNKNOWN-PROXY", "TOR-EXIT-NODE"]
SUSPICIOUS_DEVICES = ["Python-urllib/3.10", "Curl/7.68.0", "Unrecognized-Android-OS", "Automated-Script-v1"]


class CollectorAgent:
    """Stage 1: Collects and buffers software platform login & logout access events."""

    def __init__(self, buffer_size: int = 500):
        self.buffer_size = buffer_size
        self._event_buffer: List[Dict[str, Any]] = []
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
        self.logger = logger.bind(agent="collector")
        self.logger.info("collector_agent_initialized", buffer_size=buffer_size)

    def add_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest a single login/logout event directly from API server or external feed."""
        required_fields = ["user_id", "event_type"]
        for field in required_fields:
            if field not in event:
                raise ValueError(f"Missing required field: {field}")

        evt = {
            "event_id": event.get("event_id") or f"EVT-{uuid.uuid4().hex[:8].upper()}",
            "user_id": str(event["user_id"]),
            "session_id": event.get("session_id") or f"SESS-{uuid.uuid4().hex[:6].upper()}",
            "event_type": event["event_type"],  # "login", "logout", "failed_login"
            "timestamp": event.get("timestamp") or datetime.now(timezone.utc).isoformat(),
            "ip_address": event.get("ip_address", "127.0.0.1"),
            "location": event.get("location", "US-East"),
            "device_info": event.get("device_info", "Chrome/Windows"),
            "status": event.get("status", "success" if event["event_type"] != "failed_login" else "failed"),
        }

        # Track session state
        if evt["event_type"] == "login" and evt["status"] == "success":
            self._active_sessions[evt["session_id"]] = evt
        elif evt["event_type"] == "logout" and evt["session_id"] in self._active_sessions:
            self._active_sessions.pop(evt["session_id"], None)

        self._event_buffer.append(evt)
        if len(self._event_buffer) > self.buffer_size:
            self._event_buffer = self._event_buffer[-self.buffer_size:]

        self.logger.info("event_ingested", event_id=evt["event_id"], user_id=evt["user_id"], event_type=evt["event_type"])
        return evt

    def collect_events(self, count: int = 10, simulate_anomalies: bool = True) -> List[Dict[str, Any]]:
        """Collect/generate a batch of login/logout access events for analysis."""
        collected: List[Dict[str, Any]] = []

        for _ in range(count):
            # 15% chance to simulate an anomaly if enabled
            is_anomalous = simulate_anomalies and random.random() < 0.15
            user = random.choice(PLATFORM_USERS)
            now_iso = datetime.now(timezone.utc).isoformat()

            if is_anomalous:
                anomaly_kind = random.choice(["failed_burst", "off_hours_geo", "new_device", "unclosed_orphan"])
                
                if anomaly_kind == "failed_burst":
                    # Burst of failed login attempts
                    session_id = f"SESS-{uuid.uuid4().hex[:6].upper()}"
                    for _ in range(random.randint(4, 7)):
                        evt = self.add_event({
                            "user_id": user["user_id"],
                            "session_id": session_id,
                            "event_type": "failed_login",
                            "timestamp": now_iso,
                            "ip_address": f"198.51.100.{random.randint(10, 200)}",
                            "location": random.choice(SUSPICIOUS_LOCATIONS),
                            "device_info": random.choice(SUSPICIOUS_DEVICES),
                            "status": "failed"
                        })
                        collected.append(evt)
                elif anomaly_kind == "off_hours_geo":
                    # Login from suspicious location / IP at unusual time
                    evt = self.add_event({
                        "user_id": user["user_id"],
                        "session_id": f"SESS-{uuid.uuid4().hex[:6].upper()}",
                        "event_type": "login",
                        "timestamp": now_iso,
                        "ip_address": f"203.0.113.{random.randint(1, 255)}",
                        "location": random.choice(SUSPICIOUS_LOCATIONS),
                        "device_info": user["device"],
                        "status": "success"
                    })
                    collected.append(evt)
                elif anomaly_kind == "new_device":
                    # Login with unrecognized device
                    evt = self.add_event({
                        "user_id": user["user_id"],
                        "session_id": f"SESS-{uuid.uuid4().hex[:6].upper()}",
                        "event_type": "login",
                        "timestamp": now_iso,
                        "ip_address": user["normal_ip"],
                        "location": user["location"],
                        "device_info": random.choice(SUSPICIOUS_DEVICES),
                        "status": "success"
                    })
                    collected.append(evt)
                else:  # unclosed_orphan
                    evt = self.add_event({
                        "user_id": user["user_id"],
                        "session_id": f"SESS-ORPHAN-{uuid.uuid4().hex[:4].upper()}",
                        "event_type": "login",
                        "timestamp": now_iso,
                        "ip_address": user["normal_ip"],
                        "location": user["location"],
                        "device_info": user["device"],
                        "status": "success"
                    })
                    collected.append(evt)
            else:
                # Normal login or logout flow
                event_type = "login" if random.random() > 0.4 else "logout"
                session_id = f"SESS-{uuid.uuid4().hex[:6].upper()}"
                evt = self.add_event({
                    "user_id": user["user_id"],
                    "session_id": session_id,
                    "event_type": event_type,
                    "timestamp": now_iso,
                    "ip_address": user["normal_ip"],
                    "location": user["location"],
                    "device_info": user["device"],
                    "status": "success"
                })
                collected.append(evt)

        self.logger.info("events_collected", count=len(collected), total_buffered=len(self._event_buffer))
        return collected

    def get_event_buffer(self) -> List[Dict[str, Any]]:
        """Return the current event buffer."""
        return list(self._event_buffer)

    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Return active open sessions."""
        return dict(self._active_sessions)
