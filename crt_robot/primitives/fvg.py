"""Fair value gaps (DEF-17, ICT standard) with consequent encroachment and
fill state (G-10).

Three bars a, b, c. Bullish FVG if ``c.low > a.high`` (gap
``[a.high, c.low]``); bearish if ``c.high < a.low`` (gap ``[c.high, a.low]``).
The FVG is known at the close of ``c``. After that we record the first bar
whose wick touches the gap, reaches its CE (50%), and fills it completely.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

FILL_RULES = ("touch", "half", "full")


def detect_fvgs(df: pd.DataFrame, min_size: float = 0.0, max_age: int | None = None) -> pd.DataFrame:
    h = df["high"].to_numpy(dtype=float)
    l = df["low"].to_numpy(dtype=float)
    rows = []
    for c in range(2, len(df)):
        a = c - 2
        if l[c] > h[a] and l[c] - h[a] > min_size:
            rows.append(("bull", l[c], h[a], a, c))
        elif h[c] < l[a] and l[a] - h[c] > min_size:
            rows.append(("bear", l[a], h[c], a, c))
    out = pd.DataFrame(rows, columns=["kind", "top", "bottom", "a_idx", "created_idx"])
    out["ce"] = (out["top"] + out["bottom"]) / 2
    out["known_at"] = out["created_idx"]
    touched, ce_hit, filled = [], [], []
    n = len(df)
    for r in out.itertuples():
        stop = n if max_age is None else min(n, r.created_idx + 1 + max_age)
        lo, hi = r.created_idx + 1, stop
        if r.kind == "bull":  # price returns down into the gap
            w = l[lo:hi]
            t, m, f = w <= r.top, w <= r.ce, w <= r.bottom
        else:
            w = h[lo:hi]
            t, m, f = w >= r.bottom, w >= r.ce, w >= r.top
        touched.append(lo + int(np.argmax(t)) if t.any() else -1)
        ce_hit.append(lo + int(np.argmax(m)) if m.any() else -1)
        filled.append(lo + int(np.argmax(f)) if f.any() else -1)
    out["touched_idx"], out["ce_idx"], out["filled_idx"] = touched, ce_hit, filled
    return out


def fvg_open_at(fvgs: pd.DataFrame, t: int, rule: str = "touch") -> pd.DataFrame:
    """FVGs known at bar ``t`` that are not yet mitigated under ``rule``.

    ``rule``: touch = any wick into the gap mitigates; half = reaching CE;
    full = trading through the far edge.
    """
    if rule not in FILL_RULES:
        raise ValueError(f"rule must be one of {FILL_RULES}")
    col = {"touch": "touched_idx", "half": "ce_idx", "full": "filled_idx"}[rule]
    known = fvgs["known_at"] <= t
    alive = (fvgs[col] < 0) | (fvgs[col] > t)
    return fvgs[known & alive]
