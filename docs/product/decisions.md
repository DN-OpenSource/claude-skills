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

### D-12 — 2026-10-22 — How to build C23 (product page always current)? (session 3, batch 1)
- **Status:** done
- **Panel:** 6 — rounds: 2 — Round 1: A 4 / B 2; Round 2 with new option E: E 6/6
- **Pick:** E — render script + update after every change + a Stop hook that never writes
- **Winning argument:** Security / Skeptic — a hook that writes after Claude stops leaves unreported changes; E keeps every write in Claude's visible turn.
- **Strongest dissent:** Skeptic (Round 1) — a hook can't fix "the agent never updated the data"; answered by the per-change rule.
- **Veto:** Skeptic and Security on any writing hook (logged; E never writes).
- **PR:** #24

### D-13 — 2026-10-22 — How to build C24 (professional review)? (batch 2)
- **Status:** done
- **Panel:** 6 — rounds: 1 (clear: A 5/6)
- **Pick:** A — evidence-only checklist, at most 5 gaps per session, every area recorded
- **Winning argument:** Quality — evidence plus "checked" records make each session auditable.
- **Strongest dissent:** Skeptic — the same generic gaps every session; answered: known gaps aren't re-raised unless worse.
- **Veto:** Security — checks that run code/install/network ask first, else "not checked"; User advocate — security/licensing fixes never automatic.
- **PR:** #25

