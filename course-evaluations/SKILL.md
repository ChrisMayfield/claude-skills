---
name: course-evaluations
description: "Use this skill to analyze and summarize student course evaluations exported as CSVs — the kind James Madison University sends instructors at the end of each term. Triggers on phrases like 'analyze my evaluations', 'summarize student feedback', 'what did students say about my course', or whenever the user uploads one or more CSV files containing student evaluation data with Likert and open-response columns. Also use when the user uploads evaluations spanning multiple semesters or a full promotion period and wants a longitudinal or comparative analysis. The output is a report the instructor can act on, not a generic data summary."
---

# Course evaluation analysis

## Why this skill exists

The goal is a report the instructor can act on — not a table of means. Research on student evaluations of teaching (SET) consistently finds that ratings reflect more than teaching quality alone: course level, whether a course is required, grade expectations, class size, and sometimes instructor demographics all affect scores in ways that have nothing to do with how well someone teaches. Treat the output as structured student feedback, not an objective measure of teaching effectiveness.

## Institutional policy context

At James Madison University, student feedback surveys:

- **May** be used as a formative tool for faculty members.
- **May** be used as teaching evidence at the faculty member's discretion, when the evidence relates to *course content, rigor, assignments, and learning experiences*.
- **May not** be used as evidence of instructor personality or individual style.
- **May not** be used in promotion and tenure decisions without the faculty member's consent.
- **Should** be used in annual evaluation conferences only as a tool to identify areas of growth.

These constraints apply to **both modes**. In all reports, frame findings around what the instructor *did with the course* — assignment design, assessment structure, pacing decisions, course materials — rather than around personality traits or interpersonal style. This is the right framing for formative use too: it keeps the analysis focused on things the instructor can actually change.

## Modes

Detect the appropriate mode from context. If ambiguous, ask.

**Mode A — Formative / annual review** (one semester or one academic year): The instructor wants to understand what worked and what to improve. The report is for their own use or for an annual evaluation conference.

**Mode B — Longitudinal review** (2+ years): The instructor wants to document teaching practices and growth over time for a formal review — pre-tenure review (year 2 or year 4) or promotion case. The report should surface longitudinal patterns — improvements made, what changed, what stayed consistent — and frame findings in terms of course content, rigor, assignments, and learning experiences, not instructor personality.

Claude.ai allows a maximum of 20 file attachments per message. When the number of CSVs exceeds 20, instruct the user to put all CSVs in a zip archive and upload it as a single attachment. The skill's bash command handles unzipping automatically.

The time period is inferred from the CSV files themselves — the script's term auto-detection covers this. Before running the script in Mode B, ask the user:
1. Which courses are most central to the review? (This determines how much narrative depth each course gets.)
2. Are there any known inflection points to highlight — a course revision, a new course added to the portfolio, a change in teaching approach?

These answers shape the report's narrative arc before a single line is written. If the user has no specific highlights, proceed with the default structure (course-level narratives ordered by curriculum level).

## File format

The evaluations are administered by James Madison University; the specific survey questions (Q3–Q16) are defined by the CS department. Each CSV is one section. The **SubjectID column inside the CSV** is the authoritative identifier for the course-section (e.g., `CS149-0005`). Filenames are arbitrary — do not rely on them for course or section identification.

Columns (in order):

| Column | Meaning | Type |
|---|---|---|
| `SubjectID` | Course-section identifier, e.g. `CS149-0005` | string |
| `SecondarySubjectID` | Internal course key | int |
| `EnrollmentType` | Present only in Fall 2022+ exports | string |
| `FilloutDate` | Timestamp of submission | string |
| `Q3` … `Q12` | Ten Likert agreement items (see Scales) | numeric, or `D/A` |
| `Q13` | Instructor overall rating | 1–5 numeric, or `D/A` |
| `Q14` | Course overall rating | 1–5 numeric, or `D/A` |
| `Q15` | "What are the strengths of the instructor or course?" | free text |
| `Q16` | "How could the teaching of this course be improved?" | free text |
| `Unnamed: 17` or `Unnamed: 18` | Empty trailing column | ignore |

