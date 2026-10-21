# Test report — claude-skills — 2026-10-21

**6/6 new passed** · baseline: 93/101 existing passed (8 pre-existing failures) · backend (Python) · pytest

| Feature | Type | Test | Result | Time |
|---------|------|------|--------|------|
| token-budget | positive | real repo within budget, every skill measured | ✅ pass | <0.1s |
| token-budget | positive | estimates ceil(chars/4) | ✅ pass | <0.1s |
| token-budget | negative | oversized description rejected | ✅ pass | <0.1s |
| packaging | positive | every skill has README, manifest, matching names | ✅ pass | <0.1s |
| packaging | positive | marketplace, README table, versions agree | ✅ pass | <0.1s |
| packaging | negative | no dangling relative links in READMEs/SKILL.md | ✅ pass | <0.1s |

## Baseline (existing suites)
- lsp `test_lsp.py`: 44/44 ✅
- decision-maker `test_decide.py`: 15/16 — ❌ `test_add_edit_use_remove`: asserts 0o600 file mode; Windows has no POSIX modes (**test issue**, `test_decide.py:125`)
- decision-maker `test_guard.py`: 34/41 — ❌ 7 tests. Causes: (a) tests read the real `~/.claude/CLAUDE.md`, so a user rule leaks into every guard check (**test isolation bug**); (b) rule sources reported as `api\AGENTS.md` on Windows vs expected `api/AGENTS.md` (**app inconsistency**, guard.py path formatting)

## Re-run
`python -m pytest scripts/test_repo.py skills/lsp/scripts skills/decision-maker/scripts/test_decide.py skills/decision-maker/scripts/test_guard.py -q`
