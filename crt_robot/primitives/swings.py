"""Swing highs and lows.

* :func:`fractal_swings` (rulebook section 1): bar ``i`` is a swing high if its
  high is strictly greater than the highs of the ``n`` bars on each side.
  It is KNOWN only at the close of bar ``i + n``.
* :func:`ict_swings` (rulebook 6.1, G-02): short-term (level 1) = 3-bar swing;
  intermediate-term (level 2) = a level-1 swing with lower level-1 swings on
  both sides; long-term (level 3) = the same one level up. A level-k swing
  is known when the next level-(k-1) swing on its right is known.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

COLUMNS = ["idx", "kind", "price", "known_at"]


def fractal_swings(df: pd.DataFrame, n: int = 2) -> pd.DataFrame:
    if n < 1:
        raise ValueError("n must be >= 1")
    rows = []
    for kind, col, sign in (("high", "high", 1.0), ("low", "low", -1.0)):
        x = sign * df[col].to_numpy(dtype=float)
        s = pd.Series(x)
        left = s.rolling(n).max().shift(1).to_numpy()
        right = s[::-1].rolling(n).max().shift(1)[::-1].to_numpy()
        ok = (x > left) & (x > right)
        for i in np.flatnonzero(ok):
            rows.append((int(i), kind, sign * x[i], int(i + n)))
    out = pd.DataFrame(rows, columns=COLUMNS)
    return out.sort_values(["idx", "kind"], kind="stable").reset_index(drop=True)


def ict_swings(df: pd.DataFrame, max_level: int = 3) -> pd.DataFrame:
    """Swings with their ICT level (1=STH/STL, 2=ITH/ITL, 3=LTH/LTL).

    Columns: idx, kind, price, known_at (level-1 confirmation), level,
    known_at_l1..known_at_l{max_level} (-1 where the level is not reached).
    """
    base = fractal_swings(df, n=1)
    base["level"] = 1
    for k in range(1, max_level + 1):
        base[f"known_at_l{k}"] = -1
    base["known_at_l1"] = base["known_at"]
    for kind in ("high", "low"):
        sign = 1.0 if kind == "high" else -1.0
        sel = base.index[base["kind"] == kind].to_numpy()
        for level in range(2, max_level + 1):
            cand = [j for j in sel if base.at[j, "level"] >= level - 1]
            for a, b, c in zip(cand, cand[1:], cand[2:]):
                pb = sign * base.at[b, "price"]
                if pb > sign * base.at[a, "price"] and pb > sign * base.at[c, "price"]:
                    base.at[b, "level"] = level
                    base.at[b, f"known_at_l{level}"] = base.at[c, f"known_at_l{level - 1}"]
    return base


def known_swings(swings: pd.DataFrame, t: int, kind: str | None = None, min_level: int = 1) -> pd.DataFrame:
    """Swings knowable at the close of bar ``t`` (no look-ahead)."""
    col = "known_at" if min_level == 1 or "level" not in swings else f"known_at_l{min_level}"
    m = (swings[col] >= 0) & (swings[col] <= t)
    if kind is not None:
        m &= swings["kind"] == kind
    return swings[m]
