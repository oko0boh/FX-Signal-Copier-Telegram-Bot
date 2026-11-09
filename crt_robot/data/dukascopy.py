"""Downloader for free Dukascopy 1-minute BID/ASK candles.

Source files (one per UTC day and side)::

    https://datafeed.dukascopy.com/datafeed/{SYM}/{YYYY}/{MM0}/{DD}/{SIDE}_candles_min_1.bi5

``MM0`` is the zero-based month (January = 00). A ``.bi5`` file is LZMA
compressed; each record is 24 big-endian bytes::

    uint32 seconds_from_day_start, uint32 open, uint32 close,
    uint32 low, uint32 high, float32 volume

Prices are integers scaled by the instrument's ``point_divisor``. Dukascopy
fills minutes without ticks with flat zero-volume candles (including
weekends); we drop those by default so gaps stay visible to the quality
checks.

If the host refuses us (HTTP 403/429, or a closed connection) we raise
:class:`DataHostBlocked` naming the host. We never fabricate data.
"""

from __future__ import annotations

import lzma
import struct
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from crt_robot.config import DATA_CACHE
from crt_robot.data.instruments import Instrument, get_instrument

HOST = "datafeed.dukascopy.com"
BASE_URL = f"https://{HOST}/datafeed"
RECORD = struct.Struct(">5If")
SIDES = ("BID", "ASK")

Fetcher = Callable[[str], bytes]


class DataHostBlocked(RuntimeError):
    """The data host refused or dropped our requests."""

    def __init__(self, host: str, detail: str):
        super().__init__(f"data host {host} refused the request: {detail}")
        self.host = host
        self.detail = detail


def day_url(symbol: str, day: date, side: str) -> str:
    if side not in SIDES:
        raise ValueError(side)
    return f"{BASE_URL}/{symbol}/{day.year:04d}/{day.month - 1:02d}/{day.day:02d}/{side}_candles_min_1.bi5"


def decode_bi5(raw: bytes, day: date, point_divisor: float) -> pd.DataFrame:
    """Decode one day file into a UTC-indexed OHLCV frame."""
    cols = ["open", "high", "low", "close", "volume"]
    if not raw:
        return pd.DataFrame(columns=cols, index=pd.DatetimeIndex([], tz="UTC", name="ts"), dtype=float)
    data = lzma.decompress(raw)
    if len(data) % RECORD.size:
        raise ValueError(f"corrupt bi5 payload: {len(data)} bytes is not a multiple of {RECORD.size}")
    arr = np.frombuffer(data, dtype=">u4,>u4,>u4,>u4,>u4,>f4")
    secs, o, c, lo, hi, vol = (arr[f"f{i}"] for i in range(6))
    start = pd.Timestamp(day, tz="UTC")
    idx = pd.DatetimeIndex(start + pd.to_timedelta(secs.astype(np.int64), unit="s"), name="ts").as_unit("ns")
    return pd.DataFrame(
        {
            "open": o / point_divisor,
            "high": hi / point_divisor,
            "low": lo / point_divisor,
            "close": c / point_divisor,
            "volume": vol.astype(float),
        },
        index=idx,
    )


def encode_bi5(df: pd.DataFrame, day: date, point_divisor: float) -> bytes:
    """Inverse of :func:`decode_bi5` (used to build test fixtures)."""
    start = pd.Timestamp(day, tz="UTC")
    out = bytearray()
    for ts, row in df.iterrows():
        out += RECORD.pack(
            int((ts - start).total_seconds()),
            *(int(round(row[k] * point_divisor)) for k in ("open", "close", "low", "high")),
            float(row["volume"]),
        )
    return lzma.compress(bytes(out), format=lzma.FORMAT_ALONE)


