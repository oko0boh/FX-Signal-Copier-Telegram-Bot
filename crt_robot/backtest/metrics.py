"""Performance summary of a backtest run."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def max_drawdown(equity: pd.Series | np.ndarray) -> float:
    """Largest peak-to-trough fall as a positive fraction."""
    e = np.asarray(equity, dtype=float)
    if len(e) == 0:
        return 0.0
    peak = np.maximum.accumulate(e)
    return float(np.max((peak - e) / peak))


def r_stats(r: np.ndarray) -> dict[str, float]:
    r = np.asarray(r, dtype=float)
    r = r[~np.isnan(r)]
    n = len(r)
    if n == 0:
        return {"n": 0, "mean_r": 0.0, "std_r": 0.0, "t_stat": 0.0, "win_rate": 0.0, "profit_factor": 0.0}
    sd = float(r.std(ddof=1)) if n > 1 else 0.0
    wins, losses = r[r > 0].sum(), -r[r < 0].sum()
    return {
        "n": n, "mean_r": float(r.mean()), "std_r": sd,
        "t_stat": float(r.mean() / (sd / np.sqrt(n))) if sd > 0 else 0.0,
        "win_rate": float((r > 0).mean()),
        "profit_factor": float(wins / losses) if losses > 0 else float("inf"),
    }


def summarize(result: Any) -> dict[str, Any]:
    t: pd.DataFrame = result.trades
    eq: pd.Series = result.equity
    out = r_stats(t["r"].to_numpy() if len(t) else np.array([]))
    start = result.config.initial_equity
    out.update({
        "net_pnl": float(t["pnl"].sum()) if len(t) else 0.0,
        "return_pct": float((eq.iloc[-1] / start - 1) * 100) if len(eq) else 0.0,
        "max_dd_pct": max_drawdown(np.concatenate([[start], eq.to_numpy()])) * 100 if len(eq) else 0.0,
        "daily_stop_days": len(result.daily_stop_days),
        "exit_reasons": t["reason"].value_counts().to_dict() if len(t) else {},
    })
    return out
