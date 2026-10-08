"""
MiniML Lab — FastAPI backend.
Run from repo root:  uvicorn backend.app:app --reload --port 8000
"""
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import routes_agent, routes_data, routes_models, routes_progress, routes_providers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="MiniML Lab API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_data.router)
app.include_router(routes_providers.router)
app.include_router(routes_models.router)
app.include_router(routes_progress.router)
app.include_router(routes_agent.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "cwd": os.getcwd()}
