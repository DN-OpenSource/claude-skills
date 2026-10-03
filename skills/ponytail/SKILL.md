---
name: ponytail
description: Wrap up a work session so nothing is left dangling. Use when the user says "wrap up", "tie up loose ends", "end of day", "before I go", "hand this off", or is leaving a task mid-flight — and at the natural end of any long coding session, even unprompted. Sweeps every loose strand (uncommitted/unpushed work, unlabeled stashes, debug prints and TODOs introduced this session, failing checks, half-done renames, promises recorded nowhere), ties each off (commit, push, clean, or hand off), and ends with one "session tail" report for the next session.
---

# Ponytail

A ponytail gathers loose strands and ties them into one tail. This skill does that for a work session: gather every unfinished strand, tie each one off, and leave a single tail the next session can pick up.

## Why this exists

Sessions rarely *end*; they *stop*. The user steps away, the context window fills, the container gets reclaimed. What's lost at that moment is never the finished work — it's the loose strands: the change that was never committed, the stash with no message, the `console.log` left behind, the "I'll fix that after lunch" that lives only in the conversation. The next session (or the next person) then spends its first hour on archaeology, or worse, never learns the strand existed.

The fix is a deliberate closing move: **sweep, sort, tie off — then leave the tail.** Run the moves in order; the sweep must be complete before anything is tied off, because the most expensive strand is the one you never noticed.

## When to use

| Cue | Action |
|---|---|
| "Wrap up" / "tie up loose ends" / "clean up before we stop" | Full run: sweep → sort → tie off → tail |
| "End of day" / "before I go" / "I have to run" | Full run, biased toward speed — preserve first, polish later |
| "Hand this off" / "write up where we are" | Full run, biased toward the tail — the report is the deliverable |
| A long session is clearly winding down | Offer a wrap-up; run it if accepted |
| Ephemeral environment near its end (remote container, CI session) | Full run unprompted — unpushed work here *evaporates* |

An empty sweep is a valid result. If nothing is dangling, say so in one line and stop — don't manufacture work to justify the run.

## The three moves

### 1. Sweep — find every strand

Enumerate before acting. Check each category and note what you find; skip a category only after actually checking it.

- **Working tree** — `git status --porcelain`: modified, staged, and untracked files. Untracked files deserve a look, not a reflex: a scratch script is debris, a new module is unfinished work.
- **Stashes** — `git stash list`. Any stash without a message is itself a loose end.
- **Unpushed commits** — `git log --branches --not --remotes --oneline`. Local-only commits are one reclaimed container away from gone.
- **Session debris** — in the diff of *this session's* changes (`git diff` plus untracked files), look for debug output (`console.log`, `print(`, `dbg!`, `debugPrint`), commented-out blocks, and TODO/FIXME/HACK markers you introduced. Pre-existing markers are not yours to sweep.
- **Broken or half-applied state** — if the project has a cheap check (tests, lint, build), run it. After a rename or refactor, search for the old name; leftovers are strands.
- **Conversation promises** — reread the session for "later", "for now", "temporarily", "in a follow-up". Anything promised but recorded nowhere durable is a strand.
- **Scratch files** — temp scripts, downloaded samples, generated output that doesn't belong in the repo.

### 2. Sort — give each strand a fate

Every strand gets exactly one of three fates:

- **Tie off now** — finishable in minutes and clearly in scope: commit it, push it, delete it, fix it.
- **Hand off** — real work that shouldn't happen now: preserve it (WIP commit or messaged stash) and record it in the tail with enough context to resume cold.
- **Discard** — debris with no future value: remove it, and list it in the tail so the removal is visible.

When a strand is ambiguous and the user is there, ask — one short question, not a quiz. When the user is *not* there, preserve rather than destroy: a WIP commit on the current branch beats a deletion you can't take back. The asymmetry matters — an over-preserved strand costs a minute later; a destroyed one can cost a day.

### 3. Tie off — act on each fate

- **Committable work** → coherent commits with messages that describe the change, not the moment ("Add retry to webhook client", never "wip" or "end of day"). Don't bundle unrelated strands into one commit. Push if a remote exists.
- **Unfinished work** → a WIP commit on the working branch, or `git stash push -m "<what and why>"`. Either way its location goes in the tail — preserved-but-unfindable is still lost.
- **Debris you introduced** → remove debug prints and commented-out blocks that came from this session; delete scratch files. Leave pre-existing debris alone (removing it is a change, and changes belong to a task, not a cleanup).
- **Promises** → into the tail. If the repo keeps durable context (`MEMORY.md`, a TODO tracker), record them there too.
- **Never** run `git reset --hard`, `git clean -f`, or delete files you didn't create this session without explicit confirmation. The wrap-up must be the safest part of the session, not the most dangerous.

## The tail

Finish with one report — in chat, as the final message of the wrap-up. Use this shape and drop any section with nothing in it:

```markdown
# Session tail — <date>

## Done & durable
<What was committed/pushed, with branch and short hashes.>

## Tied but unfinished
<Each WIP commit or stash: where it lives, what it is, what "done" looks like.>

## Follow-ups
<Each promise or deferred item: what, why deferred, where to start.>

## Discarded
<What was removed and why — one line each.>

## Watch out
<State the next session must know: a flaky test, a migration half-applied, a decision pending.>
```

The test of a good tail: someone with no memory of this session reads it and knows exactly where to start — no archaeology required.

## Companion skills (optional, never required)

If the **memory** skill is installed, fold durable facts from the tail into `MEMORY.md`; if **agents-dox** manages the repo, run its closing pass alongside this one; after a **teammates** run, ponytail is the natural final step once outputs merge. Without any of them, the tail in chat stands on its own. **codebase-guardian** closes out each change; ponytail runs once per session to catch what fell between changes. With **decision-maker** configured, the Sort move sends every strand in one call (a Choice over tie_off / hand_off / discard, `decision-maker/references/use-cases.md` §2). Apply a fate only when `act` is true. Otherwise ask, or preserve. Never discard on low confidence.
