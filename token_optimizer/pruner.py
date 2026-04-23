"""Prunes files to reduce token count. Supports Python, SQL, JS/TS, and generic text.

Modes:
  format   — strip docstrings, type hints, comments (default)
  skeleton — keep only signatures; replace all function/method bodies with ...
"""

import ast
import re
from pathlib import Path

try:
    import sqlglot
    HAS_SQLGLOT = True
except ImportError:
    HAS_SQLGLOT = False

try:
    import tiktoken
    _enc = tiktoken.get_encoding("cl100k_base")
    def count_tokens(text: str) -> int:
        return len(_enc.encode(text))
except ImportError:
    def count_tokens(text: str) -> int:
        return len(text) // 4


# ---------------------------------------------------------------------------
# Format mode — strip noise, keep logic
# ---------------------------------------------------------------------------

def _prune_python(source: str) -> str:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return _prune_generic(source)

    class DocstringStripper(ast.NodeTransformer):
        def _strip_docstring(self, node):
            if (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)):
                node.body = node.body[1:] or [ast.Pass()]
            return node

        def visit_FunctionDef(self, node):
            self.generic_visit(node)
            node.returns = None
            for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
                arg.annotation = None
            if node.args.vararg:
                node.args.vararg.annotation = None
            if node.args.kwarg:
                node.args.kwarg.annotation = None
            return self._strip_docstring(node)

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_ClassDef(self, node):
            self.generic_visit(node)
            return self._strip_docstring(node)

        def visit_Module(self, node):
            self.generic_visit(node)
            return self._strip_docstring(node)

        def visit_AnnAssign(self, node):
            if node.value is None:
                return None
            return ast.Assign(
                targets=[node.target],
                value=node.value,
                lineno=node.lineno,
                col_offset=node.col_offset,
            )

    stripped = DocstringStripper().visit(tree)
    ast.fix_missing_locations(stripped)
    try:
        return ast.unparse(stripped)
    except Exception:
        return _prune_generic(source)


def _prune_sql(source: str, dialect: str = "") -> str:
    if not HAS_SQLGLOT:
        return _prune_generic(source)
    try:
        statements = sqlglot.parse(source, dialect=dialect or None)
        return "\n".join(s.sql(dialect=dialect or "spark") for s in statements if s)
    except Exception:
        return _prune_generic(source)


def _prune_js_ts(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    source = re.sub(r"//[^\n]*", "", source)
    source = re.sub(r"console\.\w+\([^)]*\);?", "", source)
    return _strip_extra_blank_lines(source)


def _prune_generic(source: str) -> str:
    lines = [ln.rstrip() for ln in source.splitlines()]
    return _strip_extra_blank_lines("\n".join(lines))


# ---------------------------------------------------------------------------
# Skeleton mode — keep API surface only, stub all bodies with ...
# ---------------------------------------------------------------------------

def _skeleton_python(source: str) -> str:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source

    def _ellipsis_stmt(lineno: int, col: int) -> ast.Expr:
        node = ast.Expr(value=ast.Constant(value=...))
        node.lineno = lineno
        node.col_offset = col + 4
        node.end_lineno = lineno
        node.end_col_offset = col + 7
        node.value.lineno = node.lineno
        node.value.col_offset = node.col_offset
        node.value.end_lineno = node.end_lineno
        node.value.end_col_offset = node.end_col_offset
        return node

    class Skeletonizer(ast.NodeTransformer):
        def _stub(self, node):
            node.body = [_ellipsis_stmt(node.lineno, node.col_offset)]
            ast.fix_missing_locations(node)
            return node

        def visit_FunctionDef(self, node):
            return self._stub(node)

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_ClassDef(self, node):
            self.generic_visit(node)
            if not node.body:
                node.body = [_ellipsis_stmt(node.lineno, node.col_offset)]
                ast.fix_missing_locations(node)
            return node

    result = Skeletonizer().visit(tree)
    ast.fix_missing_locations(result)
    try:
        return ast.unparse(result)
    except Exception:
        return source


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _strip_extra_blank_lines(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text).strip()


EXTENSION_MAP = {
    ".py": "python",
    ".sql": "sql",
    ".hql": "hive",
    ".hive": "hive",
    ".sparksql": "spark",
    ".js": "js",
    ".jsx": "js",
    ".ts": "ts",
    ".tsx": "ts",
}


def prune(source: str, ext: str, mode: str = "format") -> str:
    lang = EXTENSION_MAP.get(ext.lower(), "generic")
    if mode == "skeleton" and lang == "python":
        return _skeleton_python(source)
    if lang == "python":
        return _prune_python(source)
    if lang in ("sql", "hive", "spark"):
        return _prune_sql(source, "" if lang == "sql" else lang)
    if lang in ("js", "ts"):
        return _prune_js_ts(source)
    return _prune_generic(source)


def prune_file(path: Path, mode: str = "format") -> tuple:
    source = path.read_text(encoding="utf-8", errors="replace")
    pruned = prune(source, path.suffix, mode)
    before = count_tokens(source)
    after = count_tokens(pruned)
    return pruned, {"before_tokens": before, "after_tokens": after, "saved": before - after, "mode": mode}
