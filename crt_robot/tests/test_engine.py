import numpy as np
import pandas as pd
import pytest

from crt_robot.backtest.engine import Backtester, EngineConfig
from crt_robot.backtest.metrics import max_drawdown, r_stats, summarize
from crt_robot.backtest.orders import LONG, ClosePosition, Order
from crt_robot.backtest.runlog import read_runs
from crt_robot.backtest.splits import HoldoutLockedError
from crt_robot.data.instruments import get_instrument
from crt_robot.data.synthetic import random_walk
from crt_robot.tests.strategies import TimedLong
from crt_robot.timeutil import NY_TZ

EU = get_instrument("EURUSD")
HTFS = ("15m", "1H", "4H")


@pytest.fixture(scope="module")
def walk():
    return random_walk("2024-01-07 17:00", "2024-01-20", seed=4)


def test_refuses_holdout_without_flag():
    late = random_walk("2025-06-01 17:00", "2025-06-06", seed=1)
    with pytest.raises(HoldoutLockedError):
        Backtester(late, EU, HTFS)
    bt = Backtester(late, EU, HTFS, config=EngineConfig(allow_holdout=True))
    res = bt.run(TimedLong())
    assert read_runs()[-1]["uses_holdout"] is True and res.run_id


def test_refuses_data_only_instrument(walk):
    with pytest.raises(ValueError):
        Backtester(walk, get_instrument("XAGUSD"), HTFS)


def test_every_run_logged_with_params(walk):
    bt = Backtester(walk, EU, HTFS)
    bt.run(TimedLong(hour=10), params={"hour": 10})
    row = read_runs()[-1]
    assert row["strategy"] == "test_timed_long" and row["params"] == {"hour": 10}
    assert row["uses_holdout"] is False and "summary" in row and row["config"]["risk_frac"] == 0.01


def test_risk_per_trade_is_one_percent(walk):
    res = Backtester(walk, EU, HTFS).run(TimedLong(), log=False)
    t = res.trades
    assert len(t) >= 8
    # risk at entry never above 1% of the equity at that moment (rounded down lots)
    eq_before = 10_000 + t["pnl"].cumsum().shift(1, fill_value=0)
    assert (t["risk_usd"] <= eq_before * 0.01 + 1e-6).all()
    assert (t["risk_usd"] >= eq_before * 0.0095).all()
    stops = t[t.reason == "stop"]
    assert (stops["r"] < -0.95).all() and (stops["r"] > -1.2).all()


def test_entry_happens_on_next_bar_open(walk):
    res = Backtester(walk, EU, HTFS).run(TimedLong(), log=False)
    first = res.trades.iloc[0]
    ny = first.entry_time.tz_convert(NY_TZ)
    assert (ny.hour, ny.minute) == (9, 0)    # decided at 09:00 close-of-08:59 bar -> fills 09:00 bar open
    assert first.entry == pytest.approx(walk.loc[first.entry_time, "open"] + EU.spread + EU.slippage)


class AlwaysLong:
    name = "test_always_long"

    def on_bar(self, snap, state):
        if state.position is None and state.can_trade:
            px = snap.last("close")
            return [Order(LONG, stop=px - 0.0005, target=px + 0.05)]
        return []


def test_daily_stop_blocks_rest_of_ny_day():
    # steadily falling market: every long loses
    idx_len = len(random_walk("2024-01-08 00:00", "2024-01-11 00:00"))
    falling = random_walk("2024-01-08 00:00", "2024-01-11 00:00", sigma=0.00001, seed=2,
                          drift=np.full(idx_len, -0.00002))
    res = Backtester(falling, EU, HTFS).run(AlwaysLong(), log=False)
    t = res.trades
    assert len(res.daily_stop_days) >= 2
    t = t.assign(day=pd.DatetimeIndex(t.entry_time).tz_convert(NY_TZ).date)
    for day, g in t.groupby("day"):
        day_pnl = g["pnl"].cumsum()
        start = 10_000 + t[t.day < day]["pnl"].sum()
        # no new entry after the -2% line was crossed in that NY day
        crossed = np.flatnonzero(day_pnl.to_numpy() <= -0.02 * start)
        if len(crossed):
            assert crossed[0] == len(g) - 1
        assert g["pnl"].sum() >= -0.035 * start   # bounded by limit + one trade overshoot


class OpenThenClose:
    name = "test_open_close"

    def __init__(self):
        self.n = 0

    def on_bar(self, snap, state):
        self.n += 1
        if self.n == 10:
            px = snap.last("close")
            return [Order(LONG, stop=px - 0.01)]
        if self.n == 30 and state.position is not None:
            return [ClosePosition()]
        return []


