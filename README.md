# 🤖 MiniML Lab - Autonomous ML Experimentation Platform

An intelligent ML automation framework powered by LLM agents, enabling autonomous generation, execution, and optimization of ML models.

## 📋 Features

### 🧠 Autonomous ML Agent
- **LLM-Powered Code Generation**: Uses OpenRouter API (Llama 2, GPT-4, Claude) to generate Python training scripts
- **Self-Correcting Loops**: Analyzes failures and automatically improves code
- **Iterative Learning**: Learns from previous experiments to make better models
- Inspired by Karpathy's autoresearch approach

### 🛡️ Sandboxed Execution
- **Secure Subprocess Isolation**: AI-generated code runs in isolated subprocess
- **Runtime Error Capturing**: Automatically captures and logs execution errors
- **Timeout Protection**: 60-second execution timeout prevents infinite loops
- **Resource Management**: Clean temporary file handling

### 📊 Data Pipeline
- **Synthetic Data Generation**: Create classification/regression datasets on-demand
- **CSV Upload Support**: Load your own datasets
- **Automated Preprocessing**:
  - Missing value handling (median for numeric, mode for categorical)
  - Categorical encoding with LabelEncoder
  - Feature scaling with StandardScaler
  - Train/test splitting with stratification

### 📈 Interactive Dashboard
- **Real-time Monitoring**: Track agent reasoning and experiment progress
- **Performance Metrics**: View accuracy, precision, recall, and F1 scores
- **Visualization**: Plotly charts for performance trends
- **One-Click Downloads**: Export models, code, and metadata

