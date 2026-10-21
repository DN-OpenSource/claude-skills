# The panel (3-6-9)

Decisions are argued by a panel of Claude agents, not made by one.

| Size | Used for |
|------|----------|
| **3** | Ranking each batch; small calls (a bug fix, which failure first) |
| **6** | Medium — how to build a feature, a refactor |
| **9** | Direction — cutting a feature, changing the goal |

## Viewpoints

Take the first N, in this order, so a 3-panel always has the core tension.

1. **User advocate** — what users actually feel and need; friction, confusion, broken promises.
2. **Engineer** — feasibility, cost, maintainability; what this will take and what it breaks.
3. **Skeptic** — argues against the leading option; hunts for what everyone is missing.
4. **Quality / reliability** — failure modes, test coverage, what breaks in production.
5. **Business / growth** — does it move the product's success metric; adoption, retention.
6. **Security & risk** — data, auth, abuse, irreversibility.
7. **Simplicity** — what can we *not* do; the smallest change that gets the outcome.
8. **Long-term architecture** — does this paint us into a corner in a year.
9. **Newcomer** — would a first-time user or developer understand it.

## Spawning

Use the Agent tool with `subagent_type: general-purpose`. Spawn **every member of a round
in one message** so they run in parallel. Each gets the same brief plus its viewpoint.
Members may read the repo to check claims; they never edit files (the prompts say so).
Keep the brief's feature map to the rows that matter for the question.

**The brief:**
```
Goal: <from PRODUCT.md, note if unconfirmed>
Feature map: <table>
Test results: <summary line + failures from the test report>
Question: <what is being decided>
Candidates: <id — one line each>
Mode: <1-4>  (always-ask list applies in modes 1-3)
```

**The position each member returns:**
```
picks: [ranked candidate ids]   (one id for a how-to-build question)
reason: <2-4 sentences from your viewpoint>
would change my mind if: <one line>
veto: none | <always-ask item this touches>
```

## Rounds

**Round 1 prompt:**
> You are the <viewpoint> on a product panel. <viewpoint one-liner>. Read the brief and
> return your position in the exact format. Argue from your viewpoint; don't hedge.
> You may read the repo to check claims. Do not edit, create, or delete any file. Never quote secret values.
> <brief>

**Round 2 prompt:**
> You are the <viewpoint>. Here are every member's Round 1 positions, verbatim. Revise,
> rebut, or hold — say which and why. Return your position in the exact format.
> Do not edit, create, or delete any file. Never quote secret values.
> <brief> <all Round 1 positions, verbatim>

**Tie round prompt:**
> You are the <viewpoint>. The panel is split between exactly two options: <A> and <B>.
> Here are all positions so far, verbatim. Pick one and give the single strongest reason.
> Return `pick: A|B`, `reason:`, `veto:`. Do not edit, create, or delete any file. Never quote secret values.

## Conclusion

- **Scoring:** ranked picks score 1st = 3 pts, 2nd = 2, 3rd = 1; top scores fill the slots.
  A candidate is **worth doing** only if more than half the members picked it at all. The
  loop's "nothing worth doing" stop means no candidate clears that bar.
- **Clear after Round 1** — more than two thirds of members picked the same set (or, for a
  single-answer question, the same answer): skip Round 2.
- Otherwise run Round 2 and score again. **Majority** = the winning option is picked by
  more than half the members.
- **No majority, or a tie that changes which items are picked** → a tie round on the
  **top two**. A tie that only changes the order of items all picked anyway isn't a tie —
  order them by first-place votes.
- **Still tied** → modes 1–3: ask the user, showing both sides. Mode 4: take the option
  ranked higher in the skeptic's picks (the one the skeptic objected to least), and log
  it as a tie-break.

## Veto

Any member may flag `veto: <item>` when a pick touches the always-ask list. A veto raised in
**any** round counts, even if withdrawn later — the always-ask list is the user's call.
- Mode 1: mark the roadmap item "needs user OK: <item>" and list it in the end report.
- Modes 2–3: a veto stops that item until the user answers, and stops the loop in 3.
- Mode 4: logged and highlighted in the end-of-session report; work continues.

## Logging

Write the decision to `docs/product/decisions.md` **before acting**, with status `in progress` (mode 1: `proposed`): question, panel size, final pick, vote
count, the winning argument, the strongest dissent. Update the status to `done`,
`awaiting user merge`, or `failed` (with the reason) after. Format: `references/templates.md`.
