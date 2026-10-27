Status: resolved — 2026-10-26: all 21 proposed doc fixes applied; Issue 12 contested (Agent needs no grant), its clarifying sentence added anyway; code follow-ups F1–F9 done in commit a173efa.

# Goldfish Annotated Review Report

**Target:** `docs/designs/skill-reliability.md` (full file, lines 1-668)
**Reviewers:** design_critic (feature-spec-standard) · implementation_readiness (implementation-readiness-standard) · codebase_details (implementation-readiness-standard) · zoom_out (zoom-out-standard)
**Totals after deduplication:** 1 Blocker (raised by all four reviewers as Blocker or Major), 20 Major, 1 bundle of Nits. 20 PROPOSE FIX, 1 CONTEST, 1 split (part fix, part contest).

The reviewers found two kinds of problem:
- **Drift:** the doc was written before the build and wasn't updated afterwards. Most findings are this kind.
- **Real gaps in the design:** risks, what G3 and G4 actually catch, and the skipped Stage 0 gate.

Several findings also point at code, not just the doc. Those are listed at the end under **Code follow-ups**. Accepting a doc fix does not change code; each follow-up needs your own yes.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`all four`] - Severity: High
*   **Affected Scope:** [Lines 4, 117-126, 393-407, 632-645](docs/designs/skill-reliability.md#L4) (Status, Open Questions, Stage 0, Stage 4)
*   **Discrepancy Description:** The Status line says "Stages 1–4 built". But:
    *   Stage 0 says "no repo changes until it passes", yet Q6 (sandbox under WSL2) and Q7 (Jev key reaches the eval) are still open and no Stage 0 result is recorded.
    *   Stage 4's report (item 25) doesn't exist.
    *   C30 is still on the roadmap.
    *   D-24 says "done".
*   **Rationale:** A reader can't tell what was done, what's still gated, or what to run next. If Q6 fails, all 12 `does-*` cases depend on the weaker fallback (Alternative B).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** This is true. Stage 0 was skipped because the owner asked to build everything first ("implement everything that's needed"), and the doc should say so honestly.
*   ***Proposed Edit:***
    *   Location: line 4, and a new note at the top of Stage 0.
    *   Change: Status → `Approved — Stages 1–3 built 2026-10-26. Stage 0 (environment check) was not run first: the owner asked for everything to be built before any paid run. Stage 0 and Stage 4 (sweep, step checks, report) are pending.` Stage 0 gains: `If Q6 fails, the does-* cases stay as written and run on Linux or macOS instead; Alternative B is the fallback only if no such machine is available.`

### [Issue 2] [`zoom_out, implementation_readiness, design_critic, codebase_details`] - Severity: High
*   **Affected Scope:** [Lines 99-103, 282-286, 416-426](docs/designs/skill-reliability.md#L99) (Non-Goals, What does not change)
*   **Discrepancy Description:** Commits 32b47eb and 2edeac6 added a "Progress and panel" section, for the skill-checklist mod's `skill_progress` and `skill_panel` tools, to all 11 SKILL.md files. The design never mentions it, and it conflicts with the Non-Goal "Adding new skills or features". It also adds new skip wording ("Skip steps that don't apply"), and the wrap-up panel tells Claude to wait for an answer before tying anything off, which may affect `does-protect-main` and `does-check-git`. The section shifted line numbers by about 6, so item 8's line citations are now wrong.
*   **Rationale:** It's unscoped work inside a reliability project. G6's soft-word search would flag its wording, and it may change how the step checks behave.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** It's real scope the owner asked for mid-project, so the fix is to record it, not remove it. The skip sentence is about which steps to *report*, not which work to skip. Still, the wording is ambiguous, so it should change (see Code follow-up F1).
*   ***Proposed Edit:***
    *   Location: new subsection after "What does not change", titled "Added during the build: skill-checklist hooks".
    *   Change: Describe the section: it is optional, does nothing without the mod, adds body text only, and leaves the description budget unchanged. Record that the owner asked for it on 2026-10-26. Note that wrap-up's panel waits for an answer only "when the person is there", and that an eval run has no mod loaded, so the `does-*` cases are unaffected. Replace item 8's line numbers with section names.

### [Issue 3] [`design_critic`] - Severity: Medium
*   **Affected Scope:** [Lines 33-37, 132-135, 578-585](docs/designs/skill-reliability.md#L33) (Problem 2, Q2, item 19)
*   **Discrepancy Description:** memory's description still claims "starting work in a repository (… auto-bootstrap if absent)" and "err toward using it". Both seeds have no MEMORY.md, so memory still competes on the edit prompt. The probe records only the *first* Skill call, so even a PASS can't show whether the other skills also loaded, which was the gap Problem 2 named.
*   **Rationale:** G3 claims "resolved", but the measurement can't confirm it.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Correct. Memory's bootstrap at the start of work is by design (D-21 kept it), so the doc should say G3 decides who loads *first*, not who loads at all.
*   ***Proposed Edit:***
    *   Location: G3 (lines 78-80), Q2 resolved (lines 132-135).
    *   Change: G3 → `…the probe shows which skill fires first for an ordinary edit, and that matches the rule. memory may still bootstrap at the start of work in a repo with no MEMORY.md (by design, D-21); it no longer claims the edit itself.` Then see Code follow-up F2.

### [Issue 4] [`design_critic`] - Severity: Medium
*   **Affected Scope:** [Lines 132-135, 210-216, 578-585](docs/designs/skill-reliability.md#L210) (edit ownership)
*   **Discrepancy Description:** In a repo with AGENTS.md, codebase-guardian now steps back, and agents-dox doesn't run the type-check, lint or tests. agents-dox's SKILL.md still assumes "guardian's loop runs inside the DOX contract", and nothing triggers that loop any more.
*   **Rationale:** In DOX repos, the step Phase 2 exists to protect (validate with the real toolchain) may never load.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** This is a real hole the ownership rule created.
*   ***Proposed Edit:***
    *   Location: Q2 resolved and item 19.
    *   Change: Add `In a DOX repo, agents-dox owns the edit and runs codebase-guardian's verify step (Phase 1 baseline, Phase 4 toolchain) inside the contract, as its "Composing" section already says; agents-dox's body names this explicitly.` Then see Code follow-up F3.

### [Issue 5] [`design_critic, codebase_details`] - Severity: Medium
*   **Affected Scope:** [Lines 80-82, 187-196, 503-510](docs/designs/skill-reliability.md#L80) (G4, preflight)
*   **Discrepancy Description:** G4 has three gaps:
    *   If `claude plugin list --json` fails, the preflight is skipped and the run can still exit 0.
    *   It matches plugin ids only, so a same-name copy in `~/.claude/skills`, a claude.ai `anthropic-skills:*` copy, or a plugin with a different name triggers only the runtime "Loaded more than once" printout, which doesn't fail the run.
    *   Verdicts compare base names, so a foreign skill with the same name can produce a false PASS.
*   **Rationale:** G4 promises "exits with an error" for a shadowed skill; the code catches only one shape of shadowing.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Correct. Narrowing the wording alone isn't enough, because the false PASS defeats the point of the probe (see Code follow-up F4).
*   ***Proposed Edit:***
    *   Location: G4 and Phase 1 item 2.
    *   Change: G4 → `The probe exits 1 when a repo skill's name is loaded more than once (any source: another marketplace, a personal skill, a claude.ai copy) or when the preflight finds another plugin of the same name; a preflight that can't run is reported and needs --no-preflight to continue.`

### [Issue 6] [`design_critic, codebase_details`] - Severity: Medium
*   **Affected Scope:** [Lines 231-243, 269-280, 476-481](docs/designs/skill-reliability.md#L269) (wrap-up fixes, `does-protect-main`)
*   **Discrepancy Description:**
    *   Fix 2 lets wrap-up save work as a stash, and a run that stashes makes no `git commit`.
    *   The doc doesn't say how `tool_order` scores a run when the "after" tool never happens.
    *   `git switch -c wip/x && git commit` in one Bash call, or `git switch --create`, could be mis-scored.
    *   The prompt in the doc ("wrap up, I'm done for today") isn't the one built ("commit my unfinished work so it's saved…").
*   **Rationale:** The grader's behaviour is unstated, and the doc's prompt would make the case fail on valid behaviour.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The built prompt asks for a commit on purpose, so the stash path is out of scope for this case. That should be said. The plugin-eval docs define `tool_order` as "both tools were called and the first matching before precedes the first matching after", so a run with no commit fails. That's correct here, but undocumented.
*   ***Proposed Edit:***
    *   Location: item 10 and the paragraph at lines 276-280.
    *   Change: Use the built prompt. Add `The prompt asks for a commit, so the stash path is not exercised here; tool_order fails a run with no matching "after" call (plugin-eval docs).` Then see Code follow-up F5 (widen the branch regex).

### [Issue 7] [`design_critic`] - Severity: Medium
*   **Affected Scope:** whole doc (no Risks section; feature-spec-standard "Risks & Limits")
*   **Discrepancy Description:** Risks appear only as cons inside Alternatives. Not covered anywhere:
    *   Sample size: 3/3 can't tell 80% from 100%.
    *   Model drift.
    *   Token headroom: 165 tokens for up to 2 rewrites across 8 skills.
    *   Grader false negatives.
    *   The preflight skip.
    *   Scope drift.
*   **Rationale:** The standard requires this section.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Required and missing.
*   ***Proposed Edit:***
    *   Location: new `## Risks & Mitigations` after Non-Functional Requirements.
    *   Change: One line each for:
        *   sample size (3 runs, then 5/5 after rewording);
        *   model drift (rerun the sweep on each model change and before each release);
        *   token headroom (165 tokens; the per-skill cap is 260; rewrites must trim as much as they add);
        *   grader false negatives and positives (strict regexes, with the with/without delta as a cross-check);
        *   the preflight skip (Issue 5);
        *   scope drift (Issue 2);
        *   the probe's Bash runs without a sandbox (Issue 18).

### [Issue 8] [`implementation_readiness, design_critic, codebase_details`] - Severity: Medium
*   **Affected Scope:** [Lines 455-467, 663-664](docs/designs/skill-reliability.md#L663) (item 8, Rename verification)
*   **Discrepancy Description:** `git grep -i ponytail` also hits:
    *   the migration lines in both READMEs;
    *   PRODUCT.md, product.json and the product page;
    *   two rows in use-cases.md (141, 266);
    *   the design doc itself.
*   **Rationale:** As written, the check can't pass.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Use-cases rows 141 and 266 refer to the *other* plugin's "least code" mode. They were rightly kept, but the doc doesn't say why.
*   ***Proposed Edit:***
    *   Location: item 8 "Not changed" list and the Rename verification line.
    *   Change: Allowed mentions:
        *   the `# ponytail:` code comments;
        *   use-cases.md rows "drop nits under `ponytail` mode" and "cut it down (ponytail)" (the other plugin);
        *   the migration lines in README.md and skills/wrap-up/README.md;
        *   "renamed from ponytail" in PRODUCT.md, product.json and the product page;
        *   decision history, test reports, and this design.

### [Issue 9] [`implementation_readiness, design_critic, codebase_details`] - Severity: Medium
*   **Affected Scope:** [Lines 225, 529-531, 545-547, 603-614](docs/designs/skill-reliability.md#L529) (items 14, 16, 22)
*   **Discrepancy Description:**
    *   Item 14's prompt (`guardian-edit`, rename save_order in app.py) contradicts line 212 and the built `codebase-guardian-edit` slugify prompt. The app.py edit would also pull in schema-aware-db.
    *   Item 16 names `test_app.py`, but the build is `utils.py` plus `test_utils.py`.
    *   Line 225 says Phase 2 covers only skills that pass Phase 1, but all 12 `does-*` cases were built before any sweep.
*   **Rationale:** The doc contradicts itself and the code.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Doc drift; the build follows line 212.
*   ***Proposed Edit:***
    *   Location: items 14, 16 and line 225.
    *   Change: Item 14 → `codebase-guardian-edit|codebase-guardian|Make slugify in utils.py also strip leading and trailing dashes.` Item 16 → `utils.py (a slugify helper) and test_utils.py (one unittest)`. Line 225 → `Cases exist for all skills; a skill that fails Phase 1 has its does-* case run only after its description passes.`

### [Issue 10] [`implementation_readiness, codebase_details`] - Severity: Medium
*   **Affected Scope:** [Lines 231-243](docs/designs/skill-reliability.md#L231) (Phase 2 grader table)
*   **Discrepancy Description:** Five rows don't match the built graders:
    *   test-report: `file_exists` only, with no pass-count check.
    *   git-conventions: no subject regex; an undocumented `branched-off-main` check instead.
    *   lsp: no install-hint branch.
    *   teammates: `file_exists` plus `Agent min 2`, with no ordering check.
    *   product-visionary: matches the question, not the four modes.
*   **Rationale:** The table is the spec for item 22, and teammates and test-report are now weaker evidence than G5 promised.
*   ***AI Suggestion:*** PROPOSE FIX (doc table to match the build, with reasons) + Code follow-up F6 for the two weak ones
*   ***Justification:*** Some of the differences have reasons:
    *   teammates may write `state.json` through Bash, so a `Write`-before-`Agent` ordering would fail valid runs. Existence plus peers is what can be checked reliably.
    *   The lsp fixture has no language server, so the script call is the checkable step.
    *   test-report's report should still get a content regex (`\d+\s*/\s*\d+|passed`).
*   ***Proposed Edit:***
    *   Location: table rows for test-report, git-conventions, lsp, teammates, product-visionary.
    *   Change: Replace each grader cell with the built grader and add a one-line reason. For example, teammates: `file_exists .teammates/state.json + tool_used Agent min 2 (the manifest may be written by Bash, so order isn't graded)`.

### [Issue 11] [`implementation_readiness`] - Severity: Medium
*   **Affected Scope:** [Lines 231-243, 277-280, 603-608](docs/designs/skill-reliability.md#L231)
*   **Discrepancy Description:** The doc never says how `input_match` matches: against the JSON-encoded tool input. Every Bash grader uses `'"command"\s*:\s*"[^\"]*<cmd>'`, which the implementer had to work out.
*   **Rationale:** Under the Zero-Decision Rule, the implementer shouldn't have to make this call.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** One paragraph fixes it.
*   ***Proposed Edit:***
    *   Location: before the Phase 2 table.
    *   Change: `input_match is a regex over the tool's JSON-encoded input (plugin-eval docs). Bash graders anchor on the command field: '"command"\s*:\s*"[^\"]*<command>'; file graders match the path inside file_path, e.g. 'schema\.sql'.`

### [Issue 12] [`implementation_readiness`] - Severity: Medium
*   **Affected Scope:** [Lines 603-608, 627-630](docs/designs/skill-reliability.md#L627)
*   **Discrepancy Description:** The single run command grants only `Bash Write Edit`. The teammates case needs `Agent`, and the doc doesn't say how that's granted.
*   **Rationale:** As written, one command can't run every case.
*   ***AI Suggestion:*** CONTEST
*   ***Justification:*** `claude plugin eval --help` lists `--allow-tools` as the "Operator grant for gated tools (Bash, Write, Edit, WebFetch, mcp__*)". `Agent` is not a gated tool, so it needs no grant and the one command does cover the teammates case. One clarifying sentence in the doc would still help readers.
*   ***Proposed Edit:***
    *   Location: item 24.
    *   Change (optional): `Agent is not a gated tool, so no grant is needed for teammates' case.`

### [Issue 13] [`implementation_readiness, codebase_details`] - Severity: Medium
*   **Affected Scope:** [Lines 571-576](docs/designs/skill-reliability.md#L571) (item 18)
*   **Discrepancy Description:** The plan says the test requires a `case.yaml` in every `does-*` case. The test only checks the scaffold script `if case.exists()`.
*   **Rationale:** The plan and the test disagree.
*   ***AI Suggestion:*** PROPOSE FIX (code: make the test require it; all 12 cases already have one) — see F7
*   ***Justification:*** The stronger rule costs one line and every case already passes it.
*   ***Proposed Edit:***
    *   Location: item 18.
    *   Change: unchanged once F7 lands. Otherwise → `checks the scaffold script named by case.yaml exists`.

### [Issue 14] [`implementation_readiness, design_critic, codebase_details`] - Severity: Medium
*   **Affected Scope:** [Lines 656-659](docs/designs/skill-reliability.md#L656) (Verification, real environment)
*   **Discrepancy Description:** "The same with `prompts-dox.txt` and `seed-dox`" reads as `--seed probes/seed-dox`, which has no `utils.py`.
*   **Rationale:** Run literally, the command gives the edit prompt nothing to edit.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The README already has the right command.
*   ***Proposed Edit:***
    *   Location: line 657.
    *   Change: `python scripts/probe_triggers.py probes/prompts-dox.txt --runs 3 --seed probes/seed-db,probes/seed-dox`.

### [Issue 15] [`implementation_readiness, codebase_details`] - Severity: Medium
*   **Affected Scope:** [Lines 165, 187-196, 491-522](docs/designs/skill-reliability.md#L491) (items 12, 13, diagram)
*   **Discrepancy Description:** The built probe has behaviour the doc doesn't describe:
    *   a `plugin-dir` state;
    *   an installed copy plus `--plugin-dir` counts as a clash;
    *   `--runs < 1` exits 2;
    *   a skipped preflight continues;
    *   the fix line says disable only;
    *   a clash on any skill also aborts a `--only` rerun.
    The diagram suggests missing or disabled skills exit 1; only a clash does. Item 13 doesn't list these tests.
*   **Rationale:** The spec and the code have diverged.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Doc drift (commit dd860b9).
*   ***Proposed Edit:***
    *   Location: item 12 bullets, item 13, the diagram line.
    *   Change: Add the five behaviours and their exit codes (0 pass, 1 FAIL or clash, 2 bad arguments). Change the diagram line to `clash → exit 1; missing/disabled → hint`. Add the matching test cases to item 13.

### [Issue 16] [`design_critic, implementation_readiness`] - Severity: Medium
*   **Affected Scope:** [Lines 375-378](docs/designs/skill-reliability.md#L375) (Cost)
*   **Discrepancy Description:** Phase 2 is estimated at $10–30, but each command is capped at $5 across 11 skills (up to $55). The sandbox trigger evals and the 5-run reruns aren't costed, and no per-run figure is given.
*   **Rationale:** The estimate can't be checked.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Correct.
*   ***Proposed Edit:***
    *   Location: Cost bullet.
    *   Change: `Assumes $0.05–0.20 per run (sessions 4–5). Probe sweep ~26 prompts × 3 = $4–16; reworded reruns ≤ 2 × 5 runs per failing skill. Sandbox trigger evals 11 skills × 4 cases × 3 runs = $7–26. Step checks 12 cases × 3 runs × 2 arms = $4–15, capped at $5 per skill (≤ $55). Worst case ≈ $100; each command passes --max-cost-usd.`

### [Issue 17] [`zoom_out, implementation_readiness, codebase_details`] - Severity: Medium
*   **Affected Scope:** [Lines 245-252, 616-623](docs/designs/skill-reliability.md#L245) (way-out candidates, item 23)
*   **Discrepancy Description:** Two candidates are out of date:
    *   codebase-guardian "line 16, skip it for … one-line answers" no longer exists; it was rewritten before any run (D-26), which contradicts "a step that fails gets its wording changed".
    *   decision-maker's fallback is already conditional (exit 2 or 1), not "unconditional".
*   **Rationale:** Stale text and line numbers.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Correct.
*   ***Proposed Edit:***
    *   Location: lines 248-251 and item 23.
    *   Change: `codebase-guardian's "meaningful edit" was tightened up front (D-26), as its looseness was a way out on its face; decision-maker's fallback is already tied to exit codes 1 and 2. Further rewording follows failing step checks only.` Drop the line numbers.

### [Issue 18] [`codebase_details`] - Severity: Medium
*   **Affected Scope:** [Lines 311-313, 384-385](docs/designs/skill-reliability.md#L384) (Alternative B, Safety NFR)
*   **Discrepancy Description:** The probe already grants `Bash` under the owner's real config with no sandbox (`TOOLS` in probe_triggers.py), so "touches nothing outside the temp repo" is a hope, not a guarantee. Alternative B is rejected partly for that same risk.
*   **Rationale:** The safety claim is overstated.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Correct. The probe runs in a temp repo as its working directory, but Bash isn't confined to it.
*   ***Proposed Edit:***
    *   Location: Safety bullet.
    *   Change: `The probe runs claude -p in a throwaway repo with Bash allowed and no sandbox: commands start there but aren't confined to it. Its prompts don't ask for writes outside the repo; review new prompts with that in mind.`

### [Issue 19] [`codebase_details`] - Severity: Medium
*   **Affected Scope:** [Lines 469-474](docs/designs/skill-reliability.md#L469) (item 9)
*   **Discrepancy Description:** "If `site/product/index.html` is generated…" leaves the implementer to find out how the page is built.
*   **Rationale:** Zero-Decision Rule.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The renderer exists and was used.
*   ***Proposed Edit:***
    *   Location: item 9.
    *   Change: `site/product/index.html is generated: edit docs/product/product.json, then run python skills/product-visionary/scripts/render_page.py .`

### [Issue 20] [`codebase_details, implementation_readiness`] - Severity: Medium
*   **Affected Scope:** [Lines 397-407](docs/designs/skill-reliability.md#L397) (Stage 0 steps)
*   **Discrepancy Description:** Step 1's command has no case filter and no `--scaffold`, so it runs all five git-conventions cases, and `does-read-rules` runs without its fixture. Step 2 (Q7) has no command and no pass condition.
*   **Rationale:** As written, Stage 0 can't be run.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Correct.
*   ***Proposed Edit:***
    *   Location: Stage 0 steps 1-2.
    *   Change:
        *   Step 1 → `claude plugin eval skills/wrap-up --case does-protect-main --scaffold --allow-tools Bash Write Edit --runs 1 --ablation none --no-publish --max-cost-usd 1`. It passes Q6 if the run starts and is scored (exit 0 or 1). It fails if the run is refused for lack of a sandbox.
        *   Step 2 → `export TYPESAFE_API_KEY=…; claude plugin eval skills/decision-maker --case does-batch --scaffold --allow-tools Bash --runs 1 --ablation none --no-publish --keep-temp`. It passes Q7 if the transcript shows decide.py did not exit 2 ("not configured").

### [Issue 21] [`codebase_details`] - Severity: Medium
*   **Affected Scope:** [Lines 260-275](docs/designs/skill-reliability.md#L260) (wrap-up fixes)
*   **Discrepancy Description:** wrap-up's Sort section still says "a WIP commit on the current branch beats a deletion", which conflicts with the new protected-branch rule when the current branch is `main`. The doc says "without it, wrap-up behaves as today", but the shipped text now says "ask the user which they want".
*   **Rationale:** Conflicting instructions in the skill, and the doc misdescribes the fallback.
*   ***AI Suggestion:*** PROPOSE FIX (doc) + Code follow-up F8
*   ***Justification:*** Correct on both counts.
*   ***Proposed Edit:***
    *   Location: fix 3 paragraph.
    *   Change: `Without it, wrap-up asks the person whether to merge, open a PR, or keep the branch.`

### [Issue 22] [`all`] - Severity: Low (Nits, bundled)
*   **Affected Scope:** lines 14, 25-31, 90-92, 180-183, 200, 280, 285, 316, 377, 478, 501, 627-630, 650
*   **Discrepancy Description:**
    *   Stale numbers: 1196 tokens is now 1235 (and the per-skill cap of 260 isn't mentioned); the 174 test count is stale.
    *   "CI unchanged", but five test files were added to CI (and CI pins the claude-code version for `validate`).
    *   Problem 1 needs "as of before this work".
    *   The git-conventions near-miss example at line 200 doesn't match item 17.
    *   The line 280 regex isn't the built JSON-anchored one, and the fixture has no remote.
    *   Alternative B's fallback should point to Q6, not Q4.
    *   `--only` matches by prefix without a `-` separator.
    *   `parse_case` reads a two-field prompt containing `|word|` as three fields.
    *   Item 24 omits `--ablation with-without` (it's the default) and lives in "Trigger tests", not its own subsection.
    *   The same fixture is duplicated in about 8 `fixture.sh` files.
    *   The two near-miss mechanisms (probe and sandbox) are never justified.
    *   The preflight's scope should stay "detect and stop".
*   **Rationale:** Accuracy and clarity.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Each is a one-line correction. The fixture duplication is deliberate: a scaffold runs alone in an empty workspace and can't import a shared helper. The two near-miss mechanisms are justified because the sandbox isolates the description, while the real environment shows interference from other installed skills.
*   ***Proposed Edit:*** Apply each correction in place. Add one sentence each on why the fixtures are duplicated and why both near-miss checks exist.

## Code follow-ups (outside the doc — each needs a separate yes)

- **F1** — Reword "Skip steps that don't apply" in the 11 Progress sections to "Report only the steps this run uses", so it can't be read as permission to skip work (Issue 2).
- **F2** — The probe records every repo skill loaded in a run, not just the first, and a `none` line FAILs if any of them fires (Issue 3).
- **F3** — agents-dox's body explicitly runs codebase-guardian's baseline and verify steps in DOX repos. Add a `does-*` case on seed-dox (Issue 4).
- **F4** — The runtime check of the session's skill list exits 1 when a repo skill's name is loaded more than once. A preflight that can't run needs `--no-preflight` (Issue 5).
- **F5** — Widen `does-protect-main`'s branch regex to `git (switch (-c|--create)|checkout -b) wip/`, and make it work when the branch and the commit share one `&&` call (Issue 6).
- **F6** — test-report's case gains a regex on the report file for a pass/fail count; product-visionary's checks that all four modes are offered (Issue 10).
- **F7** — `test_trigger_evals.py` requires `case.yaml` in every `does-*` case (Issue 13).
- **F8** — wrap-up's Sort line becomes "a WIP commit on a `wip/` branch (never a protected one) beats a deletion" (Issue 21).
- **F9** — Set D-24 to "built, not yet run" in decisions.md, matching D-25 and D-26 (Issue 1).
