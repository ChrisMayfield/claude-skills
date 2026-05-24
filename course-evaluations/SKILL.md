---
name: course-evaluations
description: "Use this skill to analyze and summarize student course evaluations exported as CSVs — the kind universities send instructors at the end of each term. Triggers on phrases like 'analyze my evaluations', 'summarize student feedback', 'what did students say about my course', or whenever the user uploads one or more CSV files containing student evaluation data with Likert and open-response columns. Also use when the user uploads multiple semesters' worth of evaluations and wants a comparative read. The output is a report the instructor can act on, not a generic data summary."
---

# Course evaluation analysis

## Why this skill exists

End-of-term evaluations land in instructors' inboxes as CSVs with awkward column names, mixed scales, and a pile of free-text comments. The naive output — "here's a table of means" — misses what the instructor actually wants: **what should I keep doing, and what should I change.** This skill produces a report oriented around that question, grounded in both the numbers and the qualitative comments.

One thing to hold in mind throughout: research on student evaluations of teaching (SET) consistently finds that ratings reflect more than teaching quality alone. Course level, whether a course is required, grade expectations, class size, and sometimes instructor demographics all affect scores in ways that have nothing to do with how well someone teaches. Treat the output as structured student feedback to act on — not as an objective measure of teaching effectiveness.

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

The script reads section identity from the SubjectID column inside each CSV — it does not use filenames. It sorts output chronologically by term, then by department prefix, course number, and section number. **Preserve this order** in the report.

If a column is missing, the script warns and skips that item rather than failing. If `FilloutDate` is missing or malformed, the term is reported as "Unknown term."

### 2. Read the comments yourself, fully

The quantitative table is the cheap part. **The themes are in the comments.** Read every Q15 and Q16 response before you start writing. Do not summarize section-by-section by skimming — you will miss cross-cutting themes that only become visible once you have all of it in mind at once.

While reading, hold these questions in mind:

- **What repeats?** A complaint from one student is noise. The same complaint from three is a pattern. The same complaint across multiple sections is a finding.
- **Is this about the teaching or the course design?** Students often blur these. The instructor can change how they teach; sometimes they can't change scheduling, room, time of day, or department policy. Tag the comment mentally as one or the other.
- **Is this about external constraints?** Class-period length, departmental curriculum, exam policies, tooling choices — flag these so the instructor knows what they can and can't act on.
- **What specifics are named?** Named tools, TAs, specific assignments, particular topics, pacing locations ("the second half," "the Flask portion"). These are far more actionable than generic feedback.
- **What's the experience-level mix?** Intro courses especially get split feedback because students arrive with different backgrounds. Watch for "too fast / too slow" appearing simultaneously — that's usually about student variance, not pacing.
- **Are comments attributing things to the instructor vs. the course?** Students sometimes praise the instructor while criticizing the course design. Keep that distinction alive as you read.

### 3. Write the report

Use this structure. Adjust section depth to match how many courses were uploaded — a single-section analysis doesn't need a cross-cutting section. Keep prose tight; the instructor can ask follow-up questions for more detail.

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
the raw data; what they want from you is pattern recognition across them.>

**Things students consistently value.** <One short paragraph.>

**Recurring frictions.** <Numbered list of 3–5 themes. For each, name
which courses or sections raised it. Keep each item concrete and
actionable.>

