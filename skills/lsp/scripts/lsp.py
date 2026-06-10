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


# ----------------------------------------------------------- JSON-RPC framing


def write_message(stream, payload):
    body = json.dumps(payload).encode("utf-8")
    stream.write(b"Content-Length: " + str(len(body)).encode("ascii") + b"\r\n\r\n")
    stream.write(body)
    stream.flush()


def read_message(stream):
    """Read one framed message. Returns the parsed dict, or None on EOF."""
    length = None
    while True:
        line = stream.readline()
        if not line:
            return None
        line = line.strip()
        if not line:
            break  # end of headers
        if line.lower().startswith(b"content-length:"):
            length = int(line.split(b":", 1)[1])
    if length is None:
        return None
    body = stream.read(length)
    if body is None or len(body) < length:
        return None
    return json.loads(body.decode("utf-8"))


# ------------------------------------------------------------------ client


class LspClient:
    """Drives one language-server process for the lifetime of one invocation."""

    def __init__(self, cmd, root, timeout=30.0):
        self.cmd = cmd
        self.root = Path(root).resolve()
        self.timeout = timeout
        self.proc = None
        self.diagnostics = {}  # uri -> list of Diagnostic
        self._next_id = 0
        self._responses = {}
        self._cond = threading.Condition()
        self._reader = None

    def start(self):
        self.proc = subprocess.Popen(
            self.cmd, cwd=str(self.root),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL)
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        root_uri = path_to_uri(self.root)
        self.request("initialize", {
            "processId": os.getpid(),
            "rootUri": root_uri,
            "workspaceFolders": [{"uri": root_uri, "name": self.root.name}],
            "capabilities": {
                "textDocument": {
                    "synchronization": {},
                    "definition": {},
                    "references": {},
                    "hover": {"contentFormat": ["plaintext", "markdown"]},
                    "documentSymbol": {"hierarchicalDocumentSymbolSupport": True},
                    "rename": {},
                    "publishDiagnostics": {},
                },
                "workspace": {"symbol": {}, "workspaceEdit": {"documentChanges": True}},
            },
        })
        self.notify("initialized", {})

    def _read_loop(self):
        while True:
            try:
                msg = read_message(self.proc.stdout)
            except Exception:
                break
            if msg is None:
                break
            if "id" in msg and ("result" in msg or "error" in msg):
                with self._cond:
                    self._responses[msg["id"]] = msg
                    self._cond.notify_all()
            elif msg.get("method") == "textDocument/publishDiagnostics":
                params = msg.get("params") or {}
                with self._cond:
                    self.diagnostics[params.get("uri")] = params.get("diagnostics", [])
                    self._cond.notify_all()
            elif "id" in msg and "method" in msg:
                # Server-to-client request (config, registration…): answer null
                # so the server doesn't stall waiting on us.
                try:
                    write_message(self.proc.stdin,
                                  {"jsonrpc": "2.0", "id": msg["id"], "result": None})
                except Exception:
                    break

    def request(self, method, params):
        self._next_id += 1
        rid = self._next_id
        write_message(self.proc.stdin,
                      {"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        deadline = time.monotonic() + self.timeout
        with self._cond:
            while rid not in self._responses:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(f"no response to {method} within {self.timeout}s")
                self._cond.wait(remaining)
            msg = self._responses.pop(rid)
        if "error" in msg:
            raise RuntimeError(f"{method} failed: {msg['error'].get('message')}")
        return msg.get("result")

    def notify(self, method, params):
        write_message(self.proc.stdin,
                      {"jsonrpc": "2.0", "method": method, "params": params})

    def open_file(self, path):
        p = Path(path).resolve()
        self.notify("textDocument/didOpen", {"textDocument": {
            "uri": path_to_uri(p),
            "languageId": LANGUAGE_IDS.get(p.suffix, "plaintext"),
            "version": 1,
            "text": p.read_text(encoding="utf-8", errors="replace"),
        }})

    def wait_diagnostics(self, uris, wait_secs):
        """Wait until the server has pushed diagnostics for every uri (or timeout)."""
        deadline = time.monotonic() + wait_secs
        with self._cond:
            while not all(u in self.diagnostics for u in uris):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                self._cond.wait(remaining)
            return {u: self.diagnostics.get(u, []) for u in uris}

    def stop(self):
        if self.proc is None:
            return
        try:
            if self.proc.poll() is None:
                try:
                    saved, self.timeout = self.timeout, 3.0
                    self.request("shutdown", None)
                    self.timeout = saved
                except Exception:
                    pass
                self.notify("exit", {})
                self.proc.wait(timeout=5)
        except Exception:
            pass
        finally:
            if self.proc.poll() is None:
                self.proc.kill()


def query_with_retry(client, method, params, retry_secs):
    """Re-issue a query that returns None/[] (server may still be indexing)."""
    deadline = time.monotonic() + retry_secs
    while True:
        result = client.request(method, params)
        if result not in (None, []):
            return result
        if time.monotonic() >= deadline:
            return result
        time.sleep(1.0)
