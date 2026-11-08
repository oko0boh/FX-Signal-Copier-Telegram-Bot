---
source_id: crt-romeo
video_id: 3IWgc52Dqsg
title: "CRT secrets ep.6: SMT"
url: https://www.youtube.com/watch?v=3IWgc52Dqsg
author: Romeo (Romeotpt)
studied_on: 2026-11-08
---

## Summary
This episode defines SMT divergence between correlated assets (ICT **SMT**). It lists its uses (FVG fill,
confirmation, predicting equal highs/lows, CRTs) and explains the "confirmation" use in detail. This is the
most rule-heavy episode of the batch. It also adds a timing rule: if the manipulation happened at the
end of the previous candle, the next candle distributes with minimal manipulation. It also defines
a key level as the opening price of a down-close candle (support) or of an up-close candle (resistance). The example
is a EURUSD weekly with a 4H micro CRT, compared with DXY. He also gives a list of SMT pairs.
Ends with a book plug (2 Oct 2025).

## Definitions
- **SMT (divergence)**: one asset takes a high (or low) while its correlated asset does not.
  This shows that smart money is unwilling to push price there, so it signals weakness. *(2:12–3:41)*
- **SMT pairs**: EURUSD ↔ DXY (inverse) and GBPUSD. ES ↔ NQ (and YM / Dow). BTC ↔ ETH.
  Gold ↔ Silver. Inverse pairs are compared high-vs-low. Direct pairs are compared like-for-like. *(21:55–22:30, 26:10–26:27)*
- **SMT fill**: one asset fills its FVG and the correlated one does not. *(13:09–13:26)*
- **Manipulation-at-end-of-previous-candle rule**: "If the manipulation happened at the end
  of a previous candle, then expect distribution to happen in the next candle with minimal
  manipulation." *(7:31–8:05)*
- **PO3 order is not fixed**: the three phases can come as A-M-D or M-A-D. Romeo criticises fixed time models
  (e.g. "1 = accumulation, 5 = manipulation, 9 = distribution") as wrong. *(8:58–9:29)*
- **Key level (order-flow probe)**: the opening price of a down-close candle acts as support.
  The opening price of an up-close candle acts as resistance. *(17:02–17:33)*
- **Model #1 (as restated)**: a thick down-close candle pushes into the low (bullish case). An
  LTF candle then *closes above* that down-close candle. The bearish mirror is an up-close candle that liquidated the high
  followed by a down-close candle closing below it, which retail would call an engulfing bar. *(18:08–18:42, 28:44–29:01)*
- **Every entry is an exit and every exit is an entry**: a reached target is used as a new entry point. *(5:02–5:17)*
- **Fake order block / supply-demand trap**: a reaction from an order block that looks like an OTE
  but is only a KoD before continuation (ICT **order block**). *(10:56–11:29)*

## Rules / conditions
- [ ] Trade candle 3 onward. Romeo deliberately skipped the candle-2 entry. *(5:51)*
- [ ] If the HTF manipulation (sweep) occurred at the end of the previous candle (e.g. Friday
      for a weekly), expect the next candle to open and distribute quickly. Only a small
      manipulation is expected. *(10:04–10:35)*
- [ ] Weekly open is taken from the Monday open, not Sunday evening. *(14:38–14:56)*
- [ ] Bullish CRT entry needs: a LTF CRT forming inside a HTF CRT. The sweep of the CRT low happens into a
      key level (the open of a down-close candle). Two touches of the level were seen. *(15:31–17:50)*
- [ ] Model #1 confirmation: an LTF close above the down-close candle that pushed into the low. If there is
      no such close, the setup has lower probability. *(18:08–19:21)*
- [ ] SMT downgrade rule: if EURUSD takes a low but DXY does *not* take the matching high,
      expect less of a turtle soup/reversal in DXY. Consider continuation (DXY likely leaves
      relatively equal highs). *(24:15–25:37)*
