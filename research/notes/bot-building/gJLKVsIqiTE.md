---
source_id:        other-bot-building
video_id:         gJLKVsIqiTE
title:            (not stated on screen in the transcript; the speaker calls it "a full master course on how to build your own trading bot with Claude")
speaker:          Brendan (says he spent 3+ years in investment banking and studied math/econ at UCLA; sells a paid community and 1:1 builds; channel name not stated, his test bot is named "AI pathways claudebot")
url:              https://www.youtube.com/watch?v=gJLKVsIqiTE
length:           about 3:07:45
studied_on:       2026-11-09
transcript:       research/raw/transcripts/other/gJLKVsIqiTE.txt (auto captions, English, all 700 lines read)
---

Timestamps are as in the transcript: `mm:ss` under one hour and `h:mm:ss` after that.

## Summary

This is a 3-hour walkthrough of building a daily-bar ETF trading "system" with Claude (or ChatGPT Codex) in a local desktop-app project. The speaker's framework is called **ALPHA**: **A**rchitecture (project folder, house rules, system layout), **L**ogic (goal, timeframe, data, asset study, regimes, exact rules), **P**roof (train/locked-test split, test the backtester itself, a gated funnel for ideas), **H**arness (Alpaca paper bot, schedule, safety checks, Telegram alerts) and **A**dapt (paper-vs-backtest reconciliation, kill lines, sleeve rotation, scheduled reviews). His example account is a "core" (QQQ above its 200-day MA, else gold) plus up to three short-term "sleeves" (RSI(2) dip buys, 50-day breakouts) chosen by a funnel. His main point is that the code is the easy part. What decides whether a bot works is the setup and how hard you test the rules (2:44:22). He shows backtest results and no live track record.

## Why bots fail (his claims)

- **A "bot" is just one rule sending orders.** Nothing checks the incoming data, nothing tests whether the rule works, and nothing stops it if something breaks. A "system" adds data checks, tests, a risk layer that can veto orders, alerts and weekly reviews. *(5:53–6:57)*
- **Vague prompts** ("build me a trading bot") give one big file with strategies and dates the model picked itself, usually no costs, and nothing that shows whether it works. The same prompt run twice gives a different bot. *(13:05–13:54)*
- **Strategy decay.** Short-term strategies stop working as regimes change, so they must be retired and replaced. *(4:32, 30:49, 1:00:37, 1:45:16)*
- **A strategy that does not fit the asset.** A dip buy works on assets that snap back and loses on assets that keep falling. *(34:35, 51:58–52:15)*
- **Ignoring the regime.** The same dip bounces above the 200-day MA and keeps falling below it. *(1:03:17–1:03:48)*
- **No risk layer.** Twenty strategies fire on the same day and use all the capital. *(26:14–26:47)*
- **The top 10 mistakes** *(2:55:25–3:01:56)*:
  1. Tuning a parameter until the backtest looks perfect, which gives a "spike" rather than a "hill" *(2:52:46–2:53:02 area; 2:51:41)*.
  2. Looking at the locked test and then changing the rule *(2:53:02)*.
  3. Look-ahead, such as deciding on the close and filling at that same close *(2:53:53)*.
  4. Leaving out costs *(2:54:43)*.
  5. Trusting a backtester nobody checked *(2:55:46)*.
  6. Trusting a rule with few trades *(2:56:50)*.
  7. Survivorship bias, such as testing on today's S&P list *(2:57:23; also 1:36:54)*.
  8. Letting the AI make the trades *(2:58:28)*.
  9. Going too big too soon *(3:00:03)*.
  10. Quitting after a bad week *(3:00:34)*.

## Recommended architecture and process

