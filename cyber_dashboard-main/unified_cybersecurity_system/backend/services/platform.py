"""Single shared telemetry-to-decision service.

Integrates:
  1. Canonical telemetry ingestion with validation and normalization.
  2. Genuine Machine Learning model inference with feature attribution and MITRE ATT&CK mapping.
  3. Transparent heuristic fallback when no trained model checkpoint is loaded.
  4. Telemetry-derived Digital Twin state graph with node threat states.
  5. Cryptographic tamper-evident audit ledger (SHA-256 hash chaining).
"""
from __future__ import annotations

from collections import Counter, deque
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Optional

import numpy as np

from backend.adapters.normalization import normalize_flow_dict
from backend.config import settings
from backend.schemas import OperatingMode, TelemetryEvent
from backend.services.ml_engine import MLEngine
from blockchain.audit_agent import BlockchainAuditAgent
from digital_twin.state import DEFAULT_MITRE_STAGES, NetworkGraphState
from models.graph_encoder import GraphEncoder


class PlatformService:
    def __init__(self) -> None:
        self.mode = OperatingMode(settings.mode if settings.mode in OperatingMode.__members__ else "DEMO")
        self.graph = NetworkGraphState(demo_topology=False)
        self.audit = BlockchainAuditAgent(seed_demo_records=False)
        self.events: deque[dict[str, Any]] = deque(maxlen=1000)
        self.metrics = Counter(events_processed=0, predictions=0, errors=0)
        self.latencies: deque[float] = deque(maxlen=200)
        self.propagation = GraphEncoder()

        # Initialize ML engine and attempt loading serialized baseline model
        self.ml_engine = MLEngine()
        self._load_registered_model()
        self._load_registered_gnn()

    def _load_registered_model(self) -> None:
        potential_paths = [
            Path("data/models/baseline_rf.pkl"),
            Path(__file__).resolve().parent.parent / "data" / "models" / "baseline_rf.pkl",
            Path(__file__).resolve().parent.parent.parent.parent / "data" / "models" / "baseline_rf.pkl",
            Path(__file__).resolve().parent.parent.parent.parent / "digital twin 2" / "data" / "models" / "baseline_rf.pkl",
        ]
        for p in potential_paths:
            if p.exists():
                if self.ml_engine.load_model(p):
                    break

    def _load_registered_gnn(self) -> None:
        potential_gnn_paths = [
            Path("data/models/gnn_forecast_v1.0.pt"),
            Path(__file__).resolve().parent.parent / "data" / "models" / "gnn_forecast_v1.0.pt",
            Path(__file__).resolve().parent.parent.parent.parent / "data" / "models" / "gnn_forecast_v1.0.pt",
        ]
        for p in potential_gnn_paths:
            if p.exists():
                if self.propagation.load_checkpoint(p):
                    break

    @staticmethod
    def _heuristic(event: TelemetryEvent) -> dict[str, Any]:
        """Transparent fallback based solely on event fields; not a trained ML model."""
        metadata = event.metadata
        syn = float(metadata.get("syn_flag_count", metadata.get("SYN Flag Count", 0)) or 0)
        port_scan = bool(metadata.get("port_scan", False)) or (syn > 0 and event.packets <= 5)
        external = not event.source_ip.startswith(("10.", "192.168.", "172.16."))
        suspicious = port_scan or (event.destination_port in {22, 3389, 445} and external)
        score = min(0.95, 0.15 + (0.35 if port_scan else 0) + (0.2 if external else 0) + (0.15 if event.destination_port in {22, 3389, 445} else 0))
        observed = event.attack_stage or ("Reconnaissance" if suspicious else "Benign")
        next_state = "Initial Access" if observed == "Reconnaissance" and score >= 0.45 else observed
        evidence = []
        if port_scan: evidence.append("SYN activity with a small packet count")
        if external: evidence.append("external source address")
        if event.destination_port in {22, 3389, 445}: evidence.append(f"administrative service port {event.destination_port}")
        if not evidence: evidence.append("no rule-based attack indicators in this single event")
        return {
            "current_state": observed,
            "predicted_next_state": next_state,
            "confidence": round(score if suspicious else 1 - score, 3),
            "evidence": evidence,
            "model_version": "heuristic-v1",
            "inference_mode": "HEURISTIC_FALLBACK"
        }

    def ingest(self, event: TelemetryEvent, mode: OperatingMode | None = None) -> dict[str, Any]:
        started = perf_counter()
        run_mode = mode or self.mode
        try:
            feature_data = event.model_dump(mode="json")
            feature_data.update(event.metadata)
            features = normalize_flow_dict(feature_data)

            # Route decision: Genuine ML model if loaded, else transparent heuristic fallback
            if self.ml_engine.is_loaded:
                ml_result = self.ml_engine.predict(feature_data)
                decision = {
                    "current_state": ml_result["current_state"],
                    "predicted_next_state": ml_result["predicted_next_state"],
                    "confidence": ml_result["confidence"],
                    "evidence": [f"{k}: {v}" for k, v in ml_result.get("feature_explanations", {}).items()],
                    "mitre_technique": ml_result.get("mitre_technique", {}),
                    "predicted_next_technique": ml_result.get("predicted_next_technique", {}),
                    "next_stage_probabilities": ml_result.get("next_stage_probabilities", []),
                    "feature_explanations": ml_result.get("feature_explanations", {}),
                    "model_version": ml_result["model_version"],
                    "inference_mode": "TRAINED_MODEL_INFERENCE"
                }
            else:
                decision = self._heuristic(event)

            risk = min(1.0, decision["confidence"] * (0.5 + 0.5 * (0.95 if event.destination_port in {5432, 3306, 1433} else 0.5)))
            self.graph.observe_flow(event.source_ip, event.destination_ip, event.destination_port)
            target = self.graph.ensure_host(event.destination_ip, hostname=event.hostname)
            stage = decision["predicted_next_state"]
            stage_idx = DEFAULT_MITRE_STAGES.index(stage) if stage in DEFAULT_MITRE_STAGES else 0
            self.graph.update_host_state(event.destination_ip, stage_idx, stage, risk, features)

            audit_record = self.audit.record_event({
                "event_id": event.event_id,
                "user_id": event.user_id or "telemetry",
                "event_type": event.event_type,
                "ip_address": event.source_ip,
                "timestamp": event.timestamp.isoformat()
            })

            result = {
                "event": feature_data,
                "mode": run_mode.value,
                "normalized_feature_count": len(features),
                "decision": decision,
                "risk": self.risk_breakdown(target.ip_address),
                "audit": audit_record.to_dict(),
                "processing_timestamp": datetime.now(timezone.utc).isoformat()
            }
            self.events.append(result)
            self.metrics["events_processed"] += 1
            self.metrics["predictions"] += 1
            return result
        except Exception:
            self.metrics["errors"] += 1
            raise
        finally:
            self.latencies.append((perf_counter() - started) * 1000)

    def risk_breakdown(self, host_ip: str) -> dict[str, Any]:
        host = self.graph.get_host(host_ip)
        if host is None:
            return {"overall": "INSUFFICIENT_EVIDENCE", "score": None, "contributors": []}
        score = round(min(1.0, 0.65 * host.infiltration_prob + 0.35 * host.criticality), 3)
        level = "HIGH" if score >= .7 else "MEDIUM" if score >= .35 else "LOW"
        return {
            "overall": level,
            "score": score,
            "contributors": [
                {"factor": "attack_probability", "value": round(host.infiltration_prob, 3)},
                {"factor": "asset_criticality", "value": round(host.criticality, 3)}
            ]
        }

    def snapshot(self) -> dict[str, Any]:
        nodes = [host.to_dict() for host in self.graph.hosts.values()]
        edges = [{"source": u, "target": v, **dict(data)} for u, v, data in self.graph.graph.edges(data=True)]
        critical = [node for node in nodes if node["criticality"] >= .8]
        return {
            "mode": self.mode.value,
            "nodes": nodes,
            "edges": edges,
            "recent_events": list(self.events)[-20:],
            "critical_assets": critical,
            "metrics": {
                **self.metrics,
                "mean_processing_latency_ms": round(float(np.mean(self.latencies)), 2) if self.latencies else 0.0
            },
            "model_status": {
                "attack_state": f"Trained Model ({self.ml_engine.model_version})" if self.ml_engine.is_loaded else "heuristic fallback; no registered trained checkpoint",
                "is_model_trained": self.ml_engine.is_loaded,
                "model_version": self.ml_engine.model_version,
                "evaluation_metrics": self.ml_engine.metrics if self.ml_engine.is_loaded else {},
                "propagation": f"GNN (trained, {self.propagation.model_version})" if self.propagation.is_trained else "Topology risk diffusion (fallback)",
                "is_gnn_trained": self.propagation.is_trained,
                "gnn_model_version": self.propagation.model_version,
                "gnn_evaluation_metrics": self.propagation.metrics if self.propagation.is_trained else {},
            }
        }

    def forecast(self, steps: int) -> dict[str, Any]:
        nodes = [host.to_dict() for host in self.graph.hosts.values()]
        if not nodes:
            return {"status": "INSUFFICIENT_EVIDENCE", "reason": "No telemetry-derived graph exists yet."}
        edges = [{"source": u, "target": v} for u, v in self.graph.graph.edges()]
        result = self.propagation.predict_propagation(nodes, edges, steps=max(1, min(steps, 20)))
        result.update({
            "status": "PREDICTION",
        })
        return result

    def run_demo(self, scenario: str) -> list[dict[str, Any]]:
        scenarios = {
            "benign": [
                {"source_ip": "10.0.0.10", "destination_ip": "10.0.0.20", "destination_port": 443, "protocol": "tcp", "bytes": 1200, "packets": 12, "duration": .4}
            ],
            "recon_to_lateral": [
                {"source_ip": "198.51.100.10", "destination_ip": "10.0.0.20", "destination_port": 22, "protocol": "tcp", "packets": 2, "duration": .1, "metadata": {"syn_flag_count": 1, "port_scan": True}},
                {"source_ip": "10.0.0.20", "destination_ip": "10.0.0.30", "destination_port": 445, "protocol": "tcp", "packets": 3, "duration": .2, "attack_stage": "Lateral Movement"},
                {"source_ip": "10.0.0.30", "destination_ip": "10.0.0.40", "destination_port": 5432, "protocol": "tcp", "packets": 8, "duration": .5, "attack_stage": "Exfiltration", "bytes": 85000},
                {"source_ip": "198.51.100.10", "destination_ip": "10.0.0.50", "destination_port": 3389, "protocol": "tcp", "packets": 15, "duration": .3, "metadata": {"rst_flag_count": 5}},
            ],
        }
        if scenario not in scenarios:
            raise ValueError("unknown demo scenario")
        return [self.ingest(TelemetryEvent(**payload), OperatingMode.DEMO) for payload in scenarios[scenario]]


platform = PlatformService()
