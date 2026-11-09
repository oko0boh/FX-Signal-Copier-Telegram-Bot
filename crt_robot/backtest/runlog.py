"""Append-only log of every backtest run (BUILD_PLAN 3.3).

One JSON object per line. The path comes from ``CRT_RUNS_LOG`` (read at call
time) or defaults to ``runs/runs_log.jsonl``.
"""

from __future__ import annotations

import json
import os
import subprocess
import uuid
from pathlib import Path
from typing import Any

import pandas as pd

from crt_robot.config import REPO_ROOT


def runs_log_path() -> Path:
    return Path(os.environ.get("CRT_RUNS_LOG", REPO_ROOT / "runs" / "runs_log.jsonl"))


def _git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, capture_output=True,
                              text=True, timeout=5).stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def _jsonable(x: Any) -> Any:
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    if isinstance(x, (pd.Timestamp,)):
        return x.isoformat()
    if hasattr(x, "item") and callable(x.item):
        try:
            return x.item()
        except (ValueError, TypeError):
            pass
    if isinstance(x, (str, int, float, bool)) or x is None:
        return x
    return repr(x)


def log_run(record: dict[str, Any], path: Path | None = None) -> str:
    path = path or runs_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    run_id = uuid.uuid4().hex[:12]
    row = {"run_id": run_id, "logged_at": pd.Timestamp.now(tz="UTC").isoformat(), "git": _git_commit(),
           **_jsonable(record)}
    with open(path, "a") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
    return run_id


def read_runs(path: Path | None = None) -> list[dict[str, Any]]:
    path = path or runs_log_path()
    if not path.exists():
        return []
    with open(path) as fh:
        return [json.loads(line) for line in fh if line.strip()]


def previous_holdout_runs(strategy: str, path: Path | None = None) -> list[dict[str, Any]]:
    return [r for r in read_runs(path) if r.get("uses_holdout") and r.get("strategy") == strategy]
