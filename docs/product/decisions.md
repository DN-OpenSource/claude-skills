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
