---
name: decision-maker
description: Fast, cheap, calibrated decisions via TypeSafe's Jev System One model — typed yes/no (noul), choice, and score answers with confidence, in under a second, instead of reasoning through a judgment call yourself. Use when a step reduces to a closed-set judgment over text in hand (route, classify, triage, rank, verify, gate, or which element to click and whether a step passed while browser-testing an app), when an LLM prompt-and-parse step could be a typed decision, when the user mentions TypeSafe, Jev, System One, or decision provider, or wants to add/edit a provider, base URL, or API key. Confidence-gated; falls back to your own judgment when unconfigured.
---

# Decision Maker

Jev (TypeSafe's System One model) answers typed questions about some text: **noul** (yes/no probability), **choice** (one of N, with confidence) and **score** (position on ordered levels). Use it for the many narrow, closed-set judgments inside a task. Claude still does the reasoning.

`D=<this skill's dir>/scripts/decide.py`. Run `python3 $D provider list` to see providers; the default is set by the user (`references/providers.md`).

## Batch many items (the main use: content never enters your context)

```bash
python3 $D ask --items 'src/**/*.py' --brief \
  --noul hit 'Does {item} implement or call refund logic (not just mention refunds in text)?'
```

`--items` takes a file (one item per line, labelled `file:line`) or a glob (one item per file). `{item}` marks where the item goes, and batches of 100 go out as one request each. The output lists the **hits and the unsure cases only**, and each unsure case carries an excerpt of its text.

**Run this first, with no grep or reading beforehand: the batch covers every item.** Then answer straight from the output: trust the `act` lines, and judge the `ask` lines from their excerpts. Open a file only when an excerpt isn't enough. Use `--where all` to see every answer.

## Browser testing: hand all the steps to the runner

```bash
node <this skill's dir>/scripts/browser_steps.mjs --url http://localhost:3000 \
  --steps "Open the sign-in page" "Fill the work email with dana@acme.io" "Submit the login form" "Verify the page shows Welcome"
```

The runner needs `npm i playwright-core` and Chrome. Add `--cdp http://127.0.0.1:9222` to attach to a browser that's already open.

For each page view it makes **one** Jev call, which checks whether the step is done, whether the page is loading, whether something blocks it, and which element to act on. It dismisses cookie banners and modals by itself, retries after a wrong-but-harmless click, and requires 0.8 confidence for risky clicks (delete, pay, send).

**Exit 3 means it was unsure.** It prints the page's elements and text; do that step yourself, then continue. The browser benchmark measured Claude Code at about 2× faster and −67% cost against driving the browser itself, and the runner alone (CI) at 4× faster.

## One state, several questions

```bash
python3 $D ask --brief --state "Help! Payouts failing for 3 days." \
  --noul urgent "Does this convey urgency?" \
  --choice team "Which team handles this?" "billing,technical,sales" \
  --score anger "How frustrated is the customer?" "calm|frustrated|very angry"
```

State comes from `--state`, `--state-file` or stdin; JSON is sent structured. Refer to fields with backticks and put such questions in **single quotes**. For rich criteria, use `--questions @file.json`. Without `--brief` the output is full JSON, with an `act` flag per answer (`--min-confidence`, default 0.8).

## Rules

1. **Batch.** Put every independent question and item in one call. Never send one call per item.
2. **Gate on confidence, and read it right.** Act on `act`; for `ask`, decide yourself, ask the user, or take the safe option. Never delete, discard or drop on a low-confidence answer. Confidence measures how concentrated an answer is, not permission to act. A noul near 0.5 means "could be either", not "medium". When several options are acceptable, a low-confidence pick between harmless preferences is fine.
3. **One narrow judgment per question.** The full meaning goes in the question text, because ids are never sent. Give a choice a `none` option when nothing may fit.
4. **Never block.** Exit 2 means not configured or bad input; exit 1 means an API error. Say so in one line and continue on your own judgment.
5. **Decide, don't ask.** Before asking the user something with listable options, send it as a choice plus the noul "Is this a decision only the user can make (preference, credentials, money, irreversible or outward-facing)?". Proceed when the choice is confident and the noul is below 0.3, and tell the user in one line what Jev picked. Otherwise ask. Anything irreversible or outward-facing always goes to the user.

## More

- `references/use-cases.md`: recipes and thresholds for every companion skill (§1–9), general coding (§10, §13), the user's own app (§11), **browser and app testing** (§12: which element to click, blockers and errors, form fields, step and acceptance checks), and **rules, request drift and decide-don't-ask** (§14).
- **Mode:** the user chooses after install: `decide.py mode auto` (use Jev by default) or `manual` (only when asked). In manual mode, use Jev only when the user asks or invokes the skill.
- `references/guard.md` **prefetch** (on when the user chose auto mode): for "which files…" prompts, the hook scans the repo with Jev *before* your first turn and hands you the hits plus unsure excerpts. When that context is present, answer from it.
- `references/guard.md`: Claude Code hooks; the per-edit checks need `decide.py guard on` that check every edit and command against `CLAUDE.md`/`AGENTS.md` and the user's **in-prompt rules**, compare the diff with the request before Claude stops, and answer Claude's questions when confident. The user sees every intervention.
- `references/providers.md`: add or edit providers, base URLs and keys (TypeSafe, OpenRouter, OpenJEV, LiteLLM, any System One gateway).
- `references/building.md`: writing Jev into the **user's own app**: find the shape, design each judgment, compose and verify (condensed from TypeSafe's official skill).
- `references/api.md`: wire format, limits and errors. The live docs are at https://docs.typesafe.ai/llms.txt.
- `scripts/eval_usecases.py`: live accuracy eval of every recipe. `scripts/bench_claude_code.py`: Claude Code token benchmark, with and without Jev.
