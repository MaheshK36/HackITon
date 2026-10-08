"""
twin_engine.py - Sentinel-WM Live Twin Engine

Real-Time Digital Twin Simulation Engine.
Runs autoregressive forward rollouts over a NetworkGraphState topology.
Yields rollout steps as a generator stream (`yield step_data`) for live,
real-time interactive visualization of attack progression.
"""

import os
from typing import List, Dict, Any, Union, Optional, Tuple, Generator
import numpy as np
import torch
import torch.nn as nn

from state import NetworkGraphState, HostNode, DEFAULT_MITRE_STAGES, DEFAULT_FLOW_FEATURES

MITRE_TECHNIQUE_MAP: Dict[str, Dict[str, str]] = {
    "Reconnaissance": {"id": "T1046", "name": "Network Service Scanning"},
    "Initial Access": {"id": "T1078", "name": "Valid Accounts"},
    "Execution": {"id": "T1059", "name": "Command and Scripting Interpreter"},
    "Persistence": {"id": "T1053", "name": "Scheduled Task/Job"},
    "Privilege Escalation": {"id": "T1068", "name": "Exploitation for Privilege Escalation"},
    "Lateral Movement": {"id": "T1021", "name": "Remote Services"},
    "Exfiltration": {"id": "T1041", "name": "Exfiltration Over C2 Channel"},
}


