---
description: wrap-up should not trigger on a request about the same topic
tags: [trigger, negative, near-miss]
runs: 3
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Wrap this paragraph at 72 columns: The shop backend stores users, orders and order items in SQLite and exposes a helper that totals each user's orders.
