---
description: Show what Jev (decision-maker) does in this Claude Code install, what it sends where, and what it did recently
allowed-tools: Bash(python3:*)
---

Run these and show the user the results:

1. `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/decide.py" guard status`
2. `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/decide.py" guard log -n 10`

Then explain in plain words, briefly:

- **Active or not:** is a provider key set? Without one, nothing is sent and nothing runs.
- **What runs automatically:** which guard checks are on (rules, scope, ask, stop, prefetch), what each does, and that every block, ask or auto-answer is shown to the user.
- **What Claude may do on its own:** call Jev to sort many files or lines, and run browser test steps.
- **What leaves the machine,** and to which provider, exactly as the status lists it.
- **What Jev did recently,** from the log, or say it has done nothing yet.
- **How to change it:** `decide.py guard on|off [features]`, `decide.py provider ...`, and `DECISION_MAKER_HINT=0` to stop the session hint.

If the user passed an argument ($ARGUMENTS) such as "off", "on", or a feature list, run `guard <that>` first, then show the status.
