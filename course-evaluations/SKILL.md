---
name: course-evaluations
description: "Use this skill to analyze and summarize student course evaluations exported as CSVs — the kind universities send instructors at the end of each term. Triggers on phrases like 'analyze my evaluations', 'summarize student feedback', 'what did students say about my course', or whenever the user uploads one or more files matching the pattern CSDEPT###-####.csv (e.g., CS149-0005.csv) with Q3–Q16 Likert and open-response columns. Also use when the user uploads multiple semesters' worth of evaluations and wants a comparative read. The output is a report the instructor can act on, not a generic data summary."
---

# Course evaluation analysis

## Why this skill exists

End-of-term evaluations land in instructors' inboxes as CSVs with awkward column names, mixed scales, and a pile of free-text comments. The naive output — "here's a table of means" — misses what the instructor actually wants: **what should I keep doing, and what should I change.** This skill produces a report oriented around that question, grounded in both the numbers and the qualitative comments, with cross-cutting themes when multiple sections are analyzed together.

## File format

Each CSV is one section. The filename pattern is typically `<course><section>.csv` — e.g., `CS149-0005.csv` is course CS 149, section 0005. One file per section means a course with two sections shows up as two files.

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

The Q3–Q12 wording is fixed and is each Q's column-name itself contains the question text duplicated, like:
`Q3_The instructor taught clearly and stressed important points._The instructor taught clearly and stressed important points.`

The provided script renames these by substring match, so it remains robust if a future export reorders columns or tweaks wording.

### Scales

- **Q3–Q12 are 1–4 Likert agreement**: 1 = Strongly Disagree, 2 = Disagree, 3 = Agree, 4 = Strongly Agree. The scale has no neutral midpoint, so students who are merely "fine, no complaints" must pick 3, which floors most means around 3.0+. The informative range is roughly 2.8–4.0.
- **Q13–Q14 are 1–5 overall ratings**: 1 = Poor, 2 = Fair, 3 = Good, 4 = Very Good, 5 = Excellent.
- **`D/A`** appears as a string in any quantitative column. It means *Doesn't Apply* or *Decline to Answer* — exclude from means, but a high rate (>30% on Q7 especially, the "outside of class" item) is itself a signal that students didn't engage with that aspect of the course.
- **NaN/empty** is common — a student can submit only Likert items or only narrative.

**Don't use absolute thresholds for "good" vs. "bad" means.** What counts as a strong or weak rating depends on institutional and disciplinary norms the skill doesn't have access to — a 3.6 on a 4-point scale might be unusually high at one institution and unremarkable at another. Instead, surface signal *relatively*: flag the lowest 1–2 individual items per section regardless of their absolute value, and note any item that sits notably below that section's own average (≥0.3 below is a useful rule of thumb). The "lowest items" pattern is what the instructor can act on; absolute "good/bad" labels without external norms are guesses dressed up as judgments.

### Term auto-detection

The script derives each section's semester from the modal `FilloutDate` timestamp — most submissions cluster at the end of the term they're for, so the modal month reliably identifies the semester. This means any mix of files from any number of semesters can be uploaded together and the report will group them correctly. Months 1–5 are Spring, 6–8 are Summer, 9–12 are Fall. If a section's timestamps are missing or unparseable, the script labels it "Unknown term" and you should ask the user before assuming.

## Workflow

### 1. Read the inputs

Run the provided script to ingest all uploaded CSVs at once:

```bash
python scripts/parse_evaluations.py /mnt/user-data/uploads/*.csv
```

It prints two things to stdout:
- A means table across all sections (one row per file) with the auto-detected term, N, all Likert means rounded to 2 decimals, and overall ratings flagged.
- A grouped dump of all Q15 (strengths) and Q16 (improvements) free-text responses per section, headed by both the section ID and the detected term.

The script sorts its output by term (chronologically: earlier semesters first), then by department prefix, then by course number, then by section number. **Preserve this order** in both the snapshot table and the per-course narrative — don't re-order sections by rating, file upload order, or perceived importance. Consistent ordering makes term-over-term comparisons readable.

Because the term is detected per-file, a single run can ingest evaluations from any combination of semesters, and the report should organize per-course themes by term so trends across semesters are visible.

