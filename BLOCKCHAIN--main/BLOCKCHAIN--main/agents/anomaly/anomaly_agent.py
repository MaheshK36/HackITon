"""
Software Platform Login/Logout Audit & Anomaly Detection System — Anomaly Agent (Stage 2)
Detects software access anomalies using Z-Score + Isolation Forest + Rule-based Multi-Confirm Gate.
Requires ≥2 detection algorithms to agree before firing an anomaly finding (confidence ≥ 0.80).
"""
from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import structlog

logger = structlog.get_logger(__name__)

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


CONFIDENCE_THRESHOLD = 0.80
ZSCORE_THRESHOLD = 2.0
CONTAMINATION = 0.03


@dataclass
class AnomalyFinding:
    finding_id: str
    anomaly_type: str        # "failed_login_burst" | "off_hours_geo_shift" | "unrecognized_device" | "orphan_session" | "multivariate_access_anomaly"
    user_id: str
    timestamp: str
    confidence: float        # 0.80 – 1.0
    description: str
    methods_agreed: List[str] = field(default_factory=list)
    raw_metrics: Dict[str, Any] = field(default_factory=dict)
    event_ids: List[str] = field(default_factory=list)
    is_anomaly: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)

    def sha256_hash(self) -> str:
        """Canonical SHA256 hash for on-chain audit recording."""
        core = {
            "confidence": round(float(self.confidence), 4),
            "event_count": len(self.event_ids),
            "type": self.anomaly_type,
            "user_id": self.user_id,
        }
        canonical = json.dumps(core, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class AnomalyAgent:
    """Stage 2: Analyzes login/logout access logs for behavioral anomalies."""

    def __init__(self, confidence_threshold: float = CONFIDENCE_THRESHOLD):
        self.confidence_threshold = confidence_threshold
        self.logger = logger.bind(agent="anomaly")
        self.history_buffer: List[Dict[str, Any]] = []
        self.logger.info("anomaly_agent_initialized", confidence_threshold=confidence_threshold)

    def analyze_events(self, events: List[Dict[str, Any]]) -> List[AnomalyFinding]:
        """Analyze a batch of login/logout access events and return multi-confirmed anomalies."""
        if not events:
            return []

        self.history_buffer.extend(events)
        if len(self.history_buffer) > 1000:
            self.history_buffer = self.history_buffer[-1000:]

        findings: List[AnomalyFinding] = []

        # Group events by user_id
        user_groups: Dict[str, List[Dict[str, Any]]] = {}
        for evt in events:
            uid = evt.get("user_id", "unknown")
            user_groups.setdefault(uid, []).append(evt)

        # Compute baseline statistics across all users for Z-score
        user_attempt_counts = [len(evts) for evts in user_groups.values()]
        mean_attempts = float(np.mean(user_attempt_counts)) if NUMPY_AVAILABLE and user_attempt_counts else 1.0
        std_attempts = float(np.std(user_attempt_counts)) if NUMPY_AVAILABLE and user_attempt_counts else 1.0
        if std_attempts == 0:
            std_attempts = 1.0

        # Build feature matrix for Isolation Forest if available
        features_list = []
        user_id_order = []
        for uid, evts in user_groups.items():
            feat = self._extract_user_features(evts)
            features_list.append(feat)
            user_id_order.append(uid)

        iforest_anomalies = set()
        if SKLEARN_AVAILABLE and NUMPY_AVAILABLE and len(features_list) >= 3:
            try:
                X = np.array(features_list)
                clf = IsolationForest(contamination=CONTAMINATION, random_state=42)
                preds = clf.fit_predict(X)
                for idx, pred in enumerate(preds):
                    if pred == -1:  # Outlier
                        iforest_anomalies.add(user_id_order[idx])
            except Exception as err:
                self.logger.warning("iforest_failed", error=str(err))

        # Evaluate each user's activity using the Multi-Confirm Gate
        for uid, evts in user_groups.items():
            agreeing_methods = []
            anomaly_types = []
            metrics = self._extract_user_metrics(evts)

            # Method 1: Z-Score Frequency Spike
            z_score = (len(evts) - mean_attempts) / std_attempts
            if z_score >= ZSCORE_THRESHOLD:
                agreeing_methods.append("z_score")
                anomaly_types.append("failed_login_burst" if metrics["failed_count"] > 2 else "multivariate_access_anomaly")

            # Method 2: Isolation Forest Outlier
            if uid in iforest_anomalies:
                agreeing_methods.append("isolation_forest")
                anomaly_types.append("multivariate_access_anomaly")

            # Method 3: Rule-based Heuristics Gate
            rule_flags = []
            if metrics["failed_count"] >= 3:
                rule_flags.append("failed_login_burst")
            if metrics["suspicious_geo_count"] > 0:
                rule_flags.append("off_hours_geo_shift")
            if metrics["unknown_device_count"] > 0:
                rule_flags.append("unrecognized_device")

            if rule_flags:
                agreeing_methods.append("rule_heuristics")
                anomaly_types.extend(rule_flags)

            # Multi-confirm gate: REQUIRES 2+ methods to agree
            if len(agreeing_methods) >= 2:
                confidence = min(0.80 + (len(agreeing_methods) - 2) * 0.10, 0.99)
                primary_type = anomaly_types[0] if anomaly_types else "multivariate_access_anomaly"
                evt_ids = [e.get("event_id", "") for e in evts]
                
                finding = AnomalyFinding(
                    finding_id=f"ANOM-{uid[:8]}-{int(datetime.now(timezone.utc).timestamp())}",
                    anomaly_type=primary_type,
                    user_id=uid,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    confidence=round(confidence, 2),
                    description=f"Multi-confirm access anomaly for user '{uid}'. Agreed methods: {', '.join(agreeing_methods)}.",
                    methods_agreed=agreeing_methods,
                    raw_metrics=metrics,
                    event_ids=evt_ids,
                    is_anomaly=True
                )
                findings.append(finding)

        self.logger.info("anomalies_detected", total_users_analyzed=len(user_groups), anomalies_found=len(findings))
        return findings

    def _extract_user_features(self, events: List[Dict[str, Any]]) -> List[float]:
        """Extract numerical features for Isolation Forest."""
        total = len(events)
        failed = sum(1 for e in events if e.get("event_type") == "failed_login" or e.get("status") == "failed")
        failed_ratio = failed / float(total) if total > 0 else 0.0
        
        suspicious_locs = {"RU-Moscow", "CN-Shanghai", "KP-Pyongyang", "UNKNOWN-PROXY", "TOR-EXIT-NODE"}
        suspicious_devices = {"Python-urllib/3.10", "Curl/7.68.0", "Unrecognized-Android-OS", "Automated-Script-v1"}

        loc_score = sum(1 for e in events if e.get("location") in suspicious_locs)
        device_score = sum(1 for e in events if e.get("device_info") in suspicious_devices)

        return [float(total), failed_ratio, float(loc_score), float(device_score)]

    def _extract_user_metrics(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract summary metrics for a user's events."""
        suspicious_locs = {"RU-Moscow", "CN-Shanghai", "KP-Pyongyang", "UNKNOWN-PROXY", "TOR-EXIT-NODE"}
        suspicious_devices = {"Python-urllib/3.10", "Curl/7.68.0", "Unrecognized-Android-OS", "Automated-Script-v1"}

        failed_cnt = sum(1 for e in events if e.get("event_type") == "failed_login" or e.get("status") == "failed")
        susp_geo_cnt = sum(1 for e in events if e.get("location") in suspicious_locs)
        unk_dev_cnt = sum(1 for e in events if e.get("device_info") in suspicious_devices)

        return {
            "total_attempts": len(events),
            "failed_count": failed_cnt,
            "suspicious_geo_count": susp_geo_cnt,
            "unknown_device_count": unk_dev_cnt,
            "unique_ips": len(set(e.get("ip_address", "") for e in events)),
        }
