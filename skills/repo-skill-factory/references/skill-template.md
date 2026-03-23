# Skill Template

This is the template used when generating a skill from a repository. Placeholders use `{{name}}` syntax and are filled in during generation.

The generated skill follows the [Agent Skills specification](https://agentskills.io/specification.md) and is compatible with any agent that supports it (Claude Code, VS Code Copilot, OpenAI Codex, etc.).

---

## Generated SKILL.md Template

### Frontmatter

```yaml
---
name: {{skill_name}}
description: >
  Work with {{repo_name}} — {{description}}.
  Use when the user wants to {{use_cases}}.
  Also use when someone mentions {{trigger_keywords}}.
compatibility: {{compatibility}}    # e.g., "Requires Python 3.10+ and git"
metadata:
  source-commit: {{source_commit}}
  source-branch: {{source_branch}}
  source-tag: {{source_tag}}        # omit if empty
  source-dirty: "{{source_dirty}}"
  generated-at: {{generated_date}}
  agent-type: {{agent_type}}        # "claude" or "generic"
---
```

### Body (Claude agent type)

Use `${CLAUDE_SKILL_DIR}` for all path references. Claude Code resolves this
variable at runtime to the skill's directory.

```markdown
# {{repo_name}}

{{overview}}

## Quick Reference

- **Repo location:** `${CLAUDE_SKILL_DIR}/repo/`
- **Language:** {{primary_language}}
- **Source version:** `{{source_commit_short}}` ({{source_branch}}){{#if source_tag}} tag `{{source_tag}}`{{/if}}{{#if source_dirty}} ⚠ dirty{{/if}}, generated {{generated_date}}
- **Install:** `bash ${CLAUDE_SKILL_DIR}/scripts/setup.sh`
{{#if cli_command}}
- **CLI:** `{{cli_command}} --help`
{{/if}}

## How to Use This Skill

1. Check the references first — they contain pre-extracted API docs and examples
   covering most common tasks:
   - [API Reference](references/api-reference.md) — classes, functions, signatures
   - [Examples](references/examples.md) — curated usage examples
2. If references don't answer the question, explore the live repo at
   `${CLAUDE_SKILL_DIR}/repo/` using Glob, Grep, and Read.
3. For running code or CLI commands, use Bash with appropriate environment setup.

## Core Concepts

{{core_concepts}}

## Common Tasks

{{common_tasks}}

## API Overview

See [references/api-reference.md](references/api-reference.md) for full details.

Key classes and functions:
{{api_summary}}

## Project Structure

```
{{structure}}
```

## Gotchas and Tips

{{gotchas}}

## When to Explore the Repo Directly

The pre-digested references cover the public API and common workflows.
Explore `${CLAUDE_SKILL_DIR}/repo/` directly when:
- Looking for internal implementation details
- Debugging unexpected behavior
- Working with features not covered in the references
- Checking test patterns for similar functionality
- Understanding how a specific feature is implemented
```

### Body (Generic agent type)

Use relative paths from the SKILL.md file. Generic agents following the Agent
Skills spec resolve paths relative to the skill root directory.

```markdown
# {{repo_name}}

{{overview}}

## Quick Reference

- **Repo location:** `repo/`
- **Language:** {{primary_language}}
- **Source version:** `{{source_commit_short}}` ({{source_branch}}){{#if source_tag}} tag `{{source_tag}}`{{/if}}{{#if source_dirty}} ⚠ dirty{{/if}}, generated {{generated_date}}
- **Install:** `bash scripts/setup.sh`
{{#if cli_command}}
- **CLI:** `{{cli_command}} --help`
{{/if}}

## How to Use This Skill

1. Check the references first — they contain pre-extracted API docs and examples
   covering most common tasks:
   - [API Reference](references/api-reference.md) — classes, functions, signatures
   - [Examples](references/examples.md) — curated usage examples
2. If references don't answer the question, explore the live repo at
   `repo/` for source code details.
3. For running code or CLI commands, use a terminal with appropriate environment setup.

## Core Concepts

{{core_concepts}}

## Common Tasks

{{common_tasks}}

## API Overview

See [references/api-reference.md](references/api-reference.md) for full details.

Key classes and functions:
{{api_summary}}

## Project Structure

```
{{structure}}
```

## Gotchas and Tips

{{gotchas}}

## When to Explore the Repo Directly

The pre-digested references cover the public API and common workflows.
Explore `repo/` directly when:
- Looking for internal implementation details
- Debugging unexpected behavior
- Working with features not covered in the references
- Checking test patterns for similar functionality
- Understanding how a specific feature is implemented
```

---

## Generated setup.sh Template

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/../repo" && pwd)"

{{#if python}}
# Python setup
cd "$REPO_DIR"
if command -v uv &>/dev/null; then
    uv pip install -e . 2>/dev/null || pip install -e .
else
    pip install -e .
fi
{{/if}}

{{#if javascript}}
# JavaScript/TypeScript setup
cd "$REPO_DIR"
if command -v pnpm &>/dev/null; then
    pnpm install
elif command -v yarn &>/dev/null; then
    yarn install
else
    npm install
fi
{{/if}}

{{#if rust}}
# Rust setup
cd "$REPO_DIR"
cargo build
{{/if}}

{{#if go}}
# Go setup
cd "$REPO_DIR"
go build ./...
{{/if}}

echo "Setup complete for {{repo_name}}"
```