If the user uploaded files with different naming conventions, the script still works — it parses each file independently. If a column it expects is missing, it warns and skips that item rather than failing. If `FilloutDate` is missing or malformed, the term is reported as "Unknown term" and you should ask the user how to label it before writing the report.

### 2. Read the comments yourself, fully

The quantitative table is the cheap part. **The themes are in the comments.** Read every Q15 and Q16 response before you start writing. Do not summarize section-by-section by skimming — you will miss cross-cutting themes that only become visible once you have all of it in your head at once.

While reading, hold these questions in mind:

- **What repeats?** A complaint from one student is noise. The same complaint from three is a pattern. The same complaint across multiple sections is a finding.
- **Is this about the teaching or about the course design?** Students often blur these. The instructor can change the course; sometimes they can't change scheduling, room, time of day, or department policy. Tag the comment mentally as one or the other.
- **Is this about external constraints?** Class-period length, departmental curriculum, exam-on-paper policies, tooling choices (Gradescope, Canvas, Piazza) — flag these as such so the instructor knows what they can and can't act on.
- **What specifics are named?** Capture concrete nouns: named tools, named TAs, specific assignments, particular topics, specific pacing locations ("the second half," "the Flask portion"). These are far more actionable than generic feedback.
- **What's the experience-level mix?** Intro courses especially get split feedback because students arrive with different backgrounds. Watch for "too fast / too slow" appearing simultaneously.

### 3. Write the report

Use this structure. Adjust section depth to match how many courses were uploaded — a single-section analysis doesn't need a cross-cutting section.

```
# Course evaluation summary — <courses>, <term(s)>

<1-2 sentence framing: who taught what, what scales are in use,
how D/A was handled, whether multiple sections share an instructor.>

## Quantitative snapshot

<Markdown table: one row per section, columns for N, each Likert mean,
and overall ratings. Bold the two overall-rating columns so they stand
out. Highlight the lowest 2–3 individual means in the discussion below
the table, not by coloring the table itself.>

<Below the table: 2–4 bullet observations from the numbers alone.
Mention the lowest-rated items across sections, not just the lowest
section. Acknowledge sample size — these are small Ns.>

## Per-course themes

### <Course-section> (<term>) — N=<N>
**Strengths:** <prose paragraph synthesizing Q15 — not a bullet list of
every comment. Name specific things students valued. 3–5 sentences.>

**Improvements:** <prose paragraph synthesizing Q16. Lead with the
items that repeat. Distinguish teaching from course-design issues.
Note when something is an external constraint. 3–6 sentences. If a
detailed comment is particularly actionable, you can use a short
sub-list of 3–4 items.>

<Repeat for each section.>

## Cross-cutting themes

<Only include this section if 2+ sections were uploaded. This is the
highest-value part of the report — the instructor can see individual
section results in the raw data; what they want from you is pattern
recognition across sections.>

**Things students consistently value.** <One paragraph.>

**Recurring frictions.** <Numbered list of 3–6 themes that appear in
multiple sections. For each, name which sections raised it. Keep each
item concrete and actionable.>

**Unique signals worth noting.** <Any one-off but high-signal comments
that don't repeat but are worth surfacing — e.g., a student explicitly
comparing the instructor favorably to peers, or naming a specific
policy issue.>
```

End with one short offer of a follow-up — e.g., per-section action items, or a thematic spreadsheet of all comments — but no more than one line. Do not ask multiple follow-up questions.

## Judgment guidelines

These are the things that separate a useful report from a generic one. Internalize them before writing.

**Calibrate the numbers honestly, but don't overinterpret small differences.**
With N=12–24, a 0.1 gap between sections is meaningless and a 0.3 gap is suggestive at best. Report the means; don't rank sections by tiny differences. The exception is when *every item* in one section trends lower than another — that's a real pattern even if no single gap is large.

**Treat the lowest individual items as the highest signal.**
A section with a 4.5 instructor rating and a 3.3 on Q11 (exams reflect objectives) is telling you something specific. The overall rating averages over everything; the individual items localize the issue. Always look at the lowest 2–3 individual items per section.

