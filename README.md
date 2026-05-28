# claude-skills

[Custom skills](https://claude.com/docs/skills/how-to) for Claude AI.
Each skill is a self-contained directory with a `SKILL.md` specification and any supporting scripts.

## Skills

- **[course-evaluations](course-evaluations/)** —
  Analyzes JMU student course evaluation CSVs and produces actionable reports for formative reflection or promotion review.
- **[pogil-activity-writer](pogil-activity-writer/)** —
  Collaboratively authors POGIL classroom activities — structured worksheets guiding student teams through a model, questions, and application.

## Usage

Skills are loaded into Claude AI via the [Customize > skills](https://claude.ai/customize/skills) interface.
Once loaded, Claude uses the `SKILL.md` specification to determine when to trigger and how to respond.
