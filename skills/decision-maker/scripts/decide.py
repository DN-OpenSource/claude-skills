#!/usr/bin/env python3
"""decide.py: ask a System One model (TypeSafe Jev) typed questions from the CLI.

Sends one POST /v1/systemone with a `state` and a map of typed questions
(noul / choice / score) and prints the typed answers as JSON. All questions in
one call run in parallel against the same state, so batch them.

Providers are named {base_url, path, model, api_key | api_key_env} entries kept
in a user-level config file (outside any repo). Built-in presets cover TypeSafe
direct, OpenRouter and a local LiteLLM proxy. Add or edit any other gateway that
speaks the same wire format. Stdlib only, no pip installs.

Exit codes: 0 ok · 1 API/network error · 2 not configured (no key) or bad input.
Callers treat any non-zero exit as "no decision, fall back to your own judgment".
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PRESETS = {
    # Verified against each provider's docs (2026-10). All use Bearer auth.
    "typesafe": {
        "base_url": os.environ.get("TYPESAFE_BASE_URL", "https://api.typesafe.ai"),
        "path": "/v1/systemone",
        "model": os.environ.get("TYPESAFE_DEFAULT_MODEL", "jev-latest"),
        "api_key_env": "TYPESAFE_API_KEY",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api",
        "path": "/v1/systemone",
        "model": "~typesafe/jev-latest",
        "api_key_env": "OPENROUTER_API_KEY",
    },
    # Independent public gateway to Jev (not affiliated with TypeSafe). https://openjev.sh/docs
    "openjev": {
        "base_url": "https://api.openjev.sh",
        "path": "/v1/systemone",
        "model": "openjev",
        "api_key_env": "OPENJEV_API_KEY",
    },
    "litellm": {
        "base_url": "http://localhost:4000/typesafe",
        "path": "/v1/systemone",
        "model": "jev-latest",
        "api_key_env": "LITELLM_API_KEY",
    },
}
DEFAULT_PROVIDER = "typesafe"
FIELDS = ("base_url", "path", "model", "api_key", "api_key_env")
RETRY_STATUSES = {429, 500, 502, 503, 529}
MAX_CHOICE_OPTIONS = 255
SCORE_LEVELS = (2, 10)
BATCH_CHARS = 60000     # item text per request (~15k tokens), well inside the 32k-token state budget
BATCH_ITEMS = 100
ITEM_CHARS = 4000       # per file when --items is a glob
PARALLEL = 4            # concurrent batch requests (provider rate limits: ~80 req/s on TypeSafe)


class DecideError(Exception):
    def __init__(self, msg, code=2):
        super().__init__(msg)
        self.code = code


# ------------------------------------------------------------------ config

def config_path() -> Path:
    env = os.environ.get("DECISION_MAKER_CONFIG")
    if env:
        return Path(env).expanduser()
    base = os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"
    return Path(base) / "decision-maker" / "providers.json"


def load_config() -> dict:
    p = config_path()
    if not p.exists():
        return {"default": None, "providers": {}}
    cfg = json.loads(p.read_text(encoding="utf-8"))
    cfg.setdefault("providers", {})
    cfg.setdefault("default", None)
    return cfg


def save_config(cfg: dict) -> Path:
    p = config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    # The file may hold API keys: create it owner-only before writing.
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")
    os.chmod(p, 0o600)
    return p


def all_providers(cfg: dict) -> dict:
    """Presets overlaid with user entries (a user entry may edit a preset)."""
    merged = {k: dict(v) for k, v in PRESETS.items()}
    for name, entry in cfg["providers"].items():
        merged[name] = {**merged.get(name, {}), **entry}
    return merged


def resolve(cfg: dict, name=None, overrides=None, require_key=True) -> dict:
    name = name or os.environ.get("DECISION_MAKER_PROVIDER") or cfg["default"] or DEFAULT_PROVIDER
    providers = all_providers(cfg)
    if name not in providers:
        raise DecideError(f"unknown provider '{name}'. Known: {', '.join(sorted(providers))}")
    p = {"path": "/v1/systemone", "model": "jev-latest", **providers[name], "name": name}
    for k, v in (overrides or {}).items():
        if v is not None:
            p[k] = v
    if not p.get("base_url"):
        raise DecideError(f"provider '{name}' has no base_url")
    key = p.get("api_key") or (os.environ.get(p["api_key_env"]) if p.get("api_key_env") else None)
    if not key and require_key:
        where = f"export {p['api_key_env']}=..." if p.get("api_key_env") else "set api_key"
        raise DecideError(f"provider '{name}' has no API key ({where}, or "
                          f"`decide.py provider edit {name} --api-key-env VAR`)")
    p["_key"] = key
    return p


def mask(key: str) -> str:
    return key[:4] + "…" + key[-4:] if len(key) > 12 else "set"


# --------------------------------------------------------------- questions

def build_questions(args) -> dict:
    qs = {}
    if args.questions:
        raw = args.questions
        if raw.startswith("@"):
            raw = Path(raw[1:]).read_text(encoding="utf-8")
        qs.update(json.loads(raw))
    for qid, text in args.noul or []:
        qs[qid] = {"type": "noul", "instructions": text}
    for qid, text, opts in args.choice or []:
        qs[qid] = {"type": "choice", "instructions": text,
                   "criteria": {o.strip(): None for o in opts.split(",") if o.strip()}}
    for qid, text, levels in args.score or []:
        qs[qid] = {"type": "score", "instructions": text,
                   "criteria": [lv.strip() for lv in levels.split("|") if lv.strip()]}
    validate(qs)
    return qs


def validate(qs: dict):
    """Catch the 422s we can predict before spending a round trip."""
    if not qs:
        raise DecideError("no questions: pass --noul/--choice/--score or --questions")
    for qid, q in qs.items():
        t = q.get("type")
        if t not in ("noul", "choice", "score"):
            raise DecideError(f"{qid}: type must be noul, choice or score (got {t!r})")
        if not q.get("instructions"):
            raise DecideError(f"{qid}: instructions required")
        c = q.get("criteria")
        if t == "choice" and not (isinstance(c, dict) and 2 <= len(c) <= MAX_CHOICE_OPTIONS):
            raise DecideError(f"{qid}: choice needs 2..{MAX_CHOICE_OPTIONS} options in criteria")
        if t == "score" and not (isinstance(c, list) and SCORE_LEVELS[0] <= len(c) <= SCORE_LEVELS[1]):
            raise DecideError(f"{qid}: score needs {SCORE_LEVELS[0]}..{SCORE_LEVELS[1]} ordered levels")


def read_state(args):
    if args.state is not None:
        text = args.state
    elif args.state_file:
        text = Path(args.state_file).read_text(encoding="utf-8")
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        raise DecideError("no state: pass --state, --state-file, or pipe it on stdin")
    # Structured state (JSON object/array) is sent as-is; anything else is text.
    try:
        val = json.loads(text)
        return val if isinstance(val, (dict, list)) else text
    except ValueError:
        return text


def load_items(spec: str) -> list:
    """--items: one file → one item per non-empty line; a glob → one item per file.
    Item text goes straight to the provider and never through the calling agent."""
    import glob
    if not any(ch in spec for ch in "*?[") and Path(spec).is_file():
        lines = Path(spec).read_text(encoding="utf-8", errors="replace").splitlines()
        return [(f"{spec}:{n}", line.strip()) for n, line in enumerate(lines, 1) if line.strip()]
    files = [f for f in sorted(glob.glob(spec, recursive=True)) if Path(f).is_file()]
    if not files:
        raise DecideError(f"--items matched nothing: {spec}")
    return [(f, Path(f).read_text(encoding="utf-8", errors="replace")[:ITEM_CHARS]) for f in files]


def per_item(questions: dict, n: int) -> dict:
    """Expand each template question once per item; `{item}` marks where the item goes."""
    out = {}
    for qid, q in questions.items():
        tmpl = json.dumps(q)
        for k in range(n):
            ref = f"`items.i{k}`"
            body = tmpl.replace("{item}", ref) if "{item}" in tmpl else None
            item_q = json.loads(body) if body else {**q, "instructions": {"item": ref, "question": q["instructions"]}}
            out[f"{qid}#{k}"] = item_q
    return out


def batches(items: list):
    batch, size = [], 0
    for it in items:
        if batch and (size + len(it[1]) > BATCH_CHARS or len(batch) >= BATCH_ITEMS):
            yield batch
            batch, size = [], 0
        batch.append(it)
        size += len(it[1])
    if batch:
        yield batch


def keep(a: dict, where: str) -> bool:
    """--where filter: yes (noul ≥ 0.5, or any choice/score), no, unsure (not `act`)."""
    if not where:
        return True
    want = set(where.split(","))
    yes = a["noul"] >= 0.5 if "noul" in a else True
    return (("yes" in want and yes) or ("no" in want and not yes) or ("unsure" in want and not a.get("act")))


EXCERPT_CHARS = 240


def excerpt(text: str) -> str:
    one = " ".join(text.split())
    return one if len(one) <= EXCERPT_CHARS else one[:EXCERPT_CHARS] + "…"


def brief(answers: dict, labels=None, where=None, texts=None) -> str:
    """One line per answer: label, question id, value, confidence, act/ask.
    With `texts`, unsure answers carry an excerpt so the caller can judge them
    without another tool call."""
    lines = []
    for qid, a in answers.items():
        if not keep(a, where):
            continue
        base, _, k = qid.partition("#")
        label = labels[int(k)] if labels and k else "-"
        val = a.get("choice", a.get("noul", a.get("score")))
        val = f"{val:.2f}" if isinstance(val, float) else val
        conf = f"{a['confidence']:.2f}" if "confidence" in a else "-"
        lines.append(f"{label}\t{base}\t{val}\t{conf}\t{'act' if a.get('act') else 'ask'}")
        if texts and k and not a.get("act"):
            lines.append(f"    ↳ {excerpt(texts[int(k)])}")
    return "\n".join(lines)


def gate(answers: dict, threshold: float) -> dict:
    """Add `act`: true when the answer is certain enough to act on without review."""
    for a in answers.values():
        if "confidence" in a:
            a["act"] = a["confidence"] >= threshold
        elif "noul" in a:  # noul has no confidence; distance from 0.5 stands in
            a["act"] = max(a["noul"], 1 - a["noul"]) >= threshold
    return answers


# --------------------------------------------------------------------- http

def http(provider: dict, method: str, path: str, body=None, retries=3, timeout=30.0):
    url = provider["base_url"].rstrip("/") + path
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {provider['_key']}", "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            with e:
                detail = e.read().decode("utf-8", "replace")[:500]
            if e.code in RETRY_STATUSES and attempt < retries:
                ra = e.headers.get("retry-after")
                time.sleep(float(ra) if ra and ra.replace(".", "", 1).isdigit() else 0.5 * 2 ** attempt)
                continue
            hint = {401: "check the API key", 422: "request failed validation"}.get(e.code, "")
            raise DecideError(f"HTTP {e.code} from {url} {hint}: {detail}".strip(), code=1)
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < retries:
                time.sleep(0.5 * 2 ** attempt)
                continue
            raise DecideError(f"cannot reach {url}: {e}", code=1)


# ----------------------------------------------------------------- commands

def cmd_ask(args):
    cfg = load_config()
    p = resolve(cfg, args.provider, {"base_url": args.base_url, "api_key": args.api_key,
                                     "model": args.model}, require_key=not args.dry_run)
    questions = build_questions(args)
    if args.items:
        return ask_items(args, p, questions)
    body = {"state": read_state(args), "model": p["model"], "questions": questions}
    if args.dry_run:
        print(json.dumps({"url": p["base_url"].rstrip("/") + p["path"], "body": body}, indent=2))
        return
    t0 = time.monotonic()
    out = http(p, "POST", p["path"], body, retries=args.retries, timeout=args.timeout)
    out["provider"] = p["name"]
    out["latency_s"] = round(time.monotonic() - t0, 3)
    gate(out.get("answers", {}), args.min_confidence)
    print(brief(out.get("answers", {}), where=args.where) if args.brief else json.dumps(out, indent=2))


def bodies_for(p, items, questions, context=None):
    out = []
    for batch in batches(items):
        state = {"items": {f"i{k}": text for k, (_, text) in enumerate(batch)}}
        if context is not None:
            state["context"] = context
        out.append((batch, {"state": state, "model": p["model"], "questions": per_item(questions, len(batch))}))
    return out


def classify_items(p, items, questions, context=None, threshold=0.8, retries=3, timeout=30.0):
    """Ask every question about every item; batches go out in parallel (time ≈ the slowest batch).
    Returns (answers keyed 'qid#index' with `act` flags, labels, texts, Jev input tokens)."""
    from concurrent.futures import ThreadPoolExecutor
    work = bodies_for(p, items, questions, context)
    with ThreadPoolExecutor(min(PARALLEL, len(work)) or 1) as pool:
        outs = list(pool.map(lambda w: http(p, "POST", p["path"], w[1], retries=retries, timeout=timeout), work))
    answers, labels, texts, tokens = {}, [], [], 0
    for (batch, _), out in zip(work, outs):
        tokens += out.get("usage", {}).get("input_tokens", 0)
        off = len(labels)
        for qid, a in out.get("answers", {}).items():
            base, _, k = qid.partition("#")
            answers[f"{base}#{off + int(k)}"] = a
        labels += [label for label, _ in batch]
        texts += [text for _, text in batch]
    return gate(answers, threshold), labels, texts, tokens


def ask_items(args, p, questions):
    items = load_items(args.items)
    context = read_state(args) if (args.state is not None or args.state_file) else None
    if args.dry_run:
        for _, body in bodies_for(p, items, questions, context):
            print(json.dumps({"url": p["base_url"].rstrip("/") + p["path"], "body": body}, indent=2))
        return
    t0 = time.monotonic()
    answers, labels, texts, tokens = classify_items(p, items, questions, context, args.min_confidence,
                                                    args.retries, args.timeout)
    if args.brief:
        where = "" if args.where == "all" else (args.where or "yes,unsure")  # items: hits + unsure by default
        shown = brief(answers, labels, where, texts)
        if shown:
            print(shown)
        unsure = sum(1 for a in answers.values() if not a.get("act"))
        print(f"# {len(labels)} items, {len(answers)} answers, {unsure} unsure (judge their excerpts; "
              f"trust 'act' lines){'' if where == '' else f'; showing {where}'}. "
              f"{tokens} Jev tokens, {time.monotonic() - t0:.2f}s via {p['name']}")
    else:
        print(json.dumps({"provider": p["name"], "labels": labels, "answers": answers,
                          "usage": {"input_tokens": tokens}}, indent=2))


def cmd_models(args):
    p = resolve(load_config(), args.provider)
    print(json.dumps(http(p, "GET", p["path"].rsplit("/", 1)[0] + "/models"), indent=2))


def cmd_provider(args):
    cfg = load_config()
    providers = all_providers(cfg)
    default = os.environ.get("DECISION_MAKER_PROVIDER") or cfg["default"] or DEFAULT_PROVIDER
    if args.action == "list":
        for name, p in sorted(providers.items()):
            key = p.get("api_key") or (os.environ.get(p["api_key_env"]) if p.get("api_key_env") else None)
            src = (f"key in config ({mask(key)})" if p.get("api_key")
                   else f"${p.get('api_key_env')} ({'set' if key else 'NOT SET'})")
            tag = " *default" if name == default else ""
            origin = "preset" if name in PRESETS and name not in cfg["providers"] else "config"
            print(f"{name}{tag}  [{origin}]  {p.get('base_url')}{p.get('path', '/v1/systemone')}"
                  f"  model={p.get('model')}  {src}")
        print(f"config: {config_path()}")
        return
    name = args.name
    if args.action == "remove":
        if name not in cfg["providers"]:
            raise DecideError(f"'{name}' is not in {config_path()} (presets can't be removed, only edited)")
        del cfg["providers"][name]
        if cfg["default"] == name:
            cfg["default"] = None
    elif args.action == "use":
        if name not in providers:
            raise DecideError(f"unknown provider '{name}'")
        cfg["default"] = name
    else:  # add | edit
        if args.action == "add" and name in providers:
            raise DecideError(f"'{name}' exists; use `provider edit {name}`")
        if args.action == "edit" and name not in providers:
            raise DecideError(f"unknown provider '{name}'; use `provider add {name}`")
        if args.action == "add" and not args.base_url:
            raise DecideError("--base-url is required for add")
        entry = cfg["providers"].setdefault(name, {})
        for f in FIELDS:
            v = getattr(args, f, None)
            if v is not None:
                entry[f] = v
        # A key and an env-var name are alternatives: setting one clears the other.
        if args.api_key is not None:
            entry.pop("api_key_env", None)
        if args.api_key_env is not None:
            entry.pop("api_key", None)
        if args.default:
            cfg["default"] = name
    print(f"saved {save_config(cfg)}")


GUARD_FEATURES = ("rules", "scope", "ask", "stop", "prefetch")
MODES = ("auto", "manual")


def mode_of(cfg: dict):
    """The user's choice after install: 'auto' (Jev by default), 'manual' (only when asked), or None (not chosen)."""
    m = os.environ.get("DECISION_MAKER_MODE") or cfg.get("mode")
    return m if m in MODES else None


