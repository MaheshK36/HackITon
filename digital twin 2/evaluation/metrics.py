import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score, confusion_matrix

def compute_classification_metrics(y_true: List[str], y_pred: List[str]) -> Dict[str, Any]:
    """Computes Precision, Recall, F1, Accuracy, and Confusion Matrix."""
    if not y_true or not y_pred:
        return {
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "labels": [],
            "confusion_matrix": []
        }

    labels = sorted(list(set(y_true + y_pred)))
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, average="macro", zero_division=0)
    rec = recall_score(y_true, y_pred, average="macro", zero_division=0)
    f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=labels).tolist()

    return {
        "accuracy": float(acc),
        "precision": float(prec),
        "recall": float(rec),
        "f1_score": float(f1),
        "labels": labels,
        "confusion_matrix": cm
    }

def compute_lead_time(
    prediction_logs: List[Dict[str, Any]],
    actual_observations: List[Dict[str, Any]],
    prob_threshold: float = 0.60
) -> Dict[str, Any]:
    """
    Computes Average Prediction Lead Time:
    Time between a technique's predicted probability first crossing threshold
    and that technique's actual OBSERVED timestamp (computed only over cases where both exist).
    """
    first_pred_time: Dict[str, float] = {}
    actual_obs_time: Dict[str, float] = {}

    # Extract first timestamp where prediction crossed threshold
    for log in prediction_logs:
        t = log.get("timestamp", 0.0)
        for pred in log.get("predictions", []):
            tech = pred.get("name")
            prob = pred.get("probability", 0.0)
            if prob >= prob_threshold and tech not in first_pred_time:
                first_pred_time[tech] = t

    # Extract first timestamp where technique was actually OBSERVED
    for obs in actual_observations:
        t = obs.get("timestamp", 0.0)
        tech = obs.get("name")
        state = obs.get("state")
        if state == "OBSERVED" and tech and tech != "Benign Network Activity" and tech not in actual_obs_time:
            actual_obs_time[tech] = t

    lead_times = []
    matched_details = []

    for tech, t_pred in first_pred_time.items():
        if tech in actual_obs_time:
            t_obs = actual_obs_time[tech]
            dt = t_obs - t_pred
            if dt >= 0:  # Valid positive lead time
                lead_times.append(dt)
                matched_details.append({
                    "technique": tech,
                    "first_predicted_time": t_pred,
                    "actual_observed_time": t_obs,
                    "lead_time_sec": dt
                })

    avg_lead_time = float(np.mean(lead_times)) if lead_times else 0.0
    return {
        "avg_lead_time_sec": avg_lead_time,
        "matched_cases_count": len(lead_times),
        "details": matched_details
    }
