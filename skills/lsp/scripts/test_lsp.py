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


if __name__ == "__main__":
    unittest.main()
