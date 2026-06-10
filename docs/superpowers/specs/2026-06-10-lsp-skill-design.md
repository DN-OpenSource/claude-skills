# LSP Skill — Design

**Date:** 2026-06-10
**Status:** Approved for implementation
**Repo:** claude-skills

## Purpose

A new skill, `lsp`, that teaches Claude to use real language servers for semantic code
navigation instead of grep-based guessing. It covers go-to-definition, find-references,
hover/type info, document and workspace symbols, diagnostics, and safe project-wide
rename.

**Triggers:** tasks like "where is X defined", "find all usages of Y", "rename Z
everywhere", impact analysis before a refactor, and exploring large codebases where
text search produces too many false positives.

**Out of scope:** code actions, formatting, organize-imports, building LSP servers.
Rename is the only write operation.

## Supported stacks

The same four stacks as codebase-guardian, so the two skills compose:

| Stack | Language server | Install hint |
|-------|----------------|--------------|
| TypeScript/Node | `typescript-language-server --stdio` | `npm i -g typescript-language-server typescript` |
| Python | `pyright-langserver --stdio` | `npm i -g pyright` |
| Dart/Flutter | `dart language-server --protocol=lsp` | ships with the Dart SDK |
| Rust | `rust-analyzer` | `rustup component add rust-analyzer` |

## Directory structure

Mirrors codebase-guardian:

```
skills/lsp/
├── .claude-plugin/plugin.json
├── README.md
├── SKILL.md
├── scripts/
│   └── lsp.py              ← stdlib-only Python JSON-RPC client
└── references/
    ├── typescript.md
    ├── python.md
    ├── flutter.md
    └── rust.md
```

Each `references/<stack>.md` documents: the server command, install instructions,
detection markers, known startup quirks (e.g. rust-analyzer indexing latency), and any
server-specific initialization options.

## Helper script: `scripts/lsp.py`

A single cross-platform Python 3 script using only the standard library. It speaks
JSON-RPC over stdio to any LSP server.

### Lifecycle: one-shot with batching

Each invocation: start server → `initialize`/`initialized` → open the relevant
document(s) → run one or more queries → `shutdown`/`exit`. No daemon, no state between
invocations. Batch mode accepts multiple queries in a single run so a
definition + references pair pays server startup/indexing cost once.

### CLI surface

```
python lsp.py [--server "<cmd>"] [--root <dir>] [--json] [--timeout <sec>] <subcommand> ...
```

- `--server` overrides auto-detection. Auto-detection walks project markers:
  `tsconfig.json`/`package.json` → typescript-language-server, `pyproject.toml`/
  `setup.py`/`requirements.txt` → pyright, `pubspec.yaml` → dart, `Cargo.toml` →
  rust-analyzer.
- Positions on the CLI are 1-based `file:line:col` (converted internally to LSP's
  0-based positions).
- Default output is concise, human-readable `file:line:col — snippet` lines
  (clickable in terminals); `--json` emits raw LSP responses.

### Subcommands

| Subcommand | LSP request | Notes |
|------------|------------|-------|
| `definition FILE:LINE:COL` | `textDocument/definition` | |
| `references FILE:LINE:COL` | `textDocument/references` | includes declaration |
| `hover FILE:LINE:COL` | `textDocument/hover` | type info / docs |
| `symbols FILE` | `textDocument/documentSymbol` | file outline |
| `workspace-symbols QUERY` | `workspace/symbol` | search by name |
| `diagnostics FILE...` | `textDocument/publishDiagnostics` | waits for server push |
| `rename FILE:LINE:COL NEW_NAME` | `textDocument/rename` | dry-run by default; `--apply` writes the WorkspaceEdit |
| `batch` | n/a | multiple queries (one per line on stdin or as repeated args) in one server session |

### Rename safety

`rename` without flags is a dry run: it prints every file and line the WorkspaceEdit
would touch, grouped by file, and writes nothing. `--apply` applies the edits to disk.
The skill workflow requires a dry run and review before `--apply`.

### Error handling

- Per-query timeout (default ~30s, configurable) — a hung server never hangs Claude.
- Server binary missing → exit with the stack's install hint.
- Server crash / empty response → clear error message, non-zero exit.
- The SKILL.md instructs Claude to fall back to grep-based search whenever the script
  fails for any reason — the skill never blocks the user's task.

## SKILL.md workflow

1. **Detect & verify.** Identify the stack from project markers, read the matching
   `references/<stack>.md`, verify the server binary is on PATH. Missing → show install
   hint, fall back to grep.
2. **Query.** Run navigation queries through `lsp.py`, batching related queries into
   one invocation.
3. **Rename flow.** Dry-run → review the touched locations (sanity-check count and
   spread) → `--apply` → validate the result: via codebase-guardian's toolchain loop if
   that skill is installed, otherwise a plain type-check/test run.
4. **Record learnings.** Server quirks, startup flags, or detection overrides worth
   keeping go to MEMORY.md (via the memory skill if installed, by hand otherwise).

## Composability

Follows the repo's rule: self-contained, never errors because a companion skill is
absent.

- **lsp + codebase-guardian** — guardian's Orient phase can use lsp for impact
  analysis; lsp's rename flow uses guardian's validation loop after `--apply`.
- **lsp + memory** — server quirks and flags accumulate in MEMORY.md across sessions.

## Repo integration

- `skills/lsp/.claude-plugin/plugin.json` — new plugin manifest, same shape as the
  existing four.
- `.claude-plugin/marketplace.json` — add the `lsp` plugin entry.
- Root `README.md` — add a table row, update the structure diagram and the
  "How the skills work together" section.
- Bump all plugin manifests and the README version to **1.3.0** (matching the
  established "add skill → bump all" pattern).

## Testing

Manual smoke test per stack, documented in each `references/<stack>.md`: create or use
a small sample project, run `definition`, `references`, and a dry-run `rename` against
a known symbol, confirm positions are correct. The script itself is validated by
running it against this repo's tooling where available (TypeScript/Python being the
easiest on a dev machine).
