#!/usr/bin/env python3
"""guard.py: Claude Code hook that uses Jev to keep Claude on-rules and on-task.

  PreToolUse  Edit/Write/MultiEdit/NotebookEdit/Bash   rules + scope check
  PreToolUse  AskUserQuestion                          decide instead of asking
  Stop                                                 request vs. this turn's diff
  UserPromptSubmit                                     remember the request (no Jev call)

Policy, the same for every check: confident problem → deny/block with the reason
(Claude corrects itself) · unsure → ask the user · confident fine → silent.

Inert unless enabled (`decide.py guard on`, or $DECISION_MAKER_GUARD) AND a provider
key resolves. Any error or timeout fails open: the hook prints nothing, exits 0.
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import decide  # noqa: E402

# ------------------------------------------------- thresholds (tune here)
ACT = float(os.environ.get("DECISION_MAKER_ACT", 0.8))          # confident enough to act alone
# Ask the user only when Jev leans toward a problem (eval_guard.py: at 0.3, clean actions scoring
# 0.31-0.56 raised false alarms; with criteria they all scored < 0.5 and every real violation >= 0.76).
CONCERN = float(os.environ.get("DECISION_MAKER_CONCERN", 0.5))
RISKY_CONCERN = 0.3   # risky commands: a false alarm is cheap, a miss is not
FEATURES = ("rules", "scope", "ask", "stop", "prefetch")
# Defaults follow the mode the user picks after install (decide.py mode auto|manual): auto = prefetch
# (measured 20-30% faster, ~40% cheaper on find-type prompts); manual or not chosen = nothing automatic.
# `guard on <features>` / `guard off` always override the mode default.
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit", "apply_patch"}   # apply_patch: Codex file edits
PATCH_PATH = re.compile(r"^\*\*\* (?:(?:Add|Update|Delete) File|Move to): (.+?)\s*$", re.M)
# The agent host. Codex runs the same hooks (and sets CLAUDE_PLUGIN_ROOT for compatibility) but marks
# itself with PLUGIN_ROOT / a turn_id, can't "ask" from PreToolUse, and continues via Stop decision:block.
AGENT = "Claude"


def is_codex(event: dict) -> bool:
    return bool(os.environ.get("PLUGIN_ROOT")) or "turn_id" in event


def jev_cmd(arg: str = "") -> str:
    """How the user reaches the status/mode switch on this host."""
    if AGENT == "Codex":
        return f'ask Codex "$decision-maker {arg or "status"}"'
    return f"/decision-maker:jev {arg}".strip()


def edit_paths(inp: dict, cwd=None) -> list:
    """Files an edit touches: file_path/notebook_path (Claude) or the paths inside a Codex apply_patch."""
    fp = inp.get("file_path") or inp.get("notebook_path")
    if fp:
        return [fp]
    paths = PATCH_PATH.findall(inp.get("command", "") if isinstance(inp.get("command"), str) else "")
    return [p if os.path.isabs(p) or not cwd else os.path.join(cwd, p) for p in dict.fromkeys(paths)]
DIR_RULE_FILES = ("AGENTS.md", "CLAUDE.md")                  # checked in every dir, file → repo root
ROOT_RULE_FILES = (".claude/CLAUDE.md", "CLAUDE.local.md")   # checked at the repo root only
MAX_RULES = 40
# Commands that only read: no rule or scope can be broken by them, so no Jev call at all.
READ_ONLY = re.compile(r"^\s*(ls|cat|head|tail|wc|pwd|echo|which|file|stat|tree|grep|rg|ag|find|fd|du|df|"
                       r"git\s+(status|log|diff|show|branch|ls-files|blame|rev-parse))\b")
MAX_SESSION_RULES = 20
MAX_CHARS = 20000   # per state field, keeps well inside Jev's 32k-token state budget
TIMEOUT_S = 8.0

# ------------------------------------------------- questions (tune here)
Q_VIOLATES = "Does the proposed `action` violate `rule`? Answer yes only if doing `action` breaks the rule."
Q_SCOPE = ("Is `action` outside what `request` asked for, unrelated to it or beyond its scope? "
           "Supporting changes the request needs (tests, imports, callers, docs of the changed code) are in scope.")
C_VIOLATES = {"true": "Doing `action` breaks `rule`: it does what the rule forbids, or skips what it requires, "
                      "for the exact files, folders, commands or packages the rule names.",
              "false": "`action` complies with `rule`, or the rule does not apply to it (different files, folders, "
                       "commands, or topic). Running, reading or listing something is not editing it."}
C_SCOPE = {"true": "`action` changes something the user did not ask for and that the request does not need.",
           "false": "`action` is part of the request or directly supports it (the asked-for code, its tests, "
                    "imports, callers, config or docs it needs), even if the request did not name that file."}
Q_RISKY = ("Could `action` delete data, rewrite git history, push or publish to a remote, "
           "send messages, or affect production systems?")
Q_USER_ONLY = ("Is `question` a decision only the user can make: their personal preference or taste, "
               "credentials or accounts, spending money, or an irreversible or outward-facing action "
               "(deleting data, publishing, pushing, sending messages)?")
Q_STANDING = ("Is `sentence` a standing instruction from the user about HOW to work for the rest of the "
              "session (a constraint, prohibition, or required tool, file, or style, e.g. 'don't touch the "
              "tests', 'use pnpm', 'never commit', 'keep answers short') rather than the task itself or a question?")
Q_REVOKES = "Does the user's new `prompt` cancel, relax, or replace `rule`?"
Q_FIND = ("Is `prompt` asking to find, list, locate or filter which files in this codebase (or which lines of "
          "a named file) match a described meaning or criterion?")
# Short question + criteria: a long compound question made Jev unsure about everything; criteria moved the
# look-alikes (right action, wrong party) from confident hits into "unsure", where Claude reads the excerpt.
Q_ITEM = "Is {item} one of the things the user's request in `context` asks to find?"
C_ITEM = {"true": "It matches what the request describes, judged by what it actually does or says, including who "
                  "or what it is for.",
          "false": "It does not match: it only mentions the topic in text or names, or it does a similar thing for "
                   "a different party or purpose than the request names."}
PREFETCH_MAX = int(os.environ.get("DECISION_MAKER_PREFETCH_MAX", 1000))   # files scanned per prompt
PREFETCH_BYTES = 200_000                                                     # skip larger files
SKIP_DIRS = {".git", "node_modules", "dist", "build", ".venv", "venv", "__pycache__", ".next", "target", "vendor"}
SKIP_EXT = {".lock", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".gz", ".woff", ".woff2", ".ttf",
            ".mp4", ".mp3", ".svg", ".min.js", ".map", ".pyc", ".so", ".dylib", ".exe", ".bin", ".jar"}
# Never send these to the provider, whatever the prompt.
SECRET_FILE = re.compile(r"(^|/)(\.env(\..*)?|\.npmrc|\.pypirc|\.netrc|id_(rsa|dsa|ecdsa|ed25519)(\.pub)?|"
                         r"[^/]*(secret|credential|password|token)[^/]*|[^/]*\.(pem|key|p12|pfx|crt|cer|jks|keystore))$",
                         re.I)
CONTEXT_CHARS = 9000                                                         # hooks cap context at 10,000
Q_MISSING = "Does `request` ask for something that `changes` do not do yet?"
Q_EXTRA = "Do `changes` include edits unrelated to `request`?"


NOTE = {}   # what this hook invocation asked Jev, and the outcome when it stayed silent


def enabled(feature: str) -> bool:
    raw = os.environ.get("DECISION_MAKER_GUARD")
    if raw is None:
        cfg = decide.load_config()
        raw = cfg.get("guard", decide.default_features(cfg))
    raw = raw if isinstance(raw, str) else ",".join(raw)
    vals = {v.strip().lower() for v in raw.split(",") if v.strip()}
    if feature == "prefetch":   # sends file contents to the provider: only when named explicitly
        return "prefetch" in vals
    return bool(vals & {"1", "all", "on", "true"}) or feature in vals


def clip(text: str, n: int = MAX_CHARS) -> str:
    return text if len(text) <= n else text[:n] + f"\n…[{len(text) - n} chars cut]"


# ------------------------------------------------------------- transcript

def _entries(path):
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    yield json.loads(line)
                except ValueError:
                    continue
    except OSError:
        return


def _user_text(entry):
    """Text of a real user prompt, or None for tool results / meta entries."""
    if entry.get("type") != "user" or entry.get("isMeta"):
        return None
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, list):
        if any(p.get("type") == "tool_result" for p in content if isinstance(p, dict)):
            return None
        content = "\n".join(p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text")
    if not isinstance(content, str) or not content.strip():
        return None
    m = re.search(r"<command-args>(.*?)</command-args>", content, re.S)
    if m:
        return m.group(1).strip() or None
    if content.lstrip().startswith("<"):  # command output, local-command stdout, reminders
        return None
    return content.strip()


def read_transcript(path, keep=3):
    """(last `keep` user prompts joined, files edited since the latest prompt)."""
    prompts, touched = [], []
    for e in _entries(path) if path else ():
        text = _user_text(e)
        if text:
            prompts.append(text)
            touched = []
            continue
        if e.get("type") == "assistant":
            for p in (e.get("message") or {}).get("content") or []:
                if isinstance(p, dict) and p.get("type") == "tool_use" and p.get("name") in EDIT_TOOLS:
                    fp = (p.get("input") or {}).get("file_path") or (p.get("input") or {}).get("notebook_path")
                    if fp and fp not in touched:
                        touched.append(fp)
    request = "\n---\n".join(prompts[-keep:])
    return clip(request, 6000), touched


def _session_file(event):
    sid = re.sub(r"[^A-Za-z0-9_-]", "", str(event.get("session_id") or ""))
    return decide.config_path().parent / "sessions" / f"{sid}.json" if sid else None


def load_session(event) -> dict:
    f = _session_file(event)
    try:
        return json.loads(f.read_text(encoding="utf-8")) if f else {}
    except (OSError, ValueError):
        return {}


def save_session(event, state: dict):
    f = _session_file(event)
    if f:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(state), encoding="utf-8")


def context(event):
    """(request, files edited this turn). Hook-recorded state first: the transcript
    file is written asynchronously and can lag the current turn."""
    t_request, t_touched = read_transcript(event.get("transcript_path"))
    s = load_session(event)
    request = clip("\n---\n".join(s.get("prompts", [])), 6000) or t_request
    touched = list(dict.fromkeys(s.get("touched", []) + t_touched))
    return request, touched


def remember_prompt(event):
    prompt = (event.get("prompt") or "").strip()
    m = re.search(r"<command-args>(.*?)</command-args>", prompt, re.S)
    prompt = m.group(1).strip() if m else prompt
    if not prompt:
        return None
    s = load_session(event)
    s.update(prompts=(s.get("prompts", []) + [prompt])[-3:], touched=[])
    notes, ctx = [], None
    old = s.get("rules", [])
    # ONE call for everything this prompt needs: rule extraction/revocation + "is this a find task?"
    qs = rule_questions(prompt, old)[0] if enabled("rules") else {}
    if enabled("prefetch"):
        qs["find"] = {"type": "noul", "instructions": Q_FIND}
    answers = {}
    if qs:
        NOTE.update(what="read your prompt (" + " + ".join(
            ([f"rules"] if enabled("rules") else []) + (["find-task check"] if enabled("prefetch") else [])) + ")",
            ok="no new rules" * enabled("rules") + (", " if enabled("rules") and enabled("prefetch") else "") +
               "not a find task" * enabled("prefetch"))
        try:
            answers = ask_jev({"prompt": clip(prompt, 6000)}, qs)
        except Exception as e:
            log({"event": "UserPromptSubmit", "error": f"{type(e).__name__}: {e}"})
    if enabled("rules") and answers:
        s["rules"] = update_session_rules(prompt, old, answers)
        added = [r for r in s["rules"] if r not in old]
        dropped = [r for r in old if r not in s["rules"]]
        if added or dropped:
            notes.append(notice("rules", ([f"now enforcing: \"{r}\"" for r in added] +
                                          [f"no longer enforcing: \"{r}\"" for r in dropped])))
    save_session(event, s)
    find = answers.get("find", {}).get("noul", 0)
    if find >= ACT:
        try:
            ctx, note = prefetch(prompt, event.get("cwd") or os.getcwd(), find)
            notes.append(note)
        except Exception as e:  # fail open: Claude just works without the pre-scan
            log({"event": "prefetch", "error": f"{type(e).__name__}: {e}"})
    out = {}
    if notes:
        out["systemMessage"] = "\n".join(notes)
    if ctx:
        out["hookSpecificOutput"] = {"hookEventName": "UserPromptSubmit", "additionalContext": ctx}
    return out or None


def repo_files(cwd: str) -> list:
    """Text files of the repo: `git ls-files` when available, else a walk; skips vendored, binary, huge."""
    root = Path(cwd)
    try:
        names = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=cwd, capture_output=True,
                               text=True, timeout=5, check=True).stdout.splitlines()
    except (OSError, subprocess.SubprocessError):
        names = [str(f.relative_to(root)) for f in root.rglob("*") if f.is_file()]
    out = []
    for n in names:
        parts = Path(n).parts
        if any(p in SKIP_DIRS for p in parts) or any(n.endswith(e) for e in SKIP_EXT) or SECRET_FILE.search(n):
            continue
        f = root / n
        try:
            if f.stat().st_size > PREFETCH_BYTES:
                continue
        except OSError:
            continue
        out.append(n)
        if len(out) >= PREFETCH_MAX:
            break
    return out


def prefetch_items(prompt: str, cwd: str) -> list:
    """Lines of the one file the prompt names (when it asks about lines), else every repo file."""
    files = repo_files(cwd)
    named = [f for f in files if f in prompt or (Path(f).name in prompt and len(Path(f).name) > 4)]
    if len(named) == 1 and re.search(r"\blines?\b", prompt, re.I):
        lines = (Path(cwd) / named[0]).read_text(encoding="utf-8", errors="replace").splitlines()
        return [(f"{named[0]}:{n}", l.strip()) for n, l in enumerate(lines, 1) if l.strip()]
    items = []
    for f in files:
        try:
            text = (Path(cwd) / f).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        items.append((f, text[:decide.ITEM_CHARS]))
    return items


def prefetch(prompt: str, cwd: str, p_find: float):
    """Scan the repo with Jev before Claude's first turn, so it can answer without tool calls."""
    t0 = time.monotonic()
    items = prefetch_items(prompt, cwd)
    if not items:
        return None, notice("pre-scan", ["no text files to scan"])
    prov = decide.resolve(decide.load_config())
    answers, labels, texts, tokens = decide.classify_items(
        prov, items, {"hit": {"type": "noul", "instructions": Q_ITEM, "criteria": C_ITEM}}, clip(prompt, 4000),
        ACT, 1, 15)
    rows = sorted(((labels[int(k.split("#")[1])], a, texts[int(k.split("#")[1])]) for k, a in answers.items()),
                  key=lambda r: -r[1]["noul"])
    hits = [r for r in rows if r[1]["noul"] >= 0.5 and r[1]["act"]]
    unsure = [r for r in rows if not r[1]["act"]]
    secs = time.monotonic() - t0
    lines = [f"Jev pre-scan (decision-maker hook): this prompt was judged a find/filter task (p={p_find:.2f}), "
             f"so Jev already checked all {len(items)} {'lines' if ':' in labels[0] else 'files'} against it "
             f"(question: \"{Q_ITEM.replace('{item}', 'this item')}\").",
             f"Relevant, confident (trust these): {len(hits)}"]
    lines += [f"- {lab} ({a['noul']:.2f})" for lab, a, _ in hits]
    lines.append(f"Unsure (judge from the excerpt): {len(unsure)}")
    lines += [f"- {lab} ({a['noul']:.2f}): {decide.excerpt(t)}" for lab, a, t in unsure]
    lines.append("Everything else was judged not relevant with confidence. Answer from this directly: decide each "
                 "unsure item from its excerpt yourself, and open a file only if its excerpt is cut off and still "
                 "ambiguous, or you need details the request asks for.")
    ctx = clip("\n".join(lines), CONTEXT_CHARS)
    log({"event": "prefetch", "items": len(items), "hits": len(hits), "unsure": len(unsure),
         "latency_s": round(secs, 2), "tokens": tokens})
    return ctx, notice("pre-scan", [f"checked {len(items)} items in {secs:.1f}s: {len(hits)} relevant, "
                                    f"{len(unsure)} unsure; handed to {AGENT}"])


