# MiniML Lab - Autonomous ML Experimentation Platform

An intelligent ML automation framework powered by LLM agents. Generate, execute, and optimize models autonomously through iterative self-improvement.

## Features

### 4 Task Types
- **Classification** — Accuracy, Precision, Recall, F1 metrics
- **Regression** — R², RMSE, MAE metrics
- **Clustering** — Silhouette Score, Inertia (unsupervised, AI-generated data only)
- **Recommendation** — Content-based, RMSE, Precision@K (AI-generated data only)

### AI-Powered Agent
- **LLM Code Generation** — Uses SumoPod AI (OpenAI-compatible API) to generate Python training scripts
- **Self-Correcting Loops** — Analyzes failures and automatically improves code
- **Iterative Learning** — Learns from previous experiments to beat the best score
- **Any Model** — Type any model name (gpt-4o-mini, gpt-4o, claude-3-sonnet, etc.)

### Data Pipeline
- **Synthetic Data** — Generate classification/regression datasets on-demand (sklearn)
- **AI-Generated Data** — Describe your dataset in plain English, AI writes the generation script
- **CSV Upload** — Load your own datasets
- **Automated Preprocessing** — Missing values, categorical encoding, feature scaling

### Real-Time Progress Visualization
- **Interactive Plotly Chart** — Metric evolution across iterations with color-coded dots
- **Live Updates** — Graph refreshes after each iteration completes
- **Best Point Highlight** — Star marker on the best iteration
- **Summary Stats** — Total iterations, successful count, best score, improvement

