# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository contains custom skills in the open [Agent Skills](https://agentskills.io/specification) format, written for Claude but importable into ChatGPT and Gemini. Each skill lives in its own top-level directory and is a self-contained package consisting of a declarative specification (`SKILL.md`), a user-facing `README.md`, and any supporting implementation files.

## Skill structure

```
skill-name/
  SKILL.md              # Skill specification (required)
  README.md             # User-facing overview, usage, and installation
  scripts/              # Executable scripts (Python, JS, Bash)
  references/           # Additional docs Claude loads when needed
  assets/               # Templates, lookup tables, schemas, images
```

The directory name must match the `name` field in `SKILL.md`.

### SKILL.md frontmatter

```yaml
---
name: skill-name          # lowercase, hyphens only, max 64 chars; must match directory name
description: "..."        # how Claude decides when to invoke — be specific and keyword-rich; max 1024 chars; if unquoted, avoid ": " (breaks YAML)
---
```

The spec also allows optional `license`, `compatibility`, `metadata`, and `allowed-tools` fields. There is no field for package dependencies; scripts must check for missing packages and `SKILL.md` must say how to install them (see below).

The markdown body defines the full skill interface: trigger conditions, expected inputs, processing workflow, judgment guidelines, and output templates. Keep `SKILL.md` under 500 lines; move detailed material to `references/`.

### Portable paths

Skills must run on Claude.ai, Claude Code, and other platforms, so `SKILL.md` never hard-codes environment paths such as `/mnt/user-data/uploads/` or `/tmp`. Instead it names directories by role and says how each resolves per platform:

- `<skill>`: the skill's own directory. Run bundled scripts by full path (`python3 <skill>/scripts/...`), since the working directory is usually elsewhere.
- `<in>` / `<out>`: where the user's files come from and where deliverables go (Claude.ai uploads/outputs folders; in Claude Code, the paths the user names or the current directory).
- `<work>`: a scratch directory for intermediates, never the user's folder.

Use `python3`, not `python`. Install missing packages outside the user's folder: Python packages in a virtual environment under `<work>` (system Python is often protected), npm packages with `npm install --prefix <work>` plus `NODE_PATH`. Use platform-specific tools such as `present_files` only where they exist, with a fallback.

## Current skills

- **`course-evaluations/`** — Analyzes JMU student course evaluation CSVs. Produces formative reports (single semester/year) or longitudinal evidence documents (multi-year, for promotion/tenure). Implemented in `scripts/parse_evaluations.py`.
- **`pogil-activity-writer/`** — Collaboratively authors guided inquiry activities following POGIL (Process Oriented Guided Inquiry Learning) pedagogy. Walks users through backward design and produces teacher and student Word documents from a single teacher Markdown source. Drafts are never called "POGIL activities" (a trademark reserved for endorsed materials), and "pogil" stays out of titles and output filenames. Implemented in `scripts/generate_student_version.py` (student Markdown) and `scripts/build_docx.js` (Word output).

## Adding a new skill

1. Create a `skill-name/` directory at the repo root (name must be lowercase with hyphens).
2. Write `SKILL.md` with the required frontmatter and a markdown body documenting the full interface.
3. Write `README.md` with an overview, usage, and installation steps for each platform (see the existing skills' READMEs).
4. Add scripts, references, and assets in their respective subdirectories.
5. Add the skill to the list in the top-level `README.md` and in this file.

Packaging is automatic: on every push to `main` that touches a skill, `.github/workflows/package-skills.yml` zips each directory containing a `SKILL.md` (with the `skill-name/` directory at the top level of the ZIP) and republishes them on the `skills-latest` release. The skill READMEs link to those release assets.

## `import_history.py`

One-time utility for replaying skill version history from zip archives as individual git commits. Used to bootstrap a skill's git history from an external archive of versioned `.skill` files.

## Git workflow

Commits should be atomic and focused on a single change (new skill, template update, bug fix). The repository is public; do not commit real student or user data. Use the git-ignored `scratch/` directory for test inputs and outputs.