def split_sentences(text: str) -> list:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip(" -*\t") for p in parts if 8 <= len(p.strip()) <= 300][:40]


def rule_questions(prompt: str, rules: list):
    sentences = split_sentences(prompt)
    qs = {f"new{i}": {"type": "noul", "instructions": {"sentence": t, "question": Q_STANDING}}
          for i, t in enumerate(sentences)}
    qs.update({f"old{j}": {"type": "noul", "instructions": {"rule": r, "question": Q_REVOKES}}
               for j, r in enumerate(rules)})
    return qs, sentences


def update_session_rules(prompt: str, rules: list, answers=None) -> list:
    """Temporary rules from the conversation: keep the ones this prompt doesn't revoke,
    add the standing instructions it gives. Select, don't generate: each rule is a
    verbatim sentence the user wrote. Pass `answers` when they came from a shared call."""
    qs, sentences = rule_questions(prompt, rules)
    if not qs:
        return rules
    try:
        a = answers if answers is not None else ask_jev({"prompt": clip(prompt, 6000)}, qs)
    except Exception as e:  # keep the old rules if Jev is unreachable
        log({"event": "UserPromptSubmit", "error": f"{type(e).__name__}: {e}"})
        return rules
    kept = [r for j, r in enumerate(rules) if a.get(f"old{j}", {}).get("noul", 0) < ACT]
    added = [t for i, t in enumerate(sentences) if a.get(f"new{i}", {}).get("noul", 0) >= ACT]
    out = list(dict.fromkeys(kept + added))[-MAX_SESSION_RULES:]
    log({"event": "UserPromptSubmit", "session_rules": out,
         "revoked": [r for r in rules if r not in kept], "added": added})
    return out


