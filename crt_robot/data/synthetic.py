"""Synthetic 1-minute bars for TESTS ONLY.

These frames validate the code (resampler, view, backtester). They are never
written to ``data_cache`` and never presented as market data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from crt_robot.timeutil import NY_TZ


def fx_minutes(start: str, end: str) -> pd.DatetimeIndex:
    """UTC minute stamps inside the FX week (Sun 17:00 NY to Fri 17:00 NY)."""
    idx = pd.date_range(pd.Timestamp(start, tz=NY_TZ), pd.Timestamp(end, tz=NY_TZ), freq="1min",
                        inclusive="left").as_unit("ns")
    dow, hour = idx.dayofweek, idx.hour
    open_ = ~((dow == 5) | ((dow == 4) & (hour >= 17)) | ((dow == 6) & (hour < 17)))
    return idx[open_].tz_convert("UTC").rename("ts")


def random_walk(
    start: str = "2024-01-07",
    end: str = "2024-02-03",
    price: float = 1.10,
    sigma: float = 0.0001,
    seed: int = 0,
    spread: float = 0.0,
    drift: np.ndarray | None = None,
) -> pd.DataFrame:
    """Gaussian random walk minute bars (bid) with optional ask columns.

    ``drift`` (same length as the index) adds a deterministic move per bar,
    used to plant a known edge.
    """
    idx = fx_minutes(start, end)
    rng = np.random.default_rng(seed)
    n = len(idx)
    steps = rng.normal(0.0, sigma, size=(n, 4))
    if drift is not None:
        steps[:, 3] += drift
    close = price + np.cumsum(steps[:, 3])
    open_ = np.concatenate([[price], close[:-1]])
    wick_hi = np.abs(steps[:, 0]) * 0.5
    wick_lo = np.abs(steps[:, 1]) * 0.5
    high = np.maximum(open_, close) + wick_hi
    low = np.minimum(open_, close) - wick_lo
    df = pd.DataFrame({"open": open_, "high": high, "low": low, "close": close,
                       "volume": rng.integers(1, 100, n).astype(float)}, index=idx)
    if spread:
        for c in ("open", "high", "low", "close"):
            df[f"ask_{c}"] = df[c] + spread
    return df
