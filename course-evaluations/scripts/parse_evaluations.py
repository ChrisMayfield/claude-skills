#!/usr/bin/env python3
"""
parse_evaluations.py — Ingest one or more course-evaluation CSVs and print
a means table plus a grouped dump of open-text comments.

Usage:
    python parse_evaluations.py FILE [FILE ...]
    python parse_evaluations.py /mnt/user-data/uploads/*.csv

Robustness notes:
- Columns are identified by *substring* of the question text, so the script
  keeps working if the exporter changes column order or tweaks wording slightly.
- "D/A" string values are converted to NaN before computing means.
- Missing items emit a warning but do not abort.
"""

import sys
import argparse
import glob
from pathlib import Path
import pandas as pd

# (short_name, substring_to_match_in_column_name, scale_max)
ITEMS = [
    ("Q3_TaughtClearly",       "taught clearly",                         4),
    ("Q4_WellPrepared",        "well-prepared",                          4),
    ("Q5_ConcernRespect",      "concern and respect",                    4),
    ("Q6_HelpfulFeedback",     "helpful feedback",                       4),
    ("Q7_HelpOutsideClass",    "outside of class",                       4),
    ("Q8_CourseStructure",     "structure of the course",                4),
    ("Q9_AssignmentsValuable", "assignments were valuable",              4),
    ("Q10_MaterialsValuable",  "course materials",                       4),
    ("Q11_ExamsReflective",    "exams and other assessments",            4),
    ("Q12_LearnedAGreatDeal",  "learned a great deal",                   4),
    ("Q13_InstructorOverall",  "instructor overall rating",              5),
    ("Q14_CourseOverall",      "course overall rating",                  5),
]

STRENGTHS_KEY = "strengths"             # substring of Q15 column
IMPROVEMENTS_KEY = "could the teaching" # substring of Q16 column
FILLOUT_KEY = "filloutdate"             # substring of timestamp column

# Months -> term name. Late Dec/early Jan completions still count as
# the Fall/Spring term whose end-of-semester they're closest to.
TERM_BY_MONTH = {
    1: "Spring", 2: "Spring", 3: "Spring", 4: "Spring", 5: "Spring",
    6: "Summer", 7: "Summer", 8: "Summer",
    9: "Fall", 10: "Fall", 11: "Fall", 12: "Fall",
}


def detect_semester(df: pd.DataFrame) -> str:
    """
    Infer the semester ("Fall 2025", "Spring 2026", etc.) from the modal
    FilloutDate. Returns "Unknown term" if no usable timestamps are present.
    """
    col = find_column(df, FILLOUT_KEY)
    if col is None:
        return "Unknown term"
    # Format like "12/01/25 01:33 PM"; fall back to inference if format differs.
    parsed = pd.to_datetime(df[col], format="%m/%d/%y %I:%M %p", errors="coerce")
    if parsed.isna().all():
        parsed = pd.to_datetime(df[col], errors="coerce")
    parsed = parsed.dropna()
    if parsed.empty:
        return "Unknown term"
    # Modal (month, year) — most responses' term wins.
    month_year = list(zip(parsed.dt.month, parsed.dt.year))
    modal_month, modal_year = max(set(month_year), key=month_year.count)
    return f"{TERM_BY_MONTH.get(modal_month, 'Unknown')} {modal_year}"


def find_column(df: pd.DataFrame, needle: str) -> str | None:
    """Case-insensitive substring match against column names."""
    needle = needle.lower()
    for col in df.columns:
        if needle in str(col).lower():
            return col
    return None


def is_meaningful_text(value) -> bool:
    """Filter out NaN, empty strings, and 'D/A'-only responses."""
    if pd.isna(value):
        return False
    text = str(value).strip()
    if not text:
        return False
    if text.upper() in {"D/A", "N/A", "NA"}:
        return False
    return True


