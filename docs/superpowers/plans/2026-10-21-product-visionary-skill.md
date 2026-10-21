# Product Visionary Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `skills/product-visionary/`: a skill that infers a product's goal, state, and feature map, finds issues via `test-report`, decides through a 3/6/9-agent panel, and acts according to a session-start autonomy mode (report only / fix on a branch / full auto / complete auto).

**Architecture:** Markdown skill. `SKILL.md` holds the session flow and modes; `references/panel.md` holds the debate protocol and member prompts; `references/templates.md` holds the state-file and end-report templates. Packaging mirrors `skills/test-report/`. Verified by the repo's token-budget script, JSON parsing, and one pressure run by a subagent on a sample project.

**Tech Stack:** Markdown, JSON manifests, Python 3 (existing `scripts/check_token_budget.py`).

**Spec:** `docs/superpowers/specs/2026-10-21-product-visionary-skill-design.md`

## Global Constraints

- Skill name `product-visionary`; version `1.4.0`; license `Apache-2.0`; author `dhirajnikam` / `dhirajnikam78@gmail.com`.
- Frontmatter `description:` is one line, ≤ 260 tokens (≈1040 chars); aim ≤ 70 tokens. Raise `TOTAL` in `scripts/check_token_budget.py` to `1300` and its comment to `(10 skills)`.
- Modes, verbatim names: **1. Report only**, **2. Fix on a branch**, **3. Full auto**, **4. Complete auto**. Asked every session; never remembered.
- Always-ask list (modes 1–3): deleting a feature, changing the product goal, anything touching payments / auth / secrets, database migrations, force-push.
- Mode 4 floor (never skipped): every change via branch + PR; never rewrite/force-push the default branch; never write secret values into code, logs, or reports.
- Batch cap 3 items; mode 3–4 loop stops on: nothing worth doing, an unprovable item, a veto flag (modes 1–3 only), or 5 batches.
- Panel sizes: 3 small, 6 medium (feature/refactor), 9 direction (cut feature / change goal). Viewpoint order: User advocate, Engineer, Skeptic, Quality/reliability, Business/growth, Security & risk, Simplicity, Long-term architecture, Newcomer.
- State files in the analysed project: `PRODUCT.md`, `docs/product/roadmap.md`, `docs/product/decisions.md`, `test-reports/`.
- Merge gate: new `test-report` tests pass and existing suite (+ build/lint if configured) has no new failures vs the run's baseline. Merge = `gh pr merge --squash`, one PR per item; stop at PR if protected/needs review.
- Must work standalone: if `test-report` isn't installed, follow the inline 2-positive + 1-negative rules.

## Review Focus

- **Dirty working tree at session start** → modes 2–3 ask; mode 4 does its work in a fresh `git worktree` so the user's uncommitted changes are never touched. (Task 1)
- **Not a git repo, no `gh`, or no remote** → modes 2–4 still branch locally if git exists, skip PR/merge, say so in the end report; no git at all → falls back to mode 1. (Task 1)
- **Existing suite already red at baseline** → baseline records the failures; only *new* failures block; end report lists the pre-existing ones. (Task 1)
- **Monorepo / several products in one repo** → goal and feature map are per product; `PRODUCT.md` gets one section per product. (Task 3)
- **Session interrupted mid-batch** → decision log entry is written *before* acting, marked `in progress`; next session reads it and resumes or closes it. (Task 2, Task 3)

---

### Task 1: SKILL.md — modes and session flow

**Files:**
- Create: `skills/product-visionary/SKILL.md`

**Interfaces:**
- Produces: section headings later tasks link to — `## Session start`, `## The flow`, `## Acting and merging`, `## Ending the session`; links to `references/panel.md` and `references/templates.md`.

- [ ] **Step 1: Write the check** — save as a shell one-liner in the task notes:

```bash
f=skills/product-visionary/SKILL.md
for s in "name: product-visionary" "Report only" "Fix on a branch" "Full auto" "Complete auto" \
  "always ask" "5 batches" "baseline" "git worktree" "gh pr merge --squash" "references/panel.md" \
  "references/templates.md" "test-report"; do grep -qi -- "$s" $f || echo "MISSING: $s"; done
```

