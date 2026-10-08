import numpy as np
from typing import List, Dict, Tuple, Any

KNOWN_TECHNIQUE_STAGES = [
    "BENIGN",
    "PortScan",
    "BruteForce",
    "DataExfiltration",
    "DoS",
    "CommandExecution"
]

class MarkovTransitionModel:
    """Markov chain sequence model for forecasting next attack technique stage."""
    def __init__(self):
        self.stages = KNOWN_TECHNIQUE_STAGES
        self.n_stages = len(self.stages)
        self.stage_to_idx = {s: i for i, s in enumerate(self.stages)}
        
        # Initialize default transition matrix based on domain cyberattack lifecycles
        # Row: Current Stage, Col: Next Stage
        self.transition_matrix = np.zeros((self.n_stages, self.n_stages))
        self._init_domain_priors()

    def _init_domain_priors(self):
        # BENIGN -> PortScan (0.4), DoS (0.3), BENIGN (0.3)
        self._set_trans("BENIGN", "PortScan", 0.45)
        self._set_trans("BENIGN", "DoS", 0.25)
        self._set_trans("BENIGN", "BENIGN", 0.30)

        # PortScan -> BruteForce (0.5), DoS (0.3), BENIGN (0.2)
        self._set_trans("PortScan", "BruteForce", 0.50)
        self._set_trans("PortScan", "DoS", 0.30)
        self._set_trans("PortScan", "BENIGN", 0.20)

        # BruteForce -> CommandExecution (0.5), DataExfiltration (0.3), BENIGN (0.2)
        self._set_trans("BruteForce", "CommandExecution", 0.50)
        self._set_trans("BruteForce", "DataExfiltration", 0.30)
        self._set_trans("BruteForce", "BENIGN", 0.20)

        # DoS -> CommandExecution (0.6), BENIGN (0.4)
        self._set_trans("DoS", "CommandExecution", 0.60)
        self._set_trans("DoS", "BENIGN", 0.40)

        # CommandExecution -> DataExfiltration (0.7), BENIGN (0.3)
        self._set_trans("CommandExecution", "DataExfiltration", 0.70)
        self._set_trans("CommandExecution", "BENIGN", 0.30)

        # DataExfiltration -> BENIGN (0.8), DataExfiltration (0.2)
        self._set_trans("DataExfiltration", "BENIGN", 0.80)
        self._set_trans("DataExfiltration", "DataExfiltration", 0.20)

    def _set_trans(self, src: str, dst: str, prob: float):
        if src in self.stage_to_idx and dst in self.stage_to_idx:
            self.transition_matrix[self.stage_to_idx[src], self.stage_to_idx[dst]] = prob

    def fit_from_sequences(self, sequences: List[List[str]]):
        """Fit empirical transition probabilities from sequence dataset."""
        counts = np.zeros((self.n_stages, self.n_stages))
        for seq in sequences:
            for i in range(len(seq) - 1):
                s_curr = seq[i]
                s_next = seq[i+1]
                if s_curr in self.stage_to_idx and s_next in self.stage_to_idx:
                    counts[self.stage_to_idx[s_curr], self.stage_to_idx[s_next]] += 1.0

        # Normalize rows
        row_sums = counts.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        self.transition_matrix = counts / row_sums

    def predict_next_stage_probs(self, current_stage: str, history: List[str] = None) -> List[Tuple[str, float]]:
        """Given current stage (and optional history window), forecast next stage probabilities."""
        if current_stage not in self.stage_to_idx:
            current_stage = "BENIGN"

        idx = self.stage_to_idx[current_stage]
        probs = self.transition_matrix[idx]

        # Condition on history if provided (boosting sequence persistence)
        if history and len(history) >= 2:
            prev_stage = history[-2]
            if prev_stage in self.stage_to_idx:
                prev_idx = self.stage_to_idx[prev_stage]
                # Combine first order and second order transition probabilities
                probs = 0.6 * probs + 0.4 * self.transition_matrix[prev_idx]

        norm_sum = np.sum(probs)
        if norm_sum > 0:
            probs = probs / norm_sum
        else:
            probs = np.ones(self.n_stages) / self.n_stages

        results = [(self.stages[i], float(probs[i])) for i in range(self.n_stages)]
        results.sort(key=lambda x: x[1], reverse=True)
        return results
