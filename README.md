# claude-skills

A collection of custom skills for [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) and Claude.ai.

## What are skills?

Skills are Markdown files that teach Claude how to handle specific tasks — a multi-agent protocol, a document format, a repeatable workflow. Claude reads the relevant skill at the start of a task and follows its instructions. Think of them as reusable playbooks you install once and get forever.

## Skills in this repo

| Skill | Works in | Description |
|-------|----------|-------------|
| [peer-agents](skills/peer-agents/SKILL.md) | Claude Code · Claude.ai | Run any task as a flat team of peer agents — no orchestrator, no hierarchy. Agents claim their own work, message each other directly, and merge their outputs. |

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
    └── peer-agents/
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