def remember_edit(event):
    paths = edit_paths(event.get("tool_input") or {}, event.get("cwd"))
    if paths:
        s = load_session(event)
        new = [p for p in paths if p not in s.setdefault("touched", [])]
        if new:
            s["touched"] += new
            save_session(event, s)


# ------------------------------------------------------------------ rules

def rule_files(cwd: str, target=None) -> list:
    """Nearest first: rule files from the edited file's dir up to the repo root
    (the DOX chain), then root-only files, then the user's global CLAUDE.md."""
    root = Path(cwd).resolve()
    dirs = [root]
    if target:
        t = Path(target).resolve().parent
        if t == root or root in t.parents:
            dirs = [t, *[d for d in t.parents if d == root or root in d.parents]]
    files = [d / f for d in dirs for f in DIR_RULE_FILES]
    return files + [root / f for f in ROOT_RULE_FILES] + [Path.home() / ".claude" / "CLAUDE.md"]


def load_rules(cwd: str, target=None, session_rules=()) -> list:
    """[(rule, source)]: the user's in-conversation rules first (most specific and
    most recent), then directive bullet lines from the rule files, nearest first."""
    rules = [(r, "your instruction this session") for r in session_rules]
    seen = set(session_rules)
    root = Path(cwd).resolve()
    for f in rule_files(cwd, target):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        src = str(f.relative_to(root)) if root in f.parents else str(f).replace(str(Path.home()), "~")
        for line in text.splitlines():
            m = re.match(r"\s*(?:[-*+]|\d+[.)])\s+(.*)", line)
            r = m.group(1).strip() if m else ""
            if 15 <= len(r) <= 300 and r not in seen:
                seen.add(r)
                rules.append((r, src))
    # ponytail: first MAX_RULES only; rank rules by relevance to the action if repos outgrow it
    return rules[:MAX_RULES]


