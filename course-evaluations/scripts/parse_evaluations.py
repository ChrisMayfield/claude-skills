#!/usr/bin/env python3
"""
parse_evaluations.py — Ingest one or more course-evaluation CSVs and print
a means table plus a grouped dump of open-text comments.

Usage:
    python parse_evaluations.py FILE [FILE ...]
    python parse_evaluations.py /mnt/user-data/uploads/*.csv
    python parse_evaluations.py /mnt/user-data/uploads/*.csv --enrollment enrollment.json

The optional --enrollment file is a JSON object mapping SubjectID to the
number of students enrolled at end of term ("Course Audience" in the JMU
PDF report), e.g.:
    {"CS149-0001": 35, "CS149-0002": 32, "CS345-0001": 18}

When provided, response rate (respondents / enrolled) is added to both
summary tables and section comment headers. Sections below 40% response
rate are flagged — below this threshold self-selection bias becomes a
meaningful concern.

Robustness notes:
- The SubjectID column inside each CSV is the authoritative section
  identifier. Filenames are ignored for identification purposes.
- Columns are identified by *substring* of the question text, so the script
  keeps working if the exporter changes column order or tweaks wording slightly.
- "D/A" string values are converted to NaN before computing means.
- Missing items emit a warning but do not abort.
"""

import sys
import re
import json
import argparse
import glob
from pathlib import Path
from collections import defaultdict
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

STRENGTHS_KEY    = "strengths"             # substring of Q15 column
IMPROVEMENTS_KEY = "could the teaching"    # substring of Q16 column
FILLOUT_KEY      = "filloutdate"           # substring of timestamp column
SUBJECT_KEY      = "subjectid"             # substring of SubjectID column

LOW_RR_THRESHOLD = 0.40   # flag sections below this response rate

