# Test report — claude-skills — 2026-10-22

**12/12 new passed** · 139/139 in total · backend (Python) · pytest · plus `claude plugin validate`

| Feature | Type | Test | Result | Time | Video |
|---------|------|------|--------|------|-------|
| interpreter docs | positive | every documented Python run uses python3 | ✅ pass | <0.1s | — |
| interpreter docs | positive | skills that run Python carry the Windows note | ✅ pass | <0.1s | — |
| interpreter docs | negative | bare python is caught | ✅ pass | <0.1s | — |
| test video | positive | SKILL links the rules; report has a Video column | ✅ pass | <0.1s | — |
| test video | positive | rules cover every platform and safeguard | ✅ pass | <0.1s | — |
| test video | negative | never tells Claude to commit or upload recordings | ✅ pass | <0.1s | — |
| frontmatter | positive | every SKILL.md parses with name and description | ✅ pass | <0.1s | — |
| frontmatter | positive | parsed description matches what the budget counts | ✅ pass | <0.1s | — |
| frontmatter | negative | an unquoted colon is rejected | ✅ pass | <0.1s | — |
| git-conventions | positive | file covers what the owner asked for | ✅ pass | <0.1s | — |
| git-conventions | positive | attribution uses the native setting safely | ✅ pass | <0.1s | — |
| git-conventions | negative | never sets false or rewrites history | ✅ pass | <0.1s | — |

## Entry points run on this machine (Windows)
- decision-maker hooks, all 6 events via `run.sh` → exit 0
- `decide.py provider list` → ok
- `lsp.py --help` with `python` → ok; with `python3` → Microsoft Store stub (documented fallback)
- `claude plugin validate .` → ✘ 3 errors at session start (2 frontmatter, 1 reserved name) → ✔ after D-9

## Baseline
114/114 at session start; CI 5/5 (the 3.9 job broke mid-session when ubuntu-latest moved to 26.04 — fixed in #15).

Videos: none — every test here is backend (no screen).

## Re-run
`python -m pytest -q scripts/ skills/lsp/scripts skills/decision-maker/scripts && claude plugin validate .`
