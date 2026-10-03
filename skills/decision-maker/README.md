# decision-maker

Many steps in a coding session are narrow judgment calls: is this grep hit a real usage, is this file debris, which skill applies, does this migration risk data loss. Reasoning through each one with a frontier LLM is slow and costs tokens per item. TypeSafe's **Jev**, a *System One* model, answers typed questions (yes/no, choice, score) about a piece of state in about 0.1s. It returns calibrated probabilities and a confidence value, so the agent acts when Jev is sure and falls back to its own reasoning when it isn't.

## What this does

- **`scripts/decide.py`**: a stdlib-only CLI that sends one batched `POST /v1/systemone` request and prints typed answers as JSON, each with an `act` flag gated on `--min-confidence`. It retries 429/529 with backoff.
- **Providers you control**: add any gateway that speaks the System One format and edit its base URL, model and API key (`provider add|edit|use|remove|list`). Presets cover TypeSafe direct, OpenRouter, OpenJEV, and a LiteLLM proxy. The config lives in `~/.config/decision-maker/providers.json` (mode 600), never in a repo.
- **Recipes for every other skill** (`references/use-cases.md`): skill routing, ponytail's strand sorting, memory's "is this worth saving", guardian's match-vs-change, schema-aware-db's usage reranking and migration risk, teammates' claiming and merge checks, agents-dox's pass depth, and lsp's symbol disambiguation. Beyond those, there are about 20 more per-skill recipes, a catalogue of general-session uses (intent and model routing, risky-command and secret gates, commit and changelog types, review triage, file and docs ranking, claim verification, log triage, dedup), a map from the user's own app to TypeSafe cookbooks, and **browser/app testing**: when Claude drives an app (Claude in Chrome, Playwright, mobile), Jev picks the element to click from the accessibility tree, detects modals, errors and loading states, maps form fields, and verifies each step, all in one call per page.

## Quick start

```bash
export TYPESAFE_API_KEY=...        # https://console.typesafe.ai/keys
python3 scripts/decide.py ask --state "Help! Payouts failing for 3 days." \
  --noul urgent "Does this convey urgency?" \
  --choice team "Which team handles this?" "billing,technical,sales"

# another provider / custom gateway
python3 scripts/decide.py provider add mygw --base-url https://gw.example.com/typesafe --api-key-env MYGW_KEY --default
python3 scripts/decide.py provider edit mygw --base-url https://gw2.example.com/typesafe
```

## What happens after you install

**You choose how Jev is used, once, after install:**

| | **Auto**: `/decision-maker:jev auto` | **Manual**: `/decision-maker:jev manual` | Not chosen yet |
|---|---|---|---|
| **When Jev runs** | By default: "which files…" prompts are pre-scanned before Claude's first turn, and Claude uses Jev for batch sorting and browser steps | Only when you ask (`/decision-maker:decision-maker`, or "use Jev") | Only when you ask |
| **Claude's context** | About 80 tokens of ready-made Jev commands each session | Nothing added | Nothing added |
| **Sent to the provider** | File contents for find-type prompts (secrets and `.env` skipped), plus anything Claude asks Jev | Only what you or Claude explicitly ask Jev | Only what's explicitly asked |
| **Session notice** | Once, and again whenever something changes | Once, and again whenever something changes | **Every session**, until you choose |

- **Without a key,** nothing runs and nothing is sent. The first session shows how to add a key (`decide.py provider edit openjev --api-key …` or `export TYPESAFE_API_KEY=…`) and then how to choose.
- **The per-edit guard checks** (rules, scope, ask, stop) are separate in both modes. They run only after `decide.py guard on`, and `decide.py guard off` turns everything off.
- **Switching** at any time: `/decision-maker:jev auto|manual`, or `decide.py mode auto|manual`. Explicit `guard on|off` settings override the mode's defaults.
- **Running `/decision-maker:jev` with no argument while the mode isn't chosen** makes Claude ask you which mode you want, and what each one sends.

Run **`/decision-maker:jev`** at any time to see what's active, what leaves the machine and what Jev did recently. Every block, question to you and auto-answer appears as a `⚖ Jev guard (…)` line, and `decide.py guard log` keeps the history. Claude Code reports the plugin's always-on cost as about 205 tokens per session; its 4 hooks add nothing to Claude's context.

Verified by installing from a local marketplace into a separate Claude config and running real sessions: first run without a key, first run with one, a quiet second session, and the slash command. The auto/manual choice is covered by unit tests: no automatic Jev calls until a mode is chosen, a reminder every session until then, and manual mode makes no per-prompt call at all.

## Guard hooks

In auto mode prefetch is on (see above). `python3 scripts/decide.py guard on` adds the per-edit Claude Code hooks (shipped in `hooks/hooks.json`) that use Jev to keep Claude on your rules and on your request:

