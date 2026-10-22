# Decisions

### D-1 — 2026-10-21 — Which items this batch? (batch 1)
- **Status:** done
- **Panel:** 3 — User advocate, Engineer, Skeptic — rounds: 2
- **Pick:** C1 — make decision-maker tests pass on Windows (also picked: C2 → D-2, C4 → later, see roadmap)
- **Votes:** C1 9 · C2 5 · C4 3 · C3 1 (Round 2)
- **Winning argument:** Engineer — three one-line root causes verified in code; Windows is the owner's platform.
- **Strongest dissent:** User advocate — description cost (C4) first; withdrawn to "after a trigger eval" in batch 3.
- **Veto:** Skeptic flagged deleting ~2,300 tracked lines (C3) — logged (mode 4); not an always-ask item.
- **PR:** #6

### D-2 — 2026-10-21 — How to build C2 (repo tests + CI)?
- **Status:** done
- **Panel:** 6 — User advocate, Engineer, Skeptic, Quality, Business, Security — rounds: 2
- **Pick:** B, trimmed matrix: ubuntu 3.9/3.12/3.13, windows 3.12, macos 3.9
- **Votes:** Round 1 4 A / 2 B → Round 2 6/6 B
- **Winning argument:** Skeptic — hooks run bare `python3` (stock macOS is 3.9); a hook that fails to parse degrades silently, so no bug report ever arrives.
- **Strongest dissent:** Business (Round 1) — the matrix triples CI cost; withdrawn (public repo, parallel jobs).
- **Veto:** none. Security conditions adopted: `contents: read`, `pull_request` only, no secrets, SHA-pinned actions.
- **PR:** #7 — also fixed guard.py being a SyntaxError on Python ≤ 3.11.

### D-3 — 2026-10-21 — Which items this batch? (batch 3)
- **Status:** done
- **Panel:** 3 — User advocate, Engineer, Skeptic — rounds: 2
- **Pick:** C8 — decision-maker runs where `python3` is the Windows Store stub (also picked: C3 → D-4)
- **Votes:** C8 9 · C3 5 · C6 2 · C5 1 (Round 2)
- **Winning argument:** Skeptic — all 6 hooks failed open silently on Windows; users believed they were guarded.
- **Strongest dissent:** Engineer — a `python3 || python` retry re-runs guard.py on its intentional exit 2; probe first.
- **Veto:** C7 vetoed by User advocate and Skeptic (breaks installs) — logged (mode 4), not picked.
- **PR:** #8 — also pinned `*.sh` to LF (a CRLF checkout would break the launcher).

### D-4 — 2026-10-21 — (batch 3, second pick)
- **Status:** done
- **Panel:** same as D-3
- **Pick:** C3, narrowed — delete the shipped lsp spec and plan; keep the product-visionary pair
- **Votes:** 3/3 in Round 2
- **Winning argument:** Skeptic — unreferenced, shipped, git keeps history; the product-visionary rationale isn't in its SKILL.md.
- **Strongest dissent:** User advocate (Round 1) — cleanup users never see.
- **Veto:** none
- **PR:** #9

### D-5 — 2026-10-21 — Which items this batch? (batch 4)
- **Status:** done
- **Panel:** 3 — User advocate, Engineer, Skeptic — rounds: 1 (clear)
- **Pick:** C9 — decision-maker README runs every unit test; then STOP
- **Votes:** 3/3 C9; 3/3 STOP after it
- **Winning argument:** Skeptic — fix the command and drop the hard-coded count so it can't go stale.
- **Strongest dissent:** none
- **Veto:** none
- **PR:** #10

### End-of-session report — 2026-10-21
**Mode:** 4 · **Batches:** 4 · **Stopped because:** nothing left (panel voted STOP 3/3)

| # | Item | Kind | PR | Tests | Decision |
|---|------|------|----|-------|----------|
| 1 | decision-maker tests + paths on Windows | fix | #6 | ✅ 49→57/57, no new failures | D-1 |
| 2 | Repo tests + CI (3 OS, Py 3.9–3.13); guard.py parses on Py ≤ 3.11 | improvement + fix | #7 | ✅ 107/107, CI 5/5 | D-2 |
| 3 | decision-maker hooks run when `python3` is the Store stub; `*.sh` LF | fix | #8 | ✅ 111/111, CI 5/5 | D-3 |
| 4 | Remove shipped lsp spec/plan (1,964 lines) | removal | #9 | ✅ 111/111, CI 5/5 | D-4 |
| 5 | README unit-test command runs all tests | fix | #10 | ✅ CI 5/5 | D-5 |

**Pre-existing failures** (in the baseline, not caused by this session): 8 decision-maker tests on Windows — all fixed by D-1.
**Logged instead of asked** (mode 4 only): goal is unconfirmed; vetoes on C3 (Skeptic, batch 1) and C7 (User advocate + Skeptic, batch 3); no always-ask item was acted on.
**Left open:** none.
**Next on the roadmap:** 1. trigger eval for descriptions · 2. C4 description trim (after the eval) · 3. confirm the goal

