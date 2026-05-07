"""
llm_agent.py - Autonomous ML Experimentation Agent (Optimized for Learning)
"""
import os
import sys
from dotenv import load_dotenv
import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import aiohttp
import asyncio
import subprocess

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentState(Enum):
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class AgentConfig:
    openrouter_api_key: str
    model: str = "meta-llama/llama-3-8b-instruct:free" # Default ke model yang lebih stabil
    max_retries: int = 3
    temperature: float = 0.7
    max_tokens: int = 2500

@dataclass
class ExperimentResult:
    script: str
    output: Optional[str]
    error: Optional[str]
    metrics: Optional[Dict[str, Any]]
    state: AgentState
    iteration: int
    saved_model_path: Optional[str] = None

class MLAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.state = AgentState.PLANNING
        self.iteration = 0
        self.history: List[ExperimentResult] = []
        self.base_url = "https://openrouter.ai/api/v1"
        
    async def generate_experiment_code(
        self,
        dataset_info: Dict[str, Any],
        previous_results: Optional[List[ExperimentResult]] = None,
        task: str = "classification"
    ) -> str:
        self.state = AgentState.PLANNING
        self.iteration += 1
        
        # Build Context untuk Auto-Improvement
        context = self._build_learning_context(previous_results)
        
        prompt = f"""You are an Elite AutoML Engineer. Your goal is to MAXIMIZE accuracy through iterative improvement.

Task: {task}
Dataset Info:
- Shape: {dataset_info.get('shape')}
- Features: {dataset_info.get('features')}
- Target: {dataset_info.get('target')}

{context}

CRITICAL INSTRUCTIONS FOR IMPROVEMENT:
1. If previous iterations failed, FIX the errors first.
2. If previous iterations succeeded but accuracy is low (<0.85), TRY DIFFERENT algorithms (e.g., switch from RandomForest to GradientBoosting, SVM, or XGBoost if available).
3. Improve preprocessing: Try StandardScaler, handle outliers, or feature engineering.
4. Tune hyperparameters: Don't just use defaults. Use GridSearchCV or manual tuning if possible.

OUTPUT REQUIREMENTS:
1. Generate ONLY executable Python code.
2. Load data from `os.environ.get('DATA_PATH')`.
3. Save best model as 'trained_model.pkl'.
4. AT THE END, print exactly:
   METRICS_JSON: {{"accuracy": val, "precision": val}}
   MODEL_PATH: trained_model.pkl
"""
        raw_code = await self._call_openrouter(prompt)
        if not raw_code: raise Exception("LLM Empty Response")
        
        # Cleanup
        code = raw_code.strip()
        if "```python" in code: code = code.split("```python")[1].split("```")[0]
        elif "```" in code: code = code.split("```")[1].split("```")[0]
        return code

    def _build_learning_context(self, previous_results: Optional[List[ExperimentResult]]) -> str:
        if not previous_results:
            return "This is the FIRST iteration. Start with a robust baseline model (e.g., RandomForest)."
        
        context = "HISTORY OF PREVIOUS ATTEMPTS (Learn from this):\n"
        for i, res in enumerate(previous_results[-3:], 1): # Ambil 3 terakhir
            if res.state == AgentState.FAILED:
                context += f"- Iteration {res.iteration}: FAILED. Error: {res.error[:150]}\n"
            else:
                acc = res.metrics.get('accuracy', 0) if res.metrics else 0
                context += f"- Iteration {res.iteration}: SUCCESS. Accuracy: {acc:.4f}. Metrics: {res.metrics}\n"
        
        context += "\nSTRATEGY: Beat the highest accuracy seen so far. If errors occurred, fix them."
        return context

    async def _call_openrouter(self, prompt: str) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {self.config.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "MiniML Lab"
        }
        payload = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        
        for attempt in range(self.config.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=90)) as response:
                        if response.status == 429:
                            await asyncio.sleep((attempt + 1) * 5)
                            continue
                        if response.status != 200:
                            if attempt == self.config.max_retries - 1: raise Exception(f"API Error {response.status}")
                            continue
                        data = await response.json()
                        return data["choices"][0]["message"]["content"]
            except Exception as e:
                if attempt == self.config.max_retries - 1: raise e
                await asyncio.sleep(2)
        return None

    async def execute_code(self, code: str, data_path: str) -> ExperimentResult:
        self.state = AgentState.EXECUTING
        import tempfile
        temp_dir = tempfile.mkdtemp()
        script_path = os.path.join(temp_dir, "exp.py")
        with open(script_path, 'w') as f: f.write(code)
        
        try:
            process = subprocess.run([sys.executable, script_path], capture_output=True, text=True, timeout=120, env={**os.environ, "DATA_PATH": data_path}, cwd=temp_dir)
            output = process.stdout
            error = process.stderr if process.returncode != 0 else None
            metrics = self._parse_metrics(output)
            model_path = self._extract_model_path(output, temp_dir)
            
            state = AgentState.COMPLETED if process.returncode == 0 else AgentState.FAILED
            
            return ExperimentResult(script=code, output=output, error=error, metrics=metrics, state=state, iteration=self.iteration, saved_model_path=model_path)
        except Exception as e:
            return ExperimentResult(script=code, output=None, error=str(e), metrics=None, state=AgentState.FAILED, iteration=self.iteration)
        finally:
            pass # Biarkan temp dir untuk debug jika perlu, atau hapus manual

    def _extract_model_path(self, output: str, base_dir: str) -> Optional[str]:
        for line in output.splitlines():
            if line.startswith("MODEL_PATH:"):
                return os.path.join(base_dir, line.replace("MODEL_PATH:", "").strip())
        return None

    def _parse_metrics(self, output: str) -> Optional[Dict[str, Any]]:
        if not output: return None
        import re
        try:
            matches = re.findall(r'\{[^{}]*(?:"accuracy")[^{}]*\}', output)
            if matches: return json.loads(matches[-1])
        except: pass
        return None

def create_agent(api_key: str, model: str = "meta-llama/llama-3-8b-instruct:free") -> MLAgent:
    return MLAgent(AgentConfig(openrouter_api_key=api_key, model=model))