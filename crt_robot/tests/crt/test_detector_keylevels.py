"""CRT formation (group D) and key levels (group C), including the four
idealised CRT shapes of research/notes/crt/books/crt-keylevels.md p.11:
bullish at a rejection block (RB) and an old low purged (OLP), bearish at an
old high purged (OHP) and a fair value gap (FVG)."""

import pytest

from crt_robot.crt import keylevels
from crt_robot.crt.config import load_config
from crt_robot.crt.detector import c3_progress, find_crt, mother_index
from crt_robot.tests.crt.helpers import FakeMD, mk, ns

CFG = load_config("romeo")


# ---------------------------------------------------------------------------
# group D
# ---------------------------------------------------------------------------

def _h4(rows, start="2024-01-09 01:00"):
    return mk(rows, start, "4h", "4H")


def test_c2_turtle_soup_of_the_low_is_a_bull_crt():          # DEF-05, CRT-R25
    b = _h4([(1.10, 1.105, 1.095, 1.098), (1.098, 1.100, 1.093, 1.099)])
    s = find_crt(b, 3)
    assert s.outcome == "ts_low" and s.direction == "bull" and s.close_inside and s.c1 == 0


def test_c2_close_beyond_is_a_breakout_not_inside():           # CRT-R25 "let it go"
    b = _h4([(1.10, 1.105, 1.095, 1.098), (1.098, 1.100, 1.090, 1.092)])
    s = find_crt(b, 3)
    assert s.outcome == "breakout_down" and not s.close_inside


def test_inside_c2_gives_no_direction_and_mother_candle_is_kept():   # CRT-R26 / DEF-27
    b = _h4([(1.10, 1.110, 1.090, 1.100), (1.10, 1.105, 1.095, 1.101), (1.10, 1.104, 1.096, 1.099),
             (1.099, 1.112, 1.097, 1.105)])
    assert find_crt(b, 3, k=1).outcome == "inside"
    j, inside = mother_index(b, 3, 3)
    assert (j, inside) == (0, 2)
    s = find_crt(b, 3)
    assert s.c1 == 0 and s.inside_bars == 2 and s.outcome == "ts_high" and s.direction == "bear"


def test_max_inside_bars_limits_the_mother_rule():
    rows = [(1.10, 1.120, 1.080, 1.100)] + [(1.10, 1.105, 1.095, 1.10)] * 4 + [(1.10, 1.106, 1.094, 1.10)]
    b = _h4(rows)
    j, inside = mother_index(b, 5, 3)
    assert inside <= 3 and j >= 1


def test_outside_c2_is_classified_by_the_nearest_side():       # DEF-05 edge case
    b = _h4([(1.10, 1.105, 1.095, 1.100), (1.10, 1.106, 1.094, 1.104)])
    s = find_crt(b, 3)
    assert s.outside and s.outcome == "ts_high"


def test_c3_targets_50_then_opposite_extreme():                  # CRT-R53 / R59
    assert c3_progress("bull", 1.10, 1.09, 1.0960, 1.089) == {"hit_50": True, "hit_opposite": False}
    assert c3_progress("bull", 1.10, 1.09, 1.1001, 1.089)["hit_opposite"]
    assert c3_progress("bear", 1.10, 1.09, 1.10, 1.0949) == {"hit_50": True, "hit_opposite": False}


# ---------------------------------------------------------------------------
# key levels: fixtures
# ---------------------------------------------------------------------------

DAYS = "2023-12-30 00:00"          # D bars 30 Dec .. 5 Jan (two padding days first)
PAD_LOW = [(1.1000, 1.1040, 1.0990, 1.1010), (1.1010, 1.1045, 1.0995, 1.1000)]
PAD_HIGH = [(1.1000, 1.1010, 1.0950, 1.0990), (1.0990, 1.1005, 1.0945, 1.1000)]
LOW_DAYS = PAD_LOW + [(1.1000, 1.1050, 1.0980, 1.1020), (1.1020, 1.1040, 1.0960, 1.0990),
            (1.0990, 1.1000, 1.0900, 1.0985),          # swing low with a long lower wick
            (1.0985, 1.1030, 1.0970, 1.1020), (1.1020, 1.1060, 1.1000, 1.1050)]