def describe_action(tool: str, inp: dict) -> str:
    if tool == "Bash":
        return f"Run shell command: {inp.get('command', '')}\n(description: {inp.get('description', '')})"
    if tool == "apply_patch":
        return f"Apply patch (file edits):\n{inp.get('command', '')}"
    path = inp.get("file_path") or inp.get("notebook_path", "")
    if tool == "Write":
        return f"Write file {path}:\n{inp.get('content', '')}"
    if tool == "Edit":
        return f"Edit {path}: replace\n{inp.get('old_string', '')}\nwith\n{inp.get('new_string', '')}"
    if tool == "MultiEdit":
        parts = [f"replace\n{e.get('old_string', '')}\nwith\n{e.get('new_string', '')}" for e in inp.get("edits", [])]
        return f"Edit {path}:\n" + "\n...\n".join(parts)
    return f"{tool} {path}: {json.dumps(inp)[:4000]}"


# -------------------------------------------------------------------- jev

def ask_jev(state, questions):
    p = decide.resolve(decide.load_config())
    decide.validate(questions)
    t0 = time.monotonic()
    out = decide.http(p, "POST", p["path"], {"state": state, "model": p["model"], "questions": questions},
                      retries=1, timeout=TIMEOUT_S)
    log({"provider": p["name"], "latency_s": round(time.monotonic() - t0, 3), "answers": out.get("answers")})
    return out.get("answers", {})


