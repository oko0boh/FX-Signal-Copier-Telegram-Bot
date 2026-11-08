---
source_id: crt-romeo
video_id: wkSiy27a8ps
title: "CRTology episode 2: The Lens"
url: https://www.youtube.com/watch?v=wkSiy27a8ps
author: Romeo (Romeotpt)
studied_on: 2026-11-08
---

## Summary
"The Lens" is Romeo's method for predicting the **weekly candle**. He says you should
master it before trading any other timeframe. *(1:55–3:32)* The steps: get a weekly
bias from how last week closed against the week before. Mark a weekly/daily key level
(here, 50% of the weekly wick). Pair that level with an old swing low. Expect
Monday chop, then a turtle soup of a consolidation into the key level around
Tuesday. After that, a lower-timeframe expansion runs toward the targets.
He walks through a live **gold (XAUUSD)** example, with SMT against silver, a daily
FVG and a rejection block as confluence. (Promo: subscribe goal, "rewatch 5+ times".)

## Definitions
- **The Lens**: mastering the prediction of the weekly candle. *(1:55)*
- **Close/wick bias rule** ("general rule of thumb"), comparing last week's candle
  with the week before it *(12:07–12:26)*:
  - **close above** prior week high → higher prices;
  - **close below** prior week low → lower prices;
  - **wick above** prior week high (no close above) → lower prices;
  - **wick below** prior week low (no close below) → higher prices.
- **Key levels produce lower-TF expansions**. Mapping *(8:16–8:52)*:
  monthly KL → weekly expansion; weekly KL → daily expansion; daily KL → 4H
  expansion; 4H KL → 1H or 15m expansion.
- **Key level used here**: **50% of the weekly candle's wick** (the midpoint of the
  wick) *(14:51–15:07, 19:16–19:34)*. He draws it as a solid line because it is the
  HTF key level.
- **Pairing**: when bullish, pair the HTF key level with an **old low on the same
  timeframe**, "the most visible" swing low. You then expect price not to trade much
  below that low. *(6:17–6:51, 17:50–18:44)*
- **Bullish expectation**: highs get broken through, lows get turtle-souped. *(18:27)*
  ICT concept: liquidity (buy-side targeted, sell-side raided).
- **Turtle soup**: a false breakout/breakdown of a consolidation into the key
  level. *(7:42–7:59)*
- **Target rule (rule of thumb)**: in a bullish reversal, the target is the **last high
  right before the dump into the old low** (the "high that broke the low"). In reverse,
  the last low before the run into an old high. *(13:13–14:17)*
- **Rejection block**: "a turtle soup of the body". Rejection blocks "usually create
  retracements" before price attacks the high. *(20:41–21:15, 25:57–26:17)*
- **FVG-filling low as stop**: in bullish markets, the low that fills a (daily) FVG is
  usually a good stop. It is usually not revisited before the bullish target is hit.
  *(25:09–25:27)* ICT concept: FVG / balanced price range.
- **Weekly close time**: Friday 16:00 (when "the action dies out"). *(17:34)* This
  implies the New York time zone.

## Rules / conditions
- [ ] You must be able to predict the weekly candle reliably before trading other TFs. *(3:15)*
- [ ] Mark the weekly open and close times. Use vertical lines at each weekly open. *(5:24, 15:22, 17:19)*
- [ ] Determine weekly bias with the close/wick rule. *(12:07–12:26)*
- [ ] Mark the current week's high and low with lines. *(12:41)*
- [ ] On the daily, find the nearby target. Look for a close above the "high that broke the
      low" as extra bullish evidence. *(13:13–13:45)*
- [ ] Mark the 50% of the weekly wick(s) as the key level. *(14:51)*
- [ ] Bullish: the key level must be paired with an old same-TF swing low. Ignore highs as
      pairing candidates. *(17:50–18:27)*
- [ ] Expected sequence: Monday chop/consolidation, then a stab into the key level via turtle
      soup of the consolidation (often Tuesday), then expansion Wed–Fri. *(7:26–7:59, 10:27)*
