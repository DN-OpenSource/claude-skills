#!/usr/bin/env python3
"""Real-environment trigger probe: which skill fires for each prompt, with YOUR setup loaded?

    python scripts/probe_triggers.py probes/prompts.txt [--runs 3] [--seed probes/seed-db] [--max-turns 8] [-- claude args]

Sandboxed evals load only the plugin under test. This runs `claude -p` with your real config
(every installed plugin, personal skill, claude.ai skill and hook) in a throwaway git repo, copied
from --seed if given, and prints which skill each prompt fired, plus every loaded skill whose name
appears more than once (e.g. a plugin and an anthropic-skills:* copy). Prompts file: one
`id|prompt` per line. Args after `--` go to `claude` (e.g. `-- --plugin-dir skills/memory` to
probe an unreleased change; relative paths are resolved here). Calls the model with your credentials (about $0.05-0.20 per run); never in CI.
Nothing outside the temp repo is touched.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

TOOLS = ["Skill", "Read", "Bash", "Glob", "Grep"]


def parse(stream):
    """(skill fired or None, loaded skill names, cost) from `claude -p --output-format stream-json`."""
    fired, loaded, cost = None, [], 0.0
    for line in stream.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("type") == "system" and ev.get("subtype") == "init":
            loaded = ev.get("skills") or []
        if ev.get("type") == "assistant":
            for c in ev.get("message", {}).get("content", []):
                if fired is None and c.get("type") == "tool_use" and c.get("name") == "Skill":
                    fired = (c.get("input") or {}).get("skill")
        if ev.get("type") == "result":
            cost = ev.get("total_cost_usd") or 0.0
    return fired, loaded, cost


def duplicates(loaded):
    """Loaded skills sharing a base name (after the last ':')."""
    names = Counter(s.rsplit(":", 1)[-1] for s in loaded)
    return sorted(s for s in loaded if names[s.rsplit(":", 1)[-1]] > 1)


def workspace(seed):
    work = Path(tempfile.mkdtemp(prefix="probe-triggers-"))
    if seed:
        shutil.copytree(seed, work, dirs_exist_ok=True)
    else:
        (work / "README.md").write_text("# demo app\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=work, check=True)
    return work


def run_one(prompt, work, max_turns, extra=()):
    cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose",
           "--max-turns", str(max_turns), "--allowedTools", *TOOLS, *extra]
    r = subprocess.run(cmd, cwd=work, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", shell=sys.platform == "win32")
    return r.stdout


def main(argv, runner=run_one):
    extra = []
    if "--" in argv:
        i = argv.index("--"); argv, extra = argv[:i], [str(Path(a).resolve()) if Path(a).exists() else a for a in argv[i + 1:]]
    def opt(flag, default):
        return argv[argv.index(flag) + 1] if flag in argv else default
    files = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or not argv[i - 1].startswith("--"))]
    if not files:
        print(__doc__); return 2
    runs, turns, seed = int(opt("--runs", 3)), int(opt("--max-turns", 8)), opt("--seed", None)
    cases = [l.split("|", 1) for l in Path(files[0]).read_text(encoding="utf-8").splitlines() if "|" in l]
    work, total, dupes = workspace(seed), 0.0, set()
    try:
        for cid, prompt in cases:
            fired = Counter()
            for _ in range(runs):
                skill, loaded, cost = parse(runner(prompt.strip(), work, turns, extra))
                fired[skill or "none"] += 1
                total += cost
                dupes.update(duplicates(loaded))
            print(f"{cid}: " + ", ".join(f"{s} {n}/{runs}" for s, n in fired.most_common()), flush=True)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    if dupes:
        print("Loaded more than once (may split the match): " + ", ".join(sorted(dupes)))
    print(f"Cost: ${total:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
