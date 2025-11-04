"""
Thin wrapper around the local T.E.S.T. runner located under tools/external/test.

Provides a function `run_test` that executes the Python script with the given
SMILES and endpoints and returns the parsed JSON as a Python dict.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def _repo_root() -> Path:
    # Compute repo root relative to this file to avoid requiring Django setup
    # backend/chemistry/providers/external_tools/test_runner.py → repo_root = parents[4]
    here = Path(__file__).resolve()
    try:
        return here.parents[4]
    except Exception:
        # Fallback to current working directory
        return Path.cwd()


def _runner_dir() -> Path:
    return _repo_root() / "tools" / "external" / "test"


def run_test(
    smiles: Iterable[str],
    endpoints: Iterable[str],
    *,
    python_executable: str = "python3",
    timeout_sec: Optional[int] = None,
) -> Dict[str, Any]:
    """Run the local T.E.S.T. runner and return parsed JSON.

    Args:
        smiles: Iterable of SMILES strings
        endpoints: Iterable of endpoint names (e.g., ["LD50", "Mutagenicity"])
        python_executable: Python executable to use (default: python3)
        timeout_sec: Optional timeout in seconds

    Returns:
        Dict containing the JSON response from the tool

    Raises:
        FileNotFoundError: If the runner script cannot be found
        RuntimeError: If the process fails or returns non-JSON output
    """
    runner_dir = _runner_dir()
    runner_script = runner_dir / "run_test.py"
    if not runner_script.exists():
        raise FileNotFoundError(f"T.E.S.T. runner not found at: {runner_script}")

    cmd: List[str] = [python_executable, str(runner_script)]
    for s in smiles:
        cmd += ["--smiles", s]
    calc = ",".join(endpoints)
    cmd += ["--calculate", calc]

    env = os.environ.copy()
    # Ensure consistent language/decimal formats if needed
    env.setdefault("LC_ALL", "C.UTF-8")
    env.setdefault("LANG", "C.UTF-8")

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(runner_dir),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"T.E.S.T. runner failed: {e.stderr or e.stdout}") from e

    out = proc.stdout.strip()
    # Some runners may write to stderr; if stdout empty, try stderr
    if not out:
        out = (proc.stderr or "").strip()
    try:
        data = json.loads(out)
    except Exception as e:
        raise RuntimeError(f"Failed to parse T.E.S.T. JSON output: {out[:500]}") from e

    return data
