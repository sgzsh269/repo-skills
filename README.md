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

Analyzes the repo structure, extracts public APIs and usage examples, and generates a skill containing documentation, an installation script, and a symlink to the original repo. Supports Python, JavaScript/TypeScript, Rust, and Go.

## License

MIT
