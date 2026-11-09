"""Rejection block (DEF-28, G-19; ICT and books/crt-keylevels).

At a confirmed swing high, the zone runs from the highest BODY of the swing
candles up to the swing high: the wick part beyond the bodies ("a turtle
soup of the body"). Mirror at a swing low.
"""

from __future__ import annotations

import pandas as pd

from crt_robot.primitives.candles import body_bottom, body_top
from crt_robot.primitives.swings import fractal_swings

COLUMNS = ["kind", "top", "bottom", "swing_idx", "known_at"]


def detect_rejection_blocks(df: pd.DataFrame, n: int = 2, window: int = 1, min_wick_frac: float = 0.3) -> pd.DataFrame:
    """``window`` = candles each side of the swing counted as "swing candles";
    the wick zone must be at least ``min_wick_frac`` of the swing bar's range."""
    bt, bb = body_top(df), body_bottom(df)
    h, l = df["high"].to_numpy(dtype=float), df["low"].to_numpy(dtype=float)
    rows = []
    for s in fractal_swings(df, n).itertuples():
        lo, hi = max(0, s.idx - window), min(len(df), s.idx + window + 1)
        rng = h[s.idx] - l[s.idx]
        if rng <= 0:
            continue
        if s.kind == "high":
            bottom, top = bt[lo:hi].max(), h[s.idx]
            if top - bottom >= min_wick_frac * rng:
                rows.append(("bear", top, bottom, s.idx, s.known_at))
        else:
            top, bottom = bb[lo:hi].min(), l[s.idx]
            if top - bottom >= min_wick_frac * rng:
                rows.append(("bull", top, bottom, s.idx, s.known_at))
    return pd.DataFrame(rows, columns=COLUMNS)
