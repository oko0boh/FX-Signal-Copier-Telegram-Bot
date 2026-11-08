---
source_id: book-crt-keylevels
title: "Keylevel's — Candle Range Theory Complete Guide"
author: AR (community author; not Romeo)
pages: 12 (diagrams only, no text body)
studied_on: 2026-11-08
---

## Summary
This is a short diagram-only guide. It says CRT uses exactly **five key levels**.
It draws each level on its own, then shows a CRT forming at each one. The key
point of the diagrams is that **candle 2's sweep lands at or inside the key
level**. The guide gives no rules on how to choose between levels, which timeframe
to use, or when a level counts as used up.
It is a secondary source.

## The five key levels (p.3)

| Code | Name | Diagram meaning (p.5–9) | Rulebook mapping |
|---|---|---|---|
| OHP | Old High Purged | An old swing high whose wick is later traded through (purged). | DEF key level / CRT-R19 "old high"; ICT buy-side liquidity |
| OLP | Old Low Purged | Mirror: an old swing low traded through. | Old low; ICT sell-side liquidity |
| FVG | Fair Value Gap | Classic 3-candle gap: the gap between candle 1's low and candle 3's high in a bearish leg (drawn bearish). | DEF FVG |
| OB | Orderblock | The up-close candle(s) right before a bearish displacement candle. The zone covers those candles' full range (drawn bearish). | DEF OB (Sham's definition is compatible) |
| RB | Rejection Block | A candle with a long wick. The zone is the **wick part beyond the bodies**, drawn from the body edge to the wick extreme (bullish example: below a down candle's body down to its low). | G-19, ICT rejection block |

## How a CRT uses each level (p.11)
All four examples are 3-candle CRTs (C1 range, C2 sweep, C3 expansion), with CRT high and CRT low marked:

- **RB (bullish):** C2's low wicks below the CRT low **into the rejection block zone**. C3 closes up.
- **OLP (bullish):** C2's wick sweeps below the CRT low **and below the old low** (purges it). C3 expands up.
- **OHP (bearish):** C2's wick sweeps above the CRT high **and above the old high**. C3 is a bearish candle.
- **FVG (bearish):** C2's wick sweeps above the CRT high **into a bearish FVG** above. C3 is bearish.

### Rule this supports
> **The CRT's manipulation candle (C2) must sweep the CRT extreme and reach a key level: purge the old high/low, or trade into the FVG / OB / RB zone.**

This matches Romeo (romeo/10 ep.7: C2 sweeps the key level, and a CRT with no key level is invalid) and the community rule found online that a CRT is high probability when the manipulation happens inside the key level.

## Adds to the rulebook
- **G-01 key level, candidate set:** restrict key-level types to these five, `kl_types: [old_high, old_low, fvg, ob, rb]`, as the **v0.1 default**. Breakers, mitigation blocks and opening prices (ICT-K list in 6.1) become optional extras for the backtest.
- **Key-level touch condition:** for OHP/OLP, `C2.high > old_high` (bearish) or `C2.low < old_low` (bullish). For a zone (FVG/OB/RB), C2's wick must enter the zone: `C2.high >= zone.low` (bearish) or `C2.low <= zone.high` (bullish).
- **G-19 rejection block:** confirms the ICT definition. The zone is the wick beyond the bodies.

## Not answered
- Which timeframe the key level must be on. Use CRT-R22 (key level one TF above the CRT).
- How to choose when several levels qualify (G-01 scoring still applies).
- Whether a level is valid after it has been touched once.
- Whether the FVG/OB must be unmitigated.

## Chart examples to label
Schematic only (no instrument or date). p.11 gives four idealised shapes, which are good as **synthetic unit-test fixtures** for the CRT detector.