### Design System
- Off-white/cream background with dot-matrix pattern
- Inter font for UI, JetBrains Mono for code/technical elements
- Terracotta/coral (#e06c53) accent color
- Clean card-based layout with soft borders

## Quick Start

### Prerequisites
- Python 3.8+
- SumoPod AI API key (https://ai.sumopod.com)

### Installation

```bash
cd MiniML_Lab
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

### Running

```bash
streamlit run app.py
```

Dashboard opens at `http://localhost:8501`

## Configuration

Configure everything from the sidebar:

| Setting | Description | Default |
|---------|-------------|---------|
| API Key | Your SumoPod AI API key | — |
| Base URL | API endpoint | `https://ai.sumopod.com/v1` |
| Model | Any model name | `gpt-4o-mini` |
| Task Type | classification, regression, clustering, recommendation | classification |
| Data Source | Synthetic, AI-Generated, Upload CSV | Synthetic |
| Max Iterations | Number of Auto-ML iterations | 3 |

### Data Source Restrictions

| Task | Synthetic | AI-Generated | Upload CSV |
|------|-----------|--------------|------------|
| Classification | Yes | Yes | Yes |
| Regression | Yes | Yes | Yes |
| Clustering | — | Yes | — |
| Recommendation | — | Yes | — |

Clustering and Recommendation require AI-generated data because they need specific structures (natural groupings, user-item matrices).

## Usage Guide

### 1. Configure API
Enter your SumoPod AI API key, base URL, and model name in the sidebar.

### 2. Select Task Type
Choose from classification, regression, clustering, or recommendation.

### 3. Prepare Data
- **Synthetic**: Set samples/features and click "Generate Data"
- **AI-Generated**: Describe your dataset, click "Generate Data with AI" (shows progress bar)
- **CSV Upload**: Upload a file and click "Load CSV Data"

### 4. Run Auto-ML
Click "Initialize Agent", then "Start Auto-ML Loop". The agent will:
1. Analyze your data
2. Generate training code
3. Execute in a sandboxed subprocess
4. Evaluate metrics
5. Save only if it beats the previous best
6. Repeat, learning from each iteration

### 5. Monitor Progress
Switch to the **Progress** tab to see:
- Real-time metric chart with color-coded iterations
- Summary cards: total iterations, successful, best score, improvement

### 6. Download Artifacts
In the **Artifacts** tab, download the best model (.pkl), view metrics, and inspect training code.

## Architecture

### Loop Engineering Pattern

MiniML Lab implements **loop engineering** — an iterative feedback loop where the system continuously improves through structured learning cycles.

**Core Loop Components:**

1. **Iterative Feedback Loop** — Each iteration passes the last 3 results (successes + failures) to the LLM as context
2. **Self-Correction** — Failed iterations feed error messages back to the LLM for the next attempt
3. **Progressive Improvement** — Agent is instructed to try different algorithms if metrics are low
4. **Learning Context Builder** — Constructs a prompt showing previous attempts with metrics and errors

**The Loop:**

```
┌─────────────────────────────────────────────────────────────┐
│                    ITERATION N                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐                                       │
│  │ Analyze Data &   │                                       │
│  │ Build Prompt     │◄──── Previous Results (last 3)        │
│  │ (with context)   │      - Iter 1: FAILED (error: ...)    │
│  └────────┬─────────┘      - Iter 2: SUCCESS (acc=0.85)    │
│           │                  - Iter 3: SUCCESS (acc=0.87)   │
│           ▼                                                   │
│  ┌──────────────────┐                                       │
│  │ Generate Code    │                                       │
│  │ (LLM)            │                                       │
│  └────────┬─────────┘                                       │
│           │                                                   │
│           ▼                                                   │
│  ┌──────────────────┐                                       │
│  │ Execute Code     │                                       │
│  │ (Sandboxed)      │                                       │
│  └────────┬─────────┘                                       │
│           │                                                   │
│      ┌────┴────┐                                            │
│      │         │                                            │
│   Success   Failure                                         │
│      │         │                                            │
│      │         ▼                                            │
│      │  ┌────────────────┐                                 │
│      │  │ Log Error      │─────────────────────────┐       │
│      │  │ (truncated)    │                         │       │
│      │  └────────────────┘                         │       │
│      │                                             │       │
│      ▼                                             │       │
│  ┌──────────────┐                                  │       │
│  │ Better than  │──No──→ Discard                   │       │
│  │ current best?│                                  │       │
│  └──────┬───────┘                                  │       │
│         │ Yes                                      │       │
│         ▼                                          │       │
│  ┌──────────────┐                                  │       │
│  │ Save Model   │                                  │       │
│  │ Update Chart │                                  │       │
│  └──────┬───────┘                                  │       │
│         │                                          │       │
│         └──────────────────────────────────────────┘       │
│                    │                                        │
│                    ▼                                        │
│         Store in agent.history                              │
│         (feeds next iteration)                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ ITERATION N+1    │
                    │ (sees this result│
                    │  in context)     │
                    └──────────────────┘
```

**Key Implementation Details:**

- **Learning Context** (`llm_agent.py:_build_learning_context`):
  - Shows last 3 iterations with status and metrics
  - Failed iterations include truncated error messages
  - Successful iterations show all metrics (accuracy, precision, etc.)
  - Instructs agent: "Beat the best metrics seen so far. If errors occurred, fix them."

- **Best-Only Strategy**:
  - Only saves models that beat the previous best score
  - Tracks `best_score_so_far` across all iterations
  - Discards models that don't improve (even if successful)

- **Task-Specific Prompts**:
  - Classification: "If accuracy < 0.85, try different algorithms"
  - Regression: "If R² < 0.8, try different algorithms"
  - Clustering: "Optimize silhouette score by trying different cluster counts"
  - Recommendation: "Evaluate using RMSE on predicted ratings"

This creates a **self-improving system** where each iteration learns from the past, avoiding repeated mistakes and progressively discovering better models.

## Task-Specific Metrics

| Task | Primary Metric | Direction | Other Metrics |
|------|---------------|-----------|---------------|
| Classification | Accuracy | Higher is better | Precision, Recall, F1 |
| Regression | R² Score | Higher is better | RMSE, MAE |
| Clustering | Silhouette Score | Higher is better | Inertia, N Clusters |
| Recommendation | RMSE | Lower is better | MAE, Precision@K |

## Project Structure

```
MiniML_Lab/
├── app.py                 # Main Streamlit application + design system
├── llm_agent.py           # Autonomous ML agent (SumoPod AI / OpenAI-compatible)
├── data_pipeline.py       # Data preprocessing, synthetic & AI generation
├── model_manager.py       # Model artifact management & experiment tracking
├── visualization.py       # Plotly charts & Matplotlib visualizations
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variables template
├── fonts/                 # Custom fonts (Inter, JetBrains Mono)
├── models/                # Saved model artifacts
└── README.md              # This file
```

## Dependencies

| Package | Purpose |
|---------|---------|
| streamlit | Web dashboard |
| scikit-learn | ML models & synthetic data |
| pandas | Data manipulation |
| numpy | Numerical computing |
| openai | SumoPod AI API client |
| plotly | Interactive charts |
| matplotlib | Static visualizations |
| python-dotenv | Environment variables |
| pillow | Image handling |

## Troubleshooting

### "API Key not found"
Enter your SumoPod AI API key in the sidebar.

### "Timeout during code execution"
Generated code has a 120-second timeout. Simplify the model or increase data samples.

### "Script failed" during AI data generation
The AI-generated script may have errors. Check the error message and try rephrasing your data description.

### "Cannot find module 'xxx'"
Run `pip install -r requirements.txt` again.

### Encoding errors on Windows
All file writes use UTF-8 encoding. If you see charmap errors, ensure your terminal supports UTF-8.

## Contributing

Areas for enhancement:
- Deep learning models (PyTorch, TensorFlow)
- Hyperparameter optimization (Optuna)
- Ensemble model generation
- Feature engineering automation
- Distributed execution
- REST API

## License

MIT License
