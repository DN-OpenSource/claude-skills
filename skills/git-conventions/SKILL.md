---
name: git-conventions
description: Use when committing, naming a branch, or opening a PR, or when the user wants to set commit/branch/PR rules or hide Claude's name from commits. Follows the user's git-conventions file; sets attribution via the native setting, asked first.
---

# Git Conventions

Make every commit, branch and pull request Claude creates follow **the user's** rules, and
let the user hide Claude's name, using Claude Code's own settings where they exist.

## Progress and panel (shown to the user when the skill-checklist mod is installed)

If a `skill_progress` tool is available, call it as you start: `skill: "git-conventions"`, `steps: ["Read rules", "Apply"]`. Then call it with `step` as each one begins, adding a short `note` when you have a result (a test count, a file written), and with `finished: true` at the end. Report only the steps this run uses. If the tool isn't available, ignore this section.

**Panel:** if a `skill_panel` tool is available, send this skill's panel and send it again whenever it changes (it replaces the last one). Buttons the person presses arrive as their next message; treat it as their answer. GitHub accounts and this repo's git identity live in the mod's own accounts tab: when the person wants to change account or identity, tell them to run `/git-accounts`. During setup, send `Rules` with a row per answered question (mark done) and a `fill` button `Change` (text: `Change my <field> rule to `). Before a commit, send `Commit` with the message as a row and the branch as its note, buttons `Commit` (send `Commit it`) and `Edit` (fill `Use this commit message: <message>`).

## Where the rules live

1. `.claude/git-conventions.md` in the repo (project rules, committed with the repo)
2. `~/.claude/git-conventions.md` (the user's personal default)

The first one found wins. Read it **before** any `git commit`, `git checkout -b` /
`git switch -c`, `git push` or `gh pr create`. No file → work as usual, and if the user
asked for rules, run the setup below.

## Setup (first use, or "set up my git rules")

Ask these, one at a time, offering the detected default in brackets. Detect from `git log -20`
and `git branch -a`: if recent commits already follow a pattern, propose it.

1. **Commit message** — e.g. Conventional Commits `type(scope): summary`, or a custom template;
   issue key required (`PROJ-123`)? Max subject length? Body rules?
2. **Branch name** — e.g. `feature/<issue>-<slug>`, `fix/<slug>`; allowed prefixes.
3. **Attribution** — keep or hide "Co-Authored-By: Claude …" in commits and
   "Generated with Claude Code" in PRs.
4. **Pull request** — title pattern, body template, draft by default?
5. **Protected branches** — e.g. `main`, `release/*`: never commit or push to them directly.
6. **Other** — sign-off (`-s`), GPG signing, merge style, anything else the user names.

Write the answers to the file (project or personal, the user picks) using the template below,
show it, and tell the user they can edit it any time.

## Applying the rules

- **Commit:** build the message from the pattern. If the change doesn't fit a required field
  (no issue key known), ask once instead of inventing one.
- **Branch:** name it from the pattern before the first commit.
- **PR:** title and body from the template.
- **Protected branches:** never commit to them directly, never push to them, never force-push
  anything. Branch off instead.
- **Never** rewrite history, amend pushed commits or force-push to remove names from old
  commits. The rules apply from now on.

## Making it stick (asked first, each one)

A skill only loads when a request matches it, so in the middle of other work Claude may
commit without reading this. The native layers below apply on every commit. **Ask before each
change and show the exact edit.** Use the `update-config` skill if it's installed.

- **Hide Claude's name** — in the settings file the user picks (`~/.claude/settings.json` for
  everywhere, `.claude/settings.json` for this repo):
  `"attribution": {"commit": "", "pr": ""}`.
  Use empty strings, not `false`: builds older than Claude Code 2.1.281 reject `false` and then
  skip the whole settings file, including its permission rules. (`includeCoAuthoredBy` is the
  deprecated older key; leave it alone.)
- **Protected branches, hard stop** — permission deny rules such as `Bash(git push --force*)`,
  `Bash(git push origin main*)`, `Bash(git commit*)` scoped to the protected branch's checkout
  only if the user wants that strictness.
- **Rules in every session** — one line in the project `CLAUDE.md`:
  `Commits, branches and PRs follow .claude/git-conventions.md.`

Be honest about what is guaranteed: attribution and deny rules are enforced by Claude Code;
message and branch patterns are followed whenever the file is read.

## Template

```markdown
# Git conventions

## Commit message
Pattern: `type(scope): summary`  (types: feat, fix, docs, refactor, test, chore)
Issue key: required, in scope — `feat(PROJ-123): …`
Subject: ≤ 72 chars, imperative. Body: why, wrapped at 72.

## Branch name
Pattern: `<type>/<issue>-<short-slug>` — e.g. `feat/PROJ-123-login-form`

## Attribution
Hide Claude in commits and PRs: yes   (applied via settings `attribution`)

## Pull request
Title: same as the commit pattern. Body: ## Why / ## What / ## Test plan. Draft: no.

## Protected branches
main, release/*

## Other
Sign-off: no. Merge style: squash.
```