The `EnrollmentType` column is not used by the script; its presence or absence is the reliable indicator of which scale era the CSV belongs to (see Scales).

The Q3–Q12 wording is fixed; each column name contains the question text duplicated, like:
`Q3_The instructor taught clearly and stressed important points._The instructor taught clearly and stressed important points.`

The provided script renames these by substring match, so it stays robust if a future export reorders columns or tweaks wording slightly.

### Scales

The Q3–Q12 scale changed in Fall 2022. The script auto-detects which scale applies to each CSV by checking for the presence of the `EnrollmentType` column.

**Pre-Fall 2022 (old scale — no `EnrollmentType` column):**
- Q3–Q12 original: 1 = No Basis to Judge, 2 = Strongly Disagree, 3 = Somewhat Disagree, 4 = Somewhat Agree, 5 = Strongly Agree
- The script normalizes these by subtracting 1: old 2→1, 3→2, 4→3, 5→4. Old 1 (No Basis to Judge) becomes 0 and is excluded from means, just like D/A.
- After normalization, old-scale means are on the same 1–4 range as new-scale means and are directly comparable.
- The script labels these rows `1-4†` in the Scale column.

**Fall 2022 and later (new scale — `EnrollmentType` column present):**
- Q3–Q12: 1 = Strongly Disagree, 2 = Somewhat Disagree, 3 = Somewhat Agree, 4 = Strongly Agree. No adjustment needed.
- The script labels these rows `1-4` in the Scale column.

**Q13–Q14 (all eras):** 1 = Poor, 2 = Fair, 3 = Good, 4 = Very Good, 5 = Excellent. This scale did not change and requires no normalization.

After normalization, Q3–Q14 means are directly comparable across all time periods. The `†` label in the Scale column is a transparency marker — it tells the reader that those sections used the old survey form and their Q3–Q12 values were shifted. It is not a warning against comparison.

### Optional enrollment file

To include response rates, upload a JSON file (alongside the CSVs) mapping each section to its enrolled student count — what the JMU PDF report calls "Course Audience". Because SubjectIDs are not unique across terms, each key combines the term and SubjectID separated by a colon:

```json
{
  "Spring 2023:CS149-0001": 28,
  "Spring 2023:CS149-0002": 30,
  "Fall 2024:CS149-0005": 25,
  "Fall 2024:CS374-0002": 18
}
```

Keys not present in the file are silently skipped. Partial coverage is fine. When the file is present, both summary tables gain Enrolled and RR% columns, and each section's comment block is headed with its response rate. Sections below 40% are flagged with `!` in the tables and `*** LOW RESPONSE RATE ***` in the comment header.

### Other data notes

- **`D/A`** appears as a string in any quantitative column and means *Doesn't Apply* or *Decline to Answer*. It is excluded from means in all eras. A high D/A rate (≥30% on any item) is worth noting in the report.
- **Don't use absolute thresholds for "good" vs. "bad" means.** Surface signal *relatively*: flag the lowest 1–2 individual items per section, and any item that sits ≥0.3 below that section's own average.
- **Response rate**: N shown is respondents, not enrolled students. Without an enrollment file, flag small absolute N (below ~10) as a reliability caveat.

### Term auto-detection

The script derives each section's semester from the modal `FilloutDate` timestamp. Months 1–5 are Spring, 6–8 are Summer, 9–12 are Fall. If a section's timestamps are missing or unparseable, the script labels it "Unknown term" — ask the user how to label it before writing the report.

## Workflow

### 1. Read the inputs

Run the provided script to ingest all uploaded CSVs. First check whether a zip archive or JSON enrollment file was uploaded:

