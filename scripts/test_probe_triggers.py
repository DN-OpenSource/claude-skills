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


NOLIST = lambda: None  # noqa: E731  (tests never call `claude plugin list`)


def stream(*events):
    return "\n".join(json.dumps(e) for e in events)


def skill_call(name):
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": name}}]}}


def test_probe_positive_reports_fired_skill_and_duplicate_copies(capsys, tmp_path):
    out = stream(INIT, skill_call("schema-aware-db:schema-aware-db"), {"type": "result", "total_cost_usd": 0.1})
    assert pt.parse(out) == ("schema-aware-db:schema-aware-db", INIT["skills"], 0.1)
    (tmp_path / "p.txt").write_text("fix|Fix the join\n", encoding="utf-8")
    assert pt.main([str(tmp_path / "p.txt"), "--runs", "2"], runner=lambda *a: out, plugins=NOLIST) == 0
    text = capsys.readouterr().out
    assert "fix: schema-aware-db:schema-aware-db 2/2" in text
    assert "anthropic-skills:schema-aware-db, schema-aware-db:schema-aware-db" in text
    assert "memory:memory" not in text.split("Loaded more than once")[1]


def test_probe_positive_seeded_workspace_has_the_query_and_git(tmp_path):
    work = pt.workspace(str(ROOT / "probes" / "seed-db"))
    assert "JOIN order_items" in (work / "app.py").read_text(encoding="utf-8")
    assert (work / ".git").is_dir()
    layered = pt.workspace(f'{ROOT / "probes" / "seed-db"},{ROOT / "probes" / "seed-dox"}')
    assert (layered / "AGENTS.md").is_file() and (layered / "utils.py").is_file()
    assert not (work / "AGENTS.md").exists()


def test_probe_positive_every_skill_has_a_positive_and_a_near_miss_line():
    cases = [pt.parse_case(l) for l in (ROOT / "probes" / "prompts.txt").read_text(encoding="utf-8").splitlines() if "|" in l]
    for s in pt.repo_skills():
        assert any(e == s for _, e, _ in cases), s
        assert any(c == f"{s}-near" and e == "none" for c, e, _ in cases), s


def test_probe_negative_no_skill_call_is_none_and_no_file_no_run(capsys, tmp_path):
    assert pt.parse(stream(INIT, {"type": "assistant", "message": {"content": [{"type": "text", "text": "hi"}]}}))[0] is None
    (tmp_path / "p.txt").write_text("q|hello\n", encoding="utf-8")
    pt.main([str(tmp_path / "p.txt"), "--runs", "1"], runner=lambda *a: stream(INIT), plugins=NOLIST)
    assert "q: none 1/1" in capsys.readouterr().out
    seen = []
    pt.main([str(tmp_path / "p.txt"), "--runs", "1", "--", "--plugin-dir", str(tmp_path)], runner=lambda *a: seen.append(a[3]) or stream(INIT), plugins=NOLIST)
    assert seen == [["--plugin-dir", str(tmp_path.resolve())]]
    assert pt.main([]) == 2


def plugin(pid, enabled=True):
    return {"id": pid, "enabled": enabled}


def test_probe_positive_verdicts_pass_and_only_filters(capsys, tmp_path):
    (tmp_path / "p.txt").write_text("db-fix|schema-aware-db|Fix the join\nquiet|none|Write a haiku\nmem|memory|Bootstrap\n", encoding="utf-8")
    fire = lambda prompt, *a: stream(INIT, skill_call("schema-aware-db:schema-aware-db")) if "join" in prompt else stream(INIT)  # noqa: E731
    assert pt.main([str(tmp_path / "p.txt"), "--runs", "2", "--only", "schema-aware-db"], runner=fire, plugins=NOLIST) == 0
    text = capsys.readouterr().out
    assert "db-fix: schema-aware-db:schema-aware-db 2/2  PASS (expect schema-aware-db)" in text
    assert "mem:" not in text and "quiet:" not in text
    assert pt.main([str(tmp_path / "p.txt"), "--runs", "1", "--only", "quiet"], runner=fire, plugins=NOLIST) == 0
    assert "PASS (expect none)" in capsys.readouterr().out


def test_probe_positive_preflight_reports_install_state():
    listed = [plugin("memory@claude-skills"), plugin("lsp@claude-skills", enabled=False), plugin("superpowers@claude-plugins-official")]
    state = pt.preflight(listed, ["memory", "lsp", "wrap-up", "agents-dox"], [str(ROOT / "skills" / "agents-dox")])
    assert state == {"memory": "ok", "lsp": "disabled", "wrap-up": "missing", "agents-dox": "plugin-dir"}
    assert pt.parse_case("a|b c|d") == ("a", None, "b c|d")


def test_probe_negative_misses_and_clashes_exit_1(capsys, tmp_path):
    (tmp_path / "p.txt").write_text("db|schema-aware-db|Fix the join\nq|none|hello\n", encoding="utf-8")
    calls = iter([skill_call("schema-aware-db:schema-aware-db"), skill_call("memory:memory"), skill_call("memory:memory"), skill_call("memory:memory")])
    assert pt.main([str(tmp_path / "p.txt"), "--runs", "2"], runner=lambda *a: stream(INIT, next(calls)), plugins=NOLIST) == 1
    text = capsys.readouterr().out
    assert "db: schema-aware-db:schema-aware-db 1/2, memory:memory 1/2  FAIL" in text
    assert "q: memory:memory 2/2  FAIL (expect none)" in text and "FAILED: db, q" in text
    ran = []
    clash = lambda: [plugin("wrap-up@someone-else"), plugin("memory@claude-skills")]  # noqa: E731
    assert pt.main([str(tmp_path / "p.txt"), "--runs", "1"], runner=lambda *a: ran.append(1) or stream(INIT), plugins=clash) == 1
    assert "wrap-up clashes with wrap-up@someone-else" in capsys.readouterr().out and ran == []
