#!/usr/bin/env bash
set -euo pipefail
cat > schema.sql <<'SQL'
CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), total REAL NOT NULL);
CREATE TABLE order_items (id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(id), sku TEXT NOT NULL);
SQL
cat > app.py <<'PY'
import sqlite3

db = sqlite3.connect("shop.db")


def user_totals():
    return db.execute(
        "SELECT u.name, o.total FROM users u"
        " JOIN orders o ON o.user_id = u.id"
        " JOIN order_items i ON i.order_id = o.id"
    ).fetchall()
PY
cat > utils.py <<'PY'
import re


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower())
PY
cat > test_utils.py <<'PY'
import unittest

from utils import slugify


class SlugifyTest(unittest.TestCase):
    def test_lowercases_and_joins_words(self):
        self.assertEqual(slugify("Hello World"), "hello-world")


if __name__ == "__main__":
    unittest.main()
PY
printf '# shop\n\nA tiny shop backend.\n' > README.md
git init -q
git checkout -q -b main 2>/dev/null || git switch -q -c main
git config user.email eval@example.com
git config user.name eval
git add -A
git commit -qm "Initial commit"