TERM_BY_MONTH = {
    1: "Spring", 2: "Spring", 3: "Spring", 4: "Spring", 5: "Spring",
    6: "Summer", 7: "Summer", 8: "Summer",
    9: "Fall", 10: "Fall", 11: "Fall", 12: "Fall",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def detect_semester(df: pd.DataFrame) -> str:
    col = find_column(df, FILLOUT_KEY)
    if col is None:
        return "Unknown term"
    parsed = pd.to_datetime(df[col], format="%m/%d/%y %I:%M %p", errors="coerce")
    if parsed.isna().all():
        parsed = pd.to_datetime(df[col], errors="coerce")
    parsed = parsed.dropna()
    if parsed.empty:
        return "Unknown term"
    month_year = list(zip(parsed.dt.month, parsed.dt.year))
    modal_month, modal_year = max(set(month_year), key=month_year.count)
    return f"{TERM_BY_MONTH.get(modal_month, 'Unknown')} {modal_year}"


def find_column(df: pd.DataFrame, needle: str) -> str | None:
    needle = needle.lower()
    for col in df.columns:
        if needle in str(col).lower():
            return col
    return None


def is_meaningful_text(value) -> bool:
    if pd.isna(value):
        return False
    text = str(value).strip()
    if not text:
        return False
    if text.upper() in {"D/A", "N/A", "NA"}:
        return False
    return True


SEASON_ORDER = {"Spring": 1, "Summer": 2, "Fall": 3}
_SECTION_ID_RE = re.compile(r"^([A-Za-z]+)\s*(\d+)\s*[-_ ]\s*(\d+)")


def sort_key(result: dict) -> tuple:
    term = result["term"]
    parts = term.split()
    if len(parts) == 2 and parts[0] in SEASON_ORDER and parts[1].isdigit():
        term_key = (int(parts[1]), SEASON_ORDER[parts[0]])
    else:
        term_key = (9999, 9)
    m = _SECTION_ID_RE.match(result["section_id"])
    if m:
        dept = m.group(1).upper()
        course_num = int(m.group(2))
        section_num = int(m.group(3))
    else:
        dept, course_num, section_num = "ZZZZ", 99999, 99999
    return (term_key, dept, course_num, section_num)


def course_key(section_id: str) -> str:
    m = _SECTION_ID_RE.match(section_id)
    if m:
        return f"{m.group(1).upper()}{m.group(2)}"
    return section_id


def fmt_rr(response_rate: float | None) -> str:
    """Format a response rate (0–1) as a percentage string, or '—'."""
    if response_rate is None:
        return "—"
    pct = response_rate * 100
    flag = " !" if response_rate < LOW_RR_THRESHOLD else ""
    return f"{pct:.0f}%{flag}"


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def analyze_file(path: Path, enrollment: dict[str, int] | None = None) -> dict:
    df = pd.read_csv(path)

    subj_col = find_column(df, SUBJECT_KEY)
    if subj_col is not None and df[subj_col].notna().any():
        section_id = str(df[subj_col].dropna().mode().iloc[0]).strip()
    else:
        section_id = path.stem
        print(f"  [warn] {path.name}: SubjectID column not found; "
              f"using filename '{path.stem}' as section ID", file=sys.stderr)

    term = detect_semester(df)
    n_total = len(df)

    # Response rate (requires enrollment data)
    enrolled = enrollment.get(section_id) if enrollment else None
    if enrolled is not None and enrolled > 0:
        response_rate = n_total / enrolled
    else:
        response_rate = None
        if enrollment is not None and section_id not in enrollment:
            print(f"  [warn] {section_id}: not found in enrollment file; "
                  f"response rate unavailable", file=sys.stderr)

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
        "section_id":    section_id,
        "term":          term,
        "n_total":       n_total,
        "enrolled":      enrolled,
        "response_rate": response_rate,
        "means":         means,
        "da_counts":     da_counts,
        "n_responded":   n_responded,
        "strengths":     strengths,
        "improvements":  improvements,
    }


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_means_table(results: list[dict]) -> None:
    has_rr = any(r["response_rate"] is not None for r in results)

    print("=" * 78)
    print("QUANTITATIVE SUMMARY — PER SECTION")
    print("=" * 78)
    print("Scales: Q3-Q12 are 1-4 (1=Strongly Disagree, 4=Strongly Agree)")
    print("        Q13-Q14 are 1-5 (1=Poor, 2=Fair, 3=Good, 4=Very Good, 5=Excellent)")
    print("        D/A responses excluded from means.")
    print("        Term auto-detected from modal FilloutDate.")
    if has_rr:
        print(f"        RR% = response rate (respondents / enrolled)."
              f" ! = below {LOW_RR_THRESHOLD*100:.0f}% threshold.")
    print()

    headers = ["Section", "Term", "N"]
    if has_rr:
        headers += ["Enrolled", "RR%"]
    headers += [short for short, _, _ in ITEMS]
    print("\t".join(headers))

    for r in results:
        row = [r["section_id"], r["term"], str(r["n_total"])]
        if has_rr:
            row.append(str(r["enrolled"]) if r["enrolled"] is not None else "—")
            row.append(fmt_rr(r["response_rate"]))
        for short, _, _ in ITEMS:
            v = r["means"].get(short)
            row.append(f"{v:.2f}" if v is not None else "—")
        print("\t".join(row))

    # Flag low response rates
    if has_rr:
        low_rr = [r for r in results
                  if r["response_rate"] is not None
                  and r["response_rate"] < LOW_RR_THRESHOLD]
        print(f"\nSections below {LOW_RR_THRESHOLD*100:.0f}% response rate"
              f" (interpret means with caution):")
        if low_rr:
            for r in low_rr:
                print(f"  {r['section_id']} {r['term']}: "
                      f"{r['n_total']}/{r['enrolled']} "
                      f"({r['response_rate']*100:.0f}%)")
        else:
            print("  (none)")

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


