# Skill Reliability: Triggers, Then Steps

*   **Author:** nikamdhiraj
*   **Status:** Approved — Stages 1–4 built 2026-10-26; probe sweep and step checks not yet run
*   **Date:** 2026-10-26

--------------------------------------------------------------------------------

## Overview

`claude-skills` ships 11 skills. Each skill helps only if two things happen:
Claude loads it when the request calls for it, and once it is loaded, Claude
carries out its steps instead of skipping them. Today the repo checks neither in
a real Claude Code session for most skills. The unit tests (174/174 passing)
check scripts, manifests and the token budget. They do not check what the model
does.

This work runs in two phases. Phase 1 measures and fixes **triggering** for all
11 skills. Phase 2 finds and closes **skipped-step routes** in the skills that
trigger: places where a skill's wording lets Claude cut a required step and
still report the work as done.

## The Problem

**1. Triggering is unmeasured for 8 of 11 skills.** The real-environment probe
(`scripts/probe_triggers.py`, decision D-19) has run prompts only for memory,
schema-aware-db and teammates. agents-dox, codebase-guardian, decision-maker,
git-conventions, lsp, ponytail, product-visionary and test-report have never
been measured with the user's real setup loaded. The one time a description was
measured carefully, it failed: schema-aware-db fired 0/3 on a pasted query until
D-20 reworded it. There is no reason to assume the other 8 are better.

**2. Some skills compete for the same requests.** agents-dox, codebase-guardian
and memory all claim "any edit" or "starting work in a repository" and all three
say "err on trigger". When a user asks for an ordinary edit, at most one of them
can be the first skill Claude loads, and nothing records which one wins or
whether the others load at all.

**3. A skill's name can be taken by another plugin.** On the owner's machine,
`claude plugin list` shows `ponytail@ponytail` (version 4.7.0, a different
plugin whose skill is "the laziest solution that works") installed and enabled.
This repo's `ponytail@claude-skills` is not installed, and neither are
agents-dox and lsp. decision-maker is installed but disabled. Both ponytail
plugins load their skill as `ponytail:ponytail`, so once both are installed, the
session's skill list cannot tell them apart, and the probe's duplicate check
(which compares names) cannot either. No check fails when this happens, and the
user sees no warning.

