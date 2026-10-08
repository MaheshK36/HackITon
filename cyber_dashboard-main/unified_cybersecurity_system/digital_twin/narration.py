"""
narration.py - Sentinel-WM Live Narration

Explanation and prediction narration module for Sentinel-WM Digital Twin.
Transforms actual model output numbers into dynamic, live step-by-step security reports.
"""

from typing import List, Dict, Any, Optional


class TrajectoryNarrator:
    """
    Generates dynamic, model-driven natural language explanations for live streaming frames and rollouts.
    """

    def __init__(self, min_confidence: float = 0.4) -> None:
        self.min_confidence = min_confidence

    def narrate_step(self, step_data: Dict[str, Any]) -> str:
        step = step_data["step"]
        target_name = step_data.get("target_hostname", "Target-Host")
        target_ip = step_data.get("target_ip", "Target-IP")
        stage = step_data["predicted_stage"]
        conf = step_data["stage_confidence"] * 100
        inf_prob = step_data["infiltration_probability"]
        inf_pct = inf_prob * 100

        if inf_prob >= 0.85:
            icon = "[CRITICAL EXFILTRATION]"
        elif inf_prob >= 0.50:
            icon = "[ELEVATED LATERAL RISK]"
        elif inf_prob >= 0.25:
            icon = "[INITIAL ACCESS DETECTED]"
        else:
            icon = "[LOW RISK / RECONNAISSANCE]"

        warning = ""
        if step_data["stage_confidence"] < self.min_confidence:
            warning = f" [!] (Low Confidence: {conf:.1f}%)"

        return (
            f"[STEP {step}] {icon} Target: {target_name} ({target_ip}) | "
            f"Stage: {stage} ({conf:.1f}% conf) | Infiltration Risk: {inf_pct:.1f}%{warning}"
        )

    def generate_summary(
        self,
        trajectory: List[Dict[str, Any]],
        stage_names: Optional[List[str]] = None,
    ) -> str:
        if not trajectory:
            return "[Sentinel-WM Alert] Empty trajectory provided. No simulation steps recorded."

        total_steps = len(trajectory)
        first_step = trajectory[0]
        last_step = trajectory[-1]

        start_stage = first_step["predicted_stage"]
        start_inf = first_step["infiltration_probability"]
        end_inf = last_step["infiltration_probability"]

        transitions: List[Dict[str, Any]] = []
        prev_stage: Optional[str] = None
        low_confidence_steps: List[int] = []

        for step_data in trajectory:
            step_num = step_data["step"]
            stage = step_data["predicted_stage"]
            conf = step_data["stage_confidence"]
            inf_prob = step_data["infiltration_probability"]

            if conf < self.min_confidence:
                low_confidence_steps.append(step_num)

            if stage != prev_stage:
                transitions.append({
                    "step": step_num,
                    "target": step_data.get("target_hostname", "Host"),
                    "stage": stage,
                    "confidence": conf,
                    "infiltration_prob": inf_prob,
                })
                prev_stage = stage

        transition_phrases = []
        for trans in transitions:
            conf_pct = trans["confidence"] * 100
            inf_pct = trans["infiltration_prob"] * 100
            phrase = f"{trans['stage']} on {trans['target']} (step {trans['step']}, {conf_pct:.1f}% conf, risk {inf_pct:.1f}%)"
            transition_phrases.append(phrase)

        transition_chain = " -> ".join(transition_phrases)

        critical_step: Optional[int] = None
        for step_data in trajectory:
            if step_data["predicted_stage"].lower() == "exfiltration" or step_data["infiltration_probability"] >= 0.85:
                critical_step = step_data["step"]
                break

        inf_change = (end_inf - start_inf) * 100
        trend_str = f"escalating by +{inf_change:.1f}%" if inf_change >= 0 else f"decreasing by {inf_change:.1f}%"

        lines = [
            "=" * 74,
            "      [SENTINEL-WM DIGITAL TWIN REAL-TIME SIMULATION REPORT]",
            "=" * 74,
            f"Rollout Horizon: {total_steps} steps | Baseline Stage: {start_stage} (Infiltration Risk: {start_inf * 100:.1f}%)",
            "-" * 74,
            "ATTACK PATH TRAJECTORY PREDICTION:",
            f"  {transition_chain}",
            "",
            "DYNAMICS & RISK SUMMARY:",
            f"  - Infiltration probability is {trend_str} over the {total_steps}-step simulation horizon.",
        ]

        if critical_step is not None:
            lines.append(f"  - CRITICAL ALERT: Model predicts critical escalation threshold reached at step {critical_step}.")
        else:
            lines.append(f"  - STABLE: No critical exfiltration stage predicted within the {total_steps}-step window.")

        if low_confidence_steps:
            steps_str = ", ".join(map(str, low_confidence_steps))
            lines.extend([
                "",
                f"[WARNING] Low confidence (<{self.min_confidence * 100:.0f}%) detected at step(s): {steps_str}.",
                "  Trajectory predictions carry higher uncertainty beyond these points.",
            ])

        lines.append("=" * 74)
        return "\n".join(lines)


def generate_explanation(
    trajectory: List[Dict[str, Any]],
    stage_names: Optional[List[str]] = None,
    min_confidence: float = 0.4,
) -> str:
    narrator = TrajectoryNarrator(min_confidence=min_confidence)
    return narrator.generate_summary(trajectory, stage_names=stage_names)
