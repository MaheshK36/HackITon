"""
ml_engine.py - Machine Learning Engine for Threat Classification & Stage Forecasting

Provides:
  1. Real, trained Random Forest classifier for current stage detection.
  2. Markov Chain transition model for sequence progression prediction.
  3. Feature attribution (explainability) for top contributing flow metrics.
  4. Explicit MITRE ATT&CK technique mapping.
  5. Transparent fallback handling when no trained model checkpoint exists.
"""

from __future__ import annotations

import os
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, confusion_matrix
from sklearn.model_selection import train_test_split

FEATURE_NAMES = [
    "flow_count",
    "avg_duration",
    "pkt_rate",
    "byte_rate",
    "syn_ratio",
    "rst_ratio",
    "unique_dst_ports",
    "unique_dst_ips",
    "max_pkt_per_flow",
    "avg_pkt_size"
]

MITRE_TECHNIQUE_MAP: Dict[str, Dict[str, str]] = {
    "PortScan": {
        "technique_id": "T1046",
        "name": "Network Service Discovery",
        "tactic": "Discovery",
        "description": "Adversary attempting to get a listing of services running on target hosts."
    },
    "BruteForce": {
        "technique_id": "T1110",
        "name": "Brute Force Authentication",
        "tactic": "Credential Access",
        "description": "Adversary repeatedly attempting credential combinations against administrative services."
    },
    "DoS": {
        "technique_id": "T1498",
        "name": "Network Denial of Service",
        "tactic": "Impact",
        "description": "Adversary flooding network resources to degrade or disrupt service availability."
    },
    "CommandExecution": {
        "technique_id": "T1059",
        "name": "Command and Scripting Interpreter",
        "tactic": "Execution",
        "description": "Adversary executing arbitrary system commands or reverse shells."
    },
    "DataExfiltration": {
        "technique_id": "T1041",
        "name": "Exfiltration Over C2 Channel",
        "tactic": "Exfiltration",
        "description": "Adversary stealing and transmitting sensitive data over an outbound channel."
    },
    "BENIGN": {
        "technique_id": "T0000",
        "name": "Benign Network Activity",
        "tactic": "Normal Operations",
        "description": "Legitimate baseline network operations within normal parameters."
    }
}

KNOWN_STAGES = ["BENIGN", "PortScan", "BruteForce", "DataExfiltration", "DoS", "CommandExecution"]


class MarkovTransitionModel:
    """Markov transition model for next attack technique forecasting."""
    def __init__(self):
        self.stages = KNOWN_STAGES
        self.n_stages = len(self.stages)
        self.stage_to_idx = {s: i for i, s in enumerate(self.stages)}
        self.transition_matrix = np.zeros((self.n_stages, self.n_stages))
        self._init_domain_priors()

    def _init_domain_priors(self):
        priors = [
            ("BENIGN", "PortScan", 0.45), ("BENIGN", "DoS", 0.25), ("BENIGN", "BENIGN", 0.30),
            ("PortScan", "BruteForce", 0.50), ("PortScan", "DoS", 0.30), ("PortScan", "BENIGN", 0.20),
            ("BruteForce", "CommandExecution", 0.50), ("BruteForce", "DataExfiltration", 0.30), ("BruteForce", "BENIGN", 0.20),
            ("DoS", "CommandExecution", 0.60), ("DoS", "BENIGN", 0.40),
            ("CommandExecution", "DataExfiltration", 0.70), ("CommandExecution", "BENIGN", 0.30),
            ("DataExfiltration", "BENIGN", 0.80), ("DataExfiltration", "DataExfiltration", 0.20),
        ]
        for src, dst, p in priors:
            if src in self.stage_to_idx and dst in self.stage_to_idx:
                self.transition_matrix[self.stage_to_idx[src], self.stage_to_idx[dst]] = p

    def fit_from_sequences(self, sequences: List[List[str]]):
        counts = np.zeros((self.n_stages, self.n_stages))
        for seq in sequences:
            for i in range(len(seq) - 1):
                s_curr = seq[i]
                s_next = seq[i+1]
                if s_curr in self.stage_to_idx and s_next in self.stage_to_idx:
                    counts[self.stage_to_idx[s_curr], self.stage_to_idx[s_next]] += 1.0

        row_sums = counts.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        self.transition_matrix = counts / row_sums

    def predict_next_stage_probs(self, current_stage: str, history: List[str] | None = None) -> List[Tuple[str, float]]:
        if current_stage not in self.stage_to_idx:
            current_stage = "BENIGN"
        idx = self.stage_to_idx[current_stage]
        probs = self.transition_matrix[idx].copy()

        if history and len(history) >= 2:
            prev_stage = history[-2]
            if prev_stage in self.stage_to_idx:
                prev_idx = self.stage_to_idx[prev_stage]
                probs = 0.6 * probs + 0.4 * self.transition_matrix[prev_idx]

        norm_sum = np.sum(probs)
        if norm_sum > 0:
            probs = probs / norm_sum
        else:
            probs = np.ones(self.n_stages) / self.n_stages

        results = [(self.stages[i], float(probs[i])) for i in range(self.n_stages)]
        results.sort(key=lambda x: x[1], reverse=True)
        return results


