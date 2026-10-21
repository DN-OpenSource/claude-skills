"""Repo-level checks: token budget script and plugin packaging stay consistent.

Run: python -m pytest scripts/test_repo.py -q
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import check_token_budget as budget  # noqa: E402

SKILLS = sorted(p.parent.name for p in ROOT.glob("skills/*/SKILL.md"))


def _skill(tmp, name, desc):
    d = tmp / "skills" / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {desc}\n---\n# x\n", encoding="utf-8")


# --- token budget -------------------------------------------------------------

def test_token_budget_positive_real_repo_within_budget():
    rows, errors = budget.check(ROOT)
    assert errors == []
    assert {name for name, _ in rows} == set(SKILLS)


def test_token_budget_positive_estimates_ceil_chars_over_4(tmp_path):
    _skill(tmp_path, "a", "x" * 9)  # 9 chars -> 3 tokens
    rows, errors = budget.check(tmp_path)
    assert rows == [("a", 3)] and errors == []


def test_token_budget_negative_oversized_description_is_rejected(tmp_path):
    _skill(tmp_path, "big", "x" * (budget.PER_SKILL * 4 + 4))
    _, errors = budget.check(tmp_path)
    assert any(e.startswith("big:") for e in errors)


# --- packaging ----------------------------------------------------------------

def _load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def test_packaging_positive_every_skill_has_files_and_matching_manifest():
    for s in SKILLS:
        d = ROOT / "skills" / s
        assert (d / "README.md").is_file(), s
        m = _load(d / ".claude-plugin" / "plugin.json")
        assert m["name"] == s
        fm = re.search(r"^name:\s*(\S+)", (d / "SKILL.md").read_text(encoding="utf-8"), re.M)
        assert fm and fm.group(1) == s


def test_packaging_positive_marketplace_readme_and_versions_agree():
    market = _load(ROOT / ".claude-plugin" / "marketplace.json")
    entries = {p["name"]: p for p in market["plugins"]}
    assert set(entries) == set(SKILLS)
    root_version = _load(ROOT / ".claude-plugin" / "plugin.json")["version"]
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for s in SKILLS:
        assert entries[s]["source"]["path"] == f"skills/{s}"
        assert entries[s]["version"] == root_version
        assert _load(ROOT / "skills" / s / ".claude-plugin" / "plugin.json")["version"] == root_version
        assert f"| [{s}](skills/{s}/SKILL.md) | {root_version} |" in readme, s


def test_packaging_negative_no_dangling_relative_links_in_readmes():
    bad = []
    for md in [ROOT / "README.md", *ROOT.glob("skills/*/README.md"), *ROOT.glob("skills/*/SKILL.md")]:
        for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", md.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("mailto:"):
                continue
            if not (md.parent / target).exists():
                bad.append(f"{md.relative_to(ROOT)} -> {target}")
    assert bad == []