**Workspace and AI use**
- Work in a desktop app on a local folder, not the browser, so the agent can read and write files, run backtests and run scheduled jobs. *(7:13–8:48)*
- Use the strongest model only for planning and safety reviews, and a cheaper model for building. *(11:29–12:50)*
- Keep a `CLAUDE.md`/`AGENTS.md` of house rules that every prompt inherits: data source, exact dates, the train/test split, costs, how a result is judged. *(16:20–17:26)*
- Use one module per prompt, with exact numbers, written-out rules, and a check (a chart, table or test run) at the end of each step. *(13:54–15:14)*
- Escalate in three levels: a one-off prompt, then a saved "skill", then a scheduled job. *(15:14–15:47)*
- A "fingerprint" output line checks that a rerun reproduced the expected result, because LLM output is not deterministic. *(21:23–22:27)*
- **Secrets:** never paste API keys into the chat. Type them by hand into `.env`, and give the agent a rule never to open, print or log that file. *(10:23–11:13, 2:00:36–2:00:52)*

**System layout** *(23:17–28:24)*
- Data → regime (trend: price above or below its 200-day MA; volatility: calm or wild) → strategies (core and sleeves) → risk (can block orders) → broker → log, alerts and dashboard.
- **Backtest and live bot share the same code** for data, regime, signals, risk and orders. *(28:07–28:24, 1:18:01, 2:00:52)*
- **The AI is only a limited layer on top of fixed rules.** Rules do the trading because they can be tested. The AI can only make a small, time-limited change (e.g. "hold gold 10 days" after reading a Fed statement), only on the slow core, because "AI is not instant". *(31:36–33:47, 1:49:21)*

**Logic**
- Decide in this order: goal (judged by **return per drawdown**), then timeframe, then market. *(34:52–36:13)*
- Daily bars are recommended for a first bot *(36:29–41:19)*:
  - the data is free;
  - it runs once a day;
  - costs stay small;
  - orders fill at the next open exactly as the backtest assumed;
  - nothing needs to watch the market live.
- The intraday downsides are paid data, a live feed, always-on hardware and slippage.
- Data *(41:35–48:44)*:
  - adjusted OHLCV;
  - one frozen history file for research, kept separate from the live copy;
  - yfinance for daily;
  - paid intraday from Databento, Massive or Alpaca, or bought once as files (FirstRate Data);
  - free crypto minute data from the exchanges.
- **Asset study before choosing a strategy** *(52:15–55:29)*:
  - Does the asset keep going after new highs? Measure the next 20 days after a 50-day high above the 200-day MA, needing at least 6 events.
  - Does it snap back after quick drops? Measure the next 5 days, needing at least 12 events.
  - Also measure correlation with stocks, behaviour when stocks fall, volatility, the "trend gap" and calm-vs-volatile move sizes.
- **Strategy-to-asset grid:** breakouts for "keeps going", dip buys for "snaps back", safe asset for "holds up". *(1:06:11)*
- **Seven-part exact rule:** market, setup, filter, entry, exit, stop, size. "If you can't fill in all seven of these rows, it's not ready to test." *(1:08:37–1:10:14)*
- He says ICT concepts such as fair value gaps and sweeps are mean-reversion behaviour. *(51:58)*

**Proof (backtesting)**
- **Split:** tune on 2022–2024, then run the locked test on 2025-onward **once**. A failure is final. *(1:11:17–1:13:41)*
- **Seven minimum checks** *(1:13:41–1:14:31)*:
  1. costs;
  2. next-open fills;
  3. recent data;
  4. locked test;
  5. return vs drawdown;
  6. enough trades;
  7. **neighbours:** nearby parameter values must also work (100/150/250 vs 200), *(1:14:31–1:15:22)*.
- **Test the backtester before trusting it** *(1:15:39–1:19:54)*:
  - a planted edge in synthetic prices (+1% the day after a flag), which must come back as about +0.6 to 1.2% per trade after costs (the run gave about 0.8%);
  - pure noise, which must come back as about zero minus costs;
  - a cheating signal that peeks at tomorrow, which a **truncation guard** must catch (recompute the signal on 30 random days with the data cut off at each day; if it changes, it looked ahead).
- **Pass ranges are written before the run.** *(1:18:33)*
- **Funnel gates for sleeves** *(1:30:16–1:33:29)*:
  - fits the asset;
  - makes money after costs on the training window;
  - minimum trades (15 for a dip buy, 6 for a breakout);
  - profit factor at least 1.3;
  - neighbours profitable;
  - locked test passed.
