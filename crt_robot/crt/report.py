"""Setups report: CSV of every setup + a summary markdown with counts by
mode, symbol, weekday, hour, state and rejection reason (and the rule that
rejected it). It describes WHAT the detector saw and WHY setups were taken
or dropped; it reports no performance.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

WEEKDAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _md_table(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "_none_\n"
    df = df.copy()
    df.index = df.index.map(str)
    cols = [str(c) for c in df.columns]
    head = "| " + (df.index.name or "") + " | " + " | ".join(cols) + " |"
    sep = "|---" * (len(cols) + 1) + "|"
    rows = ["| " + str(i) + " | " + " | ".join(str(v) for v in r) + " |" for i, r in zip(df.index, df.to_numpy())]
    return "\n".join([head, sep, *rows]) + "\n"


def _first_fail(s: str) -> str:
    return s.split(";")[0] if isinstance(s, str) and s else ""


def summarize_setups(setups: pd.DataFrame, title: str = "CRT setups report", meta: dict | None = None) -> str:
    out = [f"# {title}\n"]
    if meta:
        out.append("\n".join(f"- **{k}**: {v}" for k, v in meta.items()) + "\n")
    if setups.empty:
        out.append("\nNo setups.\n")
        return "\n".join(out)
    s = setups.copy()
    s["taken"] = s["state"].isin(["entered", "done"])
    s["first_fail"] = s["failed_checks"].map(_first_fail)
    out.append("Counts only: what was detected, taken or rejected, and why. No performance figures.\n")
    out.append("\n## By mode and state\n")
    out.append(_md_table(pd.crosstab(s["mode"], s["state"], margins=True)))
    out.append("\n## By symbol and mode (setups / taken)\n")
    g = s.groupby(["symbol", "mode"]).agg(setups=("id", "size"), taken=("taken", "sum"))
    out.append(_md_table(g))
    out.append("\n## By CRT timeframe and mode (taken)\n")
    out.append(_md_table(pd.crosstab(s["htf"], s["mode"], values=s["taken"], aggfunc="sum").fillna(0).astype(int)))
    out.append("\n## Rejection / invalidation reasons by mode\n")
    rej = s[~s["taken"] & (s["invalid_reason"].fillna("") != "")]
    out.append(_md_table(pd.crosstab(rej["invalid_reason"], rej["mode"], margins=True)
                         .sort_values("All", ascending=False) if len(rej) else pd.DataFrame()))
    out.append("\n## First failed rule (rule:check) by mode\n")
    ff = rej[rej["first_fail"] != ""]
    out.append(_md_table(pd.crosstab(ff["first_fail"], ff["mode"], margins=True)
                         .sort_values("All", ascending=False).head(25) if len(ff) else pd.DataFrame()))
    with_sweep = s[s["sweep_weekday"].fillna("") != ""]
    out.append("\n## Sweep weekday (NY) by mode: all setups with a sweep / taken\n")
    if len(with_sweep):
        a = pd.crosstab(with_sweep["sweep_weekday"], with_sweep["mode"]).reindex(
            [d for d in WEEKDAY_ORDER if d in set(with_sweep["sweep_weekday"])])
        t = pd.crosstab(with_sweep["sweep_weekday"], with_sweep["mode"], values=with_sweep["taken"],
                        aggfunc="sum").reindex(a.index).fillna(0).astype(int)
        out.append(_md_table(a.astype(str) + " / " + t.astype(str)))
    else:
        out.append("_none_\n")
    out.append("\n## Sweep hour (NY) by mode: all / taken\n")
    if len(with_sweep):
        hrs = with_sweep.dropna(subset=["sweep_hour"]).copy()
        hrs["sweep_hour"] = hrs["sweep_hour"].astype(int)
        a = pd.crosstab(hrs["sweep_hour"], hrs["mode"])
        t = pd.crosstab(hrs["sweep_hour"], hrs["mode"], values=hrs["taken"], aggfunc="sum").reindex(a.index).fillna(0).astype(int)
        out.append(_md_table(a.astype(str) + " / " + t.astype(str)))
    else:
        out.append("_none_\n")
    out.append("\n## Key-level type of armed/taken setups\n")
    kl = s[s["kl_kind"].fillna("") != ""]
    out.append(_md_table(pd.crosstab(kl["kl_kind"], kl["mode"]) if len(kl) else pd.DataFrame()))
    out.append("\n## Entry model of taken setups\n")
    tk = s[s["taken"]]
    out.append(_md_table(pd.crosstab(tk["entry_kind"], tk["mode"]) if len(tk) else pd.DataFrame()))
    return "\n".join(out)


def write_report(setups: pd.DataFrame, out_dir: Path, title: str = "CRT setups report", meta: dict | None = None) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv = out_dir / "setups.csv"
    md = out_dir / "setups_summary.md"
    setups.to_csv(csv, index=False)
    md.write_text(summarize_setups(setups, title, meta))
    return csv, md
