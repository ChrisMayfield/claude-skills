# pogil-activity-writer

An [agent skill](https://agentskills.io/) that helps educators draft **guided inquiry activities** following POGIL pedagogy through an interactive **backward-design workflow**.

Instead of generating an activity in one shot, the skill turns authoring into a conversation. Working backward from the desired student outcomes, the AI proposes learning objectives, process skill goals, application questions, and concept-invention questions *before* designing the model, while you, the content expert, correct and extend each proposal. Core pedagogical principles are encoded as guardrails: terms are never introduced before the key question, models contain contrasting cases that distinguish the concept, and targeted process skills are developed by the structure of the questions rather than by classroom facilitation alone.

`pogil-activity-writer` is an independent work by [Chris Mayfield](https://w3.cs.jmu.edu/mayfiecs/) and is not endorsed by [The POGIL Project](https://www.pogil.org/).

## How the skill was built

[SKILL.md](SKILL.md) encodes guidance drawn from the following sources:

- Several pages from pogil.org:
  [What is POGIL?](https://www.pogil.org/what-is-pogil),
  [Additional Resources](https://www.pogil.org/additional-resources),
  [Writing Guidelines](https://www.pogil.org/authoring-materials/writing-guidelines), and
  [About the POGIL Copyright](https://www.pogil.org/about-the-pogil-project/about-the-pogil-copyrig).
- Outline of the "reverse order" workflow in Clif Kussmaul's
  [Mini-Activity Sprint](https://drive.google.com/file/d/1tNeCw3_roQ8_OtTKRYnW4K1UZh2V75GL/view)
  from the [CS POGIL Activity Writing Program](https://dl.acm.org/doi/10.1145/3545947.3576352).

I refined the skill over many iterations, testing each revision against real activities to surface edge cases in the workflow and output format.

## A note on the POGIL trademark

POGIL® is a registered trademark of The POGIL Project and is used for activities and materials that have been [**reviewed and endorsed**](https://pogil.org/authoring-materials/endorsement-publication). Drafts produced by this skill are **not** POGIL activities — they are guided inquiry activities written following POGIL pedagogical guidelines, intended as starting points for authors. The skill never labels its output as a "POGIL activity," keeps the word *POGIL* out of titles and filenames, and reserves that term for endorsed materials.

## Usage

Once installed, start with a request such as:

> Help me write a guided inquiry activity on enzyme kinetics for an intro biology class.

The skill will walk you through the backward-design steps, checking in with you at each stage, and finish by producing two Word documents, ready to print or to upload to Google Docs for students to type into:

- **`<topic>_Teacher.docx`** — sample answers inline under each question, plus facilitation notes at the end.
- **`<topic>_Student.docx`** — the same activity with answers replaced by answer boxes (sized to the expected answer, growing as students type, monospace for code) and facilitation notes removed.

Both are built from a single editable source, **`<topic>_Teacher.md`**, which is delivered alongside them. The bundled [generate_student_version.py](scripts/generate_student_version.py) derives the student Markdown from it, and [build_docx.js](scripts/build_docx.js) (Node, using the `docx` package) converts both to Word. To revise an activity, edit the teacher Markdown and rebuild; never edit the Word files by hand.

## Installation

Download the prebuilt skill package here: **[pogil-activity-writer.zip](https://github.com/ChrisMayfield/claude-skills/releases/download/skills-latest/pogil-activity-writer.zip)** (automatically built from this repository).

Only Claude currently supports uploading a skill in the native `SKILL.md` format. For ChatGPT and Gemini, you recreate the same behavior as a Custom GPT or a Gem by pasting `SKILL.md` as the system instructions and attaching the script as a reference file. The conversational backward-design workflow works on all three; the Word output depends on the platform being able to run the bundled Python and Node scripts (reliable in Claude with code execution; on ChatGPT/Gemini, expect Markdown output or a less faithful conversion).

### Claude

Claude reads the `SKILL.md` format directly, so you can upload the zip archive as-is.

1. Go to [**Customize → Skills**](https://claude.ai/customize/skills). (Requires a plan with Skills and code execution enabled.)
2. Click the `+` button, then Create Skill, then Upload a skill.
3. Start a conversation and ask for a guided inquiry activity on your topic — the skill loads automatically when relevant.

For Claude Code, place the `pogil-activity-writer/` folder in `~/.claude/skills/` (personal) or `.claude/skills/` (project-scoped).

### ChatGPT (Custom GPT)

ChatGPT has no native skill format, so recreate the skill as a Custom GPT. Requires ChatGPT Plus, Team, or Enterprise. You'll need `SKILL.md` and `scripts/generate_student_version.py` — both are inside the skill package zip.

1. Go to [chatgpt.com/gpts](https://chatgpt.com/gpts) and click **Create**, then open the **Configure** tab.
2. Give it a name and short description.
3. Open `SKILL.md`, copy everything **below** the YAML frontmatter (the `---` block at the top), and paste it into the **Instructions** field.
4. Under **Knowledge**, upload `scripts/generate_student_version.py` so the GPT can apply or reproduce the student-version transformation. Enable **Code Interpreter & Data Analysis** under Capabilities if you want it to actually run the script.
5. Save, then test by asking for a guided inquiry activity on a sample topic.

### Gemini (Gem)

Gemini's equivalent is a Gem. Creating Gems is done in the Gemini web app.

1. In Gemini, open the menu and choose **Gems → New Gem**.
2. Name the Gem.
3. Open `SKILL.md`, copy everything **below** the YAML frontmatter, and paste it into the **Instructions** field.
4. Under **Knowledge**, click **Add files** and upload `scripts/generate_student_version.py`.
5. Click **Save**, then open the Gem and request an activity on a sample topic.