def log(record):
    """Append to guard.log next to the provider config, for tuning thresholds."""
    try:
        path = decide.config_path().parent / "guard.log"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **record}) + "\n")
    except OSError:
        pass


def notice(what: str, lines: list) -> str:
    """The line the USER sees (systemMessage); Claude gets the reason separately."""
    return f"⚖ Jev guard ({what}): " + ("\n  • ".join([""] + lines) if len(lines) > 1 else lines[0])


def pre_tool_decision(decision, reason, user_note):
    if decision == "ask" and AGENT == "Codex":   # unsupported there: it would fail the hook and run the tool
        decision = "deny"
        reason = ("Not confident this is OK. Ask the user in chat to confirm before doing it, and say why:\n"
                  + reason)
        user_note += "\n  • Codex hooks can't prompt you, so Codex was told to ask you in chat first"
    return {"systemMessage": user_note,
            "hookSpecificOutput": {"hookEventName": "PreToolUse",
                                   "permissionDecision": decision,
                                   "permissionDecisionReason": reason}}


def short_target(tool, inp, cwd=None):
    if tool == "Bash":
        return inp.get("command", "")[:80]
    paths = edit_paths(inp, cwd)
    shown = [os.path.relpath(p, cwd) if cwd and p.startswith(str(cwd).rstrip("/") + "/") else p for p in paths]
    return (shown[0] + (f" (+{len(shown) - 1} more)" if len(shown) > 1 else "")) if shown else ""


def classify(qid: str, a: dict, act: float, concern: float) -> str:
    """The guard's policy for one logged answer, as a pure function of thresholds."""
    fam = qid.rstrip("0123456789")
    p, conf = a.get("noul"), a.get("confidence")
    if fam in ("rule", "scope"):
        return "deny" if p >= act else "ask" if p >= concern else "pass"
    if fam == "risky":
        return "ask" if p >= RISKY_CONCERN else "pass"
    if fam in ("missing", "extra"):
        return "send-back" if p >= act else "pass"
    if fam == "new":
        return "rule-added" if p >= act else "pass"
    if fam == "old":
        return "rule-dropped" if p >= act else "pass"
    if fam == "q":
        return "auto-answer" if conf is not None and conf >= act else "to-user"
    if fam == "user":
        return "to-user" if p >= RISKY_CONCERN else "pass"
    return "other"


def replay(act: float, concern: float) -> dict:
    """Re-score every logged Jev answer under other thresholds, with no new inference.
    Returns {decision: (count now, count with the new thresholds)}."""
    path = decide.config_path().parent / "guard.log"
    counts = {}
    for line in path.read_text(encoding="utf-8").splitlines() if path.exists() else []:
        rec = json.loads(line)
        for qid, a in (rec.get("answers") or {}).items():
            now, new = classify(qid, a, ACT, CONCERN), classify(qid, a, act, concern)
            c = counts.setdefault(now, [0, 0])
            c[0] += 1
            counts.setdefault(new, [0, 0])[1] += 1
    return {k: tuple(v) for k, v in sorted(counts.items())}


# ----------------------------------------------------------------- checks

def read_only(command: str) -> bool:
    """Every `;`/`&&`/`|` segment is a read-only command, with no redirect, -delete or -exec."""
    if re.search(r"(^|[^2&])>|-delete|-exec|\bsed\s+-i|\btee\b", command):
        return False
    parts = [p for p in re.split(r"&&|\|\||;|\|", command) if p.strip()]
    return bool(parts) and all(READ_ONLY.match(p) for p in parts)


