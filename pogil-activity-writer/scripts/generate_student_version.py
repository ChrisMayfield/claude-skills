#!/usr/bin/env python3
"""
Generate the student version of an activity from the teacher version.

Usage:
    python3 generate_student_version.py <path-to-teacher-md> [<path-to-student-md>]

Produces the student file at the given path, or by default in the same directory,
with `_Teacher.md` in the filename replaced by `_Student.md`.

Transformations:
    1. The `# Facilitation Notes` section (heading and everything after) is dropped.
    2. Every sample block (a `> ***Sample:***<br>` marker line and the `> ` answer
       lines below it) is replaced with `&nbsp;` lines of writing space, indented
       like the sample, as many as the answer is long, plus one for each empty `>`
       line outside a code fence. A marker line with extra text on it is still
       consumed, with a warning, so the answer cannot leak. The writing space gets
       an `<!-- answer: code -->` comment before it if the sample contains a fenced
       code block, or an `<!-- answer -->` comment if it is un-indented (the
       Problem), which the Word builder would otherwise read as separators.
    3. The `&nbsp;` separator that followed each sample is removed.
    4. A blank line is inserted between the question text and the writing space,
       unless one is already there.
    5. Any other indented `&nbsp;` is un-indented, so the Word builder treats it as
       a separator rather than writing space.

Everything else is preserved verbatim.
"""

import re
import sys
from pathlib import Path

# Characters of student writing per line of writing space.
CHARS_PER_LINE = 70
MIN_WRITING_LINES = 2
MAX_WRITING_LINES = 8
# Characters per printed line of a teacher sample (about 105 fit; conservative).
WRAP_CHARS = 90


def writing_lines_for(sample_text: str, rendered_lines: int) -> int:
    """Return how many `&nbsp;` lines of writing space to leave for a sample.

    Proportional to the sample's length, clamped, but never fewer than the lines
    the sample wraps to when printed, so the teacher sample fits a box of the same
    height and the two versions line up. `build_docx.js` repeats this calculation
    and must stay in step with it.
    """
    if not sample_text.strip():
        estimated = MIN_WRITING_LINES
    else:
        estimated = len(sample_text) // CHARS_PER_LINE + 1
    estimated = max(MIN_WRITING_LINES, min(MAX_WRITING_LINES, estimated))
    return max(estimated, rendered_lines)


# The marker line: a blockquote carrying the bold-italic "Sample" label. Anything else
# on the line (a stray "(variation expected)", a missing <br>) is tolerated.
SAMPLE_MARKER = re.compile(r"^(\s*)>\s*(.*?)\*\*\*Sample\b[^*]*\*\*\*(.*?)\s*$")
CANONICAL_MARKER = re.compile(r"^\s*> \*\*\*Sample:\*\*\*<br>\s*$")

# Mark writing space for a code answer, and un-indented writing space that would
# otherwise read as separators; invisible when the Markdown is rendered.
CODE_ANSWER_MARKER = "<!-- answer: code -->"
ANSWER_MARKER = "<!-- answer -->"

NBSP = re.compile(r"^\s*&nbsp;\s*$")
INDENTED_NBSP = re.compile(r"^\s+&nbsp;\s*$")


def generate_student(teacher_text: str) -> str:
    """Apply the five transformations to teacher_text and return the student version."""
    lines = teacher_text.split("\n")
    out: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # 1. Drop the Facilitation Notes section entirely.
        if line.startswith("# Facilitation Notes"):
            break

        # 2 & 3. Replace the sample with writing space; drop its separator.
        sample_match = SAMPLE_MARKER.match(line)
        if sample_match:
            indent = sample_match.group(1)
            sample_text = ""
            if not CANONICAL_MARKER.match(line):
                print(
                    f"Warning: line {i + 1}: sample marker should be exactly "
                    f"'> ***Sample:***<br>'; move other text to the next line: {line.strip()}",
                    file=sys.stderr,
                )
                extra = sample_match.group(2) + " " + sample_match.group(3)
                sample_text = " " + extra.replace("<br>", "").strip()
            i += 1

            # Consume the answer lines, measuring their length and the printed
            # lines they wrap to (fence lines are not printed).
            is_code = False
            in_fence = False
            rendered = 0
            extra_lines = 0
            while i < len(lines) and re.match(r"^\s*>", lines[i]):
                content = lines[i].lstrip().lstrip(">").strip()
                if content.startswith("```"):
                    is_code = True
                    in_fence = not in_fence
                elif in_fence or content:
                    rendered += max(1, -(-len(content) // WRAP_CHARS))
                else:
                    extra_lines += 1
                sample_text += " " + content
                i += 1

            n = writing_lines_for(sample_text, rendered) + extra_lines
            # 4. Leave a blank line between the question text and the writing space.
            if out and out[-1].strip():
                out.append("")
            if is_code:
                out.append(f"{indent}{CODE_ANSWER_MARKER}")
            elif not indent:
                out.append(ANSWER_MARKER)
            for k in range(n):
                out.append(f"{indent}&nbsp;")
                if k < n - 1:
                    out.append("")

            # Skip the `&nbsp;` separator that followed the sample, if any.
            j = i
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines) and NBSP.match(lines[j]):
                out.append("")  # delimiter
                i = j + 1
                # Eat one trailing blank line if present, to avoid stacking blanks.
                if i < len(lines) and lines[i].strip() == "":
                    i += 1
            continue

        # 5. Leftover indented breathing room is not writing space; un-indent it.
        if INDENTED_NBSP.match(line):
            out.append("&nbsp;")
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
    if len(argv) not in (2, 3):
        print(
            "Usage: python3 generate_student_version.py <path-to-teacher-md> [<path-to-student-md>]",
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

    if len(argv) == 3:
        student_path = Path(argv[2]).resolve()
    else:
        student_name = teacher_path.name[: -len("_Teacher.md")] + "_Student.md"
        student_path = teacher_path.with_name(student_name)

    teacher_text = teacher_path.read_text()
    student_text = generate_student(teacher_text)
    if "***Sample" in student_text:
        print(
            "Error: a sample label survived into the student version; "
            "check that every marker line starts with '>'.",
            file=sys.stderr,
        )
        return 1
    student_path.parent.mkdir(parents=True, exist_ok=True)
    student_path.write_text(student_text)

    print(f"Wrote: {student_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
