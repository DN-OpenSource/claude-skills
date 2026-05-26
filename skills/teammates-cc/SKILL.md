---
name: teammates-cc
description: Use when a task benefits from being split across multiple Claude Code subagents working as flat peers — no orchestrator, no hierarchy. Agents share a JSON manifest, claim work, message each other, and merge outputs.
---

# teammates-cc

A protocol for running a task as a flat team of Claude Code subagents. There is no orchestrator role. Every agent — including the one that spawned the team — follows the same loop and reads from the same shared state.

## When to use

- The task has parts that can run in parallel (research multiple topics, review multiple files, generate variants, etc.).
- You want every agent's contribution to be visible and inspectable after the fact.
- You'd rather have peers negotiate than nominate a coordinator that becomes a bottleneck.

If a task is sequential by nature, or small enough for one agent, don't use this skill.

## Coordination substrate

All state lives in one gitignored directory at the **project root** (the directory where Claude Code was invoked — same place your top-level `.git`/`package.json`/etc. live). Every peer must refer to it by absolute path or `${project_root}/.teammates/`, not by a CWD-relative path, because subagents may not inherit your working directory.

```
.teammates/
├── state.json          ← the only shared state
└── outputs/
    └── <work-id>.md    ← one file per completed work item
```

`state.json` schema:

```json
{
  "session_id": "uuid",
  "task": "free-text description of the overall goal",
  "roster": [
    {"id": "agent-0", "role": "spawner+peer", "status": "active"},
    {"id": "agent-1", "role": "researcher",   "status": "active"}
  ],
  "work_items": [
    {
      "id": "w1",
      "description": "...",
      "claimed_by": null,
      "claimed_at": null,
      "completed_at": null,
      "output_path": "outputs/w1.md"
    }
  ],
  "messages": [
    {"id": "m1", "from": "agent-1", "to": ["*"], "body": "...", "ts": "2026-05-26T10:00:00Z"}
  ]
}
```

Field meanings:
- `roster[].status`: `active` while working, `done` when nothing left to claim, `failed` if the agent gave up.
- `work_items[].claimed_by`: `null` means up for grabs.
- `messages[].to`: list of agent ids, or `["*"]` for broadcast.

## Editing state.json safely

The re-read-after-write pattern only protects the **field you just wrote**. It does **not** stop you from clobbering fields another peer changed between your read and your write. To prevent silent data loss, every peer follows three invariants:

1. **Only modify your own roster entry and the work_item you currently hold.** Never touch another peer's roster row or claim.
2. **Only append to `messages[]`. Never edit or remove existing messages.**
3. **Always read-modify-write through a small script, not by hand-editing JSON.** Hand edits will eventually corrupt the file.

A canonical Python snippet for an edit — copy and adapt:

```bash
python3 << 'PYEOF'
import json, datetime
ts = datetime.datetime.now(datetime.UTC).isoformat()  # tz-aware; utcnow() is deprecated
path = '.teammates/state.json'
with open(path) as f:
    state = json.load(f)

# ... mutate ONLY your roster entry, your work_item, or append to messages ...

with open(path, 'w') as f:
    json.dump(state, f, indent=2)
PYEOF
```

If your write is a claim, follow it with a fresh read of the same file and verify the field still names you. If not, the other writer won — back off and pick a different item.

## The peer loop

Every agent — including agent-0 — runs the same loop:

1. **Read** `.teammates/state.json`.
2. **Read new messages** addressed to you or `*` since your last read. Act on anything that needs a reply.
3. **Claim** a work item:
   - Pick a `work_item` with `claimed_by == null` that you can do.
   - Write your id into `claimed_by` and `claimed_at`.
   - **Re-read** `state.json`. If the item now lists someone else, back off and pick another. (Last-writer-wins is the only concurrency tool; the re-read is what makes it safe enough.)
4. **Work** the claimed item. Use the Read/Edit/Bash tools as needed.
5. **Message** other peers when you need to coordinate or hand off. Append to `messages[]`; never edit existing messages.
6. **Write output** to `.teammates/outputs/<work-id>.md`. Set `completed_at` on the work item.
7. **Repeat from step 1** until no claimable work remains.
8. **Finish** by setting your own roster entry to `status: done`.

If at any point you cannot make progress, set your roster status to `failed` and write a short reason into `messages[]`. Do not silently exit.

