"""Tests for guard.py (the Claude Code hook). Run: python -m unittest test_guard -v

Reuses the fake System One server from test_decide; answers are set per question id.
"""
import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import guard
import threading
from http.server import HTTPServer

from test_decide import FakeSystemOne

NO, YES, MAYBE = {"type": "noul", "noul": 0.02}, {"type": "noul", "noul": 0.95}, {"type": "noul", "noul": 0.5}


def hook(event):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), mock.patch("sys.stdin", io.StringIO(json.dumps(event))):
        code = guard.main()
    assert code == 0  # a guard never fails the hook
    return json.loads(out.getvalue()) if out.getvalue().strip() else None


class TestGuard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), FakeSystemOne)
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        FakeSystemOne.calls.clear()
        FakeSystemOne.override = {}
        FakeSystemOne.fail_first = 0
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        (self.repo / "CLAUDE.md").write_text("# Rules\n- Never commit secrets or API keys to the repo\n"
                                             "- Use pnpm, never npm, for installing packages\n")
        cfg = self.root / "cfg" / "providers.json"
        env = {k: v for k, v in os.environ.items()
               if not k.startswith(("TYPESAFE_", "DECISION_MAKER_", "OPENROUTER_", "OPENJEV_", "LITELLM_"))}
        env.update(DECISION_MAKER_CONFIG=str(cfg), HOME=str(self.root), FAKE_KEY="good-key",
                   DECISION_MAKER_GUARD="all,prefetch")
        self.env = mock.patch.dict(os.environ, env, clear=True)
        self.env.start()
        import decide
        with contextlib.redirect_stdout(io.StringIO()):
            decide.main(["provider", "add", "fake", "--base-url", self.url, "--api-key-env", "FAKE_KEY", "--default"])
        self.prompt("add a login button", {"new0": NO})
        FakeSystemOne.calls.clear()

    def prompt(self, text, answers):
        FakeSystemOne.override = {"find": NO, **answers}
        self.last_prompt_out = hook({"hook_event_name": "UserPromptSubmit", "session_id": "s1", "prompt": text})
        FakeSystemOne.override = {}
        return guard.load_session({"session_id": "s1"}).get("rules", [])

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def pre(self, tool, tool_input):
        return hook({"hook_event_name": "PreToolUse", "session_id": "s1", "cwd": str(self.repo),
                     "tool_name": tool, "tool_input": tool_input})

    # -- rules + scope -------------------------------------------------

    def test_confident_violation_denies_with_rule(self):
        FakeSystemOne.override = {"rule0": NO, "rule1": YES, "scope": NO, "risky": NO}
        out = self.pre("Bash", {"command": "npm install left-pad"})
        d = out["hookSpecificOutput"]
        self.assertEqual(d["permissionDecision"], "deny")
        self.assertIn("never npm", d["permissionDecisionReason"])
        self.assertIn("BLOCKED Bash npm install left-pad", out["systemMessage"])  # the user sees it too
        body = FakeSystemOne.calls[-1][2]
        self.assertEqual(body["state"]["request"], "add a login button")   # prompt from UserPromptSubmit
        self.assertEqual(len(FakeSystemOne.calls), 1)                      # all checks in ONE call

    def test_unsure_asks_user(self):
        FakeSystemOne.override = {"rule0": NO, "rule1": NO, "scope": MAYBE}
        out = self.pre("Edit", {"file_path": "/x/a.py", "old_string": "a", "new_string": "b"})
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "ask")

    def test_guard_log_lists_interventions(self):
        FakeSystemOne.override = {"rule0": NO, "rule1": YES, "scope": NO, "risky": NO}
        self.pre("Bash", {"command": "npm i x"})
        import decide
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            decide.main(["guard", "log"])
        self.assertIn("BLOCKED Bash", buf.getvalue())

    def test_read_only_commands_skip_jev(self):
        for cmd in ["ls -la; cat src/app.js; git ls-files", "git status && git diff | head -50", "rg -n foo src"]:
            self.assertIsNone(self.pre("Bash", {"command": cmd}), cmd)
        self.assertEqual(FakeSystemOne.calls, [])
        for cmd in ["cat a > b", "find . -name '*.pyc' -delete", "ls && rm -rf dist", "sed -i s/a/b/ f"]:
            self.assertFalse(guard.read_only(cmd), cmd)

    def test_replay_rescores_log_without_calls(self):
        FakeSystemOne.override = {"rule0": {"type": "noul", "noul": 0.6}, "rule1": NO, "scope": NO, "risky": NO}
        self.pre("Bash", {"command": "npm i x"})
        n = len(FakeSystemOne.calls)
        rows = guard.replay(act=0.8, concern=0.7)
        self.assertEqual(rows["ask"], (1, 0))            # 0.6 asks now, passes at concern 0.7
        rows = guard.replay(act=0.55, concern=0.5)
        self.assertEqual(rows["deny"][1], 1)             # ... and denies at act 0.55
        self.assertEqual(len(FakeSystemOne.calls), n)    # no inference

    def test_session_start_tells_user_what_jev_does_once(self):
        os.environ["DECISION_MAKER_MODE"] = "auto"
        start = lambda: hook({"hook_event_name": "SessionStart", "session_id": "s1"})
        out = start()
        msg = out["systemMessage"]
        self.assertIn("decision-maker active: Jev via fake", msg)
        self.assertIn("Guard hooks: rules, scope, ask, stop, prefetch", msg)
        self.assertIn("repo file contents", msg)                    # says what leaves the machine
        self.assertIn("decide.py ask --items", out["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(FakeSystemOne.calls, [])                  # no Jev call
        self.assertNotIn("systemMessage", start())                 # unchanged → not repeated
        os.environ["DECISION_MAKER_GUARD"] = "rules"
        msg = start()["systemMessage"]                              # features changed → shown again
        self.assertIn("Guard hooks: rules ", msg)
        self.assertNotIn("repo file contents", msg)

    def test_session_start_without_key_explains_setup_once(self):
        os.environ["FAKE_KEY"] = ""
        out = hook({"hook_event_name": "SessionStart", "session_id": "s1"})
        self.assertIn("INACTIVE", out["systemMessage"])
        self.assertNotIn("hookSpecificOutput", out)                 # no hint without a key
        self.assertIsNone(hook({"hook_event_name": "SessionStart", "session_id": "s1"}))

    def test_session_hint_can_be_disabled(self):
        os.environ.update(DECISION_MAKER_MODE="auto", DECISION_MAKER_HINT="0")
        out = hook({"hook_event_name": "SessionStart", "session_id": "s1"})
        self.assertNotIn("hookSpecificOutput", out)

    # -- prefetch: Jev scans before Claude's first turn ---------------------

    def make_files(self):
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        for name, body in {"a.py": "def refund(p): gateway.refund(p)", "b.py": "def add(a, b): return a + b",
                           "c.py": "def credit_back(o): wallet.add(o.total)"}.items():
            (self.repo / name).write_text(body)

    def submit(self, text, answers):
        FakeSystemOne.override = answers
        return hook({"hook_event_name": "UserPromptSubmit", "session_id": "s1", "cwd": str(self.repo), "prompt": text})

    def test_prefetch_hands_claude_the_answer(self):
        self.make_files()
        files = guard.repo_files(str(self.repo))                     # git order: AGENTS? no: CLAUDE.md, a, b, c
        idx = {f: i for i, f in enumerate(files)}
        out = self.submit("Which files implement refund logic?", {
            "find": YES, f"hit#{idx['a.py']}": YES, f"hit#{idx['b.py']}": NO,
            f"hit#{idx['c.py']}": MAYBE, f"hit#{idx['CLAUDE.md']}": NO})
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("- a.py (0.95)", ctx)
        self.assertIn("- c.py (0.50): def credit_back", ctx)       # unsure carries its excerpt
        self.assertNotIn("b.py", ctx)
        self.assertIn("pre-scan", out["systemMessage"])            # the user sees it
        state = FakeSystemOne.calls[-1][2]["state"]
        self.assertEqual(state["context"], "Which files implement refund logic?")

    def test_prefetch_never_reads_secret_files(self):
        self.make_files()
        for n in [".env", ".env.local", "config/secrets.yaml", "deploy/server.pem", "id_rsa", "aws_credentials.json"]:
            f = self.repo / n
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("SECRET=1")
        files = guard.repo_files(str(self.repo))
        self.assertIn("a.py", files)
        for n in [".env", ".env.local", "config/secrets.yaml", "deploy/server.pem", "id_rsa", "aws_credentials.json"]:
            self.assertNotIn(n, files)

    def test_prefetch_lines_of_named_file(self):
        self.make_files()
        (self.repo / "hits.txt").write_text("SELECT * FROM orders\n# sort orders\n")
        out = self.submit("Which lines of hits.txt use the orders table?", {"find": YES, "hit#0": YES, "hit#1": NO})
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("all 2 lines", ctx)
        self.assertIn("- hits.txt:1 (0.95)", ctx)

    def test_no_prefetch_when_not_a_find_task(self):
        self.make_files()
        n = len(FakeSystemOne.calls)
        out = self.submit("Fix the crash in checkout", {"find": NO})
        self.assertIsNone((out or {}).get("hookSpecificOutput"))
        self.assertEqual(len(FakeSystemOne.calls), n + 1)          # just the one shared prompt call

    def test_prefetch_fails_open(self):
        self.make_files()
        with mock.patch.object(guard.decide, "classify_items", side_effect=RuntimeError("boom")):
            out = self.submit("Which files implement refund logic?", {"find": YES})
        self.assertIsNone((out or {}).get("hookSpecificOutput"))

    def test_claude_using_jev_is_reported_after_the_command(self):
        import decide
        os.environ["DECISION_MAKER_SOURCE"] = "cli"                   # as in Claude's own Bash process
        with contextlib.redirect_stdout(io.StringIO()):
            decide.main(["ask", "--state", "s", "--noul", "q", "Is it?"])
        out = hook({"hook_event_name": "PostToolUse", "tool_name": "Bash", "session_id": "s1", "duration_ms": 900,
                    "tool_input": {"command": "python3 /x/decide.py ask --state s --noul q 'Is it?'"}})
        self.assertIn("⚖ Jev used by Claude (decide.py): 1 call", out["systemMessage"])
        other = hook({"hook_event_name": "PostToolUse", "tool_name": "Bash", "session_id": "s1",
                      "tool_input": {"command": "ls"}})
        self.assertIsNone(other)                                        # unrelated commands: nothing

    def test_usage_command_lists_every_call(self):
        import decide
        FakeSystemOne.override = {"rule0": NO, "rule1": NO, "scope": NO, "risky": NO}
        self.pre("Bash", {"command": "npm i x"})                         # one hook call
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            decide.main(["usage"])
        self.assertIn("automatic (hooks): 2 calls", buf.getvalue())     # setUp's prompt check + this edit check

    # -- Codex: same hooks, its own tool names and output rules --------------

    PATCH = "*** Begin Patch\n*** Update File: tests/test_dates.py\n@@\n-assert a\n+assert b\n*** End Patch\n"

    def codex_pre(self, tool, tool_input):
        return hook({"hook_event_name": "PreToolUse", "session_id": "s1", "turn_id": "t1",
                     "cwd": str(self.repo), "tool_name": tool, "tool_input": tool_input})

    def test_codex_apply_patch_is_checked_against_rules(self):
        self.prompt("Fix the date parser. Don't touch the tests folder.", {"new0": NO, "new1": YES})
        FakeSystemOne.override = {"rule0": YES, "rule1": NO, "rule2": NO, "scope": NO}
        out = self.codex_pre("apply_patch", {"command": self.PATCH})
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("BLOCKED apply_patch tests/test_dates.py", out["systemMessage"])
        self.assertIn("Codex was told to adjust", out["systemMessage"])
        body = FakeSystemOne.calls[-1][2]
        self.assertIn("*** Update File: tests/test_dates.py", body["state"]["action"])
        # the patched file is remembered for the end-of-turn diff check
        self.assertEqual(guard.load_session({"session_id": "s1"})["touched"],
                         [str(self.repo / "tests" / "test_dates.py")])

    def test_codex_cannot_ask_so_it_denies_and_asks_in_chat(self):
        FakeSystemOne.override = {"rule0": NO, "rule1": NO, "scope": MAYBE}
        out = self.codex_pre("apply_patch", {"command": self.PATCH})
        d = out["hookSpecificOutput"]
        self.assertEqual(d["permissionDecision"], "deny")            # never "ask": Codex would just run it
        self.assertIn("Ask the user in chat to confirm", d["permissionDecisionReason"])
        self.assertIn("Codex hooks can't prompt you", out["systemMessage"])

    def test_codex_stop_uses_decision_block(self):
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        FakeSystemOne.override = {"rule0": NO, "rule1": NO, "scope": NO}
        self.codex_pre("apply_patch", {"command": self.PATCH})
        FakeSystemOne.override = {"missing": YES, "extra": NO}
        out = hook({"hook_event_name": "Stop", "session_id": "s1", "turn_id": "t1", "cwd": str(self.repo)})
        self.assertEqual(out["decision"], "block")
        self.assertIn("don't do yet", out["reason"])
        self.assertIn("Codex was sent back", out["systemMessage"])

    def test_codex_relays_notices_to_the_model(self):
        FakeSystemOne.override = {"find": NO, "new0": NO}
        out = hook({"hook_event_name": "UserPromptSubmit", "session_id": "s1", "turn_id": "t1",
                    "cwd": str(self.repo), "prompt": "fix the typo"})
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("tell them in one short line", ctx)
        self.assertIn("⚖ Jev read your prompt", ctx)
        FakeSystemOne.override = {"find": NO, "new0": NO}
        claude = hook({"hook_event_name": "UserPromptSubmit", "session_id": "s1", "cwd": str(self.repo),
                       "prompt": "fix the typo"})
        self.assertNotIn("hookSpecificOutput", claude)               # Claude shows systemMessage itself

    def test_codex_always_gets_json(self):
        out = hook({"hook_event_name": "Stop", "session_id": "s1", "turn_id": "t1", "cwd": str(self.repo),
                    "stop_hook_active": True})
        self.assertEqual(out, {})                                    # "{}", never empty stdout

    def test_codex_session_notice_names_codex_commands(self):
        os.environ.update(DECISION_MAKER_MODE="auto", PLUGIN_ROOT="/x")
        msg = hook({"hook_event_name": "SessionStart", "session_id": "s1"})["systemMessage"]
        self.assertIn('ask Codex "$decision-maker manual"', msg)
        self.assertNotIn("/decision-maker:jev", msg)

    def test_clean_action_is_allowed_and_reported(self):
        FakeSystemOne.override = {"rule0": NO, "rule1": NO, "scope": NO}
        out = self.pre("Write", {"file_path": "/x/b.py", "content": "x"})
        self.assertNotIn("hookSpecificOutput", out)                     # no decision: allowed
        self.assertIn("⚖ Jev checked Write /x/b.py against 2 rules + scope → OK, allowed", out["systemMessage"])

    def test_risky_command_asks_never_denies(self):
        FakeSystemOne.override = {"rule0": NO, "rule1": NO, "scope": NO, "risky": YES}
        out = self.pre("Bash", {"command": "git push --force"})
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "ask")

    # -- temporary rules from the conversation -------------------------

    def test_prompt_instruction_becomes_session_rule_and_is_enforced(self):
        rules = self.prompt("Fix the date parser. Don't touch the tests folder.", {"new0": NO, "new1": YES})
        self.assertEqual(rules, ["Don't touch the tests folder."])
        self.assertIn("now enforcing", self.last_prompt_out["systemMessage"])
        FakeSystemOne.calls.clear()
        FakeSystemOne.override = {"rule0": YES, "rule1": NO, "rule2": NO, "scope": NO}
        out = self.pre("Edit", {"file_path": str(self.repo / "tests" / "t.py"), "old_string": "a", "new_string": "b"})
        reason = out["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("your instruction this session: Don't touch the tests folder.", reason)
        q = FakeSystemOne.calls[0][2]["questions"]["rule0"]["instructions"]
        self.assertEqual(q["rule"], "Don't touch the tests folder.")  # session rules come first

    def test_later_prompt_revokes_session_rule(self):
        self.prompt("Don't touch the tests folder.", {"new0": YES})
        rules = self.prompt("You can edit the tests now.", {"old0": YES, "new0": NO})
        self.assertEqual(rules, [])

    def test_rules_survive_jev_outage(self):
        self.prompt("Never run migrations.", {"new0": YES})
        os.environ["FAKE_KEY"] = "wrong"
        self.assertEqual(self.prompt("next step please", {}), ["Never run migrations."])

    def test_nested_rule_files_nearest_first(self):
        sub = self.repo / "api"
        sub.mkdir()
        (sub / "AGENTS.md").write_text("- Every handler must validate its input with pydantic\n")
        (self.repo / "CLAUDE.local.md").write_text("- Do not add new dependencies without asking\n")
        rules = guard.load_rules(str(self.repo), str(sub / "h.py"))
        self.assertEqual(rules[0], ("Every handler must validate its input with pydantic", "api/AGENTS.md"))
        self.assertIn(("Do not add new dependencies without asking", "CLAUDE.local.md"), rules)
        self.assertEqual([r for r, _ in guard.load_rules(str(self.repo))][0],
                         "Never commit secrets or API keys to the repo")  # Bash: root only

    # -- decide instead of asking ---------------------------------------

    def ask(self, choice_conf, user_only):
        FakeSystemOne.override = {
            "q0": {"type": "choice", "choice": "pytest", "probabilities": {"pytest": 0.95, "unittest": 0.05},
                   "confidence": choice_conf},
            "user0": {"type": "noul", "noul": user_only}}
        return self.pre("AskUserQuestion", {"questions": [{
            "question": "Which test runner?", "header": "Tests", "multiSelect": False,
            "options": [{"label": "pytest", "description": "repo already uses it"},
                        {"label": "unittest", "description": "stdlib"}]}]})

    def test_confident_answer_replaces_question(self):
        out = self.ask(0.92, 0.05)
        d = out["hookSpecificOutput"]
        self.assertEqual(d["permissionDecision"], "deny")
        self.assertIn("pytest", d["permissionDecisionReason"])
        self.assertIn("answered for you", out["systemMessage"])

    def test_unsure_answer_lets_user_decide(self):
        out = self.ask(0.55, 0.05)
        self.assertNotIn("hookSpecificOutput", out)                     # question goes through to the user
        self.assertIn("asking you", out["systemMessage"])

    def test_users_own_call_is_never_auto_answered(self):
        self.assertNotIn("hookSpecificOutput", self.ask(0.99, 0.6))

    # -- request vs. diff at Stop -----------------------------------------

    def stop(self, **extra):
        return hook({"hook_event_name": "Stop", "session_id": "s1", "cwd": str(self.repo), **extra})

    def test_stop_blocks_when_request_unfinished(self):
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        FakeSystemOne.override = {"rule0": NO, "rule1": NO, "scope": NO}
        self.pre("Edit", {"file_path": str(self.repo / "CLAUDE.md"), "old_string": "a", "new_string": "b"})
        FakeSystemOne.override = {"missing": YES, "extra": NO}
        out = self.stop()
        ctx = out["hookSpecificOutput"]
        self.assertEqual(ctx["hookEventName"], "Stop")
        self.assertIn("don't do yet", ctx["additionalContext"])
        self.assertIn("request vs. diff", out["systemMessage"])
        self.assertIsNone(self.stop(stop_hook_active=True))  # never loops

    def test_stop_without_edits_is_silent(self):
        self.assertIsNone(self.stop())
        self.assertEqual(FakeSystemOne.calls, [])

    # -- safety ----------------------------------------------------------

    def mode(self, m):
        import decide
        with contextlib.redirect_stdout(io.StringIO()):
            decide.main(["mode", m])

    def test_mode_not_chosen_runs_nothing_and_asks_every_session(self):
        del os.environ["DECISION_MAKER_GUARD"]                 # user never picked features
        self.assertFalse(guard.enabled("prefetch") or guard.enabled("rules"))
        for _ in range(2):                                      # reminder repeats until chosen
            out = hook({"hook_event_name": "SessionStart", "session_id": "s1"})
            self.assertIn("NOT CHOSEN", out["systemMessage"])
            self.assertNotIn("hookSpecificOutput", out)         # no command hint either

    def test_auto_mode_turns_on_prefetch_and_hint(self):
        del os.environ["DECISION_MAKER_GUARD"]
        self.mode("auto")
        self.assertTrue(guard.enabled("prefetch"))
        self.assertFalse(guard.enabled("rules"))
        out = hook({"hook_event_name": "SessionStart", "session_id": "s1"})
        self.assertIn("Mode: auto", out["systemMessage"])
        self.assertIn("decide.py ask --items", out["hookSpecificOutput"]["additionalContext"])
        again = hook({"hook_event_name": "SessionStart", "session_id": "s1"})
        self.assertNotIn("systemMessage", again)                # chosen → no repeated notice to the user
        self.assertIn("hookSpecificOutput", again)              # ... but Claude keeps getting the hint

    def test_manual_mode_runs_nothing_automatic(self):
        del os.environ["DECISION_MAKER_GUARD"]
        self.mode("manual")
        self.assertFalse(guard.enabled("prefetch"))
        out = hook({"hook_event_name": "SessionStart", "session_id": "s1"})
        self.assertIn("Mode: manual", out["systemMessage"])
        self.assertNotIn("hookSpecificOutput", out)
        n = len(FakeSystemOne.calls)
        hook({"hook_event_name": "UserPromptSubmit", "session_id": "s1", "cwd": str(self.repo),
              "prompt": "Which files implement refund logic?"})
        self.assertEqual(len(FakeSystemOne.calls), n)           # not even the per-prompt call

    def test_explicit_guard_choice_beats_mode(self):
        del os.environ["DECISION_MAKER_GUARD"]
        self.mode("auto")
        import decide
        with contextlib.redirect_stdout(io.StringIO()):
            decide.main(["guard", "off"])
        self.assertFalse(guard.enabled("prefetch"))
        self.mode("manual")
        with contextlib.redirect_stdout(io.StringIO()):
            decide.main(["guard", "on", "rules"])
        self.assertTrue(guard.enabled("rules"))

    def test_guard_on_keeps_default_prefetch(self):
        del os.environ["DECISION_MAKER_GUARD"]
        self.mode("auto")
        import decide
        with contextlib.redirect_stdout(io.StringIO()):
            decide.main(["guard", "on"])
        self.assertTrue(guard.enabled("rules") and guard.enabled("prefetch"))
        with contextlib.redirect_stdout(io.StringIO()):
            decide.main(["guard", "off"])
            decide.main(["guard", "on"])                         # after an explicit off, prefetch stays off
        self.assertTrue(guard.enabled("rules"))
        self.assertFalse(guard.enabled("prefetch"))

    def test_all_does_not_include_prefetch(self):
        os.environ["DECISION_MAKER_GUARD"] = "all"
        self.assertTrue(guard.enabled("rules"))
        self.assertFalse(guard.enabled("prefetch"))

    def test_disabled_makes_no_call(self):
        os.environ["DECISION_MAKER_GUARD"] = ""
        self.assertIsNone(self.pre("Bash", {"command": "ls"}))
        self.assertEqual(FakeSystemOne.calls, [])

    def test_fails_open_on_api_error_and_says_so(self):
        os.environ["FAKE_KEY"] = "wrong"
        out = self.pre("Bash", {"command": "npm i x"})
        self.assertNotIn("hookSpecificOutput", out)                     # fails open: allowed
        self.assertIn("Jev unavailable", out["systemMessage"])

    def test_transcript_fallback_reads_real_prompt(self):
        t = self.root / "t.jsonl"
        lines = [{"type": "user", "message": {"role": "user", "content": "<command-name>/goal</command-name>"
                                                                          "<command-args>ship the parser</command-args>"}},
                 {"type": "user", "isMeta": True, "message": {"role": "user", "content": "meta"}},
                 {"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "content": "x"}]}},
                 {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Edit",
                                                                "input": {"file_path": "/r/p.py"}}]}}]
        t.write_text("\n".join(json.dumps(x) for x in lines))
        self.assertEqual(guard.read_transcript(str(t)), ("ship the parser", ["/r/p.py"]))


if __name__ == "__main__":
    unittest.main()