class MLEngine:
    """Central ML service managing model artifacts, feature attribution, and inference."""

    def __init__(self, model_path: Optional[str | Path] = None):
        self.classifier: Optional[RandomForestClassifier] = None
        self.transition_model = MarkovTransitionModel()
        self.metrics: Dict[str, Any] = {}
        self.model_version: str = "unloaded"
        self.is_loaded: bool = False
        self.feature_names = FEATURE_NAMES
        self.recent_history: List[str] = []

        if model_path:
            self.load_model(model_path)

    def load_model(self, model_path: str | Path) -> bool:
        path = Path(model_path)
        if not path.exists():
            return False

        try:
            with open(path, "rb") as f:
                artifact = pickle.load(f)

            self.classifier = artifact["classifier"]
            self.transition_model = artifact.get("transition_model", MarkovTransitionModel())
            self.metrics = artifact.get("metrics", {})
            self.model_version = artifact.get("version", "rf-baseline-v1")
            self.is_loaded = True
            return True
        except Exception:
            self.is_loaded = False
            return False

    def extract_features_from_dict(self, event_data: Dict[str, Any]) -> np.ndarray:
        """Extracts canonical 10-dim flow feature vector from event data."""
        metadata = event_data.get("metadata", {})
        duration = float(event_data.get("duration", metadata.get("duration", 0.0)) or 0.0)
        packets = float(event_data.get("packets", metadata.get("tot_pkts", 1)) or 1.0)
        byte_count = float(event_data.get("bytes", metadata.get("tot_bytes", 0)) or 0.0)
        eff_duration = max(duration, 0.001)

        pkt_rate = packets / eff_duration
        byte_rate = byte_count / eff_duration

        syn_flag = float(metadata.get("syn_flag_count", metadata.get("SYN Flag Count", 0)) or 0)
        rst_flag = float(metadata.get("rst_flag_count", metadata.get("RST Flag Count", 0)) or 0)
        syn_ratio = min(1.0, syn_flag / max(packets, 1.0))
        rst_ratio = min(1.0, rst_flag / max(packets, 1.0))

        dst_port = float(event_data.get("destination_port", metadata.get("dst_port", 0)) or 0)
        unique_dst_ports = float(metadata.get("unique_dst_ports", 1.0))
        unique_dst_ips = float(metadata.get("unique_dst_ips", 1.0))

        if bool(metadata.get("port_scan", False)):
            unique_dst_ports = max(unique_dst_ports, 15.0)

        max_pkt = float(metadata.get("max_pkt_per_flow", packets))
        avg_pkt_size = byte_count / max(packets, 1.0)

        feature_map = {
            "flow_count": float(metadata.get("flow_count", 1.0)),
            "avg_duration": duration,
            "pkt_rate": pkt_rate,
            "byte_rate": byte_rate,
            "syn_ratio": syn_ratio,
            "rst_ratio": rst_ratio,
            "unique_dst_ports": unique_dst_ports,
            "unique_dst_ips": unique_dst_ips,
            "max_pkt_per_flow": max_pkt,
            "avg_pkt_size": avg_pkt_size
        }

        return np.array([[feature_map[f] for f in self.feature_names]], dtype=np.float32)

    def predict(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes genuine ML inference:
          - Random Forest classification of current attack technique.
          - Feature attributions calculated from tree importances.
          - Markov model next-stage forecasting.
          - MITRE ATT&CK technique mapping.
        """
        if not self.is_loaded or self.classifier is None:
            # Explicit, transparent fallback indicator
            return {
                "inference_mode": "HEURISTIC_FALLBACK",
                "current_state": "Benign",
                "confidence": 0.50,
                "mitre_technique": MITRE_TECHNIQUE_MAP["BENIGN"],
                "predicted_next_state": "Benign",
                "next_stage_probabilities": [],
                "feature_explanations": {"reason": "No trained ML model checkpoint is currently registered."},
                "model_version": "heuristic-fallback-v1"
            }

        X = self.extract_features_from_dict(event_data)
        probs = self.classifier.predict_proba(X)[0]
        classes = self.classifier.classes_
        max_idx = int(np.argmax(probs))
        predicted_label = str(classes[max_idx])
        confidence = float(probs[max_idx])

        # Feature Attribution (Feature Importance * Normalized Input Value)
        importances = self.classifier.feature_importances_
        raw_vals = X[0]
        norm_vals = raw_vals / (np.linalg.norm(raw_vals) + 1e-6)
        attributions = importances * (np.abs(norm_vals) + 0.1)
        attribution_dict = {
            name: round(float(attributions[i]), 4)
            for i, name in enumerate(self.feature_names)
        }
        sorted_attributions = dict(sorted(attribution_dict.items(), key=lambda x: x[1], reverse=True)[:5])

        # Update history and predict next stage with Markov model
        self.recent_history.append(predicted_label)
        if len(self.recent_history) > 10:
            self.recent_history.pop(0)

        next_probs = self.transition_model.predict_next_stage_probs(predicted_label, self.recent_history)
        top_next_stage = next_probs[0][0] if next_probs else "BENIGN"

        mitre_info = MITRE_TECHNIQUE_MAP.get(predicted_label, MITRE_TECHNIQUE_MAP["BENIGN"])
        next_mitre_info = MITRE_TECHNIQUE_MAP.get(top_next_stage, MITRE_TECHNIQUE_MAP["BENIGN"])

        next_probabilities_list = [
            {
                "stage": stage,
                "probability": round(prob, 4),
                "technique_id": MITRE_TECHNIQUE_MAP.get(stage, {}).get("technique_id", "T0000"),
                "technique_name": MITRE_TECHNIQUE_MAP.get(stage, {}).get("name", stage)
            }
            for stage, prob in next_probs if stage != "BENIGN" or prob >= 0.20
        ]

        return {
            "inference_mode": "TRAINED_MODEL_INFERENCE",
            "current_state": predicted_label,
            "confidence": round(confidence, 3),
            "mitre_technique": mitre_info,
            "predicted_next_state": top_next_stage,
            "predicted_next_technique": next_mitre_info,
            "next_stage_probabilities": next_probabilities_list,
            "feature_explanations": sorted_attributions,
            "model_version": self.model_version
        }

    def train_baseline_model(self, data_sources: List[pd.DataFrame], output_path: str | Path) -> Dict[str, Any]:
        """
        Trains and serializes Random Forest + Markov Transition models.
        Computes genuine evaluation metrics: Accuracy, Precision, Recall, F1.
        """
        combined = pd.concat(data_sources, ignore_index=True)
        if "label" not in combined.columns:
            raise ValueError("Training dataset must contain a 'label' column.")

        X_list = []
        y_list = []

        for _, row in combined.iterrows():
            flow_dict = row.to_dict()
            x_vec = self.extract_features_from_dict(flow_dict)[0]
            X_list.append(x_vec)
            y_list.append(str(row["label"]))

        X = np.array(X_list)
        y = np.array(y_list)

        # Train/Test Split with stratify if feasible
        try:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
        except ValueError:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

        clf = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)
        clf.fit(X_train, y_train)

        # Compute genuine evaluation metrics on held-out test data
        y_pred = clf.predict(X_test)
        labels = sorted(list(set(y_test) | set(y_pred)))

        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
        rec = float(recall_score(y_test, y_pred, average="macro", zero_division=0))
        f1 = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
        cm = confusion_matrix(y_test, y_pred, labels=labels).tolist()

        # Fit sequence transitions
        sequences = []
        for df in data_sources:
            seq = list(df["label"].drop_duplicates())
            sequences.append(seq)

        trans_model = MarkovTransitionModel()
        trans_model.fit_from_sequences(sequences)

        metrics = {
            "accuracy": round(acc, 4),
            "macro_precision": round(prec, 4),
            "macro_recall": round(rec, 4),
            "macro_f1": round(f1, 4),
            "total_samples": len(X),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "classes": labels,
            "confusion_matrix": cm,
            "trained_at": datetime.now(timezone.utc).isoformat()
        }

        artifact = {
            "classifier": clf,
            "transition_model": trans_model,
            "feature_names": self.feature_names,
            "metrics": metrics,
            "version": "rf-baseline-v1.0"
        }

        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as f:
            pickle.dump(artifact, f)

        # Update current engine state
        self.classifier = clf
        self.transition_model = trans_model
        self.metrics = metrics
        self.model_version = "rf-baseline-v1.0"
        self.is_loaded = True

        return metrics
