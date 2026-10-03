# ponytail

Sessions rarely *end*; they *stop*. What's lost is never the finished work — it's the loose strands: the uncommitted change, the stash with no message, the debug print left behind, the "I'll fix that later" that lives only in the conversation. A ponytail gathers loose strands and ties them into one tail; this skill does that for a work session.

## What this does

A deliberate closing move in three parts, ending with one report:

1. **Sweep** — enumerate every loose strand: working tree and stashes, unpushed commits, debug prints and TODO/FIXME markers introduced this session, failing checks, half-applied renames, promises made in conversation but recorded nowhere, scratch files.
2. **Sort** — give each strand exactly one fate: tie off now, hand off (preserved as a WIP commit or messaged stash), or discard. When the user isn't there to ask, preserve rather than destroy.
3. **Tie off** — coherent commits with real messages (never "wip"), push, clean up only the debris this session created, record everything deferred.

Then leave **the tail**: a single "session tail" report — done & durable, tied but unfinished, follow-ups, discarded, watch out — so the next session starts from one place, not from archaeology.

## When it fires

"Wrap up", "tie up loose ends", "end of day", "before I go", "hand this off", "clean up before we stop" — and unprompted in ephemeral environments where unpushed work evaporates. An empty sweep is a valid result: if nothing is dangling, it says so in one line and stops.

## Safety

The wrap-up is the safest part of the session, not the most dangerous: never `git reset --hard`, never `git clean -f`, never delete files it didn't create this session without explicit confirmation. Pre-existing TODOs and debris are left alone — removing them is a change, and changes belong to a task, not a cleanup.

## Companion skills (optional)

- [`memory`](../memory/SKILL.md) — durable facts from the tail fold into `MEMORY.md`.
- [`agents-dox`](../agents-dox/SKILL.md) — the DOX closing pass runs alongside the wrap-up.
- [`teammates`](../teammates/SKILL.md) — ponytail is the natural final step after a peer team's outputs merge.

## Full workflow

See [SKILL.md](SKILL.md).
