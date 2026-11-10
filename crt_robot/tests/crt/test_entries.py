"""Entry models (group F) and their stops (group G) on hand-made LTF bars."""

import pytest

from crt_robot.crt import context as ctx
from crt_robot.crt import entries
from crt_robot.crt.config import load_config
from crt_robot.tests.crt.helpers import mk, ns

CFG = load_config("romeo", ["entry.require_thick=false"])
THICK = load_config("romeo")

# 15m bars from 05:00 (C2 05:00-09:00, C3 from 09:00). CRT low = 1.0905.
LOW = 1.0905
C2_OPEN, C2_CLOSE = ns("2024-01-09 05:00"), ns("2024-01-09 09:00")


def _ltf(rows, start="2024-01-09 05:00"):
    pre = [(1.0920, 1.0923, 1.0917, 1.0920)] * 20          # history before C2 (ATR)
    return mk(pre + rows, "2024-01-09 00:00", "15min", "15m") if start == "2024-01-09 05:00" else \
        mk(rows, start, "15min", "15m")


def _flat(n, p=1.0918):
    return [(p, p + 0.0002, p - 0.0002, p)] * n


def test_model1_bull_close_above_the_model_candle_wick_in_c3():          # CRT-R39 / DEF-08
    rows = _flat(16) + [                       # C2 05:00-09:00: 16 flat bars (no sweep)
        (1.0918, 1.0919, 1.0900, 1.0902),      # 09:00 C3: thick down-close stab below the CRT low
        (1.0902, 1.0915, 1.0901, 1.0914),      # 09:15 close below M.high 1.0919: no trigger
        (1.0914, 1.0925, 1.0912, 1.0922),      # 09:30 close above M.high -> trigger
    ]
    b = _ltf(rows)
    r = entries.model1(b, "bull", LOW, C2_OPEN, C2_CLOSE, int(b.close_time[-1]), CFG, 0.0)
    assert r.status == "signal" and r.signal.kind == "model1" and r.signal.order == "market"
    assert r.signal.price == pytest.approx(1.0922) and r.signal.stop == pytest.approx(1.0900)
    assert r.signal.trigger_ns == int(b.close_time[-1])


def test_model1_wick_vs_body_reference():                                 # C-07
    rows = _flat(16) + [(1.0918, 1.0930, 1.0900, 1.0902), (1.0902, 1.0921, 1.0901, 1.0920)]
    b = _ltf(rows)
    now = int(b.close_time[-1])
    wick = entries.model1(b, "bull", LOW, C2_OPEN, C2_CLOSE, now, CFG, 0.0)
    assert wick.signal is None and wick.status == "waiting"          # 1.0920 < wick high 1.0930
    body = load_config("romeo", ["entry.require_thick=false", "entry.model1_trigger_ref=body"])
    r = entries.model1(b, "bull", LOW, C2_OPEN, C2_CLOSE, now, body, 0.0)
    assert r.signal is not None and r.info["ref"] == pytest.approx(1.0918)   # body top = the open


def test_model1_bear_is_the_mirror():
    hi = 1.0950
    rows = _flat(16, 1.0940) + [(1.0940, 1.0960, 1.0939, 1.0958),   # thick up-close stab above the CRT high
                                 (1.0958, 1.0959, 1.0930, 1.0932)]   # close below M.low 1.0939 -> trigger
    b = _ltf(rows)
    r = entries.model1(b, "bear", hi, C2_OPEN, C2_CLOSE, int(b.close_time[-1]), CFG, 0.0)
    assert r.signal is not None and r.signal.stop == pytest.approx(1.0960) and r.signal.price == pytest.approx(1.0932)


def test_model1_needs_a_thick_candle():                                   # DEF-09
    rows = _flat(16) + [(1.0910, 1.0925, 1.0900, 1.0908),     # stab, but body/range = 0.08
                        (1.0908, 1.0930, 1.0907, 1.0928)]
    b = _ltf(rows)
    r = entries.model1(b, "bull", LOW, C2_OPEN, C2_CLOSE, int(b.close_time[-1]), THICK, 0.0)
    assert r.signal is None and "thick" in r.detail


