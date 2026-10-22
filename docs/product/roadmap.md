# Roadmap

## Fix
_(none open — all known failures fixed 2026-10-22)_

## Build
1. **C18 — trigger tests with `claude plugin eval`** — the built-in eval runner (cases under `evals/`) checks each skill still fires on real prompts. Unblocks C4.
2. **C4 — tighten the 6 longest descriptions** (agents-dox, memory, decision-maker, codebase-guardian, ponytail, schema-aware-db), keeping every trigger phrase — only after C18. Saves 50+ eager tokens per session.
3. **git-conventions opt-in commit check** — a warning-only hook, off by default, if commits drift from the file (D-10 dissent).
4. **product-visionary follows git-conventions** — its `pv/D-<n>` branches and commit messages should respect a conventions file when one exists.

## Cut
_(none)_

## Proposed features
- **C7 — one owner for context files** (merge memory / agents-dox / codebase-guardian) — weight: direction — serves: fewer overlapping skills — connects to: memory, agents-dox, codebase-guardian, teammates — panel: 0/3 picked; vetoed by User advocate and Skeptic — strongest argument against: breaks existing installs; the boundary is already drawn in memory's description.

## Open questions
_(none — goal confirmed by the owner 2026-10-21)_

## Deferred (below the bar twice)
- **C5** — trim decision-maker README (418 lines): no runtime cost, 1/3 votes.

## Rejected
_(none — mode 4 session, no user rejections yet)_
