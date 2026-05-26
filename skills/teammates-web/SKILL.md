---
name: teammates-web
description: Use when building a Claude.ai React artifact that should run a task as a flat team of agents — no orchestrator role. Each agent embodies a famous programmer's personality. Peers are parallel Claude API calls; coordination happens round by round through artifact-owned state. Mirrors teammates-cc, adapted for the artifact + API substrate.
---

# teammates-web

A flat peer-agent protocol for Claude.ai React artifacts. There is no orchestrator role. Each "peer" is a Claude API call made from the artifact; the artifact itself is the substrate, not a coordinator — it holds shared state and ferries each round's actions, but it does not direct peers. Every peer embodies a famous programmer's personality, shaping how they reason, what they prioritize, and how they write.

## When to use

Build with this skill when the user asks Claude.ai for an artifact that needs to:

- Run a multi-part task in parallel inside the artifact (research, generate variants, review across lenses, etc.).
- Show coordination as it happens — visible roster with programmer names, claims, messages, outputs.
- Avoid baking in a single "lead agent" that decides for the others.

If the task is sequential, fits in one API call, or would be confusing to render as a multi-agent UI, don't use this skill. A single Claude call is often the right answer.

## Programmer Roster

When bootstrapping a team, pick N names from this roster. Choose people whose personalities create productive tension for the task — pair Dijkstra with Hopper when you need both rigor and pragmatism; pair Dean with Cerf for a distributed systems problem.

| Slug | Name | Personality |
|------|------|-------------|
| `linus-torvalds` | Linus Torvalds | Blunt, direct, zero patience for bloat or lazy thinking. Performance is a feature; anything that wastes cycles is a bug. Writes terse, unsparing analysis. Will name exactly what's wrong. |
| `donald-knuth` | Donald Knuth | Meticulous and mathematical. Won't accept a solution without understanding its correctness. Documents with rigorous precision. Treats every algorithm as something worth proving, not just running. |
| `grace-hopper` | Grace Hopper | Pragmatic and relentlessly action-oriented. Ships working solutions over perfect ones. Famous for "it's easier to ask forgiveness than permission." Cuts through process to get things done. |
| `margaret-hamilton` | Margaret Hamilton | Safety-first, every edge case matters. Defensive thinking is not paranoia — it's engineering. Error handling is a first-class concern, not an afterthought. Wrote the Apollo software; stakes are always real. |
| `edsger-dijkstra` | Edsger Dijkstra | Formal, structured, uncompromising about correctness. Thinks in invariants, pre/post conditions, and proofs. Considers "testing shows absence of bugs" naïve. Writing is dense but precise. |
| `dennis-ritchie` | Dennis Ritchie | Minimalist. If an idea can be expressed simply, express it simply. Close to the metal; loves the machine. Elegance through reduction. Designed C; keeps things small and composable. |
| `ken-thompson` | Ken Thompson | Unix hacker. Small, sharp tools that compose well. Trusts the pipeline. Skeptical of anything that can't be explained in one sentence. Builds the simplest thing that could possibly work — then ships it. |
| `john-carmack` | John Carmack | Deep optimization and first-principles reasoning. Will throw out prior work and start over if the approach is fundamentally wrong. Writes long, thorough analyses. Latency lives rent-free in his head. |
| `barbara-liskov` | Barbara Liskov | Abstraction-focused. Clean, stable interfaces matter more than clever internals. Correctness through strong contracts. Suspicious of code that mixes levels of abstraction. Named the substitution principle. |
| `alan-kay` | Alan Kay | Big-picture thinker. Objects, messages, and emergent behavior. "The best way to predict the future is to invent it." Challenges the problem statement before solving it. Synthesizes ideas across fields. |
| `rob-pike` | Rob Pike | Clarity over cleverness. Simplicity is a feature, not a constraint. If code needs a comment explaining what it does, rewrite the code. Concurrency done right. Go philosophy in everything. |
| `guido-van-rossum` | Guido van Rossum | Readability is paramount. There should be one — and preferably only one — obvious way to do it. Pythonic solutions exist even outside Python. Consistent style is non-negotiable. |
| `bjarne-stroustrup` | Bjarne Stroustrup | Zero-overhead abstractions. Systems-level thinking. Distinguishes between complexity inherent in the problem and complexity introduced by the solution. Won't sacrifice performance for false simplicity. |
| `jeff-dean` | Jeff Dean | Distributed systems mindset. Thinks at scale — millions of requests, petabytes of data. "Numbers every engineer should know." Latency percentiles and throughput are always part of the picture. |
| `ada-lovelace` | Ada Lovelace | Algorithmic elegance and first-principles analysis. Annotates every step of her reasoning. Sees the mathematical structure beneath the surface of any problem. History's first programmer; treats the work as art. |
| `vint-cerf` | Vint Cerf | Protocol designer. Layered thinking. Interoperability and standards above all. Ensures nothing is coupled that doesn't need to be. Wrote TCP/IP; considers the long-term compatibility of every interface. |
| `bill-joy` | Bill Joy | Systems depth at every layer of the stack. BSD roots. Early distributed computing pioneer. Comfortable from kernel to application. Wrote vi. Pragmatic but not careless. |
| `james-gosling` | James Gosling | Portability, safety, and principled language design. Platform independence as a first-class goal. Strong opinions about what belongs in a language core versus libraries. Designed Java; thinks in long-running, heterogeneous deployments. |

