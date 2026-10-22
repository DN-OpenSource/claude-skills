"""product-visionary's professional review: evidence-only, capped, safe with secrets.

Run: python -m pytest scripts/test_professional_review.py -q
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = (ROOT / "skills" / "product-visionary" / "SKILL.md").read_text(encoding="utf-8")
REVIEW = (ROOT / "skills" / "product-visionary" / "references" / "professional-review.md").read_text(encoding="utf-8")


def test_review_positive_skill_runs_it_every_session():
    assert "references/professional-review.md" in SKILL
    assert "Professional review" in SKILL


def test_review_positive_covers_the_areas_a_professional_checks():
    for area in ("Secrets", "Dependencies", "Privacy", "Errors & data loss", "Accessibility", "Performance",
                 "Docs & onboarding", "Release & versioning", "CI & tests", "Observability", "Licensing",
                 "Platform support"):
        assert f"**{area}" in REVIEW, area
    for rule in ("Evidence or it isn't a finding", "At most 5 gaps", "not checked", "Never quote a secret",
                 "never auto-fixed"):
        assert rule in REVIEW, rule


def test_review_negative_never_marks_unrun_checks_fine_or_fixes_secrets():
    assert "record the area as `not checked`, never as `fine`" in REVIEW
    for bad in ("rotate the key automatically", "git filter-repo", "push --force", "print the secret"):
        assert bad not in REVIEW, bad
