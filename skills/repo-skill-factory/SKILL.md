---
name: repo-skill-factory
description: >
  Convert any git repository into a Claude Skill using a hybrid approach
  (pre-digested docs + live repo access). Use when the user wants to create
  a skill from a repository, library, framework, or codebase. Also trigger
  when someone says "make a skill for this repo", "turn this library into
  a skill", "create a skill from this codebase", "skillify this repo",
  or wants to make a repo's capabilities available as a Claude skill.
  Do NOT use for creating skills from scratch that aren't based on an
  existing repository.
compatibility: Requires Python 3 and git
metadata:
  argument-hint: "<repo-path> [--output <output-dir>]"
  author: repo-skills
  version: "1.0"
---

# /repo-skills:repo-skill-factory

Convert a git repository into a hybrid Claude Skill: pre-digested documentation
for fast common queries + live repo access for deep exploration.

## Step 1: Parse Arguments

Extract the repo path from `$ARGUMENTS`. Optionally extract `--output <dir>`.

```
Repo path: $ARGUMENTS (first non-flag argument)
Output dir: --output value, or default to .claude/skills/<repo-name>/
```

Validate:
- The repo path exists and is a directory
- It contains source code (not empty)
- Derive `skill_name` from the repo directory name, normalized to kebab-case
  (lowercase, replace underscores/spaces with hyphens)

If the path is relative, resolve it from the current working directory.

## Step 2: Capture Source Repo Version

Record the exact version of the source repo being converted so the generated
skill can identify what it was built from:

```bash
cd <repo-path>
SOURCE_COMMIT=$(git rev-parse HEAD)
SOURCE_BRANCH=$(git rev-parse --abbrev-ref HEAD)
SOURCE_TAG=$(git describe --tags --exact-match 2>/dev/null || echo "")
SOURCE_DIRTY=$(git diff --quiet && echo "false" || echo "true")
cd -
```

Save these values — they will be embedded in the generated skill's metadata.

## Step 3: Run Automated Analysis

Run the analysis script to get a structured JSON report of the repo:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/analyze_repo.py <repo-path> > /tmp/repo-analysis.json
```

This produces a JSON report with: `languages`, `entry_points`, `docs`,
`examples`, `api_surface`, `metadata`, and `structure`.

Read the output. If the script fails, fall back to manual exploration:
read the README, list directories, check for package files.

## Step 4: Read the Language Profile

Read [references/language-profiles.md](references/language-profiles.md) and
find the section matching the detected primary language. This tells you:
- Where APIs are defined and how to detect them
- How dependencies and installation work
- Common project structure patterns

## Step 5: Deep Understanding (Claude Analysis)

Using the automated analysis as a foundation, build a mental model of the repo.
Read these files (in this priority order, stop when you have enough context):

1. **README** — understand the project's purpose, audience, and core workflow
2. **Key API files** — the top 3-5 files from `api_surface` in the analysis.
   Understand the main abstractions (classes, interfaces, protocols)
3. **2-3 example files** — understand typical usage patterns
4. **Quickstart docs** — if `docs/` exists, check for quickstart/getting-started

Produce a mental model covering:
- The 5-10 most common tasks a user would do with this library/tool
- Core abstractions and how they relate
- The typical workflow: install → configure → use
- Common pitfalls or non-obvious patterns
- Who the target audience is (developers, data scientists, ops, etc.)

## Step 6: Generate the Skill

Create the output directory structure:

```bash
mkdir -p <output-dir>/references
mkdir -p <output-dir>/scripts
```

Generate each file in order:

### 6a. Generate `references/api-reference.md`

Run the API extraction script:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/extract_api.py <repo-path> \
  --analysis /tmp/repo-analysis.json > /tmp/raw-api-reference.md
```

Read the raw output. Then write `<output-dir>/references/api-reference.md` with
your improvements:
- Add a table of contents at the top if >100 lines
- Group APIs by domain/purpose (not just by file)
- Add brief descriptions where the raw extraction missed them
- Remove internal/private APIs that leaked through
- Keep it factual — only document what actually exists in the source

### 6b. Generate `references/examples.md`

Run the example curation script:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/curate_examples.py <repo-path> \
  --analysis /tmp/repo-analysis.json > /tmp/raw-examples.md
