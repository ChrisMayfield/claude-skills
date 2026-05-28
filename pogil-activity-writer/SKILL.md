---
name: pogil-activity-writer
description: Collaboratively author Process Oriented Guided Inquiry Learning (POGIL) classroom activities — structured worksheets that guide student teams through a model, questions, and application. Use this skill whenever the user asks to create or draft a POGIL activity, guided inquiry worksheet, learning cycle activity, or any classroom activity following the POGIL methodology — even if they don't explicitly say "POGIL." Trigger on requests like "write a POGIL activity on photosynthesis," "make a learning cycle activity on [topic]," or "help me design an inquiry-based lesson on X." Users sometimes say "write a POGIL" as shorthand — recognize the request, but call drafts "this activity," not "your POGIL activity"; POGIL® is The POGIL Project's mark for endorsed materials only. The skill walks the user through backward design and produces two Markdown files — a teacher version with inline sample answers and facilitation notes, and a student version with writing space.
---

# POGIL Activity Writer

## What POGIL is, briefly

POGIL is a student-centered pedagogy in which small teams of students work through a specially designed activity during class while the instructor facilitates rather than lectures. Activities that follow POGIL pedagogy have three defining features:

1. **Team-based and instructor-facilitated.** Designed for self-managed teams of 3–4 students; the instructor is a facilitator, not a source of information.
2. **Guided exploration.** Students construct understanding by working through a model (data, diagram, text, equation, code, etc.) and a sequence of questions. They are not told the concept up front.
3. **Embedded process skills.** The activity is designed to develop at least one targeted process skill (e.g., critical thinking, teamwork, information processing) through the structure of the questions themselves — not solely through what the instructor does in the room.

A typical 45–50 minute activity contains 2–3 **Learning Cycles**. Each Learning Cycle has the same shape:

- **Exploration:** Students examine a model and answer short, directed questions about what they observe.
- **Concept Invention:** A key question prompts the team to articulate the underlying pattern or concept in their own words. Terminology is introduced *here*, not before.
- **Application:** Students apply the new concept to a fresh case to consolidate it.

## About the POGIL trademark

