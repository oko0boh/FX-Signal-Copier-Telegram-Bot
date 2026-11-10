"""Key levels (DEF-14, CRT-R18/R19/R20/R22, G-01).

Candidates are built on the key-level timeframe (one step above the CRT
TF, ``kl_tf_for_htf``; optionally ``kl_tf_secondary`` too) from closed bars
only, and must be knowable before C2 opens and still unswept / untouched at
that time. Types (``kl_types``):

=================  =========================================================
old_high/old_low   fractal swing (``swing_n``), unswept  (OHP / OLP)
bos_origin_hl      the low that broke a high / the high that broke a low
                   (origin of a BOS or MSS on the KL TF), unswept
fvg                ICT FVG, not mitigated under ``fvg_fill``
ob                 Sham OB (liquidity = sweep of a same-TF swing, G-13 proxy)
rb                 rejection block: wick beyond the bodies at a swing
prev_period_hl     previous KL-TF candle's high / low (PDH/PDL, PWH/PWL)
candle_open        open of the last down-close (support) / up-close candle
weekly_wick_50     50% of the last weekly candle's lower / upper wick
=================  =========================================================

Bull setups use support levels (side ``low``), bear setups resistance
(side ``high``). C2 (or the LTF purge) "reaches" a level when its wick
purges a line level (``low < level``) or enters a zone (``low <= top``),
within ``kl_touch_tol x ATR(ltf)``.
"""

from __future__ import annotations

import numpy as np

from crt_robot.crt.bars import Bars, MarketData
from crt_robot.crt.config import StrategyConfig
from crt_robot.crt.setup import BULL, KeyLevel
from crt_robot.primitives.candles import atr
from crt_robot.primitives.fvg import detect_fvgs
from crt_robot.primitives.order_block import detect_order_blocks
from crt_robot.primitives.rejection_block import detect_rejection_blocks
from crt_robot.primitives.structure import detect_structure
from crt_robot.primitives.swings import fractal_swings

LINE_TYPES = ("old_high", "old_low", "bos_origin_hl", "prev_period_hl", "candle_open", "weekly_wick_50")


def _extreme_between(path: Bars, a_ns: int, b_ns: int, side: str) -> float:
    """Highest high (side=high) / lowest low between ``a_ns`` and ``b_ns``."""
    seg = path.between(a_ns, b_ns)
    if len(seg) == 0:
        return -np.inf if side == "high" else np.inf
    return float(seg.high.max()) if side == "high" else float(seg.low.min())


def _swing_liquidity(df, swings) -> np.ndarray:
    """True where a bar swept a fractal swing that was known before it."""
    h, l = df["high"].to_numpy(), df["low"].to_numpy()
    flag = np.zeros(len(df), bool)
    for s in swings.itertuples():
        after = np.arange(len(df)) > s.known_at
        if s.kind == "low":
            flag |= after & (l < s.price)
        else:
            flag |= after & (h > s.price)
    return flag


