"""
visualize.py - Sentinel-WM

Visualization module for Sentinel-WM Digital Twin trajectories.
Provides dual-axis visualization tools using Matplotlib (for static scripts)
and Plotly (for interactive Streamlit dashboard rendering).
"""

from typing import List, Dict, Any, Optional, Tuple
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from state import DEFAULT_MITRE_STAGES


def plot_trajectory_matplotlib(
    trajectory: List[Dict[str, Any]],
    stage_names: Optional[List[str]] = None,
    output_path: Optional[str] = "twin_trajectory.png",
    title: str = "Sentinel-WM Attack Trajectory & Infiltration Simulation",
    min_confidence: float = 0.4,
) -> Optional[str]:
    """
    Plot dual-axis trajectory visualization using Matplotlib.

    Left Y-axis: MITRE ATT&CK Stage progression (categorical).
    Right Y-axis: Infiltration Probability curve (0.0 to 1.0).

    Args:
        trajectory: List of step dictionaries from DigitalTwin.rollout().
        stage_names: Optional list of MITRE stage names.
        output_path: File path to save PNG plot.
        title: Plot title text.
        min_confidence: Threshold for highlighting uncertain predictions.

    Returns:
        Optional[str]: Saved PNG file path.
    """
    if not trajectory:
        print("[visualize] Empty trajectory provided.")
        return None

    all_stages = stage_names if stage_names is not None else DEFAULT_MITRE_STAGES

    steps = [d["step"] for d in trajectory]
    predicted_stages = [d["predicted_stage"] for d in trajectory]
    inf_probs = [d["infiltration_probability"] for d in trajectory]
    confidences = [d["stage_confidence"] for d in trajectory]

    # Map stage strings to y-indices
    stage_to_idx = {name: i for i, name in enumerate(all_stages)}
    y_indices = []
    for s_name in predicted_stages:
        if s_name in stage_to_idx:
            y_indices.append(stage_to_idx[s_name])
        else:
            new_idx = len(all_stages)
            all_stages.append(s_name)
            stage_to_idx[s_name] = new_idx
            y_indices.append(new_idx)

    # Dark cyber theme setup
    plt.style.use("dark_background")
    fig, ax1 = plt.subplots(figsize=(11, 6), dpi=150)

    # 1. Plot MITRE Stage Progression (Left Y-Axis)
    ax1.plot(
        steps,
        y_indices,
        color="#00e5ff",
        linestyle="-",
        linewidth=2.5,
        marker="o",
        markersize=7,
        alpha=0.9,
        label="Predicted MITRE Stage",
    )
    ax1.set_xlabel("Simulation Step (t)", fontsize=11, color="#e0e0e0", labelpad=10)
    ax1.set_ylabel("MITRE ATT&CK Stage", fontsize=11, color="#00e5ff", labelpad=10)
    ax1.set_yticks(range(len(all_stages)))
    ax1.set_yticklabels(all_stages, fontsize=9, color="#00e5ff")
    ax1.set_ylim(-0.5, len(all_stages) - 0.5)
    ax1.set_xticks(steps)
    ax1.grid(True, linestyle=":", alpha=0.3, color="#555555")

    # Highlight low-confidence steps
    low_conf_steps = [s for s, c in zip(steps, confidences) if c < min_confidence]
    low_conf_y = [y for y, c in zip(y_indices, confidences) if c < min_confidence]
    if low_conf_steps:
        ax1.scatter(
            low_conf_steps,
            low_conf_y,
            s=350,
            facecolors="none",
            edgecolors="#ff1744",
            linewidths=2.5,
            linestyle="--",
            zorder=4,
            label=f"Low Confidence (<{int(min_confidence*100)}%)",
        )

    # 2. Overlay Infiltration Probability Curve (Right Y-Axis)
    ax2 = ax1.twinx()
    ax2.plot(
        steps,
        inf_probs,
        color="#ff5252",
        linestyle="--",
        linewidth=2.0,
        marker="s",
        markersize=6,
        alpha=0.85,
        label="Infiltration Probability",
    )
    ax2.set_ylabel("Infiltration Probability", fontsize=11, color="#ff5252", labelpad=10)
    ax2.tick_params(axis="y", labelcolor="#ff5252")
    ax2.set_ylim(0.0, 1.05)

    # Title & Combined Legend
    plt.title(title, fontsize=13, fontweight="bold", color="#ffffff", pad=15)
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper left", framealpha=0.4)

    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"[visualize] Saved static Matplotlib trajectory plot to: {output_path}")
    plt.close(fig)
    return output_path


