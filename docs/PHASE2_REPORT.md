# CRT Robot — Phase 2 Report (CRT detector, context layers, entry models, modes)

Branch `crt-robot-phase2` (based on `crt-robot-phase1`, plus the research
branch with rulebook v0.2), written 2026-11-10.

**No real market data was used in this session and no strategy performance
is reported.** Dukascopy refuses cloud IPs (see `docs/PHASE1_REPORT.md` §1).
Every number in the tests comes from synthetic paths (random walks, or
straight-line drawings of CRT shapes) and only proves that the code does
what the rule says. Run the commands in §9 on your Mac once the data is
downloaded.

## 1. What was built

```
config/strategy/
  rulebook_v0.2.yaml      rulebook section 7, every key, v0.2 defaults; alt values in comments;
                          "PHASE 2 (PROPOSED)" switches marked; plus the explicit clock section
  modes/romeo.yaml        overlay: Romeo structure, C3 entries (model #1 / true MSS), 50% + opposite extreme
  modes/sham.yaml         overlay: D1 bias, 4H framing CRT, timed 15m purge, 15m OB, 3R, no Asia
  modes/hybrid.yaml       overlay: Romeo structure + Sham timing + either entry family
config/news/fomc.yaml     FOMC statement dates 2015-2026 for the CRT-R66 blackout (compiled from memory: VERIFY)
crt_robot/crt/
  config.py     typed frozen dataclasses; unknown keys / bad values raise; overrides "a.b=value";
                check_implemented() refuses alternatives with no code yet; fingerprint() for the runs log
  bars.py       closed-bar arrays from the Snapshot; derived M (monthly) and W_MON (Mon-Fri weeks);
                cache keyed by closed-bar counts (look-ahead safe)
  setup.py      Setup / Check / KeyLevel types; every condition logged as pass / fail / score / info / pending
  detector.py   C1 (mother-candle rule), C2 classification, Sunday-stub filter, C3 progress
  keylevels.py  5 key-level types + BOS origin + variants; "reached by C2"; distance; G-01 score; select
  context.py    bias (R06, R08, R15), market profile (5 phases + outcome table, sham4, romeo_swings),
                dealing range (G-09) / rebalance (R16), killzones, macros (hour | ICT), purge hours,
                refined key times, Asia block, 1/5/9, TS at open, Monday expansion, news blackout
  smt.py        PeerFeed (peer snapshot at or before now), Romeo candle SMT, direct / inverse pairs
  entries.py    model #1 (wick | body ref, C2 trigger -> retest | skip), true MSS + OTE / full retrace,
                Sham OB entry (near edge | open | mid, premium clamp), LTF CRT inside C2
  strategy.py   CRTStrategy.on_bar(snapshot, state) for the Phase 1 engine; romeo / hybrid ("C2-close"
                flow) and sham ("framing" flow); stops, targets, partial, time exits, Friday rules,
                invalidation, account limits
  report.py     setups CSV + summary markdown (counts by mode, symbol, TF, weekday, hour, reasons, rule)
crt_robot/run.py          CLI: backtest | setups | report (tuning period only)
crt_robot/backtest/       engine: tp1 partial take-profit (one trade row per trade), ModifyStop action,
                          StrategyState.entries_total
crt_robot/data/mtf.py     Snapshot.closed_times / base_times / now_ns / has_tf (read-only accessors)
crt_robot/data/synthetic.py  from_waypoints(): straight-line minute paths for test drawings
crt_robot/tests/crt/      84 new tests (config, detector, key levels, context, entries, SMT,
                          integration, look-ahead audit per mode, rule-level, CLI)
```

