import json
import os
import logging
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MitreMapper")

TECHNIQUE_LABEL_MAP = {
    "PortScan": "T1046",
    "BruteForce": "T1110",
    "DoS": "T1498",
    "CommandExecution": "T1059",
    "DataExfiltration": "T1041",
    "BENIGN": "T0000"
}

class MitreMapper:
    """Documented and transparent mapping layer connecting model output to MITRE ATT&CK techniques."""
    def __init__(self, json_path: str = "mitre/techniques.json"):
        self.techniques = {}
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                self.techniques = json.load(f)
        else:
            logger.warning(f"Techniques JSON not found at {json_path}. Using fallback map.")

    def get_technique_info(self, label: str) -> Dict[str, Any]:
        tech_id = TECHNIQUE_LABEL_MAP.get(label, "T0000")
        info = self.techniques.get(tech_id, {
            "technique_id": tech_id,
            "name": label,
            "tactic": "Unknown",
            "description": "No metadata available."
        })
        return info

    def map_current_detection(self, label: str, confidence: float) -> Dict[str, Any]:
        """
        Maps current window detection to MITRE technique with state:
          - OBSERVED (conf >= 0.70)
          - SUSPECTED (0.35 <= conf < 0.70)
          - BENIGN/UNKNOWN (if label == 'BENIGN' or conf < 0.35)
        """
        info = self.get_technique_info(label)
        if label == "BENIGN" or confidence < 0.35:
            state = "BENIGN"
        elif confidence >= 0.70:
            state = "OBSERVED"
        else:
            state = "SUSPECTED"

        mapping_reason = f"Label '{label}' mapped to {info['technique_id']} ({info['name']}) with state {state} based on model confidence {confidence:.2f} (thresholds: 0.70 for OBSERVED, 0.35 for SUSPECTED)."
        logger.debug(mapping_reason)

        return {
            "technique_id": info["technique_id"],
            "name": info["name"],
            "tactic": info["tactic"],
            "state": state,
            "confidence": confidence,
            "mapping_reason": mapping_reason
        }

    def map_predictions(self, ranked_predictions: List[tuple]) -> List[Dict[str, Any]]:
        """
        Maps next-stage probability forecasts to PREDICTED MITRE techniques.
        """
        predicted_items = []
        for label, prob in ranked_predictions:
            if label == "BENIGN" or prob < 0.15:
                continue
            info = self.get_technique_info(label)
            predicted_items.append({
                "technique_id": info["technique_id"],
                "name": info["name"],
                "tactic": info["tactic"],
                "state": "PREDICTED",
                "probability": prob,
                "mapping_reason": f"Forecasted next technique {info['technique_id']} with Markov probability {prob:.2f}."
            })
        return predicted_items
