import pandas as pd

from crt_robot.data.quality import find_gaps, quality_report_markdown, run_checks
from crt_robot.data.synthetic import random_walk


def test_clean_synthetic_data_is_ok():
    df = random_walk("2024-01-07", "2024-01-13", spread=1e-4)
    r = run_checks(df)
    assert r.ok and r.weekend_bars == 0 and len(r.gaps) == 0
    assert r.coverage_by_year[2024] > 0.99


def test_detects_duplicates_weekend_bad_ohlc_negative_spread():
    df = random_walk("2024-01-07", "2024-01-13", spread=1e-4)
    weekend_ts = pd.Timestamp("2024-01-13 12:00", tz="America/New_York").tz_convert("UTC")
    extra = df.iloc[[0]].copy()
    extra.index = pd.DatetimeIndex([weekend_ts], name="ts")
    df = pd.concat([df, df.iloc[[5]], extra])
    df.iloc[10, df.columns.get_loc("high")] = df.iloc[10]["low"] - 1e-3
    df.iloc[20, df.columns.get_loc("ask_close")] = df.iloc[20]["close"] - 1e-3
    r = run_checks(df)
    assert r.duplicates == 1 and r.unsorted >= 1
    assert r.weekend_bars == 1 and r.bad_ohlc >= 1 and r.negative_spread == 1
    assert not r.ok
    assert "PROBLEMS FOUND" in quality_report_markdown("EURUSD", r)


def test_gap_detection_ignores_weekend():
    df = random_walk("2024-01-07", "2024-01-20")
    cut = (df.index >= pd.Timestamp("2024-01-09 10:00", tz="UTC")) & (df.index < pd.Timestamp("2024-01-09 11:00", tz="UTC"))
    gaps = find_gaps(pd.DatetimeIndex(df.index[~cut]))
    assert len(gaps) == 1 and gaps.iloc[0]["missing_minutes"] == 60


def test_spike_detection():
    df = random_walk("2024-01-07", "2024-01-09")
    i = 500
    df.iloc[i, df.columns.get_loc("high")] += 0.02
    r = run_checks(df)
    assert df.index[i] in r.spikes.index
