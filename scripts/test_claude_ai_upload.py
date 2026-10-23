"""README's claude.ai upload steps stay correct (D-22).

Run: python -m pytest scripts/test_claude_ai_upload.py -q
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
SECTION = README.split("## Use on claude.ai", 1)[1].split("\n## ", 1)[0]


def desc_len(name):
    text = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
    return len(re.search(r"^description:\s*(.*)$", text, re.M).group(1).strip("'\""))


def test_upload_positive_steps_delete_first_and_zip_with_folder_root():
    assert SECTION.index("Delete the old copy first") < SECTION.index("Upload")
    assert "--exclude=evals --exclude=.claude-plugin memory" in SECTION
    assert "-x 'memory/evals/*' 'memory/.claude-plugin/*'" in SECTION


def test_upload_positive_quoted_description_lengths_are_current():
    assert f"memory {desc_len('memory')}" in SECTION
    assert f"schema-aware-db {desc_len('schema-aware-db')}" in SECTION


def test_upload_negative_hook_and_cli_skills_are_not_offered_for_claude_ai():
    first = SECTION.split("\n\n")[1]
    for name in ("decision-maker", "product-visionary", "git-conventions", "lsp"):
        assert name in first.split("don't")[0], name  # listed as not working
