# codewatch-token-optimizer

Watches a source directory and automatically produces token-optimized copies of every file, plus a living index of the entire codebase. Reduces context size when feeding code to AI tools like Cursor.

---

## How it works

Drop any codebase into `src_code_base/`. The watcher runs two tasks in parallel on every file change:

1. **Prune** — writes a reduced copy to `src_code_base_pruned/`
2. **Map** — updates `codebase_map.md` with the file's exports and purpose

The pruned folder is what you point your AI tool at. `codebase_map.md` gives the AI a high-level index of the entire codebase before it zooms into any file. Original files stay untouched.

---

## Project structure

```
codewatch-token-optimizer/
├── pyproject.toml           # Package definition — pip install . registers the CLI
├── token_optimizer/
│   ├── cli.py               # Entry point for the token-optimizer command
│   ├── pruner.py            # Core pruning logic — format and skeleton modes
│   ├── watcher.py           # Watchdog: mirrors files + refreshes codebase_map.md
│   └── history_manager.py   # Builds and maintains codebase_map.md
├── src_code_base/           # Drop your source code here
└── src_code_base_pruned/    # Pruned output appears here automatically
```

---

## Install & run (any OS)

```bash
# 1. Clone
git clone https://github.com/rahulramachandran-labs/codewatch-token-optimizer
cd codewatch-token-optimizer

# 2. Install (once)
pip install .

# 3. Start the watcher
token-optimizer watch
```

---

## Modes

### `--mode format` (default)
Strips docstrings, type annotations, and comments. Keeps all logic intact. Best for reading and understanding implementation detail.

```python
# Input
def calculate_discount(price: float, rate: float) -> float:
    """Apply a percentage discount to a price."""
    return price * (1 - rate)

# Output
def calculate_discount(price, rate):
    return price * (1 - rate)
```

### `--mode skeleton`
Replaces every function and method body with `...`. Keeps full signatures including type annotations. Best for architectural overviews — 40–95% token savings on large codebases.

```python
# Input
class OrderProcessor:
    def create_order(self, user_id: int, items: list[str]) -> dict:
        order = {"user": user_id, "items": items}
        self.cache[user_id] = order
        return order

# Output
class OrderProcessor:
    def create_order(self, user_id: int, items: list[str]) -> dict:
        ...
```

---

## Pruning strategy by file type

| Extension | Strategy |
|---|---|
| `.py` | AST-based: format strips docstrings/hints; skeleton stubs all bodies |
| `.sql`, `.hql`, `.hive`, `.sparksql` | sqlglot parse + reformat |
| `.js`, `.jsx`, `.ts`, `.tsx` | Regex: removes block/line comments and console.* calls |
| Everything else | Generic: strips trailing whitespace, collapses blank lines |

Generic covers `.txt`, `.yaml`, `.json`, `.toml`, `.cfg`, `.ini`, `.md`, and any other format.

---

## codebase_map.md

Every file change refreshes an entry in `codebase_map.md` in the working directory. Use it as your Historical Summary Context — give it to the AI before asking about any specific file.

| File | Exports | Purpose |
|---|---|---|
| `utils/orders.py` | `class OrderProcessor`, `def send_confirmation` | Order processing utilities. |
| `config/settings.yaml` | — | YAML configuration |

---

## All commands

```bash
token-optimizer watch                        # watch + auto-prune (format mode)
token-optimizer watch --mode skeleton        # watch + skeleton mode
token-optimizer sync                         # one-shot sync, then exit
token-optimizer sync --mode skeleton
token-optimizer prune path/to/file.py        # prune a single file to stdout
token-optimizer prune path/to/file.py --mode skeleton
token-optimizer --help
```

### Zoom-in workflow
1. `token-optimizer watch --mode skeleton` — maps the whole codebase with minimal tokens
2. Read `codebase_map.md` to find the relevant files
3. Switch to `format` mode to zoom into implementation detail

---

## Dependencies

- **tiktoken** — token counting (cl100k_base, same encoding as GPT-4)
- **sqlglot** — SQL/HQL/Spark dialect parsing and reformatting
- **watchdog** — cross-platform file system event monitoring
