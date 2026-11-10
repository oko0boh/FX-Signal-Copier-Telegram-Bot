"""Intrabar fill rules. Prices in the data are BID; ask = bid + spread.

Longs buy at the ask and sell at the bid; shorts the reverse. Assumptions
are CONSERVATIVE, because the path inside a bar is unknown:

* market entry: next bar open, plus adverse slippage.
* limit entry: fills when the bar trades through the price, at the price
  (or the open, if that is better). No slippage.
* stop entry: fills at the price (or a worse open), plus slippage.
* a stop and a target in the same bar: the STOP fills.
* on the entry bar of a limit/stop order the target is ignored, but the
  stop is not: if the bar reaches the stop, the trade is stopped.
* a gap through the stop fills at the (worse) open, plus slippage.
"""

from __future__ import annotations

from dataclasses import dataclass

from crt_robot.backtest.orders import LONG, Order, Position


@dataclass(frozen=True)
class BarPrices:
    o: float
    h: float
    l: float
    c: float
    spread: float

    @property
    def ask_o(self) -> float:
        return self.o + self.spread

    @property
    def ask_h(self) -> float:
        return self.h + self.spread

    @property
    def ask_l(self) -> float:
        return self.l + self.spread

    @property
    def ask_c(self) -> float:
        return self.c + self.spread


def entry_fill(order: Order, bar: BarPrices, slippage: float) -> float | None:
    """Fill price for a pending entry on this bar, or None if not filled."""
    long = order.side == LONG
    if order.kind == "market":
        return bar.ask_o + slippage if long else bar.o - slippage
    p = order.price
    assert p is not None
    if order.kind == "limit":
        if long:
            return min(p, bar.ask_o) if bar.ask_l <= p else None
        return max(p, bar.o) if bar.h >= p else None
    # stop entry
    if long:
        return max(p, bar.ask_o) + slippage if bar.ask_h >= p else None
    return min(p, bar.o) - slippage if bar.l <= p else None


def exit_fill(pos: Position, bar: BarPrices, slippage: float, entry_bar: bool) -> tuple[float, str] | None:
    """(price, reason) if the stop or target is hit on this bar."""
    long = pos.side == LONG
    if long:
        stop_hit = bar.l <= pos.stop
        stop_px = (pos.stop if entry_bar else min(pos.stop, bar.o)) - slippage
        tgt_hit = pos.target is not None and bar.h >= pos.target
    else:
        stop_hit = bar.ask_h >= pos.stop
        stop_px = (pos.stop if entry_bar else max(pos.stop, bar.ask_o)) + slippage
        tgt_hit = pos.target is not None and bar.ask_l <= pos.target
    if stop_hit:
        return stop_px, "stop"
    if tgt_hit and not (entry_bar and pos.entry_kind != "market"):
        return float(pos.target), "target"
    return None


def market_exit(pos: Position, price_bid: float, spread: float, slippage: float) -> float:
    """Close at market given the bid: longs sell the bid, shorts buy the ask."""
    return price_bid - slippage if pos.side == LONG else price_bid + spread + slippage


def mark(pos: Position, bar: BarPrices) -> float:
    """Exit-side price used for mark-to-market at the bar close."""
    return bar.c if pos.side == LONG else bar.ask_c


def tp1_fill(pos: Position, bar: BarPrices, entry_bar: bool) -> float | None:
    """Price of the partial take-profit if ``tp1`` trades on this bar. Like the
    final target it is ignored on the entry bar of a limit/stop order, and the
    caller checks the stop first (a bar that hits both stops out)."""
    if pos.tp1 is None or pos.tp1_done or (entry_bar and pos.entry_kind != "market"):
        return None
    if pos.side == LONG:
        return float(pos.tp1) if bar.h >= pos.tp1 else None
    return float(pos.tp1) if bar.ask_l <= pos.tp1 else None
