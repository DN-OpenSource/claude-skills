"""git-conventions: settings changes are asked first and safe on old builds; no history rewriting.

Run: python -m pytest scripts/test_git_conventions.py -q
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = (ROOT / "skills" / "git-conventions" / "SKILL.md").read_text(encoding="utf-8")


def test_git_conventions_positive_file_covers_what_the_owner_asked_for():
    for must in ("Commit message", "Branch name", "Attribution", "Pull request", "Protected branches",
                 ".claude/git-conventions.md", "~/.claude/git-conventions.md"):
        assert must in SKILL, must


def test_git_conventions_positive_attribution_uses_native_setting_safely():
    assert '"attribution": {"commit": "", "pr": ""}' in SKILL
    assert "ask" in SKILL.lower() and "2.1.281" in SKILL


def test_git_conventions_negative_never_sets_false_or_rewrites_history():
    assert '"attribution": false' not in SKILL
    for bad in ("filter-branch", "rebase -i", "push --force ", "--no-verify"):
        assert bad not in SKILL.replace("`git push --force*`", ""), bad
