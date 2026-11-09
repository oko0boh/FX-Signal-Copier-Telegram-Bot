"""Data quality checks for 1-minute bars: gaps, duplicates, weekend bars,
spikes, OHLC consistency and negative spreads."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from crt_robot.timeutil import NY_TZ


@dataclass
class QualityReport:
    rows: int
    start: pd.Timestamp | None
    end: pd.Timestamp | None
    duplicates: int
    unsorted: int
    weekend_bars: int
    bad_ohlc: int
    negative_spread: int
    spikes: pd.DataFrame
    gaps: pd.DataFrame
    gap_minutes_total: int
    coverage_by_year: dict[int, float] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not (self.duplicates or self.unsorted or self.bad_ohlc or self.negative_spread)


def in_fx_week(idx: pd.DatetimeIndex) -> np.ndarray:
    """True where a UTC stamp falls in Sun 17:00 NY .. Fri 17:00 NY."""
    ny = idx.tz_convert(NY_TZ)
    dow, hour = ny.day_of_week, ny.hour
    closed = (dow == 5) | ((dow == 4) & (hour >= 17)) | ((dow == 6) & (hour < 17))
    return ~np.asarray(closed)


def find_gaps(idx: pd.DatetimeIndex, min_gap_minutes: int = 15) -> pd.DataFrame:
    """Missing stretches inside the FX week longer than ``min_gap_minutes``.

    Weekend closures are not gaps. The daily 17:00 NY rollover pause is
    counted, so expect short gaps there on real data.
    """
    if len(idx) < 2:
        return pd.DataFrame(columns=["after", "before", "missing_minutes"])
    prev, nxt = idx[:-1], idx[1:]
    delta = (nxt - prev) / pd.Timedelta(minutes=1)
    rows = []
    for i in np.flatnonzero(delta > min_gap_minutes):
        expected = pd.date_range(prev[i] + pd.Timedelta(minutes=1), nxt[i], freq="1min", inclusive="left")
        missing = int(in_fx_week(expected).sum())
        if missing > min_gap_minutes:
            rows.append((prev[i], nxt[i], missing))
    return pd.DataFrame(rows, columns=["after", "before", "missing_minutes"])


def find_spikes(df: pd.DataFrame, k: float = 12.0, window: int = 240) -> pd.DataFrame:
    """Bars whose range or close-to-close move exceeds ``k`` x the rolling
    median absolute move (robust, scale free). Flagged for review, not deleted."""
    ret = df["close"].diff().abs()
    rng = df["high"] - df["low"]
    scale = ret.rolling(window, min_periods=30).median().shift(1)
    rscale = rng.rolling(window, min_periods=30).median().shift(1)
    mask = (ret > k * scale.clip(lower=1e-12)) | (rng > k * rscale.clip(lower=1e-12))
    mask &= scale.notna()
    return df.loc[mask, ["open", "high", "low", "close"]]


def run_checks(df: pd.DataFrame, min_gap_minutes: int = 15, spike_k: float = 12.0) -> QualityReport:
    idx = pd.DatetimeIndex(df.index)
    unsorted = int((np.diff(idx.asi8) < 0).sum()) if len(idx) > 1 else 0
    dup = int(idx.duplicated().sum())
    clean = df[~idx.duplicated()].sort_index()
    cidx = pd.DatetimeIndex(clean.index)
    weekend = int((~in_fx_week(cidx)).sum()) if len(cidx) else 0
    bad = (
        (clean["high"] < clean[["open", "close"]].max(axis=1))
        | (clean["low"] > clean[["open", "close"]].min(axis=1))
        | (clean["high"] < clean["low"])
    )
    neg = int((clean["ask_close"] < clean["close"]).sum()) if "ask_close" in clean else 0
    gaps = find_gaps(cidx, min_gap_minutes)
    cov: dict[int, float] = {}
    if len(cidx):
        for year, grp in pd.Series(1, index=cidx).groupby(cidx.year):
            span = pd.date_range(f"{year}-01-01", f"{year + 1}-01-01", freq="1min", inclusive="left", tz="UTC")
            span = span[(span >= cidx[0].floor("D")) & (span <= cidx[-1])]
            expected = int(in_fx_week(span).sum())
            cov[int(year)] = round(len(grp) / expected, 4) if expected else 0.0
    return QualityReport(
        rows=len(df), start=cidx[0] if len(cidx) else None, end=cidx[-1] if len(cidx) else None,
        duplicates=dup, unsorted=unsorted, weekend_bars=weekend, bad_ohlc=int(bad.sum()),
        negative_spread=neg, spikes=find_spikes(clean, spike_k) if len(clean) > 30 else clean.iloc[:0],
        gaps=gaps, gap_minutes_total=int(gaps["missing_minutes"].sum()) if len(gaps) else 0,
        coverage_by_year=cov,
    )


def quality_report_markdown(symbol: str, r: QualityReport, max_rows: int = 15) -> str:
    lines = [
        f"## {symbol}", "",
        f"- rows: {r.rows:,}; span: {r.start} to {r.end}",
        f"- duplicates: {r.duplicates}; unsorted steps: {r.unsorted}; bad OHLC: {r.bad_ohlc}; "
        f"negative spread: {r.negative_spread}",
        f"- weekend bars (Fri 17:00 to Sun 17:00 NY): {r.weekend_bars}",
        f"- gaps > threshold: {len(r.gaps)} ({r.gap_minutes_total:,} trading minutes missing)",
        f"- spikes flagged: {len(r.spikes)}",
        f"- coverage by year (share of FX-week minutes present): {r.coverage_by_year}",
        f"- verdict: {'OK' if r.ok else 'PROBLEMS FOUND'}", "",
    ]
    if len(r.gaps):
        lines += ["Largest gaps:", "", "| after | before | missing min |", "|---|---|---|"]
        for _, g in r.gaps.nlargest(max_rows, "missing_minutes").iterrows():
            lines.append(f"| {g['after']} | {g['before']} | {g['missing_minutes']} |")
        lines.append("")
    if len(r.spikes):
        lines += ["First spikes:", "", "| ts | open | high | low | close |", "|---|---|---|---|---|"]
        for ts, s in r.spikes.head(max_rows).iterrows():
            lines.append(f"| {ts} | {s['open']} | {s['high']} | {s['low']} | {s['close']} |")
        lines.append("")
    return "\n".join(lines)
