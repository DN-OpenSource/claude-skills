# product-visionary

A visionary product manager for your codebase. It tells you what the product is for, where it stands, and how every feature connects to that goal. Then, if you let it, it fixes and improves the product.

## What this does

- **Goal:** works out what the product is for and who it serves. On the first run it asks you to confirm.
- **Where we are:** which features are built, half-built, broken, or missing.
- **Feature map:** how each feature depends on the others and contributes to the goal, and which ones are dead or orphaned.
- **Catches what you missed:** every session runs a professional review (secrets, dependencies, privacy, data loss, accessibility, performance, docs, releases, CI, observability, licensing, platform support). Only evidenced gaps are raised, at most 5 a session; secrets are never quoted and security or licensing fixes are never applied without your yes.
- **Real issues:** runs [`test-report`](../test-report/SKILL.md) on the key features (2 positive + 1 negative test each).
- **Decisions by debate:** a panel of **3, 6, or 9** Claude agents argues each decision from different viewpoints (user advocate, engineer, skeptic, and others) and reaches a conclusion by vote. Size grows with the decision: 3 for small fixes, 6 for features, 9 for direction.
- **Memory between sessions:** `PRODUCT.md`, `docs/product/roadmap.md`, and an append-only `docs/product/decisions.md` record the goal, the map, the plan, and every decision with its winning argument and strongest dissent.
- **A product page:** every session also writes one self-contained HTML page with the goal, status, feature map, roadmap and decisions, in light and dark. It goes in `docs/product/index.html`, or in your GitHub Pages site as `product/` if you have one. Example: [this repo's product status](https://dn-opensource.github.io/claude-skills/product/). At the end of every session the skill prints the page's full path and the command to open it. The page is rebuilt from `docs/product/product.json` after every decision or state change, and a Stop hook catches a missed rebuild: it never writes, it just asks Claude to re-render in a visible turn.
- **Checks what actually runs:** besides the test suite, it runs each real entry point (hooks, CLI, start script) once on your machine, and waits for CI before merging.

## Where to find your product page

| Your project | The page is at |
|---|---|
| No website folder | `docs/product/index.html` |
| A GitHub Pages / site folder (`site/`, `docs/`, `public/`) | `<site folder>/product/index.html`, linked from the site's home page — and live at `https://<owner>.github.io/<repo>/product/` once deployed |

It's one self-contained file: open it in any browser (`start` on Windows, `open` on macOS, `xdg-open` on Linux). In **report only** the file is written but not committed; in the other modes it arrives with the end-of-session state PR.

## The four modes

You choose at the start of every session:

| Mode | What it does |
|------|-------------|
| **1. Report only** | Goal, state, feature map, tests, ranked issues. No code changes. |
| **2. Fix on a branch** | Fixes the top 3 items on branches and opens PRs. You merge. |
| **3. Full auto** | Fixes, improves, and builds features; proves each with tests; merges; keeps going in batches of 3. Asks before deleting a feature, changing the goal, touching payments/auth/secrets, migrations, or force-push. |
| **4. Complete auto** | Like 3, but asks nothing. Your mode choice is the only permission. |

Even in complete auto, every change goes through its own branch and PR (so any merge can be reverted), the default branch is never force-pushed, and secrets are never written out. An end-of-session report lists every change, PR, test result, and decision so you can verify the session.

## Works with

- [`test-report`](../test-report/SKILL.md) — finds issues and proves fixes. Optional: without it, the same rules are followed inline.
- [`teammates`](../teammates/SKILL.md), [`codebase-guardian`](../codebase-guardian/SKILL.md) — optional companions for the panel and for safe edits.

## What it won't do

- Install a test framework without asking, in any mode.
- Merge something its tests didn't prove — that PR stays open.
- Merge past branch protection or required review.
- Run more than 5 batches in one session.

## Details

See [SKILL.md](SKILL.md) for the session flow, [references/panel.md](references/panel.md) for the debate protocol, [references/templates.md](references/templates.md) for the state files and end report, and [references/page.html](references/page.html) for the product page template.
