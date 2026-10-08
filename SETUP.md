# Setup Guide — MiniML Lab

Step-by-step installation and first run.

## System Requirements

- **Python** 3.10+
- **Node.js** 18+ (tested with 22)
- **Docker** (optional — sandbox falls back to subprocess mode)
- **RAM**: 4 GB minimum (8 GB recommended)
- **OS**: Windows, macOS, or Linux

## Step 1: Get an LLM API Key

1. Visit a provider — e.g. https://ai.sumopod.com (or OpenRouter / OpenAI / any OpenAI-compatible endpoint)
2. Create an API key
3. Copy it — you'll paste it into the app sidebar later (stored server-side only)

## Step 2: Clone & Enter Project

```bash
git clone https://github.com/username/MiniML-Lab.git
cd MiniML-Lab
```

## Step 3: Backend Setup

```bash
python -m venv venv

# activate
venv\Scripts\activate           # Windows
source venv/bin/activate        # macOS/Linux

pip install -r backend/requirements.txt
```

Start the API:

```bash
uvicorn backend.app:app --reload --port 8000
```

> Always run from the project root so `backend.*` imports and `storage/` paths resolve.

## Step 4: Frontend Setup

New terminal:

```bash
cd frontend
npm install
npm run dev
```

## Step 5: Open the App

- Frontend: **http://localhost:5173**
- Backend API docs: **http://localhost:8000/docs**
- Health check: `curl http://localhost:8000/api/health`

The Vite dev server proxies `/api/*` to `localhost:8000` — no CORS config needed in dev.

## Verification Checklist

- [ ] `python --version` ≥ 3.10
- [ ] `pip show fastapi` resolves
- [ ] `curl http://localhost:8000/api/health` → `{"status":"ok", ...}`
- [ ] `node --version` ≥ 18
- [ ] http://localhost:5173 renders "MiniML Lab" with sidebar
- [ ] Sidebar provider list loads (SumoPod, OpenRouter, OpenAI, Ollama)
- [ ] (Optional) `docker info` succeeds — else set `SANDBOX=subprocess`

## First-Time Usage

1. **Sidebar → API key**: select provider, paste key, click **Save** (`✓ saved` appears)
2. **Sandbox tab → Synthetic data**: pick task, click **Generate** — preview table appears
3. **Sidebar**: set task type + max iterations
4. Click **Run Auto-ML Loop** — trace streams in the Benchmark tab
5. When done: best score/model in the Hero card; model code in My Models tab

## Sandbox Modes

| Mode | How | Isolation |
|------|-----|-----------|
| `docker` (default) | runs `miniml-sandbox` image | no network, 512 MB, 1 CPU, temp mount |
| `subprocess` | host Python | env allowlist only |

```bash
# force subprocess (no Docker needed)
set SANDBOX=subprocess       # Windows
export SANDBOX=subprocess    # macOS/Linux

# pre-build the sandbox image (otherwise built on first run)
docker build -t miniml-sandbox:latest backend/sandbox
```

## Ports

| Service | Port | Override |
|---------|------|----------|
| FastAPI | 8000 | `uvicorn --port 8001` (+ update proxy in `frontend/vite.config.ts`) |
| Vite dev | 5173 | `npm run dev -- --port 5174` |

```bash
# Windows: find/kill port
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8000
kill -9 <PID>
```

## Docker Compose (production-style run)

```bash
# backend :8000 + frontend :8080 (nginx, SSE-safe proxy)
docker compose up --build

# also build the sandbox image
docker compose --profile tools build

# open http://localhost:8080
```

Notes:
- Backend defaults to `SANDBOX=subprocess` in the container (ML deps are baked into the image) — works everywhere.
- Docker-mode sandbox inside a container needs docker CLI + socket mount + identical host/container tmp paths — **Linux host only**. Add to `backend` service:
  ```yaml
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
  environment:
    SANDBOX: docker
  ```
  (and install the docker CLI in `backend/Dockerfile` — comment in the file shows the one-liner)
- Data persists in `./storage` (bind-mounted).

## Runtime Files

```
storage/
├── sessions/{id}.csv     # uploaded/generated datasets
├── sessions/{id}.json    # session config
├── providers.json        # custom providers + API keys (SECRET — gitignored)
├── models.json           # saved model registry
└── experiments.json      # experiment tracker
```

Never commit `storage/providers.json` or `.env`.

## Troubleshooting Installation

### `ModuleNotFoundError: No module named 'backend'`
Run uvicorn from project root: `uvicorn backend.app:app --port 8000`

### `ModuleNotFoundError: No module named 'fastapi'`
```bash
pip install -r backend/requirements.txt
```

### Docker: "failed to connect to the docker API"
Start Docker Desktop, or run with `SANDBOX=subprocess`.

### `npm` errors / weird UI state
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Port already in use
See Ports table above.

### Python on PATH issues (Windows)
```bash
py --version
py -m venv venv
```
Reinstall from python.org with "Add to PATH" checked if needed.

## Development

```bash
# backend: auto-reload
uvicorn backend.app:app --reload --port 8000

# frontend: dev server with HMR
cd frontend && npm run dev

# frontend: lint + typecheck + build
cd frontend
npm run lint
npm run build          # tsc -b && vite build

# sandbox test script (docker or subprocess)
python backend/tests/test_sandbox.py
```

## Uninstallation

```bash
# backend
deactivate
# Windows: rmdir /s /q venv    |    macOS/Linux: rm -rf venv

# frontend
rm -rf frontend/node_modules frontend/dist

# runtime data
rm -rf storage
```

---

Questions? See README.md for architecture and API overview.