```bash
# Unzip archive if present (Mode B users may upload a zip due to the 20-file limit)
ZIP=$(ls /mnt/user-data/uploads/*.zip 2>/dev/null | head -1)
if [ -n "$ZIP" ]; then
    unzip -q "$ZIP" -d /tmp/evals_unzipped
    CSV_GLOB="/tmp/evals_unzipped/*.csv"
else
    CSV_GLOB="/mnt/user-data/uploads/*.csv"
fi

# Auto-detect enrollment file if present
ENROLLMENT=$(ls /mnt/user-data/uploads/*.json 2>/dev/null | head -1)
if [ -n "$ENROLLMENT" ]; then
    python scripts/parse_evaluations.py $CSV_GLOB --enrollment "$ENROLLMENT"
else
    python scripts/parse_evaluations.py $CSV_GLOB
fi
```

It prints three things to stdout:
- **Per-section means table** — one row per section with the auto-detected term, N, all Likert means rounded to 2 decimals, and overall ratings. When enrollment data is present, adds Enrolled and RR% columns and lists sections below 40% response rate. Use this in Mode A reports.
- **Per-course summary table** — one row per unique course (e.g., CS149), showing the term range taught (e.g., "Spring 2023 – Fall 2025"), number of sections, total N, weighted means for Q13 and Q14, and — when enrollment data is present — total enrolled and pooled response rate. Use this as the overview table in Mode B reports.
- **Free-text comments** — all Q15 (strengths) and Q16 (improvements) responses grouped by section. When enrollment data is present, each section header includes its response rate; sections below 40% are flagged prominently.

The script reads section identity from the SubjectID column inside each CSV — it does not use filenames. It sorts output chronologically by term, then by department prefix, course number, and section number.

If a column is missing, the script warns and skips that item rather than failing. If `FilloutDate` is missing or malformed, the term is reported as "Unknown term."

**For Mode B (large batches):** The script handles all files in one pass, but 30 CSVs produce a very large comment dump. Read the quantitative table first to build a map of courses and terms, then read comments grouped by course rather than top-to-bottom. This surfaces per-course trajectories more reliably than reading chronologically.

### 2. Read the comments yourself, fully

The quantitative table is the cheap part. **The themes are in the comments.** Read every Q15 and Q16 response before you start writing. Do not summarize section-by-section by skimming — you will miss cross-cutting themes that only become visible once you have all of it in mind at once.

While reading, hold these questions in mind:

- **What repeats?** A complaint from one student is noise. The same complaint from three is a pattern. The same complaint across multiple sections is a finding.
- **Is this about the teaching or the course design?** Students often blur these. The instructor can change how they teach; sometimes they can't change scheduling, room, time of day, or department policy. Tag the comment mentally as one or the other.
- **Is this about external constraints?** Class-period length, departmental curriculum, exam policies, tooling choices — flag these so the instructor knows what they can and can't act on.
- **What specifics are named?** Named tools, TAs, specific assignments, particular topics, pacing locations. These are far more actionable than generic feedback.
- **What's the experience-level mix?** Intro courses especially get split feedback because students arrive with different backgrounds. Watch for "too fast / too slow" appearing simultaneously — that's usually about student variance, not pacing.
- **Are comments attributing things to the instructor vs. the course?** Students sometimes praise the instructor while criticizing the course design. Keep that distinction alive as you read. Note that pedagogical methodology choices (e.g., active-learning structures, group work formats) are course-design decisions and fall within the permitted framing for both modes.
- **(Mode B only) What changed between terms?** Look for the same friction appearing in early terms and disappearing later, or new positives emerging after a likely course revision. That trajectory is the evidence.

### 3. Write the report

---

#### Mode A template — Formative / annual review

Keep prose tight; the instructor can ask follow-up questions for more detail.