HIGH_DAYS = PAD_HIGH + [(1.1000, 1.1020, 1.0950, 1.0980), (1.0980, 1.1040, 1.0960, 1.1010),
             (1.1010, 1.1100, 1.1000, 1.1015),         # swing high with a long upper wick
             (1.1015, 1.1030, 1.0970, 1.0990), (1.0990, 1.1000, 1.0940, 1.0950)]
FVG_DAYS = PAD_HIGH + [(1.1060, 1.1090, 1.1050, 1.1070), (1.1070, 1.1120, 1.1080 - 0.0010, 1.1085),
            (1.1100, 1.1120, 1.1080, 1.1085), (1.1085, 1.1088, 1.0990, 1.1000),
            (1.1000, 1.1040, 1.0980, 1.1010)]          # bearish FVG [1.1040, 1.1080] (bars 2..4)


def _setup_bars(day_rows, h4_rows):
    d = mk(day_rows, DAYS, "1D", "D")
    h4 = mk(h4_rows, "2024-01-06 01:00", "4h", "4H")
    return d, h4


def _select(direction, day_rows, h4_rows, types):
    cfg = load_config("romeo", {"key_level": {"kl_types": types}, "timeframes": {"use_kl_tf_secondary": False}})
    d, h4 = _setup_bars(day_rows, h4_rows)
    md = FakeMD({"D": d, "4H": h4}, int(h4.close_time[-1]))
    c2_open = int(h4.open_time[-1])
    cands = keylevels.candidates(md, cfg, "4H", direction, c2_open, "4H")
    c1, c2 = h4.bar(len(h4) - 2), h4.bar(len(h4) - 1)
    swept = c1["low"] if direction == "bull" else c1["high"]
    purge = c2["low"] if direction == "bull" else c2["high"]
    best, scored = keylevels.score_and_select(cands, direction=direction, swept_extreme=swept, purge_extreme=purge,
                                              atr_htf=float("nan"), atr_ltf=float("nan"), eq=None,
                                              kl_bars_low=None, kl_bars_high=None, cfg=cfg)
    return best, cands, find_crt(h4, 3)


# C1 range 1.0990-1.1030 for the bull cases, 1.0960-1.1000 / 1.0990-1.1030 for the bear cases
BULL_C1 = (1.1010, 1.1030, 1.0990, 1.1000)
BEAR_C1 = (1.0980, 1.1000, 1.0960, 1.0990)


def test_shape_bull_crt_at_rejection_block():
    c2 = (1.1000, 1.1010, 1.0960, 1.1005)           # wick into the RB zone [1.0900, 1.0985], no OLP
    best, cands, shape = _select("bull", LOW_DAYS, [BULL_C1, c2], ["rb"])
    assert shape.direction == "bull" and shape.close_inside
    assert best is not None and best.kind == "rb" and best.bottom == pytest.approx(1.0900)
    assert best.top == pytest.approx(1.0985)


def test_shape_bull_crt_at_old_low_purged():
    c2 = (1.1000, 1.1010, 1.0890, 1.1005)           # purges the old low 1.0900
    best, _, shape = _select("bull", LOW_DAYS, [BULL_C1, c2], ["old_low"])
    assert shape.direction == "bull" and best.kind == "old_low" and best.price == pytest.approx(1.0900)
    c2_short = (1.1000, 1.1010, 1.0960, 1.1005)     # stays above the old low -> not reached
    best2, cands2, _ = _select("bull", LOW_DAYS, [BULL_C1, c2_short], ["old_low"])
    assert cands2 and best2 is None


def test_shape_bear_crt_at_old_high_purged():
    c2 = (1.0990, 1.1110, 1.0985, 1.0995)           # purges the old high 1.1100
    best, _, shape = _select("bear", HIGH_DAYS, [BEAR_C1, c2], ["old_high"])
    assert shape.direction == "bear" and best.kind == "old_high" and best.price == pytest.approx(1.1100)


