---
source_id: book-romeo-notes
video_id:
title: "Risk, win rate and R:R, journaling, execution consistency, why traders fail"
url:
author: R (p.48, 65–67), S (p.180–185, 239–247, 264)
studied_on: 2026-11-10
---

## Summary
Mostly money management and discipline, not setup rules. The author's example
risk is 0.5% per trade. Risk-reward and risk of ruin matter more than the win
rate. A weekly review compares the model to your own trades with a consistency
ratio.

## Definitions
- **Win rate / R:R break-even table** [R, clear], p.48: 25% at 1:3, 33% at 1:2,
  40% at 1:1.5, 50% at 1:1, 60% at 0.7:1.
- **Execution Consistency Ratio (ECR)** [S, clear], p.181–184: trades the model
  offered divided by (valid trades you executed + invalid losses + invalid wins
  + valid wins not executed + valid losses not executed + trades the model
  offered minus valid trades you executed). 100% = fully consistent; 70–100%
  good; below 70% below average; below 50% poor; below 40% consider quitting.
  Worked examples give 80% and 75% and 100% (p.184–185).
- **Weekly performance review** [S, clear], p.180–183: three parts: the model's
  trades, your trades, then a comparison.
- **Journal fields** [S, clear], p.245: HTF thought process for the DOL,
  narrative, entry framing, day, date, time, CRT timing, purge time, risk,
  result in R, narrative strength, validity, emotions.

## Rules / conditions
- [ ] Risk per trade 0.5% in the conservative model (p.243, 264). Example model:
  40% win rate, average 3R, 3–4 trades a week, 10% max drawdown, risk of ruin
  about 3.62% (p.243).
- [ ] Prop-firm risk models: aggressive 1% / 1% / 0.5% across challenge,
  verification, funded; conservative 0.5% / 0.5% / 0.35% (p.243).
- [ ] Losing 10% needs +11% to recover, 50% needs +100%, 75% needs +400%
  (p.241).
- [ ] Five-stage ideal trade: plan and mark the level; wait for the level;
  execute; wait for target or stop. Neophyte mistakes by stage are listed
  (p.66, R, clear): forcing a level, entering early, huge lots on a 1-pip stop,
  closing early, moving to break-even too soon, turning a scalp into a swing.
- [ ] Study why traders fail: shorting an old high against the HTF flow; missed
  entry; stop too tight; wrong reaction shape (p.67–69, R Q&A).
- [ ] Back-test before forward-test; the edge is the trader (p.65, 212).

## Entry, stop, target
Not covered.

## Chart examples to label
None.

## Vague / discretionary parts
- None to turn into code except the ECR formula and risk numbers.

## Conflicts with other sources
- Rulebook 6.2 rejected "1–2% risk per trade (the author's number, not
  Romeo's)". This book's 0.5% (p.243, 264) is Sham's number, and 1% appears
  for prop-firm phases. The repo's own decision log (1% risk, −2% daily loss)
  is a separate user decision and not touched here.
- Q23: risk numbers: the book gives 0.5% per trade, 3.62% risk of ruin,
  3–4 trades a week; no daily loss limit or max open risk is given.

## Open questions
- Does the bot want the ECR as a self-check metric once live trading starts?
