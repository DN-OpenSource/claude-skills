# Roadmap

## Fix
_(none open — all known failures fixed 2026-10-21)_

## Build
1. **Trigger eval for skill descriptions** — ~10 real prompts per skill, run before/after any description edit. Unblocks C4; without it, shortening descriptions risks a skill silently not firing.
2. **C4 — tighten the 6 longest descriptions** (agents-dox, memory, decision-maker, codebase-guardian, ponytail, schema-aware-db) keeping every trigger phrase verbatim — only after the eval exists. Saves ~50+ eager tokens per session.

## Cut
_(none)_

## Proposed features
- **C7 — one owner for context files** (merge memory / agents-dox / codebase-guardian) — weight: direction — serves: fewer overlapping skills — connects to: memory, agents-dox, codebase-guardian, teammates — panel: 0/3 picked; vetoed by User advocate and Skeptic — strongest argument against: breaks existing installs; the boundary is already drawn in memory's description.

## Open questions
_(none — goal confirmed by the owner 2026-10-21)_

## Deferred (below the bar twice)
- **C5** — trim decision-maker README (418 lines): no runtime cost, 1/3 votes.
- **C6** — shorten root README "how they work together" + top-level manifest descriptions: 1/3 votes.

## Rejected
_(none — mode 4 session, no user rejections yet)_