## Mental model: rounds, not loops

In `teammates-cc`, peers are long-lived subagents that loop and observe shared state. A Claude.ai artifact cannot host long-lived processes, so this variant is **round-based**:

- The artifact maintains shared state (the same schema as `teammates-cc` plus a round counter).
- Each round, the artifact dispatches **one API call per active peer in parallel**, gives each peer the current state snapshot, and asks for **exactly one structured action**.
- The artifact applies the returned actions to shared state, increments the round, and dispatches the next.
- "Spawning" is just writing programmer slugs into the initial roster. "Subagent execution" is the per-round API call. There are no real processes — just N parallel `fetch` calls per round.

The peers are still peers: the artifact does not pick winners except for unavoidable arbitration (same-round claim collisions, resolved alphabetically by slug). Everything else is the peers' decisions, expressed through actions and shaped by their personalities.

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
  id: string;            // programmer slug, e.g. "grace-hopper"
  personality: string;   // personality description from the roster above
  role: string;
  status: "active" | "done" | "failed";
};

type WorkItem = {
  id: string;
  description: string;
  claimed_by: string | null;   // programmer slug or null
  claimed_at: string | null;
  completed_at: string | null;
};

type Message = {
  id: string;
  from: string;           // programmer slug
  to: string[];           // ["*"] for broadcast, or specific slugs
  body: string;
  ts: string;             // ISO 8601, tz-aware
};
```

Optional: persist `State` to `localStorage` keyed by `session_id` so reloading the artifact resumes the run.

## The action schema

Every per-round API call asks the peer to return **exactly one** action as JSON. The artifact validates and applies it.

```ts
type Action =
  | { type: "claim"; work_id: string }
  | { type: "message"; to: string[]; body: string }
  | { type: "work"; work_id: string; output: string }          // markdown, written in character
  | { type: "done" }                                            // nothing left to do
  | { type: "noop"; reason: string };                           // intentionally wait one round
```

Why "exactly one"? It keeps each peer's contribution per round small and inspectable, and makes conflict arbitration trivial. A peer that wants to both claim and message will do so over two rounds.

## The round

Each round, the artifact:

1. **Snapshots state** for prompt construction (deep-copy so peers see a consistent view).
2. **Builds N prompts** — one per `active` peer in the roster. Each prompt contains: the protocol summary (include the action schema inline), the snapshot, the peer's programmer slug and **full personality description**, and any messages addressed to this peer or `*` since its last seen round. The personality must appear prominently — it's what makes each peer's output distinct.

   Example prompt fragment:
   > You are **john-carmack**. Your personality: Deep optimization and first-principles reasoning. Will throw out prior work and start over if the approach is fundamentally wrong. Writes long, thorough analyses. Latency lives rent-free in his head.
   >
   > Express this personality in your output and messages. Carmack's `work` output reads differently than Hopper's — make it real. But return exactly one valid Action JSON; the protocol is the contract that lets the team function.

3. **Dispatches N parallel API calls** via `Promise.all`. Use `window.claude.complete` when running inside Claude.ai; otherwise use the Anthropic SDK with the user's key. Default model: the latest Claude Sonnet (cheap enough for high-fanout coordination).
4. **Parses each response** as an `Action`. If parsing fails, treat as `{type: "noop", reason: "unparseable response"}` and log it.
5. **Applies actions** in the following order — this order is the only "rule" the artifact enforces:
   1. All `done` and `noop` actions (no state effect beyond roster status).
   2. All `work` actions (write to `outputs`, set `completed_at` on the matching `work_item`).
   3. All `message` actions (append to `messages`, assign sequential ids).
   4. All `claim` actions, arbitrated: if multiple peers claim the same `work_id`, assign to the **alphabetically-first programmer slug**; emit a synthetic message to the losing peers in the next round (e.g., `"your claim on w2 was denied; grace-hopper got it"`).
6. **Increments `round`**.
7. **Checks termination**: if every peer's status is `done` (or `failed`), proceed to merge. Otherwise dispatch the next round. Hard cap rounds at a sensible bound (default 30) to prevent runaway loops.

## Spawning

The artifact "spawns" peers by writing them into the initial roster. There's no Task tool. Default fan-out is 3–5 peers, same as `teammates-cc`. Pick programmer slugs whose strengths match the task:

- API design review → Liskov (interfaces), Pike (simplicity), Stroustrup (zero-overhead)
- Distributed system debugging → Dean (scale), Cerf (protocols), Hamilton (safety)
- Algorithm design → Knuth (correctness), Lovelace (elegance), Dijkstra (formal proof)
- Shipping under pressure → Hopper (pragmatism), Thompson (simplicity), Joy (full-stack depth)

Bootstrap state before the first round:

```ts
const ROSTER = [
  { id: "grace-hopper",   personality: "Pragmatic and relentlessly action-oriented. Ships working solutions over perfect ones..." },
  { id: "john-carmack",   personality: "Deep optimization and first-principles reasoning. Will throw out prior work..." },
  { id: "barbara-liskov", personality: "Abstraction-focused. Clean, stable interfaces matter more than clever internals..." },
  // ... pick N from the full roster above
];

