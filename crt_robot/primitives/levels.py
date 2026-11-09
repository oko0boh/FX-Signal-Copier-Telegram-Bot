"""Reference levels aligned to every bar without look-ahead:
previous day/week high and low, midnight open and weekly open.

Every value at bar ``i`` depends only on bars ``<= i``: previous-period
levels come from periods that closed before bar ``i``'s period opened, and
an opening price is NaN until its opening bar has printed.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from crt_robot.data.resample import bucket_bounds, bucket_keys, resample
from crt_robot.timeutil import NY_TZ, ny_time  # noqa: F401  (re-exported for users)


def previous_period_hl(df: pd.DataFrame, tf: str = "D") -> pd.DataFrame:
    """Columns ``prev_high``, ``prev_low`` = the last COMPLETED ``tf`` bar
    (``D`` broker day 17:00 NY, ``D_NY`` midnight day, ``W`` Sun 17:00 week)."""
    htf = resample(df, tf)
    keys = bucket_keys(pd.DatetimeIndex(df.index), tf)
    opens, _ = bucket_bounds(keys, tf)
    pos = np.searchsorted(pd.DatetimeIndex(htf.index).asi8, opens.asi8)
    prev = pos - 1
    ok = prev >= 0
    ph = np.full(len(df), np.nan)
    pl = np.full(len(df), np.nan)
    ph[ok] = htf["high"].to_numpy()[prev[ok]]
    pl[ok] = htf["low"].to_numpy()[prev[ok]]
    return pd.DataFrame({"prev_high": ph, "prev_low": pl}, index=df.index)


def open_at(df: pd.DataFrame, period: str, weekday: int | None, hour: int, minute: int = 0,
            tolerance_min: int = 59) -> pd.Series:
    """Opening price of the bar at ``hour:minute`` NY (on ``weekday`` if set),
    carried forward until the end of ``period`` (``D_NY`` or ``W``).

    If the first bar after that time comes more than ``tolerance_min``
    minutes late, the open counts as missing (NaN)."""
    idx = pd.DatetimeIndex(df.index)
    ny = idx.tz_convert(NY_TZ)
    mins = np.asarray(ny.hour * 60 + ny.minute)
    target = hour * 60 + minute
    day_ok = np.ones(len(df), bool) if weekday is None else np.asarray(ny.dayofweek == weekday)
    after = day_ok & (mins >= target)
    group = np.asarray(bucket_keys(idx, period).asi8)
    out = np.full(len(df), np.nan)
    opens = df["open"].to_numpy()
    current_group, value, seen = None, np.nan, False
    for i in range(len(df)):
        if group[i] != current_group:
            current_group, value, seen = group[i], np.nan, False
        if not seen and after[i]:
            seen = True
            value = opens[i] if mins[i] - target <= tolerance_min else np.nan
        out[i] = value
    return pd.Series(out, index=df.index)


def midnight_open(df: pd.DataFrame) -> pd.Series:
    """00:00 NY open of the current NY day (NaN before midnight prints)."""
    return open_at(df, "D_NY", None, 0, 0)


def weekly_open(df: pd.DataFrame, mode: str = "mon_0000") -> pd.Series:
    """Weekly opening price (rulebook C-02). ``mon_0000`` = Monday 00:00 NY
    (default ``week_open``); ``sun_1700`` = the Sunday 17:00 NY open."""
    if mode == "mon_0000":
        return open_at(df, "W", 0, 0, 0)
    if mode == "sun_1700":
        return open_at(df, "W", 6, 17, 0)
    raise ValueError("mode must be 'mon_0000' or 'sun_1700'")
