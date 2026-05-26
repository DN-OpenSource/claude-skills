---
name: teammates-web
description: Use when building a Claude.ai React artifact that should run a task as a flat team of agents — no orchestrator role. Peers are parallel Claude API calls; coordination happens round by round through artifact-owned state. Mirrors teammates-cc, adapted for the artifact + API substrate.
---

# teammates-web

A flat peer-agent protocol for Claude.ai React artifacts. There is no orchestrator role. Each "peer" is a Claude API call made from the artifact; the artifact itself is the substrate, not a coordinator — it holds shared state and ferries each round's actions, but it does not direct peers.

## When to use

Build with this skill when the user asks Claude.ai for an artifact that needs to:

- Run a multi-part task in parallel inside the artifact (research, generate variants, review across lenses, etc.).
- Show coordination as it happens — visible roster, claims, messages, outputs.
- Avoid baking in a single "lead agent" that decides for the others.

If the task is sequential, fits in one API call, or would be confusing to render as a multi-agent UI, don't use this skill. A single Claude call is often the right answer.

## Mental model: rounds, not loops

In `teammates-cc`, peers are long-lived subagents that loop and observe shared state. A Claude.ai artifact cannot host long-lived processes, so this variant is **round-based**:

- The artifact maintains shared state (the same schema as `teammates-cc` plus a round counter).
- Each round, the artifact dispatches **one API call per active peer in parallel**, gives each peer the current state snapshot, and asks for **exactly one structured action**.
- The artifact applies the returned actions to shared state, increments the round, and dispatches the next.
- "Spawning" is just adding a roster entry. "Subagent execution" is the per-round API call. There are no real processes — just N parallel `fetch` calls per round.

The peers are still peers: the artifact does not pick winners except for unavoidable arbitration (same-round claim collisions). Everything else is the peers' decisions, expressed through actions.

## Coordination substrate

All state lives in the artifact's React state (e.g., `useReducer`). Schema mirrors `teammates-cc`:

```ts
type State = {
  session_id: string;
  task: string;
  round: number;                    // current round, starts at 0
  roster: Peer[];
  work_items: WorkItem[];
  messages: Message[];
  outputs: Record<string, string>;  // work_id -> markdown
  final?: string;                   // populated after merge
};

type Peer = {
  id: string;            // "agent-0", "agent-1", ...
  role: string;
  status: "active" | "done" | "failed";
};

type WorkItem = {
  id: string;
  description: string;
  claimed_by: string | null;
  claimed_at: string | null;
  completed_at: string | null;
};

type Message = {
  id: string;
  from: string;
  to: string[];          // ["*"] for broadcast, or specific ids
  body: string;
  ts: string;            // ISO 8601, tz-aware
};
```

Optional: persist `State` to `localStorage` keyed by `session_id` so reloading the artifact resumes the run.

## The action schema

Every per-round API call asks the peer to return **exactly one** action as JSON. The artifact validates and applies it.

```ts
type Action =
  | { type: "claim"; work_id: string }
  | { type: "message"; to: string[]; body: string }
  | { type: "work"; work_id: string; output: string }          // markdown
  | { type: "done" }                                            // nothing left to do
  | { type: "noop"; reason: string };                           // intentionally wait one round
```

Why "exactly one"? It keeps each peer's contribution per round small and inspectable, and makes conflict arbitration trivial. A peer that wants to both claim and message will do so over two rounds.

## The round

Each round, the artifact:

