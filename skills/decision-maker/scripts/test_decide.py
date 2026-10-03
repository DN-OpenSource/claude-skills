"""Tests for decide.py. Run from this directory: python -m unittest test_decide -v

Uses a local fake System One server, so no API key or network is needed.
"""
import contextlib
import io
import json
import os
import stat
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock

import decide


class FakeSystemOne(BaseHTTPRequestHandler):
    calls = []        # (path, auth header, body)
    fail_first = 0    # respond 529 this many times before succeeding
    override = {}     # qid -> canned answer (for guard tests)

    def log_message(self, *a):
        pass

    def _reply(self, status, obj, headers=None):
        data = json.dumps(obj).encode()
        self.send_response(status)
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        FakeSystemOne.calls.append((self.path, self.headers.get("Authorization"), None))
        self._reply(200, {"models": [{"name": "jev-latest"}]})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeSystemOne.calls.append((self.path, self.headers.get("Authorization"), body))
        if FakeSystemOne.fail_first:
            FakeSystemOne.fail_first -= 1
            return self._reply(529, {"error": "overloaded"}, {"retry-after": "0"})
        if self.headers.get("Authorization") != "Bearer good-key":
            return self._reply(401, {"error": "bad key"})
        answers = {}
        for qid, q in body["questions"].items():
            if qid in FakeSystemOne.override:
                answers[qid] = FakeSystemOne.override[qid]
                continue
            if q["type"] == "noul":
                answers[qid] = {"type": "noul", "noul": 0.95}
            elif q["type"] == "choice":
                opts = list(q["criteria"])
                probs = {o: 0.0 for o in opts}
                probs[opts[0]] = 1.0
                answers[qid] = {"type": "choice", "choice": opts[0],
                                "probabilities": probs, "confidence": 0.6}
            else:
                answers[qid] = {"type": "score", "score": 1.0, "confidence": 0.9,
                                "legend": {}, "probabilities": {}}
        self._reply(200, {"model": "jev-1.13.0", "answers": answers,
                          "usage": {"input_tokens": 10, "output_tokens": 2}})


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = decide.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class TestDecide(unittest.TestCase):
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
        FakeSystemOne.fail_first = 0
        FakeSystemOne.override = {}
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = Path(self.tmp.name) / "providers.json"
        env = {k: v for k, v in os.environ.items()
               if not k.startswith(("TYPESAFE_", "DECISION_MAKER_", "OPENROUTER_", "OPENJEV_", "LITELLM_"))}
        env["DECISION_MAKER_CONFIG"] = str(self.cfg)
        self.env = mock.patch.dict(os.environ, env, clear=True)
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def add_fake(self, *extra):
        return run("provider", "add", "fake", "--base-url", self.url,
                   "--api-key-env", "FAKE_KEY", "--default", *extra)

    # -- provider management --------------------------------------------

    def test_presets_listed_without_config(self):
        code, out, _ = run("provider", "list")
        self.assertEqual(code, 0)
        for name in ("typesafe", "openrouter", "openjev", "litellm"):
            self.assertIn(name, out)
        self.assertIn("typesafe *default", out)
        self.assertIn("$TYPESAFE_API_KEY (NOT SET)", out)

    def test_add_edit_use_remove(self):
        self.assertEqual(self.add_fake()[0], 0)
        cfg = json.loads(self.cfg.read_text())
        self.assertEqual(cfg["default"], "fake")
        self.assertEqual(cfg["providers"]["fake"]["base_url"], self.url)
        # config may hold keys: owner-only
        self.assertEqual(stat.S_IMODE(self.cfg.stat().st_mode), 0o600)

        self.assertEqual(run("provider", "add", "fake", "--base-url", "x")[0], 2)  # exists
        self.assertEqual(run("provider", "edit", "fake", "--api-key", "inline")[0], 0)
        entry = json.loads(self.cfg.read_text())["providers"]["fake"]
        self.assertEqual(entry["api_key"], "inline")
        self.assertNotIn("api_key_env", entry)  # key and env var are exclusive

        self.assertEqual(run("provider", "use", "typesafe")[0], 0)
        self.assertEqual(run("provider", "remove", "fake")[0], 0)
        self.assertNotIn("fake", json.loads(self.cfg.read_text())["providers"])

    def test_edit_preset_base_url(self):
        self.assertEqual(run("provider", "edit", "litellm", "--base-url", "http://gw:9/typesafe")[0], 0)
        p = decide.all_providers(decide.load_config())["litellm"]
        self.assertEqual(p["base_url"], "http://gw:9/typesafe")
        self.assertEqual(p["api_key_env"], "LITELLM_API_KEY")  # rest of the preset kept
        self.assertEqual(run("provider", "remove", "typesafe")[0], 2)  # presets not removable

    def test_list_masks_inline_key(self):
        run("provider", "add", "x", "--base-url", self.url, "--api-key", "sk-1234567890abcdef")
        _, out, _ = run("provider", "list")
        self.assertNotIn("sk-1234567890abcdef", out)
        self.assertIn("sk-1…cdef", out)

    # -- asking ----------------------------------------------------------

    def test_ask_batches_all_questions_in_one_call(self):
        self.add_fake()
        os.environ["FAKE_KEY"] = "good-key"
        code, out, err = run("ask", "--state", "payouts failing for 3 days",
                             "--noul", "urgent", "Is this urgent?",
                             "--choice", "team", "Which team?", "billing,technical",
                             "--score", "anger", "How angry?", "calm|annoyed|furious")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(FakeSystemOne.calls), 1)
        path, auth, body = FakeSystemOne.calls[0]
        self.assertEqual((path, auth), ("/v1/systemone", "Bearer good-key"))
        self.assertEqual(body["model"], "jev-latest")  # unset model falls back to default
        self.assertEqual(body["questions"]["team"]["criteria"], {"billing": None, "technical": None})
        self.assertEqual(body["questions"]["anger"]["criteria"], ["calm", "annoyed", "furious"])
        res = json.loads(out)
        self.assertEqual(res["provider"], "fake")
        self.assertTrue(res["answers"]["urgent"]["act"])     # noul 0.95 ≥ 0.8
        self.assertFalse(res["answers"]["team"]["act"])      # confidence 0.6 < 0.8
        self.assertTrue(res["answers"]["anger"]["act"])

    def test_json_state_sent_structured(self):
        self.add_fake()
        os.environ["FAKE_KEY"] = "good-key"
        run("ask", "--state", '{"ticket": "hi"}', "--noul", "q", "Is it a greeting?")
        self.assertEqual(FakeSystemOne.calls[0][2]["state"], {"ticket": "hi"})

    def test_retries_overload_then_succeeds(self):
        self.add_fake()
        os.environ["FAKE_KEY"] = "good-key"
        FakeSystemOne.fail_first = 2
        code, _, err = run("ask", "--state", "s", "--noul", "q", "?")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(FakeSystemOne.calls), 3)

    def test_bad_key_is_exit_1(self):
        self.add_fake()
        os.environ["FAKE_KEY"] = "wrong"
        code, _, err = run("ask", "--state", "s", "--noul", "q", "?")
        self.assertEqual(code, 1)
        self.assertIn("HTTP 401", err)

    def test_missing_key_is_exit_2_and_sends_nothing(self):
        code, _, err = run("ask", "--state", "s", "--noul", "q", "?")
        self.assertEqual(code, 2)
        self.assertIn("TYPESAFE_API_KEY", err)
        self.assertEqual(FakeSystemOne.calls, [])

    def test_dry_run_needs_no_key(self):
        code, out, err = run("ask", "--dry-run", "--state", "s", "--noul", "q", "?")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["url"], "https://api.typesafe.ai/v1/systemone")
        self.assertEqual(FakeSystemOne.calls, [])

    def test_local_validation(self):
        self.add_fake()
        os.environ["FAKE_KEY"] = "good-key"
        self.assertEqual(run("ask", "--state", "s", "--choice", "c", "?", "only_one")[0], 2)
        self.assertEqual(run("ask", "--state", "s", "--score", "c", "?", "one")[0], 2)
        self.assertEqual(run("ask", "--state", "s")[0], 2)  # no questions
        self.assertEqual(FakeSystemOne.calls, [])

    def test_items_one_request_per_batch_and_brief(self):
        self.add_fake()
        os.environ["FAKE_KEY"] = "good-key"
        hits = Path(self.tmp.name) / "hits.txt"
        hits.write_text("SELECT * FROM orders\n\n# sort orders in UI\nINSERT INTO orders VALUES (1)\n")
        code, out, err = run("ask", "--items", str(hits), "--noul", "real", "Does {item} touch the orders table?",
                             "--brief", "--where", "all")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(FakeSystemOne.calls), 1)               # 3 items, one request
        body = FakeSystemOne.calls[0][2]
        self.assertEqual(body["state"]["items"]["i2"], "INSERT INTO orders VALUES (1)")
        self.assertEqual(body["questions"]["real#0"]["instructions"],
                         "Does `items.i0` touch the orders table?")
        lines = out.strip().splitlines()
        self.assertTrue(lines[0].startswith(f"{hits}:1\treal\t0.95"))
        self.assertTrue(lines[2].startswith(f"{hits}:4\t"))          # blank line skipped, numbering kept
        self.assertIn("# 3 items", lines[-1])

    def test_where_filters_brief_output(self):
        self.add_fake()
        os.environ["FAKE_KEY"] = "good-key"
        hits = Path(self.tmp.name) / "h.txt"
        hits.write_text("a\nb\n")
        FakeSystemOne.override = {"q#0": {"type": "noul", "noul": 0.9}, "q#1": {"type": "noul", "noul": 0.1}}
        code, out, _ = run("ask", "--items", str(hits), "--noul", "q", "Is {item} real?", "--brief", "--where", "yes")
        self.assertEqual(code, 0)
        lines = out.strip().splitlines()
        self.assertEqual(len(lines), 2)                 # only the yes item + footer
        self.assertTrue(lines[0].startswith(f"{hits}:1\t"))
        self.assertIn("0 unsure", lines[-1])

    def test_items_default_shows_hits_and_unsure_with_excerpt(self):
        self.add_fake()
        os.environ["FAKE_KEY"] = "good-key"
        hits = Path(self.tmp.name) / "h.txt"
        hits.write_text("yes line\nno line\nmaybe line\n")
        FakeSystemOne.override = {"q#0": {"type": "noul", "noul": 0.95}, "q#1": {"type": "noul", "noul": 0.03},
                                  "q#2": {"type": "noul", "noul": 0.55}}
        code, out, _ = run("ask", "--items", str(hits), "--noul", "q", "Is {item} real?", "--brief")
        self.assertEqual(code, 0)
        self.assertNotIn(":2\t", out)                        # confident "no" hidden
        self.assertIn(":1\tq\t0.95", out)
        self.assertIn(":3\tq\t0.55\t-\task\n    ↳ maybe line", out)   # unsure carries its text
        self.assertIn("1 unsure", out)

    def test_items_glob_batches(self):
        self.add_fake()
        os.environ["FAKE_KEY"] = "good-key"
        d = Path(self.tmp.name) / "src"
        d.mkdir()
        for i in range(5):
            (d / f"f{i}.py").write_text("x" * 100)
        with mock.patch.object(decide, "BATCH_ITEMS", 2):
            code, out, err = run("ask", "--items", str(d / "*.py"), "--noul", "q", "Is this relevant?", "--brief",
                                 "--where", "all")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(FakeSystemOne.calls), 3)                # 2 + 2 + 1, sent concurrently
        self.assertEqual([l.split("\t")[0] for l in out.strip().splitlines()[:5]],
                         [str(d / f"f{i}.py") for i in range(5)])   # order kept across parallel batches
        self.assertEqual(len(out.strip().splitlines()), 6)           # 5 answers + footer

    def test_models_endpoint(self):
        self.add_fake()
        os.environ["FAKE_KEY"] = "good-key"
        code, out, _ = run("models")
        self.assertEqual(code, 0)
        self.assertEqual(FakeSystemOne.calls[0][0], "/v1/models")
        self.assertIn("jev-latest", out)


if __name__ == "__main__":
    unittest.main()
