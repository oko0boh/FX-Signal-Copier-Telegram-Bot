# Tasks for the Mac session

The cloud sessions cannot download market data (Dukascopy blocks cloud IPs, see
`docs/PHASE1_REPORT.md`). These tasks need a home connection. Do them in order and
mark each one done at the bottom.

Rules for this machine:
- **Never commit or push** `data_cache/`, `runs/backtests/`, `reports/`, PDFs, or anything under `research/raw/`.
- Do not change code or rules. If something fails, report the exact error and stop.
- Do not invent or fill in data. If a download is refused, stop and report the `BLOCKED:` line.

## Task 1: set up and run the tests

```bash
cd FX-Signal-Copier-Telegram-Bot
git fetch origin && git checkout crt-robot-phase2 && git pull
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest -q          # expect 195 passed
```

## Task 2: download the price data (several hours, resumable)

```bash
python -m crt_robot.data download --symbols EURUSD GBPUSD XAUUSD XAGUSD DXY --start 2015-01-01
python -m crt_robot.data quality      # writes docs/DATA_QUALITY.md
```

- It pauses between requests and resumes where it stopped. If it prints `BLOCKED: ...`, stop and report that line.
- The dollar index symbol (`DXY`) is unverified. If only that symbol fails, continue with the others and report it.
- Show the contents of `docs/DATA_QUALITY.md` (gaps, duplicates, spikes, coverage per symbol and year).

## Task 3: setups report (counts only, no profit claims)

```bash
python -m crt_robot.run setups --start 2016-01-01 --end 2025-05-01 --base 15m --out reports/setups
```

- `--end 2025-05-01` is the latest allowed date. **Never run past it.** The last 18 months are a locked holdout.
- Report `reports/setups/setups_summary.md`: setups per mode, symbol, weekday and hour, and the rejection reasons table.
- Also check the look-ahead audit from section 9 of `docs/PHASE2_REPORT.md` (step 6) on real data and report the output.

## Task 4: copy back what the cloud sessions need

Commit only these two small files to branch `crt-robot-phase2` and push:
`docs/DATA_QUALITY.md` and `reports/setups/setups_summary.md` (use `git add -f` for the second, because `reports/` is git-ignored).

## Done log

- [ ] Task 1
- [ ] Task 2
- [ ] Task 3
- [ ] Task 4
