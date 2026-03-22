# repo-skills

A Claude Code plugin with skills for working with git repositories — analyzing, documenting, and transforming codebases.

## Installation

Install from a marketplace:

```bash
claude plugin install repo-skills@<marketplace-name>
```

Or test locally during development:

```bash
claude --plugin-dir /path/to/repo-skills
```

## Skills

### repo-skill-factory

Convert any git repository into a Claude Skill using a hybrid approach: pre-digested documentation for fast common queries + live repo access for deep exploration.

```
/repo-skills:repo-skill-factory <repo-path> [--output <output-dir>]
```

Supports Python, JavaScript/TypeScript, Rust, and Go.

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
