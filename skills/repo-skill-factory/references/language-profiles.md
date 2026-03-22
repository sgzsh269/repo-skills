# Language Profiles

Heuristics for analyzing repositories by primary language. Use these to guide where to look for APIs, how to install dependencies, and common project structures.

## Python

**Package files:** `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements.txt`
**API discovery:**
- Check `src/<pkg>/__init__.py` for `__all__` exports
- Public classes/functions = no leading underscore
- Key files: `__init__.py` in each subpackage
**CLI entry points:** `[project.scripts]` in pyproject.toml, `__main__.py` files
**Install:**
```bash
pip install -e .          # or: uv pip install -e .
pip install -r requirements.txt  # if no pyproject.toml
```
**Test:** `pytest`, `python -m pytest`
**Common structure:**
```
src/<package>/       # or <package>/ at root
tests/
docs/
examples/
```

## JavaScript / TypeScript

**Package files:** `package.json`, `tsconfig.json`
**API discovery:**
- Check `index.ts`/`index.js` for exports
- Check `package.json` `main`, `exports`, `types` fields
- `export class/function/const` in source files
**CLI entry points:** `bin` field in package.json, `scripts` for npm commands
**Install:**
```bash
npm install          # or: yarn install / pnpm install
npm run build        # if TypeScript
```
**Test:** `npm test`, `jest`, `vitest`
**Common structure:**
```
src/
dist/               # built output
lib/
test/ or __tests__/
```

## Rust

**Package files:** `Cargo.toml`
**API discovery:**
- `pub fn/struct/enum/trait/type` in `src/lib.rs`
- `pub mod` declarations show module structure
**CLI entry points:** `src/main.rs`, `src/bin/*.rs`
**Install:**
```bash
cargo build
cargo install --path .
```
**Test:** `cargo test`
**Common structure:**
```
src/
  lib.rs            # library root
  main.rs           # binary
  bin/              # additional binaries
tests/              # integration tests
```

## Go

**Package files:** `go.mod`
**API discovery:**
- Exported = capitalized names (`func DoThing`, `type Config struct`)
- Package-level files in each directory
**CLI entry points:** `main.go`, `cmd/*/main.go`
**Install:**
```bash
go build ./...
go install ./cmd/...
```
**Test:** `go test ./...`
**Common structure:**
```
cmd/                # binary entry points
internal/           # private packages
pkg/                # public packages (optional)
```