- **Before each edit or shell command**, Jev checks the action against your rules and against what you asked for. The rules include **temporary ones you give in a prompt** ("don't touch the tests", "use pnpm"), which last for the session until a later prompt cancels them, plus `AGENTS.md`/`CLAUDE.md` from the edited file's folder up to the root, `CLAUDE.local.md` and your global `~/.claude/CLAUDE.md`.
- **Before Claude asks you a question**, Jev answers it when it is confident and the decision isn't yours alone.
- **Before Claude finishes**, Jev compares the turn's diff with your request.

Confident problems are blocked with the reason, so Claude corrects itself. Unsure cases come to you. Clean actions pass silently. `guard off` disables it; with no key the hooks do nothing.

## Measured results (OpenJEV, 2026-10-03)

**Jev accuracy** (`scripts/eval_usecases.py`, 64 live calls covering every recipe plus 13 deliberately borderline cases): **73/73 correct**. Jev was confident enough to act on 89% of answers and was right every time it acted. The borderline cases landed in the 0.45–0.74 "unsure" band, so they went to Claude or the user. Median latency was 0.51 s per call (OpenJEV gateway); total cost was $0.0009. The cases were written by the author, so real-world accuracy will be lower; rerun with your own cases.

**Claude Code with and without Jev** (`claude -p`, Sonnet, 2 runs each). Precision was 1.00 in every run.

*Browser testing*, a 6-step sign-in flow (`scripts/bench_browser/`). The flow includes a cookie banner, look-alike buttons, a field labelled differently from the step, a spinner and a hidden account menu:

| Mode | Time | Passed | Claude cost | Turns | Context tokens |
|---|---|---|---|---|---|
| Claude drives Chrome itself | 49.6 s | 2/2 | $0.129 | 13.5 | 277k |
| **Claude + `browser_steps.mjs`** | **20.7 s (2.4× faster)** | 2/2 | **$0.043 (−67%)** | **2** | **36k (−87%)** |
| Runner alone (CI) | **11.8 s (4.2× faster)** | 2/2 | $0 | 0 | 0 |

*Semantic sorting of files* (`scripts/bench_claude_code.py`):

| Task | Plain Claude | Jev as a tool call | **Jev prefetch** (hook, no prompt hint) |
|---|---|---|---|
| 100 files: which do refunds? | 8.8 s · $0.052 · 3 turns · recall 0.78 | 9.4 s · $0.045 · 2 turns · 1.00 | **6.5 s (−26%) · $0.031 (−40%) · 1 turn · 1.00** |
| 300 files: same | 9.3 s · $0.055 · 3.5 turns · recall 0.67 | 9.9 s · $0.045 · 2 turns · 1.00 | **7.5 s (−19%) · $0.031 (−44%) · 1 turn · 1.00** |
| 80 grep hits (one small file) | 7.3 s · $0.052 · 2 turns · recall 0.90 | 10.3 s · $0.051 · 2.5 turns · 1.00 | 10.7 s · $0.056 · 2 turns · 1.00 |

Precision was 1.00 for the final prefetch version (on in auto mode; see `references/guard.md`). The redesign moves Jev before Claude's first turn: the prompt hook recognises a find task, scans the repo in parallel batches (about 1–2.5 s) and hands Claude the answer, so no tool turn is needed. What got it there:

- **Criteria instead of a long question:** this moved look-alikes ("refund", but to the merchant) from confident hits into "unsure with excerpt", which raised precision from 0.90 to 1.00.
- **Earlier wins:** a SessionStart command hint, compact batch output, parallel batches and a 4.6 KB skill file got the tool-call mode from +53% cost down to below plain Claude.

For a single small file, Claude still reads it to double-check. That's the one case where prefetch adds time, and there plain Claude is about as good.

**Guard:**
- End-to-end with real hooks, it fires correctly and shows every step to the user.
- Over 78 live precision trials (`scripts/eval_guard.py`) it had 0 false alarms, 0 misses and 0 harmful denials.
- Replayed on the real log, the new threshold cut "asked you" interruptions from 9 to 3.
- It adds about 20–40% Claude cost on a task where it intervenes.

**Known limit:** for "Open account settings", Jev's first click is the workspace "Settings" link. The runner sees the step isn't done and recovers through the account menu (3 of 3 runs), at the cost of one extra click.

## Safety

Without a key (or when the API fails), `decide.py` exits non-zero and the calling skill continues on Claude's own judgment. Nothing ever blocks on this skill. Destructive actions are never taken on a low-confidence answer.

## Tests

`cd scripts && python3 -m unittest test_decide -v` runs the tests against a local fake server, so no key or network is needed.

## Full workflow

See [SKILL.md](SKILL.md). API facts: [references/api.md](references/api.md).
