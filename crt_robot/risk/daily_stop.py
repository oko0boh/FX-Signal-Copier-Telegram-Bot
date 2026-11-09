"""Daily loss limit (CRT-R63): stop for the New York day at -2%.

The NY day runs 00:00 to 24:00 New York time. The limit is measured against
equity at the first check of the day, including open positions marked to
market. Once hit, no new trades until the next NY day.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from crt_robot.timeutil import NY_TZ

DEFAULT_LIMIT = 0.02


class DailyLossGuard:
    def __init__(self, limit: float = DEFAULT_LIMIT):
        if not 0 < limit < 1:
            raise ValueError("limit is a fraction, e.g. 0.02")
        self.limit = limit
        self.day: date | None = None
        self.start_equity = 0.0
        self.blocked = False
        self.hits: list[date] = []

    @staticmethod
    def ny_day(ts: pd.Timestamp) -> date:
        return ts.tz_convert(NY_TZ).date()

    def update(self, ts: pd.Timestamp, equity: float) -> bool:
        """Feed the current (marked-to-market) equity; returns True if
        trading is blocked for the rest of this NY day."""
        d = self.ny_day(ts)
        if d != self.day:
            self.day, self.start_equity, self.blocked = d, equity, False
        if not self.blocked and equity <= self.start_equity * (1 - self.limit):
            self.blocked = True
            self.hits.append(d)
        return self.blocked

    def can_trade(self, ts: pd.Timestamp) -> bool:
        return not (self.blocked and self.ny_day(ts) == self.day)