### 💾 Model Management
- **Artifact Storage**: Save models, training code, and metadata
- **Performance Tracking**: Complete experiment history with metrics
- **Model Comparison**: Identify best performing models
- **Report Generation**: Automated experiment summaries

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenRouter API key (get at https://openrouter.ai)

### Installation

1. **Clone and setup environment**
```bash
cd MiniML-Lab
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure API**
```bash
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

### Running the Application

```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

## 📚 Project Structure

```
MiniML-Lab/
├── app.py                 # Main Streamlit application
├── llm_agent.py          # Autonomous ML agent implementation
├── data_pipeline.py      # Data preprocessing and analysis
├── model_manager.py      # Model artifact management
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variables template
└── README.md             # This file
```

## 🔧 Configuration

### Environment Variables (.env)

```env
# API Configuration
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=meta-llama/llama-2-70b-chat

# Execution Settings
MAX_EXECUTION_TIME=30          # Seconds
MAX_RETRIES=3                  # Number of retries
SANDBOX_TIMEOUT=60             # Seconds

# Data Settings
MAX_UPLOAD_SIZE_MB=100
SUPPORTED_FILE_TYPES=csv,xlsx,json

# Logging
LOG_LEVEL=INFO
DEBUG_MODE=False
```

### Streamlit Settings

Access settings in the left sidebar:
- **API Settings**: Configure OpenRouter API and model selection
- **Data Settings**: Choose between synthetic/uploaded data
- **Experiment Settings**: Configure iteration limits and auto-improvement

## 💡 Usage Guide

### 1. Data Preparation

1. Navigate to **Data Preparation** tab
2. Choose data source:
   - **Synthetic Data**: Auto-generate dataset for testing
   - **Upload CSV**: Use your own data
3. Preview data and review statistics

### 2. Agent Initialization

1. Enter OpenRouter API key in sidebar
2. Click **Initialize Agent** button
3. Agent is ready for experiments

### 3. Run Experiments

- **Run Single Iteration**: Generate, execute, and evaluate one model
- **Run Multiple**: Automatically improve over multiple iterations
- Agent automatically handles failures with self-correction

### 4. Monitor Results

- **Experiment Log**: View each iteration's status and metrics
- **Performance Trends**: Visualize accuracy improvement over time
- **Detailed Report**: Download comprehensive analysis

### 5. Download Models

- **Model File**: Serialized pickle object (.pkl)
- **Training Code**: Python script that trained the model (.py)
- **Metadata**: Model metrics and configuration (.json)

## 🏗️ Architecture

### Agent Loop

```
┌─────────────────────────────────────┐
│  Generate Experiment Code (LLM)     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Execute Code (Sandbox)             │
└──────────────┬──────────────────────┘
               │
          ┌────┴────┐
          │          │
       Success    Failure
          │          │
          │          ▼
          │  ┌──────────────────────┐
          │  │ Analyze Error (LLM)  │
          │  └──────────┬───────────┘
          │             │
          │             ▼
          │  ┌──────────────────────┐
          │  │ Generate Fix         │
          │  └──────────┬───────────┘
          │             │
          └─────┬───────┘
                │
                ▼
        ┌──────────────────┐
        │  Store Results   │
        └──────────────────┘
```

### Data Pipeline

```
Input Data
    │
    ├─→ [Synthetic] Generate random features
    │
    └─→ [CSV Upload] Parse and validate
            │
            ▼
    [Analysis] Extract metadata
            │
            ├─→ Identify feature types
            ├─→ Count missing values
            └─→ Check data distribution
            │
            ▼
    [Preprocessing]
            │
            ├─→ Handle missing values
            ├─→ Encode categorical features
            ├─→ Scale numeric features
            └─→ Split train/test
            │
            ▼
        Ready for ML
```

## 🔐 Security Considerations

### Code Execution Safety
- ✅ Subprocess isolation prevents access to host system
- ✅ 60-second timeout prevents infinite loops
- ✅ Generated code is inspected before execution in production
- ⚠️ Never run with untrusted API keys

### Data Privacy
- ✅ Data processed locally, not sent to external services
- ✅ Models saved to local filesystem
- ⚠️ API calls to OpenRouter may send dataset summaries

### Best Practices
1. Use dedicated API key with API limits
2. Run on isolated machine for sensitive data
3. Monitor execution logs for anomalies
4. Validate generated code before production

## 📊 Supported Models

### Classification Models Generated
- Logistic Regression
- Random Forest
- Gradient Boosting
- SVM
- Neural Networks (via sklearn)

### Regression Models
- Linear Regression
- Ridge/Lasso
- Random Forest Regressor
- Gradient Boosting Regressor

### LLM Options (via OpenRouter)
- Meta Llama 2 70B
- OpenAI GPT-3.5 Turbo
- OpenAI GPT-4
- Anthropic Claude 2
- And 100+ more

## 🧪 Example Workflows

### Workflow 1: Quick Classification Test
```
1. Use Synthetic Data → Classification → 200 samples
2. Run Single Iteration → View generated code
3. Check Performance → Download best model
```

### Workflow 2: Improve Existing Dataset
```
1. Upload your CSV file
2. Run Multiple Iterations (5 loops)
3. View performance trends
4. Download best model and code
```

### Workflow 3: Debug Failed Experiments
```
1. Run iteration → See failure
2. Enable "Auto-Improve on Failure"
3. Agent analyzes error and fixes code
4. Retry with improved version
```

## 🐛 Troubleshooting

### Issue: "API Key not found"
**Solution**: Ensure OPENROUTER_API_KEY is set in .env file

### Issue: "Timeout during code execution"
**Solution**: Increase MAX_EXECUTION_TIME in .env or simplify model

### Issue: "Out of memory"
**Solution**: Reduce n_samples in data settings or run on machine with more RAM

### Issue: "Cannot find module 'xxx'"
**Solution**: Run `pip install -r requirements.txt` again

## 📈 Performance Tips

1. **Start Small**: Begin with synthetic data and few features
2. **Monitor Logs**: Check experiment logs for patterns in failures
3. **Adjust Temperature**: Lower for more deterministic code, higher for creativity
4. **Use Better Models**: GPT-4 generates more reliable code than Llama 2
5. **Increase Max Retries**: More iterations = better refinement

## 📝 Logging

Logs are stored in console output. Configure in .env:
```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
DEBUG_MODE=True # Enables detailed output
```

## 🤝 Contributing

Contributions welcome! Areas for enhancement:
- Additional preprocessing strategies
- Support for time-series models
- AutoML integration (AutoGluon, TPOT)
- Distributed experiment execution
- GPU support

## 📜 License

MIT License - See LICENSE file

## 🔗 Resources

- **OpenRouter Docs**: https://openrouter.ai/docs
- **Streamlit Docs**: https://docs.streamlit.io
- **Scikit-Learn Docs**: https://scikit-learn.org
- **Karpathy's AutoResearch**: https://github.com/karpathy/researcher

## 🎯 Roadmap

- [ ] Support for deep learning models (PyTorch, TensorFlow)
- [ ] Hyperparameter optimization with Optuna
- [ ] Ensemble model generation
- [ ] Feature engineering automation
- [ ] Multi-objective optimization
- [ ] Distributed execution
- [ ] WebUI with real-time visualization
- [ ] REST API

## 📧 Support

For issues, questions, or suggestions:
1. Check troubleshooting section
2. Review logs for error messages
3. Open GitHub issue with details

---

**Made with ❤️ for the ML community**

Happy experimenting! 🚀