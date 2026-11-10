"""Context layers (rulebook groups B, E and parts of C/D):

* HTF bias: close-vs-wick rule (CRT-R06), Sham D1 structure x close matrix
  (CRT-R08), structure label (CRT-R15).
* Market profile: five phases + the outcome table (G-04, books p.87/254),
  plus the ``sham4`` and ``romeo_swings`` proxies.
* Dealing range, equilibrium, premium/discount (DEF-19/20, CRT-R16/R21, G-09).
* Time: killzones, macros, purge hours, refined key times, 1/5/9 rhythm,
  Asia block, turtle soup at the open of a new candle (G-23), weekday and
  Monday-expansion filters (CRT-R35, G-26), closing-hour tag (G-05).
* News blackout hook (CRT-R66) with an FOMC dates file.

All functions take closed bars only.
"""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from crt_robot.config import REPO_ROOT
from crt_robot.crt.bars import Bars, ny
from crt_robot.crt.config import StrategyConfig
from crt_robot.crt.setup import BEAR, BULL
from crt_robot.primitives.candles import atr
from crt_robot.primitives.dealing_range import DealingRange
from crt_robot.primitives.fvg import detect_fvgs
from crt_robot.primitives.structure import detect_structure
from crt_robot.primitives.swings import fractal_swings

WEEKDAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


# ---------------------------------------------------------------------------
# bias
# ---------------------------------------------------------------------------

def close_wick_bias(p: dict, q: dict) -> str:
    """CRT-R06. ``p`` = last closed candle, ``q`` = the one before it.
    Returns bull / bear / neutral (outside bar closed inside) / inside."""
    if p["close"] > q["high"]:
        return BULL
    if p["close"] < q["low"]:
        return BEAR
    up = p["high"] > q["high"]
    down = p["low"] < q["low"]
    if up and not down:
        return BEAR
    if down and not up:
        return BULL
    if up and down:
        return "neutral"
    return "inside"


def close_beyond(p: dict, q: dict) -> bool:
    return p["close"] > q["high"] or p["close"] < q["low"]


def structure_label(b: Bars, swing_n: int) -> str:
    """CRT-R15 proxy: ``bull`` if the last known swing high was broken (close)
    and the last swept swing low closed back inside (TS); ``bear`` mirror;
    else the direction of the latest break, else ``range``."""
    if len(b) < 2 * swing_n + 3:
        return "range"
    df = b.df()
    st = detect_structure(df, swing_n)
    if st.empty:
        return "range"
    last = st.iloc[-1]
    return BULL if last.kind.endswith("bull") else BEAR


def sham_bias(d: Bars, swing_n: int) -> tuple[str, str, str]:
    """CRT-R08 matrix. Returns (bias, structure, close class)."""
    if len(d) < 3:
        return "neutral", "range", "inside"
    s = structure_label(d, swing_n)
    p, q = d.bar(len(d) - 1), d.bar(len(d) - 2)
    c = close_wick_bias(p, q)
    if close_beyond(p, q):
        return c, s, "close_beyond"
    if c in (BULL, BEAR) and s in (BULL, BEAR):
        # wick classes: retracement expected / retracement complete
        return c, s, f"wick_{c}"
    if c in (BULL, BEAR) and s == "range":
        return c, s, f"wick_{c}"
    return "neutral", s, c


# ---------------------------------------------------------------------------
# market profile (G-04)
# ---------------------------------------------------------------------------

OUTCOME_WITH_KL = {          # books/romeo-book p.87 [S]: last profile + key level -> next outcome
    "expansion": "reversal",
    "range": "expansion",
    "reversal": "range",
    "retracement": "expansion",
    "manipulation": "expansion",
}
OUTCOME_NO_KL = {
    "expansion": "retracement",
    "range": "manipulation",
    "reversal": "retracement",
    "retracement": "retracement",  # not in the table: PROPOSED (avoid)
    "manipulation": "expansion",
}


def five_phase(b: Bars, swing_n: int) -> str:
    """Phase of the last closed bar of ``b`` (proxy on closes, G-04 v0.2):
    reversal = structure flip at this bar; expansion = close beyond the prior
    bar's range; manipulation = sweep one side and close back inside;
    retracement = close against the last expansion; range = otherwise."""
    if len(b) < 3:
        return "range"
    p, q = b.bar(len(b) - 1), b.bar(len(b) - 2)
    if len(b) >= 2 * swing_n + 4:
        now = structure_label(b, swing_n)
        before = structure_label(b.slice(slice(0, len(b) - 1)), swing_n)
        if now in (BULL, BEAR) and before in (BULL, BEAR) and now != before:
            return "reversal"
    if close_beyond(p, q):
        return "expansion"
    up, down = p["high"] > q["high"], p["low"] < q["low"]
    if up != down:
        return "manipulation"
    # last expansion direction
    for k in range(len(b) - 2, 0, -1):
        pk, qk = b.bar(k), b.bar(k - 1)
        if close_beyond(pk, qk):
            d = 1 if pk["close"] > qk["high"] else -1
            move = p["close"] - p["open"]
            if move * d < 0:
                return "retracement"
            break
    return "range"


