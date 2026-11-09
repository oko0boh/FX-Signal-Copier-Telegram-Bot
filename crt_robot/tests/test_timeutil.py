import pandas as pd

from crt_robot.data.instruments import INSTRUMENTS, TRADEABLE, get_instrument
from crt_robot.timeutil import broker_naive_to_utc, ny_time, to_broker_naive


def test_broker_clock_is_gmt2_winter_gmt3_summer():
    winter = pd.DatetimeIndex([pd.Timestamp("2024-01-10 12:00", tz="UTC")])
    summer = pd.DatetimeIndex([pd.Timestamp("2024-07-10 12:00", tz="UTC")])
    assert to_broker_naive(winter)[0] == pd.Timestamp("2024-01-10 14:00")
    assert to_broker_naive(summer)[0] == pd.Timestamp("2024-07-10 15:00")


def test_broker_midnight_is_17_ny_both_seasons():
    for ts in [ny_time(2024, 1, 10, 17), ny_time(2024, 7, 10, 17)]:
        assert to_broker_naive(pd.DatetimeIndex([ts]))[0].hour == 0


def test_round_trip():
    idx = pd.date_range("2024-03-01", "2024-04-01", freq="37min", tz="UTC")
    # skip the Sunday DST hour, market closed anyway
    idx = idx[~((idx.tz_convert("America/New_York").day_of_week == 6)
                & (idx.tz_convert("America/New_York").hour < 4))]
    back = broker_naive_to_utc(to_broker_naive(idx))
    assert (back == idx).all()


def test_eu_dst_gap_weeks_still_ny_plus_7():
    # Between US and EU DST changes (e.g. 2024-03-12) London is GMT but the
    # broker already switched with New York: broker = NY + 7.
    ts = pd.DatetimeIndex([ny_time(2024, 3, 12, 1)])
    assert to_broker_naive(ts)[0] == pd.Timestamp("2024-03-12 08:00")


def test_instruments():
    assert TRADEABLE == ["EURUSD", "GBPUSD", "XAUUSD"]
    eu = get_instrument("eurusd")
    assert eu.tick == 1e-5
    dbl = eu.with_cost_multiplier(2)
    assert dbl.spread == 2 * eu.spread and dbl.commission_per_lot == 14.0
    assert not INSTRUMENTS["XAGUSD"].tradeable