POGIL® is a registered trademark of The POGIL Project. The mark is used for activities and materials that have been reviewed and endorsed by The POGIL Project; drafts produced by this skill are **not** POGIL activities. They are guided inquiry activities written following POGIL pedagogical guidelines, with the expectation that an author may submit them to The POGIL Project for peer review and possible endorsement (see https://pogil.org).

This shapes how Claude talks about the work, in three places:

- **In the activity itself** (title, Why?, model descriptions, question text — any prose Claude writes into the deliverable): never use the word POGIL. Use neutral terms like *"this activity"* or *"this guided inquiry activity."* A good title is topic-focused (e.g., *"Enzyme Kinetics: How Does Reaction Rate Depend on Substrate?"*), never something like *"POGIL Activity: Enzyme Kinetics."*
- **In conversation with the user** while drafting: refer to the draft as *"your activity,"* *"this learning cycle activity,"* or similar — not *"your POGIL activity."* It is fine if the user uses the shorthand themselves; Claude just doesn't echo it back.
- **In filenames**: just the topic slug and the role suffix. No "pogil" or "activity" in the filename (this is a trademark requirement, not an aesthetic one).

Reserve the phrase *"POGIL activity"* for materials that have actually been endorsed by The POGIL Project.

## How to use this skill

Activities that follow POGIL pedagogy are written by **backward design** — start from what students should be able to do at the end, and work backward to the model. When invoked, walk the user through the workflow below conversationally. Don't try to one-shot the whole activity from a one-line prompt. Each step is a small conversation: propose, get feedback, refine, then move on.

If the user's initial request is vague ("help me write a POGIL activity"), start with Step 0. If they've given a clear topic and audience ("write a POGIL activity on Newton's third law for intro physics"), still walk through the steps but move briskly through ones where the answer is obvious from context. Skipping the elicitation step entirely produces generic activities that don't fit any real classroom — the conversation is the point.

A note on pace: the user is an instructor with real expertise in their subject. Treat them as a content expert and yourself as the structural expert. Propose objectives, models, and questions; let them correct your subject-matter assumptions and push back on questions that are too easy, too hard, or wrong for their students.

## The workflow

### Step 0 — Topic and context

Before writing anything, find out:

- **Topic:** What concept(s) should the activity teach?
- **Course and level:** What course is this for? Intro? Upper-level? What grade band?
- **Class length:** How long is a class period? (Default: 45–50 minutes, 2–3 learning cycles.)
- **Activity type:** Learning Cycle (introducing a new concept) or Application (deepening prior knowledge)? Default to Learning Cycle.
- **Prior context:** What have students already covered? What comes next?

Don't ask all of these at once if most are clear from the request. Just fill in the gaps.

### Step 1 — Content learning objectives

Propose 1–3 content learning objectives. More than 3 won't fit a typical class period and will overload student cognitive processing. A good content learning objective:

- Uses an **observable action verb** ("identify," "predict," "compare," "explain in words and in a diagram," "calculate," "classify") — not vague terms like "know" or "understand."
- Is **specific** and **measurable** — you could tell whether a student met it.
- Is **achievable** given the students' prerequisite knowledge.
- Is **learner-centered** — describes what the student will do, not what the instructor will cover.

Examples of good content learning objectives:
- "Students will predict the products of a single-replacement reaction given the activity series."
- "Students will compare the use of bond enthalpies and heats of formation to calculate a heat of reaction."
- "Students will describe in words and in a diagram how the valves in the heart control the one-way flow of blood."

Propose objectives, then ask the user to confirm, edit, or add their own.

### Step 2 — Process skill goals

Choose 1–2 process skills the activity will explicitly develop. Every well-designed guided inquiry activity exercises process skills implicitly, but a strong activity targets one or two *by design* — meaning the structure of the questions develops the skill, not just classroom facilitation.

The seven canonical process skills identified by The POGIL Project:

- **Teamwork** — Interacting with others and building on individual strengths toward a common goal.
- **Oral and Written Communication** — Conveying information through speech or writing.
- **Management** — Planning, organizing, directing, and coordinating effort.
- **Problem Solving** — Analyzing a complex situation, developing a strategy, and executing it.
- **Information Processing** — Evaluating, interpreting, manipulating, or transforming information.
- **Critical Thinking** — Forming an argument or conclusion supported by evidence.
- **Self/Peer Assessment** — Reflecting on experience to improve next time.

**Metacognition** is also commonly targeted. Other field-specific process skills are valid too (e.g., "making order-of-magnitude estimates").

Process skill goals are written like content objectives but emphasize improvement in the skill itself, often naming the question or section where it develops:

- "Students will evaluate information in Model 2 to determine what is irrelevant (Information Processing)."
- "Students will identify which mathematical function best fits the data in Model 3 (Critical Thinking)."
- "Students will divide work fairly to complete Question 7 (Management)."

Propose process skills that fit the topic naturally and confirm with the user.

### Step 3 — Prerequisite knowledge

What must students already know to do this activity? List:

- Specific concepts and skills they need.
- Any reading or assignments expected before or after the activity.

For Learning Cycle activities, textbook reading on the topic should typically come **after** the activity — the whole point is for students to construct the concept themselves before encountering it formalized in a text.

### Step 4 — Application questions (work backward!)

This is where backward design earns its name. Before designing the model or writing exploration questions, **write the application questions first** — the questions at the end of each learning cycle that test whether students reached the objective.

Each learning cycle needs at least one application question. These typically:

- Apply the just-developed concept to a new case (different numbers, different context, different example).
- Are answerable directly from the concept the student just invented.
- Often serve double duty: the application of one cycle can be the exploration for the next.

Draft 1–2 application questions per learning objective and check with the user before continuing. If you can't write a clear application question, the learning objective is probably too vague — go back and tighten it.

### Step 5 — Key (concept invention) question

For each learning cycle, write the **key question** — the moment where students articulate the new insight in their own words. This is often the last question before the application step. It often looks like:

- "Based on your answers to questions 1–4, write a rule that predicts ___."
- "In one sentence, explain why ___."
- "Complete the following statement: A reaction is exothermic when ___."

The key question is where **new terminology is introduced**, not assumed. If the activity is teaching "exothermic," that exact word should not appear in the model or earlier questions — only in or after the key question.

### Step 6 — Design the model

Now design the model — the artifact students will explore. A model can be:

- A diagram, figure, table, or graph
- A worked example or sequence of examples
- A short text passage
- An equation or set of equations
- A code snippet, algorithm, or program output
- A photo, screenshot, or simulation output
- Some combination of these

A good model:

- **Fits on approximately one printed page.** A model that spills onto a second page is too much — students lose the thread between the data and the questions. If the model is growing large, split it across two learning cycles rather than cramming it into one.
- **Contains only what students need for this learning cycle.** Don't include tables, columns, schema elements, or data that aren't referenced until a later model. Presenting unused material creates noise and signals to students that they're supposed to use it — which sends them down dead ends. Each model should be self-contained: everything in it is needed, and nothing in it is extra.
- **Provides enough exemplars for inference.** A single example is rarely enough for students to spot a pattern. 3–5 contrasting cases is common. Show variation along the dimension that matters — and ideally, include cases that are similar in irrelevant ways so students have to identify the right feature.
- **Uses standard representations** for the field.
- **Is clear, concise, and visually clean.** No distracting information.
- **Does not state the concept being developed.** In a Learning Cycle activity, the model shows the evidence for the concept, not the concept itself.
- **Is engaging.** Real-world context, relevant data, or a surprising contrast helps.

Describe the model concretely. If it's a table, write the table out in Markdown. If it's code or data, include the code or data inline.

For diagrams and charts, prefer **Mermaid** code blocks (` ```mermaid ... ``` `) — they render natively in GitHub, VS Code (with the standard Markdown preview), and most modern Markdown viewers, so the diagram lives in the document itself rather than requiring the author to draw it separately. Mermaid supports over two dozen diagram types — flowcharts, state machines, sequence diagrams, class and ER diagrams, xy/bar/pie charts, timelines, and mindmaps are common examples; consult the Mermaid documentation for the full list and current syntax.

Fall back to prose description (detailed enough that the author could draw the figure) only when the diagram is outside what Mermaid can express well — e.g., labeled anatomical figures, electrical circuits, free-form scientific schematics, photographs, or charts with custom annotations. For an ASCII sketch (as in the rate-vs-[S] curve sketch in the enzyme kinetics example), a fenced code block is fine.

### Step 7 — Concept invention questions

These questions bridge the gap between the model and the key question. They:

- Start from observations in the model.
- Lead students toward the pattern they need to see.
- Often use prediction: "Predict whether reaction C will be exothermic. Then look at the value in Model 1 — were you correct? If not, what does your team need to revise about the rule you proposed?"
- Increase in difficulty across the sequence.

A common failure mode is asking students to just restate something they can read directly off the model. A better invention question asks them to **compare**, **infer**, **predict**, or **explain why** — operations that require putting the observations together.

### Step 8 — Exploration questions

These are the early questions in the sequence — short, directed, easy to answer by reading the model or applying prior knowledge. They orient the team to the model and surface the key features they'll need later.

Examples:
- "In Model 1, what units are used for energy?"
- "Which of the three reactions in Model 1 releases the most energy?"
- "Which atoms in the structure of glucose are involved in the bond shown in red?"

Aim for 2–4 exploration questions per model. They should be answerable in under a minute each. Roughly 3–10 total questions per model is a healthy range across exploration + invention + application.

### A critical point about Exploration / Invention / Application

These three categories are **a design frame for the author, not document structure for the student.** Do **not** label question groups as "Exploration" / "Concept Invention" / "Application" in the activity itself. The student sees a single numbered list of questions under each model.

Two reasons this matters:

1. Labels signal too much to the student about each question's role. The whole pedagogical move is that a student answers a directed question, then a comparing question, then a key question — and the realization that "we just discovered something" emerges from doing the work, not from a header announcing it.
2. Real activities don't follow strict E → CI → A order. A team may need an exploration-style question (a quick lookup from the model) in the *middle* of the invention sequence — e.g., after attempting an inference, you might point them to another row of the table they hadn't noticed. The author thinks in the three categories; the question sequence weaves them.

So as you draft, think of Steps 6–8 as design *checks* — does my sequence include enough orienting questions early, build inferential momentum, and end with a clear key + application? — not as document sections to write separately.

### Step 9 — Sample answers (inline)

For every question in the activity, write a sample answer **from the perspective of a student team**, not an expert. Place the answer **directly under the question it answers**, formatted as a Markdown blockquote with a bold-italic ***Sample:*** label followed by a `<br>` tag, and follow every question with an indented `&nbsp;` line as trailing breathing room (full details in the Output format section's convention #3). This is the format:

```markdown
3. As [S] increases from 20 mM to 100 mM, by roughly what factor does the rate increase?
   > ***Sample:***<br>About 1.15×. Rate goes from 33.3 to 38.5 — barely any change despite the big jump in [S].

   &nbsp;

4. The next question goes here.
   > ***Sample:***<br>Its answer goes here.
```

Inline placement matters: it lets the author (and any reviewer) read each question and its expected answer together, which is the fastest way to catch a question that is unclear, too hard, or misaimed. A traditional answer key in a separate section forces the reader to flip back and forth and loses this benefit.

Student-team answers:
- **Must be correct.** Sample answers often end up distributed to students as answer keys, so accuracy matters directly. They also matter during review: if a sample answer is wrong, the author reviewing the activity will think the *question* is broken when it isn't. Never write a deliberately wrong answer to model a misconception. Misconceptions belong in the Facilitation Notes section at the end of the document, where they are labeled as such and accompanied by probing questions for the instructor to ask.
- May use informal or incomplete phrasing — the goal is to show a credible student-team articulation, not an expert's polished version. "Rate stops going up" is a fine team answer; "rate asymptotically approaches Vmax" is not.
- For divergent questions, include "(variation expected)" before the sample and give one plausible correct version. If multiple substantively different correct answers exist, list them.

### Step 10 — Review and refine

Walk through this checklist with the user before finalizing:

- Does each learning cycle's question sequence cover all three phases (orient to the model → drive inference → apply the new concept)? Note: these are design phases the author checks for, **not** headings in the document.
- Are concepts introduced *only after* students invent them (not pre-named in the model or in early questions)?
- Is the model rich enough to support the inference it asks for? Does it vary along the dimension the concept hinges on, with enough cases to make a pattern visible? (Single examples rarely work.)
- Are the early, orienting questions short and directed?
- Are the inferential questions truly inferential — requiring students to compare, predict, or explain — not just observational?
- Is at least one process skill developed by the *structure* of the questions, not just by facilitation?
- Can a team of 3–4 students plausibly finish the in-class questions in the allotted time?
- Are there 2+ exercises per content objective for practice after class?

Offer to revise any section based on the review.

### Step 11 — Generate the student version

Once the user has accepted the activity, write the Teacher file to `/mnt/user-data/outputs/<topic-slug>_Teacher.md` (see the Output format section below for naming rules), then run the bundled script to produce the Student file:

```bash
python scripts/generate_student_version.py /mnt/user-data/outputs/<topic-slug>_Teacher.md
```

The script writes the Student file alongside the Teacher file, with `_Teacher.md` replaced by `_Student.md`. It performs four deterministic transformations on the Teacher file:

1. Drops the entire `# Facilitation Notes` section.
2. Replaces every `> ***Sample:***` block with vertical writing space — a series of indented `&nbsp;` lines, **proportional to the sample answer's total length** (roughly one writing line per ~70 characters, with a floor of 2 lines and a ceiling of 8 lines). A sample block may span multiple consecutive `> ` lines (e.g., a query result on a second line); all are consumed. Both `***Sample:***<br>` and legacy `***Sample:*** ` forms are recognised.
3. Removes the redundant `&nbsp;` separator that followed each sample answer (since the writing space now serves that role).
4. Inserts a blank line between the question text and the first `&nbsp;` writing line, so the writing space is visually separated from the question.

Everything else is preserved verbatim. Do not try to produce the Student file by paraphrasing the Teacher file — always invoke the script, since it ensures the two files stay in sync. After the script runs, call `present_files` with both filepaths, Teacher first.

## Output format

Two Markdown files in `/mnt/user-data/outputs/`:

- `<topic-slug>_Teacher.md` — the authoring/review version. Sample answers inline, facilitation notes at the end. Written by Claude.
- `<topic-slug>_Student.md` — the student-facing version. Proportional writing space in place of answers, facilitation notes removed. Generated by the bundled script.

`<topic-slug>` is a short kebab-case version of the topic (e.g., `enzyme-kinetics`, `valence-electrons`, `for-loops`). The filenames must **not** include the words "pogil" or "activity" — just the topic slug, an underscore, and the role suffix. (This is a trademark requirement; see the "About the POGIL trademark" section above.)

Four formatting conventions for the Teacher version (the script handles the Student version automatically):

1. **No question-category headings.** Under each model is a single numbered list of questions — no `### Exploration` / `### Concept invention` / `### Application` subheadings. (See the "*A critical point about Exploration / Invention / Application*" subsection earlier for why.)
2. **Sample answers inline, bold-italic label with line break.** Every question is followed immediately by its sample answer, formatted as a blockquote with a ***Sample:*** label (bold + italic) and a `<br>` tag so the answer text starts on its own line:

   ```
   3. Question text here?
      > ***Sample:***<br>Student-team-voice answer here.
   ```

3. **Vertical breathing room after every question.** The `&nbsp;` separator belongs to the question above it (it is the question's trailing breathing room), not to the gap between questions. Indent it to match the indentation of the question's content — 3 spaces under a top-level `1.` item; 7 spaces under a sub-item like `    a.`. This rule applies to **every** numbered item, including the last question of each model (before the next `## Model` heading) and the last exercise (before `## Problem`). Also insert an un-indented `&nbsp;` between each model's content (table, diagram, code block, etc.) and the first question, so the questions are visually set apart from the model they reference.
4. **No `---` horizontal rules between sections.** Use a standalone `&nbsp;` line instead. VS Code and GitHub already render a horizontal rule visually after level-1 and level-2 headings, so an explicit `---` produces a doubled rule that hurts readability. The `&nbsp;` just inserts a blank line of breathing room.

Here is the Teacher template:

```markdown
# [Activity Title — topic-focused; do not include the word "POGIL"]

## Why?
[1–3 sentences motivating the activity for students. Connects to what they've learned
and what's coming. Optional — instructors often provide this aloud at the start of class.]

## Prerequisites
- [Prior knowledge / skills students need]
- [Reading or assignments expected before/after]

## Learning Objectives

**Content:**
- [Objective 1]
- [Objective 2]

**Process:**
- [Process skill goal 1 with category in parentheses]

&nbsp;

## Model 1: [Descriptive title]

[The model itself — table, diagram description, text, code, etc.]

&nbsp;

1. [First question — typically a short directed question that orients the team to the model]
   > ***Sample:***<br>[Student-team-voice answer.]

   &nbsp;

2. [Next question — could be another orienting question, or could be an inference depending on what the sequence needs]
   > ***Sample:***<br>[Answer.]

   &nbsp;

3. [Continue sequencing — let the questions follow the natural arc from observation toward the concept, weaving in further orienting questions if a team needs to look at a specific feature mid-sequence]
   > ***Sample:***<br>[Answer.]

   &nbsp;

4. [The key question — often phrased as "in your own words, describe…" or "complete this statement…". This is where new terminology gets introduced or articulated.]
   > ***Sample:***<br>[Answer; for open phrasing, note "(variation expected)" and give one plausible version.]

   &nbsp;

5. [Application question — apply the just-developed concept to a fresh case.]
   > ***Sample:***<br>[Answer with the justification students should give.]

   &nbsp;

## Model 2: [Descriptive title]

[Repeat the inline-answer structure for each learning cycle. Typically 2–3 cycles total per 45–50 minute class.]

   &nbsp;

## Exercises

[2+ per content objective. Variations on the application questions for practice after class. Use the same inline-answer format with `&nbsp;` separators between items.]

1. [Exercise]
   > ***Sample:***<br>[Answer.]

   &nbsp;

2. [Exercise]
   > ***Sample:***<br>[Answer.]

   &nbsp;

## Problem (optional)

[A higher-order problem distinct from exercises — student doesn't immediately know what to do, may integrate multiple concepts, may sit in a real-world context.]

> ***Sample:***<br>[Answer, possibly with multiple acceptable approaches noted.]

&nbsp;

# Facilitation Notes

## Overview
- **Suggested time:** [breakdown by model]
- **Suggested team roles:** [Manager, Recorder, Presenter, Reflector — or context-specific]
- **What to watch for at the classroom level:** [high-level summary]

## Per-model notes

### Model 1
- [What teams might get stuck on]
- [Common misconceptions to address]
- [Probing questions for stuck teams]
- [Timing target for this model]

### Model 2
- [Same structure]

## If a team finishes early
- [A stretch question or extension that prepares for the next class]
```

After both files are written, briefly summarize what's in the activity and offer to revise any section. If the user requests changes, edit the Teacher file and re-run the script to regenerate the Student file.

## A few important nuances

**Don't introduce terminology before students invent it.** If the activity teaches "valence electron," that phrase shouldn't appear in the model or in exploration questions — only in or after the key question. This is the single most common mistake in drafts of guided inquiry activities. The model should contain *evidence* for the concept, presented in everyday or pre-existing terminology; the new term is the thing the students are about to coin.

**Models need contrast.** "Here is one example of an exothermic reaction" is not a sufficient model for a guided inquiry activity. "Here are five reactions, three of which release energy and two of which absorb it, with the energy values" is, because the student can see the pattern. When choosing examples for a model, ask: what would change if the concept were false? Make sure the model contains cases that distinguish.

**Questions should be a sequence, not a list.** Each question should rest on the answers to the previous ones, building toward the key question. If you could shuffle the questions and they'd still work, the sequence isn't doing enough work.

**Process skills should be earned, not asserted.** Saying an activity develops "critical thinking" because students answer questions isn't enough. The questions themselves need to demand the skill — e.g., for critical thinking, students should have to evaluate competing claims or justify a choice with evidence, not just look things up.

**Application activities** (a less common type) skip the discovery step and present the concept up front in the model, then use questions to deepen, refine, or integrate it. The structure is similar but the model contains the concept rather than evidence for it. Use this type when the concept doesn't lend itself to discovery (e.g., the postulates of quantum mechanics) or when the focus is on developing a process skill rather than new content.

**Divergent questions go at the end.** A divergent question is one with many valid answers (e.g., "Propose an experiment that would test this rule"). They're great for closure or reflection but disruptive in the middle of an invention sequence, because they pull the team in different directions before they've converged on the concept.