def http_fetch(url: str, retries: int = 3, pause: float = 1.0, timeout: float = 30.0) -> bytes:
    """Plain GET with polite retries on transient errors only.

    403/429 and dropped connections are treated as a refusal: raise at once.
    """
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 - fixed https host
                return resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return b""
            if exc.code in (401, 403, 407, 429):
                raise DataHostBlocked(HOST, f"HTTP {exc.code} for {url}") from exc
            if attempt == retries - 1:
                raise
        except (ConnectionResetError, urllib.error.URLError) as exc:
            if attempt == retries - 1:
                raise DataHostBlocked(HOST, f"{type(exc).__name__}: {exc}") from exc
        time.sleep(pause * 2**attempt)
    raise AssertionError("unreachable")


def fetch_day(inst: Instrument, day: date, fetch: Fetcher = http_fetch, drop_flat: bool = True) -> pd.DataFrame:
    """BID and ASK candles for one UTC day, joined into one frame.

    Columns: open/high/low/close (BID), ask_open/ask_high/ask_low/ask_close,
    volume (BID-side tick volume).
    """
    bid = decode_bi5(fetch(day_url(inst.dukascopy_symbol, day, "BID")), day, inst.point_divisor)
    ask = decode_bi5(fetch(day_url(inst.dukascopy_symbol, day, "ASK")), day, inst.point_divisor)
    ask = ask.drop(columns="volume").add_prefix("ask_")
    df = bid.join(ask, how="inner")
    if drop_flat:
        df = df[df["volume"] > 0]
    return df


def month_path(symbol: str, year: int, month: int, root: Path = DATA_CACHE) -> Path:
    return root / "dukascopy" / symbol / f"{year:04d}" / f"{month:02d}.parquet"


@dataclass
class DownloadResult:
    symbol: str
    months_written: int
    months_skipped: int
    rows: int


def download(
    symbol: str,
    start: date,
    end: date,
    root: Path = DATA_CACHE,
    fetch: Fetcher = http_fetch,
    pause: float = 0.2,
    overwrite: bool = False,
) -> DownloadResult:
    """Download ``[start, end]`` (UTC days) and store one parquet per month.

    A month already on disk is skipped unless ``overwrite`` is set or it is
    the current (possibly incomplete) month.
    """
    inst = get_instrument(symbol)
    today = date.today()
    written = skipped = rows = 0
    month_start = date(start.year, start.month, 1)
    while month_start <= end:
        nxt = (month_start + timedelta(days=32)).replace(day=1)
        path = month_path(inst.symbol, month_start.year, month_start.month, root)
        is_current = month_start.year == today.year and month_start.month == today.month
        if path.exists() and not overwrite and not is_current:
            skipped += 1
            month_start = nxt
            continue
        frames = []
        day = max(start, month_start)
        while day < nxt and day <= end and day <= today:
            frames.append(fetch_day(inst, day, fetch))
            if pause:
                time.sleep(pause)
            day += timedelta(days=1)
        frames = [f for f in frames if len(f)]
        if frames:
            df = pd.concat(frames).sort_index()
            path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(path)
            written += 1
            rows += len(df)
        month_start = nxt
    return DownloadResult(inst.symbol, written, skipped, rows)


def load(symbol: str, start: str | None = None, end: str | None = None, root: Path = DATA_CACHE) -> pd.DataFrame:
    """Load stored 1-minute bars for ``symbol`` (optionally sliced, UTC)."""
    files = sorted((root / "dukascopy" / get_instrument(symbol).symbol).glob("*/*.parquet"))
    if not files:
        raise FileNotFoundError(f"no cached data for {symbol} under {root}; run the downloader first")
    df = pd.concat(pd.read_parquet(f) for f in files).sort_index()
    df.index = pd.DatetimeIndex(df.index, name="ts").tz_convert("UTC").as_unit("ns")
    if start is not None:
        df = df[df.index >= pd.Timestamp(start, tz="UTC")]
    if end is not None:
        df = df[df.index < pd.Timestamp(end, tz="UTC")]
    return df
