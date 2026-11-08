---
source_id: book-secrets-of-time
title: "Time-Based Trading Mastery / The Secrets of Time"
author: TradesbyVee (based on RomeoTPT)
pages: 50
file: research/raw/books/secrets-of-time.pdf
source_rank: secondary (student interpretation of Romeo's CRT; Romeo's videos win on conflict)
studied_on: 2026-11-08
---

**Page convention.** `p.N` = PDF page (1–50), which is what `Read pages=` and the
viewer show. The book's printed page number = PDF page − 6 (from Chapter 1 on).
Everything below that goes beyond Romeo's videos is **TradesbyVee's interpretation**
(tag: **TbV**), not Romeo. All times are **New York time** unless stated; the book
says "New York Time" for the 5 PM window (p.19) and "NY midnight-midnight" for the
trading day (p.20). The other clock times (01:00, 03:00, 09:00, 09:45) are printed
with no zone, but they sit on the same NY 1–5–9 grid, so we read them as NY.

Marketing ignored: "80%+ accuracy" (p.2), "100% win-rate" (p.7), "tested over
40–50 years" (p.21), "OHLC = 70% of time importance" (p.13), the 49%/51% split
(p.21). The 81% / 70% weekly statistics (p.23) are kept only as **unverified
hypotheses to backtest**.

## 1. Summary

1. A short (about 25 pages of content), mostly motivational guide. Its one technical idea is "time comes before price": candle highs and lows form at set times, so a trader should master one time window.
2. Intraday core: the **1–5–9 rhythm**. The day has six 4H candles opening 01, 05, 09, 13, 17, 21 NY. The 01:00 candle often makes the low, 03:00 is the turtle-soup hour, the 09:00 candle gives the OTE, the 21:00 candle consolidates, and 17:00 is the author's own "kill zone".
3. Weekly core: the **Wednesday Model**, a daily 3-candle CRT. Monday is C1, Tuesday sweeps Monday's low without closing below it (C2), Wednesday expands (C3). Buy below Wednesday's midnight open and hold into Thursday. The weekly low forms Mon–Wed and the high Thu–Fri.
4. Execution is ordinary ICT/CRT: HTF bias (W→D→4H), key levels (opens, highs, lows), then a turtle soup with a body close back inside on 5m/1m. Stop beyond the sweep wick; target the next HTF level.
5. It does **not** cover Romeo's model #1, kiss of death, SMT, the weekly "six possibilities", or Sham's "closing hour logic". Chapters 1 and 6 are about mindset and journaling.

### Chapter list

| Ch | Title | PDF page | Printed page |
|---|---|---|---|
| 0 | Cover, promo, dedication, contents | p.1–6 | – |
| 1 | The Foundation of Your Learning Journey (mindset, one mentor) | p.7 | 1 |
| 2 | The Importance of Time in Trading (time > price; divisions of time) | p.11 | 5 |
| 3 | What Is a Time-Based Model and Its Components (**1–5–9**, 5 PM kill zone, weekly candle behaviour, backtest/forward-test) | p.17 | 11 |
| 4 | Time-Based Models in Action: **The Wednesday Model** (CISD, 03:00 turtle soup, analysis steps, 1 o'clock low / 9 o'clock OTE, bias extraction) | p.23 | 17 |
| 5 | Turtle Soup, Higher-Timeframe Flow & Price-Action Basics (TS definition, OB/RB/FVG, ranges, real-setup steps, failed OB, checklist, micro-trade) | p.31 | 25 |
| 6 | Why 95% of Traders Fail (focus, discipline, stages of the ideal trade, journal) | p.43 | 37 |
| – | The Journey Continues (closing words from both authors) | p.49–50 | 43–44 |

Pages with real technical content: p.13, 18–20, 23–29, 32–39. Charts checked
visually: p.19 (Fig 3.1), p.25 (Fig 4.1), p.26 (Fig 4.2), p.28 (Fig 4.3),
p.29 (Fig 4.4), p.13 (Fig 2.3), p.33–39, p.46.

## 2. Adds to the rulebook

Each item gives the page, what is new or sharper, and the rulebook IDs it touches.

### 2.1 Candle grid and day definition

