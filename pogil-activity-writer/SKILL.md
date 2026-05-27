---
name: pogil-activity-writer
description: Collaboratively author Process Oriented Guided Inquiry Learning (POGIL) classroom activities — structured worksheets that guide student teams through a model, exploration questions, concept invention, and application. Use this skill whenever the user asks to create, draft, write, or develop a POGIL activity, guided inquiry worksheet, learning cycle activity, or any classroom activity following the POGIL methodology — even if they don't explicitly say "POGIL." Trigger on requests like "write a POGIL on photosynthesis," "I need a guided inquiry worksheet for my chem class," "make a learning cycle activity for [topic]," "help me design an inquiry-based lesson on X," or "I'm writing classroom materials for student teams to work through." The skill walks the user through backward design (objectives → application → key question → model → exploration questions → sample answers) and produces a Markdown file with both the student activity and teacher materials.
---

# POGIL Activity Writer

A skill for collaboratively writing POGIL (Process Oriented Guided Inquiry Learning) classroom activities. The output is a single Markdown file containing a student-facing worksheet plus teacher materials, structured around the Learning Cycle (Exploration → Concept Invention → Application).

## What POGIL is, briefly

POGIL is a student-centered pedagogy in which small teams of students work through a specially designed activity during class while the instructor facilitates rather than lectures. A POGIL activity has three defining features:

1. **Team-based and instructor-facilitated.** Designed for self-managed teams of 3–4 students; the instructor is a facilitator, not a source of information.
2. **Guided exploration.** Students construct understanding by working through a model (data, diagram, text, equation, code, etc.) and a sequence of questions. They are not told the concept up front.
3. **Embedded process skills.** The activity is designed to develop at least one targeted process skill (e.g., critical thinking, teamwork, information processing) through the structure of the questions themselves — not solely through what the instructor does in the room.

A typical 45–50 minute activity contains 2–3 **Learning Cycles**. Each Learning Cycle has the same shape:

- **Exploration:** Students examine a model and answer short, directed questions about what they observe.
- **Concept Invention:** A key question prompts the team to articulate the underlying pattern or concept in their own words. Terminology is introduced *here*, not before.
- **Application:** Students apply the new concept to a fresh case to consolidate it.

## How to use this skill

POGIL activities are written by **backward design** — start from what students should be able to do at the end, and work backward to the model. When invoked, walk the user through the workflow below conversationally. Don't try to one-shot the whole activity from a one-line prompt. Each step is a small conversation: propose, get feedback, refine, then move on.

If the user's initial request is vague ("help me write a POGIL"), start with Step 0. If they've given a clear topic and audience ("write a POGIL on Newton's third law for intro physics"), still walk through the steps but move briskly through ones where the answer is obvious from context. Skipping the elicitation step entirely produces generic activities that don't fit any real classroom — the conversation is the point.

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

Choose 1–2 process skills the activity will explicitly develop. Every well-designed POGIL activity exercises process skills implicitly, but a strong activity targets one or two *by design* — meaning the structure of the questions develops the skill, not just classroom facilitation.

The seven canonical POGIL process skills:

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

For each learning cycle, write the **key question** — the moment where students articulate the new insight in their own words. This is the last question before the application step. It often looks like:

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

- **Provides enough exemplars for inference.** A single example is rarely enough for students to spot a pattern. 3–5 contrasting cases is common. Show variation along the dimension that matters — and ideally, include cases that are similar in irrelevant ways so students have to identify the right feature.
- **Uses standard representations** for the field.
- **Is clear, concise, and visually clean.** No distracting information.
- **Does not state the concept being developed.** In a Learning Cycle activity, the model shows the evidence for the concept, not the concept itself.
- **Is engaging.** Real-world context, relevant data, or a surprising contrast helps.

Describe the model concretely. If it's a table, write the table out in Markdown. If it's a diagram, describe it in enough detail that the user could draw or generate it. If it's code or data, include the code or data inline.

### Step 7 — Concept invention questions

These questions bridge the gap between the model and the key question. They:

- Start from observations in the model.
- Lead students toward the pattern they need to see.
- Often use prediction: "Predict whether reaction C will be exothermic. Then look at the value in Model 1 — were you correct? If not, what does your team need to revise about the rule you proposed?"
- Increase in difficulty across the sequence.

A common failure mode is asking students to just restate something they can read directly off the model. A better invention question asks them to **compare**, **infer**, **predict**, or **explain why** — operations that require putting the observations together.

### Step 8 — Exploration questions

These are the *first* questions students see after the model — short, directed, easy to answer by reading the model or applying prior knowledge. They orient the team to the model and surface the key features they'll need later.

