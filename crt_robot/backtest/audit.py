"""Look-ahead audit.

The MTF API cannot hand out future bars, but a strategy could still cheat
by reaching around it (private attributes, precomputing on the full frame,
global state). The audit catches that: decisions made on the full data must
be identical to decisions made on data cut at each checkpoint. Any decision
that changes when the future is removed used the future.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd

from crt_robot.backtest.engine import Backtester, EngineConfig, Strategy
from crt_robot.data.instruments import Instrument


class LookAheadDetected(AssertionError):
    pass


def lookahead_audit(strategy_factory: Callable[[], Strategy], base: pd.DataFrame, inst: Instrument,
                    htfs: tuple[str, ...] = ("15m", "1H", "4H", "D", "W"), n_checks: int = 6, seed: int = 0,
                    config: EngineConfig | None = None, checkpoints: list[int] | None = None) -> list[int]:
    """Raise :class:`LookAheadDetected` on the first mismatch; return the
    checkpoints tested."""
    full = Backtester(base, inst, htfs, config=config).run(strategy_factory(), log=False)
    full_dec = full.decisions
    if checkpoints is None:
        rng = np.random.default_rng(seed)
        lo = min(len(base) - 1, 200)
        checkpoints = sorted({int(x) for x in rng.integers(lo, len(base) - 1, n_checks)})
        # always test right after decision bars too: that is where cheats show
        dec_bars = [i for i, _ in full_dec if i >= lo]
        if dec_bars:
            checkpoints = sorted(set(checkpoints) | set(rng.choice(dec_bars, min(n_checks, len(dec_bars)),
                                                                     replace=False).tolist()))
    for k in checkpoints:
        cut = Backtester(base.iloc[: k + 1], inst, htfs, config=config).run(strategy_factory(), log=False)
        expected = [d for d in full_dec if d[0] <= k]
        if cut.decisions != expected:
            first = next((a, b) for a, b in zip(cut.decisions + [None] * len(expected), expected + [None] * len(cut.decisions)) if a != b)
            raise LookAheadDetected(f"decisions differ when data is cut at bar {k}: truncated={first[0]} full={first[1]}")
    return checkpoints
