"""
visualization.py - ML Training Visualization (Plotly)
"""
from typing import List, Dict, Any
import plotly.graph_objects as go


def get_task_metric(task_type: str) -> tuple:
    """Get the primary metric and display info for a task type"""
    metric_map = {
        'classification': ('accuracy', 'Accuracy', True),
        'regression': ('r2', 'R² Score', True),
        'clustering': ('silhouette_score', 'Silhouette Score', True),
        'recommendation': ('rmse', 'RMSE', False)
    }
    return metric_map.get(task_type, ('accuracy', 'Accuracy', True))


def create_training_progress_chart(experiments: List[Dict[str, Any]], task_type: str) -> go.Figure:
    """Create training progress chart with Plotly"""

    successful = [e for e in experiments if e.get('success', False)]

    metric, metric_label, higher_is_better = get_task_metric(task_type)

    if not successful:
        fig = go.Figure()
        fig.add_annotation(
            text="No successful experiments yet.<br>Run the Auto-ML loop to see progress.",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color="#888888"),
            align="center"
        )
        fig.update_layout(
            title='Training Progress',
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=400
        )
        return fig

    iterations = [e['iteration'] for e in successful]
    scores = [e['metrics'].get(metric, 0) for e in successful]
    times = [e.get('execution_time', 0) for e in successful]

    colors = []
    for i, score in enumerate(scores):
        if i == 0:
            colors.append('#e06c53')
        elif higher_is_better:
            colors.append('#28a745' if score > scores[i-1] else '#6c757d')
        else:
            colors.append('#28a745' if score < scores[i-1] else '#6c757d')

    hover_texts = [
        f"Iteration: {it}<br>{metric_label}: {sc:.4f}<br>Time: {t:.1f}s"
        for it, sc, t in zip(iterations, scores, times)
    ]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=iterations,
        y=scores,
        mode='lines+markers',
        line=dict(color='#e06c53', width=2),
        marker=dict(size=12, color=colors, line=dict(color='#111111', width=1)),
        hovertext=hover_texts,
        hoverinfo='text',
        name='Metric'
    ))

    if higher_is_better:
        best_idx = scores.index(max(scores))
    else:
        best_idx = scores.index(min(scores))

    fig.add_trace(go.Scatter(
        x=[iterations[best_idx]],
        y=[scores[best_idx]],
        mode='markers',
        marker=dict(size=18, color='#ffc107', symbol='star', line=dict(color='#111111', width=1.5)),
        name=f'Best: {scores[best_idx]:.4f}',
        hovertemplate=f'Best Iteration: {iterations[best_idx]}<br>{metric_label}: {scores[best_idx]:.4f}<extra></extra>'
    ))

    fig.update_layout(
        title=dict(
            text=f'Training Progress — {metric_label}',
            font=dict(size=16, family='Inter, sans-serif', color='#111111')
        ),
        xaxis=dict(
            title='Iteration',
            title_font=dict(size=12, family='Inter, sans-serif', color='#555555'),
            tickfont=dict(size=11, family='JetBrains Mono, monospace', color='#555555'),
            gridcolor='#e5e5e0',
            zerolinecolor='#e5e5e0'
        ),
        yaxis=dict(
            title=metric_label,
            title_font=dict(size=12, family='Inter, sans-serif', color='#555555'),
            tickfont=dict(size=11, family='JetBrains Mono, monospace', color='#555555'),
            gridcolor='#e5e5e0',
            zerolinecolor='#e5e5e0'
        ),
        plot_bgcolor='#fbfbfa',
        paper_bgcolor='rgba(0,0,0,0)',
        height=400,
        margin=dict(l=60, r=30, t=60, b=50),
        legend=dict(
            font=dict(size=11, family='Inter, sans-serif'),
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='#e5e5e0',
            borderwidth=1
        ),
        hovermode='closest'
    )

    return fig
