---
name: course-evaluations
description: "Use this skill to analyze and summarize student course evaluations exported as CSVs — the kind James Madison University's Department of Computer Science sends instructors at the end of each term. Triggers on phrases like 'analyze my evaluations', 'summarize student feedback', 'what did students say about my course', or whenever the user uploads one or more CSV files containing student evaluation data with Likert and open-response columns. Also use when the user uploads evaluations spanning multiple semesters or a full promotion period and wants a longitudinal or comparative analysis. The output is a report the instructor can act on, not a generic data summary."
---

# Course evaluation analysis

## Why this skill exists

End-of-term evaluations land in instructors' inboxes as CSVs with awkward column names, mixed scales, and a pile of free-text comments. The naive output — "here's a table of means" — misses what the instructor actually wants: **what should I keep doing, and what should I change.** This skill produces a report oriented around that question, grounded in both the numbers and the qualitative comments.

One thing to hold in mind throughout: research on student evaluations of teaching (SET) consistently finds that ratings reflect more than teaching quality alone. Course level, whether a course is required, grade expectations, class size, and sometimes instructor demographics all affect scores in ways that have nothing to do with how well someone teaches. Treat the output as structured student feedback to act on — not as an objective measure of teaching effectiveness.

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

**Mode A — Formative / annual review** (3–6 CSVs, one semester or academic year): The instructor wants to understand what worked and what to improve. The report is for their own use or for an annual evaluation conference. No special framing constraints.

**Mode B — Promotion dossier** (~30 CSVs, 4–6 year period): The instructor wants to document teaching practices and growth over time as part of a promotion case. The report should surface longitudinal patterns — improvements made, what changed, what stayed consistent — and frame findings in terms of course content, rigor, assignments, and learning experiences, not instructor personality.

The time period is inferred from the CSV files themselves — the script's term auto-detection covers this. Before running the script in Mode B, ask the user:
1. Should the report be organized by course, by curriculum level (intro / core / elective), or both?
2. Are there specific courses or changes the instructor wants to highlight?

These answers shape the report structure before a single line is written.

## File format

Each CSV is one section. The **SubjectID column inside the CSV** is the authoritative identifier for the course-section (e.g., `CS149-0005`). Filenames are arbitrary — do not rely on them for course or section identification.

Columns (in order):

| Column | Meaning | Type |
|---|---|---|
| `SubjectID` | Course-section identifier, e.g. `CS149-0005` | string |
| `SecondarySubjectID` | Internal course key | int |
| `EnrollmentType` | Always "System" in practice | string |
| `FilloutDate` | Timestamp of submission | string |
| `Q3` … `Q12` | Ten Likert agreement items (see below) | 1–4 numeric, or `D/A` |
| `Q13` | Instructor overall rating | 1–5 numeric, or `D/A` |
| `Q14` | Course overall rating | 1–5 numeric, or `D/A` |
| `Q15` | "What are the strengths of the instructor or course?" | free text |
| `Q16` | "How could the teaching of this course be improved?" | free text |
| `Unnamed: 18` | Empty trailing column from the export | ignore |

The Q3–Q12 wording is fixed; each column name contains the question text duplicated, like:
`Q3_The instructor taught clearly and stressed important points._The instructor taught clearly and stressed important points.`

The provided script renames these by substring match, so it stays robust if a future export reorders columns or tweaks wording slightly.

### Scales

- **Q3–Q12 are 1–4 Likert agreement**: 1 = Strongly Disagree, 2 = Disagree, 3 = Agree, 4 = Strongly Agree. The scale has no neutral midpoint, so students who are merely "fine" must pick 3, which floors most means around 3.0+. The informative range is roughly 2.8–4.0.
- **Q13–Q14 are 1–5 overall ratings**: 1 = Poor, 2 = Fair, 3 = Good, 4 = Very Good, 5 = Excellent.
- **`D/A`** appears as a string in any quantitative column. It means *Doesn't Apply* or *Decline to Answer* — exclude from means. A high D/A rate (>30% on any item) is itself a signal worth noting.
- **NaN/empty** is common — a student can submit only Likert items or only narrative.
- **Response rate**: N shown is respondents, not enrolled students. If the user knows enrollment, note it — 10 out of 12 enrolled is very different from 10 out of 35. Response rates below ~50% reduce representativeness and are worth flagging as a caveat.

**Don't use absolute thresholds for "good" vs. "bad" means.** What counts as strong or weak depends on institutional and disciplinary norms. Instead, surface signal *relatively*: flag the lowest 1–2 individual items per section, and any item that sits ≥0.3 below that section's own average. That's what the instructor can act on.

