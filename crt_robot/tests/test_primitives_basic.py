import numpy as np
import pytest

from crt_robot.primitives import candles as cd
from crt_robot.primitives.liquidity import (Outcome, classify, closed_above, swept_above, swept_below,
                                            turtle_soup, unswept)
from crt_robot.primitives.swings import fractal_swings, ict_swings, known_swings
from crt_robot.tests.fixtures import bars, from_highs_lows


def test_candle_helpers():
    df = bars([(1, 3, 0, 2), (2, 2.5, 1, 1), (1, 1, 1, 1)])
    assert list(cd.body_top(df)) == [2, 2, 1] and list(cd.body_bottom(df)) == [1, 1, 1]
    assert list(cd.direction(df)) == [1, -1, 0]
    assert list(cd.mid(df)) == [1.5, 1.75, 1.0]


def test_atr_wilder_and_no_lookahead():
    df = bars([(1, 2, 0, 1)] * 20)
    a = cd.atr(df, 14)
    assert np.isnan(a[12]) and a[13] == pytest.approx(2.0) and a[-1] == pytest.approx(2.0)
    df2 = df.copy()
    df2.iloc[-1, df2.columns.get_loc("high")] = 10
    assert np.allclose(cd.atr(df2, 14)[:-1], a[:-1], equal_nan=True)


def test_thick():
    df = bars([(1, 2.1, 0.9, 2.0), (1, 2, 0, 1.1)])
    assert list(cd.thick(df, np.array([1.0, 1.0]))) == [True, False]


def test_fractal_swings_strict_and_known_at():
    highs = [1, 2, 5, 2, 1, 3, 3, 1]
    lows = [0, 1, 4, 1, 0, 2, 2, 0]
    sw = fractal_swings(from_highs_lows(highs, lows), n=2)
    hi = sw[sw.kind == "high"]
    assert list(hi.idx) == [2]           # equal highs at 5,6 are not strict swings
    assert list(hi.known_at) == [4]
    lo = sw[sw.kind == "low"]
    assert list(lo.idx) == [4]
    assert known_swings(sw, 3).empty and len(known_swings(sw, 4)) == 1


def test_ict_levels():
    # STHs at 1,3,5,7,9 with prices 2,4,3,6,5 -> ITH at 3 (4>2,3) and 7 (6>3,5); LTH: 7 (6>4 and needs right ITH)
    highs = [1, 2, 1, 4, 1, 3, 1, 6, 1, 5, 1, 4.5, 1, 2, 1]
    lows = [0.5] * len(highs)
    sw = ict_swings(from_highs_lows(highs, lows), max_level=3)
    hi = sw[sw.kind == "high"].set_index("idx")
    assert hi.loc[3, "level"] == 2 and hi.loc[7, "level"] == 2
    assert hi.loc[1, "level"] == 1
    # ITH at 3 is known when STH at 5 is known (bar 6)
    assert hi.loc[3, "known_at_l2"] == 6
    assert len(known_swings(sw, 5, kind="high", min_level=2)) == 0
    assert len(known_swings(sw, 6, kind="high", min_level=2)) == 1


def test_ict_long_term():
    highs = [1, 2, 1, 4, 1, 3, 1, 8, 1, 3, 1, 5, 1, 2, 1, 1]
    sw = ict_swings(from_highs_lows(highs, [0.5] * len(highs)), max_level=3)
    hi = sw[sw.kind == "high"].set_index("idx")
    # ITHs at 3 (4), 7 (8), 11 (5) -> 7 is an LTH, known when ITH 11 is known (STH 13 known at 14)
    assert hi.loc[7, "level"] == 3 and hi.loc[7, "known_at_l3"] == 14


def test_sweep_and_close_beyond():
    assert swept_above(1.1001, 1.1) and not swept_above(1.1, 1.1)
    assert not swept_above(1.10005, 1.1, min_excess=0.0001) and swept_above(1.1001, 1.1, min_excess=0.0001)
    assert swept_below(0.99, 1.0)
    assert not closed_above(1.1, 1.1)


@pytest.mark.parametrize("nxt,expected", [
    ((5, 12, 6, 11), Outcome("breakout_up")),
    ((5, 9, 1, 2), Outcome("breakout_down")),
    ((5, 11, 4, 9), Outcome("ts_high")),
    ((5, 8, 2, 4), Outcome("ts_low")),
    ((5, 9, 4, 6), Outcome("inside")),
    ((5, 11, 2, 8.5), Outcome("ts_high", True)),
    ((5, 11, 2, 4), Outcome("ts_low", True)),
    ((5, 11, 2, 12), Outcome("breakout_up", True)),
])
def test_classify(nxt, expected):
    ref = {"open": 5, "high": 10, "low": 3, "close": 6}
    o, h, l, c = nxt
    assert classify(ref, {"open": o, "high": h, "low": l, "close": c}) == expected


def test_turtle_soup_same_bar_and_delayed():
    df = bars([(5, 6, 4, 5), (5, 10.5, 5, 9), (9, 9.5, 8, 8)])
    ts = turtle_soup(df, 10, "high")
    assert ts.sweep_idx == 1 and ts.confirm_idx == 1 and ts.extreme == 10.5
    df2 = bars([(5, 6, 4, 5), (5, 10.5, 5, 10.2), (10, 10.8, 9, 9.5)])
    assert turtle_soup(df2, 10, "high", close_back_bars=1) == "breakout"
    ts2 = turtle_soup(df2, 10, "high", close_back_bars=2)
    assert ts2.confirm_idx == 2 and ts2.extreme == 10.8
    assert turtle_soup(df, 20, "high") is None


def test_turtle_soup_low_and_unswept():
    df = bars([(5, 6, 4, 5), (5, 5.5, 2.9, 3.5)])
    ts = turtle_soup(df, 3, "low")
    assert ts.side == "low" and ts.extreme == 2.9
    assert unswept(df, 6.5, "high", 0, 2) and not unswept(df, 3, "low", 0, 2)
