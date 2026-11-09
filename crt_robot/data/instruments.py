"""Instrument specifications (contract size, tick, Dukascopy scaling, costs).

Costs are PROPOSED starting values for a typical ECN MT5 account; they are
parameters, not measurements. Re-check them against the real MetaAPI/MT5
symbol specification before trusting a backtest.
"""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Instrument:
    symbol: str
    dukascopy_symbol: str
    point_divisor: float        # Dukascopy integer price / divisor = price
    pip: float                  # pip size in price units
    contract_size: float        # units per 1.0 lot
    tradeable: bool             # False = data only (SMT comparison)
    spread: float               # typical spread, price units (PROPOSED)
    commission_per_lot: float   # USD per lot, round turn (PROPOSED)
    slippage: float             # adverse slippage on market/stop fills, price units (PROPOSED)
    lot_step: float = 0.01
    min_lot: float = 0.01

    @property
    def tick(self) -> float:
        return 1.0 / self.point_divisor

    def with_cost_multiplier(self, k: float) -> "Instrument":
        """Same instrument with spread, commission and slippage scaled by ``k``."""
        return replace(
            self,
            spread=self.spread * k,
            commission_per_lot=self.commission_per_lot * k,
            slippage=self.slippage * k,
        )


INSTRUMENTS: dict[str, Instrument] = {
    "EURUSD": Instrument("EURUSD", "EURUSD", 1e5, 0.0001, 100_000, True,
                         spread=0.00008, commission_per_lot=7.0, slippage=0.00002),
    "GBPUSD": Instrument("GBPUSD", "GBPUSD", 1e5, 0.0001, 100_000, True,
                         spread=0.00012, commission_per_lot=7.0, slippage=0.00003),
    "XAUUSD": Instrument("XAUUSD", "XAUUSD", 1e3, 0.1, 100, True,
                         spread=0.25, commission_per_lot=7.0, slippage=0.10),
    "XAGUSD": Instrument("XAGUSD", "XAGUSD", 1e3, 0.01, 5_000, False,
                         spread=0.03, commission_per_lot=7.0, slippage=0.01),
    # Dukascopy's dollar-index CFD. Symbol name and divisor are UNVERIFIED
    # (the data host could not be reached in phase 1); check before use.
    "DXY": Instrument("DXY", "DOLLARIDXUSD", 1e3, 0.01, 1, False,
                      spread=0.03, commission_per_lot=0.0, slippage=0.01),
}

TRADEABLE = [s for s, i in INSTRUMENTS.items() if i.tradeable]


def get_instrument(symbol: str) -> Instrument:
    try:
        return INSTRUMENTS[symbol.upper()]
    except KeyError as exc:
        raise KeyError(f"unknown instrument {symbol!r}; known: {sorted(INSTRUMENTS)}") from exc
