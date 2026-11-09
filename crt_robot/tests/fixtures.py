"""Tiny hand-built candle fixtures for primitive tests."""

from __future__ import annotations

import pandas as pd


def bars(rows: list[tuple[float, float, float, float]], start: str = "2024-01-08 09:00",
         freq: str = "15min") -> pd.DataFrame:
    """rows = (open, high, low, close); index in UTC."""
    idx = pd.date_range(pd.Timestamp(start, tz="America/New_York"), periods=len(rows), freq=freq).tz_convert("UTC")
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx.rename("ts"))


def from_highs_lows(highs: list[float], lows: list[float]) -> pd.DataFrame:
    rows = [((h + l) / 2, h, l, (h + l) / 2) for h, l in zip(highs, lows)]
    return bars(rows)
