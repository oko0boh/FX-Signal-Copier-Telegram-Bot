# CRT Robot — Phase 1 Report (foundation)

Branch `crt-robot-phase1`, written 2026-11-09. This phase built the
Architecture and Proof plumbing from `docs/BUILD_PLAN.md`: data, a
look-ahead-safe multi-timeframe view, primitives, and a validated
backtester. **No CRT entry strategy was built or tuned, and no strategy
profit is reported.** All numbers below come from synthetic test data and
only show that the tools work.

## 1. Blocker: no market data yet

The Dukascopy data host refused us on the **first request**:

- Host: **`datafeed.dukascopy.com`**
- Reply: `HTTP 429 {"error": "Too Many Requests. For instructions, see: https://wiki.dukascopy.com/en/development/data-export/"}`. Some attempts got a connection reset instead.
- The wiki page it points to no longer describes the datafeed. It documents a
  **requester-pays AWS S3 bucket** (`cfg-public-proper-wallaby`, `eu-west-1`).
  That route needs **your own AWS credentials**, and your AWS account pays
  the request and transfer fees.

So `data_cache/` is empty and **no data was invented**. The downloader is
built and tested against the real `.bi5` file format, using synthetic files.
Options:

1. **Run the downloader from your own machine** (a home IP is usually not
   rate-limited the same way):
   `pip install -e . && python -m crt_robot.data download --start 2015-01-01`.
   It writes `data_cache/dukascopy/{SYMBOL}/{YYYY}/{MM}.parquet`, pauses
   between requests, resumes where it stopped, and stops cleanly with
   `BLOCKED: …` if refused. The parquet files can then be copied into a
   session.
2. **Use the S3 bucket**: needs an AWS key pair and an S3 reader for the
   bucket's layout. The wiki describes daily *tick* files; we would build
   1m bars from ticks. Not built yet.
3. **Broker history via MetaAPI** for a cross-check. It is shorter, but it is
   the exact broker clock and broker prices we will trade. Planned for later
   anyway (the "backtest vs live" check in BUILD_PLAN §4).

Also unverified: the Dukascopy dollar-index symbol (`DOLLARIDXUSD`, divisor 1e3).

## 2. What was built

```
crt_robot/
  timeutil.py         NY time, broker clock = NY + 7h (GMT+2/+3 on US DST dates)
  config.py           paths (data_cache/, config/, runs/)
  data/
    instruments.py    EURUSD, GBPUSD, XAUUSD (tradeable); XAGUSD, DXY (data only); cost params
    dukascopy.py      bi5 decoder/encoder, BID+ASK day fetch, monthly parquet store, resume, DataHostBlocked
    quality.py        gaps, duplicates, unsorted, weekend bars, spikes, bad OHLC, negative spread, coverage
    resample.py       15m/1H/4H/D/D_NY/W on the broker clock, close_time + complete flags
    mtf.py            MultiTimeframeView / Snapshot: closed HTF bars + forming bar (complete=False)
    synthetic.py      random-walk minutes for TESTS ONLY
    __main__.py       CLI: `python -m crt_robot.data download|quality`
  primitives/
    candles.py        body/range/mid/direction, Wilder ATR, thick (DEF-09)
    swings.py         fractal N (known at i+N); ICT STH/ITH/LTH levels with per-level known_at
    liquidity.py      sweep vs close-beyond, DEF-05 outcome classifier, turtle soup, unswept
    fvg.py            FVG with CE; touched / CE / full-fill indices; open-at-t (touch|half|full)
    order_block.py    Sham OB (liquidity + engulf, body vs full-candle extent, growing group)
    rejection_block.py wick beyond the bodies at a confirmed swing
    structure.py      BOS vs true MSS (DEF-10), close-based, known swings only
    dealing_range.py  EQ, premium/discount, position, latest range at t
    time_windows.py   killzones, macros (hour or ICT windows), 1/5/9 4H rhythm + minute-in-4H
    levels.py         previous day/week high-low, midnight open, weekly open (mon_0000 | sun_1700)
  risk/
    sizing.py         lots for 1% risk (commission included, rounded down, skip below min lot)
    daily_stop.py     -2% New York-day guard (mark-to-market, blocks until next NY midnight)
  backtest/
    orders.py         Order (market|limit|stop, stop, target, expiry, exit_at), ClosePosition, CancelPending
    fills.py          bid/ask fills, conservative intrabar rules
    engine.py         event-driven bar-by-bar engine, holdout guard, runs log, data-hoarding check
    metrics.py        R stats, t-stat, profit factor, drawdown
    robustness.py     Monte Carlo of trade order (permute / bootstrap), cost_stress (1x, 2x, ...)
    audit.py          look-ahead audit (full vs truncated decisions)
    splits.py         tuning vs LOCKED holdout from config/data_split.toml
    runlog.py         append-only JSONL log of every run (runs/runs_log.jsonl)
  tests/              108 tests, one file per module
config/data_split.toml   holdout_start = 2025-05-01 (last 18 months), locked_on 2026-11-09
```

