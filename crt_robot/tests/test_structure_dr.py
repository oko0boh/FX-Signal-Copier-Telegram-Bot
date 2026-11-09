import pytest

from crt_robot.primitives.dealing_range import DealingRange, latest_dealing_range
from crt_robot.primitives.structure import detect_structure
from crt_robot.primitives.swings import fractal_swings
from crt_robot.tests.fixtures import bars


def _series(points):
    """points = closes; build bars with small wicks."""
    return bars([(p, p + 0.1, p - 0.1, p) for p in points])


def test_true_mss_bull():
    # down leg to L1=~3, rally to H~6, lower low L2~2, then close above H -> mss_bull
    closes = [8, 7, 5, 3, 4, 6, 5, 4, 2, 3, 4, 5, 6.5, 7]
    df = _series(closes)
    ev = detect_structure(df, n=1)
    bull = ev[ev.kind.str.endswith("bull")]
    assert len(bull) >= 1
    first = bull.iloc[0]
    assert first.kind == "mss_bull"
    assert df["close"].iloc[first.idx] > first.level
    assert first.extreme < first.ref_price
    # event only after the swing high was known
    sw = fractal_swings(df, 1).set_index(["idx", "kind"])
    assert first.idx >= sw.loc[(first.swing_idx, "high"), "known_at"]


def test_bos_bull_on_higher_low():
    closes = [1, 2, 4, 3, 2.5, 3, 4.5, 5]
    ev = detect_structure(_series(closes), n=1)
    assert ev.iloc[0].kind == "bos_bull"


def test_wick_through_does_not_break():
    rows = [(1, 1.1, 0.9, 1.0), (1.0, 2.0, 0.95, 1.9), (1.9, 1.95, 1.0, 1.1),
            (1.1, 2.5, 1.05, 1.2), (1.2, 1.3, 1.1, 1.15)]
    ev = detect_structure(bars(rows), n=1)
    assert ev[ev.kind.str.endswith("bull")].empty


def test_each_swing_broken_once():
    closes = [1, 3, 2, 4, 5, 6, 7]
    ev = detect_structure(_series(closes), n=1)
    assert ev.groupby(["kind", "swing_idx"]).size().max() == 1


def test_dealing_range():
    dr = DealingRange(high=2.0, low=1.0, high_idx=10, low_idx=5)
    assert dr.eq == 1.5 and dr.direction == "up"
    assert dr.zone(1.8) == "premium" and dr.zone(1.2) == "discount" and dr.zone(1.5) == "equilibrium"
    assert dr.position(1.25) == pytest.approx(0.25) and dr.level(0.79) == pytest.approx(1.79)
    with pytest.raises(ValueError):
        DealingRange(1.0, 2.0, 0, 1)


def test_latest_dealing_range_respects_known_at():
    closes = [1, 2, 4, 3, 2.5, 3, 4.5, 5, 4]
    df = _series(closes)
    sw = fractal_swings(df, 1)
    assert latest_dealing_range(sw, 1) is None
    dr = latest_dealing_range(sw, len(df) - 1)
    assert dr is not None and dr.high > dr.low
    assert latest_dealing_range(sw, len(df) - 1, min_size=100) is None