- **A1. 4H grid = 01/05/09/13/17/21 NY ("1–5–9").** (p.18, Fig 3.1 p.19) Each daily candle holds six 4H candles, labelled 1, 5, 9, 1, 5, 9. The text names "5 P.M. New York Time" (p.19) and "the 9 P.M. window" (p.20), so the labels are NY clock hours (am, then pm). This is the third independent source for the 01:00-anchored 4H grid, after Sham's named candles.
  → Raises the confidence of the 4H row in **0.3** (medium → medium-high) and supports `P:h4_grid_first_open = "01:00"` (**C-03**). TbV calls 1–5–9 the "structural heartbeat" and says kill zones are "customizable" once you know it (p.18).
- **A2. Trading day = NY midnight to midnight.** (p.20) "Every NY midnight" starts a new day. Step 2 of the analysis routine is to mark the **midnight opening price** (p.26).
  → Supports the Daily = 00:00 NY default (**0.3**, **C-03**) and gives the reference price for "buy below the open" (**CRT-R44**). Caveat: the real-chart example on p.25 starts "at 5PM open" (see 4.7).
- **A3. Schematic mismatch to log.** Fig 3.1 starts the day with the "1" candle. But under a midnight day, the 21:00 4H candle runs across midnight (21:00–01:00), so the drawing cannot be literal. The book never resolves this. → Keep **C-03** open. Our reading: the book uses the 01:00 grid for intraday 4H work and midnight for the daily open price. That is the same split as the current v0.1 default.

### 2.2 Intraday timing (which 4H candles and hours matter) — TbV

