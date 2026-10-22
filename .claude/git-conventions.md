# Git conventions

## Commit message
Pattern: `<area>: <summary>` — area is the skill or part touched (`product-visionary`, `lsp`, `CI`,
`README`); a product-visionary decision may use its id instead (`D-12: …`).
Subject: one line, plain English, no trailing period. Body: why the change was needed and what it
proves (tests, evals), wrapped at about 72 characters.

## Branch name
Pattern: product-visionary items `pv/D-<n>-<short-slug>`, its state PRs `pv/state-YYYY-MM-DD`;
everything else `<short-kebab-slug>` (e.g. `product-page-classical`).

## Attribution
Hide Claude in commits and PRs: yes   (applied via settings `attribution` in ~/.claude/settings.json)

## Pull request
Title: same as the commit subject. Body: what changed and why, then the proof (tests, CI, evals);
product-visionary PRs include the decision entry. Draft: no.

## Protected branches
main — never commit or push to it directly; never force-push anything.

## Other
Sign-off: no. Merge style: squash, then delete the branch. Version bumps keep every manifest in
lockstep (checked by scripts/test_repo.py).
