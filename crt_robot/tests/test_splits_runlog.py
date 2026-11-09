import pandas as pd
import pytest

from crt_robot.backtest.runlog import log_run, previous_holdout_runs, read_runs, runs_log_path
from crt_robot.backtest.splits import DataSplit, HoldoutLockedError


def _frame(start, end):
    idx = pd.date_range(start, end, freq="1D", tz="UTC")
    return pd.DataFrame({"close": range(len(idx))}, index=idx)


def test_split_file_is_locked_to_last_18_months():
    s = DataSplit.load()
    assert s.holdout_start == pd.Timestamp("2025-05-01", tz="UTC")
    assert s.holdout_months == 18 and s.data_start.year == 2015
    locked = pd.Timestamp(s.locked_on, tz="UTC")
    assert (locked - pd.DateOffset(months=18)) >= s.holdout_start


def test_guard_refuses_holdout_without_flag():
    s = DataSplit.load()
    with pytest.raises(HoldoutLockedError):
        s.guard(_frame("2025-01-01", "2025-06-01").index)
    assert s.guard(_frame("2025-01-01", "2025-06-01").index, allow_holdout=True) is True
    assert s.guard(_frame("2020-01-01", "2020-06-01").index) is False
    with pytest.raises(HoldoutLockedError):
        s.holdout(_frame("2020-01-01", "2026-01-01"))


def test_tuning_slice_excludes_holdout():
    s = DataSplit.load()
    t = s.tuning(_frame("2014-06-01", "2026-01-01"))
    assert t.index.min() >= s.data_start and t.index.max() < s.holdout_start
    assert s.guard(t.index) is False


def test_runs_log_appends(tmp_path):
    assert str(runs_log_path()).startswith(str(tmp_path))
    a = log_run({"strategy": "x", "params": {"k": 1}, "uses_holdout": False})
    log_run({"strategy": "x", "params": {"k": 2, "t": pd.Timestamp("2024-01-01", tz="UTC")}, "uses_holdout": True})
    rows = read_runs()
    assert len(rows) == 2 and rows[0]["run_id"] == a and rows[1]["params"]["k"] == 2
    assert len(previous_holdout_runs("x")) == 1 and previous_holdout_runs("y") == []