- [ ] SMT confirmation rule (key rule): when an SMT appears, you must not enter blindly. You must wait for **two
      confirmations** on the asset that took the level: (1) a model #1 close on the LTF (the initial
      move), (2) a true MSS at a key level and time (for further expansion). *(27:57–31:05)*
- [ ] Take partial / full profit at the 50% of the range, or at a high near the 50%. *(20:08)*

## Entry, stop, target
- Entry: after the model #1 close above the down-close candle at the CRT low / key level (long).
  More expansion is expected after a true MSS. *(18:08–19:04, 30:31–31:05)*
- Stop: below the sweep low (shown, "stop loss" under the low). *(19:04)*
- Target: target 1 = 50% of the CRT range. Target 2 = CRT high. *(16:12, 17:50, 19:04)*
- Timeframe pairs used: Weekly HTF with a 4H "micro CRT", and a lower TF for model #1. *(4:45–5:02, 18:08)*
- Time-of-day / session filters: weekly anchored to Monday open. The manipulation-timing rule is above.

## Chart examples to label
| mm:ss | Instrument | TF | Date on chart | What it shows |
|---|---|---|---|---|
| 4:12–5:17 | EURUSD | W / 4H | "this week" (2025, not dated) | Monday open dumps into previous week's low. 4H micro CRT hit the target |
| 6:08–6:42 | EURUSD | 4H/LTF | same | KoD TS near the target. Fake order block |
| 10:20–11:29 | EURUSD | 4H | same week | Previous Friday manipulation, minimal manipulation, violent dump. Supply-demand/OB trap |
| 12:19–12:37 | EURUSD | LTF | same | Sweep below low, pump. Fake MSS |
| 14:38–17:50 | EURUSD | W/4H | same | Buy: Monday dump into old low, LTF CRT in HTF CRT, key level = open of down-close candle, 2 touches, T1 50%, T2 |
| 18:08–19:21 | EURUSD | LTF | same | Model #1: close above thick down-close candle. Stop and targets |
| 21:36–24:15 | EURUSD vs DXY | 4H | same | SMT: EUR took the low, DXY did not take the high |
| 26:10–31:05 | none (drawing) | — | — | SMT trap and the two-confirmation rule |

## Vague / discretionary parts
- **"Manipulation at end of previous candle"**: define it as the sweep of candle-1's
  extreme occurring in the last X% of the previous HTF candle's duration (e.g. Friday for weekly,
  or the last 4H of a daily). Then check whether distribution starts within the first Y% of the next candle.
- **"Thick" down-close candle**: define it as body >= k x median body (or ATR) of the last N LTF candles.
- **Which down-close candle's open is the key level**: here it was "this previous high,
  which is the opening price of this candle". Propose: the open of the last HTF down-close candle
  before the sweep, within the CRT range.
- **"Relatively equal highs"**: two highs within tolerance (e.g. <= 0.1 x ATR).
- **True MSS "key level time"**: time component undefined. Placeholder for a killzone filter.
- **Correlation direction**: EUR/DXY is inverse, so EUR low pairs with DXY high. Code needs a
  per-pair sign.

## Conflicts with other sources
- Weekly anchor: Monday open here *(14:38)*, but ep.3 marks weekly candles at **Sunday** *(18:51)*.
  The broker/session open must be decided. In FX, Sunday evening NY = Monday Asia.
- ep.3 says the true MSS comes with the TS and model #1 (a single sequence). Here model #1 and the true MSS are two
  separate, ordered confirmations (model #1 first, then MSS for further expansion).
- Profit-taking at 50% (here) vs holding to the CRT opposite extreme (ep.2/ep.3 targets). This is
  consistent if 50% = T1 partial.

## Open questions
- The fourth SMT use ("CRTs") and the "equal highs" use are only named, not explained.
- Exact pivot rule for "took the high": a wick beyond it or a close beyond it?
- What exactly does "true market structure shift" mean here? It is again promised for later episodes.
