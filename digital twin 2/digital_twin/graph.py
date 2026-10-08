import networkx as nx
import plotly.graph_objects as go
from typing import Dict, Any
from digital_twin.state_manager import STATE_COLOR_MAP

def create_digital_twin_figure(graph: nx.DiGraph) -> go.Figure:
    """Renders NetworkX digital twin graph as an interactive Plotly figure."""
    if graph.number_of_nodes() == 0:
        fig = go.Figure()
        fig.update_layout(
            title="Digital Twin Network Graph (No Active Hosts in Window)",
            template="plotly_dark",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            annotations=[dict(text="Insufficient Data / Idle Window", showarrow=False, font=dict(size=18))]
        )
        return fig

    pos = nx.spring_layout(graph, seed=42, k=0.8)

    # Edge traces
    edge_x = []
    edge_y = []
    edge_hover_texts = []
    
    for edge in graph.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=1.5, color="rgba(150, 150, 150, 0.5)"),
        hoverinfo="none",
        mode="lines"
    )

    # Node traces
    node_x = []
    node_y = []
    node_colors = []
    node_text = []
    hover_text = []

    for node, data in graph.nodes(data=True):
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

        state = data.get("state", "BENIGN")
        color = STATE_COLOR_MAP.get(state, STATE_COLOR_MAP["BENIGN"])
        node_colors.append(color)

        node_text.append(f"<b>{node}</b><br>{state}")

        tech_id = data.get("technique_id", "T0000")
        tech_name = data.get("technique_name", "Benign Activity")
        conf = data.get("confidence", 1.0)
        next_tech = data.get("predicted_next_technique", "None")
        next_prob = data.get("predicted_probability", 0.0)

        htext = (
            f"<b>Host IP:</b> {node}<br>"
            f"<b>Threat State:</b> {state}<br>"
            f"<b>MITRE Technique:</b> {tech_id} - {tech_name}<br>"
            f"<b>Confidence:</b> {conf:.2f}<br>"
            f"<b>Predicted Next:</b> {next_tech} ({next_prob:.1%})"
        )
        hover_text.append(htext)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        hoverinfo="text",
        hovertext=hover_text,
        text=node_text,
        textposition="top center",
        marker=dict(
            showscale=False,
            color=node_colors,
            size=28,
            line=dict(width=2, color="#FFFFFF")
        )
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title="Real-Time Cyberattack Digital Twin Graph",
        title_font_size=18,
        showlegend=False,
        hovermode="closest",
        margin=dict(b=20, l=10, r=10, t=50),
        template="plotly_dark",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )

    return fig
