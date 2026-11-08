# Research — ICT & CRT study library

This folder is where we study the strategy before writing any trading code.
The goal is not to "watch everything". It is to turn **Candle Range Theory
(CRT)** into a written, testable rulebook (`notes/CRT_RULEBOOK.md`, built in
Phase 1 of the project plan) that the robot can follow.

## Study order

| Phase | What | Videos | Hours |
|---|---|---|---|
| 1a | ICT foundation: 2022 Mentorship, Market Maker Primer, OTE, Micro-structure, Precision, Market Maker series, Core Content M11–12, Scalping | 108 | ~50 |
| 2 | **CRT core**: Romeo (the creator of CRT): turtle soup → What is CRT → CRT secrets ep.1–10 → live sessions → CRTology 2026 | 18 | ~7 |
| 2 | **CRT core**: Sham: CRT selection, daily bias, entry timing, order blocks | 12 | ~5 |
| 3 | Community CRT channels: compare against Romeo, flag where they disagree | 76 | ~17 |
| 1b | ICT 2023 + 2024 Mentorships: reference only, looked up by topic | 156 | ~200 |

Total catalogued: **371 videos, ~279 hours.** The 2023 and 2024 mentorships
alone are about 200 hours, so we search them by topic rather than watching them in full.

Romeo and Sham count as the **source of truth for CRT**. ICT counts as the source
of truth for the underlying concepts (liquidity, FVG, order blocks, killzones,
OTE, SMT). Community content can only *add* detail. When it contradicts Romeo,
we log the conflict in the notes. It never overrides him.

## Folder layout

```
research/
├── sources/
│   ├── catalog.yaml        # every source: phase, order, url, status
│   └── lists/<id>.tsv      # generated: one row per video
├── scripts/
│   ├── build_catalog.py    # catalog.yaml -> lists/*.tsv (works anywhere)
│   └── fetch_transcripts.py# lists -> raw/transcripts (run on your own PC)
├── raw/                    # GIT-IGNORED: transcripts, screenshots, your PDFs
├── notes/
│   ├── _TEMPLATE.md        # format for every video note
│   ├── ict/                # one note per ICT video / concept
│   ├── crt/romeo/          # one note per Romeo video
│   ├── crt/sham/           # one note per Sham video
│   └── community/          # other creators + conflicts with Romeo
├── x-traders/              # watchlist + plan for following traders on X
└── PROGRESS.md             # checklist of what's been studied
```

## How the pipeline works

1. **Catalog**: add a source to `catalog.yaml`, then run
   `python research/scripts/build_catalog.py`.
2. **Transcripts**: YouTube blocks transcript downloads from cloud servers.
   You have two ways to get them:
   - On your PC (free): `python research/scripts/fetch_transcripts.py crt-romeo --browser chrome`
     (you need to be logged in to YouTube in that browser).
   - In Claude sessions: Claude pulls transcripts through the vidIQ connector
     (costs vidIQ credits).
3. **Notes**: Claude reads each transcript and writes a note in our own words
   (`notes/_TEMPLATE.md`). Each note lists rules, definitions, timestamps
   for chart examples, and open questions.
4. **Rulebook**: notes are combined into `notes/CRT_RULEBOOK.md`. Every rule
   in the rulebook has an ID (e.g. `CRT-R07`), cites the videos it came from,
   and later gets a unit test and a backtest.

Transcripts, purchased courses and PDFs stay in `raw/` and are never
committed, because they are the creators' copyrighted material. Only our own
notes go into git.

## Setup

```bash
pip install yt-dlp pyyaml
python research/scripts/build_catalog.py
```
