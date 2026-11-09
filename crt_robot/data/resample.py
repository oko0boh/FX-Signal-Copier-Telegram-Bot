"""Resample 1-minute bars to higher timeframes on the MT5 broker clock.

Broker clock = NY wall time + 7h (GMT+2 winter / GMT+3 summer). Grids:

=========  ======================================  ===========================
TF         open times                              close
=========  ======================================  ===========================
1m..1H     clock grid                              open + length
4H         broker 00/04/08.. = NY 17,21,01,05,09,13  open + 4h
D          broker midnight = 17:00 NY              next 17:00 NY
D_NY       00:00 NY (rulebook C-03 default)        next 00:00 NY
W          Sun 17:00 NY (broker Monday 00:00)      Fri 17:00 NY
=========  ======================================  ===========================

Every output bar has ``close_time`` (UTC) and ``complete``. A bar is
complete only if the data reaches its close time. Timestamps mark bar opens.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from crt_robot.timeutil import NY_TZ, broker_naive_to_utc, ensure_utc_index, to_broker_naive


@dataclass(frozen=True)
class TF:
    name: str
    clock: str              # "broker" or "ny"
    floor: str | None       # pandas floor freq on the clock, None = weekly
    length: pd.Timedelta    # nominal length on the clock


TIMEFRAMES: dict[str, TF] = {
    "1m": TF("1m", "broker", "1min", pd.Timedelta(minutes=1)),
    "5m": TF("5m", "broker", "5min", pd.Timedelta(minutes=5)),
    "15m": TF("15m", "broker", "15min", pd.Timedelta(minutes=15)),
    "1H": TF("1H", "broker", "1h", pd.Timedelta(hours=1)),
    "4H": TF("4H", "broker", "4h", pd.Timedelta(hours=4)),
    "D": TF("D", "broker", "1D", pd.Timedelta(days=1)),
    "D_NY": TF("D_NY", "ny", "1D", pd.Timedelta(days=1)),
    "W": TF("W", "broker", None, pd.Timedelta(days=5)),  # Mon 00:00 .. Sat 00:00 broker
}

PRICE_AGG = {"open": "first", "high": "max", "low": "min", "close": "last"}


def get_tf(name: str) -> TF:
    try:
        return TIMEFRAMES[name]
    except KeyError as exc:
        raise KeyError(f"unknown timeframe {name!r}; known: {list(TIMEFRAMES)}") from exc


def _clock_naive(index: pd.DatetimeIndex, clock: str) -> pd.DatetimeIndex:
    if clock == "broker":
        return to_broker_naive(index)
    return ensure_utc_index(index).tz_convert(NY_TZ).tz_localize(None)


def _clock_to_utc(naive: pd.DatetimeIndex, clock: str) -> pd.DatetimeIndex:
    if clock == "broker":
        return broker_naive_to_utc(naive)
    return pd.DatetimeIndex(naive).tz_localize(NY_TZ, ambiguous=True, nonexistent="shift_forward").tz_convert("UTC")


def bucket_keys(index: pd.DatetimeIndex, tf: str) -> pd.DatetimeIndex:
    """Naive clock-time bucket open for every timestamp."""
    spec = get_tf(tf)
    naive = _clock_naive(index, spec.clock)
    if spec.floor is None:  # weekly: back to Monday 00:00 on the broker clock
        return (naive - pd.to_timedelta(naive.day_of_week, unit="D")).normalize()
    return naive.floor(spec.floor)


def bucket_bounds(keys: pd.DatetimeIndex, tf: str) -> tuple[pd.DatetimeIndex, pd.DatetimeIndex]:
    """UTC open and close times for naive bucket keys."""
    spec = get_tf(tf)
    opens = _clock_to_utc(keys, spec.clock).as_unit("ns")
    closes = _clock_to_utc(keys + spec.length, spec.clock).as_unit("ns")
    return opens, closes


def resample(df: pd.DataFrame, tf: str, base: pd.Timedelta = pd.Timedelta(minutes=1)) -> pd.DataFrame:
    """Aggregate ``df`` (UTC-indexed bars of length ``base``) into ``tf`` bars."""
    if df.empty:
        raise ValueError("cannot resample an empty frame")
    idx = ensure_utc_index(pd.DatetimeIndex(df.index))
    if not idx.is_monotonic_increasing or idx.has_duplicates:
        raise ValueError("index must be sorted and unique; run the quality checks first")
    spec = get_tf(tf)
    if spec.length < base:
        raise ValueError(f"cannot resample {base} bars to shorter timeframe {tf}")
    keys = bucket_keys(idx, tf)
    agg: dict[str, str] = {k: v for k, v in PRICE_AGG.items()}
    if "volume" in df:
        agg["volume"] = "sum"
    for c in ("open", "high", "low", "close"):
        if f"ask_{c}" in df:
            agg[f"ask_{c}"] = PRICE_AGG[c]
    frame = df.copy()
    frame.index = keys
    out = frame.groupby(level=0, sort=True).agg(agg)
    out["n_bars"] = frame.groupby(level=0, sort=True).size()
    opens, closes = bucket_bounds(pd.DatetimeIndex(out.index), tf)
    out.index = pd.DatetimeIndex(opens, name="ts")
    out["close_time"] = closes
    out["complete"] = out["close_time"] <= idx[-1] + base
    return out


def resample_all(df: pd.DataFrame, tfs: list[str] | tuple[str, ...] = ("15m", "1H", "4H", "D", "W")) -> dict[str, pd.DataFrame]:
    return {tf: resample(df, tf) for tf in tfs}


def ny_hours(index: pd.DatetimeIndex) -> np.ndarray:
    return np.asarray(ensure_utc_index(index).tz_convert(NY_TZ).hour)