def analyze_file(path: Path) -> dict:
    df = pd.read_csv(path)
    section_id = path.stem  # e.g., "CS149-0005"
    term = detect_semester(df)
    n_total = len(df)

    # Quantitative means
    means = {}
    da_counts = {}
    n_responded = {}
    for short, needle, _scale in ITEMS:
        col = find_column(df, needle)
        if col is None:
            print(f"  [warn] {section_id}: column for '{needle}' not found; skipping",
                  file=sys.stderr)
            means[short] = None
            da_counts[short] = None
            n_responded[short] = None
            continue
        raw = df[col]
        da = (raw.astype(str).str.upper().str.strip() == "D/A").sum()
        numeric = pd.to_numeric(raw, errors="coerce")
        means[short] = round(float(numeric.mean()), 2) if numeric.notna().any() else None
        da_counts[short] = int(da)
        n_responded[short] = int(numeric.notna().sum())

    # Qualitative responses
    strengths_col = find_column(df, STRENGTHS_KEY)
    improvements_col = find_column(df, IMPROVEMENTS_KEY)
    strengths = (
        [s.strip() for s in df[strengths_col].tolist() if is_meaningful_text(s)]
        if strengths_col else []
    )
    improvements = (
        [s.strip() for s in df[improvements_col].tolist() if is_meaningful_text(s)]
        if improvements_col else []
    )

    return {
        "section_id": section_id,
        "term": term,
        "n_total": n_total,
        "means": means,
        "da_counts": da_counts,
        "n_responded": n_responded,
        "strengths": strengths,
        "improvements": improvements,
    }


def print_means_table(results: list[dict]) -> None:
    print("=" * 78)
    print("QUANTITATIVE SUMMARY")
    print("=" * 78)
    print("Scales: Q3-Q12 are 1-4 (1=Strongly Disagree, 4=Strongly Agree)")
    print("        Q13-Q14 are 1-5 (1=Poor, 2=Fair, 3=Good, 4=Very Good, 5=Excellent)")
    print("        D/A responses excluded from means.")
    print("        Term auto-detected from modal FilloutDate.\n")

    headers = ["Section", "Term", "N"] + [short for short, _, _ in ITEMS]
    print("\t".join(headers))
    for r in results:
        row = [r["section_id"], r["term"], str(r["n_total"])]
        for short, _, _ in ITEMS:
            v = r["means"].get(short)
            row.append(f"{v:.2f}" if v is not None else "—")
        print("\t".join(row))

    # Flag notable D/A rates
    print("\nNotable D/A rates (>=30% of responses on any item):")
    any_flagged = False
    for r in results:
        for short, _, _ in ITEMS:
            n_resp = r["n_responded"].get(short)
            da = r["da_counts"].get(short)
            if n_resp is None or da is None:
                continue
            n_with_da = n_resp + da
            if n_with_da >= 5 and da / n_with_da >= 0.30:
                print(f"  {r['section_id']} {short}: {da}/{n_with_da} D/A "
                      f"({100*da/n_with_da:.0f}%)")
                any_flagged = True
    if not any_flagged:
        print("  (none)")


def print_comments(results: list[dict]) -> None:
    for r in results:
        label = f"{r['section_id']} — {r['term']}"
        print("\n" + "=" * 78)
        print(f"{label} — STRENGTHS (Q15)  [{len(r['strengths'])} substantive responses]")
        print("=" * 78)
        for i, s in enumerate(r["strengths"], 1):
            print(f"\n[{i}] {s}")

        print("\n" + "=" * 78)
        print(f"{label} — IMPROVEMENTS (Q16)  [{len(r['improvements'])} substantive responses]")
        print("=" * 78)
        for i, s in enumerate(r["improvements"], 1):
            print(f"\n[{i}] {s}")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="+", help="CSV file paths (globs OK)")
    args = parser.parse_args()

    # Expand any globs that the shell didn't expand
    paths: list[Path] = []
    for f in args.files:
        expanded = glob.glob(f)
        if expanded:
            paths.extend(Path(p) for p in expanded)
        else:
            paths.append(Path(f))
    paths = sorted(set(paths))

    if not paths:
        print("No files found.", file=sys.stderr)
        sys.exit(1)

    results = []
    for p in paths:
        if not p.exists():
            print(f"  [warn] {p} not found; skipping", file=sys.stderr)
            continue
        results.append(analyze_file(p))

    if not results:
        print("No CSVs could be read.", file=sys.stderr)
        sys.exit(1)

    print_means_table(results)
    print_comments(results)


if __name__ == "__main__":
    main()
