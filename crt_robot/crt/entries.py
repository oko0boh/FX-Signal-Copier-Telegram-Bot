"""Entry models (rulebook group F) on the LTF, from closed bars only.

Every model is written for the BULL side; a bear setup is evaluated on
price-negated bars (high <-> -low), which is the exact mirror the rulebook
asks for, and the result is negated back.

* :func:`model1` CRT-R39 / DEF-08: the thick down-close candle M that swept
  the CRT low; trigger = a later close above ``ref(M)`` (wick high by
  default, body top as the variant). A trigger inside C2 is not an entry
  (CRT-R30); ``model1_c2_trigger=retest`` then waits for a limit at
  ``ref(M)`` in C3 (PROPOSED).
* :func:`mss_ote` CRT-R40/R41 / DEF-10/12: true MSS after the sweep (the
  lower low must reach the CRT low), activation by a close above the high
  that broke the low; entry on the retrace into the OTE zone of leg one
  (``ote_zone``, default 0.50-0.79, limit at the shallow edge) or anywhere
  in ``[L2, H]`` (``mss_entry_zone=full_retrace``, limit at H).
* :func:`sham_ob` CRT-R43/R47 / DEF-15: a 15m OB whose candle group holds
  the purge bar(s), engulfed after the purge; limit at the near edge (or
  open / mid), never in the premium part of the dealing range.
* :func:`ltf_crt_inside` G-20 confirmation: a LTF turtle soup of the CRT
  low inside C2.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from crt_robot.crt.bars import Bars
from crt_robot.crt.config import StrategyConfig
from crt_robot.crt.setup import BULL
from crt_robot.primitives.candles import atr
from crt_robot.primitives.liquidity import classify
from crt_robot.primitives.order_block import detect_order_blocks
from crt_robot.primitives.structure import detect_structure


@dataclass
class Signal:
    kind: str               # model1 | model1_retest | mss | ote | ob
    order: str              # market | limit
    price: float            # limit price, or the trigger close for a market order
    stop: float
    trigger_ns: int         # close time of the bar that produced the signal
    info: dict = field(default_factory=dict)


@dataclass
class EntryResult:
    signal: Signal | None
    status: str             # signal | waiting | fail
    detail: str = ""
    info: dict = field(default_factory=dict)


def flip(b: Bars) -> Bars:
    return Bars(b.tf, b.open_time, b.close_time, -b.open, -b.low, -b.high, -b.close)


def _orient(b: Bars, direction: str) -> tuple[Bars, float]:
    return (b, 1.0) if direction == BULL else (flip(b), -1.0)


def _unflip(sig: Signal | None, s: float) -> Signal | None:
    if sig is None or s == 1.0:
        return sig
    info = {k: (-v if isinstance(v, float) else v) for k, v in sig.info.items()}
    return Signal(sig.kind, sig.order, -sig.price, -sig.stop, sig.trigger_ns, info)


def _atr_series(b: Bars, n: int) -> np.ndarray:
    return atr(b.df(), n) if len(b) else np.empty(0)


# ---------------------------------------------------------------------------
# model #1
# ---------------------------------------------------------------------------

def model1(ltf_hist: Bars, direction: str, swept: float, c2_open_ns: int, c2_close_ns: int, now_ns: int,
           cfg: StrategyConfig, buffer: float) -> EntryResult:
    """``ltf_hist`` = closed LTF bars (with history before C2 for the ATR)."""
    e = cfg.entry
    b, s = _orient(ltf_hist, direction)
    lvl = swept * s
    a = _atr_series(b, cfg.general.atr_len)
    k0 = int(np.searchsorted(b.open_time, c2_open_ns, side="left"))
    if k0 >= len(b):
        return EntryResult(None, "waiting", "no LTF bars since C2 opened")
    idx = np.arange(k0, len(b))
    swept_m = b.low[idx] < lvl
    down = b.close[idx] < b.open[idx]
    rng = b.high[idx] - b.low[idx]
    body = b.open[idx] - b.close[idx]
    if e.require_thick:
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.where(rng > 0, body / rng, 0.0)
        av = np.nan_to_num(a[idx], nan=np.inf)
        thick = (ratio >= e.thick_body_ratio) & (rng >= e.thick_atr_mult * av)
    else:
        thick = np.ones(len(idx), bool)
    cand = idx[swept_m & down & thick]
    if len(cand) == 0:
        why = "no down-close LTF candle swept the CRT extreme" if not (swept_m & down).any() else \
            "sweep candle not thick (DEF-09)"
        return EntryResult(None, "waiting", why)
    m = int(cand[np.argmin(b.low[cand])])
    ref = b.high[m] if e.model1_trigger_ref == "wick" else max(b.open[m], b.close[m])
    stop = b.low[m] - buffer
    info = {"model_ns": int(b.open_time[m]), "model_low": float(b.low[m]), "ref": float(ref)}
    after = np.arange(m + 1, len(b))
    trig = after[b.close[after] > ref]
    if len(trig) == 0:
        return _with_info(EntryResult(None, "waiting", "model candle found, no close beyond it yet"), info, s)
    t = int(trig[0])
    t_close = int(b.close_time[t])
    info["trigger_ns"] = t_close
    if t_close <= c2_close_ns and not cfg.crt.allow_c2_entry:
        # trigger fired inside C2 (CRT-R30): wait for C3 and retest the model candle
        if cfg.crt.model1_c2_trigger == "skip":
            return _with_info(EntryResult(None, "fail", "model #1 triggered inside C2 (C2 entries off)"), info, s)
        if now_ns < c2_close_ns:
            return _with_info(EntryResult(None, "waiting", "model #1 triggered in C2; retest only in C3"), info, s)
        sig = Signal("model1_retest", "limit", float(ref), float(stop), int(c2_close_ns), dict(info))
        return _with_info(EntryResult(_unflip(sig, s), "signal", "limit at the model candle (retest in C3)"), info, s)
    if e.model1_entry == "close":
        sig = Signal("model1", "market", float(b.close[t]), float(stop), t_close, dict(info))
    else:
        sig = Signal("model1", "limit", float(ref), float(stop), t_close, dict(info))
    return _with_info(EntryResult(_unflip(sig, s), "signal", "close beyond the model candle"), info, s)


def _with_info(r: EntryResult, info: dict, s: float) -> EntryResult:
    r.info = {k: (v * s if isinstance(v, float) else v) for k, v in info.items()}
    return r


# ---------------------------------------------------------------------------
# true MSS / OTE
# ---------------------------------------------------------------------------

def mss_ote(ltf_hist: Bars, direction: str, swept: float, c2_open_ns: int, cfg: StrategyConfig,
            buffer: float, kind: str = "mss", tol: float = 0.0) -> EntryResult:
    e = cfg.entry
    b, s = _orient(ltf_hist, direction)
    lvl = swept * s
    k0 = int(np.searchsorted(b.open_time, c2_open_ns, side="left"))
    lo = max(0, k0 - e.mss_lookback_bars)
    w = b.slice(slice(lo, len(b)))
    if len(w) < 2 * cfg.general.swing_n + 3:
        return EntryResult(None, "waiting", "not enough LTF bars")
    st = detect_structure(w.df(), cfg.general.swing_n)
    c2_rel = k0 - lo
    ev = st[(st.kind == "mss_bull") & (st.idx >= c2_rel) & (st.extreme <= lvl + tol)]
    if ev.empty:
        bos = st[(st.kind == "bos_bull") & (st.idx >= c2_rel)]
        return EntryResult(None, "waiting", "no true MSS after the sweep" + (" (only a BOS)" if len(bos) else ""))
    m = ev.iloc[0]
    act = int(m.idx)
    l2 = float(m.extreme)
    h_level = float(m.level)
    a = _atr_series(w, cfg.general.atr_len)
    av = a[act] if np.isfinite(a[act]) else (w.high[act] - w.low[act])
    # leg one: highest high from the activation bar until the first bar whose
    # close retraces >= leg_end_atr x ATR from that high (G-14 proxy)
    leg_end, leg_idx, retrace_idx = w.high[act], act, None
    for j in range(act, len(w)):
        if w.high[j] > leg_end:
            leg_end, leg_idx = w.high[j], j
        if j > leg_idx and w.close[j] <= leg_end - e.leg_end_atr * av:
            retrace_idx = j
            break
    info = {"mss_ns": int(w.close_time[act]), "l2": l2, "h_broke_low": h_level, "leg_end": float(leg_end)}
    if retrace_idx is None:
        return _with_info(EntryResult(None, "waiting", "MSS activated, leg one still running"), info, s)
    if e.ote_fib_basis == "body":
        l2_idx = int(np.argmin(w.low[: act + 1]))
        origin = min(w.open[l2_idx], w.close[l2_idx])
        top = max(w.open[leg_idx], w.close[leg_idx])
    else:
        origin, top = l2, float(leg_end)
    span = top - origin
    if span <= 0:
        return _with_info(EntryResult(None, "fail", "degenerate leg"), info, s)
    if kind == "mss" and e.mss_entry_zone == "full_retrace":
        shallow, deep = h_level, l2
    else:
        z0, z1 = e.ote_zone
        shallow, deep = top - z0 * span, top - z1 * span
    info.update({"zone_shallow": float(shallow), "zone_deep": float(deep)})
    after = w.slice(slice(leg_idx + 1, len(w)))
    if len(after) and after.low.min() < deep:
        return _with_info(EntryResult(None, "fail", "retrace went through the deep edge of the zone"), info, s)
    if kind == "ote" and e.ote_stop == "fib_079":
        stop = top - 0.79 * span - buffer
    else:
        stop = l2 - buffer
    if stop >= shallow:
        return _with_info(EntryResult(None, "fail", "stop not below the entry zone"), info, s)
    sig = Signal(kind, "limit", float(shallow), float(stop), int(w.close_time[retrace_idx]), dict(info))
    return _with_info(EntryResult(_unflip(sig, s), "signal", "retrace into the entry zone"), info, s)


# ---------------------------------------------------------------------------
# Sham order block
# ---------------------------------------------------------------------------

def sham_ob(ltf_hist: Bars, direction: str, purge_level: float, purge_from_ns: int, cfg: StrategyConfig,
            buffer: float, key_time_fn, dr_eq: float | None = None) -> EntryResult:
    """``purge_level`` = the 4H CRT extreme (or key level) whose purge gives
    the OB its liquidity; only bars opening at/after ``purge_from_ns`` count
    as valid purges (CRT-R27)."""
    e = cfg.entry
    b, s = _orient(ltf_hist, direction)
    lvl = purge_level * s
    k0 = int(np.searchsorted(b.open_time, purge_from_ns, side="left"))
    if k0 >= len(b):
        return EntryResult(None, "waiting", "no LTF bars after the CRT candle")
    liq = np.zeros(len(b), bool)
    liq[k0:] = b.low[k0:] < lvl
    if not liq.any():
        return EntryResult(None, "waiting", "no purge yet")
    first = int(np.argmax(liq))
    lo = max(0, first - e.ob_max_candles)
    w = b.slice(slice(lo, len(b)))
    kt = np.array([key_time_fn(int(t)) for t in w.open_time])
    obs = detect_order_blocks(w.df(), liq[lo:], max_candles=e.ob_max_candles, key_time=kt)
    obs = obs[(obs.kind == "bull") & (obs.engulf_idx >= first - lo)]
    if obs.empty:
        return EntryResult(None, "waiting", "purge seen, no 15m OB yet", {"purge_ns": int(b.open_time[first])})
    ob = obs.iloc[0]
    eng = int(ob.engulf_idx)
    info = {"purge_ns": int(b.open_time[first]), "ob_top": float(ob.top), "ob_bottom": float(ob.bottom),
            "engulf_ns": int(w.close_time[eng]), "ob_in_key_time": bool(ob.in_key_time)}
    if cfg.timing.require_timed_entry and not ob.in_key_time:
        return _with_info(EntryResult(None, "fail", "OB engulf outside key time (CRT-R33)"), info, s)
    top, bottom = float(ob.top), float(ob.bottom)
    if e.ob_entry_edge == "near_edge":
        px = top
    elif e.ob_entry_edge == "mid":
        px = (top + bottom) / 2
    else:  # open of the last OB candle (a down-close candle's open = its body top)
        last = int(ob.last_idx)
        px = float(max(w.open[last], w.close[last]))
    if dr_eq is not None:
        eq = dr_eq * s
        if bottom > eq:
            return _with_info(EntryResult(None, "fail", "whole OB in premium of the dealing range (CRT-R47)"), info, s)
        px = min(px, eq)
    stop = bottom - buffer
    if stop >= px:
        return _with_info(EntryResult(None, "fail", "degenerate OB"), info, s)
    sig = Signal("ob", "limit", float(px), float(stop), int(w.close_time[eng]), dict(info))
    return _with_info(EntryResult(_unflip(sig, s), "signal", "15m OB after a purge"), info, s)


# ---------------------------------------------------------------------------
# confirmations
# ---------------------------------------------------------------------------

def ltf_crt_inside(ltf: Bars, direction: str, swept: float, c2_open_ns: int, c2_close_ns: int) -> bool:
    """G-20: a LTF CRT (turtle soup of the previous LTF candle) inside C2 whose
    sweep traded beyond the HTF CRT extreme."""
    b, s = _orient(ltf, direction)
    lvl = swept * s
    w = b.between(c2_open_ns, c2_close_ns)
    for j in range(1, len(w)):
        if w.low[j] >= lvl:
            continue
        out = classify(w.bar(j - 1), w.bar(j))
        if out.kind == "ts_low":
            return True
    return False