```
# Course evaluation summary — <courses>, <term(s)>

<1-2 sentence framing: courses covered, term, scales in use, and whether
old-scale sections were normalized.>

## Quantitative snapshot

<Markdown table: one row per section, columns for N, each Likert mean,
and overall ratings. Bold Q13, Q14, and the 1–2 lowest-scoring Likert
items per section — these are what the instructor should notice first.
Omit the Scale column when all sections share the same scale; if old-
scale sections are present, note the normalization in the framing text
instead.>

<1–2 sentences on what the numbers show: flag the lowest items across
sections and any sections where N is small enough to warrant a caveat.
Skip obvious platitudes.>

## Per-course themes

### <Course> — <term> (N=<total>)

Group all sections of the same course taught in the same term under one
heading. Note the section IDs and individual Ns in the heading or opening
sentence. Within the block, discuss where sections agree and where they
diverge.

**Strengths:** 2–3 sentences synthesizing Q15. Name specific things
students valued.

**Improvements:** 2–4 sentences synthesizing Q16. Lead with items that
repeat. Distinguish teaching from course-design issues. A short sub-list
(3–4 items) is appropriate when improvements are highly specific and
numerous.

<Repeat for each course–term group.>

## Cross-cutting themes

<Only include if 2+ course–term groups were analyzed. This is the
highest-value part — the instructor can see individual section results in
the raw data; what they want is pattern recognition across them.>

**Things students consistently value.** <One short paragraph.>

**Recurring frictions.** <Numbered list of 3–5 themes. For each, name
which courses or sections raised it. Keep each item concrete and
actionable.>

**Unique signals worth noting.** <1–2 high-signal one-off observations
that don't repeat but are worth surfacing.>

<If all data is from a single term, close with one sentence flagging
this: "This report covers one semester; these patterns are worth watching
but should be confirmed across future terms before acting on them as
settled findings.">
```

The course summary table (second table from the script) is not useful in
single-term Mode A runs — skip it. Use it only when Mode A spans multiple
terms and the aggregated view adds something the per-section table doesn't.

End with a single offer of a follow-up (e.g., per-section action items, full comment listing, or thematic breakdown) — one line only.

---

#### Mode B template — Longitudinal review

The goal is a document the instructor can use as teaching evidence in a formal review — pre-tenure or promotion. Frame everything in terms of course content, rigor, assignments, and learning experiences — not instructor personality or interpersonal style.

The narrative should tell a coherent story: *this is what I teach, this is what students have said about it over time, and this is how I have responded.* Where the data shows a friction that later disappeared, or a strength that remained consistent, say so explicitly — that is the evidence.

```
# Teaching evidence from student feedback — <name>, <start year>–<end year>

<2–3 sentence framing: courses covered, number of sections and students,
time period. Note whether old-scale sections are present and that they
have been normalized to the current 1–4 scale. Acknowledge the
limitations of SET data (non-teaching factors, snapshot nature) so the
reader understands this is one source of evidence among many.>

## Overview

<Paste the per-course summary table produced by the script. It shows
number of terms, sections, total N, and weighted Q13/Q14 means for each
course. This gives the reader the full quantitative picture before the
narrative begins.>

<2–3 sentences on overall patterns: are scores consistent across the
period? Are there curriculum-level differences (intro vs. elective)
consistent with what the research predicts? Do not over-interpret.>

## Course-level narratives

One subsection per course, ordered by curriculum level (intro → core →
elective), then alphabetically within level. Each subsection covers the
full period for that course.

### <Course number and title> (<curriculum level>)

<1 sentence: how many terms, total N.>

**What students have consistently valued.** 2–3 sentences. Focus on
course content, assignment design, assessment practices, learning
experiences — not instructor warmth or personality. These are the
strengths the instructor has maintained.

**Frictions and how they evolved.** 2–4 sentences. Name the specific
issue, which terms it appeared, and — if it diminished or resolved —
what likely changed. If a friction persisted throughout the review
period without resolution, say so directly rather than implying change
that didn't occur. Distinguish course-design issues from things outside
the instructor's control.

**Notable trajectory.** 1–2 sentences if applicable. A consistent
improvement over time, a persistent unresolved issue, or a split that
reflects course-level structural factors (e.g., required intro course
for non-majors). Skip this sentence if there is no meaningful trajectory.

<Repeat for each course.>

## Patterns across the curriculum

<This section is the highest-value part of the longitudinal report. It
synthesizes across courses and connects student feedback to teaching
decisions. Keep it to 3–5 paragraphs.>

**Consistent strengths across courses.** What do students value
regardless of course level? Frame in terms of pedagogical practices:
assignment design, feedback quality, course structure, assessment
alignment — not personal traits.

**Evolution over the review period.** What changed? If specific frictions
appear in early terms and diminish later, describe that arc. Attribute
change to specific decisions where possible ("students noted the lab
manual was outdated in three consecutive terms; this friction does not
appear after [year]").

**Curriculum-level patterns.** Intro courses typically rate lower than
electives for reasons unrelated to teaching quality. Note this pattern if
present, and contextualize it — this is important framing for a review
committee that might otherwise compare intro and elective scores directly.

**What the data does not show.** Briefly acknowledge what SET data
cannot capture: student learning outcomes, contribution to curriculum
design, mentoring, or professional development. This section exists to
document one strand of evidence, not the whole teaching record.
```

