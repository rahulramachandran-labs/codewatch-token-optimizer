"""Generates LLM rule files so all tools know to edit originals, not pruned copies."""

from pathlib import Path

_CORE_RULE = """\
Files in `src_code_base_pruned/` are AUTO-GENERATED and READ-ONLY.
NEVER edit files inside `src_code_base_pruned/`.
Always edit the corresponding original file in `src_code_base/`.
The watcher automatically re-prunes originals on every save.

Read  → src_code_base_pruned/  (token-optimized context for the LLM)
Edit  → src_code_base/         (the real source of truth)

Use `codebase_map.md` for a high-level index of every file's exports and purpose.\
"""

_FILES = {
    ".cursorrules": f"# codewatch-token-optimizer\n\n{_CORE_RULE}\n",

    ".windsurfrules": f"# codewatch-token-optimizer\n\n{_CORE_RULE}\n",

    "CLAUDE.md": f"""\
# codewatch-token-optimizer

## Rules

{_CORE_RULE}
""",

    ".github/copilot-instructions.md": f"""\
# codewatch-token-optimizer

{_CORE_RULE}
""",
}


def generate(cwd: Path = None) -> None:
    root = cwd or Path.cwd()
    for rel_path, content in _FILES.items():
        dest = root / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        print(f"  wrote   {rel_path}")
