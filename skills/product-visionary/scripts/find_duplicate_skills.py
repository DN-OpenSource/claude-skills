#!/usr/bin/env python3
"""Find skills installed more than once, and plugins their marketplace no longer lists.

    python3 find_duplicate_skills.py [--home DIR] [--project DIR]

When the same skill is installed twice (a personal copy in ~/.claude/skills and a plugin, or two
plugins), Claude may load the wrong one: often an old personal copy shadows the up-to-date
plugin. This lists every collision and prints the command that removes each extra copy.
It is read-only: it never removes, disables or edits anything.

Can't see: skills provisioned from claude.ai (e.g. anthropic-skills:*), which aren't on disk;
compare names against the session's skill list by hand. Stdlib only, Python 3.9+.
"""
import json
import re
import sys
from pathlib import Path

NAME = re.compile(r"^name:\s*['\"]?([^'\"\n]+?)['\"]?\s*$", re.M)


def skill_name(skill_md):
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError:
        return None
    front = text.split("---", 2)[1] if text.startswith("---") else ""
    m = NAME.search(front)
    return m.group(1).strip() if m else skill_md.parent.name


def skills_in(root):
    """SKILL.md files directly in root (a single-skill plugin) or one level down."""
    found = []
    if (root / "SKILL.md").is_file():
        found.append(root / "SKILL.md")
    for sub in ("skills", "."):
        base = root / sub
        if base.is_dir():
            found += [p for p in sorted(base.glob("*/SKILL.md")) if p not in found]
    return found


def collect(home, project):
    """(skill name, source label, location, removal hint) for every installed skill."""
    rows, stale = [], []
    for where, base in (("personal copy", home / ".claude" / "skills"), ("project copy", project / ".claude" / "skills")):
        for md in sorted(base.glob("*/SKILL.md")) if base.is_dir() else []:
            rows.append((skill_name(md), where, md.parent,
                         f'move or delete the folder "{md.parent}" (back it up first)'))
    plugins = home / ".claude" / "plugins"
    try:
        installed = json.loads((plugins / "installed_plugins.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        installed = {}
    entries = installed.get("plugins", installed) if isinstance(installed, dict) else {}
    for key, info in sorted(entries.items()):
        info = info[0] if isinstance(info, list) and info else info
        path = Path(info.get("installPath", "")) if isinstance(info, dict) else None
        if not path or not path.is_dir():
            continue
        for md in skills_in(path):
            rows.append((skill_name(md), f"plugin {key}", md.parent,
                         f"claude plugin uninstall {key}   (or: claude plugin disable {key})"))
        name, _, market = key.partition("@")
        listing = plugins / "marketplaces" / market / ".claude-plugin" / "marketplace.json"
        try:
            listed = {p.get("name") for p in json.loads(listing.read_text(encoding="utf-8")).get("plugins", [])}
        except (OSError, ValueError):
            continue
        if name not in listed:
            stale.append((key, market))
    return rows, stale


def report(home, project):
    rows, stale = collect(home, project)
    by_name = {}
    for row in rows:
        by_name.setdefault(row[0], []).append(row)
    dupes = {n: r for n, r in by_name.items() if n and len(r) > 1}
    out = []
    for name, copies in sorted(dupes.items()):
        out.append(f"\n{name} - installed {len(copies)} times; Claude may load any of them:")
        for _, where, loc, _ in copies:
            out.append(f"  - {where}: {loc}")
        out.append("  Keep one. To remove an extra copy:")
        for _, where, _, hint in copies:
            out.append(f"    {where}: {hint}")
    for key, market in stale:
        out.append(f"\n{key} - no longer in the {market} marketplace (renamed or retired); it won't get updates.")
        out.append(f"  To remove it: claude plugin uninstall {key}")
    if not out:
        print("No duplicate or stale skills found.")
    else:
        print("Duplicate or stale skills (nothing has been changed):" + "\n".join(out))
    print("\nNot checked: skills provisioned from claude.ai (e.g. anthropic-skills:*) aren't on disk.")
    return 0


def main(argv):
    def opt(flag, default):
        return Path(argv[argv.index(flag) + 1]) if flag in argv else default
    return report(opt("--home", Path.home()), opt("--project", Path.cwd()))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
