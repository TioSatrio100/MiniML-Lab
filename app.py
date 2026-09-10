"""
app.py - MiniML Lab (Best Model Only Strategy)
"""
import streamlit as st
import pandas as pd
import asyncio
import os
import tempfile
import time
import pickle
import plotly.graph_objects as go

from llm_agent import create_agent, AgentState
from data_pipeline import DataPreprocessor
from model_manager import create_model_manager, create_experiment_tracker
from visualization import create_training_progress_chart, get_task_metric

st.set_page_config(page_title="MiniML Lab", page_icon="🤖", layout="wide")

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg-cream: #fbfbfa;
    --text-dark: #111111;
    --text-muted: #555555;
    --border-soft: #e5e5e0;
    --accent-coral: #e06c53;
    --accent-coral-light: #f5a88e;
    --code-bg: #f5f2ef;
}

.stApp {
    background-color: var(--bg-cream);
    background-image: radial-gradient(circle, #d0d0d0 1px, transparent 1px);
    background-size: 24px 24px;
    font-family: 'Inter', sans-serif;
}

[data-testid="stHeader"] {
    background-color: transparent;
}

[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid var(--border-soft);
}

[data-testid="stSidebar"] * {
    font-family: 'Inter', sans-serif;
}

[data-testid="stSidebar"] .stMarkdown {
    color: var(--text-dark);
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    color: var(--text-dark);
    letter-spacing: -0.02em;
    line-height: 1.2;
}

p, span, label, .stMarkdown {
    font-family: 'Inter', sans-serif;
    color: var(--text-muted);
}

.eyebrow-text {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #888888;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}

.hero-title {
    font-size: 3rem;
    font-weight: 800;
    color: var(--text-dark);
    line-height: 1.1;
    letter-spacing: -0.03em;
    margin-bottom: 1rem;
}

.hero-subtitle {
    font-size: 1.1rem;
    color: var(--text-muted);
    line-height: 1.6;
    max-width: 500px;
}

.code-block {
    background-color: var(--code-bg);
    border: 1px solid var(--border-soft);
    border-radius: 8px;
    padding: 1.5rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    color: var(--text-dark);
    overflow-x: auto;
}

.code-block .keyword {
    color: var(--accent-coral);
}

.code-block .string {
    color: #2a9d8f;
}

.code-block .comment {
    color: #999999;
}

.stMetric {
    background-color: #ffffff;
    border: 1px solid var(--border-soft);
    border-radius: 12px;
    padding: 1.25rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.stMetric label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
}

.stMetric value {
    font-family: 'Inter', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-dark);
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    border-bottom: 1px solid var(--border-soft);
}

.stTabs [data-baseweb="tab"] {
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    font-size: 0.9rem;
    color: var(--text-muted);
    padding: 0.75rem 1.25rem;
    border-radius: 8px 8px 0 0;
    border: none;
    background-color: transparent;
}

.stTabs [aria-selected="true"] {
    color: var(--text-dark);
    background-color: #ffffff;
    border: 1px solid var(--border-soft);
    border-bottom: 1px solid #ffffff;
    margin-bottom: -1px;
}

.stButton > button {
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    border-radius: 8px;
    padding: 0.5rem 1.25rem;
    border: 1px solid var(--border-soft);
    background-color: #ffffff;
    color: var(--text-dark);
    transition: all 0.2s ease;
}

.stButton > button:hover {
    border-color: var(--accent-coral);
    color: var(--accent-coral);
}

.stButton > button[kind="primary"] {
    background-color: var(--accent-coral);
    color: #ffffff;
    border-color: var(--accent-coral);
}

.stButton > button[kind="primary"]:hover {
    background-color: #c85a42;
    border-color: #c85a42;
    color: #ffffff;
}

.stTextInput input, .stSelectbox select, .stTextArea textarea, .stRadio label {
    font-family: 'Inter', sans-serif;
    border-radius: 6px;
}

.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--accent-coral);
    box-shadow: 0 0 0 1px var(--accent-coral);
}

.stDataFrame {
    border: 1px solid var(--border-soft);
    border-radius: 8px;
    overflow: hidden;
}

.stExpander {
    border: 1px solid var(--border-soft);
    border-radius: 8px;
    background-color: #ffffff;
}

.stAlert {
    border-radius: 8px;
    border: 1px solid var(--border-soft);
}

.stAlert-success {
    background-color: #f0f9f4;
    border-color: #a8d5ba;
}

.stAlert-warning {
    background-color: #fff8f0;
    border-color: #ffd6a5;
}

