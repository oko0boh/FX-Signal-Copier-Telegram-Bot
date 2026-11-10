"""Scripted synthetic minute paths that draw specific CRT shapes.

TESTS ONLY. These are drawings made from straight-line waypoints, never
market data, and no performance is measured on them.
"""

from __future__ import annotations

from crt_robot.data.synthetic import from_waypoints


def _history(start_day: str = "2023-12-11", days: int = 16, lo: float = 1.0960, hi: float = 1.1040):
    """Zig-zag weekdays: low at 03:00 NY, high at 11:00 NY (about 80 pips a day)."""
    import pandas as pd
    pts = []
    d = pd.Timestamp(start_day)
    n = 0
    while n < days:
        if d.day_of_week < 5:
            j = (n % 3) * 0.0004
            pts.append((f"{d:%Y-%m-%d} 03:00", lo + j))
            pts.append((f"{d:%Y-%m-%d} 11:00", hi - j))
            n += 1
        d += pd.Timedelta(days=1)
    return pts


def bull_4h_crt_at_daily_old_low(close_back_inside: bool = True, seed: int = 3):
    """Tue 2024-01-09: 4H C1 (01:00-05:00) range 1.0905-1.0950; C2 (05:00-09:00)
    stabs to 1.0890 with a thick down-close 15m model candle at 06:00, purging
    the daily old low 1.0900 (Wed 2024-01-03), and closes back inside at 1.0920
    (or below 1.0905 if ``close_back_inside`` is False); C3 (09:00-13:00) dips
    to 1.0913, then expands through the 50% to 1.0956."""
    pts = _history()
    pts += [
        ("2024-01-02 03:00", 1.0990), ("2024-01-02 11:00", 1.1000),
        ("2024-01-03 03:00", 1.0950), ("2024-01-03 10:00", 1.0900), ("2024-01-03 16:00", 1.0940),
        ("2024-01-04 02:00", 1.0930), ("2024-01-04 10:00", 1.0970), ("2024-01-04 16:00", 1.0950),
        ("2024-01-05 03:00", 1.0912), ("2024-01-05 10:00", 1.0975), ("2024-01-05 16:59", 1.0940),
        ("2024-01-07 17:00", 1.0940),
        ("2024-01-08 04:00", 1.0960), ("2024-01-08 10:00", 1.0908), ("2024-01-08 23:59", 1.0932),
        ("2024-01-09 01:00", 1.0930), ("2024-01-09 02:30", 1.0950), ("2024-01-09 04:30", 1.0905),
        ("2024-01-09 04:59", 1.0915), ("2024-01-09 06:00", 1.0915), ("2024-01-09 06:10", 1.0890),
        ("2024-01-09 06:14", 1.0893),
    ]
    if close_back_inside:
        pts += [("2024-01-09 06:45", 1.0918), ("2024-01-09 08:59", 1.0920),
                ("2024-01-09 09:40", 1.0913), ("2024-01-09 11:30", 1.0956), ("2024-01-09 12:59", 1.0950)]
    else:
        pts += [("2024-01-09 06:45", 1.0898), ("2024-01-09 08:59", 1.0899),
                ("2024-01-09 09:40", 1.0895), ("2024-01-09 11:30", 1.0930), ("2024-01-09 12:59", 1.0925)]
    pts += [("2024-01-09 16:00", 1.0945), ("2024-01-10 10:00", 1.0960)]
    return from_waypoints(pts, "2023-12-10 17:00", "2024-01-10 12:00", noise=0.000015, seed=seed)
