# teammates-cc

A flat peer-agent protocol for Claude Code. When a task can be split into parallel parts, this skill runs a small team of subagents that share a JSON manifest, claim their own work, message each other, and merge outputs — without anyone playing orchestrator.

## What this does

Instead of one Claude handling a multi-part task sequentially (or one Claude orchestrating subagents top-down), teammates-cc sets up a flat team where:

- Every agent — including the one that spawned the team — follows the same loop.
- Work items live in `.teammates/state.json` and peers claim them with a re-read-after-write pattern.
- Messages are an append-only log; outputs go in `.teammates/outputs/<work-id>.md`.
- A merge step runs once all roster entries are `done`.

## When it fires

The skill activates when the current task benefits from parallel work across multiple subagents and you'd rather have peers negotiate than nominate a coordinator.

Don't use it for sequential tasks, or anything small enough for one agent.

## Example use cases

- Summarize 12 GitHub issues in parallel (self-claimed mode).
- Review a PR across four distinct lenses — security, perf, readability, tests (pre-decomposable mode).
- Generate variants A/B/C of a design and compare (pre-decomposable).
- Open-ended research where peers negotiate sub-questions as they go (emergent mode).

## Inspecting a run

Everything a run produces lives under `.teammates/` at the project root (gitignored):

- `state.json` — the shared manifest (roster, work items, messages).
- `outputs/<id>.md` — one file per completed work item.
- `FINAL.md` — the merged result.

## Protocol details

See [SKILL.md](SKILL.md) for the full protocol: substrate schema, peer loop, spawning, the three coordination modes (pre-decomposable, self-claimed, emergent), merge, failure detection, and the safety contract for editing `state.json`.

## Related

- `teammates-web` *(planned)* — same protocol adapted for a Claude.ai React artifact + API substrate.
