# Product Visionary Skill — Design

**Date:** 2026-10-21
**Status:** Draft, awaiting approval (builder check done)
**Repo:** claude-skills
**Depends on:** `test-report` (PR #4); built on branch `claude/product-visionary-skill` off it.

## Intent

The user wants a skill that acts as a **visionary product manager** for a codebase.
It reads the code, works out what the product is trying to achieve and how far along
it is, shows how every feature connects to and contributes to that goal, finds real
issues by running `test-report`, and — when left on auto — makes and carries out
decisions itself: fixes the top issues, finds improvements, and keeps everything working
at the end.

Decisions are not made by one agent. A **panel of 3, 6, or 9 Claude agents** discusses
each decision and must reach a conclusion. Panel size scales with how big the decision is.

The user decides at the **start of every session** how much autonomy the skill gets.

## Goals

1. Tell the user, in plain language: the product's **goal**, **where it stands**, and a
   **feature map** (how features connect and how each contributes to the goal / success).
2. Find real issues by running `test-report` on the key features — not by guessing.
3. Decide what to do next through a panel discussion that converges on a conclusion.
4. In the higher autonomy modes, act on the decision: fix the top issues, verify with
   `test-report`, and leave the product working.
5. Keep durable state so each session starts where the last one ended.

## Non-goals

- Not a general project-management tool (no Jira/Linear sync, sprints, estimates).
- Doesn't decide the product goal by itself — it infers one, but the user confirms it.
- Doesn't replace `test-report`, `teammates`, or `codebase-guardian`; it calls on them.

## Anti-goals (a failure even if it "works")

- Silently changing what the product is for, or deleting a feature without asking.
- A big unreviewable pile of changes from one run.
- Claiming something is fixed without a passing `test-report` run that shows it.
- A panel that just rubber-stamps the first idea — the discussion must actually weigh
  alternatives and record the argument that won.
- Leaving the codebase broken at the end of a run.

## Session start — autonomy menu (user decided)

At the start of each session the skill asks the user to pick one:

1. **Report only** — goal, state, feature map, test run, ranked issues. Changes no code.
2. **Fix on a branch** — panel decides, Claude fixes the top issues on a branch,
   re-runs `test-report`, opens a PR. The user merges.
3. **Full auto** — as 2, but merges itself when tests pass, then **loops in batches of
   3** (user decided): re-test, re-run the panel, pick the next 3, act — until nothing
   important is left. Stop conditions (my call): the ranking panel finds no item worth
   doing; a fix in the batch can't be proven green; a veto flag fires; or 5 batches done
   (session ceiling, so a run can't sprawl — the user can start another session).

The answer applies to this session only; it is never remembered as a standing permission.

**Always ask first, in every mode (user agreed):** deleting a feature, changing the
product goal, anything touching payments / auth / secrets, database migrations, force-push.

**Cap (user agreed):** at most 3 items per batch. Mode 2 runs one batch; mode 3 loops.

**What counts as an item (user decided):** fixes for issues found by tests, small
improvements, **and new features**. The session-start permission is the only approval
needed — in full auto the skill builds big new features without asking per feature
(user decided). The user verifies the results at the end of the session.

- Mode 2 builds features too, but each lands as a PR the user merges.
- Mode 1 only writes feature proposals to the roadmap.

**How a new feature is built (my call):**
1. The ranking panel proposes it with: what it is, which part of the goal it serves,
   which features it connects to, size (small / medium / large).
2. Small → counts as one of the batch's 3 items. Medium/large → gets **a batch of its
   own** and a 6-panel to agree the build approach (9-panel if it changes the product's
   direction).
3. Built on its own branch + PR; `test-report` writes and runs 2+1 tests for it; the
   existing suite must show no new failures; mode 3 merges, mode 2 leaves the PR.
4. `PRODUCT.md` feature map and roadmap are updated in the same PR.

**End-of-session verification (user decided):** the final report lists every item done,
with PR links, test results, and the decision-log entry, so the user can verify the
session.

## Decisions made during review (my calls unless noted)

- **`test-report` absent:** follow a built-in short copy of its rules (repo convention:
  every skill works standalone). Its "ask before installing a framework" rule is never
  overridden, even in full auto. Its "don't fix app code" rule applies to its own test
  step only; this skill's act step does the fixing.
- **Panel granularity:** one 3-panel ranks all candidates per batch. Any picked item that
  is medium or direction weight then gets its own 6- or 9-panel before it's acted on.
- **Pass / merge gate:** the new `test-report` tests pass **and** the project's existing
  suite (plus build/lint if configured) has no new failures versus a baseline taken at
  the start of the run. Unprovable fix (blocked, flaky, red) → left as an open PR,
  not merged; in mode 3 this also stops the loop.
- **Merging in mode 3:** one branch + PR per item, merged with `gh pr merge --squash`.
  Never force-push; if the branch is protected or needs review, stop at the PR.
- **Report-only file writes:** tests, `test-reports/`, and state files are written to the
  working tree but not committed; the user is told where they are. In modes 2/3 state
  updates go into each PR.

## Durable state (my call on names and location)

At the root of the analysed project:

- `PRODUCT.md` — goal (user-confirmed), where we are, feature map.
- `docs/product/roadmap.md` — ranked list: fix / build / cut next, with one-line why.
- `docs/product/decisions.md` — append-only decision log (format above).
- `test-reports/` — written by `test-report`, linked from `PRODUCT.md`.

## Ideas offered by me and accepted by the user

Running state file, dead/orphan feature flags, ranked roadmap, decision log.

## Repo integration

Same shape as every other skill: `skills/product-visionary/` with `SKILL.md`, `README.md`,
`.claude-plugin/plugin.json`; root README table row; entries in
`.claude-plugin/marketplace.json` and `plugin.json`; must pass
`scripts/check_token_budget.py` (currently 1183/1200 — raising `TOTAL` for a 10th skill
is acceptable). Name `product-visionary` is my call.

## Left to the builder

- Exact wording of panel prompts and the brief.
- Whether the feature map is a table, a Mermaid diagram, or both.
- How to pick "features that matter most" for the test run.
- Splitting `SKILL.md` into `references/` files if it gets long.
