"""Position sizing at a fixed fraction of equity (CRT-R62: 1% per trade).

Account currency is USD and every instrument is quoted in USD, so one lot
moves ``contract_size`` USD per 1.0 of price.
"""

from __future__ import annotations

import math

from crt_robot.data.instruments import Instrument

DEFAULT_RISK = 0.01


def lots_for_risk(equity: float, entry: float, stop: float, inst: Instrument,
                  risk_frac: float = DEFAULT_RISK, include_commission: bool = True) -> float:
    """Largest lot size (rounded DOWN to the lot step) whose loss at the stop
    is at most ``risk_frac * equity``. Returns 0.0 if even the minimum lot
    would risk more, so the trade must be skipped."""
    if equity <= 0 or risk_frac <= 0:
        return 0.0
    dist = abs(entry - stop)
    if dist <= 0:
        raise ValueError("stop must differ from entry")
    per_lot = dist * inst.contract_size + (inst.commission_per_lot if include_commission else 0.0)
    raw = equity * risk_frac / per_lot
    lots = math.floor(raw / inst.lot_step + 1e-9) * inst.lot_step
    lots = round(lots, 8)
    return lots if lots >= inst.min_lot else 0.0


def risk_amount(lots: float, entry: float, stop: float, inst: Instrument) -> float:
    return abs(entry - stop) * inst.contract_size * lots
