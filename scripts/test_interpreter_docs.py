"""Skills that tell Claude to run a Python script must work on every OS:
`python3` (stock macOS/Linux have no `python`) plus the Windows note (`python3` there is
often the Microsoft Store stub)."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS_PY = re.compile(r"^\s*`?(python3?)\s+\S+\.py\b|`(python3?) [^`]*\.py", re.M)
NOTE = "Microsoft Store"


def _docs():
    return sorted(ROOT.glob("skills/*/SKILL.md"))


def test_interpreter_docs_positive_every_python_run_uses_python3():
    bad = [f"{p.relative_to(ROOT)}: {m.group(0).strip()}" for p in _docs()
           for m in RUNS_PY.finditer(p.read_text(encoding="utf-8"))
           if "python3" not in m.group(0)]
    assert bad == []


def test_interpreter_docs_positive_skills_running_python_carry_windows_note():
    missing = [str(p.relative_to(ROOT)) for p in _docs()
               if RUNS_PY.search(p.read_text(encoding="utf-8")) and NOTE not in p.read_text(encoding="utf-8")]
    assert missing == []


def test_interpreter_docs_negative_pattern_catches_bare_python():
    assert RUNS_PY.search("python <skill-dir>/scripts/lsp.py --root .")
    assert "python3" not in RUNS_PY.search("python <skill-dir>/scripts/lsp.py").group(0)
