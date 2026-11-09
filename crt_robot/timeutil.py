"""Time-zone helpers.

Conventions (rulebook 0.3):
* Stored timestamps are tz-aware UTC and mark the bar OPEN.
* Rules run in New York time (``America/New_York``).
* The MT5 broker clock is GMT+2 in winter and GMT+3 in summer, switching on
  the US daylight-saving dates. That makes it exactly New York wall time
  + 7 hours all year, so broker midnight = 17:00 NY and the broker 4H grid
  (00, 04, 08, ...) = 17, 21, 01, 05, 09, 13 NY.

US DST switches happen on Sunday 02:00 NY, while FX is closed, so no
trading bar ever straddles a clock change.
"""

from __future__ import annotations

import pandas as pd

NY_TZ = "America/New_York"
UTC = "UTC"
BROKER_OFFSET_FROM_NY = pd.Timedelta(hours=7)


def ensure_utc_index(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Return ``index`` as tz-aware UTC; refuse naive timestamps."""
    if index.tz is None:
        raise ValueError("timestamps must be tz-aware (UTC); got naive index")
    return index.tz_convert(UTC)


def to_ny(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Convert a tz-aware index to New York time."""
    return ensure_utc_index(index).tz_convert(NY_TZ)


def to_broker_naive(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Broker wall-clock time as a naive index (NY wall time + 7h)."""
    return to_ny(index).tz_localize(None) + BROKER_OFFSET_FROM_NY


def broker_naive_to_utc(naive: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Inverse of :func:`to_broker_naive`.

    Ambiguous/non-existent NY wall times only occur on Sunday around 02:00 NY
    (market closed). We resolve them deterministically (DST side / shift
    forward) instead of raising.
    """
    ny_naive = pd.DatetimeIndex(naive) - BROKER_OFFSET_FROM_NY
    ny = ny_naive.tz_localize(NY_TZ, ambiguous=True, nonexistent="shift_forward")
    return ny.tz_convert(UTC)


def ny_time(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> pd.Timestamp:
    """Build a tz-aware UTC timestamp from a New York wall-clock time."""
    return pd.Timestamp(year=year, month=month, day=day, hour=hour, minute=minute, tz=NY_TZ).tz_convert(UTC)
