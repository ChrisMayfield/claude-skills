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

- **`<topic>_Teacher.docx`** — each sample answer in purple, in a shaded box the same size as the student's answer box (so both versions line up page for page), plus facilitation notes at the end.
- **`<topic>_Student.docx`** — the same activity with answers replaced by answer boxes (sized to the expected answer, growing as students type, monospace for code) and facilitation notes removed.

Both are built from a single editable source, **`<topic>_Teacher.md`**, which is delivered alongside them. The bundled [generate_student_version.py](scripts/generate_student_version.py) derives the student Markdown from it, and [build_docx.js](scripts/build_docx.js) (Node, using the `docx` package) converts both to Word. To revise an activity, edit the teacher Markdown and rebuild; never edit the Word files by hand.

## Installation

Download the prebuilt skill package here: **[pogil-activity-writer.zip](https://github.com/ChrisMayfield/claude-skills/releases/download/skills-latest/pogil-activity-writer.zip)** (automatically built from this repository).

The package follows the open [Agent Skills](https://agentskills.io/) format, which Claude, ChatGPT, and Gemini can all import. The conversational backward-design workflow works on every platform. The Word output requires the platform to run the bundled Python and Node scripts. It has been tested in Claude; on other platforms, expect Markdown output or a less faithful conversion.

### Claude

1. Turn on code execution: in **Settings → Capabilities**, enable **Code execution and file creation**. (On Team and Enterprise plans, an owner controls this in the organization settings.)
2. Go to [**Customize → Skills**](https://claude.ai/customize/skills).
3. Click the `+` button, then **Create skill**, then **Upload a skill**, and choose the zip file.
4. Make sure the skill's toggle is on.
5. Start a conversation and ask for a guided inquiry activity on your topic. The skill loads automatically when it is relevant.

### Claude Code

Unzip the package into `~/.claude/skills/` (personal) or `.claude/skills/` (project-scoped), so that the path is `.../skills/pogil-activity-writer/SKILL.md`. To build and check the Word files locally, you also need Python 3, Node.js with the `docx` package (`npm install docx`), LibreOffice, and `pdftoppm` (from Poppler).

### ChatGPT

ChatGPT supports uploaded skills on eligible Business, Enterprise, Healthcare, and Edu plans; your workspace admin may need to allow skill uploads.

1. In the sidebar, select **Plugins**, then open the **Skills** tab.
2. Select **Create**, then **Upload from your computer**, and choose the zip file.
3. ChatGPT scans the upload. If the skill is marked *Needs Review*, review it before use.

On Free, Plus, and Pro plans, skills are not available. A Custom GPT is not a good substitute: `SKILL.md` is about 37,000 characters, well over the 8,000-character limit for GPT instructions.

### Gemini

Gemini skills are rolling out gradually (starting October 2026) and require a personal Google account. Work and school accounts are not yet supported.

1. At [gemini.google.com](https://gemini.google.com), open **Settings → Skills**.
2. Click **Upload**, select the zip file, then click **Create** after reviewing the skill.

Gemini skills cannot run scripts that need internet access, so `npm install docx` will fail unless the package is already available. If it fails, expect Markdown output only.
