"""Killzones, ICT macros and the 1/5/9 4H rhythm (DEF-22/23, G-11, 6.2).

All windows are New York wall-clock times, ``[start, end)``; a window whose
end is before its start wraps past midnight.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from crt_robot.timeutil import NY_TZ, ensure_utc_index

KILLZONES: dict[str, tuple[str, str]] = {
    "asia": ("20:00", "00:00"),
    "london_open": ("02:00", "05:00"),
    "new_york": ("07:00", "10:00"),
    "london_close": ("10:00", "12:00"),
}
INDEX_KILLZONES: dict[str, tuple[str, str]] = {
    "ny_am": ("08:30", "11:00"), "ny_lunch": ("12:00", "13:00"), "ny_pm": ("13:30", "16:00"),
}
# rulebook 7 timing.macros, macro_window: hour
HOUR_MACROS = ("03:00", "06:00", "09:00", "11:00")
# rulebook 6.1 G-11 (macro_window: ict)
ICT_MACROS: tuple[tuple[str, str], ...] = (
    ("02:33", "03:00"), ("04:03", "04:30"), ("08:50", "09:10"), ("09:50", "10:10"),
    ("10:50", "11:10"), ("11:50", "12:10"), ("13:10", "13:40"), ("15:15", "15:45"),
)
H4_OPENS = (1, 5, 9, 13, 17, 21)


def _minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def ny_minute_of_day(index: pd.DatetimeIndex) -> np.ndarray:
    ny = ensure_utc_index(pd.DatetimeIndex(index)).tz_convert(NY_TZ)
    return np.asarray(ny.hour * 60 + ny.minute)


def in_window(index: pd.DatetimeIndex, start: str, end: str) -> np.ndarray:
    m = ny_minute_of_day(index)
    a, b = _minutes(start), _minutes(end)
    return (m >= a) & (m < b) if a < b else (m >= a) | (m < b)


def killzone_labels(index: pd.DatetimeIndex, zones: dict[str, tuple[str, str]] = KILLZONES) -> np.ndarray:
    """Name of the killzone each bar falls in ('' if none). First match wins."""
    out = np.full(len(index), "", dtype=object)
    for name, (a, b) in zones.items():
        hit = in_window(index, a, b) & (out == "")
        out[hit] = name
    return out


def in_macro(index: pd.DatetimeIndex, mode: str = "hour", hours: tuple[str, ...] = HOUR_MACROS) -> np.ndarray:
    """``hour``: the whole clock hour starting at each macro (PROPOSED,
    P:macro_window). ``ict``: the exact ICT windows."""
    if mode == "hour":
        windows = [(h, f"{(_minutes(h) // 60 + 1) % 24:02d}:00") for h in hours]
    elif mode == "ict":
        windows = list(ICT_MACROS)
    else:
        raise ValueError("mode must be 'hour' or 'ict'")
    hit = np.zeros(len(index), bool)
    for a, b in windows:
        hit |= in_window(index, a, b)
    return hit


def h4_rhythm(index: pd.DatetimeIndex) -> pd.DataFrame:
    """For each bar: open hour (NY) of its 4H candle, the 1/5/9 label and the
    minute offset inside that 4H candle (to log e.g. the 03:00 TS hour)."""
    m = ny_minute_of_day(index)
    hour = m // 60
    open_hour = (hour - ((hour - 1) % 4)) % 24
    label = np.select([np.isin(open_hour, [1, 13]), np.isin(open_hour, [5, 17])], ["1", "5"], "9")
    minute_in = ((hour - open_hour) % 24) * 60 + m % 60
    session = np.where((open_hour >= 1) & (open_hour < 13), "am", "pm")
    return pd.DataFrame({"h4_open_hour": open_hour, "rhythm": label, "half": session,
                         "minute_in_h4": minute_in}, index=index)
