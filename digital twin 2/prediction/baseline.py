import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from sklearn.ensemble import RandomForestClassifier
from prediction.base import BasePredictor
from prediction.transition_model import MarkovTransitionModel
from preprocessing.feature_engineering import FEATURE_NAMES, extract_window_features
from preprocessing.flow_extractor import FlowRecord

class BaselineClassifier:
    """Random Forest Classifier for current attack technique detection."""
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=50, random_state=42)
        self.classes_ = np.array(["BENIGN"])
        self.is_fitted = False

    def train_on_data(self, df: pd.DataFrame):
        """Train classifier using flow dataframe with ground truth labels."""
        X_rows = []
        y_rows = []

        labels = df["label"].unique()
        for label in labels:
            sub_df = df[df["label"] == label]
            records = sub_df.to_dict(orient="records")
            flows = [FlowRecord.from_dict(r) for r in records]
            
            chunk_size = 10
            for i in range(0, len(flows), chunk_size):
                chunk = flows[i:i+chunk_size]
                if chunk:
                    feats = extract_window_features(chunk, window_sec=10.0)
                    X_rows.append([feats[name] for name in FEATURE_NAMES])
                    y_rows.append(label)

        if len(X_rows) > 0:
            X = np.array(X_rows)
            y = np.array(y_rows)
            self.model.fit(X, y)
            self.classes_ = self.model.classes_
            self.is_fitted = True

    def predict(self, features: Dict[str, float]) -> Tuple[str, float, Dict[str, float]]:
        if not self.is_fitted:
            return "BENIGN", 1.0, {name: 0.1 for name in FEATURE_NAMES[:3]}

        # Check domain heuristic for clear benign traffic (low port count, low rates)
        ports = features.get("unique_dst_ports", 1.0)
        pkt_rate = features.get("pkt_rate", 0.0)
        syn_ratio = features.get("syn_ratio", 0.0)
        byte_rate = features.get("byte_rate", 0.0)

        x_vec = np.array([[features.get(name, 0.0) for name in FEATURE_NAMES]])
        probs = self.model.predict_proba(x_vec)[0]
        max_idx = int(np.argmax(probs))
        label = str(self.classes_[max_idx])
        conf = float(probs[max_idx])

        # If model predicts attack but key attack indicators are absent, fall back to BENIGN
        if label != "BENIGN":
            if label == "PortScan" and ports < 5.0:
                label, conf = "BENIGN", 0.90
            elif label == "DoS" and pkt_rate < 150.0:
                label, conf = "BENIGN", 0.90
            elif label == "BruteForce" and (syn_ratio < 0.5 or pkt_rate < 20.0):
                label, conf = "BENIGN", 0.90
            elif label == "DataExfiltration" and byte_rate < 50000.0:
                label, conf = "BENIGN", 0.90

        # Compute feature attribution via tree feature importances & sample values
        importances = self.model.feature_importances_
        raw_vals = np.array([features.get(name, 0.0) for name in FEATURE_NAMES])
        norm_vals = raw_vals / (np.linalg.norm(raw_vals) + 1e-6)
        attributions = importances * (np.abs(norm_vals) + 0.1)
        attribution_dict = {
            name: float(attributions[i])
            for i, name in enumerate(FEATURE_NAMES)
        }

        sorted_attrs = dict(sorted(attribution_dict.items(), key=lambda x: x[1], reverse=True)[:5])
        return label, conf, sorted_attrs


class BaselinePredictor(BasePredictor):
    """
    Baseline predictor combining Random Forest Classifier for current stage
    detection and Markov Chain transition model for next stage prediction.
    """
    def __init__(self):
        self.classifier = BaselineClassifier()
        self.transition_model = MarkovTransitionModel()

    @property
    def model_name(self) -> str:
        return "Baseline Model (Random Forest + Markov Transition)"

    def train_on_datasets(self, dataframes: List[pd.DataFrame]):
        """Train classifier and Markov model on sample datasets."""
        combined_df = pd.concat(dataframes, ignore_index=True)
        self.classifier.train_on_data(combined_df)
        
        # Fit sequences
        sequences = []
        for df in dataframes:
            seq = list(df["label"].drop_duplicates())
            sequences.append(seq)
        self.transition_model.fit_from_sequences(sequences)

    def predict_current_stage(self, features: Dict[str, float]) -> Tuple[str, float, Dict[str, float]]:
        return self.classifier.predict(features)

    def predict_next_stage(self, history: List[Dict[str, Any]]) -> List[Tuple[str, float]]:
        stage_history = [h.get("label", "BENIGN") for h in history]
        current_stage = stage_history[-1] if stage_history else "BENIGN"
        return self.transition_model.predict_next_stage_probs(current_stage, stage_history)