**Weight by repetition, not by length.**
A student who writes three paragraphs about one issue counts the same as a student who writes one line. The signal is in *how many students raise the same thing*, not in how vehemently any one student writes about it. If one detailed complaint is the only mention of an issue, label it as such ("one student raised…") rather than presenting it as a theme.

**Do not sanitize, but also do not pile on.**
Instructors are looking at their own teaching evaluations. Surface negative themes clearly — softening them defeats the point — but don't repeat the same criticism three different ways. State it once with specifics, note its frequency, and move on.

**Notice when complaints are mutually contradictory.**
"Lecture too fast" + "more lecture please" from different students is a real and unresolvable signal — usually about variance in student preparation. Naming the contradiction is more useful than pretending it doesn't exist.

**Don't paraphrase away the specifics.**
"Students wanted more help" loses information. "Students named the Flask-AppBuilder portion of CS 374 as the place pacing fell apart" is actionable. Keep named tools, topics, assignments, and TAs in the report.

**Quote sparingly.**
At most one short direct quote per theme, only when the exact wording carries information that paraphrase would lose. Most content should be in your own words. Never quote more than ~15 words at a time.

**Watch for "course vs. instructor" attribution.**
Students sometimes praise the instructor while criticizing the course, or vice versa. When the instructor overall rating is much higher than the course overall rating, that pattern is meaningful: it usually means the criticism is about course design (assignments, exams, pacing, materials) rather than teaching. Call this out when it appears.

**Watch for high D/A rates.**
If many students chose D/A on Q7 (effective outside of class), they may not have ever interacted with the instructor outside of class — that itself is information, separate from the mean of the students who did respond. Mention D/A rates only when they're notably high.

**Acknowledge anonymity.**
Don't speculate about which student wrote which comment. Don't try to infer demographics, grade level, or major from the writing. Each response stands on its own.

## Output format

The report should render as Markdown in the chat. **Do not** create a .docx file unless the user explicitly asks for one — instructors typically want to read this inline, not download it. **Do not** wrap the whole report in a code block.

Use the one markdown table for the quantitative snapshot. Beyond that, the report is prose with light section headers. Avoid bullet-pointing the per-course themes — write them as paragraphs. The cross-cutting recurring frictions section is the one place a numbered list is appropriate, because it's a list of distinct items.

## Example

The following is a *hypothetical* illustration of the target voice — not based on any real evaluation.

**Input:** Three CSVs uploaded together: `BIO101-0003.csv` (Fall, N=22), `BIO101-0004.csv` (Spring, N=19), and `BIO205-0001.csv` (Spring, N=14). All taught by the same instructor.

**Output excerpts illustrating the right voice:**

> Instructor overall sits at 4.6 in both BIO 101 sections and 4.4 in BIO 205; course overall lags slightly at 4.0–4.2 across the board. The gap between instructor and course ratings is consistent and worth noting — students rate the teaching itself higher than the course as a whole, which usually points to course-design or materials issues rather than teaching problems.

> Across both BIO 101 sections, the lowest individual item is Q10 (materials valuable) at 3.4 and 3.5. In the comments, four students named the lab manual specifically — "outdated," "doesn't match what we do in lab," "hard to follow before Wednesday's session." This is the clearest single signal in the dataset and is probably the highest-leverage thing to change.

> **Pacing in the second half of the semester** — flagged in BIO101-0003 (three students), BIO101-0004 (two students), and once in BIO 205. The specific complaint differs by course: in BIO 101 it's the cellular respiration unit, in BIO 205 it's the population genetics section. Worth re-examining the time allocation for those units.

> **Group work was polarizing in BIO 205.** Four students named group projects as the best part of the course; three named them as the worst. The split appears to be about *how groups were formed* rather than the concept — students who self-selected groups were positive; students assigned to groups were negative. A change to group-formation policy might resolve most of the friction without dropping the project.

> One student in BIO101-0004 wrote: "I came in afraid of biology and am leaving as a major." This kind of comment doesn't appear in the numbers and isn't a "theme" — but it's worth surfacing as a unique signal.

Note the voice: direct, specific, names exact units and assignments, distinguishes course-design issues from teaching, acknowledges trade-offs, and weights findings by how often they repeat across students and sections. That's the target.
