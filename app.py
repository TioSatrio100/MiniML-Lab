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

st.set_page_config(page_title="MiniML Lab", page_icon="🤖", layout="wide")

def init_session_state():
    if 'agent' not in st.session_state: st.session_state.agent = None
    if 'preprocessor' not in st.session_state: st.session_state.preprocessor = DataPreprocessor()
    if 'model_manager' not in st.session_state: 
        st.session_state.model_manager = create_model_manager(os.path.join(os.getcwd(), "models"))
    if 'experiment_tracker' not in st.session_state: st.session_state.experiment_tracker = create_experiment_tracker()
    
    # State untuk Data
    if 'current_dataset' not in st.session_state: st.session_state.current_dataset = None
    if 'current_target' not in st.session_state: st.session_state.current_target = None
    
    # State untuk Konfigurasi
    if 'api_key' not in st.session_state: st.session_state.api_key = ""
    if 'selected_model' not in st.session_state: st.session_state.selected_model = "meta-llama/llama-3-8b-instruct:free"
    if 'task_type' not in st.session_state: st.session_state.task_type = "classification"
    if 'data_source' not in st.session_state: st.session_state.data_source = "Synthetic Data"
    
    # State untuk Tracking Best Model
    if 'best_accuracy_so_far' not in st.session_state: st.session_state.best_accuracy_so_far = 0.0
    if 'best_model_name' not in st.session_state: st.session_state.best_model_name = "None"

init_session_state()

with st.sidebar:
    st.markdown("## ⚙️ Config")
    st.text_input("API Key", value=st.session_state.api_key, type="password", key="api_key_input")
    st.selectbox("Model", ["meta-llama/llama-3-8b-instruct:free", "microsoft/phi-3-mini-128k-instruct:free", "baidu/cobuddy:free"], key="selected_model")
    st.radio("Source", ["Synthetic", "Upload"], key="data_source")
    st.selectbox("Task", ["classification", "regression"], key="task_type")
    
    if st.session_state.data_source == "Synthetic":
        st.slider("Samples", 50, 1000, 200, key="n_samples")
        st.slider("Features", 5, 50, 10, key="n_features")
    else:
        uploaded_file = st.file_uploader("CSV", type="csv")

    st.slider("Iterations", 1, 10, 3, key="max_iterations")

def main():
    st.markdown("# 🤖 MiniML Lab: Auto-Improving Agent")
    
    # Sync API Key
    if 'api_key_input' in st.session_state: st.session_state.api_key = st.session_state.api_key_input
    if not st.session_state.api_key:
        st.warning("⚠️ Enter API Key.")
        return

    # Display Best Model Status
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🏆 Best Accuracy So Far", f"{st.session_state.best_accuracy_so_far:.4f}")
    with col2:
        st.metric("📦 Best Model Name", st.session_state.best_model_name)

    tab1, tab2, tab3 = st.tabs(["📊 Data", "🚀 Run Auto-ML", "💾 Artifacts"])
    
    # TAB 1: DATA
    with tab1:
        if st.session_state.data_source == "Synthetic":
            if st.button("Generate Data"):
                df = st.session_state.preprocessor.generate_synthetic_data(st.session_state.task_type, st.session_state.n_samples, st.session_state.n_features)
                st.session_state.current_dataset = df
                st.session_state.current_target = 'target'
                st.success("Data Generated")
        else:
            if 'uploaded_file' in locals() and uploaded_file:
                df, target = st.session_state.preprocessor.load_csv_data(uploaded_file.read(), None)
                st.session_state.current_dataset = df
                st.session_state.current_target = target
                st.success("Data Loaded")
        
        if st.session_state.current_dataset is not None:
            st.dataframe(st.session_state.current_dataset.head(), width='stretch')

    # TAB 2: RUN
    with tab2:
        if st.session_state.current_dataset is None:
            st.warning("Prepare data first.")
            return
        
        if st.session_state.agent is None:
            if st.button("Initialize Agent"):
                try:
                    st.session_state.agent = create_agent(st.session_state.api_key, st.session_state.selected_model)
                    st.success("Agent Ready")
                except Exception as e: st.error(str(e))
        else:
            st.info("Agent Ready. Click 'Start Auto-ML Loop' to begin.")
            if st.button("🚀 Start Auto-ML Loop", type="primary"):
                run_auto_ml_loop(st.session_state.max_iterations)

    # TAB 3: ARTIFACTS
    with tab3:
        models = st.session_state.model_manager.list_models()
        if not models:
            st.info("No best models saved yet. Run experiments to find one.")
        else:
            st.success(f"Found {len(models)} Top Models")
            for m in models:
                with st.expander(f"🏆 {m['name']} (Acc: {m['metrics'].get('accuracy', 0):.4f})"):
                    st.json(m['metrics'])
                    if 'model' in m['artifacts'] and os.path.exists(m['artifacts']['model']):
                        with open(m['artifacts']['model'], 'rb') as f:
                            st.download_button("Download Best Model", f.read(), file_name=os.path.basename(m['artifacts']['model']))

