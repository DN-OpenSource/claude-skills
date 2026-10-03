# decision-maker: Jev for Claude Code

Much of a coding session is small judgment calls:

- *Is this grep hit a real usage?*
- *Which of these 300 files implement refunds?*
- *Which button signs me in?*
- *Does this edit break the "don't touch tests" rule I gave earlier?*

Claude can reason through each one, but that costs a model turn and tokens every time. **Jev**, TypeSafe's *System One* decision model, answers exactly this kind of question: yes/no, pick-one or a score. It reads text or JSON, replies in under a second, and returns a **calibrated confidence**.

This plugin brings Jev into Claude Code:

- **Confident:** Claude or the hook acts on Jev's answer.
- **Unsure:** Claude decides itself, or asks you.
- **Every time Jev is used, you see a line saying so.**

## Contents

1. [Install and set up](#1-install-and-set-up)
2. [Choose how Jev is used: auto or manual](#2-choose-how-jev-is-used-auto-or-manual)
3. [You always know when Jev is used](#3-you-always-know-when-jev-is-used)
4. [What Jev can do: every feature](#4-what-jev-can-do-every-feature)
5. [Providers, base URLs and API keys](#5-providers-base-urls-and-api-keys)
6. [Privacy: what is sent, and when](#6-privacy-what-is-sent-and-when)
7. [Command reference](#7-command-reference)
8. [Configuration and environment variables](#8-configuration-and-environment-variables)
9. [Measured results](#9-measured-results)
10. [Tuning and evaluation](#10-tuning-and-evaluation)
11. [Safety, failure behaviour and limits](#11-safety-failure-behaviour-and-limits)
12. [Files in this plugin](#12-files-in-this-plugin)

`decide.py` below means `python3 <plugin dir>/scripts/decide.py`. Run `/decision-maker:jev` to see the exact path on your machine.

---

## 1. Install and set up

```bash
claude plugin marketplace add DN-OpenSource/claude-skills
claude plugin install decision-maker@claude-skills
```

Restart Claude Code, or run `/reload-plugins`. Then add a provider key, either stored in the config:

```bash
decide.py provider edit openjev --api-key YOUR_OPENJEV_KEY --default
```

or as an environment variable set **before** starting `claude`:

```bash
export TYPESAFE_API_KEY=…       # key from https://console.typesafe.ai/keys
```

Finally, choose a mode (section 2): `/decision-maker:jev auto` or `/decision-maker:jev manual`.

What you see on the first session:

| Situation | Notice at session start |
|---|---|
| No key yet | `⚖ decision-maker is installed but INACTIVE: no Jev provider key, so nothing is sent anywhere.`, plus the command to add one |
| Key set, mode not chosen | The active provider, `Mode: NOT CHOSEN, so nothing runs automatically. Choose once: /decision-maker:jev auto … or manual …`, and what is sent |
| Key set, mode chosen | Provider, mode, the active guard checks, and **exactly what is sent to the provider** |

The notice repeats every session until you choose a mode. After that it shows only when something changes: key, provider, mode or guard checks.

Claude Code reports the plugin as **2 commands** (`/decision-maker:decision-maker` and `/decision-maker:jev`) plus **6 hook events** (UserPromptSubmit, PreToolUse, Stop, SessionStart, PostToolUse, PostToolUseFailure). The always-on cost is about 205 tokens per session, and the hooks add nothing to Claude's context.

## 2. Choose how Jev is used: auto or manual

| | **Auto** (`/decision-maker:jev auto`) | **Manual** (`/decision-maker:jev manual`) | Not chosen yet |
|---|---|---|---|
| "Which files…" prompts | Pre-scanned by Jev before Claude's first turn (prefetch) | Normal Claude | Normal Claude |
| Claude using Jev tools | By default, for batch sorting and browser test steps, because Claude gets the commands at session start | Only when you ask (`/decision-maker:decision-maker`, or "use Jev") | Only when you ask |
| Per-prompt Jev call | Yes, one small call to check whether this is a find task | **None** | None |
| Added to Claude's context | About 80 tokens of commands per session | Nothing | Nothing |
| Session notice | When something changes | When something changes | Every session |

- **Switching:** `/decision-maker:jev auto|manual`, or `decide.py mode auto|manual`, at any time. `decide.py mode` shows the current mode.
- **If you haven't chosen:** running `/decision-maker:jev` with no argument makes Claude ask you, with both options explained.
- **Guard checks are separate:** the per-edit checks in section 4.3 are their own switch in both modes (`decide.py guard on|off`). An explicit guard choice always wins over the mode's defaults.

## 3. You always know when Jev is used

**Every** Jev call produces a `⚖` line in your Claude Code session, whether it changed anything or not:

| Who used Jev | Example of what you see |
|---|---|
| Prompt check (rules, find task) | `⚖ Jev read your prompt (rules + find-task check) → no new rules, not a find task (1 call, 0.6s, 439 tokens, $0.00002)` |
| Rule found in your prompt | `⚖ Jev guard (rules): now enforcing: "Don't touch the tests folder."` |
| Prefetch | `⚖ Jev guard (pre-scan): checked 101 items in 1.3s: 9 relevant, 1 unsure; handed to Claude` |
| Edit or command allowed | `⚖ Jev checked Edit src/billing/refunds.py against 3 rules + scope → OK, allowed (1 call, 0.6s, …)` |
| Edit or command blocked | `⚖ Jev guard (blocked): BLOCKED Bash npm install left-pad · rule from CLAUDE.md: Use pnpm, never npm (p=0.95) · Claude was told to adjust` |
| Unsure, asking you | `⚖ Jev guard (needs you): unsure about Write src/app.test.js · rule from your instruction this session … (p=0.78) · approve or reject below` |
| Question answered for you | `⚖ Jev guard (answered for you): Which test runner? → pytest (confidence 0.92)` |
| End-of-turn check | `⚖ Jev compared this turn's changes (1 file) with your request → complete, nothing unrelated` |
| Claude ran Jev itself | `⚖ Jev used by Claude (decide.py): 1 call, 80 items, 0.6s, 5,972 tokens, $0.00025 via openjev` |
| Browser runner | `⚖ Jev used by browser runner: 14 calls, 10.3s, …` |
| Provider down | `⚖ Jev unavailable (HTTP 503 …): continued without it` |

For history and totals:

- **`decide.py usage [--hours 24] [-n 10]`** lists every Jev call: when, by whom (automatic hooks, Claude via `decide.py`, or the browser runner), questions, items, time, tokens and cost.
- **`decide.py guard log`** lists the interventions: blocked, asked, answered, sent back, and rules added or dropped.
- **`/decision-maker:jev`** shows status, what leaves the machine, and recent activity, in plain words.

## 4. What Jev can do: every feature

### 4.1 Typed decisions (`decide.py ask`)

Jev answers three question types about any **state** (text, or a JSON object or array):

| Type | Answer | Example |
|---|---|---|
| **noul** (yes/no) | Probability of "yes", from 0 to 1 | `--noul urgent "Does this convey urgency?"` |
| **choice** | The best option, plus a probability for every option and a confidence (up to 255 options) | `--choice team "Which team?" "billing,technical,sales"` |
| **score** | A position on 2–10 ordered levels, plus confidence | `--score anger "How frustrated?" "calm|frustrated|very angry"` |

```bash
decide.py ask --brief --state "Help! Payouts failing for 3 days." \
  --noul urgent "Does this convey urgency?" \
  --choice team "Which team handles this?" "billing,technical,sales"
```

- **All questions go in one call** and are answered in parallel against the same state.
- **Each answer has an `act` flag:** true when confidence is at least `--min-confidence` (default 0.8). For a noul, confidence means `max(p, 1-p)`.
- **Richer questions:** `--questions @file.json` takes per-option descriptions, structured instructions, or criteria for what counts as yes or no.
- **Inspecting a request:** `--dry-run` prints the request and sends nothing.

### 4.2 Batch sorting of files and lines (`--items`)

```bash
decide.py ask --items 'src/**/*.py' --brief \
  --noul hit 'Does {item} implement or call refund logic (not just mention refunds in text)?'
decide.py ask --items hits.txt --brief --noul real 'Is {item} code that reads or writes the orders table?'
```

- **Items:** a glob gives one item per file (the first 4,000 characters); a file gives one item per line.
- **Batching:** batches of 100 items are sent **in parallel**. 300 files take about 2.2 s.
- **Privacy of content:** item text goes straight to Jev and **never passes through Claude's context**.
- **Output:** only the hits plus the unsure items, each unsure item with a short excerpt so Claude can judge it without opening the file. Use `--where all|yes|no|unsure` to choose what's shown.

### 4.3 Claude Code hooks

| Hook | Feature | What it does | On when |
|---|---|---|---|
| SessionStart | **Status notice** | Tells you what Jev does and what is sent where | Always |
| SessionStart | **Command hint** | Gives Claude the ready-made batch and browser commands (about 80 tokens), so it skips loading the skill | Auto mode with a key; `DECISION_MAKER_HINT=0` disables it |
| UserPromptSubmit | **Prefetch** | One call checks "is this a find-files-by-meaning request?". If yes, Jev scans the repo (or the lines of a file the prompt names) before Claude's first turn, so Claude answers in **one turn with no tool calls** | Auto mode, or `guard on prefetch` |
| UserPromptSubmit | **Rules from your prompts** | Picks up standing instructions you write ("don't touch the tests", "use pnpm", "no new dependencies") word for word, enforces them for the session, and drops one when a later prompt cancels it | `guard on` (rules) |
| PreToolUse: Edit, Write, MultiEdit, NotebookEdit, Bash | **Rules** | Checks the action against each rule: your prompt rules first, then `AGENTS.md`/`CLAUDE.md` from the edited file's folder up to the repo root, then `.claude/CLAUDE.md`, `CLAUDE.local.md` and `~/.claude/CLAUDE.md` (up to 40 rules) | `guard on` |
| PreToolUse | **Scope** | Is this action outside what you asked for? | `guard on` |
| PreToolUse: Bash | **Risky commands** | Data deletion, history rewrites, pushes, publishing, sending messages and production changes **always come to you**, never auto-blocked | `guard on` |
| PreToolUse: AskUserQuestion | **Decide, don't ask** | When Jev is confident and the decision isn't yours alone, it answers Claude's question and tells you the pick. Decisions about preferences, credentials or money, and anything irreversible or outward-facing, always come to you | `guard on` (ask) |
| Stop | **Request vs. diff** | Does this turn's diff miss part of the request, or include unrelated edits? If so, Claude is sent back once to finish, revert, or explain | `guard on` (stop) |
| PostToolUse: Bash | **Usage report** | When Claude ran `decide.py` or the browser runner, shows what Jev did: calls, items, time, cost | Always |

**One policy for every check:**

| Jev's probability | What happens |
|---|---|
| 0.8 or above, a problem | **Blocked**; Claude sees which rule, and why, and corrects itself |
| 0.5 to 0.8 | **You are asked** |
| Below 0.5 | Allowed, and you see the `⚖ … OK` line |

- **Read-only commands skip the check:** `ls`, `cat`, `grep`, `git status`, `git log`, `git diff` and similar, as long as there's no redirect, `-delete`, `-exec` or `sed -i`.
- **One call per check:** all of a check's questions go in a single Jev call.

### 4.4 Browser testing (`scripts/browser_steps.mjs`)

```bash
node browser_steps.mjs --url http://localhost:3000 \
  --steps "Open the sign-in page" "Fill the work email with dana@acme.io" "Submit the login form" "Verify the page shows Welcome"
```

It runs plain-English test steps in real Chrome. Each time it looks at the page, **one** Jev call checks four things together:
- is the step already done?
- is the page still loading?
- is something blocking it, like a cookie banner, modal or login wall?
- which element performs the step?

What it handles by itself:
- **Blockers:** it dismisses cookie banners and modals.
- **Look-alike elements:** it picks "Sign in" over "Start free trial".
- **Field labels:** it maps a step's wording to differently labelled fields ("work email" → "Company email").
- **Loading and menus:** it waits out spinners, opens menus to reach hidden items, and recovers after a wrong but harmless click.
- **Risky clicks:** delete, pay, send, transfer and publish need confidence 0.8. Ordinary clicks act from 0.6, because the next check catches a mistake.

**Exit codes:** 0 = all passed, 1 = a verify step failed, 3 = unsure; the page's elements and text are printed so Claude can do that step. `--cdp http://127.0.0.1:9222` attaches to an already-open Chrome.

**Requires:** Node 18+, `npm i playwright-core`, and Chrome.

### 4.5 Recipes for the other skills

[`references/use-cases.md`](references/use-cases.md) holds about 80 ready-made questions and thresholds, in one file so they're easy to review and tune.

| Area | What Jev decides |
|---|---|
| Skill routing | Which skills apply to a request (one yes/no per skill, one call) |
| ponytail | Commit, hand off or discard each leftover; debug-only code; deferred promises; commit message quality |
| memory | Durable? Can it be worked out from the code? Already recorded? Which `MEMORY.md` it belongs in; stale facts; your preferences |
| codebase-guardian | Follow the existing pattern or change it; how far a change spreads; which stack; "did my change break this test?"; silencing an error instead of fixing it |
| schema-aware-db | Real table usage vs. grep noise; read vs. write; migration risk and table-lock time; missing indexes; NoSQL key fit |
| teammates | Which agent takes a work item; whether a task is worth splitting; how many agents; conflicting results before merging |
| agents-dox / lsp | Full vs. verify-only `AGENTS.md` update; the nearest owning `AGENTS.md`; which symbol you meant; which references are calls; whether a rename is safe |
| Testing and browsers | Which element to click; blockers, errors and loading; step outcomes; acceptance criteria; form fields; flaky vs. real; affected end-to-end flows; test coverage |
| Git, CI and security | Merge-conflict sides; splitting commits; cherry-picks; commit and changelog types; breaking changes; secrets in diffs; deploy gates; triaging security findings |
| General | Intent and model routing; log root cause; checking claims against sources; prompt injection; deduplication; stale docs; effort estimates; spotting ambiguous requests |

For building Jev into **your own app**, see [`references/building.md`](references/building.md), condensed from TypeSafe's official skill.

## 5. Providers, base URLs and API keys

| Preset | Base URL | Model | Key variable |
|---|---|---|---|
| `typesafe` | `https://api.typesafe.ai` (or `$TYPESAFE_BASE_URL`) | `jev-latest` (or `$TYPESAFE_DEFAULT_MODEL`) | `TYPESAFE_API_KEY` |
| `openrouter` | `https://openrouter.ai/api` | `~typesafe/jev-latest` | `OPENROUTER_API_KEY` |
| `openjev` | `https://api.openjev.sh` | `openjev` | `OPENJEV_API_KEY` |
| `litellm` | `http://localhost:4000/typesafe` | `jev-latest` | `LITELLM_API_KEY` |

```bash
decide.py provider list                                         # every provider, the default marked, keys masked
decide.py provider add mygw --base-url https://gw.example.com --api-key-env MYGW_KEY --default
decide.py provider edit openjev --base-url https://api.openjev.sh --model openjev
decide.py provider edit openjev --api-key …                     # store the key itself
decide.py provider use typesafe                                 # switch the default
decide.py provider remove mygw                                  # presets can be edited, not removed
decide.py models --provider typesafe
```

- **Where config lives:** `~/.config/decision-maker/providers.json`, outside every repo, written with mode 600. Change the location with `$DECISION_MAKER_CONFIG`.
- **Key storage:** `--api-key-env` stores only the variable's name, which is the preferred way; `--api-key` stores the key itself.
- **Which providers work:** any gateway that speaks the System One format, `POST {base_url}/v1/systemone` with Bearer auth.

## 6. Privacy: what is sent, and when

| Feature | Sent to the provider | When |
|---|---|---|
| Nothing configured | Nothing | — |
| `decide.py ask` (by you or Claude) | The state and the questions | Only when it's run, and you see a line each time |
| Prefetch | Your prompt, then repo file contents (first 4,000 characters per file, up to 1,000 files) | Only for prompts Jev judges to be find tasks, in auto mode |
| Rules from your prompts | Your prompt | Each prompt, with `guard on` |
| Rules / scope / risky | Your recent prompts and the proposed edit or command | Each edit or shell command (not read-only commands), with `guard on` |
| Decide-don't-ask | Your request and Claude's question with its options | With `guard on` |
| Request vs. diff | Your request and this turn's diff of the edited files | End of a turn that edited files, with `guard on` |
| Browser runner | Each page's visible element list and text (up to 2,500 characters) | When it's run |

- **Prefetch never sends** `.env*`, keys or certificates (`*.pem`, `*.key`, `id_rsa`…), files whose names contain secret, credential, password or token, vendored and build folders, binaries, or files over 200 KB.
- **Turning it all off:** `decide.py guard off` stops every automatic feature, and `decide.py mode manual` stops the per-prompt call.

## 7. Command reference

| Command | Purpose |
|---|---|
| `/decision-maker:jev [auto\|manual\|on\|off\|features]` | Status, what's sent, recent activity, and switches |
| `/decision-maker:decision-maker` | Load the skill, which tells Claude how to use Jev |
| `decide.py ask …` | Ask typed questions: `--state`, `--state-file`, stdin, `--noul`, `--choice`, `--score`, `--questions`, `--items`, `--brief`, `--where`, `--min-confidence`, `--provider`, `--base-url`, `--api-key`, `--model`, `--retries`, `--timeout`, `--dry-run` |
| `decide.py models [--provider P]` | List the provider's models |
| `decide.py provider list\|add\|edit\|remove\|use` | Manage providers (section 5) |
| `decide.py mode [auto\|manual]` | Show or set how Jev is used |
| `decide.py guard on [rules scope ask stop prefetch]` | Turn on hook features. With no list it turns on the four per-edit checks and keeps prefetch as it was |
| `decide.py guard off` | Turn every automatic feature off |
| `decide.py guard status` | Mode, features, provider, prompt rules, and what is sent |
| `decide.py guard log [-n 20]` | Recent interventions |
| `decide.py guard replay [--act X] [--concern Y]` | Re-score past guard decisions under other thresholds, with no new Jev calls |
| `decide.py usage [--hours 24] [-n 10]` | Every Jev call: who, how many, time, tokens, cost |
| `node browser_steps.mjs …` | Browser test steps (section 4.4) |

**Exit codes** for `decide.py`: 0 = ok, 1 = API or network error, 2 = not configured or bad input. Callers treat any non-zero exit as "no decision; use your own judgment".

## 8. Configuration and environment variables

| Variable | Default | Effect |
|---|---|---|
| `TYPESAFE_API_KEY`, `OPENJEV_API_KEY`, `OPENROUTER_API_KEY`, `LITELLM_API_KEY` | — | Provider keys, read when set as the provider's `api_key_env` |
| `TYPESAFE_BASE_URL`, `TYPESAFE_DEFAULT_MODEL` | `https://api.typesafe.ai`, `jev-latest` | Override the `typesafe` preset |
| `DECISION_MAKER_CONFIG` | `~/.config/decision-maker/providers.json` | Config file location; logs sit next to it |
| `DECISION_MAKER_PROVIDER` | the configured default | Provider to use |
| `DECISION_MAKER_MODE` | the configured mode | `auto` or `manual`, overriding the stored choice |
| `DECISION_MAKER_GUARD` | the configured features | For example `rules,stop` or `all` (`all` doesn't include prefetch), overriding the stored features |
| `DECISION_MAKER_ACT` | `0.8` | Confidence at which an answer is acted on, or an action blocked |
| `DECISION_MAKER_CONCERN` | `0.5` | Probability from which the guard asks you |
| `DECISION_MAKER_CLICK_ACT` | `0.6` | Browser runner: confidence needed for an ordinary click |
| `DECISION_MAKER_PREFETCH_MAX` | `1000` | Maximum files scanned per prefetch |
| `DECISION_MAKER_HINT` | `1` | `0` stops the SessionStart command hint |

Files next to the config: `guard.log` (decisions), `usage.log` (every Jev call), `sessions/` (per-session prompts, prompt rules and edited files), and `notified.json` (when you were last shown the status).

## 9. Measured results

All runs used OpenJEV on 2026-10-03, and Claude Code ran as `claude -p` with Sonnet, 2 runs each. The scripts are in `scripts/`, so you can rerun them.

**Browser testing** (`scripts/bench_browser/`): a 6-step sign-in flow with a cookie banner, look-alike buttons, a field labelled differently from the step, a spinner and a hidden account menu.

| Mode | Time | Passed | Claude cost | Turns | Context tokens |
|---|---|---|---|---|---|
| Claude drives Chrome itself | 49.6 s | 2/2 | $0.129 | 13.5 | 277k |
| **Claude + browser runner** | **20.7 s (2.4× faster)** | 2/2 | **$0.043 (−67%)** | **2** | **36k (−87%)** |
| Runner alone (CI) | **11.8 s (4.2× faster)** | 2/2 | $0 | 0 | 0 |

**Semantic file search** (`scripts/bench_claude_code.py`):

| Task | Plain Claude | Jev as a tool call | **Prefetch** (auto mode, no hint in the prompt) |
|---|---|---|---|
| 100 files: which do refunds? | 8.8 s · $0.052 · 3 turns · recall 0.78 | 9.4 s · $0.045 · 2 turns · 1.00 | **6.5 s (−26%) · $0.031 (−40%) · 1 turn · 1.00** |
| 300 files: same | 9.3 s · $0.055 · 3.5 turns · recall 0.67 | 9.9 s · $0.045 · 2 turns · 1.00 | **7.5 s (−19%) · $0.031 (−44%) · 1 turn · 1.00** |
| 80 lines of one small file | 7.3 s · $0.052 · 2 turns · recall 0.90 | 10.3 s · $0.051 · 2.5 turns · 1.00 | 10.7 s · $0.056 · 2 turns · 1.00 |

Precision was 1.00 for the final versions. For one small file Claude still reads it to double-check, so plain Claude is about as good there.

**Accuracy and guard precision:**

| Eval | Result |
|---|---|
| `eval_usecases.py`: every recipe plus 13 borderline cases | 72/73 correct; acted on 90% of answers and was never wrong when it acted; median 0.55 s per call; $0.001 total |
| `eval_guard.py`: 26 rule and scope cases, 78 trials | 0 false alarms, 0 misses, 0 harmful blocks |
| Real log replayed under the old vs. new threshold | Questions to you dropped from 9 to 3 |
| Guard end-to-end | About 0.5–1 s per checked edit; +20–40% Claude cost on a task where it intervenes |

The use cases were written by the author, so real-world accuracy will be lower. Add your own cases and rerun.

## 10. Tuning and evaluation

- **Questions and thresholds live in one place:** at the top of `scripts/guard.py` (`Q_*`, `C_*`, `ACT`, `CONCERN`), and in `references/use-cases.md` for the recipes.
- **Try thresholds on your own history** with `decide.py guard replay --act 0.85 --concern 0.6`. No new Jev calls are made.
- **Rerun the evals:**
  - `python3 eval_usecases.py` checks the recipes;
  - `python3 eval_guard.py --variants v0,v1 --reps 2` compares guard question wordings;
  - `python3 bench_claude_code.py --reps 2` measures Claude Code token cost with and without Jev;
  - `cd bench_browser && npm i playwright-core && python3 bench_browser.py 2` benchmarks browser testing.
- **Unit tests:** `cd scripts && python3 -m unittest test_decide test_guard`. There are 51 tests against a local fake server; no key or network is needed.

## 11. Safety, failure behaviour and limits

**Safety:**
- **It never blocks your work:**
  - with no key, nothing runs;
  - on any API error or timeout, the hooks stay out of the way and you see `⚖ Jev unavailable …`;
  - `decide.py` exits non-zero and Claude continues on its own judgment.
- **Nothing destructive happens on a low-confidence answer.** Risky commands always come to you, and answering Claude's questions never covers your preferences, credentials, money, or anything irreversible.
- **Loops are impossible:** the end-of-turn check sends Claude back at most once per turn.

**Known limits:**
- At most 40 rules are checked per action.
- From rule files, only bullet-point lines count as rules.
- The end-of-turn diff check covers only files changed through edit tools, not files changed by shell commands.
- The browser runner's first click on a scope-ambiguous item can be wrong. For example, it may click "Settings" for "account settings"; it recovers through the "is it done?" check.
- Jev reads text only, so screenshots aren't used.
- On small inputs Claude can read cheaply, Jev adds overhead. Let Claude decide those.

## 12. Files in this plugin

```
decision-maker/
├── SKILL.md                 how Claude uses Jev (batch, browser, rules, decide-don't-ask)
├── commands/jev.md          /decision-maker:jev
├── hooks/hooks.json         SessionStart, UserPromptSubmit, PreToolUse, PostToolUse(+Failure), Stop → guard.py
├── references/
│   ├── use-cases.md         about 80 recipes and thresholds for every skill and general coding
│   ├── guard.md             the hooks in depth
│   ├── providers.md         provider management
│   ├── api.md               System One wire format, limits, errors
│   └── building.md          building Jev into your own app (from TypeSafe's MIT skill)
└── scripts/
    ├── decide.py            stdlib-only client and CLI (ask, items, providers, mode, guard, usage)
    ├── guard.py             all the hooks
    ├── browser_steps.mjs    browser test-step runner
    ├── eval_usecases.py · eval_guard.py · bench_claude_code.py · bench_browser/
    └── test_decide.py · test_guard.py
```

Credits: Jev and the System One API are by [TypeSafe AI](https://typesafe.ai); see the docs at https://docs.typesafe.ai. `references/building.md` is condensed from [typesafe-ai/skills](https://github.com/typesafe-ai/skills) (MIT). OpenJEV is an independent gateway and is not affiliated with TypeSafe.
