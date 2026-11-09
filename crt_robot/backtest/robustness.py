"""Robustness tools: Monte Carlo of trade order and cost-stress reruns."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Any

import numpy as np
import pandas as pd

from crt_robot.backtest.engine import Backtester, Strategy
from crt_robot.backtest.metrics import max_drawdown, summarize


def monte_carlo_trade_order(r: np.ndarray, risk_frac: float = 0.01, n_sims: int = 2000, seed: int = 0,
                            bootstrap: bool = False) -> dict[str, Any]:
    """Re-order (or bootstrap) the trade R-multiples and compound each path
    at ``risk_frac`` per trade. Shows how much the drawdown depends on luck
    of ordering. Final equity is order-independent under permutation, so
    ``bootstrap=True`` also varies the outcome."""
    r = np.asarray(r, dtype=float)
    r = r[~np.isnan(r)]
    if len(r) == 0:
        raise ValueError("no trades")
    rng = np.random.default_rng(seed)
    dds, finals, losing_streaks = np.empty(n_sims), np.empty(n_sims), np.empty(n_sims)
    for k in range(n_sims):
        path = rng.choice(r, size=len(r), replace=True) if bootstrap else rng.permutation(r)
        eq = np.concatenate([[1.0], np.cumprod(1 + path * risk_frac)])
        dds[k], finals[k] = max_drawdown(eq), eq[-1]
        neg = path < 0
        best = cur = 0
        for x in neg:
            cur = cur + 1 if x else 0
            best = max(best, cur)
        losing_streaks[k] = best
    q = [5, 50, 95, 99]
    return {
        "n_trades": len(r), "n_sims": n_sims, "bootstrap": bootstrap,
        "max_dd_pct": dict(zip([f"p{x}" for x in q], np.percentile(dds, q) * 100)),
        "final_equity_x": dict(zip([f"p{x}" for x in q], np.percentile(finals, q))),
        "max_losing_streak": dict(zip([f"p{x}" for x in q], np.percentile(losing_streaks, q))),
        "prob_loss": float((finals < 1).mean()),
    }


def cost_stress(bt: Backtester, strategy_factory: Callable[[], Strategy], multipliers=(1.0, 2.0),
                params: dict | None = None) -> pd.DataFrame:
    """Rerun the same strategy with costs scaled (BUILD_PLAN: rerun at 2x).
    A fresh strategy instance is used for every run."""
    rows = []
    base_cfg = bt.config
    try:
        for m in multipliers:
            bt.config = replace(base_cfg, cost_multiplier=m)
            res = bt.run(strategy_factory(), params={**(params or {}), "cost_multiplier": m})
            rows.append({"cost_multiplier": m, **{k: v for k, v in summarize(res).items() if k != "exit_reasons"}})
    finally:
        bt.config = base_cfg
    return pd.DataFrame(rows).set_index("cost_multiplier")
