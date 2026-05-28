#!/usr/bin/env python3
"""
Replay skill development history by importing zip archives as git commits.

For each vN.skill file in zips/ (sorted numerically), extracts to TARGET_DIR,
stages changes, generates a commit message via Claude Code CLI, and commits
using the zip file's modification time as the date.

Run from the repo root: python3 import_history.py
"""

import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

SRC_DIR = Path("TODO")
DST_DIR = Path("pogil-activity-writer")


def sorted_source_files() -> list[Path]:
    files = list(SRC_DIR.glob("[Vv]*.skill")) + list(SRC_DIR.glob("[Vv]*.md"))
    return sorted(files, key=lambda p: int(re.search(r"\d+", p.name).group()))


def get_mtime_iso(path: Path) -> str:
    mtime = path.stat().st_mtime
    return datetime.fromtimestamp(mtime).astimezone().isoformat()


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def extract(src_path: Path):
    if DST_DIR.exists():
        shutil.rmtree(DST_DIR)
    if src_path.suffix == ".md":
        DST_DIR.mkdir()
        shutil.copy2(src_path, DST_DIR / "SKILL.md")
    else:
        with zipfile.ZipFile(src_path) as z:
            z.extractall(".")


def generate_message(diff: str) -> str:
    prompt = (
        "Write a brief one-line git commit message for this diff. "
        "Use imperative mood (e.g. 'Add', 'Fix', 'Refactor'). "
        "Be specific about what changed. No conventional-commit prefix. "
        "Output only the commit message, nothing else.\n\n"
        + diff[:6000]
    )
    result = run(["claude", "-p", prompt])
    if result.returncode != 0:
        print(f"  Warning: claude exited {result.returncode}: {result.stderr.strip()}")
    return result.stdout.strip().strip('"')


def main():
    if not SRC_DIR.is_dir():
        print(f"Error: {SRC_DIR}/ not found. Run from the repo root.")
        sys.exit(1)

    source_files = sorted_source_files()
    if not source_files:
        print(f"No .skill or .md files found in {SRC_DIR}/")
        sys.exit(1)

    print(f"Found {len(source_files)} files: "
          f"{source_files[0].name} .. {source_files[-1].name}\n")

    for src_path in source_files:
        extract(src_path)
        date_str = get_mtime_iso(DST_DIR / "SKILL.md")
        print(f"{src_path.name}  ({date_str})")

        run(["git", "add", str(DST_DIR)])

        diff = run(["git", "diff", "--cached"]).stdout
        if not diff.strip():
            print("  (no changes, skipping)\n")
            continue

        message = generate_message(diff)
        print(f"  {message}")

        result = run(["git", "commit", f"--date={date_str}", "-m", message])
        if result.returncode != 0:
            print(f"  Error: {result.stderr.strip()}")
            sys.exit(1)
        print()

    print("Done.")


if __name__ == "__main__":
    main()
