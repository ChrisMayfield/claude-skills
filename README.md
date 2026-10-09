# claude-skills

Custom skills for Claude, written in the open [Agent Skills](https://agentskills.io/) format.
Each skill is a self-contained directory with a `SKILL.md` specification and any supporting scripts.
The skills are written for Claude but can also be imported into ChatGPT and Gemini.

## Skills

- **[course-evaluations](course-evaluations/)** —
  Analyzes JMU student course evaluation CSVs and produces actionable reports for formative reflection or promotion review.
- **[pogil-activity-writer](pogil-activity-writer/)** —
  Collaboratively authors guided inquiry activities following POGIL pedagogy, producing teacher and student Word documents.

## Installation

Each skill is packaged as a zip file on the [latest release](https://github.com/ChrisMayfield/claude-skills/releases/tag/skills-latest), rebuilt automatically whenever the skill changes.
See each skill's README for download links and installation steps for Claude, Claude Code, ChatGPT, and Gemini.

## Usage

In Claude and Claude Code, the most direct way to run a skill is its slash command, which is the skill's name. You can add context after the command:

```
/pogil-activity-writer enzyme kinetics for an intro biology class
/course-evaluations for my promotion review
```

You can also just ask for the task in your own words. Claude reads the `description` in each `SKILL.md` to decide when to load a skill on its own.

## License

[MIT](LICENSE)
