"""Order block, Sham's definition (DEF-15).

"A single candle or a group of consecutive candles that either fill
liquidity or purge liquidity and then gets engulfed at a key time."

Liquidity context (HTF key level touched, HTF high/low purged, SMT purge)
comes from outside, as a boolean array ``liquidity``: True where that bar
filled or purged liquidity. A group without liquidity is never an OB.

Bullish OB, engulf bar E:
  G  = run of consecutive down-close bars ending before E (max ``max_candles``)
  OB = the longest suffix of G whose body tops E closes above, and which
       holds a liquidity bar
  top    = max high of the OB bars if E also closed above their wicks, else max body top
  bottom = min low of the OB bars
A later bar (within ``engulf_window``) that engulfs a longer suffix produces a
new, larger OB. Bearish is the mirror.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from crt_robot.primitives.candles import body_bottom, body_top, direction

COLUMNS = ["kind", "top", "bottom", "first_idx", "last_idx", "engulf_idx", "known_at",
           "full_candle", "in_key_time"]


def detect_order_blocks(
    df: pd.DataFrame,
    liquidity: np.ndarray,
    max_candles: int = 4,
    engulf_window: int = 3,
    key_time: np.ndarray | None = None,
) -> pd.DataFrame:
    liquidity = np.asarray(liquidity, dtype=bool)
    if len(liquidity) != len(df):
        raise ValueError("liquidity must have one flag per bar")
    d = direction(df)
    bt, bb = body_top(df), body_bottom(df)
    h, l, c = (df[k].to_numpy(dtype=float) for k in ("high", "low", "close"))
    kt = np.zeros(len(df), bool) if key_time is None else np.asarray(key_time, bool)
    rows = []
    n = len(df)
    for kind, colour in (("bull", -1), ("bear", 1)):
        i = 0
        while i < n:
            if d[i] != colour:
                i += 1
                continue
            j = i
            while j + 1 < n and d[j + 1] == colour:
                j += 1
            g_lo = max(i, j - max_candles + 1)  # most recent candles of the run
            best = 0
            for e in range(j + 1, min(n, j + 1 + engulf_window)):
                if kind == "bull" and d[e] == -1 or kind == "bear" and d[e] == 1:
                    break  # a new opposite run starts; stop
                k = 0
                for s in range(j, g_lo - 1, -1):
                    beyond = c[e] > bt[s:j + 1].max() if kind == "bull" else c[e] < bb[s:j + 1].min()
                    if beyond:
                        k = j - s + 1
                    else:
                        break
                if k > best:
                    s = j - k + 1
                    if liquidity[s:j + 1].any():
                        if kind == "bull":
                            full = c[e] > h[s:j + 1].max()
                            top = h[s:j + 1].max() if full else bt[s:j + 1].max()
                            bottom = l[s:j + 1].min()
                        else:
                            full = c[e] < l[s:j + 1].min()
                            bottom = l[s:j + 1].min() if full else bb[s:j + 1].min()
                            top = h[s:j + 1].max()
                        rows.append((kind, top, bottom, s, j, e, e, bool(full), bool(kt[e])))
                    best = k
            i = j + 1
    return pd.DataFrame(rows, columns=COLUMNS).sort_values("engulf_idx", kind="stable").reset_index(drop=True)