def raw_candidates(kl: Bars, cfg: StrategyConfig, primary: bool) -> list[KeyLevel]:
    """Every candidate on ``kl`` (no time / sweep filtering yet), both sides."""
    k = cfg.key_level
    n = cfg.general.swing_n
    types = set(k.kl_types)
    out: list[KeyLevel] = []
    if len(kl) < 2 * n + 3:
        return out
    df = kl.df()
    ct = kl.close_time
    sw = fractal_swings(df, n)

    def known(i: int) -> int:
        return int(ct[min(int(i), len(ct) - 1)])

    if "old_high" in types or "old_low" in types:
        for s in sw.itertuples():
            if s.known_at >= len(kl):
                continue
            if s.kind == "high" and "old_high" in types:
                out.append(KeyLevel("old_high", kl.tf, "high", s.price, s.price, known(s.known_at),
                                    primary_tf=primary, score=0))
            if s.kind == "low" and "old_low" in types:
                out.append(KeyLevel("old_low", kl.tf, "low", s.price, s.price, known(s.known_at), primary_tf=primary))
    if "bos_origin_hl" in types:
        st = detect_structure(df, n, swings=sw)
        for e in st.itertuples():
            side = "low" if e.kind.endswith("bull") else "high"
            out.append(KeyLevel("bos_origin_hl", kl.tf, side, e.extreme, e.extreme, known(e.idx),
                                is_bos_origin=True, primary_tf=primary))
    if "fvg" in types:
        for f in detect_fvgs(df).itertuples():
            side = "low" if f.kind == "bull" else "high"
            out.append(KeyLevel("fvg", kl.tf, side, float(f.top), float(f.bottom), known(f.created_idx),
                                primary_tf=primary))
    if "ob" in types:
        liq = _swing_liquidity(df, sw) if k.ob_liquidity == "same_tf_swing" else np.ones(len(df), bool)
        for o in detect_order_blocks(df, liq, max_candles=cfg.entry.ob_max_candles).itertuples():
            side = "low" if o.kind == "bull" else "high"
            out.append(KeyLevel("ob", kl.tf, side, float(o.top), float(o.bottom), known(o.engulf_idx),
                                primary_tf=primary))
    if "rb" in types:
        for r in detect_rejection_blocks(df, n=n).itertuples():
            side = "low" if r.kind == "bull" else "high"
            out.append(KeyLevel("rb", kl.tf, side, float(r.top), float(r.bottom), known(r.known_at),
                                primary_tf=primary))
    last = len(kl) - 1
    if "prev_period_hl" in types:
        out.append(KeyLevel("prev_period_hl", kl.tf, "high", float(kl.high[last]), float(kl.high[last]),
                            int(ct[last]), primary_tf=primary))
        out.append(KeyLevel("prev_period_hl", kl.tf, "low", float(kl.low[last]), float(kl.low[last]),
                            int(ct[last]), primary_tf=primary))
    if "candle_open" in types:
        d = np.sign(kl.close - kl.open)
        dn, up = np.flatnonzero(d < 0), np.flatnonzero(d > 0)
        if len(dn):
            j = int(dn[-1])
            out.append(KeyLevel("candle_open", kl.tf, "low", float(kl.open[j]), float(kl.open[j]), int(ct[j]),
                                primary_tf=primary))
        if len(up):
            j = int(up[-1])
            out.append(KeyLevel("candle_open", kl.tf, "high", float(kl.open[j]), float(kl.open[j]), int(ct[j]),
                                primary_tf=primary))
    return out


def weekly_wick_levels(weekly: Bars) -> list[KeyLevel]:
    if len(weekly) == 0:
        return []
    j = len(weekly) - 1
    o, h, l, c = weekly.open[j], weekly.high[j], weekly.low[j], weekly.close[j]
    lo = (min(o, c) + l) / 2
    hi = (max(o, c) + h) / 2
    t = int(weekly.close_time[j])
    return [KeyLevel("weekly_wick_50", weekly.tf, "low", float(lo), float(lo), t),
            KeyLevel("weekly_wick_50", weekly.tf, "high", float(hi), float(hi), t)]


def candidates(md: MarketData, cfg: StrategyConfig, htf: str, direction: str, before_ns: int,
               path_tf: str) -> list[KeyLevel]:
    """Candidates for a ``direction`` setup on ``htf``: knowable before
    ``before_ns`` and unswept/untouched on the ``path_tf`` bars up to then."""
    side = "low" if direction == BULL else "high"
    tfs = [(cfg.timeframes.kl_tf_for_htf.get(htf), True)]
    if cfg.timeframes.use_kl_tf_secondary:
        tfs.append((cfg.timeframes.kl_tf_secondary.get(htf), False))
    lookback = cfg.key_level.kl_lookback_bars
    levels: list[KeyLevel] = []
    for tf, primary in tfs:
        if tf is None or tf == "Y":
            continue
        allb = md.bars(tf)
        # only KL bars that closed before C2 opened
        k = int(np.searchsorted(allb.close_time, before_ns, side="right"))
        kl = allb.slice(slice(max(0, k - lookback), k))
        key = ("kl_raw", md.resolve(tf), k, primary)
        levels += md.memo(key, lambda kl=kl, primary=primary: raw_candidates(kl, cfg, primary))
    if "weekly_wick_50" in cfg.key_level.kl_types:
        w = md.bars("W")
        kw = int(np.searchsorted(w.close_time, before_ns, side="right"))
        levels += weekly_wick_levels(w.slice(slice(0, kw)))
    path = md.bars(path_tf)
    fill = cfg.dealing_range.fvg_fill
    out = []
    for lv in levels:
        if lv.side != side or lv.known_ns > before_ns:
            continue
        ext = _extreme_between(path, lv.known_ns, before_ns, "low" if side == "low" else "high")
        if lv.kind in ("fvg", "ob", "rb"):
            if side == "low":
                edge = {"touch": lv.top, "half": (lv.top + lv.bottom) / 2, "full": lv.bottom}[fill] \
                    if lv.kind == "fvg" else lv.top
                alive = ext > edge
            else:
                edge = {"touch": lv.bottom, "half": (lv.top + lv.bottom) / 2, "full": lv.top}[fill] \
                    if lv.kind == "fvg" else lv.bottom
                alive = ext < edge
        else:
            alive = ext >= lv.price if side == "low" else ext <= lv.price
        if alive:
            out.append(lv)
    return out


