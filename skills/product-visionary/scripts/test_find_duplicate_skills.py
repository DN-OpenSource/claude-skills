"""find_duplicate_skills.py reports skills installed more than once (and stale plugins) and
prints how to remove the extras. It never removes anything.

Run: python -m pytest skills/product-visionary/scripts/test_find_duplicate_skills.py -q
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "find_duplicate_skills.py"


def skill(path, name):
    path.mkdir(parents=True, exist_ok=True)
    (path / "SKILL.md").write_text(f"---\nname: {name}\ndescription: x\n---\n", encoding="utf-8")


def fake_env(with_dupes=True):
    home = Path(tempfile.mkdtemp()); proj = Path(tempfile.mkdtemp())
    plugins = home / ".claude" / "plugins"
    skill(plugins / "cache" / "mk" / "memory" / "1.9.0", "memory")
    skill(plugins / "cache" / "mk" / "teammates-cc" / "1.1.0", "teammates")
    installed = {"memory@mk": [{"installPath": str(plugins / "cache" / "mk" / "memory" / "1.9.0"), "version": "1.9.0"}],
                 "teammates-cc@mk": [{"installPath": str(plugins / "cache" / "mk" / "teammates-cc" / "1.1.0"), "version": "1.1.0"}]}
    (plugins / "installed_plugins.json").write_text(json.dumps({"version": 2, "plugins": installed}), encoding="utf-8")
    mk = plugins / "marketplaces" / "mk" / ".claude-plugin"; mk.mkdir(parents=True)
    (mk / "marketplace.json").write_text(json.dumps({"name": "mk", "plugins": [{"name": "memory"}, {"name": "teammates"}]}), encoding="utf-8")
    if with_dupes:
        skill(home / ".claude" / "skills" / "memory", "memory")
    return home, proj


def run(home, proj):
    return subprocess.run([sys.executable, str(SCRIPT), "--home", str(home), "--project", str(proj)], capture_output=True, text=True)


def test_duplicates_positive_personal_copy_shadowing_a_plugin_is_reported_with_the_fix():
    home, proj = fake_env()
    r = run(home, proj)
    assert r.returncode == 0
    assert "memory" in r.stdout and "installed 2 times" in r.stdout
    assert "personal copy" in r.stdout and str(home / ".claude" / "skills" / "memory") in r.stdout
    assert (home / ".claude" / "skills" / "memory" / "SKILL.md").exists()  # nothing removed


def test_duplicates_positive_plugin_missing_from_its_marketplace_is_flagged_stale():
    home, proj = fake_env()
    r = run(home, proj)
    assert "teammates-cc@mk" in r.stdout and "no longer in the mk marketplace" in r.stdout
    assert "claude plugin uninstall teammates-cc@mk" in r.stdout


def test_duplicates_negative_clean_setup_reports_nothing_to_fix():
    home, proj = fake_env(with_dupes=False)
    (home / ".claude" / "plugins" / "installed_plugins.json").write_text(json.dumps({"version": 2, "plugins": {
        "memory@mk": [{"installPath": str(home / ".claude" / "plugins" / "cache" / "mk" / "memory" / "1.9.0")}]}}), encoding="utf-8")
    r = run(home, proj)
    assert r.returncode == 0 and "No duplicate or stale skills found" in r.stdout
