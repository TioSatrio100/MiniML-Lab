"""
data_gen.py - AI-generated datasets for clustering/recommendation tasks.

LLM writes a pandas snippet that builds a DataFrame and saves it to OUTPUT_PATH.
Snippet runs in the sandbox (no network); result is loaded back and set as the
session dataset. Synthetic generator covers cls/regr only — this closes the gap.
"""
import logging
import os
import re
import tempfile
from typing import Any, Dict, Optional

import pandas as pd

from backend.core.providers import get_model
from backend.sandbox import run_script

logger = logging.getLogger(__name__)

TASK_HINTS = {
    "clustering": (
        "Create an unlabeled dataset suitable for CLUSTERING: 4-6 natural groups with distinct "
        "cluster centers, some noise. NO target/label column — feature columns only. "
    ),
    "recommendation": (
        "Create a dataset for CONTENT-BASED RECOMMENDATION: item rows with descriptive numeric "
        "attribute columns plus a 'rating' column (floats 1.0-5.0) correlated with the attributes "
        "so it can be predicted. "
    ),
    "classification": "Create a labeled dataset for CLASSIFICATION with a categorical 'target' column. ",
    "regression": "Create a labeled dataset for REGRESSION with a continuous numeric 'target' column. ",
}

DATA_GEN_PROMPT = """You generate synthetic datasets as executable Python.

Write ONE complete Python snippet that builds a pandas DataFrame and saves it:
- import pandas as pd, numpy as np (nothing else; no network, no file reads)
- build a DataFrame named df with the requested shape and semantics
- df.to_csv(os.environ['OUTPUT_PATH'], index=False)  # os is pre-imported
- print nothing else

For the CSV, disable the sandbox network. {task_hint}
User description: {description}

Requirements:
- Between {n_min} and {n_max} rows, at most {n_cols} columns
- Realistic column names reflecting the description (snake_case)
- All values JSON/CSV-safe (no NaN, no inf, no datetime objects)
Return ONLY the Python code. No markdown. No explanation."""


def _extract_code(text: str) -> str:
    code = text.strip()
    if code.startswith("```python"):
        code = code[9:]
    elif code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]
    return code.strip()


def _validate_snippet(code: str) -> None:
    blocked = ("requests", "urllib", "socket", "subprocess", "open(", "__import__", "eval(", "exec(")
    lowered = code.lower()
    for token in blocked:
        if token.lower() in lowered:
            raise ValueError(f"Generated script contains forbidden operation: {token}")
    if "OUTPUT_PATH" not in code or ("pd.DataFrame" not in code and "pd.concat" not in code):
        raise ValueError("Generated script must build a DataFrame and save it to OUTPUT_PATH")


def generate_dataset(
    description: str,
    task_type: str,
    provider: str,
    model_name: str,
    n_samples: int = 200,
) -> Dict[str, Any]:
    """Ask the LLM for a dataset-builder snippet, run in sandbox, return frame + code.

    Raises ValueError on LLM/sandbox/validation failure (routes map to 400/502).
    """
    desc = (description or "").strip()
    if not desc:
        raise ValueError("Description required")
    n_samples = max(10, min(int(n_samples), 5000))

    llm = get_model(provider, model_name, temperature=0.4, max_tokens=2000)
    prompt = DATA_GEN_PROMPT.format(
        task_hint=TASK_HINTS.get(task_type, TASK_HINTS["classification"]),
        description=desc,
        n_min=int(n_samples * 0.8),
        n_max=int(n_samples * 1.2),
        n_cols=25,
    )
    raw = llm.invoke(prompt)
    content = raw.content if hasattr(raw, "content") else str(raw)
    if isinstance(content, list):  # some providers return content blocks
        content = "".join(str(getattr(b, "text", b)) for b in content)
    code = _extract_code(str(content))

    try:
        _validate_snippet(code)
        import ast
        ast.parse(code)
    except SyntaxError as e:
        raise ValueError(f"LLM produced invalid Python: {e}")

    work_dir = tempfile.mkdtemp(prefix="miniml_datagen_")
    script_path = os.path.join(work_dir, "gen_data.py")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(code + "\n")

    process = run_script(script_path, work_dir, None, timeout=90)

    output_path = os.path.join(work_dir, "output.csv")
    error_tail = (process.stderr or process.stdout or "")[-600:]

    if process.returncode != 0:
        logger.error(f"Data-gen sandbox failed: {error_tail}")
        raise ValueError(f"Generated script failed in sandbox: {error_tail}")

    if not os.path.exists(output_path):
        raise ValueError(f"Generated script produced no output.csv. Script output: {error_tail or '(empty)'}")

    try:
        df = pd.read_csv(output_path)
    except Exception as e:
        raise ValueError(f"Generated dataset unreadable: {e}")

    if df.empty or df.shape[1] == 0:
        raise ValueError("Generated dataset is empty")

    return {"df": df, "code": code, "rows": len(df)}
