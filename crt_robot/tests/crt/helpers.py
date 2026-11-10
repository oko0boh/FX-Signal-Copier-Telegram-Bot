"""Builders for hand-made Bars and a fake MarketData (tests only)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from crt_robot.crt.bars import Bars
from crt_robot.timeutil import NY_TZ


def mk(rows, start: str, freq: str, tf: str) -> Bars:
    """rows = (open, high, low, close); ``start`` = NY time of the first open."""
    step = pd.Timedelta(freq)
    t0 = pd.Timestamp(start, tz=NY_TZ).tz_convert("UTC")
    ot = np.array([(t0 + k * step).value for k in range(len(rows))], dtype=np.int64)
    ct = ot + step.value
    a = np.array(rows, dtype=float).reshape(-1, 4)
    return Bars(tf, ot, ct, a[:, 0].copy(), a[:, 1].copy(), a[:, 2].copy(), a[:, 3].copy())


def ns(t: str) -> int:
    return int(pd.Timestamp(t, tz=NY_TZ).tz_convert("UTC").value)


class FakeMD:
    def __init__(self, bars: dict[str, Bars], now: str | int):
        self._b = bars
        self.cache: dict = {}
        self.now_ns = ns(now) if isinstance(now, str) else int(now)

    def bars(self, tf: str) -> Bars:
        return self._b[tf]

    def resolve(self, tf: str) -> str:
        return tf

    def memo(self, key, fn):
        if key not in self.cache:
            self.cache[key] = fn()
        return self.cache[key]
