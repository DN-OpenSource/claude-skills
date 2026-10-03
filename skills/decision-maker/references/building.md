# Building Jev into the user's app

Use this when the user's *product* needs typed judgments, not when the coding session does. It is condensed from TypeSafe's official agent skill ([typesafe-ai/skills](https://github.com/typesafe-ai/skills), MIT, © 2026 TypeSafe AI). If you also have that plugin, follow the live docs where the two disagree.

## 1. Read the live docs first

The docs are the source of truth, and this file only gives direction. Start at https://docs.typesafe.ai/llms.txt and fetch only the pages you need; append `.md` to any page path to get Markdown. Before writing integration code, read:

- the API page or the SDK page for the stack in use;
- the primitive pages the design relies on;
- **the closest cookbook**, which often decomposes the problem better than a generic classifier would.

A stale skill or memory is the usual reason an agent invents request fields.

## 2. Find the shape

Work backward from what the app must show, select, change or hand off, to the judgments it needs. Exact rules, calculations, lookups and execution stay in code; Jev supplies the semantic common sense. Keep the user's stack and scope.

| Pattern | Use when | Cookbook |
|---|---|---|
| Route and fill arguments | a request picks a handler and its typed parameters | `function_calling`, `patterns/fan-out` |
| Select, don't generate | candidate values or spans can be found in code; Jev picks one; code copies it verbatim | `pre_parsed_value_extraction_cookbook`, `autoformat` |
| Find and judge evidence | retrieve candidates, then rank or filter them by relevance | `rerank_typesafe`, `hierarchical_classification` |
| Judgments as reusable data | score dimensions once, and let weights or filters change in code without re-running inference | `patterns/composite-scoring`, `autoresearch_feature_discovery` |
| Verify and escalate | check claims or fields against evidence; send failures to a human or a reasoning model | `citation_check`, `sde_cascade` |
| React to changing state | code keeps goals and observations; fresh judgments pick the next bounded step | — |

## 3. Design each judgment

- **Choice** picks one of a defined set. Add a no-match option when nothing may fit.
- **Noul** answers whether a condition holds. Use one per label when several labels can apply at once.
- **Score** places something on described, ordered levels. Each level must describe a concrete situation on its own.
- Put enough **state** in for the question to be answerable: source text, identities, relationships, policies and current facts. Prefer named JSON fields, and reference them with backticks (`` `ticket.messages[0].text` ``).
- Ask **one narrow judgment per question**, with the complete meaning in `instructions` and the possible answers in `criteria`. Ids are never sent to the model. Use structured instructions or criteria (definitions, contrasts, exclusions, examples) when plain strings are ambiguous. That is what fixed this repo's guard false alarms; see `scripts/eval_guard.py`.
- **Check candidate coverage:** the model cannot pick a value you left out.

## 4. Compose and verify

- **Batch** the independent questions about one state in one request, including speculative ones. State each speculative premise explicitly, and let code use only the answers it needs. Make a second request only when an earlier answer decides which evidence to fetch or which options come next.
- **Confidence measures how concentrated the distribution is, not permission to act.** A noul near 0.5 means "could be either", not "medium". When several answers are acceptable, low confidence is harmless for preference choices. Ignore uncertainty on branches you don't use.
- **Keep policy explicit:** weighted scores suit trade-offs, while "any serious violation" needs separate conditions. Store the raw judgments so you can re-tune thresholds without new calls (see `decide.py guard replay`).
- **Typed output guarantees the interface, not the truth.** Evaluate thresholds on the user's own cases and consequences; cookbook thresholds are examples. When something fails, check separately whether the evidence was missing, the model was wrong, the code was wrong, or the service failed.
- **Put questions and thresholds in one constants file** so a reviewer finds them quickly, and keep API keys server-side.