### D-14 — 2026-10-22 — Trigger tests (C18) (batch 3)
- **Status:** done
- **Panel:** 3 — rounds: 1 (picked 3/3 in batch 1)
- **Pick:** 2 fire + 1 quiet `claude plugin eval` case per skill, run locally (evals need the user's credentials)
- **Winning argument:** Engineer — the only proof of "triggers when relevant"; unblocks C4.
- **Strongest dissent:** User advocate — keep it cheap; answered with a capped command.
- **Veto:** none
- **PR:** #26

### D-15 — 2026-10-22 — Shorten descriptions (C4) (batch 4)
- **Status:** done
- **Panel:** 3 — rounds: 2 — C4 2 / STOP 1 both rounds; scope narrowed to four skills by all three
- **Pick:** agents-dox, decision-maker, codebase-guardian, ponytail shortened (−114 tokens); before/after evals 3/3 each
- **Winning argument:** User advocate — users pay for descriptions every session.
- **Strongest dissent:** Skeptic — sandboxed evals can't see duplicate installed copies; memory and schema-aware-db left unchanged.
- **Veto:** none. How-to panel skipped: the how was fixed by all three in Round 2 (logged).
- **PR:** #27

### End-of-session report — 2026-10-22 (session 3)
**Mode:** 4 · **Batches:** 4 · **Stopped because:** nothing left (C25, C26 picked by 0/3 in batch 4)

| # | Item | Kind | PR | Tests | Decision |
|---|------|------|----|-------|----------|
| 1 | Product page always current (render script, per-change rule, never-writing Stop hook) | feature (owner) | #24 | ✅ 149/149, CI 6/6 | D-12 |
| 2 | Professional review every session | feature (owner) | #25 | ✅ 152/152, CI 6/6 | D-13 |
| 3 | Trigger evals for all 11 skills | improvement | #26 | ✅ 155/155; git-conventions eval 3/3 | D-14 |
| 4 | Shorter descriptions for four skills | improvement | #27 | ✅ evals 3/3 before and after | D-15 |

**Pre-existing failures:** none.
**Logged instead of asked** (mode 4): Skeptic's batch-1 veto on a Stop hook; Security and Skeptic vetoes on writing hooks (D-12, answered by E); Security's "first write into a published site folder" (this repo's site/product/ was already published); skipped how-to panel for D-15; eval spend $2.65 in total on the user's credentials.
**Left open:** none.
**Next on the roadmap:** 1. health panel once the review proves itself · 2. duplicate-skill check · 3. opt-in commit check

### D-16 — 2026-10-23 — Which items this batch? (session 4, batch 1)
- **Status:** done
- **Panel:** 3 — rounds: 1 (clear: C28 and C27 picked 3/3; C29 0/3)
- **Pick:** C28 — install steps in every skill README (validator warning 10 → 0)
- **Winning argument:** User advocate — a user landing on a skill's README gets stuck at step one.
- **Strongest dissent:** Skeptic — keep it a line, not a project.
- **Veto:** Skeptic on C29 (icons are brand artwork that may lock in on first submit) — logged, not built.
- **PR:** #29

### D-17 — 2026-10-23 — How to build C27 (duplicate skills)? (batch 2)
- **Status:** done
- **Panel:** 6 — rounds: 1 (clear: B 5/6)
- **Pick:** B — measure in the real environment, then ship a read-only check
- **Winning argument:** User advocate — the wrong copy fires and users can't see why.
- **Strongest dissent:** Skeptic — claude.ai org skills can't be removed by `claude plugin`; answered: named as not checked.
- **Veto:** four members on C (renaming skills) — not built.
- **PR:** #30

### D-18 — 2026-10-23 — Crowded-environment triggering (C30) (batch 3)
- **Status:** done
- **Panel:** 3 — rounds: 2 — C30 2 / STOP 1, then C30a 3/3
- **Pick:** crowded evals with a 45-skill filler plugin, built in a throwaway workspace
- **Votes:** 3/3 in Round 2
- **Winning argument:** Engineer — separates crowding from shadowing with no credentials or owner files touched.
- **Strongest dissent:** Skeptic — small, synthetic sample; record as-is and change no description. Adopted.
- **Veto:** all three — never touch the owner's ~/.claude; cleanup stays printed commands.
- **PR:** #31

### End-of-session report — 2026-10-23 (session 4)
**Mode:** 4 · **Batches:** 3 · **Stopped because:** nothing left (C25, C26 and C29 picked by 0/3; C29 is the owner's call)

| # | Item | Kind | PR | Tests | Decision |
|---|------|------|----|-------|----------|
| 1 | Install steps in every skill README | fix (review gap) | #29 | ✅ 156/156, validator warning 10 → 0 | D-16 |
| 2 | Find duplicate and stale skills (measured in the real env) | feature | #30 | ✅ 159/159 | D-17 |
| 3 | Crowded trigger evals (45 filler skills) | improvement | #31 | ✅ 162/162; crowded eval 4/4 | D-18 |

**Pre-existing failures:** none.
**Logged instead of asked** (mode 4): Skeptic's veto on icons (C29); every member's veto on touching the owner's ~/.claude (respected: commands printed only); eval and probe spend about $0.70 on the owner's credentials.
**Left open:** none. **Owner actions:** remove shadowing duplicates (commands from find_duplicate_skills.py); choose plugin icon artwork.
**Next on the roadmap:** 1. re-measure real triggering after cleanup · 2. health panel · 3. opt-in commit check

### D-19 — 2026-10-23 — Repeatable real-environment trigger probe (session 5, batch 1)
- **Status:** done
- **Panel:** 3 — rounds: 2 — C33 3/3 in both rounds
- **Pick:** C33 — `scripts/probe_triggers.py` + `probes/prompts.txt` + `probes/seed-db/`
- **Winning argument:** Engineer/Skeptic — hand-rolled empty-repo probes couldn't separate wording, missing context and duplicates; a seeded probe that lists duplicate loaded skills can.
- **Strongest dissent:** none against building it; each run spends the owner's credentials, never in CI (mode 4: logged, not asked).
- **PR:** #35

### D-20 — 2026-10-23 — Query-fix prompts miss schema-aware-db (batch 1)
- **Status:** done
- **Panel:** 3 — rounds: 2 — Round 1 C31 2/3 (not clear); Round 2 C31a 3/3
- **Pick:** C31a — measure in a seeded repo first, reword only if it still misses
- **Winning argument:** Skeptic — the empty repo and a duplicate copy could each explain the miss; measure first.
- **Strongest dissent:** User advocate — the pasted-SQL miss isn't explained by an empty repo; fix it this session. Both held: seeded fix-join 2/3, pasted 0/3; reworded (+5 tokens) → 3/3 and 3/3.
- **Ruling:** the sandbox gates Bash and seeding behind opt-in flags, so the probe covers the Bash-first path; the sandbox gained a pasted-query case.
- **PR:** #36

### D-21 — 2026-10-23 — memory vs Claude Code's built-in memory (batch 1)
- **Status:** done
- **Panel:** 9 — rounds: 2 — Round 1 A 4 / B 4 / C 1; Round 2 B 7 / A 1 / C 1
- **Pick:** B — keep the trigger; one owner for personal facts per host; README names Claude Code and claude.ai
- **Winning argument:** Architecture/Engineer — a copy of this skill runs on claude.ai, which has no auto-memory directory; a capability-based rule keeps one description everywhere.
- **Strongest dissent:** Skeptic (A) — USER.md on claude.ai may not persist between conversations; unverified, now an open question.
- **PR:** #37

### D-22 — 2026-10-23 — Keep the claude.ai copies current (batch 2)
- **Status:** done
- **Panel:** 3 — rounds: 2 — Round 1 C34 2/3, STOP 1; Round 2 C34n 2/3, C34s 1
- **Pick:** C34n — README "Use on claude.ai" for memory and schema-aware-db; no script
- **Winning argument:** Engineer/Skeptic — the real risk is claude.ai's documented 200-character description limit, which a zip script can't fix; two uploads need no tool.
- **Strongest dissent:** User advocate (C34s) — hand commands differ per OS; answered with one tested command per OS.
- **PR:** #38

### End-of-session report — 2026-10-23 (session 5)
**Mode:** 4 · **Batches:** 3 · **Stopped because:** nothing left (batch 3: STOP 2/3; C30 1/3, C25/C26 0/3) · **Today's picks:** 4/4 done, 0 awaiting merge, 0 failed

| # | Item | Kind | PR | Tests | Decision |
|---|------|------|----|-------|----------|
| 1 | Real-environment trigger probe | feature | #35 | ✅ 168/168; real run 18 probes | D-19 |
| 2 | schema-aware-db fires on pasted and broken queries | fix | #36 | ✅ eval 4/4; real env 3/3 ×3 | D-20 |
| 3 | memory: one owner for personal facts per host | improvement | #37 | ✅ 171/171; eval 3/3; real env bootstrap 3/3 | D-21 |
| 4 | README steps to replace the claude.ai copies | docs | #38 | ✅ 174/174 | D-22 |

**Pre-existing failures:** none.
**Logged instead of asked** (mode 4): about $9 of eval and probe runs on the owner's credentials; panel members asked that each paid probe run be approved and that disabling claude.ai copies be the owner's call (respected: nothing changed on claude.ai).
**Left open:** none. **Owner actions:** release 1.12.0; replace the claude.ai copies; verify USER.md persistence on claude.ai.
**Next on the roadmap:** 1. probe the other 8 skills (C30) · 2. health panel · 3. opt-in commit check

### D-23 — 2026-10-26 — ponytail becomes wrap-up (design: docs/designs/skill-reliability.md)
- **Status:** done
- **Panel:** none — owner's decision during the design session
- **Pick:** rename `ponytail` to `wrap-up` and close three gaps: follow the git-conventions file and never commit or push to a protected branch (WIP goes to `wip/<date>-<slug>`); keep the hand-off text in the WIP commit body or stash message (and MEMORY.md with memory installed), not only in chat; hand merging a finished branch to superpowers' finishing-a-development-branch when installed
- **Winning argument:** `ponytail@ponytail` (an unrelated "least code" plugin) loads its skill as `ponytail:ponytail` too, so the two can't be told apart; and the old text could commit and push to `main` and lost its report when the session ended — the failure it exists to prevent
- **Strongest dissent:** the rename breaks existing installs — answered with a two-command migration line in both READMEs

### D-24 — 2026-10-26 — One owner for an ordinary edit
- **Status:** done
- **Panel:** none — owner's decision during the design session (Q2)
- **Pick:** by context file: agents-dox owns edits in a repo with `AGENTS.md`, codebase-guardian elsewhere; memory keeps bootstrap and remember and no longer claims edits. One clause in each of the three descriptions (+39 tokens, 1235/1400)
- **Winning argument:** all three claimed "any edit" and said "err on trigger", so which one loaded first was chance; the rule is measurable with one edit prompt on two seeds (`probes/prompts.txt`, `probes/prompts-dox.txt`)
- **Strongest dissent:** "codebase-guardian always" is simpler and needs one seed; rejected by the owner for precision

### D-25 — 2026-10-26 — Probe verdicts, near-miss prompts and a plugin preflight
- **Status:** done (built; sweep not yet run)
- **Panel:** none — design `docs/designs/skill-reliability.md`, phase 1
- **Pick:** `id|expect|prompt` lines with PASS/FAIL and exit 1; `--only <skill>`; layered seeds; a preflight on `claude plugin list --json` that stops on a name clash; a positive and a near-miss line for every skill; a `quiet-near-*` eval per skill. Pass bar: 3/3 for the sweep, 5/5 after any rewording. The five test files CI skipped now run there
- **Winning argument:** the old quiet cases were off-topic (a haiku, a poem), so they couldn't catch a description that fires on its own topic when it shouldn't; and a clash like ponytail's is invisible after launch, because both plugins load under the same name
- **Strongest dissent:** 3 runs can't tell an 80% skill from a 100% one; answered with 5/5 reruns for reworded skills

### D-26 — 2026-10-26 — Step checks for every skill
- **Status:** done (built; not yet run)
- **Panel:** none — design phase 2
- **Pick:** one `does-*` eval per skill (two for wrap-up), graded on tool calls (`tool_order`, `tool_used`, `file_exists`, `regex`), not the Skill call, run with `--allow-tools Bash Write Edit --scaffold` in WSL2 and the default with/without ablation. codebase-guardian's "meaningful edit" now means any edit to a tracked file
- **Winning argument:** a trigger test stops at "the skill loaded"; the skills' value is in a step (read the schema, run the tests, stay off `main`) that nothing checked
- **Strongest dissent:** native Windows has no eval sandbox, so the owner can't run these without WSL2 (Q6: the Windows copy of claude inside WSL may not get one either; check first with one case)
