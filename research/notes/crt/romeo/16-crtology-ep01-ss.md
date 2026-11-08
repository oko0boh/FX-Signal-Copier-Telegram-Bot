---
source_id: crt-romeo
video_id: 4DZWbCzEvhM
title: "CRTology episode 1: SS"
url: https://www.youtube.com/watch?v=4DZWbCzEvhM
author: Romeo (Romeotpt)
studied_on: 2026-11-08
---

## Summary
**SS stands for "Saturdays and Sundays"** *(1:04)*. This answers the open question in
note 15. It is not "stop sweep" and not "turtle soup". The episode describes a
weekend routine. On Saturday you review the week that just closed: when and where the
weekly high and low formed, the shape of the weekly candle, which key level
produced the reversal, and your own execution mistakes. On Sunday you get ready for
the coming week. You check how last week closed against the week before, mark
last week's highs and lows as liquidity pools, and predict the next weekly candle.
There is no live chart; everything is a theoretical sketch. (Promo: series runs
weekly/bi-weekly July to November; "rewatch 5+ times".)

## Definitions
- **SS**: "Saturdays and Sundays", the weekend review and preparation routine. *(1:04)*
- **Weekly review data points** (Saturday) *(6:36–8:48)*:
  - day **and** exact time of the weekly high;
  - day **and** exact time of the weekly low ("the opposing end");
  - weekly candle shape, one of "only six possibilities" of candle anatomy
    (examples named: pin bar, full/classic bullish or bearish candle,
    down-then-up, up-then-down). *(7:25)* The six are not listed here.
  - the **weekly or daily key level** at which the weekly high/low formed, i.e.
    the level that caused the reaction (the "launching pad"). *(8:15–9:04)*
- **Typical bullish week template**: Monday opens, Tuesday drops, there is a
  range and a **turtle soup** (false break of the range low) down there, then price
  goes higher. *(8:48)*
- **Next-candle prediction input** (Sunday): did the previous week **close above**
  or only **wick above** the week before it? *(21:54–22:09)* The rule for
  turning this into a direction is given in ep.2.
- **Liquidity pools**: the previous week's highs and lows (and "a bunch of" other
  highs/lows), marked before the week opens. *(24:26–26:11)* ICT concept:
  buy-side / sell-side liquidity.
- **Inside week**: a week that does not touch the previous week's high or low. It
  is a "subtype" to be taught later. *(25:22)*
- **Model (entry sketch)**: CRT on the higher TF (e.g. daily: Tuesday down,
  then Wednesday expected to be a classic bullish candle). Then on the LTF: range, then
  turtle soup, then break up, then **OTE**, then enter. *(15:17–15:54)*

## Rules / conditions
- [ ] Saturday (early morning): log the weekly high and low, each with weekday and time. *(5:13–7:07)*
- [ ] Saturday: classify the weekly candle shape. *(7:25)*
- [ ] Saturday: identify the weekly/daily key level where the weekly high/low formed. *(8:15)*
- [ ] Saturday: run the execution audit. Did you over-leverage or risk too much? Take more
      than the allowed number of trades? Trade out of boredom? Exit too early (e.g. at
      break-even before the target)? Exit too late (past the target, back to the stop)?
      Was your weekly candle prediction right, and if not, where did it fail? *(13:06–18:24)*
- [ ] Do the review for **one** asset (the one you trade), not several. *(6:05)*
- [ ] A trade must **only** be taken when the full model is present. No trading "because the
      market is open". *(15:00–15:54)*
- [ ] Sunday: check whether the previous week closed above or wicked above the prior week. *(22:09)*
- [ ] A wick/close signal must **not** be traded alone. It must be paired with a key level,
      and the market structure / **market profile** requirement must be met. *(22:26–23:33)*
- [ ] "A wick in a bullish market is going to be filled". Do not chase wicks. *(22:26)*
- [ ] Sunday: draw a vertical line at the Monday open. Mark the previous week's high and low
      (and other highs/lows) as liquidity pools. Predict next week's candle as
      down / up / inside. *(24:07–25:55)*
- [ ] During the week: watch how price reacts at the previous week's H/L (up then down, down
      then up, down then consolidate, or no touch). *(25:02–25:38)*

## Entry, stop, target
- Entry: LTF OTE after range, turtle soup and a break up, inside a HTF CRT. Sketch only. *(15:37)*
- Stop: not specified.
- Target: not specified (refers to "your target").
- Timeframe pairs used: weekly/daily key level for context; daily candles inside the
  week (Mon/Tue/Wed); "lower time frame" for entry, not specified.
- Time-of-day / session filters: weekend review early Saturday and Sunday morning. In the
  bullish template the weekly low forms around Tuesday.

## Implications for our project
- The Saturday review maps directly onto a **weekly stats logger**: weekly H/L
  timestamps, candle-shape class, nearest key level. The Sunday prep maps onto a
  **pre-week bias job** (close-above/wick-above check plus marking last week's H/L).
- The execution audit gives us risk-manager limits: max risk per trade, max trades per
  week, no trade unless every model condition is true.

## Chart examples to label
None. Romeo says he gives only a theoretical example *(5:30)*. The drawings are schematic.

| mm:ss | Instrument | TF | Date on chart | What it shows |
|---|---|---|---|---|
| 8:48 | (schematic) | W/D | – | Bullish week: Mon open, Tue drop, range + turtle soup, rally |
| 15:17 | (schematic) | D → LTF | – | Model sketch: Tue down, Wed bullish; LTF range, TS, break, OTE entry |
| 24:07 | (schematic) | W | – | Weekend vertical lines and previous week H/L marked into Monday |

## Vague / discretionary parts
- **"Six possibilities" of candle shape**: not enumerated. Proposal: classify the weekly
  OHLC by body/range ratio and wick position. For example: bullish full (body ≥ 60% of
  range, close > open), bearish full, bullish pin (lower wick ≥ 60%), bearish pin (upper
  wick ≥ 60%), down-then-up (low formed before high), up-then-down (high before low).
  Check against the full list when Romeo gives it.
- **Key level**: not defined yet (promised in a later episode). Placeholder: weekly/daily
  swing H/L, previous week/day H/L, and 50% of the weekly wick (see ep.2).
- **Market profile**: called crucial but not explained. *(23:33)* It is an open dependency.
- **Range / turtle soup on the LTF**: needs a measurable range (e.g. N bars inside x·ATR)
  and a sweep definition (wick beyond the range extreme, close back inside within k bars).
- **"Permitted number of trades"**: the number is not given. Make it a config parameter.

## Conflicts with other sources
- None found within the series. Note: "SS" is a routine, not a setup, so it has no
  rule conflict with "CRT secrets".

## Open questions
- What are the six candle-anatomy types exactly?
- Which time zone are the weekly H/L "times" logged in? (Ep.2 uses Friday 16:00 as the
  weekly close, which implies New York time.)
- How is "market profile" defined, and how does it gate the close/wick rule?