def print_course_summary_table(results: list[dict]) -> None:
    has_rr = any(r["response_rate"] is not None for r in results)

    groups: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        groups[course_key(r["section_id"])].append(r)

    def course_sort_key(course: str) -> tuple:
        m = re.match(r"^([A-Za-z]+)(\d+)$", course)
        if m:
            return (m.group(1).upper(), int(m.group(2)))
        return ("ZZZZ", 99999)

    sorted_courses = sorted(groups.keys(), key=course_sort_key)

    print("\n" + "=" * 78)
    print("COURSE SUMMARY (aggregated across all sections and terms)")
    print("=" * 78)
    print("Q13 and Q14 means are weighted by number of respondents per section.")
    print("D/A responses excluded from means.")
    if has_rr:
        print(f"Pooled RR% = total respondents / total enrolled across all sections."
              f" ! = below {LOW_RR_THRESHOLD*100:.0f}%.")
    print()

    headers = ["Course", "Terms", "Sections", "Total N"]
    if has_rr:
        headers += ["Total Enrolled", "Pooled RR%"]
    headers += ["Q13_InstructorOverall", "Q14_CourseOverall"]
    print("\t".join(headers))

    for course in sorted_courses:
        sections = groups[course]
        n_terms = len({r["term"] for r in sections})
        n_sections = len(sections)
        total_n = sum(r["n_total"] for r in sections)

        sections_with_rr = [r for r in sections if r["enrolled"] is not None]
        if has_rr and sections_with_rr:
            total_enrolled = sum(r["enrolled"] for r in sections_with_rr)
            pooled_respondents = sum(r["n_total"] for r in sections_with_rr)
            pooled_rr = pooled_respondents / total_enrolled if total_enrolled else None
        else:
            total_enrolled = None
            pooled_rr = None

        def weighted_mean(short: str) -> str:
            total_weight = sum(r["n_responded"].get(short) or 0 for r in sections)
            if total_weight == 0:
                return "—"
            wsum = sum(
                (r["means"].get(short) or 0) * (r["n_responded"].get(short) or 0)
                for r in sections
            )
            return f"{wsum / total_weight:.2f}"

        row = [course, str(n_terms), str(n_sections), str(total_n)]
        if has_rr:
            row.append(str(total_enrolled) if total_enrolled is not None else "—")
            row.append(fmt_rr(pooled_rr))
        row += [weighted_mean("Q13_InstructorOverall"), weighted_mean("Q14_CourseOverall")]
        print("\t".join(row))


def print_comments(results: list[dict]) -> None:
    for r in results:
        if r["response_rate"] is not None:
            rr_note = (f"  |  {r['n_total']}/{r['enrolled']} responded "
                       f"({r['response_rate']*100:.0f}%)")
            if r["response_rate"] < LOW_RR_THRESHOLD:
                rr_note += "  *** LOW RESPONSE RATE — interpret themes with caution ***"
        else:
            rr_note = ""

        label = f"{r['section_id']} — {r['term']}{rr_note}"

        print("\n" + "=" * 78)
        print(f"{label}")
        print(f"STRENGTHS (Q15)  [{len(r['strengths'])} substantive responses]")
        print("=" * 78)
        for i, s in enumerate(r["strengths"], 1):
            print(f"\n[{i}] {s}")

        print("\n" + "=" * 78)
        print(f"{label}")
        print(f"IMPROVEMENTS (Q16)  [{len(r['improvements'])} substantive responses]")
        print("=" * 78)
        for i, s in enumerate(r["improvements"], 1):
            print(f"\n[{i}] {s}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="+", help="CSV file paths (globs OK)")
    parser.add_argument(
        "--enrollment", metavar="JSON",
        help="Optional JSON file mapping SubjectID to enrolled student count"
    )
    args = parser.parse_args()

    # Load optional enrollment data
    enrollment: dict[str, int] | None = None
    if args.enrollment:
        enroll_path = Path(args.enrollment)
        if not enroll_path.exists():
            print(f"  [warn] enrollment file not found: {enroll_path}", file=sys.stderr)
        else:
            with open(enroll_path) as f:
                enrollment = json.load(f)
            print(f"  [info] loaded enrollment data for "
                  f"{len(enrollment)} section(s)", file=sys.stderr)

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
        results.append(analyze_file(p, enrollment))

    if not results:
        print("No CSVs could be read.", file=sys.stderr)
        sys.exit(1)

    results.sort(key=sort_key)

    print_means_table(results)
    print_course_summary_table(results)
    print_comments(results)


if __name__ == "__main__":
    main()
