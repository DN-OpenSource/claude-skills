#!/usr/bin/env python3
"""Crowded trigger evals: does a skill still fire with 45 other skills loaded?

    python scripts/run_crowded_evals.py memory schema-aware-db [-- extra claude plugin eval args]

Sandboxed `claude plugin eval` loads only the plugin under test, so it can't show crowding.
This builds a throwaway workspace with (1) a copy of each skill, (2) the 45-skill filler plugin
in evals-crowded/crowd-plugin, and (3) the cases in evals-crowded/<skill>-*, then runs the eval
there. Calls the model with your credentials (about $0.25 per case per run); never in CI.
Nothing outside the temp workspace is touched.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CROWD = ROOT / "evals-crowded"


def build(skills, work):
    for s in skills:
        shutil.copytree(ROOT / "skills" / s, work / "plugins" / s, ignore=shutil.ignore_patterns("evals", "results"))
    shutil.copytree(CROWD / "crowd-plugin", work / "plugins" / "crowd-plugin")
    for s in skills:
        for case in sorted(CROWD.glob(f"{s}-*/prompt.md")):
            dest = work / "evals" / case.parent.name
            shutil.copytree(case.parent, dest)
            p = dest / "prompt.md"
            text = p.read_text(encoding="utf-8")
            lines = [l if not l.startswith("plugins:") else f'plugins: ["../../plugins/{s}", "../../plugins/crowd-plugin"]'
                     for l in text.split("\n")]
            p.write_text("\n".join(lines), encoding="utf-8")


def main(argv):
    if "--" in argv:
        i = argv.index("--"); skills, extra = argv[:i], argv[i + 1:]
    else:
        skills, extra = argv, []
    if not skills:
        print(__doc__); return 2
    work = Path(tempfile.mkdtemp(prefix="crowded-evals-"))
    try:
        build(skills, work)
        cmd = ["claude", "plugin", "eval", str(work), "--no-publish", "--ablation", "none", *extra]
        print("running:", " ".join(cmd), flush=True)
        return subprocess.call(cmd, shell=sys.platform == "win32")
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
