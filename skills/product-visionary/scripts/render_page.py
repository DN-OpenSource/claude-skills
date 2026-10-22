#!/usr/bin/env python3
"""Render the product page: docs/product/product.json + references/page.html -> index.html.

    python3 render_page.py [PROJECT_DIR] [--if-stale]

The page shell is copied byte-for-byte from the template; only the JSON block changes, so a
rendered page can never drift from the design. The data is validated first: on any problem the
script prints every issue, exits 2 and writes nothing.

Output: <site>/product/index.html when the project has a site/ or public/ folder (GitHub Pages),
otherwise docs/product/index.html (which also covers sites published from docs/).
--if-stale: write only when the rendered page differs from the one on disk; if it's identical, just
refresh the page's mtime (a git checkout resets mtimes) so the Stop hook stops flagging it.
Stdlib only, Python 3.9+.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "references" / "page.html"
BLOCK = re.compile(r'(<script type="application/json" id="product-data">)(.*?)(</script>)', re.S)
LANES = ["Fix", "Build", "Proposed", "Cut", "Deferred"]
ENUMS = {
    "criterion": {"met", "not met", "at risk"},
    "change": {"added", "changed", "fixed", "removed"},
    "test": {"pass", "fail", "flaky", "blocked"},
    "polarity": {"positive", "negative"},
    "feature": {"done", "in progress", "broken", "planned"},
    "flag": {None, "orphan", "dead"},
    "decision": {"accepted", "vetoed", "open", "rejected"},
}


def _url_ok(u):
    return u in ("", None) or (isinstance(u, str) and re.match(r"^https?://", u, re.I) is not None)


def validate(d):
    """Every problem in the data, as 'path: problem' strings (empty list = valid)."""
    errs = []

    def need(obj, key, typ, where):
        if not isinstance(obj, dict) or key not in obj:
            errs.append(f"{where}{key}: missing")
            return None
        if typ and not isinstance(obj[key], typ):
            errs.append(f"{where}{key}: expected {typ.__name__ if isinstance(typ, type) else '/'.join(t.__name__ for t in typ)}")
            return None
        return obj[key]

    def enum(val, kind, where):
        if val not in ENUMS[kind]:
            errs.append(f"{where}: {val!r} is not one of {sorted(x for x in ENUMS[kind] if x)}")

    if not isinstance(d, dict):
        return ["product.json: must be a JSON object"]
    p = need(d, "product", dict, "")
    if p is not None:
        need(p, "name", str, "product.")
    if not _url_ok(d.get("repo", "")):
        errs.append("repo: must start with http:// or https://")
    need(d, "lastUpdated", str, "")
    g = need(d, "goal", dict, "")
    if g is not None:
        need(g, "text", str, "goal.")
        need(g, "confirmed", bool, "goal.")
    for i, c in enumerate(need(d, "successCriteria", list, "") or []):
        enum(c.get("state") if isinstance(c, dict) else None, "criterion", f"successCriteria[{i}].state")
    h = need(d, "health", dict, "")
    if h is not None:
        s = need(h, "score", (int, float), "health.")
        if s is not None and not 0 <= s <= 100:
            errs.append("health.score: must be 0-100")
    need(d, "stats", list, "")
    for i, c in enumerate(d.get("sinceLastSession") or []):
        enum(c.get("kind") if isinstance(c, dict) else None, "change", f"sinceLastSession[{i}].kind")
    t = d.get("tests") or {}
    for i, r in enumerate(t.get("rows") or []):
        enum(r.get("status"), "test", f"tests.rows[{i}].status")
        enum(r.get("polarity"), "polarity", f"tests.rows[{i}].polarity")
        if re.search(r"[A-Za-z]:\\|/(Users|home)/|file://", str(r.get("video", ""))):
            errs.append(f"tests.rows[{i}].video: no local paths on a published page")
    names = set()
    for i, f in enumerate(need(d, "features", list, "") or []):
        names.add(f.get("name"))
        enum(f.get("status"), "feature", f"features[{i}].status")
        enum(f.get("flag"), "flag", f"features[{i}].flag")
    for i, f in enumerate(d.get("features") or []):
        for dep in f.get("dependsOn") or []:
            if dep not in names:
                errs.append(f"features[{i}].dependsOn: {dep!r} is not a feature in the map")
    rm = need(d, "roadmap", dict, "")
    if rm is not None:
        lanes = need(rm, "lanes", list, "roadmap.") or []
        if [l.get("name") for l in lanes] != LANES:
            errs.append(f"roadmap.lanes: names must be {LANES} in that order")
        for l in lanes:
            for j, it in enumerate(l.get("items") or []):
                if it.get("weight") not in (1, 2, 3):
                    errs.append(f"roadmap.lanes[{l.get('name')}].items[{j}].weight: must be 1, 2 or 3")
    s = need(d, "session", dict, "")
    if s is not None and s.get("mode") not in (1, 2, 3, 4):
        errs.append("session.mode: must be 1-4")
    for i, x in enumerate(need(d, "decisions", list, "") or []):
        enum(x.get("status"), "decision", f"decisions[{i}].status")
        if x.get("panel") not in (3, 6, 9):
            errs.append(f"decisions[{i}].panel: must be 3, 6 or 9")
        if not _url_ok((x.get("pr") or {}).get("url", "")):
            errs.append(f"decisions[{i}].pr.url: must start with http:// or https://")
    return errs


def output_path(project):
    for site in ("site", "public"):
        if (project / site).is_dir():
            return project / site / "product" / "index.html"
    return project / "docs" / "product" / "index.html"


def render(project, if_stale=False):
    src = project / "docs" / "product" / "product.json"
    out = output_path(project)
    if not src.is_file():
        print(f"render_page: no {src.relative_to(project).as_posix()}; nothing to render", file=sys.stderr)
        return 0 if if_stale else 2
    try:
        data = json.loads(src.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"render_page: product.json is not valid JSON: {e}", file=sys.stderr)
        return 2
    errs = validate(data)
    if errs:
        print("render_page: product.json has problems, page not written:", *("  - " + e for e in errs), sep="\n", file=sys.stderr)
        return 2
    tpl = TEMPLATE.read_text(encoding="utf-8")
    m = BLOCK.search(tpl)
    # "<\/" is the same string in JSON, but can't end the <script> block early
    body = json.dumps(data, indent=2, ensure_ascii=False).replace("</", "<\\/")
    page = tpl[:m.start(2)] + "\n" + body + "\n" + tpl[m.end(2):]
    if if_stale and out.is_file() and out.read_text(encoding="utf-8") == page:
        t = max(os.path.getmtime(src) + 1, time.time())  # +1 s: mtime precision varies by filesystem
        os.utime(out, (t, t))  # content already current; only the mtime was behind
        print(f"render_page: {out.relative_to(project).as_posix()} already current")
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".html.tmp")
    tmp.write_text(page, encoding="utf-8")
    os.replace(tmp, out)
    print(f"render_page: wrote {out.relative_to(project).as_posix()}")
    return 0


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    project = Path(args[0] if args else ".").resolve()
    return render(project, if_stale="--if-stale" in argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
