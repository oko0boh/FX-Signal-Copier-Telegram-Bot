"""Paths and project-wide settings."""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_CACHE = Path(os.environ.get("CRT_DATA_CACHE", REPO_ROOT / "data_cache"))
CONFIG_DIR = REPO_ROOT / "config"
RUNS_LOG = Path(os.environ.get("CRT_RUNS_LOG", REPO_ROOT / "runs" / "runs_log.jsonl"))
