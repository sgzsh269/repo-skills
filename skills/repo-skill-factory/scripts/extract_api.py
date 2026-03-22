#!/usr/bin/env python3
"""Extract public API signatures from source files and output as markdown."""

import ast
import json
import re
import sys
from pathlib import Path


def extract_python_api(file_path: Path, module_name: str = "") -> str:
    """Extract public classes and functions from a Python file."""
    try:
        source = file_path.read_text(errors="replace")
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return ""

    sections = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            sections.append(format_class(node, source))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                sections.append(format_function(node, source))

    if not sections:
        return ""

    header = f"### `{module_name}`" if module_name else f"### `{file_path.name}`"
    return header + "\n\n" + "\n\n".join(sections)


def format_class(node: ast.ClassDef, source: str) -> str:
    """Format a class definition with its public methods."""
    lines = []

    # Class signature with bases
    bases = []
    for base in node.bases:
        bases.append(ast.get_source_segment(source, base) or ast.dump(base))
    base_str = f"({', '.join(bases)})" if bases else ""
    lines.append(f"**class `{node.name}{base_str}`**")

    # Docstring
    docstring = ast.get_docstring(node)
    if docstring:
        # Take first paragraph only
        first_para = docstring.split("\n\n")[0].strip()
        lines.append(f"> {first_para}")

    # Public methods
    methods = []
    for child in node.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if child.name.startswith("_") and child.name != "__init__":
                continue
            sig = get_function_signature(child, source)
            method_doc = ast.get_docstring(child)
            prefix = "async " if isinstance(child, ast.AsyncFunctionDef) else ""
            desc = f" — {method_doc.split(chr(10))[0]}" if method_doc else ""
            methods.append(f"- `{prefix}{sig}`{desc}")

    if methods:
        lines.append("\nMethods:")
        lines.extend(methods)

    return "\n".join(lines)


def format_function(node, source: str) -> str:
    """Format a standalone function."""
    prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    sig = get_function_signature(node, source)
    lines = [f"**`{prefix}{sig}`**"]

    docstring = ast.get_docstring(node)
    if docstring:
        first_para = docstring.split("\n\n")[0].strip()
        lines.append(f"> {first_para}")

    return "\n".join(lines)


def simplify_annotation(ann_str: str) -> str:
    """Simplify complex type annotations (e.g., Annotated[str, typer.Option(...)])."""
    if not ann_str:
        return ann_str
    # Simplify Annotated[X, ...] -> X (handle nested brackets in X)
    if ann_str.startswith("Annotated["):
        # Find the first top-level comma (respecting bracket nesting)
        depth = 0
        for i, ch in enumerate(ann_str[len("Annotated["):], len("Annotated[")):
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            elif ch == "," and depth == 0:
                return ann_str[len("Annotated["):i].strip()
        # No comma found, strip outer Annotated[]
        return ann_str[len("Annotated["):-1].strip() if ann_str.endswith("]") else ann_str
    # Truncate very long annotations
    if len(ann_str) > 60:
        return ann_str[:57] + "..."
    return ann_str


def get_function_signature(node, source: str) -> str:
    """Extract function signature as a string."""
    name = node.name
    args = []

    for arg in node.args.args:
        if arg.arg == "self" or arg.arg == "cls":
            continue
        annotation = ""
        if arg.annotation:
            ann_str = ast.get_source_segment(source, arg.annotation)
            if ann_str:
                ann_str = simplify_annotation(ann_str)
                annotation = f": {ann_str}"
        args.append(f"{arg.arg}{annotation}")

    # *args
    if node.args.vararg:
        args.append(f"*{node.args.vararg.arg}")
    # **kwargs
    if node.args.kwarg:
        args.append(f"**{node.args.kwarg.arg}")

    # Return type
    ret = ""
    if node.returns:
        ret_str = ast.get_source_segment(source, node.returns)
        if ret_str:
            ret = f" -> {ret_str}"

    return f"{name}({', '.join(args)}){ret}"