def test_model1_trigger_inside_c2_retests_or_skips():                     # CRT-R30, model1_c2_trigger
    rows = [(1.0918, 1.0919, 1.0900, 1.0902), (1.0902, 1.0925, 1.0901, 1.0922)] + _flat(14, 1.0925) + \
           [(1.0925, 1.0926, 1.0923, 1.0924)]                 # C3 first bar
    b = _ltf(rows)
    now = int(b.close_time[-1])
    r = entries.model1(b, "bull", LOW, C2_OPEN, C2_CLOSE, now, CFG, 0.0)
    assert r.signal.kind == "model1_retest" and r.signal.order == "limit" and r.signal.price == pytest.approx(1.0919)
    skip = load_config("romeo", ["entry.require_thick=false", "crt.model1_c2_trigger=skip"])
    assert entries.model1(b, "bull", LOW, C2_OPEN, C2_CLOSE, now, skip, 0.0).status == "fail"
    early = entries.model1(b, "bull", LOW, C2_OPEN, C2_CLOSE, C2_OPEN + 30 * 60 * 10**9, CFG, 0.0)
    assert early.signal is None


def _mss_path():
    # L1 swing low, H swing high (the high that broke the low), L2 < L1 sweep below the CRT low,
    # close above H (true MSS), leg one up, then a retrace
    return [(1.0930, 1.0932, 1.0925, 1.0927), (1.0927, 1.0928, 1.0912, 1.0914),   # L1 = 1.0912
            (1.0914, 1.0921, 1.0913, 1.0920), (1.0920, 1.0926, 1.0919, 1.0925),
            (1.0925, 1.0930, 1.0922, 1.0923),                                      # H = 1.0930
            (1.0923, 1.0924, 1.0915, 1.0916), (1.0916, 1.0917, 1.0898, 1.0900),   # L2 = 1.0898
            (1.0900, 1.0912, 1.0899, 1.0910), (1.0910, 1.0922, 1.0909, 1.0921),
            (1.0921, 1.0934, 1.0920, 1.0933),                                      # close above H: MSS
            (1.0933, 1.0950, 1.0932, 1.0948), (1.0948, 1.0952, 1.0944, 1.0946),   # leg one to 1.0952
            (1.0946, 1.0947, 1.0936, 1.0938)]                                      # retrace starts


def test_true_mss_with_ote_zone():                                         # CRT-R40/R41, DEF-10/12
    b = mk([(1.0930, 1.0935, 1.0925, 1.0930)] * 20 + _mss_path(), "2024-01-09 00:00", "15min", "15m")
    c2_open = int(b.open_time[20])
    r = entries.mss_ote(b, "bull", LOW, c2_open, CFG, 0.0)
    assert r.status == "signal" and r.signal.kind == "mss" and r.signal.order == "limit"
    span = 1.0952 - 1.0898
    assert r.signal.price == pytest.approx(1.0952 - 0.5 * span)          # shallow edge of 0.50-0.79
    assert r.signal.stop == pytest.approx(1.0898)                          # TS extreme (CRT-R50)
    assert r.info["h_broke_low"] == pytest.approx(1.0930)
    alt = load_config("romeo", ["entry.ote_zone=[0.62, 0.79]"])
    assert entries.mss_ote(b, "bull", LOW, c2_open, alt, 0.0).signal.price == pytest.approx(1.0952 - 0.62 * span)
    full = load_config("romeo", ["entry.mss_entry_zone=full_retrace"])
    assert entries.mss_ote(b, "bull", LOW, c2_open, full, 0.0).signal.price == pytest.approx(1.0930)
    ote = load_config("romeo", ["stop.ote_stop=fib_079"])
    o = entries.mss_ote(b, "bull", LOW, c2_open, ote, 0.0, kind="ote")
    assert o.signal.stop == pytest.approx(1.0952 - 0.79 * span)


def test_mss_needs_the_sweep_to_reach_the_crt_extreme():                  # CRT-R20
    b = mk([(1.0930, 1.0935, 1.0925, 1.0930)] * 20 + _mss_path(), "2024-01-09 00:00", "15min", "15m")
    r = entries.mss_ote(b, "bull", 1.0890, int(b.open_time[20]), CFG, 0.0)     # L2 1.0898 > 1.0890
    assert r.signal is None


