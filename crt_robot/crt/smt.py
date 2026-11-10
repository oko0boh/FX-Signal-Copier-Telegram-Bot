"""SMT divergence (DEF-18, CRT-R42/R57, C-24) against data-only peers.

A :class:`PeerFeed` wraps a :class:`MultiTimeframeView` of a correlated
instrument (GBPUSD for EURUSD, DXY inverse, XAGUSD for XAUUSD). At decision
time ``now`` it hands out the peer snapshot of the latest peer bar that
closed at or before ``now``, so the peer can never leak the future.

Romeo's candle SMT: compare the SAME candle (same open time) on both
assets. Bull SMT at C2: our C2 took C1's low while the peer's C2 did not
take the peer C1's low (for an inverse peer: did not take its C1 high).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from crt_robot.crt.bars import Bars, MarketData
from crt_robot.crt.setup import BULL
from crt_robot.data.mtf import MultiTimeframeView


@dataclass
class PeerFeed:
    name: str
    view: MultiTimeframeView
    inverse: bool = False

    def snapshot_at(self, now_ns: int):
        nows = self.view._now                      # close times of peer base bars
        k = int(np.searchsorted(nows, now_ns, side="right")) - 1
        if k < 0:
            return None
        return self.view.at(k)


def peer_bars(peer: PeerFeed, now_ns: int, tf: str, cache: dict, daily_tf: str) -> Bars | None:
    snap = peer.snapshot_at(now_ns)
    if snap is None:
        return None
    md = MarketData(snap, cache, daily_tf)
    try:
        return md.bars(tf)
    except KeyError:
        return None


def _bar_at(b: Bars, open_ns: int) -> dict | None:
    k = int(np.searchsorted(b.open_time, open_ns, side="left"))
    if k < len(b) and b.open_time[k] == open_ns:
        return b.bar(k)
    return None


def candle_smt(direction: str, c1: dict, c2: dict, peer_b: Bars | None, inverse: bool, take: str = "wick") -> bool | None:
    """True if SMT in ``direction`` at C2, False if the peer confirmed (no
    divergence), None if the peer has no matching candles."""
    if peer_b is None:
        return None
    p1, p2 = _bar_at(peer_b, c1["open_time"]), _bar_at(peer_b, c2["open_time"])
    if p1 is None or p2 is None:
        return None

    def took_low(a, b):
        return (b["close"] < a["low"]) if take == "close" else (b["low"] < a["low"])

    def took_high(a, b):
        return (b["close"] > a["high"]) if take == "close" else (b["high"] > a["high"])

    if direction == BULL:
        ours = took_low(c1, c2)
        theirs = took_high(p1, p2) if inverse else took_low(p1, p2)
    else:
        ours = took_high(c1, c2)
        theirs = took_low(p1, p2) if inverse else took_high(p1, p2)
    return bool(ours and not theirs)
