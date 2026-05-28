#!/usr/bin/env python3
"""
Generate the student-facing version of a POGIL activity from the teacher version.

Usage:
    python generate_student_version.py <path-to-teacher-md>

Produces: same directory, with `_Teacher.md` in the filename replaced by `_Student.md`.

Transformations:
    1. The entire `# Facilitation Notes` section (heading and everything after) is dropped.
    2. Every `> ***Sample:***` block is removed and replaced with vertical writing space —
       a series of indented `&nbsp;` lines, with the count proportional to the total
       length of the sample answer (so longer answers get more room to write). A sample
       block may span multiple consecutive `> ` lines; all are consumed and their combined
       length drives the line count. Both `***Sample:***<br>` and `***Sample:*** ` forms
       are recognised.
    3. The redundant `&nbsp;` separator that originally followed each sample answer is
       removed, because the writing space now serves the same role.
    4. A blank line is inserted between the question text and the first `&nbsp;` writing
       line so that the writing space is visually separated from the question.

The script preserves everything else verbatim: title, Why?, Prerequisites, Learning
Objectives, Models, all question text, Exercises, Problem, and the `&nbsp;` separators
between non-question sections.
"""

import re
import sys
from pathlib import Path

# Tunables. A typical handwritten / typed line of student response fits roughly
# this many characters; sample answer length is divided by this to estimate how
# many lines of writing space to leave.
CHARS_PER_LINE = 70
MIN_WRITING_LINES = 2
MAX_WRITING_LINES = 8


def writing_lines_for(sample_text: str) -> int:
    """Return how many `&nbsp;` lines of writing space to leave for a sample of this length."""
    if not sample_text.strip():
        return MIN_WRITING_LINES
    estimated = len(sample_text) // CHARS_PER_LINE + 1
    return max(MIN_WRITING_LINES, min(MAX_WRITING_LINES, estimated))


def generate_student(teacher_text: str) -> str:
    """Apply the three transformations to teacher_text and return the student version."""
    lines = teacher_text.split("\n")
    out: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # 1. Drop the Facilitation Notes section entirely.
        if line.startswith("# Facilitation Notes"):
            break

        # 2 & 3. Replace sample answer with proportional writing space,
        #        and skip the redundant trailing separator.
        # The sample line may use `***Sample:***<br>` or `***Sample:*** ` (legacy).
        sample_match = re.match(r"^(\s*)> \*\*\*Sample:\*\*\*(?:<br>)?\s*(.*)$", line)
        if sample_match:
            indent = sample_match.group(1)
            sample_text = sample_match.group(2)
            i += 1

            # Consume any continuation blockquote lines (> ...) that are part
            # of the same sample answer. Include their text in the length
            # estimate so longer multi-line answers get proportionally more
            # writing space.
            while i < len(lines) and re.match(r"^\s*>", lines[i]):
                sample_text += " " + lines[i].lstrip().lstrip(">").strip()
                i += 1

            n = writing_lines_for(sample_text)
            out.append("")  # blank line between question text and writing space
            for k in range(n):
                out.append(f"{indent}&nbsp;")
                if k < n - 1:
                    out.append("")

            # Look ahead past blank lines for the original `&nbsp;` separator
            # that belongs to this question. If found, skip past it (and add a
            # single blank line as a delimiter to the next item).
            j = i
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines) and re.match(r"^\s*&nbsp;\s*$", lines[j]):
                out.append("")  # delimiter
                i = j + 1
                # Eat one trailing blank line if present, to avoid stacking blanks.
                if i < len(lines) and lines[i].strip() == "":
                    i += 1
            continue

        out.append(line)
        i += 1

    # Trim trailing blank lines and end with a single newline.
    while out and out[-1].strip() == "":
        out.pop()
    out.append("")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(
            "Usage: python generate_student_version.py <path-to-teacher-md>",
            file=sys.stderr,
        )
        return 2

    teacher_path = Path(argv[1]).resolve()
    if not teacher_path.exists():
        print(f"Error: file not found: {teacher_path}", file=sys.stderr)
        return 1
    if not teacher_path.name.endswith("_Teacher.md"):
        print(
            f"Error: expected filename ending in '_Teacher.md', got: {teacher_path.name}",
            file=sys.stderr,
        )
        return 1

    student_name = teacher_path.name[: -len("_Teacher.md")] + "_Student.md"
    student_path = teacher_path.with_name(student_name)

    teacher_text = teacher_path.read_text()
    student_text = generate_student(teacher_text)
    student_path.write_text(student_text)

    print(f"Wrote: {student_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