def test_shape_bear_crt_at_fair_value_gap():
    c1 = (1.1010, 1.1030, 1.0990, 1.1000)
    c2 = (1.1000, 1.1050, 1.0995, 1.1010)           # wick into the bearish FVG [1.1040, 1.1080]
    best, _, shape = _select("bear", FVG_DAYS, [c1, c2], ["fvg"])
    assert shape.direction == "bear" and best.kind == "fvg"
    assert best.bottom == pytest.approx(1.1040) and best.top == pytest.approx(1.1080)


def test_a_level_swept_before_c2_is_not_a_candidate():          # unswept (DEF-07)
    c1 = (1.1000, 1.1010, 1.0895, 1.1000)           # C1 already purged the old low
    c2 = (1.1000, 1.1010, 1.0880, 1.1005)
    best, cands, _ = _select("bull", LOW_DAYS, [c1, c2], ["old_low"])
    assert not [c for c in cands if c.kind == "old_low"] and best is None


def test_levels_formed_after_c2_opened_are_not_used():          # look-ahead: known_ns <= C2 open
    cfg = load_config("romeo", {"key_level": {"kl_types": ["prev_period_hl"]}})
    d = mk(LOW_DAYS, DAYS, "1D", "D")
    h4 = mk([BULL_C1, (1.1, 1.101, 1.0890, 1.1005)], "2024-01-06 01:00", "4h", "4H")
    md = FakeMD({"D": d, "4H": h4, "W": d}, int(h4.close_time[-1]))
    early = keylevels.candidates(md, cfg, "4H", "bull", ns("2024-01-03 12:00"), "4H")
    assert all(c.known_ns <= ns("2024-01-03 12:00") for c in early)


def test_distance_limit_and_nearest_selection():               # kl_max_dist_atr, kl_select
    cfg = load_config("romeo", ["key_level.kl_select=nearest"])
    from crt_robot.crt.setup import KeyLevel
    far = KeyLevel("old_low", "D", "low", 1.0800, 1.0800, 0)
    near = KeyLevel("fvg", "D", "low", 1.0985, 1.0970, 0)
    best, scored = keylevels.score_and_select([far, near], direction="bull", swept_extreme=1.0990,
                                              purge_extreme=1.0790, atr_htf=0.0020, atr_ltf=0.0005, eq=None,
                                              kl_bars_low=None, kl_bars_high=None, cfg=cfg)
    assert [s.kind for s in scored] == ["fvg"] and best.kind == "fvg"     # 1.0800 is > 1.5 ATR away


def test_score_prefers_bos_origin_and_correct_half():          # G-01 proxy + v0.2 BOS bonus
    from crt_robot.crt.setup import KeyLevel
    a = KeyLevel("old_low", "D", "low", 1.0985, 1.0985, 0)
    b = KeyLevel("bos_origin_hl", "D", "low", 1.0980, 1.0980, 0, is_bos_origin=True)
    best, scored = keylevels.score_and_select([a, b], direction="bull", swept_extreme=1.0990, purge_extreme=1.0975,
                                              atr_htf=0.0030, atr_ltf=0.0005, eq=1.1000,
                                              kl_bars_low=None, kl_bars_high=None, cfg=CFG)
    assert best.kind == "bos_origin_hl" and best.score > [s for s in scored if s.kind == "old_low"][0].score


def test_bos_origin_levels_come_from_structure_breaks():
    cfg = load_config("romeo", {"key_level": {"kl_types": ["bos_origin_hl"]}})
    rows = [(1.10, 1.102, 1.098, 1.10), (1.10, 1.104, 1.099, 1.103), (1.103, 1.106, 1.101, 1.105),  # swing high
            (1.105, 1.105, 1.095, 1.096), (1.096, 1.098, 1.093, 1.094),                             # origin low
            (1.094, 1.099, 1.094, 1.098), (1.098, 1.110, 1.097, 1.109), (1.109, 1.112, 1.105, 1.11)]
    d = mk(rows, DAYS, "1D", "D")
    out = keylevels.raw_candidates(d, cfg, True)
    lows = [c for c in out if c.side == "low"]
    assert lows and lows[0].is_bos_origin and lows[0].price == pytest.approx(1.093)
