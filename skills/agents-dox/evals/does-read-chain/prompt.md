---
description: agents-dox reads the AGENTS.md chain before editing
tags: [step]
runs: 3
max_turns: 25
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill]
---

Make slugify in utils.py also strip leading and trailing dashes.
