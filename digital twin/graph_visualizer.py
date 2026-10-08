"""
graph_visualizer.py - Sentinel-WM Live Visualizer

Real-Time Network Topology Graph Visualizer using Plotly and NetworkX.
Renders network hosts as nodes and network flows as edges.
Dynamically highlights newly affected hosts, stage color transitions,
and glowing attack propagation vectors during live simulations.
"""

from typing import Dict, Any, Optional
import networkx as nx
import plotly.graph_objects as go
from state import NetworkGraphState, DEFAULT_MITRE_STAGES

# Stage to color palette mapping
STAGE_COLOR_MAP: Dict[str, str] = {
    "Reconnaissance": "#29b6f6",        # Bright Cyan Blue
    "Initial Access": "#ffee58",        # Bright Yellow
    "Execution": "#ffb74d",             # Amber/Orange
    "Persistence": "#ffa726",           # Deep Orange
    "Privilege Escalation": "#ff7043",  # Light Red
    "Lateral Movement": "#ff5252",      # Crimson Red
    "Exfiltration": "#ff1744",          # Deep Neon Red
}

STATUS_COLOR_MAP: Dict[str, str] = {
    "normal": "#00e676",        # Neon Green
    "target": "#ffee58",        # Bright Yellow
    "compromised": "#ff1744",   # Neon Red
}


def render_network_graph_plotly(
    graph_state: NetworkGraphState,
    active_step: Optional[Dict[str, Any]] = None,
) -> go.Figure:
    """
    Render an interactive 2D network topology graph using Plotly.

    Nodes represent network hosts (IPs, Hostnames, Roles).
    Edges represent active network flow connections.
    Colors dynamically transition based on MITRE ATT&CK stage and infiltration risk.

    Args:
        graph_state: NetworkGraphState snapshot.
        active_step: Optional streaming step dictionary for active edge highlighting.

    Returns:
        go.Figure: Interactive Plotly figure object.
    """
    G = graph_state.graph
    pos = graph_state.pos_layout

    # Extract active attack edge endpoints if available
    active_src = active_step.get("source_ip", None) if active_step else None
    active_target = active_step.get("target_ip", None) if active_step else None

    # 1. Build Normal Network Edge Traces
    edge_x = []
    edge_y = []
    active_edge_x = []
    active_edge_y = []

    for u, v, d in G.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]

        is_active = (
            d.get("active_attack", False)
            or (active_src == u and active_target == v)
            or (active_src == v and active_target == u)
        )

        if is_active:
            active_edge_x.extend([x0, x1, None])
            active_edge_y.extend([y0, y1, None])
        else:
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

    fig = go.Figure()

    # Add Normal Network Connection Lines
    if edge_x:
        fig.add_trace(
            go.Scatter(
                x=edge_x,
                y=edge_y,
                mode="lines",
                line=dict(color="#4b5563", width=1.5, dash="dot"),
                hoverinfo="none",
                name="Network Flow Connection",
                showlegend=True,
            )
        )

    # Add Active Attack Vector Propagation Lines (Glowing Red)
    if active_edge_x:
        fig.add_trace(
            go.Scatter(
                x=active_edge_x,
                y=active_edge_y,
                mode="lines",
                line=dict(color="#ff1744", width=4),
                hoverinfo="none",
                name="⚡ Active Attack Propagation Vector",
                showlegend=True,
            )
        )

    # 2. Build Host Node Traces
    node_x = []
    node_y = []
    node_colors = []
    node_sizes = []
    node_labels = []
    hover_texts = []
    line_colors = []

    for node_ip, host in graph_state.hosts.items():
        x, y = pos[node_ip]
        node_x.append(x)
        node_y.append(y)

        # Color mapping by stage or status
        if host.status == "compromised":
            color = STAGE_COLOR_MAP.get(host.stage_name, "#ff1744")
            line_color = "#ff1744"
            size = 38 + int(host.infiltration_prob * 15)
        elif host.status == "target":
            color = "#ffee58"
            line_color = "#ffa726"
            size = 32
        else:
            color = "#00e676"
            line_color = "#00c853"
            size = 28

        # Highlight currently active target node in this step
        if active_target == node_ip:
            line_color = "#00e5ff"
            size += 8

        node_colors.append(color)
        line_colors.append(line_color)
        node_sizes.append(size)

        label = f"<b>{host.hostname}</b><br>{host.ip_address}"
        node_labels.append(label)

        hover_info = (
            f"<b>Host:</b> {host.hostname} ({host.ip_address})<br>"
            f"<b>Role:</b> {host.role}<br>"
            f"<b>Status:</b> {host.status.upper()}<br>"
            f"<b>MITRE Stage:</b> {host.stage_name}<br>"
            f"<b>Infiltration Risk:</b> {host.infiltration_prob * 100:.1f}%"
        )
        hover_texts.append(hover_info)

    # Add Node Scatter Trace
    fig.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            text=[f"<b>{h.hostname}</b>" for h in graph_state.hosts.values()],
            textposition="top center",
            textfont=dict(color="#ffffff", size=11),
            hoverinfo="text",
            hovertext=hover_texts,
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(color=line_colors, width=3),
            ),
            name="Network Hosts",
            showlegend=False,
        )
    )

    # 3. Configure Plotly Layout
    fig.update_layout(
        title=dict(
            text="🛡️ Sentinel-WM Real-Time Digital Twin Network Topology Graph",
            font=dict(size=16, color="#ffffff"),
        ),
        template="plotly_dark",
        paper_bgcolor="#0f172a",
        plot_bgcolor="#1e293b",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        legend=dict(
            x=0.01,
            y=0.99,
            bgcolor="rgba(15, 23, 42, 0.8)",
            font=dict(color="#e2e8f0", size=10),
        ),
        margin=dict(l=40, r=40, t=50, b=40),
        height=520,
    )

    return fig
