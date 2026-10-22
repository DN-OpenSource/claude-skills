# Professional review

What a professional product owner checks even when nobody asks. Run it every session, right after
**Understand**, in every mode. It is read-only: it reads files and runs read-only commands.

## Rules

- **Evidence or it isn't a finding.** Every gap names what you saw: a file and line, a command and
  its output, or a missing file. "Probably", "might", "best practice says" are not evidence.
- **Only what matters here.** Skip areas that don't apply (no UI → no accessibility check) and say
  "not applicable". Rank gaps by risk to *this* product's goal, not by how generic they are.
- **Known gaps aren't news.** A gap already on the roadmap is re-checked and its status updated,
  but it only becomes a new candidate if it got worse or the user asked about it.
- **At most 5 gaps become candidates per session.** The rest go to the roadmap as Deferred with
  their evidence, so nothing is lost and the panel isn't flooded.
- **Record every area** in `PRODUCT.md` under **Professional review** as `fine`, `gap`,
  `not applicable` or `not checked`, with a one-line reason. Next session re-checks all of them,
  not just old gaps, so a new problem is never missed.
- **Never quote a secret.** A secrets finding names the file, the line and the kind of secret
  ("AWS access-key pattern in `config/prod.env:12`"), never the value. These notes are committed
  and may be published.
- **No running, installing or network without asking.** A check that would run project code,
  install anything, or reach the network (`npm audit`, `pip-audit`, a build) is asked first in
  modes 1–3. In mode 4, or with no answer, record the area as `not checked`, never as `fine`.
- **Security and licensing gaps are flagged, never auto-fixed**, in any mode. No rotating keys,
  deleting files, re-licensing or rewriting history without the user's explicit yes: propose the
  fix on the roadmap and list it under "Needs your attention" on the product page.

## Areas

| Area | Check (read-only) | Evidence of a gap |
|------|-------------------|-------------------|
| **Secrets** | `git ls-files` for `.env`, `*.pem`, `id_rsa`, credentials files; grep tracked files for key patterns (AKIA…, `-----BEGIN … PRIVATE KEY`, `xox[bp]-`, `ghp_`, `sk-`) | a tracked secret file or a matching line (file:line + kind only) |
| **Dependencies** | lockfile present and committed; versions pinned; obviously abandoned or duplicate packages | no lockfile, `*` / `latest` ranges, a manifest without its lock |
| **Privacy & data** | what personal data is stored or logged; is there a retention or deletion path | PII written to logs, no way to delete a user's data |
| **Errors & data loss** | unhandled errors on write paths, silent `except: pass`, no backup or undo for destructive actions | a write path with no error handling, a delete with no confirmation |
| **Accessibility** (UI only) | images without alt text, inputs without labels, colour-only state, no keyboard focus | a specific element or component |
| **Performance** | obvious N+1 loops, unbounded queries, huge bundles, blocking work on the main path | the loop/query/file and why it's unbounded |
| **Docs & onboarding** | README says what it is, how to install, how to run, how to test; examples work | a missing step, or a documented command that fails |
| **Release & versioning** | version source of truth, changelog or release notes, tags match versions | versions out of sync, no release notes for shipped changes |
| **CI & tests** | CI exists and runs the tests; critical paths have tests; tests run on the platforms users use | no CI, a critical feature with no test, a supported OS never tested |
| **Observability** | errors are logged or reported somewhere a maintainer will see | failures that vanish (no log, no report, no exit code) |
| **Licensing** | a LICENSE file; dependencies' licences compatible with it | no LICENSE, or a copyleft dependency in a permissive project |
| **Platform support** | the platforms the README promises are the ones actually exercised | a promised OS/runtime/browser nothing checks |

## Output

1. `PRODUCT.md` → **Professional review**: one line per area (`fine` / `gap` / `not applicable` /
   `not checked` — reason).
2. Up to 5 gaps → candidates for the ranking panel, each with its evidence line and the part of the
   goal it threatens.
3. The rest → roadmap **Deferred**, with evidence.
4. `product.json` → gaps the user must decide on (security, licensing, anything always-ask) go in
   `roadmap.openQuestions`, so the product page shows them under **Needs your attention**.
