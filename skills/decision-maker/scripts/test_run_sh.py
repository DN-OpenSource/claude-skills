"""run.sh picks a working Python before running the script (Windows' python3 is often a Store stub).

Run: python -m pytest test_run_sh.py -q
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SH = shutil.which("sh")


def _fake(bindir: Path, name: str, body: str):
    p = bindir / name
    p.write_text("#!/bin/sh\n" + body + "\n", encoding="utf-8", newline="\n")
    p.chmod(0o755)


@unittest.skipUnless(SH, "needs a POSIX sh")
class TestRunSh(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        self.count = self.tmp / "count"
        # the script counts its runs and exits 2, like guard.py blocking an action
        self.script = self.tmp / "s.py"
        self.script.write_text(
            f"import sys\nopen({str(self.count)!r}, 'a').write('x')\n"
            "print('ran', *sys.argv[1:])\nsys.exit(2)\n", encoding="utf-8")
        real = Path(sys.executable).as_posix()
        self.real = f'exec "{real}" "$@"'

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_sh(self):
        # only the fakes and sh's own dir on PATH, so no real python leaks in
        env = dict(os.environ, PATH=os.pathsep.join([str(self.bin), str(Path(SH).parent)]))
        return subprocess.run([SH, str(HERE / "run.sh"), str(self.script), "a b"],
                              capture_output=True, text=True, env=env)

    def test_run_sh_positive_uses_python3_when_it_works(self):
        _fake(self.bin, "python3", self.real)
        _fake(self.bin, "python", "exit 7")
        r = self.run_sh()
        self.assertEqual((r.returncode, r.stdout.strip()), (2, "ran a b"))

    def test_run_sh_positive_skips_store_stub_and_runs_script_once(self):
        _fake(self.bin, "python3", 'echo "Python was not found" >&2; exit 9009')
        _fake(self.bin, "python", self.real)
        r = self.run_sh()
        self.assertEqual((r.returncode, r.stdout.strip()), (2, "ran a b"))
        self.assertEqual(self.count.read_text(), "x")  # exit 2 is not retried

    def test_run_sh_negative_no_python_fails_open_without_running(self):
        _fake(self.bin, "python3", "exit 9009")
        _fake(self.bin, "python", "exit 9009")
        r = self.run_sh()
        self.assertEqual(r.returncode, 0)
        self.assertIn("no working Python", r.stderr)
        self.assertFalse(self.count.exists())


if __name__ == "__main__":
    unittest.main()
