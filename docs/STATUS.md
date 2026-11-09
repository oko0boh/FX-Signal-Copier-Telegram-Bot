# Project status: CRT trading robot

Read this first when starting a new session. Last updated 2026-11-09.

## Decided
- Strategy: Candle Range Theory (CRT), built on ICT concepts. The rules are in `research/notes/CRT_RULEBOOK.md` (draft v0.1: 73 rules, conflicts, gaps, parameters).
- Markets: EURUSD, GBPUSD, XAUUSD. XAGUSD and the dollar index are used as data only, for SMT.
- Risk: 1% per trade, daily stop at -2% (New York day).
- Broker: MT5 via MetaAPI. Candles are built on the broker clock (GMT+2/+3), so 4H candles open at 01/05/09 NY.
- Process: `docs/BUILD_PLAN.md` (Architecture → Logic → Proof → Harness → Adapt). Rollout goes alerts only → approve each trade → auto on demo → small live.

## Source priority
Romeo videos > Sham videos > ICT > the user's notebook notes / student PDF guides > community content.

## Done
- `research/`: source catalog (371 videos), notes on 30 Romeo/Sham videos, 3 PDF guides and 1 bot-building course.
- Rulebook v0.1 with ICT answers to gaps (6.1) and PDF findings (6.2).
- X trader plan: read posts in a browser; traders' calls are votes only (`research/x-traders/`).

## In progress
- **Phase 1 build** (separate session, branch `crt-robot-phase1`): data, candle building on the broker clock, primitives, a validated backtester, and a locked holdout of the last 18 months. Result: `docs/PHASE1_REPORT.md`.
- **Notebook notes** (user's Mac session, branch `ccr-774ea4ca-kf9n1i`): 268 pages of handwritten notes of Romeo's teaching. They go to `research/notes/crt/books/romeo-book/`, with `00-answers.md` mapping answers to rulebook IDs (G-xx, C-xx, Q-xx). The PDF itself stays git-ignored.

## Next
1. Merge `00-answers.md` into the rulebook (bump it to v0.2, update the defaults in section 7).
2. Phase 2: CRT detector plus Romeo/Sham/hybrid modes on top of the Phase 1 primitives. Backtest on the tuning period only.
3. Run the holdout once, then move to the alerts-only stage.

## Still open
- Sham's "closing hour logic" (G-05) and Romeo's six weekly candle shapes (G-03).
- VPS choice.
- vidIQ credits: about 85 left. They refill to 150 on 2 Dec 2026. They are needed for the ICT 2022 Mentorship transcripts.
