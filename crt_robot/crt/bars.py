"""Closed-bar arrays for the CRT logic, read only through the Snapshot.

:class:`Bars` is a light, read-only struct of numpy arrays (open/close
times as int64 UTC ns, OHLC) of CLOSED bars. :class:`MarketData` builds
them from a :class:`~crt_robot.data.mtf.Snapshot` and caches derived work
keyed by the number of closed bars, so a value is recomputed only when a
new bar of that timeframe closes. Every cached value is a function of
closed bars only, which keeps the look-ahead audit green (tested).

Derived timeframes (not built by the resampler):
* ``M``: calendar months (NY date) aggregated from closed daily bars; a
  month is closed once ``now`` reaches the next month's 00:00 NY.
* ``W_MON``: Monday 00:00 NY to Friday weeks (rulebook ``week_range_from:
  mon_0000``) aggregated from closed ``D_NY`` bars without the Sunday stub;
  closed once Friday's D_NY bar has closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
import pandas as pd

from crt_robot.data.mtf import Snapshot
from crt_robot.timeutil import NY_TZ

_BASE_NAMES = {pd.Timedelta(minutes=1): "1m", pd.Timedelta(minutes=5): "5m",
               pd.Timedelta(minutes=15): "15m", pd.Timedelta(hours=1): "1H"}
PARENT = {"15m": "1H", "1H": "4H", "4H": "D", "D": "W", "W": "M", "M": "Y"}
DAILY_TFS = ("D", "D_NY")


@dataclass(frozen=True)
class Bars:
    tf: str
    open_time: np.ndarray   # int64 ns UTC
    close_time: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray

    def __len__(self) -> int:
        return len(self.open)

    def tail(self, n: int) -> "Bars":
        s = slice(max(0, len(self) - n), len(self))
        return self.slice(s)

    def slice(self, s: slice) -> "Bars":
        return Bars(self.tf, self.open_time[s], self.close_time[s], self.open[s], self.high[s],
                    self.low[s], self.close[s])

    def since(self, t_ns: int) -> "Bars":
        """Bars opening at or after ``t_ns``."""
        k = int(np.searchsorted(self.open_time, t_ns, side="left"))
        return self.slice(slice(k, len(self)))

    def between(self, a_ns: int, b_ns: int) -> "Bars":
        """Bars with ``a_ns <= open_time < b_ns``."""
        i = int(np.searchsorted(self.open_time, a_ns, side="left"))
        j = int(np.searchsorted(self.open_time, b_ns, side="left"))
        return self.slice(slice(i, j))

    def bar(self, k: int) -> dict[str, Any]:
        return {"open": float(self.open[k]), "high": float(self.high[k]), "low": float(self.low[k]),
                "close": float(self.close[k]), "open_time": int(self.open_time[k]),
                "close_time": int(self.close_time[k])}

    def df(self) -> pd.DataFrame:
        """DataFrame view (positional index) for the Phase 1 primitives."""
        return pd.DataFrame({"open": self.open, "high": self.high, "low": self.low, "close": self.close})


def _agg(tf: str, groups: np.ndarray, src: Bars, close_times: np.ndarray) -> Bars:
    if len(src) == 0:
        return Bars(tf, *(np.empty(0, dtype=a.dtype) for a in (src.open_time, src.close_time)),
                    *(np.empty(0) for _ in range(4)))
    starts = np.flatnonzero(np.r_[True, groups[1:] != groups[:-1]])
    ends = np.r_[starts[1:], len(groups)]
    return Bars(
        tf,
        src.open_time[starts].copy(),
        close_times,
        src.open[starts].copy(),
        np.maximum.reduceat(src.high, starts),
        np.minimum.reduceat(src.low, starts),
        src.close[ends - 1].copy(),
    )


def _ny_dates(ns: np.ndarray) -> pd.DatetimeIndex:
    return pd.DatetimeIndex(ns, tz="UTC").tz_convert(NY_TZ)


def monthly_from_daily(daily: Bars, now_ns: int) -> Bars:
    """Closed calendar months from closed daily bars (month of the bar's NY
    close date, so a 17:00 broker day belongs to the day it closes on)."""
    if len(daily) == 0:
        return _agg("M", np.empty(0), daily, np.empty(0, dtype=np.int64))
    ref = _ny_dates(daily.close_time - 1)
    key = np.asarray(ref.year * 12 + ref.month - 1)
    now_ny = pd.Timestamp(now_ns, tz="UTC").tz_convert(NY_TZ)
    now_key = now_ny.year * 12 + now_ny.month - 1
    keep = key < now_key                     # months that ended before now's month
    src = daily.slice(slice(0, int(keep.sum())))
    k = key[: len(src)]
    if len(src) == 0:
        return _agg("M", k, src, np.empty(0, dtype=np.int64))
    starts = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    mk = k[starts] + 1
    close = pd.DatetimeIndex([pd.Timestamp(year=int(m // 12), month=int(m % 12) + 1, day=1, tz=NY_TZ)
                              for m in mk]).tz_convert("UTC").asi8
    return _agg("M", k, src, close)


def weeks_from_dny(dny: Bars) -> Bars:
    """Monday-to-Friday weeks from closed D_NY bars (Sunday stubs dropped).
    The last week is included only once its Friday bar has closed."""
    if len(dny) == 0:
        return _agg("W_MON", np.empty(0), dny, np.empty(0, dtype=np.int64))
    d = _ny_dates(dny.open_time)
    dow = np.asarray(d.day_of_week)
    keep = dow < 5
    src = Bars("D_NY", *(a[keep] for a in (dny.open_time, dny.close_time, dny.open, dny.high, dny.low, dny.close)))
    dd = d[keep]
    monday = np.asarray((dd.tz_localize(None).normalize() - pd.to_timedelta(dd.day_of_week, unit="D")).asi8)
    fri = np.asarray(dd.day_of_week) == 4
    if len(src) == 0:
        return _agg("W_MON", monday, src, np.empty(0, dtype=np.int64))
    starts = np.flatnonzero(np.r_[True, monday[1:] != monday[:-1]])
    ends = np.r_[starts[1:], len(monday)]
    complete = np.array([fri[s:e].any() for s, e in zip(starts, ends)])
    n_weeks = len(starts) if complete[-1] else len(starts) - 1
    if n_weeks <= 0:
        return _agg("W_MON", monday[:0], src.slice(slice(0, 0)), np.empty(0, dtype=np.int64))
    cut = int(ends[n_weeks - 1])
    src = src.slice(slice(0, cut))
    close = src.close_time[ends[:n_weeks] - 1].copy()
    return _agg("W_MON", monday[:cut], src, close)


class MarketData:
    """Per-snapshot accessor with a cache that survives across snapshots.

    ``cache`` is owned by the caller (the strategy) and holds only values
    computed from closed bars, keyed by ``(name, tf, n_closed, ...)``.
    """

    def __init__(self, snap: Snapshot, cache: dict, daily_tf: str = "D_NY", weekly_tf: str = "W"):
        self.snap = snap
        self.cache = cache
        self.daily_tf = daily_tf
        self.weekly_tf = weekly_tf
        self.now_ns = snap.now_ns

    # ---- raw bars -----------------------------------------------------
    def _base_name(self) -> str:
        name = self.cache.get("__base_name__")
        if name is None:
            name = _BASE_NAMES.get(self.snap.base_len, "")
            self.cache["__base_name__"] = name
            self.cache["__base_has_tf__"] = self.snap.has_tf(name)
        return name

    def n_closed(self, tf: str) -> int:
        tf = self.resolve(tf)
        if tf == "M":
            return len(self.bars("M"))
        if tf == "W_MON":
            return len(self.bars("W_MON"))
        if tf == self._base_name() and not self.cache["__base_has_tf__"]:
            return self.snap.i + 1
        return self.snap.n_closed(tf)

    def resolve(self, tf: str) -> str:
        """Map the logical daily / weekly names to the configured candles."""
        if tf == "D":
            return self.daily_tf
        if tf == "W":
            return self.weekly_tf
        return tf

    def bars(self, tf: str) -> Bars:
        tf = self.resolve(tf)
        s = self.snap
        if tf == "M":
            d = self.bars("D")
            key = ("M", len(d), _month_key(self.now_ns))
            return self.memo(key, lambda: monthly_from_daily(d, self.now_ns))
        if tf == "W_MON":
            ot, ct = s.closed_times("D_NY")
            d = Bars("D_NY", ot, ct, *(s.closed_array("D_NY", f) for f in ("open", "high", "low", "close")))
            return self.memo(("W_MON", len(d)), lambda: weeks_from_dny(d))
        if tf == self._base_name() and not s.has_tf(tf):
            ot, ct = s.base_times()
            return Bars(tf, ot, ct, *(s.base_array(f) for f in ("open", "high", "low", "close")))
        ot, ct = s.closed_times(tf)
        return Bars(tf, ot, ct, *(s.closed_array(tf, f) for f in ("open", "high", "low", "close")))

    def forming(self, tf: str):
        return self.snap.forming(self.resolve(tf))

    def memo(self, key: tuple, fn: Callable[[], Any]) -> Any:
        if key in self.cache:
            return self.cache[key]
        if len(self.cache) > 20_000:
            keep = {k: v for k, v in self.cache.items() if isinstance(k, str)}
            self.cache.clear()
            self.cache.update(keep)
        val = fn()
        self.cache[key] = val
        return val

    def last_price(self) -> float:
        return self.snap.last("close")


def _month_key(ns: int) -> int:
    t = pd.Timestamp(ns, tz="UTC").tz_convert(NY_TZ)
    return t.year * 12 + t.month


def ny(ns: int) -> pd.Timestamp:
    return pd.Timestamp(int(ns), tz="UTC").tz_convert(NY_TZ)


def ts(ns: int) -> pd.Timestamp:
    return pd.Timestamp(int(ns), tz="UTC")