def check_action(event):
    tool, inp = event.get("tool_name"), event.get("tool_input") or {}
    if tool == "Bash" and read_only(inp.get("command", "")):
        return None
    request, _ = context(event)
    target = (edit_paths(inp, event.get("cwd")) or [None])[0]
    rules = (load_rules(event.get("cwd") or os.getcwd(), target, load_session(event).get("rules", []))
             if enabled("rules") else [])
    qs = {}
    for i, (rule, _src) in enumerate(rules):
        qs[f"rule{i}"] = {"type": "noul", "instructions": {"rule": rule, "question": Q_VIOLATES},
                          "criteria": C_VIOLATES}
    if enabled("scope") and request:
        qs["scope"] = {"type": "noul", "instructions": Q_SCOPE, "criteria": C_SCOPE}
    if tool == "Bash" and enabled("rules"):
        qs["risky"] = {"type": "noul", "instructions": Q_RISKY}
    if not qs:
        return None
    what = f"{tool} {short_target(tool, inp, event.get('cwd'))}".strip()
    NOTE.update(what=f"checked {what} against {len(rules)} rule{'s' if len(rules) != 1 else ''}"
                     + (" + scope" if "scope" in qs else "") + (" + risk" if "risky" in qs else ""), ok="OK, allowed")
    answers = ask_jev({"request": request or "(unknown)", "action": clip(describe_action(tool, inp))}, qs)

    deny, ask = [], []
    for qid, a in answers.items():
        p = a.get("noul", 0.0)
        label = (f"rule from {rules[int(qid[4:])][1]}: {rules[int(qid[4:])][0]}" if qid.startswith("rule")
                 else {"scope": "outside what the user asked for", "risky": "risky or irreversible command"}[qid])
        if qid == "risky":  # risky never auto-denies: the user decides
            if p >= RISKY_CONCERN:
                ask.append(f"{label} (p={p:.2f})")
        elif p >= ACT:
            deny.append(f"{label} (p={p:.2f})")
        elif p >= CONCERN:
            ask.append(f"{label} (p={p:.2f})")
    log({"event": "PreToolUse", "tool": tool, "deny": deny, "ask": ask})
    what = f"{tool} {short_target(tool, inp, event.get("cwd"))}".strip()
    if deny:
        return pre_tool_decision("deny", "Jev guard blocked this action:\n- " + "\n- ".join(deny) +
                                 "\nAdjust it to comply with the rule / the user's request. If you believe the "
                                 "check is wrong, say why to the user instead of retrying the same action.",
                                 notice("blocked", [f"BLOCKED {what}"] + deny + [f"{AGENT} was told to adjust. "
                                        f"Tell {AGENT} if the block is wrong."]))
    if ask:
        return pre_tool_decision("ask", "Jev guard is unsure about this action:\n- " + "\n- ".join(ask),
                                 notice("needs you", [f"unsure about {what}"] + ask +
                                        ["approve or reject below"]))
    return None


def answer_question(event):
    """AskUserQuestion: let Jev pick when it is confident and the call isn't the user's alone."""
    questions = (event.get("tool_input") or {}).get("questions") or []
    if not questions or any(q.get("multiSelect") for q in questions):
        return None
    request, _ = context(event)
    qs = {}
    for i, q in enumerate(questions):
        opts = {o["label"]: o.get("description") for o in q.get("options", []) if o.get("label")}
        if len(opts) < 2:
            return None
        qs[f"q{i}"] = {"type": "choice", "criteria": opts,
                       "instructions": {"question": q.get("question", ""),
                                        "task": "Pick the option that best serves `request`."}}
        qs[f"user{i}"] = {"type": "noul", "instructions": {"question": q.get("question", ""), "ask": Q_USER_ONLY}}
    NOTE.update(what=f"tried to answer {AGENT}'s question for you", ok="not confident or your call: asking you")
    answers = ask_jev({"request": request or "(unknown)"}, qs)
    picks = []
    for i, q in enumerate(questions):
        c, u = answers.get(f"q{i}", {}), answers.get(f"user{i}", {})
        if c.get("confidence", 0) < ACT or u.get("noul", 1.0) >= RISKY_CONCERN:  # maybe the user's call: ask
            log({"event": "AskUserQuestion", "decided": False, "answers": answers})
            return None  # not confident, or the user's call: let the question through
        picks.append(f"- {q.get('question', '')} → {c['choice']} (confidence {c['confidence']:.2f})")
    log({"event": "AskUserQuestion", "decided": True, "picks": picks})
    return pre_tool_decision("deny", "Jev decided instead of asking the user (all answers confident):\n" +
                             "\n".join(picks) + "\nProceed with these answers and tell the user in one line "
                             "what was chosen. Ask again only if you have information Jev lacked.",
                             notice("answered for you", [p.lstrip("- ") for p in picks] +
                                    [f"tell {AGENT} if you want a different answer"]))