.stAlert-info {
    background-color: #f0f7ff;
    border-color: #a8c5e0;
}

.stAlert-error {
    background-color: #fef0f0;
    border-color: #f5a8a8;
}

.hero-container {
    display: flex;
    gap: 3rem;
    align-items: center;
    margin-bottom: 3rem;
}

.hero-left {
    flex: 1;
}

.hero-right {
    flex: 1;
}

@media (max-width: 768px) {
    .hero-container {
        flex-direction: column;
    }
    .hero-title {
        font-size: 2rem;
    }
}

.divider {
    height: 1px;
    background: linear-gradient(to right, transparent, var(--border-soft), transparent);
    margin: 2rem 0;
}

.status-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.status-badge-active {
    background-color: #e8f5e9;
    color: #2e7d32;
}

.status-badge-idle {
    background-color: #f5f5f5;
    color: #757575;
}

.progress-container {
    background-color: #ffffff;
    border: 1px solid var(--border-soft);
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1rem 0;
}

.summary-card {
    background-color: #ffffff;
    border: 1px solid var(--border-soft);
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def init_session_state():
    if 'agent' not in st.session_state: st.session_state.agent = None
    if 'preprocessor' not in st.session_state: st.session_state.preprocessor = DataPreprocessor()
    if 'model_manager' not in st.session_state: 
        st.session_state.model_manager = create_model_manager(os.path.join(os.getcwd(), "models"))
    if 'experiment_tracker' not in st.session_state: st.session_state.experiment_tracker = create_experiment_tracker()
    
    if 'current_dataset' not in st.session_state: st.session_state.current_dataset = None
    if 'current_target' not in st.session_state: st.session_state.current_target = None
    if 'uploaded_file' not in st.session_state: st.session_state.uploaded_file = None
    
    if 'api_key' not in st.session_state: st.session_state.api_key = ""
    if 'selected_model' not in st.session_state: st.session_state.selected_model = "gpt-4o-mini"
    if 'base_url' not in st.session_state: st.session_state.base_url = "https://ai.sumopod.com/v1"
    if 'task_type' not in st.session_state: st.session_state.task_type = "classification"
    if 'data_source' not in st.session_state: st.session_state.data_source = "Synthetic (Random)"
    if 'ai_description' not in st.session_state: st.session_state.ai_description = ""
    if 'last_data_code' not in st.session_state: st.session_state.last_data_code = None
    if 'max_iterations' not in st.session_state: st.session_state.max_iterations = 3
    
    if 'best_accuracy_so_far' not in st.session_state: st.session_state.best_accuracy_so_far = 0.0
    if 'best_model_name' not in st.session_state: st.session_state.best_model_name = "None"
    if 'best_score_so_far' not in st.session_state: st.session_state.best_score_so_far = 0.0

init_session_state()

with st.sidebar:
    st.markdown('<p class="eyebrow-text">CONFIGURATION</p>', unsafe_allow_html=True)
    st.markdown("### Settings")
    
    st.text_input("API Key", value=st.session_state.api_key, type="password", key="api_key_input")
    st.text_input("Base URL", value=st.session_state.base_url, key="base_url_input", help="API endpoint URL")
    
    # Enhanced Model Selection
    st.markdown("#### LLM Model")
    st.markdown("Choose or enter a model name")
    
    # Preset model options
    common_models = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "claude-3-haiku", "claude-3-sonnet", "claude-3-opus"]
    
    # Create tabs for quick selection or custom input
    model_tab1, model_tab2 = st.tabs(["Presets", "Custom"])
    
    with model_tab1:
        selected_preset = st.selectbox(
            "Popular Models:",
            common_models,
            index=common_models.index(st.session_state.selected_model) if st.session_state.selected_model in common_models else 0,
            key="model_preset_select"
        )
        st.session_state.selected_model = selected_preset
    
    with model_tab2:
        custom_model = st.text_input(
            "Enter model name:",
            value=st.session_state.selected_model,
            placeholder="e.g., gpt-4o-mini",
            key="model_input"
        )
        if custom_model:
            st.session_state.selected_model = custom_model
    
    # Display current model
    st.info(f"📌 Using: **{st.session_state.selected_model}**")
    
    if 'base_url_input' in st.session_state:
        st.session_state.base_url = st.session_state.base_url_input
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<p class="eyebrow-text">TASK TYPE</p>', unsafe_allow_html=True)
    
    task_type = st.radio(
        "Task",
        ["classification", "regression", "clustering", "recommendation"],
        index=["classification", "regression", "clustering", "recommendation"].index(st.session_state.task_type),
        key="task_type_radio",
        label_visibility="collapsed"
    )
    st.session_state.task_type = task_type
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<p class="eyebrow-text">DATA SOURCE</p>', unsafe_allow_html=True)
    
    if task_type in ["clustering", "recommendation"]:
        st.info(f"This task type requires AI-generated data with specific structure.")
        st.session_state.data_source = "AI-Generated (Smart)"
        data_source_option = "AI-Generated (Smart)"
    else:
        data_source_option = st.radio(
            "Source", 
            ["Synthetic (Random)", "AI-Generated (Smart)", "Upload CSV"], 
            key="data_source_radio",
            label_visibility="collapsed"
        )
        st.session_state.data_source = data_source_option

    if data_source_option == "AI-Generated (Smart)":
        st.session_state.ai_description = st.text_area(
            "Describe the data you need:",
            value=st.session_state.ai_description,
            placeholder="e.g., Customer data with age, income, and churn target" if task_type == "classification" else
                        "e.g., House prices with sqft, bedrooms, location" if task_type == "regression" else
                        "e.g., Customer behavior data for segmentation" if task_type == "clustering" else
                        "e.g., Movie ratings with user_id, movie_id, genres",
            height=80,
            key="ai_desc_input"
        )
        
    if data_source_option in ["Synthetic (Random)", "AI-Generated (Smart)"]:
        st.slider("Samples", 50, 1000, 200, key="n_samples")
    if data_source_option == "Synthetic (Random)":
        st.slider("Features", 5, 50, 10, key="n_features")
    elif data_source_option == "Upload CSV":
        uploaded_file = st.file_uploader("Upload CSV", type="csv")
        if uploaded_file:
            st.session_state.uploaded_file = uploaded_file
        else:
            st.session_state.uploaded_file = None

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.slider("Max Iterations", 1, 10, 3, key="max_iterations")

