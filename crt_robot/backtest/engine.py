"""Event-driven, bar-by-bar backtester on the lower timeframe.

Loop for each base bar i:
  1. fills: pending entries, time exits, stops/targets of the open position
     (rules in :mod:`crt_robot.backtest.fills`);
  2. mark to market at the close; the -2% NY daily stop may flatten and block;
  3. the strategy sees ``view.at(i)`` (closed HTF bars + forming bar only)
     and returns actions, which execute from bar i+1.

Every run is checked against the locked holdout and logged to the runs log.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

import numpy as np
import pandas as pd

from crt_robot.backtest import runlog
from crt_robot.backtest.fills import BarPrices, entry_fill, exit_fill, mark, market_exit
from crt_robot.backtest.orders import CancelPending, ClosePosition, Order, Position, StrategyState
from crt_robot.backtest.splits import DataSplit, HoldoutLockedError
from crt_robot.data.instruments import Instrument
from crt_robot.data.mtf import MultiTimeframeView, Snapshot
from crt_robot.risk.daily_stop import DailyLossGuard
from crt_robot.risk.sizing import lots_for_risk

Action = Order | ClosePosition | CancelPending


class Strategy(Protocol):
    name: str

    def on_bar(self, snap: Snapshot, state: StrategyState) -> list[Action]: ...


@dataclass
class EngineConfig:
    initial_equity: float = 10_000.0
    risk_frac: float = 0.01
    daily_limit: float = 0.02
    cost_multiplier: float = 1.0
    use_data_spread: bool = False
    max_trades_per_day: int | None = None
    allow_holdout: bool = False


@dataclass
class BacktestResult:
    strategy: str
    instrument: str
    config: EngineConfig
    trades: pd.DataFrame
    equity: pd.Series
    decisions: list[tuple[int, tuple]]
    daily_stop_days: list
    run_id: str | None = None
    params: dict[str, Any] = field(default_factory=dict)


TRADE_COLUMNS = ["entry_time", "exit_time", "side", "entry", "exit", "stop", "target", "lots",
                 "risk_usd", "pnl", "r", "reason", "tag", "entry_kind", "commission"]


class Backtester:
    def __init__(self, base: pd.DataFrame, instrument: Instrument,
                 htfs: tuple[str, ...] = ("15m", "1H", "4H", "D", "W"),
                 base_len: pd.Timedelta = pd.Timedelta(minutes=1),
                 config: EngineConfig | None = None, split: DataSplit | None = None,
                 view: MultiTimeframeView | None = None):
        self.config = config or EngineConfig()
        self.split = split or DataSplit.load()
        self.uses_holdout = self.split.guard(pd.DatetimeIndex(base.index), self.config.allow_holdout)
        if not instrument.tradeable:
            raise ValueError(f"{instrument.symbol} is data-only; it cannot be traded")
        self.base = base
        self.inst = instrument
        self.view = view or MultiTimeframeView(base, [t for t in htfs if t != _tf_name(base_len)], base_len)
        self.htfs = htfs
        self.base_len = base_len

    def _costs(self) -> tuple[Instrument, np.ndarray]:
        m = self.config.cost_multiplier
        inst = self.inst.with_cost_multiplier(m)
        if self.config.use_data_spread and "ask_close" in self.base:
            spread = np.maximum(self.base["ask_close"].to_numpy() - self.base["close"].to_numpy(), 0.0) * m
        else:
            spread = np.full(len(self.base), inst.spread)
        return inst, spread

    def run(self, strategy: Strategy, params: dict[str, Any] | None = None, log: bool = True) -> BacktestResult:
        cfg = self.config
        if self.uses_holdout and not cfg.allow_holdout:
            raise HoldoutLockedError("holdout data without allow_holdout")
        inst, spread = self._costs()
        slip = inst.slippage
        o, h, l, c = (self.base[k].to_numpy(dtype=float) for k in ("open", "high", "low", "close"))
        idx = pd.DatetimeIndex(self.base.index)
        now = idx + self.base_len
        guard = DailyLossGuard(cfg.daily_limit)

        equity = cfg.initial_equity
        pos: Position | None = None
        pending: list[Order] = []
        close_next = False
        trades: list[dict[str, Any]] = []
        eq_curve = np.empty(len(idx))
        decisions: list[tuple[int, tuple]] = []
        trades_today: dict[Any, int] = {}

        def close(p: Position, i: int, price: float, reason: str) -> None:
            nonlocal equity
            commission = inst.commission_per_lot * p.lots
            pnl = (price - p.entry) * p.side * p.lots * inst.contract_size - commission
            equity += pnl
            trades.append(dict(entry_time=p.entry_time, exit_time=now[i], side=p.side, entry=p.entry,
                               exit=price, stop=p.stop, target=p.target, lots=p.lots, risk_usd=p.risk_usd,
                               pnl=pnl, r=pnl / p.risk_usd if p.risk_usd else np.nan, reason=reason,
                               tag=p.tag, entry_kind=p.entry_kind, commission=commission))

        for i in range(len(idx)):
            bar = BarPrices(o[i], h[i], l[i], c[i], spread[i])
            # ---- 1a. forced close requested last bar / time exit at open
            if pos is not None and (close_next or (pos.exit_at is not None and idx[i] >= pos.exit_at)):
                close(pos, i, market_exit(pos, bar.o, bar.spread, slip),
                      "strategy_close" if close_next else "time_exit")
                pos = None
            close_next = False
            # ---- 1b. existing position: stop/target
            if pos is not None:
                hit = exit_fill(pos, bar, slip, entry_bar=False)
                if hit:
                    close(pos, i, hit[0], hit[1])
                    pos = None
            # ---- 1c. pending entries (only when flat)
            if pos is None and pending:
                keep: list[Order] = []
                for od in pending:
                    if od.expiry is not None and idx[i] >= od.expiry:
                        continue
                    if pos is not None:
                        continue  # one position at a time; others are dropped once filled
                    px = entry_fill(od, bar, slip)
                    if px is None:
                        keep.append(od)
                        continue
                    if (od.stop - px) * od.side >= 0:   # gapped through the stop: skip
                        continue
                    lots = lots_for_risk(equity, px, od.stop, inst, cfg.risk_frac)
                    if lots <= 0:
                        continue
                    risk = abs(px - od.stop) * inst.contract_size * lots + inst.commission_per_lot * lots
                    pos = Position(od.side, idx[i], i, px, od.stop, od.target, lots, risk, od.kind, od.exit_at, od.tag)
                    day = guard.ny_day(idx[i])
                    trades_today[day] = trades_today.get(day, 0) + 1
                    hit = exit_fill(pos, bar, slip, entry_bar=True)
                    if hit:
                        close(pos, i, hit[0], hit[1])
                        pos = None
                pending = keep if pos is None else []
            # ---- 2. mark to market and the daily stop
            mtm = equity
            if pos is not None:
                mtm += (mark(pos, bar) - pos.entry) * pos.side * pos.lots * inst.contract_size
            if guard.update(now[i], mtm) and pos is not None:
                close(pos, i, market_exit(pos, bar.c, bar.spread, slip), "daily_stop")
                pos = None
                mtm = equity
            if guard.blocked:
                pending = []
            eq_curve[i] = mtm
            # ---- 3. strategy decision at the close of bar i
            day = guard.ny_day(now[i])
            can_trade = guard.can_trade(now[i]) and (
                cfg.max_trades_per_day is None or trades_today.get(day, 0) < cfg.max_trades_per_day)
            state = StrategyState(equity=mtm, position=pos, pending=tuple(pending), can_trade=can_trade,
                                  trades_today=trades_today.get(day, 0))
            actions = strategy.on_bar(self.view.at(i), state) or []
            if actions:
                decisions.append((i, tuple(actions)))
            for a in actions:
                if isinstance(a, ClosePosition):
                    close_next = pos is not None
                elif isinstance(a, CancelPending):
                    pending = []
                elif isinstance(a, Order):
                    if can_trade and pos is None:
                        pending.append(a)
                else:
                    raise TypeError(f"unknown action {a!r}")

        if pos is not None:  # close at the last bar for reporting
            last = len(idx) - 1
            close(pos, last, market_exit(pos, c[last], spread[last], slip), "end_of_data")
            eq_curve[last] = equity

        tdf = pd.DataFrame(trades, columns=TRADE_COLUMNS)
        result = BacktestResult(getattr(strategy, "name", type(strategy).__name__), self.inst.symbol, cfg, tdf,
                                pd.Series(eq_curve, index=idx, name="equity"), decisions, guard.hits,
                                params=dict(params or {}))
        if log:
            from crt_robot.backtest.metrics import summarize
            result.run_id = runlog.log_run({
                "strategy": result.strategy, "instrument": self.inst.symbol, "params": result.params,
                "config": vars(cfg), "start": idx[0], "end": idx[-1], "uses_holdout": self.uses_holdout,
                "summary": summarize(result),
            })
        return result


def _tf_name(base_len: pd.Timedelta) -> str:
    return {pd.Timedelta(minutes=1): "1m", pd.Timedelta(minutes=5): "5m", pd.Timedelta(minutes=15): "15m",
            pd.Timedelta(hours=1): "1H"}.get(base_len, "")
