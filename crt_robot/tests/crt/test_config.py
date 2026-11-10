"""Strategy config (rulebook section 7): load, modes, validation, gaps."""

import pytest

from crt_robot.crt.config import ConfigError, MODES, check_implemented, load_config, raw_config


@pytest.mark.parametrize("mode", MODES)
def test_every_mode_loads_and_is_implemented(mode):
    cfg = load_config(mode)
    assert cfg.mode == mode and cfg.rulebook_version == "0.2"
    check_implemented(cfg)


def test_v02_defaults_match_rulebook_section7():
    c = load_config("romeo")
    assert c.candles.week_open == "sun_1700" and c.candles.daily_open == "00:00"
    assert c.clock.daily_candle == "D_NY" and c.clock.weekly_candle == "W"
    assert c.timeframes.kl_tf_for_htf == {"W": "M", "D": "W", "4H": "D", "1H": "4H", "15m": "1H"}
    assert c.timeframes.tf_pairs == {"M": "D", "W": "4H", "D": "1H", "4H": "15m"}
    assert c.key_level.kl_types == ["old_high", "old_low", "bos_origin_hl", "fvg", "ob", "rb"]
    assert c.crt.min_confirmations == 3 and c.crt.ts_timing_mode == "open_of_new"
    assert c.timing.purge_hours == ["01:00", "03:00", "06:00", "08:00", "09:00", "11:00"]
    assert c.entry.ote_zone == [0.50, 0.79] and c.entry.model1_trigger_ref == "wick"
    assert c.targets.tp1_fraction == 0.5 and c.risk.risk_per_trade == 0.01 and c.risk.daily_loss_limit_r == 2.0
    assert c.bias.market_profile_mode == "five_phase"


def test_mode_overlays_follow_rulebook_section4():
    r, s, h = (load_config(m) for m in MODES)
    assert r.crt.require_close_inside["4H"] is True
    assert s.crt.require_close_inside["4H"] is False          # CRT-R29 sham
    assert s.entry.entry_set == ["ob"] and s.targets.target_mode == "r_multiple"
    assert s.timing.require_timed_purge and s.timing.require_timed_entry and s.timing.use_asia_block
    assert h.timing.require_timed_purge and "ob" in h.entry.entry_set and h.targets.target_mode == "crt_levels"


def test_alternatives_are_switchable():
    c = load_config("romeo", ["entry.ote_zone=[0.62, 0.79]", "entry.model1_trigger_ref=body",
                              "candles.week_open=mon_0000", "bias.romeo_sweep_days=[all]"])
    assert c.entry.ote_zone == [0.62, 0.79] and c.entry.model1_trigger_ref == "body"
    assert c.candles.week_open == "mon_0000"
    d = load_config("romeo", {"candles": {"daily_open": "17:00"}, "clock": {"daily_candle": "D"}})
    assert d.daily_tf == "D"


def test_clock_decision_must_be_consistent():
    with pytest.raises(ConfigError, match="daily_candle"):
        load_config("romeo", ["candles.daily_open=\"17:00\""])
    with pytest.raises(ConfigError, match="weekly_candle"):
        load_config("romeo", ["candles.week_range_from=mon_0000"])
    c = load_config("romeo", ["candles.week_range_from=mon_0000", "clock.weekly_candle=W_MON"])
    assert c.clock.weekly_candle == "W_MON"


def test_unknown_keys_and_bad_values_are_errors():
    with pytest.raises(ConfigError, match="unknown keys"):
        load_config("romeo", ["entry.oet_zone=[0.5, 0.79]"])
    with pytest.raises(ConfigError, match="allowed"):
        load_config("romeo", ["entry.model1_trigger_ref=midpoint"])
    with pytest.raises(ConfigError, match="ote_zone"):
        load_config("romeo", ["entry.ote_zone=[0.8, 0.5]"])
    with pytest.raises(ConfigError, match="integer"):
        load_config("romeo", ["general.swing_n=two"])
    with pytest.raises(ConfigError):
        load_config("scalper")


def test_unimplemented_alternatives_are_refused_by_name():
    cfg = load_config("romeo", ["targets.target_mode=swings_one_by_one", "crt.framing_model=room_5am"])
    with pytest.raises(NotImplementedError, match="target_mode"):
        check_implemented(cfg)


def test_fingerprint_changes_with_any_parameter():
    a, b = load_config("romeo"), load_config("romeo", ["general.swing_n=3"])
    assert a.fingerprint() != b.fingerprint() and a.fingerprint() == load_config("romeo").fingerprint()
    assert raw_config("romeo")["general"]["swing_n"] == 2