- His run: 44 ideas → 25 fit the asset → 20 made money after costs → 18 had enough trades → 14 had PF ≥ 1.3 → 11 had profitable neighbours → **7 passed the locked test**. Ideas the LLM made up itself go on a "bench", and every idea is logged, including the ones that fail. *(1:32:25–1:35:02)*
- **Combine strategies greedily** by return per drawdown, one sleeve per ticker, skipping sleeves too correlated with ones already picked; then a half-size-on-volatile-days check. *(1:38:16–1:39:52)*
- **Test the picking routine, not only the picks:** a quarterly re-pick using a 2-year pick window plus a 1-year check window, using only data up to that date. A truncation test proves it. It was run at 11 quarter ends. *(1:45:16–1:49:04)*
- **Testing an AI layer:** a fresh model instance per document, dates and names hidden, every call sealed before scoring, and the dated version compared with the hidden version. He admits this is "a replay, not a clean test". *(1:49:21–1:53:37)*
- **Optional extra checks** *(1:54:43–1:56:03)*:
  - walk-forward;
  - Monte Carlo reshuffling of trade order to see the range of drawdowns;
  - double costs;
  - testing on another market.

**Harness (execution)**
- **Timing:** the bot runs after 19:00 NY and sends market-on-open orders that fill at the 09:30 open, the same timing the backtest uses. Alpaca rejects orders sent between 09:28 and 19:00. *(1:57:06–1:58:26)*
- **Broker:** start with Alpaca's paper account. IBKR is the upgrade (futures, more countries, but needs IB Gateway and a weekly login). Schwab needs a weekly login and has no paper account. *(1:58:26, 3:01:56–3:07:16)*
- **The broker adapter is the only broker-specific part.** Add a new broker *next to* the old one, test it on the new broker's paper account, then switch with one config line. *(3:02:12–3:03:50)*
- **Prompt 8 bot** *(2:00:52–2:05:29)*:
  - The signal code lives in one shared file.
  - The keys check prints only whether each key is filled in.
  - Shares are rounded down to whole shares.
  - **Order IDs are made from date, ticker, side and sleeve**, so the same order cannot be sent twice.
  - The sleeve's stop is cancelled before a sleeve sells.
  - **Reconcile** what the broker says you own against what the bot thinks you own, and stop and alert if they differ.
  - Fresh prices are saved to a separate live file.
  - Risk checks every order before it goes out.
  - A morning check places broker-side stops after the fill and re-adds any missing stop.
  - A dry-run mode can replay any past day.
  - Real runs are allowed only on paper and only in the 19:00–24:00 window.
  - **Parity test:** the bot's signals must match the backtest's on each of the last 60 days.
  - An idempotency test checks that a second run sends nothing.
- **Daily loop** *(2:05:44–2:07:40)*:
  1. lock file;
  2. trading-day check;
  3. reconcile;
  4. prices;
  5. regime;
  6. signals;
  7. AI call;
  8. weights;
  9. risk;
  10. orders;
  11. log.
  - The run stops if the data is stale (a last price not from today) or if the account holds positions the bot did not place.
- **Safety** *(2:07:40–2:11:23)*:
  - stops held at the broker;
  - no double orders;
  - lock file;
  - if the account is down more than 3% on the day, no new sleeve trades that night;
  - a cap on target size;
  - a `pause` file;
  - if the account is down more than 5% in a day, the bot pauses itself and sends a message;
  - if the drawdown goes deeper than the worst backtest drawdown, the bot stops borrowing.
  - **These limits can only make the bot do less**, and exits and stops always still run.
- **Where it runs** *(2:11:39–2:14:34, 2:19:11–2:21:37)*:
  - The bot is plain Python started by the OS scheduler (launchd or Task Scheduler) every 30 minutes, and it works out what to do from the NY clock. Claude is only for building and reviews.
  - A daily bot can run on your own PC if it is kept awake.
  - **Intraday needs a server or VPS**, a paid live feed (websocket; Alpaca paid is $99/mo; Massive or Databento about $199/mo), bigger cost assumptions, feed-drop detection, and flat-by-close logic.