### Clock and candle conventions

| TF | Opens (NY) | Close | Notes |
|---|---|---|---|
| 15m / 1H | clock grid | open + length | |
| 4H | 01, 05, 09, 13, 17, 21 | open + 4h | broker 00/04/08…, matches rulebook 0.3 |
| `D` | 17:00 | next 17:00 | broker day (user decision: broker clock) |
| `D_NY` | 00:00 | next 00:00 | rulebook 0.3 / C-03 default `daily_open: "00:00"` |
| `W` | Sun 17:00 | Fri 17:00 | broker week; = `week_range_from: sun_1700`, `week_close: fri_1700` |

The broker clock follows US DST, so it is NY + 7h all year, including the
weeks when only the US or only Europe has switched (tested). DST changes
fall on Sunday 02:00 NY, while the market is closed, so no bar crosses one.

**Your decision needed (C-03):** the brief says to build candles on the broker
clock, which makes the daily candle 17:00–17:00 NY. The rulebook's default
daily candle is midnight NY. Both exist (`D` and `D_NY`). Phase 2 must pick
one per rule. `D_NY` also has a short Sunday-evening candle (17:00–24:00);
we keep it separate rather than merging it into Monday.

## 3. No look-ahead, by design and by test

- `Snapshot.closed(tf)` returns only bars with `close_time <= now` (now = the
  close of the current base bar). `Snapshot.forming(tf)` returns the
  partial bar marked `complete=False`. Its `close` is the latest price, never
  the final close.
- Negative offsets and `closed_bar(back=0)` raise `LookAheadError`. Array
  accessors are read-only and cut at `now`.
- **Truncation invariance:** a snapshot built from the full data equals one
  built from data cut at `now`, for all timeframes (tested at random points).
- Every primitive reports `known_at` (swings at i+N, ICT levels when the
  next lower-level swing is known, FVGs at bar c, OBs at the engulf bar,
  MSS at the close). Levels (PDH/PDL, opens) are tested truncation-invariant.
- Orders decided at bar i fill from bar i+1 at the earliest.

## 4. Backtester validation results

Synthetic EURUSD minute data, 2024-01-07 to 2024-03-30, default costs
(spread 0.8 pip, $7/lot round trip, 0.2 pip slippage), 1% risk, -2% daily stop.

| Test | Result | Pass rule |
|---|---|---|
| (a) planted edge: +10 pips drift 09:00–10:00 NY, buy at 09:00 | 60 trades, mean **+0.47R**, t = **7.4**, win 87% | t > 3 |
| (a) same at **2x costs** | mean +0.28R, t = 5.0 | edge survives, smaller |
| (a) control: same strategy on pure noise | mean −0.12R, t = −1.4 | t < 2 |
| (b) coin-flip entries, zero cost | 679 trades, mean +0.05R, t = 1.4 | \|t\| < 2.5 |
| (b) coin-flip entries, with costs | 479 trades, mean **−0.22R**, t = −5.8 | mean < 0 |
| (c) cheater reads the forming 4H final close | +0.46R, t = 9.9 in the backtest, **caught** by `lookahead_audit` | must raise |
| (c) honest strategies (closed 4H only, timed, random) | pass the audit | no false alarm |
| (c) strategy holding the full DataFrame | refused (`LookAheadRisk`) | must raise |
| Monte Carlo (2000 permutations of the planted trades) | max DD p5/p50/p95/p99 = 1.0/1.3/2.1/2.9% | ordered percentiles |

The cheater's in-sample "edge" is as strong as the planted one. That is why
the audit has to be run on every Phase 2 strategy.

Fill rules (conservative): when a bar hits both the stop and the target,
the stop fills. On a limit or stop entry's own bar the target is ignored but
the stop is not. A gap through the stop fills at the worse open. Longs buy at
the ask and sell at the bid, shorts the reverse. Market and stop fills pay
slippage.

