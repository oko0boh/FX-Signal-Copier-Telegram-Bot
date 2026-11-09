"""Tuning period vs LOCKED holdout (BUILD_PLAN 3.2).

Any code path that runs a backtest calls :meth:`DataSplit.guard`. It raises
:class:`HoldoutLockedError` if the data reaches into the holdout and the
caller did not pass ``allow_holdout=True``.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from crt_robot.config import CONFIG_DIR

SPLIT_FILE = CONFIG_DIR / "data_split.toml"


class HoldoutLockedError(PermissionError):
    pass


@dataclass(frozen=True)
class DataSplit:
    data_start: pd.Timestamp
    holdout_start: pd.Timestamp
    holdout_months: int
    locked_on: str

    @classmethod
    def load(cls, path: Path = SPLIT_FILE) -> "DataSplit":
        with open(path, "rb") as fh:
            s = tomllib.load(fh)["split"]
        return cls(pd.Timestamp(s["data_start"], tz="UTC"), pd.Timestamp(s["holdout_start"], tz="UTC"),
                   int(s["holdout_months"]), str(s["locked_on"]))

    def touches_holdout(self, index: pd.DatetimeIndex) -> bool:
        return len(index) > 0 and pd.DatetimeIndex(index).max() >= self.holdout_start

    def guard(self, index: pd.DatetimeIndex, allow_holdout: bool = False) -> bool:
        """Return True if this run uses holdout data; raise unless allowed."""
        uses = self.touches_holdout(index)
        if uses and not allow_holdout:
            raise HoldoutLockedError(
                f"data reaches the locked holdout (>= {self.holdout_start.date()}). "
                "Use DataSplit.tuning() or pass allow_holdout=True for the single final run."
            )
        return uses

    def tuning(self, df: pd.DataFrame) -> pd.DataFrame:
        idx = pd.DatetimeIndex(df.index)
        return df[(idx >= self.data_start) & (idx < self.holdout_start)]

    def holdout(self, df: pd.DataFrame, allow_holdout: bool = False) -> pd.DataFrame:
        if not allow_holdout:
            raise HoldoutLockedError("holdout slice requested without allow_holdout=True")
        return df[pd.DatetimeIndex(df.index) >= self.holdout_start]