def default_features(cfg: dict) -> list:
    """Guard features when the user hasn't picked any: prefetch in auto mode, nothing otherwise."""
    return ["prefetch"] if mode_of(cfg) == "auto" else []


def cmd_mode(args):
    cfg = load_config()
    if args.mode:
        cfg["mode"] = args.mode
        save_config(cfg)
    m = mode_of(cfg)
    print({"auto": "mode: auto. Jev is used by default: prefetch pre-scans find-type prompts, and Claude gets the "
                   "Jev commands at session start.",
           "manual": "mode: manual. Jev runs only when you ask for it (/decision-maker:decision-maker, or ask "
                     "Claude to use Jev). Nothing runs automatically except guard checks you turned on yourself.",
           None: "mode: not chosen yet, so nothing runs automatically. Choose with: decide.py mode auto | manual"}[m])


def cmd_guard(args):
    cfg = load_config()
    if args.action == "on":
        # No args: add the per-edit checks and keep prefetch as it was (on by default, until turned off).
        keep_prefetch = "prefetch" in cfg.get("guard", default_features(cfg))
        feats = args.features or [f for f in GUARD_FEATURES if f != "prefetch" or keep_prefetch]
        bad = set(feats) - set(GUARD_FEATURES)
        if bad:
            raise DecideError(f"unknown guard feature(s): {', '.join(sorted(bad))}")
        cfg["guard"] = feats
    elif args.action == "off":
        cfg["guard"] = []
    if args.action == "replay":
        import guard
        act = args.act if args.act is not None else guard.ACT
        concern = args.concern if args.concern is not None else guard.CONCERN
        rows = guard.replay(act, concern)
        if not rows:
            print("no logged guard answers yet")
            return
        print(f"{'decision':<14}{'now':>6}{'replayed':>10}   (now: act={guard.ACT} concern={guard.CONCERN};"
              f" replayed: act={act} concern={concern}; no new Jev calls)")
        for k, (now, new) in rows.items():
            print(f"{k:<14}{now:>6}{new:>10}")
        return
    if args.action == "log":
        log = config_path().parent / "guard.log"
        lines = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
        shown = 0
        for line in reversed(lines):
            r = json.loads(line)
            what = (r.get("deny") and f"BLOCKED {r.get('tool')}: {'; '.join(r['deny'])}") or \
                   (r.get("ask") and f"ASKED YOU about {r.get('tool')}: {'; '.join(r['ask'])}") or \
                   (r.get("decided") and "ANSWERED for you: " + "; ".join(r.get("picks", []))) or \
                   (r.get("problems") and "SENT BACK at stop: " + "; ".join(r["problems"])) or \
                   ((r.get("added") or r.get("revoked")) and
                    f"RULES +{r.get('added') or []} -{r.get('revoked') or []}") or \
                   (r.get("error") and f"error (failed open): {r['error']}")
            if what:
                print(f"{r['ts']}  {what}")
                shown += 1
                if shown >= args.n:
                    break
        if not shown:
            print("no guard interventions logged yet")
        return
    if args.action != "status":
        save_config(cfg)
    env = os.environ.get("DECISION_MAKER_GUARD")
    on = cfg.get("guard", default_features(cfg))   # mode default until the user picks features
    print(f"guard: {', '.join(on) if on else 'off'}" + ("  (default)" if "guard" not in cfg else "") +
          (f"  (overridden by $DECISION_MAKER_GUARD={env})" if env is not None else ""))
    sessions = sorted((config_path().parent / "sessions").glob("*.json"), key=lambda f: f.stat().st_mtime)
    if sessions:
        rules = json.loads(sessions[-1].read_text(encoding="utf-8")).get("rules", [])
        print("temporary rules (latest session): " + ("; ".join(rules) if rules else "none"))
    try:
        p = resolve(cfg)
        print(f"provider: {p['name']} ({p['base_url']}) key OK")
    except DecideError as e:
        p = None
        print(f"provider: NOT READY, guard stays inert: {e}")
    import guard
    print("\nWhat Jev does in Claude Code right now:\n" + "\n".join(guard.status_lines(p)))


