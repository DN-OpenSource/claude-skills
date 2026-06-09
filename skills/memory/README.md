# memory

Durable, hierarchical memory files so context survives across sessions — for the codebase you're working in and for the user you're working with.

## What this does

The skill manages two kinds of long-lived context through one lifecycle — **bootstrap** (create from scratch), **read** (load before related work), **update** (keep in sync):

- **Codebase memory** — architecture, conventions, what each module does, and gotchas. Lives in a hierarchy: `MEMORY.md` at the repo root plus a `MEMORY.md` in each significant subfolder.
- **User memory** — the person's role, preferences, and ongoing projects. Lives in one file: `~/.memory/USER.md`.

When the skill triggers in a repo that has no root `MEMORY.md`, it **auto-bootstraps** the structure before continuing with the original task (unless the workspace clearly isn't a repo, is read-only, or the user opted out).

## When it fires

Whenever the user mentions memory, context files, `MEMORY.md`, `AGENTS.md`, project context, or codebase documentation; when starting work in an unfamiliar repo; when the user asks to remember or forget something durable; and after non-trivial changes that shift a module's purpose, public surface, or conventions.

It errs toward triggering — under-triggering (losing context) is the worse failure mode.

## Relationship to codebase-guardian

[`codebase-guardian`](../codebase-guardian/SKILL.md) runs **on top of** this skill: it reads `MEMORY.md` at the start of every run and writes learnings back at the end, which is how it "improves over time." Installing `memory` makes that dependency self-contained.

## Details

See [SKILL.md](SKILL.md) for the full workflows (bootstrap / read / update for both codebase and user memory), the file-location and "significant folder" rules, the root/folder/user templates, and the failure modes to avoid.
