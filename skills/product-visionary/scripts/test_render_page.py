"""render_page.py: product.json + template -> index.html, deterministic and validated.

Run: python -m pytest skills/product-visionary/scripts/test_render_page.py -q
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "render_page.py"
TEMPLATE = HERE.parent / "references" / "page.html"
DATA = re.compile(r'(<script type="application/json" id="product-data">)(.*?)(</script>)', re.S)


def _sample():
    return json.loads(DATA.search(TEMPLATE.read_text(encoding="utf-8")).group(2))


def _run(project):
    return subprocess.run([sys.executable, str(SCRIPT), str(project)], capture_output=True, text=True)


def _project(data):
    root = Path(tempfile.mkdtemp())
    (root / "docs" / "product").mkdir(parents=True)
    (root / "docs" / "product" / "product.json").write_text(json.dumps(data), encoding="utf-8")
    return root


def test_render_positive_writes_template_shell_with_the_data():
    data = _sample(); data["product"]["name"] = "Acme"
    root = _project(data)
    r = _run(root)
    assert r.returncode == 0, r.stderr
    out = (root / "docs" / "product" / "index.html").read_text(encoding="utf-8")
    m = DATA.search(out)
    assert json.loads(m.group(2))["product"]["name"] == "Acme"
    t = TEMPLATE.read_text(encoding="utf-8"); tm = DATA.search(t)
    assert out[:m.start(2)] == t[:tm.start(2)] and out[m.end(2):] == t[tm.end(2):]  # shell byte-identical


def test_render_positive_site_folder_wins_and_closing_tags_are_escaped():
    data = _sample(); data["goal"]["text"] = "Stop </script><b>x</b> here"
    root = _project(data); (root / "site").mkdir()
    assert _run(root).returncode == 0
    out = (root / "site" / "product" / "index.html").read_text(encoding="utf-8")
    assert "</script><b>" not in out  # data can't close the JSON block
    assert json.loads(DATA.search(out).group(2))["goal"]["text"] == "Stop </script><b>x</b> here"


def test_render_negative_invalid_data_is_rejected_and_nothing_written():
    data = _sample(); del data["goal"]; data["decisions"][0]["pr"]["url"] = "javascript:alert(1)"
    root = _project(data)
    r = _run(root)
    assert r.returncode == 2
    assert "goal" in r.stderr and "pr.url" in r.stderr
    assert not (root / "docs" / "product" / "index.html").exists()
