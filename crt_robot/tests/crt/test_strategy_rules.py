"""Rule-level tests of the strategy wrapper: invalidation (group I), risk
limits (group J), stops/targets helpers (groups G/H) on synthetic data."""

import numpy as np
import pytest

from crt_robot.backtest.engine import Backtester, EngineConfig
from crt_robot.crt import strategy as stmod
from crt_robot.crt.config import load_config
from crt_robot.crt.setup import Setup
from crt_robot.crt.strategy import CRTStrategy, view_timeframes
from crt_robot.data.instruments import get_instrument
from crt_robot.tests.crt.helpers import mk, ns
from crt_robot.tests.crt.scenarios import bull_4h_crt_at_daily_old_low

EU = get_instrument("EURUSD")


@pytest.fixture(scope="module")
def scenario():
    return bull_4h_crt_at_daily_old_low()


def _setup(direction="bull", lo=1.0905, hi=1.0950):
    return Setup(id="t", symbol="EURUSD", mode="romeo", htf="4H", ltf="15m", kl_tf="D", parent_htf="D",
                 purpose="trade", direction=direction, detected_ns=0, c1_open_ns=0, c1_close_ns=0, c1={},
                 crt_high=hi, crt_low=lo, sweep_extreme=1.0890)


def test_r45_no_chasing_once_the_50_traded():
    st = CRTStrategy(load_config("romeo"))
    s = _setup()
    path = mk([(1.0920, 1.0930, 1.0915, 1.0925)], "2024-01-09 09:00", "15min", "15m")   # 50% = 1.09275
    assert st._invalidated_before_entry(s, path) and s.invalid_reason == "chased_50_reached"


def test_r58_decisive_closes_beyond_the_sweep_extreme():
    st = CRTStrategy(load_config("romeo"))
    s = _setup()
    rows = [(1.0895, 1.0896, 1.0884, 1.0885), (1.0885, 1.0886, 1.0874, 1.0875)]      # two full-body closes below 1.0890
    assert st._invalidated_before_entry(s, mk(rows, "2024-01-09 09:00", "15min", "15m"))
    assert s.invalid_reason == "decisive_close_beyond" and s.failed[-1].rule == "CRT-R58"
    one = CRTStrategy(load_config("romeo"))
    s1 = _setup()
    assert not one._invalidated_before_entry(s1, mk(rows[:1], "2024-01-09 09:00", "15min", "15m"))
    alt = CRTStrategy(load_config("romeo", ["invalidation.decisive_closes=1"]))
    assert alt._invalidated_before_entry(_setup(), mk(rows[:1], "2024-01-09 09:00", "15min", "15m"))


def test_r64_weekly_trade_cap(scenario):
    cfg = load_config("romeo", ["risk.max_trades_per_week=0"])
    st = CRTStrategy(cfg)
    res = Backtester(scenario, EU, view_timeframes(cfg)).run(st, log=False)
    s = next(x for x in st.setups if "4H-202401090100-bull" in x.id)
    assert s.invalid_reason == "max_trades_per_week" and res.trades.empty


def test_r05_no_trade_against_an_active_higher_tf_crt(scenario):
    cfg = load_config("romeo")
    st = CRTStrategy(cfg)
    blocker = _setup("bear")
    blocker.htf, blocker.id, blocker.state = "D", "fake-daily-bear", "entered"
    st._live.append(blocker)
    Backtester(scenario, EU, view_timeframes(cfg)).run(st, log=False)
    s = next(x for x in st.setups if "4H-202401090100-bull" in x.id)
    assert s.invalid_reason == "counter_htf" and s.check("not_counter_htf").status == "fail"


def test_r67_friday_flat_and_killzone_expiry_helpers():
    assert stmod._friday_flat_ns(ns("2024-01-09 10:00"), "16:00") == ns("2024-01-12 16:00")
    assert stmod._friday_flat_ns(ns("2024-01-12 16:30"), "16:00") == ns("2024-01-19 16:00")
    assert stmod._next_killzone_end(ns("2024-01-09 06:10"), load_config("sham")) == ns("2024-01-09 10:00")
    assert stmod._next_killzone_end(ns("2024-01-09 01:10"), load_config("sham")) == ns("2024-01-09 05:00")


def test_r56_time_exit_and_no_weekend_hold_are_on_the_order(scenario):
    cfg = load_config("romeo")
    st = CRTStrategy(cfg)
    res = Backtester(scenario, EU, view_timeframes(cfg)).run(st, log=False)
    orders = [a for _, acts in res.decisions for a in acts if getattr(a, "tag", "").endswith("bull-130") or
              "202401090100-bull" in getattr(a, "tag", "")]
    o = orders[0]
    assert o.exit_at is not None and o.exit_at.value == ns("2024-01-09 13:00")    # end of C3 (CRT-R56)
    assert o.tp1 is not None and o.tp1_fraction == 0.5


def test_r52_fvg_fill_low_stop_mode(scenario):
    cfg = load_config("romeo", ["stop.stop_mode=fvg_fill_low"])
    st = CRTStrategy(cfg)
    Backtester(scenario, EU, view_timeframes(cfg)).run(st, log=False)
    s = next(x for x in st.setups if "4H-202401090100-bull" in x.id)
    assert s.stop is not None and s.stop < s.entry_price


def test_unimplemented_switches_are_refused():
    for over in (["bias.allow_delivered_counter=true"], ["entry.max_entries_per_setup=2"]):
        with pytest.raises(NotImplementedError):
            CRTStrategy(load_config("romeo", over))


def test_romeo_killzone_option_gates_the_purge(scenario):
    cfg = load_config("romeo", ["timing.romeo_use_killzones=true", "timing.purge_hours=[]",
                                "timing.macros=[\"03:00\"]"])
    st = CRTStrategy(cfg)
    Backtester(scenario, EU, view_timeframes(cfg)).run(st, log=False)
    s = next(x for x in st.setups if "4H-202401090100-bull" in x.id)
    assert s.invalid_reason == "outside_key_time"           # 06:10 purge: no killzone / macro / purge hour
    assert np.isfinite(s.crt_50)
