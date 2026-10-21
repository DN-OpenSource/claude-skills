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
**Mode:** <1-4> · **Batches:** <n> · **Stopped because:** <single batch (modes 1-2) | no PR/merge available | nothing left | unproven item | veto | 5 batches>

| # | Item | Kind | PR | Tests | Decision |
|---|------|------|----|-------|----------|
| 1 | <item> | fix / improvement / feature | <link> | ✅ 3/3, no new failures | D-12 |

**Pre-existing failures** (in the baseline, not caused by this session): <list or none>
**Logged instead of asked** (mode 4 only): <vetoes, tie-breaks, unconfirmed goal, always-ask items>
**Left open:** <unmerged PRs and why>
**Files left uncommitted** (mode 1 only): <paths>
**Next on the roadmap:** <top 3>
```
