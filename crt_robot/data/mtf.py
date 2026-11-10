"""Look-ahead-safe multi-timeframe view.

At base bar ``i`` (decision time ``now`` = close of base bar ``i``) a
:class:`Snapshot` exposes:

* ``closed(tf)``: higher-timeframe bars whose ``close_time <= now``. These
  are final and safe to use.
* ``forming(tf)``: the HTF bar still being built, from its open up to and
  including base bar ``i``, flagged ``complete=False``. Its high/low/close
  are partial and change later.

Nothing at or after base bar ``i + 1`` can be reached through this API.
Array accessors return read-only views truncated at ``now``.
:func:`crt_robot.backtest.audit.lookahead_audit` catches strategies that
reach around the API.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from crt_robot.data.resample import bucket_bounds, bucket_keys, resample

FIELDS = ("open", "high", "low", "close")


class LookAheadError(IndexError):
    """Raised when code asks for data that does not exist yet at ``now``."""


@dataclass(frozen=True)
class FormingBar:
    tf: str
    open_time: pd.Timestamp
    close_time: pd.Timestamp
    open: float
    high: float
    low: float
    close: float          # = last base close so far, NOT the final close
    n_bars: int
    complete: bool = False


def _readonly(a: np.ndarray) -> np.ndarray:
    v = a.view()
    v.flags.writeable = False
    return v


class _TFData:
    def __init__(self, base: pd.DataFrame, tf: str, base_len: pd.Timedelta, now: np.ndarray):
        self.tf = tf
        self.bars = resample(base, tf, base_len)
        self.close_times = pd.DatetimeIndex(self.bars["close_time"]).asi8
        self.open_times = pd.DatetimeIndex(self.bars.index).asi8
        self.arrays = {f: self.bars[f].to_numpy() for f in FIELDS}
        keys = bucket_keys(pd.DatetimeIndex(base.index), tf)
        opens, _ = bucket_bounds(keys, tf)
        # position of the HTF bar containing each base bar
        self.group = np.searchsorted(self.open_times, opens.asi8)
        # number of HTF bars fully closed at each base decision time
        self.n_closed = np.searchsorted(self.close_times, now, side="right")
        g = pd.Series(self.group)
        self.f_open = self.arrays["open"][self.group]
        self.f_high = base["high"].groupby(g.values).cummax().to_numpy()
        self.f_low = base["low"].groupby(g.values).cummin().to_numpy()
        self.f_close = base["close"].to_numpy()
        self.f_count = g.groupby(g.values).cumcount().to_numpy() + 1


class MultiTimeframeView:
    """Precomputed MTF view over a base series (1m or 15m bars)."""

    def __init__(self, base: pd.DataFrame, htfs: list[str] | tuple[str, ...],
                 base_len: pd.Timedelta = pd.Timedelta(minutes=1)):
        idx = pd.DatetimeIndex(base.index)
        if idx.tz is None or not idx.is_monotonic_increasing or idx.has_duplicates:
            raise ValueError("base index must be tz-aware, sorted and unique")
        self._base = base
        self.base_len = base_len
        self.index = idx
        self._now = (idx + base_len).asi8
        self._base_arrays = {f: base[f].to_numpy() for f in FIELDS}
        self._tf = {tf: _TFData(base, tf, base_len, self._now) for tf in htfs}
        self.timeframes = tuple(htfs)

    def __len__(self) -> int:
        return len(self.index)

    def at(self, i: int) -> "Snapshot":
        if not 0 <= i < len(self.index):
            raise IndexError(i)
        return Snapshot(self, i)


class Snapshot:
    """What is knowable at the close of base bar ``i``."""

    __slots__ = ("_v", "i")

    def __init__(self, view: MultiTimeframeView, i: int):
        self._v = view
        self.i = i

    @property
    def now(self) -> pd.Timestamp:
        return pd.Timestamp(self._v._now[self.i], tz="UTC")

    @property
    def bar_time(self) -> pd.Timestamp:
        return self._v.index[self.i]

    # ---- base timeframe -------------------------------------------------
    def base(self, n: int | None = None) -> pd.DataFrame:
        lo = 0 if n is None else max(0, self.i + 1 - n)
        return self._v._base.iloc[lo:self.i + 1].copy()

    def base_array(self, field: str) -> np.ndarray:
        return _readonly(self._v._base_arrays[field][: self.i + 1])

    def base_times(self) -> tuple[np.ndarray, np.ndarray]:
        """(open_times, close_times) of base bars 0..i as int64 UTC ns."""
        v = self._v
        return _readonly(v.index.asi8[: self.i + 1]), _readonly(v._now[: self.i + 1])

    @property
    def base_len(self) -> pd.Timedelta:
        return self._v.base_len

    def has_tf(self, tf: str) -> bool:
        return tf in self._v._tf

    def last(self, field: str = "close", back: int = 0) -> float:
        """Base value ``back`` bars ago (0 = current, just-closed bar)."""
        if back < 0:
            raise LookAheadError("negative offsets point into the future")
        if back > self.i:
            raise IndexError("not enough history")
        return float(self._v._base_arrays[field][self.i - back])

    # ---- higher timeframes ---------------------------------------------
    def _tf(self, tf: str) -> _TFData:
        try:
            return self._v._tf[tf]
        except KeyError as exc:
            raise KeyError(f"timeframe {tf!r} not in this view {self._v.timeframes}") from exc

    def n_closed(self, tf: str) -> int:
        return int(self._tf(tf).n_closed[self.i])

    def closed(self, tf: str, n: int | None = None) -> pd.DataFrame:
        d = self._tf(tf)
        k = int(d.n_closed[self.i])
        lo = 0 if n is None else max(0, k - n)
        out = d.bars.iloc[lo:k].drop(columns=["complete"]).copy()
        out["complete"] = True
        return out

    def closed_array(self, tf: str, field: str) -> np.ndarray:
        d = self._tf(tf)
        return _readonly(d.arrays[field][: int(d.n_closed[self.i])])

    def closed_times(self, tf: str) -> tuple[np.ndarray, np.ndarray]:
        """(open_times, close_times) of the closed ``tf`` bars as int64 UTC ns."""
        d = self._tf(tf)
        k = int(d.n_closed[self.i])
        return _readonly(d.open_times[:k]), _readonly(d.close_times[:k])

    @property
    def now_ns(self) -> int:
        return int(self._v._now[self.i])

    def closed_bar(self, tf: str, back: int = 1) -> pd.Series:
        """``back``-th most recent closed bar (1 = latest closed)."""
        if back < 1:
            raise LookAheadError("back=0 would be the forming bar; use forming()")
        d = self._tf(tf)
        k = int(d.n_closed[self.i])
        if back > k:
            raise IndexError(f"only {k} closed {tf} bars so far")
        return d.bars.iloc[k - back]

    def forming(self, tf: str) -> FormingBar | None:
        """The incomplete HTF bar containing base bar ``i``; ``None`` if that
        bar closed exactly at ``now`` (it is then the latest closed bar)."""
        d = self._tf(tf)
        g = int(d.group[self.i])
        if g < int(d.n_closed[self.i]):
            return None
        i = self.i
        return FormingBar(
            tf=tf,
            open_time=pd.Timestamp(d.open_times[g], tz="UTC"),
            close_time=pd.Timestamp(d.close_times[g], tz="UTC"),
            open=float(d.f_open[i]), high=float(d.f_high[i]), low=float(d.f_low[i]),
            close=float(d.f_close[i]), n_bars=int(d.f_count[i]),
        )
