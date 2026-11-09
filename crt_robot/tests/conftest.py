import pytest


@pytest.fixture(autouse=True)
def _isolated_runs_log(tmp_path, monkeypatch):
    """Tests never write to the real runs log."""
    monkeypatch.setenv("CRT_RUNS_LOG", str(tmp_path / "runs_log.jsonl"))
    yield
