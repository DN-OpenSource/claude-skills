# Guard hooks: rules, scope, and request vs. diff

The plugin ships `hooks/hooks.json`, which runs `scripts/guard.py`. **Defaults follow the mode you choose after install:** auto turns on prefetch; manual, or no choice yet, runs nothing automatically. The per-edit checks (rules, scope, ask, stop) run only after `decide.py guard on`. With no key, nothing runs. It fails open on any error, timeout, or missing key.

```bash
python3 decide.py guard on                 # all checks; or pick: guard on rules scope ask stop
python3 decide.py guard status             # shows what's on and whether the provider key resolves
python3 decide.py guard off
```

The hooks run in Claude Code's own environment. Export the provider key *before* starting `claude`, or store it with `provider edit NAME --api-key ...`.

| Check | When | Asks Jev | Confident problem | Unsure | Fine |
|---|---|---|---|---|---|
| `rules` | before Edit/Write/MultiEdit/NotebookEdit/Bash | Does the action violate each rule? Session rules from your prompts come first, then `AGENTS.md`/`CLAUDE.md` from the edited file's folder up to the repo root, then `.claude/CLAUDE.md`, `CLAUDE.local.md` and `~/.claude/CLAUDE.md`. For Bash, is it risky? | **deny**, and Claude sees which rule and corrects itself | **ask** the user | silent |
| `scope` | same | Is the action outside what the user asked for? | **deny** | **ask** | silent |
| `ask` | before AskUserQuestion | a Choice per question, plus "is this the user's own call?" | n/a | the question goes to the user | Jev answers, Claude proceeds and reports the pick |
| `stop` | when Claude is about to finish a turn that edited files | Does the diff miss part of the request? Does it include unrelated edits? | sends Claude back once (`additionalContext`, shown as *Stop hook feedback*, not an error), and Claude finishes, reverts or explains | silent | silent |

Read-only shell commands (`ls`, `cat`, `grep`, `git status/log/diff`, …, with no redirect, `-delete`, `-exec` or `sed -i`) skip the check entirely, because reading can't break a rule. All of a check's questions go in **one** request. Risky shell commands are never auto-denied, because the user always decides those. Thresholds: deny at `$DECISION_MAKER_ACT` (default 0.8). Ask you at `$DECISION_MAKER_CONCERN` (default 0.5), i.e. only when Jev leans toward a problem. Risky commands and "is this the user's own call?" ask from 0.3. The 0.5 default came from `scripts/eval_guard.py`: at 0.3, clean actions scoring 0.31–0.56 raised false alarms. With the shipped criteria, every clean case scored below 0.5 and every real violation 0.76 or higher (78 live trials: 0 false alarms, 0 misses). To try other thresholds against your own history, run `decide.py guard replay --act X --concern Y`; it re-scores the log without new calls. The question wording and constants are at the top of `guard.py`. Every decision is appended to `~/.config/decision-maker/guard.log`, so you can tune thresholds against real outcomes. The request comes from the `UserPromptSubmit` hook, with the transcript as a fallback, and the edited files from `PreToolUse`.

**Temporary rules from the conversation.** On every prompt (`UserPromptSubmit`), one Jev call does two things. It picks out sentences that are standing instructions about *how* to work ("don't touch the tests", "use pnpm", "no new dependencies"), as opposed to the task itself. It also checks whether the new prompt cancels or relaxes an earlier one ("you can edit tests now"). Rules are kept verbatim, as the sentences you wrote, never paraphrased. They last for the session (up to the 20 most recent) and are enforced like file rules; a deny names the source, e.g. "rule from your instruction this session". If Jev is unreachable, the existing rules are kept. `guard status` prints the active ones.

Limits: file rules are read as their bullet lines, and there are at most 40 rules in total, and the Stop check sees only files edited through Edit/Write tools this turn, not files changed by shell commands.

## What the user sees

Every intervention prints a `⚖ Jev guard (…)` line to the user (a hook `systemMessage`), separate from the reason Claude receives:

- **blocked**: the action, the rule and its source, and the probability; Claude was told to adjust.
- **needs you**: Jev was unsure, so Claude Code's own approval prompt follows.
- **answered for you**: which question Jev answered, with what, and at what confidence.
- **request vs. diff**: what was missing or unrelated; Claude was sent back once.
- **rules**: which prompt instructions are now enforced or no longer enforced.

Clean passes stay silent. `decide.py guard log [-n 20]` lists recent interventions; `guard status` shows the active session rules.

## Prefetch: Jev answers before Claude's first turn (on in auto mode)

On each prompt, the call that already handles your in-prompt rules also asks "is this a find/filter-files-by-meaning request?". If the answer is yes (≥ 0.8):

1. The hook scans the repo with Jev before Claude sees the prompt. It covers `git ls-files` plus untracked files: up to 1000 text files, the first 4,000 characters of each. Batches run in parallel, so 300 files take about 2 s.
2. If the prompt names one file and asks about its *lines*, each line is judged instead of each file.
3. Claude receives the confident hits, plus the unsure items with excerpts, as context.
4. You see `⚖ Jev guard (pre-scan): checked N items in Xs: H relevant, U unsure`.

Claude can then answer in **one turn with no tool calls**. On semantic file search this measured 26–30% faster and about 40% cheaper than plain Claude Code, with precision and recall at 1.00; see the README. On a single small file, Claude may still open it to double-check.

**Privacy:** prefetch sends file contents to the configured provider. It's on only if you choose auto mode (`/decision-maker:jev auto`) or name it (`guard on prefetch`), and the session notice says so. Turn it off with `decide.py guard off`, or choose features with `decide.py guard on rules stop …`. `guard on` with no arguments and `DECISION_MAKER_GUARD=all` cover only the per-edit checks; prefetch is added only when named, or kept as auto mode's default. It always skips `.env*`, keys and certificates (`*.pem`, `*.key`, `id_rsa`…), files with secret/credential/password/token in their name, vendored and build directories, binaries and files over 200 KB. Prompts that aren't find tasks cost only the shared prompt call. If anything fails, the hook stays silent and Claude works as usual.