Test suite: **108 passed** on Python 3.11.18 and 3.13 (pytest, about 21 s).
Speed: about 53k one-minute bars per second, so roughly 70 s per instrument for 10 years of 1m data.

## 5. Data split and runs log

- `config/data_split.toml`: tuning = 2015-01-01 to 2025-04-30; **holdout =
  2025-05-01 onward (locked)**.
- `Backtester(...)` raises `HoldoutLockedError` if the data reaches the
  holdout, unless `EngineConfig(allow_holdout=True)` is passed. `DataSplit.tuning(df)` gives the tuning slice.
- Every `run()` appends one JSON line to `runs/runs_log.jsonl` (override with
  `CRT_RUNS_LOG`). Each line holds: run id, time, git commit, strategy, params, engine
  config, data span, `uses_holdout`, and the summary. `previous_holdout_runs()`
  lists earlier holdout runs per strategy. Tests write to a temp log.

## 6. Known limitations

- **No real data yet** (section 1), so no data-quality report. Coverage numbers are not measured yet.
  `python -m crt_robot.data quality` writes `docs/DATA_QUALITY.md` once data exists.
  On real data, expect short gaps at the 17:00 NY rollover and around holidays.
- **Costs are placeholders** (`instruments.py`), not measured from the broker.
  The data spread can be used instead (`use_data_spread=True`), but the
  widening at the 17:00 rollover is not modelled separately. Swaps are not modelled.
- **One instrument and one position per run.** The −2% daily stop is checked
  per run, but the real limit is account-wide. Phase 2 needs a portfolio
  runner across EURUSD, GBPUSD and XAUUSD that shares equity and the daily stop.
- Daily stop is checked at bar closes (marked to market). A large intrabar fill can overshoot −2% by up to one trade.
- Order-block liquidity context (HTF level touched or purged, SMT purge) is
  passed in as a flag array; computing it belongs to Phase 2.
- Rejection-block "swing candles" = swing bar ± `window`; ICT ties (equal
  highs) are never swings (strict comparison), per rulebook section 1.
- The audit catches cheating through the engine's data and the
  data-hoarding check catches stored arrays. A strategy that reads prices
  from a global or a file is outside what either can see. Rule: strategies
  read prices only through `Snapshot`.
- Spike detection is a heuristic (12× the rolling median move). It flags
  bars for review and never deletes them.
- Dukascopy fills empty minutes with flat zero-volume bars; we drop them so
  gaps stay visible. The resampler therefore never invents bars.

## 7. What Phase 2 needs

1. **Data unblocked** (section 1), then the quality report, then measure
   each instrument's behaviour (BUILD_PLAN §2: trend vs mean reversion,
   how often sweeps reverse, the 1/5/9 time profile, using
   `h4_rhythm`, `turtle_soup` and `classify`).
2. **CRT detector**: C1/C2/C3 on closed HTF bars (DEF-24, `classify` for
   DEF-05). It also needs the inside-bar mother-candle rule (DEF-27,
   `max_inside_bars`) and the per-TF `require_close_inside` setting (C-04).
3. **Key-level module** combining the primitives into the five `kl_types`
   (old high/low purged, FVG, OB, RB), plus `kl_select`, `kl_max_dist_atr`
   and the IPDA 20/40/60-day lookbacks.
4. **SMT**: an aligned multi-instrument view (EURUSD/GBPUSD/DXY inverse,
   XAUUSD/XAGUSD) using the same MTF snapshot logic. The data-only
   instruments are already in `instruments.py`.
5. **Strategy modes** from rulebook section 7: `romeo` (Model #1, true MSS,
   OTE, 1/5/9 timing), `sham` (OB/FVG in killzones, Asia block, R targets)
   and `hybrid`. Load the section 7 YAML as the parameter source, and
   record its version in the runs log.
6. **Portfolio runner**: shared equity, account-wide −2% daily stop,
   `max_trades_per_day/week`, `max_open_risk`, FOMC blackout calendar,
   Friday-flat time, and no weekend holds.
7. **Fix in advance** the minimum trade count, the robustness neighbourhood
   rule ("nearby values also work") and the removal rule. Then run each
   mode through: tuning → `lookahead_audit` → 2× costs → Monte Carlo → **one** holdout run.
8. Open decisions for you: daily candle `D` vs `D_NY` (C-03), weekly open
   price `mon_0000` vs `sun_1700` (C-02; both implemented), and real broker
   costs from the MetaAPI symbol specs.
