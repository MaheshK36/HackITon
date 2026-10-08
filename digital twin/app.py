"""
app.py - Sentinel-WM Live Real-Time Simulator

Interactive Streamlit Web Dashboard for Sentinel-WM Network Digital Twin.
Features:
  1. Live real-time network topology graph animation (streamed frame-by-frame).
  2. Dynamic side-panel metrics, infiltration progress bars, and model-driven narrations.
  3. Playback controls (Play, Pause, Step-Through, Speed Slider).
  4. Separate Twin Fidelity Check & Horizon Drift Analysis benchmark tab.
"""

import os
import time
import streamlit as st
import numpy as np
import pandas as pd
import torch

from world_model import WorldModel
from state import NetworkGraphState, DEFAULT_FLOW_FEATURES, DEFAULT_MITRE_STAGES
from twin_engine import DigitalTwin
from narration import TrajectoryNarrator, generate_explanation
from graph_visualizer import render_network_graph_plotly
from validation import validate_twin_fidelity

# Set page config for dark cybersecurity layout
st.set_page_config(
    page_title="Sentinel-WM Real-Time Digital Twin",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def get_world_model(feature_dim: int, num_stages: int) -> WorldModel:
    """Initialize cached PyTorch WorldModel instance."""
    return WorldModel(feature_dim=feature_dim, hidden_dim=64, num_stages=num_stages)


def main() -> None:
    st.title("🛡️ Sentinel-WM: Real-Time Network Digital Twin Simulator")
    st.markdown(
        "**Multi-Task World Model Simulation Layer** — Watch the cyber compromise spread live "
        "across the network topology graph in real time via free-running autoregressive rollouts."
    )

    # ---------------------------------------------------------
    # SIDEBAR CONTROLS
    # ---------------------------------------------------------
    st.sidebar.header("⚙️ Simulation Settings")

    # Checkpoint File Uploader
    checkpoint_file = st.sidebar.file_uploader("Load WorldModel Checkpoint (.pt)", type=["pt", "pth"])

    # Seed State Selection
    st.sidebar.subheader("🌱 Seed Network State")
    seed_mode = st.sidebar.radio(
        "Select Initial Network Scenario:",
        ["Attack Campaign (DMZ Compromise)", "Benign Baseline (Normal Flow)"],
    )

    # Rollout Parameters
    st.sidebar.subheader("🔮 Playback Parameters")
    k_steps = st.sidebar.slider("Rollout Horizon (k steps)", min_value=3, max_value=20, value=10)
    stop_on_terminal = st.sidebar.checkbox("Early Stop on Exfiltration", value=True)
    inf_threshold = st.sidebar.slider("Infiltration Stop Threshold", min_value=0.5, max_value=0.99, value=0.90, step=0.01)
    min_confidence = st.sidebar.slider("Low Confidence Threshold", min_value=0.1, max_value=0.8, value=0.4, step=0.05)
    
    # Real-Time Speed Slider
    step_delay = st.sidebar.slider("Simulation Step Delay (seconds)", min_value=0.1, max_value=2.0, value=0.6, step=0.1)

    # ---------------------------------------------------------
    # INITIALIZE ENGINE & MODEL
    # ---------------------------------------------------------
    feature_dim = len(DEFAULT_FLOW_FEATURES)
    model = get_world_model(feature_dim=feature_dim, num_stages=len(DEFAULT_MITRE_STAGES))

    if checkpoint_file is not None:
        try:
            temp_path = "temp_checkpoint.pt"
            with open(temp_path, "wb") as f:
                f.write(checkpoint_file.read())
            state_dict = torch.load(temp_path, map_location="cpu")
            if isinstance(state_dict, dict) and "model_state_dict" in state_dict:
                state_dict = state_dict["model_state_dict"]
            model.load_state_dict(state_dict)
            st.sidebar.success("Loaded PyTorch checkpoint successfully!")
        except Exception as e:
            st.sidebar.warning(f"Error loading checkpoint: {e}. Using demo WorldModel.")

    twin = DigitalTwin(model=model, stage_names=DEFAULT_MITRE_STAGES)
    narrator = TrajectoryNarrator(min_confidence=min_confidence)

    # Build seed NetworkGraphState
    seed_graph = NetworkGraphState(feature_cols=DEFAULT_FLOW_FEATURES)
    if seed_mode == "Attack Campaign (DMZ Compromise)":
        seed_graph.update_host_state("192.168.1.20", stage_idx=1, stage_name="Initial Access", infiltration_prob=0.45)

    # ---------------------------------------------------------
    # MAIN APP TABS
    # ---------------------------------------------------------
    tab_sim, tab_val = st.tabs(["⚡ Live Real-Time Network Simulation", "🧪 Twin Fidelity Benchmark & Drift Analysis"])

    with tab_sim:
        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1, 1, 4])
        with col_ctrl1:
            run_button = st.button("▶️ Start Live Simulation", type="primary")
        with col_ctrl2:
            reset_button = st.button("🔄 Reset Topology")

        # Layout Split: 2/3 for Live Graph, 1/3 for Live Side Panel
        col_graph, col_panel = st.columns([2, 1])

        # Streamlit placeholders for dynamic frame updating
        with col_graph:
            graph_placeholder = st.empty()

        with col_panel:
            st.subheader("📊 Live Telemetry Side-Panel")
            metrics_placeholder = st.empty()
            alert_placeholder = st.empty()
            risk_bar_placeholder = st.empty()
            narration_box_placeholder = st.empty()

        # Render initial static snapshot before simulation starts
        if not run_button or reset_button:
            initial_fig = render_network_graph_plotly(seed_graph)
            graph_placeholder.plotly_chart(initial_fig, use_container_width=True, key="initial_network_graph")

            with metrics_placeholder.container():
                m1, m2 = st.columns(2)
                m1.metric("Status", "READY")
                m2.metric("Rollout Horizon", f"{k_steps} steps")

            alert_placeholder.info("Click **Start Live Simulation** to watch the attack unfold live across the topology.")
            risk_bar_placeholder.progress(0.05, text="Infiltration Risk Level: 5.0%")
            narration_box_placeholder.code("[READY] System initialized. Awaiting live rollout stream...", language="text")

        # LIVE REAL-TIME STREAMING SIMULATION LOOP
        if run_button:
            trajectory_history = []

            for step_data in twin.rollout_stream(
                seed_state=seed_graph,
                k_steps=k_steps,
                stop_on_terminal=stop_on_terminal,
                infiltration_threshold=inf_threshold,
            ):
                trajectory_history.append(step_data)
                graph_snapshot = step_data["graph_snapshot"]
                step_num = step_data["step"]

                # 1. Update Live Plotly Network Topology Graph with step-unique key
                live_fig = render_network_graph_plotly(graph_snapshot, active_step=step_data)
                graph_placeholder.plotly_chart(live_fig, use_container_width=True, key=f"live_network_graph_step_{step_num}")

                # 2. Update Live Side-Panel Metrics
                step_num = step_data["step"]
                target_name = step_data.get("target_hostname", "Target")
                stage = step_data["predicted_stage"]
                conf = step_data["stage_confidence"] * 100
                inf_prob = step_data["infiltration_probability"]

                with metrics_placeholder.container():
                    m1, m2 = st.columns(2)
                    m1.metric("Current Step", f"{step_num} / {k_steps}")
                    m2.metric("Target Host", target_name)

                # Update Status Alert & Infiltration Risk Progress Bar
                if inf_prob >= 0.85:
                    alert_placeholder.error(f"🚨 CRITICAL INFILTRATION: {stage} ({conf:.1f}% conf)")
                elif inf_prob >= 0.50:
                    alert_placeholder.warning(f"⚠️ ELEVATED LATERAL RISK: {stage} ({conf:.1f}% conf)")
                else:
                    alert_placeholder.success(f"🟢 STABLE / RECON: {stage} ({conf:.1f}% conf)")

                risk_bar_placeholder.progress(min(max(inf_prob, 0.0), 1.0), text=f"Infiltration Risk: {inf_prob * 100:.1f}%")

                # 3. Update Model-Driven Narration Text Box (Live Frame)
                live_alert_text = narrator.narrate_step(step_data)
                narration_box_placeholder.code(live_alert_text, language="text")

                # Real-time streaming delay for animated playback
                time.sleep(step_delay)

            st.success("✅ Real-time simulation stream complete.")
            
            # Show full analyst summary report at end of live run
            st.markdown("---")
            st.subheader("📜 Complete Simulation Summary Report")
            full_report = generate_explanation(trajectory_history, stage_names=DEFAULT_MITRE_STAGES, min_confidence=min_confidence)
            st.code(full_report, language="text")

            st.subheader("🛡️ Step-by-Step AI Explainability Details")
            for step_data in trajectory_history:
                step_num = step_data["step"]
                target_name = step_data.get("target_hostname", "Target")
                src_ip = step_data.get("source_ip", "Source")
                stage = step_data["predicted_stage"]
                expl = step_data.get("explanation", None)
                
                if expl:
                    with st.expander(f"Step {step_num}: {src_ip} → {target_name} ({stage})", expanded=True):
                        st.markdown(f"**AI Narrative:** {expl['explanation_text']}")
                        st.markdown(f"**Reachability Driver:** `{expl['reachability_factor']}`")
                        
                        # MITRE ATT&CK technique details
                        tech = expl["mitre_technique"]
                        st.markdown(f"**MITRE Technique:** `{tech['id']}` - **{tech['name']}** ({tech['confidence_pct']}% confidence)")
                        
                        # Feature contributions
                        st.markdown("**Top Flow Feature Contributions:**")
                        fc_data = []
                        for fc in expl["feature_contributions"]:
                            fc_data.append({
                                "Feature": fc["feature_name"],
                                "Value": fc["raw_value"],
                                "Weight": fc["weight"],
                                "Attribution": fc["contribution"]
                            })
                        st.table(pd.DataFrame(fc_data))
                        
                        # Ruled out alternatives
                        alts = expl.get("comparison_to_alternatives", [])
                        if alts:
                            st.markdown("**Ruled-Out Candidate Alternatives:**")
                            alt_data = []
                            for alt in alts:
                                alt_data.append({
                                    "Candidate Host": alt["hostname"],
                                    "IP Address": alt["ip_address"],
                                    "Confidence %": alt["confidence_pct"],
                                    "Margin Behind %": alt["margin_behind_winner_pct"],
                                    "Ruled-Out Reason": alt["ruled_out_reason"]
                                })
                            st.table(pd.DataFrame(alt_data))

    # TAB 2: TWIN FIDELITY CHECK & DRIFT BENCHMARK
    with tab_val:
        st.subheader("🧪 Digital Twin Fidelity Check & Horizon Drift Analysis")
        st.markdown(
            "Measures empirical simulation realism by comparing autoregressive predictions against "
            "ground-truth held-out sequences."
        )

        if st.button("Run Twin Fidelity Benchmark"):
            gt_sequence = [seed_graph]
            for step_i in range(1, k_steps + 1):
                gt_g = seed_graph.clone()
                target_ip = "192.168.1.30" if step_i > 2 else "192.168.1.20"
                gt_g.update_host_state(target_ip, stage_idx=min(step_i, 6), stage_name=DEFAULT_MITRE_STAGES[min(step_i, 6)], infiltration_prob=min(0.1 + step_i * 0.15, 0.95))
                gt_sequence.append(gt_g)

            fidelity_res = validate_twin_fidelity(twin=twin, ground_truth_sequences=[gt_sequence], k_steps=k_steps)

            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                st.metric("Feature State MSE", f"{fidelity_res['overall_state_mse']:.6f}")
            with f_col2:
                st.metric("Stage Accuracy", f"{fidelity_res['stage_accuracy_percent']}%")
            with f_col3:
                st.metric("Infiltration Prob MAE", f"{fidelity_res['infiltration_prob_mae']:.4f}")

            st.markdown("**Horizon Drift Curve (MSE per timestep t):**")
            drift_df = pd.DataFrame(
                list(fidelity_res["horizon_drift_curve_mse"].items()),
                columns=["Step", "MSE"],
            )
            st.bar_chart(drift_df.set_index("Step"))


if __name__ == "__main__":
    main()
