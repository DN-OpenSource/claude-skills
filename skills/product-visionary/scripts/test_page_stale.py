"""The Stop hook only ever asks Claude to re-render; it never writes. And --if-stale
compares content, so a git checkout that resets mtimes costs nothing.

Run: python -m pytest skills/product-visionary/scripts/test_page_stale.py -q
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SH = shutil.which("sh")
HOOK = HERE / "page_stale.sh"
RENDER = HERE / "render_page.py"


def project(with_data=True, site=False):
    root = Path(tempfile.mkdtemp())
    (root / "docs" / "product").mkdir(parents=True)
    if site:
        (root / "site").mkdir()
    if with_data:
        sys.path.insert(0, str(HERE))
        import render_page
        tpl = (HERE.parent / "references" / "page.html").read_text(encoding="utf-8")
        data = render_page.BLOCK.search(tpl).group(2)
        (root / "docs" / "product" / "product.json").write_text(data, encoding="utf-8")
    return root


def hook(root, stdin='{"hook_event_name": "Stop", "stop_hook_active": false}'):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(root))
    return subprocess.run([SH, str(HOOK)], input=stdin, capture_output=True, text=True, env=env)


def render(root, *args):
    return subprocess.run([sys.executable, str(RENDER), str(root), *args], capture_output=True, text=True)


def bump(path):  # make a file look newer than everything else
    t = time.time() + 5
    os.utime(path, (t, t))


@unittest.skipUnless(SH, "needs a POSIX sh")
class TestPageStale(unittest.TestCase):
    def test_hook_positive_no_product_json_is_silent(self):
        r = hook(project(with_data=False))
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_hook_positive_current_page_is_silent(self):
        root = project(); self.assertEqual(render(root).returncode, 0)
        bump(root / "docs" / "product" / "index.html")
        self.assertEqual(hook(root).stdout, "")

    def test_hook_positive_stale_page_blocks_with_fixed_reason_and_writes_nothing(self):
        root = project(site=True); render(root)
        page = root / "site" / "product" / "index.html"; before = page.read_bytes()
        bump(root / "docs" / "product" / "product.json")
        r = hook(root)
        out = json.loads(r.stdout)
        self.assertEqual(out["decision"], "block")
        self.assertIn("render_page.py --if-stale", out["reason"])
        self.assertEqual(page.read_bytes(), before)

    def test_hook_negative_stop_hook_active_never_blocks(self):
        root = project(); render(root); bump(root / "docs" / "product" / "product.json")
        r = hook(root, '{"hook_event_name": "Stop", "stop_hook_active": true}')
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_hook_negative_malformed_input_still_exits_zero(self):
        root = project()
        self.assertEqual(hook(root, "not json at all {").returncode, 0)

    def test_if_stale_positive_identical_content_only_refreshes_mtime(self):
        root = project(); render(root)
        page = root / "docs" / "product" / "index.html"; before = page.read_bytes()
        bump(root / "docs" / "product" / "product.json")        # like a checkout
        r = render(root, "--if-stale")
        self.assertIn("already current", r.stdout)
        self.assertEqual(page.read_bytes(), before)
        self.assertEqual(hook(root).stdout, "")                  # no more blocking


if __name__ == "__main__":
    unittest.main()
