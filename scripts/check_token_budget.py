#!/usr/bin/env python3
"""Guard against skill descriptions growing the eager per-session token cost.

Every SKILL.md `description:` is loaded into context at the start of *every*
session, whether or not the skill runs. This check fails (exit 1) if any skill
or the total exceeds budget, so token consumption can't creep up unnoticed.

Run: python scripts/check_token_budget.py    (also runs as the repo's test)
Tokens are estimated as ceil(chars/4) — good enough to catch regressions.
"""
import sys
from pathlib import Path

PER_SKILL = 260      # max tokens for one skill's description
TOTAL = 1200         # max tokens for all descriptions combined (8 skills)

def est_tokens(s: str) -> int:
    return -(-len(s) // 4)  # ceil

def description(skill_md: Path) -> str:
    # frontmatter description is a single line: `description: ...`
    for line in skill_md.read_text(encoding="utf-8").splitlines():
        if line.startswith("description:"):
            return line[len("description:"):].strip()
    return ""

def measure(root: Path):
    rows = []
    for md in sorted(root.glob("skills/*/SKILL.md")):
        rows.append((md.parent.name, est_tokens(description(md))))
    return rows

def check(root: Path) -> list[str]:
    rows = measure(root)
    errors = []
    for name, tok in rows:
        if tok > PER_SKILL:
            errors.append(f"{name}: {tok} tok > {PER_SKILL} per-skill budget")
    total = sum(t for _, t in rows)
    if total > TOTAL:
        errors.append(f"total: {total} tok > {TOTAL} budget")
    return rows, errors

def main():
    root = Path(__file__).resolve().parent.parent
    rows, errors = check(root)
    for name, tok in rows:
        print(f"  {tok:4d} tok  {name}")
    print(f"  ----  total {sum(t for _, t in rows)} tok (budget {TOTAL})")
    if errors:
        print("\nTOKEN BUDGET EXCEEDED:", file=sys.stderr)
        for e in errors:
            print("  -", e, file=sys.stderr)
        sys.exit(1)
    print("OK: within token budget")

if __name__ == "__main__":
    main()