def reached(lv: KeyLevel, extreme: float, direction: str, tol: float = 0.0) -> bool:
    """CRT-R18/R20: the purge wick ``extreme`` purged the line level or
    entered the zone."""
    if direction == BULL:
        return extreme < lv.price + tol if not lv.is_zone else extreme <= lv.top + tol
    return extreme > lv.price - tol if not lv.is_zone else extreme >= lv.bottom - tol


def distance(lv: KeyLevel, ref: float) -> float:
    if lv.bottom <= ref <= lv.top:
        return 0.0
    return min(abs(ref - lv.top), abs(ref - lv.bottom))


def score_and_select(cands: list[KeyLevel], *, direction: str, swept_extreme: float, purge_extreme: float,
                     atr_htf: float, atr_ltf: float, eq: float | None, kl_bars_low: float | None,
                     kl_bars_high: float | None, cfg: StrategyConfig) -> tuple[KeyLevel | None, list[KeyLevel]]:
    """Filter candidates the purge reached within ``kl_max_dist_atr x ATR(htf)``
    of the CRT extreme, score them (G-01 proxy) and pick one (``kl_select``).
    Returns (chosen, all_scored_reached)."""
    k = cfg.key_level
    tol = k.kl_touch_tol * (atr_ltf if np.isfinite(atr_ltf) else 0.0)
    maxd = k.kl_max_dist_atr * atr_htf if np.isfinite(atr_htf) else np.inf
    ok = [lv for lv in cands if reached(lv, purge_extreme, direction, tol) and distance(lv, swept_extreme) <= maxd]
    scored: list[KeyLevel] = []
    conf_tol = 0.1 * atr_htf if np.isfinite(atr_htf) else 0.0
    for lv in ok:
        s = 1.0                                   # unswept / untouched (all candidates are)
        s += 1.0 if lv.primary_tf else 0.0        # on the CRT-R22 TF
        if any(o is not lv and (distance(o, lv.price) <= conf_tol) for o in ok):
            s += 1.0                              # confluence with another candidate
        if eq is not None:
            s += 1.0 if (lv.price < eq if direction == BULL else lv.price > eq) else 0.0
        vis = kl_bars_low if direction == BULL else kl_bars_high
        if vis is not None and lv.kind in ("old_high", "old_low") and abs(lv.price - vis) < 1e-12:
            s += 1.0                              # most visible (G-17 proxy: extreme of the lookback)
        if lv.is_bos_origin:
            s += k.kl_score_bos_bonus
        scored.append(KeyLevel(lv.kind, lv.tf, lv.side, lv.top, lv.bottom, lv.known_ns, s, lv.is_bos_origin,
                               lv.primary_tf))
    if not scored:
        return None, []
    if k.kl_select == "nearest":
        best = min(scored, key=lambda lv: (distance(lv, swept_extreme), -lv.score))
    else:
        best = max(scored, key=lambda lv: (lv.score, -distance(lv, swept_extreme)))
    return best, scored


def atr_last(b: Bars, n: int) -> float:
    if len(b) < n:
        return float("nan")
    a = atr(b.tail(max(3 * n, 50)).df(), n)
    return float(a[-1])