**Unique signals worth noting.** <1–2 high-signal one-off observations
that don't repeat but are worth surfacing.>
```

End with a single offer of a follow-up (e.g., per-section action items, full comment listing, or thematic breakdown) — one line only.

## Judgment guidelines

These are what separate a useful report from a generic one.

**Calibrate the numbers honestly, but don't overinterpret small differences.**
With N=12–24, a 0.1 gap between sections is meaningless and a 0.3 gap is suggestive at best. Report the means; don't rank sections by tiny differences. The exception is when *every item* in one section trends lower than another — that's a real pattern even if no single gap is large.

**Treat the lowest individual items as the highest signal.**
A section with a 4.5 instructor rating and a 3.3 on Q11 (exams reflect objectives) is telling you something specific. The overall rating averages over everything; the individual items localize the issue. Always look at the lowest 2–3 individual items per section.

**Contextualize against non-teaching factors.**
Research consistently shows that intro and required courses rate lower than upper-division electives independent of teaching quality; larger classes tend to rate lower than small ones; and grade expectations correlate with ratings. Before attributing a gap to teaching, note structural differences that could explain it. This is especially important when comparing across courses or sections. If the same course taught the same way shows consistently lower scores than a peer's elective seminar, that gap is likely not the instructor's fault.

**A single semester is a snapshot.**
Patterns that recur across two or more semesters — especially when supported by qualitative themes — are the findings worth acting on. One term's data is a starting point, not a verdict.

**Weight by repetition, not by length.**
A student who writes three paragraphs about one issue counts the same as a student who writes one sentence. The signal is in *how many students raise the same thing*. If one detailed complaint is the only mention, label it as such ("one student raised…") rather than presenting it as a theme.

**Do not sanitize, but also do not pile on.**
Surface negative themes clearly — softening them defeats the point — but don't repeat the same criticism three different ways. State it once with specifics, note its frequency, and move on.

**Notice when complaints are mutually contradictory.**
"Lecture too fast" and "more lecture please" from different students is a real and unresolvable signal — usually about variance in student preparation. Naming the contradiction is more useful than pretending it doesn't exist.

**Don't paraphrase away the specifics.**
"Students wanted more help" loses information. "Students named the Flask-AppBuilder portion of CS 374 as the place pacing fell apart" is actionable. Keep named tools, topics, assignments, and TAs in the report.

**Quote sparingly.**
At most one short direct quote per theme, only when the exact wording carries information that paraphrase would lose. Never more than ~15 words. Most content should be in your own words.

**Watch for "course vs. instructor" attribution.**
When the instructor overall rating is notably higher than the course overall rating, that pattern usually means the criticism is about course design (assignments, exams, pacing, materials) rather than teaching. Call this out when it appears.

**Watch for high D/A rates.**
If many students chose D/A on Q7 (effective outside of class), they may not have interacted with the instructor outside class — that itself is information. Mention D/A rates only when notably high.

**Acknowledge anonymity.**
Don't speculate about which student wrote which comment. Don't try to infer demographics, grade level, or major from the writing.

## Output format

The report renders as Markdown in the chat. **Do not** create a `.docx` file unless the user explicitly asks for one. **Do not** wrap the whole report in a code block.

Use one markdown table for the quantitative snapshot. Beyond that, the report is prose with light section headers. Write per-course themes as paragraphs, not bullet lists. The cross-cutting recurring frictions section is the one place a numbered list is appropriate.

## Example

The following is a *hypothetical* illustration of the target voice — not based on any real evaluation.

**Input:** Three CSVs uploaded: one Fall section of BIO 101 (N=22), one Spring section of BIO 101 (N=19), and one Spring section of BIO 205 (N=14). All taught by the same instructor.

**Output excerpts illustrating the right voice:**

> Instructor overall sits at 4.6 in both BIO 101 sections and 4.4 in BIO 205; course overall lags at 4.0–4.2 across the board. The consistent gap between instructor and course ratings points to course-design or materials issues rather than teaching problems.

> Across both BIO 101 sections, the lowest individual item is Q10 (materials valuable) at 3.4 and 3.5. Four students named the lab manual specifically — "outdated," "doesn't match what we do in lab." This is the clearest single signal in the dataset.

> **BIO 101 — Spring (Sections 0003 & 0004, N=41 combined).** Both sections agree strongly on what worked: clear lecture structure, accessible office hours, and timely feedback on exams. The Fall section (0003) is slightly warmer on course materials than Spring (0004), but the gap is small given the sample sizes.

> **Pacing in the second half** — flagged in BIO 101 Fall (three students), BIO 101 Spring (two students), and once in BIO 205. In BIO 101 it's the cellular respiration unit; in BIO 205 it's the population genetics section.

> **Group work was polarizing in BIO 205.** Four students named group projects as the best part of the course; three named them as the worst. The split appears to be about *how groups were formed* — students who self-selected were positive; students assigned to groups were negative. A change to group-formation policy might resolve most of the friction.

> One student in BIO 101 Spring wrote that they came in afraid of biology and were leaving as a major. This kind of comment doesn't appear in the numbers and isn't a "theme" — but it's worth surfacing.

Note the voice: direct, specific, names exact units and assignments, distinguishes course-design issues from teaching, and weights findings by repetition across students and sections.