def plot_trajectory_plotly(
    trajectory: List[Dict[str, Any]],
    stage_names: Optional[List[str]] = None,
    min_confidence: float = 0.4,
) -> go.Figure:
    """
    Generate an interactive dual-axis Plotly figure for Streamlit rendering.

    Left Y-axis: MITRE Stage progression (categorical).
    Right Y-axis: Infiltration Probability curve (0.0 to 1.0).

    Args:
        trajectory: List of step dictionaries from DigitalTwin.rollout().
        stage_names: Optional list of stage names.
        min_confidence: Threshold for highlighting low-confidence steps.

    Returns:
        go.Figure: Interactive Plotly figure object.
    """
    all_stages = stage_names if stage_names is not None else DEFAULT_MITRE_STAGES

    if not trajectory:
        fig = go.Figure()
        fig.update_layout(title="No simulation trajectory data available.")
        return fig

    steps = [d["step"] for d in trajectory]
    predicted_stages = [d["predicted_stage"] for d in trajectory]
    inf_probs = [d["infiltration_probability"] for d in trajectory]
    confidences = [d["stage_confidence"] for d in trajectory]

    stage_to_idx = {name: i for i, name in enumerate(all_stages)}
    y_indices = [stage_to_idx.get(s, 0) for s in predicted_stages]

    # Create subplots with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 1. MITRE Stage Line & Markers (Left Y-Axis)
    hover_text_stage = [
        f"Step {s}<br>Stage: {st}<br>Confidence: {c*100:.1f}%<br>Inf Prob: {p:.2f}"
        for s, st, c, p in zip(steps, predicted_stages, confidences, inf_probs)
    ]

    fig.add_trace(
        go.Scatter(
            x=steps,
            y=y_indices,
            mode="lines+markers",
            name="Predicted MITRE Stage",
            text=hover_text_stage,
            hoverinfo="text",
            line=dict(color="#00e5ff", width=3),
            marker=dict(size=10, color="#00e5ff"),
        ),
        secondary_y=False,
    )

    # 2. Infiltration Probability Curve (Right Y-Axis)
    fig.add_trace(
        go.Scatter(
            x=steps,
            y=inf_probs,
            mode="lines+markers",
            name="Infiltration Probability",
            hoverinfo="y+name",
            line=dict(color="#ff5252", width=2.5, dash="dash"),
            marker=dict(size=8, color="#ff5252", symbol="square"),
        ),
        secondary_y=True,
    )

    # Highlight low confidence points
    low_conf_steps = [s for s, c in zip(steps, confidences) if c < min_confidence]
    low_conf_y = [y for y, c in zip(y_indices, confidences) if c < min_confidence]
    if low_conf_steps:
        fig.add_trace(
            go.Scatter(
                x=low_conf_steps,
                y=low_conf_y,
                mode="markers",
                name=f"Low Confidence (<{int(min_confidence*100)}%)",
                marker=dict(
                    size=16,
                    color="rgba(0,0,0,0)",
                    line=dict(color="#ff1744", width=3),
                    symbol="circle",
                ),
            ),
            secondary_y=False,
        )

    # Configure axes and layout
    fig.update_layout(
        title=dict(
            text="Sentinel-WM Digital Twin Attack Trajectory & Infiltration Curve",
            font=dict(size=16, color="#ffffff"),
        ),
        template="plotly_dark",
        paper_bgcolor="#111827",
        plot_bgcolor="#1f2937",
        xaxis=dict(
            title="Simulation Step (t)",
            tickmode="linear",
            dtick=1,
            gridcolor="#374151",
        ),
        yaxis=dict(
            title=dict(text="Predicted MITRE ATT&CK Stage", font=dict(color="#00e5ff")),
            tickmode="array",
            tickvals=list(range(len(all_stages))),
            ticktext=all_stages,
            tickfont=dict(color="#00e5ff"),
            gridcolor="#374151",
        ),
        yaxis2=dict(
            title=dict(text="Infiltration Probability", font=dict(color="#ff5252")),
            range=[0.0, 1.05],
            tickfont=dict(color="#ff5252"),
            overlaying="y",
            side="right",
        ),
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(17, 24, 39, 0.7)"),
        margin=dict(l=60, r=60, t=60, b=60),
    )

    return fig