- [ ] Confluence in the example: **SMT** with the correlated asset (gold vs silver). *(22:39)*
- [ ] LTF trigger: range, then range-low turtle soup (a "three drive pattern"), then a
      break back above the high = **market structure shift**, then entry at the **OTE**. *(22:39–22:58)*
- [ ] Expect a retracement when price reaches a rejection block, before the high is attacked. *(21:15)*
- [ ] Do not require price to reach below the 50% level if the daily FVG has already been
      filled ("price is already balanced"). *(24:49–25:09)*
- [ ] Goal: capture a portion of the planned expansion, not the whole move. *(9:22–10:10)*

## Entry, stop, target
- Entry: LTF OTE after an MSS that follows the turtle soup of the range low, at/near the
  HTF key level or the paired old low. *(22:58)*
- Stop: below the low that filled the daily FVG. *(25:27)*
- Target: the last high before the dump into the old low, then "target the highs one by
  one". *(13:45, 15:22)*
- Timeframe pairs used: weekly KL → daily expansion. Daily for structure/targets. LTF
  (unspecified) for the MSS/OTE. Generic: M→W, W→D, D→4H, 4H→1H/15m. *(8:33)*
- Time-of-day / session filters: Monday = manipulation/chop. The low of the week
  forms Mon–Wed (the example: Tuesday). Expansion Wed–Fri. The week ends Friday 16:00.

## Implications for our project
- The close/wick rule gives us a clean four-state weekly bias function on weekly OHLC.
- Key level v0 = 50% of the weekly wick (upper wick for bearish, lower wick for bullish).

## Chart examples to label
| mm:ss | Instrument | TF | Date on chart | What it shows |
|---|---|---|---|---|
| 10:59 | XAUUSD | W | "last week" (date not stated) | Long upper wick, but close above the prior week → bullish |
| 13:13 | XAUUSD | D | – | High that broke the low; close above it; target = last high before the dump |
| 14:51 | XAUUSD | W | – | 50% of the weekly wick marked as KL |
| 17:34 | XAUUSD | W/D | – | Weekly open/close vertical lines (Fri 16:00) |
| 18:27 | XAUUSD | D | – | Choosing the most visible old low to pair with the KL |
| 20:05 | XAUUSD | D/LTF | – | Reaction off the first marked low; rejection block, retracement, KL tap, rally to target |
| 22:06 | XAUUSD | LTF | Tuesday of the week shown | Monday chop, smash into the pre-marked low + KL, (SMT vs XAGUSD), range-low TS, three drive, MSS, OTE, rally |
| 24:49 | XAUUSD | D | – | Daily FVG already filled, so no need to go below 50%; FVG low as stop |

## Vague / discretionary parts
- **"Most visible" swing low**: proposal: a fractal swing low with N=3 bars each side on
  the KL's timeframe. Pick the one with the largest prominence (distance to the next lower
  low), within the last X weeks.
- **"Close above" vs "wick above"**: define as weekly close > prior week high (close above)
  vs weekly high > prior week high and close ≤ prior week high (wick above). He also says
  the wick/close signal must be paired with a KL and market profile (ep.1). Which
  wick to take 50% of when both wicks exist is not stated.
- **Consolidation / range**: needs a measurable rule, e.g. ≥ N LTF bars whose high-low is
  ≤ k·ATR.
- **Rejection block**: not formally defined beyond "turtle soup of the body". Proposal: a
  candle group whose wicks swept a prior body extreme while the bodies held. ICT
  rejection block = the wick zone beyond the bodies.
- **LTF for entry**: not given. Use 15m/5m as a first test.
- **Strength classes** (very bullish … very bearish): promised for a later episode. *(4:04)*

## Conflicts with other sources
- Romeo dismisses FVG/order-block explanations ("ICT parrots") even though he uses a filled
  FVG as stop logic. He treats FVG as context, not as a cause. *(26:17–27:22)*
- Ep.1 says a wick in a bullish market "is going to be filled". This is consistent with the
  50%-of-wick key level here.

## Open questions
- Which wick's 50% (upper or lower) is used in a bullish week that has both?
- Is the weekly open Sunday 18:00 NY (FX) or something else?
- How strong must SMT be? Is it required, or only confluence?