```

Read the raw output. Then write `<output-dir>/references/examples.md`:
- Select the 5-8 most representative examples
- Order them: quickstart first, then common use cases, then advanced
- Add a title and brief description for each
- Remove examples that are too similar to each other
- Ensure code blocks have correct language tags

### 6c. Generate `scripts/setup.sh`

Write `<output-dir>/scripts/setup.sh` based on the language and dependencies
from the analysis. Use the templates from
[references/skill-template.md](references/skill-template.md) as a guide.

The setup script should:
- Be idempotent (safe to run multiple times)
- Use the detected package manager
- Install in development/editable mode when possible
- Print a success message

Make it executable: `chmod +x <output-dir>/scripts/setup.sh`

### 6d. Create Repo Symlink

```bash
ln -sf $(realpath <repo-path>) <output-dir>/repo
```

This enables live exploration of the repo through the generated skill.

### 6e. Generate `SKILL.md`

This is the most important file. Read
[references/skill-template.md](references/skill-template.md) for the structure,
then write `<output-dir>/SKILL.md` filling in all sections from your analysis.

Key guidelines for the generated SKILL.md:

**Frontmatter:**
- `name`: the kebab-case skill name
- `description`: 2-3 sentences covering what it does AND when to trigger it.
  Be specific about trigger keywords. Be slightly "pushy" — err toward
  triggering too often rather than too rarely.
- `metadata`: include source repo version info captured in Step 2:
  - `source-commit`: the full commit SHA
  - `source-branch`: the branch name
  - `source-tag`: the tag if on an exact tag, omit otherwise
  - `source-dirty`: "true" if the working tree had uncommitted changes
  - `generated-at`: the current date (YYYY-MM-DD)
**Body structure:**
- Start with a 2-3 sentence overview
- Include a "Quick Reference" box with repo location, language, install command, CLI
- "How to Use This Skill" section explaining the hybrid approach:
  check references first, explore repo if needed
- "Core Concepts" — the 3-5 key abstractions in bullet points
- "Common Tasks" — step-by-step for the top 3-5 things users would do
- "API Overview" — summary table pointing to the full reference
- "Project Structure" — annotated directory tree
- "Gotchas and Tips" — things that aren't obvious
- "When to Explore the Repo Directly" — when references aren't enough

**Quality bar:**
- Under 500 lines total
- No hallucinated APIs — everything mentioned must exist in the source
- Use `${CLAUDE_SKILL_DIR}` for all path references
- Include actual code snippets for common tasks (copied from examples, not invented)

## Step 7: Validate

Check your work:

1. Count lines in the generated SKILL.md — must be under 500
2. Verify all referenced files exist (api-reference.md, examples.md, setup.sh)
3. Verify the symlink resolves: `ls -la <output-dir>/repo/`
4. Spot-check: pick one API mentioned in the SKILL.md and verify it exists
   in the actual source code
5. Smoke test: "If someone asked 'how do I get started with <repo-name>?',
   does this skill have enough info to answer without exploring the repo?"

## Step 8: Report

Tell the user what was created:

```
Generated skill: <output-dir>/
├── SKILL.md           (N lines)
├── references/
│   ├── api-reference.md
│   └── examples.md
├── scripts/
│   └── setup.sh
└── repo -> <original-repo-path>

The skill covers:
- <N> API classes/functions documented
- <N> examples curated
- CLI commands: <list>
- Primary language: <language>
- Source version: <commit-sha-short> (<branch>) [<tag>] [dirty]

To test: use the generated skill with test prompts.
To install: the skill is already in .claude/skills/ and will be auto-discovered.
```

## Guardrails

- Only document APIs that actually exist in the source — never hallucinate
- Do not include internal/private APIs unless they are the only way to do something
- Do not copy large code blocks verbatim (>50 lines) — summarize and point to source
- Preserve the repo's license information
- Skip generated/vendored code (node_modules, .venv, dist, build)
- If the repo has no clear public API (it's an application, not a library),
  adapt: focus on configuration, CLI usage, and operational patterns instead
- If the repo is very large (>1000 source files), focus on the top-level package
  and most-used modules rather than trying to cover everything
