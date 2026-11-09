from datetime import date

import numpy as np
import pandas as pd
import pytest

from crt_robot.data import dukascopy as dk
from crt_robot.data.instruments import get_instrument


def _day_frame(day: date, n: int = 5, base: float = 1.1, zero_vol_at: int | None = None) -> pd.DataFrame:
    idx = pd.DatetimeIndex([pd.Timestamp(day, tz="UTC") + pd.Timedelta(minutes=i) for i in range(n)], name="ts").as_unit("ns")
    o = base + np.arange(n) * 1e-5
    df = pd.DataFrame({"open": o, "high": o + 3e-5, "low": o - 2e-5, "close": o + 1e-5,
                       "volume": np.full(n, 10.0)}, index=idx)
    if zero_vol_at is not None:
        df.iloc[zero_vol_at, df.columns.get_loc("volume")] = 0.0
    return df


def test_url_uses_zero_based_month():
    assert dk.day_url("EURUSD", date(2024, 1, 3), "BID").endswith("/EURUSD/2024/00/03/BID_candles_min_1.bi5")
    assert "/2024/11/31/ASK_" in dk.day_url("EURUSD", date(2024, 12, 31), "ASK")
    with pytest.raises(ValueError):
        dk.day_url("EURUSD", date(2024, 1, 3), "MID")


def test_bi5_round_trip():
    day = date(2024, 1, 3)
    df = _day_frame(day)
    out = dk.decode_bi5(dk.encode_bi5(df, day, 1e5), day, 1e5)
    pd.testing.assert_frame_equal(out, df, check_dtype=False, atol=1e-9)


def test_empty_file_gives_empty_frame():
    assert dk.decode_bi5(b"", date(2024, 1, 6), 1e5).empty


def test_corrupt_payload_rejected():
    import lzma
    with pytest.raises(ValueError):
        dk.decode_bi5(lzma.compress(b"x" * 25, format=lzma.FORMAT_ALONE), date(2024, 1, 3), 1e5)


def _fake_fetcher(days: dict[date, pd.DataFrame], spread: float = 1e-4):
    calls = []

    def fetch(url: str) -> bytes:
        calls.append(url)
        parts = url.split("/")
        d = date(int(parts[-4]), int(parts[-3]) + 1, int(parts[-2]))
        if d not in days:
            return b""
        df = days[d].copy()
        if "ASK_" in url:
            for c in ("open", "high", "low", "close"):
                df[c] = df[c] + spread
        return dk.encode_bi5(df, d, 1e5)

    return fetch, calls


def test_fetch_day_joins_bid_ask_and_drops_flat():
    day = date(2024, 1, 3)
    fetch, _ = _fake_fetcher({day: _day_frame(day, zero_vol_at=2)})
    df = dk.fetch_day(get_instrument("EURUSD"), day, fetch)
    assert len(df) == 4
    assert np.allclose(df["ask_close"] - df["close"], 1e-4)


def test_download_writes_monthly_parquet_and_resumes(tmp_path):
    days = {date(2024, 1, 2): _day_frame(date(2024, 1, 2)), date(2024, 2, 1): _day_frame(date(2024, 2, 1))}
    fetch, calls = _fake_fetcher(days)
    res = dk.download("EURUSD", date(2024, 1, 1), date(2024, 2, 3), root=tmp_path, fetch=fetch, pause=0)
    assert res.months_written == 2 and res.rows == 10
    assert dk.month_path("EURUSD", 2024, 1, tmp_path).exists()
    n = len(calls)
    res2 = dk.download("EURUSD", date(2024, 1, 1), date(2024, 2, 3), root=tmp_path, fetch=fetch, pause=0)
    assert res2.months_skipped == 2 and len(calls) == n  # nothing refetched
    loaded = dk.load("EURUSD", root=tmp_path)
    assert len(loaded) == 10 and str(loaded.index.tz) == "UTC"


def test_blocked_host_raises_and_names_host(tmp_path):
    def fetch(url: str) -> bytes:
        raise dk.DataHostBlocked(dk.HOST, "HTTP 429")

    with pytest.raises(dk.DataHostBlocked) as exc:
        dk.download("EURUSD", date(2024, 1, 1), date(2024, 1, 2), root=tmp_path, fetch=fetch, pause=0)
    assert exc.value.host == "datafeed.dukascopy.com"
    assert not list(tmp_path.rglob("*.parquet"))


def test_load_without_cache_is_explicit(tmp_path):
    with pytest.raises(FileNotFoundError):
        dk.load("EURUSD", root=tmp_path)
