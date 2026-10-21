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

- Silently changing what the product is for, or deleting a feature — without asking
  (modes 1–3) or without it being logged and called out in the end report (mode 4).
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

4. **Complete auto** (user decided) — as 3, but asks **nothing**: the "always ask first"
   list below is skipped too, ties go to the panel's top option, and veto flags are
   logged instead of asked. The start-of-session choice is the only permission.
   Kept even here (my call — these are about recoverability, not permission): every
   change still goes through a branch + PR, so any merge can be reverted; never rewrite
   or force-push the default branch; never write secret values into code, logs, or
   reports. Claude Code's own permission settings still apply — the skill can't bypass them.

The answer applies to this session only; it is never remembered as a standing permission.

**Always ask first, in modes 1–3 (user agreed):** deleting a feature, changing the
product goal, anything touching payments / auth / secrets, database migrations, force-push.

**Cap (user agreed):** at most 3 items per batch. Mode 2 runs one batch; modes 3–4 loop.

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
4. `PRODUCT.md` feature map and roadmap are updated in one end-of-session state PR (changed after review: per-item state edits conflict).

**End-of-session verification (user decided):** the final report lists every item done,
with PR links, test results, and the decision-log entry, so the user can verify the
session.

## The flow (one session)

1. **Ask the autonomy mode.**
2. **Load state** — read `PRODUCT.md` (and roadmap / decision log) if present.
3. **Understand** — read README, docs, manifests, code structure, git history.
   - Infer the **goal**: what the product is for and who it serves. On first run (no
     `PRODUCT.md`) show the inferred goal and ask the user to confirm or correct it (complete auto: use
     the inferred goal, mark it "unconfirmed" in `PRODUCT.md`).
   - **Where we are:** built / half-built / broken / missing, per feature.
   - **Feature map:** each feature, what it depends on, what depends on it, and how it
     contributes to the goal. Flag features that contribute little or nothing
     (dead / orphan code).
4. **Test** — run `test-report` on the features that matter most to the goal.
5. **Decide** — panel discussion (below) ranks issues and improvements and picks the
   top items (max 3 fixes).
6. **Act** (modes 2–4) — fix each item; re-run `test-report` to prove it;
   mode 2 opens a PR, modes 3–4 merge when green and loop.
7. **Update state and report back** — update `PRODUCT.md`, roadmap, decision log; tell
   the user what was found, decided, done, and what's next.

## The panel (3-6-9)

Panel size by decision weight (user agreed):

| Size | Used for |
|------|----------|
| **3** | Small calls — a bug fix, which failing test to address first |
| **6** | Medium — adding a feature, a refactor |
| **9** | Direction — cutting a feature, changing the goal |

Each panel member takes a distinct **viewpoint** (my call), drawn in this order so a
3-panel always has the core tension:

1. **User advocate** — what users actually feel and need
2. **Engineer** — feasibility, cost, maintainability
3. **Skeptic** — argues against the leading option, hunts for what's being missed
4. Quality / reliability
5. Business / growth
6. Security & risk
7. Simplicity (what can we *not* do)
8. Long-term architecture
9. Newcomer (does this make sense to a first-time user / dev)

**Discussion protocol (my call):**

- **Round 1** — every member, in parallel, gets the same brief (goal, feature map,
  test-report results, the candidate items) and returns a position: ranked picks, the
  reason, and what would change their mind.
- **Round 2** — every member sees all Round 1 positions and may revise, rebut, or hold.
- **Conclusion** — the decision goes to the option with a majority after Round 2. No
  majority → one more round limited to the top two options; still tied → the skill
  presents both to the user (complete auto: takes the option the skeptic objected to least).
- Any member can raise a **veto flag** on an "always ask first" item; a flag forces a
  user question in modes 1–3; in complete auto it's logged and highlighted in the end report.
- The decision log records: question, panel size, final pick, vote count, the winning
  argument, and the strongest dissent.

Members are spawned with the Agent tool. The `teammates` skill's coordination substrate
is not required (this is a debate, not a work split); the builder may reuse its
`.teammates/` state pattern if useful.

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
  working tree but not committed; the user is told where they are. In modes 2–4 state
  updates go into one end-of-session state PR (changed after review).

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
