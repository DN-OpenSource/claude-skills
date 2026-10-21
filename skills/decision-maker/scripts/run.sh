#!/bin/sh
# Run a Python script with the first interpreter that actually works.
# On Windows `python3` is often the Microsoft Store stub ("Python was not found"),
# so probe before running: retrying after a failure would re-run the script on its
# own non-zero exits (guard.py exits 2 to block an action).
# ponytail: one extra interpreter start per call (~20 ms); cache the pick if hooks feel slow.
for py in python3 python; do
  if "$py" -c "import sys" >/dev/null 2>&1; then
    exec "$py" "$@"
  fi
done
echo "decision-maker: no working Python found (tried python3, python); skipping" >&2
exit 0  # fail open, like guard.py itself
