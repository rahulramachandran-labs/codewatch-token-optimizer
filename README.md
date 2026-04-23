# codewatch-token-optimizer

> Automatically prunes and indexes any codebase to minimize AI context tokens — works with Cursor, Claude, Copilot, Windsurf, and any LLM tool.

---

## What it does

Drop a codebase into `src_code_base/`. The watcher immediately:
- Writes a token-reduced copy to `src_code_base_pruned/`
- Updates `codebase_map.md` — a living index of every file's exports and purpose
- Generates rule files for every major LLM tool so they always edit originals, never pruned copies

---

## Requirements

- Python 3.9 or newer

---

## Installation

```bash
git clone https://github.com/rahulramachandran-labs/codewatch-token-optimizer
cd codewatch-token-optimizer
pip install .
```

---

## Usage

```bash
# Start the watcher (creates folders + rule files automatically)
token-optimizer watch

# Architectural overview mode — stubs all function bodies with ...
token-optimizer watch --mode skeleton

# One-shot prune without watching
token-optimizer sync
token-optimizer sync --mode skeleton

# Prune a single file to stdout
token-optimizer prune path/to/file.py
token-optimizer prune path/to/file.py --mode skeleton

# Generate LLM rule files only (without watching)
token-optimizer rules
```

Clone any repo directly into the watch folder:

```bash
git clone <your-repo-url> src_code_base/
```

---

## How to use with your LLM tool

```
1. token-optimizer watch
2. Point your LLM at src_code_base_pruned/<file>  ← token-optimized context
3. LLM suggests a fix
4. Edit src_code_base/<file>                       ← the original
5. Watcher detects the change and re-prunes automatically
```

The pruned files are **read-only context**. Your LLM tool should never edit them directly. The rule files generated at startup enforce this automatically.

---

## LLM rule files (auto-generated on every watch start)

| Tool | File generated |
|---|---|
| Cursor | `.cursorrules` |
| Claude Code | `CLAUDE.md` |
| GitHub Copilot | `.github/copilot-instructions.md` |
| Windsurf | `.windsurfrules` |

All four files share the same rule: *read from pruned, edit in original*. Generated from one source of truth — change `rules_generator.py` to update all tools at once.

---

## Modes

| Mode | What it removes | Best for |
|---|---|---|
| `format` (default) | Docstrings, type hints, comments | Reading implementation detail |
| `skeleton` | Entire function/method bodies (replaced with `...`) | Architectural overview, 40–95% token savings |

---

## Supported file types

| Extension | Strategy |
|---|---|
| `.py` | AST-based — precise, structure-aware |
| `.sql` `.hql` `.hive` `.sparksql` | sqlglot parse + reformat |
| `.js` `.jsx` `.ts` `.tsx` | Strips comments and console calls |
| Everything else | Whitespace normalization |

---

## codebase_map.md

Generated automatically in your working directory on every file change.

| File | Exports | Purpose |
|---|---|---|
| `utils/orders.py` | `class OrderProcessor`, `def send_confirmation` | Order processing utilities. |
| `config/settings.yaml` | — | YAML configuration |

---

## Workflow

```
1. token-optimizer watch --mode skeleton   →  map the full codebase cheaply
2. read codebase_map.md                    →  find the files that matter
3. feed pruned file to LLM                 →  get fix suggestions with minimal tokens
4. edit original file in src_code_base/   →  apply the fix
5. watcher re-prunes automatically         →  pruned copy stays in sync
```

---

## License

MIT
