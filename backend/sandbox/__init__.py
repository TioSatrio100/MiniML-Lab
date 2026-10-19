"""
sandbox - Executes LLM-generated experiment scripts isolated from host.

Modes (env SANDBOX):
  docker      container: --network none, memory/cpu caps, temp-dir mount (default if available)
  subprocess  host python with env allowlist (fallback / dev machines without Docker)

Auto-fallback: docker mode falls back to subprocess when Docker daemon unreachable.
"""
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)

IMAGE = "miniml-sandbox:latest"
SANDBOX_DIR = os.path.dirname(os.path.abspath(__file__))

ENV_MODE = os.environ.get("SANDBOX", "docker").lower()
_docker_checked = False
_docker_ok = False

# Host env allowlist for subprocess mode — never pass full os.environ.
ENV_ALLOWLIST = ["PATH", "SystemRoot", "WINDIR", "TEMP", "TMP", "HOME", "USERPROFILE", "LANG"]


def _docker_available() -> bool:
    global _docker_checked, _docker_ok
    if _docker_checked:
        return _docker_ok
    _docker_checked = True
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=15,
            env=_filtered_env(),
        )
        _docker_ok = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        _docker_ok = False
    if not _docker_ok:
        logger.warning("Docker unavailable — falling back to subprocess sandbox (SANDBOX=subprocess)")
    return _docker_ok


def _filtered_env(extra: Optional[dict] = None) -> dict:
    env = {k: os.environ[k] for k in ENV_ALLOWLIST if k in os.environ}
    if extra:
        env.update(extra)
    return env


def _ensure_image() -> bool:
    try:
        check = subprocess.run(
            ["docker", "image", "inspect", IMAGE],
            capture_output=True, timeout=30, env=_filtered_env(),
        )
        if check.returncode == 0:
            return True
        logger.info(f"Building sandbox image {IMAGE}...")
        build = subprocess.run(
            ["docker", "build", "-t", IMAGE, SANDBOX_DIR],
            capture_output=True, text=True, timeout=600, env=_filtered_env(),
        )
        if build.returncode != 0:
            logger.error(f"Image build failed: {build.stderr[-500:]}")
            return False
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.error(f"Docker image setup failed: {e}")
        return False


def run_script(
    script_path: str,
    work_dir: str,
    data_path: Optional[str],
    timeout: int = 120,
    env_extra: Optional[dict] = None,
) -> subprocess.CompletedProcess:
    """Run exp.py. Returns CompletedProcess with returncode/stdout/stderr.
    Work dir must contain script_path. data_path=None scripts run without an input
    dataset (generators write results to OUTPUT_PATH inside work_dir)."""
    if ENV_MODE == "docker" and _docker_available() and _ensure_image():
        return _run_docker(script_path, work_dir, data_path, timeout, env_extra)
    return _run_subprocess(script_path, work_dir, data_path, timeout, env_extra)


def _run_docker(
    script_path: str,
    work_dir: str,
    data_path: Optional[str],
    timeout: int,
    env_extra: Optional[dict],
) -> subprocess.CompletedProcess:
    env_args = []
    if data_path:
        # Copy dataset into mounted work dir — container reads /work/data.csv
        local_data = os.path.join(work_dir, "data.csv")
        if os.path.abspath(data_path) != os.path.abspath(local_data):
            shutil.copy2(data_path, local_data)
        env_args += ["-e", "DATA_PATH=/work/data.csv"]
    env_args += ["-e", "OUTPUT_PATH=/work/output.csv"]
    for k, v in (env_extra or {}).items():
        env_args += ["-e", f"{k}={v}"]

    mount = os.path.abspath(work_dir).replace("\\", "/")
    cmd = [
        "docker", "run", "--rm",
        "--network", "none",
        "--memory", "512m",
        "--cpus", "1",
        "-v", f"{mount}:/work",
        "-w", "/work",
        *env_args,
        IMAGE,
        "python", "/work/" + os.path.basename(script_path),
    ]
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, env=_filtered_env(),
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, returncode=124, stdout="", stderr="TIMEOUT")


def _run_subprocess(
    script_path: str,
    work_dir: str,
    data_path: Optional[str],
    timeout: int,
    env_extra: Optional[dict],
) -> subprocess.CompletedProcess:
    extra = {"OUTPUT_PATH": os.path.join(work_dir, "output.csv")}
    if data_path:
        extra["DATA_PATH"] = data_path
    extra.update(env_extra or {})
    return subprocess.run(
        [sys.executable, script_path],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=_filtered_env(extra),
        cwd=work_dir,
    )
