---
description: codebase-guardian should not trigger on a request about the same topic
tags: [trigger, negative, near-miss]
runs: 3
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Explain what this regex matches: ^\d{3}-\d{4}$