### D-6 — 2026-10-22 — Which items this batch? (session 2, batch 1)
- **Status:** done
- **Panel:** 3 — User advocate, Engineer, Skeptic — rounds: 2
- **Pick:** C10 — lsp docs use python3 + the Windows note (also picked: C17 → D-7; C14 → own batch)
- **Votes:** C10 7 · C14 7 · C17 2 → 3/3 in Round 2
- **Winning argument:** User advocate — stock macOS and Ubuntu have no `python`, so the documented command failed.
- **Strongest dissent:** Engineer — ship the owner's video request first.
- **Veto:** none
- **PR:** #15 — also moved the Python 3.9 CI job to ubuntu-24.04 (ubuntu-latest 26.04 has no 3.9).

### D-7 — 2026-10-22 — (batch 1, second pick)
- **Status:** done
- **Panel:** same as D-6
- **Pick:** C17 — README explains how to update installed plugins
- **Votes:** 3/3 in Round 2
- **Winning argument:** User advocate — the owner's install sat on 1.5.0 after 1.6.0 shipped.
- **Strongest dissent:** Skeptic — verify the command against the real CLI first (done).
- **Veto:** none
- **PR:** #16

### D-8 — 2026-10-22 — How to build C14 (test video)? (batch 2)
- **Status:** done
- **Panel:** 6 — User advocate, Engineer, Skeptic, Quality, Business, Security — rounds: 2
- **Pick:** C — record each web/mobile test, keep clips of failures only, gitignored
- **Votes:** Round 1 D 3 / C 2 / B 1 · orchestrator ruling: A and D (commit recordings) break the mode-4 floor · Round 2 C 6/6
- **Winning argument:** Security — recordings capture typed credentials, tokens and personal data; committed means permanent public history.
- **Strongest dissent:** Business / User advocate — local-only links are dead for reviewers.
- **Veto:** Security on committing recordings; Security "ask before editing .gitignore" — logged (mode 4).
- **PR:** #17

### D-9 — 2026-10-22 — Which items this batch? (batch 3)
- **Status:** done
- **Panel:** 3 — rounds: 1 (clear: C21, C20, C22 picked 3/3)
- **Pick:** C21 two skills' frontmatter invalid → quoted · C20 `claude plugin validate` in CI · C22 root plugin renamed from reserved `claude-skills`
- **Votes:** 3/3; sub-question delete vs rename tied → mode-4 tie-break: rename (the option the Skeptic objected to least)
- **Winning argument:** Skeptic — codebase-guardian was installed but missing from the session's available skills.
- **Strongest dissent:** Engineer — delete the root plugin.json.
- **Veto:** Engineer and Skeptic: git-conventions must ask before writing settings — carried into D-10.
- **PR:** #18

### D-10 — 2026-10-22 — How to build C19 (git-conventions)? (batch 4)
- **Status:** done
- **Panel:** 6 — rounds: 2
- **Pick:** A — conventions file + native settings, every change asked first
- **Votes:** Round 1 A 4 / B 2 · Round 2 A 5 / B 1
- **Winning argument:** Engineer — native `attribution` is the deterministic part; a hook would fail open on Claude's usual heredoc commits.
- **Strongest dissent:** Quality — instructions drift when the skill isn't loaded mid-task. Answered by an opt-in CLAUDE.md pointer line and native deny rules.
- **Veto:** all six — ask before any settings change; empty strings, never `false`; never rewrite history. Built in.
- **PR:** #19

### D-11 — 2026-10-22 — How to build C15 + C16 (product page + website)? (batch 5)
- **Status:** done
- **Panel:** 6 — rounds: 1 (clear: A 5/6)
- **Pick:** A — tests section, since last session, jump nav, panel detail, status filter
- **Votes:** A 5 / B 1
- **Winning argument:** Quality / Engineer — every addition is a textContent element; the existing safety tests still hold.
- **Strongest dissent:** Skeptic — keep dissent visible; the real website bug was a hand-kept skill list missing git-conventions, built with innerHTML. Adopted.
- **Veto:** none
- **PR:** #20

### End-of-session report — 2026-10-22
**Mode:** 4 · **Batches:** 5 · **Stopped because:** 5 batches (session ceiling)

| # | Item | Kind | PR | Tests | Decision |
|---|------|------|----|-------|----------|
| 1 | lsp docs: python3 + Windows note; CI 3.9 on ubuntu-24.04 | fix | #15 | ✅ 117/117, CI 5/5 | D-6 |
| 2 | README: how to update installed plugins | improvement | #16 | ✅ CI 5/5 | D-7 |
| 3 | test-report: video of failing tests, kept local | feature (owner) | #17 | ✅ 120/120, CI 5/5 | D-8 |
| 4 | Two skills never loaded (frontmatter); validate in CI; root plugin rename | fix | #18 | ✅ 132/132, CI 6/6 | D-9 |
| 5 | New skill git-conventions | feature (owner) | #19 | ✅ 135/135, CI 6/6 | D-10 |
| 6 | Product page + website improvements | feature (owner) | #20 | ✅ 139/139, CI 6/6 | D-11 |

**Pre-existing failures** (in the baseline, not caused by this session): none. (ubuntu-latest moving to 26.04 broke the 3.9 job mid-session; fixed in #15.)
**Logged instead of asked** (mode 4 only): Security's vetoes on committing recordings and on editing .gitignore (D-8); the delete-vs-rename tie-break (D-9); the owner's installed product-visionary was a stale 1.5.0 copy at session start.
**Left open:** none.
**Next on the roadmap:** 1. trigger tests with `claude plugin eval` · 2. shorten the 6 longest descriptions · 3. git-conventions opt-in commit check

