# claude-skills

A collection of custom skills for [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview). Each skill works on its own, and they compose with one another (see [How the skills work together](#how-the-skills-work-together)).

**Version:** 1.4.0 (all plugins)

## What are skills?

Skills are Markdown files that teach Claude how to handle specific tasks — a multi-agent protocol, a document format, a repeatable workflow. Claude reads the relevant skill at the start of a task and follows its instructions. Think of them as reusable playbooks you install once and get forever.

## Skills in this repo

| Skill | Version | Works in | Description |
|-------|---------|----------|-------------|
| [teammates](skills/teammates/SKILL.md) | 1.4.0 | Claude Code | Run any task as a flat team of Claude Code subagents — no orchestrator, no hierarchy. Agents share a JSON manifest, claim work, message each other, and merge outputs. |
| [codebase-guardian](skills/codebase-guardian/SKILL.md) | 1.4.0 | Claude Code | A disciplined four-phase loop for editing existing codebases safely — validate against the real toolchain, match or deliberately change the existing pattern, trace the ripple, and record learnings to MEMORY.md. Covers TypeScript/Node, Python/Django, Flutter/Dart, and Rust/Tauri. |
| [memory](skills/memory/SKILL.md) | 1.4.0 | Claude Code | Durable, hierarchical memory files so context survives across sessions — bootstrap, read, and update `MEMORY.md` at the repo root and per module, plus user-level `USER.md`. The persistence layer `codebase-guardian` builds on. |
| [agents-dox](skills/agents-dox/SKILL.md) | 1.4.0 | Claude Code | The DOX framework — a hierarchy of `AGENTS.md` files, each a binding work contract for its subtree. Read the root-to-nearest chain before editing; run a DOX pass to update the owning `AGENTS.md` and affected parents/children after. Bootstraps the tree if a repo has none. |
| [lsp](skills/lsp/SKILL.md) | 1.4.0 | Claude Code | Semantic code navigation via real language servers — definition, references, hover, symbols, diagnostics, and safe project-wide rename for TypeScript/Node, Python, Dart/Flutter, and Rust. Ships a stdlib-only Python LSP client; falls back to grep when no server is installed. |
| [schema-aware-db](skills/schema-aware-db/SKILL.md) | 1.4.0 | Claude Code | Stop guessing database schemas. A four-phase discipline for backend data code (SQL and NoSQL) — introspect the real schema, map every usage across the codebase, write the change to industry standard, then trace the ripple so no query, migration, serializer, or test goes stale. |
| [ponytail](skills/ponytail/SKILL.md) | 1.4.0 | Claude Code | Wrap up a work session so nothing is left dangling — sweep every loose strand (uncommitted or unpushed work, unlabeled stashes, session debris, promises recorded nowhere), tie each one off, and leave a single "session tail" report the next session can pick up without archaeology. |
| [decision-maker](skills/decision-maker/SKILL.md) | 1.4.0 | Claude Code | Fast, cheap, calibrated decisions via TypeSafe's Jev System One model — typed yes/no, choice, and score answers with confidence, batched in one call, so narrow judgment calls (route, classify, triage, rank, verify) don't burn LLM reasoning. Add any provider and edit its base URL, model, and API key; ships decision recipes for every other skill. Opt-in guard hooks check every edit and command against your `CLAUDE.md`/`AGENTS.md` rules and your request, answer Claude's questions when confident (asking you only when not), and compare the diff with the request before Claude finishes. Falls back to Claude's own judgment when unconfigured. |

## How the skills work together

Each skill is **self-contained** — install any one on its own and it works with no dependency on the others. They're also designed to **compose**:

- **codebase-guardian + memory** — guardian reads `MEMORY.md` before editing and writes learnings back after, so conventions and ripple traps accumulate across sessions. Without `memory` installed, guardian still maintains `MEMORY.md` files by hand; with it, that lifecycle is automatic.
- **teammates + memory** — peers can read the shared `MEMORY.md` for project context before claiming work, and the merge step can fold new learnings back in.
- **teammates + codebase-guardian** — when a peer team is editing real code, each peer follows the guardian loop (validate with the toolchain, match the pattern, trace the ripple) for its own work item, so parallelism doesn't cost safety.
- **agents-dox + everything** — in a repo that uses the DOX `AGENTS.md` hierarchy, the contract chain governs the others: guardian reads the chain during Orient and folds the DOX pass into its closeout, and each teammates peer reads the same chain before claiming work. `agents-dox` (instructions/contracts in `AGENTS.md`) and `memory` (durable facts in `MEMORY.md`) are complementary, not competing.
- **lsp + codebase-guardian** — guardian's Orient phase can use lsp for impact analysis (`references` before deciding scope), and lsp's rename flow uses guardian's verification loop after applying edits. Both cover the same four stacks.
- **lsp + memory** — per-project server quirks (monorepo roots, retry windows, venv config) accumulate in `MEMORY.md`, so the next session doesn't rediscover them.
- **schema-aware-db + lsp** — schema-aware-db's Phase 2 (map every usage across the codebase) uses lsp `references` on the ORM model/class to find call sites precisely, instead of grepping for a table name and drowning in false positives.
- **schema-aware-db + codebase-guardian** — both run an introspect → map → change → trace-the-ripple loop; guardian governs the general edit, schema-aware-db specializes it for the data layer (real schema, migrations, serializers, tests).
- **schema-aware-db + memory** — confirmed schema facts and access patterns (DynamoDB keys/GSIs, reconciled migration state) accumulate in `MEMORY.md`, so the next session starts from ground truth.
- **ponytail + memory** — durable facts from the session tail (follow-ups, watch-outs, half-applied state) fold into `MEMORY.md`, so the handoff survives beyond the chat.
- **ponytail + teammates** — after a peer team's outputs merge, ponytail is the natural final step: one sweep over the combined result, one tail for the whole run.
- **ponytail + codebase-guardian / agents-dox** — guardian's closeout and the DOX pass are per-*change*; ponytail is per-*session*. Run them for each edit, then ponytail once at the end to catch what fell between changes.
- **decision-maker + everything** — an optional accelerator for the closed-set judgment calls inside the other skills: ponytail's strand sorting, memory's "is this worth saving", guardian's match-vs-change and ripple size, schema-aware-db's real-usage-vs-grep-noise and migration risk, teammates' claim routing and merge contradictions, agents-dox's pass depth, lsp's symbol disambiguation, and skill routing itself. Every recipe batches its items into one call and is confidence-gated: high confidence → act; otherwise the skill decides exactly as it would without it. Recipes and thresholds live in one file, [`skills/decision-maker/references/use-cases.md`](skills/decision-maker/references/use-cases.md).

None of these are required: a skill never errors or stalls because a companion skill is absent.

## Installation

In Claude Code:

```bash
claude plugin marketplace add DN-OpenSource/claude-skills
claude plugin install decision-maker@claude-skills     # or any plugin name from the table above
```

Restart Claude Code or run `/reload-plugins` to load it. Both manifests pass `claude plugin validate`. See the [official Claude Code docs](https://docs.anthropic.com/en/docs/claude-code) if the install mechanism has changed.

After installing decision-maker you get one notice telling you whether it's active and exactly what it sends where. Run `/decision-maker:jev` at any time for the same summary; see [its README](skills/decision-maker/README.md#what-happens-after-you-install). **Note:** the marketplace installs from GitHub, so a plugin only installs after it has been pushed.

For **decision-maker**, install either this plugin or TypeSafe's own `typesafe@typesafe-ai`, not both. This one includes TypeSafe's design guidance (`references/building.md`) and adds the runtime client, providers, guard hooks and evals; theirs covers design guidance only.

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
    ├── agents-dox/
    │   ├── README.md
    │   └── SKILL.md
    ├── lsp/
    │   ├── README.md
    │   ├── SKILL.md
    │   ├── scripts/      ← stdlib-only LSP client + tests
    │   └── references/   ← per-stack server commands & quirks
    ├── schema-aware-db/
    │   ├── README.md
    │   ├── SKILL.md
    │   └── references/   ← per-engine introspection, standards, ripple recipe
    ├── ponytail/
    │   ├── README.md
    │   └── SKILL.md
    └── decision-maker/
        ├── README.md
        ├── SKILL.md
        ├── hooks/        ← prefetch (default) + opt-in guard hooks (rules, scope, decide-don't-ask, request vs. diff)
        ├── scripts/      ← stdlib-only System One client, guard hook + tests
        └── references/   ← API facts, provider presets, per-skill decision recipes
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
