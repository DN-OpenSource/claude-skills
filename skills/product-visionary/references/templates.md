# Templates

All files live at the root of the analysed project. Keep them short — they're read at the
start of every session.

## PRODUCT.md

```markdown
# <Product name>

**Goal:** <what it's for and who it serves — one or two sentences>
**Goal status:** confirmed by user on YYYY-MM-DD | unconfirmed (inferred, mode 4)
**Success looks like:** <the signal that the goal is being met>

## Where we are
<2-4 lines: what works end to end, what's half-built, what's broken. Link the latest
`test-reports/` file.>

## Feature map

| Feature | Status | Depends on | Used by | How it contributes to the goal |
|---------|--------|------------|---------|--------------------------------|
| login | built | users, sessions | every page | gate to everything; no login, no product |
| export-csv | half-built | orders | — | ⚠️ orphan — nothing links to it |
| legacy-api | built | — | — | ⚠️ dead — no callers since 2025 |

Flag with ⚠️ **orphan** (no entry point uses it) or **dead** (no callers / contributes
nothing to the goal).
```

Several products in one repo → one section per product (Goal, Where we are, Feature map
under a `## <product>` heading each).

### PRODUCT.md — Professional review section

```markdown
## Professional review — YYYY-MM-DD
| Area | Status | Evidence / reason |
|------|--------|-------------------|
| Secrets | fine | no tracked .env/keys; pattern scan clean |
| Licensing | gap | no LICENSE file at the root |
| Accessibility | not applicable | no UI |
| Dependencies | not checked | audit needs network; asked, no answer |
```

## docs/product/roadmap.md

```markdown
# Roadmap

## Fix
1. <item> — <one-line why> — <link to failing test / report>

## Build
1. <item> — <goal it serves>

## Cut
1. <item> — <why it doesn't earn its keep>

## Proposed features
- **<name>** — weight: small | medium | direction — serves: <part of goal> — connects to:
  <features> — panel: <votes, e.g. 5/6> — strongest argument against: <one line>

## Open questions
- <question only the user can answer> — raised by <decision id>

## Rejected
- <item> — <user's reason> — YYYY-MM-DD   (never propose again unless the goal changes)
```

## docs/product/decisions.md

Append-only. Newest at the bottom.

```markdown
### D-<n> — YYYY-MM-DD — <question>
- **Status:** proposed (mode 1) | in progress | awaiting user merge | done | failed: <reason>
- **Panel:** <3|6|9> — <viewpoints> — rounds: <1|2|3>
- **Pick:** <decision>
- **Votes:** <score or count, e.g. 7/9; note "tie-break" if one was used>
- **Winning argument:** <one or two lines, attributed to its viewpoint>
- **Strongest dissent:** <one or two lines, attributed>
- **Veto:** none | <item> — asked user | logged (mode 4)
- **PR:** <link or branch>
```

## End-of-session report

Shown to the user at the end; also appended to `docs/product/decisions.md` as-is.

```markdown
### End-of-session report — YYYY-MM-DD
**Mode:** <1-4> · **Batches:** <n> · **Stopped because:** <single batch (modes 1-2) | no PR/merge available | nothing left | veto | 5 batches> · **Today's picks:** <done>/<picked> done, <n> awaiting merge, <n> failed

| # | Item | Kind | PR | Tests | Decision |
|---|------|------|----|-------|----------|
| 1 | <item> | fix / improvement / feature | <link> | ✅ 3/3, no new failures | D-12 |

**Pre-existing failures** (in the baseline, not caused by this session): <list or none>
**Logged instead of asked** (mode 4 only): <vetoes, tie-breaks, unconfirmed goal, always-ask items>
**Left open:** <unmerged PRs and why>
**Files left uncommitted** (mode 1 only): <paths>
**Next on the roadmap:** <top 3>
```

## Product page

`references/page.html` is the template (the "Classical" design: goal + health ring, needs-your-attention,
tabs for Overview / Tests / Features / Roadmap / Decisions, vote seats on a 3/6/9 scale, light/dark).
Write the data to `docs/product/product.json` and run `scripts/render_page.py --if-stale`; it
validates every field below, embeds the JSON safely and writes the page. Fields:

- `product` `{name}`, `repo`, `back` `{label, href}` (site home, or omit), `lastUpdated`
- `goal` `{text, confirmed: bool, note}`; `successCriteria` `[{text, state: met|not met|at risk}]`
- `health` `{score: 0-100, label, note}` — score = share of success criteria met (at risk counts half),
  minus 10 per open Fix item, never below 0; label On track (≥ 70) / Needs work (40–69) / At risk (< 40)
- `stats` `[{label, value, of?, unit?, note}]` — a bar shows `value / of`
- `sinceLastSession` `[{kind: added|changed|fixed|removed, text}]`
- `tests` `{total, passing, summary, rows: [{feature, polarity: positive|negative, name, status: pass|fail|flaky|blocked, video}]}`
  — `video` is text only: `local only` or `recording unavailable: <reason>`; never a path or link
- `features` `[{name, status: done|in progress|broken|planned, dependsOn: [], usedBy: [], servesGoal, flag: null|orphan|dead}]`
- `roadmap` `{lanes: [{name: Fix|Build|Proposed|Cut|Deferred, items: [{title, reason, weight: 1-3}]}], openQuestions: [{q, context}]}`
- `session` `{mode: 1-4, batches, stopReason}`
- `decisions` `[{id, title, status: accepted|vetoed|open|rejected, panel: 3|6|9, rounds, votes: {for, against, abstain},
  winning, dissent, viewpoints: [], veto: null|{by, reason}, pr: {label, url (https only), merged}}]`, newest first

"Needs your attention" fills itself from vetoes, open questions and unmerged PRs.
