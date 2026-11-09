# CRT Robot — Build Plan (v2)

v1 had four steps: rules → backtest → paper → live. v2 adds the process from
the "build a trading system" course (`research/notes/bot-building/gJLKVsIqiTE.md`,
ALPHA framework). We take its process, not its strategy or its profit claims.

**A bot is one rule that sends orders. A system adds data checks, tests, a
risk layer that can veto orders, alerts, and reviews.** We build a system.

## 1. Architecture
- Python, one module per job: `data/`, `crt/` (signals), `risk/`, `execution/`, `alerts/` (Telegram, reused from `run.py`), `backtest/`, `reviews/`.
- **The backtest and the live bot share the same signal code.**
- Broker keys go in a hand-typed `.env` (git-ignored). Claude never reads them.
- Each module is built in its own small step, with exact numbers and a test at the end.

## 2. Logic (CRT rulebook → seven parts)
Every setup in `research/notes/CRT_RULEBOOK.md` is written as:
**market · setup · filter · entry · exit · stop · size**.
Before choosing pairs, measure each instrument's behaviour: does it trend or snap back, how often do sweeps reverse, and what does the 1/5/9 time profile look like.

## 3. Proof (backtest)
1. **Test the backtester first:**
   - a planted edge must be found
   - pure noise must show no edge
   - a look-ahead test must pass. Higher-timeframe candles may only be used *after they close*; this is the biggest risk with CRT.
2. **Split the data:**
   - tune on older years
   - keep a **locked holdout** (e.g. the latest 12–18 months)
   - run the holdout **once**
3. **Log every parameter combination tried.** A result counts only if nearby values also work.
4. **Costs:** realistic spread, commission and slippage per instrument. Re-run at **2× costs**, and run Monte Carlo on the trade order.
5. **Minimum trade count is set in advance.** CRT gives about 1–2 trades a week per instrument, so we test several instruments and years of data to reach enough trades.

## 4. Harness (live plumbing)
- Stops held at the broker, not only in our code.
- Unique order IDs, so an order can't be sent twice.
- Position check against the broker on every loop.
- A lock file, so only one bot runs at a time.
- Daily loss limit, weekly drawdown pause, and a news/FOMC blackout.
- Telegram alerts for every signal, fill, error and pause.
- A test that backtest and live signals match over the last 60 days.
- Runs on a VPS with a live intraday data feed.

## 5. Rollout
1. **Alerts only.** The bot posts setups to Telegram; nothing is traded.
2. **Approve each trade.** You tap to approve, and it trades on a demo account.
3. **Automatic on demo.**
4. **Small live**, only if demo results match the backtest within limits we write down in advance.

## 6. Adapt (monitor)
- Every week, compare live/demo results with the backtest and explain every gap.
- **Removal rule, written now:** turn a strategy off at **2× its worst tested drawdown**.
- **Never change rules after a bad week.** Rule changes go back through Proof.
- A weekly AI review may fix code bugs, but it may not change trading rules and it never places trades.

## 7. X trader feeds
Unchanged: browser-read, votes only, and counted only after 30 tracked setups (`research/x-traders/`).

## Decided
- Instruments: **EURUSD, GBPUSD, XAUUSD (gold)**. SMT comparisons: EURUSD vs GBPUSD (and DXY), gold vs silver (XAGUSD), using data only.
- Risk: **1% per trade**. Daily loss limit: **-2%** (stop for the New York day).
- Broker: **MT5 via MetaAPI** (`metaapi-cloud-sdk`), reusing the connection and lot-size logic from `run.py`. Candle times come from the broker server clock (GMT+2/+3, which aligns 4H opens with 01/05/09 New York).

## Still needed
- Romeo's book notes (being written in the user's Mac session).
- VPS choice (MetaAPI runs in the cloud, so the bot itself can run on a small VPS or Render).
