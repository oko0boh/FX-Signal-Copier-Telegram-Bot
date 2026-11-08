---
source_id: crt-sham
video_id: oBKjjUPYNOY
title: "How to TIME your entries perfectly?"
url: https://www.youtube.com/watch?v=oBKjjUPYNOY
author: Sham
studied_on: 2026-11-08
---

## Summary
Sham defines ICT killzones and key times (macros) and lists them for forex and for index
futures. He argues that liquidity purges, range expansions and SMT only matter when they
happen inside those windows. A setup outside key time is skipped however clean it looks.
He shows two EURUSD shorts (a Monday trade of about $4k and a Tuesday trade) with H4
context and M15 OB entries. He also introduces "time and price integration": the
weekly/monthly OHLC framework and the weekly/intraday profiles can override the HTF
narrative. The video includes FTMO stats promotion.

## Definitions
- **Killzone**: a time window in which the meaningful price delivery happens. *(1:19)*
- **Meaningful price delivery**: (1) liquidity purge, (2) range expansion, (3) SMT
  divergence. *(1:38–3:45)*
- **Key time / macro**: a narrower hourly window inside a killzone with even higher
  probability. *(4:02–4:18)*
- **Forex sessions (New York time)**: *(4:34–5:06)*
  - Asian range: 20:00–00:00
  - London open killzone: 02:00–05:00 (macro **03:00**)
  - New York killzone: 07:00–10:00 (macro **09:00**)
  - London close killzone: 10:00–12:00 (macro **11:00**)
  - Also used in the examples: the **06:00 macro** ("London lunch") *(15:15, 17:43)*
- **Index futures (NQ/ES/YM), New York time**: NY AM 08:30–11:00; NY lunch 12:00–13:00;
  NY PM 13:30–16:00; macros 08:30, 09:30 and others. *(6:08–6:42)*
- For JPY pairs, Asia can expand. For EU/GU, Asia is a range that frames the day. *(5:06–5:37)*
- **Time and price integration**: (1) the OHLC framework with proper timeframe alignment;
  (2) weekly and intraday profiles. *(19:34–19:50)*

## Rules / conditions
- [ ] A purge + SMT + entry model at a HTF key level in bias direction, but **outside a
  key time** → must not be traded. *(7:48–8:34)*
- [ ] A purge of the Asian high outside key time is invalid, even if price then moves the
  expected way for a while. *(11:16–11:49)*
- [ ] Price at the key level during a key time is **not** enough. An entry model (OB or
  FVG) must form. If none forms, stay risk off. *(14:12–14:59, 16:53–17:11)*
- [ ] If the planned key level is missed (price rebalanced the range but did not tag the
  OB), there is no trade from it. *(13:56–14:12)*
- [ ] An SMT with the correlated pair (GU, DXY) at a key time can stand in for the full
  sweep of the planned high. You may enter without the full range rebalance. *(10:44–11:00)*
- [ ] When the next H4 candle starts (the 05:00 NY 4H candle), you can re-select the
  candle range to that candle. *(14:59–15:15, 17:27)*
- [ ] Time/price override: if the weekly/monthly candle has already completed its
  expected expansion, the next day can be counter to the HTF bias. Ask "has price
  already delivered what it needed to deliver?" *(20:06–21:27)*
- [ ] A new weekly candle must first form its low (in a bullish context) at a HTF key level,
  which can give 1–2 bearish days (Mon/Tue) in a bullish structure. *(21:42–22:28)*
- [ ] Risk/routine: close at 2R instead of 3R on Friday before the market closes. No
  weekend holds. *(18:30–18:46)*

## Entry, stop, target
- Entry: at the M15 order block (the refined OB) after the purge at a key time. *(12:37–12:52, 17:58)*
- Stop: above the OB high (shorts). *(17:58)*
- Target: 3R (2R on Friday close). *(12:52, 18:30)*
- Timeframe pairs used: D1 bias → H4 context (dealing range, OB key level, candle range)
  → M15 entry.
- Time-of-day / session filters: London open killzone, 03:00 macro (Monday trade);
  06:00 macro (Tuesday trade); expansion carried into the New York killzone.

## Chart examples to label
| mm:ss | Instrument | TF | Date on chart | What it shows |
|---|---|---|---|---|
| 5:53–6:08 | — | intraday | — | Purge at 3 am macro, London expansion, NY continuation |
| 7:32–9:06 | — | LTF | — | Clean setup outside key time fails; same setup at key time works |
| 9:22–10:10 | EURUSD | D1 | week before / Monday | Retracement done after premium rebalance → bearish |
| 10:10–11:00 | EURUSD vs GBPUSD | H4 | Monday London open | 4H OB, candle-range purge, SMT at key time |
| 11:16–13:09 | EURUSD | M15 | Monday | Asian-high purge outside key time fails; 3 am purge + SMT + OB → 3R (~$4k) |
| 13:25–15:47 | EURUSD vs DXY/GU | H4 | Tuesday | Missed premium OB; re-select 05:00 4H candle; 6 am purge + SMT |
| 15:47–18:15 | EURUSD | M15 | Tuesday | 3 am FVG test without OB (no trade), 6 am OB entry, 3R |
| 18:15–18:46 | — | — | that month / Friday | FTMO stats; Friday trade closed at 2R |
| 21:27–22:45 | — | D1/W1 | — | Weekly profile: new week forms its low first despite bullish context |

## Vague / discretionary parts
- The macro window length is not given (is the 03:00 macro 03:00–04:00, or ±20 min?).
  Proposal: treat each macro as [HH:00, HH:59] NY time. Treat the killzone as the hard
  filter and the macro as a bonus.
- "Has the weekly/monthly candle completed its expansion?": proposal: the weekly
  (monthly) candle has already taken its target PDA/DOL, or its range ≥ the average weekly
  range (ADR × 5) in the bias direction.
- An SMT replacing a full sweep is discretionary. Define the SMT as: one pair makes a new
  swing high (fractal) and the correlated one does not, within the same key-time window.

## Conflicts with other sources
- 06:00 is used as a macro in the examples but is not on the spoken forex macro list
  (03:00, 09:00, 11:00). Also check the London killzone end (05:00) against the 06:00
  "London lunch".
- Video 06 says a purge outside key time **invalidates** the candle range, while here a
  new candle can be re-selected afterwards. These agree in spirit.

## Open questions
- The 4H candles quoted as "1:00 am" and "5:00 am" imply 4H opens at 01/05/09/13/17/21 NY
  time (broker server GMT+2/+3 alignment, e.g. FTMO MT). Confirm, because CRT candle
  boundaries depend on it.
- What exactly are the "weekly and intraday profiles" (not detailed)?
