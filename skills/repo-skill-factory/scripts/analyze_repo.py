#!/usr/bin/env python3
"""Analyze a git repository and output a JSON report of its structure, APIs, and metadata."""

import ast
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path


SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv",
    ".tox", ".mypy_cache", ".pytest_cache", "dist", "build", ".eggs",
    "site-packages", ".next", ".nuxt", "target", "vendor", ".worktrees",
}

LANGUAGE_EXTENSIONS = {
    ".py": "python", ".pyi": "python",
    ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".ts": "typescript", ".tsx": "typescript", ".jsx": "javascript",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".rb": "ruby",
    ".php": "php",
    ".c": "c", ".h": "c",
    ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".hpp": "cpp",
    ".cs": "csharp",
    ".swift": "swift",
    ".kt": "kotlin", ".kts": "kotlin",
    ".scala": "scala",
    ".lua": "lua",
    ".r": "r", ".R": "r",
    ".jl": "julia",
    ".ex": "elixir", ".exs": "elixir",
    ".sh": "shell", ".bash": "shell", ".zsh": "shell",
}

PACKAGE_FILES = {
    "pyproject.toml": "python",
    "setup.py": "python",
    "setup.cfg": "python",
    "requirements.txt": "python",
    "package.json": "javascript",
    "Cargo.toml": "rust",
    "go.mod": "go",
    "Gemfile": "ruby",
    "composer.json": "php",
    "pom.xml": "java",
    "build.gradle": "java",
    "build.gradle.kts": "kotlin",
    "build.sbt": "scala",
    "Package.swift": "swift",
    "mix.exs": "elixir",
}


def walk_repo(repo_path: Path):
    """Walk repo, skipping ignored directories. Yields (relative_path, full_path)."""
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        rel_root = Path(root).relative_to(repo_path)
        for f in files:
            yield rel_root / f, Path(root) / f


def detect_languages(repo_path: Path):
    """Detect languages by file extension counts and package file presence."""
    ext_counts = Counter()
    lang_counts = Counter()
    total_files = 0

    for rel_path, full_path in walk_repo(repo_path):
        total_files += 1
        ext = full_path.suffix.lower()
        if ext in LANGUAGE_EXTENSIONS:
            lang = LANGUAGE_EXTENSIONS[ext]
            ext_counts[ext] += 1
            lang_counts[lang] += 1

    # Boost languages with package files
    for pf, lang in PACKAGE_FILES.items():
        if (repo_path / pf).exists():
            lang_counts[lang] += 100  # strong signal

    primary = lang_counts.most_common(1)[0][0] if lang_counts else "unknown"
    return {
        "primary": primary,
        "all": dict(lang_counts.most_common()),
        "file_extensions": dict(ext_counts.most_common(20)),
        "total_files": total_files,
    }


