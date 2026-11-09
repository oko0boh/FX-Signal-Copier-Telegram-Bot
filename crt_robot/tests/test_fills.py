import pandas as pd
import pytest

from crt_robot.backtest.fills import BarPrices, entry_fill, exit_fill, market_exit
from crt_robot.backtest.orders import LONG, SHORT, Order, Position

T = pd.Timestamp("2024-01-08 15:00", tz="UTC")


def pos(side, entry, stop, target, kind="market"):
    return Position(side, T, 0, entry, stop, target, 1.0, 100.0, kind, None)


def test_market_entry_pays_spread_and_slippage():
    bar = BarPrices(1.1000, 1.1010, 1.0990, 1.1005, spread=0.0001)
    assert entry_fill(Order(LONG, stop=1.09), bar, 0.00002) == pytest.approx(1.10012)
    assert entry_fill(Order(SHORT, stop=1.12), bar, 0.00002) == pytest.approx(1.09998)


def test_limit_and_stop_entries():
    bar = BarPrices(1.1000, 1.1010, 1.0990, 1.1005, spread=0.0001)
    # long limit at 1.0995: ask low 1.0991 <= 1.0995 -> fill at limit
    assert entry_fill(Order(LONG, 1.098, kind="limit", price=1.0995), bar, 0.0) == 1.0995
    assert entry_fill(Order(LONG, 1.098, kind="limit", price=1.0980 + 0.0009), bar, 0.0) is None
    # short limit at 1.1008 (bid high 1.1010 reaches it)
    assert entry_fill(Order(SHORT, 1.103, kind="limit", price=1.1008), bar, 0.0) == 1.1008
    # long stop at 1.1008: ask high 1.1011 >= -> 1.1008 + slip
    assert entry_fill(Order(LONG, 1.099, kind="stop", price=1.1008), bar, 0.00001) == pytest.approx(1.10081)
    # gap: open already above stop-entry price -> worse fill at ask open
    gap = BarPrices(1.1020, 1.1030, 1.1015, 1.1025, 0.0001)
    assert entry_fill(Order(LONG, 1.099, kind="stop", price=1.1008), gap, 0.0) == pytest.approx(1.1021)


def test_stop_wins_when_both_hit():
    bar = BarPrices(1.1000, 1.1050, 1.0950, 1.1000, 0.0)
    assert exit_fill(pos(LONG, 1.1, 1.097, 1.103), bar, 0.0, entry_bar=False) == (1.097, "stop")
    assert exit_fill(pos(SHORT, 1.1, 1.103, 1.097), bar, 0.0, entry_bar=False) == (1.103, "stop")


def test_short_exits_use_ask():
    bar = BarPrices(1.1000, 1.1009, 1.0990, 1.1000, spread=0.0002)
    # bid high 1.1009 < stop 1.1010 but ask high 1.1011 >= stop -> stopped
    assert exit_fill(pos(SHORT, 1.1, 1.1010, 1.09), bar, 0.0, False)[1] == "stop"
    # target 1.0991: ask low 1.0992 does not reach it
    assert exit_fill(pos(SHORT, 1.1, 1.2, 1.0991), bar, 0.0, False) is None


def test_gap_through_stop_fills_at_open():
    bar = BarPrices(1.0950, 1.0960, 1.0940, 1.0955, 0.0)
    px, why = exit_fill(pos(LONG, 1.1, 1.097, 1.11), bar, 0.00001, False)
    assert why == "stop" and px == pytest.approx(1.09499)


def test_entry_bar_target_ignored_for_limit_but_stop_not():
    bar = BarPrices(1.1000, 1.1050, 1.0990, 1.1040, 0.0)
    assert exit_fill(pos(LONG, 1.0995, 1.098, 1.104, "limit"), bar, 0.0, entry_bar=True) is None
    assert exit_fill(pos(LONG, 1.0995, 1.098, 1.104, "market"), bar, 0.0, entry_bar=True) == (1.104, "target")
    assert exit_fill(pos(LONG, 1.0995, 1.0991, 1.104, "limit"), bar, 0.0, entry_bar=True)[1] == "stop"


def test_market_exit_sides():
    p = pos(SHORT, 1.1, 1.2, None)
    assert market_exit(p, 1.1000, 0.0002, 0.0) == pytest.approx(1.1002)
    assert market_exit(pos(LONG, 1.1, 1.0, None), 1.1, 0.0002, 0.00001) == pytest.approx(1.09999)


def test_order_validation():
    with pytest.raises(ValueError):
        Order(LONG, stop=1.2, kind="limit", price=1.1)
    with pytest.raises(ValueError):
        Order(SHORT, stop=1.2, target=1.3, kind="limit", price=1.1)
    with pytest.raises(ValueError):
        Order(2, stop=1.0)
    with pytest.raises(ValueError):
        Order(LONG, stop=1.0, kind="stop")
