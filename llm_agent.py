"""
llm_agent.py - Autonomous ML Experimentation Agent (SumoPod AI)
"""
import os
import sys
from dotenv import load_dotenv
import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from openai import AsyncOpenAI
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
    api_key: str
    model: str = "gpt-4o-mini"
    base_url: str = "https://ai.sumopod.com/v1"
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
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )
        
    async def generate_experiment_code(
        self,
        dataset_info: Dict[str, Any],
        previous_results: Optional[List[ExperimentResult]] = None,
        task: str = "classification"
    ) -> str:
        self.state = AgentState.PLANNING
        self.iteration += 1
        
        context = self._build_learning_context(previous_results)
        
        prompt = self._build_prompt(task, dataset_info, context)
        
        raw_code = await self._call_ai(prompt)
        if not raw_code: raise Exception("AI Empty Response")
        
        code = raw_code.strip()
        if "```python" in code: code = code.split("```python")[1].split("```")[0]
        elif "```" in code: code = code.split("```")[1].split("```")[0]
        return code

    def _build_prompt(self, task: str, dataset_info: Dict[str, Any], context: str) -> str:
        """Build task-specific prompt"""
        
        base_info = f"""Task: {task}
Dataset Info:
- Shape: {dataset_info.get('shape')}
- Features: {dataset_info.get('features')}
- Target: {dataset_info.get('target')}

{context}
"""
        
        if task == "classification":
            return base_info + """
CRITICAL INSTRUCTIONS FOR CLASSIFICATION:
1. If previous iterations failed, FIX the errors first.
2. If accuracy is low (<0.85), TRY DIFFERENT algorithms (RandomForest, GradientBoosting, SVM, XGBoost).
3. Improve preprocessing: StandardScaler, handle outliers, feature engineering.
4. Tune hyperparameters for better accuracy.

OUTPUT REQUIREMENTS:
1. Generate ONLY executable Python code.
2. Load data from `os.environ.get('DATA_PATH')`.
3. Save best model as 'trained_model.pkl'.
4. AT THE END, print exactly:
   METRICS_JSON: {"accuracy": val, "precision": val, "recall": val, "f1": val}
   MODEL_PATH: trained_model.pkl
"""

        elif task == "regression":
            return base_info + """
CRITICAL INSTRUCTIONS FOR REGRESSION:
1. If previous iterations failed, FIX the errors first.
2. If R² is low (<0.8), TRY DIFFERENT algorithms (LinearRegression, Ridge, RandomForestRegressor, GradientBoostingRegressor).
3. Improve preprocessing: StandardScaler, polynomial features, handle outliers.
4. Tune hyperparameters for better R² and lower RMSE.

OUTPUT REQUIREMENTS:
1. Generate ONLY executable Python code.
2. Load data from `os.environ.get('DATA_PATH')`.
3. Save best model as 'trained_model.pkl'.
4. AT THE END, print exactly:
   METRICS_JSON: {"r2": val, "rmse": val, "mae": val}
   MODEL_PATH: trained_model.pkl
"""

        elif task == "clustering":
            return base_info + """
CRITICAL INSTRUCTIONS FOR CLUSTERING:
1. If previous iterations failed, FIX the errors first.
2. This is UNSUPERVISED - there is NO target column.
3. Try different algorithms: KMeans, DBSCAN, AgglomerativeClustering.
4. Optimize silhouette score by trying different numbers of clusters.
5. Use StandardScaler for feature normalization.

OUTPUT REQUIREMENTS:
1. Generate ONLY executable Python code.
2. Load data from `os.environ.get('DATA_PATH')`.
3. Save best model as 'trained_model.pkl'.
4. AT THE END, print exactly:
   METRICS_JSON: {"silhouette_score": val, "inertia": val, "n_clusters": val}
   MODEL_PATH: trained_model.pkl
"""

        elif task == "recommendation":
            return base_info + """
CRITICAL INSTRUCTIONS FOR CONTENT-BASED RECOMMENDATION:
1. If previous iterations failed, FIX the errors first.
2. Build a content-based recommendation system using item features.
3. Use cosine similarity or other similarity metrics.
4. Evaluate using RMSE on predicted ratings.

OUTPUT REQUIREMENTS:
1. Generate ONLY executable Python code.
2. Load data from `os.environ.get('DATA_PATH')`.
3. Save best model as 'trained_model.pkl'.
4. AT THE END, print exactly:
   METRICS_JSON: {"rmse": val, "mae": val, "precision_at_k": val}
   MODEL_PATH: trained_model.pkl
"""

        else:
            raise ValueError(f"Unknown task type: {task}")

    def _build_learning_context(self, previous_results: Optional[List[ExperimentResult]]) -> str:
        if not previous_results:
            return "This is the FIRST iteration. Start with a robust baseline model."
        
        context = "HISTORY OF PREVIOUS ATTEMPTS (Learn from this):\n"
        for i, res in enumerate(previous_results[-3:], 1):
            if res.state == AgentState.FAILED:
                context += f"- Iteration {res.iteration}: FAILED. Error: {res.error[:150]}\n"
            else:
                metrics_str = ", ".join([f"{k}={v:.4f}" for k, v in res.metrics.items()]) if res.metrics else "N/A"
                context += f"- Iteration {res.iteration}: SUCCESS. Metrics: {metrics_str}\n"
        
        context += "\nSTRATEGY: Beat the best metrics seen so far. If errors occurred, fix them."
        return context

    async def _call_ai(self, prompt: str) -> Optional[str]:
        for attempt in range(self.config.max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.config.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"AI API error (attempt {attempt+1}): {e}")
                if attempt == self.config.max_retries - 1: raise e
                await asyncio.sleep(2)
        return None

    async def execute_code(self, code: str, data_path: str) -> ExperimentResult:
        self.state = AgentState.EXECUTING
        import tempfile
        temp_dir = tempfile.mkdtemp()
        script_path = os.path.join(temp_dir, "exp.py")
        with open(script_path, 'w', encoding='utf-8') as f: f.write(code)
        
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
            pass

    def _extract_model_path(self, output: str, base_dir: str) -> Optional[str]:
        for line in output.splitlines():
            if line.startswith("MODEL_PATH:"):
                return os.path.join(base_dir, line.replace("MODEL_PATH:", "").strip())
        return None

    def _parse_metrics(self, output: str) -> Optional[Dict[str, Any]]:
        if not output: return None
        import re
        try:
            matches = re.findall(r'\{[^{}]*(?:"accuracy"|"r2"|"rmse"|"silhouette_score")[^{}]*\}', output)
            if matches: return json.loads(matches[-1])
        except: pass
        return None

def create_agent(api_key: str, model: str = "gpt-4o-mini", base_url: str = "https://ai.sumopod.com/v1") -> MLAgent:
    return MLAgent(AgentConfig(api_key=api_key, model=model, base_url=base_url))