- **A4. 01:00 4H candle = where the day's low (bullish day) usually forms.** (p.28) "One o'clock candle often creates low." Fig 4.4 (p.29) labels the first leg "Expansion 1 (01:00–05:00)" after a "Protraction" (Judas move) away from the open.
  → New intraday rule for **CRT-R35 / G-22** (Romeo mode's missing intraday window) and **G-06** ("high/low of day first"). Proxy: in a bullish day, the low of day is expected inside 01:00–05:00.
- **A5. 03:00 = the turtle-soup hour.** (p.26) TbV calls 3 AM "crucial for turtle soup setups". Fig 4.2 (p.26) marks the Wednesday low at **03:00**. This is the same hour as Sham's London macro.
  → Sharpens **CRT-R32 / DEF-22** (03:00 macro). Gives Romeo mode a sweep-time filter for **G-22**. Window length is not stated. Default: the 03:00–04:00 hour (`P:macro_window = hour`).
- **A6. 09:00 4H candle = OTE / second expansion.** (p.28) "Nine o'clock candle often generates OTE—entry zone." Fig 4.4 labels the second leg "Expansion 2 (09:00)". Fig 4.1 (p.25) marks 01:00 and 09:00 as the two key times. Fig 4.2 shows a 09:45 pullback before the rally.
  → New timing for the **CRT-R41** OTE / **CRT-R40** retrace entry: look for the OTE retracement and leg two inside the 09:00–13:00 4H candle, especially its first hour (NY open). Links to Sham's 09:00 macro.
- **A7. Daily delivery template (AMD timing).** (p.26, p.28, Fig 4.4 p.29) Consolidation → expansion leg 1 → retracement → expansion leg 2. On the clock: protraction/Judas swing from the midnight open, turn in the 01:00 candle (often at 03:00), expansion 1 through 01:00–05:00, retracement (05:00 candle, implied by the figure, **not stated**), expansion 2 from 09:00. p.26 adds a "continuation" phase after distribution (A-M-D-continuation).
  → Gives **DEF-24** (C1/C2/C3 = AMD) an intraday clock and a computable proxy for **G-04** (market-profile state machine).
- **A8. 21:00 4H candle consolidates.** (p.20) The 9 PM window "often consolidates". → Consistent with Sham's Asia no-trade block (**CRT-R34**). It can serve as evidence for `asia_block_romeo` as a variant.
- **A9. 17:00 NY "non-conventional kill zone".** (p.19) This is the author's favourite window ("study it deeply"). The length is not given; it is either the 17:00 4H candle (17:00–21:00) or the 17:00 hour. → **TbV only**, new; not in Romeo or Sham. Add only as an experimental window (`P:extra_windows: tbv_1700`), off by default (see 4.5).
- **A10. London / New York sessions are where the Judas swing → turtle soup → CISD happens.** (p.24) No session times are given. → Reuse Sham's windows (**DEF-22**).

### 2.3 Weekday logic

- **A11. Wednesday Model = a daily 3-candle CRT with fixed weekdays.** (p.27, "Visual Logic") C1 = Monday ("forms base"). C2 = Tuesday: it takes Monday's low but does **not close below** it. C3 = Wednesday: "retraces and expands". Fig 4.3 (p.28) shows the same pattern as Monday/Tuesday/"Wednesday?" daily candles.
  → A concrete, testable instance of **CRT-R25 + CRT-R35 + CRT-R14**. It also gives Romeo mode a named daily setup:
  ```text
  wednesday_model_bull(week):
      C1 = D[Mon]; C2 = D[Tue]
      require C2.low < C1.low and C2.close >= C1.low          # DEF-05 ts_low
      bias for Wed (C3) = bull; target = C1.high (A12)
      entry on Wed: below Wed 00:00 open (CRT-R44), after protraction (A13)
      exit: by Thursday (A14)
  ```
- **A12. Bias extraction from Mon/Tue.** (p.28) If Monday makes the low and Tuesday sweeps it but fails to close below, then Wednesday or Thursday will likely take **Monday's high**. → The same logic as **CRT-R06 / CRT-R09** applied to Monday's daily candle. It supports **CRT-R10** (prefer the Monday daily CRT). The target is the opposite extreme of C1 (**CRT-R53** TP2).
- **A13. Entry location in C3.** (p.24, p.26) "Buying below open and closing above it means success". Step 4 of the routine: wait for the protraction, then a pattern "below opening price", with the opening price = the midnight open (p.26 step 2). → Confirms **CRT-R44** and fixes the daily reference to the **00:00 NY open**.
- **A14. Holding / time exit.** (p.24) Simple model: the daily candle opens, hold until the close, "close on Thursday". → A sourced time exit for **CRT-R56** (`P:time_exit = end_of_htf_candle`, with the variant `thursday_close` for the Wednesday model). Which exact Thursday time is not stated. PROPOSED: Thursday 00:00 (= Wednesday daily close) as default, Thursday 17:00 as a variant.
- **A15. Weekly extremes: low Mon–Wed, high Thu–Fri.** (p.20, p.24) The book calls this a "general rule". p.24 says the low forms Mon–Wed and the "opposite range end" forms Thu–Fri, i.e. one extreme early in the week and the other late. → Same timing as **DEF-31 / CRT-R14** (Romeo's bearish template is the mirror). Named profiles: "Monday Low" and "Thursday High" models (p.20). Feeds **G-06**. See 4.1 for the bullish-only wording.
- **A16. Weekly-extreme statistics (unverified).** (p.23) TbV claims an 81% chance that the weekly high or low forms between the Sunday open and the **Tuesday London session**, and a 70% chance that Tuesday prints the weekly high or low. → Hypotheses for the **CRT-R70** weekly log and the **G-06** priors. They agree with Romeo's "Tuesday stab" (**CRT-R35**). Backtest before using them.
- **A17. Two opportunities per week; about four Wednesday-model trades a month.** (p.20, p.29) → Fits **CRT-R64** (1–2 trades/week). See 4.4 for the internal contradiction.
- **A18. One daily candle cannot hold both the weekly high and low.** (p.20) This is a heuristic, not a fact (see 4.6). In code it can only be a soft prior: once one weekday has made one weekly extreme, look for the other extreme on a different day.

### 2.4 Weekly open: Sunday vs Monday

- **A19.** (p.23) The 81% window is measured from the **"Sunday open"**, which treats Sunday's session as part of the week for high/low statistics. The Wednesday Model counts candles from **Monday** (p.27). No time is given for the Sunday open, and there is nothing on the weekly close.
  → Supports the v0.1 split in **C-02**: weekly *range* from Sunday 17:00 NY, Monday as day 1 of the CRT sequence. It does not settle the weekly *open price* (Mon 00:00 vs Sun 17:00).

### 2.5 Closing-hour logic

- **A20.** The book never uses the phrase. Its nearest content is the 1–5–9 roles: which 4H candle makes the low (01:00), which gives the OTE (09:00), and which consolidates (21:00). It does not explain what happens at a 4H candle's close. → **G-05 stays open.** It does give one testable reading: log, for every purge, *which* 4H candle (1/5/9/13/17/21) it fell in and its minute offset, and expect bullish-day lows in the 01:00 candle near 03:00.

### 2.6 Turtle soup, execution, key levels — TbV

- **A21. Turtle soup = false break of an obvious high/low, traded when price closes back inside.** (p.33, Fig 5.3) The confirmation is a **body close** back inside (p.36, p.38, p.40 "wait for body close"). → Matches **DEF-05/DEF-06** and **CRT-R25**. It supports `P:ts_close_back_bars` measured on closes, not wicks.
- **A22. Key levels = opens, highs, lows**, with an "HTF key level" defined as a "big Weekly/Monthly open, high, or low" (p.36, p.40). → Adds **weekly and monthly opening prices** to the **CRT-R19** candidate set (Romeo's videos list only the open of the last down/up-close candle). Partial input to **G-01**.
- **A23. Real-setup procedure** (p.36): bias W→D→4H; mark key levels; execute on **5m or 1m**: TS, confluence (FVG, breaker, rejection wick), body close back inside; entry after the confirmation close; stop below the swing low; target the next HTF confluence (range midpoint, high, OB). Micro-trade (p.39): 1H bias, 5m TS, 1m close back inside, stop below the wick low, target the next 1H key level. → Stop rule = **CRT-R50**. Target "range midpoint" ≈ **CRT-R53** TP1. TFs: see 4.2.
- **A24. Range = 20+ candles between a range high and low (accumulation); a close above the range high = change of state** until an HTF key level says otherwise. (p.35) → A sourced number for **G-18** (the rulebook proxy uses ≥6 bars; add `range_min_bars: 20` as a variant).
- **A25. Market profile = trend vs range** (Fig 5.6 p.36). In the Wednesday example the profile changes from "breaking lows" to "breaking highs" (p.25). → The same as Romeo's swept-vs-broken reading (**DEF-25 / G-04**, Romeo variant); adds a two-state label (trend/range).
- **A26. CISD.** (p.24) Judas swing, then a turtle soup at the key level, then a **change in state of delivery**: on the HTF, a market structure shift; on the LTF, a **breaker** confirms it. → The same event as **DEF-16** (Sham's CSD) and **DEF-10** (true MSS / "breaker", romeo/06).
- **A27. Failed OB → breaker.** (p.37–38, Figs 5.8–5.10) A bearish OB that price closes above often leads to a rally toward the top of the failed block; later price rests on it as a bullish breaker. → New detail for the re-entry in **CRT-R48** / the breaker in **CRT-R38**. A long-wick candle that is later disrespected is called a **"Mitigation Model"** (p.28). Not defined further.
- **A28. Bodies over wicks.** (p.25, p.36) "Candle bodies tell story, not wicks"; remove wicks to see FVGs/OBs. A wick through a block with a quick rejection = liquidity grab; bodies that hold = an inefficiency fill is expected. → Leans toward `P:ote_fib_basis = body` and `model1_trigger_ref = body` as variants (**C-07**, Q7); it does not decide them.
- **A29. Premium/discount.** (p.35) Do not trade a bullish FVG in premium; only buy in discount. → **CRT-R21 / CRT-R47**.
- **A30. HTF bias is required.** (p.31–32) Trading the LTF without the HTF = "trading distribution, not manipulation". Avoid counter-trend unless there is a clear HTF reason. → **CRT-R05 / CRT-R11 / CRT-R31**.
- **A31. Daily range projection.** (p.26 step 3) Use the **CBDR and the Asian range** to estimate the day's high/low. No times are given. → Ties to the ICT answer for **G-26** in 6.1 (CBDR 14:00–20:00, Asia 20:00–00:00).
- **A32. Time divisions.** (p.13) OHLC, "daily or periodic ranges" with Gann cycles of **20/40/60 days**, squares of time and price, and time cycles. → The 20/40/60 lookback is the same as ICT's IPDA data ranges (**G-01** in 6.1). It is a second source for limiting old highs/lows to 20/40/60-day lookbacks.
- **A33. Pre-trade checklist** (p.38–39, p.41): HTF bias, HTF key level, TS visible, body close confirms, logical stop and target. If any is "no / don't know", skip. → **CRT-R37 / CRT-R69**. Stages of the ideal trade (Fig 6.2 p.46): plan (mark the key level) → wait for the level → execute → wait for target or stop. → **CRT-R68** (do not interfere).

### 2.7 Not in the book (checked)

- The weekly candle **"six possibilities"** (romeo/16): **absent**. The book names a "Possible Shapes of the Daily Candle" diagram (p.23), but the diagram is **not reproduced** (p.23 has text only). → **G-03 stays open.**
- Model #1, kiss of death, SMT, the CRT 50% target, TF pair tables, Romeo's weekly close time: absent.

## 3. Resolves conflicts / gaps

Only partial resolutions; the book is secondary and often vague. "Settles" means
it gives a sourced default where we had a PROPOSED one.

| ID | Status | Answer from the book | Page |
|---|---|---|---|
| **C-03** daily open / 4H grid | **Partly settles** | 4H grid 01/05/09/13/17/21 NY confirmed (1–5–9). Day = NY midnight–midnight; reference price = midnight open. Matches the v0.1 default. Inconsistent "5PM open" example remains. | p.18–20, 26 (vs p.25) |
| **C-02** weekly open | **Partly** | The week's high/low window starts at the "Sunday open" (range from Sunday). Monday = C1 of the weekly sequence. No close time. Supports the v0.1 split (range from Sun 17:00, Monday-based sequence). | p.23, 27 |
| **G-22** Romeo's "correct time" | **Answered (TbV)** | Bullish-day low in the 01:00 4H candle, turtle soup at 03:00, OTE/expansion 2 in the 09:00 candle, London/NY sessions. Replaces the "reuse Sham killzones" proxy with a 1–5–9 filter. | p.24, 26, 28–29 |
| **Q13** (§8) Romeo's intraday time | **Answered (TbV)** | As G-22. "9:30" from romeo/14 is not mentioned; 09:45 appears in an example (Fig 4.2). | p.26, 28 |
| **G-06** weekly/daily profiles | **Partly** | Weekly low Mon–Wed / high Thu–Fri; "Monday Low" and "Thursday High" models; Wednesday Model; Tuesday prints the weekly H/L ~70% (claim). Daily: low of day in the 01:00 candle. | p.20, 23–24, 27–28 |
| **G-04** market profile | **Partly** | Profile = trend vs range; the shift from breaking lows to breaking highs = bullish delivery; intraday leg sequence consolidation → exp 1 → retrace → exp 2. | p.25, 28, 36 |
| **G-18** consolidation/range | **Partly** | Range = 20+ candles; a close beyond the range high = change of state. | p.35 |
| **G-01** key level choice | **Small step** | Adds weekly/monthly **opens** as HTF key levels; 20/40/60-day lookbacks. Still no selection rule. | p.13, 36, 40 |
| **G-23 / CRT-R36** late manipulation | No | – | – |
| **G-05** closing hour logic | **Not resolved** | Not covered; only 4H-candle roles (A20). | – |
| **G-03** six possibilities | **Not resolved** | Diagram named, not shown. | p.23 |
| **C-07** model #1 wick/body | No (leans body) | "Bodies tell the story"; body-close confirmation. | p.25, 36 |
| **C-09** which candle | **Consistent** | Trade C3 (Wednesday) after C2 closes back inside. | p.27 |
| **C-15** macros | **Partly** | Endorses 03:00 and 09:00 as key hours (not 06:00 or 11:00). | p.26, 28 |
| **CRT-R56** time exit | **Sourced** | Hold the daily candle to its close; close by Thursday (Wednesday Model). | p.24 |
| **CRT-R44** reference open | **Sourced** | Midnight opening price. | p.26 |

## 4. Contradicts Romeo's videos / Sham / ICT

1. **Weekly extremes as one fixed direction** (p.20): "weekly low usually forms Mon–Wed, high Thu–Fri" is given as a general rule with no bullish/bearish qualifier. Romeo's template is direction-dependent (bearish week: high Mon–Wed, low Thu–Fri; romeo/03, DEF-31). p.24's "opposite range end" suggests TbV means "first extreme early, second late". **Code it direction-dependent** (Romeo).
2. **Execution timeframes** (p.36, p.39): bias W→D→4H with entries on 5m/1m, and a micro-trade with a 1H "bias" and a 5m turtle soup. Romeo's model #1 pairs are W→4H, D→1H, 4H→15m (C-01), and he puts nothing below 4H as the CRT candle (CRT-R02; 1H only for "hyper scalpers"). Keep the Romeo pairs; treat 5m/1m only as a `tf_pairs` variant.
3. **"Higher timeframe" = weekly or monthly only** (p.32) vs Romeo, who trades daily and 4H CRTs as the HTF (CRT-R02).
4. **Trade frequency** (p.19–20): about 10 day trades a week from the 17:00 window and "25 good-quality setups weekly" vs Romeo/Sham's 1–2 a week (CRT-R64). The book also contradicts itself: "four such models monthly" (p.29).
5. **17:00 NY kill zone** (p.19): not a window for Romeo, Sham or ICT. Sham blocks 20:00–02:00 (CRT-R34), and ICT treats 17:00 as the low-liquidity rollover / CBDR end. "Kill zones are customizable" (p.18) also departs from Sham's fixed windows. TbV only; off by default.
6. **"A single daily candle cannot form both the weekly high and low"** (p.20): factually wrong as an absolute. A week can have both extremes inside one day (e.g. an outside day that contains the whole week's range). Use only as a soft prior.
7. **Day definition is internally inconsistent**: midnight–midnight (p.20) and midnight open (p.26) vs a "5PM open" in the real-chart example (p.25). Romeo uses midnight (romeo/02); Sham's 4H grid implies a 17:00 broker day (C-03).
8. **Order block definition** (p.33): "a candle or cluster ... identified by a strong move away". This is much looser than Sham's (DEF-15: must purge/fill liquidity and be engulfed at a key time). Romeo is sceptical of OBs (C-19). Do not use TbV's OB definition.
9. **Bodies over wicks** (p.25, p.36) vs Romeo's CRT levels on wick extremes (DEF-02, CRT-R24) and wick-based sweeps (DEF-04). Partly in line with Romeo's "ignore the wicks, look at the bodies" (romeo/02 38:15), which refers to the closing candle. Keep wicks for levels and bodies for confirmation.
10. **Targets** (p.36, p.39): "next higher-TF confluence / next 1H key level", with the range midpoint as one option. This is looser than Romeo's fixed TP1 = CRT 50%, TP2 = C1 extreme (CRT-R53).
11. **Heavier ICT vocabulary than Romeo**: Judas swing, CISD, CBDR, protraction, breaker, mitigation, Gann/IPDA 20/40/60 (p.13, 24, 26, 28). Romeo rejects some ICT tools (6.1 note). In Romeo mode, treat these as Sham/ICT-mode inputs.
12. **03:00 / 09:00 emphasis vs Sham's macro list** (03, 06, 09, 11): the book agrees on 03:00 and 09:00 but never mentions 06:00 or 11:00 (C-15). This is an omission, not a contradiction.

## 5. Every time window in the book (→ code)

Timezone: **America/New_York** for all rows. "Stated" = the book gives the time; "inferred" = from a figure or our reading; "missing" = the book names it but gives no time (fallback from the rulebook shown).

| # | Name | Start–End (NY) | Basis | Purpose (book) | Page | Rulebook link |
|---|---|---|---|---|---|---|
| 1 | Trading day | 00:00 → 00:00 next day | stated | the daily candle; a new day = a new opportunity | p.20 | 0.3 Daily, C-03 |
| 2 | Midnight opening price | 00:00 (price at the open) | stated | reference: buy below / sell above it | p.26 | CRT-R44 |
| 3 | Alt. day open ("5PM open") | 17:00 | stated in one example | start of the example's daily delivery | p.25 | C-03 variant |
| 4 | 4H "1" (am) | 01:00–05:00 | stated (grid); role p.28 | bullish-day low forms here; expansion 1 | p.18–19, 28, 29 | CRT-R28 framing, G-22 |
| 5 | Turtle-soup hour | 03:00 (length missing → 03:00–04:00) | stated | TS / manipulation at the key level | p.26 (Fig 4.2) | DEF-22 03:00 macro, CRT-R32 |
| 6 | 4H "5" (am) | 05:00–09:00 | grid stated; role inferred | retracement between expansions (Fig 4.4) | p.19, 29 | – |
| 7 | 4H "9" (am) | 09:00–13:00 | stated | OTE entry zone; expansion 2 | p.28, 29 | CRT-R40/R41, 09:00 macro |
| 8 | Example pullback | 09:45 | figure label | retrace before expansion (example only) | p.26 | log only |
| 9 | 4H "1" (pm) | 13:00–17:00 | grid only | no role given | p.19 | – |
| 10 | 4H "5" (pm) / "non-conventional kill zone" | 17:00–21:00 (length missing; may mean the 17:00 hour) | stated start | author's main day-trading window | p.19 | new, TbV only (off by default) |
| 11 | 4H "9" (pm) | 21:00–01:00 | stated | consolidation window | p.20 | CRT-R34 Asia block |
| 12 | Protraction / Judas swing | from 00:00 open until the turn (≈ before or within the 01:00 candle) | inferred (Fig 4.4) | false move away from the open before the real move | p.24, 26, 29 | DEF-24 C2/manipulation |
| 13 | London session | missing → 02:00–05:00 (Sham) | missing | Judas → TS → CISD happen here | p.24 | DEF-22 |
| 14 | New York session | missing → 07:00–10:00 (Sham) | missing | same | p.24 | DEF-22 |
| 15 | Asian range | missing → 20:00–00:00 (Sham) | missing | estimates the day's high/low | p.26 | DEF-23 |
| 16 | CBDR | missing → 14:00–20:00 (ICT, 6.1) | missing | estimates the day's high/low | p.26 | G-26 (6.1) |
| 17 | Weekly-extreme window | Sunday open (→ Sun 17:00) to end of Tuesday London (→ Tue 05:00) | stated by name; times missing | 81% (claim) of weekly H/L form here | p.23 | CRT-R14, G-06, C-02 |
| 18 | Tuesday | Tue 00:00–Wed 00:00 | stated | 70% (claim) prints the weekly H or L | p.23 | CRT-R35 |
| 19 | Early-week extreme | Mon 00:00–Thu 00:00 | stated (weekdays) | weekly low (bullish week) | p.20, 24 | CRT-R14, DEF-31 |
| 20 | Late-week extreme | Thu 00:00–Fri close (17:00) | stated (weekdays) | weekly high (bullish week) | p.20, 24 | CRT-R14 |
| 21 | Wednesday Model C1 | Monday daily candle | stated | base / range candle | p.27 | DEF-24, CRT-R10 |
| 22 | Wednesday Model C2 | Tuesday daily candle | stated | sweeps Mon low, closes back inside | p.27 | CRT-R25 |
| 23 | Wednesday Model C3 / entry day | Wednesday 00:00–Thu 00:00; enter below the 00:00 open | stated | expansion; trade day | p.24, 27 | CRT-R30, R44 |
| 24 | Wednesday Model exit | by Thursday (exact time missing → Thu 00:00 default, Thu 17:00 variant) | stated (day) | time exit | p.24 | CRT-R56 |

Suggested parameter block (PROPOSED wiring of the book's windows; not yet in the rulebook):

```yaml
tbv_timing:                      # source: book-secrets-of-time (secondary)
  h4_roles: {"01:00": low_of_day_bull, "05:00": retrace, "09:00": ote_expansion2, "21:00": consolidation}
  ts_hour: "03:00"               # p.26
  ote_candle_open: "09:00"       # p.28
  day_open_ref: "00:00"          # p.26
  extra_windows: {tbv_1700: ["17:00", "21:00"]}   # p.19, off by default
  weekly_extreme_window: [sun_1700, tue_0500]      # p.23, hypothesis
  wednesday_model: {c1: Mon, c2: Tue, c3: Wed, exit: thu_0000}   # p.24, p.27
  range_min_bars_variant: 20     # p.35
```
