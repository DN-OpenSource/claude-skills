# memory

Durable, hierarchical memory files so context survives across sessions — for the codebase you're working in and for the user you're working with.

## Install

```bash
claude plugin marketplace add DN-OpenSource/claude-skills
claude plugin install memory@claude-skills
```

Or in one step from a Claude Code session (2.1.275+): `/plugin install memory --marketplace DN-OpenSource/claude-skills`. Restart Claude Code (or run `/reload-plugins`) to load it. To update later: `claude plugin marketplace update claude-skills`, then `claude plugin update memory@claude-skills`.

## What this does

The skill manages two kinds of long-lived context through one lifecycle — **bootstrap** (create from scratch), **read** (load before related work), **update** (keep in sync):

- **Codebase memory** — architecture, conventions, what each module does, and gotchas. Lives in a hierarchy: `MEMORY.md` at the repo root plus a `MEMORY.md` in each significant subfolder.
- **User memory** — the person's role, preferences, and ongoing projects. Lives in one file: `~/.memory/USER.md`.

When the skill triggers in a repo that has no root `MEMORY.md`, it **auto-bootstraps** the structure before continuing with the original task (unless the workspace clearly isn't a repo, is read-only, or the user opted out).

## When it fires

Whenever the user mentions memory, context files, `MEMORY.md`, project context, or codebase documentation; when starting work in an unfamiliar repo; when the user asks to remember or forget something durable; and after non-trivial changes that shift a module's purpose, public surface, or conventions.

It errs toward triggering — under-triggering (losing context) is the worse failure mode.

**Who keeps personal facts.** Works in Claude Code and as a claude.ai skill. In Claude Code, "remember that I prefer X" goes to Claude Code's own built-in memory, so this skill usually stays quiet for it and `~/.memory/USER.md` is used only when you name it. On hosts without their own memory (claude.ai skills, other agents), the skill keeps those facts in `USER.md`. "Forget X" clears both. Repo `MEMORY.md` files never hold personal facts.

## Scope and companions

This skill works standalone and owns `MEMORY.md` (codebase facts) and `~/.memory/USER.md` (user facts) only. It composes with the rest of the repo:

- [`codebase-guardian`](../codebase-guardian/SKILL.md) reads `MEMORY.md` at the start of every run and writes learnings back at the end — that's how it "improves over time." It works without `memory` (maintaining the files by hand); installing `memory` automates the lifecycle.
- [`agents-dox`](../agents-dox/SKILL.md) owns `AGENTS.md` instruction/contract files. They're complementary — `MEMORY.md` holds *facts*, `AGENTS.md` holds *contracts* — so this skill leaves `AGENTS.md` to agents-dox rather than managing it.

## Details

See [SKILL.md](SKILL.md) for the full workflows (bootstrap / read / update for both codebase and user memory), the file-location and "significant folder" rules, the root/folder/user templates, and the failure modes to avoid.
