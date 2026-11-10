"""Integration tests on synthetic data: the three strategy modes inside the
Phase 1 engine, the condition log, and a look-ahead audit for each mode.

The scripted path (scenarios.bull_4h_crt_at_daily_old_low) is a DRAWING made
from straight lines, not market data; only behaviour is asserted, never
performance.
"""

from collections import Counter

import pytest

from crt_robot.backtest.audit import lookahead_audit
from crt_robot.backtest.engine import Backtester, EngineConfig
from crt_robot.crt.config import load_config
from crt_robot.crt.smt import PeerFeed
from crt_robot.crt.strategy import CRTStrategy, view_timeframes
from crt_robot.data.instruments import get_instrument
from crt_robot.data.mtf import MultiTimeframeView
from crt_robot.data.synthetic import random_walk
from crt_robot.tests.crt.scenarios import bull_4h_crt_at_daily_old_low

EU = get_instrument("EURUSD")
SHAM_OVR = ["invalidation.sham_invalid_atr=5"]      # straight-line drawing: tiny 15m ATR
RELAX = ["bias.bias_gate=score", "bias.market_profile_mode=none", "dealing_range.require_correct_half=false",
         "crt.min_confirmations=0", "bias.romeo_sweep_days=[all]", "bias.skip_if_monday_expansion=false"]


@pytest.fixture(scope="module")
def scenario():
    return bull_4h_crt_at_daily_old_low()


def _run(df, mode, over=(), peers=None):
    cfg = load_config(mode, list(over))
    st = CRTStrategy(cfg, "EURUSD", peers=peers)
    res = Backtester(df, EU, view_timeframes(cfg), config=EngineConfig(max_trades_per_day=1)).run(st, log=False)
    return st, res


def _setup(st, stamp):
    return next(s for s in st.setups if stamp in s.id)


@pytest.fixture(scope="module")
def romeo_run(scenario):
    return _run(scenario, "romeo")


def test_romeo_takes_the_scripted_bull_crt(romeo_run):
    st, res = romeo_run
    s = _setup(st, "4H-202401090100-bull")
    passed = {c.name for c in s.checks if c.status == "pass"}
    assert {"c2_close_inside", "htf_bias", "market_profile", "correct_half", "key_level_reached",
            "sweep_weekday_ok", "min_confirmations", "entry_vs_c3_open", "order_sent"} <= passed
    assert not s.failed
    assert s.key_level.kind == "old_low" and s.key_level.tf == "D_NY"
    assert s.entry_kind == "model1_retest" and s.state == "done"
    assert s.entry_price < s.c3_open                                  # CRT-R44
    t = res.trades[res.trades.tag == s.id].iloc[0]
    assert t.reason == "target" and bool(t.tp1_hit)                   # CRT-R53: 50% partial then C1 high
    assert t.target == pytest.approx(s.crt_high) and t.tp1 == pytest.approx(s.crt_50)
    assert t.stop == pytest.approx(s.stop) and s.stop < s.crt_low     # CRT-R49: below the model candle


def test_every_rejection_has_a_reason_and_a_failed_check(romeo_run):
    st, _ = romeo_run
    rej = [s for s in st.setups if s.state in ("rejected", "invalidated")]
    assert rej
    for s in rej:
        assert s.invalid_reason, s.id
        assert s.failed, s.id
    nxt = _setup(st, "4H-202401090500-bear")                          # the C2 itself as C1, next candle broke out
    assert nxt.invalid_reason == "breakout_c2" and nxt.failed[0].rule == "CRT-R29"


def test_breakout_c2_is_dropped_in_romeo_but_scored_when_not_required():
    df = bull_4h_crt_at_daily_old_low(close_back_inside=False)
    st, _ = _run(df, "romeo")
    s = _setup(st, "4H-202401090100-bull")
    assert s.state == "rejected" and s.invalid_reason == "breakout_c2"
    st2, _ = _run(df, "romeo", ["crt.require_close_inside={W: true, D: true, 4H: false}"])
    s2 = _setup(st2, "4H-202401090100-bull")
    c = s2.check("c2_close_inside")
    assert c.status == "score" and c.value == 0 and c.rule == "C-04"


def test_hybrid_takes_the_scripted_crt_with_sham_timing(scenario):
    st, res = _run(scenario, "hybrid")
    s = _setup(st, "4H-202401090100-bull")
    assert s.check("timed_purge").status == "pass" and s.state == "done"
    assert len(res.trades) >= 1


