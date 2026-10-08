from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple

class BasePredictor(ABC):
    """Abstract base predictor interface for swappable ML models."""
    
    @abstractmethod
    def predict_current_stage(self, features: Dict[str, float]) -> Tuple[str, float, Dict[str, float]]:
        """
        Returns:
            - predicted_label: str (e.g. 'BENIGN', 'PortScan', 'BruteForce')
            - confidence: float (0.0 - 1.0)
            - feature_importance_explanation: Dict[str, float] (top feature contributions)
        """
        pass

    @abstractmethod
    def predict_next_stage(self, history: List[Dict[str, Any]]) -> List[Tuple[str, float]]:
        """
        Returns:
            - ranked list of (next_stage_label, probability)
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the active model for UI display."""
        pass
