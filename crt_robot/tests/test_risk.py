import pandas as pd
import pytest

from crt_robot.data.instruments import get_instrument
from crt_robot.risk.daily_stop import DailyLossGuard
from crt_robot.risk.sizing import lots_for_risk, risk_amount
from crt_robot.timeutil import ny_time


def test_lots_for_one_percent():
    eu, xau = get_instrument("EURUSD"), get_instrument("XAUUSD")
    assert lots_for_risk(10_000, 1.1000, 1.0990, eu, include_commission=False) == pytest.approx(1.0)
    assert lots_for_risk(10_000, 2000.0, 1995.0, xau, include_commission=False) == pytest.approx(0.2)
    lots = lots_for_risk(10_000, 1.1000, 1.0990, eu)  # commission eats some of the budget
    assert lots == pytest.approx(0.93)   # 100 / (100 + 7)
    assert risk_amount(lots, 1.1, 1.099, eu) + lots * eu.commission_per_lot <= 100 + 1e-9


def test_rounds_down_and_skips_too_small():
    eu = get_instrument("EURUSD")
    assert lots_for_risk(10_000, 1.1, 1.0, eu) == 0.0   # 1000-pip stop: below min lot -> skip
    assert lots_for_risk(10_000, 1.1, 1.09933, eu, include_commission=False) == pytest.approx(1.49)
    with pytest.raises(ValueError):
        lots_for_risk(10_000, 1.1, 1.1, eu)


def test_daily_guard_blocks_until_next_ny_day():
    g = DailyLossGuard(0.02)
    t0 = ny_time(2024, 7, 9, 0, 5)
    assert not g.update(t0, 10_000)
    assert not g.update(t0 + pd.Timedelta(hours=3), 9_850)
    assert g.update(t0 + pd.Timedelta(hours=5), 9_800)
    assert not g.can_trade(t0 + pd.Timedelta(hours=6))
    # recovering intraday does not unblock
    assert g.update(t0 + pd.Timedelta(hours=7), 10_100)
    nxt = ny_time(2024, 7, 10, 0, 1)
    assert not g.update(nxt, 9_800) and g.can_trade(nxt)
    assert g.hits == [ny_time(2024, 7, 9).tz_convert("America/New_York").date()]


def test_ny_day_boundary_not_utc():
    g = DailyLossGuard(0.02)
    a = ny_time(2024, 7, 9, 19, 0)   # 23:00 UTC
    b = ny_time(2024, 7, 9, 21, 0)   # 01:00 UTC next day, same NY day
    g.update(a, 10_000)
    assert g.update(b, 9_700)


def test_invalid_limit():
    with pytest.raises(ValueError):
        DailyLossGuard(2)