**4. Nothing checks whether a loaded skill's steps are followed.** Skills such as
test-report ("actually runs them"), codebase-guardian ("validate with the real
toolchain") and schema-aware-db ("introspect the real structure") depend on
Claude doing a concrete action before it claims a result. The probe stops at the
first `Skill` call, so it cannot see whether the toolchain ran, the schema was
read or the tests executed. Weak wording ("should", "if possible", "where
relevant", unconditional fallbacks such as "falls back to your own judgment")
gives Claude a way out that no test catches.

**Why it matters:** the product goal says each skill "triggers when relevant,
works on its own". Today the repo can prove the first half for 3 skills and the
second half for none. A user who installs a skill that never loads, or that
loads and then skips its key step, pays the context cost of its description in
every session and gets nothing back.

## Goals

*   **G1 — Every skill measured.** Each of the 11 skills has at least one prompt
    that should trigger it and one similar prompt that should not, in
    `probes/prompts.txt`. All of them have been run in the real environment, and
    the results are recorded in a dated test report.
*   **G2 — Trigger bar.** Each skill fires on its positive prompt in 3 of 3
    runs and on its near-miss prompt in 0 of 3 runs. A skill whose
    description was reworded must pass at 5 of 5 and 0 of 5. Any skill that
    misses this bar after its description is reworded gets a written reason in
    `docs/product/decisions.md` (for example, "the built-in memory feature takes
    this request by design", as with D-21).
*   **G3 — Overlap resolved.** For the edit-time skills (agents-dox,
    codebase-guardian, memory), the probe shows which one fires for an ordinary
    edit request. That outcome matches a rule written in their descriptions, not
    chance.
*   **G4 — Name clashes detected.** The probe exits with an error, not just a
    printout, when a skill from this repo is shadowed by another loaded skill of
    the same name, and the README says how to fix it.
*   **G5 — Key steps checked.** For each skill that passes G2, its one or two
    must-do steps (the action without which the skill's output is false) are
    listed. A real-environment check confirms the step ran, from the tool calls
    in the transcript, not from Claude's own summary.
*   **G6 — Way-out wording removed.** Each must-do step in each `SKILL.md` is
    worded as a requirement with a stated proof ("run X; quote its exit code"),
    and each allowed fallback names the condition that permits it.
*   **G7 — No budget regression.** The combined description cost stays within
    the 1400-token budget enforced by `scripts/check_token_budget.py` in CI. It
    is 1196 today.
*   **G8 — wrap-up replaces ponytail.** This repo's ponytail skill is renamed
    `wrap-up`, so it no longer shares a name with `ponytail@ponytail`. It
    follows the user's git rules (never commits or pushes to a protected
    branch), keeps its hand-off report beyond the chat, and hands branch
    merging to `finishing-a-development-branch` when that skill is installed.

## Non-Goals

*   **Adding new skills or features.** Roadmap items C25 (health panel) and C26
    (commit check) and proposal C7 (merging memory, agents-dox and
    codebase-guardian) stay where they are.
*   **Running the real-environment probe in CI.** It uses the owner's
    credentials and costs money per run. It stays a manual, local step.
*   **Proving step-following in every possible case.** Phase 2 checks the one
    or two steps per skill whose absence makes the output false. It does not try
    to cover every line of every `SKILL.md`.
*   **Fixing other people's plugins.** The ponytail clash is removed by
    renaming this repo's skill, and the probe detects any future clash. This
    work does not change or remove another plugin.
*   **Changes to claude.ai copies.** Replacing older uploaded copies on claude.ai
    remains the owner's manual step (D-22).
*   **A release.** Cutting version 1.12.0 or later is a separate decision for the
    owner.

## Open Questions

*   **Q6 — Does the Windows copy of Claude Code get a sandbox inside WSL2?**
    `claude` in the owner's Ubuntu resolves to the Windows npm install
    (`/mnt/c/.../npm/claude`). Step 0 of the implementation answers this with
    one cheap run; the fallback is a Linux install inside Ubuntu.
*   **Q7 — Does a Jev key reach the eval session?** `prompt.md` `env` accepts
    only `EVAL_*` keys, and decision-maker reads `TYPESAFE_API_KEY` (or its
    config under `~/.config`). Whether a key exported in the WSL shell reaches
    the sandboxed run is not documented. Step 0 checks it.

### Resolved

*   **Q1 — Sample size (resolved):** 3 runs per prompt for the full sweep; any
    skill whose description changed reruns at 5 runs and must pass 5/5.
*   **Q2 — Edit ownership (resolved):** by context file. agents-dox owns
    ordinary edits in a repo that has `AGENTS.md`; codebase-guardian owns them
    everywhere else. memory keeps bootstrap and remember requests and stops
    claiming edits.
*   **Q3 — decision-maker and product-visionary (resolved):** both are in
    full scope. The owner provides a Jev key for decision-maker's step check.
    product-visionary's step check grades the reply, since an eval run has no
    user to answer the mode question.
*   **Q4 — Where phase 2 runs (resolved):** WSL2 Ubuntu. First try the
    existing Windows copy of Claude Code from inside Ubuntu; install a Linux
    copy only if the sandbox refuses (Q6).
*   **Q5 — The ponytail clash (resolved):** rename this repo's skill to
    `wrap-up`. Existing installs reinstall once; the README carries the
    migration line.

--------------------------------------------------------------------------------

## Technical Plan (Architecture)

The plan reuses the two test tools the repo already has and adds no new runner.

| Tool | Runs where | Sees | Used for |
|---|---|---|---|
| `scripts/probe_triggers.py` | owner's machine, real config, native Windows | which skill fired first; which skills loaded | Phase 1 real-environment triggering |
| `claude plugin eval` (`skills/*/evals/`) | sandbox, only the plugin under test | every tool call, files created, final reply | Phase 1 near-miss cases; Phase 2 step checks |

```text
            Phase 1: does it fire?                    Phase 2: does it do the step?
 ┌──────────────────────────────────────┐   ┌──────────────────────────────────────────┐
 │ probes/prompts.txt  id|expect|prompt │   │ skills/<s>/evals/does-<step>/            │
 │            │                         │   │   prompt.md   (task + allowed tools)     │
 │            ▼                         │   │   case.yaml   (scaffold: tiny fixture)   │
 │ preflight: claude plugin list --json │   │   graders/    (tool_order, tool_used,    │
 │   missing / disabled / clashing ─►exit 1  │                regex, file_exists)       │
 │            │                         │   │            │                             │
 │            ▼                         │   │            ▼                             │
 │ claude -p × runs  ─► fired skill     │   │ claude plugin eval --ablation            │
 │            │                         │   │   with-without --allow-tools ...         │
 │            ▼                         │   │            │                             │
 │ compare with expect ─► PASS/FAIL,    │   │            ▼                             │
 │   exit 1 on any miss                 │   │ score (with skill) + delta (vs without)  │
 └──────────────────────────────────────┘   └──────────────────────────────────────────┘
                    │                                           │
                    └──────────► test-reports/<date>.md ◄───────┘
```

### Phase 1 — triggering

1.  **Expected outcome in the prompts file.** `probes/prompts.txt` lines gain
    an optional middle field: `id|expect|prompt`, where `expect` is a skill's
    base name (`test-report`) or `none`. Lines with two fields keep working and
    are reported without a verdict. The probe marks a case as passing when a
    positive case fires the expected skill in every run, and a `none` case
    fires none of this repo's skills in any run. The probe exits with code 1 if
    any case misses. It stays a manual, local tool (Non-Goal).
2.  **Install preflight.** Before the first run, the probe reads
    `claude plugin list --json` and the skill names under `skills/`. For each
    repo skill it reports one of: installed from `claude-skills`, missing,
    disabled, or **clashing** (an enabled plugin of the same name from another
    marketplace, as with `ponytail@ponytail`). A clash ends the run with exit 1
    and a fix line (disable the other plugin for the probe, or uninstall it).
    Missing or disabled skills are listed with the `-- --plugin-dir skills/<s>`
    argument that probes the working copy instead. The preflight is needed
    because the session's skill list carries only names, so a clash is
    invisible after launch.
3.  **Two prompts per unmeasured skill.** One positive prompt worded the way a
    user would ask (not quoting the description), and one **near-miss**: a
    request on the same subject that the skill should leave alone (for
    git-conventions: "explain what `git rebase` does", which mentions git but
    asks for no commit, branch or PR). Both go in `probes/prompts.txt`; the
    seeded repo `probes/seed-db` gains whatever the prompts need (a test file,
    an `AGENTS.md`).
4.  **Near-miss cases in the sandbox too.** Each skill's current quiet case is
    off-topic (a haiku, a sea poem), which only proves the skill does not fire
    on everything. Each skill gets one `quiet-near-<topic>` eval case with the
    same near-miss prompt and a `tool_used` grader on `Skill` with `min: 0`,
    `max: 0`, `arm: both`. `scripts/test_trigger_evals.py` then requires at
    least one near-miss case per skill.
5.  **Edit ownership rule (G3).** By context file (Q2): agents-dox owns an
    ordinary edit in a repo with `AGENTS.md`, codebase-guardian owns it
    elsewhere. The same edit prompt runs against two seeded repos, one with
    `AGENTS.md` (`expect` agents-dox) and one without (`expect`
    codebase-guardian). The three edit-time descriptions each get one boundary
    clause, paid for by trimming elsewhere so the total stays within the
    1400-token budget (G7).
6.  **Fix loop.** For each failing skill: reword the description, rerun only
    that skill's lines (`--only <skill>`, a new probe filter), and record the
    before and after in the test report. A skill that still fails after two
    rewrites gets a decision entry explaining why (G2) instead of a third
    rewrite.

### Phase 2 — skipped steps

For each skill that passes phase 1, name the one or two **must-do steps**: the
actions without which the skill's output is false. Each becomes one sandbox eval
case, `does-<step>`, seeded by a `case.yaml` scaffold script with a small
fixture project, run with `--ablation with-without` so the report shows whether
the skill *causes* the step (the delta), not only whether it happened.

| Skill | Must-do step | Grader (from the documented grader types) |
|---|---|---|
| schema-aware-db | read the real schema before changing a query | `tool_order`: `Read` of `schema.sql` before the first `Edit` |
| codebase-guardian | run tests before and after the edit | `tool_used` `Bash` matching the test command, `min: 2`; `tool_order` test run before `Edit` |
| test-report | actually run the tests it wrote | `tool_used` `Bash` matching the runner; `regex` on the report file: pass count present |
| git-conventions | read the rules before committing | `tool_order`: `Read` of `git-conventions.md` before `Bash` `git commit`; `regex` on the commit subject |
| agents-dox | read the AGENTS.md chain before editing | `tool_order`: `Read` of `AGENTS.md` before `Edit` |
| memory | bootstrap writes the root file | `file_exists`: `MEMORY.md` |
| lsp | use the language-server script, or show the install hint | `tool_used` `Bash` matching `lsp.py`; `regex` on the reply for the hint when no server exists |
| wrap-up (was ponytail) | check git state before the final report | `tool_used` `Bash` matching `git status` and `git stash list` |
| teammates | create the shared manifest before spawning peers | `tool_order`: `Write` of `.teammates/state.json` before `Agent` |
| product-visionary | ask the autonomy mode before acting | `regex` on the reply: the four modes are offered; `tool_used` `Edit` with `min: 0`, `max: 0` |
| decision-maker | one batched call for many items | `tool_used` `Bash` matching its script, `min: 1`, `max: 1` |

A step that fails gets its `SKILL.md` wording changed. Each must-do step is
written as a requirement with its proof ("run the tests; quote the exit code"),
and each allowed skip names its condition (G6). The current wording is already
strict in most skills: a search for soft words ("should", "if possible",
"skip", "fall back") finds few way-outs. The main ones are codebase-guardian's
"skip it for … one-line answers", with no definition of what counts as one,
and decision-maker's unconditional fallback to Claude's own judgement. So most
of phase 2's value is expected to come from the checks, not from rewording.

### ponytail becomes wrap-up, with three fixes

The rename removes the name clash (Q5). The other `ponytail@ponytail` plugin does
a different job (write the least code possible), so it is not a competitor.
The skill that overlaps is superpowers' `finishing-a-development-branch`, which
covers merging a finished branch but not stashes, unpushed work, session debris,
chat promises or a handoff report. Three gaps in the current text are fixed:

1.  **Git rules first.** Before any commit or push, read
    `.claude/git-conventions.md` or `~/.claude/git-conventions.md` if one
    exists. Never commit or push to a protected branch (from that file, or
    `main`/`master` when there is no file). Work that needs saving while on a
    protected branch goes to a new branch `wip/<YYYY-MM-DD>-<slug>`, and the
    tail names it. Commit messages follow the file's pattern.
2.  **A tail that outlives the session.** The tail is still the final chat
    message. In addition, the hand-off part of it goes into the body of the WIP
    commit (or the stash message) so it travels with the work, and into
    `MEMORY.md` when the memory skill is installed.
3.  **Hand off integration.** After the sweep, if a finished branch needs
    merging or a PR and `finishing-a-development-branch` is installed, wrap-up
    hands that step to it instead of repeating its merge and PR logic.
    Without it, wrap-up behaves as today.

Phase 2 adds one case for fix 1: `does-protect-main`, seeded on `main` with an
uncommitted change. Graders: `tool_order` with `Bash` matching
`git (switch -c|checkout -b) wip/` before `Bash` matching `git commit`; and
`tool_used` `Bash` matching `git push.*\bmain\b` with `min: 0`, `max: 0`.

### What does not change

The probe's output format for two-field lines, the existing `fires-*` and
`quiet-*` cases, CI (neither the probe nor the evals run there), and every
skill's file layout.

## Alternatives Considered

### Alternative A: Reword only, no step checks

Tighten every `SKILL.md` with stronger wording ("MUST", tables of excuses to
reject) and skip building checks.

*   **Pros**: Fast. No new eval cases. Works on any platform.
*   **Cons**: No way to tell whether a rewrite changed behaviour. Stronger
    wording costs tokens in the body (and in the description if it spreads
    there). The search for soft words found few way-outs, so there is little
    to reword.
*   **Reason for Rejection**: It cannot meet G5, and the owner asked to "make
    sure we deliver", which needs evidence, not wording.

### Alternative B: Check steps in the real-environment probe

Extend `probe_triggers.py` to record every tool call after the `Skill` call and
match it against expected commands, instead of using `claude plugin eval`.

*   **Pros**: Runs on native Windows with no WSL2. Uses the owner's real setup,
    so it also catches interference from other plugins.
*   **Cons**: The probe would need its own grader logic (order, counts, file
    contents), which `claude plugin eval` already provides. Granting Bash and
    Edit runs real commands on the owner's machine with no sandbox. There is no
    without-skill comparison, so a pass cannot tell whether the skill caused
    the step.
*   **Reason for Rejection**: It duplicates a documented tool and gives weaker
    evidence. It stays the fallback if Q4 is answered "no WSL2".

### Alternative C: Enforce steps with hooks

Add `PreToolUse` hooks that block the next action until the must-do step has
happened (for example, refuse `Edit` on a query file until the schema has been
read).

*   **Pros**: A real guarantee instead of a measurement. decision-maker and
    product-visionary already ship hooks, so the pattern exists in the repo.
*   **Cons**: Hooks run in every session, not only when the skill loaded, so
    each one needs its own "is this skill active?" logic. They add work on
    every tool call. A wrong block stops the user's work, which breaks the
    "fail open" rule in the professional review. 11 skills would need 11 hook
    designs. The product panel has already vetoed a Stop hook and hooks that
    write files (session 4 log, D-12).
*   **Reason for Rejection**: Too much risk and cost to apply to every skill
    at once. Listed under Future Improvements for any single step that keeps
    failing after phase 2.

### Alternative D: A new test runner for both phases

Write one harness that runs prompts, parses full transcripts and grades both
triggering and steps.

*   **Pros**: One tool and one report format.
*   **Cons**: Rebuilds what `probe_triggers.py` and `claude plugin eval`
    already do, and adds code to maintain and test. D-14 already chose
    `claude plugin eval` for skill tests.
*   **Reason for Rejection**: More code for no new capability.

### Alternative E: Merge the overlapping edit-time skills

Combine memory, agents-dox and codebase-guardian so the overlap in G3 cannot
happen.

*   **Pros**: Removes the overlap for good.
*   **Cons**: Breaks existing installs. The product panel already turned this
    down as proposal C7 (vetoed by the User advocate and the Skeptic).
*   **Reason for Rejection**: A one-sentence ownership rule in three
    descriptions solves the measured problem at a fraction of the cost.

### Alternative F: Grade steps with the LLM judge

Use `llm` graders ("did Claude read the schema before editing?") instead of
`tool_order` and `tool_used`.

*   **Pros**: Easy to write. Works for steps with no clear tool call, such as
    asking the user a question.
*   **Cons**: Each grader takes three judge votes, which adds cost and noise.
    The judge reads the transcript, so it can be swayed by Claude's own claim
    that it did the step: the same weakness this work is meant to catch.
*   **Reason for Rejection**: Deterministic graders first. `llm` only where no
    tool call can show the step, and the report marks those checks as weaker.

--------------------------------------------------------------------------------

## Non-Functional Requirements

*   **Cost:** the probe and the evals call the model with the owner's
    credentials. Every eval command passes `--max-cost-usd`. Expected spend:
    phase 1 sweep $4–14, phase 2 first pass about $10–30 (12 cases × 3 runs ×
    2 arms). Actual spend goes in the test report.
*   **Context budget:** combined descriptions stay ≤ 1400 tokens
    (`scripts/check_token_budget.py`, enforced in CI).
*   **Rollout:** the rename breaks existing `ponytail@claude-skills` installs.
    The README gives the two commands to move over. The other changes are
    backward compatible (two-field probe lines still work).
*   **Safety:** phase 2 runs inside the eval sandbox under WSL2. The probe
    keeps its throwaway temp repo and touches nothing outside it.

--------------------------------------------------------------------------------

## Detailed Implementation Plan

Work happens on branch `skill-reliability` (repo rule: short kebab slug), in
four pull requests, one per stage, each squash-merged. Commit subjects follow
`<area>: <summary>`; decisions use their `D-<n>` id.

### Stage 0 — Environment check (no repo changes until it passes)

1.  In WSL2 Ubuntu, run one existing trigger case with tools granted:
    `claude plugin eval skills/git-conventions --runs 1 --ablation none
    --allow-tools Bash --max-cost-usd 1 --no-publish`. If the run is refused
    for lack of a sandbox (Q6), install Claude Code inside Ubuntu
    (`npm install -g @anthropic-ai/claude-code` with a Linux Node), sign in,
    and repeat.
2.  Export the Jev key in the WSL shell and run decision-maker's provider check
    from inside an eval run (one throwaway case outside the repo). If the key
    does not reach the run (Q7), decision-maker's phase 2 case is recorded as
    blocked in the test report and a decision entry; the rest of the plan does
    not depend on it.

### Stage 1 — Rename ponytail to wrap-up, with the three fixes

#### 1. `skills/ponytail/` → `skills/wrap-up/` (Move)

*   **Type / Scope**: skill folder, moved with `git mv` to keep history.
*   **Proposed Changes**: the whole folder moves. Contents change as below.

#### 2. `skills/wrap-up/SKILL.md` (Modify)

*   **Type / Scope**: skill instructions.
*   **Proposed Changes**: `name: wrap-up`. The title and the opening metaphor
    stop referring to a ponytail. Description keeps its trigger phrases and
    stays within the budget. Sweep is unchanged. Tie-off gains fix 1 (read git
    rules; never commit or push to a protected branch; WIP to
    `wip/<YYYY-MM-DD>-<slug>`). The tail section gains fix 2 (hand-off text in
    the WIP commit body or stash message; `MEMORY.md` when memory is
    installed). Companion skills gain fix 3 (hand merge/PR to
    `finishing-a-development-branch` when installed) and name git-conventions.

#### 3. `skills/wrap-up/README.md` (Modify)

*   **Proposed Changes**: new name, the three behaviours above, install and
    update steps, and the migration line:
    `claude plugin uninstall ponytail@claude-skills` then
    `claude plugin install wrap-up@claude-skills`.

#### 4. `skills/wrap-up/.claude-plugin/plugin.json` (Modify)

*   **Proposed Changes**: `name` and `description` to wrap-up. Version stays in
    lockstep with the other manifests.

#### 5. `skills/wrap-up/evals/*/graders/*.md` and `prompt.md` (Modify)

*   **Proposed Changes**: `input_match` and descriptions name `wrap-up`. The
    case `fires-on-wrap-up` keeps its name.

#### 6. `.claude-plugin/marketplace.json` (Modify)

*   **Proposed Changes**: the plugin entry becomes `wrap-up` with
    `source.path` `skills/wrap-up` and homepage path updated. The marketplace
    description says "wrap-up" instead of "ponytail".

#### 7. `.claude-plugin/plugin.json` (Modify)

*   **Proposed Changes**: the collection description names wrap-up.

#### 8. Cross-references (Modify)

*   `skills/agents-dox/SKILL.md` line 133, `skills/codebase-guardian/SKILL.md`
    line 122, `skills/memory/SKILL.md` line 242, `skills/teammates/SKILL.md`
    line 217: "ponytail" → "wrap-up".
*   `skills/decision-maker/README.md` line 202,
    `skills/decision-maker/references/use-cases.md` (§1 and §2 headings and
    table rows), `skills/decision-maker/scripts/eval_usecases.py` (use-case
    keys and labels): "ponytail" → "wrap-up".
*   **Not changed:** the `# ponytail:` comments in
    `skills/decision-maker/scripts/guard.py` (lines 417, 750) and `run.sh`
    (line 6). They are markers from the other ponytail plugin, not references
    to this skill.

#### 9. `README.md`, `PRODUCT.md`, `docs/product/product.json`, `site/index.html`, `site/product/index.html` (Modify)

*   **Proposed Changes**: skill list, feature map and pages name wrap-up. The
    README's install list and migration note are updated. If
    `site/product/index.html` is generated from `product.json` by the
    product-visionary renderer, regenerate it instead of editing it by hand.

#### 10. `skills/wrap-up/evals/does-protect-main/` (Create)

*   **Type / Scope**: eval case: `prompt.md` ("wrap up, I'm done for today"),
    `case.yaml` with a scaffold script that makes a git repo on `main` with
    one commit and one uncommitted change, and two graders as in the Technical
    Plan.

#### 11. `docs/product/decisions.md` (Modify)

*   **Proposed Changes**: new entry D-23: rename to wrap-up and why (name
    clash with `ponytail@ponytail`; the two skills share no purpose), plus the
    three fixes. Older entries that say "ponytail" stay as written.

### Stage 2 — Phase 1: triggering

#### 12. `scripts/probe_triggers.py` (Modify)

*   **Type / Scope**: Python 3.9+, stdlib only.
*   **Proposed Changes**:
    *   Parse lines as `id|prompt` or `id|expect|prompt`. `expect` is a skill
        base name or `none`.
    *   Compare on the base name (text after the last `:`).
    *   Verdict per case: positive passes when the expected skill fired in
        every run; `none` passes when no skill from this repo fired in any run.
        Print `PASS`/`FAIL`/`-` (no expectation) per line.
    *   `--only <skill>`: run only lines whose `expect` or id prefix is that
        skill.
    *   Preflight before any run: run `claude plugin list --json`; read repo
        skill names from `skills/*/SKILL.md` frontmatter. For each repo skill,
        report `ok` (`<name>@claude-skills` enabled), `missing`, `disabled`
        or `clash` (an enabled plugin `<name>@<other marketplace>`). A clash
        exits 1 with the fix line. Missing and disabled skills print the
        `-- --plugin-dir skills/<name>` hint. The plugin-list call is passed
        into `main()` the same way `runner` is, so tests supply a fake list.
    *   Exit code: 1 if any verdict is FAIL or a clash was found; 0 otherwise.
    *   Docstring updated with the new format and flags.

#### 13. `scripts/test_probe_triggers.py` (Modify)

*   **Type / Scope**: pytest, fake runner and fake plugin list (no model
    calls).
*   **Proposed Changes**: positive: three-field line passes when every run
    fires the expected skill; `--only` filters. Positive: preflight reports
    `ok`/`missing`/`disabled` from a sample JSON. Negative: one run without the
    skill gives FAIL and exit 1; a `none` line that fires a repo skill gives
    FAIL; a `<name>@other` entry gives `clash` and exit 1. Two-field lines
    still print with no verdict.

#### 14. `probes/prompts.txt` (Modify)

*   **Proposed Changes**: every line moves to three fields. Existing lines
    keep their ids with `expect` added (`memory-remember` gets `none`, per
    D-21). Add a positive and a near-miss line for each of the 8 unmeasured
    skills, plus `guardian-edit|codebase-guardian|Rename the function
    save_order to create_order in app.py.` Near-miss prompts are the same
    as in item 17.

#### 15. `probes/prompts-dox.txt` and `probes/seed-dox/` (Create)

*   **Proposed Changes**: `probes/seed-dox/` holds only a root `AGENTS.md`
    (a short DOX contract); `--seed` takes a comma list and layers seeds in
    order, so `--seed probes/seed-db,probes/seed-dox` adds it to the shop
    without duplicating files. The prompts file has
    `agents-dox-edit|agents-dox|Make slugify in utils.py also strip leading
    and trailing dashes.` (an edit away from the database code, so
    schema-aware-db has no claim on it).

#### 16. `probes/seed-db/` (Modify)

*   **Proposed Changes**: add `test_app.py` (one passing pytest test) so the
    test-report and codebase-guardian prompts refer to a project that has
    tests.

#### 17. `skills/<each>/evals/quiet-near-<topic>/` (Create, 11 cases)

*   **Type / Scope**: `prompt.md` (tags `[trigger, negative, near-miss]`,
    runs 3) and `graders/skill-quiet.md` (`tool_used`, `tool: Skill`,
    `input_match` on the skill's name, `min: 0`, `max: 0`, `arm: both`).
*   **Near-miss prompts**:
    *   agents-dox: "Write a CONTRIBUTING.md for this project."
    *   codebase-guardian: "Explain what this regex matches: `^\d{3}-\d{4}$`"
    *   decision-maker: "Should I learn Rust or Go next year?"
    *   git-conventions: "Explain how git rebase differs from git merge."
    *   lsp: "What does Python's functools.lru_cache do?"
    *   memory: "How much memory does a Python dict with a million int keys use?"
    *   product-visionary: "Write a product description for a coffee grinder."
    *   schema-aware-db: "Explain the difference between a LEFT JOIN and an
        INNER JOIN."
    *   teammates: "Spawn one subagent to list the TODO comments in this repo."
    *   test-report: "What is the difference between unit and integration
        tests?"
    *   wrap-up: "Wrap this paragraph at 72 columns: …"

#### 18. `scripts/test_trigger_evals.py` (Modify)

*   **Proposed Changes**: require at least one `quiet-near-*` case per skill.
    The "graders name their own skill" check applies to `fires-*` and
    `quiet-*` cases only, so the new `does-*` cases (which grade Bash, Read
    and Edit) are allowed. Add a check that every `does-*` case has a
    `case.yaml`, the tag `step`, and at least one grader that is not on
    `Skill`.

#### 19. `skills/agents-dox/SKILL.md`, `skills/codebase-guardian/SKILL.md`, `skills/memory/SKILL.md` (Modify)

*   **Proposed Changes**: descriptions only (G3). agents-dox: owns ordinary
    edits when the repo has `AGENTS.md`. codebase-guardian: owns edits in
    repos without `AGENTS.md`; with one, defers to agents-dox. memory: drops
    the general claim on edits and keeps bootstrap, remember and "after code
    changes that alter a module's purpose". Other words trimmed to pay for
    the clauses (G7).

#### 20. Descriptions of skills that fail the sweep (Modify, conditional)

*   **Proposed Changes**: reworded per the fix loop; at most two rewrites per
    skill, each rerun at 5 runs. A skill that still fails gets a decision
    entry instead. Which files change is known only after the sweep.

#### 21. `README.md` (Modify)

*   **Proposed Changes**: the "Trigger tests" section documents the
    three-field format, `--only`, the preflight, and the two seeds. If the
    memory or schema-aware-db description changes, the quoted description
    lengths in "Use on claude.ai" are updated (checked by
    `scripts/test_claude_ai_upload.py`).

### Stage 3 — Phase 2: step checks

#### 22. `skills/<each>/evals/does-<step>/` (Create, 11 cases + item 10)

*   **Type / Scope**: `prompt.md` (tags `[step]`; `allowed_tools` read-only,
    with Bash/Edit/Write granted at run time), `case.yaml` with a scaffold
    script that builds a small fixture project, and graders from the Technical
    Plan table.
*   **Cases**: schema-aware-db `does-read-schema`, codebase-guardian
    `does-baseline-tests`, test-report `does-run-tests`, git-conventions
    `does-read-rules`, agents-dox `does-read-chain`, memory
    `does-bootstrap-file`, lsp `does-use-server`, wrap-up `does-check-git`,
    teammates `does-manifest-first`, product-visionary `does-ask-mode`,
    decision-maker `does-batch` (blocked if Q7 fails).

#### 23. `skills/<each>/SKILL.md` (Modify, conditional)

*   **Proposed Changes**: for each failing step, reword it as a requirement
    with proof and name the condition for any allowed skip (G6). Known
    candidates before any run: codebase-guardian line 16 ("skip it for …
    one-line answers": define what counts) and decision-maker's fallback
    (state when it applies: exit code 2 or 1, as the rules section already
    says, and nothing else).

#### 24. `README.md` (Modify)

*   **Proposed Changes**: a "Step checks" subsection with the WSL2 command:
    `claude plugin eval skills/<s> --tag step --ablation with-without
    --allow-tools Bash Write Edit --scaffold --runs 3 --max-cost-usd 5
    --no-publish`.

### Stage 4 — Record

#### 25. `test-reports/<date>-skill-reliability.md` (Create)

*   **Proposed Changes**: phase 1 table (prompt, expected, before, after,
    runs), phase 2 table (case, score with skill, delta without), cost,
    blocked items, rerun commands.

#### 26. `docs/product/decisions.md`, `docs/product/roadmap.md`, `PRODUCT.md` (Modify)

*   **Proposed Changes**: decisions D-24 (edit ownership by context file),
    D-25 (near-miss cases and probe verdicts), D-26 (step checks under WSL2),
    and one entry per skill that misses the bar. Roadmap: C30 moves to done.
    PRODUCT.md "Where we are" gives the new numbers.

### Verification Plan

*   **Unit tests**: `python -m pytest -q scripts/ skills/*/scripts` passes
    (174 today, plus the new probe and eval-structure tests), on the CI
    matrix (Linux, Windows, macOS; Python 3.9, 3.12, 3.13).
*   **Static checks**: `python scripts/check_token_budget.py` ≤ 1400;
    `claude plugin validate` on every manifest, including wrap-up's.
*   **Sandbox triggers**: `claude plugin eval skills/<s> --tag trigger` for
    all 11 skills: every `fires-*` and `quiet-*` case 3/3.
*   **Real environment**: `python scripts/probe_triggers.py probes/prompts.txt
    --runs 3 --seed probes/seed-db` and the same with `prompts-dox.txt` and
    `seed-dox`, exit code 0; reworded skills rerun with `--only <skill>
    --runs 5`.
*   **Step checks**: Stage 3 command per skill in WSL2: every `does-*` case
    scores 1.0 with the skill, and the report records its delta against the
    run without it.
*   **Rename**: `git grep -i ponytail` finds only the `# ponytail:` comments,
    historical decision entries and test reports.

--------------------------------------------------------------------------------

*Drafted with EGM*