def check_stop(event):
    if event.get("stop_hook_active"):
        return None  # already blocked once this turn: never loop
    request, touched = context(event)
    if not request or not touched:
        return None  # nothing edited this turn (a question, a review): nothing to compare
    cwd = event.get("cwd") or os.getcwd()
    try:
        diff = subprocess.run(["git", "diff", "HEAD", "--", *touched], cwd=cwd, capture_output=True,
                              text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        diff = ""
    if not diff.strip():
        diff = "Files edited this turn: " + ", ".join(touched)
    NOTE.update(what=f"compared this turn's changes ({len(touched)} file{'s' if len(touched) != 1 else ''}) with your request",
                ok="complete, nothing unrelated")
    answers = ask_jev({"request": request, "changes": clip(diff)},
                      {"missing": {"type": "noul", "instructions": Q_MISSING},
                       "extra": {"type": "noul", "instructions": Q_EXTRA}})
    problems = []
    if answers.get("missing", {}).get("noul", 0) >= ACT:
        problems.append(f"the request asks for something these changes don't do yet "
                        f"(p={answers['missing']['noul']:.2f})")
    if answers.get("extra", {}).get("noul", 0) >= ACT:
        problems.append(f"the changes include edits unrelated to the request (p={answers['extra']['noul']:.2f})")
    log({"event": "Stop", "touched": touched, "problems": problems})
    if not problems:
        return None
    if AGENT == "Codex":   # Codex continues the agent from decision:block + reason
        return {"decision": "block", "reason": "Jev guard, request vs. diff: " + "; ".join(problems) +
                ". Re-read the user's request, finish or revert as needed, or explain to the user why it's complete.",
                "systemMessage": notice("request vs. diff", problems + ["Codex was sent back to finish or revert"])}
    # additionalContext (not decision:block): same loop protection, shown as "Stop hook feedback", not an error
    return {"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext":
                "Jev guard, request vs. diff: " + "; ".join(problems) +
                ". Re-read the user's request, finish or revert as needed, or explain to the user why it's complete."},
            "systemMessage": notice("request vs. diff", problems + [f"{AGENT} was sent back to finish or revert"])}


def status_lines(p) -> list:
    """What Jev does in this Claude Code install, right now: the user-facing summary."""
    d = Path(__file__).resolve().parent
    if p is None:
        return ["decision-maker is installed but INACTIVE: no Jev provider key, so nothing is sent anywhere.",
                f"  Set one: python3 {d / 'decide.py'} provider edit openjev --api-key KEY --default "
                "(or export TYPESAFE_API_KEY before starting claude)",
                f"  Then choose how to use it: {jev_cmd('auto')} (by default) or {jev_cmd('manual')} (only when you ask).",
                f"  {jev_cmd()} explains what it does."]
    cfg = decide.load_config()
    mode = decide.mode_of(cfg)
    on = [f for f in FEATURES if enabled(f)]
    sent = []
    if any(f in on for f in ("rules", "scope", "ask", "stop")):
        sent.append(f"your prompts, {AGENT}'s proposed edits/commands/questions and diffs (guard)")
    if "prefetch" in on:
        sent.append("repo file contents for find-type prompts (prefetch; secrets/.env skipped)")
    mode_line = {
        None: f"  • Mode: NOT CHOSEN, so nothing runs automatically. Choose once: {jev_cmd('auto')} "
              f"(use Jev by default) or {jev_cmd('manual')} (only when you ask)",
        "auto": "  • Mode: auto. Prefetch pre-scans \"which files…\" prompts, and " + AGENT + " uses Jev for batch sorting "
                f"and browser steps by default (switch: {jev_cmd('manual')})",
        "manual": "  • Mode: manual. Jev runs only when you ask: /decision-maker:decision-maker, or \"use Jev\" "
                  f"(switch: {jev_cmd('auto')})"}[mode]
    return [f"decision-maker active: Jev via {p['name']} ({p['base_url']})",
            mode_line,
            "  • Guard hooks: " + (", ".join(on) if on else "off (nothing is checked automatically)") +
            (" (mode default)" if "guard" not in cfg and os.environ.get("DECISION_MAKER_GUARD") is None else "") +
            "  · turn on/off: decide.py guard on|off [rules scope ask stop prefetch]",
            "  • Sent to the provider: " + ("; ".join(sent) if sent else f"only what {AGENT} explicitly asks Jev"),
            f"  • Every Jev call is shown to you · history: decide.py usage / guard log · details: {jev_cmd()}"]


def changed_since_last_notice(text: str) -> bool:
    """Show the status only when what Jev does has changed (install, key, features), not every session."""
    import hashlib
    f = decide.config_path().parent / "notified.json"
    digest = hashlib.sha256(text.encode()).hexdigest()
    try:
        if json.loads(f.read_text(encoding="utf-8")).get("status") == digest:
            return False
    except (OSError, ValueError):
        pass
    try:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({"status": digest}), encoding="utf-8")
    except OSError:
        pass
    return True


def session_start():
    """SessionStart: tell the user what Jev does here (when that changed), and hand Claude the
    ready-to-run commands so it can skip loading the skill. No Jev call."""
    try:
        p = decide.resolve(decide.load_config())
    except decide.DecideError:
        p = None
    out = {}
    lines = status_lines(p)
    unchosen = p is not None and decide.mode_of(decide.load_config()) is None
    # Until the user picks a mode, remind every session; afterwards only when something changes.
    if changed_since_last_notice("\n".join(lines)) or unchosen:
        out["systemMessage"] = "⚖ " + "\n".join(lines)
    hint = session_hint(p) if p and decide.mode_of(decide.load_config()) == "auto" else None
    if hint:
        out["hookSpecificOutput"] = hint
    return out or None


