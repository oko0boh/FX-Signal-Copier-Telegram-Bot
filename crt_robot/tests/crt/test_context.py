"""Context layers: bias (group B), market profile (G-04), dealing range
(CRT-R16/R21, G-09), time filters (group E, G-11, G-23, G-26), SMT (DEF-18)
and the news blackout hook (CRT-R66)."""

import numpy as np
import pandas as pd
import pytest

from crt_robot.crt import context as ctx
from crt_robot.crt.config import load_config
from crt_robot.crt.smt import PeerFeed, candle_smt
from crt_robot.data.mtf import MultiTimeframeView
from crt_robot.data.synthetic import random_walk
from crt_robot.tests.crt.helpers import mk, ns

CFG = load_config("romeo")
Q = {"open": 1.10, "high": 1.11, "low": 1.09, "close": 1.10}


def bar(o, h, l, c):
    return {"open": o, "high": h, "low": l, "close": c}


# ---- CRT-R06 close vs wick ---------------------------------------------------
@pytest.mark.parametrize("p,want", [
    (bar(1.10, 1.115, 1.095, 1.112), "bull"),      # close above Q.high
    (bar(1.10, 1.105, 1.085, 1.088), "bear"),      # close below Q.low
    (bar(1.10, 1.115, 1.095, 1.105), "bear"),      # wick above, closed back inside
    (bar(1.10, 1.105, 1.085, 1.095), "bull"),      # wick below, closed back inside
    (bar(1.10, 1.115, 1.085, 1.100), "neutral"),   # outside bar closed inside
    (bar(1.10, 1.105, 1.095, 1.100), "inside"),
])
def test_close_wick_bias(p, want):
    assert ctx.close_wick_bias(p, Q) == want


def _trend_days(up=True, n=24):
    """Zig-zag trend: 4 bars with the trend (+30 pips each), 2 against (-40)."""
    rows, p = [], 1.10
    for k in range(n):
        step = 0.003 if k % 6 < 4 else -0.004
        step = step if up else -step
        o, c = p, p + step
        w = 0.0005 if (step > 0) == up else 0.0001       # smaller wicks on counter bars: strict swings
        rows.append((o, max(o, c) + w, min(o, c) - w, c))
        p = c
    return mk(rows, "2024-01-01 00:00", "1D", "D_NY")


def test_structure_label_and_sham_matrix():                       # CRT-R15 / CRT-R08
    up = _trend_days(True)
    assert ctx.structure_label(up, 2) == "bull"
    bias, s, cls = ctx.sham_bias(up, 2)
    assert s == "bull" and bias in ("bull", "bear") and cls
    flat = mk([(1.1, 1.101, 1.099, 1.1)] * 3, "2024-01-01", "1D", "D_NY")
    assert ctx.sham_bias(flat, 2)[0] == "neutral"


# ---- G-04 five phases + outcome table ---------------------------------------
def test_five_phase_outcome_table():
    assert ctx.OUTCOME_WITH_KL["range"] == "expansion" and ctx.OUTCOME_WITH_KL["reversal"] == "range"
    assert ctx.OUTCOME_WITH_KL["manipulation"] == "expansion" and ctx.OUTCOME_WITH_KL["expansion"] == "reversal"
    base = [(1.10, 1.11, 1.09, 1.10), (1.10, 1.11, 1.09, 1.10)]
    exp = mk(base + [(1.10, 1.125, 1.099, 1.12)], "2024-01-01", "1D", "D_NY")
    man = mk(base + [(1.10, 1.115, 1.095, 1.105)], "2024-01-01", "1D", "D_NY")
    rng = mk(base + [(1.10, 1.105, 1.095, 1.101)], "2024-01-01", "1D", "D_NY")
    assert ctx.five_phase(exp, 2) == "expansion"
    assert ctx.five_phase(man, 2) == "manipulation"
    assert ctx.five_phase(rng, 2) == "range"
    assert ctx.sham4(exp, "bull") == "expansion" and ctx.sham4(exp, "bear") == "retracement"


# ---- dealing range ------------------------------------------------------------
def test_dealing_range_needs_displacement_and_size():
    rows = [(1.100, 1.101, 1.099, 1.100), (1.100, 1.102, 1.098, 1.101), (1.101, 1.103, 1.097, 1.099),
            (1.099, 1.100, 1.090, 1.092),   # swing low area
            (1.092, 1.096, 1.091, 1.095), (1.095, 1.099, 1.094, 1.098),
            (1.098, 1.112, 1.0995, 1.111),  # displacement up, leaves an FVG
            (1.111, 1.120, 1.110, 1.118), (1.118, 1.119, 1.112, 1.114), (1.114, 1.116, 1.108, 1.110),
            (1.110, 1.112, 1.105, 1.106)]
    b = mk(rows, "2024-01-01", "4h", "4H")
    cfg = load_config("romeo", {"dealing_range": {"dr_min_atr": 0.5, "dr_require_sweep_both": False}})
    dr = ctx.dealing_range(b, cfg)
    assert dr is not None and dr.high == pytest.approx(1.120) and dr.low == pytest.approx(1.090)
    assert dr.zone(1.115) == "premium" and dr.zone(1.095) == "discount"
    assert ctx.rebalanced(dr, b.slice(slice(0, 9)), "bull") is False   # not yet back down to EQ 1.105
    assert ctx.rebalanced(dr, b, "bull") is True                       # the last low touches EQ
    big = load_config("romeo", {"dealing_range": {"dr_min_atr": 50.0}})
    assert ctx.dealing_range(b, big) is None


