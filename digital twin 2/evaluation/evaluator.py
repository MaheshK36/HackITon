from typing import List, Dict, Any
import pandas as pd
from evaluation.metrics import compute_classification_metrics, compute_lead_time

class SystemEvaluator:
    """Evaluates progression predictions against ground truth telemetry."""
    def __init__(self, lead_time_prob_threshold: float = 0.60):
        self.lead_time_threshold = lead_time_prob_threshold
        self.prediction_logs: List[Dict[str, Any]] = []
        self.actual_observations: List[Dict[str, Any]] = []
        self.y_true: List[str] = []
        self.y_pred: List[str] = []

    def record_window_event(
        self,
        timestamp: float,
        ground_truth_label: str,
        detected_label: str,
        detection_info: Dict[str, Any],
        ranked_predictions: List[Dict[str, Any]]
    ):
        """Records window model outputs and ground truth labels for scoring."""
        self.y_true.append(ground_truth_label)
        self.y_pred.append(detected_label)

        self.actual_observations.append({
            "timestamp": timestamp,
            "name": detection_info.get("name"),
            "state": detection_info.get("state")
        })

        self.prediction_logs.append({
            "timestamp": timestamp,
            "detected_label": detected_label,
            "predictions": ranked_predictions
        })

    def compute_evaluation_report(self) -> Dict[str, Any]:
        """Calculates live metrics: Precision, Recall, F1, Accuracy, Top-1/Top-3, Lead Time."""
        cls_metrics = compute_classification_metrics(self.y_true, self.y_pred)
        lead_time_info = compute_lead_time(
            self.prediction_logs,
            self.actual_observations,
            prob_threshold=self.lead_time_threshold
        )

        # Top-1 and Top-3 accuracy
        top1_hits = 0
        top3_hits = 0
        total_eval = 0

        for i in range(len(self.prediction_logs) - 1):
            preds = [p["name"] for p in self.prediction_logs[i]["predictions"]]
            actual_next = self.actual_observations[i+1]["name"]
            if actual_next and actual_next != "Benign Network Activity":
                total_eval += 1
                if len(preds) > 0 and preds[0] == actual_next:
                    top1_hits += 1
                if actual_next in preds[:3]:
                    top3_hits += 1

        top1_acc = float(top1_hits) / max(total_eval, 1)
        top3_acc = float(top3_hits) / max(total_eval, 1)

        return {
            "classification": cls_metrics,
            "top1_accuracy": top1_acc,
            "top3_accuracy": top3_acc,
            "lead_time": lead_time_info,
            "total_windows_evaluated": len(self.y_true)
        }

    def clear(self):
        self.prediction_logs.clear()
        self.actual_observations.clear()
        self.y_true.clear()
        self.y_pred.clear()
