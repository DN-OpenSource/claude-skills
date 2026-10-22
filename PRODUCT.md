# claude-skills

**Goal:** a collection of standalone, composable Claude Code skills that users install once to make Claude better at recurring work.
**Goal status:** confirmed by the owner on 2026-10-21
**Success looks like:** each skill triggers when relevant, works on its own (Linux, Windows, macOS; Python 3.9+), and costs little context — every description loads into every session (budget `scripts/check_token_budget.py`, 1400 tokens).

## Where we are
All 11 skills are built, packaged consistently, and pass the official `claude plugin validate`, now checked in CI. 139/139 tests pass locally and in CI on ubuntu 3.9 (24.04)/3.12/3.13, windows 3.12 and macos 3.9. Session 2026-10-22 found and fixed two skills that never loaded (invalid frontmatter), lsp docs that failed on macOS/Linux, and added git-conventions and test video. Latest report: [`test-reports/2026-10-22-claude-skills.md`](test-reports/2026-10-22-claude-skills.md). Product page: [dn-opensource.github.io/claude-skills/product](https://dn-opensource.github.io/claude-skills/product/).

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
