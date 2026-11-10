"""Typed Setup objects with a full condition log.

Every rule the detector, the context layers and the entry models evaluate
is written to ``Setup.checks`` as a :class:`Check` with the rulebook rule
ID, a status and the measured value, so a report can say WHY a setup was
taken or rejected. Status values:

* ``pass`` / ``fail``: a hard gate (``fail`` rejects the setup);
* ``score``: a scoring factor (``value`` holds the points, 0 or more);
* ``info``: logged only (e.g. the 1/5/9 label, purge minute in the 4H);
* ``pending``: not decidable yet at decision time (e.g. a 4H purge candle
  that has not closed); never used by a decision.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import pandas as pd

BULL, BEAR = "bull", "bear"
STATUSES = ("pass", "fail", "score", "info", "pending")
STATES = ("candidate", "rejected", "armed", "entered", "expired", "invalidated", "done")


@dataclass(frozen=True)
class Check:
    rule: str          # rulebook ID, e.g. "CRT-R25", "G-20", "DEF-05"
    name: str          # short machine name, e.g. "c2_close_inside"
    status: str
    value: Any = None
    detail: str = ""

    def __post_init__(self):
        if self.status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}")


@dataclass(frozen=True)
class KeyLevel:
    kind: str          # old_high, old_low, bos_origin_hl, fvg, ob, rb, prev_period_hl, candle_open, weekly_wick_50
    tf: str
    side: str          # "high" (resistance, bear setups) or "low" (support, bull setups)
    top: float         # zone top (= price for a line level)
    bottom: float
    known_ns: int      # time the level was knowable (UTC ns)
    score: float = 0.0
    is_bos_origin: bool = False
    primary_tf: bool = True

    @property
    def is_zone(self) -> bool:
        return self.top != self.bottom

    @property
    def price(self) -> float:
        """The edge price reaches first from inside the CRT range."""
        return self.bottom if self.side == "high" else self.top


@dataclass
class Setup:
    id: str
    symbol: str
    mode: str
    htf: str
    ltf: str
    kl_tf: str
    parent_htf: str
    purpose: str                       # CRT-R01: bias | framing | trade
    direction: str                     # bull | bear
    detected_ns: int
    c1_open_ns: int
    c1_close_ns: int
    c1: dict
    crt_high: float
    crt_low: float
    c2_open_ns: int | None = None
    c2_close_ns: int | None = None
    c2: dict | None = None
    c2_class: str = ""
    c3_open_ns: int | None = None
    c3_close_ns: int | None = None
    c3_open: float | None = None
    inside_bars: int = 0
    sweep_extreme: float | None = None  # most extreme price of the purge (C2 wick / LTF purge)
    sweep_ns: int | None = None         # first LTF bar that traded beyond the CRT extreme
    key_level: KeyLevel | None = None
    kl_candidates: int = 0
    checks: list[Check] = field(default_factory=list)
    state: str = "candidate"
    invalid_reason: str = ""
    entry_kind: str = ""
    entry_ns: int | None = None
    entry_price: float | None = None
    stop: float | None = None
    tp1: float | None = None
    target: float | None = None
    order_kind: str = ""
    expiry_ns: int | None = None
    extra: dict = field(default_factory=dict)

    # ---- derived ------------------------------------------------------
    @property
    def crt_50(self) -> float:
        """DEF-03: midpoint of C1's full wick range."""
        return (self.crt_high + self.crt_low) / 2

    @property
    def side(self) -> int:
        return 1 if self.direction == BULL else -1

    @property
    def swept_extreme(self) -> float:
        """The C1 extreme the setup purges (CRT low for bull, high for bear)."""
        return self.crt_low if self.direction == BULL else self.crt_high

    @property
    def opposite_extreme(self) -> float:
        return self.crt_high if self.direction == BULL else self.crt_low

    # ---- logging ------------------------------------------------------
    def log(self, rule: str, name: str, status: str, value: Any = None, detail: str = "") -> Check:
        c = Check(rule, name, status, value, detail)
        self.checks.append(c)
        return c

    def gate(self, rule: str, name: str, ok: bool, value: Any = None, detail: str = "") -> bool:
        self.log(rule, name, "pass" if ok else "fail", value, detail)
        return ok

    def reject(self, reason: str) -> None:
        if self.state in ("candidate", "armed"):
            self.state = "rejected" if self.state == "candidate" else "invalidated"
            self.invalid_reason = reason

    @property
    def failed(self) -> list[Check]:
        return [c for c in self.checks if c.status == "fail"]

    @property
    def score(self) -> float:
        return float(sum(c.value or 0 for c in self.checks if c.status == "score"))

    def check(self, name: str) -> Check | None:
        for c in reversed(self.checks):
            if c.name == name:
                return c
        return None

    def to_row(self) -> dict[str, Any]:
        """Flat record for the setups CSV."""
        from crt_robot.crt.bars import ny
        sweep_t = ny(self.sweep_ns) if self.sweep_ns is not None else None
        row = {
            "id": self.id, "symbol": self.symbol, "mode": self.mode, "htf": self.htf, "ltf": self.ltf,
            "kl_tf": self.kl_tf, "direction": self.direction, "state": self.state,
            "invalid_reason": self.invalid_reason,
            "detected_ny": ny(self.detected_ns), "c1_open_ny": ny(self.c1_open_ns),
            "c2_open_ny": ny(self.c2_open_ns) if self.c2_open_ns else None,
            "crt_high": self.crt_high, "crt_low": self.crt_low, "crt_50": self.crt_50,
            "c2_class": self.c2_class, "inside_bars": self.inside_bars,
            "sweep_ny": sweep_t, "sweep_weekday": sweep_t.day_name()[:3] if sweep_t is not None else "",
            "sweep_hour": sweep_t.hour if sweep_t is not None else None,
            "kl_kind": self.key_level.kind if self.key_level else "", "kl_tf_used": self.key_level.tf if self.key_level else "",
            "kl_score": self.key_level.score if self.key_level else None, "kl_candidates": self.kl_candidates,
            "score": self.score, "entry_kind": self.entry_kind,
            "entry_ny": ny(self.entry_ns) if self.entry_ns else None, "entry_price": self.entry_price,
            "stop": self.stop, "tp1": self.tp1, "target": self.target,
            "failed_checks": ";".join(f"{c.rule}:{c.name}" for c in self.failed),
            "checks": ";".join(f"{c.rule}:{c.name}={c.status}" + (f"({c.value})" if c.value is not None else "")
                               for c in self.checks),
        }
        for c in self.checks:
            if c.status == "info":
                row[f"info_{c.name}"] = c.value
        return row


def setups_frame(setups: list[Setup]) -> pd.DataFrame:
    return pd.DataFrame([s.to_row() for s in setups])


def check_dict(c: Check) -> dict:
    return asdict(c)
