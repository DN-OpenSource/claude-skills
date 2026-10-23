---
description: schema-aware-db should trigger on a pasted query
tags: [trigger, positive]
runs: 3
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

This query returns duplicate rows, fix it: SELECT u.name, o.total FROM users u JOIN orders o ON o.user_id = u.id JOIN order_items i ON i.order_id = o.id;
