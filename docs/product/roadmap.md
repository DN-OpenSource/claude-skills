# Roadmap

## Fix
_(none open — all known failures fixed 2026-10-22)_

## Build
1. **Probe the other 8 skills in the real environment (C30)** — add one positive and one near-miss prompt per skill to `probes/prompts.txt` and run the D-19 probe; only memory, schema-aware-db and teammates have been measured (proposed by the Skeptic, 1/3 in session 5).
2. **Health panel on the product page (C25)** — once the professional review has run in a few projects (0/3 three times).
3. **git-conventions opt-in commit check (C26)** — only if commits drift (0/3 three times).

## Cut
_(none)_

## Proposed features
- **C7 — one owner for context files** (merge memory / agents-dox / codebase-guardian) — weight: direction — serves: fewer overlapping skills — connects to: memory, agents-dox, codebase-guardian, teammates — panel: 0/3 picked; vetoed by User advocate and Skeptic — strongest argument against: breaks existing installs; the boundary is already drawn in memory's description.

## Open questions
- Release 1.12.0? Installs don't get D-20 (schema-aware-db fires on pasted queries) or D-21 until a release. Owner's call.
- Replace the older claude.ai copies of memory and schema-aware-db (README › Use on claude.ai). Owner's action. — raised by D-22
- Does `~/.memory/USER.md` written by the skill on claude.ai persist into the next conversation? Unverified; test with one upload. — raised by the Skeptic, D-21
- Plugin icons: what artwork? They may lock in on first submit. — C29, vetoed for automation

## Deferred (below the bar twice)
- **C5** — trim decision-maker README (418 lines): no runtime cost, 1/3 votes.

## Rejected
_(none — mode 4 session, no user rejections yet)_