const chosen = pickN(ROSTER, N); // your selection logic

const initial: State = {
  session_id: crypto.randomUUID(),
  task: userProvidedTask,
  round: 0,
  roster: chosen.map(p => ({ ...p, role: "peer", status: "active" })),
  work_items: /* mode-dependent, see below */,
  messages: [],
  outputs: {},
};
```

## Three coordination modes

Same three shapes as `teammates-cc`, picked at bootstrap by how `work_items` is populated:

- **Pre-decomposable** — `work_items[]` has items with `claimed_by` already set to specific programmer slugs. Round 1: every peer emits `work` for its assigned item, in character. Round 2: `done`. Two rounds total in the happy path. Example: assign `margaret-hamilton` to error handling, `john-carmack` to performance, `rob-pike` to clarity review.
- **Self-claimed** — `work_items[]` has items with `claimed_by: null`. Round 1: peers race to `claim`. Round 2: peers `work` their claimed item. Round 3: `done`. Three rounds in the happy path; more if there are more items than peers.
- **Emergent** — `work_items[]` is empty. Round 1: peers `message` to propose items. Round 2: a peer `message`s a synthesized list (peers self-organize this via the protocol). Round 3+: claim and work. Slowest mode; use only when decomposition truly can't be done upfront.

## Merge

When every roster entry is `done` (or `failed`):

1. The artifact issues **one final API call** as the first programmer slug in the roster (alphabetically-first `done` peer if that peer failed) with all `outputs` and the original `task`. The prompt identifies the merger by name and personality, and asks for a synthesized `FINAL.md`-style markdown answer in that programmer's voice.
2. The result is stored in `state.final` and rendered as the answer.
3. The roster/messages/outputs panels remain visible so the user can inspect what each peer contributed and how their personalities shaped the work.

## Rendering (recommended UI shape)

The artifact's UI is part of the substrate, not optional decoration — it's how the human inspects a peer team. Recommended panels:

- **Roster** — one row per peer with their name, personality summary, and live status badge. Names make the transcript readable; show them prominently.
- **Work items** — table with id, description, claimed_by (programmer name), completed_at.
- **Messages** — chat-style transcript grouped by round, attributed by programmer name. Distinct voices make the conversation legible.
- **Outputs** — per-peer markdown previews, labelled by programmer name. A Knuth output looks different from a Hopper output; the labels are load-bearing.
- **Final** — the merged synthesis once available, attributed to the merger.
- **Round counter + "next round" button** for step-debugging, hidden behind a "Show controls" toggle in normal use.

## What to avoid

- **Don't let the artifact decide outcomes.** Its only judgment is same-round claim arbitration (alphabetically-first slug wins). Everything else — what to claim, what to message, what to write — is the peers' call.
- **Don't return multiple actions per round.** One action per peer per round keeps arbitration trivial and the transcript readable.
- **Don't skip the synthetic "claim denied" message.** Without it, a losing peer will keep retrying the same claim forever.
- **Don't run unbounded rounds.** Cap at ~30 and surface the cap to the user as a "stalled" state.
- **Don't hide messages from peers.** Every peer sees every message addressed to it or `*` since its last seen round — that's how peers coordinate without an orchestrator.
- **Don't reach for web workers** unless you genuinely need long-running peers. Round-based is the documented protocol; workers are out of scope.
- **Don't let personality override protocol.** Torvalds may want to rewrite everything; he still returns exactly one Action per round like everyone else.
- **Don't pick programmers at random.** Choose the roster deliberately — the personalities should create useful friction, not noise.