### Term auto-detection

The script derives each section's semester from the modal `FilloutDate` timestamp. Months 1–5 are Spring, 6–8 are Summer, 9–12 are Fall. If a section's timestamps are missing or unparseable, the script labels it "Unknown term" — ask the user how to label it before writing the report.

## Workflow

### 1. Read the inputs

Run the provided script to ingest all uploaded CSVs at once:

```bash
python scripts/parse_evaluations.py /mnt/user-data/uploads/*.csv
```

It prints two things to stdout:
- A means table across all sections (one row per file) with the auto-detected term, N, all Likert means rounded to 2 decimals, and overall ratings.
- A grouped dump of all Q15 (strengths) and Q16 (improvements) free-text responses per section.

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
- **Are comments attributing things to the instructor vs. the course?** Students sometimes praise the instructor while criticizing the course design. Keep that distinction alive as you read.
- **(Mode B only) What changed between terms?** Look for the same friction appearing in early terms and disappearing later, or new positives emerging after a likely course revision. That trajectory is the evidence.

### 3. Write the report

---

#### Mode A template — Formative / annual review

Keep prose tight; the instructor can ask follow-up questions for more detail.

```
# Course evaluation summary — <courses>, <term(s)>

<1-2 sentence framing: who taught what, scales in use, how D/A was
handled, whether multiple sections share an instructor.>

## Quantitative snapshot

<Markdown table: one row per section, columns for N, each Likert mean,
and overall ratings. Bold the two overall-rating columns.>

<2–3 bullet observations from the numbers alone: flag the lowest-rated
items across sections; acknowledge sample size. Skip obvious platitudes.>

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
```

End with a single offer of a follow-up (e.g., per-section action items, full comment listing, or thematic breakdown) — one line only.

---

#### Mode B template — Promotion dossier

The goal is a document the instructor can use as teaching evidence in a promotion case. Frame everything in terms of course content, rigor, assignments, and learning experiences — not instructor personality or interpersonal style.

The narrative should tell a coherent story: *this is what I teach, this is what students have said about it over time, and this is how I have responded.* Where the data shows a friction that later disappeared, or a strength that remained consistent, say so explicitly — that is the evidence.

