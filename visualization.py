"""
visualization.py - Font configuration and ML Training Visualization
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from typing import List, Dict, Any, Optional
import os
import urllib.request
import plotly.graph_objects as go

def setup_fonts():
    jetbrains_path = os.path.join(os.path.dirname(__file__), "fonts", "JetBrainsMono-Regular.ttf")
    inter_path = os.path.join(os.path.dirname(__file__), "fonts", "Inter-Regular.ttf")
    font_dir = os.path.join(os.path.dirname(__file__), "fonts")
    
    if not os.path.exists(font_dir):
        os.makedirs(font_dir, exist_ok=True)
    
    fonts_downloaded = False
    if not os.path.exists(jetbrains_path):
        try:
            urllib.request.urlretrieve(
                "https://github.com/jetbrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-Regular.ttf",
                jetbrains_path
            )
            fonts_downloaded = True
        except:
            pass
    
    if not os.path.exists(inter_path):
        try:
            urllib.request.urlretrieve(
                "https://github.com/rsms/inter/releases/download/v3.19.01/Inter-Regular.ttf",
                inter_path
            )
            fonts_downloaded = True
        except:
            pass
    
    if os.path.exists(jetbrains_path):
        fm.fontManager.addfont(jetbrains_path)
    if os.path.exists(inter_path):
        fm.fontManager.addfont(inter_path)
    
    available_fonts = []
    for f in fm.findSystemFonts(fontpaths=[font_dir]):
        try:
            font_name = fm.FontProperties(fname=f).get_name()
            available_fonts.append(font_name)
        except:
            pass
    
    font_family = 'DejaVu Sans'
    for font in ['JetBrains Mono', 'Inter', 'DejaVu Sans']:
        if font in available_fonts:
            font_family = font
            break
    
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': [font_family, 'Arial', 'sans-serif'],
        'font.size': 10,
        'axes.titlesize': 12,
        'axes.labelsize': 10,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9,
        'figure.titlesize': 14,
    })
    
    return font_family

def create_training_graph(experiments_history: List[Dict[str, Any]], 
                          metric: str = 'accuracy',
                          benchmark_score: float = 0.85):
    fig, ax = plt.subplots(figsize=(10, 6))
    
    iterations = []
    scores = []
    colors = []
    
    for exp in experiments_history:
        if exp.get('success', False):
            iterations.append(exp['iteration'])
            score = exp['metrics'].get(metric, 0)
            scores.append(score)
            if score >= benchmark_score:
                colors.append('#28a745')
            else:
                colors.append('#007bff')
    
    if not iterations:
        ax.text(0.5, 0.5, 'No successful experiments yet', 
                ha='center', va='center', transform=ax.transAxes, fontsize=12)
        ax.set_title('Training Progress')
        return fig
    
    for i, (iter_, score, color) in enumerate(zip(iterations, scores, colors)):
        ax.scatter(iter_, score, c=color, s=100, zorder=5, edgecolors='black', linewidth=0.5)
    
    if len(iterations) > 1:
        ax.plot(iterations, scores, color='#6c757d', linestyle='-', linewidth=1.5, alpha=0.7)
    
    ax.axhline(y=benchmark_score, color='#28a745', linestyle='--', linewidth=2, 
               label=f'Benchmark: {benchmark_score:.2f}')
    
    best_score = max(scores) if scores else 0
    best_iter = iterations[scores.index(best_score)] if scores else 0
    ax.scatter([best_iter], [best_score], c='#ffc107', s=150, marker='*', 
               zorder=6, edgecolors='black', linewidth=1, label=f'Best: {best_score:.4f}')
    
    ax.fill_between(iterations, 0, scores, alpha=0.2, color='#007bff')
    
    ax.set_xlabel('Iteration', fontsize=10, fontweight='bold')
    ax.set_ylabel(f'{metric.title()}', fontsize=10, fontweight='bold')
    ax.set_title('Training Progress Benchmark', fontsize=14, fontweight='bold')
    ax.legend(loc='best', framealpha=0.9)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.05)
    
    if scores:
        auc = np.trapz(scores, iterations) / len(iterations) if len(iterations) > 1 else scores[0]
        ax.text(0.02, 0.98, f'Progress Score: {auc:.4f}', transform=ax.transAxes, 
                fontsize=10, verticalalignment='top', 
                bbox=dict(boxstyle='round', facecolor='#f8f9fa', alpha=0.8))
    
    plt.tight_layout()
    return fig

def create_confidence_band(experiments_history: List[Dict[str, Any]], 
                           metric: str = 'accuracy'):
    fig, ax = plt.subplots(figsize=(10, 6))
    
    successful = [e for e in experiments_history if e.get('success', False)]
    if len(successful) < 2:
        return create_training_graph(experiments_history, metric)
    
    iterations = [e['iteration'] for e in successful]
    scores = [e['metrics'].get(metric, 0) for e in successful]
    
    window_size = min(3, len(scores))
    smoothed = []
    for i in range(len(scores)):
        start = max(0, i - window_size // 2)
        end = min(len(scores), i + window_size // 2 + 1)
        smoothed.append(np.mean(scores[start:end]))
    
    ax.plot(iterations, scores, 'o-', color='#007bff', markersize=8, 
            alpha=0.5, label='Raw Scores')
    ax.plot(iterations, smoothed, '-', color='#28a745', linewidth=2.5, 
            label=f'Smoothed (window={window_size})')
    
    mean_score = np.mean(scores)
    std_score = np.std(scores)
    ax.fill_between(iterations, 
                    [max(0, s - std_score) for s in smoothed],
                    [min(1, s + std_score) for s in smoothed],
                    alpha=0.3, color='#28a745', label=f'±1 Std Dev')
    
    ax.axhline(y=mean_score, color='#ffc107', linestyle=':', linewidth=2,
               label=f'Mean: {mean_score:.4f}')
    
    ax.set_xlabel('Iteration', fontsize=11, fontweight='bold')
    ax.set_ylabel(f'{metric.title()}', fontsize=11, fontweight='bold')
    ax.set_title('Training Confidence Band Analysis', fontsize=14, fontweight='bold')
    ax.legend(loc='lower right', framealpha=0.9)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.05)
    
    plt.tight_layout()
    return fig

def get_best_benchmark_score(experiments_history: List[Dict[str, Any]], 
                             benchmark_thresholds: List[float] = None) -> Dict[str, Any]:
    if benchmark_thresholds is None:
        benchmark_thresholds = [0.7, 0.75, 0.8, 0.85, 0.9, 0.95]
    
    successful = [e for e in experiments_history if e.get('success', False)]
    if not successful:
        return {'score': 0, 'benchmark': None, 'status': 'No successful experiments'}
    
    best_score = max(e['metrics'].get('accuracy', 0) for e in successful)
    
    reached = None
    for threshold in sorted(benchmark_thresholds, reverse=True):
        if best_score >= threshold:
            reached = threshold
            break
    
    next_benchmark = None
    for threshold in sorted(benchmark_thresholds):
        if best_score < threshold:
            next_benchmark = threshold
            break
    
    if best_score >= 0.95:
        status = 'Outstanding!'
    elif best_score >= 0.9:
        status = 'Excellent'
    elif best_score >= 0.85:
        status = 'Good'
    elif best_score >= 0.8:
        status = 'Fair'
    else:
        status = 'Needs Improvement'
    
    return {
        'score': best_score,
        'benchmark': reached,
        'next_benchmark': next_benchmark,
        'status': status,
        'distance_to_next': (next_benchmark - best_score) if next_benchmark else 0
    }


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
    """Create real-time training progress chart with Plotly"""
    
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
