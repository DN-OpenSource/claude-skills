---
description: agents-dox runs the checks before and after an edit in a DOX repo
tags: [step]
runs: 3
max_turns: 25
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill]
---

Make slugify in utils.py also strip leading and trailing dashes.