```
# Teaching evidence from student feedback — <name>, <start year>–<end year>

<2–3 sentence framing: courses covered, number of sections and students,
time period, scale conventions, how D/A was handled. Acknowledge the
limitations of SET data (non-teaching factors, snapshot nature) so the
reader understands this is one source of evidence among many.>

## Overview

<Quantitative summary table: one row per unique course (not per section),
showing number of terms offered, total N across all sections, and mean
Q13 (instructor overall) and Q14 (course overall) across all sections.
This gives the reader the full picture before the narrative begins.>

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
what likely changed. If a friction is ongoing, say so. Distinguish
course-design issues from things outside the instructor's control.

**Notable trajectory.** 1–2 sentences if applicable. A consistent
improvement over time, a persistent unresolved issue, or a split that
reflects course-level structural factors (e.g., required intro course
for non-majors). Skip this sentence if there is no meaningful trajectory.

<Repeat for each course.>

## Patterns across the curriculum

<This section is the highest-value part of the promotion report. It
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
present, and contextualize it — this is important framing for a promotion
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
A section with a 4.5 instructor rating and a 3.3 on Q11 (exams reflect objectives) is telling you something specific. The overall rating averages over everything; the individual items localize the issue. Always look at the lowest 2–3 individual items per section.

**Contextualize against non-teaching factors.**
Research consistently shows that intro and required courses rate lower than upper-division electives independent of teaching quality; larger classes tend to rate lower than small ones; and grade expectations correlate with ratings. Before attributing a gap to teaching, note structural differences that could explain it. This is especially important in Mode B, where a promotion committee might compare intro and elective scores directly.

**A single semester is a snapshot.**
Patterns that recur across two or more semesters — especially when supported by qualitative themes — are the findings worth acting on. One term's data is a starting point, not a verdict.

**Weight by repetition, not by length.**
A student who writes three paragraphs about one issue counts the same as a student who writes one sentence. The signal is in *how many students raise the same thing*. If one detailed complaint is the only mention, label it as such ("one student raised…") rather than presenting it as a theme.

**Do not sanitize, but also do not pile on.**
Surface negative themes clearly — softening them defeats the point — but don't repeat the same criticism three different ways. State it once with specifics, note its frequency, and move on.

**Notice when complaints are mutually contradictory.**
"Lecture too fast" and "more lecture please" from different students is a real and unresolvable signal — usually about variance in student preparation. Naming the contradiction is more useful than pretending it doesn't exist.

**Don't paraphrase away the specifics.**
"Students wanted more help" loses information. "Students named the recursion unit in CS 149 as the week pacing fell apart" is actionable. Keep named tools, topics, assignments, and TAs in the report.

**Quote sparingly.**
At most one short direct quote per theme, only when the exact wording carries information that paraphrase would lose. Never more than ~15 words. Most content should be in your own words.

**Watch for "course vs. instructor" attribution.**
When the instructor overall rating is notably higher than the course overall rating, that pattern usually means the criticism is about course design (assignments, exams, pacing, materials) rather than teaching. Call this out when it appears — it's particularly useful framing in a promotion report.

**Watch for high D/A rates.**
If many students chose D/A on Q7 (effective outside of class), they may not have interacted with the instructor outside class — that itself is information. Mention D/A rates only when notably high.

**Acknowledge anonymity.**
Don't speculate about which student wrote which comment. Don't try to infer demographics, grade level, or major from the writing.

## Output format

The report renders as Markdown in the chat. **Do not** create a `.docx` file unless the user explicitly asks for one. **Do not** wrap the whole report in a code block.

Use one markdown table for the quantitative snapshot (Mode A) or overview table (Mode B). Beyond that, the report is prose with light section headers. Write per-course themes as paragraphs, not bullet lists. The recurring frictions list (Mode A) and curriculum-level patterns section (Mode B) are the places where a numbered list or structured paragraphs are appropriate.

## Example

The following is a *hypothetical* illustration of the target voice — not based on any real evaluation.

**Input (Mode A):** Three CSVs uploaded: one Fall section of CS 149 (N=24), one Spring section of CS 149 (N=21), and one Spring section of CS 345 (N=16). All taught by the same instructor.

**Output excerpts illustrating the right voice:**

> Instructor overall sits at 4.5 in both CS 149 sections and 4.6 in CS 345; course overall lags at 3.9–4.1 in CS 149 but reaches 4.4 in CS 345. The consistent gap between instructor and course ratings in CS 149 points to course-design or materials issues rather than teaching problems — and is consistent with what intro required courses typically show.

> Across both CS 149 sections, the lowest individual item is Q11 (exams reflect objectives) at 3.2 and 3.3. Five students across the two sections described the exams as covering material that felt disconnected from the programming assignments. This is the clearest single signal in the dataset and sits squarely in assessment design, which the instructor can address.

> **CS 149 — Spring (Sections 0003 & 0004, N=45 combined).** Both sections valued the structured lab exercises and the pace of early lectures. The Fall section (0003) was warmer on assignment feedback turnaround than Spring (0004), where three students mentioned waiting more than a week for grades on larger projects. The gap is plausible given different section sizes but worth watching.

> **Pacing in the second half of the semester** — flagged in CS 149 Fall (four students) and CS 149 Spring (two students). In both cases students pointed to the recursion and linked-list units arriving in the same three-week stretch. No comparable pacing concern appeared in CS 345.

> **Group project structure was polarizing in CS 345.** Five students named the team project as the most valuable part of the course; three named it as the most frustrating. The frustration comments were specific: uneven contribution and no mechanism for peer accountability. The positive comments came from students who described their teams as self-organized. A structured peer-evaluation component might resolve most of the friction.

> One student in CS 149 Spring wrote that they had never written a program before and were now planning to major in CS. This kind of comment doesn't appear in the numbers and isn't a "theme" — but it's worth surfacing.

---

**Output excerpt illustrating Mode B voice** (same courses, now imagined across 5 years):

> **CS 149 — Introduction to Programming (intro, required for CS majors).** Taught 9 times over the review period, total N=201. Q11 (exams reflect objectives) was the lowest-rated item in six of those nine terms, consistently in the 3.1–3.4 range through Spring 2022. Student comments in Q16 during that period describe the exams as emphasizing syntax recall over problem-solving, which did not match how the labs and assignments were structured. Q11 scores rise to 3.7–3.9 beginning Fall 2022 and comments about exam alignment largely disappear, suggesting a revision to assessment design. Assignment value (Q9) has remained among the highest-rated items throughout the review period, with students in nearly every term naming the weekly lab exercises as the most useful part of the course.

> CS 149 course overall averages 3.9 across the review period, lower than the instructor's upper-division scores. This is consistent with the pattern research identifies for required introductory courses serving students with wide variation in prior experience — it reflects course-level structural factors rather than differences in teaching quality.

Note the Mode B voice: it frames evidence in terms of assessment design and assignment structure; attributes a score change to a specific course revision; contextualizes the lower intro-course scores for a promotion committee; and stays entirely clear of language about instructor personality or style.
