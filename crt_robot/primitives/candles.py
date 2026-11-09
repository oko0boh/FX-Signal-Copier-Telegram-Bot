"""Basic candle helpers (rulebook 0.3 price conventions, section 1)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def body_top(df: pd.DataFrame) -> np.ndarray:
    return np.maximum(df["open"].to_numpy(), df["close"].to_numpy())


def body_bottom(df: pd.DataFrame) -> np.ndarray:
    return np.minimum(df["open"].to_numpy(), df["close"].to_numpy())


def candle_range(df: pd.DataFrame) -> np.ndarray:
    return (df["high"] - df["low"]).to_numpy()


def mid(df: pd.DataFrame) -> np.ndarray:
    """DEF-03: midpoint of the full wick range."""
    return ((df["high"] + df["low"]) / 2).to_numpy()


def direction(df: pd.DataFrame) -> np.ndarray:
    """+1 up-close, -1 down-close, 0 doji (neither colour)."""
    return np.sign(df["close"].to_numpy() - df["open"].to_numpy()).astype(int)


def atr(df: pd.DataFrame, n: int = 14) -> np.ndarray:
    """Wilder ATR. Value at bar i uses bars <= i only; NaN for the first n-1."""
    h, l, c = (df[k].to_numpy(dtype=float) for k in ("high", "low", "close"))
    prev_c = np.concatenate([[np.nan], c[:-1]])
    tr = np.nanmax(np.vstack([h - l, np.abs(h - prev_c), np.abs(l - prev_c)]), axis=0)
    out = np.full(len(tr), np.nan)
    if len(tr) < n:
        return out
    out[n - 1] = tr[:n].mean()
    for i in range(n, len(tr)):
        out[i] = (out[i - 1] * (n - 1) + tr[i]) / n
    return out


def thick(df: pd.DataFrame, atr_values: np.ndarray, body_ratio: float = 0.6, atr_mult: float = 1.0) -> np.ndarray:
    """DEF-09 (PROPOSED): body/range >= body_ratio and range >= atr_mult * ATR."""
    rng = candle_range(df)
    body = body_top(df) - body_bottom(df)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(rng > 0, body / rng, 0.0)
    return (ratio >= body_ratio) & (rng >= atr_mult * np.nan_to_num(atr_values, nan=np.inf))