Test suite: **195 passed** (Phase 1's 108 + 3 engine tests + 84 Phase 2), Python 3.13, about 1.5 minutes
(the per-mode look-ahead audits are most of it).

## 2. Clock decisions (now explicit config)

| Item | Rulebook v0.2 | Phase 1 | Phase 2 default (config key) | Alternative |
|---|---|---|---|---|
| 4H grid | 01/05/09/13/17/21 NY | broker clock NY+7h gives exactly this | same (`candles.h4_grid_first_open: "01:00"`) | `"00:00"` grid: not built |
| Daily candle | 00:00 NY (C-03) | both `D` (17:00 broker day) and `D_NY` built | **`D_NY`** (`clock.daily_candle`, must match `candles.daily_open: "00:00"`) | `D` with `daily_open: "17:00"` |
| D_NY Sunday stub (Sun 17:00–24:00) | – | kept as its own bar | never a CRT / bias candle (`clock.skip_sunday_stub: true`) | `false` |
| Weekly range | Sunday 17:00 → Friday 17:00 (`week_range_from: sun_1700`) | `W` = broker week | **`W`** (`clock.weekly_candle`) | `W_MON`: Mon–Fri weeks aggregated from D_NY, with `week_range_from: mon_0000` |
| Weekly open price | Sunday 17:00 (`week_open: sun_1700`) | `weekly_open(mode)` | `sun_1700` | `mon_0000` |
| Monthly | first calendar day | not built | aggregated from closed daily bars, closed at the next month's 00:00 NY | – |

The loader refuses contradictory settings (e.g. `daily_open: "17:00"` with `daily_candle: D_NY`).
Note for overrides: YAML reads an unquoted `17:00` as a number, so write `--set 'candles.daily_open="17:00"'`.

Key-level timeframes follow `kl_tf_for_htf` (4H CRT → D levels, D → W, W → M), so with the defaults a 4H
CRT reads its levels from **D_NY** candles and its parent bias from **D_NY**.

## 3. How each mode works

**romeo / hybrid ("C2-close" flow).** At every close of a CRT-timeframe bar (romeo: 4H, D, W; hybrid: 4H, D)
the bar is C2: C1 = the bar before, or the mother candle (≤ `max_inside_bars` inside bars). C2 is classified
(DEF-05). Then, in this order, each gate is logged: close back inside (required or scored per TF), parent-TF
close/wick bias, no active higher-TF CRT against it, market profile, correct premium/discount half, key level
reached by C2's wick, timed purge (hybrid only, or Romeo with `romeo_use_killzones`), weekday of the sweep,
Monday-expansion week, ≥ 3 confirmations, SMT (score). A passing setup is armed for candle 3. On each LTF
close the entries in `entry_set` run (model #1, true MSS / OTE, and in hybrid also the 15m OB). Before
entry: 50% reached → skip; decisive closes beyond the sweep → invalid; C3 close → expired. At entry: price
below C3's open (bull), not in the mid-range band, no Asia block (hybrid), no FOMC day, account limits.
Order: stop by entry type; TP1 = CRT 50% with a 50% partial, final target = C1's opposite extreme; exit at
C3's close; flat Friday 16:00; Friday target capped at 2R.

**sham ("framing" flow).** At each close of a 4H candle that opens at 21:00, 01:00 or 05:00 NY, the D1 bias
(CRT-R08 matrix) sets the direction (neutral → no trade). The 15m path then waits for the first purge of the
candle's extreme after it closed; it must be in a key time (killzone, macro or purge hour). The purge may
reach the key level later in the killzone (CRT-R23: the setup waits until the killzone ends). Then the same
context gates run, with the dealing range on the 4H and the rebalance rule on. Entry: a 15m OB whose candles
include the purge, engulfed in key time, limit at the near edge (never in the premium part of the dealing
range), stop beyond the OB, 3R target (2R Friday), expiry at the end of the killzone, no new orders 20:00–02:00.

## 4. Rule coverage

I = implemented, P = partial, N = not implemented, L = logged only. Tests: `cfg` test_config,
`dk` test_detector_keylevels, `cx` test_context, `en` test_entries, `it` test_strategy_integration,
`ru` test_strategy_rules, `cli` test_run_cli, `eng` test_engine (all under `crt_robot/tests/`).

| Rule | What | Status | Test |
|---|---|---|---|
| CRT-R01 | name HTF / LTF / parent / purpose | I (Setup fields + `htf_named` check) | it |
| CRT-R02 | HTF ≥ 4H | I (`htf_allowed`; M and 1H refused as unimplemented) | cfg |
| CRT-R03 | TF pairs | I (`tf_pairs`) | it |
| CRT-R04 | Sham stack D / 4H / 15m | I | it (sham) |
| CRT-R05 | no LTF CRT against the active HTF CRT | I (live higher-TF setups) | ru |
| CRT-R06 | close / wick bias | I | cx |
| CRT-R07 | bias only with key level + profile | I (all three are gates) | it |
| CRT-R08 | Sham D1 structure × close matrix | P (the "retracement reached EQ → neutral" clause is not coded) | cx, it |
| CRT-R09 | D/W bias CRT confirmation and held target | N | – |
| CRT-R10 | prefer the Monday bias CRT | N | – |
| CRT-R11 | no opposite patterns while a target is pending | P (via R05 and R57) | ru |
| CRT-R12 | bias re-derived each time | I (stateless) | it |
| CRT-R13 | neutral days | P (neutral Sham bias only; Monday counter-SMT and ranging-day proxy not coded) | it |
| CRT-R14 | weekly time theory | P (sweep weekday Mon–Wed; no "Thursday + model #1" preference) | ru |
| CRT-R15 | structure label | I (proxy on close-based BOS/MSS) | cx |
| CRT-R16 | Sham rebalance first | P (EQ rule; KOD-S and all-time-high exceptions not coded) | cx, it |
| CRT-R17 | delivered → counter allowed | N (`allow_delivered_counter: true` refused) | ru |
| CRT-R18 | key level required, reached by C2 | I | dk, it |
| CRT-R19 | key-level candidate set | I (old high/low, BOS origin, FVG, OB, RB; variants prev_period_hl, candle_open, weekly_wick_50; breaker N) | dk |
| CRT-R20 | no buy before the key level is touched | I (C2 / model candle / MSS low must reach the CRT extreme and level) | dk, en |
| CRT-R21 | premium / discount half | I (DR on the parent TF; parent-candle 50% fallback, PROPOSED) | it |
| CRT-R22 | key-level TF one step up (+ secondary) | I | cfg, it |
| CRT-R23 | key level tagged in time | P (levels must exist before C2; Sham waits until the killzone ends) | it |
| CRT-R24 | CRT high / low / 50% from C1 wicks | I | dk |
| CRT-R25 | C2 breakout → drop | I | dk, it |
| CRT-R26 | mother candle | I | dk |
| CRT-R27 | purge only after C1 closed | I | en, it |
| CRT-R28 | Sham framing candle | I (opens 21/01/05, bias, half, rebalance; re-selection = each framing candle is a new candidate) | it |
| CRT-R29 | close back inside per TF and mode | I (+ C-04 score when not required) | it |
| CRT-R30 | C3 entries only | I (C2 trigger → retest in C3 or skip) | en |
| CRT-R31 | bias direction only | I (`bias_gate: hard`, `score` alt) | it |
| CRT-R32 | timed purge (Sham) | I (killzone / macro / purge hour) | cx, it |
| CRT-R33 | OB in key time | I | en |
| CRT-R34 | no Asia / midnight trading | I (`use_asia_block`) | cx |
| CRT-R35 | Romeo weekly template | P (sweep weekday filter, Monday-expansion skip; Monday-chop detection not coded) | ru, cx |
| CRT-R36 / G-23 | TS at the open of the new candle (or late in it) | I (score, both modes) | cx |
| CRT-R37 | wait for the entry model; expiry | I (C3 close / end of killzone) | it |
| CRT-R38 | Romeo entries | I | en |
| CRT-R39 | model #1 | I (wick default, body alt, thick candle) | en |
| CRT-R40 | true MSS retrace | I (OTE zone or full retrace) | en |
| CRT-R41 | OTE 0.50–0.79, close activation | P (touch trigger; `ltf_ts` trigger and union / intersection fib not coded) | en |
| CRT-R42 | SMT confirmation | P (SMT scored, optional gate; `model1_then_mss` order not coded) | cx, it |
| CRT-R43 | Sham 15m OB entry | I | en, it |
| CRT-R44 | entry beyond C3's open | I | it |
| CRT-R45 | no chasing | P (50% reached → skip; stage counter not needed with one entry per setup) | ru |
| CRT-R46 | confluence score | I (logged; `min_confluence` log only, as in the rulebook) | it |
| CRT-R47 | no OB entry in premium | I | en |
| CRT-R48 | re-entries | N (`max_entries_per_setup > 1` refused) | ru |
| CRT-R49 | model #1 stop | I | en, it |
| CRT-R50 | TS / MSS stop; OTE stop | I (`ote_stop: leg_origin`, `fib_079`) | en |
| CRT-R51 | OB stop | I | en |
| CRT-R52 | daily-FVG-fill stop | I | ru |
| CRT-R53 | 50% partial + opposite extreme | I (engine tp1 partial) | eng, it |
| CRT-R54 | intermediate targets | N (alternatives refused) | cfg |
| CRT-R55 | Sham 3R | I | it |
| CRT-R56 | time exit | I (`end_of_htf_candle`; `end_of_killzone` N) | ru |
| CRT-R57 | opposing SMT cancels the target | I (close or break-even when an opposite CRT with SMT gets a model #1 / MSS) | – (no fixture yet) |
| CRT-R58 | decisive closes beyond the sweep | I (before entry and in the trade; first-close warn / break-even) | ru |
| CRT-R59 | 50% hit counts as a win | P (tp1 partial booked and flagged per trade; `c3_progress` helper) | dk, eng |
| CRT-R60 | Sham invalidation | I (no OB by expiry; close beyond by > ATR) | it |
| CRT-R61 | every invalidation has a reason | I | it |
| CRT-R62 | 1% risk | I (Phase 1 engine) | Phase 1 |
| CRT-R63 | −2% NY-day stop | I (engine; account-wide across symbols still N) | Phase 1 |
| CRT-R64 | ≤ 1 trade a day, ≤ 2 a week | I (per symbol) | ru |
| CRT-R65 | stop after the setup's target | P (setup done; Sham `day_done` not coded) | it |
| CRT-R66 | FOMC blackout | I (dates file hook, whole NY day) | cx, it |
| CRT-R67 | Friday 2R, flat by Friday 16:00 | I | ru |
| CRT-R68 | partial then hold; optional break-even | I (`be_after_tp1`) | eng |
| CRT-R69 | versioned rules | I (rulebook version + config fingerprint + overrides in the runs log) | cli |
| CRT-R70–R73 | Saturday / Sunday routine, weekly logs | N (Phase 3, reviews) | – |
| DEF-05/24 | candle outcomes, C1/C2/C3 | I | dk |
| DEF-08/09 | model candle, thick | I | en |
| DEF-10/12 | true MSS, OTE | I | en |
| DEF-15 | Sham OB | I (Phase 1 primitive + purge liquidity) | en |
| DEF-18 | SMT | I | cx |
| DEF-27 | mother candle | I | dk |
| G-01 | key-level choice | P (score proxy + BOS bonus; ranking is still a gap) | dk |
| G-04 | market profile | I (5-phase proxy + outcome table; sham4, romeo_swings alts) | cx |
| G-05 | closing-hour logic | L (purge minute in the 4H logged; `closing_hour_filter` first / last) | – |
| G-09 | dealing range | I | cx |
| G-11 | killzones / macros / purge hours | I | cx |
| G-14 | OTE leg end | I (`leg_end_atr` proxy) | en |
| G-20 | ≥ 3 confirmations | I | it, ru |
| G-26 | Monday expansion, mid-range | I (ranging-day and CBDR not coded) | cx, it |

## 5. Parameters that exist but Phase 2 does not read yet

Kept in the YAML so they stay switchable later; changing them has no effect today:
`bias.bias_crt_days`, `bias.bias_crt_target` (R09/R10), `bias.ranging_adr_frac`, `bias.near_target_atr`,
`bias.delivered_adr_mult`, `dealing_range.kod_s_dist`, `dealing_range.kod_r_requires_tp1`,
`crt.room_5am`, `timing.london_lunch`, `timing.cbdr_window`, `timing.index_killzones`,
`entry.ob_liq_tf_steps` (the KL-TF OB uses the same-TF swing proxy, `key_level.ob_liquidity`),
`entry.min_confluence` (log only by design), `entry.smt_confirm`, `targets.weak_ts_atr` (G-24),
`risk.max_open_risk` (one position per run), `risk.instruments`, `logging.*`.
Values with no code are refused at start-up by `check_implemented` (listed in `crt/config.py: UNIMPLEMENTED`),
e.g. `target_mode: swings_one_by_one`, `framing_model: room_5am`, `stop_mode: weekly_model_extreme`,
`news_events: [NFP, CPI]`, `structure_break: wick`, `htf_allowed: [M]`.

## 6. Known gaps (decisions or sources still needed)

- **G-05 closing-hour logic** (Sham): not taught anywhere we have. We log `purge_minute_in_h4` for every
  setup and offer `timing.closing_hour_filter: first | last` as a test, nothing more.
- **G-03 Romeo's six weekly possibilities**: not coded; no weekly shape classifier yet (`week_shape_mode`).
- **Key-level ranking (G-01 core)**: the selection is our score proxy (+1 unswept, +1 primary TF, +1 confluence,
  +1 correct half, +1 most visible, + BOS bonus) or `nearest`. Every setup logs the chosen level, its score and
  the number of candidates, so the report can show which types actually get picked.
- **OTE zone (C-06, G-14)**: a parameter, `entry.ote_zone` (0.50–0.79 default, 0.62–0.79 and 0.382–0.79 alts);
  the leg end is the `leg_end_atr` proxy.
- **Model #1 wick vs body (C-07)**: a parameter, `entry.model1_trigger_ref: wick | body`.
- **Model #1 triggered inside C2**: our own rule `crt.model1_c2_trigger: retest` (limit at the model candle in C3)
  vs `skip`. PROPOSED, not from a source; worth testing both.
- **Single-symbol runs.** The −2% day stop and the trade caps are per run (per symbol). A portfolio runner that
  shares equity across EURUSD, GBPUSD and XAUUSD is still Phase 3 work.
- **FOMC dates** in `config/news/fomc.yaml` were typed from memory in this session. Check them against the
  Federal Reserve calendar before trusting the blackout.
- **Dukascopy DXY symbol** (`DOLLARIDXUSD`, divisor 1e3) is still unverified (Phase 1). If it fails, SMT for
  EURUSD/GBPUSD still has the EURUSD↔GBPUSD pair.
- R09 / R10 (bias CRT), R13 ranging day, R16 exceptions, R17, R48, R54, R70–R73: not coded (§4).

## 7. Look-ahead safety

- The strategy reads prices only through the Snapshot (`MarketData`); it stores no DataFrame / array
  (`check_strategy_holds_no_data` passes). Caches hold values derived from closed bars, keyed by the
  number of closed bars, so the same history always gives the same value.
- Key levels must be knowable before C2 opens; C3's open / close come from the forming bar only once it
  has started; peers (SMT) are read at the latest peer bar that closed at or before `now`.
- `lookahead_audit` (Phase 1: decisions on full data = decisions on data cut at each checkpoint) passes for
  **romeo, sham and hybrid**, on the scripted CRT drawing and on a 4-week random walk with relaxed gates
  (so that there are decisions to compare). Run it again on real data (§9).

## 8. Speed

On this container: about 19,000 one-minute bars per second for the default Romeo mode (synthetic data),
so roughly 3–4 minutes per mode and symbol for 10 years of 1m data. `--base 15m` is much faster with
coarser fills (all fill rules stay conservative). Real data may form more setups and run slower.

## 9. Commands for your Mac

```bash
cd FX-Signal-Copier-Telegram-Bot
git fetch origin && git checkout crt-robot-phase2 && git pull
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest -q                         # expect 195 passed

# 1) data (Phase 1 downloader; resumable; stops with BLOCKED if refused)
python -m crt_robot.data download --symbols EURUSD GBPUSD XAUUSD XAGUSD DXY --start 2015-01-01
python -m crt_robot.data quality            # writes docs/DATA_QUALITY.md

# 2) one backtest, tuning period only (--end is exclusive; 2025-05-01 is the latest allowed)
python -m crt_robot.run backtest --mode romeo --symbol EURUSD --start 2016-01-01 --end 2025-05-01
python -m crt_robot.run backtest --mode sham  --symbol GBPUSD --start 2016-01-01 --end 2025-05-01 --base 15m
#    -> runs/backtests/<run_id>/{trades.csv, setups.csv, setups_summary.md, summary.json}
#    -> one line appended to runs/runs_log.jsonl (mode, rulebook version, config fingerprint, overrides)

# 3) the setups report: every mode x symbol, CSV + summary markdown
python -m crt_robot.run setups --start 2016-01-01 --end 2025-05-01 --base 15m --out reports/setups
#    -> reports/setups/setups.csv, reports/setups/setups_summary.md, one sub-folder per mode_symbol

# 4) switch any parameter (repeatable --set); examples of the open questions
python -m crt_robot.run backtest --mode romeo --symbol EURUSD --start 2016-01-01 --end 2025-05-01 \
    --set entry.ote_zone=[0.62,0.79] --set entry.model1_trigger_ref=body --set crt.model1_c2_trigger=skip
python -m crt_robot.run backtest --mode romeo --symbol EURUSD --start 2016-01-01 --end 2025-05-01 \
    --set 'candles.daily_open="17:00"' --set clock.daily_candle=D          # broker-day daily candle

# 5) rebuild one report from several runs
python -m crt_robot.run report --inputs runs/backtests/*/setups.csv --out reports/setups_all

# 6) look-ahead audit on real data (one mode, a few months)
python - <<'EOF'
from crt_robot.backtest.audit import lookahead_audit
from crt_robot.crt.config import load_config
from crt_robot.crt.strategy import CRTStrategy, view_timeframes
from crt_robot.data import dukascopy
from crt_robot.data.instruments import get_instrument
df = dukascopy.load("EURUSD", "2019-01-01", "2019-04-01")
for mode in ("romeo", "sham", "hybrid"):
    cfg = load_config(mode)
    print(mode, lookahead_audit(lambda: CRTStrategy(cfg, "EURUSD"), df, get_instrument("EURUSD"),
                                view_timeframes(cfg), n_checks=4))
EOF
```

What to send back: `reports/setups/setups_summary.md` (counts only) and, if you want a review of the
rules, a few `setups.csv` rows of taken and rejected setups. Do not commit `data_cache/`, `runs/backtests/`
or `reports/` (all git-ignored).

## 10. Next

1. Run §9 on real data: data quality report, then the setups report per mode. Read the rejection table first:
   it shows which gate removes most setups and whether the counts per week are near the sources' 1–2.
2. Fix in advance the minimum trade count, the "nearby values also work" rule and the removal rule
   (BUILD_PLAN §3, §6), then tune on the tuning period only.
3. Portfolio runner (shared equity, account-wide −2%, trade caps across symbols).
4. Then: 2× costs, Monte Carlo, one holdout run per chosen mode, and the alerts-only stage.