End with a one-line note that raw section-level data and full comment listings are available on request.

---

## Judgment guidelines

These apply to both modes.

**Calibrate the numbers honestly, but don't overinterpret small differences.**
With N=12–24, a 0.1 gap between sections is meaningless and a 0.3 gap is suggestive at best. Report the means; don't rank sections by tiny differences. The exception is when *every item* in one section trends lower than another — that's a real pattern even if no single gap is large.

**Treat the lowest individual items as the highest signal.**
Bolding them in the table draws the eye; the prose should explain what they mean. A section with a 4.5 instructor rating and a 3.3 on Q11 (exams reflect objectives) is telling you something specific that the overall rating averages away. Always look at the lowest 2–3 individual items per section and connect them to the qualitative comments before writing the per-course themes.

**Contextualize against non-teaching factors.**
Research consistently shows that intro and required courses rate lower than upper-division electives independent of teaching quality; larger classes tend to rate lower than small ones; and grade expectations correlate with ratings. Before attributing a gap to teaching, note structural differences that could explain it. This is especially important in Mode B, where a review committee might compare intro and elective scores directly.

**Treat response rate as a reliability weight, not a score.**
When enrollment data is present, sections below 40% response rate are flagged in the script output. For those sections, be explicit in the report: note the rate, acknowledge that the comments may not represent the full class, and avoid presenting themes from low-response sections with the same confidence as themes from high-response ones. A section with N=8 out of 10 enrolled (80%) is very different from N=8 out of 30 enrolled (27%), even though both produce the same raw comment count. When response rates are unavailable, flag small absolute N (below ~10) as a reliability caveat instead.

**A single semester is a snapshot.**
Patterns that recur across two or more semesters — especially when supported by qualitative themes — are the findings worth acting on. One term's data is a starting point, not a verdict.

**Weight by repetition; surface negatives clearly but don't pile on.**
The signal is in how many students raise the same thing, not how much any one student wrote. A student who writes three paragraphs about one issue counts the same as a student who writes one sentence. If one detailed complaint is the only mention, label it as such ("one student raised…"). Surface negative themes directly — softening them defeats the point — but don't repeat the same criticism three different ways. State it once with specifics, note its frequency, and move on.

**Notice when complaints are mutually contradictory.**
"Lecture too fast" and "more lecture please" from different students is a real and unresolvable signal — usually about variance in student preparation. Naming the contradiction is more useful than pretending it doesn't exist.

**Don't paraphrase away the specifics.**
"Students wanted more help" loses information. "Students named the recursion unit in CS 149 as the week pacing fell apart" is actionable. Keep named tools, topics, assignments, and TAs in the report.

**Quote sparingly.**
At most one short direct quote per theme, only when the exact wording carries information that paraphrase would lose. Never more than ~15 words. Most content should be in your own words.

