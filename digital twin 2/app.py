import time
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ingestion.stream import CSVTelemetryStream, PCAPTelemetryStream
from preprocessing.windowing import WindowEngine
from prediction.inference import InferencePipeline
from digital_twin.state_manager import DigitalTwinStateManager
from digital_twin.graph import create_digital_twin_figure
from evaluation.evaluator import SystemEvaluator

# Streamlit Page Setup
st.set_page_config(
    page_title="Real-Time Cyberattack Digital Twin & Progression Predictor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Dark Theme Styling
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    .stMetric { background-color: #1E222D; padding: 12px; border-radius: 8px; border: 1px solid #2E3440; }
    .stAlert { border-radius: 8px; }
    .badge-observed { background-color: #E63946; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; }
    .badge-suspected { background-color: #F4A261; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; }
    .badge-predicted { background-color: #9D4EDD; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; }
    .badge-benign { background-color: #2A9D8F; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# Initialize Session State
if "window_idx" not in st.session_state:
    st.session_state.window_idx = 0
if "is_playing" not in st.session_state:
    st.session_state.is_playing = False
if "history_log" not in st.session_state:
    st.session_state.history_log = []
if "evaluator" not in st.session_state:
    st.session_state.evaluator = SystemEvaluator()
if "dt_state_manager" not in st.session_state:
    st.session_state.dt_state_manager = DigitalTwinStateManager()

# Sidebar Setup
st.sidebar.title("🛡️ Cyber Twin Controls")
st.sidebar.markdown("---")

# 1. Dataset Selector
data_sources = {
    "Scenario A: Recon -> Brute Force -> Exfil": "data/raw/scenario_a_recon_bruteforce_exfil.csv",
    "Scenario B: PortScan -> DoS -> Command Exec": "data/raw/scenario_b_dos_command_exec.csv",
    "Scenario C: Benign Network Activity": "data/raw/scenario_c_benign.csv"
}

selected_dataset_name = st.sidebar.selectbox("Telemetry Data Source", list(data_sources.keys()))
dataset_path = data_sources[selected_dataset_name]

# Check dataset file existence
if not os.path.exists(dataset_path):
    st.warning("Sample dataset not found. Generating default datasets...")
    from scripts.generate_sample_data import generate_datasets
    generate_datasets()

# 2. Pipeline Controls
window_sec = st.sidebar.slider("Time Window (seconds)", min_value=5, max_value=30, value=10, step=5)
replay_speed = st.sidebar.select_slider("Replay Speed Multiplier", options=[0.5, 1.0, 2.0, 5.0, 10.0], value=1.0)
model_choice = st.sidebar.radio(
    "Prediction Model Engine",
    ["Baseline Model (Random Forest + Markov)", "Deep Learning Model (PyTorch GRU)"],
    help="Swappable model interface. Select Baseline or Deep Learning."
)
model_key = "baseline" if "Baseline" in model_choice else "deep_learning"

st.sidebar.markdown("---")
# Playback Controls
col_btn1, col_btn2, col_btn3 = st.sidebar.columns(3)
if col_btn1.button("▶️ Play"):
    st.session_state.is_playing = True
if col_btn2.button("⏸️ Pause"):
    st.session_state.is_playing = False
if col_btn3.button("🔄 Reset"):
    st.session_state.window_idx = 0
    st.session_state.is_playing = False
    st.session_state.history_log.clear()
    st.session_state.evaluator.clear()
    st.session_state.dt_state_manager = DigitalTwinStateManager()

# Load telemetry and process windows
@st.cache_data(show_spinner=False)
def load_windows(path: str, win_sec: float):
    stream = CSVTelemetryStream(path)
    records = stream.get_records()
    engine = WindowEngine(window_size_sec=win_sec, window_step_sec=win_sec / 2.0)
    return records, engine.process_records(records)

raw_records, windows = load_windows(dataset_path, float(window_sec))

if not windows:
    st.error("No telemetry windows could be generated from the selected dataset.")
    st.stop()

# Ensure window_idx stays within bounds
if st.session_state.window_idx >= len(windows):
    st.session_state.window_idx = len(windows) - 1

curr_window = windows[st.session_state.window_idx]

# Initialize Inference Pipeline
@st.cache_resource
def get_pipeline(mtype: str):
    return InferencePipeline(model_type=mtype)

pipeline = get_pipeline(model_key)
if pipeline.model_type != model_key:
    pipeline.switch_model(model_key)

# Run Inference for Current Window
inference_out = pipeline.process_window(curr_window)

# Extract Inference Results
curr_det = inference_out["current_detection"]
feat_why = inference_out["feature_explanations"]
next_preds = inference_out["next_predictions"]
per_host_dets = inference_out["per_host_detections"]
active_model_name = inference_out["active_model_name"]

# Ground truth label for evaluation (most frequent label in current window flows)
flow_labels = [f.label for f in curr_window.flows]
ground_truth_label = max(set(flow_labels), key=flow_labels.count) if flow_labels else "BENIGN"

# Record event in evaluator & history
st.session_state.evaluator.record_window_event(
    timestamp=curr_window.end_time,
    ground_truth_label=ground_truth_label,
    detected_label=inference_out["raw_detected_label"],
    detection_info=curr_det,
    ranked_predictions=next_preds
)

st.session_state.dt_state_manager.update_window_state(
    window_flows=curr_window.flows,
    current_detection=curr_det,
    per_host_detections=per_host_dets,
    predictions=next_preds,
    window_timestamp=curr_window.end_time
)

# Top Header Stats
st.title("🌐 Cyberattack Digital Twin & Progression Predictor")
st.caption(f"Active Model: **{active_model_name}** | Simulation Time: **{curr_window.end_time:.2f}s** | Window {st.session_state.window_idx + 1} of {len(windows)}")

# Layout Columns
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("🕸️ Live Digital Twin Graph")
    fig = create_digital_twin_figure(st.session_state.dt_state_manager.graph)
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("🎯 Threat State & Analysis")
    
    state_str = curr_det["state"]
    if state_str == "OBSERVED":
        badge_html = '<span class="badge-observed">OBSERVED</span>'
    elif state_str == "SUSPECTED":
        badge_html = '<span class="badge-suspected">SUSPECTED</span>'
    else:
        badge_html = '<span class="badge-benign">BENIGN</span>'

    st.markdown(f"**Current State:** {badge_html}", unsafe_allow_html=True)
    st.markdown(f"**Technique:** `{curr_det['technique_id']}` - **{curr_det['name']}**")
    st.markdown(f"**Tactic:** {curr_det['tactic']} | **Confidence:** {curr_det['confidence']:.1%}")
    st.caption(f"🔍 *{curr_det['mapping_reason']}*")

    st.markdown("---")
    st.subheader("🔮 Predicted Next Stage (Markov Sequence)")
    if next_preds:
        for pred in next_preds[:3]:
            st.write(f"**{pred['technique_id']} - {pred['name']}**")
            st.progress(min(max(float(pred['probability']), 0.0), 1.0))
            st.caption(f"Probability: {pred['probability']:.1%}")
    else:
        st.info("Insufficient data for sequence forecasting.")

    st.markdown("---")
    st.subheader("💡 Decision Explanation ('Why')")
    if feat_why:
        df_why = pd.DataFrame(list(feat_why.items()), columns=["Feature", "Attribution Weight"]).sort_values("Attribution Weight", ascending=True)
        fig_why = px.bar(df_why, x="Attribution Weight", y="Feature", orientation="h", title="Top Contributing Features", color_discrete_sequence=["#00B4D8"])
        fig_why.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=200, template="plotly_dark")
        st.plotly_chart(fig_why, use_container_width=True)

# Bottom Panel Tabs
st.markdown("---")
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Telemetry Flows",
    "📈 Attack Progression Timeline",
    "📉 Technique Probabilities",
    "📜 History Log",
    "🏆 Evaluation Metrics"
])

with tab1:
    st.subheader("Raw Window Telemetry Flows")
    df_flows = pd.DataFrame([f.__dict__ for f in curr_window.flows])
    st.dataframe(df_flows, use_container_width=True)

with tab2:
    st.subheader("Observed vs Predicted Progression Timeline")
    history_events = st.session_state.evaluator.actual_observations
    if history_events:
        df_hist = pd.DataFrame(history_events)
        fig_timeline = px.scatter(
            df_hist,
            x="timestamp",
            y="name",
            color="state",
            color_discrete_map={"OBSERVED": "#E63946", "SUSPECTED": "#F4A261", "BENIGN": "#2A9D8F"},
            title="Technique Progression over Simulation Clock"
        )
        fig_timeline.update_layout(template="plotly_dark", height=280)
        st.plotly_chart(fig_timeline, use_container_width=True)

with tab3:
    st.subheader("Probability Time-Series per Technique")
    prob_logs = []
    for log in st.session_state.evaluator.prediction_logs:
        t = log["timestamp"]
        for p in log["predictions"]:
            prob_logs.append({"timestamp": t, "technique": p["name"], "probability": p["probability"]})
    if prob_logs:
        df_probs = pd.DataFrame(prob_logs)
        fig_probs = px.line(df_probs, x="timestamp", y="probability", color="technique", title="Forecast Probabilities Over Time")
        fig_probs.update_layout(template="plotly_dark", height=280)
        st.plotly_chart(fig_probs, use_container_width=True)

with tab4:
    st.subheader("Prediction Audit History Log")
    if st.session_state.evaluator.prediction_logs:
        log_records = []
        for l in st.session_state.evaluator.prediction_logs:
            top_p = l["predictions"][0] if l["predictions"] else {"name": "None", "probability": 0.0}
            log_records.append({
                "Timestamp": l["timestamp"],
                "Observed Detection": l["detected_label"],
                "Predicted Next": top_p["name"],
                "Next Probability": f"{top_p['probability']:.1%}"
            })
        st.dataframe(pd.DataFrame(log_records), use_container_width=True)

with tab5:
    st.subheader("Evaluation & Lead Time Metrics")
    report = st.session_state.evaluator.compute_evaluation_report()
    
    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    cls_m = report["classification"]
    col_m1.metric("Accuracy", f"{cls_m['accuracy']:.1%}")
    col_m2.metric("Precision", f"{cls_m['precision']:.1%}")
    col_m3.metric("Recall", f"{cls_m['recall']:.1%}")
    col_m4.metric("F1-Score", f"{cls_m['f1_score']:.1%}")
    col_m5.metric("Avg Lead Time", f"{report['lead_time']['avg_lead_time_sec']:.1f} s")

    col_acc1, col_acc2 = st.columns(2)
    col_acc1.metric("Top-1 Prediction Accuracy", f"{report['top1_accuracy']:.1%}")
    col_acc2.metric("Top-3 Prediction Accuracy", f"{report['top3_accuracy']:.1%}")

    if cls_m["confusion_matrix"]:
        st.markdown("**Confusion Matrix**")
        df_cm = pd.DataFrame(cls_m["confusion_matrix"], index=cls_m["labels"], columns=cls_m["labels"])
        st.dataframe(df_cm, use_container_width=True)

# Handle Auto-Playback
if st.session_state.is_playing:
    if st.session_state.window_idx < len(windows) - 1:
        st.session_state.window_idx += 1
        time.sleep(max(0.1, 1.0 / float(replay_speed)))
        st.rerun()
    else:
        st.session_state.is_playing = False
        st.success("Replay complete.")
