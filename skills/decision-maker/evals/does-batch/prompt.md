---
description: decision-maker sends every item in one batched call
tags: [step]
runs: 3
max_turns: 25
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill]
---

Use Jev to decide which of these files touch the database: app.py, utils.py, schema.sql, README.md.
