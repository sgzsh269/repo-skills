# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Claude Code plugin named "repo-skills" that bundles skills for working with git repositories. Skills live under `skills/` as subdirectories containing a `SKILL.md` and supporting files.

## Plugin Structure

- `.claude-plugin/plugin.json` — plugin manifest (name, version, description)
- `skills/<skill-name>/SKILL.md` — skill definition with frontmatter (name, description, argument-hint)
- `skills/<skill-name>/references/` — reference docs used by the skill
- `skills/<skill-name>/scripts/` — Python scripts invoked by the skill

## Current Skills

- **repo-skill-factory** — converts a git repo into a Claude Skill by analyzing its structure, extracting APIs/examples, and generating documentation. Supports Python, JS/TS, Rust, Go.

## Testing Locally

```bash
claude --plugin-dir .
```

Then invoke a skill with `/repo-skills:<skill-name>`.

## Key Files for repo-skill-factory

- `skills/repo-skill-factory/scripts/analyze_repo.py` — repo analysis engine, outputs structured JSON
- `skills/repo-skill-factory/scripts/extract_api.py` — extracts public API signatures using AST (Python) or regex (JS/TS, Rust, Go)
- `skills/repo-skill-factory/scripts/curate_examples.py` — finds and curates usage examples from READMEs, example dirs, notebooks
- `skills/repo-skill-factory/references/language-profiles.md` — language-specific heuristics for analysis
- `skills/repo-skill-factory/references/skill-template.md` — template for generated skills
