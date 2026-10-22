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


# --- product-visionary product page ------------------------------------------

PAGE = ROOT / "skills" / "product-visionary" / "references" / "page.html"
SITE_PAGE = ROOT / "site" / "product" / "index.html"
DATA = re.compile(r'(<script type="application/json" id="product-data">)(.*?)(</script>)', re.S)
KEYS = {"product", "updated", "repo", "goal", "goal_status", "success", "stats", "features",
        "roadmap", "open_questions", "session", "decisions"}


def _split(path):
    html = path.read_text(encoding="utf-8")
    m = DATA.search(html)
    assert m, path
    return json.loads(m.group(2)), html[:m.start(2)] + html[m.end(2):]


def test_product_page_positive_template_data_has_every_section():
    data, _ = _split(PAGE)
    assert KEYS <= set(data)
    assert set(data["roadmap"]) == {"fix", "build", "proposed", "cut", "deferred"}


def test_product_page_positive_site_page_is_template_plus_data_only():
    data, shell = _split(SITE_PAGE)
    _, template_shell = _split(PAGE)
    assert KEYS <= set(data)
    assert shell == template_shell  # generating the page = replacing the JSON, nothing else


def test_product_page_negative_data_never_rendered_as_html():
    _, shell = _split(PAGE)
    for sink in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write"):
        assert sink not in shell, sink


def test_packaging_negative_no_dangling_relative_links_in_readmes():
    bad = []
    for md in [ROOT / "README.md", *ROOT.glob("skills/*/README.md"), *ROOT.glob("skills/*/SKILL.md")]:
        prose = re.sub(r"```.*?```", "", md.read_text(encoding="utf-8"), flags=re.S)  # examples in code blocks aren't links
        for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", prose):
            if "://" in target or target.startswith("mailto:"):
                continue
            if not (md.parent / target).exists():
                bad.append(f"{md.relative_to(ROOT)} -> {target}")
    assert bad == []


# --- pages: never embed recordings; home page lists every skill safely --------

HOME = ROOT / "site" / "index.html"


def test_product_page_negative_never_embeds_media():
    _, shell = _split(PAGE)
    for tag in ("<video", "<source", "<iframe", "<img", "<embed", "<object"):
        assert tag not in shell.lower(), tag
    for el in ("video", "source", "iframe", "img", "embed", "object"):  # links (<a>) to PRs are fine
        assert f'createElement("{el}")' not in shell and f'el("{el}"' not in shell, el


def test_home_page_positive_lists_every_skill():
    html = HOME.read_text(encoding="utf-8")
    missing = [s for s in SKILLS if f'n: "{s}"' not in html]
    assert missing == []


def test_home_page_negative_never_renders_with_innerhtml():
    html = HOME.read_text(encoding="utf-8")
    for sink in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write"):
        assert sink not in html, sink
