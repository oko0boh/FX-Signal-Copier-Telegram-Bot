"""Sweeps, closes beyond a level, candle outcomes (DEF-04/05) and turtle
soup (DEF-06)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


def swept_above(high: float | np.ndarray, level: float, min_excess: float = 0.0):
    """DEF-04 bearish side: traded above ``level`` (by >= ``min_excess`` if set)."""
    return high >= level + min_excess if min_excess > 0 else high > level


def swept_below(low: float | np.ndarray, level: float, min_excess: float = 0.0):
    return low <= level - min_excess if min_excess > 0 else low < level


def closed_above(close: float | np.ndarray, level: float):
    """Strictly beyond; a wick beyond never counts as a close beyond."""
    return close > level


def closed_below(close: float | np.ndarray, level: float):
    return close < level


@dataclass(frozen=True)
class Outcome:
    kind: str           # breakout_up, breakout_down, ts_high, ts_low, inside, none
    outside: bool = False   # True if the candle swept both sides of the reference


def classify(ref: pd.Series | dict, nxt: pd.Series | dict, min_excess: float = 0.0) -> Outcome:
    """DEF-05: classify candle ``nxt`` against reference candle ``ref``."""
    up = swept_above(nxt["high"], ref["high"], min_excess)
    dn = swept_below(nxt["low"], ref["low"], min_excess)
    c = nxt["close"]
    if closed_above(c, ref["high"]):
        return Outcome("breakout_up", bool(dn))
    if closed_below(c, ref["low"]):
        return Outcome("breakout_down", bool(up))
    if up and dn:  # PROPOSED: nearest side to the close
        side = "ts_high" if (ref["high"] - c) <= (c - ref["low"]) else "ts_low"
        return Outcome(side, True)
    if up:
        return Outcome("ts_high")
    if dn:
        return Outcome("ts_low")
    return Outcome("inside")


@dataclass(frozen=True)
class TurtleSoup:
    side: str           # "high" (bearish TS) or "low" (bullish TS)
    level: float
    sweep_idx: int
    confirm_idx: int    # bar whose close confirmed the close back inside
    extreme: float      # most extreme price reached during the sweep


def turtle_soup(
    df: pd.DataFrame, level: float, side: str, start: int = 0,
    close_back_bars: int = 1, min_excess: float = 0.0, end: int | None = None,
) -> TurtleSoup | str | None:
    """Scan from ``start`` for the first sweep of ``level`` and decide its outcome.

    Returns a :class:`TurtleSoup` if price closes back on the original side
    within ``close_back_bars`` bars (the sweep bar is bar 1), ``"breakout"``
    if a close beyond the level comes first or no close back happens in time,
    or ``None`` if the level is never swept.
    """
    if side not in ("high", "low"):
        raise ValueError(side)
    h, l, c = (df[k].to_numpy(dtype=float) for k in ("high", "low", "close"))
    stop = len(df) if end is None else min(end, len(df))
    for i in range(start, stop):
        hit = swept_above(h[i], level, min_excess) if side == "high" else swept_below(l[i], level, min_excess)
        if not hit:
            continue
        extreme = h[i] if side == "high" else l[i]
        for j in range(i, min(i + close_back_bars, stop)):
            extreme = max(extreme, h[j]) if side == "high" else min(extreme, l[j])
            back = c[j] <= level if side == "high" else c[j] >= level
            if back:
                return TurtleSoup(side, level, i, j, extreme)
        return "breakout"
    return None


def unswept(df: pd.DataFrame, level: float, side: str, start: int, end: int) -> bool:
    """True if no bar in ``[start, end)`` traded through ``level``."""
    if end <= start:
        return True
    if side == "high":
        return bool(df["high"].to_numpy()[start:end].max() <= level)
    return bool(df["low"].to_numpy()[start:end].min() >= level)
