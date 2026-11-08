#!/usr/bin/env python3
"""Download English transcripts for every video in a source list.

Transcripts go to research/raw/transcripts/<source_id>/<video_id>.txt.
That folder is git-ignored: the transcripts are the creators' content and
stay on your machine. Our own notes (research/notes/) are what gets committed.

YouTube blocks transcript downloads from cloud servers, so run this on
your own computer, logged in to YouTube in a browser:

    pip install yt-dlp pyyaml
    python research/scripts/fetch_transcripts.py crt-romeo --browser chrome

Already-downloaded transcripts are skipped, so you can re-run it any time.
"""
import argparse
import csv
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LISTS = ROOT / "sources" / "lists"
OUT = ROOT / "raw" / "transcripts"


def vtt_to_text(vtt: str) -> str:
    """Turn a VTT caption file into plain text with [mm:ss] markers per cue,
    dropping the duplicate rolling lines that auto-captions produce."""
    lines, last = [], None
    stamp = None
    for raw in vtt.splitlines():
        m = re.match(r"(\d+):(\d+):(\d+)\.\d+ -->", raw)
        if m:
            h, mi, s = map(int, m.groups())
            stamp = f"[{h * 60 + mi}:{s:02d}]"
            continue
        text = re.sub(r"<[^>]+>", "", raw).strip()
        if not text or text in ("WEBVTT",) or text.startswith(("Kind:", "Language:")):
            continue
        if text == last:
            continue
        last = text
        lines.append(f"{stamp} {text}" if stamp else text)
        stamp = None
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source_id", help="id from sources/catalog.yaml")
    ap.add_argument("--browser", default="chrome",
                    help="browser to read YouTube cookies from (chrome, firefox, edge, safari)")
    args = ap.parse_args()

    out_dir = OUT / args.source_id
    out_dir.mkdir(parents=True, exist_ok=True)
    with (LISTS / f"{args.source_id}.tsv").open() as f:
        rows = list(csv.DictReader(f, delimiter="\t"))

    for row in rows:
        vid = row["video_id"]
        target = out_dir / f"{vid}.txt"
        if target.exists():
            continue
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(
                ["yt-dlp", "--skip-download", "--write-subs", "--write-auto-subs",
                 "--sub-langs", "en.*,en", "--sub-format", "vtt",
                 "--cookies-from-browser", args.browser,
                 "-o", f"{tmp}/%(id)s", row["url"]],
                capture_output=True, text=True, check=False,
            )
            vtts = sorted(Path(tmp).glob("*.vtt"))
            if not vtts:
                print(f"MISSING  {vid}  {row['title']}")
                continue
            body = vtt_to_text(vtts[0].read_text(errors="ignore"))
            target.write_text(f"# {row['title']}\n# {row['url']}\n\n{body}\n")
            print(f"saved    {vid}  {row['title']}")


if __name__ == "__main__":
    main()
