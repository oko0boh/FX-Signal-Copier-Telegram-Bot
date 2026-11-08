# CRT Rulebook

## 0. Header

| Field | Value |
|---|---|
| Status | **Draft v0.1**. Not approved. Not yet backtested. |
| Built from | 29 videos: 17 Romeo (creator of CRT) + 12 Sham (CRT/ICT trader), via the 30 notes in `research/notes/crt/romeo/` (18 files, one of which, the CRTology intro, has no transcript) and `research/notes/crt/sham/` (12 files). |
| Pending | Romeo's book (on sale 1 Feb 2026, `romeo/13-secrets-ep10-clean-close`), remaining CRTology 2026 episodes, the ICT foundation notes (`notes/ict/` is still empty), community notes (Phase 3). |
| Written | 2026-11-08 |

### 0.1 How to read this file

- **DEF-xx** = a defined term (section 2). Every rule uses only defined terms.
- **CRT-Rxx** = a rule (section 3). Each rule has:
  - a one-line statement in *must / must not* form;
  - **Sources**: the note file (stem, under `research/notes/crt/`) and the video timestamps quoted in that note;
  - **Implementation**: pseudo-code or an exact condition over OHLC data;
  - **Confidence**: *high* (stated clearly, usually more than once), *medium* (stated once, or wording is ambiguous), *low* (implied, a claim, or only shown in one example).
- **C-xx** = a conflict between or within sources (section 5), with a proposed v0.1 default.
- **G-xx** = a discretionary gap that cannot be coded yet, with a proxy (section 6).
- **P:name** = a backtester parameter (section 7). When a rule depends on a parameter, its name is given.
- Text marked **PROPOSED (not from source)** is our own suggestion to make something computable. It is not something Romeo or Sham said. Everything else must be traceable to a note.
- Source priority (from `research/README.md` and the task brief): **Romeo is the source for CRT structure. Sham adds timing, order block (OB) and risk detail. Newer Romeo (CRTology 2026, notes 15–18) beats older Romeo (2025 "CRT secrets" and earlier).**

### 0.2 Source keys

| Key | File | Key | File |
|---|---|---|---|
| romeo/01 | `romeo/01-what-is-turtle-soup` | sham/01 | `sham/01-10k-in-one-trade` |
| romeo/02 | `romeo/02-what-is-crt` | sham/02 | `sham/02-orderblocks-concept` |
| romeo/03 | `romeo/03-secrets-ep01-one-crt-model` | sham/03 | `sham/03-daily-bias` |
| romeo/04 | `romeo/04-live-tape-reading-1` | sham/04 | `sham/04-timing-entries` |
| romeo/05 | `romeo/05-secrets-ep02-kiss-of-death` | sham/05 | `sham/05-crt-under-30-min` |
| romeo/06 | `romeo/06-secrets-ep03-the-journey` | sham/06 | `sham/06-15-minute-strategy-2026` |
| romeo/07 | `romeo/07-secrets-ep04-candle-anatomy` | sham/07 | `sham/07-6-years-advice` |
| romeo/08 | `romeo/08-secrets-ep05-key-level` | sham/08 | `sham/08-select-find-crt` |
| romeo/09 | `romeo/09-secrets-ep06-smt` | sham/09 | `sham/09-what-it-takes` |
| romeo/10 | `romeo/10-secrets-ep07-candle-3` | sham/10 | `sham/10-failing-with-ict` |
| romeo/11 | `romeo/11-secrets-ep08-when-crt-fails` | sham/11 | `sham/11-two-concepts` |
| romeo/12 | `romeo/12-secrets-ep09-connecting-the-dots` | sham/12 | `sham/12-path-to-profitability` |
| romeo/13 | `romeo/13-secrets-ep10-clean-close` | | |
| romeo/14 | `romeo/14-live-tape-reading-2` | | |
| romeo/15 | `romeo/15-crtology-introduction` | | |
| romeo/16 | `romeo/16-crtology-ep01-ss` (CRTology 2026) | | |
| romeo/17 | `romeo/17-crtology-ep02-the-lens` (CRTology 2026) | | |
| romeo/18 | `romeo/18-crtology-ep03-ote` (CRTology 2026) | | |

Note: romeo/13, romeo/15, sham/07, sham/09, sham/12 contain no strategy rules. They are cited only for routine, risk and meta rules.

### 0.3 Conventions

**Time zone.** All times are **New York local time** (IANA `America/New_York`, with daylight saving). Romeo: "all New York time, because that's the time the algorithm functions" (romeo/02 22:00). Sham's session times are New York (sham/04 4:34). The data layer must convert broker/server time to NY time before any rule runs.

**Candle open alignment.**

| TF | Open times (NY) | Source | Confidence |
|---|---|---|---|
| 15m, 5m, 1m | standard clock grid (:00, :15, ...) | not discussed; PROPOSED (not from source) | – |
| 1H | on the hour | not discussed; PROPOSED (not from source) | – |
| **4H** | **01:00, 05:00, 09:00, 13:00, 17:00, 21:00** | Sham names the "1 a.m.", "5 a.m." and "9 p.m." 4H candles (sham/04 14:59, sham/06 15:33, sham/08 33:22). This is the grid of a broker that closes the day at 17:00 NY (e.g. FTMO MT). | medium (inferred from three named candles; not stated as a rule) |
| **Daily** | **00:00** (midnight NY) | Romeo: the daily range resets at midnight NY (romeo/02 9:57); a daily candle is "Tuesday midnight to Wednesday midnight" (romeo/12 10:07). | medium. See **C-03**: Sham's 4H grid implies a 17:00 NY daily. |
| **Weekly** | **open question**, default Monday 00:00 open, Friday 17:00 close | Sunday 17:00 (romeo/02 17:34; romeo/06 18:51; romeo/10 10:54) vs Monday 00:00 (romeo/02 17:49 "true week open"; romeo/03 24:03; romeo/09 14:38). Close Friday 17:00 (romeo/03 24:19) vs Friday 16:00 (romeo/17 17:34). | low. See **C-02**. |
| Monthly | first calendar day, same open time as the daily | not discussed; PROPOSED (not from source) | – |

**Price conventions.**
- "High" and "low" always mean the wick extremes unless a rule says *body*.
- `body_top = max(open, close)`, `body_bottom = min(open, close)`.
- A **close beyond** a level means the bar's `close` is strictly beyond it. A wick beyond it is never a close beyond it (romeo/03 22:01; romeo/18 5:01).
- Up-close candle: `close > open`. Down-close candle: `close < open`. A doji (`close == open`) is neither. PROPOSED (not from source): treat a doji as neither colour.
- "Bullish/bearish" rules are written for one side. The other side is the exact mirror (swap high/low, above/below, buy/sell) unless stated.
- All indicators use **closed bars only**. A rule evaluated "at bar i" may read bars `<= i`. No look-ahead.

---

## 1. Primitives (helper functions every rule may use)

These are building blocks, not rules. Where a source gives no exact definition, the formula is **PROPOSED (not from source)** and has a parameter.

```text
bars(tf)                    # closed OHLC bars on timeframe tf, NY-time aligned (section 0.3)
range(c)    = c.high - c.low
mid(c)      = (c.high + c.low) / 2                    # DEF-03
atr(tf, n)  = Wilder ATR over n closed bars           # PROPOSED, P:atr_len = 14
swing_high(tf, i, N): bars[i].high > max(high of bars i-N..i-1, i+1..i+N)   # PROPOSED fractal, P:swing_n
swing_low (tf, i, N): mirror
  # a swing at i is only KNOWN at bar i+N (no look-ahead)
unswept(level, t): no bar after the level formed and before t has traded through it
```

---

## 2. Glossary

**DEF-01 Candle / candle range.** A candle is defined by its open time, its close time and the price action between them (romeo/07 4:43). "Every single candle is a range" from its high to its low, with the open and close marked (romeo/02 1:31). Sham: a higher-timeframe candle "can be treated as a range or a true range" only under the right context and conditions (sham/05 1:34).
Computable: `CR(c) = [c.low, c.high]`.

**DEF-02 CRT high / CRT low.** The high and low of candle 1 (C1, DEF-24), wick to wick (romeo/02 16:32, 34:37; romeo/05 6:36; romeo/10 5:50).
Computable: `crt_high = C1.high`, `crt_low = C1.low`.

**DEF-03 CRT 50% / equilibrium (EQ).**
- *CRT 50%*: the midpoint of C1's full wick range (romeo/02 16:48; romeo/05 6:52; romeo/11 12:17). `crt_50 = (C1.high + C1.low) / 2`. That it uses the full wick range is our reading (romeo/02 open question); confidence medium.
- *Dealing-range EQ*: the 50% of a dealing range (DEF-19) (sham/08 23:31). `eq = (dr.high + dr.low) / 2`.

**DEF-04 Sweep / purge / stab.** Price trades beyond a prior high or low. Romeo says "stab", "turtle soup" or "liquidate"; Sham says "purge".
- Computable (bearish side): `swept(level, bar) := bar.high > level`. Bullish: `bar.low < level`.
- PROPOSED (not from source): a minimum excess of 1 tick (P:sweep_min_ticks = 1).
- Sham's validity condition: a purge of a CRT candle only counts **after that CRT candle has closed** (sham/05 4:14, 15:12). See CRT-R25.

**DEF-05 Close-back-inside vs close-beyond (the two outcomes).** For a reference candle R and the next candle N (romeo/02 2:04–2:38; sham/11 3:27–5:04):
- *Breakout / close beyond / "close outside"*: `N.close > R.high` (bullish) or `N.close < R.low` (bearish).
- *Turtle soup / close back inside / "close inside"*: `N.high > R.high and N.close <= R.high` (bearish TS of the high) or `N.low < R.low and N.close >= R.low` (bullish TS of the low).
- *Inside bar*: `N.high <= R.high and N.low >= R.low`. Inside bars may sit between C1 and the TS candle (romeo/02 2:38).
- Edge case PROPOSED (not from source): if N sweeps both sides, classify by the side its close is nearest to; log it as `outside_bar` for review.

**DEF-06 Turtle soup (TS).** "A false breakout or a false breakdown" of an old high or old low (romeo/01 6:45). Bearish TS: price trades above an old high, then reverses down. Bullish TS: mirror (romeo/01 11:00–16:09).
- On the HTF candle level, a TS is the *close back inside* outcome of DEF-05.
- On the LTF, PROPOSED (not from source): `swept(old_level)` and a close back on the original side within `P:ts_close_back_bars` bars (default 1 = the same bar).

**DEF-07 Old high / old low.** A prior swing high/low from which price has already moved away (romeo/01 11:00, 15:20). Romeo: the only "real support/resistance" (romeo/03 18:58). No lookback or swing strength is given.
Computable PROPOSED (not from source): `swing_high(tf, i, P:swing_n)` that is `unswept` at the time of use.

**DEF-08 Model #1.** Romeo's single-candle entry (romeo/02 37:21; romeo/03 9:59–10:52; romeo/09 18:08; romeo/11 8:30; romeo/12 1:51):
- *Bullish*: on the LTF, the **one specific down-close candle** (the "model candle", M) that stabbed the old low. It should be **thick** (DEF-09). The trigger is a later LTF candle that **closes above** M. A wick above M does not count.
- *Bearish*: mirror (a thick up-close candle that stabbed an old high; trigger = a close below it). Retail would call the pair an engulfing pattern (romeo/09 28:44).
- It is "one specific candle, not a zone, not a bunch of candles" (romeo/03 19:13).
- Computable (bullish):
  ```text
  M = the LTF bar with M.low < key_low (it made the sweep), M.close < M.open, thick(M)
      # if several bars swept, M = the one that printed the lowest low (PROPOSED, not from source)
  trigger bar T: first bar after M with T.close > ref(M)
      ref(M) = M.high          # default, P:model1_trigger_ref = wick
             | M.body_top      # variant, P:model1_trigger_ref = body   (see C-07)
  ```
- "Partial model #1": a weekly candle closes below the up-close sweep candle but not all criteria are met; expect a pump back into that candle first (romeo/12 4:41).

**DEF-09 Thick candle.** Romeo insists the model candle must be thick; a "flimsy" one is weaker (romeo/02 38:15; romeo/03 11:42). No number is given.
PROPOSED (not from source): `thick(c) := body(c)/range(c) >= P:thick_body_ratio (0.6) and range(c) >= P:thick_atr_mult (1.0) * atr(tf,14)`.

**DEF-10 True market structure shift (true MSS).** Bullish: low → high → lower low (the stab into the old low / TS) → a **close above "the high that broke the low"**, i.e. the swing high that formed just before the lower low (romeo/06 11:52; romeo/08 13:51; romeo/11 9:17; romeo/12 8:46, 15:28). Romeo uses "breaker" for the same event (romeo/06 17:39). Bearish: mirror.
```text
L1 = swing low; H = swing high after L1; L2 = new low < L1 (the sweep), formed after H
true_mss_bull at bar t := t.close > H.high, t after L2, and no close below L2 between L2 and t
retrace_zone = [L2.low, H.high]   # "the area between the high that broke the low and the TS low" (romeo/12 16:16)
```
Romeo's MSS is close-based (romeo/12 8:46 "closes above"; romeo/18 5:01 for the OTE variant).

**DEF-11 Fake MSS / fake bottom.** An MSS (or a convincing bottoming pattern) against the pending target, formed **before** price reaches the key level or target. It is expected to fail (romeo/08 13:19–15:13; romeo/14 1:42). Computable only by context: an MSS whose sweep extreme has not reached the active key level / target (see CRT-R20, CRT-R11).

