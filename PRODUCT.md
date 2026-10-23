# claude-skills

**Goal:** a collection of standalone, composable Claude Code skills that users install once to make Claude better at recurring work.
**Goal status:** confirmed by the owner on 2026-10-21
**Success looks like:** each skill triggers when relevant, works on its own (Linux, Windows, macOS; Python 3.9+), and costs little context — every description loads into every session (budget `scripts/check_token_budget.py`, 1400 tokens).

## Where we are
All 11 skills pass the official validator and have trigger tests. 174/174 tests pass locally and in CI on ubuntu 3.9 (24.04)/3.12/3.13, windows 3.12 and macos 3.9. Session 5 (2026-10-23), after the owner's cleanup, measured triggering with a new repeatable real-environment probe (`scripts/probe_triggers.py`, seeded repo): memory bootstrap 3/3, teammates 3/3, and, after rewording schema-aware-db's description (D-20), save-order 3/3, fix-join 3/3, pasted-SQL fix 3/3 (was 0/3). "Remember I prefer X" goes to Claude Code's built-in memory by design (D-21). Only 3 of 11 skills have been probed in the real environment so far. Latest report: [`test-reports/2026-10-23-session-5.md`](test-reports/2026-10-23-session-5.md). Product page: [dn-opensource.github.io/claude-skills/product](https://dn-opensource.github.io/claude-skills/product/).

## Professional review — 2026-10-23
| Area | Status | Evidence / reason |
|------|--------|-------------------|
| Secrets | fine | no tracked .env/key files; key-pattern scan of tracked files clean |
| Dependencies | not applicable | no dependency manifests; scripts are stdlib-only |
| Privacy & data | not applicable | the skills store no personal data |
| Errors & data loss | fine | hooks and launchers fail open; render_page writes atomically |
| Accessibility | fine | site and product pages: no images without alt, labelled controls, focus styles |
| Performance | fine | eager description cost 1196/1400 tokens, enforced in CI |
| Docs & onboarding | fine | every skill README now has install + update steps (validator warning 10 → 0, D-16) |
| Release & versioning | fine | all manifests in lockstep (checked by tests); GitHub release notes per version |
| CI & tests | fine | sandbox trigger evals (D-14) plus a real-environment probe (D-19); real-env coverage is 3 of 11 skills |
| Observability | not applicable | no running service |
| Licensing | fine | Apache-2.0 LICENSE at the root |
| Duplicate skills | gap (owner's claude.ai) | on-disk duplicates removed by the owner (check: none); the probe still lists claude.ai's older anthropic-skills:memory and :schema-aware-db next to the plugins — README › Use on claude.ai has the replace steps (D-22) |
| Plugin listing | gap | ICON_MISSING for all 11 plugins; icons are brand artwork the owner chooses (vetoed for automation) |
| Platform support | fine | Linux, Windows and macOS all in the CI matrix |

## Feature map

| Feature | Status | Depends on | Used by | How it contributes to the goal |
|---------|--------|------------|---------|--------------------------------|
| teammates | built | — | product-visionary (panel idea) | runs big tasks as peer subagents |
| codebase-guardian | built (loads again since D-9) | memory (optional) | — | safe edits to existing code |
| memory | built | — | codebase-guardian, teammates | context that survives sessions |
| agents-dox | built | — | codebase-guardian, teammates | per-folder work contracts |
| lsp | built, tested 44 | language servers | codebase-guardian, schema-aware-db | precise code navigation and rename |
| schema-aware-db | built (loads again since D-9) | lsp (optional) | — | no guessed schemas in DB code |
| ponytail | built | memory (optional) | — | clean end-of-session handoff |
| decision-maker | built, tested 61 | Jev provider key | every skill (optional recipes) | cheap typed judgments; guard hooks |
| test-report | built | project test framework | product-visionary | real tests + pass/fail report; video of failures, kept local |
| git-conventions | built (new) | native `attribution` setting | — | Claude's commits, branches and PRs follow the user's rules |
| product-visionary | built | test-report (optional) | — | goal/state/feature map; panel-driven fixes |
| repo tooling | built, tested 34 | — | CI | token budget, packaging, links, frontmatter, interpreter docs, pages, official validation |

No dead or orphan features found.
