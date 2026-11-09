import numpy as np
import pytest

from crt_robot.primitives.fvg import detect_fvgs, fvg_open_at
from crt_robot.primitives.order_block import detect_order_blocks
from crt_robot.primitives.rejection_block import detect_rejection_blocks
from crt_robot.tests.fixtures import bars


def test_bullish_fvg_and_states():
    df = bars([
        (1.0, 1.2, 0.9, 1.1),   # a: high 1.2
        (1.1, 1.8, 1.1, 1.7),   # b
        (1.7, 2.0, 1.5, 1.9),   # c: low 1.5 > 1.2 -> gap [1.2, 1.5], CE 1.35
        (1.9, 2.1, 1.45, 2.0),  # touches
        (2.0, 2.0, 1.3, 1.6),   # passes CE
        (1.6, 1.7, 1.1, 1.2),   # full fill
    ])
    f = detect_fvgs(df)
    assert len(f) == 1
    r = f.iloc[0]
    assert r.kind == "bull" and r.bottom == 1.2 and r.top == 1.5 and r.ce == pytest.approx(1.35)
    assert (r.known_at, r.touched_idx, r.ce_idx, r.filled_idx) == (2, 3, 4, 5)
    assert len(fvg_open_at(f, 1)) == 0          # not known yet
    assert len(fvg_open_at(f, 2, "touch")) == 1
    assert len(fvg_open_at(f, 3, "touch")) == 0 and len(fvg_open_at(f, 3, "half")) == 1
    assert len(fvg_open_at(f, 4, "full")) == 1 and len(fvg_open_at(f, 5, "full")) == 0
    with pytest.raises(ValueError):
        fvg_open_at(f, 3, "bogus")


def test_bearish_fvg_and_min_size():
    df = bars([(2.0, 2.1, 1.8, 1.9), (1.9, 1.9, 1.2, 1.3), (1.3, 1.6, 1.1, 1.2)])
    f = detect_fvgs(df)
    assert f.iloc[0].kind == "bear" and f.iloc[0].top == 1.8 and f.iloc[0].bottom == 1.6
    assert f.iloc[0].touched_idx == -1
    assert detect_fvgs(df, min_size=0.5).empty


def test_no_fvg_when_wicks_overlap():
    df = bars([(1, 1.5, 0.9, 1.2), (1.2, 1.8, 1.1, 1.7), (1.7, 2.0, 1.4, 1.9)])
    assert detect_fvgs(df).empty


def _ob_fixture():
    return bars([
        (2.0, 2.1, 1.9, 2.05),  # 0 up
        (2.05, 2.06, 1.8, 1.85),  # 1 down
        (1.85, 1.86, 1.5, 1.6),   # 2 down, purges liquidity
        (1.6, 1.95, 1.58, 1.9),   # 3 up: engulfs bar 2 only (1.9 < bar 1 body top 2.05)
        (1.9, 2.2, 1.85, 2.15),   # 4 up: closes above all bodies and wicks of 1..2
    ])


def test_order_block_suffix_then_larger():
    df = _ob_fixture()
    liq = np.array([0, 0, 1, 0, 0], bool)
    ob = detect_order_blocks(df, liq)
    bull = ob[ob.kind == "bull"]
    assert list(zip(bull.first_idx, bull.last_idx, bull.engulf_idx)) == [(2, 2, 3), (1, 2, 4)]
    first, second = bull.iloc[0], bull.iloc[1]
    assert first.top == 1.86 and first.full_candle      # close 1.9 > wick 1.86 -> full candle
    assert second.full_candle and second.top == 2.06 and second.bottom == 1.5


def test_order_block_requires_liquidity():
    df = _ob_fixture()
    assert detect_order_blocks(df, np.zeros(5, bool)).query("kind=='bull'").empty
    # liquidity only on bar 1: first engulf (suffix = bar 2 only) is rejected, larger one accepted
    ob = detect_order_blocks(df, np.array([0, 1, 0, 0, 0], bool)).query("kind=='bull'")
    assert list(ob.engulf_idx) == [4]


def test_order_block_body_only_extent():
    df = bars([(2.0, 2.0, 1.5, 1.6), (1.6, 1.95, 1.6, 1.8)])  # close 1.8 > body top 2.0? no
    assert detect_order_blocks(df, np.array([1, 0], bool)).empty
    df = bars([(2.0, 2.3, 1.5, 1.6), (1.6, 2.2, 1.6, 2.1)])  # closes above body (2.0) not wick (2.3)
    ob = detect_order_blocks(df, np.array([1, 0], bool)).iloc[0]
    assert ob.top == 2.0 and ob.bottom == 1.5 and not ob.full_candle


def test_bearish_order_block():
    df = bars([(1.0, 1.4, 0.95, 1.3), (1.3, 1.35, 0.9, 0.92)])
    ob = detect_order_blocks(df, np.array([1, 0], bool), key_time=np.array([0, 1], bool)).iloc[0]
    assert ob.kind == "bear" and ob.full_candle and ob.top == 1.4 and ob.bottom == 0.95 and ob.in_key_time


def test_order_block_liquidity_length_checked():
    with pytest.raises(ValueError):
        detect_order_blocks(_ob_fixture(), np.zeros(3, bool))


def test_rejection_block_zone():
    df = bars([
        (1.0, 1.1, 0.9, 1.05), (1.05, 1.15, 1.0, 1.1),
        (1.1, 1.6, 1.05, 1.2),   # swing high, long upper wick; bodies top 1.2
        (1.2, 1.25, 1.0, 1.05), (1.05, 1.1, 0.95, 1.0),
    ])
    rb = detect_rejection_blocks(df, n=2, window=1, min_wick_frac=0.3)
    bear = rb[rb.kind == "bear"].iloc[0]
    assert bear.swing_idx == 2 and bear.top == 1.6 and bear.bottom == 1.2 and bear.known_at == 4
    assert detect_rejection_blocks(df, n=2, min_wick_frac=0.9).query("kind=='bear'").empty
