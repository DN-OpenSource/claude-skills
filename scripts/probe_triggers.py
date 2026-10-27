#!/usr/bin/env python3
"""Real-environment trigger probe: which skill fires for each prompt, with YOUR setup loaded?

    python scripts/probe_triggers.py probes/prompts.txt [--runs 3] [--seed probes/seed-db[,probes/seed-dox]] [--max-turns 8] [--only SKILL] [--no-preflight] [-- claude args]

Sandboxed evals load only the plugin under test. This runs `claude -p` with your real config
(every installed plugin, personal skill, claude.ai skill and hook) in a throwaway git repo, copied
from --seed if given, and prints which skill each prompt fired, plus every loaded skill whose name
appears more than once (e.g. a plugin and an anthropic-skills:* copy). Prompts file: one
`id|prompt` or `id|expect|prompt` per line; `expect` is a skill name or `none`. With it each line
gets PASS (the skill was the first to fire in every run; for `none`, no skill from this repo
loaded at any point of any run) or FAIL, and any FAIL exits 1. `--only SKILL` runs just the lines
expecting SKILL or whose id is SKILL or starts with `SKILL-`. Before running, a preflight reads
`claude plugin list --json`: a repo skill that another marketplace's enabled plugin also names, or
an enabled install plus `--plugin-dir` of the same skill (both load as `name:name`), exits 1;
missing or disabled ones get a --plugin-dir hint. If the list can't be read the probe stops (exit 2)
unless --no-preflight is given. A repo skill's name loaded more than once in a run (a personal
copy, a claude.ai `anthropic-skills:*` copy) also exits 1: a PASS could have come from the copy.
Bad arguments exit 2. Args after `--` go to `claude` (e.g. `-- --plugin-dir skills/memory` to
probe an unreleased change; relative paths are resolved here). Calls the model with your
credentials (about $0.05-0.20 per run); never in CI. Runs start in the temp repo with Bash allowed
and no sandbox: the prompts don't ask for anything outside it, but nothing enforces that.
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

TOOLS = ["Skill", "Read", "Bash", "Glob", "Grep"]
ROOT = Path(__file__).resolve().parent.parent
MARKET = "claude-skills"


def base(skill):
    return skill.rsplit(":", 1)[-1]


def repo_skills():
    names = (re.search(r"^name:\s*(\S+)", p.read_text(encoding="utf-8"), re.M) for p in ROOT.glob("skills/*/SKILL.md"))
    return sorted(m.group(1) for m in names if m)


def list_plugins():
    """`claude plugin list --json`, or None when claude can't be run."""
    try:
        r = subprocess.run(["claude", "plugin", "list", "--json"], stdin=subprocess.DEVNULL, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", shell=sys.platform == "win32")
        return json.loads(r.stdout)
    except (OSError, ValueError):
        return None


def preflight(plugins, skills, extra=()):
    """{skill: ok | plugin-dir | missing | disabled | clash <id>} for each repo skill.

    An enabled install plus --plugin-dir of the same skill is a clash too: both copies load as
    name:name, so a PASS couldn't say which description fired."""
    dirs = {Path(a).name for a in extra if Path(a).is_dir()}
    out = {}
    for s in skills:
        mine = [p for p in plugins if p.get("id") == f"{s}@{MARKET}"]
        other = [p["id"] for p in plugins if p.get("id", "").split("@")[0] == s and p["id"] != f"{s}@{MARKET}" and p.get("enabled")]
        if s in dirs and mine and mine[0].get("enabled"):
            other.append(mine[0]["id"])
        out[s] = (f"clash {other[0]}" if other else "plugin-dir" if s in dirs else
                  "ok" if mine and mine[0].get("enabled") else "disabled" if mine else "missing")
    return out


def parse_case(line):
    """(id, expect or None, prompt) from `id|prompt` or `id|expect|prompt`."""
    parts = line.split("|", 2)
    if len(parts) == 3 and re.fullmatch(r"[a-z0-9-]+", parts[1].strip()):
        return parts[0].strip(), parts[1].strip(), parts[2].strip()
    cid, prompt = line.split("|", 1)
    return cid.strip(), None, prompt.strip()


def verdict(expect, fired, runs, skills, seen=()):
    """PASS/FAIL for one case, or None when it has no expectation.

    `fired` counts the first skill of each run; `seen` is every skill loaded in any run."""
    if expect is None:
        return None
    if expect == "none":
        return "FAIL" if any(base(s) in skills for s in [*fired, *seen] if s != "none") else "PASS"
    return "PASS" if sum(n for s, n in fired.items() if base(s) == expect) == runs else "FAIL"


def parse(stream):
    """(first skill fired or None, loaded skill names, cost, every skill fired) from
    `claude -p --output-format stream-json`."""
    fired, loaded, cost, seen = None, [], 0.0, []
    for line in stream.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("type") == "system" and ev.get("subtype") == "init":
            loaded = ev.get("skills") or []
        if ev.get("type") == "assistant":
            for c in ev.get("message", {}).get("content", []):
                if c.get("type") == "tool_use" and c.get("name") == "Skill":
                    seen.append((c.get("input") or {}).get("skill"))
                    fired = fired or seen[-1]
        if ev.get("type") == "result":
            cost = ev.get("total_cost_usd") or 0.0
    return fired, loaded, cost, [s for s in seen if s]


def duplicates(loaded):
    """Loaded skills sharing a base name (after the last ':')."""
    names = Counter(base(s) for s in loaded)
    return sorted(s for s in loaded if names[base(s)] > 1)


def workspace(seed):
    work = Path(tempfile.mkdtemp(prefix="probe-triggers-"))
    for s in (seed or "").split(","):  # later seeds add to earlier ones
        if s:
            shutil.copytree(s, work, dirs_exist_ok=True)
    if not seed:
        (work / "README.md").write_text("# demo app\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=work, check=True)
    return work


def run_one(prompt, work, max_turns, extra=()):
    cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose",
           "--max-turns", str(max_turns), "--allowedTools", *TOOLS, *extra]
    r = subprocess.run(cmd, cwd=work, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", shell=sys.platform == "win32")
    return r.stdout


def main(argv, runner=run_one, plugins=list_plugins):  # noqa: C901 (one linear script)
    extra = []
    if "--" in argv:
        i = argv.index("--"); argv, extra = argv[:i], [str(Path(a).resolve()) if Path(a).exists() else a for a in argv[i + 1:]]
    def opt(flag, default):
        return argv[argv.index(flag) + 1] if flag in argv else default
    files = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or not argv[i - 1].startswith("--"))]
    if not files:
        print(__doc__); return 2
    runs, turns, seed, only = int(opt("--runs", 3)), int(opt("--max-turns", 8)), opt("--seed", None), opt("--only", None)
    if runs < 1:  # 0 runs would make every positive line "fire in all of them"
        print("--runs must be at least 1"); return 2
    cases = [parse_case(l) for l in Path(files[0]).read_text(encoding="utf-8").splitlines() if "|" in l]
    if only:
        cases = [c for c in cases if c[1] == only or c[0] == only or c[0].startswith(f"{only}-")]
    skills = repo_skills()
    listed = plugins()
    if listed is None and "--no-preflight" not in argv:
        print("Preflight failed: `claude plugin list --json` did not run. Fix that, or pass --no-preflight "
              "to probe without checking for clashing plugins.")
        return 2
    if listed is not None:
        state = preflight(listed, skills, extra)
        clashes = {s: v for s, v in state.items() if v.startswith("clash")}
        for s, v in state.items():
            if v in ("missing", "disabled"):
                print(f"Preflight: {s} {v}; probe the working copy with: -- --plugin-dir skills/{s}")
        if clashes:
            for s, v in clashes.items():
                print(f"Preflight: {s} clashes with {v.split()[1]} (both load as {s}:{s}). "
                      f"Disable it for the probe (claude plugin disable {v.split()[1]}) or uninstall it.")
            return 1
    work, total, dupes, failed = workspace(seed), 0.0, set(), []
    try:
        for cid, expect, prompt in cases:
            fired, seen = Counter(), set()
            for _ in range(runs):
                skill, loaded, cost, also = parse(runner(prompt, work, turns, extra))
                fired[skill or "none"] += 1
                seen.update(also)
                total += cost
                dupes.update(duplicates(loaded))
            v = verdict(expect, fired, runs, skills, seen)
            if v == "FAIL":
                failed.append(cid)
            tail = f"  {v} (expect {expect})" if v else ""
            later = sorted(s for s in seen if s not in fired)
            also_line = f"  (also loaded: {', '.join(later)})" if later else ""
            print(f"{cid}: " + ", ".join(f"{s} {n}/{runs}" for s, n in fired.most_common()) + also_line + tail, flush=True)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    if dupes:
        print("Loaded more than once (may split the match): " + ", ".join(sorted(dupes)))
    shadowed = sorted({base(s) for s in dupes if base(s) in skills})
    if shadowed:
        print("FAILED: a repo skill is loaded more than once, so a PASS may have come from the other copy: "
              + ", ".join(shadowed) + ". Remove the extra copy (README › Duplicate or stale skills).")
    if failed:
        print("FAILED: " + ", ".join(failed))
    print(f"Cost: ${total:.2f}")
    return 1 if failed or shadowed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
