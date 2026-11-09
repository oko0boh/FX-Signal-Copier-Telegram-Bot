import numpy as np
import pandas as pd
import pytest

from crt_robot.data.synthetic import random_walk
from crt_robot.primitives.levels import midnight_open, previous_period_hl, weekly_open
from crt_robot.primitives.time_windows import h4_rhythm, in_macro, in_window, killzone_labels
from crt_robot.timeutil import ny_time


def _idx(*ny_times):
    return pd.DatetimeIndex([ny_time(2024, 7, 9, h, m) for h, m in ny_times])


def test_killzones_and_wrap():
    idx = _idx((1, 59), (2, 0), (4, 59), (5, 0), (7, 30), (10, 0), (11, 59), (12, 0), (21, 0), (23, 59))
    assert list(killzone_labels(idx)) == ["", "london_open", "london_open", "", "new_york",
                                          "london_close", "london_close", "", "asia", "asia"]
    # winter gives the same NY labels
    w = pd.DatetimeIndex([ny_time(2024, 1, 9, 2, 0)])
    assert killzone_labels(w)[0] == "london_open"
    assert list(in_window(_idx((23, 0), (0, 30), (1, 0)), "23:00", "01:00")) == [True, True, False]


def test_macros():
    idx = _idx((3, 0), (3, 59), (4, 0), (9, 5), (8, 49), (2, 40))
    assert list(in_macro(idx, "hour")) == [True, True, False, True, False, False]
    assert list(in_macro(idx, "ict")) == [False, False, False, True, False, True]
    with pytest.raises(ValueError):
        in_macro(idx, "x")


def test_h4_rhythm_labels():
    idx = _idx((0, 30), (1, 0), (3, 15), (5, 0), (9, 59), (13, 0), (17, 0), (21, 0), (23, 59))
    r = h4_rhythm(idx)
    assert list(r.h4_open_hour) == [21, 1, 1, 5, 9, 13, 17, 21, 21]
    assert list(r.rhythm) == ["9", "1", "1", "5", "9", "1", "5", "9", "9"]
    assert list(r.minute_in_h4) == [210, 0, 135, 0, 59, 0, 0, 0, 179]
    assert list(r.half[:5]) == ["pm", "am", "am", "am", "am"]


@pytest.fixture(scope="module")
def m1():
    return random_walk("2024-07-07 17:00", "2024-07-20", seed=5)


def test_previous_day_high_low_no_lookahead(m1):
    pd_ = previous_period_hl(m1, "D")
    t = ny_time(2024, 7, 10, 3, 0)            # inside broker day Tue 17:00 -> Wed 17:00
    prev = m1[(m1.index >= ny_time(2024, 7, 8, 17)) & (m1.index < ny_time(2024, 7, 9, 17))]
    assert pd_.loc[t, "prev_high"] == prev["high"].max() and pd_.loc[t, "prev_low"] == prev["low"].min()
    first_day = m1.index < ny_time(2024, 7, 8, 17)
    assert pd_.loc[first_day, "prev_high"].isna().all()


def test_previous_week_and_ny_day(m1):
    pw = previous_period_hl(m1, "W")
    wk1 = m1[m1.index < ny_time(2024, 7, 12, 17)]
    t = ny_time(2024, 7, 16, 10)
    assert pw.loc[t, "prev_high"] == wk1["high"].max()
    pdn = previous_period_hl(m1, "D_NY")
    day = m1[(m1.index >= ny_time(2024, 7, 9)) & (m1.index < ny_time(2024, 7, 10))]
    assert pdn.loc[ny_time(2024, 7, 10, 8), "prev_low"] == day["low"].min()


def test_midnight_and_weekly_open(m1):
    mo = midnight_open(m1)
    assert not np.isnan(mo.loc[ny_time(2024, 7, 9, 23, 59)])
    assert mo.loc[ny_time(2024, 7, 10, 0, 0)] == m1.loc[ny_time(2024, 7, 10, 0, 0), "open"]
    assert mo.loc[ny_time(2024, 7, 10, 15, 0)] == m1.loc[ny_time(2024, 7, 10, 0, 0), "open"]
    assert np.isnan(mo.loc[ny_time(2024, 7, 7, 18, 0)])   # Sunday evening: no midnight yet
    wo = weekly_open(m1, "mon_0000")
    assert np.isnan(wo.loc[ny_time(2024, 7, 7, 20, 0)])   # before Monday 00:00
    assert wo.loc[ny_time(2024, 7, 11, 9)] == m1.loc[ny_time(2024, 7, 8, 0, 0), "open"]
    ws = weekly_open(m1, "sun_1700")
    assert ws.loc[ny_time(2024, 7, 11, 9)] == m1.loc[ny_time(2024, 7, 7, 17, 0), "open"]
    with pytest.raises(ValueError):
        weekly_open(m1, "tue")


def test_levels_truncation_invariant(m1):
    cut = m1.iloc[:5000]
    for f in (lambda d: previous_period_hl(d, "D")["prev_high"], midnight_open, weekly_open):
        full, part = f(m1).iloc[:5000], f(cut)
        pd.testing.assert_series_equal(full, part, check_names=False)