- [ ] **Step 2: Run it** — Expected: `MISSING:` for every string (file absent → grep errors count as failures).
- [ ] **Step 3: Write `SKILL.md`** covering, in order: frontmatter; Session start (menu verbatim, always-ask list, mode 4 floor + "Claude Code permission settings still apply"); The flow (spec steps 1–7, first-run goal confirmation / "unconfirmed" in mode 4); Testing (invoke `test-report`, else inline rules); Deciding (one-paragraph summary, link to `references/panel.md`); What counts as an item + how features are built (spec's 4 steps); Acting and merging (merge gate, baseline, one PR per item, loop + stop conditions, and the Review Focus rules for dirty tree / no git / no gh / red baseline); Ending the session (end report, link to templates); mode 1 writes tests/state files uncommitted and says where; modes 2–4 put state updates in each PR; mode 2 = one batch. Keep under ~150 lines.
- [ ] **Step 4: Run the check** — Expected: no output.
- [ ] **Step 5: Commit** — `git add skills/product-visionary/SKILL.md && git commit -m "product-visionary: SKILL.md flow and modes"`

### Task 2: references/panel.md — the 3-6-9 debate

**Files:**
- Create: `skills/product-visionary/references/panel.md`

**Interfaces:**
- Consumes: Task 1's "Deciding" link.
- Produces: the **brief** format (goal, feature map, test results, candidates) and the **position** format members return: `picks: [ranked ids]`, `reason`, `would change my mind if`, `veto: none | <always-ask item>`.

- [ ] **Step 1: Write the check**

```bash
f=skills/product-visionary/references/panel.md
for s in "User advocate" "Engineer" "Skeptic" "Newcomer" "Round 1" "Round 2" "majority" \
  "top two" "skeptic objected to least" "veto" "in progress" "strongest dissent" "Agent tool"; do
  grep -qi -- "$s" $f || echo "MISSING: $s"; done
```

- [ ] **Step 2: Run it** — Expected: all `MISSING:`.
- [ ] **Step 3: Write `panel.md`** — size table; 9 viewpoints with a one-line stance each; spawning (Agent tool, all members of a round in one message so they run in parallel); the brief and position formats; Rounds 1–2, majority rule, tie round on top two, tie-break (ask user in modes 1–3; mode 4 takes the option the skeptic objected to least); veto handling per mode; decision-log entry written as `in progress` before acting, updated to `done`/`failed` after; one prompt template per round.
- [ ] **Step 4: Run the check** — Expected: no output.
- [ ] **Step 5: Commit** — `git add skills/product-visionary/references/panel.md && git commit -m "product-visionary: panel protocol"`

### Task 3: references/templates.md — state files and end report

**Files:**
- Create: `skills/product-visionary/references/templates.md`

**Interfaces:**
- Consumes: decision-log fields from Task 2 (question, panel size, pick, votes, winning argument, strongest dissent, status).

- [ ] **Step 1: Write the check**

```bash
f=skills/product-visionary/references/templates.md
for s in "PRODUCT.md" "unconfirmed" "Feature map" "contributes" "orphan" "roadmap.md" \
  "Proposed features" "decisions.md" "strongest dissent" "in progress" "End-of-session report" \
  "pre-existing failures" "one section per product"; do grep -qi -- "$s" $f || echo "MISSING: $s"; done
```

- [ ] **Step 2: Run it** — Expected: all `MISSING:`.
- [ ] **Step 3: Write `templates.md`** — `PRODUCT.md` (goal + confirmed/unconfirmed, where we are, feature map table: feature · status · depends on · used by · how it contributes to the goal · flag dead/orphan; monorepo note: one section per product); `roadmap.md` (Fix / Build / Cut / Proposed features with size, goal served, panel vote, strongest argument against; rejected items with the user's reason); `decisions.md` entry; End-of-session report (mode, batches run, each item with PR link + test result + decision link, pre-existing failures, what was logged instead of asked in mode 4, what's next).
- [ ] **Step 4: Run the check** — Expected: no output.
- [ ] **Step 5: Commit** — `git add skills/product-visionary/references/templates.md && git commit -m "product-visionary: state and report templates"`

### Task 4: Packaging and repo integration

**Files:**
- Create: `skills/product-visionary/README.md`, `skills/product-visionary/.claude-plugin/plugin.json`
- Modify: `README.md` (skill table row after `test-report`; one "How the skills work together" bullet: product-visionary + test-report / teammates / codebase-guardian), `.claude-plugin/marketplace.json` (append plugin, `category: "workflow"`, update top description), `.claude-plugin/plugin.json` (description + keywords `product`, `roadmap`), `scripts/check_token_budget.py` (`TOTAL = 1300`, comment `(10 skills)`).

- [ ] **Step 1: Run the checks before changes**

```bash
python scripts/check_token_budget.py
python -c "import json,sys;[json.load(open(f,encoding='utf-8')) for f in sys.argv[1:]]" .claude-plugin/plugin.json .claude-plugin/marketplace.json skills/product-visionary/.claude-plugin/plugin.json
```
Expected: budget prints `product-visionary` row (SKILL.md exists from Task 1) and may exceed 1200; JSON fails on the missing plugin file.

- [ ] **Step 2: Make the changes listed above**, copying `skills/test-report/.claude-plugin/plugin.json` and `README.md` as the shape. README sections: What this does, The four modes, Works with, What it won't do, Details.
- [ ] **Step 3: Run the checks** — Expected: `OK: within token budget` (total ≤ 1300) and no JSON error.
- [ ] **Step 4: Commit** — `git add -A && git commit -m "product-visionary: packaging and repo integration"`

### Task 5: Pressure run

**Files:**
- Test: a throwaway sample project in the scratchpad (not committed)

- [ ] **Step 1: Build the sample** — a tiny Python Flask or Node Express app with a README stating a goal, 3 endpoints, one with an obvious bug (e.g. returns 500 on empty input), one orphan module, and an existing test suite with one pre-existing failure; `git init` + commit.
- [ ] **Step 2: Dispatch a fresh subagent** told to follow `skills/product-visionary/SKILL.md` in **mode 1 (Report only)** on the sample, with `skills/test-report/SKILL.md` available.
- [ ] **Step 3: Check the output** — Expected: `PRODUCT.md` with goal, feature map flagging the orphan module; a `test-reports/` file showing the 500 bug; decision log with a 3-panel entry incl. strongest dissent; pre-existing failure listed as pre-existing; **no commits** and no app code changed (`git log` and `git diff -- <app files>` unchanged).
- [ ] **Step 4: Fix any SKILL.md gap the run exposed**, re-run Step 2 if a fix was needed, commit: `git commit -am "product-visionary: fixes from pressure run"`
