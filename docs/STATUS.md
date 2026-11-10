# Project status: CRT trading robot

Read this first when starting a new session. Last updated 2026-11-10.

## Decided
- Strategy: Candle Range Theory (CRT), built on ICT concepts. The rules are in `research/notes/CRT_RULEBOOK.md` (draft v0.2: 73 rules, conflicts, gaps, parameters; v0.2 merged the notebook notes, see its changelog in section 9).
- Markets: EURUSD, GBPUSD, XAUUSD. XAGUSD and the dollar index are used as data only, for SMT.
- Risk: 1% per trade, daily stop at -2% (New York day).
- Broker: MT5 via MetaAPI. Candles are built on the broker clock (GMT+2/+3), so 4H candles open at 01/05/09 NY.
- Process: `docs/BUILD_PLAN.md` (Architecture → Logic → Proof → Harness → Adapt). Rollout goes alerts only → approve each trade → auto on demo → small live.

## Source priority
Romeo videos > Sham videos > ICT > notebook [R] > notebook [S] / [Room] > student PDF guides > community content. (The notebook is mostly Sham's "CRT Unlocked" course [S], plus Romeo-family [R] and "Soup Room" [Room] notes; it is not Romeo's own published book, which is still unstudied.)

## Done
- `research/`: source catalog (371 videos), notes on 30 Romeo/Sham videos, 3 PDF guides and 1 bot-building course.
- Rulebook v0.1 with ICT answers to gaps (6.1) and PDF findings (6.2).
- Notebook notes (268 pages) in `research/notes/crt/books/romeo-book/` and merged into rulebook v0.2 (section 6.3, changelog in section 9). Changed defaults include: weekly open Sunday 17:00, key-level TF table (option c, +15m→1h), BOS-origin key levels, close-back-inside as a score factor where not required, at least 3 confirmations, turtle soup at the open of a new candle (G-23 reversed), purge hours 01/03/06/08/09/11, five-phase market profile.
- X trader plan: read posts in a browser; traders' calls are votes only (`research/x-traders/`).

## In progress
- **Phase 1 build** (separate session, branch `crt-robot-phase1`): data, candle building on the broker clock, primitives, a validated backtester, and a locked holdout of the last 18 months. Result: `docs/PHASE1_REPORT.md`.

## Next
1. ~~Merge `00-answers.md` into the rulebook (bump it to v0.2, update the defaults in section 7).~~ Done 2026-11-10 (rulebook v0.2).
2. Phase 2: CRT detector plus Romeo/Sham/hybrid modes on top of the Phase 1 primitives, using the rulebook v0.2 parameters (section 7). Backtest on the tuning period only.
3. Run the holdout once, then move to the alerts-only stage.

## Still open
Not answered by the notebook either:
- Sham's "closing hour logic" (G-05).
- Romeo's "six possibilities" of weekly candle shapes (G-03); the notebook has only three weekly profiles drawn bull and bear.
- The key-level ranking algorithm (G-01 core): which of several candidate levels to pick.
- The OTE zone numbers (C-06, G-14).
- Model #1 trigger on the model candle's wick or body (C-07, Q9).
- Romeo's own published book is still not studied.

Other:
- VPS choice.
- vidIQ credits: about 85 left. They refill to 150 on 2 Dec 2026. They are needed for the ICT 2022 Mentorship transcripts.
