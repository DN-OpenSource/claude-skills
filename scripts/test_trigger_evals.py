"""Every skill ships trigger evals for `claude plugin eval`: 2 prompts that must fire it and
1 that must not, each graded on the skill's own name, plus a near-miss (`quiet-near-*`: same
topic, should still not fire) and step checks (`does-*`: graded on what Claude did after loading).

Run: python -m pytest scripts/test_trigger_evals.py -q   (structure only; the evals themselves
call the model: see README "Trigger tests")
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = sorted(p.parent.name for p in ROOT.glob("skills/*/SKILL.md"))


def _cases(skill):
    return sorted(p for p in (ROOT / "skills" / skill / "evals").glob("*/prompt.md"))


def test_trigger_evals_positive_every_skill_has_two_fire_and_one_quiet_case():
    for s in SKILLS:
        names = [p.parent.name for p in _cases(s)]
        assert sum(n.startswith("fires-") for n in names) >= 2, s
        assert sum(n.startswith("quiet-") for n in names) >= 1, s
        assert sum(n.startswith("quiet-near-") for n in names) >= 1, s


def test_trigger_evals_positive_graders_name_their_own_skill():
    for s in SKILLS:
        for p in _cases(s):
            if p.parent.name.startswith("does-"):
                continue
            for g in (p.parent / "graders").glob("*.md"):
                text = g.read_text(encoding="utf-8")
                assert "type: tool_used" in text and "tool: Skill" in text, g
                assert f'?{s}"' in text, f"{g} must match skill {s}"


def test_trigger_evals_negative_quiet_cases_forbid_the_skill():
    for s in SKILLS:
        for p in _cases(s):
            if p.parent.name.startswith("quiet-"):
                g = (p.parent / "graders" / "skill-quiet.md").read_text(encoding="utf-8")
                assert re.search(r"^min: 0$", g, re.M) and re.search(r"^max: 0$", g, re.M), p
                assert "arm: both" in g, p


def test_trigger_evals_positive_step_cases_grade_actions_not_the_skill_call():
    for s in SKILLS:
        for p in _cases(s):
            if not p.parent.name.startswith("does-"):
                continue
            assert re.search(r"^tags:.*\bstep\b", p.read_text(encoding="utf-8"), re.M), p
            graders = [g.read_text(encoding="utf-8") for g in (p.parent / "graders").glob("*.md")]
            assert any("tool: Skill" not in g for g in graders), f"{p.parent} must grade an action"
            case = p.parent / "case.yaml"
            assert case.is_file(), f"{p.parent} needs a case.yaml with its scaffold"
            script = re.search(r"scaffold_script:\s*(\S+)", case.read_text(encoding="utf-8"))
            assert script and (p.parent / script.group(1)).is_file(), case
