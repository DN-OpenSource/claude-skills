# claude-skills

A collection of custom skills for [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview). Each skill works on its own, and they compose with one another (see [How the skills work together](#how-the-skills-work-together)).

**Version:** 1.2.0 (all plugins)

## What are skills?

Skills are Markdown files that teach Claude how to handle specific tasks — a multi-agent protocol, a document format, a repeatable workflow. Claude reads the relevant skill at the start of a task and follows its instructions. Think of them as reusable playbooks you install once and get forever.

## Skills in this repo

| Skill | Version | Works in | Description |
|-------|---------|----------|-------------|
| [teammates](skills/teammates/SKILL.md) | 1.2.0 | Claude Code | Run any task as a flat team of Claude Code subagents — no orchestrator, no hierarchy. Agents share a JSON manifest, claim work, message each other, and merge outputs. |
| [codebase-guardian](skills/codebase-guardian/SKILL.md) | 1.2.0 | Claude Code | A disciplined four-phase loop for editing existing codebases safely — validate against the real toolchain, match or deliberately change the existing pattern, trace the ripple, and record learnings to MEMORY.md. Covers TypeScript/Node, Python/Django, Flutter/Dart, and Rust/Tauri. |
| [memory](skills/memory/SKILL.md) | 1.2.0 | Claude Code | Durable, hierarchical memory files so context survives across sessions — bootstrap, read, and update `MEMORY.md` at the repo root and per module, plus user-level `USER.md`. The persistence layer `codebase-guardian` builds on. |
| [agents-dox](skills/agents-dox/SKILL.md) | 1.2.0 | Claude Code | The DOX framework — a hierarchy of `AGENTS.md` files, each a binding work contract for its subtree. Read the root-to-nearest chain before editing; run a DOX pass to update the owning `AGENTS.md` and affected parents/children after. Bootstraps the tree if a repo has none. |

## How the skills work together

Each skill is **self-contained** — install any one on its own and it works with no dependency on the others. They're also designed to **compose**:

- **codebase-guardian + memory** — guardian reads `MEMORY.md` before editing and writes learnings back after, so conventions and ripple traps accumulate across sessions. Without `memory` installed, guardian still maintains `MEMORY.md` files by hand; with it, that lifecycle is automatic.
- **teammates + memory** — peers can read the shared `MEMORY.md` for project context before claiming work, and the merge step can fold new learnings back in.
- **teammates + codebase-guardian** — when a peer team is editing real code, each peer follows the guardian loop (validate with the toolchain, match the pattern, trace the ripple) for its own work item, so parallelism doesn't cost safety.
- **agents-dox + everything** — in a repo that uses the DOX `AGENTS.md` hierarchy, the contract chain governs the others: guardian reads the chain during Orient and folds the DOX pass into its closeout, and each teammates peer reads the same chain before claiming work. `agents-dox` (instructions/contracts in `AGENTS.md`) and `memory` (durable facts in `MEMORY.md`) are complementary, not competing.

None of these are required: a skill never errors or stalls because a companion skill is absent.

## Installation

> Check the [official Claude Code docs](https://docs.anthropic.com/en/docs/claude-code) for the most current installation steps — the install mechanism may have been updated since this README was written.

## Adding a new skill

1. Create a new directory under `skills/`:
   ```
   skills/your-skill-name/
   └── SKILL.md
   ```

2. `SKILL.md` must start with YAML frontmatter:
   ```markdown
   ---
   name: your-skill-name
   description: When to trigger this skill and what it does. Be specific — this is what Claude reads to decide whether to use the skill.
   ---

   # Your Skill Name
   ...
   ```

3. Open a PR with a one-line summary of what the skill does and when to use it.

## Structure

```
claude-skills/
├── README.md
└── skills/
    ├── teammates/
    │   ├── README.md
    │   └── SKILL.md
    ├── codebase-guardian/
    │   ├── README.md
    │   ├── SKILL.md
    │   └── references/   ← per-stack commands & ripple traps
    ├── memory/
    │   ├── README.md
    │   └── SKILL.md
    └── agents-dox/
        ├── README.md
        └── SKILL.md
```

Each skill lives in its own subdirectory. If the skill needs supporting files (scripts, reference docs, templates), they go in subdirectories alongside `SKILL.md`:

```
skills/your-skill/
├── SKILL.md
├── scripts/       ← executable helpers
├── references/    ← docs loaded on demand
└── assets/        ← templates, fonts, etc.
```

## License

Apache-2.0