Examples:
- "In Model 1, what units are used for energy?"
- "Which of the three reactions in Model 1 releases the most energy?"
- "Which atoms in the structure of glucose are involved in the bond shown in red?"

Aim for 2–4 exploration questions per model. They should be answerable in under a minute each. Roughly 3–10 total questions per model is a healthy range across exploration + invention + application.

### Step 9 — Sample answers (teacher materials)

For every question in the activity, write a sample answer **from the perspective of a student team**, not an expert. Student-team answers:

- Are sometimes incomplete or use informal language.
- May contain a common error or two that the instructor can address through facilitation.
- For divergent questions, may include several valid responses.

Also write brief **facilitation notes** for each model — common misconceptions to watch for, probing questions to ask teams that are stuck, and how long teams should be spending on each section.

### Step 10 — Review and refine

Walk through this checklist with the user before finalizing:

- Does each learning cycle have all three phases (Exploration → Concept Invention → Application)?
- Are concepts introduced *only after* students invent them (not pre-named in the model)?
- Is the model rich enough to support the inference it asks for? (Single examples rarely work.)
- Are exploration questions short and directed?
- Are invention questions truly inferential (not just observational)?
- Is at least one process skill developed by the *structure* of the questions, not just by facilitation?
- Can a team of 3–4 students plausibly finish the in-class questions in the allotted time?
- Are there 2+ exercises per content objective for practice after class?

Offer to revise any section based on the review.

## Output format

After all sections are drafted, write a single Markdown file using the template below. Save it to `/mnt/user-data/outputs/<topic-slug>-pogil-activity.md` (replace `<topic-slug>` with a short kebab-case version of the topic) and call `present_files` so the user can download it.

```markdown
# [Activity Title]

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

**Process skills:**
- [Process skill goal 1 with category in parentheses]

---

## Model 1: [Descriptive title]

[The model itself — table, diagram description, text, code, etc.]

### Exploration
1. [Short directed question]
2. [Short directed question]

### Concept invention
3. [Inferential question]
4. [Inferential question building on #3]
5. **Key question:** [Articulate the concept in your own words]

### Application
6. [Apply the concept to a new case]

---

## Model 2: [Descriptive title]

[Repeat structure for each learning cycle. Typically 2–3 cycles total.]

---

## Exercises
[2–10 per content objective. Variations on application questions for practice after class.]

1. ...
2. ...

## Problems (optional)
[Higher-order problems that integrate concepts or apply them in a new real-world context.
Distinct from exercises in that the student doesn't immediately know what to do.]

---

# Teacher Materials

## Facilitation overview
- Suggested time: [breakdown by model]
- Suggested team roles: [Manager, Recorder, Presenter, Reflector — or context-specific]
- What to watch for: [high-level summary]

## Sample answers

### Model 1
1. [Student-perspective answer]
2. [Student-perspective answer]
...

### Facilitation notes for Model 1
- [What teams might get stuck on]
- [Common misconceptions]
- [Probing questions for stuck teams]

[Repeat per model.]
```

After saving, briefly summarize what's in the file and offer to revise any section.

## A few important nuances

**Don't introduce terminology before students invent it.** If the activity teaches "valence electron," that phrase shouldn't appear in the model or in exploration questions — only in or after the key question. This is the single most common mistake in POGIL drafts. The model should contain *evidence* for the concept, presented in everyday or pre-existing terminology; the new term is the thing the students are about to coin.

**Models need contrast.** "Here is one example of an exothermic reaction" is not a POGIL model. "Here are five reactions, three of which release energy and two of which absorb it, with the energy values" is, because the student can see the pattern. When choosing examples for a model, ask: what would change if the concept were false? Make sure the model contains cases that distinguish.

**Questions should be a sequence, not a list.** Each question should rest on the answers to the previous ones, building toward the key question. If you could shuffle the questions and they'd still work, the sequence isn't doing enough work.

**Process skills should be earned, not asserted.** Saying an activity develops "critical thinking" because students answer questions isn't enough. The questions themselves need to demand the skill — e.g., for critical thinking, students should have to evaluate competing claims or justify a choice with evidence, not just look things up.

**Application activities** (a less common type) skip the discovery step and present the concept up front in the model, then use questions to deepen, refine, or integrate it. The structure is similar but the model contains the concept rather than evidence for it. Use this type when the concept doesn't lend itself to discovery (e.g., the postulates of quantum mechanics) or when the focus is on developing a process skill rather than new content.

**Divergent questions go at the end.** A divergent question is one with many valid answers (e.g., "Propose an experiment that would test this rule"). They're great for closure or reflection but disruptive in the middle of an invention sequence, because they pull the team in different directions before they've converged on the concept.
