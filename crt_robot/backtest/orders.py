"""Order and position types used between strategies and the engine."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

LONG, SHORT = 1, -1
ENTRY_KINDS = ("market", "limit", "stop")


@dataclass(frozen=True)
class Order:
    """Entry order with a protective stop and optional target.

    Decided at the close of bar i; it can fill from bar i+1 onward.
    ``market`` fills at the next bar's open. ``limit``/``stop`` wait at
    ``price`` until ``expiry`` (UTC; None = good till cancelled).
    ``exit_at`` closes the trade at the first bar opening at or after it.
    """

    side: int
    stop: float
    target: float | None = None
    kind: str = "market"
    price: float | None = None
    expiry: pd.Timestamp | None = None
    exit_at: pd.Timestamp | None = None
    tag: str = ""
    tp1: float | None = None          # partial take-profit level (CRT-R53 TP1)
    tp1_fraction: float = 0.0         # share of the lots closed at tp1

    def __post_init__(self):
        if self.side not in (LONG, SHORT):
            raise ValueError("side must be +1 or -1")
        if self.kind not in ENTRY_KINDS:
            raise ValueError(f"kind must be one of {ENTRY_KINDS}")
        if self.kind != "market" and self.price is None:
            raise ValueError(f"{self.kind} order needs a price")
        ref = self.price
        if ref is not None:
            if self.side == LONG and not self.stop < ref:
                raise ValueError("long stop must be below the entry price")
            if self.side == SHORT and not self.stop > ref:
                raise ValueError("short stop must be above the entry price")
            if self.target is not None and (self.target - ref) * self.side <= 0:
                raise ValueError("target must be on the profit side of the entry price")
            if self.tp1 is not None and (self.tp1 - ref) * self.side <= 0:
                raise ValueError("tp1 must be on the profit side of the entry price")
        if not 0.0 <= self.tp1_fraction < 1.0:
            raise ValueError("tp1_fraction must be in [0, 1)")
        if self.tp1 is not None and self.target is not None and (self.target - self.tp1) * self.side <= 0:
            raise ValueError("tp1 must lie between the entry and the final target")


@dataclass(frozen=True)
class ClosePosition:
    """Close the open position at the next bar's open."""
    reason: str = "strategy"


@dataclass(frozen=True)
class CancelPending:
    """Cancel all pending entry orders."""


@dataclass(frozen=True)
class ModifyStop:
    """Move the open position's stop (e.g. to break-even) from the next bar."""
    price: float
    reason: str = "strategy"


@dataclass
class Position:
    side: int
    entry_time: pd.Timestamp
    entry_idx: int
    entry: float
    stop: float
    target: float | None
    lots: float
    risk_usd: float
    entry_kind: str
    exit_at: pd.Timestamp | None
    tag: str = ""
    tp1: float | None = None
    tp1_fraction: float = 0.0
    tp1_done: bool = False
    realized_pnl: float = 0.0       # booked by the tp1 partial
    initial_lots: float = 0.0
    tp1_time: pd.Timestamp | None = None
    tp1_commission: float = 0.0


@dataclass
class StrategyState:
    """Read-only account state handed to the strategy each bar."""
    equity: float
    position: Position | None
    pending: tuple[Order, ...]
    can_trade: bool
    trades_today: int = 0
    extra: dict = field(default_factory=dict)
    entries_total: int = 0          # fills so far in this run (lets a strategy see a same-bar stop-out)
