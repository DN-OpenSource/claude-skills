#!/usr/bin/env python3
"""One-shot LSP client: semantic code navigation from the command line.

Speaks JSON-RPC over stdio to a language server, runs one or more queries,
then shuts the server down. No daemon, no state between invocations.
Stdlib only — no pip installs.

Positions on the CLI are 1-based FILE:LINE:COL; LSP's 0-based positions are
an internal detail. Known limitation: LSP positions count UTF-16 code units;
this client converts correctly when applying rename edits, but column numbers
printed for lines containing astral-plane characters may differ from what
your editor shows.
"""
import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

# --------------------------------------------------------------- constants

# (stack, project markers checked in --root, server command, install hint)
SERVERS = [
    ("typescript", ("tsconfig.json", "package.json"),
     ["typescript-language-server", "--stdio"],
     "npm i -g typescript-language-server typescript"),
    ("python", ("pyproject.toml", "setup.py", "requirements.txt"),
     ["pyright-langserver", "--stdio"],
     "npm i -g pyright"),
    ("dart", ("pubspec.yaml",),
     ["dart", "language-server", "--protocol=lsp"],
     "install the Dart SDK (https://dart.dev/get-dart)"),
    ("rust", ("Cargo.toml",),
     ["rust-analyzer"],
     "rustup component add rust-analyzer"),
]

LANGUAGE_IDS = {
    ".ts": "typescript", ".tsx": "typescriptreact",
    ".mts": "typescript", ".cts": "typescript",
    ".js": "javascript", ".jsx": "javascriptreact",
    ".py": "python", ".pyi": "python",
    ".dart": "dart",
    ".rs": "rust",
}

SYMBOL_KINDS = {
    1: "file", 2: "module", 3: "namespace", 4: "package", 5: "class",
    6: "method", 7: "property", 8: "field", 9: "constructor", 10: "enum",
    11: "interface", 12: "function", 13: "variable", 14: "constant",
    15: "string", 16: "number", 17: "boolean", 18: "array", 19: "object",
    20: "key", 21: "null", 22: "enum-member", 23: "struct", 24: "event",
    25: "operator", 26: "type-parameter",
}

SEVERITIES = {1: "error", 2: "warning", 3: "info", 4: "hint"}

# ----------------------------------------------------------------- helpers


def parse_location(spec):
    """'FILE:LINE:COL' (1-based) -> (path, line, col). Windows-drive safe."""
    parts = spec.rsplit(":", 2)
    if len(parts) != 3:
        raise ValueError(f"expected FILE:LINE:COL, got {spec!r}")
    try:
        line, col = int(parts[1]), int(parts[2])
    except ValueError:
        raise ValueError(f"expected FILE:LINE:COL, got {spec!r}")
    if line < 1 or col < 1:
        raise ValueError("line and column are 1-based (must be >= 1)")
    return parts[0], line, col


def path_to_uri(path):
    s = str(Path(path).resolve()).replace("\\", "/")
    if not s.startswith("/"):
        s = "/" + s  # Windows drive paths: /C:/...
    return "file://" + quote(s, safe="/:")


def uri_to_path(uri):
    path = unquote(urlparse(uri).path)
    if re.match(r"^/[A-Za-z]:", path):
        path = path[1:]
    return str(Path(path))


def detect_server(root):
    """Return (stack, command, install_hint) from project markers, else None."""
    root = Path(root)
    for stack, markers, cmd, hint in SERVERS:
        if any((root / m).exists() for m in markers):
            return stack, list(cmd), hint
    return None


def split_command(value):
    """Split a --server string into argv. Windows-safe (keeps backslashes)."""
    if os.name == "nt":
        return [t.strip('"') for t in shlex.split(value, posix=False)]
    return shlex.split(value)
