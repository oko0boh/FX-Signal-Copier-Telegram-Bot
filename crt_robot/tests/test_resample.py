import numpy as np
import pandas as pd
import pytest

from crt_robot.data.resample import resample
from crt_robot.data.synthetic import random_walk
from crt_robot.timeutil import NY_TZ


@pytest.fixture(scope="module")
def m1():
    # spans the 2024-03-10 US DST change and the EU change on 2024-03-31
    return random_walk("2024-03-03 17:00", "2024-04-06", spread=1e-4, seed=3)


def _ny(idx):
    return pd.DatetimeIndex(idx).tz_convert(NY_TZ)


def test_4h_opens_on_1_5_9_grid_across_dst(m1):
    h4 = resample(m1, "4H")
    assert set(_ny(h4.index).hour) == {1, 5, 9, 13, 17, 21}
    assert (_ny(h4.index).minute == 0).all()
    assert ((h4["close_time"] - h4.index) == pd.Timedelta(hours=4)).all()


def test_daily_opens_17_ny_and_weekly_sunday_17(m1):
    d = resample(m1, "D")
    assert set(_ny(d.index).hour) == {17}
    w = resample(m1, "W")
    assert (_ny(w.index).dayofweek == 6).all() and set(_ny(w.index).hour) == {17}
    wc = _ny(pd.DatetimeIndex(w["close_time"]))
    assert (wc.dayofweek == 4).all() and set(wc.hour) == {17}
    # five broker days per week, Sunday-evening bars belong to Monday's candle
    assert len(d) == 5 * len(w)


def test_d_ny_is_midnight(m1):
    d = resample(m1, "D_NY")
    assert set(_ny(d.index).hour) == {0}


def test_ohlc_aggregation_matches_manual(m1):
    h1 = resample(m1, "1H")
    t0 = h1.index[7]
    chunk = m1[(m1.index >= t0) & (m1.index < t0 + pd.Timedelta(hours=1))]
    row = h1.loc[t0]
    assert row["open"] == chunk["open"].iloc[0] and row["close"] == chunk["close"].iloc[-1]
    assert row["high"] == chunk["high"].max() and row["low"] == chunk["low"].min()
    assert row["ask_high"] == chunk["ask_high"].max() and row["n_bars"] == 60
    assert row["volume"] == chunk["volume"].sum()


def test_every_minute_lands_in_exactly_one_bar(m1):
    for tf in ["15m", "1H", "4H", "D", "W"]:
        out = resample(m1, tf)
        assert out["n_bars"].sum() == len(m1)
        # bars do not overlap
        assert (out.index[1:] >= pd.DatetimeIndex(out["close_time"])[:-1]).all()


def test_incomplete_last_bar_flagged(m1):
    cut = m1[m1.index < m1.index[0] + pd.Timedelta(hours=6, minutes=30)]
    h4 = resample(cut, "4H")
    assert h4["complete"].tolist()[:-1] == [True] * (len(h4) - 1)
    assert not h4["complete"].iloc[-1]


def test_rejects_unsorted_or_naive(m1):
    with pytest.raises(ValueError):
        resample(m1.iloc[::-1], "1H")
    naive = m1.copy()
    naive.index = naive.index.tz_localize(None)
    with pytest.raises(ValueError):
        resample(naive, "1H")


def test_summer_vs_winter_utc_offsets(m1):
    h4 = resample(m1, "4H")
    winter = h4[h4.index < pd.Timestamp("2024-03-08", tz="UTC")]
    summer = h4[h4.index > pd.Timestamp("2024-03-12", tz="UTC")]
    # 01:00 NY = 06:00 UTC in winter, 05:00 UTC in summer
    assert np.isin(winter.index.hour, [22, 2, 6, 10, 14, 18]).all()
    assert np.isin(summer.index.hour, [21, 1, 5, 9, 13, 17]).all()