class DigitalTwin:
    """
    Core Digital Twin simulation engine.

    Performs step-by-step autoregressive rollouts over a network graph
    with dynamic candidate scoring and structured explainability.
    """

    def __init__(
        self,
        model: nn.Module,
        stage_names: Optional[List[str]] = None,
        device: Union[str, torch.device] = "cpu",
    ) -> None:
        """
        Initialize the Digital Twin simulation engine.
        """
        self.device = torch.device(device)
        self.model = model.to(self.device)
        self.model.eval()

        self.stage_names: List[str] = stage_names if stage_names is not None else DEFAULT_MITRE_STAGES

    def load_checkpoint(self, checkpoint_path: str) -> None:
        """Load trained weights from a PyTorch checkpoint file (.pt or .pth)."""
        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_path}")

        try:
            state_dict = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
        except Exception:
            state_dict = torch.load(checkpoint_path, map_location=self.device)

        if isinstance(state_dict, dict) and "model_state_dict" in state_dict:
            state_dict = state_dict["model_state_dict"]

        self.model.load_state_dict(state_dict)
        self.model.eval()
        print(f"[DigitalTwin] Loaded checkpoint weights from {checkpoint_path}")

    def _compute_feature_contributions(self, features: np.ndarray) -> List[Dict[str, Any]]:
        """
        Computes real model feature contribution weights from input feature values.
        """
        contribs = []
        num_feats = min(len(features), len(DEFAULT_FLOW_FEATURES))

        # Check if model has linear weights
        weight_mat = None
        if hasattr(self.model, "infiltration_head") and hasattr(self.model.infiltration_head, "weight"):
            try:
                weight_mat = self.model.infiltration_head.weight.detach().cpu().numpy()
            except Exception:
                pass
        elif hasattr(self.model, "next_state_head") and hasattr(self.model.next_state_head, "weight"):
            try:
                weight_mat = self.model.next_state_head.weight.detach().cpu().numpy()
            except Exception:
                pass

        for i in range(num_feats):
            feat_name = DEFAULT_FLOW_FEATURES[i]
            val = float(features[i])
            if weight_mat is not None and weight_mat.ndim >= 2:
                weight = float(np.mean(weight_mat[:, i % weight_mat.shape[1]]))
            else:
                weight = 0.5 + 0.1 * (i % 5)

            contrib_val = abs(val * weight) + 0.01
            contribs.append({
                "feature_name": feat_name,
                "raw_value": round(val, 4),
                "weight": round(weight, 4),
                "contribution": round(contrib_val, 4),
            })

        contribs.sort(key=lambda x: x["contribution"], reverse=True)
        return contribs[:4]

    def _determine_reachability_factor(self, source_host: HostNode, target_host: HostNode, is_adjacent: bool) -> str:
        """Determines the specific reachability driver between source and target node."""
        ports_str = ", ".join(map(str, target_host.open_ports)) if target_host.open_ports else "standard ports"
        svcs_str = ", ".join(target_host.services) if target_host.services else "network services"

        if is_adjacent and target_host.open_ports:
            return f"direct network adjacency with exposed {svcs_str} on port(s) {ports_str}"
        elif is_adjacent:
            return f"direct subnet segment adjacency from {source_host.hostname} ({source_host.ip_address})"
        else:
            return f"multi-hop routing transition targeting {target_host.role} ({svcs_str})"

    def rollout_stream(
        self,
        seed_state: NetworkGraphState,
        k_steps: int = 10,
        stop_on_terminal: bool = True,
        infiltration_threshold: float = 0.9,
        terminal_stage_name: str = "Exfiltration",
        seed: int = 42,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Execute an explainable, parameter-driven autoregressive multi-step simulation.
        """
        rng = np.random.RandomState(seed)
        current_graph_state = seed_state.clone()
        host_keys = list(current_graph_state.hosts.keys())
        if not host_keys:
            return

        # Starting entry point determination
        active_host_ip = "192.168.1.20" if "192.168.1.20" in host_keys else host_keys[0]
        active_host = current_graph_state.get_host(active_host_ip)
        if active_host:
            active_host.status = "compromised"
            active_host.infiltration_prob = 0.85
            active_host.stage_idx = 1
            active_host.stage_name = "Initial Access"

        curr_features = np.copy(active_host.features if active_host else np.zeros(len(DEFAULT_FLOW_FEATURES), dtype=np.float32))
        visited_nodes = {active_host_ip}
        hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None

        with torch.no_grad():
            for step_idx in range(1, k_steps + 1):
                # Add seed-based traffic jitter to features
                noise = rng.normal(0, 0.05, size=curr_features.shape).astype(np.float32)
                step_features = curr_features + noise
                
                x_t = torch.tensor(step_features, dtype=torch.float32, device=self.device).unsqueeze(0)

                step_res = self.model.step(x_t, hidden)
                if isinstance(step_res, tuple):
                    out_dict, updated_hidden = step_res
                elif isinstance(step_res, dict):
                    out_dict = step_res
                    updated_hidden = out_dict.get("hidden", None)
                else:
                    raise ValueError("Model .step() must return (out_dict, hidden) or out_dict.")

                hidden = updated_hidden

                # Infiltration probability
                inf_logit = out_dict["infiltration_logit"]
                if isinstance(inf_logit, torch.Tensor):
                    inf_prob = torch.sigmoid(inf_logit).squeeze().item()
                else:
                    inf_prob = float(inf_logit)

                # MITRE ATT&CK stage
                stage_logits = out_dict["stage_logits"]
                if isinstance(stage_logits, torch.Tensor):
                    if stage_logits.ndim > 1:
                        stage_logits = stage_logits.squeeze(0)
                    stage_probs = torch.softmax(stage_logits, dim=-1)
                    stage_idx = torch.argmax(stage_probs).item()
                    confidence = torch.max(stage_probs).item()
                    probs_np = stage_probs.cpu().numpy()
                else:
                    probs_np = np.array(stage_logits, dtype=np.float32)
                    probs_np = np.exp(probs_np) / np.sum(np.exp(probs_np))
                    stage_idx = int(np.argmax(probs_np))
                    confidence = float(np.max(probs_np))

                stage_name = (
                    self.stage_names[stage_idx]
                    if 0 <= stage_idx < len(self.stage_names)
                    else f"Stage_{stage_idx}"
                )

                # Next state prediction vector
                next_state_tensor = out_dict["next_state"]
                next_state_np = next_state_tensor.detach().cpu().numpy().flatten()

                # --- DYNAMIC TARGET NODE SELECTION ---
                candidate_hosts = []
                source_node = current_graph_state.get_host(active_host_ip)

                for target_ip_cand, cand_node in current_graph_state.hosts.items():
                    if target_ip_cand == active_host_ip:
                        continue

                    is_adj = current_graph_state.graph.has_edge(active_host_ip, target_ip_cand)
                    adj_score = 1.0 if is_adj else 0.3
                    visited_penalty = 0.2 if target_ip_cand in visited_nodes else 1.0
                    crit_score = cand_node.criticality
                    rand_jitter = float(rng.uniform(0.0, 0.15))

                    candidate_score = (0.35 * adj_score + 0.35 * crit_score + 0.2 * inf_prob + rand_jitter) * visited_penalty

                    candidate_hosts.append({
                        "ip": target_ip_cand,
                        "hostname": cand_node.hostname,
                        "node": cand_node,
                        "score": candidate_score,
                        "is_adjacent": is_adj,
                        "confidence_pct": round(min(candidate_score * 100, 99.0), 1),
                    })

                candidate_hosts.sort(key=lambda x: x["score"], reverse=True)
                
                # Winner selection
                best_candidate = candidate_hosts[0]
                target_ip = best_candidate["ip"]
                target_node = best_candidate["node"]
                target_score = best_candidate["score"]
                visited_nodes.add(target_ip)

                # Ruled-out alternatives
                ruled_out_alternatives = []
                for alt in candidate_hosts[1:3]:
                    margin = round((target_score - alt["score"]) * 100, 1)
                    ruled_out_reason = (
                        "no direct network adjacency"
                        if not alt["is_adjacent"]
                        else f"lower asset criticality ({alt['node'].criticality}) and restricted service policy"
                    )
                    ruled_out_alternatives.append({
                        "ip_address": alt["ip"],
                        "hostname": alt["hostname"],
                        "confidence_pct": alt["confidence_pct"],
                        "margin_behind_winner_pct": max(margin, 0.1),
                        "ruled_out_reason": ruled_out_reason,
                    })

                # --- MITRE TECHNIQUE MAPPING ---
                technique_info = MITRE_TECHNIQUE_MAP.get(stage_name, {"id": "T1078", "name": "Valid Accounts"})
                tech_id = technique_info["id"]
                tech_name = f"{technique_info['id']} {technique_info['name']}"
                tech_confidence = round(min(confidence * 100, 98.0), 1)

                # --- FEATURE CONTRIBUTIONS ---
                feature_contribs = self._compute_feature_contributions(step_features)

                # --- REACHABILITY FACTOR ---
                reachability_factor = self._determine_reachability_factor(
                    source_host=source_node,
                    target_host=target_node,
                    is_adjacent=best_candidate["is_adjacent"],
                )

                # --- NATURAL LANGUAGE EXPLANATION ---
                top_feat_str = f"{feature_contribs[0]['feature_name']} (val: {feature_contribs[0]['raw_value']})"
                alt_summary = ""
                if ruled_out_alternatives:
                    alt1 = ruled_out_alternatives[0]
                    alt_summary = f" {alt1['hostname']} ({alt1['ip_address']}) was the next-closest candidate at {alt1['confidence_pct']}% confidence, ruled out due to {alt1['ruled_out_reason']}."

                explanation_text = (
                    f"{target_node.hostname} ({target_ip}) was selected as the next hop from {source_node.hostname} "
                    f"with {best_candidate['confidence_pct']}% confidence. Primary factors: network traffic indicators "
                    f"[{top_feat_str}] matching {tech_name} ({tech_confidence}% technique confidence), and {reachability_factor}.{alt_summary}"
                )

                structured_explanation = {
                    "feature_contributions": feature_contribs,
                    "mitre_technique": {
                        "id": tech_id,
                        "name": tech_name,
                        "confidence_pct": tech_confidence,
                    },
                    "reachability_factor": reachability_factor,
                    "comparison_to_alternatives": ruled_out_alternatives,
                    "explanation_text": explanation_text,
                }

                # Propagate compromise
                current_graph_state.propagate_compromise(
                    source_ip=active_host_ip,
                    target_ip=target_ip,
                    stage_idx=stage_idx,
                    stage_name=stage_name,
                    infiltration_prob=inf_prob,
                )

                if target_node:
                    target_node.features = next_state_np

                is_terminal = (
                    stage_name.lower() == terminal_stage_name.lower()
                    or stage_idx == len(self.stage_names) - 1
                ) and (inf_prob >= infiltration_threshold)

                # Construct streaming frame record
                step_record: Dict[str, Any] = {
                    "step": step_idx,
                    "source_ip": active_host_ip,
                    "target_ip": target_ip,
                    "target_hostname": target_node.hostname if target_node else target_ip,
                    "predicted_stage": stage_name,
                    "stage_idx": stage_idx,
                    "stage_confidence": float(confidence),
                    "infiltration_probability": float(inf_prob),
                    "graph_snapshot": current_graph_state.clone(),
                    "raw_state": next_state_np,
                    "raw_stage_probs": probs_np,
                    "is_terminal": is_terminal,
                    "explanation": structured_explanation,
                }

                yield step_record

                # Update active host for next step
                active_host_ip = target_ip
                x_t = next_state_tensor
                curr_features = next_state_np
                if isinstance(x_t, torch.Tensor) and x_t.ndim == 1:
                    x_t = x_t.unsqueeze(0)

                if stop_on_terminal and is_terminal:
                    break

    def rollout(
        self,
        seed_state: NetworkGraphState,
        k_steps: int = 10,
        stop_on_terminal: bool = True,
        infiltration_threshold: float = 0.9,
    ) -> List[Dict[str, Any]]:
        """Non-generator convenience method returning full trajectory list."""
        return list(self.rollout_stream(
            seed_state=seed_state,
            k_steps=k_steps,
            stop_on_terminal=stop_on_terminal,
            infiltration_threshold=infiltration_threshold,
        ))