def test_mss_zone_blown_through_is_a_fail():
    path = _mss_path() + [(1.0938, 1.0939, 1.0905, 1.0907)]              # below the 0.79 level
    b = mk([(1.0930, 1.0935, 1.0925, 1.0930)] * 20 + path, "2024-01-09 00:00", "15min", "15m")
    assert entries.mss_ote(b, "bull", LOW, int(b.open_time[20]), CFG, 0.0).status == "fail"


SHAM = load_config("sham")


def _kt(t):
    return ctx.in_key_time(t, SHAM)


def test_sham_ob_after_a_purge_limit_at_the_near_edge():                  # CRT-R43, DEF-15
    # 4H C1 05:00-09:00 closed; 15m from 09:00 (NY killzone): purge of 1.0905, then engulf
    rows = [(1.0915, 1.0916, 1.0908, 1.0910), (1.0910, 1.0911, 1.0899, 1.0901),   # down-close purge bars
            (1.0901, 1.0925, 1.0900, 1.0923)]                                      # engulf above the bodies
    b = mk([(1.0915, 1.0918, 1.0912, 1.0915)] * 20 + rows, "2024-01-09 04:00", "15min", "15m")
    purge_from = ns("2024-01-09 09:00")
    r = entries.sham_ob(b, "bull", LOW, purge_from, SHAM, 0.0, _kt)
    assert r.status == "signal" and r.signal.kind == "ob"
    assert r.signal.price == pytest.approx(1.0916) and r.signal.stop == pytest.approx(1.0899)
    mid = load_config("sham", ["entry.ob_entry_edge=mid"])
    assert entries.sham_ob(b, "bull", LOW, purge_from, mid, 0.0, _kt).signal.price == pytest.approx((1.0916 + 1.0899) / 2)
    eq = entries.sham_ob(b, "bull", LOW, purge_from, SHAM, 0.0, _kt, dr_eq=1.0910)
    assert eq.signal.price == pytest.approx(1.0910)                                # CRT-R47
    prem = entries.sham_ob(b, "bull", LOW, purge_from, SHAM, 0.0, _kt, dr_eq=1.0890)
    assert prem.status == "fail"


def test_sham_ob_outside_key_time_invalidates():                          # CRT-R33
    rows = [(1.0915, 1.0916, 1.0908, 1.0910), (1.0910, 1.0911, 1.0899, 1.0901), (1.0901, 1.0925, 1.0900, 1.0923)]
    b = mk([(1.0915, 1.0918, 1.0912, 1.0915)] * 20 + rows, "2024-01-09 07:45", "15min", "15m")  # engulf 13:15
    r = entries.sham_ob(b, "bull", LOW, ns("2024-01-09 12:00"), SHAM, 0.0, _kt)
    assert r.status == "fail" and "key time" in r.detail


def test_sham_ob_ignores_purges_before_the_crt_candle_closed():           # CRT-R27
    rows = [(1.0915, 1.0916, 1.0908, 1.0910), (1.0910, 1.0911, 1.0899, 1.0901), (1.0901, 1.0925, 1.0900, 1.0923)]
    b = mk([(1.0915, 1.0918, 1.0912, 1.0915)] * 20 + rows, "2024-01-09 04:00", "15min", "15m")
    r = entries.sham_ob(b, "bull", LOW, ns("2024-01-09 09:40"), SHAM, 0.0, _kt)
    assert r.signal is None


def test_ltf_crt_inside_htf_confirmation():                               # G-20
    rows = [(1.0915, 1.0920, 1.0910, 1.0912), (1.0912, 1.0914, 1.0900, 1.0913)] + _flat(14)
    b = _ltf(rows)
    assert entries.ltf_crt_inside(b, "bull", LOW, C2_OPEN, C2_CLOSE)
    assert not entries.ltf_crt_inside(b, "bull", 1.0895, C2_OPEN, C2_CLOSE)