def parse_pyproject_toml(path: Path):
    """Parse pyproject.toml without tomllib (works on Python 3.10+)."""
    try:
        import tomllib
        with open(path, "rb") as f:
            return tomllib.load(f)
    except ImportError:
        pass
    # Fallback: regex-based extraction for key fields
    text = path.read_text(errors="replace")
    result = {"project": {}, "scripts": {}}

    # Extract [project] fields
    name_m = re.search(r'^\s*name\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if name_m:
        result["project"]["name"] = name_m.group(1)

    version_m = re.search(r'^\s*version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if version_m:
        result["project"]["version"] = version_m.group(1)

    desc_m = re.search(r'^\s*description\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if desc_m:
        result["project"]["description"] = desc_m.group(1)

    # Extract [project.scripts]
    scripts_section = re.search(
        r'\[project\.scripts\]\s*\n((?:\s*\w[^\[]*\n)*)', text
    )
    if scripts_section:
        for line in scripts_section.group(1).strip().split("\n"):
            m = re.match(r'\s*(\S+)\s*=\s*"([^"]+)"', line)
            if m:
                result["scripts"][m.group(1)] = m.group(2)

    # Extract dependencies
    deps_m = re.search(r'dependencies\s*=\s*\[(.*?)\]', text, re.DOTALL)
    if deps_m:
        deps = re.findall(r'"([^"]+)"', deps_m.group(1))
        result["project"]["dependencies"] = deps

    return result


def parse_package_json(path: Path):
    """Parse package.json."""
    with open(path) as f:
        return json.load(f)


def find_entry_points(repo_path: Path, languages: dict):
    """Find CLI entry points and main files."""
    entries = []
    primary = languages["primary"]

    if primary == "python":
        # pyproject.toml scripts
        pyproject = repo_path / "pyproject.toml"
        if pyproject.exists():
            data = parse_pyproject_toml(pyproject)
            scripts = data.get("project", {}).get("scripts", {})
            # Fallback key used by regex parser
            if not scripts:
                scripts = data.get("scripts", {})
            for cmd, target in scripts.items():
                entries.append({"type": "cli", "command": cmd, "target": target})

        # __main__.py files
        for rel_path, full_path in walk_repo(repo_path):
            if rel_path.name == "__main__.py":
                entries.append({
                    "type": "main_module",
                    "path": str(rel_path),
                    "module": str(rel_path.parent).replace("/", "."),
                })

    elif primary in ("javascript", "typescript"):
        pkg = repo_path / "package.json"
        if pkg.exists():
            data = parse_package_json(pkg)
            # bin entries
            bin_field = data.get("bin", {})
            if isinstance(bin_field, str):
                bin_field = {data.get("name", "main"): bin_field}
            for cmd, target in bin_field.items():
                entries.append({"type": "cli", "command": cmd, "target": target})
            # scripts
            for cmd, script in data.get("scripts", {}).items():
                if cmd in ("start", "dev", "build", "test"):
                    entries.append({"type": "npm_script", "command": cmd, "script": script})

    elif primary == "rust":
        main_rs = repo_path / "src" / "main.rs"
        if main_rs.exists():
            entries.append({"type": "binary", "path": "src/main.rs"})
        bin_dir = repo_path / "src" / "bin"
        if bin_dir.is_dir():
            for f in bin_dir.glob("*.rs"):
                entries.append({"type": "binary", "path": str(f.relative_to(repo_path))})

    elif primary == "go":
        main_go = repo_path / "main.go"
        if main_go.exists():
            entries.append({"type": "binary", "path": "main.go"})
        cmd_dir = repo_path / "cmd"
        if cmd_dir.is_dir():
            for d in cmd_dir.iterdir():
                if d.is_dir():
                    entries.append({"type": "binary", "path": str(d.relative_to(repo_path))})

    return entries


def find_docs(repo_path: Path):
    """Find documentation files and directories."""
    docs = []
    # Root-level docs
    for pattern in ["README*", "CONTRIBUTING*", "CHANGELOG*", "CHANGES*", "HISTORY*"]:
        for f in repo_path.glob(pattern):
            if f.is_file():
                docs.append({"type": "file", "path": str(f.relative_to(repo_path))})

    # Doc directories
    for dirname in ["docs", "doc", "documentation", "wiki"]:
        d = repo_path / dirname
        if d.is_dir():
            md_count = len(list(d.rglob("*.md")))
            rst_count = len(list(d.rglob("*.rst")))
            docs.append({
                "type": "directory",
                "path": dirname,
                "md_files": md_count,
                "rst_files": rst_count,
            })

    return docs


def find_examples(repo_path: Path):
    """Find example files and directories."""
    examples = []
    # Example directories
    for dirname in ["examples", "example", "demos", "demo", "tutorial", "tutorials", "samples"]:
        d = repo_path / dirname
        if d.is_dir():
            files = []
            for rel_path, full_path in walk_repo(d):
                if full_path.suffix in (".py", ".js", ".ts", ".rs", ".go", ".ipynb", ".sh"):
                    files.append(str(d.name / rel_path))
            examples.append({
                "type": "directory",
                "path": dirname,
                "files": files[:30],  # cap at 30
            })

    # Notebooks in root
    for nb in repo_path.glob("*.ipynb"):
        examples.append({"type": "notebook", "path": str(nb.relative_to(repo_path))})

    return examples


def find_api_surface_python(repo_path: Path):
    """Find public Python API by parsing __init__.py and public modules."""
    api = []
    src_dirs = []

    # Find source roots
    src = repo_path / "src"
    if src.is_dir():
        for pkg in src.iterdir():
            if pkg.is_dir() and (pkg / "__init__.py").exists():
                src_dirs.append(pkg)
    else:
        # Root-level packages
        for item in repo_path.iterdir():
            if item.is_dir() and (item / "__init__.py").exists() and item.name not in SKIP_DIRS:
                if not item.name.startswith((".", "test")):
                    src_dirs.append(item)

    for pkg_dir in src_dirs:
        pkg_name = pkg_dir.name
        init_file = pkg_dir / "__init__.py"

        # Parse __init__.py for __all__ and imports
        if init_file.exists():
            try:
                tree = ast.parse(init_file.read_text(errors="replace"))
                all_names = []
                imports = []

                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id == "__all__":
                                if isinstance(node.value, (ast.List, ast.Tuple)):
                                    all_names = [
                                        elt.value for elt in node.value.elts
                                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                                    ]
                    elif isinstance(node, ast.ImportFrom):
                        if node.names:
                            for alias in node.names:
                                imports.append(alias.name if alias.asname is None else alias.asname)

                exported = all_names or [n for n in imports if not n.startswith("_")]
                if exported:
                    api.append({
                        "package": pkg_name,
                        "init_exports": exported[:50],
                        "source": str(init_file.relative_to(repo_path)),
                    })
            except (SyntaxError, UnicodeDecodeError):
                pass

        # Find submodules with public classes/functions
        for py_file in pkg_dir.rglob("*.py"):
            if py_file.name.startswith("_") and py_file.name != "__init__.py":
                continue
            rel = py_file.relative_to(repo_path)
            try:
                tree = ast.parse(py_file.read_text(errors="replace"))
                classes = []
                functions = []
                for node in ast.iter_child_nodes(tree):
                    if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                        methods = [
                            n.name for n in node.body
                            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                            and not n.name.startswith("_")
                        ]
                        classes.append({"name": node.name, "methods": methods[:15]})
                    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if not node.name.startswith("_"):
                            functions.append(node.name)

                if classes or functions:
                    api.append({
                        "module": str(rel),
                        "classes": classes[:10],
                        "functions": functions[:20],
                    })
            except (SyntaxError, UnicodeDecodeError):
                pass

    return api


def find_api_surface(repo_path: Path, languages: dict):
    """Find public API surface based on primary language."""
    primary = languages["primary"]
    if primary == "python":
        return find_api_surface_python(repo_path)

    # For other languages, return file-level info for Claude to analyze
    api_files = []
    patterns = {
        "javascript": ["index.js", "index.ts", "index.mjs"],
        "typescript": ["index.ts", "index.tsx", "index.js"],
        "rust": ["src/lib.rs"],
        "go": [],  # Go uses package-level exports
    }

    for pattern in patterns.get(primary, []):
        f = repo_path / pattern
        if f.exists():
            api_files.append(str(f.relative_to(repo_path)))

    # Also find src/ top-level files
    src = repo_path / "src"
    if src.is_dir():
        for f in src.iterdir():
            if f.is_file() and f.suffix in LANGUAGE_EXTENSIONS:
                api_files.append(str(f.relative_to(repo_path)))

    return [{"type": "files_to_analyze", "files": api_files}] if api_files else []


def get_repo_metadata(repo_path: Path, languages: dict):
    """Extract repo metadata from package manifest."""
    meta = {"name": repo_path.name}
    primary = languages["primary"]

    if primary == "python":
        pyproject = repo_path / "pyproject.toml"
        if pyproject.exists():
            data = parse_pyproject_toml(pyproject)
            proj = data.get("project", {})
            meta.update({
                "name": proj.get("name", repo_path.name),
                "version": proj.get("version", ""),
                "description": proj.get("description", ""),
                "dependencies": proj.get("dependencies", []),
            })

    elif primary in ("javascript", "typescript"):
        pkg = repo_path / "package.json"
        if pkg.exists():
            data = parse_package_json(pkg)
            meta.update({
                "name": data.get("name", repo_path.name),
                "version": data.get("version", ""),
                "description": data.get("description", ""),
                "dependencies": list(data.get("dependencies", {}).keys()),
            })

    elif primary == "rust":
        cargo = repo_path / "Cargo.toml"
        if cargo.exists():
            text = cargo.read_text(errors="replace")
            for field in ("name", "version", "description"):
                m = re.search(rf'^\s*{field}\s*=\s*"([^"]+)"', text, re.MULTILINE)
                if m:
                    meta[field] = m.group(1)

    elif primary == "go":
        gomod = repo_path / "go.mod"
        if gomod.exists():
            text = gomod.read_text(errors="replace")
            m = re.search(r'^module\s+(\S+)', text, re.MULTILINE)
            if m:
                meta["name"] = m.group(1).split("/")[-1]
                meta["module_path"] = m.group(1)

    return meta


def get_structure(repo_path: Path):
    """Get top-level directory structure with file counts."""
    structure = []
    for item in sorted(repo_path.iterdir()):
        if item.name in SKIP_DIRS or item.name.startswith("."):
            continue
        if item.is_dir():
            file_count = sum(1 for _ in item.rglob("*") if _.is_file())
            structure.append({"name": item.name, "type": "directory", "file_count": file_count})
        elif item.is_file():
            structure.append({"name": item.name, "type": "file", "size": item.stat().st_size})
    return structure


def analyze(repo_path: Path):
    """Run full analysis and return JSON report."""
    languages = detect_languages(repo_path)
    return {
        "repo_path": str(repo_path.resolve()),
        "languages": languages,
        "entry_points": find_entry_points(repo_path, languages),
        "docs": find_docs(repo_path),
        "examples": find_examples(repo_path),
        "api_surface": find_api_surface(repo_path, languages),
        "metadata": get_repo_metadata(repo_path, languages),
        "structure": get_structure(repo_path),
    }


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <repo-path>", file=sys.stderr)
        sys.exit(1)

    repo_path = Path(sys.argv[1]).resolve()
    if not repo_path.is_dir():
        print(f"Error: {repo_path} is not a directory", file=sys.stderr)
        sys.exit(1)

    report = analyze(repo_path)
    json.dump(report, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
