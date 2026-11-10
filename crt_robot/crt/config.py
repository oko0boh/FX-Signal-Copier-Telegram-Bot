"""Typed strategy configuration (rulebook section 7).

``load_config(mode)`` reads ``config/strategy/rulebook_v0.2.yaml``, deep-merges
the mode overlay ``config/strategy/modes/<mode>.yaml`` and any ``overrides``
(nested dict or ``"section.key=value"`` strings), then builds frozen
dataclasses. Unknown keys and values outside the allowed choices raise
:class:`ConfigError`, so a typo can never silently fall back to a default.

Alternatives the rulebook lists but Phase 2 does not compute yet are
accepted by the loader (they stay switchable parameters) and refused by
:func:`check_implemented`, which every strategy calls, with a message
naming the gap.
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
import types
import typing
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from crt_robot.config import CONFIG_DIR

STRATEGY_DIR = CONFIG_DIR / "strategy"
BASE_FILE = STRATEGY_DIR / "rulebook_v0.2.yaml"
MODES = ("romeo", "sham", "hybrid")
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


class ConfigError(ValueError):
    pass


# ---------------------------------------------------------------------------
# sections
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Clock:
    daily_candle: str
    weekly_candle: str
    skip_sunday_stub: bool
    monthly_from: str


@dataclass(frozen=True)
class General:
    strategy_mode: str
    timezone: str
    atr_len: int
    swing_n: int
    sweep_min_ticks: int
    ts_close_back_bars: int


@dataclass(frozen=True)
class Candles:
    daily_open: str
    h4_grid_first_open: str
    week_open: str
    week_range_from: str
    week_sequence_start: str
    week_close: str
    max_inside_bars: int


@dataclass(frozen=True)
class Timeframes:
    htf_allowed: list
    tf_pairs: dict
    kl_tf_for_htf: dict
    kl_tf_secondary: dict
    use_kl_tf_secondary: bool
    tf_pairs_alt_notebook: dict
    sham_stack: dict


@dataclass(frozen=True)
class Bias:
    bias_inputs: list
    bias_gate: str
    bias_tf: str
    structure_break: str
    bias_crt_days: list
    bias_crt_target: str
    allow_counter_htf: bool
    allow_delivered_counter: bool
    delivered_adr_mult: float
    ranging_adr_frac: float
    near_target_atr: float
    use_weekly_time_theory: bool
    romeo_sweep_days: list
    skip_if_monday_expansion: bool
    monday_expansion_adr: float
    mid_range_block: list
    market_profile_mode: str
    trade_outcomes: list
    profile_k: int


@dataclass(frozen=True)
class DealingRangeCfg:
    dr_tf: str
    dr_min_atr: float
    dr_require_sweep_both: bool
    dr_require_fvg: bool
    require_correct_half: bool
    rebalance_required: bool
    rebalance_level: str
    kod_s_dist: float
    kod_r_requires_tp1: bool
    weekly_model: str
    fvg_fill: str


@dataclass(frozen=True)
class KeyLevelCfg:
    kl_types: list
    kl_score_bos_bonus: int
    kl_select: str
    kl_max_dist_atr: float
    kl_touch_tol: float
    visible_lookback: int
    kl_lookback_bars: int
    ob_liquidity: str


@dataclass(frozen=True)
class CRTCfg:
    require_close_inside: dict
    close_inside_score: bool
    min_confirmations: int
    confirmation_types: list
    timed_crt_h4_opens: list
    framing_model: str
    room_5am: dict
    allow_c2_entry: bool
    framing_candle_opens: list
    allow_reselect: bool
    ts_timing_mode: str
    ts_at_open_frac: float
    late_frac: float
    model1_c2_trigger: str


@dataclass(frozen=True)
class Timing:
    killzones: dict
    index_killzones: dict
    macros: list
    purge_hours: list
    refined_key_times: list
    london_lunch: list
    cbdr_window: list
    macro_window: str
    key_time_strictness: str
    require_timed_purge: bool
    require_timed_entry: bool
    asia_block: list
    use_asia_block: bool
    asia_block_romeo: bool
    romeo_use_killzones: bool
    closing_hour_filter: str


@dataclass(frozen=True)
class Entry:
    entry_set: list
    romeo_entry_set: list
    require_thick: bool
    thick_body_ratio: float
    thick_atr_mult: float
    model1_trigger_ref: str
    model1_entry: str
    mss_entry_zone: str
    mss_lookback_bars: int
    ote_zone: list
    ote_fib_basis: str
    ote_trigger: str
    leg_end_atr: float
    smt_confirm: str
    require_smt: bool
    smt_take: str
    smt_pairs: dict
    ob_entry_edge: str
    ob_max_candles: int
    ob_liq_tf_steps: int
    min_confluence: int
    max_entries_per_setup: int
    setup_expiry: str


@dataclass(frozen=True)
class Stop:
    stop_mode: str
    ote_stop: str
    stop_buffer_ticks: int


@dataclass(frozen=True)
class Targets:
    target_mode: str
    tp1_fraction: float
    r_target: float
    friday_r_target: float
    time_exit: str
    be_after_tp1: bool
    weak_ts_atr: float


@dataclass(frozen=True)
class Invalidation:
    on_opposing_smt: str
    decisive_closes: int
    on_first_close_beyond: str
    sham_invalid_atr: float
    skip_if_50_reached: bool


@dataclass(frozen=True)
class Risk:
    risk_per_trade: float
    instruments: list
    daily_loss_limit_r: float
    max_open_risk: float
    max_trades_per_day: int
    max_trades_per_week: int
    news_events: list
    news_block: str
    news_calendar: str
    friday_flat_time: str
    no_weekend_holds: bool


@dataclass(frozen=True)
class Logging:
    log_weekly_stats: bool
    week_shape_mode: str
    log_fields: list


@dataclass(frozen=True)
class StrategyConfig:
    rulebook_version: str
    clock: Clock
    general: General
    candles: Candles
    timeframes: Timeframes
    bias: Bias
    dealing_range: DealingRangeCfg
    key_level: KeyLevelCfg
    crt: CRTCfg
    timing: Timing
    entry: Entry
    stop: Stop
    targets: Targets
    invalidation: Invalidation
    risk: Risk
    logging: Logging
    raw: dict = dataclasses.field(repr=False, compare=False, default_factory=dict)

    @property
    def mode(self) -> str:
        return self.general.strategy_mode

    @property
    def daily_tf(self) -> str:
        return self.clock.daily_candle

    def fingerprint(self) -> str:
        """Short hash of every parameter value (for the runs log)."""
        blob = json.dumps(self.raw, sort_keys=True, default=str).encode()
        return hashlib.sha256(blob).hexdigest()[:12]

    def flat(self) -> dict[str, Any]:
        out: dict[str, Any] = {}

        def walk(prefix: str, d: Any) -> None:
            if isinstance(d, dict):
                for k, v in d.items():
                    walk(f"{prefix}.{k}" if prefix else k, v)
            else:
                out[prefix] = d
        walk("", self.raw)
        return out


SECTIONS: dict[str, type] = {
    "clock": Clock, "general": General, "candles": Candles, "timeframes": Timeframes, "bias": Bias,
    "dealing_range": DealingRangeCfg, "key_level": KeyLevelCfg, "crt": CRTCfg, "timing": Timing,
    "entry": Entry, "stop": Stop, "targets": Targets, "invalidation": Invalidation, "risk": Risk,
    "logging": Logging,
}

# Allowed values (every alternative named in the rulebook is accepted).
CHOICES: dict[str, tuple] = {
    "clock.daily_candle": ("D_NY", "D"),
    "clock.weekly_candle": ("W", "W_MON"),
    "clock.monthly_from": ("daily",),
    "general.strategy_mode": MODES,
    "candles.daily_open": ("00:00", "17:00"),
    "candles.h4_grid_first_open": ("01:00", "00:00"),
    "candles.week_open": ("sun_1700", "mon_0000"),
    "candles.week_range_from": ("sun_1700", "mon_0000"),
    "candles.week_close": ("fri_1700", "fri_1600"),
    "bias.bias_gate": ("hard", "score"),
    "bias.bias_tf": ("parent", "weekly"),
    "bias.structure_break": ("close", "wick"),
    "bias.bias_crt_target": ("opposite_extreme", "dr_eq"),
    "bias.market_profile_mode": ("five_phase", "romeo_swings", "sham4", "none"),
    "dealing_range.dr_tf": ("parent", "htf"),
    "dealing_range.rebalance_level": ("eq", "premium_fvg"),
    "dealing_range.weekly_model": ("none", "wednesday"),
    "dealing_range.fvg_fill": ("touch", "half", "full"),
    "key_level.kl_select": ("score", "nearest"),
    "key_level.ob_liquidity": ("same_tf_swing", "any"),
    "crt.framing_model": ("default", "room_5am"),
    "crt.ts_timing_mode": ("open_of_new", "late_of_prev"),
    "crt.model1_c2_trigger": ("retest", "skip"),
    "timing.macro_window": ("hour", "ict"),
    "timing.key_time_strictness": ("killzone_or_macro", "macro_only"),
    "timing.closing_hour_filter": ("none", "first", "last"),
    "entry.model1_trigger_ref": ("wick", "body"),
    "entry.model1_entry": ("close", "model_high"),
    "entry.mss_entry_zone": ("ote", "full_retrace"),
    "entry.ote_fib_basis": ("wick", "body", "union", "intersection"),
    "entry.ote_trigger": ("touch", "ltf_ts"),
    "entry.smt_confirm": ("model1_or_mss", "model1_then_mss"),
    "entry.smt_take": ("wick", "close"),
    "entry.ob_entry_edge": ("near_edge", "open", "mid"),
    "entry.setup_expiry": ("c3_close", "killzone_end"),
    "stop.stop_mode": ("by_entry_type", "fvg_fill_low", "weekly_model_extreme"),
    "stop.ote_stop": ("leg_origin", "fib_079"),
    "targets.target_mode": ("crt_levels", "to_50_only", "r_multiple", "swings_one_by_one", "ote_body",
                            "last_high_before_dump", "opposing_kl"),
    "targets.time_exit": ("end_of_htf_candle", "none", "end_of_killzone"),
    "invalidation.on_opposing_smt": ("close", "breakeven", "ignore"),
    "invalidation.on_first_close_beyond": ("warn", "breakeven"),
    "risk.news_block": ("whole_day",),
    "logging.week_shape_mode": ("proxy6", "sham_profiles"),
}
LIST_CHOICES: dict[str, tuple] = {
    "timeframes.htf_allowed": ("4H", "D", "W", "M", "1H"),
    "bias.bias_inputs": ("close_wick", "structure", "weekly_ohlc", "monthly_ohlc", "smt"),
    "bias.romeo_sweep_days": WEEKDAYS + ("all",),
    "bias.bias_crt_days": WEEKDAYS,
    "bias.trade_outcomes": ("expansion", "reversal", "range", "manipulation", "retracement"),
    "key_level.kl_types": ("old_high", "old_low", "bos_origin_hl", "fvg", "ob", "rb", "breaker",
                           "prev_period_hl", "candle_open", "weekly_wick_50"),
    "crt.confirmation_types": ("timed_crt", "timed_purge", "htf_key_level", "inside_bars", "ltf_crt_inside_htf"),
    "entry.entry_set": ("model1", "mss", "ote", "ob", "kod_r"),
    "entry.romeo_entry_set": ("model1", "mss", "ote", "kod_r"),
    "risk.news_events": ("FOMC", "NFP", "CPI"),
}

# Accepted by the loader, not computed yet (Phase 2 gaps; see PHASE2_REPORT).
UNIMPLEMENTED: dict[str, tuple] = {
    "candles.h4_grid_first_open": ("00:00",),
    "bias.bias_inputs": ("weekly_ohlc", "monthly_ohlc", "smt"),
    "bias.structure_break": ("wick",),
    "dealing_range.rebalance_level": ("premium_fvg",),
    "dealing_range.weekly_model": ("wednesday",),
    "key_level.kl_types": ("breaker",),
    "crt.framing_model": ("room_5am",),
    "entry.entry_set": ("kod_r",),
    "entry.romeo_entry_set": ("kod_r",),
    "entry.ote_trigger": ("ltf_ts",),
    "entry.smt_confirm": ("model1_then_mss",),
    "entry.ote_fib_basis": ("union", "intersection"),
    "stop.stop_mode": ("weekly_model_extreme",),
    "targets.target_mode": ("swings_one_by_one", "ote_body", "last_high_before_dump", "opposing_kl"),
    "targets.time_exit": ("end_of_killzone",),
    "timeframes.htf_allowed": ("M", "1H"),
    "risk.news_events": ("NFP", "CPI"),
    "logging.week_shape_mode": ("sham_profiles",),
}


def _deep_merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict) and k not in _REPLACE_WHOLE:
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


# dict-valued parameters that an overlay replaces as a whole (they are maps
# of values, not sub-sections)
_REPLACE_WHOLE: set[str] = set()


def _parse_override(item: str) -> dict:
    if "=" not in item:
        raise ConfigError(f"override {item!r} must look like section.key=value")
    path, value = item.split("=", 1)
    keys = path.strip().split(".")
    val = yaml.safe_load(value)
    d: dict = {}
    cur = d
    for k in keys[:-1]:
        cur = cur.setdefault(k, {})
    cur[keys[-1]] = val
    return d


def _check_type(path: str, val: Any, hint: Any) -> Any:
    origin = typing.get_origin(hint)
    if hint is bool:
        if not isinstance(val, bool):
            raise ConfigError(f"{path} must be true/false, got {val!r}")
    elif hint is int:
        if isinstance(val, bool) or not isinstance(val, int):
            raise ConfigError(f"{path} must be an integer, got {val!r}")
    elif hint is float:
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            raise ConfigError(f"{path} must be a number, got {val!r}")
        val = float(val)
    elif hint is str:
        if not isinstance(val, str):
            raise ConfigError(f"{path} must be a string, got {val!r}")
    elif hint is list or origin is list:
        if not isinstance(val, list):
            raise ConfigError(f"{path} must be a list, got {val!r}")
    elif hint is dict or origin is dict:
        if not isinstance(val, dict):
            raise ConfigError(f"{path} must be a mapping, got {val!r}")
    elif isinstance(hint, types.UnionType):
        pass
    return val


def build(raw: dict) -> StrategyConfig:
    raw = copy.deepcopy(raw)
    known = set(SECTIONS) | {"rulebook_version"}
    unknown = set(raw) - known
    if unknown:
        raise ConfigError(f"unknown top-level keys: {sorted(unknown)}")
    built: dict[str, Any] = {"rulebook_version": str(raw.get("rulebook_version", ""))}
    for name, cls in SECTIONS.items():
        sec = raw.get(name)
        if not isinstance(sec, dict):
            raise ConfigError(f"section {name!r} is missing")
        hints = typing.get_type_hints(cls)
        fields = {f.name for f in dataclasses.fields(cls)}
        extra = set(sec) - fields
        missing = fields - set(sec)
        if extra:
            raise ConfigError(f"unknown keys in {name}: {sorted(extra)}")
        if missing:
            raise ConfigError(f"missing keys in {name}: {sorted(missing)}")
        vals = {}
        for k in fields:
            path = f"{name}.{k}"
            v = _check_type(path, sec[k], hints[k])
            if path in CHOICES and v not in CHOICES[path]:
                raise ConfigError(f"{path}={v!r}; allowed: {CHOICES[path]}")
            if path in LIST_CHOICES:
                bad = [x for x in v if x not in LIST_CHOICES[path]]
                if bad:
                    raise ConfigError(f"{path} has unknown values {bad}; allowed: {LIST_CHOICES[path]}")
            vals[k] = v
        built[name] = cls(**vals)
    cfg = StrategyConfig(**built, raw=raw)
    _validate(cfg)
    return cfg


def _validate(cfg: StrategyConfig) -> None:
    want = {"00:00": "D_NY", "17:00": "D"}[cfg.candles.daily_open]
    if cfg.clock.daily_candle != want:
        raise ConfigError(f"clock.daily_candle={cfg.clock.daily_candle} contradicts candles.daily_open="
                          f"{cfg.candles.daily_open!r} (expects {want})")
    wk = {"sun_1700": "W", "mon_0000": "W_MON"}[cfg.candles.week_range_from]
    if cfg.clock.weekly_candle != wk:
        raise ConfigError(f"clock.weekly_candle={cfg.clock.weekly_candle} contradicts candles.week_range_from="
                          f"{cfg.candles.week_range_from!r} (expects {wk})")
    for htf in cfg.timeframes.htf_allowed:
        if htf not in cfg.timeframes.tf_pairs:
            raise ConfigError(f"no tf_pairs entry for htf {htf}")
    lo, hi = cfg.entry.ote_zone
    if not 0 < lo < hi < 1:
        raise ConfigError(f"entry.ote_zone must be 0 < lo < hi < 1, got {cfg.entry.ote_zone}")
    a, b = cfg.bias.mid_range_block
    if not 0 <= a <= b <= 1:
        raise ConfigError("bias.mid_range_block must be [lo, hi] inside [0, 1]")
    if not 0 <= cfg.targets.tp1_fraction < 1:
        raise ConfigError("targets.tp1_fraction must be in [0, 1)")
    if cfg.crt.min_confirmations > len(cfg.crt.confirmation_types):
        raise ConfigError("crt.min_confirmations exceeds the number of confirmation_types")


def check_implemented(cfg: StrategyConfig) -> None:
    """Raise NotImplementedError if the config selects an alternative that
    Phase 2 does not compute yet."""
    flat = cfg.flat()
    problems = []
    if cfg.bias.allow_delivered_counter:
        problems.append("bias.allow_delivered_counter=true (CRT-R17)")
    if cfg.entry.max_entries_per_setup != 1:
        problems.append("entry.max_entries_per_setup>1 (CRT-R48 re-entries)")
    if not cfg.crt.allow_reselect:
        problems.append("crt.allow_reselect=false")
    for path, bad in UNIMPLEMENTED.items():
        v = flat.get(path)
        vals = v if isinstance(v, list) else [v]
        hit = [x for x in vals if x in bad]
        if hit:
            problems.append(f"{path}={hit}")
    if problems:
        raise NotImplementedError("not implemented in Phase 2 (switchable, but no code yet): " + ", ".join(problems))


def raw_config(mode: str = "romeo", overrides: list[str] | dict | None = None,
               base_file: Path = BASE_FILE) -> dict:
    if mode not in MODES:
        raise ConfigError(f"mode must be one of {MODES}")
    with open(base_file) as fh:
        raw = yaml.safe_load(fh)
    with open(STRATEGY_DIR / "modes" / f"{mode}.yaml") as fh:
        raw = _deep_merge(raw, yaml.safe_load(fh) or {})
    if isinstance(overrides, dict):
        raw = _deep_merge(raw, overrides)
    else:
        for item in overrides or []:
            raw = _deep_merge(raw, _parse_override(item))
    return raw


def load_config(mode: str = "romeo", overrides: list[str] | dict | None = None,
                base_file: Path = BASE_FILE) -> StrategyConfig:
    return build(raw_config(mode, overrides, base_file))