- **Alerts** go by Telegram: a failure alert, an evening summary, a morning summary, and a missed-run alert at 23:30. *(2:12:57–2:13:45)*
- **Automation ladder:** (1) alerts only, you place the trades; (2) approve each order; (3) fully automatic. *(2:23:46–2:24:51)*

**Adapt (monitoring)**
- **Paper vs backtest replay** over the same days *(2:25:22–2:28:01)*. Every gap goes into one group: fills, timing, data, rounding, limits or "fuzzy rules", and each gap gets one plain line saying what happened.
- **Removal rules written before going live** *(2:28:01–2:31:48)*:
  1. a **kill line = 2× the sleeve's worst tested drawdown**, which switches the sleeve off automatically;
  2. not re-picked at the quarterly re-pick;
  3. after 3+ months live, trading less than half or more than twice as often as in testing.
- For the core, the threshold is 1.5× its worst drawdown, and it only alerts.
- Statuses are keep, watch, review and out. **Never remove a sleeve because of one bad week.**
- **Rotation** from the bench needs the swap to pass three checks: no ticker clash, correlation ≤ 0.6, and return per drawdown not worse. Every change goes in a change log. *(2:31:48–2:33:09)*
- **A rule change counts as a new idea.** It goes through the gates and then weeks of paper. Never edit the live code because of recent results. *(2:33:09–2:34:29)*
- **Scheduled LLM review** every Saturday: a weekly report, a monthly status for each sleeve, a quarterly re-pick proposal. The LLM may fix code bugs (committed with a plain message, then the tests are rerun) but never changes rules. It proposes and waits for "yes". *(2:34:29–2:37:25)*
- **Human check of about 10 minutes a week.** *(2:37:25–2:39:17)*
- **Automate the routine steps:** data, signals, orders, stops, logs. **Do not automate** rule changes, core changes, the move from paper to live, or anything that needs judgement or news reading (keep those at "alerts"). *(2:41:11–2:41:43)*

## Concrete numbers mentioned

| Item | Value | mm:ss |
|---|---|---|
| Cost assumption | 0.05% per side (0.1% round trip) | 37:02, 2:54:58 |
| Cost drag | 5 trades/yr → 0.5%/yr; 50 → 5%; 250 → 25%/yr ("about 25% of profits" for daily trading) | 37:35, 2:55:14 |
| Train / locked test | 2022–2024 / 2025-onward, run once | 1:11:17 |
| Backtester planted-edge pass range | 0.6–1.2% per trade for a planted +1% (got about 0.8%) | 1:16:43, 1:19:05 |
| Look-ahead guard | 30 random truncation dates | 1:17:31 |
| Sleeve gates | ≥15 trades (dip) / ≥6 (breakout); PF ≥ 1.3; neighbours profitable | 1:30:32 |
| Re-pick gates | ≥10 / ≥4 trades; 2-year pick window + 1-year check window; up to 3 sleeves | 1:47:12 |
| Funnel | 44 → 25 → 20 → 18 → 14 → 11 → 7 | 1:32:25 |
| Core locked-test result | 24.8%/yr, max DD 11.2% | 1:27:40 |
| Full-account locked test | about 29–30%/yr, max DD 13%; account worst drawdown about 30% in 2022 | 1:40:41, 1:41:31, 1:42:52 |
| Sleeve size | 20% (10% on volatile days); margin up to 60% | 1:39:20, 1:41:13 |
| Filter search | "over 1,600 filters" tested to find the VIX/breadth rule | 1:44:43 |
| Daily loss rules | −3% → no new sleeves that night; −5% → self-pause | 2:08:27, 2:09:33 |
| Kill lines | sleeve 2× worst tested drawdown; core 1.5× | 2:28:18, 2:29:53 |
| Correlation caps | ≤ 0.5 safe vs engine; ≤ 0.6 for a rotation swap | 1:24:27, 2:32:21 |
| Win-rate uncertainty | 55% on 10 trades → about 25–85%; 100 trades → 45–65%; 400 → 50–60% | 2:56:50 |
| Parity test | bot vs backtest signals on the last 60 days | 2:03:35 |
| Live data | Alpaca paid $99/mo; Massive or Databento about $199/mo; intraday history $29–199/mo | 47:39, 2:19:28 |

