"""Watches src_code_base/ (in cwd) and in parallel:
  1. Mirrors pruned/skeleton output into src_code_base_pruned/
  2. Keeps codebase_map.md up to date
"""

import threading
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .pruner import prune_file
from . import history_manager as hm
from . import rules_generator

SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".venv", "venv", ".mypy_cache"}

_lock = threading.Lock()


def _paths():
    cwd = Path.cwd()
    return cwd / "src_code_base", cwd / "src_code_base_pruned"


def _out_path(src_path: Path, src_root: Path, out_root: Path) -> Path:
    return out_root / src_path.relative_to(src_root)


def _sync(src_path: Path, src_root: Path, out_root: Path, mode: str) -> None:
    if src_path.is_dir():
        return
    dest = _out_path(src_path, src_root, out_root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        pruned, stats = prune_file(src_path, mode)
        dest.write_text(pruned, encoding="utf-8")
        print(f"  [{mode}]  {src_path.relative_to(src_root)}  (saved {stats['saved']} tokens)")
    except Exception as exc:
        print(f"  error   {src_path.relative_to(src_root)}: {exc}")
    try:
        hm.update_file(src_root, src_path)
    except Exception as exc:
        print(f"  map-err {src_path.relative_to(src_root)}: {exc}")


def _delete(src_path: Path, src_root: Path, out_root: Path) -> None:
    dest = _out_path(src_path, src_root, out_root)
    if dest.exists():
        dest.unlink()
        print(f"  deleted {src_path.relative_to(src_root)}")
    try:
        hm.remove_file(src_root, src_path)
    except Exception:
        pass


class _Handler(FileSystemEventHandler):
    def __init__(self, mode: str, src_root: Path, out_root: Path):
        super().__init__()
        self.mode = mode
        self.src_root = src_root
        self.out_root = out_root

    def _skip(self, path: str) -> bool:
        return any(d in SKIP_DIRS for d in Path(path).parts)

    def on_created(self, event):
        if self._skip(event.src_path) or event.is_directory:
            return
        with _lock:
            _sync(Path(event.src_path), self.src_root, self.out_root, self.mode)

    def on_modified(self, event):
        if self._skip(event.src_path) or event.is_directory:
            return
        with _lock:
            _sync(Path(event.src_path), self.src_root, self.out_root, self.mode)

    def on_deleted(self, event):
        if self._skip(event.src_path) or event.is_directory:
            return
        with _lock:
            _delete(Path(event.src_path), self.src_root, self.out_root)

    def on_moved(self, event):
        if self._skip(event.src_path) or event.is_directory:
            return
        with _lock:
            _delete(Path(event.src_path), self.src_root, self.out_root)
            _sync(Path(event.dest_path), self.src_root, self.out_root, self.mode)


def initial_sync(mode: str = "format") -> None:
    src_root, out_root = _paths()
    print(f"Syncing {src_root} → {out_root}  [mode: {mode}]")
    for src_path in sorted(src_root.rglob("*")):
        if src_path.is_file() and not any(d in SKIP_DIRS for d in src_path.parts):
            _sync(src_path, src_root, out_root, mode)
    hm.full_rebuild(src_root)
    print("Initial sync complete.\n")


def watch(mode: str = "format") -> None:
    src_root, out_root = _paths()
    src_root.mkdir(exist_ok=True)
    out_root.mkdir(exist_ok=True)
    print("Generating LLM rule files...")
    rules_generator.generate()
    initial_sync(mode)
    observer = Observer()
    observer.schedule(_Handler(mode, src_root, out_root), str(src_root), recursive=True)
    observer.start()
    print(f"Watching {src_root}  [mode: {mode}]  (Ctrl-C to stop)")
    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
        print("\nWatcher stopped.")