1. **Snapshots state** for prompt construction (deep-copy so peers see a consistent view).
2. **Builds N prompts** — one per `active` peer in the roster. The prompt contains: the protocol summary (link to this SKILL.md is fine, but include the action schema inline), the snapshot, the peer's id, and any messages addressed to this peer or `*` since its last seen round.
3. **Dispatches N parallel API calls** via `Promise.all`. Use `window.claude.complete` when running inside Claude.ai; otherwise use the Anthropic SDK with the user's key. Default model: the latest Claude Sonnet (cheap enough for high-fanout coordination).
4. **Parses each response** as an `Action`. If parsing fails, treat as `{type: "noop", reason: "unparseable response"}` and log it.
5. **Applies actions** in the following order — this order is the only "rule" the artifact enforces:
   1. All `done` and `noop` actions (no state effect beyond roster status).
   2. All `work` actions (write to `outputs`, set `completed_at` on the matching `work_item`).
   3. All `message` actions (append to `messages`, assign sequential ids).
   4. All `claim` actions, arbitrated: if multiple peers claim the same `work_id`, assign to the lowest-numbered peer; emit a synthetic message to the losing peers in the next round (`"your claim on w2 was denied; agent-K got it"`).
6. **Increments `round`**.
7. **Checks termination**: if every peer's status is `done` (or `failed`), proceed to merge. Otherwise dispatch the next round. Hard cap rounds at a sensible bound (default 30) to prevent runaway loops.

## Spawning

The artifact "spawns" peers by writing them into the initial roster. There's no Task tool. Default fan-out is 3–5 peers, same as `teammates-cc`. The artifact picks the count from the task (or accepts a prop) and bootstraps state before the first round:

```ts
const initial: State = {
  session_id: crypto.randomUUID(),
  task: userProvidedTask,
  round: 0,
  roster: Array.from({length: N}, (_, i) => ({
    id: `agent-${i}`, role: "peer", status: "active"
  })),
  work_items: /* mode-dependent, see below */,
  messages: [],
  outputs: {},
};
```

## Three coordination modes

Same three shapes as `teammates-cc`, picked at bootstrap by how `work_items` is populated:

- **Pre-decomposable** — `work_items[]` has items with `claimed_by` already set to specific peers. Round 1: every peer emits `work` for its assigned item. Round 2: `done`. Two rounds total in the happy path.
- **Self-claimed** — `work_items[]` has items with `claimed_by: null`. Round 1: peers race to `claim`. Round 2: peers `work` their claimed item. Round 3: `done`. Three rounds in the happy path; more if there are more items than peers.
- **Emergent** — `work_items[]` is empty. Round 1: peers `message` to propose items. Round 2: a peer `message`s a synthesized list (peers self-organize this via the protocol). Round 3+: claim and work. Slowest mode; use only when decomposition truly can't be done upfront.

## Merge

When every roster entry is `done` (or `failed`):

1. The artifact issues **one final API call** as agent-0 (or the lowest-numbered `done` peer if agent-0 failed) with all `outputs` and the original `task`. The prompt asks for a synthesized `FINAL.md`-style markdown answer.
2. The result is stored in `state.final` and rendered as the answer.
3. The roster/messages/outputs panels remain visible so the user can inspect what each peer contributed.

## Rendering (recommended UI shape)

The artifact's UI is part of the substrate, not optional decoration — it's how the human inspects a peer team. Recommended panels:

- **Roster** — one row per peer with live status badges.
- **Work items** — table with id, description, claimed_by, completed_at.
- **Messages** — chat-style transcript, grouped by round.
- **Outputs** — per-peer markdown previews.
- **Final** — the merged synthesis once available.
- **Round counter + "next round" button** for step-debugging, hidden behind a "Show controls" toggle in normal use.

## What to avoid

- **Don't let the artifact decide outcomes.** Its only judgment is same-round claim arbitration. Everything else — what to claim, what to message, what to write — is the peers' call.
- **Don't return multiple actions per round.** One action per peer per round keeps arbitration trivial and the transcript readable.
- **Don't skip the synthetic "claim denied" message.** Without it, a losing peer will keep retrying the same claim forever.
- **Don't run unbounded rounds.** Cap at ~30 and surface the cap to the user as a "stalled" state.
- **Don't hide messages from peers.** Every peer sees every message addressed to it or `*` since its last seen round — that's how peers coordinate without an orchestrator.
- **Don't reach for web workers** unless you genuinely need long-running peers. Round-based is the documented protocol; workers are out of scope.
