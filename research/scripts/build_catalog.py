#!/usr/bin/env python3
"""Expand every source in sources/catalog.yaml into a per-video list.

Writes sources/lists/<source_id>.tsv with columns:
    video_id  title  duration_sec  url

Only metadata is fetched (no video/transcript download), so this works
without YouTube cookies.

Usage:
    pip install yt-dlp pyyaml
    python research/scripts/build_catalog.py            # all sources
    python research/scripts/build_catalog.py crt-romeo  # one source
"""
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "sources" / "catalog.yaml"
LISTS = ROOT / "sources" / "lists"


def list_videos(url: str) -> list[tuple[str, str, str]]:
    out = subprocess.run(
        ["yt-dlp", "--flat-playlist", "--ignore-errors",
         "--print", "%(id)s\t%(title)s\t%(duration)s", url],
        capture_output=True, text=True, check=False,
    ).stdout
    rows = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) == 3 and parts[0]:
            rows.append((parts[0], parts[1], parts[2]))
    return rows


def main() -> None:
    wanted = set(sys.argv[1:])
    sources = yaml.safe_load(CATALOG.read_text())["sources"]
    LISTS.mkdir(parents=True, exist_ok=True)
    for src in sources:
        if wanted and src["id"] not in wanted:
            continue
        rows = list_videos(src["url"])
        # Channel "/videos" tabs list newest first; study oldest first.
        if "/videos" in src["url"]:
            rows.reverse()
        path = LISTS / f"{src['id']}.tsv"
        with path.open("w") as f:
            f.write("video_id\ttitle\tduration_sec\turl\n")
            for vid, title, dur in rows:
                f.write(f"{vid}\t{title}\t{dur}\thttps://www.youtube.com/watch?v={vid}\n")
        print(f"{src['id']}: {len(rows)} videos -> {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