def extract_js_ts_api(file_path: Path) -> str:
    """Extract exports from JS/TS files using regex."""
    try:
        source = file_path.read_text(errors="replace")
    except UnicodeDecodeError:
        return ""

    lines = []

    # export class/function/const
    for m in re.finditer(
        r'export\s+(?:default\s+)?(?:abstract\s+)?(class|function|const|let|var|interface|type|enum)\s+(\w+)',
        source
    ):
        kind, name = m.group(1), m.group(2)
        lines.append(f"- `export {kind} {name}`")

    # export { ... }
    for m in re.finditer(r'export\s*\{([^}]+)\}', source):
        names = [n.strip().split(" as ")[0].strip() for n in m.group(1).split(",")]
        for n in names:
            if n:
                lines.append(f"- `export {{ {n} }}`")

    if not lines:
        return ""

    return f"### `{file_path.name}`\n\n" + "\n".join(lines)


def extract_rust_api(file_path: Path) -> str:
    """Extract pub items from Rust files using regex."""
    try:
        source = file_path.read_text(errors="replace")
    except UnicodeDecodeError:
        return ""

    lines = []
    for m in re.finditer(
        r'pub\s+(?:async\s+)?(fn|struct|enum|trait|type|const|static|mod)\s+(\w+)',
        source
    ):
        kind, name = m.group(1), m.group(2)
        lines.append(f"- `pub {kind} {name}`")

    if not lines:
        return ""

    return f"### `{file_path.name}`\n\n" + "\n".join(lines)


def extract_go_api(file_path: Path) -> str:
    """Extract exported (capitalized) items from Go files."""
    try:
        source = file_path.read_text(errors="replace")
    except UnicodeDecodeError:
        return ""

    lines = []
    # Exported functions
    for m in re.finditer(r'^func\s+(?:\([^)]+\)\s+)?([A-Z]\w*)\s*\(', source, re.MULTILINE):
        lines.append(f"- `func {m.group(1)}(...)`")
    # Exported types
    for m in re.finditer(r'^type\s+([A-Z]\w*)\s+(struct|interface)', source, re.MULTILINE):
        lines.append(f"- `type {m.group(1)} {m.group(2)}`")

    if not lines:
        return ""

    return f"### `{file_path.name}`\n\n" + "\n".join(lines)


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

    # Determine files to analyze
    files_to_analyze = []
    primary_lang = "python"

    if analysis:
        primary_lang = analysis.get("languages", {}).get("primary", "python")
        for entry in analysis.get("api_surface", []):
            if "source" in entry:
                files_to_analyze.append(repo_path / entry["source"])
            if "module" in entry:
                files_to_analyze.append(repo_path / entry["module"])
            if "files" in entry:
                for f in entry["files"]:
                    files_to_analyze.append(repo_path / f)
    else:
        # Auto-detect: find main source files
        src = repo_path / "src"
        if src.is_dir():
            for py in src.rglob("*.py"):
                if not py.name.startswith("_") or py.name == "__init__.py":
                    files_to_analyze.append(py)
        else:
            for py in repo_path.rglob("*.py"):
                if not any(p in str(py) for p in ["test", "venv", "node_modules"]):
                    files_to_analyze.append(py)

    # Deduplicate and sort
    seen = set()
    unique_files = []
    for f in files_to_analyze:
        if f.exists() and f not in seen:
            seen.add(f)
            unique_files.append(f)

    # Extract and format
    print("# API Reference\n")

    extractors = {
        "python": extract_python_api,
        "javascript": extract_js_ts_api,
        "typescript": extract_js_ts_api,
        "rust": extract_rust_api,
        "go": extract_go_api,
    }

    extractor = extractors.get(primary_lang, extract_python_api)

    for file_path in sorted(unique_files):
        rel_path = file_path.relative_to(repo_path)
        module_name = str(rel_path).replace("/", ".").replace(".py", "")

        if primary_lang == "python":
            result = extract_python_api(file_path, module_name)
        else:
            result = extractor(file_path)

        if result:
            print(result)
            print()


if __name__ == "__main__":
    main()
