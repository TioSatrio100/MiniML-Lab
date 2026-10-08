"""
providers.py - LLM Provider Registry
Built-in templates + user-defined providers persisted to storage/providers.json.
User supplies platform name, base_url, api_key, model names — any OpenAI-compatible endpoint.
"""
import json
import logging
import os
import threading
from typing import Optional, Dict, List, Any

import httpx
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

STORAGE_DIR = os.path.join(os.getcwd(), "storage")
PROVIDERS_FILE = os.path.join(STORAGE_DIR, "providers.json")

BUILTIN_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "SumoPod": {
        "base_url": "https://ai.sumopod.com/v1",
        "models": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
    },
    "OpenRouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "models": ["openai/gpt-4o-mini", "anthropic/claude-3-haiku", "google/gemini-pro"],
    },
    "OpenAI": {
        "base_url": None,
        "models": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
    },
    "Ollama": {
        "base_url": "http://localhost:11434/v1",
        "models": ["llama3", "mistral", "qwen2.5"],
    },
}

_lock = threading.Lock()


def _load_file() -> Dict[str, Dict]:
    if not os.path.exists(PROVIDERS_FILE):
        return {}
    try:
        with open(PROVIDERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read {PROVIDERS_FILE}: {e}")
        return {}


def _save_file(data: Dict[str, Dict]) -> None:
    os.makedirs(STORAGE_DIR, exist_ok=True)
    tmp = PROVIDERS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PROVIDERS_FILE)


class ProviderRegistry:
    """Global registry of user-defined providers, persisted as JSON.
    Built-in presets act as templates — listable without persisting."""

    def list(self) -> List[Dict]:
        custom = _load_file()
        providers = []
        for name, tpl in BUILTIN_TEMPLATES.items():
            entry = custom.get(name, {})
            providers.append({
                "name": name,
                "base_url": tpl["base_url"],
                "models": entry.get("models", tpl["models"]),
                "has_key": bool(entry.get("api_key")),
                "builtin": True,
            })
        for name, entry in custom.items():
            if name in BUILTIN_TEMPLATES:
                continue
            providers.append({
                "name": name,
                "base_url": entry.get("base_url", ""),
                "models": entry.get("models", []),
                "has_key": bool(entry.get("api_key")),
                "builtin": False,
            })
        return providers

    def add(
        self,
        name: str,
        base_url: str,
        api_key: str,
        models: Optional[List[str]] = None,
    ) -> Dict:
        if not name.strip():
            raise ValueError("Provider name required")
        with _lock:
            data = _load_file()
            tpl = BUILTIN_TEMPLATES.get(name, {})
            entry = data.get(name) or {"base_url": tpl.get("base_url") or "", "models": list(tpl.get("models", []))}
            entry["base_url"] = base_url.strip()
            if api_key:
                entry["api_key"] = api_key
            existing = entry.get("models", [])
            for m in models or []:
                if m and m not in existing:
                    existing.append(m)
            entry["models"] = existing
            data[name] = entry
            _save_file(data)
        logger.info(f"Provider saved: {name}")
        return {"name": name, "base_url": base_url, "models": entry["models"], "has_key": bool(entry.get("api_key"))}

    def update(self, name: str, base_url: Optional[str] = None, api_key: Optional[str] = None) -> Dict:
        with _lock:
            data = _load_file()
            entry = data.get(name, {"base_url": _builtin_base(name) or "", "models": list(BUILTIN_TEMPLATES.get(name, {}).get("models", []))})
            if base_url is not None:
                entry["base_url"] = base_url.strip()
            if api_key:
                entry["api_key"] = api_key
            data[name] = entry
            _save_file(data)
        return {"name": name, "base_url": entry.get("base_url", ""), "has_key": bool(entry.get("api_key"))}

    def add_model(self, name: str, model: str) -> List[str]:
        if not model.strip():
            raise ValueError("Model name required")
        with _lock:
            data = _load_file()
            if name in data:
                entry = data[name]
            else:
                tpl = BUILTIN_TEMPLATES.get(name, {})
                entry = {"base_url": tpl.get("base_url") or "", "models": list(tpl.get("models", []))}
            if model not in entry["models"]:
                entry["models"].append(model)
            data[name] = entry
            _save_file(data)
        return data[name]["models"]

    def remove(self, name: str) -> None:
        with _lock:
            data = _load_file()
            if name in data:
                del data[name]
                _save_file(data)

    def remove_model(self, name: str, model: str) -> List[str]:
        with _lock:
            data = _load_file()
            if name in data:
                entry = data[name]
            else:
                tpl = BUILTIN_TEMPLATES.get(name, {})
                if not tpl:
                    raise KeyError(f"Unknown provider: {name}")
                entry = {"base_url": tpl.get("base_url") or "", "models": list(tpl.get("models", []))}
            entry["models"] = [m for m in entry.get("models", []) if m != model]
            data[name] = entry
            _save_file(data)
        return data[name]["models"]

    def resolve(self, name: str) -> Dict[str, Optional[str]]:
        """Server-side only: return base_url + api_key. Never send api_key to client."""
        entry = _load_file().get(name, {})
        base_url = entry.get("base_url") or _builtin_base(name)
        api_key = entry.get("api_key", "")
        return {"base_url": base_url, "api_key": api_key}

    async def fetch_models(self, name: str) -> List[str]:
        """GET {base_url}/models — OpenAI-compatible discovery."""
        resolved = self.resolve(name)
        base_url = resolved["base_url"]
        if not base_url:
            raise ValueError(f"No base_url for provider: {name}")
        url = base_url.rstrip("/") + "/models"
        headers = {}
        if resolved["api_key"]:
            headers["Authorization"] = f"Bearer {resolved['api_key']}"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            payload = resp.json()
        items = payload.get("data", payload if isinstance(payload, list) else [])
        return [m.get("id") for m in items if isinstance(m, dict) and m.get("id")]


def _builtin_base(name: str) -> Optional[str]:
    tpl = BUILTIN_TEMPLATES.get(name)
    return tpl["base_url"] if tpl else None


def get_model(
    provider: str,
    model_name: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2500,
) -> ChatOpenAI:
    """Build ChatOpenAI. api_key/base_url omitted → resolved from ProviderRegistry."""
    if api_key is None or base_url is None:
        resolved = ProviderRegistry().resolve(provider)
        api_key = api_key if api_key is not None else resolved["api_key"]
        base_url = base_url if base_url is not None else resolved["base_url"]

    if not api_key:
        raise ValueError(f"No API key for provider '{provider}'. Add it in the sidebar.")

    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url or None,
        temperature=temperature,
        max_tokens=max_tokens,
        streaming=True,
    )
