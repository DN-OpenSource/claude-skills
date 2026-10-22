#!/bin/sh
# Stop hook: if this project's product.json is newer than its product page, ask Claude (by
# blocking the stop) to re-render inside its own visible turn. Never writes anything itself.
# Pure shell, no Python: projects without docs/product/product.json pay two file tests.
cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0
data=docs/product/product.json
[ -f "$data" ] || exit 0
# a stop that this hook already blocked once: let it through (no loops)
input=$(cat 2>/dev/null)
case "$input" in *'"stop_hook_active": true'*|*'"stop_hook_active":true'*) exit 0 ;; esac
page=docs/product/index.html                      # same choice as render_page.py
if [ -d site ]; then page=site/product/index.html; elif [ -d public ]; then page=public/product/index.html; fi
if [ ! -f "$page" ] || [ "$data" -nt "$page" ]; then
  printf '%s\n' '{"decision": "block", "reason": "The product page is older than docs/product/product.json. Run the product-visionary render script with --if-stale (python3 <product-visionary plugin>/scripts/render_page.py --if-stale) and tell the user what changed."}'
fi
exit 0
