---
description: memory should not trigger on a request about the same topic
tags: [trigger, negative, near-miss]
runs: 3
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

How much memory does a Python dict with a million int keys use?
