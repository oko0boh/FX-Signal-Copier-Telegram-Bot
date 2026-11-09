"""Test-only strategies used to validate the backtester. None of these is
a trading idea; they exist to prove the engine finds planted edges, finds
nothing in noise, and catches look-ahead."""

from __future__ import annotations

import numpy as np
import pandas as pd

from crt_robot.backtest.orders import LONG, SHORT, Order
from crt_robot.timeutil import NY_TZ


class TimedLong:
    """Buy at the close of the bar ending at ``hour`` NY, fixed stop/target,
    out after ``hold`` minutes."""

    name = "test_timed_long"

    def __init__(self, hour: int = 9, stop: float = 0.0010, target: float = 0.0010, hold: int = 60):
        self.hour, self.stop, self.target, self.hold = hour, stop, target, hold

    def on_bar(self, snap, state):
        now = snap.now.tz_convert(NY_TZ)
        if state.position is None and state.can_trade and now.hour == self.hour and now.minute == 0:
            px = snap.last("close")
            return [Order(LONG, stop=px - self.stop, target=px + self.target,
                          exit_at=snap.now + pd.Timedelta(minutes=self.hold))]
        return []


class CoinFlip:
    """Random side, symmetric stop/target, deterministic seed."""

    name = "test_coin_flip"

    def __init__(self, p: float = 0.02, dist: float = 0.0006, seed: int = 1):
        self.p, self.dist, self.rng = p, dist, np.random.default_rng(seed)

    def on_bar(self, snap, state):
        u, side = self.rng.random(), self.rng.random() < 0.5
        if state.position is None and not state.pending and state.can_trade and u < self.p:
            px = snap.last("close")
            s = LONG if side else SHORT
            return [Order(s, stop=px - s * self.dist, target=px + s * self.dist)]
        return []


class PeekForming4H:
    """CHEATER: reads the final close of the still-forming 4H bar through a
    private attribute and trades in its direction."""

    name = "test_cheat_peek_4h"

    def on_bar(self, snap, state):
        f = snap.forming("4H")
        if f is None or state.position is not None or not state.can_trade:
            return []
        d = snap._v._tf["4H"]                                # reaching around the API
        final_close = d.arrays["close"][d.group[snap.i]]
        px = snap.last("close")
        if f.n_bars == 60:  # once per 4H bar, after the first hour
            s = LONG if final_close > px else SHORT
            return [Order(s, stop=px - s * 0.0015, target=px + s * 0.0015, exit_at=f.close_time)]
        return []


class Closed4HMomentum:
    """Honest: uses only closed 4H bars."""

    name = "test_closed_4h_momentum"

    def on_bar(self, snap, state):
        if state.position is not None or not state.can_trade or snap.n_closed("4H") < 2:
            return []
        f = snap.forming("4H")
        if f is None or f.n_bars != 1:
            return []
        last = snap.closed_bar("4H", 1)
        s = LONG if last["close"] > last["open"] else SHORT
        px = snap.last("close")
        return [Order(s, stop=px - s * 0.0015, target=px + s * 0.0015, exit_at=f.close_time)]
