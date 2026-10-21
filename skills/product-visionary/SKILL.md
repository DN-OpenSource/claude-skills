---
name: product-visionary
description: Use when asked what a product's goal is, where it stands, how features connect, or to run/manage/improve a product. Maps goal, state, and features; finds issues via test-report; a 3/6/9-agent panel decides; acts per a session-start autonomy mode.
---

# Product Visionary

Act as the product's visionary manager. Work out **what the product is for**, **where it
stands**, and **how every feature serves that goal**; find real issues by running tests;
let a panel of agents decide what to do; then act — as far as the user allows this session.

## Session start

Ask this first, every session. Never reuse an earlier session's answer.

> How much should I do this session?
> 1. **Report only** — goal, state, feature map, test run, ranked issues. No code changes.
> 2. **Fix on a branch** — fix the top items on branches and open PRs. You merge.
> 3. **Full auto** — fix, prove, merge, and keep going. I still ask before anything on the always-ask list.
> 4. **Complete auto** — like 3, but I ask nothing. This choice is the only permission.

**Always ask first (modes 1–3):** deleting a feature, changing the product goal, anything
touching payments / auth / secrets, database migrations, force-push. "Database migration"
means any schema change, including creating new tables or a new datastore.

**Mode 4 floor — kept even in complete auto** (recoverability, not permission):
every change goes through a branch + PR so any merge can be reverted; never rewrite or
force-push the default branch; never write secret values into code, logs, or reports.
Claude Code's own permission settings still apply; this skill can't bypass them.

## The flow

1. **Ask the mode** (above).
2. **Load state** — read `PRODUCT.md`, `docs/product/roadmap.md`, `docs/product/decisions.md`
   if present. A decision marked `in progress` was interrupted: check its branch/PR, then
   finish it or mark it `failed`.
3. **Understand** — README, docs, manifests, code structure, `git log`.
   - **Goal:** what it's for and who it serves. First run (no `PRODUCT.md`): show the
     inferred goal and ask the user to confirm or correct it. Mode 4: use it and mark it
     `unconfirmed`.
   - **Where we are:** each feature built / half-built / broken / missing.
   - **Feature map:** each feature, what it depends on, what uses it, how it contributes to
     the goal. Flag dead or orphan features. Several products in one repo → one section
     per product.
4. **Baseline + test** — run the existing suite (and build/lint if configured) and save the
   result, in every mode; then run the key features through `test-report` (below).
5. **Decide** — panel ranks candidates (below).
6. **Act** — modes 2–4 only (see Acting and merging).
7. **Update state and report** — see Ending the session.

Templates for every file: `references/templates.md`.

## Testing

Use the `test-report` skill on the features on the goal's critical path — at most 5, skip
dead/orphan ones (they're already flagged). Name them to `test-report` explicitly. If it isn't
installed, follow its rules inline: per feature, 2 positive tests + 1 negative test in the
project's own framework; run them for real; retry a failure once (passes → flaky);
can't run → blocked with reason; write `test-reports/YYYY-MM-DD-<scope>.md`.
Never install a test framework without asking — not even in mode 4.

## Deciding

Candidates come from failing tests, the feature map (gaps, orphans, weak links to the goal),
and the roadmap. Each batch:

- **One 3-agent panel** ranks all candidates, picks up to 3 items, and labels each pick's
  weight: **small**, **medium** (new screen / endpoint / model, a refactor, or touches more
  than one feature), or **direction** (cut a feature, change the goal). Applies to fixes,
  improvements, and features alike.
- Modes 2–4: each **medium** pick gets its own batch and its own **6-agent** panel on how to
  do it; **direction** gets **9**. Mode 1 runs only the 3-panel — nothing is built, so the
  how-to panels would be wasted.

Protocol, viewpoints, prompts, tie-breaks, vetoes: `references/panel.md`.

## What counts as an item

Fixes for test failures, small improvements, and new features. The session-start choice is
the only approval needed — modes 3–4 build new features without asking per feature.
Mode 2 builds them too but leaves the PR. Mode 1 writes every pick to the roadmap —
fixes under Fix, improvements under Build, new features under Proposed features — with
decision status `proposed`.

New features: the ranking panel proposes it (what, goal served, connected features, weight).
Prove it like a fix: 2+1 tests for the new behavior.

## Acting and merging

**Before the first change:**
- **Baseline** (taken in flow step 4): only *new* failures block; pre-existing ones go in
  the end report.
- **Dirty working tree:** modes 2–3 ask what to do. Mode 4 works in a fresh
  `git worktree` so the user's uncommitted changes are never touched.
- **No git:** fall back to mode 1 and say so. **No `gh` or no remote:** branch locally,
  skip PR/merge, say so in the end report.

**Per item:**
1. Write the decision-log entry as `in progress` (so an interrupted session can resume).
2. New branch off the default branch; make the change; update `PRODUCT.md` and the roadmap
   in the same branch.
3. Prove it: the item's `test-report` tests pass **and** the existing suite shows no new
   failures vs the baseline.
4. Open a PR. Mode 2 stops here. Modes 3–4 merge with `gh pr merge --squash`; if the
   branch is protected or needs review, stop at the PR.
5. Mark the decision `done`, or `failed` with the reason.

An item that can't be proven (red, flaky, blocked) stays an open, unmerged PR.

**Loop (modes 3–4):** after a batch, re-test, re-run the ranking panel, pick the next 3.
Stop when: the panel finds nothing worth doing; an item in the batch couldn't be proven;
a veto flag fires (modes 1–3); or **5 batches** are done. Mode 2 runs one batch.

**Mode 1 writes, doesn't commit:** tests, `test-reports/`, and state files are left in the
working tree; tell the user where they are.

## Ending the session

Write the end-of-session report (`references/templates.md`) and show it to the user: mode,
batches run, every item with its PR link, test result and decision entry, pre-existing
failures, and — in mode 4 — everything that would have been asked but was logged instead.
This is how the user verifies the session. End with what's next on the roadmap.
