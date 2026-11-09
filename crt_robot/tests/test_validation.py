"""Backtester validation (BUILD_PLAN 3.1). Must pass before any strategy work.

(a) a planted edge is detected; (b) random entries on noise show no edge
after costs; (c) a strategy that peeks at a not-yet-closed HTF candle is
caught. Plus Monte Carlo of trade order and the 2x-cost rerun.
All data here is synthetic (crt_robot.data.synthetic), never market data.
"""

import numpy as np
import pandas as pd
import pytest

from crt_robot.backtest.audit import LookAheadDetected, lookahead_audit
from crt_robot.backtest.engine import Backtester, EngineConfig, LookAheadRisk
from crt_robot.backtest.metrics import summarize
from crt_robot.backtest.robustness import cost_stress, monte_carlo_trade_order
from crt_robot.data.instruments import get_instrument
from crt_robot.data.synthetic import fx_minutes, random_walk
from crt_robot.tests.strategies import Closed4HMomentum, CoinFlip, PeekForming4H, TimedLong
from crt_robot.timeutil import NY_TZ

EU = get_instrument("EURUSD")
HTFS = ("15m", "1H", "4H")
START, END = "2024-01-07 17:00", "2024-03-30"


def _planted_drift(start: str, end: str, total: float = 0.0010) -> np.ndarray:
    idx = fx_minutes(start, end)
    ny_hour = idx.tz_convert(NY_TZ).hour
    return np.where(ny_hour == 9, total / 60, 0.0)


@pytest.fixture(scope="module")
def planted():
    return random_walk(START, END, seed=21, drift=_planted_drift(START, END))


@pytest.fixture(scope="module")
def noise():
    return random_walk(START, END, seed=22)


@pytest.fixture(scope="module")
def planted_result(planted):
    return Backtester(planted, EU, HTFS).run(TimedLong(), log=False)


def test_a_planted_edge_is_detected(planted_result):
    s = summarize(planted_result)
    assert s["n"] >= 50
    assert s["mean_r"] > 0.3 and s["t_stat"] > 3.0, s


def test_a_control_same_strategy_on_noise_finds_nothing(noise):
    s = summarize(Backtester(noise, EU, HTFS).run(TimedLong(), log=False))
    assert s["t_stat"] < 2.0, s


def test_b_random_strategy_has_no_edge_after_costs(noise):
    gross = summarize(Backtester(noise, EU, HTFS, config=EngineConfig(cost_multiplier=0.0))
                      .run(CoinFlip(), log=False))
    net = summarize(Backtester(noise, EU, HTFS).run(CoinFlip(), log=False))
    assert gross["n"] >= 400 and net["n"] >= 400
    assert abs(gross["t_stat"]) < 2.5, gross          # zero-cost coin flip ~ zero expectancy
    assert net["mean_r"] < 0 and net["t_stat"] < 0, net
    assert net["mean_r"] < gross["mean_r"] - 0.15      # costs show up in R
    assert net["return_pct"] < 0


def test_c_cheater_profits_in_backtest_but_audit_catches_it():
    data = random_walk("2024-01-07 17:00", "2024-01-27", seed=23)
    cheat = summarize(Backtester(data, EU, HTFS).run(PeekForming4H(), log=False))
    assert cheat["win_rate"] > 0.6 and cheat["t_stat"] > 3   # the leak is real ...
    with pytest.raises(LookAheadDetected):                    # ... and caught
        lookahead_audit(PeekForming4H, data, EU, HTFS, n_checks=4)


def test_c_honest_strategies_pass_audit():
    data = random_walk("2024-01-07 17:00", "2024-01-20", seed=24)
    for factory in (Closed4HMomentum, TimedLong, CoinFlip):
        assert lookahead_audit(factory, data, EU, HTFS, n_checks=4)


def test_c_strategy_holding_full_data_is_refused(noise):
    class Hoarder:
        name = "test_hoarder"

        def __init__(self, df):
            self.df = df

        def on_bar(self, snap, state):
            return []

    with pytest.raises(LookAheadRisk):
        Backtester(noise.iloc[:2000], EU, HTFS).run(Hoarder(noise))


def test_c_api_cannot_reach_forming_final_values(noise):
    from crt_robot.data.mtf import MultiTimeframeView
    v = MultiTimeframeView(noise.iloc[:3000], ("4H",))
    for i in range(0, 3000, 97):
        s = v.at(i)
        c = s.closed("4H")
        assert len(c) == 0 or (pd.DatetimeIndex(c["close_time"]) <= s.now).all()
        f = s.forming("4H")
        if f is not None:
            assert f.close == s.last("close")   # partial close = latest price, never the final close


def test_monte_carlo_trade_order(planted_result):
    r = planted_result.trades["r"].to_numpy()
    mc = monte_carlo_trade_order(r, n_sims=500, seed=1)
    assert mc["n_trades"] == len(r)
    dd = mc["max_dd_pct"]
    assert dd["p5"] <= dd["p50"] <= dd["p95"] <= dd["p99"]
    fe = mc["final_equity_x"]
    assert fe["p5"] == pytest.approx(fe["p95"])      # permutation keeps the final equity
    boot = monte_carlo_trade_order(r, n_sims=500, seed=1, bootstrap=True)
    assert boot["final_equity_x"]["p5"] < boot["final_equity_x"]["p95"]
    with pytest.raises(ValueError):
        monte_carlo_trade_order(np.array([]))


def test_two_x_cost_rerun(planted):
    bt = Backtester(planted, EU, HTFS)
    table = cost_stress(bt, TimedLong, multipliers=(1.0, 2.0))
    assert list(table.index) == [1.0, 2.0]
    assert table.loc[2.0, "net_pnl"] < table.loc[1.0, "net_pnl"]
    assert bt.config.cost_multiplier == 1.0   # restored
