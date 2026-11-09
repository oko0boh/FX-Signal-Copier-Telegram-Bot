import numpy as np
import pandas as pd
import pytest

from crt_robot.data.mtf import LookAheadError, MultiTimeframeView
from crt_robot.data.synthetic import random_walk

TFS = ("15m", "1H", "4H", "D", "W")


@pytest.fixture(scope="module")
def base():
    return random_walk("2024-03-03 17:00", "2024-03-23", seed=11)


@pytest.fixture(scope="module")
def view(base):
    return MultiTimeframeView(base, TFS)


def test_closed_bars_never_close_after_now(view):
    rng = np.random.default_rng(0)
    for i in rng.integers(0, len(view), 400):
        s = view.at(int(i))
        for tf in TFS:
            c = s.closed(tf)
            if len(c):
                assert (pd.DatetimeIndex(c["close_time"]) <= s.now).all()
                assert c["complete"].all()


def test_forming_bar_matches_base_bars_so_far(view, base):
    rng = np.random.default_rng(1)
    for i in rng.integers(0, len(view), 300):
        s = view.at(int(i))
        for tf in TFS:
            f = s.forming(tf)
            if f is None:
                continue
            assert not f.complete
            assert f.open_time <= s.bar_time < f.close_time
            assert f.close_time > s.now
            chunk = base[(base.index >= f.open_time) & (base.index <= s.bar_time)]
            assert f.open == chunk["open"].iloc[0]
            assert f.high == chunk["high"].max() and f.low == chunk["low"].min()
            assert f.close == chunk["close"].iloc[-1] and f.n_bars == len(chunk)


def test_truncation_invariance(base, view):
    """A snapshot from the full data equals one built from data cut at now.
    If any future bar leaked in, the two would differ."""
    rng = np.random.default_rng(2)
    for i in sorted(rng.integers(100, len(view), 12)):
        i = int(i)
        cut = MultiTimeframeView(base.iloc[: i + 1], TFS)
        a, b = view.at(i), cut.at(i)
        for tf in TFS:
            pd.testing.assert_frame_equal(a.closed(tf), b.closed(tf))
            assert a.forming(tf) == b.forming(tf)


def test_bar_becomes_closed_exactly_at_its_close(view):
    s0 = view.at(0)
    h1_open = s0.forming("1H").open_time
    # walk to the last minute of that hour
    i = next(j for j in range(len(view)) if view.index[j] == h1_open + pd.Timedelta(minutes=59))
    before, at = view.at(i - 1), view.at(i)
    assert before.forming("1H") is not None and before.n_closed("1H") == 0
    assert at.forming("1H") is None and at.n_closed("1H") == 1
    assert at.closed_bar("1H", 1)["close"] == at.last("close")
    nxt = view.at(i + 1)
    assert nxt.forming("1H").n_bars == 1


def test_api_refuses_future(view):
    s = view.at(500)
    with pytest.raises(LookAheadError):
        s.last("close", back=-1)
    with pytest.raises(LookAheadError):
        s.closed_bar("4H", back=0)
    arr = s.closed_array("4H", "high")
    assert len(arr) == s.n_closed("4H")
    with pytest.raises(ValueError):
        arr[0] = 0.0  # read-only
    assert len(s.base_array("close")) == 501
    with pytest.raises(IndexError):
        s.closed_bar("W", back=10)


def test_weekly_forming_until_friday_close(view):
    i = len(view) - 1
    s = view.at(i)
    # data ends Friday 23:59 UTC... last week bar closes Fri 17:00 NY = end of data
    assert s.forming("W") is None
    assert s.closed_bar("W")["n_bars"] > 7000


def test_unknown_tf_raises(view):
    with pytest.raises(KeyError):
        view.at(0).closed("2H")
