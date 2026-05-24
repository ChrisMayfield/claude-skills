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

Scale history:
  Before Fall 2022 (no EnrollmentType column in CSV):
    Q3-Q12: 1=No Basis to Judge, 2=Strongly Disagree, 3=Somewhat Disagree,
            4=Somewhat Agree, 5=Strongly Agree  (effective range 2-5)
    "1" responses are excluded from means and counted as NB (No Basis).

  Fall 2022 and later (EnrollmentType column present in CSV):
    Q3-Q12: 1=Strongly Disagree, 2=Somewhat Disagree,
            3=Somewhat Agree, 4=Strongly Agree  (range 1-4)

  Q13-Q14 use a 1-5 quality scale in both eras and are directly comparable
  across the scale change.

Robustness notes:
- The SubjectID column inside each CSV is the authoritative section
  identifier. Filenames are ignored for identification purposes.
- Columns are identified by *substring* of the question text, so the script
  keeps working if the exporter changes column order or tweaks wording slightly.
- "D/A" string values are excluded from means in all eras.
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

# Each entry is (short_name, substring_to_match_in_column_name, is_q13_q14).
# is_q13_q14 flags the two overall-rating items, which use a fixed 1–5 scale
# across both survey eras and never treat "1" as No Basis to Judge.
ITEMS = [
    ("Q3_TaughtClearly",       "taught clearly",                False),
    ("Q4_WellPrepared",        "well-prepared",                 False),
    ("Q5_ConcernRespect",      "concern and respect",           False),
    ("Q6_HelpfulFeedback",     "helpful feedback",              False),
    ("Q7_HelpOutsideClass",    "outside of class",              False),
    ("Q8_CourseStructure",     "structure of the course",       False),
    ("Q9_AssignmentsValuable", "assignments were valuable",     False),
    ("Q10_MaterialsValuable",  "course materials",              False),
    ("Q11_ExamsReflective",    "exams and other assessments",   False),
    ("Q12_LearnedAGreatDeal",  "learned a great deal",          False),
    ("Q13_InstructorOverall",  "instructor overall rating",     True),
    ("Q14_CourseOverall",      "course overall rating",         True),
]

# Substrings used to locate specific columns by partial name match.
STRENGTHS_KEY      = "strengths"             # Q15: open-text strengths
IMPROVEMENTS_KEY   = "could the teaching"    # Q16: open-text improvements
FILLOUT_KEY        = "filloutdate"           # submission timestamp
SUBJECT_KEY        = "subjectid"             # course-section identifier
ENROLLMENT_TYPE_KEY = "enrollmenttype"       # present only in new-scale CSVs

LOW_RR_THRESHOLD = 0.40   # response rates below this are flagged in output