def render_hero():
    hero_col1, hero_col2 = st.columns([1, 1])
    
    with hero_col1:
        st.markdown('<p class="eyebrow-text">AUTONOMOUS ML PLATFORM</p>', unsafe_allow_html=True)
        st.markdown('<h1 class="hero-title">MiniML Lab</h1>', unsafe_allow_html=True)
        st.markdown('<p class="hero-subtitle">An intelligent ML automation framework powered by LLM agents. Generate, execute, and optimize models autonomously through iterative self-improvement.</p>', unsafe_allow_html=True)
        st.markdown('')
        status_class = "status-badge-active" if st.session_state.api_key else "status-badge-idle"
        status_text = "READY" if st.session_state.api_key else "NO API KEY"
        st.markdown(f'<span class="status-badge {status_class}">{status_text}</span>', unsafe_allow_html=True)
    
    with hero_col2:
        code_snippet = '''<span class="comment"># Auto-ML in 3 lines</span>
<span class="keyword">from</span> miniml <span class="keyword">import</span> Agent

agent = Agent(model=<span class="string">"gpt-4o-mini"</span>)
result = agent.run(data)

<span class="keyword">print</span>(result.accuracy)
<span class="comment"># → 0.94</span>'''
        st.markdown(f'<div class="code-block">{code_snippet}</div>', unsafe_allow_html=True)

def main():
    render_hero()
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    if 'api_key_input' in st.session_state: st.session_state.api_key = st.session_state.api_key_input
    if not st.session_state.api_key:
        st.warning("Enter your API Key in the sidebar to begin.")
        return

    metric, metric_label, _ = get_task_metric(st.session_state.task_type)
    
    metric_col1, metric_col2 = st.columns(2)
    with metric_col1:
        st.metric(f"Best {metric_label}", f"{st.session_state.best_score_so_far:.4f}")
    with metric_col2:
        st.metric("Best Model", st.session_state.best_model_name)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["Data", "Run Auto-ML", "Artifacts", "Progress"])
    
    with tab1:
        render_data_tab()

    with tab2:
        render_run_tab()

    with tab3:
        render_artifacts_tab()

    with tab4:
        render_progress_tab()

