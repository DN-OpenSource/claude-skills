"""Tests for lsp.py. Run from this directory: python -m unittest test_lsp -v"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

import lsp


class TestHelpers(unittest.TestCase):
    def test_parse_location_simple(self):
        self.assertEqual(lsp.parse_location("src/app.py:10:5"), ("src/app.py", 10, 5))

    def test_parse_location_windows_drive(self):
        # The drive colon must not be mistaken for a position separator.
        path, line, col = lsp.parse_location(r"C:\proj\src\app.ts:3:7")
        self.assertEqual((path, line, col), (r"C:\proj\src\app.ts", 3, 7))

    def test_parse_location_rejects_missing_parts(self):
        with self.assertRaises(ValueError):
            lsp.parse_location("src/app.py:10")

    def test_parse_location_rejects_zero(self):
        with self.assertRaises(ValueError):
            lsp.parse_location("src/app.py:0:1")

    def test_uri_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "a b" / "f.py"
            p.parent.mkdir()
            p.write_text("x = 1\n", encoding="utf-8")
            uri = lsp.path_to_uri(p)
            self.assertTrue(uri.startswith("file:///"))
            self.assertNotIn(" ", uri)  # space must be percent-encoded
            self.assertEqual(Path(lsp.uri_to_path(uri)), p.resolve())

    def test_language_id(self):
        self.assertEqual(lsp.LANGUAGE_IDS[".py"], "python")
        self.assertEqual(lsp.LANGUAGE_IDS[".tsx"], "typescriptreact")
        self.assertEqual(lsp.LANGUAGE_IDS[".rs"], "rust")
        self.assertEqual(lsp.LANGUAGE_IDS[".dart"], "dart")

    def test_detect_server_typescript_wins_over_python(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "package.json").write_text("{}", encoding="utf-8")
            (Path(tmp) / "pyproject.toml").write_text("", encoding="utf-8")
            stack, cmd, hint = lsp.detect_server(tmp)
            self.assertEqual(stack, "typescript")
            self.assertEqual(cmd[0], "typescript-language-server")

    def test_detect_server_rust(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "Cargo.toml").write_text("", encoding="utf-8")
            stack, cmd, hint = lsp.detect_server(tmp)
            self.assertEqual(stack, "rust")

    def test_detect_server_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(lsp.detect_server(tmp))

    def test_split_command_strips_quotes(self):
        parts = lsp.split_command('"/usr/bin/python3" "/tmp/fake server.py" --stdio')
        self.assertEqual(parts[-1], "--stdio")
        self.assertEqual(len(parts), 3)
        for part in parts:
            self.assertFalse(part.startswith('"'))


import io


class TestFraming(unittest.TestCase):
    def test_write_then_read_roundtrip(self):
        buf = io.BytesIO()
        lsp.write_message(buf, {"jsonrpc": "2.0", "id": 1, "method": "x"})
        buf.seek(0)
        msg = lsp.read_message(buf)
        self.assertEqual(msg, {"jsonrpc": "2.0", "id": 1, "method": "x"})

    def test_read_handles_extra_headers(self):
        body = json.dumps({"ok": True}).encode()
        raw = (b"Content-Type: application/vscode-jsonrpc; charset=utf-8\r\n"
               b"Content-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body)
        msg = lsp.read_message(io.BytesIO(raw))
        self.assertEqual(msg, {"ok": True})

    def test_read_eof_returns_none(self):
        self.assertIsNone(lsp.read_message(io.BytesIO(b"")))

    def test_write_counts_utf8_bytes_not_chars(self):
        buf = io.BytesIO()
        lsp.write_message(buf, {"name": "héllo"})
        buf.seek(0)
        self.assertEqual(lsp.read_message(buf), {"name": "héllo"})


FAKE_SERVER = [sys.executable, str(Path(__file__).resolve().parent / "fake_lsp_server.py")]


def make_project(tmp):
    """A two-line file: 'foo = 1\\nbar = foo\\n'."""
    p = Path(tmp) / "sample.py"
    p.write_text("foo = 1\nbar = foo\n", encoding="utf-8")
    return p


class TestClient(unittest.TestCase):
    def _client(self, root):
        c = lsp.LspClient(FAKE_SERVER, root, timeout=10.0)
        c.start()
        self.addCleanup(c.stop)
        return c

    def test_initialize_and_definition(self):
        # stop() inside the with-block: on Windows the temp dir can't be
        # removed while the server child still has it as its cwd.
        with tempfile.TemporaryDirectory() as tmp:
            p = make_project(tmp)
            c = self._client(tmp)
            try:
                c.open_file(p)
                result = c.request("textDocument/definition", {
                    "textDocument": {"uri": lsp.path_to_uri(p)},
                    "position": {"line": 1, "character": 6}})
                self.assertEqual(result[0]["range"]["start"],
                                 {"line": 0, "character": 0})
            finally:
                c.stop()

    def test_diagnostics_push_collected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = make_project(tmp)
            c = self._client(tmp)
            try:
                c.open_file(p)
                uri = lsp.path_to_uri(p)
                by_uri = c.wait_diagnostics([uri], wait_secs=10.0)
                self.assertEqual(by_uri[uri][0]["message"], "fake warning")
            finally:
                c.stop()

    def test_request_timeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            c = self._client(tmp)
            try:
                c.timeout = 0.5
                with self.assertRaises(TimeoutError):
                    # the fake server deliberately never answers $/test/noreply
                    c.request("$/test/noreply", {})
            finally:
                c.stop()


class TestQueryRetry(unittest.TestCase):
    def test_retries_empty_then_returns(self):
        calls = []

        class Stub:
            def request(self, method, params):
                calls.append(method)
                return [] if len(calls) < 2 else ["hit"]

        result = lsp.query_with_retry(Stub(), "m", {}, retry_secs=5.0)
        self.assertEqual(result, ["hit"])
        self.assertEqual(len(calls), 2)

    def test_gives_up_after_window(self):
        class Stub:
            def request(self, method, params):
                return None

        result = lsp.query_with_retry(Stub(), "m", {}, retry_secs=0.0)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