def test_strategy_close_and_costs(walk):
    res = Backtester(walk, EU, HTFS).run(OpenThenClose(), log=False)
    t = res.trades.iloc[0]
    assert t.reason == "strategy_close"
    gross = (t.exit - t.entry) * t.lots * EU.contract_size
    assert t.pnl == pytest.approx(gross - EU.commission_per_lot * t.lots)


def test_cost_multiplier_scales_costs(walk):
    one = Backtester(walk, EU, HTFS).run(TimedLong(), log=False)
    two = Backtester(walk, EU, HTFS, config=EngineConfig(cost_multiplier=2.0)).run(TimedLong(), log=False)
    per_lot = lambda r: (r.trades["commission"] / r.trades["lots"]).mean()  # noqa: E731
    assert per_lot(two) == pytest.approx(2 * per_lot(one))
    assert summarize(two)["net_pnl"] < summarize(one)["net_pnl"]


def test_metrics_helpers():
    assert max_drawdown([100, 120, 90, 130]) == pytest.approx(0.25)
    s = r_stats(np.array([1.0, -1.0, 2.0, -1.0]))
    assert s["n"] == 4 and s["mean_r"] == pytest.approx(0.25) and s["profit_factor"] == pytest.approx(1.5)


# ---- Phase 2 additions: tp1 partial and ModifyStop -------------------------

from crt_robot.backtest.orders import ModifyStop  # noqa: E402


class _OneShot:
    """Buy once at a fixed bar with a tp1 partial; optionally move the stop."""

    name = "test_one_shot_tp1"

    def __init__(self, at: int, stop: float, tp1: float, target: float, frac: float = 0.5,
                 be_at: int | None = None):
        self.at, self.stop, self.tp1, self.target, self.frac, self.be_at = at, stop, tp1, target, frac, be_at
        self.entry = None

    def on_bar(self, snap, state):
        if snap.i == self.at:
            return [Order(LONG, stop=self.stop, target=self.target, tp1=self.tp1, tp1_fraction=self.frac)]
        if self.be_at is not None and snap.i == self.be_at and state.position is not None:
            return [ModifyStop(state.position.entry)]
        return []


def _path(prices):
    rows = [(p, p + 0.00001, p - 0.00001, p) for p in prices]
    from crt_robot.tests.fixtures import bars
    return bars(rows, start="2024-01-09 03:00", freq="1min")


def test_tp1_partial_then_target_books_one_trade():
    from crt_robot.backtest.engine import Backtester
    from crt_robot.data.instruments import get_instrument
    prices = [1.1000] * 3 + [1.1010, 1.1020, 1.1030, 1.1040]
    df = _path(prices)
    res = Backtester(df, get_instrument("EURUSD"), htfs=("15m",)).run(
        _OneShot(at=1, stop=1.0990, tp1=1.1015, target=1.1035), log=False)
    t = res.trades
    assert len(t) == 1
    row = t.iloc[0]
    assert row.reason == "target" and bool(row.tp1_hit)
    assert row.tp1_pnl > 0 and row.pnl > row.tp1_pnl
    # half closed at tp1, half at target: total R between the two single-exit outcomes
    assert 1.0 < row.r < 3.5


def test_tp1_partial_then_breakeven_stop():
    from crt_robot.backtest.engine import Backtester
    from crt_robot.data.instruments import get_instrument
    prices = [1.1000] * 3 + [1.1010, 1.1020, 1.1010, 1.1000, 1.0995, 1.0990]
    df = _path(prices)
    res = Backtester(df, get_instrument("EURUSD"), htfs=("15m",)).run(
        _OneShot(at=1, stop=1.0980, tp1=1.1015, target=1.1050, be_at=4), log=False)
    row = res.trades.iloc[0]
    assert row.reason == "stop" and bool(row.tp1_hit)
    assert abs(row.stop - row.entry) < 1e-9          # moved to break-even
    assert row.pnl > 0                              # the partial paid; the rest ~flat (minus costs)


def test_stop_and_tp1_in_same_bar_stops_out_whole_position():
    from crt_robot.backtest.engine import Backtester
    from crt_robot.data.instruments import get_instrument
    from crt_robot.tests.fixtures import bars
    rows = [(1.1, 1.10001, 1.09999, 1.1)] * 3 + [(1.1, 1.1020, 1.0980, 1.1)]
    df = bars(rows, start="2024-01-09 03:00", freq="1min")
    res = Backtester(df, get_instrument("EURUSD"), htfs=("15m",)).run(
        _OneShot(at=1, stop=1.0990, tp1=1.1010, target=1.1030), log=False)
    row = res.trades.iloc[0]
    assert row.reason == "stop" and not bool(row.tp1_hit) and row.r < -0.9
