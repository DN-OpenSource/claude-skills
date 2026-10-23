"""run_crowded_evals.py builds a valid throwaway workspace (no model calls here).

Run: python -m pytest scripts/test_crowded_evals.py -q
"""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import run_crowded_evals as rce  # noqa: E402


def test_crowded_positive_fixture_has_45_filler_skills():
    assert len(list((rce.CROWD / "crowd-plugin" / "skills").glob("*/SKILL.md"))) == 45


def test_crowded_positive_workspace_keeps_plugins_and_cases_separate():
    work = Path(tempfile.mkdtemp())
    rce.build(["memory"], work)
    assert (work / "plugins" / "memory" / "SKILL.md").is_file()
    assert not (work / "plugins" / "memory" / "evals").exists()
    cases = sorted((work / "evals").glob("memory-*/prompt.md"))
    assert len(cases) == 2
    assert 'plugins: ["../../plugins/memory", "../../plugins/crowd-plugin"]' in cases[0].read_text(encoding="utf-8")


def test_crowded_negative_no_skill_names_no_run():
    assert rce.main([]) == 2