## Anti-patterns ("not the right way")

- Asking the model to "build me a trading bot" in one prompt. *(13:05)*
- Browser chat instead of an agent working in the project folder. *(7:46)*
- Pasting broker keys into the chat. *(10:23)*
- Choosing pass marks after seeing results. *(1:18:33)*
- Re-running the locked test after a tweak. *(1:12:53, 2:53:02)*
- Testing on 2008-era data as if it were today's market. This is his view and is contested below. *(1:13:25)*
- A screener tested on today's index members. *(1:36:54, 2:57:23)*
- Letting the LLM pick the trades. It cannot be backtested and its answers change with every model release. *(2:58:28–3:00:03)*
- Two bots on one account. *(2:50:35)*
- Removing or changing a strategy after a bad week. *(2:33:56, 3:00:34)*
- Freezing the core in the pause state, which could leave you holding QQQ all the way down in a crash. *(2:09:16)*
- Starting with intraday or minute bars as a first bot. *(37:50, 2:40:54)*
- Going live at full size before paper and backtest agree. *(3:00:03)*

## Implications for our CRT robot plan

Our plan is: formalize → backtest → paper → small live. The video mostly **strengthens the "backtest" and "paper" stages and adds a "monitor/adapt" stage**. The biggest difference is that CRT is **intraday FX/indices** (4H framing, 15m/5m/1m entries, NY killzones). The speaker says this is the hard case: it needs paid tick/minute data, realistic spread and slippage, a VPS, and a live feed.

**Add to "formalize" (the rulebook)**
1. Check that every CRT-Rxx fills in the seven-part template (market, setup, filter, entry, exit, stop, size). The G-xx gaps that cannot be filled must have a coded proxy, **not an LLM judgement**, or be dropped.
2. Add an **asset-fit study** for our instruments at our timeframes. Measure how often a sweep of a prior-candle high or low closes back inside and reaches the opposite side, against a random-time baseline. CRT is a "snap back" idea, and we should first check that our instruments and sessions actually snap back.
3. Keep `rulebook_version` and write the **pass gates and pass ranges before any run**, in a frozen file.

**Add to "backtest"**
4. **Validate the engine first** with synthetic tests:
   - a planted edge, e.g. synthetic bars where a sweep-and-close-back pattern is followed by a known drift;
   - pure noise;
   - a deliberately cheating signal;
   - a **truncation (look-ahead) guard**.
   This matters a lot for us. Multi-timeframe CRT (a 4H candle still forming, the daily open at 00:00 vs 17:00 NY, the "closed bars only" rule in §0.3) is a classic place for look-ahead bugs.
5. **Locked holdout, run once:** e.g. tune on 2019–2023 and lock 2024–2026, plus a separate instrument holdout (an FX pair and an index never used in tuning).
6. **Multiple-testing control.** §7 has dozens of `alt` values and many `# PROPOSED` knobs. The number of combinations is large. We should log **every** configuration tried, in an experiment registry, and report the count. Use the **neighbour/plateau test** on each PROPOSED parameter (`swing_n`, `thick_body_ratio`, `kl_max_dist_atr`, `late_frac`, ...). Prefer walk-forward and a deflated-Sharpe or similar haircut over a single best run.
7. **Trade-count reality check.** `max_trades_per_week: 2` means about 100 trades a year per instrument at most, and probably far fewer after filters. His 10-vs-400-trade interval chart applies directly. Set a minimum (e.g. ≥ 200 trades pooled across instruments) before trusting the win rate or PF.
8. **Costs for intraday FX/indices, not 0.05%:**
   - spread varying by session and news;
   - commission;
   - slippage on stops and market entries;
   - swap for any overnight hold.
   Run a double-cost check and a Monte Carlo reshuffle of trade order for the drawdown range. A "next-open fill" assumption does not apply to us. The fill model must be bid/ask or spread based, and should be pessimistic when the stop and the target are hit inside the same bar.

