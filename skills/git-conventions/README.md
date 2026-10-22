# git-conventions

Make the commits, branches and pull requests Claude creates follow your rules, and hide Claude's name from them if you want.

## What this does

- **One short interview** writes `.claude/git-conventions.md` (for the repo) or `~/.claude/git-conventions.md` (for you everywhere). It proposes what your recent commits already do.
- **Commit messages** follow your pattern: Conventional Commits, a custom template, required issue keys, subject length.
- **Branch names** follow your pattern, e.g. `feat/PROJ-123-login-form`.
- **Pull requests** get your title pattern and body template.
- **Protected branches** (`main`, `release/*`, …): Claude never commits or pushes to them directly and never force-pushes.
- **Hide Claude's name**: sets Claude Code's native `attribution` setting to `{"commit": "", "pr": ""}`, which removes the Co-Authored-By trailer and the "Generated with Claude Code" PR line.

## Safe by design

- Every settings change (attribution, permission deny rules, a pointer line in `CLAUDE.md`) is shown first and written only after you say yes.
- Attribution uses empty strings, not `false`: Claude Code builds older than 2.1.281 reject `false` and skip the whole settings file.
- It never rewrites history or amends pushed commits to remove names. The rules apply from now on.

## What's guaranteed

Attribution and permission deny rules are enforced by Claude Code on every commit. Message and branch patterns are followed whenever the conventions file is read; adding the suggested line to your project `CLAUDE.md` makes that every session.

## Details

See [SKILL.md](SKILL.md) for the setup questions, rules and the file template.
