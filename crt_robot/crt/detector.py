"""CRT formation (rulebook group D): candle 1 / 2 / 3.

* C1 = the candle before C2, or the outer (mother) candle when the candles
  between it and C2 are inside it (CRT-R26 / DEF-27, up to ``max_inside_bars``).
* CRT high / low / 50% from C1's full wick range (CRT-R24, DEF-02/03).
* C2 classified against C1 at C2's close (DEF-05, CRT-R25): ``ts_low`` ->
  bull CRT, ``ts_high`` -> bear CRT, breakout -> dropped where the close back
  inside is required (CRT-R29), otherwise kept with ``close_inside = False``
  (scored, C-04), inside -> no CRT yet (C1 stays the mother candle).
* C3 = the next candle; targets 50% then the opposite extreme (CRT-R53),
  tracked by :func:`c3_progress`.
"""

from __future__ import annotations

from dataclasses import dataclass

from crt_robot.crt.bars import Bars
from crt_robot.crt.context import is_sunday_stub
from crt_robot.crt.setup import BEAR, BULL
from crt_robot.primitives.liquidity import classify


@dataclass(frozen=True)
class CRTShape:
    c1: int                 # positions in the (filtered) bar array
    c2: int
    inside_bars: int
    outcome: str            # ts_low | ts_high | breakout_up | breakout_down | inside
    outside: bool           # C2 swept both sides
    direction: str | None   # bull | bear | None
    close_inside: bool


def crt_bars(b: Bars, skip_sunday_stub: bool) -> Bars:
    """Bars eligible as CRT / bias candles (drops the D_NY Sunday stub)."""
    if not skip_sunday_stub or b.tf != "D_NY" or len(b) == 0:
        return b
    import numpy as np
    keep = np.array([not is_sunday_stub(int(t)) for t in b.open_time])
    if keep.all():
        return b
    return Bars(b.tf, *(a[keep] for a in (b.open_time, b.close_time, b.open, b.high, b.low, b.close)))


def mother_index(b: Bars, k: int, max_inside: int) -> tuple[int, int]:
    """C1 for C2 = bar ``k``: the farthest bar j (within ``max_inside`` inside
    bars) such that all bars j+1..k-1 lie inside bar j. Returns (j, inside)."""
    best = k - 1
    for j in range(k - 2, max(-1, k - 2 - max_inside), -1):
        if j < 0:
            break
        seg_h = b.high[j + 1:k]
        seg_l = b.low[j + 1:k]
        if (seg_h <= b.high[j]).all() and (seg_l >= b.low[j]).all():
            best = j
    return best, k - 1 - best


def find_crt(b: Bars, max_inside: int, min_excess: float = 0.0, k: int | None = None) -> CRTShape | None:
    """Classify the latest closed bar (or bar ``k``) as C2 of a CRT."""
    k = len(b) - 1 if k is None else k
    if k < 1:
        return None
    j, inside = mother_index(b, k, max_inside)
    out = classify(b.bar(j), b.bar(k), min_excess)
    direction = None
    close_inside = out.kind in ("ts_low", "ts_high")
    if out.kind == "ts_low":
        direction = BULL
    elif out.kind == "ts_high":
        direction = BEAR
    elif out.kind == "breakout_down":
        direction = BULL       # swept the low and closed below: only a CRT where close-inside is not required
    elif out.kind == "breakout_up":
        direction = BEAR
    return CRTShape(j, k, inside, out.kind, out.outside, direction, close_inside)


def c3_progress(direction: str, crt_high: float, crt_low: float, path_high: float, path_low: float) -> dict:
    """CRT-R59: whether the C3 path reached the 50% and the opposite extreme."""
    mid = (crt_high + crt_low) / 2
    if direction == BULL:
        return {"hit_50": path_high >= mid, "hit_opposite": path_high >= crt_high}
    return {"hit_50": path_low <= mid, "hit_opposite": path_low <= crt_low}