**Add to "paper"**
9. **One signal module** shared by the backtester and the live bot, plus a **parity test**: the live bot's signals must equal the backtest's on the last N sessions.
10. **Reconciliation and safety:**
    - broker positions vs bot state, halting on mismatch;
    - **idempotent order IDs** (e.g. an MT5 magic number + comment built from setup id, date and side);
    - lock file;
    - stale-data halt;
    - stops held at the broker;
    - the existing `daily_loss_limit_r` plus a `pause` file;
    - limits that can only reduce risk and never block exits.
11. **Paper-vs-backtest replay** with gap categories: fills/spread, timing (time-zone and DST errors are likely for us), data revisions, lot rounding (0.01-lot steps at 0.5% risk), limits, fuzzy rules.
12. **Run on a VPS** close to the broker's server, with a heartbeat or missed-run alert. **Telegram alerts** fit naturally, since this repo is a Telegram signal copier and we can reuse it.
13. Use the **automation ladder**: run paper as "alerts only", then "approve each order", then auto. This also suits this repo's signal-copier design.

**Add a "monitor/adapt" stage before and during small live**
14. Write the removal and stop rules in advance:
    - a kill line (e.g. 2× the worst holdout drawdown, or a set R loss);
    - a trade-frequency drift check (less than half or more than twice the tested rate);
    - no rule change because of recent results; every change goes back through the gates and paper, and into a change log.
15. **LLM use:** for writing code, reviewing logs and drafting weekly reports only. Never for trade decisions or for changing rules unprompted.
16. Do not move from paper to small live until paper and backtest agree within explained gaps over enough trades (set a number, e.g. ≥ 30–50 paper trades). Scale up only after small live also matches.

## Where the speaker is wrong or overclaims

- **The profit claims are backtests over a very short, favourable holdout.** The lock test is 2025–2026, about 1.8 years, a period when both QQQ and gold rallied strongly. "24.8%/yr" and "about 29–30%/yr" are one path, with no live or audited record, and they are shown alongside a paid community and 1:1 offer. Treat them as unverified.
- **The holdout is not really blind.**
  - He says "I already know the engine's going to be QQQ" (1:25:15) before running the selection.
  - The sleeve families and the VIX/breadth filter came from his earlier study ("over 1,600 filters", 1:44:43), which very likely used 2025 data.
  - Prior knowledge leaks into the "locked" period. A single-use holdout only protects you if the *researcher* has also not seen it.
- **There is no multiple-testing correction in the funnel.** With 44 ideas, some will pass every gate by chance. 7/44 passing the holdout is not strong evidence on its own. The neighbour test helps but does not replace a correction.
- **A 3-year training window plus "don't test 2008"** means the core has very few switches (a few a year), far below his own "enough trades" rule. Excluding older crises lowers the drawdown estimate. Recent data is worth more for strategy decay, but **stress periods are still useful for risk sizing**. For us, keep older FX and index data at least for drawdown and robustness checks.
- **The drawdown numbers do not line up.** The headline max DD of 13% on the holdout sits next to an account worst drop of about 30% in 2022 (1:42:52), with up to 60% margin. The risk is higher than the headline numbers suggest.
- **"Daily fills match the backtest exactly"** is too strong. Opening-auction prices, partial fills and gaps still differ. He later lists "fills" as a gap source (2:25:54).
- **Survivorship bias:** he flags it correctly for screeners. But the ETF universe and the "asset study" choices are also picked with hindsight: the assets popular today are the ones that did well.
- **The "25% of profits in costs if you trade daily" figure** is a rule of thumb that depends on edge per trade. The cost table in percent per year is the more accurate version.
- **The AI-layer replay with hidden dates** cannot remove the model's memory of what happened next, which he admits (1:51:14). Results from it should be ignored for go/no-go decisions.
- **Side claims I have not verified**, all irrelevant to FX: model names and plans, Alpaca's 09:28–19:00 order window, a FINRA PDT-rule change "June 4th of 2026" (2:40:06), IBKR margin rates.
- **Scope mismatch:** his whole process is built for daily ETFs. He explicitly says intraday is "a lot more involved" (2:21:37) and does not show it, so all the intraday-specific work (data, costs, VPS, feed handling, session timing) is on us.
