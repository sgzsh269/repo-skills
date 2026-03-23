# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Agent skills for working with git repositories, packaged as a Claude Code plugin. Skills follow the [Agent Skills specification](https://agentskills.io/specification.md) and work with Claude Code, VS Code Copilot, and any compatible agent. Skills live under `skills/` as subdirectories containing a `SKILL.md` and supporting files.

## Plugin Structure

- `.claude-plugin/plugin.json` — plugin manifest (name, version, description)
- `skills/<skill-name>/SKILL.md` — skill definition with frontmatter (name, description, compatibility, metadata)
- `skills/<skill-name>/references/` — reference docs used by the skill
- `skills/<skill-name>/scripts/` — Python scripts invoked by the skill

## Current Skills

- **repo-skill-factory** — converts a git repo into an Agent Skill by analyzing its structure, extracting APIs/examples, and generating documentation. Supports Python, JS/TS, Rust, Go. Generates skills for Claude Code (`--agent claude`) or any compatible agent (`--agent generic`).

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
- `skills/repo-skill-factory/references/skill-template.md` — template for generated skills (has both Claude and generic agent variants)
