---
description: teammates creates the shared manifest and spawns peers
tags: [step]
runs: 3
max_turns: 25
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill]
---

Use a flat team of peer agents to review utils.py, app.py and schema.sql in parallel and merge what they find.