def run_auto_ml_loop(num_iterations: int):
    """
    Loop utama yang menjalankan iterasi, memperbaiki diri, dan HANYA menyimpan jika lebih baik.
    """
    progress_bar = st.progress(0)
    status_text = st.empty()
    log_container = st.empty()
    
    agent = st.session_state.agent
    preprocessor = st.session_state.preprocessor
    model_manager = st.session_state.model_manager
    
    # Siapkan data
    data_path = os.path.join(tempfile.gettempdir(), "mini_ml_data.csv")
    st.session_state.current_dataset.to_csv(data_path, index=False)
    
    logs = []

    for i in range(num_iterations):
        status_text.text(f"🔄 Iteration {i+1}/{num_iterations}... Analyzing & Coding...")
        
        try:
            # 1. Generate Code (dengan context history)
            dataset_info = preprocessor.analyze_data(st.session_state.current_dataset, st.session_state.current_target)
            code = asyncio.run(agent.generate_experiment_code(
                dataset_info=dataset_info.__dict__,
                previous_results=agent.history, # Agent melihat history di sini
                task=st.session_state.task_type
            ))
            
            status_text.text(f"⚙️ Iteration {i+1}: Executing...")
            
            # 2. Execute
            start = time.time()
            result = asyncio.run(agent.execute_code(code, data_path))
            duration = time.time() - start
            
            # 3. Evaluate & Decide to Save
            current_acc = result.metrics.get('accuracy', 0) if result.metrics else 0
            best_acc = st.session_state.best_accuracy_so_far
            
            log_msg = f"Iter {i+1}: Acc={current_acc:.4f} | Status={result.state.value}"
            
            if result.state == AgentState.COMPLETED:
                if current_acc > best_acc:
                    # NEW RECORD! Simpan model
                    with st.spinner(f"✨ New Best Model Found! ({current_acc:.4f} > {best_acc:.4f}) Saving..."):
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
                                # Update Global State
                                st.session_state.best_accuracy_so_far = current_acc
                                st.session_state.best_model_name = model_name
                                log_msg += " | 🏆 NEW BEST SAVED"
                        except Exception as e:
                            log_msg += f" | Save Error: {e}"
                else:
                    log_msg += f" | Discarded (Best: {best_acc:.4f})"
            else:
                log_msg += f" | Failed: {result.error[:50]}"
                
            # Log ke tracker
            st.session_state.experiment_tracker.log_experiment(
                iteration=i+1, code=code, execution_time=duration, 
                success=(result.state==AgentState.COMPLETED), 
                metrics=result.metrics, error=result.error
            )
            
            logs.append(log_msg)
            log_container.code("\n".join(logs[-5:])) # Tampilkan 5 log terakhir
            
        except Exception as e:
            logs.append(f"Iter {i+1}: CRITICAL ERROR - {str(e)}")
            log_container.code("\n".join(logs[-5:]))

        progress_bar.progress((i + 1) / num_iterations)
    
    status_text.text("✅ Auto-ML Loop Completed!")
    st.balloons()
    st.rerun() # Refresh untuk update metric di atas

if __name__ == "__main__":
    main()