"""CLI: ``python -m crt_robot.data download|quality``."""

from __future__ import annotations

import argparse
import sys
from datetime import date

from crt_robot.data import dukascopy
from crt_robot.data.instruments import INSTRUMENTS


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m crt_robot.data")
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("download", help="download Dukascopy 1m bid/ask history")
    d.add_argument("--symbols", nargs="+", default=list(INSTRUMENTS))
    d.add_argument("--start", default="2015-01-01")
    d.add_argument("--end", default=date.today().isoformat())
    q = sub.add_parser("quality", help="write a data quality report")
    q.add_argument("--symbols", nargs="+", default=list(INSTRUMENTS))
    q.add_argument("--out", default="docs/DATA_QUALITY.md")
    args = p.parse_args(argv)

    if args.cmd == "download":
        for sym in args.symbols:
            try:
                res = dukascopy.download(sym, date.fromisoformat(args.start), date.fromisoformat(args.end))
            except dukascopy.DataHostBlocked as exc:
                print(f"BLOCKED: {exc}. No data was invented; stopping.", file=sys.stderr)
                return 2
            print(res)
        return 0

    from crt_robot.data.quality import quality_report_markdown, run_checks

    sections = []
    for sym in args.symbols:
        try:
            df = dukascopy.load(sym)
        except FileNotFoundError as exc:
            sections.append(f"## {sym}\n\nNo data: {exc}\n")
            continue
        sections.append(quality_report_markdown(sym, run_checks(df)))
    with open(args.out, "w") as fh:
        fh.write("# Data quality report\n\n" + "\n".join(sections))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
