"""Maintains codebase_map.md in the current working directory.

Each entry records the file path, exported classes/functions, and a
1-sentence purpose derived from its docstring or leading comment.
"""

import ast
import re
from datetime import datetime
from pathlib import Path

SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".venv", "venv", ".mypy_cache"}

_EXT_LABELS = {
    ".json": "JSON data file",
    ".yaml": "YAML configuration",
    ".yml": "YAML configuration",
    ".toml": "TOML configuration",
    ".cfg": "configuration file",
    ".ini": "configuration file",
    ".env": "environment variables",
    ".md": "Markdown document",
    ".txt": "plain text file",
    ".sh": "shell script",
    ".sql": "SQL query / schema",
    ".hql": "Hive query",
    ".hive": "Hive query",
    ".js": "JavaScript module",
    ".jsx": "React component",
    ".ts": "TypeScript module",
    ".tsx": "React TypeScript component",
}


def _map_file() -> Path:
    return Path.cwd() / "codebase_map.md"


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def _extract_python(path: Path):
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
    except Exception:
        return [], ""

    purpose = ""
    if (tree.body
            and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)):
        purpose = tree.body[0].value.value.strip().splitlines()[0]

    exports = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            exports.append(f"class {node.name}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            exports.append(f"def {node.name}")

    if not purpose and exports:
        n_cls = sum(1 for e in exports if e.startswith("class"))
        n_fn = sum(1 for e in exports if e.startswith("def"))
        parts = []
        if n_cls:
            parts.append(f"{n_cls} class{'es' if n_cls > 1 else ''}")
        if n_fn:
            parts.append(f"{n_fn} function{'s' if n_fn > 1 else ''}")
        purpose = "Defines " + " and ".join(parts) + "."

    return exports, purpose


def _extract_generic(path: Path):
    ext = path.suffix.lower()
    comment_chars = {
        ".yaml": "#", ".yml": "#", ".toml": "#",
        ".cfg": "#", ".ini": "#", ".sh": "#",
        ".sql": "--", ".hql": "--", ".hive": "--",
        ".js": "//", ".ts": "//", ".jsx": "//", ".tsx": "//",
    }
    purpose = ""
    prefix = comment_chars.get(ext)
    if prefix:
        try:
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if line.startswith(prefix):
                    candidate = line.lstrip(prefix).strip(" -")
                    if len(candidate) > 4:
                        purpose = candidate
                        break
        except Exception:
            pass
    elif ext in (".txt", ".md"):
        try:
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip().lstrip("#").strip()
                if len(line) > 4:
                    purpose = line
                    break
        except Exception:
            pass

    return [], purpose or _EXT_LABELS.get(ext, f"{ext} file")


def _build_row(src_root: Path, path: Path) -> str:
    rel = path.relative_to(src_root)
    if path.suffix.lower() == ".py":
        exports, purpose = _extract_python(path)
    else:
        exports, purpose = _extract_generic(path)
    exports_str = ", ".join(f"`{e}`" for e in exports) if exports else "—"
    return f"| `{rel}` | {exports_str} | {purpose} |"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def update_file(src_root: Path, path: Path) -> None:
    _ensure_map()
    rel = str(path.relative_to(src_root))
    new_row = _build_row(src_root, path)
    map_file = _map_file()
    lines = map_file.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if re.match(rf"^\| `{re.escape(rel)}`", line):
            lines[i] = new_row
            map_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return
    lines.append(new_row)
    map_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def remove_file(src_root: Path, path: Path) -> None:
    map_file = _map_file()
    if not map_file.exists():
        return
    rel = re.escape(str(path.relative_to(src_root)))
    lines = map_file.read_text(encoding="utf-8").splitlines()
    lines = [ln for ln in lines if not re.match(rf"^\| `{rel}`", ln)]
    map_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def full_rebuild(src_root: Path) -> None:
    rows = []
    for path in sorted(src_root.rglob("*")):
        if path.is_file() and not any(d in SKIP_DIRS for d in path.parts):
            rows.append(_build_row(src_root, path))

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    content = (
        "# Codebase Map\n\n"
        f"Auto-generated index — last rebuilt {timestamp}.\n\n"
        "| File | Exports | Purpose |\n"
        "|---|---|---|\n"
        + "\n".join(rows) + "\n"
    )
    _map_file().write_text(content, encoding="utf-8")
    print(f"  codebase_map.md rebuilt ({len(rows)} files)")


def _ensure_map() -> None:
    map_file = _map_file()
    if not map_file.exists():
        map_file.write_text(
            "# Codebase Map\n\n"
            "Auto-generated index. Updated on every file change.\n\n"
            "| File | Exports | Purpose |\n"
            "|---|---|---|\n",
            encoding="utf-8",
        )
