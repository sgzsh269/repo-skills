# repo-skills

Agent skills for working with git repositories — analyzing, documenting, and transforming codebases. Works with [Claude Code](https://claude.ai/code) as a plugin and with any AI agent via the [Skills CLI](https://skills.sh).

## Installation

### Claude Code

Add the marketplace and install the plugin:

```bash
/plugin marketplace add sgzsh269/repo-skills
/plugin install repo-skills@repo-skills-plugins
```

After installing, run `/reload-plugins` to activate. Skills are namespaced under the plugin name:

```
/repo-skills:repo-skill-factory <repo-path>
```

See the [Claude Code plugins guide](https://code.claude.com/docs/en/discover-plugins.md) for more details on managing plugins and marketplaces.

#### Local development

To test the plugin locally during development:

```bash
claude --plugin-dir /path/to/repo-skills
```

### Skills CLI (any agent)

Install with the [Skills CLI](https://skills.sh) to use with any compatible AI agent:

```bash
npx skills add sgzsh269/repo-skills
```

This makes the skills available to any agent that supports the [Agent Skills specification](https://agentskills.io/specification.md).

See the [Skills CLI docs](https://skills.sh/docs) for more details.

## Skills

### repo-skill-factory

Convert any git repository into an Agent Skill using a hybrid approach: pre-digested documentation for fast common queries + live repo access for deep exploration.

```
/repo-skills:repo-skill-factory <repo-path> [--output <output-dir>] [--agent claude|generic]
```

Supports Python, JavaScript/TypeScript, Rust, and Go.

The `--agent` flag controls the output format:
- **`claude`** — outputs to `.claude/skills/`, uses `${CLAUDE_SKILL_DIR}` for paths
- **`generic`** (default) — outputs to `.agents/skills/`, uses relative paths per the [Agent Skills spec](https://agentskills.io/specification.md)

If omitted, the agent type is auto-detected from your project structure (`.claude/` → claude, otherwise → generic).

#### How it works

The skill factory runs a multi-step pipeline to turn a repository into a ready-to-use skill:

1. **Automated analysis** — Runs `analyze_repo.py` to produce a structured JSON report of the repo's languages, entry points, documentation, examples, API surface, and project structure.
2. **Language profiling** — Loads language-specific heuristics (from `references/language-profiles.md`) for the detected primary language to guide API detection and dependency handling.
3. **Deep understanding** — Reads the README, key API files, examples, and quickstart docs to build a mental model of the repo's core abstractions, common tasks, and typical workflows.
4. **Skill generation** — Produces the output skill directory:
   - `references/api-reference.md` — Public API signatures extracted via `extract_api.py` (uses AST parsing for Python, regex for other languages), then curated and grouped by domain.
   - `references/examples.md` — Usage examples found by `curate_examples.py` from READMEs, example directories, and notebooks, then filtered to the 5-8 most representative.
   - `scripts/setup.sh` — Idempotent installation script using the detected package manager.
   - `repo` — Symlink to the original repository for live exploration.
   - `SKILL.md` — The main skill file with frontmatter, quick reference, core concepts, common tasks, API overview, project structure, and gotchas. Kept under 500 lines.
5. **Validation** — Verifies line counts, file existence, symlink resolution, and spot-checks that documented APIs actually exist in the source.

#### Output structure

```
<output-dir>/
├── SKILL.md              # Main skill instructions (<500 lines)
├── references/
│   ├── api-reference.md  # Extracted and curated public API docs
│   └── examples.md       # Selected usage examples
├── scripts/
│   └── setup.sh          # Idempotent install script
└── repo -> <repo-path>   # Symlink to original repo
```

The generated skill follows the [Agent Skills specification](https://agentskills.io/specification.md), making it compatible with any agent that supports the format.

## License

MIT
