"""Break of structure (BOS) and market structure shift (MSS, DEF-10).

Uses swings only once they are KNOWN (fractal confirmation), and closes,
not wicks (Romeo's MSS is close-based).

Bullish break at bar t: ``close[t] > H.price``, where H is the most recent
known swing high not yet broken. Let L1 be the last known swing low before H
and L2 the lowest low between H and t.

* ``L2 < L1``: a lower low after H, then a close above "the high that broke
  the low" = **true MSS** (``mss_bull``). Retrace zone = ``[L2, H]``.
* otherwise: a continuation **BOS** (``bos_bull``).

Bearish is the mirror.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from crt_robot.primitives.swings import fractal_swings

COLUMNS = ["idx", "kind", "level", "swing_idx", "ref_idx", "ref_price", "extreme"]


def detect_structure(df: pd.DataFrame, n: int = 2, swings: pd.DataFrame | None = None) -> pd.DataFrame:
    sw = fractal_swings(df, n) if swings is None else swings
    h, l, c = (df[k].to_numpy(dtype=float) for k in ("high", "low", "close"))
    highs = sw[sw.kind == "high"].sort_values("known_at")
    lows = sw[sw.kind == "low"].sort_values("known_at")
    hi_k, lo_k = highs["known_at"].to_numpy(), lows["known_at"].to_numpy()
    rows = []
    broken: set[tuple[str, int]] = set()
    for t in range(len(df)):
        for kind, sws, karr in (("bull", highs, hi_k), ("bear", lows, lo_k)):
            k = int(np.searchsorted(karr, t, side="right"))
            if k == 0:
                continue
            s = sws.iloc[k - 1]          # most recent known swing of this kind
            key = (kind, int(s.idx))
            if key in broken:
                continue
            crossed = c[t] > s.price if kind == "bull" else c[t] < s.price
            if not crossed:
                continue
            broken.add(key)
            opp = lows if kind == "bull" else highs
            before = opp[(opp.idx < s.idx) & (opp.known_at <= t)]
            seg = slice(int(s.idx) + 1, t + 1)
            extreme = l[seg].min() if kind == "bull" else h[seg].max()
            ref_idx, ref_price, label = -1, np.nan, f"bos_{kind}"
            if len(before):
                ref = before.sort_values("idx").iloc[-1]
                ref_idx, ref_price = int(ref.idx), float(ref.price)
                if (kind == "bull" and extreme < ref_price) or (kind == "bear" and extreme > ref_price):
                    label = f"mss_{kind}"
            rows.append((t, label, float(s.price), int(s.idx), ref_idx, ref_price, float(extreme)))
    return pd.DataFrame(rows, columns=COLUMNS)
