---
description: schema-aware-db should trigger even with 45 other skills loaded
tags: [trigger, crowded]
plugins: []
runs: 3
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Fix this SQL query that joins users and orders; it returns duplicate rows.