def sham4(b: Bars, direction: str) -> str:
    if len(b) < 2:
        return "consolidation"
    p, q = b.bar(len(b) - 1), b.bar(len(b) - 2)
    if close_beyond(p, q):
        up = p["close"] > q["high"]
        return "expansion" if (up and direction == BULL) or (not up and direction == BEAR) else "retracement"
    if p["high"] > q["high"] or p["low"] < q["low"]:
        return "manipulation"
    return "consolidation"


def romeo_swings_profile(b: Bars, swing_n: int, k: int) -> str:
    """G-04 Romeo proxy: bear profile if the last k swing highs were swept and
    closed back (TS) and the last k swing lows were broken by closes."""
    if len(b) < 2 * swing_n + 3:
        return "none"
    df = b.df()
    sw = fractal_swings(df, swing_n)
    c = df["close"].to_numpy()
    h, l = df["high"].to_numpy(), df["low"].to_numpy()

    def fate(s) -> str:
        after = slice(int(s.known_at) + 1, len(df))
        if s.kind == "high":
            if (c[after] > s.price).any():
                return "broken"
            return "ts" if (h[after] > s.price).any() else "open"
        if (c[after] < s.price).any():
            return "broken"
        return "ts" if (l[after] < s.price).any() else "open"

    highs = [fate(s) for s in sw[sw.kind == "high"].tail(k).itertuples()]
    lows = [fate(s) for s in sw[sw.kind == "low"].tail(k).itertuples()]
    if len(highs) == k and len(lows) == k:
        if all(x == "ts" for x in highs) and all(x == "broken" for x in lows):
            return BEAR
        if all(x == "broken" for x in highs) and all(x == "ts" for x in lows):
            return BULL
    return "none"


# ---------------------------------------------------------------------------
# dealing range (G-09)
# ---------------------------------------------------------------------------

