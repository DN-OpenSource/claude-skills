# claude-skills

**Goal:** a collection of standalone, composable Claude Code skills that users install once to make Claude better at recurring work.
**Goal status:** unconfirmed (inferred from README, mode 4 session 2026-10-21)
**Success looks like:** each skill triggers when relevant, works on its own (Linux, Windows, macOS; Python 3.9+), and costs little context — every description loads into every session (budget `scripts/check_token_budget.py`, 1300 tokens).

## Where we are
All 10 skills are built and packaged consistently. The tested code (lsp, decision-maker, repo tooling) passes 111/111 tests locally and in CI on ubuntu 3.9/3.12/3.13, windows 3.12, macos 3.9. This session fixed decision-maker on Windows (its hooks never ran there) and on Python ≤ 3.11 (guard.py didn't parse). Latest report: [`test-reports/2026-10-21-claude-skills.md`](test-reports/2026-10-21-claude-skills.md).

## Feature map

| Feature | Status | Depends on | Used by | How it contributes to the goal |
|---------|--------|------------|---------|--------------------------------|
| teammates | built | — | product-visionary (panel idea) | runs big tasks as peer subagents |
| codebase-guardian | built | memory (optional) | — | safe edits to existing code |
| memory | built | — | codebase-guardian, teammates | context that survives sessions |
| agents-dox | built | — | codebase-guardian, teammates | per-folder work contracts |
| lsp | built, tested 44 | language servers | codebase-guardian, schema-aware-db | precise code navigation and rename |
| schema-aware-db | built | lsp (optional) | — | no guessed schemas in DB code |
| ponytail | built | memory (optional) | — | clean end-of-session handoff |
| decision-maker | built, tested 61 | Jev provider key | every skill (optional recipes) | cheap typed judgments; guard hooks |
| test-report | built | project test framework | product-visionary | real tests + pass/fail report |
| product-visionary | built | test-report (optional) | — | goal/state/feature map; panel-driven fixes |
| repo tooling | built, tested 6 | — | CI | token budget, packaging consistency, links |

No dead or orphan features found.
