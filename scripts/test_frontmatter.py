"""Every SKILL.md frontmatter must be valid YAML. An unquoted ": " in a description makes
Claude Code load the skill with empty metadata, so it silently never triggers.

Run: python -m pytest scripts/test_frontmatter.py -q   (needs PyYAML)
"""
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")
ROOT = Path(__file__).resolve().parent.parent
SKILLS = sorted(ROOT.glob("skills/*/SKILL.md"))


def _front(p):
    text = p.read_text(encoding="utf-8")
    assert text.startswith("---\n"), p
    return text.split("---\n", 2)[1]


@pytest.mark.parametrize("path", SKILLS, ids=lambda p: p.parent.name)
def test_frontmatter_positive_parses_with_name_and_description(path):
    meta = yaml.safe_load(_front(path))
    assert meta["name"] == path.parent.name
    assert isinstance(meta["description"], str) and len(meta["description"]) > 40


def test_frontmatter_positive_description_matches_what_budget_script_counts():
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    import check_token_budget as budget
    for p in SKILLS:
        raw = budget.description(p)
        assert yaml.safe_load(_front(p))["description"] in (raw, raw[1:-1])  # quoted or plain


def test_frontmatter_negative_unquoted_colon_is_rejected():
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load("name: x\ndescription: Do this: then that\n")