def dealing_range(b: Bars, cfg: StrategyConfig) -> DealingRange | None:
    """Latest expansion swing (swing high <-> swing low) of size
    >= ``dr_min_atr x ATR``, optionally containing an FVG (displacement,
    ICT-K) and optionally after both a swing high and a swing low were taken
    (books p.96: origin swing swept a prior swing on its side, and the end
    swing swept a prior swing on its side)."""
    d = cfg.dealing_range
    n = cfg.general.swing_n
    if len(b) < 2 * n + 5:
        return None
    df = b.df()
    sw = fractal_swings(df, n)
    sw = sw[sw.known_at < len(df)]
    if len(sw) < 2:
        return None
    a = atr(df, min(cfg.general.atr_len, max(2, len(df) // 2)))
    fvgs = detect_fvgs(df) if d.dr_require_fvg else None
    rows = list(sw.sort_values("idx").itertuples())
    for j in range(len(rows) - 1, 0, -1):
        e = rows[j]
        # most recent opposite swing before e
        o = next((rows[i] for i in range(j - 1, -1, -1) if rows[i].kind != e.kind), None)
        if o is None:
            continue
        hi, lo = (e, o) if e.kind == "high" else (o, e)
        size = hi.price - lo.price
        av = a[min(int(e.idx), len(a) - 1)]
        if not np.isfinite(av) or size < d.dr_min_atr * av:
            continue
        s, t = sorted((int(o.idx), int(e.idx)))
        if fvgs is not None:
            leg = fvgs[(fvgs.a_idx >= s) & (fvgs.created_idx <= t)]
            want = "bull" if lo.idx < hi.idx else "bear"
            if not (leg.kind == want).any():
                continue
        if d.dr_require_sweep_both:
            prev_lo = [r.price for r in rows if r.kind == "low" and r.idx < lo.idx]
            prev_hi = [r.price for r in rows if r.kind == "high" and r.idx < hi.idx]
            if not prev_lo or not prev_hi or not (lo.price < prev_lo[-1] and hi.price > prev_hi[-1]):
                continue
        return DealingRange(float(hi.price), float(lo.price), int(hi.idx), int(lo.idx))
    return None


def rebalanced(dr: DealingRange, b: Bars, direction: str) -> bool:
    """CRT-R16: since the range formed, price traded back to EQ (bear: up to
    EQ before selling; bull: down to EQ before buying)."""
    end = max(dr.high_idx, dr.low_idx)
    seg = b.slice(slice(end + 1, len(b)))
    if len(seg) == 0:
        return False
    return bool(seg.high.max() >= dr.eq) if direction == BEAR else bool(seg.low.min() <= dr.eq)


# ---------------------------------------------------------------------------
# time
# ---------------------------------------------------------------------------

def _mins(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def in_window(minute: int, a: str, b: str) -> bool:
    x, y = _mins(a), _mins(b)
    return x <= minute < y if x < y else (minute >= x or minute < y)


def minute_of_day(ns: int) -> int:
    t = ny(ns)
    return t.hour * 60 + t.minute


ICT_MACROS = (("02:33", "03:00"), ("04:03", "04:30"), ("08:50", "09:10"), ("09:50", "10:10"),
              ("10:50", "11:10"), ("11:50", "12:10"), ("13:10", "13:40"), ("15:15", "15:45"))


def in_macro(ns: int, cfg: StrategyConfig) -> bool:
    m = minute_of_day(ns)
    if cfg.timing.macro_window == "ict":
        return any(in_window(m, a, b) for a, b in ICT_MACROS)
    return any(in_window(m, h, f"{(_mins(h) // 60 + 1) % 24:02d}:00") for h in cfg.timing.macros)


def killzone(ns: int, cfg: StrategyConfig) -> str:
    m = minute_of_day(ns)
    for name, (a, b) in cfg.timing.killzones.items():
        if in_window(m, a, b):
            return name
    return ""


def in_purge_hour(ns: int, cfg: StrategyConfig) -> bool:
    h = ny(ns).hour
    return any(h == int(x.split(":")[0]) for x in cfg.timing.purge_hours)


def in_refined_key_time(ns: int, cfg: StrategyConfig) -> bool:
    m = minute_of_day(ns)
    return any(in_window(m, a, b) for a, b in cfg.timing.refined_key_times)


def in_key_time(ns: int, cfg: StrategyConfig, purge: bool = False) -> bool:
    """CRT-R32: killzone or macro (``killzone_or_macro``) or macro only;
    a purge also counts in a purge key hour (v0.2)."""
    t = cfg.timing
    ok = in_macro(ns, cfg) if t.key_time_strictness == "macro_only" else (bool(killzone(ns, cfg)) or in_macro(ns, cfg))
    if purge and in_purge_hour(ns, cfg):
        ok = True
    return ok


def killzone_end_ns(ns: int, cfg: StrategyConfig) -> int | None:
    """End of the killzone containing ``ns`` (UTC ns), or None."""
    name = killzone(ns, cfg)
    if not name:
        return None
    a, b = cfg.timing.killzones[name]
    t = ny(ns)
    end = t.normalize() + pd.Timedelta(minutes=_mins(b))
    if end <= t:
        end += pd.Timedelta(days=1)
    return int(end.tz_convert("UTC").value)


def in_asia_block(ns: int, cfg: StrategyConfig) -> bool:
    a, b = cfg.timing.asia_block
    return in_window(minute_of_day(ns), a, b)


def rhythm_159(open_ns: int) -> str:
    """1/5/9 label of a 4H candle open (books/secrets-of-time)."""
    h = ny(open_ns).hour
    return {1: "1", 13: "1", 5: "5", 17: "5", 9: "9", 21: "9"}.get(h, "")


def frac_in_candle(ns: int, open_ns: int, close_ns: int) -> float:
    return (ns - open_ns) / max(1, close_ns - open_ns)


def weekday(ns: int) -> str:
    return WEEKDAY_NAMES[ny(ns).day_of_week]


def week_of_month(ns: int) -> int:
    return (ny(ns).day - 1) // 7 + 1


def adr(daily: Bars, n: int = 20) -> float:
    if len(daily) < 2:
        return float("nan")
    r = (daily.high - daily.low)[-n:]
    return float(np.mean(r))


def monday_expansion(dny: Bars, ns: int, cfg: StrategyConfig) -> bool | None:
    """G-26 proxy: the closed Monday D_NY candle of ``ns``'s week had a range
    >= ``monday_expansion_adr x ADR(20)`` and closed in the outer 25% of its
    range. None if that Monday has not closed (or is the current day)."""
    t = ny(ns)
    monday = (t.normalize() - pd.Timedelta(days=t.day_of_week))
    if t.day_of_week == 0 or t.day_of_week >= 5:
        return None
    m_ns = int(monday.tz_convert("UTC").value)
    k = int(np.searchsorted(dny.open_time, m_ns, side="left"))
    if k >= len(dny) or dny.open_time[k] != m_ns:
        return None
    prior = dny.slice(slice(max(0, k - 20), k))
    a = adr(prior)
    rng = dny.high[k] - dny.low[k]
    if not np.isfinite(a) or rng <= 0:
        return None
    pos = (dny.close[k] - dny.low[k]) / rng
    return bool(rng >= cfg.bias.monday_expansion_adr * a and (pos >= 0.75 or pos <= 0.25))


def is_sunday_stub(open_ns: int) -> bool:
    return ny(open_ns).day_of_week == 6


# ---------------------------------------------------------------------------
# news blackout (CRT-R66)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=8)
def _calendar(path: str) -> dict[str, frozenset]:
    p = Path(path)
    if not p.is_absolute():
        p = REPO_ROOT / p
    if not p.exists():
        return {}
    with open(p) as fh:
        raw = yaml.safe_load(fh) or {}
    out = {}
    for ev, dates in (raw.get("events") or {}).items():
        out[ev] = frozenset(date.fromisoformat(str(d)) for d in dates or [])
    return out


def news_blocked(ns: int, cfg: StrategyConfig) -> str:
    """Name of the blocking event on the NY day of ``ns`` ('' if none)."""
    cal = _calendar(cfg.risk.news_calendar)
    d = ny(ns).date()
    for ev in cfg.risk.news_events:
        if d in cal.get(ev, ()):
            return ev
    return ""
