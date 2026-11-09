"""Dealing range, equilibrium and premium/discount (DEF-19/20)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from crt_robot.primitives.swings import known_swings


@dataclass(frozen=True)
class DealingRange:
    high: float
    low: float
    high_idx: int
    low_idx: int

    def __post_init__(self):
        if self.high <= self.low:
            raise ValueError("dealing range needs high > low")

    @property
    def eq(self) -> float:
        return (self.high + self.low) / 2

    @property
    def direction(self) -> str:
        """``up`` if the leg ran low -> high (expansion up), else ``down``."""
        return "up" if self.low_idx < self.high_idx else "down"

    def position(self, price: float | np.ndarray):
        """0 at the low, 1 at the high, 0.5 at equilibrium."""
        return (price - self.low) / (self.high - self.low)

    def zone(self, price: float) -> str:
        if price > self.eq:
            return "premium"
        if price < self.eq:
            return "discount"
        return "equilibrium"

    def level(self, frac: float) -> float:
        return self.low + frac * (self.high - self.low)


def latest_dealing_range(swings: pd.DataFrame, t: int, min_size: float = 0.0,
                         min_level: int = 1) -> DealingRange | None:
    """Range between the latest known swing high and swing low at bar ``t``."""
    hi = known_swings(swings, t, "high", min_level)
    lo = known_swings(swings, t, "low", min_level)
    if hi.empty or lo.empty:
        return None
    h = hi.sort_values("idx").iloc[-1]
    l = lo.sort_values("idx").iloc[-1]
    if h.price - l.price <= max(min_size, 0.0):
        return None
    return DealingRange(float(h.price), float(l.price), int(h.idx), int(l.idx))