TERM_BY_MONTH = {
    1: "Spring", 2: "Spring", 3: "Spring", 4: "Spring", 5: "Spring",
    6: "Summer", 7: "Summer", 8: "Summer",
    9: "Fall", 10: "Fall", 11: "Fall", 12: "Fall",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def detect_semester(df: pd.DataFrame) -> str:
    """Infer the semester label (e.g. 'Fall 2025') from the modal FilloutDate."""
    col = find_column(df, FILLOUT_KEY)
    if col is None:
        return "Unknown term"

    # Try the known JMU export format first; fall back to pandas inference.
    parsed = pd.to_datetime(df[col], format="%m/%d/%y %I:%M %p", errors="coerce")
    if parsed.isna().all():
        parsed = pd.to_datetime(df[col], errors="coerce")

    parsed = parsed.dropna()
    if parsed.empty:
        return "Unknown term"

    # Use the modal (month, year) pair rather than min/max to be robust against
    # stray timestamps from adjacent terms (e.g. late submissions).
    month_year = list(zip(parsed.dt.month, parsed.dt.year))
    modal_month, modal_year = max(set(month_year), key=month_year.count)
    return f"{TERM_BY_MONTH.get(modal_month, 'Unknown')} {modal_year}"


def detect_scale(df: pd.DataFrame) -> str:
    """Return 'old' or 'new' based on whether the EnrollmentType column is present.

    The EnrollmentType column was added in Fall 2022, coinciding with the
    Q3-Q12 scale change from 1-5 (1=No Basis to Judge) to 1-4 (1=Strongly
    Disagree). Its presence is the most reliable indicator of which era the
    CSV is from.
    """
    return "new" if find_column(df, ENROLLMENT_TYPE_KEY) is not None else "old"


def find_column(df: pd.DataFrame, needle: str) -> str | None:
    """Return the first column whose name contains `needle` (case-insensitive), or None."""
    needle = needle.lower()
    for col in df.columns:
        if needle in str(col).lower():
            return col
    return None


def is_meaningful_text(value) -> bool:
    """Return True if `value` is a non-empty string that isn't a D/A placeholder."""
    if pd.isna(value):
        return False
    text = str(value).strip()
    if not text:
        return False
    if text.upper() in {"D/A", "N/A", "NA"}:
        return False
    return True


# Maps season name to a sort index so terms order chronologically within a year.
SEASON_ORDER = {"Spring": 1, "Summer": 2, "Fall": 3}

# Matches section IDs of the form "CS149-0005", "MATH 235_001", etc.
# Groups: (1) dept letters, (2) course number, (3) section number.
_SECTION_ID_RE = re.compile(r"^([A-Za-z]+)\s*(\d+)\s*[-_ ]\s*(\d+)")


def sort_key(result: dict) -> tuple:
    """Composite sort key: (year, season, dept, course_num, section_num).

    Unparseable terms and section IDs sort to the end rather than raising.
    """
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


def term_sort_key(term: str) -> tuple:
    """Sort key for a term string alone (used when sorting sets of term labels)."""
    parts = term.split()
    if len(parts) == 2 and parts[0] in SEASON_ORDER and parts[1].isdigit():
        return (int(parts[1]), SEASON_ORDER[parts[0]])
    return (9999, 9)


def course_key(section_id: str) -> str:
    """Strip the section number from a section ID to get the course identifier.

    E.g. 'CS149-0005' -> 'CS149'. Falls back to the full ID if unparseable.
    """
    m = _SECTION_ID_RE.match(section_id)
    if m:
        return f"{m.group(1).upper()}{m.group(2)}"
    return section_id


def fmt_rr(response_rate: float | None) -> str:
    """Format a response rate (0–1) as a percentage string, appending '!' if below threshold."""
    if response_rate is None:
        return "—"
    flag = " !" if response_rate < LOW_RR_THRESHOLD else ""
    return f"{response_rate * 100:.0f}%{flag}"


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def analyze_file(path: Path, enrollment: dict[str, int] | None = None) -> dict:
    """Parse one CSV and return a result dict with quantitative means and raw comments.

    `enrollment`, if provided, is used to compute response rate for this section.
    Scale (old vs new) is auto-detected from the presence of the EnrollmentType column.
    """
    df = pd.read_csv(path)

    # Prefer the SubjectID embedded in the CSV over the filename, since filenames
    # are arbitrary and may not reflect the actual course-section.
    subj_col = find_column(df, SUBJECT_KEY)
    if subj_col is not None and df[subj_col].notna().any():
        section_id = str(df[subj_col].dropna().mode().iloc[0]).strip()
    else:
        section_id = path.stem
        print(f"  [warn] {path.name}: SubjectID column not found; "
              f"using filename '{path.stem}' as section ID", file=sys.stderr)

    term  = detect_semester(df)
    scale = detect_scale(df)
    n_total = len(df)

    enrolled = enrollment.get(section_id) if enrollment else None
    if enrolled is not None and enrolled > 0:
        response_rate = n_total / enrolled
    else:
        response_rate = None
        if enrollment is not None and section_id not in enrollment:
            print(f"  [warn] {section_id}: not found in enrollment file; "
                  f"response rate unavailable", file=sys.stderr)

    # Compute means, tracking D/A and (for old-scale Q3-Q12) No Basis to Judge
    # responses separately so they don't silently inflate missing-data counts.
    means      = {}
    da_counts  = {}
    nb_counts  = {}   # "No Basis to Judge" — old scale only, Q3-Q12 only
    n_responded = {}

    for short, needle, is_overall in ITEMS:
        col = find_column(df, needle)
        if col is None:
            print(f"  [warn] {section_id}: column for '{needle}' not found; skipping",
                  file=sys.stderr)
            means[short] = da_counts[short] = nb_counts[short] = n_responded[short] = None
            continue

        raw = df[col]

        # Explicit D/A responses (appear as the string "D/A" in any era).
        da = (raw.astype(str).str.upper().str.strip() == "D/A").sum()

        numeric = pd.to_numeric(raw, errors="coerce")

        # On old-scale Q3-Q12, subtract 1 to normalize to the new 1-4 range:
        #   old 2→1 (Strongly Disagree), 3→2, 4→3, 5→4 (Strongly Agree)
        #   old 1 (No Basis to Judge) → 0, then excluded like D/A.
        # Q13-Q14 use a fixed 1-5 quality scale in all eras; no adjustment needed.
        if scale == "old" and not is_overall:
            nb = int((numeric == 1).sum())   # count No Basis before shifting
            numeric = numeric - 1
            numeric = numeric.where(numeric > 0)  # exclude the 0s (were No Basis)
        else:
            nb = 0

        means[short]      = round(float(numeric.mean()), 2) if numeric.notna().any() else None
        da_counts[short]  = int(da)
        nb_counts[short]  = nb
        n_responded[short] = int(numeric.notna().sum())

    strengths_col    = find_column(df, STRENGTHS_KEY)
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
        "scale":         scale,
        "n_total":       n_total,
        "enrolled":      enrolled,
        "response_rate": response_rate,
        "means":         means,
        "da_counts":     da_counts,
        "nb_counts":     nb_counts,
        "n_responded":   n_responded,
        "strengths":     strengths,
        "improvements":  improvements,
    }


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_means_table(results: list[dict]) -> None:
    """Print the per-section quantitative summary table."""
    has_rr      = any(r["response_rate"] is not None for r in results)
    has_old     = any(r["scale"] == "old" for r in results)

    print("=" * 78)
    print("QUANTITATIVE SUMMARY — PER SECTION")
    print("=" * 78)
    print("Q3-Q12: 1=Strongly Disagree, 2=Somewhat Disagree, 3=Somewhat Agree, 4=Strongly Agree")
    if has_old:
        print("        (old-scale sections normalized: original 2-5 mapped to 1-4;")
        print("         original 1=No Basis to Judge excluded, shown as NB)")
    print("Q13-Q14 (all eras): 1=Poor, 2=Fair, 3=Good, 4=Very Good, 5=Excellent")
    print("D/A responses excluded from means. Term auto-detected from modal FilloutDate.")
    if has_rr:
        print(f"RR% = response rate (respondents / enrolled)."
              f" ! = below {LOW_RR_THRESHOLD*100:.0f}% threshold.")
    print()

    headers = ["Section", "Term", "Scale", "N"]
    if has_rr:
        headers += ["Enrolled", "RR%"]
    headers += [short for short, _, _ in ITEMS]
    print("\t".join(headers))

    for r in results:
        # Label old-scale sections to show normalization was applied.
        scale_label = "1-4" if r["scale"] == "new" else "1-4†"
        row = [r["section_id"], r["term"], scale_label, str(r["n_total"])]
        if has_rr:
            row.append(str(r["enrolled"]) if r["enrolled"] is not None else "—")
            row.append(fmt_rr(r["response_rate"]))
        for short, _, _ in ITEMS:
            v = r["means"].get(short)
            row.append(f"{v:.2f}" if v is not None else "—")
        print("\t".join(row))

    if has_old:
        print("\n† Normalized from old scale: original 2-5 mapped to 1-4; original 1 (No Basis) excluded.")

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

    # Flag notable D/A and NB rates together
    print("\nNotable exclusion rates (D/A or No Basis >= 30% of responses on any item):")
    any_flagged = False
    for r in results:
        for short, _, is_overall in ITEMS:
            n_resp = r["n_responded"].get(short)
            da     = r["da_counts"].get(short) or 0
            nb     = r["nb_counts"].get(short) or 0
            if n_resp is None:
                continue
            excluded = da + nb
            n_with_excluded = n_resp + excluded
            if n_with_excluded >= 5 and excluded / n_with_excluded >= 0.30:
                parts = []
                if da: parts.append(f"{da} D/A")
                if nb: parts.append(f"{nb} NB")
                print(f"  {r['section_id']} {short}: {' + '.join(parts)} "
                      f"/ {n_with_excluded} ({100*excluded/n_with_excluded:.0f}%)")
                any_flagged = True
    if not any_flagged:
        print("  (none)")