def session_hint(p):
    """The ready-to-run batch and browser commands for Claude (~80 tokens)."""
    if os.environ.get("DECISION_MAKER_HINT", "1") == "0":
        return None
    cmd = f"python3 {Path(__file__).resolve().parent / 'decide.py'}"
    return {"hookEventName": "SessionStart", "additionalContext":
            f"decision-maker is configured (Jev via {p['name']}). To sort or filter many files/lines by meaning, "
            f"run this first instead of grepping or reading them (no need to load the skill): "
            f"{cmd} ask --items 'GLOB_OR_FILE' --brief --noul hit 'Does {{item}} <precise criterion, incl. what does "
            f"NOT count>?' It prints the hits plus unsure items with excerpts: trust 'act' lines, judge 'ask' "
            f"lines from their excerpts. For browser test steps: node {Path(__file__).resolve().parent / 'browser_steps.mjs'} "
            f"--url URL --steps 'step 1' 'step 2' ... (needs playwright-core; exit 3 = do that step yourself)."}


JEV_CMD = re.compile(r"decide\.py|browser_steps\.mjs")


def report_claude_usage(event):
    """PostToolUse(Bash): Claude ran decide.py / the browser runner. Tell the user what Jev did."""
    cmd = (event.get("tool_input") or {}).get("command", "")
    if not JEV_CMD.search(cmd):
        return None
    f = decide.config_path().parent / "usage.log"
    since = time.time() - (event.get("duration_ms") or 60000) / 1000 - 2
    try:
        recs = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines()[-500:]]
    except (OSError, ValueError):
        return None
    # ponytail: time-window match; two sessions running Jev at the same second could share a line
    recs = [r for r in recs if r.get("ts", 0) >= since and r.get("source") != "hook"]
    if not recs:
        return None
    who = "browser runner" if any(r["source"] == "browser" for r in recs) else f"{AGENT} (decide.py)"
    return {"systemMessage": f"⚖ Jev used by {who}: {decide.summarize(recs)} via {recs[-1].get('provider')}"}


def with_usage(out, calls):
    """Every Jev call a hook made is shown to the user: interventions get a usage line, passes get one line."""
    if not calls:
        return out
    stats = decide.summarize(calls)
    out = out or {}
    if any(c.get("error") for c in calls):
        err = next(c["error"] for c in calls if c.get("error"))
        line = f"⚖ Jev unavailable ({err[:80]}): continued without it ({stats})"
    elif out.get("systemMessage"):
        out["systemMessage"] += f"\n  ({NOTE.get('what', 'Jev')}: {stats})"
        return out
    else:
        line = f"⚖ Jev {NOTE.get('what', 'was used')} → {NOTE.get('ok', 'done')} ({stats})"
    out["systemMessage"] = (out["systemMessage"] + "\n" + line) if out.get("systemMessage") else line
    return out


RELAY_EVENTS = ("SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse")


def relay_for_codex(out, name):
    """Codex may not display hook systemMessages (codex exec shows none), so also hand the notice to the
    model as context with an instruction to tell the user. Not combined with a deny: its reason carries it."""
    if AGENT != "Codex" or not out or not out.get("systemMessage") or name not in RELAY_EVENTS:
        return out
    hso = out.setdefault("hookSpecificOutput", {"hookEventName": name})
    if "permissionDecision" in hso:
        return out
    relay = ("Jev activity (the user may not see hook messages in Codex, so tell them in one short line "
             "in your next message): " + out["systemMessage"])
    hso["additionalContext"] = (hso.get("additionalContext", "") + "\n" + relay).strip()
    return out


def main():
    global AGENT
    os.environ["DECISION_MAKER_SOURCE"] = "hook"
    n0, out, name = len(decide.CALLS), None, None
    try:
        event = json.load(sys.stdin)
        AGENT = "Codex" if is_codex(event) else "Claude"
        name, tool = event.get("hook_event_name"), event.get("tool_name")
        if name == "SessionStart":
            out = session_start()
        elif name in ("PostToolUse", "PostToolUseFailure"):
            out = report_claude_usage(event)            # always: Claude's own Jev use, in any mode
        elif not any(enabled(f) for f in FEATURES):
            pass
        elif name == "UserPromptSubmit":
            out = remember_prompt(event)
        elif name == "PreToolUse" and tool == "AskUserQuestion" and enabled("ask"):
            out = answer_question(event)
        elif name == "PreToolUse" and tool in EDIT_TOOLS | {"Bash"}:
            if tool in EDIT_TOOLS:
                remember_edit(event)
            if enabled("rules") or enabled("scope"):
                out = check_action(event)
        elif name == "Stop" and enabled("stop"):
            out = check_stop(event)
    except Exception as e:  # fail open, always: a guard must never break the session
        log({"error": f"{type(e).__name__}: {e}"})
    out = with_usage(out, decide.CALLS[n0:])
    out = relay_for_codex(out, name)
    if out:
        print(json.dumps(out))
    elif AGENT == "Codex":
        print("{}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
