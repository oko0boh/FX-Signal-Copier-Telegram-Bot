---
source_id: crt-sham
video_id: Hk13lBszyPo
title: "6 Years of Brutally Honest Trading Advice in Under 30 Minutes"
url: https://www.youtube.com/watch?v=Hk13lBszyPo
author: Sham
studied_on: 2026-11-08
---

## Summary
A mindset video with no strategy content. Sham's view is that profitability needs
three equally important parts: technical edge, behavioural edge and risk
management. An edge is a fully documented system with positive expectancy, not
just knowledge. It shows only over a large sample, and changing rules after
losses resets it. He ends with a daily routine. (Promo: he says he has been
profitable for 3 years and averages about $25k/month.)

## Definitions
- **Edge**: a complete, written, repeatable system. That means rules, filters,
  session and timing rules, validation and entry rules, no-trade conditions,
  trade management, risk parameters, journaling and review, plus data showing
  positive expectancy. *(6:54–7:43, 10:07)*
- **Technical edge**: bias, context, liquidity, key levels and entry model. It
  tells you when, where and which direction to trade, and what confirmation you
  need. *(2:05–2:37)*

## Rules / conditions
- [ ] The system must be documented: when to trade, when not to, what confirms,
  what invalidates. *(7:27–7:58, 10:38)*
- [ ] Do not change rules or filters after a losing streak without data. Even a
  small change makes it a different system. *(13:33–15:42)*
- [ ] Do not skip valid setups. Skipping changes the edge's sample. *(15:42–16:30)*
- [ ] Judge each trade on whether the process was followed, not on P&L. *(18:54, 22:54)*

## Risk / routine
- Risk: fixed risk per trade, exposure limits, **daily loss limit**, capital
  preservation. *(4:12–4:28)* No numbers are given.
- Daily routine *(25:17–26:21)*:
  1. Pre-session: daily bias, market context, key levels, what you are waiting for.
  2. Trade only in set session or key windows.
  3. Active monitoring during the execution window: wait for the candle range
     purge or key-level test, then the entry model.
  4. Passive monitoring after execution or when done: alerts only.
  5. Execute only when the model is present. Otherwise do nothing.

## Entry, stop, target
Not covered.

## Chart examples to label
None.

## Vague / discretionary parts
None that need a measurable rule. The routine maps directly onto a bot's session
scheduler.

## Implications for our project
- The bot should run a fixed rule set with no changes driven by short-term
  results. Change rules only after a backtest on a large sample.
- Add a daily loss limit and an exposure cap. Values are to be decided.