def render_data_tab():
    data_source = st.session_state.data_source
    
    if data_source == "Synthetic (Random)":
        if st.button("Generate Data"):
            with st.spinner("Generating synthetic data..."):
                df = st.session_state.preprocessor.generate_synthetic_data(
                    st.session_state.task_type, 
                    st.session_state.n_samples, 
                    st.session_state.n_features
                )
                st.session_state.current_dataset = df
                if st.session_state.task_type in ["classification", "regression"]:
                    st.session_state.current_target = 'target'
                else:
                    st.session_state.current_target = None
                st.success("Data generated successfully.")
                st.rerun()
    
    elif data_source == "AI-Generated (Smart)":
        if not st.session_state.ai_description:
            st.warning("Please describe the data you need in the sidebar.")
            return
        
        if st.button("Generate Data with AI", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("Sending request to AI...")
                progress_bar.progress(10)
                
                status_text.text("AI is generating data script...")
                progress_bar.progress(30)
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                df, target, code = loop.run_until_complete(
                    st.session_state.preprocessor.generate_ai_data(
                        api_key=st.session_state.api_key,
                        model=st.session_state.selected_model,
                        base_url=st.session_state.base_url,
                        user_description=st.session_state.ai_description,
                        n_samples=st.session_state.n_samples,
                        task=st.session_state.task_type
                    )
                )
                loop.close()
                
                st.session_state.last_data_code = code
                
                progress_bar.progress(70)
                status_text.text("Loading generated data...")
                
                st.session_state.current_dataset = df
                st.session_state.current_target = target
                
                progress_bar.progress(100)
                status_text.text("Data generated successfully!")
                time.sleep(0.5)
                
                st.success(f"Data generated: {df.shape[0]} rows, {df.shape[1]} columns")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error generating data: {str(e)}")
                progress_bar.progress(0)
                status_text.text("")
    
    elif data_source == "Upload CSV":
        if st.session_state.get('uploaded_file'):
            if st.button("Load CSV Data"):
                df, target = st.session_state.preprocessor.load_csv_data(
                    st.session_state.uploaded_file.read(), None
                )
                st.session_state.current_dataset = df
                st.session_state.current_target = target
                st.success("Data loaded successfully.")
                st.rerun()
    
    if st.session_state.current_dataset is not None:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("### Data Preview")
        st.dataframe(st.session_state.current_dataset.head(20), use_container_width=True)
        
        if st.session_state.last_data_code:
            with st.expander("View Generated Code"):
                st.code(st.session_state.last_data_code, language="python")

def render_run_tab():
    if st.session_state.current_dataset is None:
        st.warning("Prepare data first in the Data tab.")
        return
    
    # Display current configuration
    st.markdown("### Run Configuration")
    config_col1, config_col2, config_col3 = st.columns(3)
    with config_col1:
        st.metric("Task Type", st.session_state.task_type.title())
    with config_col2:
        st.metric("LLM Model", st.session_state.selected_model)
    with config_col3:
        st.metric("Max Iterations", st.session_state.max_iterations)
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    if st.session_state.agent is None:
        st.markdown("### Initialize Agent")
        st.markdown(f"Ready to use **{st.session_state.selected_model}** for generating ML experiments.")
        if st.button("Initialize Agent", type="primary"):
            try:
                st.session_state.agent = create_agent(
                    api_key=st.session_state.api_key,
                    model=st.session_state.selected_model,
                    base_url=st.session_state.base_url
                )
                st.success(f"✓ Agent initialized with model: {st.session_state.selected_model}")
                st.rerun()
            except Exception as e: st.error(str(e))
    else:
        st.markdown("### Auto-ML Loop")
        st.success(f"✓ Agent is ready. Using model: **{st.session_state.selected_model}** for task: **{st.session_state.task_type}**")
        if st.button("Start Auto-ML Loop", type="primary", key="start_automl"):
            run_auto_ml_loop(st.session_state.max_iterations)

def render_artifacts_tab():
    models = st.session_state.model_manager.list_models()
    if not models:
        st.info("No models saved yet. Run experiments to find the best one.")
    else:
        st.success(f"Found {len(models)} model(s).")
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # Model Selection Section
        st.markdown("### Choose Model to Manage")
        model_options = [f"{m['name']} - {m['metrics'].get('accuracy', 0):.4f}" for m in models]
        selected_idx = st.selectbox("Select a model:", range(len(models)), 
                                     format_func=lambda i: model_options[i], key="model_select")
        
        selected_model = models[selected_idx]
        metric, metric_label, _ = get_task_metric(st.session_state.task_type)
        score = selected_model['metrics'].get(metric, 0)
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # Model Details
        st.markdown("### Model Details")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Current Name", selected_model['name'])
            st.metric(metric_label, f"{score:.4f}")
        with col2:
            st.metric("Timestamp", selected_model['timestamp'])
            st.metric("Metrics Count", len(selected_model['metrics']))
        
        # Display all metrics
        with st.expander("View All Metrics"):
            st.json(selected_model['metrics'])
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # Rename Section
        st.markdown("### Rename Model")
        new_name = st.text_input(
            "New model name:",
            value=selected_model['name'],
            placeholder="Enter new model name",
            key=f"rename_input_{selected_idx}"
        )
        
        col_rename1, col_rename2 = st.columns(2)
        with col_rename1:
            if st.button("Save New Name", type="primary", key=f"rename_btn_{selected_idx}"):
                if new_name and new_name != selected_model['name']:
                    success = st.session_state.model_manager.rename_model(
                        selected_model['model_name'], 
                        new_name
                    )
                    if success:
                        st.success(f"Model renamed to: {new_name}")
                        st.rerun()
                    else:
                        st.error("Failed to rename model")
                else:
                    st.warning("Enter a different name")
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # Download Section
        st.markdown("### Download Model")
        if 'model' in selected_model['artifacts'] and os.path.exists(selected_model['artifacts']['model']):
            with open(selected_model['artifacts']['model'], 'rb') as f:
                st.download_button(
                    "Download Model File",
                    f.read(),
                    file_name=os.path.basename(selected_model['artifacts']['model']),
                    key=f"dl_{selected_model['model_name']}"
                )
        
        # Code Section
        if 'code' in selected_model['artifacts'] and os.path.exists(selected_model['artifacts']['code']):
            with st.expander("View Model Code"):
                with open(selected_model['artifacts']['code'], 'r', encoding='utf-8') as f:
                    st.code(f.read(), language="python")
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # All Models Overview
        st.markdown("### All Saved Models")
        models_df = pd.DataFrame([
            {
                'Name': m['name'],
                metric_label: f"{m['metrics'].get(metric, 0):.4f}",
                'Timestamp': m['timestamp']
            }
            for m in models
        ])
        st.dataframe(models_df, use_container_width=True)

def render_progress_tab():
    experiments = st.session_state.experiment_tracker.experiments
    
    if not experiments:
        st.info("Run experiments to see training progress here.")
        return
    
    st.markdown("### Training Progress")
    fig = create_training_progress_chart(experiments, st.session_state.task_type)
    st.plotly_chart(fig, use_container_width=True, key="progress_chart_tab")
    
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    successful = [e for e in experiments if e.get('success', False)]
    if successful:
        metric, metric_label, higher_is_better = get_task_metric(st.session_state.task_type)
        scores = [e['metrics'].get(metric, 0) for e in successful]
        
        if higher_is_better:
            best_score = max(scores)
            first_score = scores[0]
            improvement = best_score - first_score
        else:
            best_score = min(scores)
            first_score = scores[0]
            improvement = first_score - best_score
        
        st.markdown("### Statistics")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Iterations", len(experiments))
        with col2:
            st.metric("Successful", len(successful))
        with col3:
            st.metric(f"Best {metric_label}", f"{best_score:.4f}")
        with col4:
            st.metric("Improvement", f"{improvement:.4f}")
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # Model Selection and Saving Section
        st.markdown("### Save Model to Artifacts")
        
        # Create options for each successful experiment
        exp_options = []
        for exp in successful:
            iter_num = exp['iteration']
            iter_score = exp['metrics'].get(metric, 0)
            exp_options.append(f"Iteration {iter_num} — {metric_label}: {iter_score:.4f}")
        
        selected_exp_idx = st.selectbox(
            "Choose experiment to save:",
            range(len(successful)),
            format_func=lambda i: exp_options[i],
            key="save_model_select"
        )
        
        selected_exp = successful[selected_exp_idx]
        selected_score = selected_exp['metrics'].get(metric, 0)
        
        st.markdown("#### Selected Experiment Details")
        col_detail1, col_detail2 = st.columns(2)
        with col_detail1:
            st.metric("Iteration", selected_exp['iteration'])
            st.metric("Score", f"{selected_score:.4f}")
        with col_detail2:
            st.metric("Execution Time", f"{selected_exp.get('execution_time', 0):.1f}s")
            st.metric("Status", "✓ Success" if selected_exp['success'] else "✗ Failed")
        
        # Model Name Input
        st.markdown("#### Name Your Model")
        default_name = f"Model_Iter{selected_exp['iteration']}"
        model_name = st.text_input(
            "Model name:",
            value=default_name,
            placeholder="Enter a descriptive name for your model",
            key=f"model_name_input_{selected_exp_idx}"
        )
        
        # Save Button
        if st.button("Save Model to Artifacts", type="primary", key=f"save_model_btn_{selected_exp_idx}"):
            if not model_name:
                st.error("Please enter a model name")
            else:
                try:
                    with st.spinner(f"Saving model '{model_name}'..."):
                        # Get the model code from the experiment
                        exp_code = selected_exp.get('code', '# No code available')
                        
                        # Save to model manager
                        st.session_state.model_manager.save_model(
                            model={"iteration": selected_exp['iteration'], "metrics": selected_exp['metrics']},
                            name=model_name,
                            metrics=selected_exp['metrics'],
                            metadata={
                                "iteration": selected_exp['iteration'],
                                "task_type": st.session_state.task_type
                            },
                            code=exp_code
                        )
                        st.success(f"✓ Model '{model_name}' saved to Artifacts!")
                        st.balloons()
                except Exception as e:
                    st.error(f"Failed to save model: {str(e)}")

def run_auto_ml_loop(num_iterations: int):
    progress_bar = st.progress(0)
    status_text = st.empty()
    log_container = st.empty()
    graph_placeholder = st.empty()
    
    agent = st.session_state.agent
    preprocessor = st.session_state.preprocessor
    model_manager = st.session_state.model_manager
    
    data_path = os.path.join(tempfile.gettempdir(), "mini_ml_data.csv")
    st.session_state.current_dataset.to_csv(data_path, index=False)
    
    logs = []
    metric, metric_label, higher_is_better = get_task_metric(st.session_state.task_type)

    for i in range(num_iterations):
        status_text.text(f"Iteration {i+1}/{num_iterations} — Analyzing & generating code...")
        
        try:
            dataset_info = preprocessor.analyze_data(
                st.session_state.current_dataset, 
                st.session_state.current_target,
                st.session_state.task_type
            )
            code = asyncio.run(agent.generate_experiment_code(
                dataset_info=dataset_info.__dict__,
                previous_results=agent.history,
                task=st.session_state.task_type
            ))
            
            status_text.text(f"Iteration {i+1} — Executing experiment...")
            
            start = time.time()
            result = asyncio.run(agent.execute_code(code, data_path))
            duration = time.time() - start
            
            current_score = result.metrics.get(metric, 0) if result.metrics else 0
            best_score = st.session_state.best_score_so_far
            
            log_msg = f"Iter {i+1}: {metric_label}={current_score:.4f} | Status={result.state.value}"
            
            if result.state == AgentState.COMPLETED:
                is_better = (current_score > best_score) if higher_is_better else (current_score < best_score and current_score > 0)
                
                if is_better:
                    with st.spinner(f"New best model found ({current_score:.4f}). Saving..."):
                        try:
                            if result.saved_model_path and os.path.exists(result.saved_model_path):
                                with open(result.saved_model_path, 'rb') as f:
                                    model_obj = pickle.load(f)
                                
                                model_name = f"BEST_Model_Iter{i+1}"
                                model_manager.save_model(
                                    model=model_obj,
                                    name=model_name,
                                    metrics=result.metrics,
                                    code=code
                                )
                                st.session_state.best_score_so_far = current_score
                                st.session_state.best_model_name = model_name
                                log_msg += " | NEW BEST SAVED"
                        except Exception as e:
                            log_msg += f" | Save Error: {e}"
                else:
                    log_msg += f" | Discarded (Best: {best_score:.4f})"
            else:
                log_msg += f" | Failed: {result.error[:50] if result.error else 'Unknown'}"
                
            st.session_state.experiment_tracker.log_experiment(
                iteration=i+1, code=code, execution_time=duration, 
                success=(result.state==AgentState.COMPLETED), 
                metrics=result.metrics, error=result.error
            )
            
            logs.append(log_msg)
            log_container.code("\n".join(logs[-5:]))
            
            fig = create_training_progress_chart(
                st.session_state.experiment_tracker.experiments,
                st.session_state.task_type
            )
            graph_placeholder.plotly_chart(fig, use_container_width=True, key=f"progress_chart_iter_{i}")
            
        except Exception as e:
            logs.append(f"Iter {i+1}: CRITICAL ERROR - {str(e)}")
            log_container.code("\n".join(logs[-5:]))

        progress_bar.progress((i + 1) / num_iterations)
    
    status_text.text("Auto-ML loop completed.")
    st.balloons()
    st.rerun() 

if __name__ == "__main__":
    main()
