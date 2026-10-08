"""
replay_service.py - Telemetry Replay Service for Attack Progression Scenarios

Streams raw network flow telemetry through the canonical PlatformService pipeline.
Enables verifiable demonstration of cyberattack progressions (Recon -> Brute Force -> Exfiltration, DoS, Benign).
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from backend.schemas import OperatingMode, TelemetryEvent
from backend.services.platform import platform

SCENARIOS: Dict[str, str] = {
    "scenario_a": "scenario_a_recon_bruteforce_exfil.csv",
    "scenario_b": "scenario_b_dos_command_exec.csv",
    "scenario_c": "scenario_c_benign.csv",
    "recon_to_exfil": "scenario_a_recon_bruteforce_exfil.csv",
    "dos_attack": "scenario_b_dos_command_exec.csv",
    "benign": "scenario_c_benign.csv"
}


class ReplayService:
    def __init__(self, data_dirs: Optional[List[Path]] = None):
        self.data_dirs = data_dirs or [
            Path("data/raw"),
            Path(__file__).resolve().parent.parent / "data" / "raw",
            Path(__file__).resolve().parent.parent.parent.parent / "digital twin 2" / "data" / "raw",
            Path(__file__).resolve().parent.parent.parent.parent / "data" / "raw",
        ]
        self.current_scenario: Optional[str] = None
        self.is_playing: bool = False
        self.replay_stats: Dict[str, Any] = {
            "total_events_replayed": 0,
            "last_replayed_at": None,
            "scenario": None
        }

    def find_scenario_file(self, scenario_name: str) -> Optional[Path]:
        canonical_name = SCENARIOS.get(scenario_name.lower(), scenario_name)
        for d in self.data_dirs:
            p = d / canonical_name
            if p.exists() and p.is_file():
                return p
        return None

    def list_available_scenarios(self) -> List[Dict[str, Any]]:
        available = []
        for name, filename in SCENARIOS.items():
            found = self.find_scenario_file(name)
            available.append({
                "scenario_id": name,
                "filename": filename,
                "available": found is not None,
                "file_path": str(found) if found else None
            })
        return available

    def read_scenario_events(self, scenario_name: str, max_events: Optional[int] = None) -> List[Dict[str, Any]]:
        file_path = self.find_scenario_file(scenario_name)
        if not file_path:
            raise FileNotFoundError(f"Scenario dataset for '{scenario_name}' not found.")

        events = []
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if max_events and i >= max_events:
                    break
                events.append(row)
        return events

    def replay_scenario(self, scenario_name: str, max_events: Optional[int] = None) -> List[Dict[str, Any]]:
        """Synchronously replays scenario flows through the canonical PlatformService."""
        raw_rows = self.read_scenario_events(scenario_name, max_events)
        results = []

        for row in raw_rows:
            # Map raw CSV row to canonical TelemetryEvent
            timestamp_val = float(row.get("timestamp", datetime.now(timezone.utc).timestamp()) or datetime.now(timezone.utc).timestamp())
            dt = datetime.fromtimestamp(timestamp_val, tz=timezone.utc)

            event = TelemetryEvent(
                timestamp=dt,
                source_ip=str(row.get("src_ip", "192.168.1.50")),
                destination_ip=str(row.get("dst_ip", "192.168.1.100")),
                source_port=int(float(row.get("src_port", 0))),
                destination_port=int(float(row.get("dst_port", 80))),
                protocol=str(row.get("protocol", "TCP")).lower(),
                bytes=int(float(row.get("tot_bytes", 0))),
                packets=int(float(row.get("tot_pkts", 1))),
                duration=float(row.get("duration", 0.0)),
                event_type="flow_replay",
                label=str(row.get("label", "BENIGN")),
                attack_stage=str(row.get("label", "BENIGN")),
                metadata={
                    "syn_flag_count": float(row.get("syn_flag_cnt", 0)),
                    "rst_flag_count": float(row.get("rst_flag_cnt", 0)),
                    "raw_label": str(row.get("label", "BENIGN")),
                    "scenario": scenario_name
                }
            )

            res = platform.ingest(event, mode=OperatingMode.REPLAY)
            results.append(res)
            self.replay_stats["total_events_replayed"] += 1

        self.replay_stats["scenario"] = scenario_name
        self.replay_stats["last_replayed_at"] = datetime.now(timezone.utc).isoformat()
        return results


replay_service = ReplayService()
