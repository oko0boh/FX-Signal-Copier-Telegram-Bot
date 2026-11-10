"""CLI for CRT strategy runs on the TUNING period only.

    python -m crt_robot.run backtest --mode romeo --symbol EURUSD --start 2018-01-01 --end 2024-12-31
    python -m crt_robot.run setups --modes romeo sham hybrid --symbols EURUSD GBPUSD XAUUSD \
        --start 2018-01-01 --end 2025-04-30
    python -m crt_robot.run report --inputs runs/backtests/*/setups.csv --out reports/setups

Data comes from the Phase 1 cache (``data_cache/dukascopy/...``, or
``--data-root`` / ``CRT_DATA_CACHE``). Nothing is downloaded or invented
here. The locked holdout (``config/data_split.toml``) is refused: ``--end``
must be before ``holdout_start``. Every backtest is appended to the runs log
with the mode, the config fingerprint and the overrides.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import pandas as pd

from crt_robot.config import REPO_ROOT

DEFAULT_OUT = REPO_ROOT / "runs" / "backtests"


def _data_root(arg: str | None) -> Path:
    return Path(arg or os.environ.get("CRT_DATA_CACHE", REPO_ROOT / "data_cache"))


def _load(symbol: str, start: pd.Timestamp, end: pd.Timestamp, root: Path) -> pd.DataFrame:
    from crt_robot.data import dukascopy
    return dukascopy.load(symbol, start=str(start.date()), end=str(end.date()), root=root)


def _to_base(df: pd.DataFrame, base: str) -> tuple[pd.DataFrame, pd.Timedelta]:
    if base == "1m":
        return df, pd.Timedelta(minutes=1)
    from crt_robot.data.resample import resample
    out = resample(df, base)
    out = out[[c for c in out.columns if c not in ("close_time", "complete", "n_bars")]]
    return out, pd.Timedelta(base.replace("m", "min"))


def run_backtest(mode: str, symbol: str, start: str, end: str, overrides: list[str] | None = None,
                 base: str = "1m", warmup_days: int = 120, data_root: str | None = None, peers: bool = True,
                 out_dir: Path | None = None, log: bool = True, frames: dict | None = None, quiet: bool = False):
    """Run one mode on one symbol. ``frames`` = {symbol: 1m DataFrame} may be
    passed instead of reading the cache (tests)."""
    from crt_robot.backtest.engine import Backtester, EngineConfig
    from crt_robot.backtest.metrics import summarize
    from crt_robot.backtest.splits import DataSplit, HoldoutLockedError
    from crt_robot.crt.config import load_config
    from crt_robot.crt.report import write_report
    from crt_robot.crt.smt import PeerFeed
    from crt_robot.crt.strategy import CRTStrategy, view_timeframes
    from crt_robot.data.instruments import get_instrument
    from crt_robot.data.mtf import MultiTimeframeView

    split = DataSplit.load()
    t0, t1 = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
    if t1 > split.holdout_start:
        raise HoldoutLockedError(f"--end {end} reaches the locked holdout (starts {split.holdout_start.date()}); "
                                 "Phase 2 runs use the tuning period only")
    if t0 < split.data_start:
        raise ValueError(f"--start is before data_start {split.data_start.date()}")
    cfg = load_config(mode, overrides or [])
    inst = get_instrument(symbol)
    load_from = max(split.data_start, t0 - pd.Timedelta(days=warmup_days))
    root = _data_root(data_root)

    def get(sym: str) -> pd.DataFrame:
        if frames is not None:
            df = frames[sym]
            return df[(df.index >= load_from) & (df.index < t1)]
        return _load(sym, load_from, t1, root)

    raw = get(symbol)
    if raw.empty:
        raise FileNotFoundError(f"no {symbol} data between {load_from.date()} and {t1.date()}")
    base_df, base_len = _to_base(raw, base)
    tfs = view_timeframes(cfg, base)
    feeds = []
    if peers:
        for name in cfg.entry.smt_pairs.get(symbol, []):
            inverse = name.endswith("_inv")
            sym = name.removesuffix("_inv")
            try:
                pdf = get(sym)
            except (FileNotFoundError, KeyError) as exc:
                if not quiet:
                    print(f"note: SMT peer {sym} skipped ({exc})", file=sys.stderr)
                continue
            if pdf.empty:
                continue
            pbase, _ = _to_base(pdf, base)
            feeds.append(PeerFeed(sym, MultiTimeframeView(pbase, list(tfs), base_len), inverse))
    strat = CRTStrategy(cfg, symbol, peers=feeds, trade_from=t0)
    ecfg = EngineConfig(risk_frac=cfg.risk.risk_per_trade,
                        daily_limit=cfg.risk.daily_loss_limit_r * cfg.risk.risk_per_trade,
                        max_trades_per_day=cfg.risk.max_trades_per_day)
    bt = Backtester(base_df, inst, tfs, base_len=base_len, config=ecfg, split=split)
    params = {"mode": mode, "rulebook_version": cfg.rulebook_version, "config_fingerprint": cfg.fingerprint(),
              "overrides": list(overrides or []), "base": base, "trade_from": str(t0.date()),
              "peers": [f.name + ("_inv" if f.inverse else "") for f in feeds]}
    res = bt.run(strat, params=params, log=log)
    setups = strat.setups_frame()
    summary = summarize(res)
    out = Path(out_dir) if out_dir else DEFAULT_OUT / (res.run_id or f"{mode}_{symbol}")
    out.mkdir(parents=True, exist_ok=True)
    res.trades.to_csv(out / "trades.csv", index=False)
    meta = {"mode": mode, "symbol": symbol, "period": f"{t0.date()} .. {t1.date()} (tuning)", "base": base,
            "config_fingerprint": cfg.fingerprint(), "overrides": " ".join(overrides or []) or "none",
            "SMT peers": ", ".join(params["peers"]) or "none", "run_id": res.run_id or "not logged"}
    write_report(setups, out, f"CRT setups: {mode} {symbol}", meta)
    (out / "summary.json").write_text(json.dumps({"params": params, "summary": summary}, indent=2, default=str))
    return res, strat, out, summary


def run_setups(modes, symbols, start, end, overrides=None, base="1m", data_root=None, out="reports/setups",
               peers=True, frames=None, log=True):
    from crt_robot.crt.report import write_report
    frames_all = []
    for m in modes:
        for s in symbols:
            _, strat, d, _ = run_backtest(m, s, start, end, overrides, base, data_root=data_root, peers=peers,
                                          out_dir=Path(out) / f"{m}_{s}", frames=frames, log=log, quiet=False)
            frames_all.append(strat.setups_frame())
            print(f"{m} {s}: {len(strat.setups)} setups -> {d}")
    allx = pd.concat(frames_all, ignore_index=True) if frames_all else pd.DataFrame()
    meta = {"modes": " ".join(modes), "symbols": " ".join(symbols), "period": f"{start} .. {end} (tuning)",
            "overrides": " ".join(overrides or []) or "none"}
    return write_report(allx, Path(out), "CRT setups report (all modes and symbols)", meta)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m crt_robot.run")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--start", required=True, help="first trading day (UTC date), tuning period")
        sp.add_argument("--end", required=True, help="end (exclusive, UTC date); must be before the holdout")
        sp.add_argument("--set", dest="overrides", action="append", default=[],
                        help="override a parameter, e.g. --set entry.ote_zone=[0.62,0.79] (repeatable)")
        sp.add_argument("--base", default="1m", choices=["1m", "5m", "15m"],
                        help="engine base bars (1m = most exact fills; 15m = faster)")
        sp.add_argument("--data-root", default=None, help="data cache root (default data_cache/ or $CRT_DATA_CACHE)")
        sp.add_argument("--no-peers", action="store_true", help="skip SMT peers")
        sp.add_argument("--no-log", action="store_true", help="do not append to the runs log")

    b = sub.add_parser("backtest", help="one mode on one symbol (tuning period)")
    b.add_argument("--mode", required=True, choices=["romeo", "sham", "hybrid"])
    b.add_argument("--symbol", required=True)
    b.add_argument("--warmup-days", type=int, default=120)
    b.add_argument("--out", default=None)
    common(b)
    s = sub.add_parser("setups", help="setups report over modes x symbols (CSV + summary markdown)")
    s.add_argument("--modes", nargs="+", default=["romeo", "sham", "hybrid"])
    s.add_argument("--symbols", nargs="+", default=["EURUSD", "GBPUSD", "XAUUSD"])
    s.add_argument("--out", default="reports/setups")
    common(s)
    r = sub.add_parser("report", help="rebuild a summary from existing setups CSVs")
    r.add_argument("--inputs", nargs="+", required=True)
    r.add_argument("--out", default="reports/setups")
    a = p.parse_args(argv)

    from crt_robot.backtest.splits import HoldoutLockedError
    try:
        if a.cmd == "backtest":
            res, strat, out, summary = run_backtest(a.mode, a.symbol, a.start, a.end, a.overrides, a.base,
                                                    a.warmup_days, a.data_root, not a.no_peers,
                                                    Path(a.out) if a.out else None, not a.no_log)
            states = pd.Series([x.state for x in strat.setups]).value_counts().to_dict()
            print(f"{a.mode} {a.symbol} {a.start}..{a.end}: {len(strat.setups)} setups {states}; "
                  f"{summary['n']} trades")
            print(json.dumps({k: summary[k] for k in ("n", "mean_r", "t_stat", "win_rate", "profit_factor",
                                                      "max_dd_pct", "daily_stop_days")}, default=str))
            print(f"wrote {out}")
        elif a.cmd == "setups":
            csv, md = run_setups(a.modes, a.symbols, a.start, a.end, a.overrides, a.base, a.data_root, a.out,
                                 not a.no_peers, log=not a.no_log)
            print(f"wrote {csv} and {md}")
        else:
            from crt_robot.crt.report import write_report
            df = pd.concat([pd.read_csv(f) for f in a.inputs], ignore_index=True)
            csv, md = write_report(df, Path(a.out), "CRT setups report", {"inputs": len(a.inputs)})
            print(f"wrote {csv} and {md}")
    except HoldoutLockedError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 3
    except FileNotFoundError as exc:
        print(f"NO DATA: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