# ---- time ---------------------------------------------------------------------
def test_killzones_macros_purge_hours_and_asia():
    assert ctx.killzone(ns("2024-01-09 03:10"), CFG) == "london_open"
    assert ctx.killzone(ns("2024-01-09 12:30"), CFG) == ""
    assert ctx.in_macro(ns("2024-01-09 09:30"), CFG)                     # hour macro
    ict = load_config("romeo", ["timing.macro_window=ict"])
    assert not ctx.in_macro(ns("2024-01-09 09:30"), ict) and ctx.in_macro(ns("2024-01-09 09:05"), ict)
    assert ctx.in_purge_hour(ns("2024-01-09 01:20"), CFG) and not ctx.in_purge_hour(ns("2024-01-09 02:20"), CFG)
    assert ctx.in_key_time(ns("2024-01-09 01:20"), CFG, purge=True)      # 01:00 purge hour counts for purges
    assert not ctx.in_key_time(ns("2024-01-09 01:20"), CFG, purge=False)
    assert ctx.in_asia_block(ns("2024-01-09 21:00"), CFG) and ctx.in_asia_block(ns("2024-01-09 01:59"), CFG)
    assert not ctx.in_asia_block(ns("2024-01-09 02:00"), CFG)
    assert ctx.in_refined_key_time(ns("2024-01-09 08:45"), CFG)
    assert ctx.killzone_end_ns(ns("2024-01-09 07:30"), CFG) == ns("2024-01-09 10:00")


def test_159_rhythm_and_turtle_soup_at_the_open():                     # 6.2, G-23
    assert [ctx.rhythm_159(ns(f"2024-01-09 {h:02d}:00")) for h in (1, 5, 9, 13, 17, 21)] == list("159159")
    o, c = ns("2024-01-09 05:00"), ns("2024-01-09 09:00")
    assert ctx.frac_in_candle(ns("2024-01-09 05:30"), o, c) == pytest.approx(0.125)
    assert ctx.frac_in_candle(ns("2024-01-09 08:30"), o, c) == pytest.approx(0.875)


def test_monday_expansion_filter():                                     # G-26
    rows = [(1.10, 1.105, 1.095, 1.10)] * 20
    days = mk(rows, "2023-12-11", "1D", "D_NY")
    mon = mk([(1.10, 1.125, 1.099, 1.124)], "2023-12-31", "1D", "D_NY")      # Sunday stub slot skipped below
    allb = mk(rows + [(1.10, 1.125, 1.099, 1.124)], "2023-12-12", "1D", "D_NY")
    # make the last bar a Monday: 2024-01-01 is a Monday
    assert pd.Timestamp(int(allb.open_time[-1]), tz="UTC").tz_convert("America/New_York").day_of_week == 0
    assert ctx.monday_expansion(allb, ns("2024-01-02 10:00"), CFG) is True
    calm = mk(rows + [(1.10, 1.104, 1.096, 1.10)], "2023-12-12", "1D", "D_NY")
    assert ctx.monday_expansion(calm, ns("2024-01-02 10:00"), CFG) is False
    assert ctx.monday_expansion(calm, ns("2024-01-01 10:00"), CFG) is None    # Monday itself: not closed yet
    assert days is not None and mon is not None


def test_news_blackout_on_fomc_days():                                  # CRT-R66
    assert ctx.news_blocked(ns("2024-01-31 10:00"), CFG) == "FOMC"
    assert ctx.news_blocked(ns("2024-01-30 10:00"), CFG) == ""
    off = load_config("romeo", {"risk": {"news_events": []}})
    assert ctx.news_blocked(ns("2024-01-31 10:00"), off) == ""


def test_weekday_and_week_of_month():
    assert ctx.weekday(ns("2024-01-09 06:00")) == "Tue" and ctx.week_of_month(ns("2024-01-09 06:00")) == 2


# ---- SMT -----------------------------------------------------------------------
def test_candle_smt_direct_and_inverse():                               # DEF-18
    t1, t2 = ns("2024-01-09 01:00"), ns("2024-01-09 05:00")
    c1 = {"open_time": t1, "open": 1.10, "high": 1.11, "low": 1.09, "close": 1.10}
    c2 = {"open_time": t2, "open": 1.10, "high": 1.105, "low": 1.085, "close": 1.095}
    peer_hold = mk([(1.27, 1.28, 1.26, 1.27), (1.27, 1.275, 1.262, 1.27)], "2024-01-09 01:00", "4h", "4H")
    peer_take = mk([(1.27, 1.28, 1.26, 1.27), (1.27, 1.275, 1.255, 1.27)], "2024-01-09 01:00", "4h", "4H")
    assert candle_smt("bull", c1, c2, peer_hold, inverse=False) is True
    assert candle_smt("bull", c1, c2, peer_take, inverse=False) is False
    dxy_hold = mk([(104.0, 104.5, 103.5, 104.0), (104.0, 104.4, 103.8, 104.2)], "2024-01-09 01:00", "4h", "4H")
    assert candle_smt("bull", c1, c2, dxy_hold, inverse=True) is True    # EUR took its low, DXY not its high
    assert candle_smt("bull", c1, c2, None, inverse=False) is None


def test_peer_feed_never_returns_future_bars():
    df = random_walk("2024-01-07 17:00", "2024-01-10", seed=4)
    view = MultiTimeframeView(df, ["15m", "4H"])
    peer = PeerFeed("GBPUSD", view)
    now = int(df.index[500].value) + 60_000_000_000          # close of base bar 500
    snap = peer.snapshot_at(now)
    assert snap.i == 500 and snap.now_ns <= now
    assert peer.snapshot_at(int(df.index[500].value) + 30_000_000_000).i == 499
    assert np.all(snap.closed_times("4H")[1] <= now)
