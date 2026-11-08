---
source_id: crt-sham
video_id: eviwQ97Ftjg
title: "Trading ORDERBLOCKS was hard until I applied this concept"
url: https://www.youtube.com/watch?v=eviwQ97Ftjg
author: Sham
studied_on: 2026-11-08
---

## Summary
Sham gives an "objective" definition of an ICT order block (OB): one candle or a
group of consecutive candles that performs a liquidity function and is then engulfed
at a key time. He lists five things that raise an OB's probability. He explains how
the engulfing close decides the OB's extent (one candle or several, body or wick), and
lists five uses of an OB beyond entries. Examples: EURUSD (D1/H4/M15, including a June
monthly-CRT-low purge) and USDCAD (D1/W1/MN). The video closes with Telegram promotion.

## Definitions
- **Order block (OB)**: "a single candle or a group of consecutive candles that either
  fill liquidity or purge liquidity and then gets engulfed at a key time." *(1:55–2:12)*
- **Fill liquidity**: the candle(s) trade into a pre-existing **higher-timeframe key level**
  (FVG, rejection block, an existing OB, etc.). *(2:45–3:01, 36:25)*
- **Purge liquidity**: the candle(s) take out a meaningful **higher-timeframe high or
  low** (swing high/low, range low, CRT low). *(3:01)*
- **Purge via SMT**: if the instrument fails to take a high but a correlated asset
  (DXY, GBPUSD, 6E) does take its matching high, the liquidity function counts as done
  for the instrument's candles. *(8:42–11:20)*
- **Engulfment (confirmation)**: bullish = a later candle **closes above** the OB
  candle(s); bearish = a later candle **closes below** them. "Ideally" during a key time
  or macro. *(3:48–4:22)*
- **OB extent (type)**: decided by where the engulfing candle closes. *(34:33–35:05)*
  - Close beyond the **body only** (not the wick) → the OB is the body. *(35:21–36:09)*
  - Close beyond the wick too → the whole candle, wick included. *(35:53)*
  - Close beyond only the last candle of a group → OB = that single candle. Later close
    beyond all of them → OB = the whole group (a new, larger OB). *(36:41–37:27, 40:04–40:36)*
- **Refined OB**: the single candle inside a multi-candle OB that actually did the
  purge, or only the part of the OB that lies in the correct premium/discount half of the
  dealing range. *(27:01, 28:04–28:20, 37:59)*

## Rules / conditions
- [ ] A candle that did not fill or purge liquidity **must not** be called an OB, however
  strong the engulfing candle looks. *(3:16–3:32)*
- [ ] Probability factors (stack as many as possible): *(13:12–17:43)*
  1. aligned with the HTF directional bias / DOL;
  2. at or near a HTF key level;
  3. coupled with an SMT divergence;
  4. bullish OB in **discount**, bearish OB in **premium** of the dealing range;
  5. formed at a key time (mainly for M15 OBs: 3:00, 6:00, 9:00 am macros).
- [ ] When a new dealing range has just formed, do not enter at the part of the OB that
  lies in premium (for longs). Wait for price to reach the discount part. *(37:43–39:01)*
- [ ] D1 OB use: once a D1 OB is confirmed, hold the bias in its direction until the
  short-term DOL is reached (example: about 10 days). *(25:09, 45:44–46:48)*
- [ ] After the short-term DOL is reached, stay **neutral** until a new OB forms in the
  opposite direction. That OB confirms the shift in structure. *(46:48–47:21)*
- [ ] Every concept has its own operational timeframes; the timeframes must not be
  mixed. The OB timeframe combinations were on a slide that is not read aloud. *(33:15–33:30)*
- [ ] Five functions of an OB: confirm HTF bias, confirm major SMT, confirm structural
  shift (CSD), confirm entries, act as a HTF key level for context. *(41:57–42:31)*
- [ ] Monthly OHLC idea: if the monthly objective (e.g. the CRT low) is completed in the
  **last week of the month**, expect a retracement to form the monthly wick. *(20:53–21:42, 43:18–43:52)*

## Entry, stop, target
- Entry: bullish at the **high** of the M15 OB (bearish mirror: at its low). *(31:52, 40:04)*
- Stop: below the OB (bullish). *(31:52)*
- Target: 3R. *(31:52, 40:04)*
- Timeframe pairs used: MN/W1 objective → D1 OB (bias) → refined H4 OB (context) →
  M15 OB (entry). *(19:17–19:33, 25:41–29:27)*
- Time-of-day / session filters: M15 OB formed at the **9:00 am macro** (New York
  open killzone) in the main example. *(31:03)*
- Re-entry: if the first OB entry is missed, a later close above the whole group
  creates a second entry. *(40:20–40:36)*

## Chart examples to label
| mm:ss | Instrument | TF | Date on chart | What it shows |
|---|---|---|---|---|
| 4:55–7:21 | EURUSD | D1? | — | Bearish OB that filled a D1 FVG and purged a swing high, then engulfed |
| 7:21–11:36 | EURUSD vs GBPUSD | — | — | Two-candle OB valid via SMT (GU took high, EU did not) |
| 19:50–25:09 | EURUSD (+ MN inset) | D1/MN | June (last week of month) | Two candles purge monthly CRT low, engulfed → bullish D1 OB, bias held |
| 25:41–29:10 | EURUSD | H4 | Monday | Refined 4H OB, new dealing range, body chosen in discount |
| 29:27–32:10 | EURUSD vs DXY | M15 | — | M15 OB in 4H OB, discount, SMT, 9:00 am; entry at OB high, SL below, 3R |
| 35:21–36:09 | — | — | — | Body-only engulf → body OB |
| 36:25–39:01 | — | H4 | — | Three candles fill 4H FVG/OB; partial and full engulf |
| 39:18–40:36 | — | M15 | — | First entry (one-candle OB) and second entry (two-candle OB) |
| 42:47–48:42 | USDCAD (+W1, MN) | D1 | — | Monthly objective done, SMT, 4-candle OB → 10-day bullish bias; then bearish OB in premium, weekly OB |

## Vague / discretionary parts
- "Meaningful HTF high/low": proposal: a swing high/low on a timeframe at least one
  step above the OB's timeframe (fractal with N=2 or 3 bars each side), or a prior
  D/W/M candle high/low, or a CRT high/low.
- "HTF key level": proposal: an untested FVG/OB/rejection block on a timeframe ≥ 2
  steps above (e.g. M15 OB needs an H4 or D1 PDA).
- Which group of consecutive candles counts: proposal: the maximal run of candles
  (in the direction opposite to the expected move) whose wicks touched the level or
  swept the swing, ending at the candle before the engulfing close.
- "Ideally at a key time" for engulfment: rule strength unclear (required or a bonus?).
  Proposal: required on M15, a bonus on H4/D1.
- The probability-factor weighting is not specified. Proposal: score 0–5 and require ≥ 4.

## Conflicts with other sources
- Romeo's CRT material (to compare): Sham's OB is defined by the liquidity function,
  not by "last opposite candle".
- In video 01, the bearish entry is at the "open" of the OB. Here, the bullish entry is at
  the OB "high". Both are the edge of the OB that is nearest to the current price.

## Open questions
- The slide with the OB timeframe combinations (33:30) is not read aloud. Get it from the video frames.
- Does an SMT-based purge need the correlated asset to sweep on the same timeframe?
