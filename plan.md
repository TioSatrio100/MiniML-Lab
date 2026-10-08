# MiniML Lab — Remaining Work Plan

> Status snapshot: Phases 1–6 shipped (uncommitted, 32 pending changes).
> Backend FastAPI + React frontend + sandbox all functional; build/lint green.
> This plan = everything left to close the project. Newest last.

---

## Done (reference)

| Phase | Scope | State |
|-------|-------|-------|
| 1 | FastAPI REST: session/config/data/providers/models/progress | ✅ tested via curl |
| 2 | Core modules moved → `backend/core/`, LangChain agent | ✅ |
| 3 | Sandbox: Dockerfile, docker/subprocess modes, env allowlist | ✅ test_sandbox.py |
| 4 | Vite + React + Tailwind v4 + shadcn, Sidebar/Hero/Tabs shell | ✅ headless render |
| 5 | Benchmark chart (SVG) + iteration cards + summary, Models compare/download, ProviderDialog | ✅ build+lint |
| 6 | Dockerfiles (backend/frontend), docker-compose, README/SETUP rewrite, bugfixes (cancel→server, models refresh) | ✅ compose NOT E2E-tested |

---

## Phase 7 — Feature Parity Gaps (medium)

Old Streamlit features lost in migration. Do in this order:

### 7a. AI-Generated Data
Route existed in Streamlit, dropped in rewrite. `ai_description` config field still exists but is dead.

- [ ] `backend/api/routes_data.py` — `POST /api/session/{id}/data/ai`
      body `{description}` → LLM writes gen script → sandbox executes → preview
- [ ] Agent tool `generate_data(description)` in `backend/core/llm_agent.py`
      (task types clustering/recommendation depend on this — synthetic only covers cls/regr)
- [ ] `frontend`: Sandbox tab gets "AI data" card (description textarea + button)
- [ ] Provider restriction table: clustering/recommendation → disable synthetic button when task = cluster/reco
- [ ] Test: generate iris-like clustering set end-to-end

**Accept:** clustering task runnable from zero with AI data.

### 7b. Rename Model
- [ ] `PATCH /api/models/{name}/rename` body `{new_name}` — update `models.json` + registry, keep files
- [ ] Frontend `ModelsPanel`: rename input on card
- [ ] Test: rename persists after restart (registry.json)

### 7c. Data-source restriction enforcement
- [ ] Backend `PUT config` rejects `task=clustering/recommendation` + `data_source=synthetic` (400)
- [ ] Mirror in `DataPanel` UI

**Estimate:** 7a ≈ half-day, 7b ≈ 1 h, 7c ≈ 1 h.

---

## Phase 8 — Test Suite (medium)

Only `backend/tests/test_sandbox.py` exists. Plan called for unit tests.

### 8a. Backend (pytest)
- [ ] `tests/test_session.py` — create/config/save-load roundtrip
- [ ] `tests/test_providers.py` — registry CRUD, key never in GET response, builtin protection
- [ ] `tests/test_data.py` — synthetic cls/regr, CSV upload + target detect, preview
- [ ] `tests/test_progress.py` — stats math incl. lower-is-better (recommendation/RMSE)
- [ ] `tests/test_agent_mock.py` — fake LLM (deterministic tool sequence) → SSE events order:
      `trace* → iteration* → done`, budget stop, cancel path
- [ ] `requirements-dev.txt` — pytest, httpx (TestClient)
- [ ] CI-ready command: `python -m pytest backend/tests -q`

### 8b. Frontend
- [ ] Vitest + @testing-library: `MetricChart` (points/best), `store` reducers, `runAgent` event handling (mock fetch)
- [ ] `npm run test` script

**Accept:** `pytest` green + `npm run test` green + existing build/lint.

---

## Phase 9 — E2E Hardening (medium)

### 9a. Compose real run
```bash
docker compose up --build          # :8080
docker compose --profile tools build
```
- [ ] full loop on Linux/WSL: generate data → run agent → model saved → download .pkl via nginx proxy
- [ ] SSE through nginx verified (buffering off — config exists, untested)
- [ ] `.env` handling: compose passes API key? add `SUMOPOD_API_KEY` env passthrough or sidebar-entry only

### 9b. Failure paths
- [ ] LLM 401 → `error` SSE event → red banner + button re-enabled (banner exists, path untested)
- [ ] cancel mid-run → backend `agent_running=False`, second run works
- [ ] refresh page mid-run → store re-hydrates from `/status` (route exists, `applyStatus` in store currently unused → wire on init)
- [ ] no dataset + Run → 400 surfaced, not silent

### 9c. Multi-session isolation
- [ ] two sessions, separate datasets/sessions dir, no tracker bleed (session.tracker — verify)

**Accept:** scripted happy path + 4 failure cases pass on compose build.

---

## Phase 10 — Polish (low, do last)

- [ ] Store dead code: `applyStatus`, `TabId`, `DataPreview` import cleanup (oxlint silent on unused state fields — manual pass)
- [ ] oxlint warnings: `Sidebar.tsx:32` set-state-in-effect → derive `keySaved` during render
- [ ] `.gitignore`: add `vite.log`, `frontend/dist` (dist present), `.dockerignore` review
- [ ] Remove legacy tracked deletions: `git rm` old `models/*` artifacts, `__pycache__`, `requirements.txt`, `app.py` (staged already — verify)
- [ ] `storage/` first-run: directory auto-created? (check `os.makedirs` in storage.py/session.py — if missing, add)
- [ ] README: add "Quick verify" snippet (`/api/health`, headless test command)
- [ ] favicon/og: replace Vite default svg with real mark (optional)
- [ ] Hero: show `improvement` from progress endpoint instead of recompute from live iterations (minor drift when page reloaded mid-history)

---

## Phase 11 — Release (small)

- [ ] Full manual pass (checklist below)
- [ ] `git add -A && git commit` — split into logical commits:
      1. `refactor: migrate Streamlit app to FastAPI backend`
      2. `feat(sandbox): docker/subprocess isolation modes`
      3. `feat(frontend): Vite+React rewrite with shadcn`
      4. `chore: docker-compose + docs`
- [ ] Tag `v1.0.0`
- [ ] Optional: push to remote

**Manual pass checklist:**
- [ ] fresh clone → SETUP.md steps → running in <10 min
- [ ] all 4 task types complete one run (cls via synthetic; reg via synthetic; cluster/reco via AI data)
- [ ] provider add/discover/delete roundtrip
- [ ] model download opens (pkl loads with `joblib`)
- [ ] cancel + rerun
- [ ] compose path on port 8080

---

## Priority Order

```
7b rename ─┐
7c restrict ┴→ 8a pytest → 9b failure paths → 10 polish → 11 commit/tag
7a AI data ──────────────┘ ↑
9a compose E2E ────────────┘ (needs Docker run; schedule after 7a)
```

**Critical path to "done": 7a → 8a → 9b → 10 → 11.**
7b/7c/8b/9a/9c nice-to-have; can ship without 8b (frontend tests) if time-boxed.

## Out of Scope (parked)

- Dark mode (CSS has `.dark` block; no toggle — skip unless asked)
- Deep learning / Optuna / ensembles (old README wishlist)
- Auth / multi-user (in-memory sessions are dev-only by design)
- Plotly in frontend (custom SVG ships; backend still returns Plotly JSON for API consumers)
