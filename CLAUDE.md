# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository contains custom skills for Claude AI. Each skill lives in its own top-level directory and is a self-contained package consisting of a declarative specification (`SKILL.md`) and any supporting implementation files.

## Skill structure

```
skill-name/
  SKILL.md              # Skill specification (required)
  scripts/              # Executable scripts (Python, JS, Bash)
  references/           # Additional docs Claude loads when needed
  assets/               # Templates, lookup tables, schemas, images
```

The directory name must match the `name` field in `SKILL.md`.

### SKILL.md frontmatter

```yaml
---
name: skill-name          # lowercase, hyphens only, max 64 chars; must match directory name
description: "..."        # how Claude decides when to invoke — be specific and keyword-rich; max 200 chars on claude.ai
dependencies: python>=3.8, pandas>=1.5.0   # optional; Claude installs from PyPI/npm at load time
---
```

The markdown body defines the full skill interface: trigger conditions, expected inputs, processing workflow, judgment guidelines, and output templates. Keep `SKILL.md` under 500 lines; move detailed material to `references/`.

## Current skills

- **`course-evaluations/`** — Analyzes JMU student course evaluation CSVs. Produces formative reports (single semester/year) or longitudinal evidence documents (multi-year, for promotion/tenure). Implemented in `scripts/parse_evaluations.py`.
- **`pogil-activity-writer/`** — Collaboratively authors POGIL (Process Oriented Guided Inquiry Learning) classroom activities. Walks users through backward design and produces a teacher version (with sample answers and facilitation notes) and a student version (with writing space).

## Adding a new skill

1. Create a `skill-name/` directory at the repo root (name must be lowercase with hyphens).
2. Write `SKILL.md` with the required frontmatter and a markdown body documenting the full interface.
3. Add scripts, references, and assets in their respective subdirectories.
4. Package as a ZIP: the ZIP must contain the `skill-name/` directory, not loose files at the root.

## `import_history.py`

One-time utility for replaying skill version history from zip archives as individual git commits. Used to bootstrap a skill's git history from an external archive of versioned `.skill` files.

## Git workflow

Commits should be atomic and focused on a single change (new skill, template update, bug fix). The repository is public; do not commit real student or user data.
