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

ZIPS_DIR = Path("zips")
TARGET_DIR = Path("course-evaluations")


def sorted_skill_files() -> list[Path]:
    files = list(ZIPS_DIR.glob("v*.skill"))
    return sorted(files, key=lambda p: int(re.search(r"\d+", p.name).group()))


def get_mtime_iso(path: Path) -> str:
    mtime = path.stat().st_mtime
    return datetime.fromtimestamp(mtime).astimezone().isoformat()


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def extract(zip_path: Path):
    if TARGET_DIR.exists():
        shutil.rmtree(TARGET_DIR)
    with zipfile.ZipFile(zip_path) as z:
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
    if not ZIPS_DIR.is_dir():
        print(f"Error: {ZIPS_DIR}/ not found. Run from the repo root.")
        sys.exit(1)

    skill_files = sorted_skill_files()
    if not skill_files:
        print(f"No .skill files found in {ZIPS_DIR}/")
        sys.exit(1)

    print(f"Found {len(skill_files)} skill files: "
          f"{skill_files[0].name} .. {skill_files[-1].name}\n")

    for zip_path in skill_files:
        date_str = get_mtime_iso(zip_path)
        print(f"{zip_path.name}  ({date_str})")

        extract(zip_path)
        run(["git", "add", str(TARGET_DIR)])

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
