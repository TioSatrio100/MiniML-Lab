# MiniML Lab — Autonomous ML Experimentation Platform

LLM agent that generates, executes, and improves ML experiments on its own. Full-stack: FastAPI backend + React frontend + sandboxed code execution.

## Features

### 4 Task Types
- **Classification** — Accuracy, Precision, Recall, F1
- **Regression** — R², RMSE, MAE
- **Clustering** — Silhouette Score, Inertia (unsupervised)
- **Recommendation** — Content-based, RMSE, Precision@K

### AI-Powered Agent
- **LangChain Tool-Calling Agent** — decides its own workflow via tools (`analyze_dataset`, `run_experiment`, `get_history`, `save_model`, `finish`)
- **Multi-Provider Support** — SumoPod, OpenRouter, OpenAI, Ollama, or any OpenAI-compatible endpoint (custom base_url + API key + model list)
- **Self-Correcting Loops** — tool errors feed back to the agent; budget-gated iterations
- **Real-Time Streaming** — agent trace, iterations, and results stream live over SSE

### Data Pipeline
- **Synthetic Data** — generate classification/regression datasets on demand (sklearn)
- **CSV Upload** — load your own dataset, target auto-detected
- **Automated Preprocessing** — missing values, categorical encoding, feature scaling

### Sandboxed Execution
- LLM-generated code runs isolated from the host:
  - **Docker mode** (default): `--network none`, 512 MB RAM, 1 CPU, temp-dir mount only
  - **Subprocess mode**: host Python with strict env allowlist (no secret leakage)
- `SANDBOX=docker|subprocess`, auto-fallback when Docker daemon is unreachable

