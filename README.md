# codewatch-token-optimizer

> Automatically prunes and indexes any codebase to minimize AI context tokens — works with Cursor, Claude, and any LLM tool.

---

## What it does

Drop a codebase into `src_code_base/`. The watcher immediately:
- Writes a token-reduced copy to `src_code_base_pruned/`
- Updates `codebase_map.md` — a living index of every file's exports and purpose

Point your AI tool at the pruned folder and the map. Feed less. Get more.

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
# Start the watcher (creates src_code_base/ and src_code_base_pruned/ automatically)
token-optimizer watch

# Architectural overview mode — stubs all function bodies with ...
token-optimizer watch --mode skeleton

# One-shot prune without watching
token-optimizer sync
token-optimizer sync --mode skeleton

# Prune a single file
token-optimizer prune path/to/file.py
token-optimizer prune path/to/file.py --mode skeleton
```

Clone any repo directly into the watch folder and it's pruned instantly:

```bash
git clone <your-repo-url> src_code_base/
```

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

Use it as a high-level context file — give it to your AI before diving into any specific file.

---

## Workflow

```
1. token-optimizer watch --mode skeleton   →  see the full shape of the codebase cheaply
2. read codebase_map.md                    →  find the files that matter
3. token-optimizer watch                   →  zoom into implementation detail
```

---

## License

MIT