**DEF-12 OTE (optimal trade entry).**
- *Romeo (CRTology, romeo/18)*: a structural pattern, not a fib level. Bearish: high → low → higher high **into a key level** → a **candle close** below "the low that broke the high" (activation; a wick does not activate) → leg one (impulse) → retracement into **0.5–0.79** of leg one → leg two (the trade). Fib is drawn from the swing high to the end of leg one, on wicks; a second fib on bodies is a refinement. The shallow half of the zone is preferred (romeo/18 1:59–14:16).
- *ICT standard (for comparison only; not in our notes as an ICT note yet)*: fib entry 0.62–0.79, sweet spot 0.705 (romeo/18 conflicts section).
```text
leg1_start = HH.high (bearish)   # swing high into the key level
leg1_end   = lowest low after activation, before retrace begins   # PROPOSED definition, see G-14
zone = [leg1_end + 0.50*(leg1_start-leg1_end), leg1_end + 0.79*(leg1_start-leg1_end)]   # P:ote_zone
```

**DEF-13 Kiss of death (two different meanings, keep apart).**
- **KoD-R (Romeo)**: "the final turtle soup before the target is hit" (romeo/05 6:20; romeo/06 8:26; romeo/10 14:29). A fake reversal that traps counter-trend traders, usually followed by a fast move into the target (romeo/04 0:32). Also the last sweep into a key level before the true reversal (romeo/08 15:13). It can coincide with the OTE (romeo/06 18:16; romeo/10 17:16).
- **KOD-S (Sham)**: the "kiss of death sequence", "the last distribution leg inside of a bearish market maker model": price is very close to the HTF draw on liquidity, pauses, forms SMT, and makes a small retracement that **ends in discount** (bearish case) instead of rebalancing the dealing range to premium (sham/01 10:26–13:07; sham/06 20:36). It is "the only exception" to the rebalance rule (CRT-R16).

**DEF-14 Key level (KL).** "A price point at which you expect price to give a bounce", either a counter-trend reaction or the candle's actual high/low (romeo/08 8:18). Usually on a higher TF than the one traded (romeo/02 10:47; romeo/08 9:41). Can be a **price** level or a **time** level (romeo/08 5:46). Types named in the sources:
| Type | Source |
|---|---|
| Old high / old low (liquidity pool) on the HTF | romeo/02 11:04; romeo/03 17:52; romeo/10 2:27 |
| Opening price of a down-close candle (support) / of an up-close candle (resistance) | romeo/09 17:02 |
| 50% of the weekly candle's wick | romeo/17 14:51 (CRTology) |
| CRT high / CRT low | romeo/18 10:50 |
| Sham's set: **order blocks, fair value gaps, significant highs/lows** | sham/10 7:44 |
| Sham's examples: HTF FVG, OB, rejection block, previous week high/low | sham/02 2:45; sham/08 2:53 |
How to choose *the correct* key level is **not taught** (romeo/13 9:16; romeo/10). See G-01.

**DEF-15 Order block (OB), Sham's definition.** "A single candle or a group of consecutive candles that either fill liquidity or purge liquidity and then gets engulfed at a key time" (sham/02 1:55).
- *Fill liquidity*: the candle(s) trade into a pre-existing HTF key level (FVG, rejection block, OB) (sham/02 2:45).
- *Purge liquidity*: the candle(s) take a meaningful HTF high/low (swing, range low, CRT low) (sham/02 3:01). Also counts if a correlated asset purges its matching level (SMT purge, sham/02 8:42).
- *Engulfment*: bullish OB = a later candle **closes above** the OB candle(s); bearish = closes below. "Ideally" in a key time (sham/02 3:48).
- *Extent* (sham/02 34:33–37:27): engulfing close beyond the body only → OB = the body; close beyond the wick too → OB = the full candle. Close beyond only the last candle of a group → OB = that candle; a later close beyond the whole group → a new, larger OB.
- A candle that did not fill or purge liquidity **is not an OB** (sham/02 3:16).
```text
bullish OB at engulf bar E:
  G = maximal run of consecutive down-close bars ending at E-1     # PROPOSED grouping, see G-12
  require: any bar in G swept an HTF low or touched an HTF key level (or SMT purge)
  require: E.close > max(g.body_top for g in G)                    # engulfed
  ob_top = max(g.high) if E.close > max(g.high) else max(g.body_top)
  ob_bottom = min(g.low)
```

**DEF-16 Change in state of delivery (CSD).** Sham: a candle purges the previous low, then a later candle closes above (engulfs) the candles that purged (sham/03 35:31). In practice it is the same event that creates a Sham OB (sham/08 20:19; sham/11 13:15).

**DEF-17 Fair value gap (FVG).** Not defined by either source in these notes; both use the ICT standard. PROPOSED (ICT standard, to be confirmed in `notes/ict/`): three bars a, b, c; bullish FVG if `c.low > a.high` (gap = `[a.high, c.low]`); bearish if `c.high < a.low`. "Filled" when a later wick enters the gap (PROPOSED fill rule: touches its far edge, P:fvg_fill = touch|half|full).

**DEF-18 SMT divergence.** One asset takes a high (or low) while its correlated asset does not (romeo/09 2:12). Romeo's *candle SMT*: compare the **same candle** on both assets; SMT exists when that candle turtle-soups a prior low on one asset and not on the other (romeo/11 7:41). Pairs (romeo/09 21:55, 26:10):
| Pair | Sign |
|---|---|
| EURUSD ↔ DXY | inverse (EUR low vs DXY high) |
| EURUSD ↔ GBPUSD | direct (sham/01, sham/04 use GU vs EU) |
| ES ↔ NQ ↔ YM | direct |
| BTC ↔ ETH | direct |
| XAU ↔ XAG | direct |
| USDCAD ↔ DXY | direct (sham/03 25:15) |
```text
smt_bull(t, A, B, level_A, level_B):   # same bar t on both assets
  A.low[t] < level_A and B.low'[t] >= level_B       # ' = sign-adjusted (inverse pairs use high)
```
Whether "took the low" means wick or close is not stated (romeo/09 open question). Default: wick (P:smt_take = wick).

**DEF-19 Dealing range (DR).** Sham: the most recent **expansion swing** on the TF in question, swing high to swing low (sham/01 7:00; sham/08 23:31). It is the *relevant* dealing range only if it holds **unfilled liquidity** (an untested FVG/OB) (sham/03 14:19), and it is confirmed only after a counter-direction CSD (D1 or H4; H4 is the lowest TF allowed for a D1 range) (sham/03 15:55, 34:41). It is re-anchored as new swings form (sham/06 12:35). Swing algorithm: see G-09.

**DEF-20 Premium / discount.** Above the dealing-range EQ = premium; below = discount (sham/08 23:31). Romeo: "buy low, sell high" (romeo/01 20:07); "never buy above a high or sell below a low" (romeo/02 28:17).
`premium(p) := p > eq`, `discount(p) := p < eq`.

**DEF-21 Draw on liquidity (DOL).** The pending target price is heading for, e.g. an old low; "the draw on liquidity is paramount, it comes first" (romeo/04 0:15–1:40). Sham splits it: *short-term DOL* = inside the range (premium FVG / EQ); *long-term DOL* = the external range high/low (sham/03 3:16, 18:36). Romeo: price moves only to take a high/low or fill an imbalance (romeo/06 8:43).

**DEF-22 Key times: killzones and macros.** A killzone is a window in which meaningful delivery (purge, expansion, SMT) happens; a macro is a narrower hourly window inside it (sham/04 1:19–4:18). Forex, New York time (sham/04 4:34–5:06):
| Window | NY time | Macro |
|---|---|---|
| Asian range | 20:00–00:00 | – |
| London open killzone | 02:00–05:00 | 03:00 |
| (London lunch, used in examples) | – | 06:00 (sham/04 15:15; sham/06 15:18) |
| New York killzone | 07:00–10:00 | 09:00 |
| London close killzone | 10:00–12:00 | 11:00 |
Index futures (NQ/ES/YM): NY AM 08:30–11:00; NY lunch 12:00–13:00; NY PM 13:30–16:00; macros 08:30, 09:30 and others (sham/04 6:08).
Macro length is not given. PROPOSED (not from source): macro = `[HH:00, HH:59]` (P:macro_window).
Romeo talks about "time" ("where time meets price", "correct time") but gives no intraday window in these notes (romeo/06 12:28; romeo/08 13:51). His only stated session is London on a Tuesday (romeo/12 15:28).

**DEF-23 Sessions.** Asia = 20:00–00:00 NY, a range that frames the day for EU/GU (it can expand on JPY pairs) (sham/04 5:06). London opens 02:00. New York killzone 07:00. Daily candle = 00:00 NY (romeo/02 9:57).

**DEF-24 Candle 1 / 2 / 3 (CRT phases).** Romeo maps ICT power of three (accumulation, manipulation, distribution) onto three consecutive HTF candles (romeo/02 17:49; romeo/06 2:14; romeo/10 3:01–7:48):
- **C1** = accumulation; sets the range; the candle right before price reaches the key level (often a thick down-close candle in a bullish setup).
- **C2** = manipulation; sweeps one side of C1 / the key level; slow and choppy.
- **C3** = distribution; fast expansion after C2 closes, toward C1's 50% and then the opposite extreme.
- **Two-candle CRT**: C2 itself expands quickly to the target; there is no C3 entry (romeo/10 23:06).
- The phase order is not fixed (A-M-D or M-A-D) (romeo/09 8:58).
Sham: the number of candles (2–5) does not matter; context and timing come first (sham/05 28:33).

**DEF-25 Market profile.** *Romeo*: reading the sequence of highs and lows, which are swept and which are broken (romeo/12 8:46); called "one of the most crucial elements" but not explained (romeo/16 23:33). Bearish continuation profile: highs keep getting turtle-souped and lows keep breaking (romeo/14 12:03). *Sham*: four "market profiles": expansion, retracement, consolidation, manipulation; trade only in expansion toward the HTF DOL (sham/01 2:09, 5:56). See G-04.

**DEF-26 Relatively equal highs/lows.** Two or more swing highs/lows at about the same price, treated as a liquidity pool / target (romeo/09 24:15; romeo/14 0:52). PROPOSED (not from source): within `P:equal_tol_atr (0.1) × atr(14)`.

**DEF-27 Mother candle (inside-bar rule).** If the latest candles sit inside an earlier candle, use the outer candle as the CRT (sham/08 30:40).

**DEF-28 Rejection block.** "A turtle soup of the body"; usually creates a retracement before price attacks the high (romeo/17 20:41). Not used as a rule input in v0.1 (see G-19).

**DEF-29 Failure swing.** After the TS low, price drops back almost to that low once more before rallying (romeo/02 33:29). Not used as a rule input in v0.1.

**DEF-30 Refined OB.** The single candle inside a multi-candle OB that actually did the purge, or only the part of the OB in the correct premium/discount half (sham/02 27:01, 37:59).

**DEF-31 Weekly time theory.** Romeo: weekly open Monday midnight, close Friday 17:00; in a bearish week the high forms Mon/Tue/Wed and the low Thu/Fri; typical: fake high Monday, real high Tuesday with model #1, decline into Thu/Fri; "Thursday plus model one" is the highest-probability point (romeo/03 23:11–26:28). Bullish template: Monday opens, Tuesday drops into a range and a TS, then higher (romeo/16 8:48; romeo/17 7:26).

---

## 3. Rules

Notation used in the pseudo-code: `HTF` = the candle timeframe being traded (the CRT timeframe), `LTF` = its execution timeframe (CRT-R03), `C1, C2, C3` = consecutive closed HTF candles, `dir` = `bull` or `bear`, `t` = the current LTF bar. Functions return `True/False` or a value; nothing reads bars that are not yet closed.

### A) Timeframe pairing

**CRT-R01. Before any pattern or entry, the bot must name the HTF candle it is trading** (e.g. "the daily CRT inside the weekly candle"); the entry model is the last thing considered.
- Sources: romeo/07 (5:33–5:49, 14:26); romeo/10 (11:44–12:31); romeo/12 (8:02, 9:30); sham/08 (1:19, 1:50).
- Implementation: every setup object carries `htf`, `ltf`, `purpose ∈ {bias, framing, trade}` and `parent_htf` (the candle it sits inside). A signal without these fields is rejected.
- Confidence: high.

**CRT-R02. The HTF candle must be 4H, daily or weekly; it must not be below 4H.** Monthly and above only in an "advanced" mode. 1H only for "hyper scalpers".
- Sources: romeo/07 (6:05–6:24, 8:06–8:40); romeo/10 (11:11–11:44); romeo/05 (2:53, 6:03: M/W/D, mostly W and D); romeo/02 (4:35, 8:33: M/W/D/4H, mainly D and 4H); sham/05 (25:25: D1/W1 for bias, H4 for framing).
- Implementation: `htf ∈ P:htf_allowed` (default `[4H, D, W]`); reject `htf < 4H`.
- Confidence: high for "nothing below 4H"; medium for the exact set (see C-10).

