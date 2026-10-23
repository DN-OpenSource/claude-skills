"""memory: one owner for personal facts per host (D-21).

Run: python -m pytest scripts/test_memory_owner.py -q
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = (ROOT / "skills" / "memory" / "SKILL.md").read_text(encoding="utf-8")
README = (ROOT / "skills" / "memory" / "README.md").read_text(encoding="utf-8")


def test_owner_positive_defers_to_host_memory_and_keeps_user_md_elsewhere():
    assert "**One owner per host.**" in SKILL
    assert "leave personal preferences to it" in SKILL and "`USER.md` is the store" in SKILL


def test_owner_positive_readme_names_both_hosts():
    assert "Works in Claude Code and as a claude.ai skill" in README
    assert "built-in memory" in README


def test_owner_negative_personal_fact_never_bootstraps_or_lands_in_repo_memory():
    assert "A personal fact never triggers\nauto-bootstrap and never goes into a repo `MEMORY.md`" in SKILL
    assert '"forget W" removes the fact from both' in SKILL