## Spawning peers

The first invocation in a Claude Code session is `agent-0`. Agent-0:

1. Creates `.teammates/state.json` with `roster: [{"id": "agent-0", ...}]` and the task text.
2. Decides which mode (see below) and populates `work_items` accordingly.
3. Adds each new peer to `roster[]` **before** spawning (so other peers see it).
4. Spawns N peer agents via the Task tool, in parallel, with `run_in_background: true` so agent-0 can participate concurrently. Each spawn uses this prompt template (fill in `${project_root}`, `${N}`, `${task}`):

   > You are `agent-${N}` in a flat peer team running in Claude Code. There is no orchestrator.
   >
   > Project root (absolute path): `${project_root}`
   >
   > Required reading, in order:
   > 1. `${project_root}/skills/teammates-cc/SKILL.md` — the protocol you must follow
   > 2. `${project_root}/.teammates/state.json` — current shared state
   >
   > Then run the peer loop in the skill exactly. Use small Python snippets via Bash for every read-modify-write on `state.json` — the skill shows the template. Do not hand-edit JSON. Only modify your own roster entry and the work_item you currently hold; only append to `messages[]`.
   >
   > Overall task: `${task}`. Stop when your roster status is `done`. Do not summarize for me — your output goes in `.teammates/outputs/`. Return only a one-line confirmation like `agent-${N} done, claimed: <work-id>`.

5. Then runs the peer loop itself.

Default fan-out: 3 to 5 peers including agent-0. More than that usually adds coordination drag rather than throughput.

## Three coordination modes

The same substrate supports three task shapes. Agent-0 picks the mode when it populates the initial state.

**Pre-decomposable** — work splits cleanly upfront.
Agent-0 fills `work_items[]` with explicit `claimed_by` set to specific agent ids at spawn time. Peers just execute their assigned items. Use this when you can name the parts before starting (e.g., "review this PR for security, perf, readability, tests").

**Self-claimed** — work is a queue.
Agent-0 fills `work_items[]` with `claimed_by: null`. Peers race to claim. Use this when items are similar in shape but you don't care who does which (e.g., "summarize each of these 12 issues").

**Emergent** — the work itself has to be negotiated.
Agent-0 leaves `work_items[]` empty. Peers propose items via `messages`, agree, then add them to `work_items[]` as they go. Use this only when you genuinely cannot decompose upfront — it's slower than the other two modes.

## Merge

When **all** roster entries are `status: done` (or `failed`), the merge step runs:

1. Agent-0 is the default merger. Agent-0 waits for the other peers to finish using whichever signal is cheapest:
   - **Preferred:** if peers were spawned via the Task tool with `run_in_background: true`, the Claude Code harness sends a completion notification for each. Wait for those — no polling needed.
   - **Fallback:** if you have no notification source, re-read `state.json` opportunistically (e.g., after every Bash call you make for other reasons). Do not enter a tight `sleep` loop in the foreground.
2. The merger reads every file in `.teammates/outputs/` and synthesizes them into `.teammates/FINAL.md`, addressed to the original task.
3. The merger writes a one-line summary to chat pointing at `FINAL.md` so the human can find it.

**Failure detection.** If a peer's `status` stays `active` long after its spawning Task call returned (or has been running an unreasonable amount of time given the work), agent-0 may set that peer's roster `status` to `failed`, append a message explaining why, and proceed with the merge using whatever outputs exist. The skill makes no promise of unbounded waiting — better to ship a partial merge with a note than hang forever.

If agent-0 itself has failed (status `failed`), the lowest-numbered `done` peer takes over the merge.

## What to avoid

- **Don't appoint an orchestrator.** The moment one agent starts directing the others, the protocol is broken — you've reinvented hierarchy. Coordinate through `messages` and `work_items`, not by giving orders.
- **Don't skip the re-read in claim.** Without it, two peers can claim the same item and silently duplicate work.
- **Don't read other peers' `outputs/` files mid-work.** Outputs are for the merge step. If you need information in-flight, send a message and wait for a reply.
- **Don't mutate `messages[]` entries** — only append. Past messages are history.
- **Don't spawn more peers than the task can absorb.** 3–5 is the sweet spot in CC. If you find yourself wanting 10, the task probably isn't actually parallelizable.
- **Don't silently exit.** Set roster `status` to `done` or `failed` before stopping.