def parser():
    ap = argparse.ArgumentParser(prog="decide.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("ask", help="ask typed questions about a state")
    a.add_argument("--state", help="state text or JSON (else --state-file or stdin)")
    a.add_argument("--state-file")
    a.add_argument("--noul", nargs=2, action="append", metavar=("ID", "QUESTION"))
    a.add_argument("--choice", nargs=3, action="append", metavar=("ID", "QUESTION", "OPT1,OPT2,..."))
    a.add_argument("--score", nargs=3, action="append", metavar=("ID", "QUESTION", "LOW|...|HIGH"))
    a.add_argument("--questions", help="full questions map as JSON, or @file.json")
    a.add_argument("--min-confidence", type=float, default=0.8,
                   help="threshold for the `act` flag on each answer (default 0.8)")
    a.add_argument("--provider")
    a.add_argument("--base-url", help="one-off override of the provider's base URL")
    a.add_argument("--api-key", help="one-off override (prefer env vars)")
    a.add_argument("--model")
    a.add_argument("--retries", type=int, default=3)
    a.add_argument("--timeout", type=float, default=30.0)
    a.add_argument("--dry-run", action="store_true", help="print the request, send nothing")
    a.add_argument("--items", help="ask every question once per item: a file (one item per line) or a glob "
                                   "(one item per file). Use {item} in a question to place the item. "
                                   "Item text never passes through the caller")
    a.add_argument("--brief", action="store_true", help="compact output: label, question, value, confidence, act/ask")
    a.add_argument("--where", help="with --brief, only print: yes, no, unsure (comma-separated) or all. "
                                   "--items defaults to yes,unsure")
    a.set_defaults(func=cmd_ask)

    m = sub.add_parser("models", help="list models the provider serves")
    m.add_argument("--provider")
    m.set_defaults(func=cmd_models)

    p = sub.add_parser("provider", help="list / add / edit / remove / use providers")
    p.add_argument("action", choices=["list", "add", "edit", "remove", "use"])
    p.add_argument("name", nargs="?")
    p.add_argument("--base-url")
    p.add_argument("--path", help="endpoint path (default /v1/systemone)")
    p.add_argument("--model")
    p.add_argument("--api-key", help="store the key in the config file (chmod 600)")
    p.add_argument("--api-key-env", help="read the key from this env var instead (preferred)")
    p.add_argument("--default", action="store_true", help="also make this the default provider")
    p.set_defaults(func=cmd_provider)

    md = sub.add_parser("mode", help="how Jev is used in Claude Code: auto (by default) or manual (when asked)")
    md.add_argument("mode", nargs="?", choices=MODES, help="omit to show the current mode")
    md.set_defaults(func=cmd_mode)

    g = sub.add_parser("guard", help="turn the Claude Code Jev guard hooks on/off")
    g.add_argument("action", choices=["on", "off", "status", "log", "replay"])
    g.add_argument("--act", type=float, help="replay: confident threshold to try")
    g.add_argument("--concern", type=float, help="replay: ask-the-user threshold to try")
    g.add_argument("-n", type=int, default=20, help="log: how many recent interventions")
    g.add_argument("features", nargs="*", help=f"subset of {', '.join(GUARD_FEATURES)} (default: all but prefetch, "
                                               "which sends file contents to the provider)")
    g.set_defaults(func=cmd_guard)
    return ap


def main(argv=None):
    args = parser().parse_args(argv)
    if args.cmd == "provider" and args.action != "list" and not args.name:
        print("error: provider name required", file=sys.stderr)
        return 2
    try:
        args.func(args)
    except DecideError as e:
        print(f"error: {e}", file=sys.stderr)
        return e.code
    except (OSError, ValueError) as e:  # unreadable files, malformed JSON
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