**CRT-R03. Each HTF must use its paired LTF for the entry model.** Default pairs (Romeo, model #1 "golden rule"): **Monthly → Daily, Weekly → 4H, Daily → 1H, 4H → 15m.**
- Sources: romeo/03 (16:49–17:22, 28:25); romeo/05 (6:03); alternatives in romeo/02 (5:30–6:23: M→4H, W→1H, D→15m, 4H→5m, "for viewing the PO3"); romeo/12 (daily trade, 5m entry); sham/01, sham/06, sham/11 (D1 → H4 → M15).
- Implementation: `ltf = P:tf_pairs[htf]`. Default `{M: D, W: 4H, D: 1H, 4H: 15m}`. Romeo says no alignment is fixed (romeo/02 7:46), so keep this a parameter.
- Confidence: medium (three different tables exist; see C-01).

**CRT-R04. In the Sham stack each timeframe must have one job: D1 = bias, H4 = context + candle range (framing CRT), M15 = entry confirmation. The jobs must not be mixed.**
- Sources: sham/01 (0:48, 1:39, 2:44); sham/06 (1:19–1:35); sham/10 (10:25, 13:34–13:50); sham/02 (33:15); sham/11.
- Implementation: in `P:strategy_mode = sham`, `bias_tf = D`, `framing_tf = 4H`, `entry_tf = 15m`; CSD for a D1 dealing range may use H4 (lowest allowed, sham/03 34:41).
- Confidence: high.

**CRT-R05. A LTF CRT must only be traded in the direction of the HTF CRT that contains it** (from the HTF sweep extreme, "point A", toward the HTF target).
- Sources: romeo/09 (15:31–17:50: "LTF CRT forming inside a HTF CRT"); romeo/11 (13:51–16:56, failure case 3); sham/05 (5:51).
- Implementation: `allowed(ltf_setup) := ltf_setup.dir == parent_htf_crt.dir` while `parent_htf_crt.state == active` (not yet at its final target). Counter-direction CRTs "sometimes work" but are excluded by default (`P:allow_counter_htf = false`).
- Confidence: high.

### B) Higher-timeframe bias

**CRT-R06. The next-candle bias must be read from how the last closed candle (P) ended relative to the one before it (Q):** close above Q.high → higher; close below Q.low → lower; wick above Q.high but close not above → lower; wick below Q.low but close not below → higher.
- Sources: romeo/02 (35:09–35:57, any candle); romeo/17 (12:07–12:26, weekly, CRTology); romeo/16 (21:54–22:09); sham/11 (3:27–5:04, same "close inside / close outside" logic on D1).
- Implementation:
  ```text
  def close_wick_bias(P, Q):
      if P.close > Q.high: return bull            # close above
      if P.close < Q.low:  return bear            # close below
      up   = P.high > Q.high                       # wick above, closed back inside
      down = P.low  < Q.low                        # wick below, closed back inside
      if up and not down: return bear
      if down and not up: return bull
      if up and down:     return neutral           # outside bar closed inside: PROPOSED (not from source)
      return inside                                # inside candle (romeo/16 25:22 "inside week", subtype not taught)
  ```
- Confidence: high (stated in both an old and a CRTology video).

**CRT-R07. The close/wick signal (R06) must not be traded on its own; it must be paired with a key level and the market-profile requirement.** "A wick in a bullish market is going to be filled"; do not chase wicks.
- Sources: romeo/16 (22:26–23:33); romeo/17 (6:17–6:51, 17:50–18:44).
- Implementation: `bias_ok := close_wick_bias(...) in {bull,bear} and key_level_present(dir) and market_profile_ok(dir)`. `market_profile_ok` is not defined by Romeo; v0.1 proxy in G-04.
- Confidence: high for the requirement; low for how to compute market profile.

**CRT-R08. In Sham mode the daily bias must come from D1 market structure S and the previous daily candle's close C, using this table; conflicting signals must give "neutral" (no trade).**
- Sources: sham/11 (3:59–9:32); sham/03 (13:45–14:02, 19:23–20:12).
- Implementation:
  ```text
  S = structure(D)                        # CRT-R15
  C = close_wick_bias(D[-1], D[-2])       # CRT-R06 classes
  if C is close-beyond (close above/below):  bias = direction of that close    # "continuation of the current leg"
  elif S == bull and C == bear(wick above):  bias = bear                       # retracement expected
  elif S == bull and C == bull(wick below):  bias = bull                       # retracement complete
  elif S == bear and C == bull(wick below):  bias = bull                       # retracement
  elif S == bear and C == bear(wick above):  bias = bear                       # retracement complete
  if retracement_reached_eq and C is close-beyond against S: bias = neutral    # sham/11 7:44–8:30
  ```
  Optional inputs (sham/03 19:23, sham/06 1:51): weekly OHLC, monthly OHLC, SMT (P:bias_inputs).
- Confidence: high for the table; medium for the optional inputs (see C-13).

**CRT-R09. A D1/W1 "CRT for bias" must be confirmed by the purging candle closing back inside the CRT range; then bias is held toward the opposite end until it is reached. If the purging candle closes outside, the CRT is rejected.**
- Sources: sham/05 (25:25–27:45); sham/08 (12:39–13:26, 16:21–17:39, 28:50); romeo/02 (42:55 "let it go").
- Implementation:
  ```text
  on close of candle N after CRT candle R (htf in {D, W}):
      if swept(R.high, N) and N.close <= R.high and N.close >= R.low: bias = bear; target = R.low   # until hit
      elif swept(R.low, N) and N.close >= R.low and N.close <= R.high: bias = bull; target = R.high
      elif N.close > R.high or N.close < R.low: reject R; choose a new candidate
  ```
  Sham sometimes targets the dealing-range EQ/premium instead of the far end (sham/08 25:53, 29:22): `P:bias_crt_target = opposite_extreme | dr_eq`.
- Confidence: high.

**CRT-R10. When choosing a daily CRT for bias, the Monday daily candle must be preferred; Thursday/Friday candidates have ambiguous timing.** A Wednesday CRT is allowed in a midweek-retracement week.
- Sources: sham/08 (14:14–15:51, 26:23, 27:45–28:17).
- Implementation: candidate priority `Mon > Tue > Wed > Thu/Fri`, with `P:bias_crt_days = [Mon, Tue, Wed]`. Inside-bar rule CRT-R26 applies first.
- Confidence: medium.

**CRT-R11. While a higher-timeframe draw on liquidity / CRT target is pending, the bot must not take or consider any pattern in the opposite direction, and must treat counter-direction MSS signals near that target as fake.** The only exception is a confirmed opposing SMT (CRT-R57).
- Sources: romeo/04 (1:40–1:56, 3:01–3:18, 10:11, 29:31); romeo/10 (13:55, 18:06); romeo/14 (1:08, 1:59, 2:17); romeo/08 (12:13); sham/02 (25:09, D1 OB bias held until short-term DOL is reached).
- Implementation: `block_dir = opposite(active_target.dir)` while `active_target` is unhit. Entry functions return `False` for `block_dir`. Open trades are not closed on a counter MSS while `distance(price, target) <= P:near_target_atr (0.5) × atr(ltf,14)` (the distance is PROPOSED, not from source).
- Confidence: high.

**CRT-R12. Once the day's bias is set, trades must be taken in that direction only; the bias must be re-derived every day from new data (stateless), and a narrative must be dropped once invalidated.**
- Sources: sham/01 (14:25); sham/03 (1:20, per-day bias); sham/09 (7:12, 7:57–9:52); sham/06 (18:27: bias "can change with just a single candle").
- Implementation: `daily_bias` is recomputed at every D close from CRT-R08/R09 inputs; no carry-over flag except an active bias-CRT target (CRT-R09).
- Confidence: high.

**CRT-R13. The bot must stay neutral (no trades) on days with conflicting information: a Monday with a counter SMT at the start of a new week, ranging days (e.g. some Fridays), or a bias-table conflict.**
- Sources: sham/03 (25:15–25:48, 31:22, 33:39–34:11); sham/11 (7:44–8:30).
- Implementation: `neutral if (weekday == Mon and opposing_smt(D)) or bias_table_conflict or ranging_day_flag`. `ranging_day_flag` PROPOSED (not from source): previous day range < `P:ranging_adr_frac (0.5) × ADR(20)`.
- Confidence: medium.

**CRT-R14. A new weekly (or monthly) candle must be expected to form its opposite extreme at a HTF key level before its real expansion;** e.g. in a bullish context Mon/Tue can be bearish while the week forms its low. Romeo's weekly time theory gives the timing: in a bearish week the high forms Mon–Wed and the low is reached Thu–Fri; in the bullish template the low forms around Tuesday.
- Sources: sham/03 (21:15–22:03, 28:03–28:36: "it never happens" otherwise); sham/04 (21:42–22:28); romeo/03 (23:11–26:28); romeo/16 (8:48); romeo/17 (7:26–7:59, 10:27).
- Implementation (filter, P:use_weekly_time_theory = true):
  ```text
  if weekly_bias == bear: allow short entries whose sweep high is on Mon|Tue|Wed; prefer Thu for model #1 (romeo/03 26:28)
  if weekly_bias == bull: allow long entries whose sweep low is on Mon|Tue|Wed (Tue preferred)
  # Day-of-week membership by NY date of the sweep bar.
  ```
- Confidence: medium (stated as typical, not absolute, by Romeo; stated as absolute by Sham).

**CRT-R15. Market structure must be labelled bullish when price rejects below old lows and breaks above old highs (higher highs, higher lows, bullish expansions); bearish is the mirror.**
- Sources: sham/03 (13:45–14:02); sham/01 (4:36–4:52); sham/11 (1:51–2:55).
- Implementation PROPOSED (not from source) on the swing list of `tf`: `bull` if the last swing high was broken by a close and the last swing low that was swept closed back inside (TS); `bear` mirror; else `range`. Parameters `P:swing_n`, `P:structure_break = close`.
- Confidence: medium (concept clear, algorithm ours).

**CRT-R16. In Sham mode a trade in the main structure direction must wait until price has rebalanced the dealing range (reached EQ or premium for a bearish range); exceptions: the KOD-S sequence and the all-time-high case.**
- Sources: sham/01 (8:36–9:25, default; 10:26–13:07 KOD-S exception); sham/06 (20:36–21:24 "the only exception"); sham/08 (22:44–24:18, 35:44–36:00; 7:36–8:24 ATH case); sham/11 (12:29).
- Implementation:
  ```text
  rebalanced(bear) := max(high since dr formed) >= dr.eq      # P:rebalance_level = eq | premium_fvg
  allow_main_dir := rebalanced or kod_s_active or (no_dr_above and at_ath)
  kod_s_active PROPOSED (not from source): dist(price, long_term_dol) < P:kod_s_dist (0.25) × dr.height
                    and smt_present and retracement stayed below dr.eq
  ```
- Confidence: high for the default; low for the KOD-S trigger numbers.

**CRT-R17. If the weekly/monthly candle has already delivered its expected expansion, the next day may be traded against the HTF bias** ("has price already delivered what it needed to deliver?"). A Sham counter-trend trade is allowed when the short-term DOL is the rebalance of a new dealing range confirmed by a strong SMT.
- Sources: sham/04 (20:06–21:27); sham/06 (13:07, 14:46–16:06, 19:00–20:05); sham/02 (20:53: monthly objective done in the last week of the month → expect a retracement).
- Implementation: PROPOSED proxy (not from source): `delivered(W) := W has traded through its target PDA/DOL` or `W.range >= P:delivered_adr_mult (5) × ADR(20)` in the bias direction. Off by default (`P:allow_delivered_counter = false`).
- Confidence: low.

### C) Key level

**CRT-R18. A CRT must always be paired with a key level, and C2 must sweep that key level.** Trading CRT without a key level is "a beginner mistake".
- Sources: romeo/10 (2:27, 3:33, 3:54); romeo/02 (10:31–11:19 "open → key level → TS → decline"); romeo/07 (8:40–8:57); sham/05 (12:48–13:05, "true expansions happen only after liquidity is taken and a HTF key level is tested").
- Implementation: `crt_valid := exists kl in key_levels(htf_above, dir) with C2 swept kl and kl within [C2.low, C2.high]` (bearish: `C2.high >= kl`). Key levels come from CRT-R19.
- Confidence: high.

**CRT-R19. Key levels must come only from this candidate set, on a timeframe higher than (or equal to) the CRT timeframe:** unswept old swing highs/lows; previous day/week highs and lows; the open of the last down-close candle (support) / up-close candle (resistance); 50% of the weekly wick; HTF FVGs and OBs.
- Sources: romeo/02 (10:47–11:04, 13:32: high may be a wick or a body); romeo/03 (17:52, 28:25); romeo/09 (17:02–17:33); romeo/17 (14:51, 19:16; pair with "the most visible" same-TF old low, 17:50–18:44); sham/10 (7:44); sham/08 (2:53, 5:30); sham/02 (2:45, 3:01).
- Implementation:
  ```text
  key_levels(tf, dir) = union(
      unswept swing lows (bull) / highs (bear) on tf             # P:swing_n
      PDL/PWL (bull), PDH/PWH (bear)
      open of most recent down-close candle on tf (bull) / up-close (bear)
      0.5 * (W[-1] lower wick) for bull:  (min(open,close) + low)/2   # upper wick for bear
      unfilled FVGs and OBs on tf in the matching half (discount bull, premium bear)
  )   # which members are enabled: P:kl_types
  ```
  Which wick to use when a week has both is not stated (romeo/17 open question); default: the lower wick for bull, upper for bear (PROPOSED, not from source).
- Confidence: medium (each type is sourced; the selection among them is a gap, G-01).

**CRT-R20. The bot must not buy bullish CRTs or bullish MSS that form on the way down before price has touched the bullish key level; the first bottoming pattern above the level is assumed fake.** Mirror for bearish.
- Sources: romeo/08 (12:13–12:46, 13:04, 14:57–15:13: "always ... no exception"); romeo/14 (1:42–1:59).
- Implementation: `long_allowed := min(low since setup start) <= kl + P:kl_touch_tol × atr(ltf,14)` (tolerance default 0, PROPOSED). Any bullish model #1/MSS whose sweep low is above `kl` is ignored.
- Confidence: medium (stated strongly but is a claim to test).

**CRT-R21. A bearish CRT/OB must sit at a premium key level and a bullish one at a discount key level of the relevant dealing range** ("buy low, sell high").
- Sources: romeo/01 (20:07); romeo/02 (28:17); sham/05 (2:54, 7:10, 8:30); sham/11 (11:24); sham/02 (13:12 factor 4); sham/08 (2:53).
- Implementation: bearish: `C1.high >= dr.eq` (or `kl > dr.eq`); bullish: `C1.low <= dr.eq`. In Romeo mode, PROPOSED (not from source): use the parent HTF candle's 50% as EQ when no dealing range is defined.
- Confidence: high.

**CRT-R22. The key level's timeframe sets the timeframe of the expansion it produces:** monthly KL → weekly expansion; weekly KL → daily; daily KL → 4H; 4H KL → 1H or 15m.
- Sources: romeo/17 (8:16–8:52, CRTology).
- Implementation: `kl.tf` must be `P:kl_tf_for_htf[htf]`, default `{W: M, D: W, 4H: D, 1H: 4H}` (inverse of Romeo's map). Used to pick which key levels feed CRT-R18.
- Confidence: medium (see C-01: a fourth TF table).

**CRT-R23. If price tags the planned key level before the CRT candle exists, or outside a key time, or misses the key level entirely, there must be no entry from it.**
- Sources: sham/05 (3:26–4:14, 17:38–18:58); sham/04 (13:56–14:12).
- Implementation: `entry_allowed(kl) := first_touch_time(kl) > crt_candle.close_time and in_key_time(first_touch_time)`; if `kl` never touched before the killzone ends → setup expires.
- Confidence: high (Sham).

### D) CRT formation (candle 1 / 2 / 3)

**CRT-R24. The CRT levels must be computed from C1 only: CRT high = C1.high, CRT low = C1.low, CRT 50% = midpoint of C1.**
- Sources: romeo/02 (16:32, 34:37); romeo/05 (6:36–7:08); romeo/10 (5:50); romeo/11 (12:17).
- Implementation: see DEF-02/DEF-03. If inside bars follow C1, C1 stays the reference (CRT-R26).
- Confidence: high (the full-wick 50% is medium).

**CRT-R25. The bot must wait for C2 to close and must classify it; if C2 closes beyond the C1 extreme it swept, it is a breakout: the setup must be dropped ("let it go").** Only a sweep followed by a close back inside (turtle soup) makes a CRT.
- Sources: romeo/02 (2:04–2:38, 42:55–43:11); romeo/10 (6:08–6:56: shape known only at the close); sham/08 (17:39) for the bias CRT.
- Implementation:
  ```text
  on close of C2:
      cls = DEF-05(C1, C2)
      if cls == breakout: drop; return
      if cls == ts_high: crt = CRT(dir=bear, C1, C2)
      if cls == ts_low:  crt = CRT(dir=bull, C1, C2)
      if cls == inside:  keep C1, wait for next candle (CRT-R26)
  ```
  Whether this close-back-inside is required on the 4H depends on mode (CRT-R29).
- Confidence: high.

**CRT-R26. If the newest candles are inside an earlier candle, the outer (mother) candle must be used as C1;** "C1, inside bars, then turtle soup" is the same CRT.
- Sources: romeo/02 (2:38); sham/08 (30:40).
- Implementation: `while next.high <= C1.high and next.low >= C1.low: skip next` up to `P:max_inside_bars` (default 3, PROPOSED, not from source).
- Confidence: high.

**CRT-R27. In Sham mode a purge must only count if it happens after the CRT candle has closed; repeated sweeps of lesser highs/lows inside a still-forming candle are invalid.**
- Sources: sham/05 (4:14–4:31, 14:25–15:46, 20:32–21:36).
- Implementation: `valid_purge(bar, R) := bar.open_time >= R.close_time and swept(R.extreme, bar)`.
- Confidence: high.

**CRT-R28. In Sham mode the 4H framing CRT must be a closed 4H candle that sits at the refined key level in the correct premium/discount half of the 4H dealing range, aligned with the daily bias, and selected at or after the session start.** If the selected candle is invalidated, the next 4H candle (e.g. the 05:00 candle) may be re-selected.
- Sources: sham/06 (8:52–10:12); sham/11 (12:45–13:00: "the 4H candle that closed inside the discount key level"); sham/05 (9:04–9:36, 11:11–12:16); sham/04 (14:59–15:15, 17:27); sham/08 (33:22: the 21:00 NY 4H candle into London).
- Implementation:
  ```text
  candidates = 4H bars with open in P:framing_candle_opens (default [21:00, 01:00, 05:00]) that are closed
  pick first c where: dir == daily_bias
                      and c.close inside kl_zone (bull: discount KL; bear: premium KL)
                      and dr rebalanced (CRT-R16)
  on invalidation of c (CRT-R32, CRT-R60): pick next candidate in the same day
  ```
  The open list is PROPOSED from Sham's named examples (21:00, 01:00, 05:00), not a stated rule.
- Confidence: medium ("which candle makes the most sense" is partly a gap, G-07).

**CRT-R29. On D and W the sweep candle must close back inside the CRT range (both sources). On 4H, Romeo mode must require it; Sham mode must not (Sham confirms the 4H CRT on the 15m instead).**
- Sources: romeo/02 (2:04–2:38, TS definition for every candle); romeo/07 (6:40–7:30, every TF works the same); sham/08 (20:19, 34:09: "the 4H candle does not need to close back inside"); sham/11.
- Implementation: `P:require_close_inside = {W: true, D: true, 4H: true}` in Romeo mode; `{W: true, D: true, 4H: false}` in Sham mode.
- Confidence: high for each source's own position (see C-04).

**CRT-R30. The bot must enter only in candle 3 or later (after C2 has closed); entries inside C2 must be disabled by default.**
- Sources: romeo/06 (1:10–2:14, 5:50–6:59); romeo/09 (5:51); romeo/10 (4:43); romeo/02 (27:11 "avoid trades in C2 if you can"; 37:21 C2 entries are "most advanced").
- Implementation: `entry_time >= C2.close_time` unless `P:allow_c2_entry = true`. Romeo mode only; Sham's framing CRT has no C2/C3 split (sham/05 28:33).
- Confidence: high.

**CRT-R31. Only CRTs in the bias direction must be considered; with a bearish bias, bullish CRTs (purges of lows) are ignored.**
- Sources: sham/05 (5:51–6:06); sham/08 (2:22, 5:13); romeo/11 (13:51–16:56).
- Implementation: `crt.dir == bias` (bias from CRT-R06/R08/R09, by mode).
- Confidence: high.

### E) Timing filters

**CRT-R32. In Sham mode the CRT purge must happen inside a key time (killzone or macro); a purge outside key time invalidates that candle range and the trade idea.**
- Sources: sham/06 (10:28–10:43, 13:24–14:28); sham/04 (7:48–8:34, 11:16–11:49: Asian-high purge outside key time is invalid); sham/08 (18:59–19:14); sham/05 (19:14).
- Implementation:
  ```text
  in_key_time(ts) := ts.time in any(P:killzones) or ts.time in any(P:macros)   # P:key_time_strictness = killzone|macro
  on first valid_purge(bar, crt):
      if not in_key_time(bar.open_time): crt.state = invalid   # then CRT-R28 may re-select the next 4H candle
  ```
  Default killzones: London 02:00–05:00, NY 07:00–10:00, London close 10:00–12:00. Default macros: 03:00, 06:00, 09:00, 11:00 (06:00 see C-15).
- Confidence: high.

**CRT-R33. In Sham mode the entry order block must form inside a key time; otherwise the idea is invalidated. Price at the key level in key time is not enough: an OB (or FVG) must form.**
- Sources: sham/11 (11:56–12:14, 13:48); sham/02 (13:12 factor 5, 31:03: the 09:00 macro); sham/04 (14:12–14:59, 16:53–17:11).
- Implementation: `ob.engulf_bar.open_time in key_time` else `crt.state = invalid`.
- Confidence: high.

**CRT-R34. The bot must not select candles or trade during the Asian range or around midnight; before the session/killzone it must only monitor.**
- Sources: sham/05 (6:22–6:54); sham/06 (8:52–9:25); sham/07 (25:17–26:21).
- Implementation: `no_new_setups if 20:00 <= time < 02:00` (Asia + until London open). Romeo mode does not have this rule; apply it there only if `P:asia_block_romeo = true` (default false).
- Confidence: high (Sham).

**CRT-R35. In Romeo mode the bot should prefer setups that follow the weekly template: Monday chop/consolidation, Tuesday stab into the key level via a turtle soup of the consolidation, expansion Wednesday to Friday.**
- Sources: romeo/17 (7:26–7:59, 10:27, 22:06); romeo/16 (8:48, 15:17); romeo/03 (24:35–26:28); romeo/12 (10:07, 15:28: Tuesday London entry).
- Implementation: tag every setup with `weekday(sweep_bar)`; filter `P:romeo_sweep_days` (default `[Mon, Tue, Wed]`) and log results by weekday. The intraday window Romeo uses is not stated; PROPOSED (not from source): reuse Sham's killzones as an optional filter (`P:romeo_use_killzones = false`).
- Confidence: medium.

**CRT-R36. If the HTF manipulation (sweep) happened at the end of the previous HTF candle, the bot must expect the next candle to distribute quickly with only minimal manipulation** (e.g. a Friday sweep for a weekly).
- Sources: romeo/09 (7:31–8:05, 10:04–10:35).
- Implementation PROPOSED (not from source): `late_manip := sweep_time >= prev.open + P:late_frac (0.8) × duration(prev)`. If true, allow entries from the first LTF trigger after the new candle opens without waiting for a fresh sweep of the new candle's opposite side.
- Confidence: low.

### F) Entry models

**CRT-R37. After a sweep/purge the bot must not enter immediately; it must wait for the entry model, which is always the last step. If no entry model forms, there must be no trade.**
- Sources: romeo/05 (18:27); romeo/07 (5:33); romeo/16 (15:00–15:54: only when the full model is present); sham/06 (6:08–6:29, 11:14, 18:27); sham/04 (14:12–14:59); sham/08 (38:07–38:56).
- Implementation: a setup creates a pending state; orders are placed only when an entry function (R38–R42, by mode) returns a signal before the setup expires (`P:setup_expiry`, default end of the C3 candle in Romeo mode, end of the current killzone in Sham mode; PROPOSED, not from source).
- Confidence: high.

**CRT-R38. Romeo mode entries must be either a model #1 or a true MSS (with its retrace / OTE).**
- Sources: romeo/12 (14:16, 14:46); romeo/06 (9:17: TS and model #1 are his "two favorite" entries; breaker/OTE/KoD are re-entries); romeo/02 (39:38–40:14: entry 1 = TS/model #1, entry 2 = OB, entry 3 = MSS then breaker or OTE).
- Implementation: `romeo_entry := model1_signal or mss_retrace_signal or ote_signal` (R39–R41).
- Confidence: high.

**CRT-R39. Model #1 entry: on the LTF, the bot must find the one thick opposite-close candle that swept the key level (the CRT extreme) and must enter only when a later LTF candle closes beyond it; a wick through it must not trigger.**
- Sources: romeo/02 (37:21–39:22); romeo/03 (9:59–10:52, 11:42, 15:05–15:38, 20:04–20:20, 22:01, 27:04); romeo/09 (18:08–19:21, 28:44); romeo/11 (8:30–9:02); romeo/12 (1:51–2:43).
- Implementation (bullish):
  ```text
  M = DEF-08 model candle at the CRT low / key level (ltf), thick(M) if P:require_thick
  T = first ltf bar after M with T.close > ref(M)     # P:model1_trigger_ref = wick (M.high) | body (M.body_top)
  entry: market at T.close  (P:model1_entry = close)  | limit at M.high (P:model1_entry = model_high)
         # romeo/03 20:04 "as soon as they close, that's the trigger"; 20:20 "entry is the high of model number one"
  stop: CRT-R49
  ```
  Expire if price makes a new low below `M.low` before `T` (PROPOSED, not from source).
- Confidence: high for the pattern; medium for trigger reference and entry price (C-07).

**CRT-R40. True-MSS entry: after the turtle soup of the low, the bot must wait for a candle close above the high that broke the low, then wait for a retrace into the zone between that high and the TS low, and buy there.**
- Sources: romeo/12 (8:46, 15:28, 16:16); romeo/06 (11:52–12:28, 16:14–18:00); romeo/08 (13:51–14:06, 16:46–17:34); romeo/11 (9:17–9:32); romeo/17 (22:39–22:58).
- Implementation:
  ```text
  mss = DEF-10 on ltf (sweep L2 must be at the CRT low / key level, CRT-R20)
  after mss bar: limit buy when price re-enters the entry zone
  entry zone: P:mss_entry_zone = ote          # default: OTE 0.50-0.79 of the MSS leg (CRT-R41; CRTology is newer)
                               | full_retrace # variant: anywhere in [L2.low, H.high] (romeo/12 16:16)
  ```
- Confidence: high.

**CRT-R41. Romeo OTE entry: the OTE must be activated only by a candle close (not a wick) through the low that broke the high (bearish), and entry must be inside the 0.50–0.79 retracement of leg one; a fixed fib level (0.618/0.705) must not be required.** The shallow half is preferred.
- Sources: romeo/18 (1:59–14:16, CRTology); romeo/10 (19:11–21:44: price need not reach 50%; near-50% plus a TS of a key level is enough); romeo/17 (22:39–22:58).
- Implementation (bearish):
  ```text
  structure: swing high SH1, swing low SL (the low that broke the high), higher high HH into a key level
  activation bar A: A.close < SL.low
  leg1_end = min(low) after A until first bar with close > (leg1_end + P:leg_end_atr × atr)   # G-14
  zone = fib(HH.high -> leg1_end, P:ote_zone = [0.50, 0.79])   # P:ote_fib_basis = wick | body | union | intersection
  entry: P:ote_trigger = touch   -> limit sell at the 0.50 level of the zone (first touch of the zone)
                       | ltf_ts  -> sell when a lower-TF turtle soup / CRT forms inside the zone (romeo/18 7:45, 14:16)
  prefer: reaction inside [0.50, 0.65] (romeo/18 13:45) -> logged, not a filter in v0.1
  ```
  Romeo says a "wave" of several closes through the level is better than one (romeo/18 2:32): log `closes_through_count`.
- Confidence: high for the pattern and zone; medium for leg-end and trigger details.

**CRT-R42. When an SMT appears, the bot must not enter blindly: it must take SMT setups only in the HTF direction and only after confirmation on the asset that took the level.** Romeo ep.6: two confirmations in order, (1) a model #1 close, then (2) a true MSS for further expansion. Romeo ep.8: a model #1 *or* a true MSS.
- Sources: romeo/09 (27:57–31:05); romeo/11 (8:13, 9:47); romeo/12 (12:43, 13:39); romeo/08 (10:45: BTC needs ETH).
- Implementation: `smt_entry := smt(...) and htf_dir == smt.dir and confirm(P:smt_confirm = model1_or_mss | model1_then_mss)`. Default `model1_or_mss` for the first entry; add to the position only after the MSS (PROPOSED reading that reconciles both, see C-08 and C-23).
- Confidence: medium.

**CRT-R43. Sham mode entry: after a valid purge of the 4H CRT at a key time, the bot must wait for a 15m order block (CSD) in the trade direction and enter with a limit order at the OB edge nearest to price** (longs: OB high; shorts: OB low).
- Sources: sham/11 (13:00–13:31); sham/02 (31:52, 40:04); sham/06 (11:14–11:32, 16:52, 22:45); sham/08 (20:19, 36:16, 37:36); sham/05 (28:03–28:33); sham/01 (18:39–18:56: "at the open of the OB").
- Implementation:
  ```text
  after valid_purge (CRT-R27, CRT-R32):
      ob = DEF-15 on 15m, the run G must include the purge bar(s), engulf bar in key time (CRT-R33)
      entry_limit = ob_top (long) | ob_bottom (short)       # P:ob_entry_edge = near_edge | open
      if price rebalanced dr first required (CRT-R16): ignore OBs formed before rebalance (sham/08 35:44)
  ```
- Confidence: high.

**CRT-R44. In candle 3, a bearish entry must be above C3's open and a bullish entry below C3's open.**
- Sources: romeo/02 (21:11–22:48; he mis-says "sell below" at 22:32); romeo/10 (24:16); romeo/07 (8:40–8:57, candle anatomy: open, move against, then expansion).
- Implementation: `bear: entry_price > C3.open`; `bull: entry_price < C3.open`. Weekly variant: use the Monday 00:00 open (romeo/02 21:44; C-02).
- Confidence: high.

**CRT-R45. The bot must not chase: if candle 3 does not give the planned entry, skip; if a later-stage entry (breaker/OTE) has already been hit, the bot must not look for the first-stage entry (TS / model #1).**
- Sources: romeo/10 (23:26); romeo/02 (39:38–40:14); romeo/04 (16:36–16:51: sell "at the extremities").
- Implementation: setup stage counter `stage ∈ {ts_model1, ob, mss_ote}`; an entry of stage k is not allowed once stage > k has triggered. If `price reaches crt_50` before any entry → `skip` (PROPOSED reading of "no chasing", not from source).
- Confidence: medium.

**CRT-R46. Confluence scoring: an entry should be ranked higher when** the model candle comes with an FVG (Romeo), and an OB should stack Sham's five probability factors (HTF bias/DOL alignment, at a HTF key level, SMT, correct premium/discount half, formed at a key time).
- Sources: romeo/03 (15:59, 20:38–21:12, 27:53); romeo/05 (17:36–18:12: FVG above an old high supports the KoD sell); sham/02 (13:12–17:43).
- Implementation: `score = sum(factors)`; `P:min_confluence` (default: no hard filter in v0.1; log the score). FVG "with" the model candle PROPOSED (not from source): an FVG whose middle bar is M or T, within 3 bars.
- Confidence: medium.

**CRT-R47. For longs the bot must not enter at the part of an OB that lies in premium of a just-formed dealing range; wait for the discount part (mirror for shorts).**
- Sources: sham/02 (37:43–39:01; refined OB 27:01, 28:04).
- Implementation: `entry_limit = min(ob_top, dr.eq)` for longs if `ob` straddles `dr.eq`; if `ob_bottom > dr.eq` → no entry.
- Confidence: medium.

**CRT-R48. Re-entries: if the first OB entry is missed, a later close beyond the whole candle group creates a second OB entry (Sham); in Romeo mode the breaker/OTE and the KoD-R turtle soup are valid re-entries after the TS/model #1.**
- Sources: sham/02 (40:20–40:36); romeo/06 (9:17); romeo/05 (18:27).
- Implementation: `P:max_entries_per_setup` (default 1 for the backtest baseline; 2 as a variant). A re-entry uses the same target and its own stop.
- Confidence: medium.

### G) Stop loss

**CRT-R49. Model #1 stop must be at the opposite extreme of the model candle** (bullish: below `M.low`; bearish: above `M.high`).
- Sources: romeo/03 (10:34, 20:20).
- Implementation: `stop = M.low - P:stop_buffer_ticks` (buffer default 0; PROPOSED, not from source).
- Confidence: high.

**CRT-R50. Turtle-soup, true-MSS and KoD-R entries must place the stop beyond the turtle-soup (sweep) extreme.**
- Sources: romeo/12 (16:16: "if the stop is the turtle-soup extreme you are unlikely to be swept"); romeo/09 (19:04); romeo/05 (18:44: above the KoD sweep high); romeo/04 (17:09: implied above the key high).
- Implementation: `stop = L2.low` (bullish MSS) / `KoD.high` (bearish KoD). For OTE entries the stop is **not stated** (romeo/18). PROPOSED (not from source): beyond the leg-one origin `HH.high` (bearish), with the variant "beyond the 0.79 level" (`P:ote_stop = leg_origin | fib_079`).
- Confidence: high for TS/MSS; low for OTE.

**CRT-R51. Sham OB entries must place the stop just beyond the order block** (shorts: above `ob_top`; longs: below `ob_bottom`).
- Sources: sham/01 (18:56); sham/02 (31:52); sham/05 (22:08); sham/06 (11:32, 16:52); sham/08 (37:52); sham/11 (13:31).
- Implementation: `stop = ob_bottom - buffer` (long). The OB extent (body vs wick) follows DEF-15.
- Confidence: high.

**CRT-R52. Alternative stop (Romeo, CRTology): in bullish markets the low that filled a daily FVG may be used as the stop.**
- Sources: romeo/17 (25:09–25:27).
- Implementation: `P:stop_mode = default | fvg_fill_low`; `fvg_fill_low = lowest low of the bars that entered the most recent daily bullish FVG`.
- Confidence: low (one example).

### H) Targets and partials

**CRT-R53. Romeo mode targets must be: TP1 = the CRT 50%, where a partial is always taken; TP2 = the opposite extreme of C1.**
- Sources: romeo/02 (16:48–18:38, 28:00–28:17, 29:23–29:40: the 50% is "the correct technical target", not the nearest FVG); romeo/05 (6:52–7:08); romeo/10 (12:31, 24:33); romeo/11 (12:17–13:36); romeo/09 (16:12, 19:04, 20:08); romeo/06 (13:00: 50%, then old highs, then CRT high); romeo/18 (11:06).
- Implementation: `tp1 = crt_50` with `P:tp1_fraction` (default 0.5); `tp2 = crt_low` (bear) / `crt_high` (bull). If entry is already past 50% (e.g. a late KoD-R entry), the only target is TP2.
- Confidence: high.

**CRT-R54. Optional Romeo intermediate targets may be used for the partials: the body of the high that started the decline into the OTE zone ("most guaranteed"); the last high before the dump into the old low ("the high that broke the low"); "highs/lows one by one" (successive opposing swing points); relatively equal highs/lows on the way; the previous day's high when the turtle soup was not convincing.**
- Sources: romeo/18 (10:02–10:18, 11:06–11:39); romeo/17 (13:13–14:17, 15:22); romeo/03 (10:34, 19:48, 22:01); romeo/04 (23:16–23:49: partial at the initial target, further FVG = "greed" target); romeo/14 (0:52); romeo/12 (16:56–17:48).
- Implementation: `P:target_mode = crt_levels | swings_one_by_one | ote_body | last_high_before_dump | r_multiple`. `swings_one_by_one`: TPs at each unswept opposing `swing(ltf, P:swing_n)` between entry and TP2.
- Confidence: medium (each form sourced; which applies when is not defined, see C-05).

**CRT-R55. Sham mode target must be a fixed R multiple, default 3R** ("1 to 3R"), or the dealing-range EQ / DOL when it is the planned objective.
- Sources: sham/01 (18:56); sham/02 (31:52, 40:04); sham/05 (12:16, 22:08); sham/06 (11:32, 16:52, 23:00); sham/08 (37:52).
- Implementation: `tp = entry ± P:r_target (3.0) × |entry - stop|`; counter-trend trades: `tp = dr.eq` (sham/06 16:52).
- Confidence: high.

**CRT-R56. Exits may be by price or by time.**
- Sources: romeo/12 (18:14).
- Implementation PROPOSED (not from source): `P:time_exit = none | end_of_killzone | end_of_htf_candle`; default `end_of_htf_candle` for Romeo mode (close at the close of the traded HTF candle if no target hit), `none` for Sham.
- Confidence: low.

### I) Invalidation / when CRT fails

**CRT-R57. A confirmed opposing SMT must cancel the pending target:** if, before the target, a CRT in the opposite direction forms with an SMT and a confirmation (model #1 or true MSS), the bot must drop the original target and may follow the new direction. "SMT stops targets from being met."
- Sources: romeo/11 (6:19, 8:13–10:38, 16:07); romeo/04 (10:11–10:27, 15:40: the only reason a target fails); romeo/09 (24:15–25:37: SMT downgrade, expect continuation instead of a TS).
- Implementation: on `smt(opposite_dir) and confirm(opposite_dir)`: close or tighten the open trade (`P:on_opposing_smt = close | breakeven | ignore`, default `close`), set `active_target = None`.
- Confidence: high.

**CRT-R58. A close beyond the key high (the KoD-R / sweep high that started the move) must be treated as a warning; repeated decisive closes beyond it must invalidate the bias.** Price should usually not trade above the KoD-R high ("litmus test").
- Sources: romeo/04 (15:24–17:48); romeo/14 (12:18–12:34: the continuation ends when highs stop being turtle-souped).
- Implementation PROPOSED (not from source) for "decisive": `count(ltf closes > key_high, body/range >= 0.5) >= P:decisive_closes (2)` → invalidate setup, close trade. One close → move stop to break-even (`P:on_first_close_beyond = warn | breakeven`).
- Confidence: medium.

**CRT-R59. Reaching the CRT 50% and then reversing must be scored as a valid, winning CRT, not a failure; trading only from the CRT extreme to the 50% is a complete strategy.**
- Sources: romeo/11 (12:17–13:36).
- Implementation: backtest metric `crt_hit_50` (bool) separate from `crt_complete` (TP2 hit). A variant `P:target_mode = to_50_only` exits 100% at TP1.
- Confidence: high.

**CRT-R60. In Sham mode, if no 15m confirmation forms after the purge, or price keeps going against the idea, the 4H CRT must be marked invalid and the bot stays risk-off.**
- Sources: sham/08 (38:07–38:56); sham/06 (18:27–18:42).
- Implementation: invalidate if `setup_expiry` passes with no OB, or if price closes beyond the CRT extreme that was purged by more than PROPOSED `P:sham_invalid_atr (1.0) × atr(15m,14)` (not from source).
- Confidence: medium.

**CRT-R61. The bot must not take a counter-HTF CRT (wrong selection); see CRT-R05. A breakout close of C2 (CRT-R25) and a rejected bias CRT (CRT-R09) also invalidate.** This rule only groups the failure reasons Romeo lists (SMT, 50% reached, wrong selection) with Sham's.
- Sources: romeo/11 (whole episode); romeo/02 (42:55); sham/08 (17:39).
- Implementation: `invalid_reason ∈ {breakout_c2, rejected_bias_crt, opposing_smt, counter_htf, outside_key_time, no_entry_model, key_level_missed, decisive_close_beyond}`; every invalidation is logged with its reason.
- Confidence: high.

### J) Trade management and risk

**CRT-R62. Every trade must risk a fixed amount (fixed fraction of equity); the value is not given by either source.**
- Sources: sham/07 (4:12–4:28: fixed risk per trade, exposure limits, daily loss limit, capital preservation); romeo/16 (13:06–18:24: audit over-leverage / risking too much).
- Implementation: `size = equity × P:risk_per_trade / |entry - stop|`. Default PROPOSED (not from source): 0.5%.
- Confidence: high for the rule; the number is ours.

**CRT-R63. The bot must enforce a daily loss limit and an exposure cap.**
- Sources: sham/07 (4:12–4:28).
- Implementation: stop opening trades for the NY day once `realized_pnl_day <= -P:daily_loss_limit` (PROPOSED default 1R, not from source); `open_risk_total <= P:max_open_risk` (PROPOSED 1%).
- Confidence: high for the rule; values ours.

**CRT-R64. Trade frequency must stay low: about one to two trades a week, at most about one a day; never trade "because the market is open" or out of boredom.**
- Sources: romeo/07 (11:17); romeo/16 (13:06–15:54); sham/09 (0:00–1:22: 5 trades in a month).
- Implementation: `P:max_trades_per_day = 1`, `P:max_trades_per_week = 2`. Backtest flag: if signals per week ≫ 2, filters are looser than the sources' (sham/09 implication).
- Confidence: medium.

**CRT-R65. After a HTF CRT is complete, or after the day's objective is reached, the bot must stop trading that setup/day and wait for the next one.**
- Sources: romeo/04 (23:49); sham/06 (17:07–17:39); sham/02 (46:48–47:21: after the short-term DOL is reached stay neutral until a new opposite OB forms).
- Implementation: `on target_hit(setup): setup.state = done`; Sham mode: `day_done = true` until the next NY day.
- Confidence: high.

**CRT-R66. On high-impact news days (FOMC named) the bot must be risk-off.**
- Sources: sham/06 (17:54–18:11).
- Implementation: `no_trades if date in news_calendar(P:news_events = [FOMC])`. The window (whole day vs ±N hours) is not stated; default whole NY day (PROPOSED). Other events (NFP, CPI) are not named in the sources: `P:news_events` may add them only as a tested variant.
- Confidence: medium (one example).

**CRT-R67. On Friday the bot must take profit at 2R instead of 3R before the market closes, and must not hold positions over the weekend.**
- Sources: sham/04 (18:30–18:46).
- Implementation: `if weekday == Fri: tp = min(tp, entry ± 2R)`; force-close all positions at `P:friday_flat_time` (PROPOSED default 16:00 NY, from Romeo's "Friday 16:00 when the action dies out", romeo/17 17:34).
- Confidence: medium.

**CRT-R68. Once in a trade toward a pending target, the bot must take the partial at the first target and hold the rest; it must not exit on bounces or counter MSS that form near the target, and must not exit early at break-even before the target.**
- Sources: romeo/04 (23:16–23:49); romeo/14 (1:08–2:17; final move expected fast, 10–30 minutes, 1:24, 1:59); romeo/16 (13:06–18:24: exiting too early or too late is an execution error); romeo/09 (20:08).
- Implementation: after TP1, `stop` may move to entry only if `P:be_after_tp1 = true` (default false, since Romeo lists early break-even exits as a mistake); counter-MSS signals do not close the trade (CRT-R11) unless CRT-R57/R58 fire.
- Confidence: medium.

**CRT-R69. The bot must trade only when every condition of the model is true, must not skip valid setups, and the rule set must not be changed after losses without data from a large sample.**
- Sources: romeo/16 (15:00–15:54); sham/07 (7:27–7:58, 13:33–16:30); sham/10 (8:15–8:50, 16:28–16:44: one mechanical entry model, one checklist).
- Implementation: each rule-set version has an ID (this file's version); backtest and live results are always stored per version; no parameter changes in live mode.
- Confidence: high.

### K) Weekly routine (Saturday / Sunday)

**CRT-R70. Every Saturday the bot must log, for the asset traded, the previous week's: high and low with weekday and exact time, weekly candle shape class, the key level where the weekly high/low formed, and the execution audit.**
- Sources: romeo/16 (5:13–9:04, 13:06–18:24, CRTology); romeo/16 (6:05: one asset).
- Implementation:
  ```text
  weekly_log(W): {how_time, how_weekday, low_time, low_weekday,
                  shape = classify_week(W)            # G-03 proxy (Romeo's six types not yet listed)
                  kl_at_high = nearest key_levels(W/D) to W.high within tol, kl_at_low = ...
                  audit = {max_risk_used, trades_count vs P:max_trades_per_week,
                           trades_outside_model, early_exits, late_exits,
                           prediction (R71) vs actual}}
  ```
- Confidence: high (the shape classes themselves are a gap).

**CRT-R71. Every Sunday the bot must prepare the coming week: compute last week's close/wick bias against the week before (CRT-R06), mark last week's high and low (and other highs/lows) as liquidity pools, mark the weekly open, and store a prediction of next week's candle as up / down / inside.**
- Sources: romeo/16 (21:54–25:55); romeo/17 (5:24, 12:07–12:41, 14:51, 15:22, 17:19).
- Implementation: job at Sunday 12:00 NY (PROPOSED time): `weekly_bias = close_wick_bias(W[-1], W[-2])`; `pools = [W[-1].high, W[-1].low] + unswept swings(W, D)`; `kl_week = 50% of W[-1] wick` (CRT-R19); `prediction = weekly_bias`. During the week log how price reacts at each pool (up-then-down, down-then-up, down-then-consolidate, no touch) (romeo/16 25:02).
- Confidence: high.

**CRT-R72. At the start of each week the full Sham analysis (structure, dealing range, DOLs, weekly/monthly OHLC, SMT) must be done, then updated each day; each day has a pre-session plan, an active window and passive monitoring.**
- Sources: sham/03 (40:03–40:36); sham/07 (25:17–26:21).
- Implementation: scheduler: Sunday job (R71) + daily job at 00:00 NY (bias, CRT-R08/R12) + active window = `P:killzones` + passive (alerts only) outside them.
- Confidence: high.

**CRT-R73. Reviews and statistics must be kept per asset; the bot must not mix several assets in one weekly review.**
- Sources: romeo/16 (6:05).
- Implementation: all logs keyed by `symbol`.
- Confidence: medium.

---

## 4. Romeo vs Sham comparison

The two sources describe two different, partly overlapping systems. v0.1 implements both as **modes** (`P:strategy_mode = romeo | sham | hybrid`) so a backtest can compare them on the same data.

| Topic | Romeo | Sham | v0.1 default |
|---|---|---|---|
| What CRT is | Every candle is a range; next candle breaks out (close beyond) or turtle-soups (wick beyond, close inside); C1/C2/C3 = AMD (romeo/02) | A HTF candle treated as a "true range" only in the right ICT context; tells you which purge is valid (sham/05) | Romeo structure (DEF-05, DEF-24) |
| HTF candles | 4H / D / W; M+ for advanced (romeo/07) | D/W = bias CRT; 4H = framing CRT (sham/05, sham/08) | `[4H, D, W]` |
| Execution TF | Model #1 pairs M→D, W→4H, D→1H, 4H→15m (romeo/03); other tables exist (C-01) | D1 → H4 → M15 always | Romeo pairs; Sham fixed stack in Sham mode |
| Bias | Close/wick rule on previous candle, weekly first ("The Lens", romeo/17) | D1 structure × close inside/outside matrix; bias CRT confirmation; weekly/monthly OHLC; SMT (sham/03, sham/11) | Romeo weekly bias + Sham daily matrix in hybrid |
| Key level | Old HTF high/low; open of down/up-close candle; 50% of weekly wick; CRT high/low; selection not taught | OB, FVG, significant highs/lows, PWH/PWL; must be in premium/discount | Union candidate set (CRT-R19) + G-01 proxy |
| Close back inside | Required (TS definition, every TF) | Required on D/W bias CRT; **not** on 4H framing CRT | Per mode (CRT-R29) |
| Candle count | 3 candles (2-candle CRT exists) | Irrelevant (2–5) | Romeo 3-candle; Sham any count |
| Which candle to enter in | C3 only for most traders | Not framed as C2/C3; after a purge at key time | C3 (Romeo mode) |
| Timing | Weekly time theory (HOW Mon–Wed / Thu–Fri), Tuesday stab; "time beats price" but no intraday windows public | Killzones and macros (03, 06, 09, 11 NY); purge and OB must be in key time; no Asia | Sham windows in Sham mode; Romeo weekday filter in Romeo mode |
| Entry model | Model #1 or true MSS (+ retrace/OTE 0.5–0.79) | 15m OB (CSD) at key time, limit at OB edge | Per mode |
| Order blocks | Sceptical ("not supply and demand", "fake order blocks", romeo/02 39:06, romeo/09 10:56) | Central concept with an exact definition (sham/02) | Sham mode only |
| SMT | Only reason a target fails; needs confirmation; only in HTF direction | Confluence; can replace a full sweep at key time; counter SMT can make a day neutral | Both, per CRT-R42 / R57 / R13 |
| Stop | Model candle extreme; TS extreme; daily-FVG-fill low | Beyond the OB | Per mode |
| Target | 50% (partial) then opposite C1 extreme; other forms exist | Fixed 3R (1–3R); 2R on Friday | Per mode |
| Kiss of death | Last TS before the target (trap) | "KOD sequence": last leg near the DOL, retrace ends in discount, no rebalance needed | Both kept, different names (DEF-13) |
| Risk | Over-leverage audit; 1–2 trades/week | Fixed risk, daily loss limit, FOMC off, flat on Friday, ~5 trades/month | Sham risk rules apply to both modes |
| Routine | Saturday review + Sunday prep (CRTology "SS") | Start-of-week analysis + daily pre-session / active / passive | Both |

---

## 5. Conflicts and decisions

Principle for v0.1 defaults: **Romeo decides CRT structure; Sham adds timing, OB and risk detail; newer Romeo (CRTology 2026, romeo/16–18) beats older Romeo.** "Decide by" says whether the choice should be a backtest parameter or a user decision.

**C-01. Timeframe pair tables differ between Romeo videos.**
- Options: (a) romeo/03 + romeo/05 model #1 "golden rule": M→D, W→4H, D→1H, 4H→15m (romeo/05 omits 4H). (b) romeo/02 "viewing PO3": M→4H, W→1H, D→15m, 4H→5m. (c) romeo/17 (CRTology) key-level → expansion: M→W, W→D, D→4H, 4H→1H/15m. (d) romeo/12 trade: daily candle, 5m entry. (e) Sham: D1→H4→M15.
- Reading: (a), (b) and (c) answer different questions (where to execute model #1, where to watch PO3, which TF a key level drives). (c) is newest but it maps key levels, not execution.
- v0.1 default: execution pairs = (a); key-level TF = (c) (CRT-R22); Sham mode = (e).
- Decide by: **backtest** (`P:tf_pairs`, test (a) vs (b) vs one step lower).

**C-02. Weekly candle open and close.**
- Options: open Sunday 17:00 NY (romeo/02 17:34; romeo/06 18:51 weekly separators at Sunday; romeo/10 10:54 "weekly open on Sunday") vs Monday 00:00 NY (romeo/02 17:49 "true week open of course is Monday"; romeo/03 24:03; romeo/09 14:38 "they open on Monday, not Sunday evening"). Close Friday 17:00 (romeo/03 24:19) vs Friday 16:00 (romeo/17 17:34, CRTology: "when the action dies out").
- v0.1 default: weekly **range** (high/low used for CRT levels and pools) = all bars from Sunday 17:00 to Friday 17:00 NY (that is what FX weekly data contains); weekly **open price** (for "sell above the open", CRT-R44, and time theory) = Monday 00:00 NY; weekly close for bias = last bar before Friday 17:00. Flag Friday 16:00 as an alternative close.
- Decide by: **both**. Backtest `P:week_open = sun_1700 | mon_0000` and `P:week_close = fri_1700 | fri_1600`; the user should confirm with Romeo's book which one he uses for the weekly CRT range.

**C-03. Daily candle open: 00:00 NY vs a 17:00 NY broker day.**
- Options: Romeo's daily resets at midnight NY (romeo/02 9:57; romeo/12 10:07). Sham's 4H grid (01/05/09/13/17/21) is the grid of a broker day that opens 17:00 NY, which suggests his D1 candles may be 17:00–17:00 (not stated by Sham).
- v0.1 default: Daily = 00:00 NY (Romeo, structure source); 4H = 01/05/09/... grid (Sham, timing source). Note that a 4H candle (21:00–01:00) then spans the daily boundary.
- Decide by: **backtest** (`P:daily_open = 0000 | 1700`, `P:h4_grid = 01 | 00`) and **user** (confirm Sham's chart settings).

**C-04. Close back inside required on the 4H, or not.**
- Options: Romeo: a turtle soup always means wick beyond and close back inside, on every TF (romeo/02, romeo/07 fractal). Sham: the 4H framing CRT does not need to close back inside; the 15m OB confirms it (sham/08 20:19, 34:09; sham/11). Both require it for D/W bias CRTs.
- v0.1 default: required in Romeo mode, not in Sham mode (CRT-R29).
- Decide by: **backtest** (`P:require_close_inside.4H`).

**C-05. Targets: 50% / opposite extreme vs R multiple vs other forms.**
- Options: Romeo: TP1 = CRT 50% (partial "always"), TP2 = opposite extreme of C1 (romeo/02, 05, 10, 11). Within Romeo: "highs/lows one by one" (romeo/03); DOL old low with partial at the initial target (romeo/04); previous day high when the TS is weak (romeo/12); body of the high that started the leg, then 50%, then CRT extreme (romeo/18, CRTology); the last high before the dump (romeo/17, CRTology). Sham: fixed 3R (sham/01, 02, 05, 08), "1 to 3R" (sham/06), 2R on Friday (sham/04).
- v0.1 default: Romeo mode = 50% partial (`tp1_fraction = 0.5`) + opposite C1 extreme; Sham mode = 3R (2R Friday). CRTology targets are added as an option, not the default, because they are tied to the OTE/Lens entries.
- Decide by: **backtest** (`P:target_mode`, `P:r_target`, `P:tp1_fraction`).

**C-06. OTE zone.**
- Options: Romeo (CRTology) 0.50–0.79, wick fib, body fib as refinement, shallow half preferred, no fixed fib (romeo/18). ICT standard 0.62–0.79 with 0.705. Romeo ep.7: the retrace need not reach 50% in a strong trend (romeo/10 19:11–21:44), which is shallower than 0.50.
- v0.1 default: 0.50–0.79 on wicks (newest Romeo).
- Decide by: **backtest** (`P:ote_zone = [0.5,0.79] | [0.62,0.79] | [0.382,0.79]`, `P:ote_fib_basis`).

**C-07. Model #1 trigger: close beyond the model candle's body or its wick.**
- Options: "entry is the high of model number one" (romeo/03 20:20) implies the wick high; "ignore the wicks, look at the bodies" (romeo/02 38:15). The transcript around romeo/02 37:52 reads "you close above the wick, it doesn't count; when you close above this one specific candle ... from the high to the wick", which most likely means *a wick poking above does not count; a body close above the candle does*. So the "bodies" remark is probably about the trigger candle closing (body), not about the model candle's body top.
- v0.1 default: trigger = a **close** above the model candle's **wick high** (`model1_trigger_ref = wick`); entry at that close.
- Decide by: **backtest** (`wick | body`). Low risk either way: for a down-close model candle the body top is its open.

**C-08. Model #1 and true MSS: one sequence or two separate confirmations; which entry belongs to which candle.**
- Options: romeo/06: TS → MSS → model #1 → breaker → OTE → KoD, one sequence (and the MSS is "marked by the TS and model #1"). romeo/09: model #1 first (initial move), then true MSS (further expansion), two ordered confirmations. romeo/12: every entry is model #1 or true MSS. romeo/10: "candle 1 contains a model #1, candle 3 contains an OTE".
- v0.1 default: either model #1 or true MSS can open a trade (romeo/12, the latest of these); for SMT-based setups require model #1 first and allow adding on the MSS (CRT-R42).
- Decide by: **backtest** (`P:romeo_entry_set`, `P:smt_confirm`).

**C-09. Which candle to trade; candle count.**
- Options: Romeo: C3 only for most traders, C2 "with extreme precaution" (romeo/06, 10); romeo/02 lists a C2 entry as the most advanced. Two-candle CRT exists (romeo/10 23:06). Sham: candle count does not matter (sham/05 28:33).
- v0.1 default: C3 only in Romeo mode (`allow_c2_entry = false`).
- Decide by: **user** (risk appetite) with a **backtest** variant.

**C-10. Tradable HTF set.**
- Options: M/W/D (romeo/05); 4H/D/W with M+ for advanced (romeo/07); M/W/D/4H, 1H for hyper scalpers (romeo/10); M/W/D/4H (romeo/02).
- v0.1 default: `[4H, D, W]`.
- Decide by: **backtest** (one run per HTF) and **user** (holding time preference).

**C-11. Kiss of death: two meanings, and where it forms.**
- Options: Romeo KoD-R = the last turtle soup before a target (romeo/04, 05, 06, 10) or before a key level (romeo/08); prefers it in "the lower 25% of the range" (romeo/05 19:16, ambiguous for a bearish setup) and says it can be the OTE (romeo/05, 06, 10). Sham KOD-S = a sequence near the DOL where the retracement ends in discount and the dealing range is not rebalanced (sham/01, sham/06).
- v0.1 default: keep both as separate concepts (DEF-13). KoD-R is used only as an optional re-entry and as the stop anchor for CRT-R58. KOD-S is used only as the exception in CRT-R16. "Lower 25%" is logged (`kod_pos_pct`), not filtered.
- Decide by: **backtest** (log, then decide).

**C-12. OB entry price: OB "open" vs OB high/low.**
- Options: sham/01 enters a bearish OB "at the open"; sham/02, sham/06, sham/11 enter at the OB high (long) / low (short).
- Reading: for an up-close bearish OB candle, the body low is its open; so both mean "the OB edge nearest to price" when the OB extent is the body (DEF-15).
- v0.1 default: near edge of the OB extent.
- Decide by: **backtest** (`P:ob_entry_edge = near_edge | open | mid`).

**C-13. Daily bias inputs differ within Sham, and from Romeo.**
- Options: sham/03: structure + dealing range + DOLs + monthly and weekly OHLC + SMT + timing. sham/06: weekly OHLC only (no monthly). sham/11: structure + candle close. Romeo: close/wick rule, weekly first (romeo/17), paired with a key level and market profile (romeo/16).
- v0.1 default: Sham mode = sham/11 matrix (fully computable) + optional weekly/monthly OHLC filter; Romeo mode = weekly close/wick bias (romeo/17) + daily close/wick on the traded daily candle.
- Decide by: **backtest** (`P:bias_inputs`).

**C-14. Rebalance the dealing range first vs exceptions.**
- Options: sham/03, sham/08: price must first rebalance the range (EQ/premium). sham/01, sham/06: KOD-S exception near the DOL. sham/08: at all-time highs with no range, a sweep of a nearby low is enough.
- v0.1 default: rebalance required, with both exceptions (CRT-R16).
- Decide by: **backtest** (`P:rebalance_required`, `P:kod_s_dist`).

**C-15. Which forex macros count.**
- Options: spoken list 03:00, 09:00, 11:00 (sham/04 4:34–5:06); the 06:00 "London lunch" macro is used in two traded examples (sham/04 15:15; sham/06 15:18) though it lies after the London killzone (02:00–05:00).
- v0.1 default: macros `[03, 06, 09, 11]`; killzones as the hard filter (`key_time_strictness = killzone_or_macro`).
- Decide by: **backtest**.

**C-16. A purge outside key time: invalidate or re-select.**
- Options: sham/06: invalidates the candle range and the trade idea. sham/04: a new 4H candle (05:00) can be re-selected afterwards.
- Reading: compatible: the candle is invalid, a later candle may become a new CRT.
- v0.1 default: invalidate that candle; allow re-selection of the next 4H candle the same day (CRT-R28).
- Decide by: **backtest** (`P:allow_reselect`).

**C-17. "Expecting the OTE 50% to hit is a requirement" (romeo/10 19:30).**
- Options: literal requirement vs a slip for "mistake" (the rest of the episode argues price often does not reach 50%).
- v0.1 default: not required (slip).
- Decide by: **user** (confirm), low impact.

**C-18. Speed of C3.**
- Options: C3 "usually the fastest" (romeo/02 28:17, 41:03; romeo/10 3:17) vs a slow grind with consolidations to the target (romeo/04 4:28–5:18, 12:10).
- v0.1 default: no speed filter. Log `bars_to_tp1`, `bars_to_tp2`.
- Decide by: **backtest** (descriptive).

**C-19. Romeo's scepticism of OBs/FVGs vs Sham's OB-centred model.**
- Options: Romeo: model #1 "is not supply and demand" (romeo/02 39:06); fake order blocks / fake PD arrays (romeo/05 11:48; romeo/09 10:56); FVG is context, not cause (romeo/17 26:17). Yet he lists the OB as "entry 2" (romeo/02 39:38) and uses FVG confluence (romeo/03, romeo/05) and an FVG-fill stop (romeo/17). Sham builds everything on OBs.
- v0.1 default: Romeo mode does not use OBs as entries; Sham mode does. Hybrid mode: Romeo structure + Sham timing + either entry.
- Decide by: **backtest** (`P:strategy_mode`).

**C-20. Stop placement.**
- Options: model candle extreme (romeo/03); TS / KoD extreme (romeo/05, 09, 12); daily-FVG-fill low (romeo/17); beyond the OB (Sham). OTE stop not stated (romeo/18).
- v0.1 default: by entry type (CRT-R49 to R52); OTE stop = leg origin (PROPOSED).
- Decide by: **backtest** (`P:stop_mode`, `P:ote_stop`).

**C-21. Fixed 3R vs "1 to 3R".**
- Options: 3R (sham/01, 02, 05, 08) vs 1–3R (sham/06 11:32, 16:52); 2R Friday (sham/04).
- v0.1 default: 3R; 2R Friday.
- Decide by: **backtest** (`P:r_target = 1 | 2 | 3`).

**C-22. Counter-HTF trades.**
- Options: Romeo forbids LTF CRTs against the HTF CRT (romeo/11 failure case 3) and against a pending DOL (romeo/04). Sham sets bias per day and allows days against the HTF structure while a dealing range rebalances (sham/03, sham/08 5:46–6:16), and a counter-trend trade to EQ with a strong SMT (sham/06 13:07).
- Reading: they agree if Sham's "rebalance" leg is itself the active HTF draw (the short-term DOL). They disagree when HTF structure and short-term DOL point opposite ways.
- v0.1 default: Romeo rule in Romeo mode; Sham rule in Sham mode; `allow_counter_htf = false` in hybrid.
- Decide by: **backtest**.

**C-23. SMT confirmation: model #1 *or* MSS, or both in order.**
- Options: romeo/11: model #1 or true MSS. romeo/09: two confirmations, model #1 then MSS. Sham: SMT can stand in for a full sweep at a key time (sham/04 10:44) and an SMT purge counts as the OB liquidity function (sham/02 8:42).
- v0.1 default: see C-08 (first entry on model #1 or MSS; add on MSS).
- Decide by: **backtest**.

**C-24. Is SMT required?**
- Options: Romeo: SMT is the only thing that stops a target (romeo/04) and a confluence on most shown trades (romeo/08, 12, 17), but no rule says every trade needs one. Sham: probability factor and bias input, not required.
- v0.1 default: not required for entry; used for invalidation (CRT-R57) and scoring (CRT-R46). Requires a second symbol's data (`P:smt_pairs`).
- Decide by: **backtest** (`P:require_smt`).

**C-25. Bias CRT target: opposite extreme vs dealing-range EQ.**
- Options: sham/05 26:27: keep bias toward the opposite end (CRT low). sham/08 25:53, 29:22: opposite side or dealing-range EQ/premium.
- v0.1 default: opposite extreme.
- Decide by: **backtest** (`P:bias_crt_target`).

---

## 6. Discretionary gaps

Things the sources leave to judgement. Each has a **PROPOSED (not from source)** measurable proxy, so the backtest can run now and the proxy can be replaced when a better source appears.

| ID | Gap | Where | PROPOSED proxy (not from source) | Params |
|---|---|---|---|---|
| G-01 | **How to choose the correct key level.** Romeo says this was not taught publicly and is "very important". | romeo/13 9:16–9:48; romeo/10; romeo/08 | Score every candidate from CRT-R19 within `kl_max_dist_atr × ATR(htf)` of C1: +1 unswept, +1 on a TF ≥ CRT-R22's TF, +1 confluence with another candidate within 0.1 ATR, +1 correct premium/discount half, +1 "most visible" (largest prominence, G-17). Use the highest-scoring level; log all. | `kl_types`, `kl_max_dist_atr: 1.5`, `kl_select: score|nearest` |
| G-02 | **Old high / old low, swing strength.** | romeo/01; romeo/03 | Fractal swing with N bars each side on the TF in question, unswept. | `swing_n: 2` (test 2, 3, 5) |
| G-03 | **Romeo's "six possibilities" of weekly candle anatomy.** Only examples named (pin bar, full bullish/bearish, down-then-up, up-then-down). | romeo/16 7:25 | Classifier on weekly OHLC + time of H/L: `bull_full` (body ≥ 60%, close > open), `bear_full`, `bull_pin` (lower wick ≥ 60%), `bear_pin` (upper wick ≥ 60%), `down_then_up` (low before high, else neither full nor pin), `up_then_down`. Replace when the list is published. | `shape_body_full: 0.6`, `shape_wick_pin: 0.6` |
| G-04 | **Market profile** (Romeo: sequence of swept vs broken highs/lows; Sham: expansion / retracement / consolidation / manipulation). | romeo/12 8:46; romeo/16 23:33; romeo/14 12:03; sham/01 2:09 | Romeo: on the LTF swing list, `bear_profile` if the last k swing highs were swept-and-closed-back (TS) and the last k swing lows were broken by closes; mirror for bull; else `none`. Sham: `expansion` if the last D candle closed beyond the prior range in the bias direction; `retracement` if it closed against; `consolidation` if inside; `manipulation` if CRT-R08 bias flips after a strong counter D1 + H4 CSD (sham/06 19:00). | `profile_k: 2` |
| G-05 | **Closing-hour logic of the 4H candle.** Sham: "one of the most important" timing elements, not explained. | sham/08 19:31; sham/06 10:43 | Log for every purge: minute offset inside its 4H candle, and whether the purge happened in the first or last hour of that candle. Test as a filter "purge in last hour" vs "first hour". | `closing_hour_filter: none|first|last` |
| G-06 | **Weekly / daily profiles** ("is the week in expansion or retracement; has the high/low of the week formed?"). | sham/08 11:05–12:23, 18:12; sham/04 19:34 | Weekly: `how_formed` = the current week's high is ≥ X ATR above the current price and was set Mon–Wed. Daily: "high of day first" if the day's high is before 05:00 NY. Build weekday-of-high/low statistics from history and use them as priors. | `profile_lookback_weeks: 104` |
| G-07 | **"Which candle makes the most sense" as the 4H CRT.** | sham/05; sham/06 9:25; sham/11 12:45 | First closed 4H candle with open in {21:00, 01:00, 05:00} that closes inside the key-level zone, in the correct half, after the range is rebalanced (CRT-R28). | `framing_candle_opens` |
| G-08 | **"Thick" candle.** | romeo/02, 03, 09, 10 | DEF-09: body/range ≥ 0.6 and range ≥ 1.0 × ATR(14). Variant: body ≥ 1.5 × median body of last 20. | `thick_body_ratio`, `thick_atr_mult` |
| G-09 | **Dealing range = "most recent expansion swing".** | sham/01 7:00; sham/03 14:19; sham/08 23:31 | Last pair of opposite fractal swings whose leg length ≥ `dr_min_atr × ATR(tf)` and which contains at least one FVG ("displacement"). Re-anchor when a new swing beyond it is confirmed. | `dr_min_atr: 2.0` |
| G-10 | **"Unfilled liquidity" in a dealing range.** | sham/03 14:19; sham/01 | At least one FVG or OB inside the swing not touched by any later wick. | `fvg_fill` |
| G-11 | **Killzone vs macro strictness; macro length.** | sham/04 | Killzone = hard filter; macro = bonus; macro = `[HH:00, HH:59]`. Variant: ICT-style `[HH-10min, HH+10min]`. | `macro_window`, `key_time_strictness` |
| G-12 | **Which candles form a multi-candle OB.** | sham/02 36:41 | Maximal run of consecutive opposite-colour candles ending at the bar before the engulf, that includes the purge bar. | `ob_max_candles: 4` |
| G-13 | **"Meaningful HTF high/low" for OB purges.** | sham/02 3:01 | Fractal swing on a TF ≥ one step above the OB TF, or a prior D/W candle high/low, or a CRT high/low. | `ob_liq_tf_steps: 1` |
| G-14 | **End of OTE leg one; "wave" of closes; "sharp" retrace.** | romeo/18 | Leg end = extreme after activation until the first close that retraces ≥ `leg_end_atr × ATR`. Log the number of closes through the level. | `leg_end_atr: 0.5` |
| G-15 | **Identifying KoD-R in real time.** Only clear afterwards. | romeo/04, 05, 10 | Inside an active CRT after TP1: any LTF sweep of the latest swing high (bear) that closes back below, with no new C2 high. Use as stop/invalidation anchor and optional re-entry only. | `kod_r_requires_tp1: true` |
| G-16 | **"Decisive" / "multiple" closes beyond the key high.** | romeo/04 16:04 | ≥ 2 LTF closes beyond, each with body/range ≥ 0.5. | `decisive_closes: 2` |
| G-17 | **"Most visible" old low** (pairing for the Lens). | romeo/17 17:50 | Fractal swing with the largest prominence (distance to the next swing beyond it) within the last 12 candles of that TF. | `visible_lookback: 12` |
| G-18 | **Consolidation / range on the LTF** (Monday chop; range then TS). | romeo/16, romeo/17 | ≥ 6 LTF bars whose total high-low ≤ 1.5 × ATR(ltf). | `range_min_bars: 6`, `range_max_atr: 1.5` |
| G-19 | **Rejection block** ("a turtle soup of the body"). | romeo/17 20:41 | Candle group whose wicks swept a prior body extreme while bodies held; zone = wick beyond bodies. Logged only. | – |
| G-20 | **"Overwhelmingly one-sided" confluence.** | romeo/12 9:30 | All of: HTF bias, market profile (G-04), key level present, entry model; SMT optional. | `min_confluence` |
| G-21 | **"Has the weekly/monthly candle already delivered?"** | sham/04 20:06 | CRT-R17 proxy (target PDA hit, or range ≥ 5 × ADR). | `delivered_adr_mult` |
| G-22 | **"Correct time" / "where time meets price" (Romeo).** | romeo/03 16:16; romeo/06 12:28; romeo/08 13:51 | Weekday filter (CRT-R35) + optional Sham killzones. Log hour-of-day of every Romeo sweep and trigger. | `romeo_use_killzones` |
| G-23 | **Manipulation at the end of the previous candle.** | romeo/09 7:31 | Sweep in the last 20% of the previous HTF candle's duration (CRT-R36). | `late_frac: 0.8` |
| G-24 | **"Not very convincing" turtle soup** (smaller target). | romeo/12 16:56 | Sweep depth < 0.25 × ATR(htf) → target = previous day high/low only. | `weak_ts_atr: 0.25` |
| G-25 | **"Clean" weekly range; fake vs real PD arrays; strength classes (very bullish … very bearish).** | romeo/02; romeo/05 11:48; romeo/17 4:04 | Not modelled in v0.1. Log weekly range / ATR(W). | – |
| G-26 | **Ranging day / when to stay neutral.** | sham/03 31:22; sham/11 | CRT-R13 proxy: previous day range < 0.5 × ADR(20), or a bias-table conflict. | `ranging_adr_frac` |

---

## 7. Parameters for the backtester

Every knob in one place. `default` is the v0.1 value; `alt` are values to test. Values marked `# PROPOSED` are not from any source.

```yaml
rulebook_version: "0.1"

general:
  strategy_mode: romeo            # alt: sham, hybrid           (C-19)
  timezone: America/New_York
  atr_len: 14                     # PROPOSED
  swing_n: 2                      # PROPOSED; alt: 3, 5        (G-02)
  sweep_min_ticks: 1              # PROPOSED
  ts_close_back_bars: 1           # PROPOSED; alt: 2, 3        (DEF-06)

candles:
  daily_open: "00:00"             # alt: "17:00"               (C-03)
  h4_grid_first_open: "01:00"     # alt: "00:00"               (C-03)
  week_open: mon_0000             # alt: sun_1700              (C-02)  open PRICE reference
  week_range_from: sun_1700       # alt: mon_0000              (C-02)  which bars count for weekly H/L
  week_close: fri_1700            # alt: fri_1600              (C-02)
  max_inside_bars: 3              # PROPOSED                   (CRT-R26)

timeframes:
  htf_allowed: [4H, D, W]         # alt: [D, W], [4H], [W, M]   (C-10)
  tf_pairs: {M: D, W: 4H, D: 1H, 4H: 15m}     # alt: {M: 4H, W: 1H, D: 15m, 4H: 5m}  (C-01)
  kl_tf_for_htf: {W: M, D: W, 4H: D, 1H: 4H}  # (CRT-R22)
  sham_stack: {bias: D, framing: 4H, entry: 15m}

bias:
  bias_inputs: [close_wick]       # romeo default; sham: [structure, close_wick]; alt add: [weekly_ohlc, monthly_ohlc, smt]  (C-13)
  structure_break: close          # alt: wick
  bias_crt_days: [Mon, Tue, Wed]  # (CRT-R10)
  bias_crt_target: opposite_extreme   # alt: dr_eq            (C-25)
  allow_counter_htf: false        # (CRT-R05, C-22)
  allow_delivered_counter: false  # (CRT-R17)
  delivered_adr_mult: 5           # PROPOSED
  ranging_adr_frac: 0.5           # PROPOSED                  (CRT-R13)
  near_target_atr: 0.5            # PROPOSED                  (CRT-R11)
  use_weekly_time_theory: true    # (CRT-R14)
  romeo_sweep_days: [Mon, Tue, Wed]   # alt: all              (CRT-R35)

dealing_range:
  dr_min_atr: 2.0                 # PROPOSED                  (G-09)
  rebalance_required: true        # alt: false                (C-14)
  rebalance_level: eq             # alt: premium_fvg
  kod_s_dist: 0.25                # PROPOSED fraction of DR height  (CRT-R16)
  fvg_fill: touch                 # PROPOSED; alt: half, full (DEF-17)

key_level:
  kl_types: [swing, prev_period_hl, candle_open, weekly_wick_50, fvg, ob]   # (CRT-R19)
  kl_select: score                # PROPOSED; alt: nearest    (G-01)
  kl_max_dist_atr: 1.5            # PROPOSED
  kl_touch_tol: 0.0               # PROPOSED, in ATR(ltf)     (CRT-R20)
  visible_lookback: 12            # PROPOSED                  (G-17)

crt:
  require_close_inside: {W: true, D: true, 4H: true}   # sham mode: {W: true, D: true, 4H: false}  (C-04)
  allow_c2_entry: false           # (C-09)
  framing_candle_opens: ["21:00", "01:00", "05:00"]    # PROPOSED from Sham examples  (CRT-R28)
  allow_reselect: true            # (C-16)
  late_frac: 0.8                  # PROPOSED                  (CRT-R36)

timing:
  killzones:                      # sham/04
    london_open: ["02:00", "05:00"]
    new_york:    ["07:00", "10:00"]
    london_close: ["10:00", "12:00"]
  index_killzones:
    ny_am: ["08:30", "11:00"]
    ny_lunch: ["12:00", "13:00"]
    ny_pm: ["13:30", "16:00"]
  macros: ["03:00", "06:00", "09:00", "11:00"]   # alt: without 06:00   (C-15)
  macro_window: hour              # PROPOSED; alt: pm10min    (G-11)
  key_time_strictness: killzone_or_macro   # alt: macro_only
  asia_block: ["20:00", "02:00"]  # sham mode (CRT-R34)
  asia_block_romeo: false
  romeo_use_killzones: false      # PROPOSED                  (G-22)
  closing_hour_filter: none       # PROPOSED; alt: first, last  (G-05)

entry:
  romeo_entry_set: [model1, mss]  # alt: [model1], [mss], [model1, mss, ote, kod_r]   (C-08)
  require_thick: true
  thick_body_ratio: 0.6           # PROPOSED                  (G-08)
  thick_atr_mult: 1.0             # PROPOSED
  model1_trigger_ref: wick        # alt: body                 (C-07)
  model1_entry: close             # alt: model_high
  mss_entry_zone: ote             # alt: full_retrace         (CRT-R40)
  ote_zone: [0.50, 0.79]          # alt: [0.62, 0.79], [0.382, 0.79]  (C-06)
  ote_fib_basis: wick             # alt: body, union, intersection
  ote_trigger: touch              # alt: ltf_ts
  leg_end_atr: 0.5                # PROPOSED                  (G-14)
  smt_confirm: model1_or_mss      # alt: model1_then_mss      (C-23)
  require_smt: false              # (C-24)
  smt_take: wick                  # alt: close
  smt_pairs: {EURUSD: [DXY_inv, GBPUSD], GBPUSD: [EURUSD, DXY_inv], USDCAD: [DXY], NQ: [ES, YM], ES: [NQ], BTCUSD: [ETHUSD], XAUUSD: [XAGUSD]}
  ob_entry_edge: near_edge        # alt: open, mid            (C-12)
  ob_max_candles: 4               # PROPOSED                  (G-12)
  ob_liq_tf_steps: 1              # PROPOSED                  (G-13)
  min_confluence: 0               # PROPOSED; log only        (CRT-R46)
  max_entries_per_setup: 1        # alt: 2                    (CRT-R48)
  setup_expiry: c3_close          # sham mode: killzone_end   (CRT-R37)

stop:
  stop_mode: by_entry_type        # alt: fvg_fill_low          (C-20)
  ote_stop: leg_origin            # PROPOSED; alt: fib_079
  stop_buffer_ticks: 0            # PROPOSED

targets:
  target_mode: crt_levels         # alt: to_50_only, swings_one_by_one, ote_body, last_high_before_dump, r_multiple  (C-05)
  tp1_fraction: 0.5               # PROPOSED share closed at the 50%
  r_target: 3.0                   # sham mode; alt: 1, 2      (C-21)
  friday_r_target: 2.0            # (CRT-R67)
  time_exit: end_of_htf_candle    # PROPOSED; alt: none, end_of_killzone  (CRT-R56)
  be_after_tp1: false             # alt: true                 (CRT-R68)
  weak_ts_atr: 0.25               # PROPOSED                  (G-24)

invalidation:
  on_opposing_smt: close          # alt: breakeven, ignore    (CRT-R57)
  decisive_closes: 2              # PROPOSED                  (CRT-R58)
  on_first_close_beyond: warn     # alt: breakeven
  sham_invalid_atr: 1.0           # PROPOSED                  (CRT-R60)

risk:
  risk_per_trade: 0.005           # PROPOSED (0.5% of equity) (CRT-R62)
  daily_loss_limit_r: 1.0         # PROPOSED                  (CRT-R63)
  max_open_risk: 0.01             # PROPOSED
  max_trades_per_day: 1           # (CRT-R64)
  max_trades_per_week: 2
  news_events: [FOMC]             # alt: [FOMC, NFP, CPI]  (only FOMC is sourced)  (CRT-R66)
  news_block: whole_day           # PROPOSED
  friday_flat_time: "16:00"       # PROPOSED from romeo/17   (CRT-R67)
  no_weekend_holds: true

logging:
  log_weekly_stats: true          # (CRT-R70)
  log_fields: [how_time, low_time, week_shape, kl_at_high, kl_at_low, purge_minute_in_h4, kod_pos_pct, closes_through_count, bars_to_tp1, bars_to_tp2, confluence_score, invalid_reason]
```

---

## 8. Open questions for the user / Romeo's book

**Data and time conventions**
1. Which weekly candle does Romeo use for the weekly CRT range: Sunday 17:00 or Monday 00:00 open; Friday 16:00 or 17:00 close (C-02)? Does the book say?
2. Daily candle: midnight NY (Romeo) or 17:00 NY broker day? Which chart settings does Sham use for D1 and 4H (C-03)? Which broker/data feed will the bot trade on?
3. Monthly candle open time (not in any source).

**CRT structure (book)**
4. How is the correct key level chosen ("types of key levels", "types of reactions", marking), promised but not taught (romeo/08, romeo/13)? This is the largest gap (G-01).
5. The exact "six possibilities" of weekly candle anatomy (romeo/16) and the "strength classes" (romeo/17).
6. Romeo's definition of "market profile" and how it gates the close/wick bias (romeo/16 23:33).
7. Is the CRT 50% measured on C1's full wick range or on bodies?
8. Must C2 close back inside by its own close, or can the close back inside come later after inside bars (romeo/02 open question)?
9. Model #1: trigger on the model candle's wick high or body (C-07)? Must the model candle itself close back inside the level?
10. Which LTF is used for the C3 turtle-soup entry on a daily CRT (romeo/10)? Which TF pairs apply to the CRTology OTE (romeo/18)?
11. Where is the stop on an OTE entry (romeo/18)? What are the "narrower stops" not taught publicly (romeo/03)?
12. Is KoD-R "lower 25% of the range" measured from the target side (romeo/05)?
13. What is Romeo's intraday "time": which hours does he use to time the high/low of the day? Is "9:30" in romeo/14 New York time?
14. What is a "clean close" (romeo/13 title, not defined)?
15. What does the "SS" bullish/bearish week template look like for an inside week (romeo/16 25:22)?

**Sham details**
16. What is "closing hour logic" of the 4H candle (sham/08 19:31)?
17. The slide with OB timeframe combinations (sham/02 33:30) is not read aloud. Can the user capture it from the video frames?
18. Is a counter-trend trade (sham/06 Tuesday) part of his core model? Does a neutral daily bias forbid all trades or only counter-bias trades (sham/11)?
19. Must the 4H framing CRT match the D1 bias-CRT direction, or only the D1 dealing-range context (sham/08)?
20. Which correlated asset is required for SMT on GBPUSD: EURUSD, DXY or both (sham/01)?

**User decisions**
21. Which mode should be built first: Romeo, Sham or hybrid? (Proposed: Romeo mode for structure, then add Sham timing as a filter.)
22. Instruments to trade and test (the examples cover EURUSD, GBPUSD, USDCAD, DXY, XAUUSD, BTC/ETH, NQ). SMT needs a second symbol's data for each.
23. Risk numbers: risk per trade, daily loss limit, max open risk, max trades per day/week (CRT-R62 to R64; no source gives values).
24. Which news events besides FOMC should block trading, and for how long?
25. Is entry inside C2 ever allowed (C-09)? Which HTFs (4H only, D, W) match your holding-time preference (C-10)?
26. Can we get Sham's posted live trades (Twitter) and Romeo's live calls (X) with dates, to use as labelled test cases?
