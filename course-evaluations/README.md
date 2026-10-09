# course-evaluations

An [agent skill](https://agentskills.io/) that turns **student course evaluation CSVs** for the JMU CS department into a written report an instructor can act on.

The skill runs a bundled script to compute per-section and per-course statistics and to collect every open-ended comment. Claude then reads all of the comments and writes a report built around recurring themes, the lowest-rated items, and changes over time. The guidance in [SKILL.md](SKILL.md) is based on research about student evaluations of teaching (SET): ratings are affected by course level, class size, whether a course is required, and grade expectations. The report therefore treats ratings as structured student feedback, not as an objective measure of teaching quality. It also follows JMU policy by describing findings in terms of course content, rigor, assignments, and learning experiences, never instructor personality or style.

## Two report modes

The skill picks a mode based on the terms covered by the uploaded files, and asks if that is unclear.

- **Formative / annual review** (one semester or one academic year): a quantitative snapshot table, the strengths and suggested improvements for each course, and themes that appear across courses. Intended for your own reflection or an annual evaluation conference.
- **Longitudinal review** (two or more years): a teaching-evidence document for a pre-tenure (e.g., year 2 or 4) or promotion review. It includes a per-course overview table, a narrative for each course showing how frictions changed over time, and patterns across the curriculum. Before writing, the skill asks which courses matter most to the review and whether there were known turning points, such as a course redesign.

## Usage

### 1. Download your evaluations

Download the CSV export for each course section you want analyzed. Each CSV holds one section. The skill identifies a section by the `SubjectID` column inside the file (e.g., `CS149-0005`), so the filename does not matter.

The term (e.g., `Fall 2024`) is taken from the most common submission date in each file: January–May is Spring, June–August is Summer, and September–December is Fall. Sections from before Fall 2022, which used the older 1–5 agreement scale, are automatically converted to the current 1–4 scale so that every term can be compared.

### 2. Upload and ask

Attach the CSVs and invoke the skill with its slash command:

```
/course-evaluations
```

You can add context after the command, such as the purpose of the report (e.g., `/course-evaluations for my promotion review`).

Claude.ai accepts at most 20 attachments per message. If you have more than 20 CSVs, put them all in one **zip archive** and upload the zip instead.

If you run `/course-evaluations` without attaching any CSVs, Claude will reply with brief upload instructions.

### 3. (Optional) Add enrollment numbers for response rates

The CSVs include only the students who **responded**, not the number of students **enrolled**, so the skill cannot calculate response rates from them alone. To add response rates to the report, also upload a small JSON file that gives the enrollment for each section.

**Where to find the numbers.** Use the **"Course Audience"** figure from the PDF evaluation report for each section. This is the end-of-term enrollment.

**File format.** The file is a single JSON object. Each key is the term and the `SubjectID`, joined by a colon, and each value is the enrollment:

```json
{
  "Fall 2024:CS149-0005": 24,
  "Fall 2024:CS374-0002": 22,
  "Spring 2023:CS149-0001": 30
}
```

Things to get right:

- **The term must match the skill's term labels exactly**: a capitalized season, a space, and a four-digit year (`Fall 2024`, `Spring 2023`, `Summer 2022`). The term is part of the key because the same section number (e.g., `CS149-0001`) is used again in different semesters.
- **The `SubjectID` must match the CSV exactly**, including the hyphen and leading zeros (`CS149-0005`, not `CS 149-5`).
- **The file needs a `.json` extension** so that it is detected automatically. Name it anything you like, e.g. `enrollment.json`. Upload it next to the CSVs (or the zip). Do not put it inside the zip.
- **Partial coverage is fine.** Sections missing from the file are reported without a response rate, and the script warns about each key it cannot find. Any extra keys that don't match an uploaded CSV are ignored.

**What it adds to the report.** With enrollment data, the script:

- adds **Enrolled** and **RR%** columns to the per-section table, and **Total Enrolled** and **Pooled RR%** to the per-course table. The pooled rate is total respondents divided by total enrollment, so small sections do not count for more than their size;
- lists every section with a response rate **below 40%**, the point at which self-selection bias becomes a real concern;
- shows each section's response rate next to its comments, with a warning on low-response sections.

The report then uses response rate to judge how reliable each section's feedback is. Themes from a section where 8 of 10 students responded get more weight than themes from a section where 8 of 30 responded. Without an enrollment file, the skill instead cautions about any section with fewer than about 10 respondents.

## Running the script directly

You can also run [parse_evaluations.py](scripts/parse_evaluations.py) yourself to get the raw tables and comments without a written report. It requires Python 3.10+ and pandas.

```bash
python3 scripts/parse_evaluations.py path/to/*.csv
python3 scripts/parse_evaluations.py path/to/*.csv --enrollment enrollment.json
```

Output goes to stdout in three parts: the per-section means table, the per-course summary table, and all Q15 (strengths) and Q16 (improvements) comments grouped by section. Warnings, such as missing columns or enrollment keys that were not found, go to stderr.

## Installation

Download the prebuilt skill package here: **[course-evaluations.zip](https://github.com/ChrisMayfield/claude-skills/releases/download/skills-latest/course-evaluations.zip)** (automatically built from this repository).

### Claude

1. Go to [**Customize → Skills**](https://claude.ai/customize/skills). (Requires a plan with Skills and code execution enabled.)
2. Click the `+` button, then Create Skill, then Upload a skill.
3. Start a conversation, attach your evaluation CSVs, and ask for an analysis. The skill loads automatically when it is relevant.

For Claude Code, place the `course-evaluations/` folder in `~/.claude/skills/` (personal) or `.claude/skills/` (project-scoped).