def print_course_summary_table(results: list[dict]) -> None:
    """Print a per-course aggregate table (one row per course, all terms combined).

    Q13/Q14 means are weighted by n_responded so larger sections contribute
    proportionally more. Pooled response rate is sum(respondents)/sum(enrolled)
    rather than a mean of per-section rates, which would over-weight small sections.
    Courses with sections from both scale eras are flagged.
    """
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
    print("D/A and No Basis responses excluded from means.")
    print("† = old-scale sections normalized (original 2-5 mapped to 1-4).")
    if has_rr:
        print(f"Pooled RR% = total respondents / total enrolled across all sections."
              f" ! = below {LOW_RR_THRESHOLD*100:.0f}%.")
    print()

    headers = ["Course", "Term range", "Scale(s)", "Sections", "Total N"]
    if has_rr:
        headers += ["Total Enrolled", "Pooled RR%"]
    headers += ["Q13_InstructorOverall", "Q14_CourseOverall"]
    print("\t".join(headers))

    for course in sorted_courses:
        sections = groups[course]

        # Show the first and last term taught rather than just a count,
        # which is far more informative for a longitudinal promotion report.
        terms = sorted({r["term"] for r in sections}, key=term_sort_key)
        term_range = terms[0] if len(terms) == 1 else f"{terms[0]} – {terms[-1]}"

        scales_present = {r["scale"] for r in sections}
        if scales_present == {"new"}:
            scale_label = "1-4"
        else:
            # Any old-scale sections were normalized; flag with † for transparency.
            scale_label = "1-4†"

        n_sections = len(sections)
        total_n    = sum(r["n_total"] for r in sections)

        # Only pool response rate over sections that have enrollment data;
        # sections without it are excluded rather than treated as 0.
        sections_with_rr = [r for r in sections if r["enrolled"] is not None]
        if has_rr and sections_with_rr:
            total_enrolled     = sum(r["enrolled"] for r in sections_with_rr)
            pooled_respondents = sum(r["n_total"]  for r in sections_with_rr)
            pooled_rr = pooled_respondents / total_enrolled if total_enrolled else None
        else:
            total_enrolled = None
            pooled_rr      = None

        def weighted_mean(short: str) -> str:
            """Weighted mean for `short` across all sections in this course group."""
            total_weight = sum(r["n_responded"].get(short) or 0 for r in sections)
            if total_weight == 0:
                return "—"
            wsum = sum(
                (r["means"].get(short) or 0) * (r["n_responded"].get(short) or 0)
                for r in sections
            )
            return f"{wsum / total_weight:.2f}"

        row = [course, term_range, scale_label, str(n_sections), str(total_n)]
        if has_rr:
            row.append(str(total_enrolled) if total_enrolled is not None else "—")
            row.append(fmt_rr(pooled_rr))
        row += [weighted_mean("Q13_InstructorOverall"), weighted_mean("Q14_CourseOverall")]
        print("\t".join(row))


def print_comments(results: list[dict]) -> None:
    """Print all Q15/Q16 free-text responses, grouped by section."""
    for r in results:
        if r["response_rate"] is not None:
            rr_note = (f"  |  {r['n_total']}/{r['enrolled']} responded "
                       f"({r['response_rate']*100:.0f}%)")
            if r["response_rate"] < LOW_RR_THRESHOLD:
                rr_note += "  *** LOW RESPONSE RATE — interpret themes with caution ***"
        else:
            rr_note = ""

        scale_note = "" if r["scale"] == "new" else "  [Q3-Q12 normalized from old scale]"
        label = f"{r['section_id']} — {r['term']}{scale_note}{rr_note}"

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
    """Parse arguments, load data, and drive the three output sections."""
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="+", help="CSV file paths (globs OK)")
    parser.add_argument(
        "--enrollment", metavar="JSON",
        help="Optional JSON file mapping SubjectID to enrolled student count"
    )
    args = parser.parse_args()

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

    # Expand globs manually to handle shells that don't (e.g. when invoked
    # programmatically with a literal glob string like "*.csv").
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
