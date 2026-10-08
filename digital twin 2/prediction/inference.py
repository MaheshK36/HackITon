import pandas as pd
from typing import Dict, Any, List, Optional
from prediction.base import BasePredictor
from prediction.baseline import BaselinePredictor
from prediction.temporal_model import DeepTemporalPredictor
from mitre.attack_mapping import MitreMapper
from preprocessing.windowing import RollingStateBuffer, TimeWindow

class InferencePipeline:
    """Unified inference engine managing models, feature attribution, and MITRE mapping."""
    def __init__(self, model_type: str = "baseline", json_mitre_path: str = "mitre/techniques.json"):
        self.mitre_mapper = MitreMapper(json_mitre_path)
        self.rolling_buffer = RollingStateBuffer(maxlen=5)
        self.model_type = model_type
        self.predictor: BasePredictor = self._init_predictor(model_type)

    def _init_predictor(self, model_type: str) -> BasePredictor:
        if model_type.lower() == "deep_learning":
            return DeepTemporalPredictor()
        else:
            predictor = BaselinePredictor()
            # Train baseline on generated raw data if available
            try:
                import os
                if os.path.exists("data/raw/scenario_a_recon_bruteforce_exfil.csv"):
                    df_a = pd.read_csv("data/raw/scenario_a_recon_bruteforce_exfil.csv")
                    df_b = pd.read_csv("data/raw/scenario_b_dos_command_exec.csv") if os.path.exists("data/raw/scenario_b_dos_command_exec.csv") else df_a
                    predictor.train_on_datasets([df_a, df_b])
            except Exception as e:
                pass
            return predictor

    def switch_model(self, model_type: str):
        self.model_type = model_type
        self.predictor = self._init_predictor(model_type)

    def process_window(self, window: TimeWindow) -> Dict[str, Any]:
        """
        Runs complete inference pipeline for a time window:
          1. Current technique detection + feature attribution
          2. Transparent MITRE ATT&CK mapping
          3. Next-stage forecasting over rolling history
          4. Per-host technique detections
        """
        feats = window.features
        raw_label, conf, feature_explanations = self.predictor.predict_current_stage(feats)

        current_mitre = self.mitre_mapper.map_current_detection(raw_label, conf)

        # Update rolling buffer
        self.rolling_buffer.append({
            "timestamp": window.end_time,
            "label": raw_label,
            "features": feats
        })

        # Forecast next stage
        history = self.rolling_buffer.get_history()
        raw_next_probs = self.predictor.predict_next_stage(history)
        predicted_mitre = self.mitre_mapper.map_predictions(raw_next_probs)

        # Per-host detections
        per_host_mitre = {}
        for host_ip, hfeats in window.host_features.items():
            h_label, h_conf, _ = self.predictor.predict_current_stage(hfeats)
            per_host_mitre[host_ip] = self.mitre_mapper.map_current_detection(h_label, h_conf)

        return {
            "timestamp": window.end_time,
            "raw_detected_label": raw_label,
            "current_detection": current_mitre,
            "feature_explanations": feature_explanations,
            "next_predictions": predicted_mitre,
            "per_host_detections": per_host_mitre,
            "active_model_name": self.predictor.model_name
        }
