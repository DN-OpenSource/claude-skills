"""probe_triggers.py parses claude -p output and builds its workspace (no model calls here).

Run: python -m pytest scripts/test_probe_triggers.py -q
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import probe_triggers as pt  # noqa: E402

INIT = {"type": "system", "subtype": "init",
        "skills": ["schema-aware-db:schema-aware-db", "anthropic-skills:schema-aware-db", "memory:memory"]}


def stream(*events):
    return "\n".join(json.dumps(e) for e in events)


def skill_call(name):
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": name}}]}}


def test_probe_positive_reports_fired_skill_and_duplicate_copies(capsys, tmp_path):
    out = stream(INIT, skill_call("schema-aware-db:schema-aware-db"), {"type": "result", "total_cost_usd": 0.1})
    assert pt.parse(out) == ("schema-aware-db:schema-aware-db", INIT["skills"], 0.1)
    (tmp_path / "p.txt").write_text("fix|Fix the join\n", encoding="utf-8")
    assert pt.main([str(tmp_path / "p.txt"), "--runs", "2"], runner=lambda *a: out) == 0
    text = capsys.readouterr().out
    assert "fix: schema-aware-db:schema-aware-db 2/2" in text
    assert "anthropic-skills:schema-aware-db, schema-aware-db:schema-aware-db" in text
    assert "memory:memory" not in text.split("Loaded more than once")[1]


def test_probe_positive_seeded_workspace_has_the_query_and_git(tmp_path):
    work = pt.workspace(str(ROOT / "probes" / "seed-db"))
    assert "JOIN order_items" in (work / "app.py").read_text(encoding="utf-8")
    assert (work / ".git").is_dir()


def test_probe_negative_no_skill_call_is_none_and_no_file_no_run(capsys, tmp_path):
    assert pt.parse(stream(INIT, {"type": "assistant", "message": {"content": [{"type": "text", "text": "hi"}]}}))[0] is None
    (tmp_path / "p.txt").write_text("q|hello\n", encoding="utf-8")
    pt.main([str(tmp_path / "p.txt"), "--runs", "1"], runner=lambda *a: stream(INIT))
    assert "q: none 1/1" in capsys.readouterr().out
    seen = []
    pt.main([str(tmp_path / "p.txt"), "--runs", "1", "--", "--plugin-dir", str(tmp_path)], runner=lambda *a: seen.append(a[3]) or stream(INIT))
    assert seen == [["--plugin-dir", str(tmp_path.resolve())]]
    assert pt.main([]) == 2