def test_sham_frames_the_01_candle_and_enters_on_the_15m_ob(scenario):
    st, res = _run(scenario, "sham", SHAM_OVR)
    s = _setup(st, "4H-202401090100-bull")
    assert s.purpose == "framing" and s.check("framing_open").status == "pass"
    assert s.check("daily_bias").status == "pass" and s.check("timed_purge").status == "pass"
    assert s.entry_kind == "ob" and s.state in ("entered", "done")
    t = res.trades[res.trades.tag == s.id].iloc[0]
    risk = abs(t.entry - t.stop)
    assert (t.target - t.entry) == pytest.approx(3.0 * risk, rel=0.02)    # CRT-R55 3R


def test_a_strict_option_rejects_with_its_rule(scenario):
    st, _ = _run(scenario, "romeo", ["bias.romeo_sweep_days=[Mon]"])
    s = _setup(st, "4H-202401090100-bull")
    assert s.invalid_reason == "weekday" and s.failed[-1].rule == "CRT-R35"
    st, _ = _run(scenario, "romeo", ["crt.min_confirmations=4"])
    assert _setup(st, "4H-202401090100-bull").invalid_reason == "too_few_confirmations"


def test_news_blackout_blocks_entries(scenario):
    import yaml
    from pathlib import Path
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "cal.yaml"
        p.write_text(yaml.safe_dump({"events": {"FOMC": ["2024-01-09"]}}))
        st, res = _run(scenario, "romeo", [f"risk.news_calendar={p}"])
    s = _setup(st, "4H-202401090100-bull")
    assert s.invalid_reason == "news_blackout" and s.check("no_news_blackout").status == "fail"
    assert res.trades.empty or not (res.trades.tag == s.id).any()


def test_smt_with_a_peer_is_scored(scenario):
    """DEF-18 candle SMT: our C2 takes C1's low, the peer's C2 does not."""
    import pandas as pd
    peer_df = scenario.copy()
    ny = peer_df.index.tz_convert("America/New_York")
    c2 = (ny >= pd.Timestamp("2024-01-09 05:00", tz="America/New_York")) & \
         (ny < pd.Timestamp("2024-01-09 09:00", tz="America/New_York"))
    floor = 1.0907                                   # above the C1 low 1.0905: the peer holds its low
    for col in ("open", "high", "low", "close"):
        peer_df.loc[c2, col] = peer_df.loc[c2, col].clip(lower=floor)
    peer = PeerFeed("GBPUSD", MultiTimeframeView(peer_df, list(view_timeframes(load_config("romeo")))))
    st, _ = _run(scenario, "romeo", (), peers=[peer])
    smt = _setup(st, "4H-202401090100-bull").check("smt")
    assert smt.status == "score" and smt.value == 1
    st2, _ = _run(scenario, "romeo", (), peers=[PeerFeed("GBPUSD", MultiTimeframeView(
        scenario, list(view_timeframes(load_config("romeo")))))])
    assert _setup(st2, "4H-202401090100-bull").check("smt").value == 0     # same path: no divergence


def test_strategy_holds_no_price_data(romeo_run):
    from crt_robot.backtest.engine import check_strategy_holds_no_data
    st, _ = romeo_run
    check_strategy_holds_no_data(st)


# ---- look-ahead audit on each mode ------------------------------------------

@pytest.mark.parametrize("mode,over", [("romeo", []), ("sham", SHAM_OVR), ("hybrid", [])])
def test_lookahead_audit_on_the_scripted_crt(scenario, mode, over):
    cfg = load_config(mode, over)
    checks = lookahead_audit(lambda: CRTStrategy(cfg, "EURUSD"), scenario, EU, view_timeframes(cfg),
                             n_checks=3, seed=1)
    assert checks


@pytest.mark.parametrize("mode", ["romeo", "sham", "hybrid"])
def test_lookahead_audit_on_noise_with_relaxed_gates(mode):
    df = random_walk("2024-01-07 17:00", "2024-02-03", sigma=0.00015, seed=5)
    sham_relax = SHAM_OVR + ["dealing_range.rebalance_required=false", "key_level.kl_max_dist_atr=5"]
    cfg = load_config(mode, RELAX + (sham_relax if mode == "sham" else []))
    full = Backtester(df, EU, view_timeframes(cfg)).run(CRTStrategy(cfg, "EURUSD"), log=False)
    checks = lookahead_audit(lambda: CRTStrategy(cfg, "EURUSD"), df, EU, view_timeframes(cfg), n_checks=3, seed=2)
    assert checks and len(full.decisions) >= 1      # the audit had decisions to compare


def test_counts_by_state_are_consistent(romeo_run):
    st, res = romeo_run
    states = Counter(s.state for s in st.setups)
    assert states["done"] + states["entered"] == len(res.trades)
