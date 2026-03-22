#!/usr/bin/env python3
"""Find and extract usage examples from a repository, output as markdown."""

import json
import re
import sys
from pathlib import Path


MAX_EXAMPLE_LINES = 80  # Truncate very long examples
MAX_EXAMPLES = 15


def extract_readme_code_blocks(repo_path: Path) -> list:
    """Extract code blocks from README files."""
    blocks = []
    for name in ["README.md", "README.rst", "README.txt", "README"]:
        readme = repo_path / name
        if readme.exists():
            text = readme.read_text(errors="replace")
            # Markdown fenced code blocks
            for m in re.finditer(r'```(\w*)\n(.*?)```', text, re.DOTALL):
                lang = m.group(1) or "text"
                code = m.group(2).strip()
                if len(code.split("\n")) >= 2:  # Skip trivial one-liners
                    blocks.append({
                        "source": name,
                        "language": lang,
                        "code": code,
                        "type": "readme",
                    })
            break
    return blocks


def extract_example_files(repo_path: Path, example_dirs: list) -> list:
    """Extract content from example files."""
    examples = []
    extensions = {".py", ".js", ".ts", ".rs", ".go", ".sh", ".rb"}

    for dir_info in example_dirs:
        if dir_info.get("type") != "directory":
            continue
        dir_path = repo_path / dir_info["path"]
        if not dir_path.is_dir():
            continue

        for file_path_str in dir_info.get("files", []):
            file_path = repo_path / file_path_str
            if not file_path.exists():
                continue
            if file_path.suffix not in extensions:
                continue

            try:
                content = file_path.read_text(errors="replace")
            except (OSError, UnicodeDecodeError):
                continue

            lines = content.split("\n")
            # Extract docstring/description from top of file
            description = ""
            if file_path.suffix == ".py":
                # Try to get module docstring
                first_lines = "\n".join(lines[:10])
                m = re.match(r'^(?:#.*\n)*\s*(?:"""(.*?)"""|\'\'\'(.*?)\'\'\')', first_lines, re.DOTALL)
                if m:
                    description = (m.group(1) or m.group(2) or "").strip().split("\n")[0]

            # For files with shebang/comments at top, extract description
            if not description:
                for line in lines[:5]:
                    line = line.strip()
                    if line.startswith("#") and not line.startswith("#!"):
                        description = line.lstrip("# ").strip()
                        break

            # Truncate long files
            if len(lines) > MAX_EXAMPLE_LINES:
                content = "\n".join(lines[:MAX_EXAMPLE_LINES]) + f"\n# ... ({len(lines) - MAX_EXAMPLE_LINES} more lines)"

            examples.append({
                "source": file_path_str,
                "description": description,
                "code": content.strip(),
                "language": file_path.suffix.lstrip("."),
                "type": "file",
                "line_count": len(lines),
            })

    # Sort: shorter examples first (simpler is usually better for learning)
    examples.sort(key=lambda x: x["line_count"])
    return examples[:MAX_EXAMPLES]


def format_markdown(readme_blocks: list, file_examples: list, repo_name: str) -> str:
    """Format all examples as markdown."""
    sections = [f"# Examples for {repo_name}\n"]

    if readme_blocks:
        sections.append("## From README\n")
        for i, block in enumerate(readme_blocks[:8]):
            sections.append(f"### README Example {i + 1}\n")
            sections.append(f"```{block['language']}")
            sections.append(block["code"])
            sections.append("```\n")

    if file_examples:
        sections.append("## Example Files\n")
        for ex in file_examples:
            title = ex["description"] or ex["source"]
            sections.append(f"### {title}\n")
            sections.append(f"**Source:** `{ex['source']}`\n")
            lang = {"py": "python", "js": "javascript", "ts": "typescript", "rs": "rust"}.get(
                ex["language"], ex["language"]
            )
            sections.append(f"```{lang}")
            sections.append(ex["code"])
            sections.append("```\n")

    return "\n".join(sections)


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <repo-path> [--analysis <analysis.json>]", file=sys.stderr)
        sys.exit(1)

    repo_path = Path(sys.argv[1]).resolve()
    analysis = None

    if "--analysis" in sys.argv:
        idx = sys.argv.index("--analysis")
        with open(sys.argv[idx + 1]) as f:
            analysis = json.load(f)

    repo_name = repo_path.name
    if analysis:
        repo_name = analysis.get("metadata", {}).get("name", repo_name)

    # Extract from README
    readme_blocks = extract_readme_code_blocks(repo_path)

    # Extract from example files
    example_dirs = analysis.get("examples", []) if analysis else []
    if not example_dirs:
        # Auto-detect
        for dirname in ["examples", "example", "demos", "demo", "tutorial"]:
            d = repo_path / dirname
            if d.is_dir():
                files = []
                for f in d.rglob("*"):
                    if f.is_file() and f.suffix in {".py", ".js", ".ts", ".rs", ".go"}:
                        files.append(str(f.relative_to(repo_path)))
                example_dirs.append({"type": "directory", "path": dirname, "files": files})

    file_examples = extract_example_files(repo_path, example_dirs)

    # Output
    print(format_markdown(readme_blocks, file_examples, repo_name))


if __name__ == "__main__":
    main()