### Design System
- Off-white/cream background with dot-matrix pattern
- Inter for UI, JetBrains Mono for code/technical elements
- Terracotta/coral (`#e06c53`) accent, hairline borders, card layout

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker (optional — subprocess fallback works without it)
- An LLM API key (e.g. SumoPod: https://ai.sumopod.com)

### 1. Backend

```bash
cd MiniML_Lab
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r backend/requirements.txt
uvicorn backend.app:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 2. Frontend

```bash
cd MiniML_Lab/frontend
npm install
npm run dev
```

Open http://localhost:5173 — `/api` is proxied to the backend automatically.

## Quick verify

```bash
# API up?
curl http://localhost:8000/api/health          # {"status":"ok",...}

# backend test suite
pip install -r backend/requirements-dev.txt
python -m pytest backend/tests -q              # 36 passed

# frontend typecheck + build
cd frontend && npm run build
```

## Usage

1. **Configure** (sidebar): pick provider + model, paste API key (stored server-side in `storage/providers.json`, never sent back to the browser), choose task type and max iterations.
2. **Prepare data** (Sandbox tab): generate synthetic data or upload CSV; preview shows shape, dtypes, target.
3. **Run** — "Run Auto-ML Loop": the agent analyzes the dataset, writes training code, executes it in the sandbox, evaluates metrics, and iterates until the budget is exhausted or it calls `finish`.
4. **Monitor** (Benchmark tab): live trace, experiment stats (successful/total, best metric, improvement).
5. **Save & inspect** (My Models tab): agent registers the best model via `save_model`; view metrics and the exact training code.

### Configuration

| Setting | Where | Notes |
|---------|-------|-------|
| Provider / Base URL | sidebar or `POST /api/providers` | any OpenAI-compatible endpoint |
| API key | sidebar (Save) | server-side only, `has_key` flag returned to UI |
| Model | sidebar | editable model list per provider |
| Task type | sidebar / Sandbox tab | drives prompts + primary metric |
| Max iterations | sidebar (1–10) | agent budget |

## Architecture

```
Browser (React + zustand)
   │  fetch + SSE
   ▼
FastAPI (backend/app.py)
   ├── api/routes_*        REST: session, data, providers, models, progress, agent
   ├── core/session.py     in-memory session state (replaces st.session_state)
   ├── core/llm_agent.py   LangChain agent + tools
   ├── core/model_manager  artifacts + experiment tracker (JSON-persisted)
   ├── core/providers.py   provider registry → storage/providers.json
   └── sandbox/            run_script(): docker | subprocess execution
```

**Agent loop:**

```
analyze_dataset → generate code → run_experiment (sandbox)
      ↑                                    │
      │         metrics / error ───────────┘
      ├─ is_better → save_model
      └─ budget exhausted → finish(summary)
```

**Streaming:** `POST /api/session/{id}/agent/run` → job id; `GET /api/session/{id}/agent/stream/{job}` emits SSE events: `trace`, `iteration`, `error`, `done`.

### Task Metrics

| Task | Primary Metric | Direction | Other |
|------|---------------|-----------|-------|
| Classification | Accuracy | ↑ better | Precision, Recall, F1 |
| Regression | R² Score | ↑ better | RMSE, MAE |
| Clustering | Silhouette | ↑ better | Inertia, N Clusters |
| Recommendation | RMSE | ↓ better | MAE, Precision@K |

## Project Structure

```
MiniML_Lab/
├── backend/
│   ├── app.py                 # FastAPI entrypoint
│   ├── requirements.txt
│   ├── api/
│   │   ├── routes_data.py     # session, config, synthetic, CSV, preview
│   │   ├── routes_providers.py# provider CRUD + model discovery
│   │   ├── routes_models.py   # list / best / code / download
│   │   ├── routes_progress.py # history, stats, Plotly chart JSON
│   │   └── routes_agent.py    # init / run / SSE stream / cancel
│   ├── core/
│   │   ├── llm_agent.py       # LangChain tools + prompts
│   │   ├── session.py         # session state
│   │   ├── providers.py       # ProviderRegistry
│   │   ├── storage.py         # JSON persistence
│   │   ├── model_manager.py   # artifacts + tracker
│   │   ├── data_pipeline.py   # preprocessing + synthetic data
│   │   └── visualization.py   # metric helpers + Plotly charts
│   ├── sandbox/
│   │   ├── Dockerfile         # python:3.12-slim + ML deps
│   │   └── __init__.py        # docker | subprocess runner
│   └── tests/
│       └── test_sandbox.py
├── frontend/
│   └── src/
│       ├── App.tsx            # Sidebar + Hero + TabShell
│       ├── components/        # Sidebar, Hero, TabShell, panels/
│       └── lib/               # api.ts (REST+SSE), store.ts, runAgent.ts
├── storage/                   # runtime: sessions/, providers.json, models.json
├── README.md
└── SETUP.md
```

## API Overview

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/session` | create session |
| PUT | `/api/session/{id}/config` | update config |
| POST | `/api/session/{id}/data/synthetic` | generate data |
| POST | `/api/session/{id}/data/csv` | upload CSV |
| GET | `/api/providers` | list providers (keys hidden) |
| POST | `/api/providers` | add custom provider |
| POST | `/api/providers/{name}/discovery` | fetch model list from endpoint |
| GET | `/api/models` | saved artifacts |
| GET | `/api/session/{id}/progress` | stats + Plotly chart |
| POST | `/api/session/{id}/agent/run` | start agent job |
| GET | `/api/session/{id}/agent/stream/{job}` | SSE event stream |

## Troubleshooting

- **"No API key for provider"** — paste key in sidebar, click Save (stored in `storage/providers.json`).
- **"Connection error" on run** — LLM endpoint unreachable; check base_url / key.
- **Docker sandbox warnings** — start Docker Desktop or set `SANDBOX=subprocess`.
- **Experiment timeout** — 120 s cap; reduce samples or pick a smaller model class.
- **Port in use** — `uvicorn --port 8001` and update the Vite proxy in `frontend/vite.config.ts`.

## License

MIT License
