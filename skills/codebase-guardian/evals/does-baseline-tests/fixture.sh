#!/usr/bin/env bash
set -euo pipefail
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
git init -q
git checkout -q -b main 2>/dev/null || git switch -q -c main
git config user.email eval@example.com
git config user.name eval
git add -A
git commit -qm "Initial commit"