**Watch for high D/A rates.**
If many students chose D/A on Q7 (effective outside of class), they may not have interacted with the instructor outside class — that itself is information. Mention D/A rates only when notably high.

## Output format

The report renders as Markdown in the chat. **Do not** create a `.docx` file unless the user explicitly asks for one. **Do not** wrap the whole report in a code block.

Use one markdown table for the quantitative snapshot (Mode A) or overview table (Mode B). Beyond that, the report is prose with light section headers. Write per-course themes as paragraphs, not bullet lists. The recurring frictions list (Mode A) and curriculum-level patterns section (Mode B) are the places where a numbered list or structured paragraphs are appropriate.

## Example

The following is a *hypothetical* illustration of the target voice — not based on any real evaluation.

**Input:** Three CSVs uploaded: one Fall section of CS 149 (N=24), one Spring section of CS 149 (N=21), and one Spring section of CS 345 (N=16). All taught by the same instructor.

**Output excerpts illustrating the right voice:**

> Instructor overall sits at 4.5 in both CS 149 sections and 4.6 in CS 345; course overall lags at 3.9–4.1 in CS 149 but reaches 4.4 in CS 345. The consistent gap between instructor and course ratings in CS 149 points to course-design or materials issues rather than teaching problems — and is consistent with what intro required courses typically show.

> Across both CS 149 sections, the lowest individual item is Q11 (exams reflect objectives) at 3.2 and 3.3. Five students across the two sections described the exams as covering material that felt disconnected from the programming assignments. This is the clearest single signal in the dataset and sits squarely in assessment design, which the instructor can address.

> **CS 149 — Spring (Sections 0003 & 0004, N=45 combined).** Both sections valued the structured lab exercises and the pace of early lectures. The Fall section (0003) was warmer on assignment feedback turnaround than Spring (0004), where three students mentioned waiting more than a week for grades on larger projects. The gap is plausible given different section sizes but worth watching.

> **Pacing in the second half of the semester** — flagged in CS 149 Fall (four students) and CS 149 Spring (two students). In both cases students pointed to the recursion and linked-list units arriving in the same three-week stretch. No comparable pacing concern appeared in CS 345.

> **Group project structure was polarizing in CS 345.** Five students named the team project as the most valuable part of the course; three named it as the most frustrating. The frustration comments were specific: uneven contribution and no mechanism for peer accountability. The positive comments came from students who described their teams as self-organized. A structured peer-evaluation component might resolve most of the friction.

> One student in CS 149 Spring wrote that they had never written a program before and were now planning to major in CS. This kind of comment doesn't appear in the numbers and isn't a "theme" — but it's worth surfacing.

---

**Output excerpt illustrating Mode B voice** (same courses, now imagined across 5 years; Q3–Q12 values for pre-Fall 2022 sections are normalized to the current 1–4 scale):

> **CS 149 — Introduction to Programming (intro, required for CS majors).** Taught 9 times over the review period, total N=201. Q11 (exams reflect objectives) was the lowest-rated item in six of those nine terms, consistently in the 3.1–3.4 range through Spring 2022. Student comments in Q16 during that period describe the exams as emphasizing syntax recall over problem-solving, which did not match how the labs and assignments were structured. Q11 scores rise to 3.7–3.9 beginning Fall 2022 and comments about exam alignment largely disappear, suggesting a revision to assessment design. Assignment value (Q9) has remained among the highest-rated items throughout the review period, with students in nearly every term naming the weekly lab exercises as the most useful part of the course.

> CS 149 course overall averages 3.9 across the review period, lower than the instructor's upper-division scores. This is consistent with the pattern research identifies for required introductory courses serving students with wide variation in prior experience — it reflects course-level structural factors rather than differences in teaching quality.

Note the Mode B voice: it frames evidence in terms of assessment design and assignment structure; attributes a score change to a specific course revision; contextualizes the lower intro-course scores for a review committee; and stays entirely clear of language about instructor personality or style.
