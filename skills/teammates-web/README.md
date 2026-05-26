# teammates-web

A flat peer-agent protocol for Claude.ai React artifacts. When the user asks for an artifact that should run a multi-part task across several agents, this skill produces a round-based artifact where peers share state, claim work, message each other, and merge outputs — without anyone playing orchestrator.

## What this does

Claude.ai artifacts can't spawn long-running subagents, so this variant adapts the [teammates-cc](../teammates-cc/SKILL.md) protocol to a round-based shape that fits the substrate:

- The artifact holds shared state (roster, work items, messages, outputs) in React.
- Each **round**, the artifact dispatches one parallel API call per active peer and asks each for exactly one structured action (claim / message / work / done / noop).
- The artifact applies the returned actions to state, arbitrates same-round claim collisions, and dispatches the next round.
- When all peers report `done`, a final merge call synthesizes the result.

The artifact is the substrate, not an orchestrator. Its only judgment is breaking same-round claim ties.

## When it fires

The skill activates when Claude.ai is building an artifact whose task benefits from parallel agent work and visible coordination — research, generate-and-compare, multi-lens review, open-ended brainstorming.

Don't use it for sequential tasks, single-API-call answers, or anything that would be confusing to render as a multi-agent UI.

## Example use cases

- A research artifact that splits a question across three subtopics and shows each agent's findings live (self-claimed mode).
- A "PR review playground" where four agents review the same diff for security / perf / readability / tests (pre-decomposable mode).
- A brainstorming artifact where peers negotiate sub-questions before working them (emergent mode).
- Side-by-side variant generation: A/B/C agents each produce a design, then a merge round synthesizes a comparison.

## Inspecting a run

The artifact UI itself is how you inspect a run:

- **Roster** panel — live status per peer.
- **Work items** table — claims and completions.
- **Messages** transcript — every cross-peer message, grouped by round.
- **Outputs** previews — per-peer markdown.
- **Final** — the merged synthesis once the merge round completes.

A round counter + "next round" button (behind a "Show controls" toggle) is useful for step-debugging.

## Protocol details

See [SKILL.md](SKILL.md) for the full protocol: state schema, action schema, the round algorithm, conflict arbitration, the three coordination modes (pre-decomposable, self-claimed, emergent), merge, and the rendering recommendations.

## Related

- [`teammates-cc`](../teammates-cc/SKILL.md) — the Claude Code variant. Same coordination model, but peers are long-lived subagents and the substrate is the filesystem instead of React state.
