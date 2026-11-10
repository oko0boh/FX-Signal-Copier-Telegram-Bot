"""CLI ``python -m crt_robot.run``: tuning-only guard, outputs, setups report.
Uses a temporary cache filled with the scripted SYNTHETIC path (never real
data); nothing is written to data_cache/."""

import json

import pandas as pd
import pytest

from crt_robot import run as cli
from crt_robot.crt.report import summarize_setups
from crt_robot.data import dukascopy as dk
from crt_robot.tests.crt.scenarios import bull_4h_crt_at_daily_old_low


@pytest.fixture(scope="module")
def cache(tmp_path_factory):
    root = tmp_path_factory.mktemp("cache")
    df = bull_4h_crt_at_daily_old_low()
    for sym, shift in (("EURUSD", 0.0), ("GBPUSD", 0.18)):
        d = df.copy()
        d[["open", "high", "low", "close"]] += shift
        for (y, m), part in d.groupby([d.index.year, d.index.month]):
            p = dk.month_path(sym, y, m, root)
            p.parent.mkdir(parents=True, exist_ok=True)
            part.to_parquet(p)
    return root


def test_backtest_cli_writes_trades_setups_and_summary(cache, tmp_path, capsys):
    out = tmp_path / "bt"
    rc = cli.main(["backtest", "--mode", "romeo", "--symbol", "EURUSD", "--start", "2024-01-02",
                   "--end", "2024-01-11", "--data-root", str(cache), "--out", str(out), "--no-log"])
    assert rc == 0
    setups = pd.read_csv(out / "setups.csv")
    assert (setups["state"] == "done").sum() >= 1
    assert {"failed_checks", "checks", "sweep_weekday", "sweep_hour", "invalid_reason"} <= set(setups.columns)
    assert pd.read_csv(out / "trades.csv").shape[0] >= 1
    summary = json.loads((out / "summary.json").read_text())
    assert summary["params"]["mode"] == "romeo" and summary["params"]["config_fingerprint"]
    assert summary["params"]["peers"] == ["GBPUSD"]               # DXY not in the cache -> skipped
    md = (out / "setups_summary.md").read_text()
    assert "Rejection / invalidation reasons" in md and "Sweep weekday" in md and "Sweep hour" in md
    assert "No performance figures" in md


def test_backtest_cli_refuses_the_holdout(cache, capsys):
    rc = cli.main(["backtest", "--mode", "romeo", "--symbol", "EURUSD", "--start", "2025-01-01",
                   "--end", "2025-06-01", "--data-root", str(cache), "--no-log"])
    assert rc == 3 and "holdout" in capsys.readouterr().err


def test_backtest_cli_without_data_says_so(tmp_path, capsys):
    rc = cli.main(["backtest", "--mode", "sham", "--symbol", "XAUUSD", "--start", "2024-01-02",
                   "--end", "2024-01-11", "--data-root", str(tmp_path), "--no-log"])
    assert rc == 2 and "NO DATA" in capsys.readouterr().err


def test_backtest_logs_mode_and_fingerprint(cache, tmp_path):
    from crt_robot.backtest.runlog import read_runs
    cli.main(["backtest", "--mode", "hybrid", "--symbol", "EURUSD", "--start", "2024-01-02", "--end", "2024-01-11",
              "--data-root", str(cache), "--out", str(tmp_path / "h"), "--set", "general.swing_n=3", "--no-peers"])
    run = read_runs()[-1]
    assert run["params"]["mode"] == "hybrid" and run["params"]["overrides"] == ["general.swing_n=3"]
    assert run["uses_holdout"] is False


def test_setups_command_combines_modes_and_symbols(cache, tmp_path):
    out = tmp_path / "rep"
    rc = cli.main(["setups", "--modes", "romeo", "hybrid", "--symbols", "EURUSD", "GBPUSD", "--start", "2024-01-02",
                   "--end", "2024-01-11", "--data-root", str(cache), "--out", str(out), "--no-log", "--base", "15m"])
    assert rc == 0
    df = pd.read_csv(out / "setups.csv")
    assert set(df["mode"]) == {"romeo", "hybrid"} and set(df["symbol"]) == {"EURUSD", "GBPUSD"}
    text = (out / "setups_summary.md").read_text()
    assert "By symbol and mode" in text and "First failed rule" in text


def test_summary_of_an_empty_frame():
    assert "No setups" in summarize_setups(pd.DataFrame())
