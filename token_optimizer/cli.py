"""token-optimizer CLI.

Commands:
  token-optimizer watch [--mode format|skeleton]        watch src_code_base/ and auto-prune
  token-optimizer sync  [--mode format|skeleton]        one-shot sync
  token-optimizer prune <file> [--mode format|skeleton] prune a single file to stdout

Modes:
  format    Strip docstrings, type hints, comments. Keeps all logic intact. (default)
  skeleton  Replace every function/method body with '...'. API surface only.
            Ideal for architectural overviews — 40-95% token savings on large codebases.

The watcher always keeps codebase_map.md up to date with each file's exports
and purpose, regardless of mode.
"""

import sys
from pathlib import Path

from .pruner import prune_file


def _parse_mode(args: list) -> tuple:
    mode = "format"
    remaining = []
    i = 0
    while i < len(args):
        if args[i] == "--mode" and i + 1 < len(args):
            mode = args[i + 1]
            if mode not in ("format", "skeleton"):
                print(f"Unknown mode '{mode}'. Use 'format' or 'skeleton'.")
                sys.exit(1)
            i += 2
        else:
            remaining.append(args[i])
            i += 1
    return mode, remaining


def cmd_watch(mode: str) -> None:
    from .watcher import watch
    watch(mode)


def cmd_sync(mode: str) -> None:
    from .watcher import initial_sync
    initial_sync(mode)


def cmd_prune(path_str: str, mode: str) -> None:
    path = Path(path_str)
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)
    pruned, stats = prune_file(path, mode)
    print(pruned)
    print(
        f"\n---\nmode: {stats['mode']}  "
        f"before: {stats['before_tokens']} tokens  "
        f"after: {stats['after_tokens']} tokens  "
        f"saved: {stats['saved']} tokens",
        file=sys.stderr,
    )


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return

    cmd = args[0]
    rest = args[1:]

    if cmd == "watch":
        mode, _ = _parse_mode(rest)
        cmd_watch(mode)
    elif cmd == "sync":
        mode, _ = _parse_mode(rest)
        cmd_sync(mode)
    elif cmd == "prune":
        mode, rest2 = _parse_mode(rest)
        if not rest2:
            print("Usage: token-optimizer prune <file> [--mode format|skeleton]")
            sys.exit(1)
        cmd_prune(rest2[0], mode)
    else:
        print(f"Unknown command: {cmd}\n{__doc__}")
        sys.exit(1)
